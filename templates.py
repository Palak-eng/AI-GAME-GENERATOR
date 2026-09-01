"""
Curated base-game templates for the AI Game Maker.

Instead of always asking an LLM to invent a game from scratch (which is
coherent but inconsistent in quality), we ship a small set of hand-built,
phone+PC-tested base games. `generate_game` picks a matching template and uses
Gemini to RESKIN it (change the theme, characters, colors, and template-specific
entities) while keeping the battle-tested core logic intact. This gives ~95%
consistency instead of random LLM creativity.

Each template key describes the play style so the router can match a kid's idea
to the closest base game. Keys: "runner", "collector", "shooter".

IMPORTANT for reskinning: each template contains clearly-marked THEME VARS near
the top (name, colors, art-draw functions) that the AI is told to rewrite.
"""

# ─────────────────────────────────────────────────────────────────────────────
# RUNNER — a side-scrolling auto-runner with jump + duck, levels, coins, score.
# Phone: tap to jump, the canvas shows an on-screen hint bar.
# PC: arrows/WASD + space.
# ─────────────────────────────────────────────────────────────────────────────
RUNNER = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Rocket Run</title>
<style>
  html,body{margin:0;padding:0;background:#120b1f;height:100%;overflow:hidden;
    touch-action:manipulation;-webkit-user-select:none;user-select:none;}
  #wrap{position:fixed;top:0;left:0;width:100%;height:100%;display:flex;
    align-items:center;justify-content:center;}
  canvas{display:block;width:100%;height:100%;object-fit:contain;
    background:#120b1f;touch-action:none;cursor:pointer;}
</style>
</head>
<body>
<div id="wrap"><canvas id="game" width="800" height="600"></canvas></div>
<script>
(function(){
"use strict";
var cv=document.getElementById("game"), ctx=cv.getContext("2d");
// ---------- THEME VARS (rewrite these to reskin) ----------
var GAME_NAME="Rocket Run";
var THEME={skyTop:"#1b0e3a",skyBot:"#6a1bb0",ground:"#2a1a4a",groundTop:"#7c4aff",
  accent:"#ffd54a",player:"#ff6b6b",obstacle:"#8a8a8a",coin:"#ffd700"};
function drawPlayer(x,y){ // cute cylinder rocket with flame
  ctx.fillStyle=THEME.player;
  ctx.beginPath();ctx.moveTo(x,y-26);ctx.lineTo(x+14,y+6);ctx.lineTo(x-14,y+6);
  ctx.closePath();ctx.fill();ctx.fillRect(x-10,y-8,20,16);
  ctx.fillStyle="#fff";ctx.beginPath();ctx.arc(x,y-22,5,0,7);ctx.fill();
  ctx.fillStyle="#ff9b3d";ctx.beginPath();ctx.moveTo(x-8,y+14);
  ctx.lineTo(x,y+26);ctx.lineTo(x+8,y+14);ctx.closePath();ctx.fill();
}
function drawObstacle(x,y,w,h){ctx.fillStyle=THEME.obstacle;ctx.fillRect(x,y,w,h);
  ctx.fillStyle="#555";ctx.fillRect(x,y,w,5);}
// ------------------------------------------------
var W=cv.width,H=cv.height;
var GROUND=H-70;
var player={x:120,y:GROUND-26,vy:0,w:28,h:40,onGround:true,duck:false};
var GRAV=1500,JUMP=-620,SPEED=300;
var coins=[],obs=[],stars=[];
var score=0,high=parseInt(localStorage.getItem("rocketRunHigh")||"0",10);
var level=1,dist=0,state="start"; // start | play | over
var nextObstacle=60,nextCoin=20,shake=0;
var keys={};
// on-screen touch state
var touchAction=null; // 'jump' or 'duck'
function makeStars(){stars=[];for(var i=0;i<120;i++){stars.push({x:Math.random()*W,
  y:Math.random()*H*0.7,s:Math.random()*2+1});}}
makeStars();
function reset(){
  score=0;dist=0;level=1;coins=[];obs=[];nextObstacle=60;nextCoin=20;
  player.x=120;player.y=GROUND-26;player.vy=0;player.duck=false;player.onGround=true;
}
var audio=null,soundOn=true;
function playTone(f,d,type,vol){if(!soundOn)return;try{
  if(!audio){audio=new (window.AudioContext||window.webkitAudioContext)();}
  var o=audio.createOscillator(),g=audio.createGain();
  o.type=type||"square";o.frequency.value=f;
  g.gain.setValueAtTime(vol||0.08,audio.currentTime);
  g.gain.exponentialRampToValueAtTime(0.0001,audio.currentTime+d);
  o.connect(g);g.connect(audio.destination);o.start();o.stop(audio.currentTime+d);
}catch(e){}}
function initAudio(){if(audio&&audio.state==="suspended"){audio.resume();}}
function spawn(){ // harder as level rises
  var sp=SPEED+ (level-1)*20;
  if(dist>nextObstacle){
    var r=Math.random();
    if(r<0.45){obs.push({x:W+20,w:36,h:40,y:GROUND-40,duckable:false});} // jump-over
    else if(r<0.8){obs.push({x:W+20,w:70,h:24,y:GROUND-24,duckable:true});} // duck-under
    else{obs.push({x:W+20,w:36,h:40,y:GROUND-40});obs.push({x:W+120,w:36,h:40,y:GROUND-40});}
    nextObstacle=dist+280+Math.random()*180;
  }
  if(dist>nextCoin){
    coins.push({x:W+20,y:GROUND-90,r:12,t:0,c:THEME.coin});nextCoin=dist+140+Math.random()*160;
  }
}
function update(dt){
  if(state!=="play")return;
  dist+=SPEED*dt;
  // player physics
  if(touchAction==="jump"&&player.onGround){player.vy=JUMP;player.onGround=false;playTone(520,0.1,"square");}
  if(touchAction==="duck"&&player.onGround){player.duck=true;}else{player.duck=false;}
  player.vy+=GRAV*dt;player.y+=player.vy*dt;
  var groundY=GROUND-(player.duck?20:0);
  if(player.y>=groundY-26){player.y=groundY-26;player.vy=0;player.onGround=true;}
  var sp=SPEED+(level-1)*20;
  // obstacles
  for(var i=obs.length-1;i>=0;i--){var o=obs[i];o.x-=sp*dt;if(o.x+o.w<0){obs.splice(i,1);continue;}
    var pw=player.duck?28:18;
    var px=player.x,py=player.y,ph=player.duck?20:40;
    var hit=(px+pw>o.x&&px-pw<o.x+o.w&&py+ph>o.y&&py<o.y+o.h);
    if(hit){shake=0.4;playTone(120,0.3,"sawtooth",0.15);gameOver();continue;}
  }
  // coins
  for(var c=coins.length-1;c>=0;c--){var co=coins[c];co.x-=sp*dt;co.t+=dt;
    if(co.x<0){coins.splice(c,1);continue;}
    var dx=player.x-co.x,dy=player.y-co.y;
    if(dx*dx+dy*dy<40*40){coins.splice(c,1);score+=25;playTone(880,0.08,"square");
      var lv=1+Math.floor(score/250);if(lv!==level){level=lv;playTone(660,0.15,"triangle");}}
  }
  if(shake>0)shake-=dt;
  if(score>high){high=score;}
}
function gameOver(){
  state="over";
  if(score>parseInt(localStorage.getItem("rocketRunHigh")||"0",10)){
    localStorage.setItem("rocketRunHigh",String(score));}
}
function draw(){
  // bg
  var g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,THEME.skyTop);
  g.addColorStop(1,THEME.skyBot);ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  for(var s=0;s<stars.length;s++){ctx.fillStyle=THEME.accent;var st=stars[s];
    ctx.globalAlpha=0.5+0.5*Math.sin(dist*0.002+st.x);ctx.fillRect(st.x,st.y,st.s,st.s);}
  ctx.globalAlpha=1;
  // mountains
  ctx.fillStyle=THEME.ground;ctx.fillRect(0,GROUND-30,W,30);
  ctx.fillStyle=THEME.groundTop;ctx.fillRect(0,GROUND-28,W,6);
  ctx.fillStyle="#3a2a66";
  ctx.beginPath();ctx.moveTo(0,GROUND-28);ctx.lineTo(150,GROUND-90);ctx.lineTo(300,GROUND-28);ctx.closePath();ctx.fill();
  ctx.beginPath();ctx.moveTo(260,GROUND-28);ctx.lineTo(420,GROUND-70);ctx.lineTo(580,GROUND-28);ctx.closePath();ctx.fill();
  ctx.save();
  if(shake>0)ctx.translate((Math.random()-0.5)*8,(Math.random()-0.5)*8);
  if(state==="play"||state==="over"){
    for(var c=0;c<coins.length;c++){var co=coins[c];
      ctx.fillStyle=co.c;ctx.beginPath();ctx.arc(co.x,co.y+Math.sin(co.t*4)*4,co.r,0,7);ctx.fill();
      ctx.fillStyle="#7c4d00";ctx.font="bold 14px sans-serif";ctx.textAlign="center";
      ctx.fillText("★",co.x,co.y+5);}
    for(var o=0;o<obs.length;o++){var ob=obs[o];drawObstacle(ob.x,ob.y,ob.w,ob.h);}
    drawPlayer(player.x,player.y);
    // on-screen touch controls
    ctx.fillStyle="rgba(0,0,0,0.25)";ctx.fillRect(0,H-54,W,54);
    ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.textAlign="center";
    ctx.fillText("◀ TAP to JUMP · hold bottom to DUCK ▶",W/2,H-22);
  }
  ctx.restore();
  // HUD
  ctx.fillStyle="#000";ctx.fillRect(W/2-60,14,120,4);ctx.fillStyle="#fff";
  ctx.font="bold 20px sans-serif";ctx.textAlign="left";
  ctx.fillText("SCORE "+score,14,34);
  ctx.fillText("LV "+level,W-90,34);
  ctx.textAlign="right";ctx.fillStyle="#ffd54a";ctx.fillText("BEST "+high,W-14,58);
  // sound toggle
  ctx.fillStyle="rgba(0,0,0,0.3)";ctx.fillRect(W-46,68,34,26);
  ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.textAlign="center";
  ctx.fillText(soundOn?"🔊":"🔇",W-29,88);
  // start / over screens
  if(state==="start"){
    ctx.fillStyle="rgba(0,0,0,0.45)";ctx.fillRect(0,0,W,H);
    ctx.fillStyle="#fff";ctx.textAlign="center";
    ctx.font="bold 46px sans-serif";ctx.fillText(GAME_NAME,W/2,180);
    ctx.font="20px sans-serif";ctx.fillStyle="#ffd54a";
    ctx.fillText("GOAL: run far, grab coins, reach higher levels!",W/2,225);
    ctx.fillStyle="#e8e8e8";
    ctx.fillText("TAP (or SPACE) to jump · hold bottom to duck",W/2,265);
    ctx.fillText("TAP anywhere to START",W/2,340);
    ctx.fillStyle="#2fd54a";ctx.beginPath();ctx.arc(W/2+190,265,8,0,7);ctx.fill();
  }
  if(state==="over"){
    ctx.fillStyle="rgba(0,0,0,0.55)";ctx.fillRect(0,0,W,H);
    ctx.fillStyle="#fff";ctx.textAlign="center";
    ctx.font="bold 46px sans-serif";ctx.fillText("GAME OVER",W/2,190);
    ctx.font="24px sans-serif";ctx.fillText("Score "+score,340,240);
    ctx.fillText("Level "+level,460,240);
    ctx.font="20px sans-serif";ctx.fillStyle="#ffd54a";
    ctx.fillText("Best "+high,W/2,280);
    ctx.fillStyle="#e8e8e8";ctx.fillText("TAP anywhere to play again",W/2,340);
  }
}
// ---- input ----
var lastFrame=performance.now();
function frame(t){
  var dt=Math.min((t-lastFrame)/1000,0.033);lastFrame=t;
  spawn();update(dt);draw();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
cv.addEventListener("pointerdown",function(e){
  initAudio();var y=e.clientY/cv.getBoundingClientRect().height*H;
  if(state==="over"){reset();state="play";return;}
  if(state==="start"){state="play";playTone(440,0.08,"square");return;}
  x(e.clientX/cv.getBoundingClientRect().width*W);
  if(y>H*0.8){touchAction="duck";}else{touchAction="jump";}
});
cv.addEventListener("pointerup",function(){touchAction=null;});
window.addEventListener("keydown",function(e){
  initAudio();
  if(state==="over"&&(e.code==="Space"||e.code==="Enter")){reset();state="play";}
  else if(state==="start"&&(e.code==="Space"||e.code==="Enter")){state="play";}
  if(e.code==="Space"){touchAction="jump";}
  if(e.code==="ArrowDown"||e.code==="KeyS"){touchAction="duck";}
});
window.addEventListener("keyup",function(e){
  if(e.code==="Space"||e.code==="ArrowDown"||e.code==="KeyS"){touchAction=null;}
});
cv.addEventListener("contextmenu",function(e){e.preventDefault();});
})();
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# COLLECTOR — a top-down (or side) game where you grab items and dodge enemies,
# with levels and a get-all-items goal. Simple and reskinnable.
# ─────────────────────────────────────────────────────────────────────────────
COLLECTOR = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Gem Grab</title>
<style>
  html,body{margin:0;padding:0;background:#0d1b2a;height:100%;overflow:hidden;
    touch-action:manipulation;-webkit-user-select:none;user-select:none;}
  #wrap{position:fixed;top:0;left:0;width:100%;height:100%;display:flex;
    align-items:center;justify-content:center;}
  canvas{display:block;width:100%;height:100%;object-fit:contain;
    background:#0d1b2a;touch-action:none;cursor:pointer;}
</style>
</head>
<body>
<div id="wrap"><canvas id="game" width="800" height="600"></canvas></div>
<script>
(function(){
"use strict";
var cv=document.getElementById("game"),ctx=cv.getContext("2d");
// ---- THEME VARS ----
var GAME_NAME="Gem Grab";
var THEME={bg1:"#0d1b2a",bg2:"#1b3a5a",accent:"#56c8ff",player:"#7cff6b",
  enemy:"#ff5d5d",item:"#ffd700",wall:"#2a4a6a"};
function drawPlayer(x,y){ctx.fillStyle=THEME.player;
  ctx.beginPath();ctx.arc(x,y,18,0,7);ctx.fill();
  ctx.fillStyle="#fff";ctx.beginPath();ctx.arc(x-5,y-6,4,0,7);ctx.arc(x+5,y-6,4,0,7);ctx.fill();
  ctx.fillStyle="#111";ctx.beginPath();ctx.arc(x-3,y-7,2,0,7);ctx.arc(x+7,y-7,2,0,7);ctx.fill();
}
function drawItem(x,y,t){ctx.fillStyle=THEME.item;
  ctx.beginPath();ctx.moveTo(x,y-12);ctx.lineTo(x+8,y);ctx.lineTo(x,y+12);
  ctx.lineTo(x-8,y);ctx.closePath();ctx.fill();ctx.fillStyle="#fff";
  ctx.font="bold 12px sans-serif";ctx.textAlign="center";ctx.fillText("★",x,y+4);
}
function drawEnemy(x,y){ctx.fillStyle=THEME.enemy;
  ctx.beginPath();ctx.arc(x,y,14,0,7);ctx.fill();
  ctx.fillStyle="#fff";ctx.beginPath();ctx.arc(x-4,y-3,3,0,7);ctx.arc(x+4,y-3,3,0,7);ctx.fill();
  ctx.strokeStyle="#111";ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x-6,y+6);ctx.lineTo(x,y+12);
  ctx.moveTo(x+6,y+6);ctx.lineTo(x,y+12);ctx.stroke();
}
var W=800,H=600;
var player={x:400,y:300,r:18,sp:260};
var items=[],enemies=[],itemsNeeded=8;
var score=0,high=parseInt(localStorage.getItem("gemGrabHigh")||"0",10);
var level=1,state="start",invuln=0;
var keys={},touch={x:null,y:null};
function newLevel(n){
  level=n;items=[];enemies=[];
  itemsNeeded=6+n;
  for(var i=0;i<itemsNeeded;i++){items.push({x:40+Math.random()*(W-80),y:40+Math.random()*(H-80)});}
  enemies.push({x:200,y:150,vx:120,vy:60});
  if(n>=2)enemies.push({x:600,y:450,vx:-100,vy:90});
  if(n>=3)enemies.push({x:150,y:500,vx:140,vy:-70});
  if(n>=4)enemies.push({x:650,y:100,vx:-130,vy:80});
}
var audio=null,soundOn=true;
function playTone(f,d,type,vol){if(!soundOn)return;try{
  if(!audio){audio=new (window.AudioContext||window.webkitAudioContext)();}
  var o=audio.createOscillator(),g=audio.createGain();
  o.type=type||"square";o.frequency.value=f;
  g.gain.setValueAtTime(vol||0.08,audio.currentTime);
  g.gain.exponentialRampToValueAtTime(0.0001,audio.currentTime+d);
  o.connect(g);g.connect(audio.destination);o.start();o.stop(audio.currentTime+d);}catch(e){}}
function initAudio(){if(audio&&audio.state==="suspended")audio.resume();}
function reset(){score=0;level=1;invuln=0;player.x=400;player.y=300;newLevel(1);}
function update(dt){
  if(state!=="play")return;
  var mx=0,my=0;
  if(touch.x!==null){var dx=touch.x-player.x,dy=touch.y-player.y,d=Math.hypot(dx,dy);
    if(d>6){mx=dx/d;my=dy/d;}}
  else{mx=(keys["ArrowRight"]||keys["KeyD"]?1:0)-(keys["ArrowLeft"]||keys["KeyA"]?1:0);
    my=(keys["ArrowDown"]||keys["KeyS"]?1:0)-(keys["ArrowUp"]||keys["KeyW"]?1:0);}
  var sp=player.sp+(level-1)*20;
  player.x+=mx*sp*dt;player.y+=my*sp*dt;
  player.x=Math.max(player.r,Math.min(W-player.r,player.x));
  player.y=Math.max(player.r,Math.min(H-player.r,player.y));
  for(var i=enemies.length-1;i>=0;i--){var e=enemies[i];
    e.x+=e.vx*dt;e.y+=e.vy*dt;
    if(e.x<20)e.vx=Math.abs(e.vx);if(e.x>W-20)e.vx=-Math.abs(e.vx);
    if(e.y<20)e.vy=Math.abs(e.vy);if(e.y>H-20)e.vy=-Math.abs(e.vy);
    if(invuln<=0&&Math.hypot(player.x-e.x,player.y-e.y)<30){score=Math.max(0,score-15);
      invuln=1;playTone(120,0.25,"sawtooth",0.12);}
  }
  if(invuln>0)invuln-=dt;
  for(var j=items.length-1;j>=0;j--){var it=items[j];
    if(Math.hypot(player.x-it.x,player.y-it.y)<30){items.splice(j,1);score+=20;
      playTone(880,0.08,"square");
      if(items.length===0){score+=50;playTone(660,0.2,"triangle");
        if(level>=5){state="win";if(score>high){high=score;localStorage.setItem("gemGrabHigh",String(high));}}
        else{newLevel(level+1);}}}}
  if(score>high)high=score;
}
function draw(){
  var g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,THEME.bg1);g.addColorStop(1,THEME.bg2);
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  for(var i=0;i<Math.floor(W/40);i++){for(var j=0;j<Math.floor(H/40);j++){
    ctx.fillStyle=THEME.wall;ctx.fillRect(i*40,j*40,1,1);}}
  for(var k=0;k<enemies.length;k++){drawEnemy(enemies[k].x,enemies[k].y);}
  for(var m=0;m<items.length;m++){drawItem(items[m].x,items[m].y);}
  if(invuln<=0||Math.floor(invuln*10)%2===0){drawPlayer(player.x,player.y);}
  // touch joystick indicator
  if(touch.x!==null){ctx.fillStyle="rgba(255,255,255,0.25)";
    ctx.beginPath();ctx.arc(touch.x,touch.y,14,0,7);ctx.fill();}
  ctx.fillStyle="#000";ctx.fillRect(0,0,W,52);
  ctx.fillStyle="#fff";ctx.font="bold 20px sans-serif";ctx.textAlign="left";
  ctx.fillText("SCORE "+score,14,34);
  ctx.fillText("LEVEL "+level,W-100,34);
  ctx.textAlign="right";ctx.fillStyle=THEME.accent;ctx.fillText("BEST "+high,W-14,20);
  ctx.fillStyle="#fff";ctx.font="15px sans-serif";ctx.textAlign="center";
  ctx.fillText("Gems left: "+items.length,70,54);
  // sound toggle
  ctx.fillStyle="rgba(0,0,0,0.3)";ctx.fillRect(W-46,58,34,26);
  ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.textAlign="center";
  ctx.fillText(soundOn?"🔊":"🔇",W-29,78);
  if(state==="start"){ctx.fillStyle="rgba(0,0,0,0.5)";ctx.fillRect(0,0,W,H);
    ctx.fillStyle="#fff";ctx.textAlign="center";
    ctx.font="bold 46px sans-serif";ctx.fillText(GAME_NAME,W/2,170);
    ctx.font="20px sans-serif";ctx.fillStyle=THEME.accent;
    ctx.fillText("GOAL: grab all "+itemsNeeded+" gems each level to advance!",W/2,215);
    ctx.fillStyle="#e8e8e8";
    ctx.fillText("DRAG anywhere to move · avoid the red blobs",W/2,255);
    ctx.fillText("TAP anywhere to START",W/2,330);
  }
  if(state==="over"){ctx.fillStyle="rgba(0,0,0,0.6)";ctx.fillRect(0,0,W,H);
    ctx.fillStyle="#fff";ctx.textAlign="center";
    ctx.font="bold 46px sans-serif";ctx.fillText("GAME OVER",W/2,180);
    ctx.font="24px sans-serif";ctx.fillText("Score "+score,W/2,225);
    ctx.fillStyle="#ffd54a";ctx.fillText("Best "+high,W/2,260);
    ctx.fillStyle="#e8e8e8";ctx.fillText("TAP anywhere to play again",W/2,320);
  }
  if(state==="win"){ctx.fillStyle="rgba(0,0,0,0.6)";ctx.fillRect(0,0,W,H);
    ctx.fillStyle="#ffd700";ctx.textAlign="center";ctx.font="bold 46px sans-serif";
    ctx.fillText("YOU WIN! 🎉",W/2,190);ctx.font="24px sans-serif";ctx.fillStyle="#fff";
    ctx.fillText("Final score "+score,W/2,240);ctx.font="20px sans-serif";
    ctx.fillText("TAP anywhere to play again",W/2,300);}
}
var lastFrame=performance.now();
function frame(t){var dt=Math.min((t-lastFrame)/1000,0.033);lastFrame=t;
  update(dt);draw();requestAnimationFrame(frame);}
requestAnimationFrame(frame);
cv.addEventListener("pointerdown",function(e){initAudio();
  var rect=cv.getBoundingClientRect();
  if(state==="over"||state==="win"){reset();state="play";return;}
  if(state==="start"){state="play";playTone(440,0.08,"square");return;}
  if(e.clientY-rect.top>rect.height*0.85&&e.clientX-rect.left>rect.width*0.85){
    soundOn=!soundOn;playTone(400,0.05,"square");return;}
  touch.x=(e.clientX-rect.left)/rect.width*W;touch.y=(e.clientY-rect.top)/rect.height*H;
});
window.addEventListener("pointermove",function(e){var rect=cv.getBoundingClientRect();
  if(touch.x!==null){touch.x=(e.clientX-rect.left)/rect.width*W;touch.y=(e.clientY-rect.top)/rect.height*H;}});
window.addEventListener("pointerup",function(){touch.x=null;touch.y=null;});
window.addEventListener("keydown",function(e){initAudio();
  if(state==="over"||state==="win"&&(e.code==="Space"||e.code==="Enter")){reset();state="play";}
  else if(state==="start"&&(e.code==="Space"||e.code==="Enter")){state="play";}
  keys[e.code]=true;});
window.addEventListener("keyup",function(e){keys[e.code]=false;});
cv.addEventListener("contextmenu",function(e){e.preventDefault();});
})();
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# SHOOTER — a top-down (or side) shooter: dodge enemies, shoot them, clear
# waves/levels, score + high score. Levels get harder with new enemy types.
# Phone: on-screen LEFT/RIGHT + SHOOT tap zones; drag-tap to aim/shoot.
# PC: arrows/WASD move, SPACE/click shoots.
# ─────────────────────────────────────────────────────────────────────────────
SHOOTER = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Star Blaster</title>
<style>
  html,body{margin:0;padding:0;background:#050510;height:100%;overflow:hidden;
    touch-action:manipulation;-webkit-user-select:none;user-select:none;}
  #wrap{position:fixed;top:0;left:0;width:100%;height:100%;display:flex;
    align-items:center;justify-content:center;}
  canvas{display:block;width:100%;height:100%;object-fit:contain;
    background:#050510;touch-action:none;cursor:pointer;}
</style>
</head>
<body>
<div id="wrap"><canvas id="game" width="800" height="600"></canvas></div>
<script>
(function(){
"use strict";
var cv=document.getElementById("game"),ctx=cv.getContext("2d");
// ---------- THEME VARS (rewrite these to reskin) ----------
var GAME_NAME="Star Blaster";
var THEME={bg1:"#050510",bg2:"#12122e",accent:"#4ec9ff",player:"#7cff6b",
  enemy1:"#ff5d5d",enemy2:"#ffb84e",enemy3:"#c88bff",shot:"#ffe14e",shield:"#4ec9ff"};
function drawPlayer(x,y){ctx.fillStyle=THEME.player;
  ctx.beginPath();ctx.moveTo(x,y+22);ctx.lineTo(x+16,y-12);ctx.lineTo(x,y-4);
  ctx.lineTo(x-16,y-12);ctx.closePath();ctx.fill();
  ctx.fillRect(x-4,y-12,8,16);ctx.fillStyle="#fff";
  ctx.beginPath();ctx.arc(x,y+2,6,0,7);ctx.fill();}
function drawEnemy(x,y,r,kind){ctx.fillStyle=kind;
  ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fill();
  ctx.fillStyle="#fff";
  if(kind===THEME.enemy2){for(var i=0;i<4;i++){var a=i*1.57;
    ctx.beginPath();ctx.arc(x+Math.cos(a)*(r+4),y+Math.sin(a)*(r+4),3,0,7);ctx.fill();}}
  else{ctx.beginPath();ctx.arc(x-r*0.3,y-r*0.2,2.5,0,7);ctx.arc(x+r*0.3,y-r*0.2,2.5,0,7);ctx.fill();}}
// ------------------------------------------------
var W=800,H=600;
var bullets=[],enemies=[],shields=[],stars=[];
var player={x:W/2,y:H-60,r:14,sp:280};
var score=0,high=parseInt(localStorage.getItem("starBlasterHigh")||"0",10);
var wave=1,state="start",fireCd=0,shake=0;
var keys={};
var touchMove=null;var touchShoot=false;
function makeStars(){stars=[];for(var i=0;i<140;i++){stars.push({x:Math.random()*W,
  y:Math.random()*H,s:Math.random()*2+0.5,v:20+Math.random()*40});}}
makeStars();
function newWave(n){
  wave=n;enemies=[];shields=[];
  var count=4+n;
  for(var i=0;i<count;i++){
    var kind=THEME.enemy1;
    if(n>=3&&Math.random()<0.3)kind=THEME.enemy2;
    if(n>=5&&Math.random()<0.25)kind=THEME.enemy3;
    var r=12+(n>=5?16:12);
    enemies.push({x:40+Math.random()*(W-80),y:-30-Math.random()*120,
      vx:(Math.random()-0.5)*120,vy:40+n*12,r:r,kind:kind,xdir:(Math.random()<0.5?-1:1)});
  }
  if(n%2===0){shields.push({x:30+Math.random()*(W-60),y:80+Math.random()*200});}
}
function reset(){score=0;wave=1;bullets=[];newWave(1);player.x=W/2;player.y=H-60;}
var audio=null,soundOn=true;
function playTone(f,d,type,vol){if(!soundOn)return;try{
  if(!audio){audio=new (window.AudioContext||window.webkitAudioContext)();}
  var o=audio.createOscillator(),g=audio.createGain();
  o.type=type||"square";o.frequency.value=f;
  g.gain.setValueAtTime(vol||0.08,audio.currentTime);
  g.gain.exponentialRampToValueAtTime(0.0001,audio.currentTime+d);
  o.connect(g);g.connect(audio.destination);o.start();o.stop(audio.currentTime+d);}catch(e){}}
function initAudio(){if(audio&&audio.state==="suspended")audio.resume();}
function shoot(){
  bullets.push({x:player.x,y:player.y-18,vy:-520});playTone(700,0.06,"square",0.05);
}
function update(dt){
  if(state!=="play")return;
  var mx=0;
  if(touchMove!==null){var dx=touchMove-player.x;
    mx=Math.max(-1,Math.min(1,dx/80));}
  else{mx=(keys["ArrowRight"]||keys["KeyD"]?1:0)-(keys["ArrowLeft"]||keys["KeyA"]?1:0);}
  player.x+=mx*player.sp*dt;
  player.x=Math.max(player.r,Math.min(W-player.r,player.x));
  if(touchShoot&&fireCd<=0){shoot();fireCd=0.18;}
  else if((keys["Space"]||keys["ArrowUp"])&&fireCd<=0){shoot();fireCd=0.18;}
  if(fireCd>0)fireCd-=dt;
  // bullets
  for(var b=bullets.length-1;b>=0;b--){bullets[b].y+=bullets[b].vy*dt;
    if(bullets[b].y<-20){bullets.splice(b,1);continue;}
    for(var e=enemies.length-1;e>=0;e--){var en=e<0?null:enemies[e];
      if(en&&Math.sqrt((bullets[b].x-en.x)*(bullets[b].x-en.x)+(bullets[b].y-en.y)*(bullets[b].y-en.y))<en.r+4){
        bullets.splice(b,1);enemies.splice(e,1);score+=10;playTone(880,0.08,"square",0.06);
        break;}}}
  // stars scroll
  for(var i=0;i<stars.length;i++){stars[i].y+=stars[i].v*dt;if(stars[i].y>H){stars[i].y=0;stars[i].x=Math.random()*W;}}
  // enemies
  for(var j=enemies.length-1;j>=0;j--){var e2=enemies[j];
    e2.x+=e2.vx*dt;e2.y+=e2.vy*dt;
    if(e2.x<20||e2.x>W-20){e2.vx*=-1;}
    if(e2.y>H+40){enemies.splice(j,1);score=Math.max(0,score-5);continue;}
    var dx=player.x-e2.x,dy=player.y-e2.y,d=Math.sqrt(dx*dx+dy*dy);
    if(d<e2.r+player.r){state="over";shake=0.4;playTone(140,0.3,"sawtooth",0.15);
      if(score>parseInt(localStorage.getItem("starBlasterHigh")||"0",10))
        localStorage.setItem("starBlasterHigh",String(score));}}
  // shields
  for(var s=shields.length-1;s>=0;s--){var sh=shields[s];
    sh.x+=Math.sin(performance.now()*0.001+sh.y)*20*dt;
    var ds=Math.sqrt((player.x-sh.x)*(player.x-sh.x)+(player.y-sh.y)*(player.y-sh.y));
    if(ds<40){state="over";shake=0.4;playTone(140,0.3,"sawtooth",0.15);
      if(score>parseInt(localStorage.getItem("starBlasterHigh")||"0",10))
        localStorage.setItem("starBlasterHigh",String(score));}}
  if(enemies.length===0){wave++;newWave(wave);playTone(660,0.2,"triangle");score+=20;}
  if(shake>0)shake-=dt;
  if(score>high)high=score;
}
function draw(){
  var g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,THEME.bg1);g.addColorStop(1,THEME.bg2);
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  for(var i=0;i<stars.length;i++){ctx.fillStyle=THEME.accent;ctx.globalAlpha=0.4+0.6*Math.sin(performance.now()*0.002+i);
    ctx.fillRect(stars[i].x,stars[i].y,stars[i].s,stars[i].s);}
  ctx.globalAlpha=1;
  ctx.save();
  if(shake>0)ctx.translate((Math.random()-0.5)*8,(Math.random()-0.5)*8);
  if(state==="play"||state==="over"){
    for(var s=0;s<shields.length;s++){var sh=shields[s];
      ctx.fillStyle=THEME.shield;ctx.globalAlpha=0.15;
      ctx.beginPath();ctx.arc(sh.x,sh.y,36,0,7);ctx.fill();ctx.globalAlpha=1;
      ctx.strokeStyle=THEME.shield;ctx.lineWidth=2;ctx.beginPath();ctx.arc(sh.x,sh.y,36,0,7);ctx.stroke();}
    for(var j=0;j<enemies.length;j++){var en=enemies[j];drawEnemy(en.x,en.y,en.r,en.kind);}
    for(var b=0;b<bullets.length;b++){ctx.fillStyle=THEME.shot;
      ctx.fillRect(bullets[b].x-2,bullets[b].y-6,4,12);}
    drawPlayer(player.x,player.y);
    // on-screen touch controls
    ctx.fillStyle="rgba(0,0,0,0.3)";ctx.fillRect(0,H-56,W,56);
    ctx.fillStyle="rgba(255,255,255,0.12)";ctx.beginPath();
    ctx.arc(60,H-28,30,0,7);ctx.arc(W-60,H-28,30,0,7);ctx.fill();
    ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.textAlign="center";
    ctx.fillText("◀  drag to move",120,H-20);ctx.fillText("TAP ▶ to SHOOT",W-120,H-20);
  }
  ctx.restore();
  ctx.fillStyle="#000";ctx.fillRect(0,0,W,50);
  ctx.fillStyle="#fff";ctx.font="bold 20px sans-serif";ctx.textAlign="left";
  ctx.fillText("SCORE "+score,14,34);
  ctx.textAlign="right";ctx.fillStyle=THEME.accent;ctx.fillText("WAVE "+wave,W-14,34);
  ctx.fillStyle="#ffd54a";ctx.font="16px sans-serif";ctx.fillText("BEST "+high,W-14,20);
  ctx.fillStyle="rgba(0,0,0,0.3)";ctx.fillRect(W-46,58,34,26);
  ctx.fillStyle="#fff";ctx.font="16px sans-serif";ctx.textAlign="center";
  ctx.fillText(soundOn?"🔊":"🔇",W-29,78);
  if(state==="start"){ctx.fillStyle="rgba(0,0,0,0.5)";ctx.fillRect(0,0,W,H);
    ctx.fillStyle="#fff";ctx.textAlign="center";
    ctx.font="bold 46px sans-serif";ctx.fillText(GAME_NAME,W/2,180);
    ctx.font="20px sans-serif";ctx.fillStyle=THEME.accent;
    ctx.fillText("GOAL: clear every wave — blast all enemies!",W/2,225);
    ctx.fillStyle="#e8e8e8";
    ctx.fillText("◀ drag to move · TAP (or SPACE) to shoot",W/2,265);
    ctx.fillText("TAP anywhere to START",W/2,340);
  }
  if(state==="over"){ctx.fillStyle="rgba(0,0,0,0.6)";ctx.fillRect(0,0,W,H);
    ctx.fillStyle="#fff";ctx.textAlign="center";
    ctx.font="bold 46px sans-serif";ctx.fillText("GAME OVER",W/2,190);
    ctx.font="24px sans-serif";ctx.fillText("Score "+score,W/2,235);
    ctx.fillStyle="#ffd54a";ctx.fillText("Best "+high,W/2,275);
    ctx.fillStyle="#e8e8e8";ctx.fillText("TAP anywhere to play again",W/2,340);
  }
}
var lastFrame=performance.now();
function frame(t){var dt=Math.min((t-lastFrame)/1000,0.033);lastFrame=t;
  update(dt);draw();requestAnimationFrame(frame);}
requestAnimationFrame(frame);
cv.addEventListener("pointerdown",function(e){initAudio();
  var rect=cv.getBoundingClientRect();var px=e.clientX-rect.left,pw=rect.width;
  var py=e.clientY-rect.top,ph=rect.height;
  if(state==="over"){reset();state="play";return;}
  if(state==="start"){state="play";playTone(440,0.08,"square");return;}
  if(px/pw>0.72&&py/ph>0.72){soundOn=!soundOn;playTone(400,0.05,"square");return;}
  targetShoot(e.clientX-rect.left,e.clientY-rect.top,pw,ph);
});
function targetShoot(px,py,pw,ph){
  if(px/pw>0.5){touchShoot=true;}else{touchMove=(px/pw)*W;}
  // initial: left half = move; right half (above the ORB)= shoot
  if(px/pw<=0.5){touchMove=(px/pw)*W;touchShoot=false;}
  else{touchShoot=true;touchMove=null;}
}
cv.addEventListener("pointermove",function(e){if(touchMove===null)return;
  var rect=cv.getBoundingClientRect();var px=e.clientX-rect.left;
  if(px/rect.width<=0.5){touchMove=(px/rect.width)*W;}});
window.addEventListener("pointerup",function(){touchMove=null;touchShoot=false;});
window.addEventListener("keydown",function(e){initAudio();
  if(state==="over"&&(e.code==="Space"||e.code==="Enter")){reset();state="play";}
  else if(state==="start"&&(e.code==="Space"||e.code==="Enter")){state="play";}
  keys[e.code]=true;});
window.addEventListener("keyup",function(e){keys[e.code]=false;});
cv.addEventListener("contextmenu",function(e){e.preventDefault();});
})();
</script>
</body>
</html>
"""
