import logging
import uuid
from typing import Any

import pytest
from django.conf import settings

from modules.identity.models import Consent, IdempotencyRecord, User

from .conftest import (
    CSRF,
    LOGIN,
    LOGOUT,
    ME,
    PASSWORD,
    SIGNUP,
    VERIFY,
    Api,
    forget_mail_limits,
    queued_code,
    signup_body,
    too_young,
)

pytestmark = pytest.mark.django_db


def problem(response: Any) -> dict[str, Any]:
    assert response["Content-Type"].startswith("application/problem+json")
    return dict(response.json())


@pytest.mark.success("GET /api/v1/auth/csrf")
def test_csrf_returns_a_token(api: Api) -> None:
    response = api.get(CSRF)
    assert response.status_code == 200
    assert response.json()["csrf_token"]
    assert response["Cache-Control"] == "no-store"


@pytest.mark.not_found("GET /api/v1/auth/csrf")
def test_csrf_has_no_write_method(api: Api) -> None:
    assert api.post(CSRF).status_code == 405


@pytest.mark.refused("GET /api/v1/auth/csrf")
def test_csrf_from_a_foreign_origin_gets_no_cors_headers(api: Api) -> None:
    response = api.get(CSRF, HTTP_ORIGIN="https://evil.example")
    assert "Access-Control-Allow-Origin" not in response
    assert "Access-Control-Allow-Credentials" not in response


@pytest.mark.success("POST /api/v1/auth/signup")
def test_signup_creates_account_session_and_profile(api: Api) -> None:
    response = api.sign_up(email="Ada@Example.com", interface_language="fr")
    assert response.status_code == 201
    body = response.json()
    assert body["interface_language"] == "fr"
    assert body["csrf_token"]
    user = User.objects.get(email="ada@example.com")
    assert str(user.id) == body["learner_id"]
    assert user.password.startswith("argon2$")
    consent = Consent.objects.get(user=user)
    assert (consent.kind, consent.granted, consent.source) == (
        "processing",
        True,
        "signup",
    )
    assert not body["email_verified"]
    assert api.get(ME).status_code == 401
    code = {"email": "ada@example.com", "code": queued_code()}
    assert api.post(VERIFY, code).status_code == 200
    me = api.get(ME)
    assert me.status_code == 200
    assert me.json()["interface_language"] == "fr"
    assert me.json()["email_verified"]


@pytest.mark.not_found("POST /api/v1/auth/signup")
def test_signup_with_a_malformed_body_is_a_validation_problem(api: Api) -> None:
    response = api.post(SIGNUP, {"email": "not-an-email", "password": "x"})
    assert response.status_code == 422
    body = problem(response)
    assert body["code"] == "validation_error"
    assert "not-an-email" not in response.content.decode()
    assert User.objects.count() == 0


@pytest.mark.refused("POST /api/v1/auth/signup")
def test_signup_under_16_is_refused_in_the_learners_language(api: Api) -> None:
    response = api.sign_up(date_of_birth=too_young(), interface_language="fr")
    assert response.status_code == 422
    assert problem(response)["code"] == "age_below_minimum"
    assert response["Content-Language"] == "fr"
    assert User.objects.count() == 0
    assert Consent.objects.count() == 0


def test_signup_without_consent_stores_nothing(api: Api) -> None:
    response = api.sign_up(processing_consent=False)
    assert response.status_code == 422
    assert problem(response)["code"] == "consent_required"
    assert User.objects.count() == 0
    assert Consent.objects.count() == 0


def test_signup_without_consent_field_is_refused(api: Api) -> None:
    body = signup_body()
    del body["processing_consent"]
    response = api.post(SIGNUP, body)
    assert response.status_code == 422
    assert User.objects.count() == 0


def test_signup_rejects_a_weak_password(api: Api) -> None:
    response = api.sign_up(password="password1234")
    assert response.status_code == 422
    assert problem(response)["code"] == "weak_password"
    assert User.objects.count() == 0


def test_duplicate_email_in_any_case_looks_like_a_new_signup(learner: Api) -> None:
    other = Api()
    response = other.sign_up(email="ADA@example.COM", password="Another-Pass-9921")
    assert response.status_code == 201
    assert set(response.json()) == set(learner.get(ME).json()) | {"csrf_token"}
    assert User.objects.count() == 1
    assert other.get(ME).status_code == 401
    assert User.objects.get().check_password(PASSWORD)


def test_duplicate_and_new_signups_set_the_same_cookies(api: Api, learner: Api) -> None:
    fresh = Api().sign_up(email="grace@example.com")
    forget_mail_limits()
    duplicate = Api().sign_up(email="ada@example.com", password="Another-Pass-9921")
    assert fresh.cookies.keys() == duplicate.cookies.keys()


def test_idempotent_replay_stores_no_name_or_email(api: Api) -> None:
    key = str(uuid.uuid4())
    api.post(SIGNUP, signup_body(), HTTP_IDEMPOTENCY_KEY=key)
    stored = IdempotencyRecord.objects.get().response
    assert set(stored) == {"learner_id"}


def test_idempotent_replay_of_a_duplicate_email_matches_the_first_answer(
    learner: Api,
) -> None:
    key = str(uuid.uuid4())
    body = signup_body(password="Another-Pass-9921", display_name="Eve")
    first = Api().post(SIGNUP, body, HTTP_IDEMPOTENCY_KEY=key)
    second = Api().post(SIGNUP, body, HTTP_IDEMPOTENCY_KEY=key)
    assert first.json()["learner_id"] == second.json()["learner_id"]
    assert second.json()["display_name"] == "Eve"


def test_write_without_csrf_token_is_refused(api: Api) -> None:
    response = api.post(SIGNUP, signup_body(), csrf=False)
    assert response.status_code == 403
    assert problem(response)["code"] == "csrf_failed"
    assert User.objects.count() == 0


def test_write_from_a_foreign_origin_is_refused(api: Api) -> None:
    api.fetch_token()
    response = api.post(SIGNUP, signup_body(), HTTP_ORIGIN="https://evil.example")
    assert response.status_code == 403
    assert User.objects.count() == 0


def test_idempotent_replay_returns_the_same_account(api: Api) -> None:
    key = str(uuid.uuid4())
    first = api.post(SIGNUP, signup_body(), HTTP_IDEMPOTENCY_KEY=key)
    second = api.post(SIGNUP, signup_body(), HTTP_IDEMPOTENCY_KEY=key)
    assert (first.status_code, second.status_code) == (201, 201)
    assert first.json()["learner_id"] == second.json()["learner_id"]
    assert User.objects.count() == 1
    assert Consent.objects.count() == 1


def test_idempotency_key_reused_with_another_body_conflicts(api: Api) -> None:
    key = str(uuid.uuid4())
    api.post(SIGNUP, signup_body(), HTTP_IDEMPOTENCY_KEY=key)
    response = api.post(
        SIGNUP, signup_body(email="grace@example.com"), HTTP_IDEMPOTENCY_KEY=key
    )
    assert response.status_code == 409
    assert problem(response)["code"] == "idempotency_conflict"
    assert User.objects.count() == 1


def test_idempotency_key_must_be_a_uuid(api: Api) -> None:
    response = api.post(SIGNUP, signup_body(), HTTP_IDEMPOTENCY_KEY="nope")
    assert response.status_code == 422
    assert User.objects.count() == 0


def test_signup_is_rate_limited_per_address(api: Api) -> None:
    for n in range(20):
        api.sign_up(email=f"user{n}@example.com")
    response = api.sign_up(email="one-too-many@example.com")
    assert response.status_code == 429
    assert problem(response)["code"] == "rate_limited"
    assert int(response["Retry-After"]) >= 1


@pytest.mark.success("POST /api/v1/auth/login")
def test_login_returns_profile_and_session(learner: Api) -> None:
    other = Api()
    response = other.post(LOGIN, {"email": "ADA@example.com", "password": PASSWORD})
    assert response.status_code == 200
    assert response.json()["email"] == "ada@example.com"
    assert other.get(ME).status_code == 200


@pytest.mark.not_found("POST /api/v1/auth/login")
def test_unknown_email_and_wrong_password_look_the_same(learner: Api) -> None:
    other = Api()
    wrong = other.post(LOGIN, {"email": "ada@example.com", "password": "Wrong-Pass-1"})
    unknown = other.post(LOGIN, {"email": "who@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.content == unknown.content
    assert problem(wrong)["code"] == "invalid_credentials"


@pytest.mark.refused("POST /api/v1/auth/login")
def test_seventh_login_from_one_address_is_refused_even_with_the_right_password(
    learner: Api,
) -> None:
    other = Api()
    bad = {"email": "ada@example.com", "password": "Wrong-Pass-1"}
    codes = [other.post(LOGIN, bad).status_code for _ in range(6)]
    assert codes == [401] * 6
    refused = other.post(LOGIN, bad)
    assert refused.status_code == 429
    assert problem(refused)["code"] == "rate_limited"
    assert int(refused["Retry-After"]) >= 1
    good = other.post(LOGIN, {"email": "ada@example.com", "password": PASSWORD})
    assert good.status_code == 429


def test_successful_logins_do_not_count_as_failures(learner: Api) -> None:
    other = Api()
    good = {"email": "ada@example.com", "password": PASSWORD}
    assert all(other.post(LOGIN, good).status_code == 200 for _ in range(8))


def test_account_without_a_password_cannot_log_in(db: None) -> None:
    from modules.identity.services import create_account

    create_account(
        email="nopass@example.com",
        date_of_birth=__import__("datetime").date(1990, 1, 2),
        interface_language="en",
        processing_consent=True,
    )
    response = Api().post(LOGIN, {"email": "nopass@example.com", "password": PASSWORD})
    assert response.status_code == 401


@pytest.mark.success("POST /api/v1/auth/logout")
def test_logout_invalidates_the_session(learner: Api) -> None:
    old_cookie = learner.client.cookies[settings.SESSION_COOKIE_NAME].value
    response = learner.post(LOGOUT)
    assert response.status_code == 204
    assert learner.get(ME).status_code == 401
    replay = Api()
    replay.client.cookies[settings.SESSION_COOKIE_NAME] = old_cookie
    assert replay.get(ME).status_code == 401


@pytest.mark.not_found("POST /api/v1/auth/logout")
def test_logout_without_a_session_is_unauthenticated(api: Api) -> None:
    response = api.post(LOGOUT)
    assert response.status_code == 401
    assert problem(response)["code"] == "not_authenticated"


@pytest.mark.refused("POST /api/v1/auth/logout")
def test_logout_without_csrf_token_is_refused(learner: Api) -> None:
    assert learner.post(LOGOUT, csrf=False).status_code == 403
    assert learner.get(ME).status_code == 200


@pytest.mark.success("GET /api/v1/me")
def test_me_returns_the_profile(learner: Api) -> None:
    body = learner.get(ME).json()
    assert body["email"] == "ada@example.com"
    assert body["display_name"] == "Ada"
    assert "password" not in body


@pytest.mark.not_found("GET /api/v1/me")
def test_me_with_an_unknown_session_cookie_is_unauthenticated(api: Api) -> None:
    api.client.cookies[settings.SESSION_COOKIE_NAME] = "doesnotexist"
    assert api.get(ME).status_code == 401


@pytest.mark.refused("GET /api/v1/me")
def test_me_without_a_session_is_refused(api: Api) -> None:
    response = api.get(ME)
    assert response.status_code == 401
    assert problem(response)["code"] == "not_authenticated"


@pytest.mark.success("PATCH /api/v1/me")
def test_language_change_applies_to_next_response_and_later_logins(
    learner: Api,
) -> None:
    response = learner.patch(ME, {"interface_language": "fr"})
    assert response.status_code == 200
    assert response.json()["interface_language"] == "fr"
    denied = learner.patch(ME, {"interface_language": "de"})
    assert denied["Content-Language"] == "fr"
    other = Api()
    login = other.post(LOGIN, {"email": "ada@example.com", "password": PASSWORD})
    assert login.json()["interface_language"] == "fr"
    assert User.objects.get().interface_language == "fr"


@pytest.mark.not_found("PATCH /api/v1/me")
def test_patch_me_without_a_session_is_unauthenticated(api: Api) -> None:
    response = api.patch(ME, {"interface_language": "fr"})
    assert response.status_code == 401


@pytest.mark.refused("PATCH /api/v1/me")
def test_patch_me_refuses_an_unsupported_language_and_missing_csrf(
    learner: Api,
) -> None:
    assert learner.patch(ME, {"interface_language": "de"}).status_code == 422
    assert (
        learner.patch(ME, {"interface_language": "fr"}, csrf=False).status_code == 403
    )
    assert User.objects.get().interface_language == "en"


def test_every_response_carries_hsts_of_a_year_or_more(api: Api) -> None:
    responses = [
        api.client.get(CSRF, secure=True),
        api.client.get(ME, secure=True),
        api.client.post(SIGNUP, secure=True),
        api.client.options(SIGNUP, secure=True, HTTP_ORIGIN=settings.WEB_APP_ORIGIN),
    ]
    for response in responses:
        assert "max-age=63072000" in response["Strict-Transport-Security"]
    assert settings.SECURE_HSTS_SECONDS >= 31536000


def test_cors_allows_only_the_exact_app_origin(api: Api) -> None:
    allowed = api.get(CSRF)
    assert allowed["Access-Control-Allow-Origin"] == settings.WEB_APP_ORIGIN
    assert allowed["Access-Control-Allow-Credentials"] == "true"
    assert allowed["Access-Control-Allow-Origin"] != "*"
    assert "Origin" in allowed["Vary"]
    for origin in ("https://evil.example", settings.WEB_APP_ORIGIN + ".evil.example"):
        denied = api.get(CSRF, HTTP_ORIGIN=origin)
        assert "Access-Control-Allow-Origin" not in denied


def test_preflight_lists_methods_headers_and_max_age(api: Api) -> None:
    response = api.client.options(
        SIGNUP,
        HTTP_ORIGIN=settings.WEB_APP_ORIGIN,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert response.status_code == 204
    assert response["Access-Control-Allow-Origin"] == settings.WEB_APP_ORIGIN
    assert response["Access-Control-Allow-Credentials"] == "true"
    assert response["Access-Control-Max-Age"] == "7200"
    headers = response["Access-Control-Allow-Headers"]
    for name in ("Content-Type", "X-CSRFToken", "Idempotency-Key"):
        assert name in headers
    foreign = api.client.options(
        SIGNUP,
        HTTP_ORIGIN="https://evil.example",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert "Access-Control-Allow-Origin" not in foreign


def test_session_and_csrf_cookie_attributes(learner: Api) -> None:
    session = learner.client.cookies[settings.SESSION_COOKIE_NAME]
    csrf = learner.client.cookies[settings.CSRF_COOKIE_NAME]
    assert session["httponly"]
    assert session["samesite"] == "Lax"
    assert session["path"] == "/"
    assert not session["domain"]
    assert csrf["samesite"] == "Lax"
    assert not csrf["domain"]
    assert not csrf["httponly"]


def test_logs_hold_the_learner_id_and_no_personal_data(
    api: Api, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    response = api.sign_up(email="private.person@example.com", display_name="Zorba")
    api.post(LOGIN, {"email": "private.person@example.com", "password": "Bad-Pass-1"})
    api.post(LOGOUT)
    api.sign_up(email="private.person@example.com", date_of_birth="2001-02-03")
    api.sign_up(email="young@example.com", date_of_birth=too_young())
    text = caplog.text
    assert f"learner_id={response.json()['learner_id']}" in text
    for secret in ("private.person", "Zorba", "1990-01-02", "2001-02-03", PASSWORD):
        assert secret not in text


def test_retry_after_is_readable_from_the_app_origin(api: Api) -> None:
    for n in range(21):
        response = api.sign_up(email=f"user{n}@example.com")
    assert response.status_code == 429
    assert response["Access-Control-Expose-Headers"] == "Retry-After"


def test_login_right_after_signup_is_refused_alike_for_new_and_known_emails(
    learner: Api,
) -> None:
    forget_mail_limits()
    other = "Another-Pass-9921"
    Api().sign_up(email="grace@example.com", password=other)
    assert Api().sign_up(email="ada@example.com", password=other).status_code == 201
    new = Api().post(LOGIN, {"email": "grace@example.com", "password": other})
    known = Api().post(LOGIN, {"email": "ada@example.com", "password": other})
    assert new.status_code == known.status_code == 401
    assert new.content == known.content
