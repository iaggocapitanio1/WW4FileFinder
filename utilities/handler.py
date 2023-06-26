import functools
import logging.config
import os
from pathlib import Path
from queue import Queue
from typing import Union

from utilities.funtions import validate_path
from watchdog.events import FileSystemEvent, FileModifiedEvent
from watchdog.events import FileSystemEventHandler

import settings

logger = logging.getLogger(__name__)


class EventHandler(FileSystemEventHandler):
    def __init__(self, event_queue: Queue, delayed_scan_queue: Queue, directories_in_queue: Union[Queue, set, list],
                 process_and_scan: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_queue = event_queue
        self.delayed_scan_queue = delayed_scan_queue
        self.directories_in_queue = directories_in_queue
        self.process_and_scan = process_and_scan
        logger.info(f"------------- FILE FINDER INITIALIZED -------------")

    @staticmethod
    @functools.cache
    def parse_path(path: str) -> Path:
        return Path(path).resolve()

    @functools.cache
    def is_valid_path(self, path: Path) -> bool:
        """
                Verifies if the given source_path contains the specified reference directory
                and that the source_path is a file located under the reference directory.

                Parameters:
                - source_path (Path): The path of the file to be verified.
                - reference (str): The reference directory to check if source_path is under. Default is 'Lists_and_Tags'.

                Returns:
                - bool: True if source_path is a file and is under the reference directory, False otherwise.
                """
        string_path: str = path.__str__()
        if string_path.endswith('tmp') or string_path.startswith('syncthing'):
            return False
        path = validate_path(path)
        if path.is_dir():
            return False
        if settings.KEY_PATH not in path.parts:
            return False
        current_path = Path(*path.parts[path.parts.index(settings.KEY_PATH):])
        while current_path != current_path.parent:  # Stop when reaching the root directory
            if current_path.name == settings.KEY_PATH:
                return True
            current_path = current_path.parent
        return False

    def add_to_event_queue(self, event: FileSystemEvent, event_type: str):
        self.event_queue.put((event, event_type))

    def add_to_dir_queue(self, path: Path):
        if not path.is_dir():
            path = path.parent
        if path not in self.directories_in_queue:
            self.directories_in_queue.add(path)
            self.delayed_scan_queue.put(path)

    def add_to_queue(self, event: FileSystemEvent, event_type: str) -> None:
        file_path: Path = self.parse_path(event.src_path)
        dir_path = file_path.parent
        if self.is_valid_path(file_path):
            logger.info(f"'{event_type.upper()}' event triggered for 'file': {event.src_path}")
            self.add_to_dir_queue(dir_path)
            if self.process_and_scan:
                self.add_to_event_queue(event, event_type)

    def on_created(self, event: FileCreatedEvent):
        self.add_to_queue(event, 'created')

    def on_modified(self, event: FileSystemEvent):
        self.add_to_queue(event, 'modified')

    def on_moved(self, event):
        self.add_to_queue(event, 'moved')

    def on_deleted(self, event):
        self.add_to_queue(event, 'deleted')

    def scan_directory(self, directory):
        logger.info(f"Scanning directory: {directory}")
        for root, dirs, files in os.walk(directory):
            for file in files:
                path = Path(os.path.join(root, file))
                logger.info(f"Found file: ... {path.parent}/{path.name}")
                event = FileModifiedEvent(path)
                if event.event_type == 'deleted':
                    continue
                if not path.__str__().endswith('tmp') and not path.__str__().startswith('syncthing'):
                    self.add_to_event_queue(event, event_type=event.event_type)
