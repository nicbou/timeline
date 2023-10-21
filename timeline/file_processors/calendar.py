from datetime import date, datetime, timedelta
from icalendar import Calendar
from pathlib import Path
from timeline.database import get_connection, date_from_db
from timeline.models import TimelineFile, TimelineEntry, EntryType


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


def process_calendar_db(file: TimelineFile, metadata_root: Path):
    # Calendar database used by Calendar on MacOS. Usual location: ~/Library/Calendars/Calendar.sqlitedb

    if file.file_path.suffix.lower() != '.sqlitedb':
        return

    connection = get_connection(file.file_path)
    cursor = connection.cursor()

    cursor.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name='CalendarItem';
    ''')

    if len(cursor.fetchone()) == 0:
        return

    # Mac calendar timestamps start on 2001-01-01 (unix 978307200)
    cursor.execute('''
        SELECT
            CalendarItem.ROWID,
            summary,
            description,
            DATETIME(start_date + 978307200, 'unixepoch') as "[timestamp]",
            DATETIME(end_date + 978307200, 'unixepoch') as "[timestamp]",
            Location.title,
            Participant.email
        FROM CalendarItem
        LEFT JOIN Location ON Location.ROWID = CalendarItem.location_id
        LEFT JOIN Participant ON Participant.owner_id = CalendarItem.ROWID
        ORDER BY CalendarItem.ROWID DESC
    ''')

    # The query above returns one row per participant. Group rows by event, and create an entry for each.

    event_groups = {}

    for row in cursor.fetchall():
        event_id = row[0]

        if event_id in event_groups:
            event_groups[event_id]['data'].setdefault('participants', [])
            if row[6] not in event_groups[event_id]['data']['participants']:
                event_groups[event_id]['data']['participants'].append(row[6])
        else:
            event_groups[event_id] = {
                'date_start': date_from_db(row[3]),
                'date_end': date_from_db(row[4]) - timedelta(seconds=1),
                'data': {},
            }
            if row[1]:
                event_groups[event_id]['data']['summary'] = row[1]
            if row[2]:
                event_groups[event_id]['data']['description'] = row[2]
            if row[5]:
                event_groups[event_id]['data']['location'] = {
                    'name': row[5]
                }
            if row[6]:
                event_groups[event_id]['data']['participants'] = [row[6], ]

    for event in event_groups.values():
        yield TimelineEntry(
            file_path=file.file_path,
            checksum=file.checksum,
            entry_type=EntryType.EVENT,
            **event,
        )


def process_icalendar(file: TimelineFile, metadata_root: Path):
    if file.file_path.suffix.lower() not in (".ical", ".ics", ".ifb", ".icalendar"):
        return

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

            date_end = normalize_date(event['DTEND'].dt) - timedelta(seconds=1) if event.get('DTEND') else None

            yield TimelineEntry(
                file_path=file.file_path,
                checksum=file.checksum,
                entry_type=EntryType.EVENT,
                date_start=normalize_date(event['DTSTART'].dt),
                date_end=date_end,
                data=event_data
            )
