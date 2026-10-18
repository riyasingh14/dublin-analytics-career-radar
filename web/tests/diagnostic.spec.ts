import { test, expect } from '@playwright/test';

test('diagnostic traces Unicode evidence and reviews additions without changing the source', async ({ page }) => {
  const original = '📊 Data Analyst\nDublin, permanent, hybrid.\nSQL required. Competitive salary. You will create reports.';
  await page.goto('/#/diagnostic');
  await page.getByLabel('Job description', { exact: true }).fill(original);
  await page.getByRole('button', { name: 'Analyse description' }).click();
  const finding = page.locator('details.finding').filter({ hasText: 'clarity / vague phrase' }).first();
  await finding.locator('summary').click();
  await finding.getByRole('button', { name: 'Locate evidence' }).click();
  await expect(page.getByTestId('diagnostic-highlight')).toHaveText('Competitive salary');
  await expect(page.getByTestId('diagnostic-source')).toHaveText(original);
  await finding.getByLabel('Editable clarification proposal').fill('What is the annual salary range in EUR? [Author to confirm]');
  await finding.getByLabel('Your review').selectOption('Accepted for clarification');
  await expect(page.locator('ins')).toContainText('What is the annual salary range in EUR?');
  await expect(page.getByLabel('Job description', { exact: true })).toHaveValue(original);
  await finding.getByLabel('Your review').selectOption('Dismissed');
  await expect(page.locator('ins')).toHaveCount(0);
  await expect(page.getByTestId('diagnostic-highlight')).toHaveText('Competitive salary');
  const benchmark = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Comparable-posting benchmark' }) });
  await expect(benchmark).toContainText('0 comparable observed postings');
  const waiting = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download report' }).click();
  const download = await waiting;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(Buffer.from(chunk));
  const report = JSON.parse(Buffer.concat(chunks).toString());
  expect(report.review_summary.dismissed).toBe(1);
  expect(JSON.stringify(report)).not.toContain(original);
  expect(report.benchmark_status.available).toBe(false);
});

test('diagnostic absent fields remain absent and source selection stays explicitly synthetic', async ({ page }) => {
  await page.goto('/#/diagnostic');
  await page.getByLabel('Or select a fictional source posting').selectOption('synthetic-0');
  await page.getByRole('button', { name: 'Analyse description' }).click();
  const finding = page.locator('details.finding').filter({ hasText: 'completeness / salary' }).first();
  await finding.locator('summary').click();
  await finding.getByRole('button', { name: 'Locate evidence' }).click();
  await expect(page.getByTestId('diagnostic-highlight')).toHaveCount(0);
  await expect(page.getByText('Absent field: salary. There is no source span to highlight.')).toBeVisible();
  await page.getByRole('button', { name: 'Clear all', exact: true }).click();
  await expect(page.getByTestId('diagnostic-source')).toHaveCount(0);
  await expect(page.getByLabel('Job description', { exact: true })).toHaveValue('');
});
