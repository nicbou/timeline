from datetime import datetime
from importlib.resources import path
from pathlib import Path
from timeline.file_processors.image import process_image
from timeline.file_processors.text import process_text, process_markdown
from timeline.file_processors.gpx import process_gpx
from timeline.filesystem import get_files_in_paths
from timeline.models import TimelineFile
from timeline import templates
from typing import Iterable
import json
import logging
import timeline.database as db


logger = logging.getLogger(__name__)


def get_timeline_files_in_paths(paths, includerules, ignorerules) -> Iterable[TimelineFile]:
    now = datetime.now().astimezone()
    for file_path in get_files_in_paths(paths, includerules, ignorerules):
        file_stats = file_path.stat()
        yield TimelineFile(
            file_path=file_path,
            checksum=None,
            date_added=now,
            file_mtime=datetime.fromtimestamp(file_stats.st_mtime).astimezone(),
            size=file_stats.st_size,
        )


def process_timeline_files(cursor, input_paths, includerules, ignorerules, metadata_root: Path) -> int:
    logger.info("Updating file list")
    db.create_database(cursor)
    db.update_file_database(
        cursor, get_timeline_files_in_paths(input_paths, includerules, ignorerules)
    )

    timeline_file_processors = [
        process_text,
        process_markdown,
        process_image,
        process_gpx,
    ]

    new_file_count = 0
    for file in db.get_unprocessed_timeline_files(cursor):
        new_file_count += 1
        logger.info(f"Processing {file.file_path}")

        entries = []
        for process_function in timeline_file_processors:
            entries = process_function(file, entries, metadata_root)

        db.delete_timeline_entries(cursor, file.file_path)
        db.add_timeline_entries(cursor, entries)
        db.mark_timeline_file_as_processed(cursor, file.file_path)

    logger.info(f"Processed {new_file_count} new files")


def generate(input_paths, includerules, ignorerules, output_root: Path):
    metadata_root = output_root / 'metadata'
    metadata_root.mkdir(parents=True, exist_ok=True)
    connection = db.get_connection(metadata_root / 'timeline.db')
    cursor = connection.cursor()

    process_timeline_files(cursor, input_paths, includerules, ignorerules, metadata_root)
    connection.commit()

    templates_root = path(package=templates, resource="").__enter__()
    new_page_count = 0

    # Generate entries .json for each day
    (output_root / 'entries').mkdir(parents=True, exist_ok=True)
    for day, date_processed in db.dates_with_entries(cursor).items():
        day_json_path = output_root / 'entries' / f"{day.strftime('%Y-%m-%d')}.json"
        if not day_json_path.exists() or date_processed.timestamp() > day_json_path.stat().st_mtime:
            new_page_count += 1
            with day_json_path.open('w') as json_file:
                json.dump({
                    'entries': [entry.to_json_dict() for entry in db.get_entries_for_date(cursor, day)],
                }, json_file)

    # Copy frontend code and assets
    for file in get_files_in_paths([templates_root, ]):
        output_file = output_root / file.relative_to(templates_root)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.unlink(missing_ok=True)
        output_file.hardlink_to(file)

    logger.info(f"Generated {new_page_count} date pages")
