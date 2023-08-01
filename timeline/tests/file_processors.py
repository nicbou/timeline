from datetime import datetime
from pathlib import Path
from timeline.file_processors import dates_from_filename, dates_from_file, process_text
from timeline.models import TimelineFile, EntryType
import pytest

september_10 = (datetime(2023, 9, 10, 0, 0, 0), None)
september_10_to_october_12 = (datetime(2023, 9, 10, 0, 0, 0), datetime(2023, 10, 12, 23, 59, 59))
no_date = (None, None)


@pytest.mark.parametrize("input,expected", [
    ('test/test-2023-09-10.md', september_10),
    ('test/2023-09-10.md', september_10),
    ('test/2023.md', no_date),

    # Date range
    ('test/test 2023-09-10 to 2023-10-12.md', september_10_to_october_12),
    ('test/2023-09-10 to 2023-10-12.md', september_10_to_october_12),

    # Date not at the end
    ('test/2023-09-10 to 2023-09-11 test.md', no_date),
    ('test/2023-09-10 test.md', no_date),
    ('test/2023-09 test.md', no_date),
    ('test/2023 test.md', no_date),

    # Date not valid
    ('test/test-1800-10-01.md', no_date),
    ('test/test-9999-10-01.md', no_date),
    ('test/test-2023-13-01.md', no_date),
    ('test/test-2023-09-1.md', no_date),
    ('test/test-2023-9-10.md', no_date),
    ('test/test-2023-9.md', no_date),
])
def test_dates_from_filename(input, expected):
    assert dates_from_filename(Path(input)) == expected, f"Unexpected result for {input}"


def test_dates_from_file_mtime(tmp_path):
    file_path = tmp_path / 'test.txt'
    file_path.touch()
    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    assert dates_from_file(file_path) == (file_mtime, None)


def test_dates_from_file_filename_override(tmp_path):
    file_path = tmp_path / 'test 2023-01-10.txt'
    file_path.touch()
    assert dates_from_file(file_path) == (datetime(2023, 1, 10), None)


def test_process_text(tmp_path):
    file_path = tmp_path / 'test.txt'
    with file_path.open('w') as file:
        file.write('Hello world')

    timeline_file = TimelineFile(
        file_path=file_path,
        date_added=datetime.now(),
        file_mtime=datetime.now(),
        checksum='not important',
        size=111,
    )
    entries = process_text(timeline_file, [])
    assert entries[0].file_path == file_path
    assert entries[0].entry_type == EntryType.TEXT
    assert entries[0].date_start == datetime.fromtimestamp(file_path.stat().st_mtime)
    assert entries[0].date_end is None
    assert entries[0].data == {
        'content': 'Hello world',
    }
