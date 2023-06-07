import logging.config
import queue
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import settings
from utilities import task, query

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)

event_queue = queue.Queue()


class EventHandler(FileSystemEventHandler):

    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__()
        logger.info(f"File System Event Handler initialized.")

    def on_modified(self, event):
        if not event.is_directory and not event.src_path.endswith('.tmp'):
            logger.info(
                f"'Modified' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}. "
                f"Adding to queue for processing.")
            event_queue.put(('created', event))

    # def on_created(self, event):
    #     if not event.src_path.endswith('.tmp'):
    #         logger.info(
    #             f"'Created' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}. "
    #             f"Adding to queue for processing.")
    #         event_queue.put(('created', event))

    def on_moved(self, event):
        if not event.src_path.endswith('.tmp'):
            logger.info(
                f"'Moved' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path} to "
                f"{event.dest_path}. Adding to queue for processing.")
            event_queue.put(('moved', event))

    def on_deleted(self, event):
        if not event.src_path.endswith('.tmp'):
            logger.info(f"'Deleted' event triggered for"
                        f" {'folder' if event.is_directory else 'file'}: {event.src_path}. "
                        f"Adding to queue for processing.")
            event_queue.put(('deleted', event))


def worker():
    while True:
        event_tuple = event_queue.get()
        if event_tuple is None:
            break
        event_type, event = event_tuple
        task.process_event(event_type, event)


if __name__ == "__main__":
    query.test_connection()
    worker_thread = threading.Thread(target=worker)
    worker_thread.start()

    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=settings.WATCHING_DIR, recursive=True)
    logger.info(f"Watching DIR: {settings.WATCHING_DIR}")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    # Stop worker thread
    event_queue.put(None)
    worker_thread.join()
