from datetime import datetime
from pathlib import Path
from PIL import Image, ImageFile, ExifTags
from PIL.ImageOps import exif_transpose
from PIL.ExifTags import TAGS, GPSTAGS
from timeline.file_processors import dates_from_file
from timeline.models import TimelineFile, TimelineEntry, EntryType
from typing import Iterable
import logging
import math
import reverse_geocode

logger = logging.getLogger(__name__)


image_extensions = {
    ext for ext, f in Image.registered_extensions().items()
    if f in Image.OPEN
    and ext != '.psd'
}

ImageFile.LOAD_TRUNCATED_IMAGES = True


def get_image_exif(pil_image) -> dict:
    raw_exif = pil_image.getexif()

    if not raw_exif:
        return {}

    exif = {}
    for (key, val) in raw_exif.items():
        exif[TAGS.get(key)] = val

    exif['GPSInfo'] = {}
    gps_info = raw_exif.get_ifd(ExifTags.IFD.GPSInfo)
    for (tag_id, tag_name) in GPSTAGS.items():
        if tag_id in gps_info:
            exif['GPSInfo'][tag_name] = gps_info[tag_id]

    return exif


def parse_exif_date(date_str: str) -> datetime:
    # Official format: YYYY:MM:DD HH:MM:SS
    # Also seen: YYYY-MM-DD HH:MM:SS and YYYY-MM-DDTHH:MM:SS+ZZZZ
    # Assumes that the dates are in the current timezone
    return datetime.strptime(
        date_str.replace('\x00', '').replace('-', ':').replace('T', ' ')[:19],
        '%Y:%m:%d %H:%M:%S'
    ).astimezone()


def parse_exif_coordinate(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    decimal = round(degrees + minutes + seconds, 5)
    if math.isnan(decimal):
        raise ValueError
    return decimal


def get_image_metadata(image_path: Path) -> dict:
    metadata = {
        'media': {}
    }

    with Image.open(image_path) as image:  # https://github.com/python-pillow/Pillow/issues/4007
        image.verify()

    with Image.open(image_path) as image:
        metadata['media']['width'], metadata['media']['height'] = image.size
        assert metadata['media']['width'] > 0 and metadata['media']['height'] > 0, "Invalid image dimensions"
        exif = get_image_exif(image)

    # Camera orientation
    if 'Orientation' in exif:
        orientation_map = {0: 0, 1: 0, 3: 180, 6: 270, 8: 90}  # 0 is not an official value, but it happens
        try:
            metadata['media']['orientation'] = orientation_map[exif['Orientation']]
        except KeyError:
            logger.warning(f"{image_path} has unexpected EXIF orientation: {exif['Orientation']}")

        # Set the correct width/height according to EXIF orientation
        if metadata['media']['orientation'] == 90 or metadata['media']['orientation'] == 270:
            width = metadata['media']['width']
            height = metadata['media']['height']
            metadata['media']['width'] = height
            metadata['media']['height'] = width
            del metadata['media']['orientation']

    # Camera type
    if 'Make' in exif or 'Model' in exif:
        metadata['media']['camera'] = f"{exif.get('Make', '')} {exif.get('Model', '')}".replace('\x00', '').strip()

    # Geolocation
    if 'GPSInfo' in exif:
        if 'GPSLatitude' in exif['GPSInfo'] and 'GPSLongitude' in exif['GPSInfo']:
            try:
                metadata['location'] = {
                    'latitude': parse_exif_coordinate(
                        exif['GPSInfo']['GPSLatitude'], exif['GPSInfo'].get('GPSLatitudeRef')
                    ),
                    'longitude': parse_exif_coordinate(
                        exif['GPSInfo']['GPSLongitude'], exif['GPSInfo'].get('GPSLongitudeRef')
                    ),
                }
                reverse_geolocation = reverse_geocode.search(
                    (
                        (metadata['location']['latitude'], metadata['location']['longitude']),
                    )
                )[0]
                metadata['location']['city'] = reverse_geolocation['city']
                metadata['location']['country'] = reverse_geolocation['country']
            except ValueError:
                logger.warning(f"Invalid GPS coordinates: "
                               f"{exif['GPSInfo']['GPSLatitude']}, { exif['GPSInfo']['GPSLongitude']}"
                               f" - {str(image_path)}")

    # Date
    if 'GPSDateStamp' in exif.get('GPSInfo', {}) and 'GPSTimeStamp' in exif.get('GPSInfo', {}):
        gps_datetime = ''  # GPS dates are UTC
        try:
            gps_date = exif['GPSInfo']['GPSDateStamp']
            gps_time_fragments = exif['GPSInfo']['GPSTimeStamp']
        except KeyError:
            pass

        try:
            gps_time = ":".join(f"{int(timefragment):02}" for timefragment in gps_time_fragments)
            gps_datetime = f"{gps_date} {gps_time}"
            metadata['media']['creation_date'] = parse_exif_date(gps_datetime)
        except ValueError:
            logger.warning(f"Could not parse EXIF GPS date '{gps_datetime}' - {image_path}")
    elif exif_date := (exif.get('DateTimeOriginal') or exif.get('DateTime')):
        # There is no timezone information on exif dates
        try:
            metadata['media']['creation_date'] = parse_exif_date(exif_date)
        except ValueError:
            logger.exception(f"Could not parse EXIF date '{exif_date}' ({image_path})")

    return metadata


def make_thumbnail(image_path: Path, output_path: Path, max_width: int, max_height: int):
    with Image.open(image_path) as image:
        exif_transpose(image, in_place=True)
        image.thumbnail((max_width, max_height), Image.LANCZOS)
        save_args = {'optimize': True, 'exact': True}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, **save_args)


def process_image(file: TimelineFile, entries: Iterable[TimelineEntry], metadata_root: Path) -> Iterable[TimelineEntry]:
    if file.file_path.suffix.lower() in image_extensions:
        try:
            image_data = get_image_metadata(file.file_path)
        except:
            logger.exception(f"Could not process image metadata - {file.file_path}")
            return entries

        try:
            date_start = image_data['media'].pop('creation_date')
            date_end = None
        except KeyError:
            date_start, date_end = dates_from_file(file.file_path)

        output_path = metadata_root / file.checksum / 'thumbnail.webp'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not output_path.exists():
            make_thumbnail(file.file_path, output_path, 800, 600)

        entries.append(
            TimelineEntry(
                file_path=file.file_path,
                checksum=file.checksum,
                entry_type=EntryType.IMAGE,
                date_start=date_start,
                date_end=date_end,
                data=image_data,
            )
        )
    return entries
