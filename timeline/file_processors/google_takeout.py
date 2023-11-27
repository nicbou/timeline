"""
Parses data from Google Takeout exports
"""
from datetime import datetime, timezone
from itertools import tee, islice, chain
from pathlib import Path
from timeline.models import TimelineEntry, TimelineFile, EntryType
import json


def e7_to_decimal(e7_coordinate: int) -> float:
    # -727864786 -> -72.78647 (the precision is reduced to 4 decimals, 11 metres) - xkcd.com/2170
    return float(e7_coordinate // 1000) / 10000


def millis_str_to_time(timestamp: str) -> datetime:
    return datetime.fromtimestamp(int(timestamp) / 1000).replace(tzinfo=timezone.utc).astimezone()


def microseconds_to_time(timestamp: int):
    return datetime.fromtimestamp(int(timestamp) / 1000000).replace(tzinfo=timezone.utc).astimezone()


def _process_google_location_history(file: TimelineFile, metadata_root: Path):
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


def previous_and_next(iterable):
    prevs, items, nexts = tee(iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)


def process_google_location_history(file: TimelineFile, metadata_root: Path):
    entries = _process_google_location_history(file, metadata_root)

    # Deduplicate sequential entries with the same geolocation
    for prev_entry, entry, next_entry in previous_and_next(entries):
        if prev_entry and next_entry and prev_entry.data == entry.data == next_entry.data:
            continue
        yield entry


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
