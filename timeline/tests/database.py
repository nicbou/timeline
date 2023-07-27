from timeline.database import create_timeline_files_table, add_timeline_files, clear_table, \
    add_cached_checksum_to_timeline_files, update_checksum_cache, get_timeline_files_without_checksum, \
    set_found_file_checksums
from timeline.models import TimelineFile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
import sqlite3


def fake_timeline_files():
    now = datetime.now().astimezone()
    yesterday = now - timedelta(days=1)

    return [
        TimelineFile(
            file_path=Path('/path/to/file_a.txt'),
            checksum=None,
            date_found=now,
            size=111,
            date_modified=now,
        ),
        TimelineFile(
            file_path=Path('/path/to/file_b.txt'),
            checksum=None,
            date_found=now,
            size=222,
            date_modified=yesterday,
        ),
        TimelineFile(
            file_path=Path('/path/to/file_c.txt'),
            checksum='5FI7E739THTU8R4SI7EG6QMGA6IL0CAKBI2FAPKFSA4BR8DTMQPG',
            date_found=now,
            size=10995116277760,  # 10 TB
            date_modified=yesterday,
        ),
    ]


@pytest.fixture
def cursor():
    connection = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = connection.cursor()
    create_timeline_files_table(cursor)
    yield cursor
    connection.close()


def test_add_timeline_files(cursor):
    timeline_files = fake_timeline_files()
    add_timeline_files(cursor, timeline_files)

    cursor.execute("SELECT file_path, checksum, date_found, size, date_modified FROM timeline_files")
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        assert row == (
            str(timeline_files[index].file_path),
            timeline_files[index].checksum,
            timeline_files[index].date_found.replace(tzinfo=None),
            timeline_files[index].size,
            timeline_files[index].date_modified.replace(tzinfo=None),
        )


def test_add_timeline_files_multiple_times(cursor):
    timeline_files = fake_timeline_files()
    add_timeline_files(cursor, timeline_files)
    new_file = TimelineFile(
        file_path=Path('/path/to/file_a.txt'),
        checksum=None,
        date_found=datetime.now(),
        size=999,
        date_modified=datetime.now(),
    )
    timeline_files[0] = new_file
    add_timeline_files(cursor, [new_file, ])

    cursor.execute("SELECT file_path, checksum, date_found, size, date_modified FROM timeline_files")
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        assert row == (
            str(timeline_files[index].file_path),
            timeline_files[index].checksum,
            timeline_files[index].date_found.replace(tzinfo=None),
            timeline_files[index].size,
            timeline_files[index].date_modified.replace(tzinfo=None),
        )


def test_clear_table(cursor):
    add_timeline_files(cursor, fake_timeline_files())
    cursor.execute("SELECT * FROM timeline_files")
    assert len(cursor.fetchall()) > 0
    clear_table(cursor, 'timeline_files')
    cursor.execute("SELECT * FROM timeline_files")
    assert len(cursor.fetchall()) == 0


def test_update_checksum_cache(cursor):
    timeline_files = fake_timeline_files()
    add_timeline_files(cursor, timeline_files)

    # Populate checksum cache
    update_checksum_cache(cursor)
    cursor.execute('SELECT file_path, size, date_modified, checksum FROM checksum_cache')
    assert cursor.fetchall() == [
        (
            str(timeline_files[2].file_path),
            timeline_files[2].size,
            timeline_files[2].date_modified.replace(tzinfo=None),
            timeline_files[2].checksum
        ),
    ]


def test_add_cached_checksum_to_timeline_files(cursor):
    add_timeline_files(cursor, fake_timeline_files())

    cursor.execute("SELECT checksum FROM timeline_files WHERE checksum IS NOT null")
    assert len(cursor.fetchall()) == 1

    # Cache is empty, no effect
    add_cached_checksum_to_timeline_files(cursor)
    cursor.execute("SELECT checksum FROM timeline_files WHERE checksum IS NOT null")
    assert len(cursor.fetchall()) == 1

    update_checksum_cache(cursor)
    assert len(cursor.execute('SELECT * FROM checksum_cache').fetchall()) == 1
    cursor.execute("UPDATE timeline_files SET checksum=null")
    cursor.execute("SELECT checksum FROM timeline_files WHERE checksum IS NOT null")
    assert len(cursor.fetchall()) == 0

    add_cached_checksum_to_timeline_files(cursor)
    cursor.execute("SELECT checksum FROM timeline_files WHERE checksum IS NOT null")
    assert cursor.fetchone() == ('5FI7E739THTU8R4SI7EG6QMGA6IL0CAKBI2FAPKFSA4BR8DTMQPG', )


def test_get_timeline_files_without_checksum(cursor):
    timeline_files = fake_timeline_files()
    add_timeline_files(cursor, timeline_files)
    assert sorted(get_timeline_files_without_checksum(cursor)) == sorted([
        timeline_files[0].file_path,
        timeline_files[1].file_path
    ])


def test_set_found_file_checksums(cursor):
    timeline_files = fake_timeline_files()
    add_timeline_files(cursor, timeline_files)
    assert len(get_timeline_files_without_checksum(cursor)) == 2

    set_found_file_checksums(cursor, (
        (timeline_files[1].file_path, 'TEST_CHECKSUM_A'),
        (timeline_files[2].file_path, 'TEST_CHECKSUM_B'),
    ))

    assert len(get_timeline_files_without_checksum(cursor)) == 1
    cursor.execute("SELECT file_path, checksum FROM timeline_files WHERE checksum IS NOT null")
    assert sorted(cursor.fetchall()) == sorted([
        (str(timeline_files[1].file_path), 'TEST_CHECKSUM_A'),
        (str(timeline_files[2].file_path), 'TEST_CHECKSUM_B'),
    ])
