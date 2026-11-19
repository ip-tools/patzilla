const { test, expect } = require('@playwright/test');

test.use({ storageState: { cookies: [], origins: [] } });

const chooserName = '#project-chooser-name';
const editor = '#project-name-editor .editable-container';
const projectList = '#project-chooser-list';
const actionsToggle =
  '#project-chooser-actions > .btn-group:not(#project-chooser-list) > button';

async function waitForActiveProject(page, name) {

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
  await expect(page.locator(chooserName)).toBeVisible();
  await expect(page.locator('#basket')).toBeVisible();
}

async function openActions(page) {
  await page.locator(actionsToggle).click();
}

async function startCreate(page) {
  await openActions(page);
  await page.locator('#project-create-button').click();
  await expect(page.locator(editor)).toBeVisible();
}

async function submitEditor(page, value) {
  await page.locator(`${editor} .editable-input input`).fill(value);
  await page.locator(`${editor} .editable-submit`).click();
}

async function createProject(page, name) {
  await startCreate(page);
  await submitEditor(page, name);
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

async function projectId(page) {
  return page.evaluate(() => window.navigatorApp.project.id);
}

async function storedProject(page, id) {
  // Read the datastore to wait for a save or deletion. Do not modify it.
  return page.evaluate(async (projectId) => {
    const dump = await window.navigatorApp.storage.dump();
    return dump.database[`Project/${projectId}`] || null;
  }, id);
}

test.beforeEach(async ({ page }) => {
  await openNavigator(page);
});

test('creates projects, switches between them, and reloads their list', async ({
  page,
}) => {
  await createProject(page, 'Alpha');
  await createProject(page, 'Beta');

  await switchProject(page, 'Alpha');
  await switchProject(page, 'Beta');

  // Start from the base URL rather than assuming the selected project is
  // restored from the current URL.
  await openNavigator(page);
  await switchProject(page, 'Alpha');
  await switchProject(page, 'Beta');
});

test('validates empty and duplicate names during creation', async ({ page }) => {
  await createProject(page, 'Alpha');
  await startCreate(page);

  await submitEditor(page, '');
  await expect(page.locator(`${editor} .editable-error-block`)).toHaveText(
    'Project name must not be empty.'
  );

  await submitEditor(page, 'Alpha');
  await expect(page.locator(`${editor} .editable-error-block`)).toHaveText(
    'Project name already exists.'
  );

  await submitEditor(page, 'Beta');
  await waitForActiveProject(page, 'Beta');
});

test('validates and persists a renamed project', async ({ page }) => {
  await createProject(page, 'Alpha');
  await createProject(page, 'Beta');
  const id = await projectId(page);

  await page.locator(chooserName).click();
  await expect(page.locator(editor)).toBeVisible();

  await submitEditor(page, 'Alpha');
  await expect(page.locator(`${editor} .editable-error-block`)).toHaveText(
    'Project name already exists.'
  );

  await submitEditor(page, 'Gamma');
  await expect(page.locator(chooserName)).toHaveText('Gamma');

  // A rerender can precede completion of the asynchronous save.
  await expect
    .poll(async () => (await storedProject(page, id))?.name)
    .toBe('Gamma');

  await switchProject(page, 'Alpha');
  await switchProject(page, 'Gamma');
  expect(await projectId(page)).toBe(id);

  await openNavigator(page);
  await switchProject(page, 'Gamma');
  expect(await projectId(page)).toBe(id);
});

test('cancels and confirms project deletion', async ({ page }) => {
  await createProject(page, 'Alpha');
  await createProject(page, 'Beta');
  const betaId = await projectId(page);

  await openActions(page);
  await page.locator('#project-delete-button').click();

  var dialog = page.locator('.mdc-dialog');
  await expect(dialog).toContainText('Beta');
  await dialog.locator('[data-mdc-dialog-action="close"]').click();
  await expect(dialog).toBeHidden();
  await waitForActiveProject(page, 'Beta');
  expect((await storedProject(page, betaId))?.name).toBe('Beta');

  await openActions(page);
  await page.locator('#project-delete-button').click();

  dialog = page.locator('.mdc-dialog');
  await expect(dialog).toContainText('Beta');
  await dialog.locator('[data-mdc-dialog-action="confirm"]').click();

  await expect
    .poll(async () => await storedProject(page, betaId))
    .toBeNull();

  await switchProject(page, 'Alpha');

  await openNavigator(page);
  await page.locator(`${projectList} > button`).click();
  await expect(
    page
      .locator(`${projectList} .dropdown-menu a`)
      .filter({ has: page.getByText('Beta', { exact: true }) })
  ).toHaveCount(0);
});
