const { test, expect } = require('@playwright/test');

// Each test gets a clean browser context, including a new localforage database.
test.use({ storageState: { cookies: [], origins: [] } });

const SORTS = {
  applicationDate: { field: 'ad', label: 'Application date' },
  reclassifiedIpc: { field: 'mcsf', label: 'Reclassified IPC (MCD)' },
};

const SEARCH_PATH = '/api/depatisnet/published-data/search';

async function openQueryBuilder(page) {
  const response = await page.goto('/navigator/');
  expect(response && response.ok()).toBeTruthy();

  await expect(page.locator('#querybuilder-area')).toBeVisible();

  // Project activation is asynchronous. History requires an active project.
  await page.waitForFunction(() => Boolean(window.navigatorApp?.project));

  const dpma = page.locator('#datasource label[data-value="depatisnet"]');
  await expect(dpma).toBeVisible();

  if (!(await dpma.evaluate((element) => element.classList.contains('active')))) {
    await dpma.click();
  }

  await expect(page.locator('#sorting-chooser')).toBeVisible();
}

async function chooseSortField(page, sort) {
  const selection = page.locator(
    '#sort-field-chooser + .select2 .select2-selection'
  );

  await selection.click();
  await page.getByRole('option', { name: sort.label, exact: true }).click();
  await expect(page.locator('#sort-field-chooser')).toHaveValue(sort.field);
}

async function expectSort(page, sort, order) {
  const field = page.locator('#sort-field-chooser');
  const icon = page.locator('#sort-order-chooser i');

  if (!sort) {
    await expect(field).toHaveValue('');
    await expect(icon).toHaveClass(/glyphicon-resize-vertical/);
    return;
  }

  await expect(field).toHaveValue(sort.field);
  await expect(
    page.locator('#sort-field-chooser + .select2 .select2-selection__rendered')
  ).toContainText(sort.label);

  const iconClass =
    order === 'asc'
      ? /glyphicon-sort-by-alphabet(?:\s|$)/
      : /glyphicon-sort-by-alphabet-alt(?:\s|$)/;

  await expect(icon).toHaveClass(iconClass);
}

async function submitSearch(page) {
  const [response] = await Promise.all([
    page.waitForResponse((response) => {
      const request = response.request();
      return (
        new URL(response.url()).pathname === SEARCH_PATH &&
        request.method() === 'POST'
      );
    }),
    page.getByRole('button', { name: 'Start search', exact: true }).click(),
  ]);

  expect(response.ok()).toBeTruthy();

  return new URLSearchParams(response.request().postData() || '');
}

function expectRequestSorting(params, sort, order) {
  const fieldKey = 'query_data[sorting][field]';
  const orderKey = 'query_data[sorting][order]';

  if (!sort) {
    expect(
      [...params.keys()].filter((key) => key.startsWith('query_data[sorting]'))
    ).toEqual([]);
    return;
  }

  expect(params.getAll(fieldKey)).toEqual([sort.field]);
  expect(params.getAll(orderKey)).toEqual([order]);
}

async function waitForHistoryEntry(page, flavor, sort, order) {
  // Read application state only to wait for the asynchronous history save.
  // The test does not replace the project or history implementation.
  await expect
    .poll(
      () =>
        page.evaluate(
          ({ flavor, field, order }) => {
            const queries = window.navigatorApp?.project?.get('queries');
            return Boolean(
              queries &&
                queries.some((query) => {
                  const data = query.get('query_data') || {};
                  const sorting = data.sorting;
                  return (
                    query.get('flavor') === flavor &&
                    (field
                      ? sorting?.field === field && sorting?.order === order
                      : !sorting)
                  );
                })
            );
          },
          { flavor, field: sort?.field || null, order }
        ),
      { message: 'The search should be saved to the active project history' }
    )
    .toBe(true);
}

async function restoreHistoryEntry(page, marker, sort, order) {
  await page.locator('#btn-query-history').click();

  const entry = page
    .locator('.select2-results__option:visible')
    .filter({ hasText: marker });

  await expect(entry).toHaveCount(1);
  if (sort) {
    await expect(entry).toContainText(`${sort.field}:${order}`);
  }

  await entry.click();
}

test.beforeEach(async ({ page }) => {
  // This synthetic successful response records the query without fetching
  // publication details from OPS. It does not simulate the real DPMA service.
  await page.route(`**${SEARCH_PATH}*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        meta: {
          navigator: { count_total: 0, count_page: 0, max_hits: 1000, limit: 10 },
        },
        details: [],
      }),
    });
  });

  await openQueryBuilder(page);
});

test('switches query modes and clears Standard form values', async ({ page }) => {
  const applicant = page.locator(
    '#querybuilder-comfort-form input[name="applicant"]'
  );

  await applicant.fill('Siemens');
  await page.locator('#querybuilder-comfort-actions').click();
  await page.locator('#btn-comfort-clear').click();
  await expect(applicant).toHaveValue('');

  await page.locator('#querybuilder-flavor-chooser [data-value="cql"]').click();
  await expect(page.locator('#query')).toBeVisible();
  await expect(page.locator('#btn-query-history')).toBeVisible();

  await page
    .locator('#querybuilder-flavor-chooser [data-value="numberlist"]')
    .click();
  await expect(page.locator('#numberlist')).toBeVisible();
  await expect(page.locator('#cql-history-chooser')).toBeHidden();

  await page
    .locator('#querybuilder-flavor-chooser [data-value="comfort"]')
    .click();
  await expect(applicant).toBeVisible();
  await expect(page.locator('#btn-query-history')).toBeVisible();
});

test('replaces and clears a sort field and cycles the direction', async ({
  page,
}) => {
  await chooseSortField(page, SORTS.applicationDate);
  await expectSort(page, SORTS.applicationDate, 'asc');

  await page.locator('#sort-order-chooser').click();
  await expectSort(page, SORTS.applicationDate, 'desc');

  await page.locator('#sort-order-chooser').click();
  await expect(page.locator('#sort-order-chooser i')).toHaveClass(
    /glyphicon-resize-vertical/
  );

  await page.locator('#sort-order-chooser').click();
  await expectSort(page, SORTS.applicationDate, 'asc');

  await chooseSortField(page, SORTS.reclassifiedIpc);
  await expectSort(page, SORTS.reclassifiedIpc, 'asc');
  await expect(
    page.locator('#sort-field-chooser option:checked')
  ).toHaveCount(1);

  await page
    .locator('#sort-field-chooser + .select2 .select2-selection__clear')
    .click();
  await expect(page.locator('#sort-field-chooser')).toHaveValue('');
});

const historyCases = [
  { name: 'application date ascending', sort: SORTS.applicationDate, order: 'asc' },
  { name: 'reclassified IPC descending', sort: SORTS.reclassifiedIpc, order: 'desc' },
  { name: 'no sorting', sort: null, order: null },
];

for (const flavor of ['comfort', 'cql']) {
  for (const { name, sort, order } of historyCases) {
    test(`${flavor} history restores ${name}`, async ({ page }) => {
      const marker = 'SIEMENS';
      const applicant = page.locator(
        '#querybuilder-comfort-form input[name="applicant"]'
      );
      const expression = page.locator('#query');

      if (flavor === 'comfort') {
        await applicant.fill(marker);
      } else {
        await page.locator('#querybuilder-flavor-chooser [data-value="cql"]').click();
        await expect(expression).toBeVisible();
        await expression.fill(`pa=${marker}`);
      }

      if (sort) {
        await chooseSortField(page, sort);
        if (order === 'desc') {
          await page.locator('#sort-order-chooser').click();
        }
        await expectSort(page, sort, order);
      }

      const originalRequest = await submitSearch(page);
      expectRequestSorting(originalRequest, sort, order);
      await waitForHistoryEntry(page, flavor, sort, order);

      // Change both the query and the sorting before restoring the entry.
      if (flavor === 'comfort') {
        await applicant.fill('Changed');
      } else {
        await expression.fill('pa=Changed');
      }

      const replacement =
        sort?.field === SORTS.applicationDate.field
          ? SORTS.reclassifiedIpc
          : SORTS.applicationDate;
      await chooseSortField(page, replacement);

      await restoreHistoryEntry(page, marker, sort, order);
      await expectSort(page, sort, order);

      if (flavor === 'comfort') {
        await expect(applicant).toHaveValue(marker);
      } else {
        await expect(expression).toHaveValue(`pa=${marker}`);
      }

      const restoredRequest = await submitSearch(page);
      expectRequestSorting(restoredRequest, sort, order);
    });
  }
}
