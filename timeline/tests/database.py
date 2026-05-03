from timeline.database import (
    create_database,
    add_found_files,
    clear_table,
    get_connection,
    apply_cached_checksums_to_found_files,
    commit_found_files,
    fill_missing_found_file_checksums,
    add_timeline_entries,
    update_timeline_entries_for_file,
    mark_timeline_file_as_processed,
    dates_with_changes,
    get_entries_for_date,
    to_db_datetime,
)
from timeline.filesystem import get_checksum
from timeline.models import TimelineEntry, TimelineFile, EntryType
from datetime import date, datetime, timedelta
import json
import pytest
import sqlite3


def fake_found_files(tmp_path):
    now = datetime.now().astimezone()
    yesterday = now - timedelta(days=1)

    file_paths = [
        tmp_path / "file_a.text",
        tmp_path / "file_b.text",
        tmp_path / "file_c.text",
    ]

    file_mtimes = [
        now,
        now,
        yesterday,
    ]

    for index, file_path in enumerate(file_paths):
        with file_path.open("w") as file:
            file.write("Hello file!" * (index + 1))
        checksum = get_checksum(file_path)

        yield TimelineFile(
            file_path=file_path,
            checksum=checksum,
            date_added=now,
            size=file_path.stat().st_size,
            file_mtime=file_mtimes[index],
        )


def fake_timeline_entries(tmp_path):
    return [
        TimelineEntry(
            file_path=tmp_path / "file_a.text",
            checksum="improperly mocked value",
            entry_type=EntryType.IMAGE,
            date_start=datetime(2023, 7, 1).astimezone(),
            date_end=datetime(2023, 7, 4).astimezone(),
            data={
                "size": [640, 480],
                "location": [52.44, 49.44],
                "description": "A man sitting on a treestump",
            },
        ),
        TimelineEntry(
            file_path=tmp_path / "file_b.text",
            checksum="improperly mocked value",
            entry_type=EntryType.HTML,
            date_start=datetime(2023, 7, 3).astimezone(),
            date_end=None,
            data={
                "content": "# This is my journal\n\nIt was a dark and stormy night..."
            },
        ),
        TimelineEntry(
            file_path=tmp_path / "file_b.text",
            checksum="improperly mocked value",
            entry_type=EntryType.HTML,
            date_start=datetime(2023, 7, 7).astimezone(),
            date_end=datetime(2023, 7, 10, 23, 59, 59).astimezone(),
            data={"content": "All quiet on the western front"},
        ),
    ]


def assert_result_count(cursor, query, count):
    cursor.execute(query)
    assert cursor.fetchone()[0] == count


@pytest.fixture
def cursor(tmp_path):
    connection = get_connection(tmp_path / "database.db")
    cursor = connection.cursor()
    create_database(connection)
    yield cursor
    cursor.close()
    connection.close()


def test_clear_table(cursor, tmp_path):
    add_found_files(cursor, fake_found_files(tmp_path))
    assert_result_count(cursor, "SELECT COUNT(*) FROM found_files", 3)
    clear_table(cursor, "found_files")
    cursor.execute("SELECT * FROM found_files")
    assert_result_count(cursor, "SELECT COUNT(*) FROM found_files", 0)


def test_add_found_files(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    add_found_files(cursor, found_files)

    cursor.execute(
        "SELECT file_path, checksum, date_added, size, file_mtime FROM found_files"
    )
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        assert row == (
            str(found_files[index].file_path),
            found_files[index].checksum,
            to_db_datetime(found_files[index].date_added),
            found_files[index].size,
            to_db_datetime(found_files[index].file_mtime),
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
        add_found_files(cursor, [new_file])


def test_apply_cached_checksums_to_found_files(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))

    add_found_files(cursor, found_files)
    commit_found_files(cursor)

    clear_table(cursor, "found_files")
    add_found_files(cursor, found_files)
    cursor.execute("UPDATE found_files SET checksum=null")

    apply_cached_checksums_to_found_files(cursor)

    # Checksum is set to the cached value
    cursor.execute("SELECT file_path, checksum FROM found_files")
    assert sorted(cursor.fetchall()) == sorted(
        [(str(file.file_path), file.checksum) for file in found_files]
    )


def test_apply_cached_checksums_to_found_files_file_has_changed(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))

    add_found_files(cursor, found_files)
    commit_found_files(cursor)

    clear_table(cursor, "found_files")
    found_files = list(fake_found_files(tmp_path))  # New, different date_updated
    add_found_files(cursor, found_files)
    cursor.execute("UPDATE found_files SET checksum=null")

    apply_cached_checksums_to_found_files(cursor)

    # Checksum is not set to the cached value, because the modified date differs
    cursor.execute("SELECT file_path, checksum FROM found_files")
    assert sorted(cursor.fetchall()) == sorted(
        [(str(file.file_path), None) for file in found_files]
    )


def test_fill_missing_found_file_checksums(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    add_found_files(cursor, found_files)
    cursor.execute("UPDATE found_files SET checksum=NULL")
    fill_missing_found_file_checksums(cursor)

    cursor.execute("SELECT file_path, checksum FROM found_files")
    assert sorted(cursor.fetchall()) == sorted(
        [(str(file.file_path), file.checksum) for file in found_files]
    )


def test_commit_found_files(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))

    add_found_files(cursor, found_files)
    commit_found_files(cursor)
    cursor.execute(
        "SELECT file_path, size, file_mtime, checksum, date_processed FROM timeline_files"
    )
    assert sorted(cursor.fetchall()) == sorted(
        [
            (
                str(file.file_path),
                file.size,
                to_db_datetime(file.file_mtime),
                file.checksum,
                None,
            )
            for file in found_files
        ]
    )

    assert_result_count(cursor, "SELECT COUNT(*) FROM found_files", 0)


def test_commit_found_files_handle_removed(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))

    add_found_files(cursor, found_files)
    commit_found_files(cursor)
    cursor.execute(
        "SELECT file_path, size, file_mtime, checksum, date_processed FROM timeline_files"
    )
    assert sorted(cursor.fetchall()) == sorted(
        [
            (
                str(file.file_path),
                file.size,
                to_db_datetime(file.file_mtime),
                file.checksum,
                None,
            )
            for file in found_files
        ]
    )

    # Do it again, with one found_file removed
    clear_table(cursor, "found_files")
    found_files.pop()
    add_found_files(cursor, found_files)
    commit_found_files(cursor)

    cursor.execute(
        "SELECT file_path, size, file_mtime, checksum, date_processed FROM timeline_files"
    )
    assert sorted(cursor.fetchall()) == sorted(
        [
            (
                str(file.file_path),
                file.size,
                to_db_datetime(file.file_mtime),
                file.checksum,
                None,
            )
            for file in found_files
        ]
    )

    assert_result_count(cursor, "SELECT COUNT(*) FROM found_files", 0)


def test_commit_found_files_handle_existing_checksum(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    timeline_entries = fake_timeline_entries(tmp_path)

    add_found_files(cursor, found_files)
    commit_found_files(cursor)
    add_timeline_entries(cursor, timeline_entries)

    # Do it again, with different date_added and file_mtime
    clear_table(cursor, "found_files")
    new_found_files = list(
        fake_found_files(tmp_path)
    )  # Same files, new date_added and mtime
    add_found_files(cursor, new_found_files)
    commit_found_files(cursor)

    # The timeline_file row gets updated with the new date_added and mtime
    cursor.execute(
        "SELECT file_path, size, file_mtime, checksum, date_processed FROM timeline_files"
    )
    assert sorted(cursor.fetchall()) == sorted(
        [
            (
                str(file.file_path),
                file.size,
                to_db_datetime(file.file_mtime) if file.file_mtime else None,
                file.checksum,
                None,
            )
            for file in new_found_files
        ]
    )

    # Timeline entries should still be there (for found_files[0] which was replaced by new_file)
    cursor.execute("""
        SELECT file_path, entry_type, date_start, date_end, entry_data FROM timeline_entries
    """)
    assert sorted(cursor.fetchall()) == sorted(
        [
            (
                str(entry.file_path),
                entry.entry_type.value,
                to_db_datetime(entry.date_start),
                to_db_datetime(entry.date_end) if entry.date_end else None,
                json.dumps(entry.data),
            )
            for entry in timeline_entries
        ]
    )


def test_commit_found_files_handle_new_checksum(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    timeline_entries = fake_timeline_entries(tmp_path)

    add_found_files(cursor, found_files)
    commit_found_files(cursor)
    add_timeline_entries(cursor, timeline_entries)

    # This timeline_file has entries
    cursor.execute(
        "SELECT COUNT(*) FROM timeline_entries WHERE file_path=?",
        [
            str(found_files[0].file_path),
        ],
    )
    assert cursor.fetchone()[0] == 1

    # Update the file (same path, new checksum), and add it back to the timeline
    with found_files[0].file_path.open("w") as file:
        file.write("New file!")
    checksum = get_checksum(found_files[0].file_path)
    new_file = TimelineFile(
        file_path=found_files[0].file_path,
        checksum=checksum,
        date_added=found_files[0].date_added,
        size=found_files[0].size,
        file_mtime=found_files[0].file_mtime,
    )
    new_found_files = [found_files[1], found_files[2], new_file]

    add_found_files(cursor, new_found_files)
    commit_found_files(cursor)

    # found_files[0] with the old checksum is removed, new_file is added
    cursor.execute(
        "SELECT file_path, size, file_mtime, checksum, date_processed FROM timeline_files"
    )
    assert sorted(cursor.fetchall()) == sorted(
        [
            (
                str(file.file_path),
                file.size,
                to_db_datetime(file.file_mtime),
                file.checksum,
                None,
            )
            for file in new_found_files
        ]
    )

    # Entries are kept so update_timeline_entries_for_file can diff them on re-processing
    cursor.execute(
        "SELECT COUNT(*) FROM timeline_entries WHERE file_path=?",
        [
            str(new_file.file_path),
        ],
    )
    assert cursor.fetchone()[0] == 1


def test_commit_found_files_reset_date_processed(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))

    add_found_files(cursor, found_files)
    commit_found_files(cursor)

    # Mark all as processed
    date_processed = datetime.now() - timedelta(days=7)
    cursor.execute("UPDATE timeline_files SET date_processed=?", [date_processed])

    # Pretend that found_files[0] was updated and has a new checksum
    with found_files[0].file_path.open("w") as file:
        file.write("This is a different file now")
    found_files[0] = TimelineFile(
        file_path=found_files[0].file_path,
        checksum=get_checksum(found_files[0].file_path),  # New checksum
        date_added=found_files[0].date_added,
        file_mtime=found_files[0].file_mtime,
        size=found_files[0].size,
    )
    add_found_files(cursor, found_files)
    commit_found_files(cursor)

    cursor.execute("SELECT file_path, date_processed FROM timeline_files")
    assert sorted(cursor.fetchall()) == sorted(
        [
            (str(found_files[0].file_path), None),  # Reset
            (str(found_files[1].file_path), date_processed),  # Unchanged
            (str(found_files[2].file_path), date_processed),  # Unchanged
        ]
    )


def test_add_timeline_entries(cursor, tmp_path):
    found_files = fake_found_files(tmp_path)
    timeline_entries = fake_timeline_entries(tmp_path)
    add_found_files(cursor, found_files)
    commit_found_files(cursor)
    add_timeline_entries(cursor, timeline_entries)

    cursor.execute("""
        SELECT file_path, entry_type, date_start, date_end, entry_data FROM timeline_entries
    """)
    rows = cursor.fetchall()
    for index, row in enumerate(rows):
        assert row == (
            str(timeline_entries[index].file_path),
            timeline_entries[index].entry_type.value,
            to_db_datetime(timeline_entries[index].date_start),
            to_db_datetime(timeline_entries[index].date_end)
            if timeline_entries[index].date_end
            else None,
            json.dumps(timeline_entries[index].data),
        )


def test_add_timeline_entries_invalid_path(cursor, tmp_path):
    clear_table(cursor, "found_files")
    clear_table(cursor, "timeline_entries")

    timeline_entries = fake_timeline_entries(tmp_path)
    with pytest.raises(sqlite3.IntegrityError):
        add_timeline_entries(cursor, timeline_entries)


def test_dates_with_changes(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    timeline_entries = fake_timeline_entries(tmp_path)
    add_found_files(cursor, found_files)
    commit_found_files(cursor)

    file_a_entries = [
        e for e in timeline_entries if e.file_path == tmp_path / "file_a.text"
    ]
    file_b_entries = [
        e for e in timeline_entries if e.file_path == tmp_path / "file_b.text"
    ]
    update_timeline_entries_for_file(cursor, tmp_path / "file_a.text", file_a_entries)
    update_timeline_entries_for_file(cursor, tmp_path / "file_b.text", file_b_entries)

    days_to_update = dates_with_changes(cursor)

    assert set(days_to_update.keys()) == {
        date(2023, 7, 1),
        date(2023, 7, 2),
        date(2023, 7, 3),
        date(2023, 7, 4),
        date(2023, 7, 7),
        date(2023, 7, 8),
        date(2023, 7, 9),
        date(2023, 7, 10),
    }
    # Timestamps should be recent (within the last few seconds)
    now = datetime.now().astimezone()
    for ts in days_to_update.values():
        assert (now - ts).total_seconds() < 5


def test_dates_with_changes_deleted_entries(cursor, tmp_path):
    found_files = list(fake_found_files(tmp_path))
    timeline_entries = fake_timeline_entries(tmp_path)

    # Initial run: add all files and process them
    add_found_files(cursor, found_files)
    commit_found_files(cursor)
    file_a_entries = [
        e for e in timeline_entries if e.file_path == tmp_path / "file_a.text"
    ]
    file_b_entries = [
        e for e in timeline_entries if e.file_path == tmp_path / "file_b.text"
    ]
    update_timeline_entries_for_file(cursor, tmp_path / "file_a.text", file_a_entries)
    update_timeline_entries_for_file(cursor, tmp_path / "file_b.text", file_b_entries)
    mark_timeline_file_as_processed(cursor, tmp_path / "file_a.text")
    mark_timeline_file_as_processed(cursor, tmp_path / "file_b.text")

    # Simulate start of a new run by clearing the session-scoped temp table
    cursor.execute("DELETE FROM dates_with_changes")

    # Second run: file_b is deleted from the filesystem
    file_b = next(f for f in found_files if f.file_path.name == "file_b.text")
    file_b.file_path.unlink()
    remaining_files = [f for f in found_files if f.file_path.name != "file_b.text"]
    add_found_files(cursor, remaining_files)
    commit_found_files(cursor)
    # file_a unchanged → not re-processed; file_b deleted → entries cascade-deleted

    days_to_update = dates_with_changes(cursor)

    # Day 07-03 had a file_b entry deleted, but file_a's entry (07-01 to 07-04) still covers it
    assert date(2023, 7, 3) in days_to_update
    assert datetime.timestamp(days_to_update[date(2023, 7, 3)]) == pytest.approx(
        datetime.timestamp(datetime.now()), abs=5
    )

    # Days only covered by file_b → no remaining entries → marked for deletion
    assert date(2023, 7, 7) in days_to_update
    assert date(2023, 7, 8) in days_to_update
    assert date(2023, 7, 9) in days_to_update
    assert date(2023, 7, 10) in days_to_update

    # Days only from file_a (unchanged this run) → not in days_to_update
    assert date(2023, 7, 1) not in days_to_update
    assert date(2023, 7, 2) not in days_to_update
    assert date(2023, 7, 4) not in days_to_update


def test_get_entries_for_date(cursor, tmp_path):
    found_files = fake_found_files(tmp_path)
    timeline_entries = fake_timeline_entries(tmp_path)
    add_found_files(cursor, found_files)
    commit_found_files(cursor)
    add_timeline_entries(cursor, timeline_entries)

    assert list(get_entries_for_date(cursor, date(2023, 6, 30))) == []

    entries_2023_07_01 = list(get_entries_for_date(cursor, date(2023, 7, 1)))
    assert len(entries_2023_07_01) == 1
    assert entries_2023_07_01[0].date_start == timeline_entries[0].date_start
    assert entries_2023_07_01[0].date_end == timeline_entries[0].date_end

    # Same entry spread over two days
    entries_2023_07_09 = list(get_entries_for_date(cursor, date(2023, 7, 9)))
    assert len(entries_2023_07_09) == 1
    assert entries_2023_07_09[0].date_start == timeline_entries[2].date_start
    assert entries_2023_07_09[0].date_end == timeline_entries[2].date_end

    entries_2023_07_10 = list(get_entries_for_date(cursor, date(2023, 7, 10)))
    assert len(entries_2023_07_10) == 1
    assert entries_2023_07_10[0].date_start == timeline_entries[2].date_start
    assert entries_2023_07_10[0].date_end == timeline_entries[2].date_end

    assert list(get_entries_for_date(cursor, date(2023, 7, 11))) == []
