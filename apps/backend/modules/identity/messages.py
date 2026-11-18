from django.http import HttpRequest

LANGUAGES = ("fr", "en")
DEFAULT_LANGUAGE = "en"

# code -> language -> (title, detail)
CATALOG: dict[str, dict[str, tuple[str, str]]] = {
    "age_below_minimum": {
        "en": ("Too young", "You must be 16 or older to create an account."),
        "fr": (
            "Âge insuffisant",
            "Vous devez avoir 16 ans ou plus pour créer un compte.",
        ),
    },
    "consent_required": {
        "en": (
            "Consent required",
            "You must agree to the processing of your data to sign up.",
        ),
        "fr": (
            "Consentement requis",
            "Vous devez accepter le traitement de vos données pour vous inscrire.",
        ),
    },
    "weak_password": {
        "en": (
            "Password too weak",
            "Use at least 10 characters that are not too common.",
        ),
        "fr": (
            "Mot de passe trop faible",
            "Utilisez au moins 10 caractères, sans mot de passe trop courant.",
        ),
    },
    "invalid_credentials": {
        "en": ("Sign-in failed", "The email or the password is wrong."),
        "fr": (
            "Connexion refusée",
            "L'adresse e-mail ou le mot de passe est incorrect.",
        ),
    },
    "rate_limited": {
        "en": ("Too many attempts", "Too many attempts. Try again in a moment."),
        "fr": ("Trop de tentatives", "Trop de tentatives. Réessayez dans un instant."),
    },
    "not_authenticated": {
        "en": ("Not signed in", "Sign in to continue."),
        "fr": ("Non connecté", "Connectez-vous pour continuer."),
    },
    "csrf_failed": {
        "en": (
            "Request refused",
            "The security token is missing or wrong. Reload and retry.",
        ),
        "fr": (
            "Requête refusée",
            "Le jeton de sécurité est absent ou incorrect. Rechargez et réessayez.",
        ),
    },
    "validation_error": {
        "en": ("Invalid request", "Some fields are missing or invalid."),
        "fr": ("Requête invalide", "Certains champs sont absents ou invalides."),
    },
    "idempotency_conflict": {
        "en": (
            "Key already used",
            "This Idempotency-Key was used with a different request.",
        ),
        "fr": (
            "Clé déjà utilisée",
            "Cette clé Idempotency-Key a déjà servi pour une requête différente.",
        ),
    },
}


def pick_language(header: str) -> str:
    ranked: list[tuple[float, int, str]] = []
    for position, part in enumerate(header.split(",")):
        tag, _, params = part.strip().partition(";")
        base = tag.strip().lower().split("-")[0]
        weight = 1.0
        if params.strip().startswith("q="):
            try:
                weight = float(params.strip()[2:])
            except ValueError:
                weight = 0.0
        if base in LANGUAGES and weight > 0:
            ranked.append((-weight, position, base))
    return min(ranked)[2] if ranked else DEFAULT_LANGUAGE


def request_language(request: HttpRequest) -> str:
    """The signed-in learner's language, else Accept-Language, else English."""
    user = getattr(request, "user", None)
    language = getattr(user, "interface_language", None) if user else None
    if user is not None and user.is_authenticated and language in LANGUAGES:
        return str(language)
    return pick_language(request.headers.get("Accept-Language", ""))
