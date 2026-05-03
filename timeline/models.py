from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class EntryType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    HTML = "html"
    PDF = "pdf"

    MESSAGE = "message"
    EVENT = "event"
    DIARY = "diary"

    SEARCH = "search"
    BROWSING_HISTORY = "browse"
    WATCHED_CONTENT = "watch"

    COMMIT = "commit"

    BALANCE = "balance"
    TRANSACTION = "transaction"

    POST = "post"
    COMMENT = "comment"

    GEOLOCATION = "geolocation"


@dataclass
class TimelineEntry:
    file_path: Path
    checksum: str | None
    entry_type: EntryType
    date_start: datetime
    date_end: datetime | None
    data: dict


@dataclass(frozen=True)
class TimelineFile:
    file_path: Path
    checksum: str | None
    date_added: datetime
    file_mtime: datetime
    size: int
