from datetime import datetime
from pathlib import Path
import markdown as md_lib
from timeline.models import TimelineFile, TimelineEntry, EntryType


def process_reddit(file: TimelineFile, metadata_root: Path):
    if not file.file_path.name.lower().endswith(".reddit.md"):
        return

    text = file.file_path.read_text(encoding="utf-8")
    markdown_parser = md_lib.Markdown(extensions=["meta"])
    rendered_body = markdown_parser.convert(text)
    meta = {k: v[0] if v else None for k, v in markdown_parser.Meta.items()}

    entry_type = EntryType.POST if meta.get("type") == "post" else EntryType.COMMENT

    data: dict = {
        "author": meta.get("author"),
        "subreddit": meta.get("subreddit"),
        "id": meta.get("id"),
        "url": meta.get("url"),
        "body": rendered_body,
    }

    if entry_type == EntryType.POST:
        data["title"] = meta.get("title")
    else:
        data["post_title"] = meta.get("post_title")
        data["post_url"] = meta.get("post_url")

    date_start = datetime.fromisoformat(meta["date"])
    yield TimelineEntry(
        file_path=file.file_path,
        checksum=file.checksum,
        entry_type=entry_type,
        date_start=date_start,
        date_end=None,
        data=data,
    )
