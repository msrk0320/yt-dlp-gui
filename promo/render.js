// Renders promo.html to MP4 (1920x1080, 60fps). Usage: node render.js [workers]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
// Motion blur: SUB sub-frames per output frame across a 180-degree shutter, averaged by ffmpeg tmix.
const FPS = 60, DUR = 45, N = FPS * DUR, W = +(process.argv[2] || 4), SUB = 4, SHUTTER = .5;
const out = path.resolve(__dirname, 'build'); fs.mkdirSync(out, { recursive: true });
async function worker(i, b) {
  const a = Math.floor(N * i / W), z = Math.floor(N * (i + 1) / W);
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.resolve(__dirname, 'promo.html') + '?render=1');
  await p.evaluate(() => document.fonts.ready);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-c:v', 'mjpeg', '-i', '-',
    '-vf', `tmix=frames=${SUB},select='eq(mod(n,${SUB}),${SUB - 1})',setpts=N/${FPS}/TB`, '-r', String(FPS), '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', `${out}/seg${i}.mp4`], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = a; f < z; f++) {
    for (let k = 0; k < SUB; k++) {
      const t = Math.max(0, f / FPS + ((k + .5) / SUB - .5) * SHUTTER / FPS);
      await p.evaluate(t => window.seek(t), t);
      const buf = await p.screenshot({ type: 'jpeg', quality: 93 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    if (f % 300 === 0) console.log(`worker ${i}: frame ${f}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
(async () => {
  const b = await chromium.launch();
  await Promise.all([...Array(W).keys()].map(i => worker(i, b)));
  await b.close();
  fs.writeFileSync(`${out}/list.txt`, [...Array(W).keys()].map(i => `file 'seg${i}.mp4'`).join('\n'));
  console.log('done');
})();
