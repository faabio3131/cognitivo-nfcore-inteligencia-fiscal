import { test, expect } from '@playwright/test';

test('browser trial survives committed response loss and provisions one canonical owner/subscription', async ({ page }) => {
  test.skip(!process.env.NFCORE_TEST_POSTGRES_DSN, 'Disposable PostgreSQL required; mandatory in CI');
  const origin = 'https://127.0.0.1:4176';
  let lost = false;
  let firstKey;
  await page.route('**/v1/public/trials', async route => {
    const key = route.request().headers()['idempotency-key'];
    const upstream = await route.fetch();
    if (!lost) {
      expect(upstream.status()).toBe(201);
      expect(await upstream.text()).not.toContain('reset_token');
      firstKey = key;
      lost = true;
      await route.fulfill({ status: 503, json: { detail: 'synthetic response loss after commit' } });
    } else {
      expect(key).toBe(firstKey);
      expect(upstream.status()).toBe(200);
      expect((await upstream.json()).replay).toBe(true);
      await route.fulfill({ response: upstream });
    }
  });
  await page.goto(`${origin}/trial.html`);
  await page.getByLabel('Nome da empresa').fill('Empresa Browser Sintética');
  await page.getByLabel('E-mail para ativação').fill('browser-owner@example.test');
  await page.getByRole('button', { name: 'Solicitar teste' }).click();
  await expect(page.locator('#trial-result')).toContainText('mesmos dados');
  const before = await (await page.request.get(`${origin}/__test/trial-proof`)).json();
  expect(Object.values(before.counts)).toEqual([1, 1, 1, 1]);
  expect(before.deliveries).toBe(1);
  await page.reload();
  await page.getByLabel('Nome da empresa').fill('Empresa Browser Sintética');
  await page.getByLabel('E-mail para ativação').fill('browser-owner@example.test');
  await page.getByRole('button', { name: 'Solicitar teste' }).click();
  await expect(page.locator('#trial-result')).toContainText('Confira seu e-mail');
  const after = await (await page.request.get(`${origin}/__test/trial-proof`)).json();
  expect(after.counts).toEqual(before.counts);
  expect(after.subscription_id).toBe(before.subscription_id);
  expect(after.deliveries).toBe(2);
  expect(await page.content()).not.toContain(after.reset_token);
  const password = 'Synthetic-Trial-Browser-2026';
  const activated = await page.request.post(`${origin}/v1/auth/password-reset/complete`, {
    data: { reset_token: after.reset_token, new_password: password },
  });
  expect(activated.status()).toBe(204);
  const login = await page.request.post(`${origin}/v1/auth/login`, {
    data: { email: 'browser-owner@example.test', password },
  });
  expect(login.status()).toBe(200);
  const final = await (await page.request.get(`${origin}/__test/trial-proof`)).json();
  expect(final.counts).toEqual(before.counts);
});
