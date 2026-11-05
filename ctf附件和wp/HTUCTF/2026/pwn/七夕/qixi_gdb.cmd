# qixi_gift 自动检查点脚本（GDB command file）
# 用法（在 wsl -d Ubuntu-24 的 pwn-venv 里）：
#   gdb -q -x qixi_gdb.cmd ./qixi_gift
#
# 原理：程序在 4 个空函数（first_checkpoint / place_checkpoint /
# ribbon_checkpoint / gift_checkpoint）里留了断点位置，
# 这些函数体是空的，所以正确答案只能从运行时状态里读出来。

set pagination off
set confirm off
set disassembly-flavor intel

# 第 1 关：编号在 r12 里（stage_one 把 random_u64 的返回值 mov 到 r12）
break first_checkpoint
commands
  silent
  printf "\n[*] 第1关 卡片编号 r12 = 0x%lx  (%lu)\n", $r12, $r12
  printf "[*] 停住，按 continue 后把上面的十六进制填进去\n"
  continue
end

# 第 2 关：地点就是 gift_place 这个全局字符串
break place_checkpoint
commands
  silent
  printf "\n[*] 第2关 礼物地点 gift_place = %s\n", gift_place
  continue
end

# 第 3 关：丝带密码 = main 里 random_u32() 的返回值，作为参数传进 stage_three
break ribbon_checkpoint
commands
  silent
  printf "\n[*] 第3关 丝带密码 = %u  (0x%x)\n", $edi, $edi
  continue
end

# 第 4 关：盒子还锁着，直接把 gift_box_open 改成 1（全局变量，符号可直呼）
break gift_checkpoint
commands
  silent
  printf "\n[*] 第4关 gift_box_open 原值 = %d\n", gift_box_open
  set var gift_box_open = 1
  printf "[*] 已改为 %d，礼物盒即将打开\n", gift_box_open
  continue
end

run
