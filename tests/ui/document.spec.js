const { test, expect: baseExpect } = require('@playwright/test');

const expect = baseExpect.configure({ timeout: 5_000 });

test.use({ storageState: { cookies: [], origins: [] } });

async function waitForOpsResponse(page, pathnameMatches, action) {
  const [response] = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.request().method() === 'GET' &&
        pathnameMatches(new URL(response.url()).pathname),
      { timeout: 5_000 }
    ),
    action(),
  ]);

  expect(response.ok(), `OPS request failed: ${response.url()}`).toBeTruthy();
  return response;
}

test('navigates document details for EP666666', async ({ page }) => {
  test.setTimeout(30_000);

  const response = await page.goto('/navigator/');
  expect(response && response.ok()).toBeTruthy();
  await expect(page.locator('#querybuilder-area')).toBeVisible();
  await page.waitForFunction(() => Boolean(window.navigatorApp?.project));

  // Numberlist mode selects OPS for the document search.
  await page
    .locator('#querybuilder-flavor-chooser [data-value="numberlist"]')
    .click();
  await expect(page.locator('#datasource label[data-value="ops"]')).toBeVisible();
  await expect(page.locator('#numberlist')).toBeVisible();
  await page.locator('#numberlist').fill('EP666666');

  const searchResponse = await waitForOpsResponse(
    page,
    (path) => path === '/api/ops/published-data/search',
    () => page.getByRole('button', { name: 'Start search', exact: true }).click()
  );
  const expression = new URL(searchResponse.url()).searchParams.get('expression');
  expect(expression).toMatch(/EP0?666666/i);

  // OPS may include the leading zero and a kind code in the displayed number.
  const document = page.locator(
    '.ops-collection-entry:is([data-document-number^="EP0666666"], ' +
      '[data-document-number^="EP666666"])'
  );
  await expect(document).toHaveCount(1);
  await expect(document.locator('.document-title')).toBeVisible();

  const button = (type) =>
    document.locator(`.document-details-chooser button[data-details-type="${type}"]`);
  const panel = (type) =>
    document.locator(
      `.document-details > [id^="document-details-${type}-container-"]`
    );

  await expect(button('biblio')).toHaveClass(/\bactive\b/);
  await expect(panel('biblio')).toBeVisible();

  for (const type of ['description', 'claims']) {
    await expect(button(type)).toBeVisible();

    await waitForOpsResponse(
      page,
      (path) => path.startsWith('/api/ops/') && path.endsWith(`/${type}`),
      () => button(type).click()
    );

    await expect(button(type)).toHaveClass(/\bactive\b/);
    await expect(panel(type)).toBeVisible();

    // The source label and a nonempty paragraph exclude the fallback message.
    await expect(
      panel(type).locator('[data-area="text"]:visible .datasource-label')
    ).toHaveText('EPO/OPS');
    await expect(
      panel(type)
        .locator('[data-area="text"]:visible .keyword p')
        .filter({ hasText: /\S/ })
        .first()
    ).toBeVisible();
  }

  await expect(panel('description')).toBeHidden();

  await waitForOpsResponse(
    page,
    (path) =>
      path.startsWith('/api/ops/publication/') &&
      path.endsWith('/family/inpadoc'),
    () => button('family').click()
  );

  const family = panel('family');
  await expect(button('family')).toHaveClass(/\bactive\b/);
  await expect(family).toBeVisible();
  await expect(panel('claims')).toBeHidden();

  const compactButton = family.locator('button[data-view-type="compact"]');
  const fullButton = family.locator('button[data-view-type="verbose"]');
  await expect(compactButton).toHaveClass(/\bactive\b/);

  const compactRow = family
    .locator('#ops-family-compact-collection tbody tr')
    .filter({ has: page.locator('a.anchor-pdf') })
    .first();
  await expect(compactRow).toBeVisible();
  await expect(compactRow.locator('td').nth(1)).toContainText(/[A-Z]{2}.*\d{3}/);

  await waitForOpsResponse(
    page,
    (path) =>
      path.startsWith('/api/ops/publication/') &&
      path.endsWith('/family/inpadoc'),
    () => fullButton.click()
  );

  await expect(fullButton).toHaveClass(/\bactive\b/);
  await expect(compactButton).not.toHaveClass(/\bactive\b/);
  const fullRow = family
    .locator('#ops-family-verbose-verbose-collection tbody tr')
    .first();
  await expect(fullRow).toBeVisible();
  await expect(fullRow.locator('td').nth(1)).toContainText(/[A-Z]{2}.*\d{3}/);

  await button('biblio').click();
  await expect(button('biblio')).toHaveClass(/\bactive\b/);
  await expect(panel('biblio')).toBeVisible();
  await expect(family).toBeHidden();
});
