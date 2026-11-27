import logging
from typing import Annotated, Any

from config.problems import FieldProblem, Problem
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from ninja import Header, Router, Status

from . import idempotency, throttle, verification
from .auth import learner_auth
from .models import IdempotencyRecord, User
from .problems import problem_for
from .schemas import (
    AccountSession,
    CsrfToken,
    EmailIn,
    LoginIn,
    Profile,
    ProfilePatch,
    ResendAccepted,
    SignUpIn,
    VerifyEmailIn,
)
from .services import (
    AccountDetails,
    AccountRefused,
    MailRateLimited,
    decoy_profile,
    ensure_strong_password,
    normalize_email,
    profile_of,
    register,
)

logger = logging.getLogger(__name__)
router = Router(tags=["account"])

SIGNUP_SCOPE = "signup"
RESEND_SCOPE = "resend"


def _replay(
    saved: IdempotencyRecord, details: AccountDetails
) -> tuple[User | None, dict[str, Any]]:
    # WHY: the record keeps only the learner ID; the profile is rebuilt, never stored.
    if saved.user is not None:
        return saved.user, profile_of(saved.user)
    return None, decoy_profile(details, saved.response["learner_id"])


def _rate_limited(
    request: HttpRequest, wait: int, language: str | None = None
) -> HttpResponse:
    return problem_for(
        request,
        429,
        "rate_limited",
        language=language,
        headers={"Retry-After": str(wait)},
    )


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
        "Access: public. Creates the account and mails a six-digit code; the "
        "learner is signed in only by entering it. An email already in use gets "
        "the same answer and an account notice instead of a code. 20 sign-ups per "
        "hour from one address, and the mail limits of the resend endpoint. "
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
    # SECURITY: count first, so the request past the limit is the one refused.
    wait = throttle.wait_if_over(
        throttle.SIGNUPS, throttle.record(throttle.SIGNUPS, address)
    )
    if wait is not None:
        return _rate_limited(request, wait, language)
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
    except MailRateLimited as limited:
        logger.info("event=signup_throttled reason=mail")
        return _rate_limited(request, limited.wait, language)

    return Status(
        201,
        AccountSession.model_validate(dict(profile, csrf_token=get_token(request))),
    )


@router.post(
    "/auth/verify-email",
    auth=None,
    response={200: AccountSession, 403: Problem, 422: Problem, 429: Problem},
    summary="Verify the email with a code",
    description=(
        "Access: public. A right code, within 10 minutes and before 5 wrong tries, "
        "verifies the address, sets the password sent with it and signs the learner "
        "in. A weak password is a 422 weak_password before the code is checked. At "
        "most 10 wrong tries a day per account and 10 tries a minute from one client "
        "address. Every other refusal gets the same 422 invalid_code answer; request "
        "a new code after one."
    ),
)
def verify_email(
    request: HttpRequest, payload: VerifyEmailIn
) -> Status[AccountSession] | HttpResponse:
    # SECURITY: count first, so a guess past the limit is refused before it is checked.
    wait = throttle.wait_if_over(
        throttle.VERIFY_TRIES,
        throttle.record(throttle.VERIFY_TRIES, throttle.client_address(request)),
    )
    if wait is not None:
        logger.info("event=verification_throttled")
        return _rate_limited(request, wait)
    try:
        ensure_strong_password(payload.password)
    except AccountRefused as refused:
        return problem_for(request, 422, refused.code)
    user = verification.verify_code(
        normalize_email(payload.email), payload.code, payload.password
    )
    if user is None:
        return problem_for(request, 422, "invalid_code")
    login(request, user)
    return Status(
        200,
        AccountSession.model_validate(
            dict(profile_of(user), csrf_token=get_token(request))
        ),
    )


@router.post(
    "/auth/verify-email/resend",
    auth=None,
    response={
        202: ResendAccepted,
        403: Problem,
        409: Problem,
        422: Problem,
        429: Problem,
    },
    summary="Send a new verification code",
    description=(
        "Access: public. Always answers 202 the same way; a new code is mailed only "
        "when an unverified account exists, and the old one stops working. At most "
        "1 mail a minute and 5 an hour per address, shared with sign-up, and 10 "
        "requests a minute from one client address; over that the answer is 429 "
        "with Retry-After. Accepts an Idempotency-Key (UUID)."
    ),
)
def resend_code(
    request: HttpRequest,
    payload: EmailIn,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="UUID. Retrying with the same key and body replays the answer.",
        ),
    ] = None,
) -> Status[ResendAccepted] | HttpResponse:
    address = normalize_email(payload.email)
    wait = throttle.wait_if_over(
        throttle.RESEND_REQUESTS,
        throttle.record(throttle.RESEND_REQUESTS, throttle.client_address(request)),
    )
    if wait is not None:
        logger.info("event=verification_throttled")
        return _rate_limited(request, wait)
    key = None
    if idempotency_key is not None:
        key = idempotency.parse_key(idempotency_key)
        if key is None:
            return problem_for(
                request,
                422,
                "validation_error",
                errors=[FieldProblem(field="Idempotency-Key", code="invalid")],
            )
    fingerprint = idempotency.fingerprint(dict(email=address))
    try:
        with transaction.atomic():
            saved = None
            if key is not None:
                idempotency.lock(RESEND_SCOPE, key)
                saved = idempotency.find(RESEND_SCOPE, key)
                if saved is not None and not idempotency.matches(saved, fingerprint):
                    return problem_for(request, 409, "idempotency_conflict")
            if saved is None:
                wait = verification.reserve_mail(address)
                if wait is not None:
                    raise MailRateLimited(wait)
                verification.queue_for_address(address)
                if key is not None:
                    idempotency.store(RESEND_SCOPE, key, fingerprint, None, 202, {})
    except MailRateLimited as limited:
        logger.info("event=resend_throttled")
        return _rate_limited(request, limited.wait)
    logger.info("event=verification_resent")
    return Status(
        202,
        ResendAccepted(resend_available_in=throttle.MAILS_PER_MINUTE.window_seconds),
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
        "After 6 failed attempts in a minute from one address (an IPv6 /64 range "
        "counts as one), or 10 in an hour against one email, the next attempt is "
        "refused with a 429 and a Retry-After header."
    ),
)
def log_in(
    request: HttpRequest, payload: LoginIn
) -> Status[AccountSession] | HttpResponse:
    address = throttle.client_address(request)
    email = normalize_email(payload.email)
    # SECURITY: count before the check, so an error in it still costs an attempt.
    by_address = throttle.record(throttle.LOGIN_FAILURES, address)
    wait = throttle.wait_if_over(throttle.LOGIN_FAILURES, by_address)
    if wait is None:
        by_email = throttle.record(throttle.LOGIN_EMAIL_FAILURES, email)
        wait = throttle.wait_if_over(throttle.LOGIN_EMAIL_FAILURES, by_email)
    if wait is not None:
        logger.info("event=login_throttled")
        return problem_for(
            request, 429, "rate_limited", headers={"Retry-After": str(wait)}
        )
    user = authenticate(request, email=payload.email, password=payload.password)
    if not isinstance(user, User):
        logger.info("event=login_failed")
        return problem_for(request, 401, "invalid_credentials")
    throttle.release(throttle.LOGIN_FAILURES, address)
    throttle.release(throttle.LOGIN_EMAIL_FAILURES, email)
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
