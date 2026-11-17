const { test, expect } = require('@playwright/test');

test('navigator loads the query builder', async ({ page }) => {
  const response = await page.goto('/navigator/');

  expect(response?.ok()).toBe(true);
  await expect(page.locator('#querybuilder-area')).toBeAttached();
});
