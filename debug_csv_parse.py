#!/usr/bin/env python3
"""Debug CSV line parsing."""

import csv
from io import StringIO

# Read first data line from layanan_PPB.csv
with open('documents/layanan_PPB.csv', 'r', encoding='utf-8') as f:
    header_line = f.readline().strip()
    data_line = f.readline().strip()

print("Header line:")
print(repr(header_line[:100]))

print("\nData line:")
print(repr(data_line[:100]))

# Parse header
headers = [h.strip().strip('"') for h in header_line.split(',')]
print(f"\nHeaders ({len(headers)}): {headers}")

# Parse data line
try:
    reader = csv.reader(StringIO(data_line))
    values = next(reader)
    print(f"\nValues ({len(values)}): ")
    for i, v in enumerate(values):
        preview = v[:60] + '...' if len(v) > 60 else v
        print(f"  {i}: {preview}")
except Exception as e:
    print(f"Error parsing: {e}")
    values = data_line.split(',')
    print(f"Fallback split ({len(values)}): {values[:3]}")

# Map headers to values
print("\nMapped key-value pairs:")
for i, header in enumerate(headers):
    if i < len(values):
        value = values[i].strip().strip('"')
        preview = value[:50] + '...' if len(value) > 50 else value
        print(f"  {header}: {preview}")
