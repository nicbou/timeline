from pathlib import Path
from timeline.models import TimelineFile, TimelineEntry, EntryType
from datetime import datetime
from decimal import Decimal
import codecs
import csv


def process_degiro_transactions(file: TimelineFile, metadata_root: Path):
    if not file.file_path.name.lower().endswith('.degiro.csv'):
        return

    for line in csv.DictReader(codecs.iterdecode(file.file_path.open('rb'), 'utf-8'), delimiter=',', quotechar='"'):
        # No timezone attached. Assume current system timezone.
        transaction_date = datetime.strptime(f"{line['Datum']} {line['Uhrzeit']}", '%d-%m-%Y %H:%M').astimezone()
        share_price = Decimal(line['Kurs'].strip())
        quantity = abs(int(line['Anzahl'].strip()))
        buy_or_sell = "Sell" if line['Anzahl'].startswith('-') else "Buy"

        yield TimelineEntry(
            file_path=file.file_path,
            checksum=file.checksum,
            entry_type=EntryType.TRANSACTION,
            date_start=transaction_date,
            date_end=None,
            data={
                'account': 'Degiro',
                'amount': line['Gesamt'].strip(),  # String, not number
                'otherParty': 'Degiro',
                'description': f"{buy_or_sell} {quantity} {line['Produkt'].strip()} shares at {share_price:,.2f} per share",
            }
        )
