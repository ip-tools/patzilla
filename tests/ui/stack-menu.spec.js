const { test, expect } = require('@playwright/test');

test.use({ storageState: { cookies: [], origins: [] } });

test('reopens the stack menu and restores focus after Escape', async ({ page }) => {
  const response = await page.goto('/navigator/');
  expect(response?.ok()).toBe(true);
  await page.waitForFunction(() => Boolean(window.navigatorApp?.project));

  // Load a result, as in tests/ui/document.spec.js.
  await page.locator('#querybuilder-flavor-chooser [data-value="numberlist"]').click();
  await page.locator('#numberlist').fill('EP666666');
  await page.getByRole('button', { name: 'Start search', exact: true }).click();

  await expect(page.locator(
    '.ops-collection-entry:is([data-document-number^="EP0666666"], ' +
    '[data-document-number^="EP666666"])'
  )).toHaveCount(1);

  await page.locator('#region-stack-opener + .btn-group > button').click();
  await page.locator('.action-select-documents').click();

  const opener = page.locator('#region-stack-opener md-outlined-button');
  const menu = page.locator('md-menu.stack-menu');
  await expect(opener).toBeVisible();

  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));

  for (let i = 0; i < 3; i++) {

    // Open the menu.
    await opener.click();
    await expect(menu).toHaveCount(1);
    await expect(menu).toHaveJSProperty('open', true);
    //await expect(opener).toHaveAttribute('aria-expanded', 'true');

    // Close the menu again.
    await page.keyboard.press('Escape');

    // Verify the menu was closed.
    await expect(menu).toHaveJSProperty('open', false);
    //await expect(opener).toHaveAttribute('aria-expanded', 'false');
    await expect.poll(() =>
      opener.evaluate((element) => document.activeElement === element)
    ).toBe(true);
  }

  expect(pageErrors).toEqual([]);
});
