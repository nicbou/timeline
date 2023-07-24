from timeline.database import create_found_files_table, add_found_files, clear_table, \
    add_cached_checksum_to_found_files, update_checksum_cache, get_found_files_without_checksum, \
    set_found_file_checksums
from timeline.models import TimelineFile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
import sqlite3


def fake_found_files():
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
    create_found_files_table(cursor)
    yield cursor
    connection.close()


def test_add_found_files(cursor):
    found_files = fake_found_files()
    add_found_files(cursor, found_files)

    cursor.execute("SELECT file_path, checksum, date_found, size, date_modified FROM found_files")
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        assert row == (
            str(found_files[index].file_path),
            found_files[index].checksum,
            found_files[index].date_found.replace(tzinfo=None),
            found_files[index].size,
            found_files[index].date_modified.replace(tzinfo=None),
        )


def test_add_found_files_multiple_times(cursor):
    found_files = fake_found_files()
    add_found_files(cursor, found_files)
    new_file = TimelineFile(
        file_path=Path('/path/to/file_a.txt'),
        checksum=None,
        date_found=datetime.now(),
        size=999,
        date_modified=datetime.now(),
    )
    found_files[0] = new_file
    add_found_files(cursor, [new_file, ])

    cursor.execute("SELECT file_path, checksum, date_found, size, date_modified FROM found_files")
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        assert row == (
            str(found_files[index].file_path),
            found_files[index].checksum,
            found_files[index].date_found.replace(tzinfo=None),
            found_files[index].size,
            found_files[index].date_modified.replace(tzinfo=None),
        )


def test_clear_table(cursor):
    add_found_files(cursor, fake_found_files())
    cursor.execute("SELECT * FROM found_files")
    assert len(cursor.fetchall()) > 0
    clear_table(cursor, 'found_files')
    cursor.execute("SELECT * FROM found_files")
    assert len(cursor.fetchall()) == 0


def test_update_checksum_cache(cursor):
    found_files = fake_found_files()
    add_found_files(cursor, found_files)

    # Populate checksum cache
    update_checksum_cache(cursor)
    cursor.execute('SELECT file_path, size, date_modified, checksum FROM checksum_cache')
    assert cursor.fetchall() == [
        (
            str(found_files[2].file_path),
            found_files[2].size,
            found_files[2].date_modified.replace(tzinfo=None),
            found_files[2].checksum
        ),
    ]


def test_add_cached_checksum_to_found_files(cursor):
    add_found_files(cursor, fake_found_files())

    cursor.execute("SELECT checksum FROM found_files WHERE checksum IS NOT null")
    assert len(cursor.fetchall()) == 1

    # Cache is empty, no effect
    add_cached_checksum_to_found_files(cursor)
    cursor.execute("SELECT checksum FROM found_files WHERE checksum IS NOT null")
    assert len(cursor.fetchall()) == 1

    update_checksum_cache(cursor)
    assert len(cursor.execute('SELECT * FROM checksum_cache').fetchall()) == 1
    cursor.execute("UPDATE found_files SET checksum=null")
    cursor.execute("SELECT checksum FROM found_files WHERE checksum IS NOT null")
    assert len(cursor.fetchall()) == 0

    add_cached_checksum_to_found_files(cursor)
    cursor.execute("SELECT checksum FROM found_files WHERE checksum IS NOT null")
    assert cursor.fetchone() == ('5FI7E739THTU8R4SI7EG6QMGA6IL0CAKBI2FAPKFSA4BR8DTMQPG', )


def test_get_found_files_without_checksum(cursor):
    found_files = fake_found_files()
    add_found_files(cursor, found_files)
    assert sorted(get_found_files_without_checksum(cursor)) == sorted([
        found_files[0].file_path,
        found_files[1].file_path
    ])


def test_set_found_file_checksums(cursor):
    found_files = fake_found_files()
    add_found_files(cursor, found_files)
    assert len(get_found_files_without_checksum(cursor)) == 2

    set_found_file_checksums(cursor, (
        (found_files[1].file_path, 'TEST_CHECKSUM_A'),
        (found_files[2].file_path, 'TEST_CHECKSUM_B'),
    ))

    assert len(get_found_files_without_checksum(cursor)) == 1
    cursor.execute("SELECT file_path, checksum FROM found_files WHERE checksum IS NOT null")
    assert sorted(cursor.fetchall()) == sorted([
        (str(found_files[1].file_path), 'TEST_CHECKSUM_A'),
        (str(found_files[2].file_path), 'TEST_CHECKSUM_B'),
    ])
