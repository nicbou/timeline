from datetime import datetime, timedelta
from decimal import Decimal
from importlib.resources import files
from itertools import chain
from pathlib import Path
from timeline.file_processors.balance import process_balance_list
from timeline.file_processors.calendar import process_icalendar, process_calendar_db
from timeline.file_processors.degiro import process_degiro_transactions
from timeline.post_processors.geo import add_reverse_geolocation
from timeline.file_processors.google_takeout import process_google_browser_history, process_google_location_history
from timeline.file_processors.gpx import process_gpx
from timeline.file_processors.image import process_image
from timeline.file_processors.kontist import process_kontist_transactions
from timeline.file_processors.n26 import process_n26_transactions
from timeline.file_processors.pdf import process_pdf
from timeline.file_processors.search import process_search_logs
from timeline.file_processors.text import process_text, process_markdown
from timeline.file_processors.video import process_video, can_process_videos
from timeline.filesystem import get_files_in_paths
from timeline.models import TimelineFile, EntryType
from typing import Iterable
import json
import logging
import shutil
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
        process_balance_list,
        process_calendar_db,
        process_degiro_transactions,
        process_google_browser_history,
        process_google_location_history,
        process_gpx,
        process_icalendar,
        process_image,
        process_kontist_transactions,
        process_markdown,
        process_n26_transactions,
        process_pdf,
        process_search_logs,
        process_text,
    ]

    timeline_post_processors = [
        add_reverse_geolocation,
    ]

    if can_process_videos():
        timeline_file_processors.append(process_video)
    else:
        logging.warning(
            'ffmpeg is not installed. Videos will not be processed.'
        )

    new_file_count = 0
    for file in db.get_unprocessed_timeline_files(cursor):
        new_file_count += 1
        logger.info(f"Processing {file.file_path}")

        # Chain all the file processors together
        entry_generator = chain(*[
            process_function(file, metadata_root) for process_function in timeline_file_processors
        ])

        # Apply each post processor to the entries from entry_generator
        for post_process_function in timeline_post_processors:
            entry_generator = map(post_process_function, entry_generator)

        db.delete_timeline_entries(cursor, file.file_path)
        db.add_timeline_entries(cursor, entry_generator)
        db.mark_timeline_file_as_processed(cursor, file.file_path)

    logger.info(f"Processed {new_file_count} new files")


def generate_daily_entry_lists(cursor, output_path: Path):
    logger.info("Generating entry lists by day")
    # Generate entries .json for each day
    # Only generate missing days or days that have changes to speed things up
    output_path.mkdir(parents=True, exist_ok=True)

    days_to_update, days_to_delete = db.dates_with_changes(cursor)

    days_updated = 0
    for day, date_last_changed in days_to_update.items():
        day_json_path = output_path / f"{day.strftime('%Y-%m-%d')}.json"

        if not day_json_path.exists() or date_last_changed.timestamp() > day_json_path.stat().st_mtime:
            days_updated += 1
            with day_json_path.open('w') as json_file:
                json.dump({
                    'entries': [entry.to_json_dict() for entry in db.get_entries_for_date(cursor, day)],
                }, json_file)

    for day in days_to_delete:
        day_json_path = output_path / f"{day.strftime('%Y-%m-%d')}.json"
        day_json_path.unlink(missing_ok=True)

    logger.info(f"Generated entry lists for {len(days_to_update)} days: updated {days_updated}, removed {len(days_to_delete)}")


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Or float(obj) if you prefer float representation
        return super(DecimalEncoder, self).default(obj)


def generate_financial_report(cursor, output_path: Path):
    logger.info("Generating financial report")

    # List the total amount of transactions for each day
    transaction_amount_by_day = {}
    for entry in db.get_entries_by_type(cursor, EntryType.TRANSACTION):
        amount = Decimal(entry.data['amount'])
        date_str = entry.date_start.strftime('%Y-%m-%d')
        transaction_amount_by_day.setdefault(date_str, Decimal('0'))
        transaction_amount_by_day[date_str] += amount

    balances_by_date = {}
    first_balance_date = None  # The first recorded account balance. There is no history before that.
    for entry in db.get_entries_by_type(cursor, EntryType.BALANCE):
        first_balance_date = first_balance_date or entry.date_start.date()
        date_str = entry.date_start.strftime('%Y-%m-%d')
        account = entry.data['account']

        balances_by_date.setdefault(date_str, {})
        balances_by_date[date_str][account] = {
            'amount': Decimal(entry.data['amount']),
            'date': date_str,
        }

    current_date = first_balance_date
    while current_date < datetime.now().date():
        previous_balance = balances_by_date[current_date.strftime('%Y-%m-%d')].copy()
        current_date += timedelta(days=1)
        current_date_str = current_date.strftime('%Y-%m-%d')
        current_balance = balances_by_date.get(current_date_str, {})
        balances_by_date[current_date_str] = previous_balance
        balances_by_date[current_date_str].update(current_balance)

    for current_date_str in balances_by_date:
        balances_by_date[current_date_str]['total'] = {
            'amount': sum([b['amount'] for b in balances_by_date[current_date_str].values() ]),
            'date': max(b['date'] for b in balances_by_date[current_date_str].values()),
            'transactionAmount': transaction_amount_by_day.get(current_date_str, Decimal(0))
        }

    with output_path.open('w') as json_file:
        json.dump(
            balances_by_date,
            json_file,
            cls=DecimalEncoder
        )


def generate(input_paths, includerules, ignorerules, output_root: Path, site_url: str = '', google_maps_api_key: str = '', live_templates: bool = False):
    logging.info(f'Building timeline, saving it to {str(output_root)}')

    metadata_root = output_root / 'metadata'
    metadata_root.mkdir(parents=True, exist_ok=True)

    connection = db.get_connection(metadata_root / 'timeline.db')
    cursor = connection.cursor()

    process_timeline_files(cursor, input_paths, includerules, ignorerules, metadata_root)
    connection.commit()

    templates_root = files("timeline") / 'templates'

    # Copy frontend code and assets
    for file in get_files_in_paths([templates_root, ]):
        output_file = output_root / file.relative_to(templates_root)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.unlink(missing_ok=True)
        if live_templates:
            output_file.symlink_to(file)
        else:
            shutil.copy(file, output_file)

    # Generate .js config file
    js_config_path = output_root / 'js/config.js'
    with js_config_path.open() as config_file:
        config = (
            config_file.read()
            .replace("${GOOGLE_MAPS_API_KEY}", google_maps_api_key or '')
            .replace("${SITE_URL}", site_url)
        )
    js_config_path.unlink()  # This is a hard link to the original. Remove it and create a copy of it.
    with js_config_path.open('w') as config_file:
        config_file.write(config)

    generate_daily_entry_lists(cursor, output_root / 'entries')
    generate_financial_report(cursor, output_root / 'entries' / 'finances.json')