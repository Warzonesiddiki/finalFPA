import csv

import pytest


def test_debug_csv():
    filepath = r"C:\Users\Tahir\Documents\GitHub\finalFPA\sample-data\d365_gl_actuals.csv"
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        print(f"Fields: {reader.fieldnames}")
        for i, row in enumerate(reader):
            if i > 2:
                break
            print(f"Row {i}: {row}")


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
