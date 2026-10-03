#!/usr/bin/env python3
"""
Chess Master — bitta Python faylli loyiha.

Ishga tushirish:   python3 chess_game.py
Port tanlash:      python3 chess_game.py --port 9000
Brauzersiz:        python3 chess_game.py --no-browser
Online (do'st bilan): python3 chess_game.py --lan   (bir Wi-Fi tarmog'ida; internet uchun ngrok/cloudflared)
Fayllarni chiqarish (index.html, style.css, script.js, README.md):
                   python3 chess_game.py --export papka_nomi

Faqat Python standart kutubxonasi kerak (o'rnatish shart emas).
O'yin brauzerda ishlaydi; Hard darajasi uchun Stockfish CDN'dan yuklanadi (internet kerak).
"""
import argparse, http.server, json, os, random, socket, socketserver, threading, time, urllib.parse, webbrowser

INDEX_HTML = r'''<!DOCTYPE html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Chess Master</title>
<link rel="stylesheet" href="style.css"></head><body>
<header><h1>♞ CHESS MASTER</h1><span><button id="bm" aria-label="Menu" title="Main menu">☰ Menu</button> <button id="bs" aria-label="Settings" title="Settings">⚙ Settings</button></span></header>
<main>
<section class="bw"><div id="bd" role="grid" aria-label="Chess board"></div></section>
<aside>
<div class="c"><div id="sts" role="status" aria-live="polite"></div></div>
<div class="c tm" id="tmc"><div id="tw"><span>White</span><b>10:00</b></div><div id="tb"><span>Black</span><b>10:00</b></div></div>
<div class="c"><h3>Move History</h3><div id="mh"></div></div>
<div class="c"><div class="cap"><span id="cw"></span></div><div class="cap"><span id="cb"></span></div></div>
<div class="c row"><select id="mo" aria-label="Game mode" title="Mode"><option value="pvp">Player vs Player</option><option value="pvc">Player vs Computer</option><option value="online">Online (friend)</option></select>
<select id="lv" aria-label="Difficulty" title="Difficulty"><option value="0">Easy</option><option value="1">Medium</option><option value="2">Hard</option></select>
<select id="sd" aria-label="Your color" title="Your color"><option value="w">Play White</option><option value="b">Play Black</option><option value="r">Random</option></select>
<select id="tc" aria-label="Time control" title="Time control"><option value="1">1 min</option><option value="3">3 min</option><option value="5">5 min</option><option value="10">10 min</option><option value="15">15 min</option><option value="30">30 min</option></select></div>
<div class="c row"><button id="bn" aria-label="New game" title="New game (N)">New Game</button><button id="bu" aria-label="Undo" title="Undo (U)">↶ Undo</button><button id="br" aria-label="Redo" title="Redo (R)">↷ Redo</button><button id="bdr" aria-label="Offer draw" title="Offer draw">Draw</button><button id="bz" aria-label="Resign" title="Resign">Resign</button><button id="bf" aria-label="Flip board" title="Flip board (F)">⇅ Flip</button><button id="bh" aria-label="Hint" title="Hint (H)">💡 Hint</button><button id="bp" aria-label="Copy PGN" title="Copy PGN">PGN</button><button id="bsn" aria-label="Toggle sound" title="Sound">🔊</button></div>
<div class="c"><h3>Statistics</h3><div class="sg" id="stt"></div></div>
<div class="c"><h3>Game History</h3><div id="gh"></div></div>
</aside></main>
<div class="ov on" id="mn" role="dialog" aria-label="Main menu"><div class="md" style="width:min(480px,100%);max-height:94vh;overflow:auto"><h1 style="font-size:26px;margin-bottom:12px">♞ CHESS MASTER</h1><div id="mb" class="mg"></div></div></div>
<div class="ov" id="om"><div class="md"><h2>Online game</h2><p><small>Create a room and share the code, or join a friend's room.</small></p><div id="oi"></div><div class="row"><button id="oc">Create room</button></div><div class="row" style="margin-top:8px"><input id="oj" type="text" maxlength="5" placeholder="CODE" aria-label="Room code"><button id="oj2">Join</button></div><br><button id="ox" aria-label="Close">Close</button></div></div>
<div class="ov" id="pm"><div class="md"><h2>Promotion</h2><div class="row"><button data-p="Q" aria-label="Queen">♕ Queen</button><button data-p="R" aria-label="Rook">♖ Rook</button><button data-p="B" aria-label="Bishop">♗ Bishop</button><button data-p="N" aria-label="Knight">♘ Knight</button></div></div></div>
<div class="ov" id="sm"><div class="md"><h2>Settings</h2><div id="sf"></div><br><button id="sc" aria-label="Close settings">Close</button></div></div>
<div class="ov" id="rm"><div class="md"><h2 id="rt"></h2><h3 id="rs" style="font-size:22px;color:#fff"></h3><p id="rx"></p><div class="row"><button id="r1">New Game</button><button id="r2" title="Use ← → keys to step through moves">Review Game</button><button id="r3">Close</button></div></div></div>
<div class="ov" id="tn"><div class="md" style="max-height:90vh;overflow:auto"><div id="tv"></div><div class="row"><button id="tp">▶ Play next game</button><button id="tq">☰ Menu</button></div></div></div>
<script src="script.js"></script></body></html>
'''

STYLE_CSS = r''':root{--bg:#0e1220;--g:rgba(255,255,255,.07);--bd:rgba(255,255,255,.14);--ac:#7c5cff;--tx:#e8eaf6;--mu:#9aa3c7;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);color-scheme:dark}
*{box-sizing:inherit}html{scroll-padding-top:env(safe-area-inset-top,0px)}
body{margin:0;min-height:100%;background:radial-gradient(circle at 15% 0,#2a2358,transparent 50%),radial-gradient(circle at 90% 100%,#0d3a52,transparent 45%),var(--bg);color:var(--tx);font:15px/1.4 system-ui,Segoe UI,Roboto,sans-serif}
header{display:flex;justify-content:space-between;align-items:center;padding:12px 20px;max-width:1150px;margin:auto}
h1{font-size:20px;letter-spacing:3px;margin:0}h2,h3{margin:0 0 8px}h3{font-size:14px;color:var(--mu);text-transform:uppercase;letter-spacing:1px}
main{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:20px;max-width:1150px;margin:auto;padding:0 16px 24px}
.bw{display:flex;flex-direction:column;align-items:center}
#bd{width:min(100%,calc(100svh - 120px));min-width:280px;aspect-ratio:1;display:grid;grid-template:repeat(8,1fr)/repeat(8,1fr);border-radius:10px;overflow:hidden;box-shadow:0 20px 60px #000a;border:1px solid var(--bd);container-type:inline-size;user-select:none}
.q{position:relative;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:9.5cqw;line-height:1;background:var(--l);transition:filter .15s}
.q.d{background:var(--dk)}.q:hover{filter:brightness(1.15)}
.q.lm{box-shadow:inset 0 0 0 100px rgba(255,235,59,.3)}.q.sel{box-shadow:inset 0 0 0 100px rgba(255,235,59,.5)}
.q.ck{background:radial-gradient(circle,#ff5252 0,#b30000 75%)}
.q.mv::after{content:"";position:absolute;width:28%;height:28%;border-radius:50%;background:rgba(0,0,0,.3)}
.q.mv.cp::after{width:88%;height:88%;background:none;border:5px solid rgba(0,0,0,.3)}
.pw{color:#fff;text-shadow:0 0 2px #000,0 0 2px #000,0 2px 4px #0008}.pb{color:#15151c;text-shadow:0 0 2px #fff7,0 2px 4px #0006}
.cls .pw,.cls .pb{color:#111;text-shadow:none}
.pop{animation:pop .22s ease-out}@keyframes pop{from{transform:scale(.6);opacity:.5}to{transform:none;opacity:1}}
.q i{position:absolute;font:600 10px system-ui;font-style:normal;color:#888c;pointer-events:none}.q i.r{top:2px;left:3px}.q i.f{bottom:1px;right:3px}
aside{display:flex;flex-direction:column;gap:12px;min-width:0}
.c{background:var(--g);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid var(--bd);border-radius:16px;padding:14px;box-shadow:0 8px 30px #0005}
.tm{display:flex;gap:10px}.tm div{flex:1;padding:8px;border-radius:12px;background:#0004;text-align:center;transition:.25s}.tm div.on{background:var(--ac);box-shadow:0 0 18px #7c5cff88}
.tm b{display:block;font:700 26px ui-monospace,Consolas,monospace}
#sts{font-weight:600;font-size:17px}
#mh{max-height:170px;overflow:auto;display:grid;grid-template-columns:34px 1fr 1fr;gap:2px 6px;font-family:ui-monospace,Consolas,monospace;align-content:start}
.m{cursor:pointer;padding:1px 6px;border-radius:5px}.m:hover,.m.cur{background:#fff3}
.row{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}.row>*{flex:1 1 auto}
button,select{font:inherit;color:var(--tx);background:var(--g);border:1px solid var(--bd);border-radius:10px;padding:8px 12px;cursor:pointer;transition:.2s}
button:hover{background:rgba(124,92,255,.4);transform:translateY(-1px)}select option{color:#000}
button:focus-visible,.q:focus-visible,select:focus-visible{outline:2px solid #fff;outline-offset:-2px}
.cap{display:flex;justify-content:space-between;font-size:20px;min-height:28px}.cap small{font-size:13px;color:var(--mu)}
.hi{font-size:13px;padding:6px 0;border-bottom:1px solid var(--bd)}.sg{display:grid;grid-template-columns:repeat(5,1fr);text-align:center;font-size:12px;color:var(--mu)}.sg b{display:block;font-size:20px;color:var(--tx)}
.ov{position:fixed;inset:0;background:#000b;display:none;align-items:center;justify-content:center;z-index:9;padding:16px}.ov.on{display:flex}
.md{background:#1a1f38;border:1px solid var(--bd);border-radius:18px;padding:22px;width:min(380px,100%);animation:pop .25s;text-align:center}
.md label{display:flex;justify-content:space-between;align-items:center;padding:6px 0;text-align:left}.md input{width:20px;height:20px}
@media(max-width:900px){main{grid-template-columns:1fr}#bd{width:100%}}

.q span{width:100%;height:100%;display:flex;align-items:center;justify-content:center;position:relative;z-index:1}
.q img{width:90%;height:90%;pointer-events:none;filter:drop-shadow(0 2px 2px #0006)}
.sl{animation:sl .22s ease-out;z-index:3!important}@keyframes sl{from{transform:translate(calc(var(--dx)*1%),calc(var(--dy)*1%))}}
.q.ht{box-shadow:inset 0 0 0 100px rgba(80,170,255,.55)}

.md input#oj{width:130px;height:auto;padding:8px;font:inherit;text-transform:uppercase;text-align:center;letter-spacing:3px;color:var(--tx);background:#0004;border:1px solid var(--bd);border-radius:10px}
select:disabled{opacity:.5}

.mg{display:grid;gap:10px}.mb{display:grid;grid-template-columns:44px 1fr;text-align:left;align-items:center;padding:12px 14px;border-radius:14px}
.mb span{grid-row:span 2;font-size:26px;text-align:center}.mb small{color:var(--mu)}.mg>small{color:var(--mu);text-align:left}
.tb{width:100%;border-collapse:collapse;margin-bottom:10px}.tb td{padding:5px 8px;border-bottom:1px solid var(--bd);text-align:left}
'''

SCRIPT_JS = r'''"use strict";
const $=i=>document.getElementById(i),esc=s=>String(s).replace(/[&<>"']/g,c=>'&#'+c.charCodeAt(0)+';');
const GL={K:'♚',Q:'♛',R:'♜',B:'♝',N:'♞',P:'♟'},OL={K:'♔',Q:'♕',R:'♖',B:'♗',N:'♘',P:'♙'},NM={K:'king',Q:'queen',R:'rook',B:'bishop',N:'knight',P:'pawn'};
const TH={Classic:['#f0d9b5','#b58863'],Green:['#eeeed2','#769656'],Blue:['#dee3e6','#8ca2ad'],Brown:['#d9b38c','#7b4a2a'],Neon:['#1b1b3a','#3a1f7a'],Dark:['#5a6074','#2c303d']};
const V={P:100,N:320,B:330,R:500,Q:900,K:0},RT={60:'KQ',4:'kq',63:'K',56:'Q',7:'k',0:'q'};
const D=[[1,0],[-1,0],[0,1],[0,-1]],Gd=[[1,1],[1,-1],[-1,1],[-1,-1]],N=[[1,2],[2,1],[-1,2],[-2,1],[1,-2],[2,-1],[-1,-2],[-2,-1]];
const sq=i=>'abcdefgh'[i&7]+(8-(i>>3));
/* ---------- ENGINE ---------- */
function start(){const b=Array(64).fill(null);[...'RNBQKBNR'].forEach((k,c)=>{b[c]='b'+k;b[8+c]='bP';b[48+c]='wP';b[56+c]='w'+k});return{b,t:'w',c:'KQkq',ep:-1,hm:0,cap:null}}
// Is square s attacked by color `by`?
function att(b,s,by){const r=s>>3,c=s&7,at=(y,x)=>y>=0&&y<8&&x>=0&&x<8?b[y*8+x]:null,pr=by=='w'?r+1:r-1;
 if(at(pr,c-1)==by+'P'||at(pr,c+1)==by+'P')return 1;
 for(const[a,d]of N)if(at(r+a,c+d)==by+'N')return 1;
 for(const[a,d]of[...D,...Gd])if(at(r+a,c+d)==by+'K')return 1;
 for(const[ds,k]of[[D,'R'],[Gd,'B']])for(const[a,d]of ds)for(let y=r+a,x=c+d;y>=0&&y<8&&x>=0&&x<8;y+=a,x+=d){const p=b[y*8+x];if(p){if(p[0]==by&&(p[1]==k||p[1]=='Q'))return 1;break}}
 return 0}
// Pseudo-legal moves (incl. castling, en passant, promotion)
function pseudo(s){const m=[],{b,t}=s,o=t=='w'?'b':'w';
 for(let i=0;i<64;i++){const p=b[i];if(!p||p[0]!=t)continue;const r=i>>3,c=i&7,k=p[1],add=(to,x)=>m.push({f:i,t:to,...x});
  if(k=='P'){const d=t=='w'?-1:1,pr=r+d,push=(to,x)=>{if(pr%7==0)for(const q of'QRBN')add(to,{...x,p:q});else add(to,x)};if(pr<0||pr>7)continue;
   if(!b[pr*8+c]){push(pr*8+c,{});if(r==(t=='w'?6:1)&&!b[(r+d*2)*8+c])add((r+d*2)*8+c,{dp:1})}
   for(const dc of[-1,1]){const cc=c+dc,to=pr*8+cc;if(cc<0||cc>7)continue;if(b[to]&&b[to][0]==o)push(to,{x:1});else if(to==s.ep)add(to,{x:1,e:1})}
  }else{const one=k=='N'||k=='K',ds=k=='N'?N:k=='B'?Gd:k=='R'?D:[...D,...Gd];
   for(const[a,d]of ds)for(let y=r+a,x=c+d;y>=0&&y<8&&x>=0&&x<8;y+=a,x+=d){const to=y*8+x,q=b[to];if(q&&q[0]==t)break;add(to,{x:q?1:0});if(q||one)break}
   if(k=='K'&&i==(t=='w'?60:4)&&!att(b,i,o)){const K=t=='w'?'K':'k',Q=t=='w'?'Q':'q';
    if(s.c.includes(K)&&!b[i+1]&&!b[i+2]&&!att(b,i+1,o)&&!att(b,i+2,o))add(i+2,{cs:'K'});
    if(s.c.includes(Q)&&!b[i-1]&&!b[i-2]&&!b[i-3]&&!att(b,i-1,o)&&!att(b,i-2,o))add(i-2,{cs:'Q'})}}}
 return m}
// Apply move → new state
function ap(s,m){const b=s.b.slice(),p=b[m.f],t=s.t;let c=s.c,cap=b[m.t];
 if(m.e){const x=m.t+(t=='w'?8:-8);cap=b[x];b[x]=null}
 b[m.t]=m.p?t+m.p:p;b[m.f]=null;
 if(m.cs=='K'){b[m.t-1]=b[m.t+1];b[m.t+1]=null}else if(m.cs=='Q'){b[m.t+1]=b[m.t-2];b[m.t-2]=null}
 for(const q of[m.f,m.t])if(RT[q])for(const ch of RT[q])c=c.replace(ch,'');
 return{b,t:t=='w'?'b':'w',c,ep:m.dp?(m.f+m.t)/2:-1,hm:p[1]=='P'||cap?0:s.hm+1,cap}}
const kp=(b,t)=>b.indexOf(t+'K'),chk=s=>att(s.b,kp(s.b,s.t),s.t=='w'?'b':'w');
const legal=s=>pseudo(s).filter(m=>{const n=ap(s,m);return!att(n.b,kp(n.b,s.t),n.t)});
// Standard algebraic notation
function san(s,m,n,lg){let r;
 if(m.cs)r=m.cs=='K'?'O-O':'O-O-O';else{const p=s.b[m.f][1],f=sq(m.f);
  if(p=='P')r=(m.x?f[0]+'x':'')+sq(m.t)+(m.p?'='+m.p:'');
  else{const o=legal(s).filter(y=>y.t==m.t&&y.f!=m.f&&s.b[y.f][1]==p);let dis='';
   if(o.length)dis=o.every(y=>(y.f&7)!=(m.f&7))?f[0]:o.every(y=>(y.f>>3)!=(m.f>>3))?f[1]:f;
   r=p+dis+(m.x?'x':'')+sq(m.t)}}
 return r+(chk(n)?(lg.length?'+':'#'):'')}
function insuf(b){const l=[];b.forEach((p,i)=>{if(p&&p[1]!='K')l.push([p[1],((i>>3)+(i&7))%2])});
 return!l.length||(l.length==1&&'BN'.includes(l[0][0]))||(l.every(x=>x[0]=='B')&&l.every(x=>x[1]==l[0][1]))}
const key=s=>s.b.join()+s.t+s.c+s.ep;
/* ---------- AI (negamax + alpha-beta) ---------- */
function ev(s){let v=0;for(let i=0;i<64;i++){const p=s.b[i];if(!p)continue;const r=i>>3,c=i&7,w=p[0]=='w';
 const x=V[p[1]]+(p[1]=='P'?(w?6-r:r-1)*8:p[1]=='K'?0:10-(Math.abs(3.5-r)+Math.abs(3.5-c))*3);v+=w?x:-x}return v}
function nm(s,d,a,b){if(!d)return(s.t=='w'?1:-1)*ev(s);const l=legal(s);if(!l.length)return chk(s)?-1e5-d:0;
 l.sort((x,y)=>(y.x?1:0)-(x.x?1:0));let best=-1e9;for(const m of l){const v=-nm(ap(s,m),d-1,-b,-a);if(v>best)best=v;if(v>a)a=v;if(a>=b)break}return best}
function ai(s,lv){const l=legal(s),nz=[300,25,0][lv],d=[1,2,3][lv];let best=-1e9,bm=l[0];l.sort((a,b)=>(b.x?1:0)-(a.x?1:0));
 for(const m of l){const v=-nm(ap(s,m),d-1,-1e9,nz?1e9:-best)+Math.random()*nz;if(v>best){best=v;bm=m}}return bm}
/* ---------- STATE / STORAGE ---------- */
const DS={th:'Classic',ps:'Pro',sd:'w',snd:1,an:1,co:1,hl:1,tm:1,mode:'pvc',lv:1,tc:10};
const load=(k,d)=>{try{return JSON.parse(localStorage.getItem(k))||d}catch{return d}},save=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch{}};
const S={...DS,...load('cm_s',{})};let HI=load('cm_h',[]),G,AC;
const cur=()=>G.st[G.st.length-1],persist=()=>S.mode!='online'&&!G.tn&&save('cm_g',{mv:G.rc.map(r=>r.m),tm:G.tm,over:G.over,me:G.me});
/* ---------- SOUND ---------- */
function snd(f,d=.09,ty='sine'){if(!S.snd)return;try{AC=AC||new AudioContext();const o=AC.createOscillator(),g=AC.createGain();o.type=ty;o.frequency.value=f;g.gain.setValueAtTime(.12,AC.currentTime);g.gain.exponentialRampToValueAtTime(.001,AC.currentTime+d);o.connect(g);g.connect(AC.destination);o.start();o.stop(AC.currentTime+d)}catch{}}
/* ---------- ONLINE (long-polling against the Python server in chess_game.py) ---------- */
let NET=null;
const post=(p,b)=>fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json());
const lock=()=>G.over||G.pend||G.v!=null||G.wait||(S.mode=='pvc'&&cur().t==AIC())||(S.mode=='online'&&cur().t!=G.me);
// Play own move and relay it to the opponent
function mv(m){if(NET)post('/api/move',{code:NET.code,c:NET.me,n:G.rc.length,m:{f:m.f,t:m.t,p:m.p}}).catch(()=>{});play(m)}
function netGame(r,wait){NET={code:r.code,me:r.c,v:0,ask:0};S.mode='online';S.tc=r.tc;$('mo').value='online';$('tc').value=r.tc;newGame(1);G.me=r.c;G.fl=r.c=='b';G.wait=wait;apply();render();poll()}
async function joinRoom(code){try{const r=await post('/api/join',{code});if(r.err)return alert(r.err);r.code=code;$('om').classList.remove('on');$('mn').classList.remove('on');netGame(r,false)}catch{alert('Server not reachable')}}
// Wait for opponent moves / events; the server holds each request open until something changes
async function poll(){const N=NET;while(N&&N===NET){try{const r=await(await fetch(`/api/poll?code=${N.code}&v=${N.v}&n=${G.rc.length}`)).json();if(N!==NET)return;
 if(r.err){alert(r.err);NET=null;return}N.v=r.v;
 if(r.joined&&G.wait){G.wait=false;G.last=Date.now();$('om').classList.remove('on');snd(523,.2);render()}
 for(const m of r.moves){if(G.over)break;const x=legal(cur()).find(y=>y.f==m.f&&y.t==m.t&&y.p==(m.p||undefined));if(x)play(x)}
 if(r.over&&!G.over)finish({...r.over,net:1});
 if(!r.offer)N.ask=0;else if(r.offer!=N.me&&!G.over&&!N.ask){N.ask=1;if(confirm('Opponent offers a draw. Accept?'))finish({t:'DRAW',w:0,msg:'Draw by agreement'});else post('/api/offer',{code:N.code,c:N.me,clear:1}).catch(()=>{})}
 }catch{await new Promise(z=>setTimeout(z,2000))}}}
$('oc').onclick=async()=>{try{const r=await post('/api/new',{tc:S.tc});$('oi').innerHTML=`Room code: <b style="font-size:26px;letter-spacing:4px">${esc(r.code)}</b><br><small>Link: ${esc(location.origin)}/?room=${esc(r.code)}</small>`;netGame(r,true)}catch{alert('Server not reachable')}};
$('oj2').onclick=()=>joinRoom($('oj').value.trim().toUpperCase());
$('ox').onclick=()=>{$('om').classList.remove('on');if(S.mode!='online'){$('mo').value=S.mode;if(G.idle)menu('main')}};
/* ---------- GAME FLOW ---------- */
function newGame(q){if(!q&&S.mode=='online'){NET=null;S.mode='pvp';$('mo').value='pvp';apply()}const me=S.mode=='pvc'?(S.sd=='r'?(Math.random()<.5?'w':'b'):S.sd):'w';G={st:[start()],rc:[],rd:[],tm:{w:S.tc*6e4,b:S.tc*6e4},over:null,v:null,sel:null,pend:null,last:Date.now(),me,fl:me=='b',an:-1};if(!q)snd(523,.2);render();persist();if(!q)aiTurn()}
// Terminal-state detection
function term(s,lg=legal(s)){if(!lg.length)return chk(s)?{t:'CHECKMATE',w:s.t=='w'?'b':'w',msg:'Checkmate!'}:{t:'STALEMATE',w:0,msg:'Stalemate'};
 if(insuf(s.b))return{t:'DRAW',w:0,msg:'Insufficient material'};if(s.hm>=100)return{t:'DRAW',w:0,msg:'Fifty-move rule'};
 const k=key(s);if(G.st.filter(x=>key(x)==k).length>=3)return{t:'DRAW',w:0,msg:'Threefold repetition'}}
function play(m,q){const s=cur(),n=ap(s,m),lg=legal(n);G.rc.push({m:{f:m.f,t:m.t,p:m.p},sn:san(s,m,n,lg),cap:n.cap});G.st.push(n);G.rd=[];G.v=null;G.sel=null;G.hint=null;G.an=G.st.length-1;
 if(q)return;const o=term(n,lg);
 if(o)finish(o);else{snd(n.cap?220:440,.09,n.cap?'square':'sine');if(chk(n))setTimeout(()=>snd(700,.2,'sawtooth'),100);render();persist();aiTurn()}}
function finish(o,rec=1){G.over=o;G.sel=null;snd(330,.5,'triangle');
 if(NET&&!o.net&&(o.t=='RESIGN'||o.t=='TIME'||o.msg=='Draw by agreement'))post('/api/end',{code:NET.code,c:NET.me,o}).catch(()=>{});
 if(G.tn==1){tnResult(o.w?(o.w==G.me?1:0):.5);G.tn=2}$('r1').textContent=G.tn?'Tournament':'New Game';
 if(rec){HI.unshift({d:new Date().toLocaleString('en-GB'),m:S.mode,u:S.mode!='pvp'?G.me:'w',r:o.w?(o.w=='w'?'White Wins':'Black Wins'):'Draw',n:Math.ceil(G.rc.length/2)});HI=HI.slice(0,50);save('cm_h',HI)}
 $('rt').textContent=o.t;$('rs').textContent=o.w?(o.w=='w'?'White Wins!':'Black Wins!'):'Draw';$('rx').textContent=o.msg;$('rm').classList.add('on');render();persist()}
/* ---------- STOCKFISH (Hard) : CDN worker via Blob; falls back to built-in AI on any failure ---------- */
const SF_URL='https://cdnjs.cloudflare.com/ajax/libs/stockfish.js/10.0.2/stockfish.js';let SF=null,sfBad=false;
function sfInit(){if(SF||sfBad)return;try{const b=new Blob([`importScripts('${SF_URL}')`],{type:'application/javascript'});SF=new Worker(URL.createObjectURL(b));SF.onerror=()=>{SF=null;sfBad=true};SF.postMessage('uci')}catch{sfBad=true}}
const fen=s=>{const r=[];for(let y=0;y<8;y++){let z='',e=0;for(let x=0;x<8;x++){const p=s.b[y*8+x];if(!p)e++;else{if(e){z+=e;e=0}z+=p[0]=='w'?p[1]:p[1].toLowerCase()}}r.push(z+(e||''))}
 return r.join('/')+' '+s.t+' '+(s.c||'-')+' '+(s.ep<0?'-':sq(s.ep))+' '+s.hm+' '+((G.st.length-1>>1)+1)};
// Ask Stockfish (UCI). o={sk:skill 0-20, mt:ms}. cb(null) on failure/timeout
function sfMove(s,cb,o={sk:20,mt:1000}){if(!SF)return cb(null);let ok=1;const fin=u=>{if(ok){ok=0;clearTimeout(to);if(SF)SF.onmessage=null;cb(u)}},to=setTimeout(()=>fin(null),9000);
 SF.onerror=()=>{SF=null;sfBad=true;fin(null)};SF.onmessage=e=>{const m=/^bestmove (\S+)/.exec(String(e.data));if(m)fin(m[1])};
 SF.postMessage('setoption name Skill Level value '+o.sk);SF.postMessage('position fen '+fen(s));SF.postMessage('go movetime '+o.mt)}
const uci2m=(u,l)=>{if(!u)return null;const f=(8-+u[1])*8+'abcdefgh'.indexOf(u[0]),t=(8-+u[3])*8+'abcdefgh'.indexOf(u[2]),p=u[4]?u[4].toUpperCase():undefined;return l.find(x=>x.f==f&&x.t==t&&x.p==p)||null};
// Grandmaster opponents: [name, approx. peak Elo, Stockfish skill, ms/move]. Simulated STRENGTH only — not the real players' styles.
const GM=[['Judit Polgár',2700,16,900],['Mikhail Tal',2700,16,700],['Bobby Fischer',2785,18,1000],['Garry Kasparov',2850,19,1200],['Hikaru Nakamura',2800,19,500],['Magnus Carlsen',2880,20,1500]];
const AIC=()=>G.me=='w'?'b':'w',SK=[0,{sk:5,mt:400},{sk:20,mt:1000},...GM.map(g=>({sk:g[2],mt:g[3]}))];
// Computer move: Easy = built-in; Medium/Hard = Stockfish (skill 5 / 20) with built-in fallback
function aiTurn(){const ok=()=>S.mode=='pvc'&&!G.over&&cur().t==AIC();if(!ok())return;const go=m=>{if(ok()&&m)play(m)};
 setTimeout(()=>{if(!ok())return;if(!S.lv)return go(ai(cur(),0));
  sfInit();const fe=fen(cur());
  sfMove(cur(),u=>{if(G.over||fen(cur())!=fe)return;go(uci2m(u,legal(cur()))||ai(cur(),Math.min(S.lv,2)))},SK[S.lv])},350)}
// Hint: highlight Stockfish's (or built-in) best move
function hint(){if(S.mode=='online'||G.tn||G.over||(S.mode=='pvc'&&cur().t==AIC()))return;sfInit();const fe=fen(cur());
 sfMove(cur(),u=>{if(fen(cur())!=fe)return;const m=uci2m(u,legal(cur()))||ai(cur(),2);G.hint=[m.f,m.t];render()},{sk:20,mt:600})}
function click(i){if(lock())return;const s=cur(),p=s.b[i];
 if(G.sel!=null){const ms=legal(s).filter(m=>m.f==G.sel&&m.t==i);if(ms.length){if(ms[0].p){G.pend=ms;$('pm').classList.add('on')}else mv(ms[0]);return}}
 G.sel=p&&p[0]==s.t?i:null;render()}
function undo(){const n=S.mode=='pvc'?2:1;if(G.pend||G.tn||S.mode=='online')return;for(let k=0;k<n&&G.rc.length;k++)G.rd.push({r:G.rc.pop(),s:G.st.pop()});G.over=null;G.v=null;G.sel=null;G.hint=null;render();persist();aiTurn()}
function redo(){if(G.tn||S.mode=='online')return;const n=S.mode=='pvc'?2:1;for(let k=0;k<n&&G.rd.length;k++){const x=G.rd.pop();G.rc.push(x.r);G.st.push(x.s)}G.v=null;const o=term(cur());if(o)G.over=o;render();persist();aiTurn()}
function view(d){const l=G.st.length-1,v=Math.min(l,Math.max(0,(G.v??l)+d));G.v=v==l?null:v;render()}
/* ---------- MAIN MENU / SAVED GAME ---------- */
const MENU=()=>$('mn').classList.contains('on');
// Restore the saved game (only when the player asks for it)
function resume(){const g=load('cm_g',null);if(!g||!g.mv||!g.mv.length)return;newGame(1);
 for(const m of g.mv){const l=legal(cur()).find(x=>x.f==m.f&&x.t==m.t&&x.p==m.p);if(!l)break;play(l,1)}
 if(g.me){G.me=g.me;G.fl=g.me=='b'}if(g.tm)G.tm=g.tm;G.over=g.over||null;G.last=Date.now();render();aiTurn()}
function menu(v='main'){const can=G.rc.length&&!G.over,sv=load('cm_g',null),saved=sv&&sv.mv&&sv.mv.length&&!sv.over;
 const b=(a,i,t,s='')=>`<button class="mb" data-a="${a}"><span>${i}</span><b>${t}</b><small>${s}</small></button>`,bk=b('main','←','Back');let h='';
 if(v=='main'){if(can)h+=b('resume','▶','Resume game','Back to the current board');else if(saved)h+=b('cont','▶','Continue saved game','Pick up where you left off');
  const live=t=>TN&&TN.t==t&&!TN.end;
  h+=b('quick','🎮','Quick Game','Two players or vs computer')+b('gm','👑','Grandmasters','Play 6 simulated legends')+b('online','🌐','Online','Play a friend with a room code')
   +b('champ','🥇','Championship',live('champ')?'Continue — round '+(TN.i+1)+'/'+POOL.length:'League against 9 opponents')
   +b('cup','🏆','Cup',live('cup')?'Continue the knockout':'8-player knockout tournament')+b('settings','⚙','Settings','Themes, pieces, sound')}
 else if(v=='quick')h+=b('pvp','👥','Two players','Same device')+['Easy','Medium','Hard'].map((n,i)=>b('lv'+i,['🟢','🟡','🔴'][i],'Vs Computer — '+n)).join('')+bk;
 else h+=GM.map((g,i)=>b('gm'+i,'♚',g[0],'~'+g[1]+' Elo')).join('')+'<small>Stockfish-based strength simulation — not the real players\' style.</small>'+bk;
 $('mb').innerHTML=h;$('mn').classList.add('on')}
function begin(mode,lv){S.mode=mode;if(lv!=null)S.lv=lv;save('cm_s',S);$('mo').value=mode;$('lv').value=S.lv;apply();$('mn').classList.remove('on');newGame()}
function act(a){
 if(a=='main'||a=='quick'||a=='gm')return menu(a);
 if(a=='resume')return $('mn').classList.remove('on');
 if(a=='cont'){$('mn').classList.remove('on');return resume()}
 if(a=='settings')return openSettings();
 if(a=='online'){$('mn').classList.remove('on');$('oi').textContent='';return $('om').classList.add('on')}
 if(a=='champ'||a=='cup'){if(!TN||TN.t!=a||TN.end){if(TN&&!TN.end&&!confirm('Replace the unfinished '+TN.t+'?'))return;a=='champ'?champStart():cupStart()}return tnShow()}
 if(a=='pvp')return begin('pvp');
 if(a.startsWith('lv'))return begin('pvc',+a.slice(2));
 if(a.startsWith('gm'))return begin('pvc',+a.slice(2)+3)}
$('mn').onclick=e=>{const a=e.target.closest('[data-a]');if(a)act(a.dataset.a)};
$('bm').onclick=()=>menu('main');
/* ---------- TOURNAMENTS (Championship league + Cup knockout) vs simulated opponents ---------- */
const POOL=[['Rookie bot',1000,0],['Club bot',1600,1],['Hard bot',2200,2],...GM.map((g,i)=>[g[0],g[1],i+3])];// [name, Elo, level]
let TN=load('cm_t',null);
const pn=i=>i<0?'You':POOL[i][0];
// Simulated result of bot a vs bot b (score for a): 20% draws, otherwise Elo-based
const sim=(a,b)=>{const p=1/(1+10**((POOL[b][1]-POOL[a][1])/400)),r=Math.random();return r<.2?.5:r<.2+.8*p?1:0};
function champStart(){const n=POOL.length,pts=Array(n).fill(0);for(let a=0;a<n;a++)for(let b=a+1;b<n;b++){const s=sim(a,b);pts[a]+=s;pts[b]+=1-s}TN={t:'champ',i:0,me:0,pts,end:0};save('cm_t',TN)}
function cupStart(){const f=[-1,...POOL.map((p,i)=>i).sort(()=>Math.random()-.5).slice(0,7)].sort(()=>Math.random()-.5);TN={t:'cup',cur:f,rd:[],sw:0,end:0};cupRound()}
// New cup round: bots' matches are simulated, yours stays pending
function cupRound(){const L=TN.cur,pr=[];for(let i=0;i<L.length;i+=2){const a=L[i],b=L[i+1],m={a,b,w:null};if(a>=0&&b>=0){const s=sim(a,b);m.w=s==.5?(Math.random()<.5?a:b):s?a:b}pr.push(m)}TN.rd.push(pr);TN.sw=0;save('cm_t',TN)}
// Record your game result (score 1 / .5 / 0)
function tnResult(sc){if(!TN)return;
 if(TN.t=='champ'){TN.me+=sc;TN.pts[TN.i]+=1-sc;if(++TN.i>=POOL.length)TN.end=1}
 else{const m=TN.rd[TN.rd.length-1].find(m=>m.w==null),o=m.a<0?m.b:m.a;
  if(sc==.5)TN.sw++;// draw → rematch with colors swapped
  else{m.w=sc?-1:o;if(!sc)TN.end='out';else{const nl=TN.rd[TN.rd.length-1].map(m=>m.w);if(nl.length==1)TN.end='champ';else{TN.cur=nl;cupRound()}}}}
 save('cm_t',TN)}
function tnShow(){const T=TN;let h='';
 if(T.t=='champ'){const rows=[['You',T.me,1],...POOL.map((p,i)=>[p[0],T.pts[i],0])].sort((a,b)=>b[1]-a[1]);
  h='<h2>🥇 Championship</h2><table class="tb">'+rows.map((r,i)=>`<tr${r[2]?' style="background:#7c5cff55"':''}><td>${i+1}</td><td>${esc(r[0])}</td><td>${r[1]}</td></tr>`).join('')+'</table>';
  if(T.end){const k=rows.findIndex(r=>r[2]);h+=`<p><b>${['🥇 CHAMPION!','🥈 Runner-up','🥉 Third place'][k]||'Finished #'+(k+1)}</b></p>`}
  else h+=`<p>Round ${T.i+1}/${POOL.length} — vs <b>${esc(POOL[T.i][0])}</b> (you: ${T.i%2?'Black':'White'})</p>`}
 else{h='<h2>🏆 Cup</h2>'+T.rd.map(pr=>`<h3>${{4:'Quarterfinals',2:'Semifinals',1:'Final'}[pr.length]}</h3>`+pr.map(m=>`<div class="hi">${esc(pn(m.a))} vs ${esc(pn(m.b))} → ${m.w==null?'⏳':'<b>'+esc(pn(m.w))+'</b>'}</div>`).join('')).join('');
  if(T.end)h+=`<p><b>${T.end=='champ'?'🏆 You won the Cup!':'❌ Eliminated'}</b></p>`;else if(T.sw)h+='<p><small>Draw — rematch with swapped colors</small></p>'}
 $('tv').innerHTML=h;$('tp').hidden=!!T.end;$('tn').classList.add('on')}
// Start your next tournament game
function tnPlay(){let o,col;
 if(TN.t=='champ'){o=TN.i;col=TN.i%2?'b':'w'}else{const m=TN.rd[TN.rd.length-1].find(m=>m.w==null);o=m.a<0?m.b:m.a;col=(TN.rd.length+TN.sw)%2?'b':'w'}
 S.mode='pvc';S.lv=POOL[o][2];$('mo').value='pvc';$('lv').value=S.lv;apply();newGame(1);G.me=col;G.fl=col=='b';G.tn=1;snd(523,.2);render();aiTurn()}
$('tp').onclick=()=>{$('tn').classList.remove('on');tnPlay()};
$('tq').onclick=()=>{$('tn').classList.remove('on');menu('main')};
/* ---------- RENDER ---------- */
const fmt=ms=>{const s=Math.max(0,Math.ceil(ms/1000));return String(s/60|0).padStart(2,'0')+':'+String(s%60).padStart(2,'0')};
function clock(){const t=cur().t;for(const c of'wb'){$('t'+c).querySelector('b').textContent=fmt(G.tm[c]);$('t'+c).classList.toggle('on',!G.over&&t==c)}}
const PU='https://cdn.jsdelivr.net/gh/lichess-org/lila@master/public/piece/cburnett/';
// Piece markup: SVG set (falls back to Unicode glyph if the CDN is unreachable) or Unicode
const pc=p=>S.ps=='Pro'?`<img src="${PU}${p}.svg" alt="${GL[p[1]]}\uFE0E" draggable="false" onerror="this.replaceWith(this.alt)">`:(S.ps=='Classic'&&p[0]=='w'?OL:GL)[p[1]]+'\uFE0E';
function render(){const last=G.st.length-1,v=G.v??last,s=G.st[v],lg=legal(s),lm=v?G.rc[v-1].m:null,c=chk(s);
 const mv=G.sel!=null&&S.hl&&v==last?lg.filter(m=>m.f==G.sel):[];let h='';
 const ani=S.an&&G.an==v;G.an=-1;const dp=i=>G.fl?63-i:i,ht=G.hint||[];
 for(let k=0;k<64;k++){const i=dp(k),r=i>>3,f=i&7,p=s.b[i],cl=['q'];if((r+f)%2)cl.push('d');if(i==G.sel)cl.push('sel');if(lm&&(i==lm.f||i==lm.t))cl.push('lm');if(ht.includes(i))cl.push('ht');
  const x=mv.find(m=>m.t==i);if(x){cl.push('mv');if(x.x)cl.push('cp')}if(c&&p==s.t+'K')cl.push('ck');
  const sl=ani&&lm&&i==lm.t?` style="--dx:${((dp(lm.f)&7)-(k&7))*100};--dy:${((dp(lm.f)>>3)-(k>>3))*100}"`:'';
  h+=`<div class="${cl.join(' ')}" data-i="${i}" tabindex="0" role="gridcell" aria-label="${sq(i)}${p?' '+(p[0]=='w'?'white ':'black ')+NM[p[1]]:''}"${p&&p[0]==s.t?' draggable="true"':''}>`
   +(p?`<span class="${p[0]=='w'?'pw':'pb'}${sl?' sl':''}"${sl}>${pc(p)}</span>`:'')
   +(S.co&&(k&7)==0?`<i class="r">${8-r}</i>`:'')+(S.co&&k>>3==7?`<i class="f">${'abcdefgh'[f]}</i>`:'')+'</div>'}
 $('bd').innerHTML=h;
 const o=G.over;$('sts').textContent=G.wait?'⏳ Waiting for opponent — room '+NET.code:o?'🏁 '+(o.w?(o.w=='w'?'White wins — ':'Black wins — '):'')+o.msg:(c?'⚠ CHECK! ':'')+(s.t=='w'?'♔ White\'s turn':'♚ Black\'s turn')+(S.mode=='pvc'&&s.t==AIC()?' ('+(S.lv>2?GM[S.lv-3][0]:'computer')+' is thinking)':'');
 let mh='';for(let i=0;i<G.rc.length;i+=2)mh+=`<span>${i/2+1}.</span><span class="m${v==i+1?' cur':''}" data-v="${i+1}">${esc(G.rc[i].sn)}</span>`+(G.rc[i+1]?`<span class="m${v==i+2?' cur':''}" data-v="${i+2}">${esc(G.rc[i+1].sn)}</span>`:'<span></span>');
 $('mh').innerHTML=mh;$('mh').scrollTop=1e6;
 const cp={w:[],b:[]};G.rc.forEach((r,i)=>{if(r.cap)cp[i%2?'b':'w'].push(r.cap)});
 const sc=a=>a.reduce((z,x)=>z+V[x[1]],0),df=(sc(cp.w)-sc(cp.b))/100,line=(a,n)=>`${n} captured: ${a.sort((x,y)=>V[y[1]]-V[x[1]]).map(x=>GL[x[1]]+'\uFE0E').join('')} `;
 $('cw').innerHTML=line(cp.w,'White')+(df>0?`<small>+${df}</small>`:'');$('cb').innerHTML=line(cp.b,'Black')+(df<0?`<small>+${-df}</small>`:'');
 const win=x=>x.r==(x.u=='b'?'Black Wins':'White Wins'),w=HI.filter(win).length,d=HI.filter(x=>x.r=='Draw').length,l=HI.length-w-d;
 $('stt').innerHTML=[['Games',HI.length],['Wins',w],['Losses',l],['Draws',d],['Win %',HI.length?Math.round(w/HI.length*100):0]].map(([a,b])=>`<div><b>${b}</b>${a}</div>`).join('');
 $('gh').innerHTML=HI.slice(0,8).map(x=>`<div class="hi"><b>${esc(x.d)}</b><br>${x.m=='pvc'?'Player vs Computer':x.m=='online'?'Online game':'Player vs Player'} · ${esc(x.r)} · ${esc(x.n)} moves</div>`).join('')||'<small>No games yet</small>';
 const on=S.mode=='pvc'?(S.lv>2?GM[S.lv-3][0]:['Easy bot','Medium bot','Hard bot'][S.lv]):S.mode=='online'?'Opponent':'';
 for(const c of'wb')$('t'+c).querySelector('span').textContent=(c=='w'?'White':'Black')+(on?(G.me==c?' · You':' · '+on):'');
 clock()}
function apply(){const t=TH[S.th]||TH.Classic,b=$('bd');b.style.setProperty('--l',t[0]);b.style.setProperty('--dk',t[1]);b.classList.toggle('cls',S.ps=='Classic');
 $('tmc').hidden=!S.tm;$('lv').hidden=S.mode!='pvc';$('sd').hidden=S.mode!='pvc';$('tc').disabled=S.mode=='online';$('bsn').textContent=S.snd?'🔊':'🔇'}
/* ---------- SETTINGS ---------- */
const F=[['th','Board Theme',Object.keys(TH)],['ps','Piece Style',['Pro','Solid','Classic']],['snd','Sound'],['an','Move Animation'],['co','Coordinates'],['hl','Highlight Moves'],['tm','Timer']];
function openSettings(){$('sf').innerHTML=F.map(([k,l,o])=>`<label>${l}`+(o?`<select data-k="${k}" aria-label="${l}">${o.map(x=>`<option${S[k]==x?' selected':''}>${x}</option>`).join('')}</select>`:`<input type="checkbox" data-k="${k}" aria-label="${l}"${S[k]?' checked':''}>`)+'</label>').join('');$('sm').classList.add('on')}
$('sf').onchange=e=>{const t=e.target,k=t.dataset.k;S[k]=t.type=='checkbox'?+t.checked:t.value;save('cm_s',S);apply();render()};
$('bs').onclick=openSettings;$('sc').onclick=()=>$('sm').classList.remove('on');
/* ---------- EVENTS ---------- */
const bd=$('bd');
bd.onclick=e=>{const q=e.target.closest('.q');if(q)click(+q.dataset.i)};
bd.ondragstart=e=>{const q=e.target.closest('.q');if(!q||lock())return;G.sel=+q.dataset.i;e.dataTransfer.setData('text','x')};
bd.ondragover=e=>e.preventDefault();
bd.ondrop=e=>{e.preventDefault();const q=e.target.closest('.q');if(q&&G.sel!=null)click(+q.dataset.i)};
$('mh').onclick=e=>{const m=e.target.closest('[data-v]');if(m){const v=+m.dataset.v;G.v=v==G.st.length-1?null:v;render()}};
$('pm').onclick=e=>{const b=e.target.closest('[data-p]');if(!b||!G.pend)return;const m=G.pend.find(x=>x.p==b.dataset.p);G.pend=null;$('pm').classList.remove('on');mv(m)};
$('bn').onclick=()=>{if(!G.rc.length||G.over||confirm('Start a new game?'))newGame()};
$('bu').onclick=undo;$('br').onclick=redo;
$('bz').onclick=()=>{if(G.over||!confirm('Resign?'))return;const t=S.mode!='pvp'?G.me:cur().t;finish({t:'RESIGN',w:t=='w'?'b':'w',msg:(t=='w'?'White':'Black')+' resigned'})};
$('bdr').onclick=()=>{if(G.over||G.tn)return;if(S.mode=='online'){post('/api/offer',{code:NET.code,c:NET.me}).catch(()=>{});alert('Draw offer sent');return}const ok=S.mode=='pvc'?(AIC()=='w'?1:-1)*ev(cur())<=50:confirm((cur().t=='w'?'White':'Black')+' offers a draw. Does the opponent accept?');
 if(ok)finish({t:'DRAW',w:0,msg:'Draw by agreement'});else if(S.mode=='pvc')alert('Computer declined the draw offer.')};
$('bsn').onclick=()=>{S.snd=S.snd?0:1;save('cm_s',S);apply()};
$('sd').onchange=e=>{S.sd=e.target.value;save('cm_s',S);newGame()};
$('bf').onclick=()=>{G.fl=!G.fl;render()};$('bh').onclick=hint;
// Copy game as PGN
$('bp').onclick=()=>{const o=G.over,r=o?(o.w?(o.w=='w'?'1-0':'0-1'):'1/2-1/2'):'*',cm=S.mode=='pvc'?'Computer':'Player';
 let t=`[Event "Chess Master"]\n[Date "${new Date().toISOString().slice(0,10).replace(/-/g,'.')}"]\n[White "${S.mode=='pvc'&&G.me=='b'?cm:'Player'}"]\n[Black "${S.mode=='pvc'&&G.me=='w'?cm:'Player'}"]\n[Result "${r}"]\n\n`;
 G.rc.forEach((x,i)=>t+=(i%2?'':(i/2+1)+'. ')+x.sn+' ');t+=r;
 (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>alert('PGN copied'),()=>prompt('PGN:',t))};
$('mo').onchange=e=>{NET=null;if(e.target.value=='online'){$('oi').textContent='';$('om').classList.add('on');return}S.mode=e.target.value;save('cm_s',S);apply();newGame()};
$('lv').onchange=e=>{S.lv=+e.target.value;save('cm_s',S);newGame()};
$('tc').onchange=e=>{S.tc=+e.target.value;save('cm_s',S);newGame()};
$('r1').onclick=()=>{$('rm').classList.remove('on');if(G.tn)tnShow();else newGame()};$('r3').onclick=()=>$('rm').classList.remove('on');
$('r2').onclick=()=>{$('rm').classList.remove('on');G.v=0;render()};
addEventListener('keydown',e=>{const t=e.target;
 if(e.key=='Escape'){$('sm').classList.remove('on');$('rm').classList.remove('on');$('pm').classList.remove('on');G.pend=null;return}
 if(t.matches&&t.matches('.q')&&(e.key=='Enter'||e.key==' ')){e.preventDefault();click(+t.dataset.i);const q=bd.querySelector(`[data-i="${t.dataset.i}"]`);if(q)q.focus();return}
 if(/select|input/i.test(t.tagName))return;
 if(e.key=='ArrowLeft')view(-1);else if(e.key=='ArrowRight')view(1);else if(e.key=='u')undo();else if(e.key=='r')redo();else if(e.key=='n')$('bn').click();else if(e.key=='f')$('bf').click();else if(e.key=='h')hint()});
// Clock tick
setInterval(()=>{const n=Date.now(),d=n-G.last;G.last=n;if(!S.tm||G.over||G.wait||G.idle||MENU())return;const t=cur().t;G.tm[t]-=d;
 if(G.tm[t]<=0){G.tm[t]=0;finish({t:'TIME',w:t=='w'?'b':'w',msg:(t=='w'?'White':'Black')+' ran out of time'})}clock()},200);
addEventListener('beforeunload',()=>G&&persist());
/* ---------- INIT ---------- */
(function(){if(S.mode=='online')S.mode='pvc';
 $('lv').insertAdjacentHTML('beforeend','<optgroup label="Grandmasters (Stockfish simulation)">'+GM.map((g,i)=>`<option value="${i+3}">${g[0]} · ~${g[1]}</option>`).join('')+'</optgroup>');
 $('mo').value=S.mode;$('lv').value=S.lv;$('sd').value=S.sd;$('tc').value=S.tc;apply();newGame(1);G.idle=true;menu('main')
 const rm=new URLSearchParams(location.search).get('room');if(rm)joinRoom(rm.toUpperCase().slice(0,5))})();
'''

README_MD = r'''# ♞ Chess Master

Brauzerda ishlaydigan to'liq shaxmat o'yini (frontend-only, backend kerak emas).

## Features
- Barcha qoidalar: shax, mat, pat, rokirovka, en passant, piyoda almashishi, 3 marta takrorlanish, 50 yurish, yetarsiz material
- Player vs Player va Player vs Computer (Easy / Medium / Hard)
- Timer (1–30 daq), yurishlar tarixi (SAN), olingan donalar, Undo / Redo, Resign, Draw taklifi
- Game History va statistika, natija modali
- Glassmorphism dark UI, 6 ta taxta mavzusi, responsive (desktop/tablet/telefon)
- Oq/qora tanlash (yoki tasodifiy), taxtani aylantirish, Hint (eng yaxshi yurish), PGN nusxalash, silliq yurish animatsiyasi, SVG donalar
- Ovoz effektlari (WebAudio), LocalStorage (sozlamalar, joriy o'yin, tarix)

## Technologies
HTML5, CSS3, JavaScript ES6+. Shaxmat dvigateli o'zimiz yozgan (kutubxonasiz). Hard darajasi uchun Stockfish.js (cdnjs CDN).

## Installation
O'rnatish shart emas. Uchta fayl bir papkada bo'lsin: `index.html`, `style.css`, `script.js`.

## How to run
`index.html` ni brauzerda oching. Yoki lokal server:
```
python3 -m http.server 8000   # so'ng http://localhost:8000
```

## Game controls
- Donani bosing, so'ng belgilangan katakka bosing (yoki sudrab tashlang)
- Klaviatura: `Tab` — kataklar, `Enter`/`Space` — tanlash, `N` yangi o'yin, `U` undo, `R` redo, `←` `→` yurishlarni ko'rish, `Esc` — oynani yopish
- Tarixdagi yurishni bossangiz, o'sha holat ko'rsatiladi

## AI mode
- **Easy** — o'zining dvigateli (1 yurish + tasodifiylik)
- **Medium** — Stockfish, Skill Level 5
- **Hard** — Stockfish, Skill Level 20 (~1 soniya/yurish)
- Stockfish CDN'dan Web Worker orqali yuklanadi; internet bo'lmasa yoki bloklansa o'zining minimax dvigateliga o'tadi.
- Rangni tanlash mumkin: Play White / Play Black / Random. Klaviatura: `F` aylantirish, `H` hint.

## Settings
Board Theme (Classic, Green, Blue, Brown, Neon, Dark), Piece Style, Sound, Move Animation, Coordinates, Highlight Moves, Timer.

## Project structure
```
index.html   — sahifa tuzilmasi va modallar
style.css    — dizayn, mavzular, responsive
script.js    — dvigatel (qoidalar), AI + Stockfish, UI, LocalStorage
README.md
```

## Online o'yin (do'st bilan)
1. Serverni ishga tushiring: `python3 chess_game.py --lan` (bir Wi-Fi tarmog'idagi qurilmalar uchun) — konsolda `http://192.168.x.x:8000/` manzili chiqadi.
2. Mode → **Online (friend)** → **Create room**. 5 belgili kod (va havola) paydo bo'ladi.
3. Do'stingiz o'sha manzilni ochib, kodni **Join** ga kiritadi (yoki `…/?room=KOD` havolasini ochadi).
4. Rang tasodifiy beriladi. Yurish, taslim bo'lish, durang taklifi va vaqt tugashi sinxron ishlaydi.
- Internet orqali o'ynash uchun portni tunnel bilan oching, masalan `cloudflared tunnel --url http://localhost:8000` yoki `ngrok http 8000`.
- Xonalar server xotirasida saqlanadi (server o'chsa yo'qoladi). Server faqat yurishlarni uzatadi; qoidalarni har bir brauzer o'zi tekshiradi.

## Grandmasters
Level ro'yxatidagi **Grandmasters** bo'limida 6 ta raqib: Judit Polgár, Mikhail Tal, Bobby Fischer, Garry Kasparov, Hikaru Nakamura, Magnus Carlsen. Bu Stockfish'ning taxminiy **kuch darajasi** simulyatsiyasi (Skill Level + yurish vaqti) — haqiqiy o'yinchilarning uslubi yoki o'yini emas. Elo qiymatlari taxminiy.

## Bosh menyu va turnirlar
- O'yin sahifa ochilganda **o'zi boshlanmaydi** — avval bosh menyu chiqadi (Resume / Continue, Quick Game, Grandmasters, Online, Championship, Cup, Settings). Yuqoridagi **☰ Menu** tugmasi istalgan vaqt menyuga qaytaradi.
- **Championship** — 9 raqib (3 bot + 6 grandmaster) bilan liga: har biriga qarshi bitta o'yin (ranglar navbatma-navbat). Raqiblarning o'zaro natijalari Elo bo'yicha simulyatsiya qilinadi, jadvalda o'rningiz ko'rinadi (g'alaba 1, durang ½).
- **Cup** — 8 o'yinchilik olib tashlash (nokaut) turniri: chorak final → yarim final → final. Siz bilan o'ynamaydigan o'yinlar simulyatsiya qilinadi. Durang bo'lsa ranglar almashtirilib qayta o'ynaladi.
- Turnir o'yinlarida Undo, Redo, Hint va durang taklifi o'chirilgan. Turnir holati LocalStorage'da saqlanadi (o'yin o'rtasida sahifani yangilasangiz, o'sha o'yin hisobga olinmaydi).
'''

ROUTES = {
    "/": ("text/html", INDEX_HTML), "/index.html": ("text/html", INDEX_HTML),
    "/style.css": ("text/css", STYLE_CSS), "/script.js": ("text/javascript", SCRIPT_JS),
    "/README.md": ("text/markdown", README_MD),
}


ROOMS = {}
COND = threading.Condition()


def clean(o):
    """Sanitize a game-over object coming from a client."""
    o = o if isinstance(o, dict) else {}
    w = o.get("w") if o.get("w") in ("w", "b") else 0
    return {"t": str(o.get("t", "DRAW"))[:20], "w": w, "msg": str(o.get("msg", ""))[:60], "net": 1}


def api(path, q, body):
    """Online-play API (rooms in memory). The server only relays moves; clients validate chess rules."""
    with COND:
        if path == "/api/new":
            for k in [k for k, v in ROOMS.items() if time.time() - v["t"] > 6 * 3600]:
                del ROOMS[k]
            code = "".join(random.choice("ABCDEFGHJKMNPQRSTUVWXYZ23456789") for _ in range(5))
            tc = body.get("tc") if body.get("tc") in (1, 3, 5, 10, 15, 30) else 10
            ROOMS[code] = dict(moves=[], joined=False, over=None, offer=None, tc=tc, ver=1, host=random.choice("wb"), t=time.time())
            return dict(code=code, c=ROOMS[code]["host"], tc=tc)
        r = ROOMS.get(str(body.get("code") or q.get("code") or "").upper())
        if not r:
            return dict(err="Room not found")
        c = body.get("c") or q.get("c")
        if path == "/api/poll":
            try:
                v, n = int(q.get("v", 0)), max(0, int(q.get("n", 0)))
            except ValueError:
                return dict(err="Bad request")
            COND.wait_for(lambda: r["ver"] > v, timeout=20)
            return dict(v=r["ver"], moves=r["moves"][n:], joined=r["joined"], over=r["over"], offer=r["offer"])
        if path == "/api/join":
            if r["joined"]:
                return dict(err="Room is full")
            r["joined"] = True
            res = dict(c="b" if r["host"] == "w" else "w", tc=r["tc"])
        elif path == "/api/move":
            m, n = body.get("m") or {}, body.get("n")
            ok = all(isinstance(m.get(k), int) and 0 <= m[k] < 64 for k in ("f", "t"))
            if not ok or r["over"] or not r["joined"] or n != len(r["moves"]) or c != "wb"[n % 2]:
                return dict(err="Illegal move or turn")
            r["moves"].append({"f": m["f"], "t": m["t"], "p": m.get("p") if m.get("p") in ("Q", "R", "B", "N") else None})
            r["offer"] = None
            res = dict(ok=1)
        elif path == "/api/end":
            if not r["over"]:
                r["over"] = clean(body.get("o"))
            res = dict(ok=1)
        elif path == "/api/offer" and c in ("w", "b"):
            r["offer"] = None if body.get("clear") else c
            res = dict(ok=1)
        else:
            return dict(err="Bad request")
        r["ver"] += 1
        COND.notify_all()
        return res


class Handler(http.server.BaseHTTPRequestHandler):
    """Serves the embedded game files from memory plus the /api/* online endpoints."""

    def send_body(self, ctype, data):
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path.startswith("/api/"):
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            return self.send_body("application/json", json.dumps(api(u.path, q, {})).encode())
        route = ROUTES.get(u.path)
        if not route:
            return self.send_error(404)
        self.send_body(route[0], route[1].encode("utf-8"))

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        try:
            body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 10000)) or b"{}")
        except ValueError:
            body = {}
        if not path.startswith("/api/") or not isinstance(body, dict):
            return self.send_error(404)
        self.send_body("application/json", json.dumps(api(path, {}, body)).encode())

    def log_message(self, *args):
        pass


def lan_ip():
    """Best-effort LAN address for sharing with friends on the same network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def export(folder):
    """Write the embedded files to a folder."""
    os.makedirs(folder, exist_ok=True)
    for path, (_, text) in ROUTES.items():
        if path != "/":
            with open(os.path.join(folder, path[1:]), "w", encoding="utf-8") as f:
                f.write(text)
    print("Fayllar yozildi:", os.path.abspath(folder))


def main():
    ap = argparse.ArgumentParser(description="Chess Master")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--lan", action="store_true", help="LAN'da ochiq qilish (online o'yin uchun)")
    ap.add_argument("--export", metavar="PAPKA")
    a = ap.parse_args()
    if a.export:
        return export(a.export)
    socketserver.TCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    host = "0.0.0.0" if a.lan else "127.0.0.1"
    try:
        srv = socketserver.ThreadingTCPServer((host, a.port), Handler)
    except OSError:
        srv = socketserver.ThreadingTCPServer((host, 0), Handler)  # band bo'lsa — bo'sh port
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    print("Chess Master ishga tushdi:", url, "(to'xtatish: Ctrl+C)")
    if a.lan:
        print("Do'stlar uchun manzil: http://%s:%d/" % (lan_ip(), srv.server_address[1]))
    if not a.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nTo'xtatildi.")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
