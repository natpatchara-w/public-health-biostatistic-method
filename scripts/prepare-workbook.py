#!/usr/bin/env python3
"""Repair only the authoring engine's unsupported inverse-t formula serialization.

Do not synthesize results: native Excel must calculate and save this staged file.
The final delivered workbook has already passed that native verification.
"""
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET

path = Path(sys.argv[1])
ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
ET.register_namespace('', ns)
with ZipFile(path) as z:
    entries = {item.filename: (item, z.read(item.filename)) for item in z.infolist()}
name = 'xl/worksheets/sheet2.xml'
root = ET.fromstring(entries[name][1])
for cell in root.findall(f'.//{{{ns}}}c'):
    if cell.attrib['r'] not in ('B22', 'B24'):
        continue
    formula = cell.find(f'{{{ns}}}f')
    if formula is None:
        raise ValueError('Expected the retained native Excel formula')
    if cell.attrib['r'] == 'B22':
        formula.text = '_xlfn.T.INV.2T(B9,B21)'
    for value in cell.findall(f'{{{ns}}}v'):
        cell.remove(value)
    cell.attrib.pop('t', None)
entries[name] = (entries[name][0], ET.tostring(root, encoding='utf-8', xml_declaration=True))
name = 'xl/workbook.xml'
root = ET.fromstring(entries[name][1])
calc = root.find(f'{{{ns}}}calcPr')
if calc is None:
    calc = ET.SubElement(root, f'{{{ns}}}calcPr')
calc.set('calcMode', 'auto')
calc.set('fullCalcOnLoad', '1')
calc.set('forceFullCalc', '1')
entries[name] = (entries[name][0], ET.tostring(root, encoding='utf-8', xml_declaration=True))
staged = path.with_suffix('.prepared.xlsx')
with ZipFile(staged, 'w', ZIP_DEFLATED) as z:
    for info, content in entries.values():
        z.writestr(info, content)
staged.replace(path)
print('Preserved inverse-t formulas; cleared unsupported caches for native recalculation.')
