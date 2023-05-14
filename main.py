import concurrent.futures
import logging.config
import queue
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from utilities import task
import settings

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)

event_queue = queue.Queue()


class EventHandler(FileSystemEventHandler):

    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__()
        logger.info(f"File System Event Handler initialized.")

    def on_created(self, event):
        logger.info(f"'Created' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}. "
                    f"Adding to queue for processing.")
        event_queue.put(('created', event))

    def on_moved(self, event):
        logger.info(f"'Moved' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path} to "
                    f"{event.dest_path}. Adding to queue for processing.")
        event_queue.put(('moved', event))

    def on_deleted(self, event):
        logger.info(f"'Deleted' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}. "
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
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for _ in range(settings.NUM_WORKER_THREADS):
            executor.submit(worker)
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

        # Stop worker threads
        for _ in range(settings.NUM_WORKER_THREADS):
            event_queue.put(None)
