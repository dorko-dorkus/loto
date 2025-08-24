import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore - pdf-parse has no types
import pdfParse from 'pdf-parse';

test('golden path: upload → generate → publish → export PDF', async ({ page }, testInfo) => {
  const downloads: string[] = [];
  page.on('download', async (download) => {
    const filePath = testInfo.outputPath(download.suggestedFilename());
    await download.saveAs(filePath);
    downloads.push(filePath);
  });

  await page.goto('http://localhost:3000/wizard');

  await page.setInputFiles(
    '[data-testid="wizard-upload-input"]',
    path.join(__dirname, '../../../demo/line_list.csv')
  );

  await page.getByRole('button', { name: /generate/i }).click();
  await page.getByRole('button', { name: /publish/i }).click();
  await page.getByRole('button', { name: /export pdf/i }).click();

  await expect.poll(() => downloads.some((f) => f.endsWith('.pdf'))).toBeTruthy();
  await expect.poll(() => downloads.some((f) => f.endsWith('.zip'))).toBeTruthy();

  const pdfPath = downloads.find((f) => f.endsWith('.pdf'))!;
  const zipPath = downloads.find((f) => f.endsWith('.zip'))!;

  expect(fs.existsSync(pdfPath)).toBeTruthy();
  expect(fs.existsSync(zipPath)).toBeTruthy();

  const pdfData = await pdfParse(fs.readFileSync(pdfPath));
  expect(pdfData.numpages).toBeGreaterThan(0);
  expect(pdfData.text.trim().length).toBeGreaterThan(0);

  const zipList = execSync(`unzip -Z1 ${zipPath}`).toString('utf8').trim().split('\n');
  expect(zipList.length).toBeGreaterThan(0);

  const forbidden = ['apikey', 'password', 'secret'];
  const textsToCheck = [pdfData.text.toLowerCase(), execSync(`unzip -p ${zipPath}`).toString('utf8').toLowerCase()];
  for (const text of textsToCheck) {
    for (const word of forbidden) {
      expect(text).not.toContain(word);
    }
  }
});
