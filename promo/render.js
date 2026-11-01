// Renders promo/scene.html frame-by-frame with Playwright into a PNG sequence.
// usage: node render.js <outdir> [fps] [duration] [start] [end]
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
(async()=>{
 const out=process.argv[2]||'frames', fps=+(process.argv[3]||30), dur=+(process.argv[4]||38);
 const start=+(process.argv[5]||0), end=+(process.argv[6]||dur);
 fs.mkdirSync(out,{recursive:true});
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:720,height:1280},deviceScaleFactor:1});
 await p.goto('file://'+path.resolve(__dirname,'scene.html'));await p.waitForTimeout(300);
 const n0=Math.round(start*fps), n1=Math.round(end*fps);
 for(let i=n0;i<n1;i++){const t=i/fps;await p.evaluate(t=>window.render(t),t);
   await p.screenshot({path:path.join(out,`f${String(i).padStart(5,'0')}.png`),type:'png'});
   if(i%60===0)console.log('frame',i,'/',n1)}
 await b.close();
})();
