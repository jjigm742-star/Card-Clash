"""3.0 FastAPI/Render-layout online and UI smoke checks. Run as python tests/test_3_0_online.py."""
import os, time, json, asyncio, subprocess, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright
from websockets.asyncio.client import connect
BASE=Path(__file__).resolve().parents[1];PORT=8893

def wait_server(p):
 for _ in range(80):
  if p.poll() is not None:raise RuntimeError('server exited')
  try:
   with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/health',timeout=.4) as r:
    d=json.load(r)
   assert d['version']=='3.0',d
   return
  except Exception:time.sleep(.12)
 raise RuntimeError('server startup timeout')

async def main():
 proc=subprocess.Popen(['uvicorn','server:app','--host','127.0.0.1','--port',str(PORT),'--log-level','warning'],cwd=BASE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env={**os.environ,'CARDCLASH_CHROMIUM_PATH':'/usr/bin/chromium'})
 try:
  wait_server(proc)
  with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/config') as f:data=json.load(f)
  assert len(data['cards'])==92
  assert all(c.get('emoji') for c in data['cards'])
  assert data['version'].startswith('카드클래시 3.0')
  async with async_playwright() as p:
   b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   page=await b.new_page();errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
   html=(BASE/'app/online.html').read_text('utf-8').replace('<script src="decks.js"></script>','<script>'+(BASE/'app/decks.js').read_text('utf-8')+'</script>')
   stub='<script>window.fetch=async()=>({ok:true,json:async()=>('+json.dumps(data,ensure_ascii=False)+')});</script>'
   html=html.replace("<script>\n'use strict';",stub+"<script>\n'use strict';")
   await page.set_content(html,wait_until='load')
   await page.wait_for_function("() => document.querySelector('#deckStatus')?.textContent.includes('30')")
   await page.evaluate('''()=>{state={turn:4,active:0,priority:null,winner:null,logs:[],stacks:[],triggers:[],prompt:null,players:[{race:'Others',deck_count:20,hand_count:1,hand:['원한 인형'],grave:[],a:[{name:'도굴 고블린',uid:11,bonus:0,mods:[],actions:0}],b:[],me:50,te:100,summons:1},{race:'Sky',deck_count:20,hand_count:1,hand:null,grave:[],a:[{name:'벌새',uid:12,bonus:0,mods:[],actions:0}],b:[],me:100,te:100,summons:1}]};seat=0;room='TEST1';selection={zone:'a',id:11};render();}''')
   assert '👺' in await page.locator('#board').inner_text()
   assert '직접 공격' in await page.locator('#combatPreview').inner_text()
   await page.evaluate('''()=>{state.players[0].a=[{name:'좀비미라',uid:22,bonus:500,mods:[{delta:500,source:'칠흑의 망토'}],tempStealth:true,actions:0}];selection={zone:'a',id:22};render();}''')
   assert '직접 공격' in await page.locator('#combatPreview').inner_text(), 'online preview must show temporary cloak stealth'
   assert '🥷은신' in await page.locator('#board').inner_text(), 'online field must reveal temporary stealth'
   for n,k,v in [('암흑룡','cost',180),('돌진 양','cost',50),('북소리','cost',140),('좀비미라','atk',3000)]:
    assert next(c for c in data['cards'] if c['name']==n)[k]==v,(n,k)
   assert 'grant_stealth' in next(c for c in data['cards'] if c['name']=='칠흑의 망토')['effects']
   assert not errs,errs
   await b.close()
  async with connect(f'ws://127.0.0.1:{PORT}/ws') as a,connect(f'ws://127.0.0.1:{PORT}/ws') as b:
   await a.send(json.dumps({'type':'create','race':'Sky','deck':data['decks']['Sky']}))
   l=json.loads(await asyncio.wait_for(a.recv(),timeout=5))
   assert l['type']=='lobby'
   await b.send(json.dumps({'type':'join','code':l['room'],'race':'Others','deck':data['decks']['Others']}))
   assert (json.loads(await asyncio.wait_for(b.recv(),timeout=5)))['type']=='lobby'
   sa=json.loads(await asyncio.wait_for(a.recv(),timeout=15))
   sb=json.loads(await asyncio.wait_for(b.recv(),timeout=15))
   assert sa['type']==sb['type']=='state'
   assert sa['state']['players'][1]['hand'] is None
   assert sb['state']['players'][0]['hand'] is None
   assert sa['state']['players'][0]['deck_count']==24
   print('PASS: 3.0 online startup, 92 cards, emoji UI, battle preview, hidden hands, websocket match')
 finally:
  proc.terminate()
  try:out=proc.communicate(timeout=8)[0]
  except subprocess.TimeoutExpired:proc.kill();out=proc.communicate()[0]
  if proc.returncode not in (0,-15,-2):print(out.decode('utf8','replace')[-3000:])
if __name__=='__main__':asyncio.run(main())
