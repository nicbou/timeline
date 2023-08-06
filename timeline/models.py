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
    checksum: str
    entry_type: EntryType
    date_start: datetime
    date_end: datetime
    data: dict


@dataclass(frozen=True)
class TimelineFile:
    file_path: Path
    checksum: str
    date_added: datetime
    file_mtime: datetime
    size: int
