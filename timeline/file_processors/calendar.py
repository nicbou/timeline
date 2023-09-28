from datetime import date, datetime
from icalendar import Calendar
from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry, EntryType
from typing import Iterable


def normalize_date(date_obj: date | datetime):
    if type(date_obj) == date:
        return datetime(
            year=date_obj.year,
            month=date_obj.month,
            day=date_obj.day,
            hour=0,
            minute=0,
            second=0
        ).astimezone()
    return date_obj.astimezone()


def process_icalendar(file: TimelineFile, entries: Iterable[TimelineEntry], metadata_root: Path) -> Iterable[TimelineEntry]:
    if file.file_path.suffix.lower() in (".ical", ".ics", ".ifb", ".icalendar"):
        with file.file_path.open() as ical_file:
            calendar = Calendar.from_ical(ical_file.read())
            for event in calendar.walk('VEVENT'):
                event_data = {}

                if event.get('SUMMARY'):
                    event_data['summary'] = event.get('SUMMARY')
                if event.get('DESCRIPTION'):
                    event_data['description'] = event.get('DESCRIPTION')
                if event.get('LOCATION'):
                    event_data['location'] = {
                        'name': event.get('LOCATION')
                    }

                date_end = normalize_date(event['DTEND'].dt) if event.get('DTEND') else None

                entries.append(
                    TimelineEntry(
                        file_path=file.file_path,
                        checksum=file.checksum,
                        entry_type=EntryType.EVENT,
                        date_start=normalize_date(event['DTSTART'].dt),
                        date_end=date_end,
                        data=event_data
                    )
                )

    return entries
