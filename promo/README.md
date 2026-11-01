# Promo video generator

Produces `yt-dlp-gui-promo.mp4` (720x1280, 30 fps, 38 s) – a desk/monitor
UI motion video with kinetic typography, camera moves and a beat-synced track.

- `scene.html` – the whole animation, driven by `window.render(t)` (seconds)
- `render.js` – Playwright frame renderer (`node render.js <outdir> 30 38 [start end]`)
- `audio.py` – numpy-only soundtrack synth; hit times match the scene timeline
- `wall.png`, `grain.png` – baked static layers (keeps per-frame render fast)

Build:

```bash
node render.js frames 30 38
python3 audio.py track.wav
ffmpeg -framerate 30 -i frames/f%05d.png -i track.wav -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 192k -shortest yt-dlp-gui-promo.mp4
```
