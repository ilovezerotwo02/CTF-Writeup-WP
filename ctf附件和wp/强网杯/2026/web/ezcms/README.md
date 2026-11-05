# ezcms 题目文件（强网杯 Web）

- Flag：`flag{8c9ab620-7cf7-4693-985a-17a80b43c09c}`
- 完整题解：`WP-ezcms.md`
- 复现脚本：`exp_ezcms.py`
- 附件/证据：`attachments/`

题目只提供了容器地址（nc 101.200.174.245 34855），无官方附件；
`attachments/` 内是解题产物：SQL 报错页、管理员哈希、JSP 载荷、flag 回显证据。

快速复现：

```bash
python exp_ezcms.py --stage flag
# 或分阶段
python exp_ezcms.py --stage extract
python exp_ezcms.py --stage crack --wordlist rockyou.txt
python exp_ezcms.py --stage admin --user altair --password freedom
python exp_ezcms.py --stage rce --cmd "id"
```
