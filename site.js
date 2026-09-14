(() => {
  "use strict";
  const canvas = document.getElementById("development-canvas");
  const ctx = canvas.getContext("2d");
  const matrixCanvas = document.getElementById("matrix-canvas");
  const mctx = matrixCanvas.getContext("2d");
  const armEl = document.getElementById("arm");
  const seedEl = document.getElementById("seed");
  const ageEl = document.getElementById("age");
  const stateEl = document.getElementById("state");
  const connectionEl = document.getElementById("connection-count");
  const topoEl = document.getElementById("topographic-error");
  const meanPathEl = document.getElementById("mean-path");
  const branchEl = document.getElementById("branch-count");

  const ARMS = new Set(["guided", "shuffled_labels", "random_walk"]);
  const N = 8, STEPS = 56, STEP = 0.025, CAPTURE = 0.05, SIGMA = 0.11, THRESHOLD = 0.72;
  const turns = [-60,-30,0,30,60].map(v => v * Math.PI / 180);
  let sim, paused = false, last = 0;

  function rngFromSeed(seed) {
    let s = (seed >>> 0) || 1;
    return () => { s += 0x6D2B79F5; let t=s; t=Math.imul(t^t>>>15,t|1); t^=t+Math.imul(t^t>>>7,t|61); return ((t^t>>>14)>>>0)/4294967296; };
  }
  function gaussian(rng) { const u=Math.max(rng(),1e-9), v=rng(); return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v); }
  function ys() { return Array.from({length:N},(_,i)=>0.12+0.76*i/(N-1)); }
  function compatible(a,b) { const d=(a-b); return Math.exp(-(d*d)/(2*SIGMA*SIGMA)); }
  function shuffle(a,rng){ const b=a.slice(); for(let i=b.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[b[i],b[j]]=[b[j],b[i]];} if(b.every((v,i)=>v===a[i])) b.push(b.shift()); return b; }

  function reset() {
    const seed = Number(seedEl.value) || 0;
    const arm = armEl.value;
    if (!ARMS.has(arm)) throw new Error(`unknown developmental arm: ${arm}`);
    const growthRng = rngFromSeed(seed * 9973 + 9107);
    const labelRng = rngFromSeed(seed * 9973 + 9106);
    const y = ys();
    const labels = arm === "shuffled_labels" ? shuffle(y,labelRng) : y.slice();
    const dendrites=[];
    const offsets=[[-.10,0],[-.13,-.025],[-.13,.025],[-.16,-.045],[-.16,.045],[-.07,-.018],[-.07,.018]];
    y.forEach((yy,r)=>offsets.forEach(([dx,dy])=>dendrites.push({receiver:r,x:.88+dx,y:Math.max(0,Math.min(1,yy+dy))})));
    const tips=y.map((yy,i)=>({sender:i,heading:0,points:[[.08,yy]],alive:true,path:0,branchIndex:i}));
    sim={seed,arm,rng:growthRng,y,labels,dendrites,tips,branchesMade:Array(N).fill(0),nextBranch:N,synapses:[],pairs:new Set(),age:0};
    paused=false; document.getElementById("pause").textContent="Pause"; updateMetrics(); draw();
  }

  function crowding(x,y){ let best=0; for(const tip of sim.tips) for(const p of tip.points){const dx=x-p[0],dy=y-p[1],d2=dx*dx+dy*dy; best=Math.max(best,Math.exp(-d2/(2*.035*.035)));} return best; }
  function advanceTip(tip){
    if(!tip.alive) return;
    const [cx,cy]=tip.points[tip.points.length-1], targetY=sim.labels[tip.sender], chemo=sim.arm!=="random_walk";
    const current=Math.hypot(.78-cx,targetY-cy); let best=null;
    for(const turn of turns){ const h=tip.heading+turn, x=cx+STEP*Math.cos(h), y=cy+STEP*Math.sin(h); if(x<0||x>1||y<0||y>1) continue;
      const next=Math.hypot(.78-x,targetY-y); const score=14*(chemo?(current-next):0)+.22*Math.cos(turn)-.08*crowding(x,y)+.035*gaussian(sim.rng);
      if(!best||score>best.score) best={score,x,y,h}; }
    if(!best){tip.alive=false;return;} tip.points.push([best.x,best.y]); tip.heading=best.h; tip.path+=STEP;
    for(const d of sim.dendrites){ const key=`${tip.sender}:${d.receiver}`; if(sim.pairs.has(key)) continue; if(Math.hypot(best.x-d.x,best.y-d.y)<=CAPTURE){ const w=compatible(sim.labels[tip.sender],sim.y[d.receiver]); if(w>=THRESHOLD){sim.pairs.add(key);sim.synapses.push({sender:tip.sender,receiver:d.receiver,w,path:tip.path,x:best.x,y:best.y});}}}
    if(best.x>=.96){tip.alive=false;return;}
    if(sim.branchesMade[tip.sender]<2 && tip.points.length>=5 && sim.rng()<.045){ const dir=sim.rng()<.5?-1:1; sim.tips.push({sender:tip.sender,heading:tip.heading+dir*42*Math.PI/180,points:[[best.x,best.y]],alive:true,path:tip.path,branchIndex:sim.nextBranch++}); sim.branchesMade[tip.sender]++; }
  }
  function step(){ if(sim.age>=STEPS){stateEl.textContent="frozen";return;} const current=sim.tips.slice(); current.forEach(advanceTip); sim.age++; updateMetrics(); draw(); }

  function sx(x){return 45+x*(canvas.width-90)} function sy(y){return 30+y*(canvas.height-60)}
  function draw(){
    ctx.clearRect(0,0,canvas.width,canvas.height); ctx.fillStyle="#07100c";ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.strokeStyle="#12231a";ctx.lineWidth=1; for(let i=1;i<10;i++){ctx.beginPath();ctx.moveTo(i*canvas.width/10,0);ctx.lineTo(i*canvas.width/10,canvas.height);ctx.stroke();}
    ctx.strokeStyle="#365447";ctx.lineWidth=1.4; for(let r=0;r<N;r++){const pts=sim.dendrites.filter(d=>d.receiver===r); const cx=sx(.88),cy=sy(sim.y[r]); for(const d of pts){ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(sx(d.x),sy(d.y));ctx.stroke();}}
    sim.tips.forEach((tip,idx)=>{ctx.strokeStyle=`hsla(${85+(tip.sender*18)},80%,68%,${tip.alive ? .78 : .42})`;ctx.lineWidth=idx<N?2.2:1.3;ctx.beginPath();tip.points.forEach((p,i)=>i?ctx.lineTo(sx(p[0]),sy(p[1])):ctx.moveTo(sx(p[0]),sy(p[1])));ctx.stroke();});
    for(let i=0;i<N;i++){ctx.fillStyle="#b9ff66";ctx.beginPath();ctx.arc(sx(.08),sy(sim.y[i]),6,0,Math.PI*2);ctx.fill();ctx.fillStyle="#6fe8d5";ctx.beginPath();ctx.arc(sx(.88),sy(sim.y[i]),7,0,Math.PI*2);ctx.fill();}
    ctx.fillStyle="#ffcf70";sim.synapses.forEach(s=>{ctx.beginPath();ctx.arc(sx(s.x),sy(s.y),5,0,Math.PI*2);ctx.fill();});
    drawMatrix(); ageEl.textContent=`age ${sim.age}`;stateEl.textContent=sim.age>=STEPS?"frozen":paused?"paused":"growing";
  }
  function drawMatrix(){mctx.clearRect(0,0,matrixCanvas.width,matrixCanvas.height);mctx.fillStyle="#07100c";mctx.fillRect(0,0,matrixCanvas.width,matrixCanvas.height);const pad=28,cell=(matrixCanvas.width-pad*2)/N; const map=new Map(sim.synapses.map(s=>[`${s.sender}:${s.receiver}`,s.w])); for(let i=0;i<N;i++)for(let j=0;j<N;j++){const w=map.get(`${i}:${j}`)||0;mctx.fillStyle=w?`rgba(185,255,102,${.24+.76*w})`:"#102019";mctx.fillRect(pad+j*cell+2,pad+i*cell+2,cell-4,cell-4);} }
  function updateMetrics(){ const s=sim.synapses;connectionEl.textContent=s.length;branchEl.textContent=sim.tips.length; if(!s.length){topoEl.textContent="—";meanPathEl.textContent="—";return;} topoEl.textContent=(s.reduce((a,v)=>a+Math.abs(sim.y[v.sender]-sim.y[v.receiver])/.76,0)/s.length).toFixed(3);meanPathEl.textContent=(s.reduce((a,v)=>a+v.path,0)/s.length).toFixed(3); }
  function loop(ts){ if(!paused && ts-last>80){step();last=ts;} requestAnimationFrame(loop); }
  document.getElementById("reset").addEventListener("click",reset); armEl.addEventListener("change",reset); seedEl.addEventListener("change",reset);
  document.getElementById("pause").addEventListener("click",e=>{paused=!paused;e.target.textContent=paused?"Resume":"Pause";draw();});
  document.getElementById("step").addEventListener("click",()=>{paused=true;document.getElementById("pause").textContent="Resume";step();});
  reset(); requestAnimationFrame(loop);
})();
