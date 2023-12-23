from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from timeline.filesystem import get_checksum
from timeline.models import TimelineFile, TimelineEntry, EntryType
from typing import Dict, Iterable, Set, Tuple
import json
import sqlite3


def get_connection(db_path: Path):
    connection = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def db_date(date: datetime) -> datetime:
    """
    Converts a timezone-aware datetime to UTC and removes timezone information.
    Sqlite does not support timezones properly.
    """
    return date.astimezone(timezone.utc).replace(tzinfo=None) if date else None


def date_from_db(date: datetime) -> datetime:
    """
    Converts a date from the database into a timezone-aware datetime object.
    """
    return date.replace(tzinfo=timezone.utc).astimezone() if date else None  # Local timezone


def days_in_range(start: datetime, end: datetime) -> Iterable[date]:
    date_start = start.date()
    days_count = (end.date() - date_start).days + 1
    return [
        date_start + timedelta(days=x) for x in range(days_count)
    ]


def clear_table(cursor, table_name):
    cursor.execute(f"DELETE FROM {table_name}")


def create_found_files_table(cursor):
    # All files currently found on the filesystem
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS found_files (
            file_path TEXT PRIMARY KEY NOT NULL,
            size INTEGER,
            date_added TIMESTAMP NOT NULL,
            file_mtime TIMESTAMP,
            checksum TEXT
        );
    ''')


def create_timeline_files_table(cursor):
    # All files currently included on the timeline
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_files (
            file_path TEXT PRIMARY KEY NOT NULL,
            size INTEGER,
            date_added TIMESTAMP NOT NULL,
            date_processed TIMESTAMP,
            file_mtime TIMESTAMP,
            checksum TEXT
        );
    ''')


def create_timeline_entries_table(cursor):
    # All entries on the timeline
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_entries (
            file_path TEXT NOT NULL REFERENCES timeline_files (file_path) ON DELETE CASCADE,
            entry_type TEXT NOT NULL,
            date_start TIMESTAMP NOT NULL,
            date_end TIMESTAMP,
            entry_data TEXT NOT NULL
        );
    ''')


def create_dates_with_deleted_entries_table(cursor):
    # All days where a timeline entry was deleted, and the date of the last
    # deletion.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dates_with_deleted_entries (
            timeline_date TIMESTAMP PRIMARY KEY NOT NULL,
            date_last_deletion TIMESTAMP NOT NULL
        );
    ''')


def create_database(cursor):
    create_found_files_table(cursor)
    create_timeline_files_table(cursor)
    create_timeline_entries_table(cursor)
    create_dates_with_deleted_entries_table(cursor)


def add_found_files(cursor, files: Iterable[TimelineFile]):
    """
    Add files found on a filesystem to the database.

    The files are added to the temporary found_files table.
    """
    cursor.executemany(
        '''
        INSERT INTO found_files (
            file_path,
            checksum,
            date_added,
            file_mtime,
            size
        )
        VALUES (?, ?, ?, ?, ?)
        ''',
        [
            (
                str(file.file_path),
                file.checksum,
                db_date(file.date_added),
                db_date(file.file_mtime),
                file.size,
            )
            for file in files
        ],
    )


def apply_cached_checksums_to_found_files(cursor):
    """
    Apply checksums from the timeline_files table to files in the found_files
    table. This is faster than recalculating the checksum for files that have
    not changed since the last pass.
    """
    cursor.execute('''
        UPDATE found_files
        SET checksum = timeline.checksum
        FROM (
            SELECT checksum, file_path, size, file_mtime
            FROM timeline_files
        ) AS timeline
        WHERE
            found_files.checksum IS NULL
            AND timeline.checksum IS NOT NULL
            AND found_files.file_path=timeline.file_path
            AND found_files.size=timeline.size
            AND found_files.file_mtime=timeline.file_mtime
    ''')


def fill_missing_found_file_checksums(cursor):
    """
    Calculate the checksum for all files in the found_files table that don't
    have a checksum set.
    """
    cursor.execute('''
        SELECT file_path FROM found_files WHERE checksum IS NULL
    ''')

    cursor.executemany(
        '''
        UPDATE found_files
        SET checksum = :checksum
        WHERE file_path = :file_path
        ''',
        [
            {
                'checksum': get_checksum(Path(row[0])),
                'file_path': row[0],
            }
            for row in cursor.fetchall()
        ]
    )


def commit_found_files(cursor):
    """
    Sync the found_files and timeline_files tables.

    The new found_files are added. The missing timeline_files are removed.

    A table of dates with the date of the last delete entries is generated.
    """

    # Select timeline_files that no longer exist in the list of found_files
    cursor.executescript('''
        DROP VIEW IF EXISTS existing_files_to_preserve;
        CREATE VIEW existing_files_to_preserve AS
            SELECT timeline.file_path AS file_path FROM timeline_files timeline
            INNER JOIN found_files found
                ON timeline.file_path = found.file_path
                AND timeline.checksum = found.checksum
    ''')
    cursor.executescript('''
        DROP VIEW IF EXISTS timeline_files_to_delete;
        CREATE VIEW timeline_files_to_delete AS
            SELECT file_path FROM timeline_files
            WHERE file_path NOT IN existing_files_to_preserve
    ''')

    # Select a list of entries to be deleted
    cursor.execute('''
        SELECT date_start, date_end FROM timeline_entries WHERE file_path IN timeline_files_to_delete
    ''')

    # Update the table of dates with deleted entries
    now = datetime.now()
    dates_with_deleted_entries = {}
    for row in cursor.fetchall():
        date_start = date_from_db(row[0])
        date_end = date_from_db(row[1]) if row[1] else date_start
        for day in days_in_range(date_start, date_end):
            dates_with_deleted_entries[day] = now

    cursor.executemany(
        '''
        INSERT INTO dates_with_deleted_entries (
            timeline_date, date_last_deletion
        )
        VALUES (?, ?)
        ON CONFLICT (timeline_date) DO UPDATE
            SET
                timeline_date = excluded.timeline_date,
                date_last_deletion = date_last_deletion
        ''',
        [
            (
                db_date(datetime.combine(timeline_date, datetime.min.time())),
                db_date(date_last_deletion),
            )
            for timeline_date, date_last_deletion in dates_with_deleted_entries.items()
        ]
    )

    # Delete the old timeline_files
    cursor.execute('''
        DELETE FROM timeline_files WHERE file_path IN timeline_files_to_delete
    ''')

    # Insert the new timeline_files from found_files. Update existing rows when possible.
    cursor.execute('''
        INSERT INTO timeline_files (
            file_path,
            checksum,
            date_added,
            file_mtime,
            size,
            date_processed
        )
        SELECT file_path, checksum, date_added, file_mtime, size, NULL FROM found_files WHERE true
        ON CONFLICT (file_path) DO UPDATE
            SET
                checksum = excluded.checksum,
                date_added = excluded.date_added,
                file_mtime = excluded.file_mtime,
                date_processed = date_processed
    ''')

    clear_table(cursor, 'found_files')


def update_file_database(cursor, timeline_files: Iterable[TimelineFile]):
    """
    Syncs the list of files in the database with the actual list of files on the
    filesystem. The result is an up-to-date timeline_files table.
    """
    clear_table(cursor, 'found_files')
    add_found_files(cursor, timeline_files)
    apply_cached_checksums_to_found_files(cursor)
    fill_missing_found_file_checksums(cursor)
    commit_found_files(cursor)


def get_unprocessed_timeline_files(cursor) -> Iterable[TimelineFile]:
    """
    Returns a list of unprocessed files. These are files for which entries,
    thumbnails, previews and other metadata was not yet generated.
    """
    cursor.execute('''
        SELECT
            file_path,
            checksum,
            date_added,
            file_mtime,
            size,
            date_processed
        FROM timeline_files WHERE date_processed IS NULL
    ''')
    for row in cursor.fetchall():
        yield TimelineFile(
            file_path=Path(row[0]),
            checksum=row[1],
            date_added=date_from_db(row[2]),
            file_mtime=date_from_db(row[3]),
            size=row[4]
        )


def add_timeline_entries(cursor, entries: Iterable[TimelineEntry]):
    cursor.executemany(
        '''
        INSERT INTO timeline_entries (
            file_path,
            entry_type,
            date_start,
            date_end,
            entry_data
        )
        VALUES (?, ?, ?, ?, ?)
        ''',
        [
            (
                str(entry.file_path),
                entry.entry_type.value,
                db_date(entry.date_start),
                db_date(entry.date_end),
                json.dumps(entry.data)
            )
            for entry in entries
        ],
    )


def dates_with_changes(cursor) -> Tuple[Dict[datetime, datetime], Set[datetime]]:
    """Summary
    Returns:
        A tuple with two values:
            1. days_to_update:
                The keys are dates that have entries.
                The values are the date of the latest change to entries on that
                day. A change is an entry that was processed or deleted.
            2. days_to_delete:
                A set of dates that have deleted entries and no entries left.
    """
    days_to_update = {}
    days_to_delete = set()

    # Days with entries
    cursor.execute('''
        SELECT entries.date_start, entries.date_end, files.date_processed FROM timeline_entries entries
        JOIN timeline_files files ON entries.file_path=files.file_path
        ORDER BY date_start
    ''')
    for entry_row in cursor.fetchall():
        date_start = date_from_db(entry_row[0])
        date_end = date_from_db(entry_row[1]) if entry_row[1] else date_start
        date_processed = date_from_db(entry_row[2])
        for day in days_in_range(date_start, date_end):
            if day in days_to_update:
                days_to_update[day] = max(date_processed, days_to_update[day])
            else:
                days_to_update[day] = date_processed

    # Days with deleted entries
    cursor.execute('''
        SELECT timeline_date, date_last_deletion
        FROM dates_with_deleted_entries
    ''')
    for deleted_entry_row in cursor.fetchall():
        day = date_from_db(deleted_entry_row[0]).date()
        last_deletion_date = date_from_db(deleted_entry_row[1])

        # Day has entries. Update date of latest change.
        if day in days_to_update:
            days_to_update[day] = max(last_deletion_date, days_to_update[day])
        # Day has no entries, only deleted entries. Add to days to delete.
        else:
            days_to_delete.add(day)

    return days_to_update, days_to_delete


def get_entries_for_date(cursor, timeline_date: date):
    tz_aware_timeline_date = datetime(timeline_date.year, timeline_date.month, timeline_date.day).astimezone()
    cursor.execute(
        '''
            SELECT
                entries.file_path,
                files.checksum,
                entry_type,
                date_start,
                date_end,
                entry_data
            FROM timeline_entries entries
            INNER JOIN timeline_files files
                ON entries.file_path = files.file_path
            WHERE
                (date_start>=:start AND date_start<:end)
                OR (date_start<:start AND date_end>=:start)
        ''',
        {
            'start': db_date(tz_aware_timeline_date),
            'end': db_date(tz_aware_timeline_date + timedelta(days=1)),
        },
    )
    for row in cursor.fetchall():
        yield TimelineEntry(
            file_path=Path(row[0]),
            checksum=row[1],
            entry_type=EntryType(row[2]),
            date_start=date_from_db(row[3]),
            date_end=date_from_db(row[4]),
            data=json.loads(row[5]),
        )


def get_entries_by_type(cursor, entry_type: EntryType):
    cursor.execute(
        '''
            SELECT
                entries.file_path,
                files.checksum,
                entry_type,
                date_start,
                date_end,
                entry_data
            FROM timeline_entries entries
            INNER JOIN timeline_files files
                ON entries.file_path = files.file_path
            WHERE
                entry_type=:type
        ''',
        {
            'type': entry_type.value
        },
    )
    for row in cursor.fetchall():
        yield TimelineEntry(
            file_path=Path(row[0]),
            checksum=row[1],
            entry_type=EntryType(row[2]),
            date_start=date_from_db(row[3]),
            date_end=date_from_db(row[4]),
            data=json.loads(row[5]),
        )


def delete_timeline_entries(cursor, file_path: Path):
    cursor.execute(
        "DELETE FROM timeline_entries WHERE file_path=?",
        [str(file_path), ]
    )


def mark_timeline_file_as_processed(cursor, file_path: Path):
    cursor.execute(
        "UPDATE timeline_files SET date_processed=? WHERE file_path=?",
        [
            db_date(datetime.now()),
            str(file_path),
        ]
    )
