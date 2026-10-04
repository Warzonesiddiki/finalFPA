
import csv
from decimal import Decimal

# Read the file and calculate imbalance
total_debit = Decimal("0.00")
total_credit = Decimal("0.00")

with open(r'C:\Users\Tahir\Documents\GitHub\finalFPA\sample-data\d365_gl_actuals.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader) # skip header
    next(reader) # skip watermark
    for row in reader:
        # Voucher,PostingDate,CompanyCode,MainAccount,CostCenter,ProjectCode,VendorCode,InvoiceNumber,TransactionDescription,Debit,Credit,Currency,Watermark,ProjectType
        try:
            total_debit += Decimal(row[9])
            total_credit += Decimal(row[10])
        except Exception:
            continue

print(f"Total Debit: {total_debit}")
print(f"Total Credit: {total_credit}")
print(f"Imbalance: {total_debit - total_credit}")
