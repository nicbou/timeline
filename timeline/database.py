from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry
from typing import Iterable
import json
import sqlite3


def get_cursor(db_path: Path):
    connection = sqlite3.connect(
        'timeline.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    return connection.cursor()


def clear_table(cursor, table_name):
    cursor.execute(f"DELETE FROM {table_name}")


def create_timeline_files_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_files (
            file_path TEXT PRIMARY KEY NOT NULL,
            size INTEGER,
            date_found TIMESTAMP NOT NULL,
            date_modified TIMESTAMP,
            checksum TEXT
        );
    ''')


def create_checksum_cache_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checksum_cache (
            file_path TEXT PRIMARY KEY NOT NULL,
            size INTEGER,
            date_modified TIMESTAMP,
            checksum TEXT
        );
    ''')


def create_timeline_entries_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_entries (
            file_path TEXT NOT NULL,
            entry_type TEXT NOT NULL,
            date_start TIMESTAMP NOT NULL,
            date_end TIMESTAMP NOT NULL,
            entry_data TEXT NOT NULL,
            FOREIGN KEY (file_path)
                REFERENCES timeline_files (file_path)
                ON UPDATE RESTRICT
                ON DELETE RESTRICT
        );
    ''')


def add_timeline_files(cursor, files: Iterable[TimelineFile]):
    cursor.executemany(
        '''
        INSERT INTO timeline_files (
            file_path,
            checksum,
            date_found,
            date_modified,
            size
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE
        SET
            checksum=excluded.checksum,
            date_found=excluded.date_found,
            date_modified=excluded.date_modified,
            size=excluded.size
        ''',
        [
            (
                str(file.file_path),
                file.checksum,
                file.date_found,
                file.date_modified,
                file.size,
            )
            for file in files
        ],
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
                str(entry.entry_type),
                entry.date_start,
                entry.date_end,
                json.dumps(entry.data)
            )
            for entry in entries
        ],
    )


def add_cached_checksum_to_timeline_files(cursor):
    """
    Checksums are expensive to calculate. We build a cache of checksums instead
    of calculating it for every file. We assume that if the path, size and mtime
    are the same, the checksum should be the same.
    """
    create_checksum_cache_table(cursor)
    cursor.execute('''
        UPDATE timeline_files
        SET checksum = cache.checksum
        FROM (
            SELECT checksum, file_path, size, date_modified
            FROM checksum_cache
        ) AS cache
        WHERE timeline_files.checksum IS NULL
        AND cache.checksum IS NOT NULL
        AND timeline_files.file_path=cache.file_path
        AND timeline_files.size=cache.size
        AND timeline_files.date_modified=cache.date_modified
    ''')
    return cursor.rowcount


def update_checksum_cache(cursor):
    create_checksum_cache_table(cursor)
    clear_table(cursor, 'checksum_cache')
    cursor.execute('''
        INSERT INTO checksum_cache (file_path, checksum, size, date_modified)
        SELECT file_path, checksum, size, date_modified FROM timeline_files
        WHERE checksum IS NOT NULL
    ''')


def get_timeline_files_without_checksum(cursor) -> list[Path]:
    cursor.execute('''
        SELECT file_path FROM timeline_files WHERE checksum IS null
    ''')
    return [Path(row[0]) for row in cursor.fetchall()]


def set_found_file_checksums(cursor, file_path_checksum_tuples):
    cursor.executemany(
        '''
        UPDATE timeline_files
        SET checksum = ?
        WHERE file_path = ?
        ''',
        [
            (checksum, str(file_path))
            for file_path, checksum in file_path_checksum_tuples
        ]
    )
