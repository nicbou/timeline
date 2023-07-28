from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class EntryType(Enum):
    IMAGE = 'image'
    VIDEO = 'video'
    TEXT = 'text'
    MARKDOWN = 'markdown'

    MESSAGE = 'message'
    EVENT = 'event'

    SEARCH = 'search'
    BROWSING_HISTORY = 'browse'

    COMMIT = 'commit'

    BALANCE = 'balance'
    INCOME = 'income'
    EXPENSE = 'expense'

    POST = 'post'
    COMMENT = 'comment'

    GEOLOCATION = 'geolocation'


@dataclass(frozen=True)
class TimelineEntry:
    file_path: Path
    entry_type: EntryType
    date_start: datetime
    date_end: datetime
    data: dict

    # If there are multiple entries for one file, allow each of them a sub-ID, so that they have a unique URI
    id: str = field(default=None)

    @property
    def uri(self):
        return '#'.join([self.file_path, self.id]) if self.id else self.file_path


@dataclass(frozen=True)
class TimelineFile:
    file_path: Path
    checksum: str
    date_found: datetime
    date_modified: datetime
    size: int