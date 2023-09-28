from datetime import datetime
from decimal import Decimal
from importlib.resources import path
from pathlib import Path
from timeline.file_processors.calendar import process_icalendar
from timeline.file_processors.gpx import process_gpx
from timeline.file_processors.image import process_image
from timeline.file_processors.n26 import process_n26_transactions
from timeline.file_processors.text import process_text, process_markdown
from timeline.filesystem import get_files_in_paths
from timeline.models import TimelineFile, EntryType
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
        process_n26_transactions,
        process_icalendar,
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


def generate_daily_entry_lists(cursor, output_path: Path):
    logger.info("Generating entry lists by day")
    # Generate entries .json for each day
    output_path.mkdir(parents=True, exist_ok=True)
    dates_with_entries = db.dates_with_entries(cursor)
    for day, date_processed in dates_with_entries.items():
        day_json_path = output_path / f"{day.strftime('%Y-%m-%d')}.json"
        with day_json_path.open('w') as json_file:
            json.dump({
                'entries': [entry.to_json_dict() for entry in db.get_entries_for_date(cursor, day)],
            }, json_file)

    logger.info(f"Generated {len(dates_with_entries)} entry lists")


def generate_financial_report(cursor, output_path: Path):
    logger.info("Generating transaction report")
    transaction_amount_by_day = {}
    for entry in db.get_entries_by_type(cursor, EntryType.TRANSACTION):
        amount = Decimal(entry.data['amount'])
        date = entry.date_start.strftime('%Y-%m-%d')
        transaction_amount_by_day.setdefault(date, Decimal('0'))
        transaction_amount_by_day[date] += amount

    for key in transaction_amount_by_day:
        transaction_amount_by_day[key] = str(transaction_amount_by_day[key])

    with output_path.open('w') as json_file:
        json.dump(transaction_amount_by_day, json_file)


def generate(input_paths, includerules, ignorerules, output_root: Path, site_url: str = '', google_maps_api_key: str = ''):
    metadata_root = output_root / 'metadata'
    metadata_root.mkdir(parents=True, exist_ok=True)
    connection = db.get_connection(metadata_root / 'timeline.db')
    cursor = connection.cursor()

    process_timeline_files(cursor, input_paths, includerules, ignorerules, metadata_root)
    connection.commit()

    templates_root = path(package=templates, resource="").__enter__()

    generate_daily_entry_lists(cursor, output_root / 'entries')
    generate_financial_report(cursor, output_root / 'entries' / 'finances.json')

    # Copy frontend code and assets
    for file in get_files_in_paths([templates_root, ]):
        output_file = output_root / file.relative_to(templates_root)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.unlink(missing_ok=True)
        output_file.hardlink_to(file)

    # Generate .js config file
    js_config_path = output_root / 'js/config.js'
    with js_config_path.open() as config_file:
        config = (
            config_file.read()
            .replace("${GOOGLE_MAPS_API_KEY}", google_maps_api_key)
            .replace("${SITE_URL}", site_url)
        )
    js_config_path.unlink()  # This is a hard link to the original. Remove it and create a copy of it.
    with js_config_path.open('w') as config_file:
        config_file.write(config)
