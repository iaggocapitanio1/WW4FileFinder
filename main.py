import logging.config
import queue
import threading
import time
from typing import Tuple

from watchdog.events import FileSystemEvent
from watchdog.observers import Observer

import settings
from utilities import task, http_requests as http
from utilities.handler import EventHandler

# Logger Configuration
logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)

# Queues and set for directories
event_queue = queue.Queue()
delayed_scan_queue = queue.Queue()
directories_in_queue = set()

# Sentinel object for termination
sentinel = object()


# Worker functions
def worker():
    while True:
        event_tuple: Tuple[FileSystemEvent, str] = event_queue.get()
        if event_tuple is sentinel:
            break
        event, event_type = event_tuple
        task.process_event(event, event_type)


def delayed_scan_worker(event_handler):
    while True:
        directory = delayed_scan_queue.get()
        if directory is sentinel:
            break
        time.sleep(settings.DELAY_FOR_SCAN)
        event_handler.scan_directory(directory)
        directories_in_queue.remove(directory)


# Main
if __name__ == "__main__":
    http.test_connection()

    event_handler_instance = EventHandler(event_queue, delayed_scan_queue, directories_in_queue)

    # Threads
    worker_thread = threading.Thread(target=worker, daemon=True)
    delayed_scan_thread = threading.Thread(target=delayed_scan_worker, args=(event_handler_instance,), daemon=True)

    # Start Threads
    worker_thread.start()
    delayed_scan_thread.start()

    # Observer
    observer = Observer()
    observer.schedule(event_handler_instance, path=settings.WATCHING_DIR, recursive=True)
    logger.info(f"WATCHING DIR: {settings.WATCHING_DIR}")
    observer.start()

    # Main loop
    try:
        while True:
            time.sleep(settings.SLEEP_DURATION)
    except KeyboardInterrupt:
        observer.stop()

    # Cleanup
    event_queue.put(sentinel)
    delayed_scan_queue.put(sentinel)

    # Wait for threads to finish
    worker_thread.join()
    delayed_scan_thread.join()

    # Wait for observer to finish
    observer.join()
