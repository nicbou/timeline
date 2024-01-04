from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry, EntryType
from datetime import datetime
import codecs
import csv


def process_kontist_transactions(file: TimelineFile, metadata_root: Path):
    if not file.file_path.name.lower().endswith('.kontist.csv'):
        return

    for line in csv.DictReader(codecs.iterdecode(file.file_path.open('rb'), 'latin-1'), delimiter=';', quotechar='"'):
        # No timezone attached. Assume current system timezone.
        transaction_date = datetime.strptime(line['Wertstellungsdatum'], '%Y-%m-%d').astimezone()
        yield TimelineEntry(
            file_path=file.file_path,
            checksum=file.checksum,
            entry_type=EntryType.TRANSACTION,
            date_start=transaction_date,
            date_end=None,
            data={
                'account': 'Kontist',
                'amount': line['Betrag'].replace(',', '.'),  # String, not number
                'otherParty': line['Empfänger'],
                'description': line['Verwendungszweck'],
            }
        )
