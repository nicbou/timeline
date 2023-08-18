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

    def to_json_dict(self):
        return {
            'file_path': str(self.file_path),
            'checksum': self.checksum,
            'entry_type': self.entry_type.value,
            'date_start': self.date_start.isoformat(),
            'date_end': self.date_end.isoformat() if self.date_end else None,
            'data': self.data,
        }


@dataclass(frozen=True)
class TimelineFile:
    file_path: Path
    checksum: str
    date_added: datetime
    file_mtime: datetime
    size: int
