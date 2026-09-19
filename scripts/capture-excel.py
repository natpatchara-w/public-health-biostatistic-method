#!/usr/bin/env python3
"""Extract saved native Excel values without calculating or rewriting the workbook.

Run after executing the documented worksheet formulas and ToolPak test in Excel:
  python3 scripts/capture-excel.py _build/excel-verification.xlsx --version 16.113
The temporary verification workbook has Sheet1 with key/value columns D/E and
ToolPak result with the unmodified standard unequal-variance output in A1:C13.
"""
import argparse
import csv
import hashlib
import json
import posixpath
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def sheet_values(path):
    with ZipFile(path) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(x.itertext()) for x in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        rels = {x.attrib['Id']: posixpath.normpath(posixpath.join('xl', x.attrib['Target']))
                for x in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        result = {}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS):
            target = rels[sheet.attrib['{'+NS['r']+'}id']].lstrip('/')
            cells = {}
            for cell in ET.fromstring(archive.read(target)).findall('.//s:sheetData/s:row/s:c', NS):
                v = cell.find('s:v', NS)
                value = v.text if v is not None else None
                if cell.attrib.get('t') == 'e':
                    raise ValueError(f"Excel error in {sheet.attrib['name']}!{cell.attrib['r']}: {value}")
                if cell.attrib.get('t') == 's' and value is not None:
                    value = shared[int(value)]
                elif value is not None:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                cells[cell.attrib['r']] = value
            result[sheet.attrib['name']] = cells
        return result

def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workbook', type=Path)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    sheets = sheet_values(args.workbook)
    formulas = sheets['Sheet1']
    toolpak = sheets['ToolPak result']
    assert toolpak['B4'] == formulas['E2'] == 123
    assert toolpak['C4'] == formulas['E3'] == 135
    assert toolpak['B6'] == toolpak['C6'] == 8
    assert abs(toolpak['B9'] - formulas['E12']) < 1e-10
    assert abs(toolpak['B13'] - formulas['E15']) < 1e-10
    out = Path('topics/hypothesis-testing/_examples/independent-t-test')
    output = out / 'excel-output.csv'
    rows = [(formulas[f'D{r}'], formulas[f'E{r}']) for r in range(2, 17)]
    rows += [('toolpak_p_value', toolpak['B12'])]
    with output.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['key', 'value'])
        writer.writerows(rows)
    table = out / 'excel-toolpak.csv'
    with table.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Statistic', 'Group A / result', 'Group B'])
        for r in range(4, 14):
            writer.writerow([toolpak.get(f'{c}{r}', '') for c in 'ABC'])
    provenance_path = out / 'provenance.json'
    provenance = json.loads(provenance_path.read_text())
    provenance['excel'] = {
        'application': 'Microsoft Excel for Mac', 'version': args.version,
        'verified_utc': datetime.now(timezone.utc).isoformat(),
        'source_md5': md5('topics/hypothesis-testing/data/independent-t-test.csv'),
        'verification_workbook_md5': md5(args.workbook),
        'output_md5': md5(output), 'toolpak_output_md5': md5(table),
        'method': 'Native Excel T.TEST(two-tailed, type=3), worksheet formulas, and Analysis ToolPak Two-Sample Assuming Unequal Variances',
        'download_workbook': 'Recalculated, input-change tested, saved and reopened in Excel without a repair prompt.'
    }
    provenance_path.write_text(json.dumps(provenance, indent=2)+'\n')
    print(f'Captured {len(rows)} values from native Excel {args.version}.')
