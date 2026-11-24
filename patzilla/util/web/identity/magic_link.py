# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Passwordless email magic-link authentication workflow.

Security properties:
- Tokens use 256-bit cryptographic entropy (`secrets.token_urlsafe(32)`).
- Only SHA-256 hashes are persisted in MongoDB.
- Tokens are short-lived (default: 15 minutes) and single-use via atomic MongoDB update.
- Users are provisioned in MongoDB only upon successful link verification, never on request.
- Per-email and per-IP rate limits protect against email flooding.
- Redirect targets (`came_from`) are strictly validated against open redirects.
"""
from __future__ import annotations

import datetime
import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import quote, urlsplit

from mongoengine.errors import NotUniqueError
from mongoengine.queryset.visitor import Q

from patzilla.util.email.message import EmailMessage
from patzilla.util.web.identity.config import AuthSettings
from patzilla.util.web.identity.session import generate_token, hash_token
from patzilla.util.web.identity.store import MagicLinkToken, User, UserHistory, ensure_utc_naive, utcnow

log = logging.getLogger(__name__)

# Practical, strict email validation regex (rejects whitespace, control chars, missing TLD).
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)
_MAX_EMAIL_LENGTH = 254


# ------------------------------------------
#   Exceptions
# ------------------------------------------
class MagicLinkError(Exception):
    """Base exception for magic-link authentication failures."""

    code: str = "magic-link-error"

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class InvalidEmailError(MagicLinkError):
    code = "invalid-email"


class MagicLinkDisabledError(MagicLinkError):
    code = "magic-link-disabled"


class RateLimitExceededError(MagicLinkError):
    code = "rate-limit-exceeded"


class InvalidTokenError(MagicLinkError):
    code = "invalid-token"


class ExpiredTokenError(MagicLinkError):
    code = "expired-token"


class ConsumedTokenError(MagicLinkError):
    code = "consumed-token"


class SignupDisabledError(MagicLinkError):
    code = "signup-disabled"


class UserDisabledError(MagicLinkError):
    code = "login-disabled"


# ------------------------------------------
#   Data structures
# ------------------------------------------
@dataclass(frozen=True)
class MagicLinkRequestResult:
    email: str
    verify_url: str
    expires_at: datetime.datetime
    delivered: bool


# ------------------------------------------
#   Validation & URL helpers
# ------------------------------------------
def normalize_email(email: Optional[str]) -> str:
    """
    Normalize and validate an email address.
    Raises `InvalidEmailError` if the address is missing or malformed.
    """
    if not isinstance(email, str):
        raise InvalidEmailError("Please provide a valid email address.")

    cleaned = email.strip().lower()
    if not cleaned or len(cleaned) > _MAX_EMAIL_LENGTH or not _EMAIL_RE.match(cleaned):
        raise InvalidEmailError("Please provide a valid email address.")

    return cleaned


def sanitize_redirect_url(came_from: Optional[str], default: str = "/") -> str:
    """
    Ensure `came_from` is a safe relative application path (prevents open redirects).
    """
    if not came_from or not isinstance(came_from, str):
        return default

    candidate = came_from.strip()
    if not candidate or any(ch in candidate for ch in ("\r", "\n", "\x00")):
        return default

    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc:
        return default

    if not candidate.startswith("/") or candidate.startswith("//") or candidate.startswith("/\\"):
        return default

    return candidate


def build_verify_url(raw_token: str, base_url: str) -> str:
    """
    Build the full verification URL sent in the magic-link email.
    """
    base = base_url.rstrip("/")
    return f"{base}/auth/magic/verify?token={quote(raw_token, safe='')}"


def resolve_base_url(request: Any, settings: AuthSettings) -> str:
    """
    Determine the public base URL used to construct magic links.
    Prefers explicit `[auth] public_base_url` over `request.application_url`.
    """
    if settings.public_base_url:
        return settings.public_base_url
    return str(getattr(request, "application_url", "http://localhost:6543")).rstrip("/")


def get_client_ip(request: Any) -> Optional[str]:
    """
    Extract client IP address from a Pyramid request (respecting X-Forwarded-For).
    """
    if request is None:
        return None
    forwarded = getattr(request, "headers", {}).get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return getattr(request, "client_addr", None) or getattr(request, "remote_addr", None)


# ------------------------------------------
#   Rate limiting
# ------------------------------------------
def is_rate_limited(
    email: str,
    settings: AuthSettings,
    request_ip: Optional[str] = None,
) -> bool:
    """
    Check whether magic-link requests for `email` (or `request_ip`) exceed configured limits.
    """
    window_start = utcnow() - datetime.timedelta(seconds=settings.magic_link_rate_limit_window_seconds)

    email_count = MagicLinkToken.objects(  # ty: ignore[unresolved-attribute]
        email=email,
        created_at__gte=window_start,
    ).count()
    if email_count >= settings.magic_link_rate_limit_count:
        return True

    if request_ip:
        # Allow a higher threshold per IP to avoid blocking shared office NATs.
        ip_limit = settings.magic_link_rate_limit_count * 3
        ip_count = MagicLinkToken.objects(  # ty: ignore[unresolved-attribute]
            request_ip=request_ip,
            created_at__gte=window_start,
        ).count()
        if ip_count >= ip_limit:
            return True

    return False


# ------------------------------------------
#   Email delivery
# ------------------------------------------
def _is_smtp_configured(smtp_settings: dict[str, Any]) -> bool:
    hostname = str(smtp_settings.get("hostname", "")).strip()
    if not hostname or hostname.startswith("{"):
        return False
    return True


def _is_development_mode(request: Any) -> bool:
    try:
        return bool(request.registry.application_settings.get("ip_navigator", {}).get("development_mode", False))
    except Exception:
        return False


def send_magic_link_email(
    email: str,
    verify_url: str,
    ttl_minutes: int,
    request: Any = None,
    settings: Optional[AuthSettings] = None,
) -> bool:
    """
    Send a magic-link sign-in email using PatZilla's `EmailMessage` subsystem.
    In development mode with unconfigured SMTP, logs the link instead of raising.
    """
    auth_settings = settings or AuthSettings()
    smtp_settings: dict[str, Any] = {}
    email_settings: dict[str, Any] = {"addressbook": {}, "content": {}}
    productname = "PatZilla"

    if request is not None:
        app_settings = getattr(request.registry, "application_settings", {}) or {}
        smtp_settings = dict(app_settings.get("smtp", {}) or {})
        runtime_settings = getattr(request, "runtime_settings", None)
        if runtime_settings is not None:
            vendor = getattr(runtime_settings, "vendor", None)
            if vendor is not None:
                productname = vendor.get("productname", productname)
                vendor_email = vendor.get("email") or {}
                email_settings["addressbook"] = dict(vendor_email.get("addressbook", {}) or {})
                email_settings["content"] = dict(vendor_email.get("content", {}) or {})

    if not _is_smtp_configured(smtp_settings):
        if auth_settings.log_magic_link_in_dev and (request is None or _is_development_mode(request)):
            log.warning(
                "SMTP is not configured; logging magic link for %s (valid %d min): %s",
                email,
                ttl_minutes,
                verify_url,
            )
            return False
        raise MagicLinkError("Email delivery is not configured.", code="email-not-configured")

    email_settings["content"]["body"] = (
        "Hello,\n\n"
        f"Use the link below to sign in to {productname}:\n\n"
        "{{ message }}\n\n"
        f"This link is valid for {ttl_minutes} minutes and can only be used once.\n"
        "If you did not request this sign-in link, you can safely ignore this email."
    )

    msg = EmailMessage(smtp_settings, email_settings)
    msg.add_recipient(email)
    msg.send(
        subject=f"Sign in to {productname}",
        message=verify_url,
    )
    return True


# ------------------------------------------
#   Core workflow
# ------------------------------------------
def request_magic_link(
    email: Optional[str],
    settings: AuthSettings,
    base_url: str,
    came_from: Optional[str] = None,
    request_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    request: Any = None,
    send_mail_fn: Optional[Callable[..., bool]] = None,
) -> MagicLinkRequestResult:
    """
    Create a single-use magic-link token and dispatch it via email.
    Does not create a `User` document yet to prevent unverified account spam.
    """
    if not settings.magic_link_enabled:
        raise MagicLinkDisabledError("Magic-link authentication is currently disabled.")

    normalized_email = normalize_email(email)

    if is_rate_limited(normalized_email, settings=settings, request_ip=request_ip):
        raise RateLimitExceededError(
            "Too many sign-in links requested. Please wait a few minutes and try again."
        )

    now = utcnow()
    expires_at = now + datetime.timedelta(seconds=settings.magic_link_ttl_seconds)
    raw_token = generate_token()
    safe_came_from = sanitize_redirect_url(came_from)

    token_doc = MagicLinkToken(
        token_hash=hash_token(raw_token),
        email=normalized_email,
        purpose="login",
        came_from=safe_came_from,
        created_at=now,
        expires_at=expires_at,
        request_ip=request_ip,
        user_agent=user_agent[:512] if user_agent else None,
    )
    token_doc.save()

    verify_url = build_verify_url(raw_token, base_url=base_url)
    ttl_minutes = max(1, round(settings.magic_link_ttl_seconds / 60))

    sender = send_mail_fn or send_magic_link_email
    delivered = sender(
        email=normalized_email,
        verify_url=verify_url,
        ttl_minutes=ttl_minutes,
        request=request,
        settings=settings,
    )

    existing_user = find_user_by_email(normalized_email)
    if existing_user is not None:
        UserHistory(userid=existing_user.userid, action="magic-link-requested").save()

    return MagicLinkRequestResult(
        email=normalized_email,
        verify_url=verify_url,
        expires_at=expires_at,
        delivered=bool(delivered),
    )


def find_user_by_email(email: str) -> Optional[User]:
    """
    Find an existing user by normalized `email` or legacy `username`.
    """
    return User.objects(  # ty: ignore[unresolved-attribute]
        Q(email__iexact=email) | Q(username__iexact=email)
    ).first()


def inspect_magic_link_token(raw_token: Optional[str]) -> MagicLinkToken:
    """
    Read-only validation of a magic-link token for the GET confirmation page.
    Does NOT consume the token (protects against email link scanners / prefetchers).
    """
    if not raw_token or not isinstance(raw_token, str):
        raise InvalidTokenError("Sign-in link is missing or invalid.")

    token_doc = MagicLinkToken.objects(  # ty: ignore[unresolved-attribute]
        token_hash=hash_token(raw_token.strip())
    ).first()

    if token_doc is None:
        raise InvalidTokenError("This sign-in link is invalid.")

    if token_doc.consumed_at is not None:
        raise ConsumedTokenError("This sign-in link has already been used. Please request a new one.")

    if ensure_utc_naive(token_doc.expires_at) <= utcnow():
        raise ExpiredTokenError("This sign-in link has expired. Please request a new one.")

    return token_doc


def consume_magic_link(
    raw_token: Optional[str],
    settings: AuthSettings,
) -> tuple[User, str]:
    """
    Atomically consume a magic-link token and return `(user, redirect_url)`.
    Creates a verified `User` document if none exists yet and self-signup is allowed.
    """
    if not settings.magic_link_enabled:
        raise MagicLinkDisabledError("Magic-link authentication is currently disabled.")

    if not raw_token or not isinstance(raw_token, str):
        raise InvalidTokenError("Sign-in link is missing or invalid.")

    token_hash = hash_token(raw_token.strip())
    now = utcnow()

    # Atomic single-use consumption prevents race conditions and replay attacks.
    token_doc = MagicLinkToken.objects(  # ty: ignore[unresolved-attribute]
        token_hash=token_hash,
        consumed_at=None,
        expires_at__gt=now,
    ).modify(set__consumed_at=now, new=True)

    if token_doc is None:
        existing = MagicLinkToken.objects(token_hash=token_hash).first()  # ty: ignore[unresolved-attribute]
        if existing is None:
            raise InvalidTokenError("This sign-in link is invalid.")
        if existing.consumed_at is not None:
            raise ConsumedTokenError("This sign-in link has already been used. Please request a new one.")
        raise ExpiredTokenError("This sign-in link has expired. Please request a new one.")

    email = normalize_email(token_doc.email)
    user = find_user_by_email(email)

    if user is not None:
        if not user.is_active:
            raise UserDisabledError("Your account is disabled. Please contact support.")

        user.email = email
        user.email_verified = True
        if not user.email_verified_at:
            user.email_verified_at = now
        user.last_login_at = now
        user.modified = now
        user.save()
    else:
        if not settings.magic_link_allow_signup:
            raise SignupDisabledError("No account found for this email address.")

        user = User(
            username=email,
            email=email,
            fullname="",
            email_verified=True,
            email_verified_at=now,
            last_login_at=now,
            status="active",
            tags=list(settings.magic_link_default_tags),
            modules=list(settings.magic_link_default_modules),
        )
        try:
            user.save()
        except NotUniqueError:
            # Handle rare concurrent creation for the same email gracefully.
            user = find_user_by_email(email)
            if user is None:
                raise
        else:
            UserHistory(userid=user.userid, action="user-created").save()

    UserHistory(userid=user.userid, action="magic-link-login").save()
    redirect_url = sanitize_redirect_url(token_doc.came_from)
    return user, redirect_url
