from timeline.database import add_found_files, add_cached_checksum_to_found_files, clear_table,\
    update_checksum_cache, set_found_file_checksums, get_found_files_without_checksum, create_found_files_table
from timeline.filesystem import get_checksum
from pathlib import Path
from typing import Iterable


def update_entries_db(cursor, found_files: Iterable[Path]):
    create_found_files_table(cursor)
    clear_table(cursor, 'found_files')
    add_found_files(cursor, found_files)

    add_cached_checksum_to_found_files(cursor)
    set_found_file_checksums(
        cursor,
        (
            (file, get_checksum(file))
            for file in get_found_files_without_checksum(cursor)
        )
    )
    update_checksum_cache(cursor)
