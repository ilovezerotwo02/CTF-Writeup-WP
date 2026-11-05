(async()=>{
const H='0123456789abcdef';
const inp=document.querySelector('input[placeholder="请输入目标答案"]');
const btn=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='提交');
const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
if(!inp||!btn){alert('请先打开 vmshare 题目弹窗');return}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const toast=async()=>{let m='';for(let k=0;k<20;k++){await sleep(300);const el=[...document.querySelectorAll('.el-message')].map(e=>e.textContent).join('|');if(el){m=el;break}}return m};
set.call(inp,'flag{probe}');inp.dispatchEvent(new Event('input',{bubbles:true}));await sleep(600);btn.click();const p=await toast();
if(!p){alert('自检失败：提交后没有任何提示，脚本点不动弹窗，请确认题目弹窗在最前面');return}
console.log('自检提示:',p);
let i=0,err=0,freq=0;
for(const a of H)for(const b of H){
const f='flag{'+a+'174812_'+b+'1af718}';let done=0;
for(let t=0;t<4&&!done;t++){
set.call(inp,f);inp.dispatchEvent(new Event('input',{bubbles:true}));await sleep(600);btn.click();
const m=await toast();
if(/频繁/.test(m)){freq++;await sleep(25000);continue}
if(!m){await sleep(3000);continue}
done=1;err++;
if(!/错误/.test(m)){document.title='WIN '+f;console.log('%c FOUND '+f,'color:red');alert('FOUND '+f);return}
}
i++;document.title='['+i+'/256] '+f;console.log(i,f);
await sleep(7000)}
document.title='DONE';alert('小写空间跑完，未命中。错误'+err+' 限流'+freq)
})()