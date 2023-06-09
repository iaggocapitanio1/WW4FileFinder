import logging.config
import os.path

from watchdog.events import FileSystemEvent

from utilities import folders, files

logger = logging.getLogger(__name__)


def process_event(event: FileSystemEvent, event_type: str):
    if event_type == 'created':
        logger.info(f"Event 'created' triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}")
        if event.is_directory:
            result: bool = folders.on_folder_created(src_path=event.src_path)
            status = 'succeeded' if result else 'failed'
            logger.info(f"Post folder '{os.path.basename(event.src_path)}' {status}.")
        else:
            logger.info(f"Posting file '{os.path.basename(event.src_path)}'....")
            files.on_file_created(src_path=event.src_path)

    elif event_type == 'moved' or event_type == 'modified':
        logger.info(f"Event 'moved' triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}"
                    f" to {event.dest_path}")
        if event.is_directory:
            result: bool = folders.on_folder_updated(src_path=event.src_path, dest_path=event.dest_path)
        else:
            result: bool = files.on_file_updated(src_path=event.src_path, dest_path=event.dest_path)
        status = 'succeeded' if result else 'failed'
        logger.info(f"Moving {'folder' if event.is_directory else 'file'} '{os.path.basename(event.src_path)}'"
                    f" {status}.")

    elif event_type == 'deleted':
        logger.info(f"Event 'deleted' triggered for {'folder' if event.is_directory else 'file'}: {event.src_path}")
        if event.is_directory:
            result: bool = folders.on_folder_deleted(src_path=event.src_path)
        else:
            result: bool = files.on_file_deleted(src_path=event.src_path)
        status = 'succeeded' if result else 'failed'
        logger.info(f"Deleting {'folder' if event.is_directory else 'file'} '{os.path.basename(event.src_path)}'"
                    f" {status}.")
