from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from timeline.file_processors import dates_from_file
from timeline.models import TimelineFile, TimelineEntry, EntryType
from timezonefinder import TimezoneFinder
import json
import logging
import pytz
import re
import shutil
import subprocess


logger = logging.getLogger(__name__)
tz_finder = TimezoneFinder()


video_extensions = set([
    '.webm', '.mkv', '.flv', '.vob', '.ogv', '.ogg', '.rrc', '.gifv', '.mng', '.mov', '.avi', '.qt', '.wmv', '.yuv',
    '.rm', '.asf', '.amv', '.mp4', '.m4p', '.m4v', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.m4v', '.svi', '.3gp',
    '.3g2', '.mxf', '.roq', '.nsv', '.flv', '.f4v', '.f4p', '.f4a', '.f4b', '.mod'
])
video_geolocation_regex = re.compile(r"^(?P<lat>[+-]\d+\.\d+)(?P<lng>[+-]\d+\.\d+)(?P<alt>[+-]\d+\.\d+)?/.*$")


def can_process_videos():
    return bool(shutil.which('ffmpeg')) and bool(shutil.which('ffprobe'))


def parse_video_geolocation(value: str):
    if match := video_geolocation_regex.match(value):
        raw_alt = match.groupdict().get('alt', '')
        return (
            str(Decimal(match['lat'])),
            str(Decimal(match['lng'])),
            str(Decimal(raw_alt)) if raw_alt else None
        )


def make_preview(input_path: Path, output_path: Path, video_duration: int, max_width: int, max_height: int):
    if output_path.exists():
        raise FileExistsError

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if video_duration is None or video_duration == 0:
        raise ValueError(
            f'Could not generate video preview. Video duration is {video_duration}.'
        )

    try:
        sample_count = 10
        sample_duration = 2
        if video_duration <= 10:
            sample_count = 1
            sample_duration = video_duration
        elif video_duration <= 30:
            sample_count = 5
            sample_duration = 1
        elif video_duration <= 5 * 60:
            sample_count = 5
            sample_duration = 2

        # Take a [sample_duration] video sample at every 1/[sample_count] of the video
        preview_intervals = [
            (sample_start, sample_start + sample_duration)
            for sample_start in [
                int(i / sample_count * video_duration)
                for i in range(0, sample_count)
            ]
        ]

        # Cut the sample
        ffmpeg_filter = " ".join(
            f"[0:v]trim={start}:{end},setpts=PTS-STARTPTS[v{index}];"
            for index, (start, end) in enumerate(preview_intervals)  # noqa
        )

        # Concatenate the samples
        ffmpeg_filter += "".join(
            f"[v{i}]" for i in range(0, len(preview_intervals))
        )
        ffmpeg_filter += f"concat=n={sample_count}:v=1[allclips];"

        # Scale the output to fit max size, but don't enlarge, don't crop, and don't change aspect ratio
        ffmpeg_filter += \
            f"[allclips]scale=ceil(iw*min(1\\,min({max_width}/iw\\,{max_height}/ih))/2)*2:-2[out]"

        command = [
            'ffmpeg',
            '-y',  # Overwrite if exists, without asking
            '-i', str(input_path),
            '-filter_complex', ffmpeg_filter,
            '-map', '[out]',
            '-codec:v', 'libvpx-vp9',
            str(output_path),
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as exc:
        command = " ".join(exc.cmd)
        raise Exception(
            f'Could not generate video preview.\n'
            f"FFMPEG COMMAND:\n{command}\n"
            f"FFMPEG OUTPUT:\n{exc.stderr.decode('UTF-8')}"
        )


def process_video(file: TimelineFile, metadata_root: Path):
    if file.file_path.suffix.lower() not in video_extensions:
        return

    ffprobe_cmd = subprocess.run(
        [
            'ffprobe',
            '-v', 'error',
            '-show_format', '-show_streams',
            '-print_format', 'json',
            str(file.file_path)
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    try:
        ffprobe_data = json.loads(ffprobe_cmd.stdout.decode('utf-8'))
    except KeyError:
        raise ValueError(f"Could not read metadata of {str(file.file_path)}")

    date_start, date_end = dates_from_file(file.file_path)
    entry_data = {
        'media': {},
    }

    for stream in ffprobe_data['streams']:
        if stream['codec_type'] == 'video':
            entry_data['media']['width'] = int(stream['width'])
            entry_data['media']['height'] = int(stream['height'])
        if 'codec_name' in stream:
            entry_data['media']['codec'] = stream['codec_name']
        if 'rotate' in stream.get('tags', {}):
            entry_data['media']['orientation'] = int(stream['tags']['rotate'])

    entry_data['media']['duration'] = int(float(ffprobe_data['format']['duration']))

    if ffprobe_data['format'].get('tags', {}).get('location'):
        lat, lng, alt = parse_video_geolocation(ffprobe_data['format']['tags']['location'])
        entry_data['location'] = {
            'latitude': float(lat),
            'longitude': float(lng),
        }
        if alt:
            entry_data['location']['altitude'] = alt

    if ffprobe_data['format'].get('tags', {}).get('creation_time'):
        # The dates are stored as UTC. EXIF metadata might contain timezone-aware dates, but accessing them would
        # require exiftool, which is a non-Python external dependency. It's easier to just get the timezone from the
        # GPS coordinates.
        date_start = datetime.strptime(
            ffprobe_data['format']['tags']['creation_time'],
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ).replace(tzinfo=timezone.utc)

        if entry_data.get('location'):
            timezone_string = tz_finder.timezone_at(
                lat=entry_data['location']['latitude'],
                lng=entry_data['location']['longitude']
            )
            date_start = date_start.astimezone(pytz.timezone(timezone_string))



    output_path = metadata_root / file.checksum / 'thumbnail.webm'
    if not output_path.exists():
        try:
            make_preview(file.file_path, output_path, entry_data['media']['duration'], 800, 600)
        except:
            logger.exception(f"Could not process video - {file.file_path}")
            return

    yield TimelineEntry(
        file_path=file.file_path,
        checksum=file.checksum,
        entry_type=EntryType.VIDEO,
        date_start=date_start,
        date_end=date_end,
        data=entry_data,
    )
