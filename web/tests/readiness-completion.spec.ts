import { test, expect } from "@playwright/test";

test("readiness synthetic source is labelled and clearing removes source and checklist", async ({ page }) => {
  await page.goto('/#/readiness');
  const source = page.getByLabel('Choose a synthetic source posting (optional)', { exact: true });
  await expect(source).toBeEnabled();
  await source.selectOption({ index: 1 });
  await expect(page.getByLabel('Job description', { exact: true })).toHaveValue(/Synthetic example only[.]/);
  await expect(page.getByText('All 30 fixtures are fictional Data Analyst examples,', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Extract requirements', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Conditions to check with the source.' })).toBeVisible();
  await expect(page.getByText('No condition cues detected.', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Clear all', exact: true }).click();
  await expect(source).toHaveValue('');
  await expect(page.getByRole('heading', { name: 'Conditions to check with the source.' })).toHaveCount(0);
});

test("provenance and listing conditions stay outside skill scoring, scenario retains baseline", async ({ page }) => {
  const readinessBodies: string[] = [];
  page.on('request', request => { if (request.method() === 'POST') readinessBodies.push(request.postData() || ''); });
  await page.goto('/#/readiness');
  await page.getByLabel('Job description', { exact: true }).fill('SQL is required. Python is preferred. A degree or equivalent experience is accepted. Right to work in Ireland.');
  await page.getByRole('button', { name: 'Extract requirements', exact: true }).click();
  const qualification = page.getByLabel('Your private checklist: Qualification or grade', { exact: true });
  await expect(qualification).toHaveValue('unknown');
  await qualification.selectOption('clarify');
  await page.getByLabel('Evidence status for SQL', { exact: true }).selectOption('missing');
  await page.getByLabel('Evidence status for Python', { exact: true }).selectOption('supported');
  await page.getByLabel('Evidence provenance for Python', { exact: true }).selectOption('coursework_linked');
  await page.getByLabel('Evidence note for Python', { exact: true }).fill('PRIVATE_PROVENANCE_NOTE assessed coursework');
  await page.getByRole('button', { name: 'Assess my evidence', exact: true }).click();
  await expect(page.getByRole('cell', { name: 'Coursework-linked', exact: true })).toBeVisible();
  await page.getByLabel('Requirement to explore', { exact: true }).selectOption({ label: 'SQL · required' });
  await page.getByLabel('Planned evidence', { exact: true }).fill('A reproducible SQL project');
  await page.getByRole('button', { name: 'Compare hypothetical evidence', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Submitted baseline comparison' })).toContainText('25 / 100');
  await expect(page.getByRole('region', { name: 'Hypothetical comparison', exact: true })).toContainText('100 / 100');
  await expect(qualification).toHaveValue('clarify');
  expect(readinessBodies.every(body => !body.includes('appears_met') && !body.includes('"clarify"'))).toBeTruthy();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download analysis', exact: true }).click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  let contents = '';
  for await (const chunk of stream!) contents += chunk;
  expect(contents).toContain('coursework_linked');
  expect(contents).not.toContain('PRIVATE_PROVENANCE_NOTE');
  expect(contents).not.toContain('Right to work');
  expect(JSON.parse(contents)).not.toHaveProperty('condition_answers');
  expect(JSON.parse(contents)).not.toHaveProperty('listing_conditions');
});

test("only manually changed classifications become user-confirmed in reports", async ({ page }) => {
  await page.goto('/#/readiness');
  await page.getByLabel('Job description', { exact: true }).fill('SQL is required. Python is preferred.');
  await page.getByRole('button', { name: 'Extract requirements', exact: true }).click();
  await expect(page.getByLabel('Confirm classification for SQL', { exact: true })).toHaveValue('required');
  await page.getByRole('button', { name: 'Assess my evidence', exact: true }).click();
  async function getReport() {
    const pending = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download analysis', exact: true }).click();
    const download = await pending;
    const stream = await download.createReadStream();
    let contents = '';
    for await (const chunk of stream!) contents += chunk;
    return JSON.parse(contents);
  }
  const untouched = await getReport();
  expect(untouched.requirements.every((r: any) => r.classification_provenance === 'rule-extracted')).toBeTruthy();
  expect(untouched.requirements.every((r: any) => r.classification_corrected === false)).toBeTruthy();
  await page.getByLabel('Confirm classification for Python', { exact: true }).selectOption('required');
  await page.getByRole('button', { name: 'Assess my evidence', exact: true }).click();
  const corrected = await getReport();
  expect(corrected.requirements.find((r: any) => r.skill_id === 'python')).toMatchObject({
    classification_provenance: 'user-confirmed', classification_corrected: true,
    extracted_requirement_type: 'preferred', requirement_type: 'required',
  });
  expect(corrected.requirements.find((r: any) => r.skill_id === 'sql')).toMatchObject({
    classification_provenance: 'rule-extracted', classification_corrected: false,
  });
  expect(corrected.total_weight).toBe(6);
});
