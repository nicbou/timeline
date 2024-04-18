from decimal import Decimal
from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry, EntryType
from datetime import datetime
import codecs
import csv


def process_balance_list(file: TimelineFile, metadata_root: Path):
    if not file.file_path.name.lower().endswith('.balances.csv'):
        return

    for line in csv.DictReader(codecs.iterdecode(file.file_path.open('rb'), 'utf-8'), delimiter=',', quotechar='"'):
        # No timezone attached. Assume current system timezone.
        balance_date = datetime.strptime(line['date'], '%Y-%m-%d').astimezone()
        yield TimelineEntry(
            file_path=file.file_path,
            checksum=file.checksum,
            entry_type=EntryType.BALANCE,
            date_start=balance_date,
            date_end=None,
            data={
                'account': line['account'],
                'amount': str(Decimal(line['balance'])),  # String, not number
            }
        )
