from asgiref.sync import sync_to_async
from config.jobs import RETRY, observed
from procrastinate import JobContext
from procrastinate.contrib.django import app

from . import mail
from .models import MailOutbox


def queue_mail(kind: str, recipient: str, language: str, nonce: str = "") -> None:
    """Write the mail and its job; call inside the transaction that causes it."""
    row = MailOutbox.objects.create(
        kind=kind, recipient=recipient, language=language, nonce=nonce
    )
    send_mail_job.defer(outbox_id=str(row.id))


@app.task(name="identity_send_mail", pass_context=True, retry=RETRY)
@observed
async def send_mail_job(context: JobContext, outbox_id: str) -> None:
    await sync_to_async(mail.deliver)(outbox_id)


# WHY: a mail that failed every retry would keep its address in the table.
@app.periodic(cron="17 * * * *")
@app.task(name="identity_purge_mail_outbox", queueing_lock="identity_purge_mail_outbox")
async def purge_mail_outbox(timestamp: int) -> None:
    await sync_to_async(mail.purge_unsent)()
