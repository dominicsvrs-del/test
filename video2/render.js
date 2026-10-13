// Renders index.html frame-by-frame (with sub-frame motion blur) to MP4 via ffmpeg.
const {chromium}=require('playwright'); const {spawn}=require('child_process'); const fs=require('fs');
const FPS=30, SUB=+process.env.SUB||3, DUR=+process.argv[2]||30.4, OUT=process.argv[3]||'frames.mp4';
(async()=>{
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
  await p.goto('file://'+__dirname+'/index.html'); await p.waitForFunction('window.READY');
  fs.writeFileSync(__dirname+'/sfx.json',JSON.stringify(await p.evaluate('SFX()'),null,1));
  const ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate',String(FPS*SUB),'-c:v','mjpeg','-i','-',
    '-vf',`tmix=frames=${SUB}:weights='${Array(SUB).fill(1).join(' ')}',select='not(mod(n\\,${SUB}))',setpts=N/${FPS}/TB`,'-r',String(FPS),'-c:v','libx264','-crf','16','-preset','medium','-pix_fmt','yuv420p',OUT],{stdio:['pipe','inherit','inherit']});
  const N=Math.ceil(DUR*FPS*SUB);
  for(let i=0;i<N;i++){
    await p.evaluate(t=>render(t),i/(FPS*SUB));
    const buf=await p.screenshot({type:'jpeg',quality:94});
    if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));
    if(i%270==0) console.log('frame',i,'/',N);
  }
  ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await b.close(); console.log('done');
})();
