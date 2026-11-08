"""3.0 smoke/integration tests, Chromium headless: python tests/test_3_0_engine.py."""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
JS=r'''async()=>{
 const ok=(v,m)=>{if(!v)throw Error(m)};
 let results={};
 ok(DATA.cards.length===92,'92 cards');
 ok(new Set(DATA.cards.map(c=>c.id)).size===92,'unique ids');
 ok(DATA.cards.every(c=>c.emoji&&[...c.emoji].length<9),'all cards have compact emoji');
 ok(!CARDMAP['기생충']&&!CARDMAP['빗방울'],'deferred cards excluded');
 for(const [name,cost] of Object.entries({'최면술 로봇':105,'화산 분출':65,'저돌맹진':70,'마녀여왕':175,'대왕고래':215,'종이 비행기':40,'도굴 고블린':115}))ok(CARDMAP[name].cost===cost,'cost '+name);
 ok(!has(CARDMAP['벌새'],'rush')&&has(CARDMAP['벌새'],'on_summon_sky_swarm'),'hummingbird nerf');
 ok(has(CARDMAP['타이거드라고'],'smash')&&number(CARDMAP['타이거드라고'],'smash')===2,'tiger nerf');
 ok(number(CARDMAP['해룡 레비아탄'],'leviathan_buff')===1000,'leviathan buff');
 ok(number(CARDMAP['흉폭한 크라켄'],'smash')===2,'octopus buff');
 ok(CARDMAP['암흑룡'].cost===180,'2.5 dark dragon cost carried forward');
 ok(CARDMAP['좀비미라'].atk===3000,'2.5 zombie mummy power carried forward');
 ok(CARDMAP['돌진 양'].cost===50,'2.5 charging sheep cost carried forward');
 ok(CARDMAP['북소리'].cost===140,'2.5 drumbeat cost carried forward');
 ok(has(CARDMAP['칠흑의 망토'],'grant_stealth'),'2.5 cloak stealth effect carried forward');

 ok(has(CARDMAP['유령 고양이'],'stealth')&&has(CARDMAP['도굴 고블린'],'stealth'),'stealth standardized');
 for(let r of ['Land','Ocean','Sky','Others'])ok(deckCount(DATA.decks[r])===30,'default deck preserved '+r);
 results.data='pass';
 const reset=(r0='Others',r1='Land')=>{g={rng:3,turn:5,active:0,players:[r0,r1].map(r=>({race:r,deck:['크라켄','청새치','보호 가리비','해룡 레비아탄','평화의 참새','보물 상자','종이 비행기'],hand:[],grave:[],a:[],b:[],me:200,te:300,summons:0})),winner:null,logs:[],priority:null,passes:0,stack:[],attack:null,reactions:[],triggers:[],endingTurn:false,playedTechThisTurn:[false,false]};sel=null;uid=0;stackUid=0;};
 choice=async(_title,items)=>items[0]||null;
 chooseUpTo=async(_title,items,max)=>items.slice(0,max);
 reset();let gob=deploy(0,'도굴 고블린','a'),def=deploy(1,'크라켄','a');P(0).me=40;P(1).me=13;let count=P(1).deck.length;
 g.attack={owner:0,attacker:gob.uid,target:null};await resolveCombat();ok(P(1).deck.length===count-1,'stealth bypass');ok(g.triggers.length===1,'goblin trigger');await resolve(g.triggers.pop());ok(P(0).me===53&&P(1).me===0,'transfer lesser amount');results.goblin='pass';
 reset('Ocean','Land');let whale=deploy(0,'대왕고래','a');P(0).grave=['방어벽','생명의 물'];await resolve({type:'monster',owner:0,name:'@whaleEnd',source:whale.uid});ok(P(0).hand[0]==='방어벽'&&P(0).grave.length===1,'whale recovery');results.whale='pass';
 reset('Land','Sky');let bear=deploy(0,'헬킹콩','b');await resolve({type:'technique',owner:0,name:'저돌맹진',target:bear.uid});ok(bear.tempRush&&!bear.smashPlus,'rush only');
 results.rush='pass';
 reset('Sky','Land');let front=deploy(0,'종이 비행기','a'),rear=deploy(0,'벌새','b'),enemy=deploy(1,'크라켄','a');await resolve({type:'technique',owner:0,name:'전이'});ok(P(0).a.includes(rear)&&P(0).b.includes(front),'swap both lines');results.transfer='pass';
 reset('Others','Land');let doll=deploy(0,'원한 인형','b'),enemy2=deploy(1,'크라켄','a');let eid=enemy2.uid;await resolve({type:'monster',owner:0,name:'@active',kind:'doll_debuff',target:eid,source:doll.uid});ok(enemy2.bonus===-1000,'doll active -1000');
 reset('Others','Land');P(0).grave=['원한 인형'];g.reactions=[{owner:0,name:'원한 인형',tag:'reaction_doll:A'}];await oneReaction();ok(P(0).a.length===1&&!P(0).grave.includes('원한 인형'),'doll reaction without enemy');results.doll='pass';
 reset('Others','Land');let cloakUnit=deploy(0,'좀비미라','a');deploy(1,'크라켄','a');
 let beforeDeck=P(1).deck.length;
 await resolve({type:'technique',owner:0,name:'칠흑의 망토',target:cloakUnit.uid});
 ok(cloakUnit.bonus===500&&cloakUnit.tempStealth&&stealth(cloakUnit),'cloak grants +500 and temporary stealth');
 sel={i:0,zone:'a',id:cloakUnit.uid};refresh();
 ok(document.querySelector('#combatPreview').textContent.includes('직접 공격'),'cloak stealth battle preview');
 g.attack={owner:0,attacker:cloakUnit.uid,target:null};await resolveCombat();
 ok(P(1).deck.length===beforeDeck-2,'cloak bypasses occupied A line and deals smash 2');
 completeEndTurn();ok(!cloakUnit.tempStealth&&!stealth(cloakUnit),'cloak stealth ends with turn');
 results.cloak='pass';
 reset('Ocean','Land');let fish=deploy(0,'넘기기 넙치','a');g.stack=[{id:8,type:'technique',name:'파이어볼',owner:1,canceled:false}];g.priority=0;ok(eligibleAbilities(0,fish).includes('flounder'),'flounder available');await resolve({type:'monster',name:'@active',owner:0,kind:'flounder',source:fish.uid,negateId:8});ok(g.stack[0].canceled,'flounder counter');results.flounder='pass';
 reset('Land','Ocean');let x=deploy(1,'크라켄','a'),y=deploy(1,'청새치','a');await resolve({type:'technique',owner:0,name:'지진',targets:[x.uid,y.uid]});ok(x.bonus===-2000&&y.bonus===-2000,'earthquake both');results.earthquake='pass';
 reset('Sky','Land');let bird=deploy(0,'종이 비행기','a');deploy(1,'크라켄','a');sel={i:0,zone:'a',id:bird.uid};refresh();ok(document.querySelector('#combatPreview').textContent.includes('직접 공격'),'forecast bypass direct');let buttons=[...document.querySelectorAll('.card')];ok(buttons.some(b=>b.querySelector('.card-emoji')?.textContent==='✈️'),'emoji icon rendered');results.ui='pass';
 return results;
}'''
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  html=(ROOT/'app/solo.html').read_text('utf-8').replace('<script src="decks.js"></script>','<script>'+(ROOT/'app/decks.js').read_text('utf-8')+'</script>')
  await page.set_content(html,wait_until='load')
  print(json.dumps(await page.evaluate(JS),ensure_ascii=False,indent=2))
  assert not errors,errors
  await b.close()
if __name__=='__main__':asyncio.run(main())
