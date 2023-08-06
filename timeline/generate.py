from datetime import datetime
from importlib.resources import path
from jinja2.ext import Extension
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined, nodes
from markupsafe import Markup
from pathlib import Path
from timeline.file_processors import process_text, process_markdown
from timeline.filesystem import get_files_in_paths
from timeline.models import TimelineFile, EntryType
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


class IncludeRawExtension(Extension):
    tags = {"include_raw"}

    def parse(self, parser):
        lineno = parser.stream.expect("name:include_raw").lineno
        template = parser.parse_expression()
        result = self.call_method("_render", [template], lineno=lineno)
        return nodes.Output([result], lineno=lineno)

    def _render(self, filename):
        return Markup(self.environment.loader.get_source(self.environment, filename)[0])


def get_template_environment(templates_root: Path, metadata_root: Path):
    env = Environment(
        loader=FileSystemLoader([str(templates_root), str(metadata_root)]),
        autoescape=select_autoescape(),
        extensions=[IncludeRawExtension],
        undefined=StrictUndefined
    )
    return env


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

    template_environment = get_template_environment(path(package=templates, resource="").__enter__(), metadata_root)
    new_page_count = 0
    for day, date_processed in db.dates_with_entries(cursor).items():
        output_path = output_root / f"{day.strftime('%Y-%m-%d')}.html"
        if not output_path.exists() or date_processed.timestamp() > output_path.stat().st_mtime:
            logging.info(f"Generating page for {day.strftime('%Y-%m-%d')}")
            new_page_count += 1
            render_template(
                template_environment,
                'day.html.jinja',
                {
                    'entries': db.get_entries_for_date(cursor, day),
                    'EntryType': EntryType,
                },
                output_path
            )

    logging.info(f"Generated {new_page_count} date pages")