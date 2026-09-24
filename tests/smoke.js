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

  await browser.close();
  if (errors.length) { console.error('FAIL', errors); process.exit(1); }
  console.log('OK');
})();
