const { test, expect } = require('@playwright/test');

test.use({ storageState: { cookies: [], origins: [] } });

const chooserName = '#project-chooser-name';
const projectList = '#project-chooser-list';
const actionsToggle =
  '#project-chooser-actions > .btn-group:not(#project-chooser-list) > button';
const editor = '#project-name-editor .editable-container';

async function waitForActiveProject(page, name) {

  // The chooser renders before the basket has finished loading.
  await page.waitForFunction((expectedName) => {
    const app = window.navigatorApp;
    return Boolean(
      app?.project &&
        app.project.get('name') === expectedName &&
        app.options.config.get('project') === expectedName
    );
  }, name);

  await expect(page.locator(chooserName)).toHaveText(name);
  await expect(page.locator('#basket')).toBeVisible();
}

async function openNavigator(page) {
  const response = await page.goto('/navigator/');
  expect(response?.ok()).toBe(true);
  await expect(page.locator('#basket')).toBeVisible();
}

async function createProject(page, name) {
  await page.locator(actionsToggle).click();
  await page.locator('#project-create-button').click();
  await expect(page.locator(editor)).toBeVisible();
  await page.locator(`${editor} .editable-input input`).fill(name);
  await page.locator(`${editor} .editable-submit`).click();
  await waitForActiveProject(page, name);
}

async function switchProject(page, name) {
  await page.locator(`${projectList} > button`).click();

  const entry = page
    .locator(`${projectList} .dropdown-menu a`)
    .filter({ has: page.getByText(name, { exact: true }) });

  await expect(entry).toHaveCount(1);
  await entry.click();
  await waitForActiveProject(page, name);
}

async function pasteNumbers(page, text) {
  // Dispatch a paste event with clipboard data. The application handles the
  // event and performs its normal asynchronous saves and rerenders.
  await page.locator('#basket').evaluate((element, clipboardText) => {
    const clipboardData = new DataTransfer();
    clipboardData.setData('text/plain', clipboardText);
    element.dispatchEvent(
      new ClipboardEvent('paste', {
        bubbles: true,
        cancelable: true,
        clipboardData,
      })
    );
  }, text);
}

async function expectBasket(page, numbers) {
  await expect(page.locator('.basket-entry-count')).toHaveText(
    String(numbers.length)
  );
  await expect(page.locator('.basket-seen-count')).toHaveText('0');

  // The application pads each displayed number and may append rating marks.
  await expect
    .poll(async () => {
      const value = await page.locator('#basket').inputValue();
      return value
        .split('\n')
        .map((line) => line.trim().split(/\s+/)[0])
        .filter(Boolean)
        .sort();
    })
    .toEqual([...numbers].sort());
}

test.beforeEach(async ({ page }) => {
  await openNavigator(page);
});

test('warns when an empty basket is reviewed', async ({ page }) => {
  await expectBasket(page, []);
  await page.locator('#basket-review-button').click();

  const label = page.locator('md-gb-snackbar [part="label"]');
  await expect(label).toBeVisible();
  await expect(label).toHaveText(
    "An empty collection can't be reviewed, please add some documents."
  );
  await expectBasket(page, []);
});

test('imports pasted numbers and restores them after reload', async ({ page }) => {
  await createProject(page, 'Paste test');
  await expectBasket(page, []);

  await pasteNumbers(page, 'EP1000000A1\nUS1234567A');
  await expectBasket(page, ['EP1000000A1', 'US1234567A']);

  // Select the project again after navigation to check persisted content.
  await openNavigator(page);
  await switchProject(page, 'Paste test');
  await expectBasket(page, ['EP1000000A1', 'US1234567A']);
});

test('keeps basket content separate between projects', async ({ page }) => {
  await createProject(page, 'Alpha');
  await pasteNumbers(page, 'EP1000000A1');
  await expectBasket(page, ['EP1000000A1']);

  await createProject(page, 'Beta');
  await expectBasket(page, []);
  await pasteNumbers(page, 'US1234567A');
  await expectBasket(page, ['US1234567A']);

  await switchProject(page, 'Alpha');
  await expectBasket(page, ['EP1000000A1']);

  await switchProject(page, 'Beta');
  await expectBasket(page, ['US1234567A']);

  await openNavigator(page);
  await switchProject(page, 'Alpha');
  await expectBasket(page, ['EP1000000A1']);
  await switchProject(page, 'Beta');
  await expectBasket(page, ['US1234567A']);
});
