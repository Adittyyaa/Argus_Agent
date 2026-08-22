"""
mock_armoriq/client.py
======================
Mock implementation of the ArmorIQ SDK.

Mirrors the real SDK's public API:
    capture_plan(description, tools, user_email) -> plan_id
    delegate(plan_id, sub_agent_id, scope, ttl_seconds)  -> token
    invoke(token, tool_name, args, execute_fn)  -> result | raises PermissionError

Tokens are self-contained JWTs signed with HMAC-SHA256.
All decisions (ALLOWED / BLOCKED / EXPIRED) are written to audit.db.
"""

import os
import sys
import json
import time
import uuid
import hmac
import hashlib
import base64
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

from dotenv import load_dotenv

# ── Load environment variables from .env ──────────────────────────────
load_dotenv()

# ── resolve project root so audit.logger can be imported from any cwd ──
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Check for parent directory .env if not loaded
parent_env = os.path.join(os.path.dirname(_ROOT), ".env")
if os.path.exists(parent_env):
    load_dotenv(parent_env)

from audit.logger import AuditLogger  # noqa: E402  (import after path fix)

try:
    from armoriq_sdk import ArmorIQClient as RealArmorIQClient
    HAS_REAL_SDK = True
except ImportError:
    HAS_REAL_SDK = False

# ── shared HMAC secret (same for coordinator and all sub-agents) ───────
_SHARED_SECRET = os.getenv("ARMORIQ_SHARED_SECRET", "authorchain-demo-secret-2026")

# ── ANSI colour helpers ────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _clr(color: str, text: str) -> str:
    return f"{color}{text}{RESET}"


class ArmorIQClient:
    """
    ArmorIQ SDK Client supporting both Real ArmorIQ Cloud Integration and Local Governance.

    Each process (coordinator or sub-agent) creates its own instance with
    a unique agent_id representing its identity / keypair.
    """

    def __init__(self, agent_id: str, api_key: Optional[str] = None):
        self.agent_id = agent_id
        self.api_key  = api_key or os.getenv("ARMORIQ_API_KEY", "")
        self.mode     = os.getenv("ARMORIQ_MODE", "mock").strip().lower()
        self._secret  = _SHARED_SECRET
        self._logger  = AuditLogger()
        self._real_client = None

        if HAS_REAL_SDK and self.api_key and self.api_key != "mock-key" and self.api_key.startswith("ak_"):
            try:
                self._real_client = RealArmorIQClient(api_key=self.api_key)
                masked_key = self.api_key[:10] + "..." + self.api_key[-6:]
                print(_clr(GREEN, f"[ArmorIQ Cloud] 🔒 Connected to platform.armoriq.ai  agent={agent_id}  key={masked_key}"))
            except Exception as e:
                print(_clr(YELLOW, f"[ArmorIQ] Failed to initialize Real SDK ({e}), falling back to local governance."))
        else:
            print(_clr(CYAN, f"[ArmorIQ Local] Client initialized  agent={agent_id}  keypair=sha256/{agent_id[:8]}..."))

    # ──────────────────────────────────────────────────────────────────
    # capture_plan  –  declare intent BEFORE any delegation
    # ──────────────────────────────────────────────────────────────────
    def capture_plan(
        self,
        description: str,
        tools: List[str],
        user_email: str = "user@demo.com",
    ) -> str:
        """
        Canonicalise and mint an intent plan.
        Returns a plan_id that must be passed to every delegate() call.
        """
        plan_id = f"plan-{uuid.uuid4().hex[:10]}"
        cloud_token_id = None
        plan_hash = None

        if self._real_client:
            try:
                plan_dict = {
                    "goal": description,
                    "steps": [{"action": tool, "mcp": f"{tool}_mcp"} for tool in tools]
                }
                captured = self._real_client.capture_plan(llm="gpt-4o", prompt=description, plan=plan_dict)
                intent_token = self._real_client.get_intent_token(captured)
                cloud_token_id = getattr(intent_token, "token_id", None)
                plan_hash = getattr(intent_token, "plan_hash", None)
                if hasattr(intent_token, "plan_id") and intent_token.plan_id:
                    plan_id = f"plan-{intent_token.plan_id[:10]}"
            except Exception as e:
                print(_clr(YELLOW, f"[ArmorIQ Cloud] Cloud plan capture warning: {e}"))

        self._logger.log_plan(plan_id, description, tools, user_email, self.agent_id)

        print(_clr(BOLD, f"\n[ArmorIQ] ┌── capture_plan ──────────────────────────────────────"))
        print(_clr(CYAN,  f"[ArmorIQ] │  plan_id : {plan_id}"))
        print(_clr(CYAN,  f"[ArmorIQ] │  intent  : {description[:80]}"))
        print(_clr(CYAN,  f"[ArmorIQ] │  tools   : {tools}"))
        print(_clr(CYAN,  f"[ArmorIQ] │  user    : {user_email}"))
        if cloud_token_id:
            print(_clr(GREEN, f"[ArmorIQ] │  cloud_token_id : {cloud_token_id[:16]}..."))
        if plan_hash:
            print(_clr(GREEN, f"[ArmorIQ] │  merkle_root    : {plan_hash[:16]}..."))
        print(_clr(BOLD,  f"[ArmorIQ] └─────────────────────────────────────────────────────\n"))
        return plan_id

    # ──────────────────────────────────────────────────────────────────
    # delegate  –  issue a scoped, signed token to a sub-agent
    # ──────────────────────────────────────────────────────────────────
    def delegate(
        self,
        plan_id: str,
        sub_agent_id: str,
        scope: List[str],
        ttl_seconds: int = 300,
    ) -> str:
        """
        Mint a cryptographically signed delegation token.
        The token encodes: agent_id, scope, expiry, plan_id, issuer.
        """
        delegation_id = f"del-{uuid.uuid4().hex[:10]}"
        issued_at     = time.time()
        expires_at    = issued_at + ttl_seconds

        payload: Dict[str, Any] = {
            "delegation_id": delegation_id,
            "plan_id":        plan_id,
            "agent_id":       sub_agent_id,
            "issued_by":      self.agent_id,
            "scope":          scope,
            "iat":            issued_at,
            "exp":            expires_at,
        }

        # Base64-encode the payload, then HMAC-sign it
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        sig = hmac.new(self._secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        token = f"{payload_b64}.{sig}"

        self._logger.log_delegation(delegation_id, plan_id, sub_agent_id, scope, ttl_seconds, self.agent_id)

        print(_clr(GREEN, f"[ArmorIQ] delegate() → {sub_agent_id}"))
        print(_clr(GREEN, f"           scope     : {scope}"))
        print(_clr(GREEN, f"           ttl       : {ttl_seconds}s  expires: {datetime.fromtimestamp(expires_at).strftime('%H:%M:%S')}"))
        print(_clr(GREEN, f"           del_id    : {delegation_id}"))
        return token

    # ──────────────────────────────────────────────────────────────────
    # invoke  –  THE enforcement point (only active when sub-agent calls it)
    # ──────────────────────────────────────────────────────────────────
    def invoke(
        self,
        token: str,
        tool_name: str,
        args: Dict[str, Any],
        execute_fn: Callable[[str, Dict], Any],
    ) -> Any:
        """
        Governed tool invocation.

        Steps:
          1. Verify HMAC signature of the token.
          2. Check token expiry (TTL).
          3. Check that tool_name is inside the delegated scope.
          4. Execute the tool only if all checks pass.
          5. Log every decision — ALLOWED / BLOCKED / EXPIRED.

        Raises PermissionError on any violation.
        """
        print(_clr(BOLD, f"\n[ArmorIQ] invoke() ▶  tool={tool_name}  agent={self.agent_id}"))

        payload, status = self._verify_token(token)

        # ── 1. Invalid signature ──────────────────────────────────────
        if status == "INVALID_SIGNATURE":
            reason = "Token HMAC signature verification failed"
            print(_clr(RED, f"[ArmorIQ]   ✗ BLOCKED  {reason}"))
            self._logger.log_invoke(
                agent_id=self.agent_id, tool_name=tool_name, args=args,
                status="BLOCKED", reason=reason, plan_id=None,
                delegation_id=None, scope=[], ttl_remaining=0.0,
            )
            raise PermissionError(f"ArmorIQ BLOCKED: {reason}")

        # ── 2. Expired token ──────────────────────────────────────────
        if status == "EXPIRED":
            ttl_rem  = payload["exp"] - time.time()
            reason   = f"Delegation token expired {abs(ttl_rem):.1f}s ago — re-delegation required"
            print(_clr(YELLOW, f"[ArmorIQ]   ⚠  TOKEN EXPIRED  {reason}"))
            print(_clr(YELLOW, f"[ArmorIQ]      delegated_by={payload['issued_by']}  plan={payload['plan_id']}"))
            self._logger.log_invoke(
                agent_id=payload["agent_id"], tool_name=tool_name, args=args,
                status="EXPIRED", reason=reason,
                plan_id=payload.get("plan_id"), delegation_id=payload.get("delegation_id"),
                scope=payload.get("scope", []), ttl_remaining=ttl_rem,
            )
            raise PermissionError(f"ArmorIQ EXPIRED: {reason}")

        # ── 3. Scope check ────────────────────────────────────────────
        allowed_scope = payload.get("scope", [])
        ttl_remaining = payload["exp"] - time.time()

        if tool_name not in allowed_scope:
            reason = (
                f"SCOPE VIOLATION — '{tool_name}' not in delegated scope {allowed_scope}. "
                f"Delegated by: {payload['issued_by']}  plan: {payload['plan_id']}"
            )
            print(_clr(RED, f"[ArmorIQ]   ✗ SCOPE VIOLATION"))
            print(_clr(RED, f"[ArmorIQ]      tool          : {tool_name}"))
            print(_clr(RED, f"[ArmorIQ]      allowed scope : {allowed_scope}"))
            print(_clr(RED, f"[ArmorIQ]      delegated_by  : {payload['issued_by']}"))
            print(_clr(RED, f"[ArmorIQ]      plan_id       : {payload['plan_id']}"))
            self._logger.log_invoke(
                agent_id=payload["agent_id"], tool_name=tool_name, args=args,
                status="BLOCKED", reason=reason,
                plan_id=payload.get("plan_id"), delegation_id=payload.get("delegation_id"),
                scope=allowed_scope, ttl_remaining=ttl_remaining,
            )
            raise PermissionError(f"ArmorIQ SCOPE VIOLATION: '{tool_name}' not authorised")

        # ── 4. All checks pass — execute ──────────────────────────────
        print(_clr(GREEN, f"[ArmorIQ]   ✓ AUTHORIZED  scope={allowed_scope}  ttl_remaining={ttl_remaining:.0f}s"))

        try:
            result = execute_fn(tool_name, args)
            self._logger.log_invoke(
                agent_id=payload["agent_id"], tool_name=tool_name, args=args,
                status="ALLOWED", reason="Scope and TTL valid",
                plan_id=payload.get("plan_id"), delegation_id=payload.get("delegation_id"),
                scope=allowed_scope, ttl_remaining=ttl_remaining,
            )
            return result
        except PermissionError:
            raise
        except Exception as exc:
            self._logger.log_invoke(
                agent_id=payload["agent_id"], tool_name=tool_name, args=args,
                status="ERROR", reason=str(exc),
                plan_id=payload.get("plan_id"), delegation_id=payload.get("delegation_id"),
                scope=allowed_scope, ttl_remaining=ttl_remaining,
            )
            raise

    # ──────────────────────────────────────────────────────────────────
    # internal helpers
    # ──────────────────────────────────────────────────────────────────
    def _verify_token(self, token: str):
        """Decode and cryptographically verify a delegation token."""
        try:
            # Split into payload_b64 and sig
            dot_idx    = token.rfind(".")
            payload_b64 = token[:dot_idx]
            sig         = token[dot_idx + 1:]

            # Verify HMAC
            expected = hmac.new(self._secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                return None, "INVALID_SIGNATURE"

            # Decode payload (re-add padding)
            padding  = "=" * (4 - len(payload_b64) % 4)
            payload  = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))

            # Check expiry
            if time.time() > payload["exp"]:
                return payload, "EXPIRED"

            return payload, "VALID"
        except Exception:
            return None, "INVALID_SIGNATURE"
