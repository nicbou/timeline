from pathlib import Path
from timeline.file_processors import dates_from_file
from timeline.models import TimelineFile, TimelineEntry, EntryType
import markdown
import shutil


def process_text(file: TimelineFile, metadata_root: Path):
    if file.file_path.suffix.lower() != '.txt':
        return

    output_path = metadata_root / file.checksum / 'content.txt'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not output_path.exists():
        shutil.copy(file.file_path, output_path)

    date_start, date_end = dates_from_file(file.file_path)
    yield TimelineEntry(
        file_path=file.file_path,
        checksum=file.checksum,
        entry_type=EntryType.TEXT,
        date_start=date_start,
        date_end=date_end,
        data={}
    )


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


def process_markdown(file: TimelineFile, metadata_root: Path):
    if file.file_path.suffix.lower() != '.md':
        return

    output_path = metadata_root / file.checksum
    output_path.mkdir(parents=True, exist_ok=True)
    rendered_path = output_path / 'content.html'

    if not rendered_path.exists():
        markdown_parser.convertFile(
            input=str(file.file_path),
            output=str(rendered_path)
        )

    date_start, date_end = dates_from_file(file.file_path)
    if file.file_path.name.lower().endswith('.diary.md'):
        entry_type = EntryType.DIARY
    else:
        entry_type = EntryType.HTML
    yield TimelineEntry(
        file_path=file.file_path,
        checksum=file.checksum,
        entry_type=entry_type,
        date_start=date_start,
        date_end=date_end,
        data={}
    )
