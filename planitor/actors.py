import os
import signal
import time
from queue import Empty

import dramatiq
from dramatiq.worker import _WorkerThread

from .attachments import update_pdf_attachment
from .database import db_context
from .monitor import create_deliveries, send_meeting_emails, send_weekly_emails
from .notifications import send_applicant_notifications
from .postprocess import update_minute_search_vector, update_minute_with_entity_mentions


@dramatiq.actor
def test_actor(num):
    with db_context() as db:
        result = db.execute("select 1;").scalar()
        return result


# Hack the Dramatiq worker thread to send a SIGHUP which elegantly kills the process upon empty queue
# The reason we do this is to be able to run this on Render Cron with beefier hardware. We start this
# once a day and then don't pay for the hardware if there is no work to be done.
def run(self: _WorkerThread):
    self.logger.debug("Running worker thread...")
    self.running = True
    while self.running:
        if self.paused:
            self.logger.debug("Worker is paused. Sleeping for %.02f...", self.timeout)
            self.paused_event.set()
            time.sleep(self.timeout)
            continue

        try:
            _, message = self.work_queue.get(timeout=self.timeout)
            self.process_message(message)
        except Empty:
            # Here comes the hacked line - kill when work is done
            os.kill(os.getpid(), signal.SIGHUP)
            continue

    self.broker.emit_before("worker_thread_shutdown", self)
    self.logger.debug("Worker thread stopped.")


_WorkerThread.run = run

__all__ = [
    "update_minute_with_entity_mentions",
    "update_minute_search_vector",
    "update_pdf_attachment",
    "create_deliveries",
    "send_meeting_emails",
    "send_weekly_emails",
    "send_applicant_notifications",
]
