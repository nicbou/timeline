from timeline.database import create_timeline_files_table, add_found_files, clear_table, \
    apply_cached_checksums_to_found_files, commit_found_files, fill_missing_found_file_checksums, \
    create_timeline_entries_table, add_timeline_entries, create_found_files_table
from timeline.filesystem import get_checksum
from timeline.models import TimelineEntry, TimelineFile, EntryType
from datetime import datetime, timedelta
from pathlib import Path
import json
import pytest
import sqlite3


def fake_found_files(tmp_path):
    now = datetime.now().astimezone()
    yesterday = now - timedelta(days=1)

    file_paths = [
        tmp_path / 'file_a.text',
        tmp_path / 'file_b.text',
        tmp_path / 'file_c.text',
    ]

    dates_modified = [
        now,
        now,
        yesterday,
    ]

    for index, file_path in enumerate(file_paths):
        with file_path.open('w') as file:
            file.write('Hello file!' * (index + 1))
        checksum = get_checksum(file_path)

        yield TimelineFile(
            file_path=file_path,
            checksum=checksum,
            date_added=now,
            size=file_path.stat().st_size,
            file_mtime=dates_modified[index],
        )


def fake_timeline_entries():
    now = datetime.now().astimezone()
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)

    return [
        TimelineEntry(
            file_path=Path('/path/to/file_a.txt'),
            entry_type=EntryType.IMAGE,
            date_start=last_month,
            date_end=last_month,
            data={
                'size': [640, 480],
                'location': [52.44, 49.44],
                'description': 'A man sitting on a treestump'
            },
        ),
        TimelineEntry(
            file_path=Path('/path/to/file_b.txt'),
            entry_type=EntryType.MARKDOWN,
            date_start=last_month,
            date_end=last_week,
            data={
                'content': '# This is my journal\n\nIt was a dark and stormy night...'
            },
        ),
        TimelineEntry(
            file_path=Path('/path/to/file_b.txt'),
            entry_type=EntryType.MARKDOWN,
            date_start=last_week,
            date_end=now,
            data={
                'content': 'All quiet on the western front'
            },
        ),
    ]


def assert_result_count(cursor, query, count):
    cursor.execute(query)
    assert cursor.fetchone()[0] == count


@pytest.fixture
def cursor():
    connection = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = connection.cursor()
    create_found_files_table(cursor)
    create_timeline_files_table(cursor)
    create_timeline_entries_table(cursor)
    yield cursor
    connection.close()


def test_clear_table(cursor, tmp_path):
    add_found_files(cursor, fake_found_files(tmp_path))
    assert_result_count(cursor, 'SELECT COUNT(*) FROM found_files', 3)
    clear_table(cursor, 'found_files')
    cursor.execute("SELECT * FROM found_files")
    assert_result_count(cursor, 'SELECT COUNT(*) FROM found_files', 0)


def test_add_found_files(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    add_found_files(cursor, found_files)

    cursor.execute("SELECT file_path, checksum, date_added, size, file_mtime FROM found_files")
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        assert row == (
            str(found_files[index].file_path),
            found_files[index].checksum,
            found_files[index].date_added.replace(tzinfo=None),
            found_files[index].size,
            found_files[index].file_mtime.replace(tzinfo=None),
        )


def test_add_found_files_multiple_times(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    add_found_files(cursor, found_files)
    new_file = TimelineFile(
        file_path=found_files[0].file_path,
        checksum=None,
        date_added=datetime.now(),
        size=999,
        file_mtime=datetime.now(),
    )
    found_files[0] = new_file

    with pytest.raises(sqlite3.IntegrityError):
        add_found_files(cursor, [new_file, ])


def test_apply_cached_checksums_to_found_files(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))

    add_found_files(cursor, found_files)
    commit_found_files(cursor)

    clear_table(cursor, 'found_files')
    add_found_files(cursor, found_files)
    cursor.execute("UPDATE found_files SET checksum=null")

    apply_cached_checksums_to_found_files(cursor)

    # Checksum is set to the cached value
    cursor.execute("SELECT file_path, checksum FROM found_files")
    assert sorted(cursor.fetchall()) == sorted([
        (str(file.file_path), file.checksum) for file in found_files
    ])


def test_apply_cached_checksums_to_found_files_file_has_changed(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))

    add_found_files(cursor, found_files)
    commit_found_files(cursor)

    clear_table(cursor, 'found_files')
    found_files = list(fake_found_files(tmp_path))  # New, different date_updated
    add_found_files(cursor, found_files)
    cursor.execute("UPDATE found_files SET checksum=null")

    apply_cached_checksums_to_found_files(cursor)

    # Checksum is not set to the cached value, because the modified date differes
    cursor.execute("SELECT file_path, checksum FROM found_files")
    assert sorted(cursor.fetchall()) == sorted([
        (str(file.file_path), None) for file in found_files
    ])


def test_fill_missing_found_file_checksums(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    add_found_files(cursor, found_files)
    cursor.execute('UPDATE found_files SET checksum=NULL')
    fill_missing_found_file_checksums(cursor)

    cursor.execute("SELECT file_path, checksum FROM found_files")
    assert sorted(cursor.fetchall()) == sorted([
        (str(file.file_path), file.checksum) for file in found_files
    ])


def test_commit_found_files(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))

    add_found_files(cursor, found_files)
    commit_found_files(cursor)
    cursor.execute('SELECT file_path, size, file_mtime, checksum FROM timeline_files')
    assert sorted(cursor.fetchall()) == sorted([
        (
            str(file.file_path),
            file.size,
            file.file_mtime.replace(tzinfo=None),
            file.checksum
        ) for file in found_files
    ])

    assert_result_count(cursor, 'SELECT COUNT(*) FROM found_files', 0)


def test_add_timeline_entries(cursor, tmp_path):
    timeline_files = fake_found_files(tmp_path)
    timeline_entries = fake_timeline_entries()
    add_found_files(cursor, timeline_files)
    add_timeline_entries(cursor, timeline_entries)

    cursor.execute("SELECT file_path, entry_type, date_start, date_end, entry_data FROM timeline_entries")
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        assert row == (
            str(timeline_entries[index].file_path),
            str(timeline_entries[index].entry_type),
            timeline_entries[index].date_start.replace(tzinfo=None),
            timeline_entries[index].date_end.replace(tzinfo=None),
            json.dumps(timeline_entries[index].data)
        )