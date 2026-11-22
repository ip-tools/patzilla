const { test, expect } = require('@playwright/test');

test.use({ storageState: { cookies: [], origins: [] } });

const actionsToggle =
  '#project-chooser-actions > .btn-group:not(#project-chooser-list) > button';
const editor = '#project-name-editor .editable-container';

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

  await page.waitForFunction((expectedName) => {
    const app = window.navigatorApp;
    return Boolean(
      app?.project &&
      app.project.get('name') === expectedName &&
      app.options.config.get('project') === expectedName
    );
  }, name);
  await expect(page.locator('#project-chooser-name')).toHaveText(name);
}

async function pasteNumbers(page, text) {
  await page.locator('#basket').evaluate((element, clipboardText) => {
    const clipboardData = new DataTransfer();
    clipboardData.setData('text/plain', clipboardText);
    element.dispatchEvent(new ClipboardEvent('paste', {
      bubbles: true,
      cancelable: true,
      clipboardData,
    }));
  }, text);
}

async function prepareExport(page) {
  await createProject(page, 'Export test');
  await pasteNumbers(page, 'EP1000000A1');
  await expect(page.locator('.basket-entry-count')).toHaveText('1');

  // Isolate dialog mechanics from live-view URL generation.
  await page.evaluate(() => {
    window.navigatorApp.basketModel.get_numberlist_url_liveview = () =>
      Promise.resolve('https://example.test/shared');
  });

  await page.locator('#dossier-export-button').click();
  await expect(page.locator('#export-dialog')).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await openNavigator(page);
});

test('does not export an empty basket', async ({ page }) => {
  await expect(page.locator('.basket-entry-count')).toHaveText('0');
  await page.locator('#dossier-export-button').click();

  await expect(page.locator('.mdc-snackbar__label')).toHaveText(
    "An empty collection can't be exported, please add some documents."
  );
  await expect(page.locator('#export-dialog')).toBeHidden();
});

test('updates document content when the dialog is reopened', async ({ page }) => {
  await prepareExport(page);

  const dialog = page.locator('#export-dialog');
  const display = dialog.locator('.export-format[data-value="display"]');
  const share = dialog.locator('.export-format[data-value="link_embed"]');

  await expect(dialog.locator('#export_title')).toHaveText('Export test');
  await display.click();
  await expect(dialog.locator('#output-format')).toHaveText('Display');
  await expect(dialog.locator('#display-content')).toBeVisible();
  await expect(dialog.locator('#result-count-rated')).toHaveText('#1');
  await expect(dialog.locator('#result-content-rated')).toHaveValue('EP1000000A1');
  await expect(dialog.locator('#result-count-seen')).toHaveText('#0');
  await expect(dialog.locator('#result-content-seen')).toHaveValue('');

  await share.click();
  await expect(dialog.locator('#display-content')).toBeHidden();
  await expect(dialog.locator('#link-embed-content')).toBeVisible();
  await expect(dialog.locator('#share-link-external'))
    .toHaveValue('https://example.test/shared');
  const internalURL = await dialog.locator('#share-link-numberlist').inputValue();
  expect(new URL(internalURL, page.url()).searchParams.get('numberlist'))
    .toBe('EP1000000A1');

  await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
  await expect(dialog).toBeHidden();

  await pasteNumbers(page, 'US1234567A');
  await expect(page.locator('.basket-entry-count')).toHaveText('2');
  await page.locator('#dossier-export-button').click();
  await expect(dialog).toBeVisible();
  await display.click();

  await expect(dialog.locator('#result-count-rated')).toHaveText('#2');
  await expect.poll(async () => (
    await dialog.locator('#result-content-rated').inputValue()
  ).split('\n').sort()).toEqual(['EP1000000A1', 'US1234567A']);
});

test('validates output format and ZIP content selection', async ({ page }) => {
  await prepareExport(page);

  const dialog = page.locator('#export-dialog');
  const status = dialog.locator('#export-dialog-status-text');
  const send = dialog.locator('#export-dialog-send-button');
  const zip = dialog.locator('.export-format[data-value="zip"]');
  const reports = dialog.locator('.export-content[data-name="report"]');
  const reportAll = dialog.locator(
    '[data-name="report"] [data-toggle="select-all"]'
  );

  await send.click();
  await expect(status).toHaveText('Please select output format.');
  await expect(dialog.locator('#export-dialog-spinner')).toBeHidden();

  await zip.click();
  await expect(dialog.locator('#output-format')).toHaveText('ZIP');
  await expect(dialog.locator('#zip-content')).toBeVisible();
  await send.click();
  await expect(status).toHaveText('Please choose any report or media format.');

  await reportAll.click();
  await expect(reports.locator('[aria-pressed="true"]')).toHaveCount(0);
  await expect(dialog.locator(
    '.export-content[data-name="report"][aria-pressed="true"]'
  )).toHaveCount(5);
  await expect(dialog.locator('#report-parts'))
    .toHaveText('Workbook, Text report, PDF report, CSV, JSON');

  await reportAll.click();
  await expect(dialog.locator(
    '.export-content[data-name="report"][aria-pressed="true"]'
  )).toHaveCount(0);
  await expect(dialog.locator('#report-parts')).toHaveText('');
});
