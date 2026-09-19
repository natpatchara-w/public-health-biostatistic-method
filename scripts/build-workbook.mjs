// Optional authoring utility: requires @oai/artifact-tool in the authoring runtime.
// The exported workbook is committed; this script is not part of quarto render.
import fs from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const summary = JSON.parse(await fs.readFile('_build/summary.json', 'utf8'));
const outputPath = process.argv[2] || '_build/independent-t-test-unverified.xlsx';
const wb = Workbook.create();
const formulaRows = [
  [13, 'Difference in means (mmHg)', '=B7-C7', 'Group A minus Group B'],
  [14, 'Group A contribution', '=B8^2/B6', 'Square the SD, then divide by sample size'],
  [15, 'Group B contribution', '=C8^2/C6', 'Square the SD, then divide by sample size'],
  [16, 'Standard error (mmHg)', '=SQRT(B14+B15)', 'Square root of the sum of the two contributions'],
  [17, 'Test statistic t', '=(B13-B10)/B16', 'Difference from the null value, divided by standard error'],
  [18, 'First df denominator term', '=B14^2/(B6-1)', 'Use the Group A contribution and sample size'],
  [19, 'Second df denominator term', '=B15^2/(C6-1)', 'Use the Group B contribution and sample size'],
  [20, 'Welch degrees of freedom', '=(B14+B15)^2/(B18+B19)', 'Keep this decimal value for comparison with software'],
  [21, 'Reference-table row', '=ROUND(B20,0)', 'Round to the nearest whole number, as in class'],
  [22, 'Two-sided critical value', '=T.INV.2T(B9,B21)', 'Use the significance level and rounded table row'],
  [23, 'Absolute test statistic', '=ABS(B17)', 'Compare this value with the critical value'],
  [24, 'Decision', '=IF(B23>B22,"Reject H0","Do not reject H0")', 'Reject H0 only when the absolute statistic exceeds the cutoff'],
];
for (const name of ['Practice', 'Worked solution']) {
  const worked = name === 'Worked solution';
  const sh = wb.worksheets.add(name);
  sh.showGridLines = false;
  sh.tabColor = worked ? '#194E75' : '#66788A';
  const all = sh.getRange('A1:D30');
  all.format.font = {name:'Arial',size:11,color:'#233444'};
  all.format.rowHeight = 25;
  all.format.verticalAlignment = 'center';
  sh.getRange('A1:A30').format.columnWidth = 32;
  sh.getRange('B1:C30').format.columnWidth = 21;
  sh.getRange('D1:D30').format.columnWidth = 77;
  sh.getRange('A2').values = [[worked ? 'Welch t-test: worked solution' : 'Welch t-test: practice']];
  sh.getRange('A2').format.font = {name:'Arial',size:16,bold:true,color:'#194E75'};
  sh.getRange('A2:D2').format.rowHeight = 32;
  sh.getRange('A2:D2').format.borders = {bottom:{style:'thin',color:'#194E75'}};
  sh.getRange('A3').values = [['Two independent groups. Supplied means and standard deviations.']];
  sh.getRange('A4').values = [['Synthetic blood pressure example (mmHg). Source: independent-t-test.csv.']];
  sh.getRange('A3:D4').format.font = {name:'Arial',size:10,color:'#536575'};
  sh.getRange('A5:D10').values = [
    ['Supplied information','Group A','Group B','Meaning'],
    ['Sample size',summary.n1,summary.n2,'Number of independent observations'],
    ['Mean (mmHg)',summary.m1,summary.m2,'Population comparison uses A minus B'],
    ['Standard deviation (mmHg)',summary.s1,summary.s2,'Use these supplied values; underlying precision is retained'],
    ['Significance level',summary.alpha,null,'Two-sided test; 5% level'],
    ['Null difference (mmHg)',0,null,'H0: equal population means; H1: different population means'],
  ];
  sh.getRange('B6:C8').format.fill = '#FFF4D5';
  sh.getRange('B9:B10').format.fill = '#FFF4D5';
  sh.getRange('B6:C7').setNumberFormat('0');
  sh.getRange('B8:C8').setNumberFormat('0.000000');
  sh.getRange('B9').setNumberFormat('0%');
  sh.getRange('A12:D12').values = [['Calculation','Result',null,worked?'Formula and explanation':'Enter a formula in each amber result cell']];
  for (const row of [5,12]) {
    sh.getRange(`A${row}:D${row}`).format.fill = '#194E75';
    sh.getRange(`A${row}:D${row}`).format.font = {name:'Arial',size:11,bold:true,color:'#FFFFFF'};
  }
  for (const [row,label,formula,explanation] of formulaRows) {
    sh.getRange(`A${row}`).values = [[label]];
    sh.getRange(`B${row}`).setNumberFormat(row===21?'0':'0.000000');
    sh.getRange(`D${row}`).values = [[worked ? `'${formula}  —  ${explanation}` : explanation]];
    sh.getRange(`D${row}`).format.wrapText = true;
    sh.getRange(`A${row}:D${row}`).format.rowHeight = row===24 ? 50 : 42;
    if (worked) sh.getRange(`B${row}`).formulas = [[formula]];
    else sh.getRange(`B${row}`).format.fill = '#FFF4D5';
    if (row % 2 === 0) sh.getRange(`A${row}`).format.fill = '#F2F6F9';
  }
  sh.getRange('A24:D24').format.borders = {top:{style:'thin',color:'#194E75'}};
  sh.getRange('B24').format.font = {name:'Arial',size:11,bold:true,color:'#194E75'};
  sh.getRange('B24').format.wrapText = true;
  sh.getRange('A26').values = [['Interpret the result']];
  sh.getRange('A26').format.font = {name:'Arial',size:11,bold:true,color:'#194E75'};
  sh.getRange('A27').values = [[worked ? 'For the supplied example, Group A’s sample mean is 12 mmHg lower.' : 'Write your conclusion: direction, size of the difference, and the test decision.']];
  sh.getRange('A28').values = [[worked ? 'At the 5% level, the test gives evidence that the population means differ.' : 'Use the Worked solution tab to check your calculations after completing the exercise.']];
  sh.getRange('A29').values = [['A test result alone does not establish causation.']];
  sh.getRange('A30').values = [['Amber cells are inputs or practice answers. Keep calculations unrounded; round only the table row.']];
  sh.getRange('A30:D30').format.font = {name:'Arial',size:10,color:'#536575'};
}
wb.recalculate();
const worked = wb.worksheets.getItem('Worked solution');
const expected = {13:summary.difference,16:summary.se,17:summary.t_stat,20:summary.df,21:summary.df_class};
for (const [row,value] of Object.entries(expected)) {
  const actual=worked.getRange(`B${row}`).values[0][0];
  if (typeof actual !== 'number' || Math.abs(actual-value)>1e-8) throw Error(`B${row}: expected ${value}, found ${actual}`);
}
// This artifact-tool runtime cannot evaluate T.INV.2T correctly. Preserve the
// native Excel formula; Excel must recalculate and save the exported file.
// Final critical-value/decision checks are made against that native saved file.
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:20},summary:'Formula error check'})).ndjson);
await fs.mkdir('_build/workbook-preview',{recursive:true});
for (const name of ['Practice','Worked solution']) {
  const png = await wb.render({sheetName:name,range:'A1:D21',scale:1.5,format:'png'});
  await fs.writeFile(`_build/workbook-preview/${name.toLowerCase().replaceAll(' ','-')}.png`,new Uint8Array(await png.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(outputPath);
execFileSync('python3', ['scripts/prepare-workbook.py', outputPath], {stdio:'inherit'});
console.log('Workbook exported; basic arithmetic verified. Native Excel recalculation of T.INV.2T and decision is required before delivery.');
