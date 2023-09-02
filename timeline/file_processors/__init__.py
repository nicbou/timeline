from datetime import datetime, timedelta
from pathlib import Path
import re


date_regex = r'(19\d\d|20\d\d)-([0][1-9]|1[0-2])-([0-2][1-9]|[1-3]0|3[01])(T([01][0-9]|2[0-3])([0-5][0-9]))?'
date_range_regex = f"((?P<date_a>{date_regex}) to )?(?P<date_b>{date_regex})"

file_dates_regex = re.compile(date_range_regex + '$')


def str_to_datetime(date_string: str):
    try:
        return datetime.strptime(date_string, '%Y-%m-%dT%H%M').astimezone()
    except ValueError:
        return datetime.strptime(date_string, '%Y-%m-%d').astimezone()


def dates_from_filename(file_path: Path):
    file_name, _, _ = file_path.name.partition('.')

    if match := file_dates_regex.search(file_name):
        try:
            if match['date_a']:
                if 'T' in match['date_b']:
                    return (
                        str_to_datetime(match['date_a']),
                        str_to_datetime(match['date_b']) + timedelta(seconds=-1)
                    )
                else:
                    return (
                        str_to_datetime(match['date_a']),
                        str_to_datetime(match['date_b']) + timedelta(days=1, seconds=-1)
                    )
            return (str_to_datetime(match['date_b']), None)
        except ValueError:
            return (None, None)

    return (None, None)


def dates_from_file(file_path: Path):
    date_start, date_end = dates_from_filename(file_path)

    if date_start is None and date_end is None:
        date_start = datetime.fromtimestamp(file_path.stat().st_mtime).astimezone()
    return date_start, date_end
