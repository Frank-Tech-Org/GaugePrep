# Background jobs that belong to no module: the mail health check, stalled-job recovery.

import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.mail import send_mail
from procrastinate import JobContext, RetryStrategy
from procrastinate.contrib.django import app

logger = logging.getLogger("gaugeprep.jobs")

# WHY: four retries after 2, 4, 8 and 16 s make five runs, then the job stays failed.
RETRIES = 4
RUNS = RETRIES + 1
RETRY = RetryStrategy(max_attempts=RETRIES, exponential_wait=2)


# One log line per start, success and failure; never the job arguments.
def observed(
    func: Callable[..., Awaitable[None]],
) -> Callable[..., Awaitable[None]]:
    @wraps(func)
    async def run(context: JobContext, *args: Any, **kwargs: Any) -> None:
        name, attempt = context.task.name, context.job.attempts + 1
        logger.info("job_started job=%s attempt=%d", name, attempt)
        try:
            await func(context, *args, **kwargs)
        except Exception:
            logger.exception("job_failed job=%s attempt=%d", name, attempt)
            raise
        logger.info("job_succeeded job=%s attempt=%d", name, attempt)

    return run


@app.task(name="mail_health", pass_context=True, retry=RETRY)
@observed
async def mail_health(context: JobContext) -> None:
    await sync_to_async(send_mail)(
        "GaugePrep mail check",
        "This message proves the worker can send mail.",
        None,
        [settings.MAIL_HEALTH_TO],
    )
    logger.info("mail_sent template=health")


# WHY: a killed worker leaves its job in doing; this puts it back in the queue.
@app.periodic(cron="* * * * *")
@app.task(name="retry_stalled_jobs", queueing_lock="retry_stalled_jobs")
async def retry_stalled_jobs(timestamp: int) -> None:
    for job in await app.job_manager.get_stalled_jobs():
        logger.warning("job_requeued job=%s attempt=%d", job.task_name, job.attempts)
        await app.job_manager.retry_job(job)
