# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Server-side session management and HttpOnly cookie helpers.
"""
from __future__ import annotations

import datetime
import hashlib
import logging
import secrets
from typing import Any, Optional

from patzilla.util.web.identity.config import AuthSettings
from patzilla.util.web.identity.store import User, UserSession, ensure_utc_naive, utcnow

log = logging.getLogger(__name__)


# ------------------------------------------
#   Token helpers
# ------------------------------------------
def generate_token(nbytes: int = 32) -> str:
    """
    Generate a cryptographically secure URL-safe random token (default: 256-bit entropy).
    """
    return secrets.token_urlsafe(nbytes)


def hash_token(raw_token: str) -> str:
    """
    Compute the SHA-256 hex digest of a raw token.
    Only hashed tokens are ever stored in MongoDB.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# ------------------------------------------
#   Session lifecycle
# ------------------------------------------
def create_session(
    user: User,
    settings: AuthSettings,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[str, UserSession]:
    """
    Create and persist a new server-side session for `user`.
    Returns `(raw_session_token, session_document)`.
    """
    now = utcnow()
    raw_token = generate_token()
    session = UserSession(
        session_hash=hash_token(raw_token),
        userid=user.userid,
        created_at=now,
        last_seen_at=now,
        expires_at=now + datetime.timedelta(seconds=settings.session_ttl_seconds),
        ip_address=ip_address,
        user_agent=user_agent[:512] if user_agent else None,
    )
    session.save()
    return raw_token, session


def get_active_session(raw_token: str) -> Optional[UserSession]:
    """
    Look up an active (non-revoked, non-expired) `UserSession` by raw cookie token.
    """
    if not raw_token:
        return None

    now = utcnow()
    session = UserSession.objects(  # ty: ignore[unresolved-attribute]
        session_hash=hash_token(raw_token),
        revoked_at=None,
        expires_at__gt=now,
    ).first()
    return session


def authenticate_session(
    raw_token: str,
    settings: AuthSettings,
) -> tuple[Optional[User], Optional[UserSession], bool]:
    """
    Validate a raw session token, load the associated active `User`, and perform
    sliding expiration renewal when remaining lifetime drops below the threshold.

    Returns `(user, session, renewed)`.
    """
    session = get_active_session(raw_token)
    if session is None:
        return None, None, False

    user = User.objects(userid=session.userid).first()  # ty: ignore[unresolved-attribute]
    if user is None or not user.is_active:
        return None, None, False

    now = utcnow()
    remaining = ensure_utc_naive(session.expires_at) - now
    renewed = False

    if (
        settings.session_renewal_threshold_seconds > 0
        and remaining.total_seconds() <= settings.session_renewal_threshold_seconds
    ):
        session.expires_at = now + datetime.timedelta(seconds=settings.session_ttl_seconds)
        session.last_seen_at = now
        session.save()
        renewed = True
    elif session.last_seen_at is None or (now - ensure_utc_naive(session.last_seen_at)).total_seconds() >= 300:
        # Throttle `last_seen_at` writes to avoid a DB write on every static/API request.
        session.last_seen_at = now
        session.save()

    return user, session, renewed


def revoke_session(raw_token: str) -> bool:
    """
    Revoke a single session by its raw cookie token.
    Returns True if an active session was revoked.
    """
    if not raw_token:
        return False

    now = utcnow()
    updated = UserSession.objects(  # ty: ignore[unresolved-attribute]
        session_hash=hash_token(raw_token),
        revoked_at=None,
    ).update(set__revoked_at=now)
    return bool(updated)


def revoke_all_user_sessions(userid: str) -> int:
    """
    Revoke all active sessions belonging to `userid` (e.g. on account lock or logout-all).
    Returns the number of revoked sessions.
    """
    if not userid:
        return 0

    now = utcnow()
    return int(
        UserSession.objects(  # ty: ignore[unresolved-attribute]
            userid=userid,
            revoked_at=None,
        ).update(set__revoked_at=now)
    )


# ------------------------------------------
#   HTTP cookie helpers
# ------------------------------------------
def _should_set_secure_cookie(settings: AuthSettings, request: Any = None) -> bool:
    if settings.session_cookie_secure:
        return True
    if request is not None:
        scheme = getattr(request, "scheme", None)
        forwarded_proto = getattr(request, "headers", {}).get("X-Forwarded-Proto", "")
        if scheme == "https" or forwarded_proto.lower() == "https":
            return True
    return False


def set_session_cookie(
    response: Any,
    raw_token: str,
    settings: AuthSettings,
    request: Any = None,
) -> None:
    """
    Attach a hardened HttpOnly session cookie to a Pyramid response.
    """
    response.set_cookie(
        name=settings.session_cookie_name,
        value=raw_token,
        max_age=settings.session_ttl_seconds,
        path="/",
        httponly=True,
        secure=_should_set_secure_cookie(settings, request=request),
        samesite=settings.session_cookie_samesite,
    )


def clear_session_cookie(
    response: Any,
    settings: AuthSettings,
    request: Any = None,
) -> None:
    """
    Delete the session cookie from a Pyramid response.
    """
    response.delete_cookie(
        name=settings.session_cookie_name,
        path="/",
    )
