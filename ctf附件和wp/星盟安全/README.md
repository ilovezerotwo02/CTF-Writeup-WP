# 星盟安全

B 站「星盟安全」的 PWN 教程，跟着做练习的时候把课件和代码存下来了。课件署名 IZAYOI，这里只是把跟练的东西归到一起。

## chapter_3 · 格式化字符串

51 页课件，从 printf 的格式串讲起：`%p` 泄露、`%s` 取值、`%n / %hn / %hhn` 写值，怎么用 `fmtarg` 定位自己的输入落在第几个参数，以及 32 位和 64 位传参的差别。后半部分按套路走，先是栈上格式化，再是非栈上的四马分肥和诸葛连弩，最后是星号和只能打一次的杂项。

课件里带了 6 道例题：网鼎杯 2018 easyfmt、Playfmt、Pwn1、强网杯 2020 siri、网鼎杯 2020 quantum_entanglement、ciscn 2019 sw_1。

### 跟练程序

照课件顺序自己写的五组，源码和编译好的程序都在，方便对着调。`.i64` 是 IDA 数据库，`.py` 是当时写的 exp。

| 目录 | 内容 |
|---|---|
| fmt_test1 | 先看栈。`fmt_test_1` 打印局部变量的内容和地址；`fmt_test_2` 循环 `read` 后直接 `printf`，要把 `test3` 写成 100 才给 shell |
| fmt_test2 | 栈上格式化。循环读入直接 `printf`，输入 `quit` 退出，练的是改 got |
| fmt_test3 | 非栈上，底子是 HITCON-Training lab9，buf 在 bss；另有一份 `_buf` 版本，多绕一层指针 |
| fmt_test4 | 星号。从 `/dev/random` 读两个随机数，相等才给 shell，得用 `%*c` 控制宽度一次写完 |
| fmt_test5 | 只能打一次，`printf` 完就 return。分有 `system` 和没有 `system` 两种，各自编了 pie 与 nopie |

有个坑：几个 exp 里 `import duchao_pwn_script` 是别人写的辅助模块，仓库里没有，直接跑会报错。要么把它补上，要么把用到的函数挪进脚本里。
