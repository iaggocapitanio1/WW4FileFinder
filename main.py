import concurrent.futures
import logging.config
import queue
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import settings
from utilities.funtions import get_path_after_keyword
from utilities.query import folder_already_exists

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)

event_queue = queue.Queue()


class EventHandler(FileSystemEventHandler):

    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__()
        logger.info(f"File System Event Handler initialized.")

    def on_created(self, event):
        from pathlib import Path
        if event.is_directory:
            logger.info(f"Folder created: {Path(event.src_path).name}")
            folder_already_exists(path=event.src_path)
        else:
            logger.info(f"File creation event triggered!")

        event_queue.put(('created', event))

    def on_modified(self, event):
        if event.is_directory:
            logger.info(f"Folder has been modified: {event.src_path}")
            logger.info(f"Path: {get_path_after_keyword(path=event.src_path, keyword='mofreitas')}")
        else:
            logger.info(f"File has been modified: {event.src_path}")
        event_queue.put(('modified', event))

    def on_deleted(self, event):
        if event.is_directory:
            logger.info(f"Folder has been deleted: {event.src_path}")
        else:
            logger.info(f"File has been deleted: {event.src_path}")
        event_queue.put(('deleted', event))


def process_event(event_type, event):
    if event_type == 'created':
        logger.info("Trying to post file ....")

    elif event_type == 'modified':
        logger.info("Trying to put file ....")

    elif event_type == 'deleted':
        logger.info("Trying to delete file ....")


def worker():
    while True:
        event_tuple = event_queue.get()
        if event_tuple is None:
            break
        event_type, event = event_tuple
        process_event(event_type, event)


if __name__ == "__main__":

    # Create a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start worker threads
        for _ in range(settings.NUM_WORKER_THREADS):
            executor.submit(worker)

        # Start the observer
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
