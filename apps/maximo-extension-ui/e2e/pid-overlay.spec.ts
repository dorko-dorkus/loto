import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import ts from 'typescript';

declare global {
  interface Window {
    applyPidOverlay: (svg: SVGSVGElement, overlay: any) => void;
  }
}

// Load and transpile the overlay script so it can run in the browser context
const overlaySrcPath = path.join(__dirname, '../src/lib/pidOverlay.ts');
let overlaySrc = fs.readFileSync(overlaySrcPath, 'utf8').replace(/export /g, '');
const overlayJs = ts.transpileModule(overlaySrc, {
  compilerOptions: { module: ts.ModuleKind.None }
}).outputText + '\nwindow.applyPidOverlay = applyPidOverlay;';

test('renders overlay with viewBox and nested groups', async ({ page }) => {
  const svgPath = path.join(__dirname, 'fixtures', 'nested.svg');
  const svg = fs.readFileSync(svgPath, 'utf8');
  await page.setContent(`<html><body>${svg}</body></html>`);
  await page.addScriptTag({ content: overlayJs });
  await page.evaluate(() => {
    const svgEl = document.querySelector('svg') as SVGSVGElement;
    window.applyPidOverlay(svgEl, {
      highlight: ['#target'],
      badges: [{ selector: '#target', type: 'asset' }],
      paths: []
    });
  });
  const screenshot = await page.screenshot({ fullPage: true });
  const baseline = fs
    .readFileSync(path.join(__dirname, 'pid-overlay-linux.base64'), 'utf8')
    .trim();
  expect(screenshot.toString('base64')).toBe(baseline);
});
