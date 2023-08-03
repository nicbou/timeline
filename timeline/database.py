from datetime import date, datetime, timedelta
from pathlib import Path
from timeline.filesystem import get_checksum
from timeline.models import TimelineFile, TimelineEntry, EntryType
from typing import Iterable
import json
import sqlite3


def get_connection(db_path: Path):
    connection = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def clear_table(cursor, table_name):
    cursor.execute(f"DELETE FROM {table_name}")


def create_found_files_table(cursor):
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_entries (
            file_path TEXT NOT NULL REFERENCES timeline_files (file_path) ON DELETE CASCADE,
            entry_type TEXT NOT NULL,
            date_start TIMESTAMP NOT NULL,
            date_end TIMESTAMP,
            entry_data TEXT NOT NULL
        );
    ''')


def create_database(cursor):
    create_found_files_table(cursor)
    create_timeline_files_table(cursor)
    create_timeline_entries_table(cursor)


def add_found_files(cursor, files: Iterable[TimelineFile]):
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
                file.date_added,
                file.file_mtime,
                file.size,
            )
            for file in files
        ],
    )


def apply_cached_checksums_to_found_files(cursor):
    """
    Apply existing checksums from timeline_files to found_files. This avoids
    repeatedly calculating the same checksums.
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
    Calculate and set the checksum of all found_files that don't have one.
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
    Remove old timeline_files, add new timeline_files from found_files
    """

    # Delete timeline files that no longer exist
    cursor.execute('''
        DELETE FROM timeline_files
        WHERE file_path NOT IN (
            SELECT timeline.file_path AS file_path FROM timeline_files timeline
            INNER JOIN found_files found
                ON timeline.file_path = found.file_path
                AND timeline.checksum = found.checksum
        )
    ''')

    # Insert new found files into timeline files, updating when possible,
    # so that relationships to timeline_entries are preserved
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
    add_found_files(cursor, timeline_files)
    apply_cached_checksums_to_found_files(cursor)
    fill_missing_found_file_checksums(cursor)
    commit_found_files(cursor)


def get_unprocessed_timeline_files(cursor):
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
            date_added=row[2],
            file_mtime=row[3],
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
                entry.date_start,
                entry.date_end,
                json.dumps(entry.data)
            )
            for entry in entries
        ],
    )


def dates_with_entries(cursor):
    cursor.execute('''
        SELECT entries.date_start, entries.date_end, files.date_processed FROM timeline_entries entries
        JOIN timeline_files files ON entries.file_path=files.file_path
        ORDER BY date_start
    ''')
    dates_with_entries = {}
    for row in cursor.fetchall():
        date_start = row[0].date()
        date_end = (row[1] or row[0]).date()
        date_processed = row[2]

        days_count = (date_end - date_start).days + 1
        date_range = [
            date_start + timedelta(days=x) for x in range(days_count)
        ]
        for date_in_range in date_range:
            if date_in_range in dates_with_entries:
                dates_with_entries[date_in_range] = max(date_processed, dates_with_entries[date_in_range])
            else:
                dates_with_entries[date_in_range] = date_processed
    return dates_with_entries


def get_entries_for_date(cursor, timeline_date: date):
    cursor.execute(
        '''
            SELECT
                file_path,
                entry_type,
                date_start,
                date_end,
                entry_data
            FROM timeline_entries
            WHERE
                (date_start>=:start AND date_start<:end)
                OR (date_start<:start AND date_end>=:start)
        ''',
        {
            'start': timeline_date,
            'end': timeline_date + timedelta(days=1)
        },
    )
    for row in cursor.fetchall():
        yield TimelineEntry(
            file_path=Path(row[0]),
            entry_type=EntryType(row[1]),
            date_start=row[2],
            date_end=row[3],
            data=json.loads(row[4]),
        )


def delete_timeline_entries(cursor, file_path: Path):
    cursor.execute(
        "DELETE FROM timeline_entries WHERE file_path=?",
        [str(file_path), ]
    )


def mark_timeline_file_as_processed(cursor, file_path: Path):
    cursor.execute(
        "UPDATE timeline_files SET date_processed=? WHERE file_path=?",
        [datetime.now(), str(file_path), ]
    )
