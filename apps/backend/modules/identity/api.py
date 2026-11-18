import logging
from typing import Annotated, Any

from config.problems import FieldProblem, Problem
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token, rotate_token
from ninja import Header, Router, Status

from . import idempotency, throttle
from .auth import learner_auth
from .models import IdempotencyRecord, User
from .problems import problem_for
from .schemas import (
    AccountSession,
    CsrfToken,
    LoginIn,
    Profile,
    ProfilePatch,
    SignUpIn,
)
from .services import (
    AccountDetails,
    AccountRefused,
    decoy_profile,
    normalize_email,
    profile_of,
    register,
)

logger = logging.getLogger(__name__)
router = Router(tags=["account"])

SIGNUP_SCOPE = "signup"


def _replay(
    saved: IdempotencyRecord, details: AccountDetails
) -> tuple[User | None, dict[str, Any]]:
    # WHY: the record keeps only the learner ID; the profile is rebuilt, never stored.
    if saved.user is not None:
        return saved.user, profile_of(saved.user)
    return None, decoy_profile(details, saved.response["learner_id"])


def _anonymous_session(request: HttpRequest) -> None:
    # SECURITY: a used email gets the same cookies as a new account, but no login.
    request.session["anonymous"] = True
    request.session.cycle_key()
    rotate_token(request)


def _user(request: HttpRequest) -> User:
    user = request.user
    assert isinstance(user, User)
    return user


@router.get(
    "/auth/csrf",
    auth=None,
    response={200: CsrfToken},
    summary="Get a CSRF token",
    description="Access: public. Send the token as X-CSRFToken on every write.",
)
def csrf(request: HttpRequest) -> CsrfToken:
    return CsrfToken(csrf_token=get_token(request))


@router.post(
    "/auth/signup",
    auth=None,
    response={
        201: AccountSession,
        403: Problem,
        409: Problem,
        422: Problem,
        429: Problem,
    },
    summary="Sign up",
    description=(
        "Access: public. Creates the account and signs the learner in. "
        "An email already in use gets the same answer, without signing in. "
        "Accepts an Idempotency-Key (UUID), kept for 24 hours."
    ),
)
def signup(
    request: HttpRequest,
    payload: SignUpIn,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="UUID. Retrying with the same key and body replays the answer.",
        ),
    ] = None,
) -> Status[AccountSession] | HttpResponse:
    language = payload.interface_language
    address = throttle.client_address(request)
    wait = throttle.retry_after(throttle.SIGNUPS, address)
    if wait is not None:
        return problem_for(
            request,
            429,
            "rate_limited",
            language=language,
            headers={"Retry-After": str(wait)},
        )
    throttle.record(throttle.SIGNUPS, address)
    logger.info("event=signup_submitted")

    key = None
    if idempotency_key is not None:
        key = idempotency.parse_key(idempotency_key)
        if key is None:
            return problem_for(
                request,
                422,
                "validation_error",
                language=language,
                errors=[FieldProblem(field="Idempotency-Key", code="invalid")],
            )

    details = AccountDetails(
        email=payload.email,
        date_of_birth=payload.date_of_birth,
        interface_language=payload.interface_language,
        processing_consent=payload.processing_consent,
        display_name=payload.display_name,
    )
    fingerprint = idempotency.fingerprint(
        dict(
            email=normalize_email(payload.email),
            password=payload.password,
            date_of_birth=payload.date_of_birth,
            interface_language=payload.interface_language,
            display_name=payload.display_name.strip(),
            processing_consent=payload.processing_consent,
        )
    )
    user: User | None = None
    profile: dict[str, Any] | None = None
    try:
        with transaction.atomic():
            if key is not None:
                idempotency.lock(SIGNUP_SCOPE, key)
                saved = idempotency.find(SIGNUP_SCOPE, key)
                if saved is not None:
                    if not idempotency.matches(saved, fingerprint):
                        return problem_for(
                            request, 409, "idempotency_conflict", language=language
                        )
                    user, profile = _replay(saved, details)
            if profile is None:
                user, profile = register(details, payload.password)
                if user is None:
                    logger.info("event=signup_refused reason=duplicate")
                else:
                    logger.info("event=signup_completed learner_id=%s", user.id)
                if key is not None:
                    idempotency.store(
                        SIGNUP_SCOPE,
                        key,
                        fingerprint,
                        user,
                        201,
                        {"learner_id": profile["learner_id"]},
                    )
    except AccountRefused as refused:
        reason = {"age_below_minimum": "age", "consent_required": "consent"}
        logger.info(
            "event=signup_refused reason=%s", reason.get(refused.code, "invalid")
        )
        return problem_for(request, 422, refused.code, language=language)

    if user is not None:
        login(request, user)
    else:
        _anonymous_session(request)
    return Status(
        201,
        AccountSession.model_validate(dict(profile, csrf_token=get_token(request))),
    )


@router.post(
    "/auth/login",
    auth=None,
    response={
        200: AccountSession,
        401: Problem,
        403: Problem,
        422: Problem,
        429: Problem,
    },
    summary="Log in",
    description=(
        "Access: public. A wrong password and an unknown email get the same answer. "
        "After 5 failures in a minute from one address, the next attempt is refused."
    ),
)
def log_in(
    request: HttpRequest, payload: LoginIn
) -> Status[AccountSession] | HttpResponse:
    address = throttle.client_address(request)
    wait = throttle.retry_after(throttle.LOGIN_FAILURES, address)
    if wait is not None:
        return problem_for(
            request, 429, "rate_limited", headers={"Retry-After": str(wait)}
        )
    user = authenticate(request, email=payload.email, password=payload.password)
    if not isinstance(user, User):
        throttle.record(throttle.LOGIN_FAILURES, address)
        logger.info("event=login_failed")
        return problem_for(request, 401, "invalid_credentials")
    login(request, user)
    logger.info("event=login_succeeded learner_id=%s", user.id)
    return Status(
        200,
        AccountSession.model_validate(
            dict(profile_of(user), csrf_token=get_token(request))
        ),
    )


@router.post(
    "/auth/logout",
    auth=learner_auth,
    response={204: None, 401: Problem, 403: Problem},
    summary="Log out",
    description="Access: learner. Ends this session on the server.",
)
def log_out(request: HttpRequest) -> Status[None]:
    learner_id = _user(request).id
    logout(request)
    logger.info("event=logout learner_id=%s", learner_id)
    return Status(204, None)


@router.get(
    "/me",
    auth=learner_auth,
    response={200: Profile, 401: Problem},
    summary="Read the profile",
    description="Access: learner.",
)
def read_profile(request: HttpRequest) -> dict[str, Any]:
    return profile_of(_user(request))


@router.patch(
    "/me",
    auth=learner_auth,
    response={200: Profile, 401: Problem, 403: Problem, 422: Problem},
    summary="Update the profile",
    description="Access: learner. Changes the interface language or the display name.",
)
def update_profile(request: HttpRequest, payload: ProfilePatch) -> dict[str, Any]:
    user = _user(request)
    changed = []
    if payload.interface_language is not None:
        user.interface_language = payload.interface_language
        changed.append("interface_language")
    if payload.display_name is not None:
        user.display_name = payload.display_name.strip()
        changed.append("display_name")
    if changed:
        user.save(update_fields=changed)
    return profile_of(user)
