
import csv

input_file = r'C:\Users\Tahir\Documents\GitHub\finalFPA\sample-data\d365_gl_actuals.csv'
output_file = r'C:\Users\Tahir\Documents\GitHub\finalFPA\balanced_d365_gl_actuals.csv'

# Imbalance was: Total Debit: 15656391730.54, Total Credit: 15647447431.54, Imbalance: 8944299.00 (Debit > Credit)
# Need to add a credit line of 8,944,299.00

with open(input_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', newline='', encoding='utf-8') as fout:
    reader = csv.reader(fin)
    writer = csv.writer(fout)
    
    # Read the first two lines (watermark and header)
    watermark = next(reader)
    header = next(reader)
    
    writer.writerow(watermark)
    writer.writerow(header)
    
    for row in reader:
        writer.writerow(row)
    
    # Add balancing row
    # Voucher,PostingDate,CompanyCode,MainAccount,CostCenter,ProjectCode,VendorCode,InvoiceNumber,TransactionDescription,Debit,Credit,Currency,Watermark,ProjectType
    balancing_row = ["VCH-FIX-2026-1003", "2026-10-03", "IN01", "1010", "CC-110", "PRJ-GEN", "N/A", "FIX-001", "Correction for Trial Balance", "0.00", "8944299.00", "INR", "SAMPLE DATA - FICTIONAL - DO NOT USE FOR ACCOUNTING OR REPORTING", "sample"]
    writer.writerow(balancing_row)

print("Balanced file created at", output_file)
