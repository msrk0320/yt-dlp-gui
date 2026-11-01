// Usage: node snap.js out_dir t1 t2 ...   -> contact sheet frames for quick review
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [out, ...ts] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + path.resolve(__dirname, 'promo.html') + '?render=1');
  await p.evaluate(() => document.fonts.ready);
  for (const t of ts) {
    await p.evaluate(t => window.seek(t), +t);
    await p.screenshot({ path: `${out}/t_${(+t).toFixed(2).padStart(6, '0')}.jpg`, quality: 70, type: 'jpeg' });
  }
  if (errs.length) console.log('ERRORS', errs);
  await b.close();
})();
