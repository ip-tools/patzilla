const { test, expect } = require('@playwright/test');
const { readFile } = require('node:fs/promises');

test.use({ storageState: { cookies: [], origins: [] } });

async function openNavigator(page, { enableIfi = false } = {}) {
  // Capture application:ready before the application starts.
  await page.addInitScript(({ enableIfi }) => {
    let app;

    Object.defineProperty(window, 'navigatorApp', {
      configurable: true,
      get() {
        return app;
      },
      set(value) {
        app = value;

        if (!value || typeof value.once !== 'function') {
          return;
        }

        if (enableIfi) {
          const config = value.options.config;
          const enabled = config.get('datasources_enabled') || [];
          config.set('datasources_enabled', [...new Set([...enabled, 'ificlaims'])]);
        }

        value.once('application:ready', () => {
          // Let the other synchronous application:ready handlers finish.
          setTimeout(() => {
            window.__menuTestReady = true;
          }, 0);
        });
      },
    });
  }, { enableIfi });

  const response = await page.goto('/navigator/');
  expect(response && response.ok()).toBeTruthy();

  await page.waitForFunction(() => window.__menuTestReady === true);
  await expect(page.locator('#menu-region .menu-opener')).toBeVisible();
}

async function openMenu(page) {
  const menu = page.locator('#menu-region .dropdown-menu');
  if (!(await menu.isVisible())) {
    await page.locator('#menu-region .menu-opener').click();
  }
  await expect(menu).toBeVisible();
}

async function renderMenuWith(page, flags) {
  await page.evaluate(({ keywords, storage, ificlaims }) => {
    const app = window.navigatorApp;
    const config = app.options.config;

    const components = (config.get('component_list') || [])
      .filter((name) => name !== 'keywords' && name !== 'storage');
    if (keywords) components.push('keywords');
    if (storage) components.push('storage');

    const datasources = (config.get('datasources_enabled') || [])
      .filter((name) => name !== 'ificlaims');
    if (ificlaims) datasources.push('ificlaims');

    config.set({
      component_list: components,
      datasources_enabled: datasources,
    });

    const header = app.mainView.getRegion('header').currentView;
    const currentMenu = header.getRegion('menu').currentView;
    header.showChildView('menu', new currentMenu.constructor());
  }, flags);
}

test.describe('menu content', () => {
  for (const keywords of [false, true]) {
    for (const storage of [false, true]) {
      for (const ificlaims of [false, true]) {
        test(`renders keywords=${keywords}, storage=${storage}, ificlaims=${ificlaims}`, async ({ page }) => {
          await openNavigator(page);
          await renderMenuWith(page, { keywords, storage, ificlaims });

          const menu = page.locator('#menu-region .dropdown-menu');

          await expect(menu.locator('.action-keyword-editor'))
            .toHaveCount(keywords ? 1 : 0);
          await expect(menu.locator('#data-import-button'))
            .toHaveCount(storage ? 1 : 0);
          await expect(menu.locator('#data-import-file'))
            .toHaveCount(storage ? 1 : 0);
          await expect(menu.locator('#data-export-button'))
            .toHaveCount(storage ? 1 : 0);
          await expect(menu.locator('#database-wipe-button'))
            .toHaveCount(storage ? 1 : 0);
          await expect(menu.locator('.dropdown-header', { hasText: 'Database' }))
            .toHaveCount(storage ? 1 : 0);
          await expect(menu.locator('.action-help-ificlaims'))
            .toHaveCount(ificlaims ? 1 : 0);

          await expect(menu.locator('.action-fullscreen')).toHaveCount(1);
          await expect(menu.locator('.action-help-shortcuts')).toHaveCount(1);
          await expect(menu.locator('.report-issue-feature')).toHaveCount(1);
          await expect(menu.locator('.report-issue-problem')).toHaveCount(1);
          await expect(menu.locator('a[href="/logout"]')).toContainText('Sign out');
        });
      }
    }
  }
});

test.describe('menu actions', () => {
  test('opens and closes the dropdown', async ({ page }) => {
    await openNavigator(page);

    const opener = page.locator('#menu-region .menu-opener');
    const menu = page.locator('#menu-region .dropdown-menu');

    await expect(menu).toBeHidden();
    await opener.click();
    await expect(menu).toBeVisible();
    await opener.click();
    await expect(menu).toBeHidden();
  });

  test('initializes the help links', async ({ page }) => {
    await openNavigator(page, { enableIfi: true });
    await openMenu(page);

    for (const [selector, pathname] of [
      ['.action-help-shortcuts', '/navigator/help/hotkeys'],
      ['.action-help-ificlaims', '/navigator/help/ificlaims'],
    ]) {
      const link = page.locator(`#menu-region ${selector}`);
      await expect(link).toBeVisible();
      await expect(link).toHaveAttribute('target', '_blank');
      await expect.poll(() => link.evaluate((element) => (
        new URL(element.href).pathname
      ))).toBe(pathname);
    }
  });

  test('opens and closes the keyword editor', async ({ page }) => {
    await openNavigator(page);

    // Exercise the editor even when the test user has no keywords-user module.
    await page.evaluate(() => {
      window.navigatorApp.keywords.module_available = true;
    });

    await openMenu(page);
    await page.locator('#menu-region .action-keyword-editor').click();

    const editor = page.locator('#keyword-editor');
    await expect(editor).toBeVisible();
    await expect(editor.locator('#keyword-editor-label')).toHaveText('Keyword editor');
    await editor.getByRole('button', { name: 'Close', exact: true }).last().click();
    await expect(editor).toHaveCount(0);
  });

  for (const [selector, kind, title, remark] of [
    ['.report-issue-feature', 'feature', 'Request feature', 'It would be cool, if ...'],
    ['.report-issue-problem', 'problem', 'Report problem', 'We experienced a problem with ...'],
  ]) {
    test(`opens the ${kind} report dialog without submitting`, async ({ page }) => {
      await openNavigator(page);
      await openMenu(page);
      await page.locator(`#menu-region ${selector}`).click();

      const dialog = page.locator('#issue-reporter-dialog');
      await expect(dialog).toBeVisible();
      await expect(dialog.locator('#issue-reporter-label')).toContainText(title);
      await expect(dialog.locator('#issue-reporter-what')).toHaveValue(kind);
      await expect(dialog.locator('#issue-reporter-remark')).toHaveValue(remark);

      await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
      await expect(dialog).toBeHidden();
    });
  }

  test('exports a database backup', async ({ page }) => {
    await openNavigator(page);
    await openMenu(page);

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('#data-export-button').click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/^ip-navigator-database_.*\.json$/);
    const backup = JSON.parse(await readFile(await download.path(), 'utf8'));
    expect(backup.metadata.type).toBe('patzilla.navigator.database');
    expect(backup.database).toEqual(expect.any(Object));
  });

  test('cancels database import', async ({ page }) => {
    await openNavigator(page);

    await page.evaluate(() => {
      window.__deactivateCalls = 0;
      window.navigatorApp.project_deactivate = () => {
        window.__deactivateCalls += 1;
      };
    });

    await openMenu(page);
    await page.locator('#data-import-button').click();

    const dialog = page.locator('.mdc-dialog > md-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText('Continue import operation?');
    await dialog.locator('[data-mdc-dialog-action="close"]').click();
    await expect(dialog).toBeHidden();
    expect(await page.evaluate(() => window.__deactivateCalls)).toBe(0);
  });

  test('confirms import and opens the file chooser', async ({ page }) => {
    await openNavigator(page);

    await page.evaluate(() => {
      window.__deactivateCalls = 0;
      window.navigatorApp.project_deactivate = () => {
        window.__deactivateCalls += 1;
      };
    });

    await openMenu(page);
    await page.locator('#data-import-button').click();

    const dialog = page.locator('.mdc-dialog > md-dialog');
    await expect(dialog).toBeVisible();
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      dialog.locator('[data-mdc-dialog-action="confirm"]').click(),
    ]);

    expect(chooser.isMultiple()).toBe(false);
    expect(await page.evaluate(() => window.__deactivateCalls)).toBe(1);
    // Do not select a file or start an import.
  });

  test('cancels database wipe', async ({ page }) => {
    await openNavigator(page);

    await page.evaluate(() => {
      window.__resetCalls = [];
      window.navigatorApp.storage.dbreset = (options) => {
        window.__resetCalls.push(options);
      };
    });

    await openMenu(page);
    await page.locator('#database-wipe-button').click();

    const dialog = page.locator('.mdc-dialog > md-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText('All data will be lost.');
    await dialog.locator('[data-mdc-dialog-action="close"]').click(),
    await expect(dialog).toBeHidden();
    expect(await page.evaluate(() => window.__resetCalls)).toEqual([]);
  });

  test('confirms database wipe without clearing data', async ({ page }) => {
    await openNavigator(page);

    await page.evaluate(() => {
      window.__resetCalls = [];
      window.navigatorApp.storage.dbreset = (options) => {
        window.__resetCalls.push(options);
      };
    });

    await openMenu(page);
    await page.locator('#database-wipe-button').click();

    const dialog = page.locator('.mdc-dialog > md-dialog');
    await expect(dialog).toBeVisible();
    await dialog.locator('[data-mdc-dialog-action="confirm"]').click(),
    await expect(dialog).toBeHidden();

    expect(await page.evaluate(() => window.__resetCalls))
      .toEqual([{ shutdown_gui: true }]);
  });

  test('requests fullscreen when supported', async ({ page }) => {
    await openNavigator(page);

    const supported = await page.evaluate(() => document.fullscreenEnabled);
    test.skip(!supported, 'Fullscreen is not enabled in this browser.');

    await openMenu(page);
    const action = page.locator('#menu-region .action-fullscreen');

    // Prevent the link's target="_blank" navigation without blocking its handler.
    await action.evaluate((element) => {
      element.addEventListener('click', (event) => event.preventDefault(), { once: true });
    });
    await action.click();

    await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement)))
      .toBe(true);
    await page.evaluate(() => document.exitFullscreen());
  });
});
