from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry, EntryType
from typing import Iterable
from datetime import datetime
import codecs
import csv


def process_n26_transactions(file: TimelineFile, entries: Iterable[TimelineEntry], metadata_root: Path) -> Iterable[TimelineEntry]:
    if file.file_path.name.lower().endswith('.n26.csv'):
        for line in csv.DictReader(codecs.iterdecode(file.file_path.open('rb'), 'utf-8'), delimiter=',', quotechar='"'):
            # No timezone attached. Assume current system timezone.
            transaction_date = datetime.strptime(line['Date'], '%Y-%m-%d').astimezone()
            entries.append(
                TimelineEntry(
                    file_path=file.file_path,
                    checksum=file.checksum,
                    entry_type=EntryType.TRANSACTION,
                    date_start=transaction_date,
                    date_end=None,
                    data={
                        'account': 'N26',
                        'amount': line['Amount (EUR)'],  # String, not number
                        'otherParty': line['Payee'],
                        'description': '' if line['Payment reference'] == '-' else line['Payment reference'],
                    }
                )
            )
    return entries
