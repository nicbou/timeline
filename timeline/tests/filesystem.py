from datetime import datetime
from pathlib import Path
from timeline.filesystem import get_files_in_paths, get_checksum
import os
import pytest


sample_files = (
    ('hello_world.txt', datetime(2023, 3, 24)),
    ('hello_world.html', datetime(2023, 3, 25)),
    ('logs/2023-01-01.log', datetime(2023, 1, 1)),
    ('logs/2023-02-01.log', datetime(2023, 2, 1)),
    ('logs/2023-03-01.log', datetime(2023, 3, 1)),
    ('logs/2023-04-01.log', datetime(2023, 4, 1)),
    ('logs/2023-05-01.log', datetime(2023, 5, 1)),
    ('logs/2023-06-01.log', datetime(2023, 6, 1)),
    ('logs/2023-07-01.log', datetime(2023, 7, 1)),
    ('logs/2023-08-01.log', datetime(2023, 8, 1)),
    ('logs/2023-09-01.log', datetime(2023, 9, 1)),
    ('logs/2023-10-01.log', datetime(2023, 10, 1)),
    ('logs/2023-11-01.log', datetime(2023, 11, 1)),
)


def fill_directory(dir_path, files):
    for file_path, file_date in files:
        abs_path = dir_path / file_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.touch()
        os.utime(abs_path, (file_date.timestamp(), file_date.timestamp()))


def test_get_files_in_paths(tmp_path):
    fill_directory(tmp_path, sample_files)

    paths = get_files_in_paths([tmp_path,])
    assert len(paths) == len(sample_files)
    for file_path, file_date in sample_files:
        assert tmp_path / file_path in paths


def test_get_files_in_paths_relative_paths(tmp_path):
    fill_directory(tmp_path, sample_files)
    get_files_in_paths([tmp_path / 'logs/test', ])
    with pytest.raises(ValueError):
        get_files_in_paths([Path('logs/test'), ])


def test_get_files_in_paths_overlapping_paths(tmp_path):
    fill_directory(tmp_path, sample_files)

    paths = get_files_in_paths([tmp_path, tmp_path / 'logs'])
    assert len(paths) == len(sample_files)
    for file_path, file_date in sample_files:
        assert tmp_path / file_path in paths


def test_get_files_in_paths_identical_relative_paths(tmp_path):
    fill_directory(tmp_path / 'dir_a', sample_files)
    fill_directory(tmp_path / 'dir_b', sample_files)

    paths = get_files_in_paths([tmp_path / 'dir_a', tmp_path / 'dir_b'])
    assert len(paths) == len(sample_files) * 2
    for file_path, file_date in sample_files:
        assert tmp_path / 'dir_a' / file_path in paths
        assert tmp_path / 'dir_b' / file_path in paths


def test_get_files_in_paths_includerules(tmp_path):
    fill_directory(tmp_path, sample_files)

    paths = get_files_in_paths([tmp_path,], includerules=['logs/*', ])
    assert sorted(paths) == sorted([
        tmp_path / 'logs/2023-01-01.log',
        tmp_path / 'logs/2023-02-01.log',
        tmp_path / 'logs/2023-03-01.log',
        tmp_path / 'logs/2023-04-01.log',
        tmp_path / 'logs/2023-05-01.log',
        tmp_path / 'logs/2023-06-01.log',
        tmp_path / 'logs/2023-07-01.log',
        tmp_path / 'logs/2023-08-01.log',
        tmp_path / 'logs/2023-09-01.log',
        tmp_path / 'logs/2023-10-01.log',
        tmp_path / 'logs/2023-11-01.log',
    ])

    paths = get_files_in_paths([tmp_path, ], includerules=['logs/2023-1*', ])
    assert sorted(paths) == sorted([
        tmp_path / 'logs/2023-10-01.log',
        tmp_path / 'logs/2023-11-01.log',
    ])


def test_get_files_in_paths_ignorerules(tmp_path):
    fill_directory(tmp_path, sample_files)

    paths = get_files_in_paths([tmp_path,], ignorerules=['*.log', ])
    for path in paths:
        assert path.suffix != '.log'


def test_get_files_in_paths_includerules_and_ignorerules(tmp_path):
    fill_directory(tmp_path, sample_files)

    paths = get_files_in_paths([tmp_path,], includerules=['logs/2023-1*', ], ignorerules=['logs/*1-01.log', ])
    assert sorted(paths) == sorted([
        tmp_path / 'logs/2023-10-01.log',
    ])


def test_get_files_in_paths_ignorerules_beat_includerules(tmp_path):
    fill_directory(tmp_path, sample_files)

    paths = get_files_in_paths([tmp_path,], includerules=['*.log', ], ignorerules=['*.log', ])
    for path in paths:
        assert path.suffix != '.log'


def test_get_checksum(tmp_path):
    file_path = tmp_path / 'test.txt'
    with file_path.open('w') as file:
        file.write('hello_world')
    assert get_checksum(file_path) == '5FI7E739THTU8R4SI7EG6QMGA6IL0CAKBI2FAPKFSA4BR8DTMQPG'

    with file_path.open('w') as file:
        file.write('goodbye_world')
    assert get_checksum(file_path) == 'OHFPSH9B8RMMENQQQMLEJ9F2HHFUIBAEEEABFVVE2OT6BKTUINQG'
