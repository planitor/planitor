import os
import signal
import time
from queue import Empty

import dramatiq
from dramatiq.worker import _WorkerThread

from . import broker
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
    print("CONSUMSER", self.consumers)
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

            for consumer in self.consumers.values():
                if consumer.delay_queue.unfinished_tasks:
                    continue
            else:
                if self.work_queue.unfinished_tasks:
                    continue

            break

    self.logger.info("Queue is empty, shutting down process")
    os.kill(os.getppid(), signal.SIGTERM)

    self.broker.emit_before("worker_thread_shutdown", self)
    self.logger.debug("Worker thread stopped.")


# _WorkerThread.run = run

__all__ = [
    "update_minute_with_entity_mentions",
    "update_minute_search_vector",
    "update_pdf_attachment",
    "create_deliveries",
    "send_meeting_emails",
    "send_weekly_emails",
    "send_applicant_notifications",
]

"""

    def join(self):
        while True:
            for consumer in self.consumers.values():
                consumer.delay_queue.join()

            self.work_queue.join()

            # If nothing got put on the delay queues while we were
            # joining on the work queue then it shoud be safe to exit.
            # This could still miss stuff but the chances are slim.
            for consumer in self.consumers.values():
                if consumer.delay_queue.unfinished_tasks:
                    break
            else:
                if self.work_queue.unfinished_tasks:
                    continue
                return"""
