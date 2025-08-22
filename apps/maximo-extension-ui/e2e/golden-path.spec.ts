import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test('golden path: upload → generate → publish → export PDF', async ({ page }, testInfo) => {
  const downloads: string[] = [];
  page.on('download', async (download) => {
    const filePath = testInfo.outputPath(download.suggestedFilename());
    await download.saveAs(filePath);
    downloads.push(filePath);
  });

  await page.goto('http://localhost:3000/');

  await page.getByRole('button', { name: /upload/i }).click();
  await page.setInputFiles('input[type="file"]', path.join(__dirname, '../../demo/line_list.csv'));

  await page.getByRole('button', { name: /generate/i }).click();
  await page.getByRole('button', { name: /publish/i }).click();
  await page.getByRole('button', { name: /export pdf/i }).click();

  await expect.poll(() => downloads.filter(f => f.endsWith('.pdf')).length).toBeGreaterThan(0);
  for (const file of downloads) {
    expect(fs.existsSync(file)).toBeTruthy();
  }
});
