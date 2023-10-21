from pathlib import Path
from timeline.models import TimelineEntry, TimelineFile, EntryType
import gpxpy


def point_to_entry(file: TimelineFile, point) -> TimelineEntry:
    return TimelineEntry(
        file_path=file.file_path,
        checksum=file.checksum,
        entry_type=EntryType.GEOLOCATION,
        date_start=point.time,
        date_end=None,
        data={
            'location': {
                'latitude': point.latitude,
                'longitude': point.longitude,
                'altitude': point.elevation,
            },
        },
    )


def process_gpx(file: TimelineFile, metadata_root: Path):
    if file.file_path.suffix.lower() != '.gpx':
        return

    with file.file_path.open() as gpx_file:
        gpx_data = gpxpy.parse(gpx_file)

    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                yield point_to_entry(file, point)

    for route in gpx_data.routes:
        for point in route.points:
            yield point_to_entry(file, point)

    for point in gpx_data.waypoints:
        yield point_to_entry(file, point)
