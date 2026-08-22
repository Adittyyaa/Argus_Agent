"""
mock_armoriq — Local mock of the ArmorIQ SDK.

Implements the same interface as the real ArmorIQ SDK:
  - capture_plan()   : declare intent before delegation
  - delegate()       : issue a scoped, HMAC-signed token
  - invoke()         : governed tool call (scope + TTL enforcement)

Tokens are HMAC-SHA256 signed with a shared secret so they are
cryptographically verifiable across separate processes.
"""
from .client import ArmorIQClient

__all__ = ["ArmorIQClient"]
