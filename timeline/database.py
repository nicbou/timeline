from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from timeline.filesystem import get_checksum
from timeline.models import TimelineFile, TimelineEntry, EntryType
from typing import Iterable
import json
import sqlite3


sqlite3.register_adapter(datetime, lambda val: val.isoformat())
sqlite3.register_converter(
    "timestamp", lambda val: datetime.fromisoformat(val.decode())
)


def get_connection(db_path: Path):
    connection = sqlite3.connect(
        db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def to_db_datetime(python_date: datetime | date) -> datetime:
    """
    Converts a timezone-aware datetime to UTC and removes timezone information.
    Sqlite does not support timezones properly.
    """
    if not isinstance(python_date, datetime):
        python_date = datetime.combine(python_date, time.min)
    return python_date.astimezone(timezone.utc).replace(tzinfo=None)


def datetime_from_db(date: datetime) -> datetime:
    """
    Converts a date from the database into a timezone-aware datetime object.
    """
    return date.replace(tzinfo=timezone.utc).astimezone()  # Local timezone


def days_in_range(start: datetime, end: datetime) -> Iterable[date]:
    date_start = start.date()
    days_count = (end.date() - date_start).days + 1
    return [date_start + timedelta(days=x) for x in range(days_count)]


def clear_table(cursor, table_name):
    cursor.execute(f"DELETE FROM {table_name}")


def create_found_files_table(cursor):
    # All files currently found on the filesystem
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS found_files (
            file_path TEXT PRIMARY KEY NOT NULL,
            size INTEGER,
            date_added TIMESTAMP NOT NULL,
            file_mtime TIMESTAMP,
            checksum TEXT
        );
    """)


def create_timeline_files_table(cursor):
    # All files currently included on the timeline
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_files (
            file_path TEXT PRIMARY KEY NOT NULL,
            size INTEGER,
            date_added TIMESTAMP NOT NULL,
            date_processed TIMESTAMP,
            file_mtime TIMESTAMP,
            checksum TEXT
        );
    """)


def create_timeline_entries_table(cursor):
    # All entries on the timeline
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_entries (
            file_path TEXT NOT NULL REFERENCES timeline_files (file_path) ON DELETE CASCADE,
            entry_type TEXT NOT NULL,
            date_start TIMESTAMP NOT NULL,
            date_end TIMESTAMP,
            entry_data TEXT NOT NULL
        );
    """)


def create_dates_with_changes_table(cursor):
    # All days where a timeline entry was created or updated
    cursor.execute("""
        CREATE TEMP TABLE IF NOT EXISTS dates_with_changes (
            timeline_date TIMESTAMP PRIMARY KEY NOT NULL
        )
    """)


def create_database(cursor):
    create_found_files_table(cursor)
    create_timeline_files_table(cursor)
    create_timeline_entries_table(cursor)
    create_dates_with_changes_table(cursor)


def add_found_files(cursor, files: Iterable[TimelineFile]):
    """
    Add files found on the filesystem to the database.

    The files are added to the temporary found_files table.
    """
    cursor.executemany(
        """
        INSERT INTO found_files (
            file_path,
            checksum,
            date_added,
            file_mtime,
            size
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                str(file.file_path),
                file.checksum,
                to_db_datetime(file.date_added),
                to_db_datetime(file.file_mtime),
                file.size,
            )
            for file in files
        ],
    )


def apply_cached_checksums_to_found_files(cursor):
    """
    Copy the checksums from the timeline_files table to the found_files table.
    It avoids recalculating the checksum for files that have not changed since
    the last pass.
    """
    cursor.execute("""
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
    """)


def fill_missing_found_file_checksums(cursor):
    """
    Calculate the checksum for all files in the found_files table that don't
    have a checksum.
    """
    cursor.execute("""
        SELECT file_path FROM found_files WHERE checksum IS NULL
    """)

    cursor.executemany(
        """
        UPDATE found_files
        SET checksum = :checksum
        WHERE file_path = :file_path
        """,
        [
            {
                "checksum": get_checksum(Path(row[0])),
                "file_path": row[0],
            }
            for row in cursor.fetchall()
        ],
    )


def commit_found_files(cursor):
    """
    Sync the found_files and timeline_files tables.

    Delete entries related to missing files.

    Update dates_with_changes with the dates of the deleted entries.
    """

    cursor.executescript("""
        DROP VIEW IF EXISTS deleted_timeline_files;
        CREATE VIEW deleted_timeline_files AS
            SELECT file_path FROM timeline_files
            WHERE file_path NOT IN (SELECT file_path FROM found_files)
    """)

    deleted_timeline_entries = cursor.execute("""
        SELECT date_start, date_end FROM timeline_entries WHERE file_path IN deleted_timeline_files
    """).fetchall()

    dates_with_deleted_entries = set()
    for date_start, date_end in deleted_timeline_entries:
        date_start = datetime_from_db(date_start)
        date_end = datetime_from_db(date_end) if date_end else date_start
        for day in days_in_range(date_start, date_end):
            dates_with_deleted_entries.add(day)

    # Mark the dates with deleted entries as modified
    cursor.executemany(
        """
        INSERT INTO dates_with_changes (timeline_date) VALUES (?)
        ON CONFLICT DO NOTHING;
        """,
        [
            [
                to_db_datetime(datetime.combine(d, datetime.min.time())),
            ]
            for d in dates_with_deleted_entries
        ],
    )

    # Delete timeline_files that are not in found_files
    cursor.executescript("""
        DELETE FROM timeline_files WHERE file_path IN deleted_timeline_files;
        DROP VIEW deleted_timeline_files;
    """)

    # Insert found_files into timeline_files, update existing timeline_files.
    # New/changed files have their date_processed set to NULL.
    cursor.execute("""
        INSERT INTO timeline_files (file_path, checksum, date_added, file_mtime, size, date_processed)
        SELECT file_path, checksum, date_added, file_mtime, size, NULL FROM found_files WHERE true
        ON CONFLICT (file_path) DO UPDATE
            SET
                checksum = excluded.checksum,
                date_added = excluded.date_added,
                file_mtime = excluded.file_mtime,
                size = excluded.size,
                date_processed = CASE
                    WHEN timeline_files.checksum != excluded.checksum THEN NULL
                    ELSE timeline_files.date_processed
                END
    """)

    clear_table(cursor, "found_files")


def update_file_database(cursor, timeline_files: Iterable[TimelineFile]):
    """
    Syncs the list of files in the database with the actual list of files on the
    filesystem. The result is an up-to-date timeline_files table.
    """
    clear_table(cursor, "found_files")
    add_found_files(cursor, timeline_files)
    apply_cached_checksums_to_found_files(cursor)
    fill_missing_found_file_checksums(cursor)
    commit_found_files(cursor)


def get_unprocessed_timeline_files(cursor) -> Iterable[TimelineFile]:
    """
    Returns a list of unprocessed files. These are files for which entries,
    thumbnails, previews and other metadata was not yet generated.
    """
    cursor.execute("""
        SELECT
            file_path,
            checksum,
            date_added,
            file_mtime,
            size,
            date_processed
        FROM timeline_files WHERE date_processed IS NULL
    """)
    for row in cursor.fetchall():
        yield TimelineFile(
            file_path=Path(row[0]),
            checksum=row[1],
            date_added=datetime_from_db(row[2]),
            file_mtime=datetime_from_db(row[3]),
            size=row[4],
        )


def add_timeline_entries(cursor, entries: Iterable[TimelineEntry]):
    cursor.executemany(
        """
        INSERT INTO timeline_entries (
            file_path,
            entry_type,
            date_start,
            date_end,
            entry_data
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                str(entry.file_path),
                entry.entry_type.value,
                to_db_datetime(entry.date_start),
                to_db_datetime(entry.date_end) if entry.date_end else None,
                json.dumps(entry.data),
            )
            for entry in entries
        ],
    )


def update_timeline_entries_for_file(
    cursor, timeline_file: Path, new_entries: Iterable[TimelineEntry]
) -> None:
    """
    Update a file's entries in the timeline. Create/update entries that changed and delete obsolete ones.
    """
    cursor.execute(
        "SELECT entry_type, date_start, date_end, entry_data FROM timeline_entries WHERE file_path=?",
        [str(timeline_file)],
    )
    previous_entries = {row for row in cursor.fetchall()}

    current_entries = {
        (
            entry.entry_type.value,
            to_db_datetime(entry.date_start),
            to_db_datetime(entry.date_end) if entry.date_end else None,
            json.dumps(entry.data),
        )
        for entry in new_entries
    }

    entries_to_remove = previous_entries - current_entries
    entries_to_add = current_entries - previous_entries

    dates_with_changes: set[date] = set()

    # Delete obsolete entries
    for entry_type, date_start, date_end, entry_data in entries_to_remove:
        cursor.execute(
            """
            DELETE FROM timeline_entries
            WHERE file_path=? AND entry_type=? AND date_start=? AND entry_data=?
            """,
            [str(timeline_file), entry_type, date_start, entry_data],
        )
        entry_start = datetime_from_db(date_start)
        entry_end = datetime_from_db(date_end) if date_end else entry_start
        dates_with_changes.update(days_in_range(entry_start, entry_end))

    # Add/update new entries
    for entry_type, date_start, date_end, entry_data in entries_to_add:
        cursor.execute(
            """
            INSERT INTO timeline_entries (file_path, entry_type, date_start, date_end, entry_data)
            VALUES (?, ?, ?, ?, ?)
            """,
            [str(timeline_file), entry_type, date_start, date_end, entry_data],
        )
        entry_start = datetime_from_db(date_start)
        entry_end = datetime_from_db(date_end) if date_end else entry_start
        dates_with_changes.update(days_in_range(entry_start, entry_end))

    # Log all dates that have entry changes
    cursor.executemany(
        "INSERT OR IGNORE INTO dates_with_changes (timeline_date) VALUES (?)",
        [[to_db_datetime(d)] for d in dates_with_changes],
    )


def dates_with_changes(cursor) -> dict[date, datetime]:
    """
    Returns a tuple with two values:
        1. days_to_update (dict):
            Keys: dates where entries changed this run.
            Value: timestamp of the change.
        2. days_to_delete (set):
            Dates that have no entries left, because they were all deleted.
    """
    return {
        datetime_from_db(row[0]).date(): datetime.now().astimezone()
        for row in cursor.execute(
            "SELECT timeline_date FROM dates_with_changes"
        ).fetchall()
    }


def get_entries_for_date(cursor, timeline_date: date):
    tz_aware_timeline_date = datetime(
        timeline_date.year, timeline_date.month, timeline_date.day
    ).astimezone()
    cursor.execute(
        """
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
        """,
        {
            "start": to_db_datetime(tz_aware_timeline_date),
            "end": to_db_datetime(tz_aware_timeline_date + timedelta(days=1)),
        },
    )
    for row in cursor.fetchall():
        yield TimelineEntry(
            file_path=Path(row[0]),
            checksum=row[1],
            entry_type=EntryType(row[2]),
            date_start=datetime_from_db(row[3]),
            date_end=datetime_from_db(row[4]) if row[4] else None,
            data=json.loads(row[5]),
        )


def get_entries_by_type(cursor, entry_type: EntryType):
    cursor.execute(
        """
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
        """,
        {"type": entry_type.value},
    )
    for row in cursor.fetchall():
        yield TimelineEntry(
            file_path=Path(row[0]),
            checksum=row[1],
            entry_type=EntryType(row[2]),
            date_start=datetime_from_db(row[3]),
            date_end=datetime_from_db(row[4]) if row[4] else None,
            data=json.loads(row[5]),
        )


def delete_timeline_entries(cursor, file_path: Path):
    cursor.execute(
        "DELETE FROM timeline_entries WHERE file_path=?",
        [
            str(file_path),
        ],
    )


def mark_timeline_file_as_processed(cursor, file_path: Path):
    cursor.execute(
        "UPDATE timeline_files SET date_processed=? WHERE file_path=?",
        [
            to_db_datetime(datetime.now()),
            str(file_path),
        ],
    )
