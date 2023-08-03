from datetime import datetime, timedelta
from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry, EntryType
from typing import Iterable
import markdown
import re
import shutil


date_regex = r'(19\d\d|20\d\d)-([0][1-9]|1[0-2])-([0-2][1-9]|[1-3]0|3[01])'
date_range_regex = f"((?P<date_a>{date_regex}) to )?(?P<date_b>{date_regex})"

file_dates_regex = re.compile(date_range_regex + '$')


def str_to_datetime(date_string: str):
    return datetime.strptime(date_string, '%Y-%m-%d')


def dates_from_filename(file_path: Path):
    file_name = file_path.stem

    if match := file_dates_regex.search(file_name):
        try:
            if match['date_a']:
                return (
                    str_to_datetime(match['date_a']),
                    str_to_datetime(match['date_b']) + timedelta(days=1, seconds=-1)
                )
            return (str_to_datetime(match['date_b']), None)
        except ValueError:
            return (None, None)

    return (None, None)


def dates_from_file(file_path: Path):
    date_start, date_end = dates_from_filename(file_path)
    if date_start is None and date_end is None:
        date_start = datetime.fromtimestamp(file_path.stat().st_mtime)
    return date_start, date_end


def process_text(file: TimelineFile, entries: Iterable[TimelineEntry], metadata_root: Path) -> Iterable[TimelineEntry]:
    if file.file_path.suffix.lower() == '.txt':
        output_path = metadata_root / file.checksum
        output_path.mkdir(parents=True, exist_ok=True)
        if not (output_path / 'content.txt').exists():
            shutil.copy(file.file_path, output_path / 'content.txt')

        date_start, date_end = dates_from_file(file.file_path)
        entries.append(
            TimelineEntry(
                file_path=file.file_path,
                entry_type=EntryType.TEXT,
                date_start=date_start,
                date_end=date_end,
                data={}
            )
        )
    return entries


markdown_parser = markdown.Markdown(
    output_format='html',
    extensions=[
        'fenced_code',
        'meta',
        'tables',
        'smarty',
        'codehilite',
    ]
)


def process_markdown(file: TimelineFile, entries: Iterable[TimelineEntry], metadata_root: Path) -> Iterable[TimelineEntry]:
    if file.file_path.suffix.lower() == '.md':
        output_path = metadata_root / file.checksum
        output_path.mkdir(parents=True, exist_ok=True)
        rendered_path = output_path / 'content.html'

        if not rendered_path.exists():
            markdown_parser.convertFile(
                input=str(file.file_path),
                output=str(rendered_path)
            )

        date_start, date_end = dates_from_file(file.file_path)
        entries.append(
            TimelineEntry(
                file_path=file.file_path,
                entry_type=EntryType.TEXT,
                date_start=date_start,
                date_end=date_end,
                data={}
            )
        )
    return entries
