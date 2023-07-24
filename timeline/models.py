from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class TimelineFile:
    file_path: Path
    checksum: str
    date_found: datetime
    date_modified: datetime
    size: int


@dataclass(frozen=True)
class TimelineEntry:
    file_path: Path
    date_start: datetime
    date_end: datetime

    # If there are multiple entries for one file, allow each of them a sub-ID, so that they have a unique URI
    id: str = field(default=None)

    @property
    def uri(self):
        return '#'.join([self.file_path, self.id]) if self.id else self.file_path