from datetime import datetime
from pathlib import Path
from timeline.database import create_found_files_table, create_timeline_files_table, create_timeline_entries_table
from timeline.file_processors import process_text, process_markdown
from timeline.filesystem import get_files_in_paths
from timeline.models import TimelineFile, TimelineEntry
from typing import Iterable
import logging
import timeline.database as db


def get_timeline_files_in_paths(paths, includerules, ignorerules) -> Iterable[TimelineFile]:
    now = datetime.now().astimezone()
    for path in get_files_in_paths(paths, includerules, ignorerules):
        file_stats = path.stat()
        yield TimelineFile(
            file_path=path,
            checksum=None,
            date_added=now,
            file_mtime=datetime.fromtimestamp(file_stats.st_mtime),
            size=file_stats.st_size,
        )


def process_timeline_file(cursor, file: TimelineFile, metadata_path: Path) -> Iterable[TimelineEntry]:
    timeline_file_processors = [
        process_text,
        process_markdown,
    ]

    entries = []
    for process_function in timeline_file_processors:
        entries = process_function(file, entries, metadata_path)

    db.delete_timeline_entries(cursor, file.file_path)
    db.add_timeline_entries(cursor, entries)
    db.mark_timeline_file_as_processed(cursor, file.file_path)


def generate(input_paths, includerules, ignorerules, metadata_path: Path):
    metadata_path.mkdir(parents=True, exist_ok=True)
    connection = db.get_connection(metadata_path / 'timeline.db')
    cursor = connection.cursor()
    create_found_files_table(cursor)
    create_timeline_files_table(cursor)
    create_timeline_entries_table(cursor)

    timeline_files = get_timeline_files_in_paths(input_paths, includerules, ignorerules)
    db.update_file_database(cursor, timeline_files)

    file_count = 0
    for file in db.get_unprocessed_timeline_files(cursor):
        file_count += 1
        logging.info(f"Processing {file.file_path}")
        process_timeline_file(cursor, file, metadata_path)
    logging.info(f"Processed {file_count} new files")

    connection.commit()
