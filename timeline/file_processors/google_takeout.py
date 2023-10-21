"""
Parses data from Google Takeout exports
"""
from datetime import datetime, timezone
from pathlib import Path
from timeline.models import TimelineEntry, TimelineFile, EntryType
import json


def e7_to_decimal(e7_coordinate: int) -> float:
    return float(e7_coordinate) / 10000000


def millis_str_to_time(timestamp: str) -> datetime:
    return datetime.fromtimestamp(int(timestamp) / 1000).replace(tzinfo=timezone.utc).astimezone()


def microseconds_to_time(timestamp: int):
    return datetime.fromtimestamp(int(timestamp) / 1000000).replace(tzinfo=timezone.utc).astimezone()


def process_google_location_history(file: TimelineFile, metadata_root: Path):
    if file.file_path.name != 'Location History.json':
        return

    with file.file_path.open(encoding='utf-8') as json_file:
        json_entries = json.load(json_file)['locations']

    for json_entry in json_entries:
        entry_data = {
            'location': {
                'latitude': e7_to_decimal(json_entry['latitudeE7']),
                'longitude': e7_to_decimal(json_entry['longitudeE7']),
            },
        }

        if altitude := json_entry.get('altitude'):
            entry_data['location']['altitude'] = altitude

        yield TimelineEntry(
            file_path=file.file_path,
            checksum=file.checksum,
            entry_type=EntryType.GEOLOCATION,
            date_start=millis_str_to_time(json_entry['timestampMs']),
            date_end=None,
            data=entry_data,
        )


def process_google_browser_history(file: TimelineFile, metadata_root: Path):
    if file.file_path.name != 'BrowserHistory.json':
        return

    with file.file_path.open(encoding='utf-8') as json_file:
        json_entries = json.load(json_file)['Browser History']

    for json_entry in json_entries:
        if json_entry['page_transition'] in ('FORM_SUBMIT', 'RELOAD'):
            continue

        if json_entry['url'] == 'chrome://newtab/':
            continue

        yield TimelineEntry(
            file_path=file.file_path,
            checksum=file.checksum,
            entry_type=EntryType.BROWSING_HISTORY,
            date_start=microseconds_to_time(json_entry['time_usec']),
            date_end=None,
            data={
                'title': json_entry['title'],
                'url': json_entry['url'],
            },
        )
