from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry, EntryType
from datetime import datetime, timezone
import codecs
import csv


def process_search_logs(file: TimelineFile, metadata_root: Path):
    if not file.file_path.name.lower().endswith('.searches.csv'):
        return

    for line in csv.DictReader(codecs.iterdecode(file.file_path.open('rb'), 'utf-8'), delimiter=',', quotechar='"'):
        search_date = datetime.strptime(line['date'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).astimezone()
        yield TimelineEntry(
            file_path=file.file_path,
            checksum=file.checksum,
            entry_type=EntryType.SEARCH,
            date_start=search_date,
            date_end=None,
            data={
                'query': line['query'],
                'url': line['url'],
            }
        )
