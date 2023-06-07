import logging.config
import queue
import threading
import time
import os
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent

import settings
from utilities import task, query

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)

event_queue = queue.Queue()
delayed_scan_queue = queue.Queue()
directories_in_queue = set()


class EventHandler(FileSystemEventHandler):

    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__()
        logger.info(f"File System Event Handler initialized.")

    def on_modified(self, event):
        if not event.is_directory and not event.src_path.endswith('tmp') and not event.src_path.startswith('syncthing'):
            logger.info(
                f"'Modified' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}. "
                f"Adding to queue for processing.")
            event_queue.put(('created', event))
            dir_path = os.path.dirname(event.src_path)
            if dir_path not in directories_in_queue:
                delayed_scan_queue.put(dir_path)
                directories_in_queue.add(dir_path)

    def on_created(self, event):
        pass
        # if not event.src_path.endswith('tmp') and not event.src_path.startswith('syncthing'):
        #     logger.info(
        #         f"'Created' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}. "
        #         f"Adding to queue for processing.")
        #     event_queue.put(('created', event))
        #     if event.is_directory:
        #         dir_path = event.src_path
        #     else:
        #         dir_path = os.path.dirname(event.src_path)
        #     if dir_path not in directories_in_queue:
        #         delayed_scan_queue.put(dir_path)
        #         directories_in_queue.add(dir_path)

    def on_moved(self, event):
        if not event.src_path.endswith('tmp') and not event.src_path.startswith('syncthing'):
            logger.info(
                f"'Moved' event triggered for {'folder' if event.is_directory else 'file'}: {event.src_path} to "
                f"{event.dest_path}. Adding to queue for processing.")
            event_queue.put(('moved', event))
            if event.is_directory:
                dir_path = event.src_path
            else:
                dir_path = os.path.dirname(event.src_path)
            if dir_path not in directories_in_queue:
                delayed_scan_queue.put(dir_path)
                directories_in_queue.add(dir_path)

    def on_deleted(self, event):
        if not event.src_path.endswith('tmp') and not event.src_path.startswith('syncthing'):
            logger.info(f"'Deleted' event triggered for"
                        f" {'folder' if event.is_directory else 'file'}: {event.src_path}. "
                        f"Adding to queue for processing.")
            event_queue.put(('deleted', event))

    def scan_directory(self, directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                path = Path(os.path.join(root, file))
                logger.info(f"Found file: ... {path.parent}/{path.name}")
                event = FileCreatedEvent(path)
                event_queue.put(('created', event))


def worker():
    while True:
        event_tuple = event_queue.get()
        if event_tuple is None:
            break
        event_type, event = event_tuple
        task.process_event(event_type, event)


def delayed_scan_worker():
    while True:
        directory = delayed_scan_queue.get()
        if directory is None:
            break
        time.sleep(25)
        EventHandler().scan_directory(directory)
        directories_in_queue.remove(directory)


if __name__ == "__main__":
    query.test_connection()
    worker_thread = threading.Thread(target=worker)
    worker_thread.start()

    delayed_scan_thread = threading.Thread(target=delayed_scan_worker)
    delayed_scan_thread.start()

    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=settings.WATCHING_DIR, recursive=True)
    logger.info(f"Watching DIR: {settings.WATCHING_DIR}")
    observer.start()

    try:
        while True:
            time.sleep(.7)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    # Stop worker thread
    event_queue.put(None)
    worker_thread.join()
