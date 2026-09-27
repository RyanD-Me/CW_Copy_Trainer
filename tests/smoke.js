// 簡易動作確認: ページを開いて主要な画面を操作し、JSエラーが出ないことを確かめる。
// 実行: npm i -D playwright && npx playwright install chromium && node tests/smoke.js
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('file://' + path.resolve(__dirname, '..', 'index.html'));

  // 練習モード: 各出題セットで問題を作って判定まで進める
  const sets = await page.$$eval('#charsetSel option', os => os.map(o => o.value));
  for (const v of sets) {
    await page.selectOption('#charsetSel', v);
    await page.fill('#guessInput', 'X');
    await page.click('#checkBtn');
    const ans = await page.textContent('#fbAnswer');
    if (!ans || /undefined/.test(ans)) errors.push(`bad answer for ${v}: ${ans}`);
    await page.click('#nextBtn');
  }

  // スコアアタック: 全モード×全コンテストで開始→途中終了
  await page.click('#tabAttack');
  for (const m of ['practice', 'callsign', 'number', 'contest']) {
    const contests = (m === 'number' || m === 'contest') ? ['allja', 'fd', 'okayama', 'acag'] : [null];
    for (const c of contests) {
      await page.selectOption('#atkMode', m);
      if (c) await page.selectOption('#atkContest', c);
      await page.click('#atkStartBtn');
      await page.waitForTimeout(2700);
      const st = await page.textContent('#atkStatus');
      if (!/受信中/.test(st)) errors.push(`${m}/${c}: status "${st}"`);
      await page.click('#atkQuitBtn');
      await page.click('#modalOk');
    }
  }

  // localStorage に細工した値が入っていても、スクリプトが動かず画面も壊れないこと
  await page.evaluate(() => {
    localStorage.setItem('cwtrainer.highscores', JSON.stringify([
      { id: 'x"><img src=x onerror=window.__xss=1>', score: '<img src=x onerror=window.__xss=1>', name: '<img src=x onerror=window.__xss=1>',
        wc: '<img src=x onerror=window.__xss=1>', wf: 14, mode: 'practice', date: '<x>' },
      { id: 'ok', score: 3, name: '<img src=x onerror=window.__xss=1>', wc: 20, wf: 14, mode: 'practice', date: '2026-01-01T00:00:00Z' }]));
    localStorage.setItem('cwtrainer.settings', JSON.stringify({ atkMode: 'bogus', atkContest: 'bogus', charset: 'bogus', wc: 'x' }));
  });
  await page.reload();
  await page.click('#tabAttack');
  await page.waitForTimeout(200);
  if (await page.evaluate(() => window.__xss === 1)) errors.push('script ran from a crafted high score record');
  const rows = await page.$$eval('#hsBody tr', rs => rs.length);
  if (rows !== 1) errors.push(`expected 1 valid high score row, got ${rows}`);
  await page.evaluate(() => localStorage.clear());

  await browser.close();
  if (errors.length) { console.error('FAIL', errors); process.exit(1); }
  console.log('OK');
})();
