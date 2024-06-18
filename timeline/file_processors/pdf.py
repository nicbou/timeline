from pathlib import Path
from PIL import Image
from timeline.file_processors import dates_from_file
from timeline.models import TimelineFile, TimelineEntry, EntryType
import fitz
import logging

logger = logging.getLogger(__name__)


def process_pdf(file: TimelineFile, metadata_root: Path):
    if file.file_path.suffix.lower() != '.pdf':
        return

    try:
        pdf_file = fitz.open(file.file_path)
        pixmap = pdf_file[0].get_pixmap(dpi=128, alpha=False)
        image = Image.frombytes('RGB', [pixmap.width, pixmap.height], pixmap.samples)
        image.thumbnail((800, 1128), Image.Resampling.LANCZOS)  # 1128:800 is the ratio of an A4 sheet
        output_path = metadata_root / file.checksum / 'thumbnail.webp'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, optimize=True, exact=True)
    except:
        logger.exception(f"Could not process PDF - {file.file_path}")
        return

    date_start, date_end = dates_from_file(file.file_path)
    yield TimelineEntry(
        file_path=file.file_path,
        checksum=file.checksum,
        entry_type=EntryType.PDF,
        date_start=date_start,
        date_end=date_end,
        data={},
    )
