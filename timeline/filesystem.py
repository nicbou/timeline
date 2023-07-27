from fnmatch import fnmatch
from pathlib import Path
import base64
import hashlib


def get_files_in_paths(paths: list[Path], includerules: set = {'*'}, ignorerules: set = set()) -> list[Path]:
    files = set()

    for path in paths:
        if not path.is_absolute():
            # If paths are not absolute, two paths can include the same file multiple times:
            # get_files_in_paths([test/logs, test]) includes test/logs/hello.log as logs/hello.log and hello.log
            # Similar files can also be included as one: test/logs/hello.log and test/hello.log
            raise ValueError('Paths must be absolute')

        for includerule in includerules:
            files.update(
                f for f in path.rglob(includerule)
                if f.is_file()
                and not any(fnmatch(str(f), str('*/' + ignorerule)) for ignorerule in ignorerules)
            )

    return list(files)


def get_checksum(file_path: Path) -> str:
    with open(file_path, "rb") as f:
        file_hash = hashlib.blake2b(digest_size=32)
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return base64.b32hexencode(file_hash.digest()).decode('utf-8').strip('=')
