from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry, EntryType
from datetime import datetime
import codecs
import csv


def process_n26_transactions(file: TimelineFile, metadata_root: Path):
    if not file.file_path.name.lower().endswith('.n26.csv'):
        return

    for line in csv.DictReader(codecs.iterdecode(file.file_path.open('rb'), 'utf-8'), delimiter=',', quotechar='"'):
        # No timezone attached. Assume current system timezone.
        transaction_date = datetime.strptime(line.get('Booking Date') or line.get('Date'), '%Y-%m-%d').astimezone()
        description = line.get('Payment Reference') or line.get('Payment reference')
        yield TimelineEntry(
            file_path=file.file_path,
            checksum=file.checksum,
            entry_type=EntryType.TRANSACTION,
            date_start=transaction_date,
            date_end=None,
            data={
                'account': 'N26',
                'amount': line['Amount (EUR)'],  # String, not number
                'otherParty': line.get('Partner Name') or line.get('Payee'),
                'description': '' if description == '-' else description,
            }
        )
