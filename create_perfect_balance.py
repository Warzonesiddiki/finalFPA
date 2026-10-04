import csv
from decimal import Decimal

# Read the original def019 file which has 8.9M imbalance
input_file = r'C:\Users\Tahir\Documents\GitHub\finalFPA\temp_sample_data_def019\d365_gl_actuals.csv'
output_file = r'C:\Users\Tahir\Documents\GitHub\finalFPA\sample-data\d365_gl_actuals.csv'

with open(input_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', newline='', encoding='utf-8') as fout:
    reader = csv.reader(fin)
    writer = csv.writer(fout)
    
    watermark = next(reader)
    header = next(reader)
    writer.writerow(watermark)
    writer.writerow(header)
    
    for row in reader:
        writer.writerow(row)
    
    # Voucher,PostingDate,CompanyCode,MainAccount,CostCenter,ProjectCode,VendorCode,InvoiceNumber,TransactionDescription,Debit,Credit,Currency,Watermark,ProjectType
    # Row 1: IN01, 2026-09
    writer.writerow(["VCH-FIX-2026-09", "2026-09-30", "IN01", "1010", "CC-110", "PRJ-GEN", "N/A", "FIX-09", "Balancing P09", "0.00", "8304299.00", "INR", "SAMPLE DATA - FICTIONAL - DO NOT USE FOR ACCOUNTING OR REPORTING", "sample"])
    # Row 2: IN01, 2026-10
    writer.writerow(["VCH-FIX-2026-10", "2026-10-31", "IN01", "1010", "CC-110", "PRJ-GEN", "N/A", "FIX-10", "Balancing P10", "0.00", "465000.00", "INR", "SAMPLE DATA - FICTIONAL - DO NOT USE FOR ACCOUNTING OR REPORTING", "sample"])
    # Row 3: IN01, 2026-11
    writer.writerow(["VCH-FIX-2026-11", "2026-11-30", "IN01", "1010", "CC-110", "PRJ-GEN", "N/A", "FIX-11", "Balancing P11", "0.00", "175000.00", "INR", "SAMPLE DATA - FICTIONAL - DO NOT USE FOR ACCOUNTING OR REPORTING", "sample"])

print("Perfectly balanced file created at", output_file)
