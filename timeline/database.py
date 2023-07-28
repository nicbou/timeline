from timeline.filesystem import get_checksum
from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry
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
            date_end TIMESTAMP NOT NULL,
            entry_data TEXT NOT NULL
        );
    ''')


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
    return cursor.rowcount


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
                str(entry.entry_type),
                entry.date_start,
                entry.date_end,
                json.dumps(entry.data)
            )
            for entry in entries
        ],
    )
