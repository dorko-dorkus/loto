import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

test('golden path: upload → generate → publish → export PDF', async ({ page }, testInfo) => {
  const downloads: string[] = [];
  page.on('download', async (download) => {
    const filePath = testInfo.outputPath(download.suggestedFilename());
    await download.saveAs(filePath);
    downloads.push(filePath);
  });

  await page.goto('http://localhost:3000/');

  await page.setInputFiles('[data-testid="wizard-upload-input"]', path.join(__dirname, '../../demo/line_list.csv'));

  await page.getByRole('button', { name: /generate/i }).click();
  await page.getByRole('button', { name: /publish/i }).click();
  await page.getByRole('button', { name: /export pdf/i }).click();

  await expect.poll(() => downloads.filter(f => f.endsWith('.pdf')).length).toBeGreaterThan(0);
  const forbidden = ['apikey', 'password', 'secret'];
  for (const file of downloads) {
    expect(fs.existsSync(file)).toBeTruthy();
    let content = '';
    if (file.endsWith('.zip')) {
      content = execSync(`unzip -p ${file}`).toString('utf8');
    } else {
      content = fs.readFileSync(file).toString('utf8');
    }
    for (const word of forbidden) {
      expect(content.toLowerCase()).not.toContain(word);
    }
  }
});
