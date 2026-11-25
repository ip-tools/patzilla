# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Unit and integration tests for email magic-link authentication and server-side sessions.

Uses a lightweight in-memory store for MongoEngine documents so the full test suite
runs deterministically without requiring a live MongoDB daemon.
"""
from __future__ import annotations

import datetime
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from patzilla.web.exceptions import HTTPFound
from patzilla.web.testing import DummyRequest

from patzilla.navigator.views import auth_magic_verify, login_page, logout_view
from patzilla.util.web.identity.config import AuthSettings
from patzilla.util.web.identity.magic_link import (
    ConsumedTokenError,
    ExpiredTokenError,
    InvalidEmailError,
    InvalidTokenError,
    MagicLinkDisabledError,
    RateLimitExceededError,
    SignupDisabledError,
    UserDisabledError,
    build_verify_url,
    consume_magic_link,
    inspect_magic_link_token,
    normalize_email,
    request_magic_link,
    sanitize_redirect_url,
    send_magic_link_email,
)
from patzilla.util.web.identity.service import (
    attach_user,
    identity_logout_handler,
    identity_magic_link_handler,
    identity_session_handler,
)
from patzilla.util.web.identity.session import (
    authenticate_session,
    create_session,
    generate_token,
    hash_token,
    revoke_all_user_sessions,
    revoke_session,
    set_session_cookie,
)
from patzilla.util.web.identity.store import (
    MagicLinkToken,
    User,
    UserHistory,
    UserSession,
    utcnow,
)


# ------------------------------------------
#   In-memory MongoEngine test harness
# ------------------------------------------
class _InMemoryQuerySet:
    """Minimal MongoEngine-compatible queryset over an in-memory list of documents."""

    def __init__(self, store: list, filters: dict, q_obj=None):
        self._store = store
        self._filters = filters
        self._q_obj = q_obj

    @staticmethod
    def _match_field(doc, key: str, expected) -> bool:
        if "__" in key:
            field, op = key.split("__", 1)
        else:
            field, op = key, "eq"

        value = getattr(doc, field, None)
        if op == "eq":
            return value == expected
        if op == "iexact":
            return isinstance(value, str) and isinstance(expected, str) and value.lower() == expected.lower()
        if op == "gt":
            return value is not None and value > expected
        if op == "gte":
            return value is not None and value >= expected
        if op == "lt":
            return value is not None and value < expected
        if op == "lte":
            return value is not None and value <= expected
        raise ValueError(f"Unsupported filter operator: {op}")

    def _match_q(self, doc, q_obj) -> bool:
        from mongoengine.queryset.visitor import Q, QCombination

        if isinstance(q_obj, Q):
            return all(self._match_field(doc, k, v) for k, v in q_obj.query.items())
        if isinstance(q_obj, QCombination):
            if q_obj.operation == QCombination.OR:
                return any(self._match_q(doc, child) for child in q_obj.children)
            return all(self._match_q(doc, child) for child in q_obj.children)
        return True

    def _matched(self) -> list:
        results = []
        for doc in self._store:
            if self._q_obj is not None and not self._match_q(doc, self._q_obj):
                continue
            if all(self._match_field(doc, k, v) for k, v in self._filters.items()):
                results.append(doc)
        return results

    def first(self):
        matches = self._matched()
        return matches[0] if matches else None

    def count(self) -> int:
        return len(self._matched())

    def modify(self, new: bool = False, **updates):
        doc = self.first()
        if doc is None:
            return None
        for key, value in updates.items():
            if key.startswith("set__"):
                setattr(doc, key.removeprefix("set__"), value)
        return doc

    def update(self, **updates) -> int:
        matches = self._matched()
        for doc in matches:
            for key, value in updates.items():
                if key.startswith("set__"):
                    setattr(doc, key.removeprefix("set__"), value)
        return len(matches)


class _InMemoryCollection:
    def __init__(self):
        self.docs: list = []

    def __call__(self, q_obj=None, **filters):
        return _InMemoryQuerySet(self.docs, filters, q_obj=q_obj)

    def save(self, doc):
        if doc not in self.docs:
            self.docs.append(doc)
        return doc


@pytest.fixture
def memory_db(monkeypatch):
    """
    Patch `User`, `MagicLinkToken`, `UserSession`, and `UserHistory` with
    in-memory collections for fast, isolated tests without a MongoDB server.
    """
    collections = {
        "users": _InMemoryCollection(),
        "tokens": _InMemoryCollection(),
        "sessions": _InMemoryCollection(),
        "history": _InMemoryCollection(),
    }

    mapping = [
        (User, collections["users"]),
        (MagicLinkToken, collections["tokens"]),
        (UserSession, collections["sessions"]),
        (UserHistory, collections["history"]),
    ]

    originals = []
    for cls, coll in mapping:
        orig_objects = cls.__dict__.get("objects")
        orig_save = cls.__dict__.get("save")
        originals.append((cls, orig_objects, orig_save))

        def _make_save(collection):
            def _save(self, *args, **kwargs):
                return collection.save(self)
            return _save

        setattr(cls, "objects", coll)
        setattr(cls, "save", _make_save(coll))

    try:
        yield SimpleNamespace(**collections)
    finally:
        for cls, orig_objects, orig_save in originals:
            if orig_objects is not None:
                setattr(cls, "objects", orig_objects)
            if orig_save is not None:
                setattr(cls, "save", orig_save)
            elif "save" in cls.__dict__:
                delattr(cls, "save")


# ------------------------------------------
#   Configuration tests
# ------------------------------------------
def test_auth_settings_defaults():
    settings = AuthSettings()
    assert settings.magic_link_enabled is True
    assert settings.magic_link_allow_signup is True
    assert settings.magic_link_ttl_seconds == 900
    assert settings.session_ttl_seconds == 14 * 24 * 60 * 60
    assert settings.session_renewal_threshold_seconds == 7 * 24 * 60 * 60
    assert settings.session_cookie_name == "patzilla_session"
    assert settings.session_cookie_samesite == "Lax"


def test_auth_settings_from_mapping():
    settings = AuthSettings.from_mapping({
        "magic_link_enabled": "false",
        "magic_link_allow_signup": "no",
        "magic_link_ttl_seconds": "600",
        "magic_link_default_tags": "beta, self-registered",
        "session_ttl_seconds": "3600",
        "session_cookie_secure": "true",
        "session_cookie_samesite": "InvalidValue",
        "public_base_url": "https://patzilla.example.org/",
    })
    assert settings.magic_link_enabled is False
    assert settings.magic_link_allow_signup is False
    assert settings.magic_link_ttl_seconds == 600
    assert settings.magic_link_default_tags == ("beta", "self-registered")
    assert settings.session_ttl_seconds == 3600
    assert settings.session_cookie_secure is True
    assert settings.session_cookie_samesite == "Lax"
    assert settings.public_base_url == "https://patzilla.example.org"


# ------------------------------------------
#   Validation & URL helper tests
# ------------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Alice@Example.ORG", "alice@example.org"),
        ("  bob+patents@sub.domain.de  ", "bob+patents@sub.domain.de"),
    ],
)
def test_normalize_email_valid(raw, expected):
    assert normalize_email(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [None, "", "   ", "not-an-email", "a@localhost", "a b@example.org", "@example.org", "a@" + "x" * 255 + ".com"],
)
def test_normalize_email_invalid(raw):
    with pytest.raises(InvalidEmailError):
        normalize_email(raw)


@pytest.mark.parametrize(
    "came_from, expected",
    [
        (None, "/"),
        ("", "/"),
        ("/navigator/?query=wind", "/navigator/?query=wind"),
        ("https://evil.example/phish", "/"),
        ("//evil.example/phish", "/"),
        ("/\\evil.example", "/"),
        ("javascript:alert(1)", "/"),
        ("/ok\r\nSet-Cookie: evil=1", "/"),
    ],
)
def test_sanitize_redirect_url(came_from, expected):
    assert sanitize_redirect_url(came_from) == expected


def test_token_generation_and_hashing():
    token1 = generate_token()
    token2 = generate_token()
    assert token1 != token2
    assert len(token1) >= 32
    digest = hash_token(token1)
    assert digest != token1
    assert len(digest) == 64
    assert hash_token(token1) == digest


# ------------------------------------------
#   Magic-link workflow tests
# ------------------------------------------
def test_request_and_consume_magic_link_provisions_new_user(memory_db):
    settings = AuthSettings()
    sent_emails = []

    def fake_send(**kwargs):
        sent_emails.append(kwargs)
        return True

    result = request_magic_link(
        email="New.User@Example.ORG",
        settings=settings,
        base_url="https://patzilla.example.org",
        came_from="/navigator/?query=solar",
        request_ip="203.0.113.10",
        send_mail_fn=fake_send,
    )

    # User is NOT created on request (spam protection).
    assert len(memory_db.users.docs) == 0
    assert len(memory_db.tokens.docs) == 1
    assert result.delivered is True
    assert len(sent_emails) == 1

    # Extract raw token from emailed URL and confirm DB stores only SHA-256 hash.
    raw_token = parse_qs(urlsplit(result.verify_url).query)["token"][0]
    stored_token = memory_db.tokens.docs[0]
    assert stored_token.token_hash == hash_token(raw_token)
    assert stored_token.token_hash != raw_token
    assert stored_token.consumed_at is None

    # GET inspection is read-only (protects against email link scanners).
    inspected1 = inspect_magic_link_token(raw_token)
    inspected2 = inspect_magic_link_token(raw_token)
    assert inspected1.email == "new.user@example.org"
    assert inspected2.consumed_at is None

    # POST consumption provisions a verified User and marks token consumed.
    user, redirect_url = consume_magic_link(raw_token, settings)
    assert redirect_url == "/navigator/?query=solar"
    assert user.email == "new.user@example.org"
    assert user.username == "new.user@example.org"
    assert user.email_verified is True
    assert user.email_verified_at is not None
    assert user.last_login_at is not None
    assert user.is_active is True
    assert "self-registered" in user.tags
    assert len(memory_db.users.docs) == 1
    assert [h.action for h in memory_db.history.docs] == ["user-created", "magic-link-login"]

    # Replay must fail (single-use).
    with pytest.raises(ConsumedTokenError):
        consume_magic_link(raw_token, settings)


def test_consume_magic_link_existing_legacy_user(memory_db):
    settings = AuthSettings()
    legacy_user = User(
        username="existing@example.org",
        fullname="Existing User",
        tags=["trial"],
        modules=["analytics"],
    )
    legacy_user.save()

    result = request_magic_link(
        email="existing@example.org",
        settings=settings,
        base_url="http://localhost:6543",
        send_mail_fn=lambda **kwargs: True,
    )
    raw_token = parse_qs(urlsplit(result.verify_url).query)["token"][0]

    user, redirect_url = consume_magic_link(raw_token, settings)
    assert user.userid == legacy_user.userid
    assert user.email == "existing@example.org"
    assert user.email_verified is True
    assert redirect_url == "/"
    assert len(memory_db.users.docs) == 1


def test_consume_magic_link_expired_and_invalid_tokens(memory_db):
    settings = AuthSettings()

    with pytest.raises(InvalidTokenError):
        consume_magic_link("nonexistent-token", settings)

    raw_token = generate_token()
    MagicLinkToken(
        token_hash=hash_token(raw_token),
        email="expired@example.org",
        expires_at=utcnow() - datetime.timedelta(seconds=5),
    ).save()

    with pytest.raises(ExpiredTokenError):
        inspect_magic_link_token(raw_token)

    with pytest.raises(ExpiredTokenError):
        consume_magic_link(raw_token, settings)


def test_consume_magic_link_blocks_disabled_user(memory_db):
    settings = AuthSettings()
    User(
        username="locked@example.org",
        email="locked@example.org",
        tags=["login:disabled"],
    ).save()

    result = request_magic_link(
        email="locked@example.org",
        settings=settings,
        base_url="http://localhost:6543",
        send_mail_fn=lambda **kwargs: True,
    )
    raw_token = parse_qs(urlsplit(result.verify_url).query)["token"][0]

    with pytest.raises(UserDisabledError):
        consume_magic_link(raw_token, settings)


def test_consume_magic_link_respects_allow_signup_false(memory_db):
    settings = AuthSettings(magic_link_allow_signup=False)
    result = request_magic_link(
        email="stranger@example.org",
        settings=settings,
        base_url="http://localhost:6543",
        send_mail_fn=lambda **kwargs: True,
    )
    raw_token = parse_qs(urlsplit(result.verify_url).query)["token"][0]

    with pytest.raises(SignupDisabledError):
        consume_magic_link(raw_token, settings)


def test_request_magic_link_rate_limit(memory_db):
    settings = AuthSettings(magic_link_rate_limit_count=2, magic_link_rate_limit_window_seconds=900)

    for _ in range(2):
        request_magic_link(
            email="burst@example.org",
            settings=settings,
            base_url="http://localhost:6543",
            send_mail_fn=lambda **kwargs: True,
        )

    with pytest.raises(RateLimitExceededError):
        request_magic_link(
            email="burst@example.org",
            settings=settings,
            base_url="http://localhost:6543",
            send_mail_fn=lambda **kwargs: True,
        )


def test_request_magic_link_when_disabled(memory_db):
    settings = AuthSettings(magic_link_enabled=False)
    with pytest.raises(MagicLinkDisabledError):
        request_magic_link(
            email="user@example.org",
            settings=settings,
            base_url="http://localhost:6543",
            send_mail_fn=lambda **kwargs: True,
        )


def test_send_magic_link_email_logs_in_dev_when_smtp_unconfigured(caplog):
    settings = AuthSettings(log_magic_link_in_dev=True)
    verify_url = build_verify_url("dev-token", "http://localhost:6543")
    with caplog.at_level("WARNING"):
        delivered = send_magic_link_email(
            email="dev@example.org",
            verify_url=verify_url,
            ttl_minutes=15,
            request=None,
            settings=settings,
        )
    assert delivered is False
    assert verify_url in caplog.text


# ------------------------------------------
#   Session & cookie tests
# ------------------------------------------
def test_session_lifecycle_renewal_and_revocation(memory_db):
    settings = AuthSettings(
        session_ttl_seconds=14 * 24 * 60 * 60,
        session_renewal_threshold_seconds=7 * 24 * 60 * 60,
    )
    user = User(username="alice@example.org", email="alice@example.org", email_verified=True)
    user.save()

    raw_token, session = create_session(user, settings, ip_address="198.51.100.5", user_agent="pytest")
    assert session.session_hash == hash_token(raw_token)
    assert session.session_hash != raw_token

    # Fresh session: valid, no renewal needed.
    auth_user, auth_session, renewed = authenticate_session(raw_token, settings)
    assert auth_user is not None and auth_user.userid == user.userid
    assert auth_session is not None
    assert renewed is False

    # Simulate session nearing expiry (< 7 days remaining): triggers sliding renewal.
    session.expires_at = utcnow() + datetime.timedelta(days=2)
    auth_user, auth_session, renewed = authenticate_session(raw_token, settings)
    assert auth_user is not None
    assert renewed is True
    assert (session.expires_at - utcnow()).days >= 13

    # Revoke single session.
    assert revoke_session(raw_token) is True
    assert authenticate_session(raw_token, settings) == (None, None, False)

    # Revoke all sessions for user.
    t1, _ = create_session(user, settings)
    t2, _ = create_session(user, settings)
    assert revoke_all_user_sessions(user.userid) == 2
    assert authenticate_session(t1, settings) == (None, None, False)
    assert authenticate_session(t2, settings) == (None, None, False)


# ------------------------------------------
#   Pyramid request/view/service integration tests
# ------------------------------------------
class _DummyErrors:
    def __init__(self):
        self.status = None
        self.items: list[tuple[str, str, str]] = []

    def add(self, loc: str, name: str, desc: str) -> None:
        self.items.append((loc, name, desc))


def _make_request(**kwargs) -> Any:
    request: Any = DummyRequest(**kwargs)
    request.errors = _DummyErrors()
    request.registry.application_settings = {
        "ip_navigator": {"development_mode": True},
        "auth": {
            "magic_link_enabled": True,
            "magic_link_allow_signup": True,
            "log_magic_link_in_dev": True,
        },
        "smtp": {"hostname": "{smtp_hostname}"},
    }
    return request


def test_attach_user_cookie_and_nginx_coexistence(memory_db):
    settings = AuthSettings()
    cookie_user = User(username="cookie@example.org", email="cookie@example.org", email_verified=True)
    cookie_user.save()
    nginx_user = User(username="nginx@example.org", email="nginx@example.org")
    nginx_user.save()

    raw_session, _ = create_session(cookie_user, settings)

    # 1. Native Pyramid session cookie takes precedence.
    req1 = _make_request(cookies={settings.session_cookie_name: raw_session})
    attach_user(SimpleNamespace(request=req1))
    assert req1.user.userid == cookie_user.userid
    assert req1.auth_session is not None

    # 2. Fallback to nginx-auth X-User-Id header when no session cookie is set.
    req2 = _make_request(headers={"X-User-Id": nginx_user.userid})
    attach_user(SimpleNamespace(request=req2))
    assert req2.user.userid == nginx_user.userid
    assert req2.auth_session is None

    # 3. Anonymous placeholder when neither is present.
    req3 = _make_request()
    attach_user(SimpleNamespace(request=req3))
    assert req3.user.is_authenticated is False


def test_identity_api_and_verify_views_end_to_end(memory_db):
    # 1. Request magic link via API (neutral response).
    req_ml = _make_request(
        content_type="application/json",
        json_body={"email": "founder@example.org", "came_from": "/navigator/"},
    )
    resp_ml = identity_magic_link_handler(req_ml)
    assert resp_ml["status"] == "ok"
    assert len(memory_db.tokens.docs) == 1

    # Capture raw token by creating a controlled link for verify view test.
    settings = AuthSettings()
    captured = {}
    res = request_magic_link(
        email="founder2@example.org",
        settings=settings,
        base_url="http://localhost:6543",
        came_from="/navigator/?query=battery",
        send_mail_fn=lambda **kw: captured.update(kw) or True,
    )
    raw_token = parse_qs(urlsplit(res.verify_url).query)["token"][0]

    # 2. GET /auth/magic/verify renders confirmation without consuming token.
    req_get = _make_request(params={"token": raw_token})
    req_get.method = "GET"
    ctx_get = auth_magic_verify(req_get)
    assert ctx_get["valid"] is True
    assert ctx_get["email"] == "founder2@example.org"

    # 3. POST /auth/magic/verify consumes token, sets HttpOnly cookie, redirects.
    req_post = _make_request(post={"token": raw_token})
    req_post.method = "POST"
    resp_post = auth_magic_verify(req_post)
    assert isinstance(resp_post, HTTPFound)
    assert resp_post.location == "/navigator/?query=battery"
    set_cookie_header = resp_post.headers.get("Set-Cookie", "")
    assert "patzilla_session=" in set_cookie_header
    assert "HttpOnly" in set_cookie_header

    # Extract session cookie value and verify /api/identity/session.
    cookie_val = set_cookie_header.split("patzilla_session=", 1)[1].split(";", 1)[0]
    req_sess = _make_request(cookies={"patzilla_session": cookie_val})
    attach_user(SimpleNamespace(request=req_sess))
    sess_payload = identity_session_handler(req_sess)
    assert sess_payload["authenticated"] is True
    assert sess_payload["user"]["email"] == "founder2@example.org"
    assert "password" not in sess_payload["user"]
    assert "billing" not in sess_payload["user"]

    # 4. Second POST with same token returns error context (single-use).
    req_replay = _make_request(post={"token": raw_token})
    req_replay.method = "POST"
    ctx_replay = auth_magic_verify(req_replay)
    assert ctx_replay["valid"] is False
    assert ctx_replay["error_code"] == "consumed-token"

    # 5. Logout revokes session.
    req_logout = _make_request(cookies={"patzilla_session": cookie_val})
    attach_user(SimpleNamespace(request=req_logout))
    logout_payload = identity_logout_handler(req_logout)
    assert logout_payload["status"] == "ok"
    assert authenticate_session(cookie_val, settings) == (None, None, False)

    # 6. Browser /logout view redirects to /login and clears cookie.
    req_logout_view = _make_request()
    resp_logout_view = logout_view(req_logout_view)
    assert isinstance(resp_logout_view, HTTPFound)
    assert resp_logout_view.location == "/login"

    # 7. Login page exposes magic_link_enabled and sanitizes came_from.
    req_login = _make_request(params={"came_from": "https://evil.example"})
    ctx_login = login_page(req_login)
    assert ctx_login["magic_link_enabled"] is True
    assert ctx_login["came_from"] == ""
