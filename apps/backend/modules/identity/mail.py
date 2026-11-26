import logging
from datetime import timedelta

from django.core.mail import send_mail
from django.utils import timezone

from .models import MailOutbox

logger = logging.getLogger(__name__)

KEEP_UNSENT = timedelta(hours=1)

TEXTS: dict[str, dict[str, tuple[str, str]]] = {
    MailOutbox.Kind.VERIFICATION_CODE: {
        "en": (
            "Your GaugePrep verification code",
            "Your GaugePrep code is {code}.\n\n"
            "It works for 10 minutes. If you did not create an account, ignore "
            "this message.\n",
        ),
        "fr": (
            "Votre code de vérification GaugePrep",
            "Votre code GaugePrep est {code}.\n\n"
            "Il est valable 10 minutes. Si vous n'avez pas créé de compte, "
            "ignorez ce message.\n",
        ),
    },
    MailOutbox.Kind.ACCOUNT_EXISTS: {
        "en": (
            "You already have a GaugePrep account",
            "Someone used this address to sign up for GaugePrep, but an account "
            "already exists.\n\n"
            "If it was you, sign in with your password. If you have not "
            "confirmed your address yet, ask the app for a new code. If it was "
            "not you, ignore this message.\n",
        ),
        "fr": (
            "Vous avez déjà un compte GaugePrep",
            "Quelqu'un a utilisé cette adresse pour s'inscrire sur GaugePrep, "
            "mais un compte existe déjà.\n\n"
            "Si c'était vous, connectez-vous avec votre mot de passe. Si vous "
            "n'avez pas encore confirmé votre adresse, demandez un nouveau code "
            "dans l'application. Si ce n'était pas vous, ignorez ce message.\n",
        ),
    },
}


def render(row: MailOutbox) -> tuple[str, str]:
    from .verification import code_for  # WHY: verification imports the job module

    subject, body = TEXTS[row.kind][row.language]
    code = code_for(row.nonce) if row.nonce else ""
    return subject, body.format(code=code)


def deliver(outbox_id: str) -> None:
    """Send one queued mail and drop its row; a row already gone was sent."""
    row = MailOutbox.objects.filter(id=outbox_id).first()
    if row is None:
        return
    subject, body = render(row)
    send_mail(subject, body, None, [row.recipient])
    row.delete()
    logger.info("mail_sent template=%s", row.kind)


def purge_unsent() -> int:
    """Delete rows a failed job left behind, so no address stays in the table."""
    cutoff = timezone.now() - KEEP_UNSENT
    deleted, _ = MailOutbox.objects.filter(created_at__lt=cutoff).delete()
    return deleted
