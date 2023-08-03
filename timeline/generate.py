from datetime import datetime
from importlib.resources import path
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined
from pathlib import Path
from timeline.file_processors import process_text, process_markdown
from timeline.filesystem import get_files_in_paths
from timeline.models import TimelineFile
from timeline import templates
from typing import Iterable
import logging
import timeline.database as db


def get_timeline_files_in_paths(paths, includerules, ignorerules) -> Iterable[TimelineFile]:
    now = datetime.now().astimezone()
    for file_path in get_files_in_paths(paths, includerules, ignorerules):
        file_stats = file_path.stat()
        yield TimelineFile(
            file_path=file_path,
            checksum=None,
            date_added=now,
            file_mtime=datetime.fromtimestamp(file_stats.st_mtime),
            size=file_stats.st_size,
        )


def process_timeline_files(cursor, input_paths, includerules, ignorerules, metadata_root: Path) -> int:
    db.create_database(cursor)
    db.update_file_database(
        cursor, get_timeline_files_in_paths(input_paths, includerules, ignorerules)
    )

    timeline_file_processors = [
        process_text,
        process_markdown,
    ]

    new_file_count = 0
    for file in db.get_unprocessed_timeline_files(cursor):
        new_file_count += 1
        logging.info(f"Processing {file.file_path}")

        entries = []
        for process_function in timeline_file_processors:
            entries = process_function(file, entries, metadata_root)

        db.delete_timeline_entries(cursor, file.file_path)
        db.add_timeline_entries(cursor, entries)
        db.mark_timeline_file_as_processed(cursor, file.file_path)

    logging.info(f"Processed {new_file_count} new files")


def get_template_environment(templates_root: Path):
    return Environment(
        loader=FileSystemLoader(str(templates_root)),
        autoescape=select_autoescape(),
        undefined=StrictUndefined
    )


def render_template(template_environment: Environment, template_path: Path, context: dict, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template = template_environment.get_template(str(template_path))
    template.stream(**context).dump(str(output_path))


def generate(input_paths, includerules, ignorerules, metadata_root: Path, output_root: Path):
    metadata_root.mkdir(parents=True, exist_ok=True)
    connection = db.get_connection(metadata_root / 'timeline.db')
    cursor = connection.cursor()

    process_timeline_files(cursor, input_paths, includerules, ignorerules, metadata_root)
    connection.commit()

    logging.info("Generating timeline pages")
    template_environment = get_template_environment(path(package=templates, resource="").__enter__())
    for day, date_processed in db.dates_with_entries(cursor).items():
        logging.info(f"Generating page for {day.strftime('%Y-%m-%d')}")
        output_path = output_root / f"{day.strftime('%Y-%m-%d')}.html"

        if not output_path.exists() or date_processed.timestamp() > output_path.stat().st_mtime:
            render_template(
                template_environment,
                'day.html.jinja',
                {'entries': db.get_entries_for_date(cursor, day)},
                output_path
            )
