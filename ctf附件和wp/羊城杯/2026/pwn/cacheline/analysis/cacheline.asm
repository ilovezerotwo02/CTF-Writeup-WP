
cacheline.so:     file format elf64-x86-64


Disassembly of section .plt:

0000000000001000 <ngx_http_arg@plt-0x10>:
    1000:	push   QWORD PTR [rip+0x4f62]        # 5f68 <free@plt+0x4e68>
    1006:	jmp    QWORD PTR [rip+0x4f64]        # 5f70 <free@plt+0x4e70>
    100c:	nop    DWORD PTR [rax+0x0]

0000000000001010 <ngx_http_arg@plt>:
    1010:	jmp    QWORD PTR [rip+0x4f62]        # 5f78 <free@plt+0x4e78>
    1016:	push   0x0
    101b:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001020 <ngx_http_output_filter@plt>:
    1020:	jmp    QWORD PTR [rip+0x4f5a]        # 5f80 <free@plt+0x4e80>
    1026:	push   0x1
    102b:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001030 <connect@plt>:
    1030:	jmp    QWORD PTR [rip+0x4f52]        # 5f88 <free@plt+0x4e88>
    1036:	push   0x2
    103b:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001040 <syscall@plt>:
    1040:	jmp    QWORD PTR [rip+0x4f4a]        # 5f90 <free@plt+0x4e90>
    1046:	push   0x3
    104b:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001050 <socket@plt>:
    1050:	jmp    QWORD PTR [rip+0x4f42]        # 5f98 <free@plt+0x4e98>
    1056:	push   0x4
    105b:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001060 <ngx_alloc@plt>:
    1060:	jmp    QWORD PTR [rip+0x4f3a]        # 5fa0 <free@plt+0x4ea0>
    1066:	push   0x5
    106b:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001070 <write@plt>:
    1070:	jmp    QWORD PTR [rip+0x4f32]        # 5fa8 <free@plt+0x4ea8>
    1076:	push   0x6
    107b:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001080 <ngx_hextoi@plt>:
    1080:	jmp    QWORD PTR [rip+0x4f2a]        # 5fb0 <free@plt+0x4eb0>
    1086:	push   0x7
    108b:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001090 <read@plt>:
    1090:	jmp    QWORD PTR [rip+0x4f22]        # 5fb8 <free@plt+0x4eb8>
    1096:	push   0x8
    109b:	jmp    1000 <ngx_http_arg@plt-0x10>

00000000000010a0 <ngx_pool_cleanup_add@plt>:
    10a0:	jmp    QWORD PTR [rip+0x4f1a]        # 5fc0 <free@plt+0x4ec0>
    10a6:	push   0x9
    10ab:	jmp    1000 <ngx_http_arg@plt-0x10>

00000000000010b0 <htons@plt>:
    10b0:	jmp    QWORD PTR [rip+0x4f12]        # 5fc8 <free@plt+0x4ec8>
    10b6:	push   0xa
    10bb:	jmp    1000 <ngx_http_arg@plt-0x10>

00000000000010c0 <_exit@plt>:
    10c0:	jmp    QWORD PTR [rip+0x4f0a]        # 5fd0 <free@plt+0x4ed0>
    10c6:	push   0xb
    10cb:	jmp    1000 <ngx_http_arg@plt-0x10>

00000000000010d0 <ngx_pcalloc@plt>:
    10d0:	jmp    QWORD PTR [rip+0x4f02]        # 5fd8 <free@plt+0x4ed8>
    10d6:	push   0xc
    10db:	jmp    1000 <ngx_http_arg@plt-0x10>

00000000000010e0 <close@plt>:
    10e0:	jmp    QWORD PTR [rip+0x4efa]        # 5fe0 <free@plt+0x4ee0>
    10e6:	push   0xd
    10eb:	jmp    1000 <ngx_http_arg@plt-0x10>

00000000000010f0 <ngx_http_send_header@plt>:
    10f0:	jmp    QWORD PTR [rip+0x4ef2]        # 5fe8 <free@plt+0x4ee8>
    10f6:	push   0xe
    10fb:	jmp    1000 <ngx_http_arg@plt-0x10>

0000000000001100 <free@plt>:
    1100:	jmp    QWORD PTR [rip+0x4eea]        # 5ff0 <free@plt+0x4ef0>
    1106:	push   0xf
    110b:	jmp    1000 <ngx_http_arg@plt-0x10>

Disassembly of section .text:

0000000000001120 <.text>:
    1120:	mov    rax,rdi
    1123:	shr    rax,0x1e
    1127:	xor    rax,rdi
    112a:	movabs rdx,0xbf58476d1ce4e5b9
    1134:	imul   rax,rdx
    1138:	mov    rdx,rax
    113b:	shr    rdx,0x1b
    113f:	xor    rdx,rax
    1142:	movabs rax,0x94d049bb133111eb
    114c:	imul   rdx,rax
    1150:	mov    rax,rdx
    1153:	shr    rax,0x1f
    1157:	xor    rax,rdx
    115a:	ret
    115b:	push   r15
    115d:	push   r14
    115f:	push   r13
    1161:	push   r12
    1163:	push   rbp
    1164:	push   rbx
    1165:	sub    rsp,0x10
    1169:	mov    QWORD PTR [rsp],rdi
    116d:	mov    r14,rsi
    1170:	mov    QWORD PTR [rsp+0x8],rsi
    1175:	mov    r13,rdx
    1178:	mov    r12,rcx
    117b:	xor    rdi,rcx
    117e:	movabs rax,0x9e3779b97f4a7c15
    1188:	xor    rdi,rax
    118b:	call   1120 <free@plt+0x20>
    1190:	mov    rbx,rax
    1193:	test   r12,r12
    1196:	je     11f2 <free@plt+0xf2>
    1198:	mov    rbp,r13
    119b:	lea    r15,[r13+r12*8+0x0]
    11a0:	mov    r13d,0x0
    11a6:	mov    r12d,0x11
    11ac:	mov    rdi,r14
    11af:	add    rdi,QWORD PTR [rbp+0x0]
    11b3:	call   1120 <free@plt+0x20>
    11b8:	xor    rax,rbx
    11bb:	mov    ecx,r12d
    11be:	rol    rax,cl
    11c1:	mov    rbx,QWORD PTR [rsp]
    11c5:	xor    rbx,r13
    11c8:	add    rbx,rax
    11cb:	add    rbp,0x8
    11cf:	movabs rax,0x517cc1b727220a95
    11d9:	add    r14,rax
    11dc:	add    r12d,0xb
    11e0:	movabs rax,0x6a09e667f3bcc909
    11ea:	add    r13,rax
    11ed:	cmp    rbp,r15
    11f0:	jne    11ac <free@plt+0xac>
    11f2:	mov    rdi,QWORD PTR [rsp+0x8]
    11f7:	xor    rdi,rbx
    11fa:	movabs rax,0xa54ff53a5f1d36f1
    1204:	xor    rdi,rax
    1207:	call   1120 <free@plt+0x20>
    120c:	add    rsp,0x10
    1210:	pop    rbx
    1211:	pop    rbp
    1212:	pop    r12
    1214:	pop    r13
    1216:	pop    r14
    1218:	pop    r15
    121a:	ret
    121b:	sub    rsp,0x38
    121f:	mov    rax,QWORD PTR [rdi+0x30]
    1223:	mov    QWORD PTR [rsp],rax
    1227:	mov    rax,QWORD PTR [rdi+0x38]
    122b:	mov    QWORD PTR [rsp+0x8],rax
    1230:	mov    rax,QWORD PTR [rdi+0x40]
    1234:	mov    QWORD PTR [rsp+0x10],rax
    1239:	mov    rax,QWORD PTR [rdi+0x48]
    123d:	mov    QWORD PTR [rsp+0x18],rax
    1242:	mov    rax,QWORD PTR [rdi+0x50]
    1246:	mov    QWORD PTR [rsp+0x20],rax
    124b:	mov    rdx,rsp
    124e:	mov    ecx,0x5
    1253:	mov    rsi,QWORD PTR [rip+0x53b6]        # 6610 <ngx_modules+0x490>
    125a:	mov    rdi,QWORD PTR [rip+0x53a7]        # 6608 <ngx_modules+0x488>
    1261:	call   115b <free@plt+0x5b>
    1266:	add    rsp,0x38
    126a:	ret
    126b:	sub    rsp,0x38
    126f:	mov    rax,QWORD PTR [rdi+0x28]
    1273:	mov    QWORD PTR [rsp],rax
    1277:	mov    rax,QWORD PTR [rdi+0x30]
    127b:	mov    QWORD PTR [rsp+0x8],rax
    1280:	mov    rax,QWORD PTR [rdi+0x38]
    1284:	mov    QWORD PTR [rsp+0x10],rax
    1289:	mov    rax,QWORD PTR [rdi+0x40]
    128d:	mov    QWORD PTR [rsp+0x18],rax
    1292:	mov    rax,QWORD PTR [rdi+0x48]
    1296:	mov    QWORD PTR [rsp+0x20],rax
    129b:	mov    rax,QWORD PTR [rdi+0x50]
    129f:	mov    QWORD PTR [rsp+0x28],rax
    12a4:	mov    rdx,rsp
    12a7:	mov    ecx,0x6
    12ac:	mov    rsi,QWORD PTR [rip+0x535d]        # 6610 <ngx_modules+0x490>
    12b3:	mov    rdi,QWORD PTR [rip+0x534e]        # 6608 <ngx_modules+0x488>
    12ba:	call   115b <free@plt+0x5b>
    12bf:	add    rsp,0x38
    12c3:	ret
    12c4:	mov    eax,0x0
    12c9:	test   rdi,rdi
    12cc:	je     12de <free@plt+0x1de>
    12ce:	movabs rdx,0x344e4f4341454243
    12d8:	cmp    QWORD PTR [rdi+0x30],rdx
    12dc:	je     12e1 <free@plt+0x1e1>
    12de:	cdqe
    12e0:	ret
    12e1:	push   rbx
    12e2:	mov    rbx,QWORD PTR [rdi+0x58]
    12e6:	call   121b <free@plt+0x11b>
    12eb:	cmp    rbx,rax
    12ee:	sete   al
    12f1:	movzx  eax,al
    12f4:	cdqe
    12f6:	pop    rbx
    12f7:	ret
    12f8:	push   r15
    12fa:	push   r14
    12fc:	push   r12
    12fe:	push   rbp
    12ff:	push   rbx
    1300:	sub    rsp,0x30
    1304:	mov    rbx,rdi
    1307:	mov    r12,QWORD PTR [rdx+0x8]
    130b:	mov    QWORD PTR [rsp+0x10],r12
    1310:	lea    rax,[rip+0xe82]        # 2199 <free@plt+0x1099>
    1317:	mov    QWORD PTR [rsp+0x18],rax
    131c:	mov    rbp,QWORD PTR [rsi+0x38]
    1320:	mov    QWORD PTR [rsp+0x20],rbp
    1325:	mov    rax,QWORD PTR [rdi+0x30]
    1329:	mov    QWORD PTR [rsp+0x28],rax
    132e:	mov    QWORD PTR [rsp],rax
    1332:	mov    QWORD PTR [rsp+0x8],rbp
    1337:	mov    eax,0x0
    133c:	test   rdi,rdi
    133f:	je     1366 <free@plt+0x266>
    1341:	mov    rdi,rsi
    1344:	call   12c4 <free@plt+0x1c4>
    1349:	mov    rdx,rax
    134c:	mov    eax,0x0
    1351:	test   rdx,rdx
    1354:	je     1366 <free@plt+0x266>
    1356:	movabs rdx,0x34524744454c4c43
    1360:	cmp    QWORD PTR [rbx+0x28],rdx
    1364:	je     1375 <free@plt+0x275>
    1366:	cdqe
    1368:	add    rsp,0x30
    136c:	pop    rbx
    136d:	pop    rbp
    136e:	pop    r12
    1370:	pop    r14
    1372:	pop    r15
    1374:	ret
    1375:	cmp    QWORD PTR [rbx+0x50],0x1
    137a:	jne    1366 <free@plt+0x266>
    137c:	cmp    rbp,QWORD PTR [rbx+0x38]
    1380:	jne    1366 <free@plt+0x266>
    1382:	mov    r14,QWORD PTR [rbx+0x40]
    1386:	mov    rax,QWORD PTR [rip+0x5283]        # 6610 <ngx_modules+0x490>
    138d:	mov    r15,rax
    1390:	mov    rbp,QWORD PTR [rip+0x5271]        # 6608 <ngx_modules+0x488>
    1397:	mov    rdx,rsp
    139a:	mov    ecx,0x2
    139f:	mov    rsi,rax
    13a2:	mov    rdi,rbp
    13a5:	call   115b <free@plt+0x5b>
    13aa:	xor    rax,r12
    13ad:	mov    rdx,rax
    13b0:	mov    eax,0x0
    13b5:	cmp    r14,rdx
    13b8:	jne    1366 <free@plt+0x266>
    13ba:	mov    r12,QWORD PTR [rbx+0x48]
    13be:	lea    rdx,[rsp+0x10]
    13c3:	mov    ecx,0x4
    13c8:	mov    rsi,r15
    13cb:	mov    rdi,rbp
    13ce:	call   115b <free@plt+0x5b>
    13d3:	mov    rdx,rax
    13d6:	mov    eax,0x0
    13db:	cmp    r12,rdx
    13de:	jne    1366 <free@plt+0x266>
    13e0:	mov    rbp,QWORD PTR [rbx+0x58]
    13e4:	mov    rdi,rbx
    13e7:	call   126b <free@plt+0x16b>
    13ec:	cmp    rbp,rax
    13ef:	sete   al
    13f2:	movzx  eax,al
    13f5:	jmp    1366 <free@plt+0x266>
    13fa:	push   r15
    13fc:	push   r14
    13fe:	push   r13
    1400:	push   r12
    1402:	push   rbp
    1403:	push   rbx
    1404:	sub    rsp,0x88
    140b:	mov    rbx,rdi
    140e:	mov    rdi,rdx
    1411:	mov    rax,QWORD PTR [rcx+0x8]
    1415:	mov    r15,rax
    1418:	mov    rbp,QWORD PTR [rbx+0x40]
    141c:	mov    QWORD PTR [rsp+0x60],rbp
    1421:	mov    r13,QWORD PTR [rsi+0x38]
    1425:	mov    QWORD PTR [rsp+0x68],r13
    142a:	mov    r12,QWORD PTR [rdx+0x30]
    142e:	mov    QWORD PTR [rsp+0x70],r12
    1433:	mov    eax,0x0
    1438:	test   rbx,rbx
    143b:	je     1462 <free@plt+0x362>
    143d:	mov    rdx,rcx
    1440:	call   12f8 <free@plt+0x1f8>
    1445:	mov    rdx,rax
    1448:	mov    eax,0x0
    144d:	test   rdx,rdx
    1450:	je     1462 <free@plt+0x362>
    1452:	movabs rdx,0x3454554f524c4c43
    145c:	cmp    QWORD PTR [rbx+0x38],rdx
    1460:	je     1476 <free@plt+0x376>
    1462:	cdqe
    1464:	add    rsp,0x88
    146b:	pop    rbx
    146c:	pop    rbp
    146d:	pop    r12
    146f:	pop    r13
    1471:	pop    r14
    1473:	pop    r15
    1475:	ret
    1476:	cmp    QWORD PTR [rbx+0x70],0x1
    147b:	jne    1462 <free@plt+0x362>
    147d:	mov    rax,QWORD PTR [rbx+0x50]
    1481:	mov    rcx,rax
    1484:	mov    QWORD PTR [rsp],rax
    1488:	mov    eax,0x0
    148d:	cmp    r13,rcx
    1490:	jne    1462 <free@plt+0x362>
    1492:	mov    r13,QWORD PTR [rbx+0x58]
    1496:	cmp    r12,r13
    1499:	jne    1462 <free@plt+0x362>
    149b:	mov    r12,QWORD PTR [rbx+0x68]
    149f:	test   r12,r12
    14a2:	je     1462 <free@plt+0x362>
    14a4:	mov    r14,QWORD PTR [rbx+0x48]
    14a8:	mov    QWORD PTR [rsp+0x8],r14
    14ad:	mov    rsi,QWORD PTR [rip+0x515c]        # 6610 <ngx_modules+0x490>
    14b4:	mov    QWORD PTR [rsp+0x10],rsi
    14b9:	mov    rax,QWORD PTR [rip+0x5148]        # 6608 <ngx_modules+0x488>
    14c0:	mov    QWORD PTR [rsp+0x18],rax
    14c5:	lea    rdx,[rsp+0x60]
    14ca:	mov    ecx,0x3
    14cf:	mov    rdi,rax
    14d2:	call   115b <free@plt+0x5b>
    14d7:	mov    rdx,r15
    14da:	xor    rdx,rax
    14dd:	mov    eax,0x0
    14e2:	cmp    r14,rdx
    14e5:	jne    1462 <free@plt+0x362>
    14eb:	mov    r14,QWORD PTR [rbx+0x78]
    14ef:	movabs rax,0x3454554f524c4c43
    14f9:	mov    QWORD PTR [rsp+0x20],rax
    14fe:	mov    QWORD PTR [rsp+0x28],rbp
    1503:	mov    rax,QWORD PTR [rsp+0x8]
    1508:	mov    QWORD PTR [rsp+0x30],rax
    150d:	mov    rax,QWORD PTR [rsp]
    1511:	mov    QWORD PTR [rsp+0x38],rax
    1516:	mov    QWORD PTR [rsp+0x40],r13
    151b:	mov    rax,QWORD PTR [rbx+0x60]
    151f:	mov    QWORD PTR [rsp+0x48],rax
    1524:	mov    QWORD PTR [rsp+0x50],r12
    1529:	mov    QWORD PTR [rsp+0x58],0x1
    1532:	lea    rdx,[rsp+0x20]
    1537:	mov    ecx,0x8
    153c:	mov    rsi,QWORD PTR [rsp+0x10]
    1541:	mov    rdi,QWORD PTR [rsp+0x18]
    1546:	call   115b <free@plt+0x5b>
    154b:	cmp    r14,rax
    154e:	sete   al
    1551:	movzx  eax,al
    1554:	jmp    1462 <free@plt+0x362>
    1559:	test   rdi,rdi
    155c:	je     1636 <free@plt+0x536>
    1562:	test   rsi,rsi
    1565:	je     1636 <free@plt+0x536>
    156b:	mov    eax,0x0
    1570:	movabs r8,0x344c4145534c4c43
    157a:	cmp    QWORD PTR [rdi+0x28],r8
    157e:	jne    163b <free@plt+0x53b>
    1584:	cmp    QWORD PTR [rdi+0x58],0x1
    1589:	jne    163b <free@plt+0x53b>
    158f:	mov    r8,QWORD PTR [rdi+0x30]
    1593:	cmp    r8,QWORD PTR [rsi+0x68]
    1597:	jne    163b <free@plt+0x53b>
    159d:	mov    r9,QWORD PTR [rdi+0x38]
    15a1:	cmp    r9,QWORD PTR [rsi+0x40]
    15a5:	jne    163b <free@plt+0x53b>
    15ab:	mov    rsi,QWORD PTR [rdi+0x40]
    15af:	cmp    rsi,QWORD PTR [rdx+0x38]
    15b3:	jne    163b <free@plt+0x53b>
    15b9:	mov    rdx,QWORD PTR [rdi+0x48]
    15bd:	cmp    rdx,QWORD PTR [rcx+0x30]
    15c1:	jne    163b <free@plt+0x53b>
    15c3:	push   rbx
    15c4:	sub    rsp,0x40
    15c8:	mov    rbx,QWORD PTR [rdi+0x60]
    15cc:	movabs rax,0x344c4145534c4c43
    15d6:	mov    QWORD PTR [rsp],rax
    15da:	mov    QWORD PTR [rsp+0x8],r8
    15df:	mov    QWORD PTR [rsp+0x10],r9
    15e4:	mov    QWORD PTR [rsp+0x18],rsi
    15e9:	mov    QWORD PTR [rsp+0x20],rdx
    15ee:	mov    rax,QWORD PTR [rdi+0x50]
    15f2:	mov    QWORD PTR [rsp+0x28],rax
    15f7:	mov    QWORD PTR [rsp+0x30],0x1
    1600:	mov    rdx,rsp
    1603:	movabs rdi,0x243f6a8885a308d3
    160d:	xor    rdi,QWORD PTR [rip+0x4ff4]        # 6608 <ngx_modules+0x488>
    1614:	mov    ecx,0x7
    1619:	mov    rsi,QWORD PTR [rip+0x4ff0]        # 6610 <ngx_modules+0x490>
    1620:	call   115b <free@plt+0x5b>
    1625:	cmp    rbx,rax
    1628:	sete   al
    162b:	movzx  eax,al
    162e:	cdqe
    1630:	add    rsp,0x40
    1634:	pop    rbx
    1635:	ret
    1636:	mov    eax,0x0
    163b:	cdqe
    163d:	ret
    163e:	push   r15
    1640:	push   r14
    1642:	push   r13
    1644:	push   r12
    1646:	push   rbp
    1647:	push   rbx
    1648:	sub    rsp,0xe8
    164f:	mov    r14,rsi
    1652:	mov    rax,QWORD PTR [r9+0x8]
    1656:	mov    QWORD PTR [rsp+0x10],rax
    165b:	mov    r13,QWORD PTR [rdi+0x40]
    165f:	mov    QWORD PTR [rsp+0xc0],r13
    1667:	mov    rbp,QWORD PTR [rsi+0x40]
    166b:	mov    QWORD PTR [rsp+0xc8],rbp
    1673:	mov    r12,QWORD PTR [rdx+0x30]
    1677:	mov    QWORD PTR [rsp+0xd0],r12
    167f:	mov    eax,0x0
    1684:	test   rdi,rdi
    1687:	je     16e7 <free@plt+0x5e7>
    1689:	mov    rbx,rdi
    168c:	mov    r15,rdx
    168f:	mov    rsi,rcx
    1692:	mov    rcx,r9
    1695:	mov    QWORD PTR [rsp+0x8],r8
    169a:	mov    rdx,r8
    169d:	mov    QWORD PTR [rsp],rsi
    16a1:	mov    rdi,r14
    16a4:	call   13fa <free@plt+0x2fa>
    16a9:	mov    rdx,rax
    16ac:	mov    eax,0x0
    16b1:	test   rdx,rdx
    16b4:	je     16e7 <free@plt+0x5e7>
    16b6:	mov    rcx,QWORD PTR [rsp+0x8]
    16bb:	mov    rdx,QWORD PTR [rsp]
    16bf:	mov    rsi,r14
    16c2:	mov    rdi,r15
    16c5:	call   1559 <free@plt+0x459>
    16ca:	mov    rdx,rax
    16cd:	mov    eax,0x0
    16d2:	test   rdx,rdx
    16d5:	je     16e7 <free@plt+0x5e7>
    16d7:	movabs rdx,0x34544e4152474c43
    16e1:	cmp    QWORD PTR [rbx+0x38],rdx
    16e5:	je     16fb <free@plt+0x5fb>
    16e7:	cdqe
    16e9:	add    rsp,0xe8
    16f0:	pop    rbx
    16f1:	pop    rbp
    16f2:	pop    r12
    16f4:	pop    r13
    16f6:	pop    r14
    16f8:	pop    r15
    16fa:	ret
    16fb:	cmp    QWORD PTR [rbx+0x88],0x1
    1703:	jne    16e7 <free@plt+0x5e7>
    1705:	mov    rdi,QWORD PTR [rbx+0x50]
    1709:	mov    QWORD PTR [rsp+0x18],rdi
    170e:	mov    rax,QWORD PTR [rsp]
    1712:	mov    rdx,QWORD PTR [rax+0x38]
    1716:	mov    QWORD PTR [rsp],rdx
    171a:	mov    eax,0x0
    171f:	cmp    rdi,rdx
    1722:	jne    16e7 <free@plt+0x5e7>
    1724:	mov    rdi,QWORD PTR [rbx+0x58]
    1728:	mov    QWORD PTR [rsp+0x20],rdi
    172d:	mov    rax,QWORD PTR [rsp+0x8]
    1732:	mov    rdx,QWORD PTR [rax+0x30]
    1736:	mov    QWORD PTR [rsp+0x8],rdx
    173b:	mov    eax,0x0
    1740:	cmp    rdi,rdx
    1743:	jne    16e7 <free@plt+0x5e7>
    1745:	mov    rax,QWORD PTR [rbx+0x60]
    1749:	mov    rdi,rax
    174c:	mov    QWORD PTR [rsp+0x28],rax
    1751:	mov    eax,0x0
    1756:	cmp    rbp,rdi
    1759:	jne    16e7 <free@plt+0x5e7>
    175b:	mov    rax,QWORD PTR [rbx+0x68]
    175f:	mov    rdi,rax
    1762:	mov    QWORD PTR [rsp+0x50],rax
    1767:	mov    eax,0x0
    176c:	cmp    r12,rdi
    176f:	jne    16e7 <free@plt+0x5e7>
    1775:	mov    rax,QWORD PTR [rbx+0x78]
    1779:	mov    rdi,rax
    177c:	mov    QWORD PTR [rsp+0x58],rax
    1781:	mov    eax,0x0
    1786:	test   rdi,rdi
    1789:	je     16e7 <free@plt+0x5e7>
    178f:	mov    rax,QWORD PTR [rbx+0x48]
    1793:	mov    QWORD PTR [rsp+0x30],rax
    1798:	mov    rsi,QWORD PTR [rip+0x4e71]        # 6610 <ngx_modules+0x490>
    179f:	mov    QWORD PTR [rsp+0x38],rsi
    17a4:	mov    rdx,QWORD PTR [rip+0x4e5d]        # 6608 <ngx_modules+0x488>
    17ab:	mov    rdi,rdx
    17ae:	mov    QWORD PTR [rsp+0x40],rdx
    17b3:	lea    rdx,[rsp+0xc0]
    17bb:	mov    ecx,0x3
    17c0:	call   115b <free@plt+0x5b>
    17c5:	mov    rdx,QWORD PTR [rsp+0x10]
    17ca:	xor    rdx,rax
    17cd:	mov    eax,0x0
    17d2:	cmp    QWORD PTR [rsp+0x30],rdx
    17d7:	jne    16e7 <free@plt+0x5e7>
    17dd:	mov    rax,QWORD PTR [rbx+0x80]
    17e4:	mov    QWORD PTR [rsp+0x48],rax
    17e9:	lea    rdx,[rip+0x9a9]        # 2199 <free@plt+0x1099>
    17f0:	mov    QWORD PTR [rsp+0x60],rdx
    17f5:	mov    rdx,QWORD PTR [rsp+0x10]
    17fa:	mov    QWORD PTR [rsp+0x68],rdx
    17ff:	mov    rdx,QWORD PTR [rsp]
    1803:	mov    QWORD PTR [rsp+0x70],rdx
    1808:	mov    rdx,QWORD PTR [rsp+0x8]
    180d:	mov    QWORD PTR [rsp+0x78],rdx
    1812:	mov    QWORD PTR [rsp+0x80],rbp
    181a:	mov    QWORD PTR [rsp+0x88],r12
    1822:	mov    rax,QWORD PTR [r14+0x60]
    1826:	mov    QWORD PTR [rsp+0x90],rax
    182e:	mov    rax,QWORD PTR [r15+0x50]
    1832:	mov    QWORD PTR [rsp+0x98],rax
    183a:	lea    rdx,[rsp+0x60]
    183f:	mov    rdi,QWORD PTR [rsp+0x38]
    1844:	mov    rcx,QWORD PTR [rsp+0x40]
    1849:	lea    rsi,[rdi+rcx*1]
    184d:	xor    rdi,rcx
    1850:	mov    ecx,0x8
    1855:	call   115b <free@plt+0x5b>
    185a:	mov    rdx,rax
    185d:	mov    eax,0x0
    1862:	cmp    QWORD PTR [rsp+0x48],rdx
    1867:	jne    16e7 <free@plt+0x5e7>
    186d:	mov    rbp,QWORD PTR [rbx+0x90]
    1874:	movabs rax,0x34544e4152474c43
    187e:	mov    QWORD PTR [rsp+0x60],rax
    1883:	mov    QWORD PTR [rsp+0x68],r13
    1888:	mov    rax,QWORD PTR [rsp+0x30]
    188d:	mov    QWORD PTR [rsp+0x70],rax
    1892:	mov    rax,QWORD PTR [rsp+0x18]
    1897:	mov    QWORD PTR [rsp+0x78],rax
    189c:	mov    rax,QWORD PTR [rsp+0x20]
    18a1:	mov    QWORD PTR [rsp+0x80],rax
    18a9:	mov    rax,QWORD PTR [rsp+0x28]
    18ae:	mov    QWORD PTR [rsp+0x88],rax
    18b6:	mov    rax,QWORD PTR [rsp+0x50]
    18bb:	mov    QWORD PTR [rsp+0x90],rax
    18c3:	mov    rax,QWORD PTR [rbx+0x70]
    18c7:	mov    QWORD PTR [rsp+0x98],rax
    18cf:	mov    rax,QWORD PTR [rsp+0x58]
    18d4:	mov    QWORD PTR [rsp+0xa0],rax
    18dc:	mov    rax,QWORD PTR [rsp+0x48]
    18e1:	mov    QWORD PTR [rsp+0xa8],rax
    18e9:	mov    QWORD PTR [rsp+0xb0],0x1
    18f5:	lea    rdx,[rsp+0x60]
    18fa:	movabs rax,0x13198a2e03707344
    1904:	mov    rdi,QWORD PTR [rsp+0x40]
    1909:	xor    rdi,rax
    190c:	mov    ecx,0xb
    1911:	mov    rsi,QWORD PTR [rsp+0x38]
    1916:	call   115b <free@plt+0x5b>
    191b:	cmp    rbp,rax
    191e:	sete   al
    1921:	movzx  eax,al
    1924:	jmp    16e7 <free@plt+0x5e7>
    1929:	test   rdi,rdi
    192c:	je     1a3c <free@plt+0x93c>
    1932:	test   rsi,rsi
    1935:	je     1a3c <free@plt+0x93c>
    193b:	mov    eax,0x0
    1940:	movabs r10,0x34524843554f5643
    194a:	cmp    QWORD PTR [rdi+0x28],r10
    194e:	jne    1a41 <free@plt+0x941>
    1954:	cmp    QWORD PTR [rdi+0x68],0x1
    1959:	jne    1a41 <free@plt+0x941>
    195f:	mov    r10,QWORD PTR [rdi+0x30]
    1963:	cmp    r10,QWORD PTR [rsi+0x78]
    1967:	jne    1a41 <free@plt+0x941>
    196d:	mov    r11,QWORD PTR [rdi+0x38]
    1971:	cmp    r11,QWORD PTR [rsi+0x40]
    1975:	jne    1a41 <free@plt+0x941>
    197b:	mov    rsi,QWORD PTR [rdi+0x40]
    197f:	cmp    rsi,QWORD PTR [rdx+0x40]
    1983:	jne    1a41 <free@plt+0x941>
    1989:	mov    rdx,QWORD PTR [rdi+0x48]
    198d:	cmp    rdx,QWORD PTR [rcx+0x30]
    1991:	jne    1a41 <free@plt+0x941>
    1997:	push   r14
    1999:	push   rbx
    199a:	sub    rsp,0x58
    199e:	mov    rax,QWORD PTR [rdi+0x50]
    19a2:	mov    rcx,rax
    19a5:	mov    r14,rax
    19a8:	mov    eax,0x0
    19ad:	cmp    rcx,QWORD PTR [r8+0x38]
    19b1:	je     19bd <free@plt+0x8bd>
    19b3:	cdqe
    19b5:	add    rsp,0x58
    19b9:	pop    rbx
    19ba:	pop    r14
    19bc:	ret
    19bd:	mov    rcx,QWORD PTR [rdi+0x58]
    19c1:	cmp    rcx,QWORD PTR [r9+0x30]
    19c5:	jne    19b3 <free@plt+0x8b3>
    19c7:	mov    rbx,QWORD PTR [rdi+0x70]
    19cb:	movabs rax,0x34524843554f5643
    19d5:	mov    QWORD PTR [rsp],rax
    19d9:	mov    QWORD PTR [rsp+0x8],r10
    19de:	mov    QWORD PTR [rsp+0x10],r11
    19e3:	mov    QWORD PTR [rsp+0x18],rsi
    19e8:	mov    QWORD PTR [rsp+0x20],rdx
    19ed:	mov    QWORD PTR [rsp+0x28],r14
    19f2:	mov    QWORD PTR [rsp+0x30],rcx
    19f7:	mov    rax,QWORD PTR [rdi+0x60]
    19fb:	mov    QWORD PTR [rsp+0x38],rax
    1a00:	mov    QWORD PTR [rsp+0x40],0x1
    1a09:	mov    rdx,rsp
    1a0c:	movabs rdi,0x3c6ef372fe94f82b
    1a16:	xor    rdi,QWORD PTR [rip+0x4beb]        # 6608 <ngx_modules+0x488>
    1a1d:	mov    ecx,0x9
    1a22:	mov    rsi,QWORD PTR [rip+0x4be7]        # 6610 <ngx_modules+0x490>
    1a29:	call   115b <free@plt+0x5b>
    1a2e:	cmp    rbx,rax
    1a31:	sete   al
    1a34:	movzx  eax,al
    1a37:	jmp    19b3 <free@plt+0x8b3>
    1a3c:	mov    eax,0x0
    1a41:	cdqe
    1a43:	ret
    1a44:	mov    eax,0x0
    1a49:	cmp    rcx,rdi
    1a4c:	jne    1a84 <free@plt+0x984>
    1a4e:	test   rcx,rcx
    1a51:	je     1a79 <free@plt+0x979>
    1a53:	xchg   ax,ax
    1a55:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1a60:	movzx  edi,BYTE PTR [rdx+rax*1]
    1a64:	cmp    BYTE PTR [rsi+rax*1],dil
    1a68:	jne    1a7f <free@plt+0x97f>
    1a6a:	add    rax,0x1
    1a6e:	cmp    rcx,rax
    1a71:	jne    1a60 <free@plt+0x960>
    1a73:	mov    eax,0x1
    1a78:	ret
    1a79:	mov    eax,0x1
    1a7e:	ret
    1a7f:	mov    eax,0x0
    1a84:	ret
    1a85:	mov    r8,rdi
    1a88:	mov    ecx,0x3c
    1a8d:	lea    r9,[rip+0x268c]        # 4120 <free@plt+0x3020>
    1a94:	nop
    1a95:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1aa0:	mov    rdx,rsi
    1aa3:	shr    rdx,cl
    1aa6:	and    edx,0xf
    1aa9:	movzx  edx,BYTE PTR [r9+rdx*1]
    1aae:	mov    BYTE PTR [r8],dl
    1ab1:	sub    ecx,0x4
    1ab4:	add    r8,0x1
    1ab8:	cmp    ecx,0xfffffffc
    1abb:	jne    1aa0 <free@plt+0x9a0>
    1abd:	lea    rax,[rdi+0x10]
    1ac1:	ret
    1ac2:	mov    eax,0x193
    1ac7:	ret
    1ac8:	mov    rax,QWORD PTR [rdi+0x38]
    1acc:	mov    rdx,QWORD PTR [rip+0x4525]        # 5ff8 <free@plt+0x4ef8>
    1ad3:	mov    rdx,QWORD PTR [rdx]
    1ad6:	mov    rax,QWORD PTR [rax+0x10]
    1ada:	mov    rax,QWORD PTR [rax+rdx*8]
    1ade:	lea    rcx,[rip+0x6b4]        # 2199 <free@plt+0x1099>
    1ae5:	mov    QWORD PTR [rax+0x68],rcx
    1ae9:	mov    eax,0x0
    1aee:	ret
    1aef:	mov    rdx,QWORD PTR [rdi+0x8]
    1af3:	mov    rax,QWORD PTR [rip+0x46e6]        # 61e0 <ngx_modules+0x60>
    1afa:	cmp    rdx,rax
    1afd:	je     1b45 <free@plt+0xa45>
    1aff:	push   rbx
    1b00:	mov    rbx,rdi
    1b03:	mov    ecx,0x193
    1b08:	test   rax,rax
    1b0b:	je     1b12 <free@plt+0xa12>
    1b0d:	mov    rax,rcx
    1b10:	pop    rbx
    1b11:	ret
    1b12:	mov    rdi,QWORD PTR [rdx+0x58]
    1b16:	mov    esi,0x0
    1b1b:	call   10a0 <ngx_pool_cleanup_add@plt>
    1b20:	test   rax,rax
    1b23:	je     1b4e <free@plt+0xa4e>
    1b25:	lea    rsi,[rip+0x29]        # 1b55 <free@plt+0xa55>
    1b2c:	mov    QWORD PTR [rax],rsi
    1b2f:	mov    rdx,QWORD PTR [rbx+0x8]
    1b33:	mov    QWORD PTR [rax+0x8],rdx
    1b37:	mov    QWORD PTR [rip+0x46a2],rdx        # 61e0 <ngx_modules+0x60>
    1b3e:	mov    ecx,0x0
    1b43:	jmp    1b0d <free@plt+0xa0d>
    1b45:	mov    ecx,0x0
    1b4a:	mov    rax,rcx
    1b4d:	ret
    1b4e:	mov    ecx,0x1f4
    1b53:	jmp    1b0d <free@plt+0xa0d>
    1b55:	cmp    QWORD PTR [rip+0x4684],rdi        # 61e0 <ngx_modules+0x60>
    1b5c:	je     1b5f <free@plt+0xa5f>
    1b5e:	ret
    1b5f:	sub    rsp,0x8
    1b63:	mov    QWORD PTR [rip+0x4672],0x0        # 61e0 <ngx_modules+0x60>
    1b6e:	mov    edi,DWORD PTR [rip+0x448c]        # 6000 <free@plt+0x4f00>
    1b74:	test   edi,edi
    1b76:	jns    1b8c <free@plt+0xa8c>
    1b78:	mov    DWORD PTR [rip+0x447e],0xffffffff        # 6000 <free@plt+0x4f00>
    1b82:	mov    edi,0x0
    1b87:	call   10c0 <_exit@plt>
    1b8c:	call   10e0 <close@plt>
    1b91:	jmp    1b78 <free@plt+0xa78>
    1b93:	push   rbp
    1b94:	push   rbx
    1b95:	sub    rsp,0x8
    1b99:	mov    rbp,rdi
    1b9c:	mov    rdi,rsi
    1b9f:	mov    rax,QWORD PTR [rbp+0x8]
    1ba3:	mov    rsi,QWORD PTR [rax+0x50]
    1ba7:	call   1060 <ngx_alloc@plt>
    1bac:	mov    rbx,rax
    1baf:	test   rax,rax
    1bb2:	je     1bd9 <free@plt+0xad9>
    1bb4:	mov    rdi,QWORD PTR [rbp+0x58]
    1bb8:	mov    esi,0x0
    1bbd:	call   10a0 <ngx_pool_cleanup_add@plt>
    1bc2:	mov    rbp,rax
    1bc5:	test   rax,rax
    1bc8:	je     1be3 <free@plt+0xae3>
    1bca:	lea    rax,[rip+0x1f]        # 1bf0 <free@plt+0xaf0>
    1bd1:	mov    QWORD PTR [rbp+0x0],rax
    1bd5:	mov    QWORD PTR [rbp+0x8],rbx
    1bd9:	mov    rax,rbx
    1bdc:	add    rsp,0x8
    1be0:	pop    rbx
    1be1:	pop    rbp
    1be2:	ret
    1be3:	mov    rdi,rbx
    1be6:	call   1100 <free@plt>
    1beb:	mov    rbx,rbp
    1bee:	jmp    1bd9 <free@plt+0xad9>
    1bf0:	test   rdi,rdi
    1bf3:	je     1c03 <free@plt+0xb03>
    1bf5:	sub    rsp,0x8
    1bf9:	call   1100 <free@plt>
    1bfe:	add    rsp,0x8
    1c02:	ret
    1c03:	ret
    1c04:	lea    rax,[rcx+rcx*1]
    1c08:	cmp    rax,rdi
    1c0b:	jne    1c5c <free@plt+0xb5c>
    1c0d:	push   r13
    1c0f:	push   r12
    1c11:	push   rbp
    1c12:	push   rbx
    1c13:	sub    rsp,0x8
    1c17:	mov    r12,rsi
    1c1a:	mov    r13,rdx
    1c1d:	mov    rbp,rcx
    1c20:	test   rcx,rcx
    1c23:	je     1c64 <free@plt+0xb64>
    1c25:	mov    ebx,0x0
    1c2a:	lea    rdi,[r12+rbx*2]
    1c2e:	mov    esi,0x2
    1c33:	call   1080 <ngx_hextoi@plt>
    1c38:	cmp    rax,0xffffffffffffffff
    1c3c:	je     1c51 <free@plt+0xb51>
    1c3e:	mov    BYTE PTR [r13+rbx*1+0x0],al
    1c43:	add    rbx,0x1
    1c47:	cmp    rbp,rbx
    1c4a:	jne    1c2a <free@plt+0xb2a>
    1c4c:	mov    eax,0x0
    1c51:	add    rsp,0x8
    1c55:	pop    rbx
    1c56:	pop    rbp
    1c57:	pop    r12
    1c59:	pop    r13
    1c5b:	ret
    1c5c:	mov    rax,0xffffffffffffffff
    1c63:	ret
    1c64:	mov    eax,0x0
    1c69:	jmp    1c51 <free@plt+0xb51>
    1c6b:	push   r12
    1c6d:	push   rbp
    1c6e:	push   rbx
    1c6f:	mov    r12d,edi
    1c72:	mov    rbp,rsi
    1c75:	mov    rbx,rdx
    1c78:	test   rdx,rdx
    1c7b:	je     1c9f <free@plt+0xb9f>
    1c7d:	mov    rdx,rbx
    1c80:	mov    rsi,rbp
    1c83:	mov    edi,r12d
    1c86:	call   1070 <write@plt>
    1c8b:	test   rax,rax
    1c8e:	jle    1ca6 <free@plt+0xba6>
    1c90:	add    rbp,rax
    1c93:	sub    rbx,rax
    1c96:	jne    1c7d <free@plt+0xb7d>
    1c98:	mov    eax,0x1
    1c9d:	jmp    1cab <free@plt+0xbab>
    1c9f:	mov    eax,0x1
    1ca4:	jmp    1cab <free@plt+0xbab>
    1ca6:	mov    eax,0x0
    1cab:	pop    rbx
    1cac:	pop    rbp
    1cad:	pop    r12
    1caf:	ret
    1cb0:	push   r15
    1cb2:	push   r14
    1cb4:	push   rbp
    1cb5:	push   rbx
    1cb6:	sub    rsp,0x878
    1cbd:	lea    rax,[rdi-0x1]
    1cc1:	cmp    rax,0xfff
    1cc7:	ja     1ede <free@plt+0xdde>
    1ccd:	mov    r14,rdx
    1cd0:	test   dil,0x1
    1cd4:	jne    1ee5 <free@plt+0xde5>
    1cda:	mov    rbp,rdi
    1cdd:	shr    rbp,1
    1ce0:	lea    rdx,[rsp+0x70]
    1ce5:	mov    rcx,rbp
    1ce8:	call   1c04 <free@plt+0xb04>
    1ced:	mov    rbx,rax
    1cf0:	test   rax,rax
    1cf3:	jne    1efb <free@plt+0xdfb>
    1cf9:	cmp    DWORD PTR [rip+0x4300],0x0        # 6000 <free@plt+0x4f00>
    1d00:	js     1da8 <free@plt+0xca8>
    1d06:	mov    rax,QWORD PTR [rip+0x48f3]        # 6600 <ngx_modules+0x480>
    1d0d:	mov    r15,rax
    1d10:	cmp    rax,0x8
    1d14:	ja     1d3d <free@plt+0xc3d>
    1d16:	movzx  edi,bp
    1d19:	call   10b0 <htons@plt>
    1d1e:	mov    WORD PTR [rsp],ax
    1d22:	mov    rsi,rsp
    1d25:	mov    edx,0x2
    1d2a:	mov    edi,DWORD PTR [rip+0x42d0]        # 6000 <free@plt+0x4f00>
    1d30:	call   1c6b <free@plt+0xb6b>
    1d35:	test   eax,eax
    1d37:	je     1e62 <free@plt+0xd62>
    1d3d:	lea    rsi,[rsp+0x70]
    1d42:	mov    rdx,rbp
    1d45:	mov    edi,DWORD PTR [rip+0x42b5]        # 6000 <free@plt+0x4f00>
    1d4b:	call   1c6b <free@plt+0xb6b>
    1d50:	test   eax,eax
    1d52:	je     1e62 <free@plt+0xd62>
    1d58:	mov    edx,0x400
    1d5d:	lea    rsi,[rip+0x449c]        # 6200 <ngx_modules+0x80>
    1d64:	mov    edi,DWORD PTR [rip+0x4296]        # 6000 <free@plt+0x4f00>
    1d6a:	call   1090 <read@plt>
    1d6f:	test   rax,rax
    1d72:	jle    1e62 <free@plt+0xd62>
    1d78:	cmp    r15,0x8
    1d7c:	ja     1d95 <free@plt+0xc95>
    1d7e:	cmp    rbp,0xb
    1d82:	jne    1d95 <free@plt+0xc95>
    1d84:	cmp    BYTE PTR [rsp+0x70],0x43
    1d89:	jne    1d95 <free@plt+0xc95>
    1d8b:	cmp    rax,0x3
    1d8f:	jg     1e87 <free@plt+0xd87>
    1d95:	lea    rdx,[rip+0x4464]        # 6200 <ngx_modules+0x80>
    1d9c:	mov    QWORD PTR [r14+0x8],rdx
    1da0:	mov    QWORD PTR [r14],rax
    1da3:	jmp    1eea <free@plt+0xdea>
    1da8:	mov    edx,0x0
    1dad:	mov    esi,0x1
    1db2:	mov    edi,0x1
    1db7:	call   1050 <socket@plt>
    1dbc:	mov    r8d,eax
    1dbf:	mov    DWORD PTR [rip+0x423b],eax        # 6000 <free@plt+0x4f00>
    1dc5:	test   eax,eax
    1dc7:	js     1e7e <free@plt+0xd7e>
    1dcd:	mov    QWORD PTR [rsp+0x66],0x0
    1dd6:	lea    rdi,[rsp+0x8]
    1ddb:	mov    ecx,0xc
    1de0:	mov    eax,0x0
    1de5:	rep stos QWORD PTR es:[rdi],rax
    1de8:	mov    WORD PTR [rsp],0x1
    1dee:	lea    rax,[rsp+0x1d]
    1df3:	lea    rdx,[rip+0x2306]        # 4100 <free@plt+0x3000>
    1dfa:	cmp    rdx,rax
    1dfd:	jae    1e10 <free@plt+0xd10>
    1dff:	lea    rdx,[rsp+0x2]
    1e04:	lea    rax,[rip+0x22f5]        # 4100 <free@plt+0x3000>
    1e0b:	cmp    rdx,rax
    1e0e:	jb     1e85 <free@plt+0xd85>
    1e10:	lea    rdx,[rsp+0x2]
    1e15:	lea    rax,[rip+0x22ff]        # 411b <free@plt+0x301b>
    1e1c:	cmp    rdx,rax
    1e1f:	jae    1e30 <free@plt+0xd30>
    1e21:	mov    rax,rdx
    1e24:	lea    rdx,[rip+0x22d5]        # 4100 <free@plt+0x3000>
    1e2b:	cmp    rdx,rax
    1e2e:	jb     1e85 <free@plt+0xd85>
    1e30:	movdqa xmm0,XMMWORD PTR [rip+0x22c8]        # 4100 <free@plt+0x3000>
    1e38:	movups XMMWORD PTR [rsp+0x2],xmm0
    1e3d:	movdqu xmm1,XMMWORD PTR [rip+0x22c6]        # 410b <free@plt+0x300b>
    1e45:	movups XMMWORD PTR [rsp+0xd],xmm1
    1e4a:	mov    rsi,rsp
    1e4d:	mov    edx,0x6e
    1e52:	mov    edi,r8d
    1e55:	call   1030 <connect@plt>
    1e5a:	test   eax,eax
    1e5c:	je     1d06 <free@plt+0xc06>
    1e62:	mov    edi,DWORD PTR [rip+0x4198]        # 6000 <free@plt+0x4f00>
    1e68:	call   10e0 <close@plt>
    1e6d:	mov    DWORD PTR [rip+0x4189],0xffffffff        # 6000 <free@plt+0x4f00>
    1e77:	mov    ebx,0x1f4
    1e7c:	jmp    1eea <free@plt+0xdea>
    1e7e:	mov    ebx,0x1f4
    1e83:	jmp    1eea <free@plt+0xdea>
    1e85:	ud2
    1e87:	lea    rdx,[rsp+0x4]
    1e8c:	lea    rcx,[rip+0x436d]        # 6200 <ngx_modules+0x80>
    1e93:	cmp    rcx,rdx
    1e96:	jae    1ea4 <free@plt+0xda4>
    1e98:	lea    rdx,[rip+0x4361]        # 6200 <ngx_modules+0x80>
    1e9f:	cmp    rsp,rdx
    1ea2:	jb     1edc <free@plt+0xddc>
    1ea4:	lea    rdx,[rip+0x4359]        # 6204 <ngx_modules+0x84>
    1eab:	cmp    rsp,rdx
    1eae:	jae    1ebc <free@plt+0xdbc>
    1eb0:	lea    rcx,[rip+0x4349]        # 6200 <ngx_modules+0x80>
    1eb7:	cmp    rcx,rsp
    1eba:	jb     1edc <free@plt+0xddc>
    1ebc:	cmp    DWORD PTR [rip+0x433a],0x34524c43        # 6200 <ngx_modules+0x80>
    1ec6:	jne    1d95 <free@plt+0xc95>
    1ecc:	mov    QWORD PTR [rip+0x4729],0x9        # 6600 <ngx_modules+0x480>
    1ed7:	jmp    1d95 <free@plt+0xc95>
    1edc:	ud2
    1ede:	mov    ebx,0x190
    1ee3:	jmp    1eea <free@plt+0xdea>
    1ee5:	mov    ebx,0x190
    1eea:	mov    rax,rbx
    1eed:	add    rsp,0x878
    1ef4:	pop    rbx
    1ef5:	pop    rbp
    1ef6:	pop    r14
    1ef8:	pop    r15
    1efa:	ret
    1efb:	mov    ebx,0x190
    1f00:	jmp    1eea <free@plt+0xdea>
    1f02:	push   r14
    1f04:	push   r12
    1f06:	push   rbp
    1f07:	push   rbx
    1f08:	mov    WORD PTR [rsp-0x68],0x20
    1f0f:	mov    BYTE PTR [rsp-0x66],0x0
    1f14:	mov    BYTE PTR [rsp-0x65],0x0
    1f19:	mov    DWORD PTR [rsp-0x64],0x4
    1f21:	mov    WORD PTR [rsp-0x60],0x15
    1f28:	mov    BYTE PTR [rsp-0x5e],0x1
    1f2d:	mov    BYTE PTR [rsp-0x5d],0x0
    1f32:	mov    DWORD PTR [rsp-0x5c],0xc000003e
    1f3a:	mov    WORD PTR [rsp-0x58],0x6
    1f41:	mov    BYTE PTR [rsp-0x56],0x0
    1f46:	mov    BYTE PTR [rsp-0x55],0x0
    1f4b:	mov    DWORD PTR [rsp-0x54],0x80000000
    1f53:	mov    WORD PTR [rsp-0x50],0x20
    1f5a:	mov    BYTE PTR [rsp-0x4e],0x0
    1f5f:	mov    BYTE PTR [rsp-0x4d],0x0
    1f64:	mov    DWORD PTR [rsp-0x4c],0x0
    1f6c:	mov    WORD PTR [rsp-0x48],0x45
    1f73:	mov    BYTE PTR [rsp-0x46],0x0
    1f78:	mov    BYTE PTR [rsp-0x45],0x1
    1f7d:	mov    DWORD PTR [rsp-0x44],0x40000000
    1f85:	mov    WORD PTR [rsp-0x40],0x6
    1f8c:	mov    BYTE PTR [rsp-0x3e],0x0
    1f91:	mov    BYTE PTR [rsp-0x3d],0x0
    1f96:	mov    DWORD PTR [rsp-0x3c],0x80000000
    1f9e:	mov    WORD PTR [rsp-0x38],0x15
    1fa5:	mov    BYTE PTR [rsp-0x36],0x0
    1faa:	mov    BYTE PTR [rsp-0x35],0x1
    1faf:	mov    DWORD PTR [rsp-0x34],0x3b
    1fb7:	mov    WORD PTR [rsp-0x30],0x6
    1fbe:	mov    BYTE PTR [rsp-0x2e],0x0
    1fc3:	mov    BYTE PTR [rsp-0x2d],0x0
    1fc8:	mov    DWORD PTR [rsp-0x2c],0x50001
    1fd0:	mov    WORD PTR [rsp-0x28],0x15
    1fd7:	mov    BYTE PTR [rsp-0x26],0x0
    1fdc:	mov    BYTE PTR [rsp-0x25],0x1
    1fe1:	mov    DWORD PTR [rsp-0x24],0x142
    1fe9:	mov    WORD PTR [rsp-0x20],0x6
    1ff0:	mov    BYTE PTR [rsp-0x1e],0x0
    1ff5:	mov    BYTE PTR [rsp-0x1d],0x0
    1ffa:	mov    DWORD PTR [rsp-0x1c],0x50001
    2002:	mov    WORD PTR [rsp-0x18],0x6
    2009:	mov    BYTE PTR [rsp-0x16],0x0
    200e:	mov    BYTE PTR [rsp-0x15],0x0
    2013:	mov    DWORD PTR [rsp-0x14],0x7fff0000
    201b:	mov    QWORD PTR [rsp-0x78],0x0
    2024:	mov    WORD PTR [rsp-0x78],0xb
    202b:	lea    rax,[rsp-0x68]
    2030:	mov    QWORD PTR [rsp-0x70],rax
    2035:	mov    r10d,0x0
    203b:	mov    r8d,0x0
    2041:	mov    r9d,0x0
    2047:	mov    eax,0x9d
    204c:	mov    edi,0x26
    2051:	mov    esi,0x1
    2056:	mov    edx,0x0
    205b:	syscall
    205d:	test   rax,rax
    2060:	jne    216c <free@plt+0x106c>
    2066:	lea    rdx,[rsp-0x78]
    206b:	mov    eax,0x13d
    2070:	mov    edi,0x1
    2075:	mov    esi,0x0
    207a:	syscall
    207c:	mov    r14,rax
    207f:	test   rax,rax
    2082:	jne    2175 <free@plt+0x1075>
    2088:	lea    rdi,[rip+0x4581]        # 6610 <ngx_modules+0x490>
    208f:	mov    eax,0x13e
    2094:	mov    esi,0x8
    2099:	mov    edx,0x0
    209e:	syscall
    20a0:	cmp    rax,0x8
    20a4:	jne    217e <free@plt+0x107e>
    20aa:	lea    rdi,[rip+0x4557]        # 6608 <ngx_modules+0x488>
    20b1:	mov    eax,0x13e
    20b6:	syscall
    20b8:	cmp    rax,0x8
    20bc:	jne    2187 <free@plt+0x1087>
    20c2:	cmp    QWORD PTR [rip+0x4546],0x0        # 6610 <ngx_modules+0x490>
    20ca:	jne    20e7 <free@plt+0xfe7>
    20cc:	lea    rax,[rip+0x453d]        # 6610 <ngx_modules+0x490>
    20d3:	movabs rdx,0x9e3779b97f4a7c15
    20dd:	xor    rax,rdx
    20e0:	mov    QWORD PTR [rip+0x4529],rax        # 6610 <ngx_modules+0x490>
    20e7:	cmp    QWORD PTR [rip+0x4519],0x0        # 6608 <ngx_modules+0x488>
    20ef:	jne    210c <free@plt+0x100c>
    20f1:	lea    rax,[rip+0x4510]        # 6608 <ngx_modules+0x488>
    20f8:	movabs rdx,0x61c8864680b583ea
    2102:	xor    rax,rdx
    2105:	mov    QWORD PTR [rip+0x44fc],rax        # 6608 <ngx_modules+0x488>
    210c:	mov    rax,QWORD PTR [rip+0x44f5]        # 6608 <ngx_modules+0x488>
    2113:	xor    eax,DWORD PTR [rip+0x44f7]        # 6610 <ngx_modules+0x490>
    2119:	and    eax,0x7
    211c:	lea    r12,[rax+0x1]
    2120:	mov    ebx,0x0
    2125:	lea    rsi,[rip+0x200c]        # 4138 <free@plt+0x3038>
    212c:	mov    ebp,0x101
    2131:	mov    rdi,0xffffffffffffff9c
    2138:	mov    r10d,0x0
    213e:	mov    r8d,0x0
    2144:	mov    r9d,0x0
    214a:	mov    edx,0x0
    214f:	mov    rax,rbp
    2152:	syscall
    2154:	test   rax,rax
    2157:	js     2190 <free@plt+0x1090>
    2159:	add    rbx,0x1
    215d:	cmp    r12,rbx
    2160:	jne    2138 <free@plt+0x1038>
    2162:	mov    rax,r14
    2165:	pop    rbx
    2166:	pop    rbp
    2167:	pop    r12
    2169:	pop    r14
    216b:	ret
    216c:	mov    r14,0xffffffffffffffff
    2173:	jmp    2162 <free@plt+0x1062>
    2175:	mov    r14,0xffffffffffffffff
    217c:	jmp    2162 <free@plt+0x1062>
    217e:	mov    r14,0xffffffffffffffff
    2185:	jmp    2162 <free@plt+0x1062>
    2187:	mov    r14,0xffffffffffffffff
    218e:	jmp    2162 <free@plt+0x1062>
    2190:	mov    r14,0xffffffffffffffff
    2197:	jmp    2162 <free@plt+0x1062>
    2199:	test   BYTE PTR [rdi+0x368],0x2
    21a0:	je     3015 <free@plt+0x1f15>
    21a6:	push   r15
    21a8:	push   r14
    21aa:	push   r12
    21ac:	push   rbp
    21ad:	push   rbx
    21ae:	sub    rsp,0x70
    21b2:	mov    rbx,rdi
    21b5:	mov    QWORD PTR [rsp+0x60],0x0
    21be:	mov    QWORD PTR [rsp+0x68],0x0
    21c7:	mov    QWORD PTR [rsp+0x50],0x0
    21d0:	mov    QWORD PTR [rsp+0x58],0x0
    21d9:	lea    rcx,[rsp+0x60]
    21de:	mov    edx,0x2
    21e3:	lea    rsi,[rip+0x1e16]        # 4000 <free@plt+0x2f00>
    21ea:	call   1010 <ngx_http_arg@plt>
    21ef:	lea    rcx,[rsp+0x50]
    21f4:	mov    edx,0x4
    21f9:	lea    rsi,[rip+0x1e03]        # 4003 <free@plt+0x2f03>
    2200:	mov    rdi,rbx
    2203:	call   1010 <ngx_http_arg@plt>
    2208:	mov    QWORD PTR [rsp+0x40],0xd
    2211:	lea    rax,[rip+0x1df0]        # 4008 <free@plt+0x2f08>
    2218:	mov    QWORD PTR [rsp+0x48],rax
    221d:	mov    ecx,0x6
    2222:	lea    rdx,[rip+0x1ded]        # 4016 <free@plt+0x2f16>
    2229:	mov    rdi,QWORD PTR [rsp+0x60]
    222e:	mov    rsi,QWORD PTR [rsp+0x68]
    2233:	call   1a44 <free@plt+0x944>
    2238:	test   rax,rax
    223b:	je     2386 <free@plt+0x1286>
    2241:	mov    eax,0x190
    2246:	cmp    QWORD PTR [rip+0x43b2],0x0        # 6600 <ngx_modules+0x480>
    224e:	jne    225b <free@plt+0x115b>
    2250:	cmp    QWORD PTR [rsp+0x50],0x300
    2259:	je     2268 <free@plt+0x1168>
    225b:	add    rsp,0x70
    225f:	pop    rbx
    2260:	pop    rbp
    2261:	pop    r12
    2263:	pop    r14
    2265:	pop    r15
    2267:	ret
    2268:	mov    esi,0x180
    226d:	mov    rdi,rbx
    2270:	call   1b93 <free@plt+0xa93>
    2275:	test   rax,rax
    2278:	je     301b <free@plt+0x1f1b>
    227e:	mov    ecx,0x180
    2283:	mov    r14,rax
    2286:	mov    rdx,rax
    2289:	mov    rdi,QWORD PTR [rsp+0x50]
    228e:	mov    rsi,QWORD PTR [rsp+0x58]
    2293:	call   1c04 <free@plt+0xb04>
    2298:	mov    rdx,rax
    229b:	mov    eax,0x190
    22a0:	test   rdx,rdx
    22a3:	jne    225b <free@plt+0x115b>
    22a5:	movabs rsi,0x34544b4341544c43
    22af:	mov    QWORD PTR [r14+0x38],rsi
    22b3:	mov    QWORD PTR [r14+0x40],0x180
    22bb:	mov    QWORD PTR [rip+0x4386],r14        # 6648 <ngx_modules+0x4c8>
    22c2:	mov    QWORD PTR [rip+0x4333],0x1        # 6600 <ngx_modules+0x480>
    22cd:	mov    QWORD PTR [rsp+0x40],0x8
    22d6:	lea    rax,[rip+0x1d40]        # 401d <free@plt+0x2f1d>
    22dd:	mov    QWORD PTR [rsp+0x48],rax
    22e2:	mov    QWORD PTR [rbx+0x258],0xc8
    22ed:	mov    rax,QWORD PTR [rsp+0x40]
    22f2:	mov    QWORD PTR [rbx+0x328],rax
    22f9:	mov    QWORD PTR [rbx+0x2f8],0xa
    2304:	lea    rax,[rip+0x1dbe]        # 40c9 <free@plt+0x2fc9>
    230b:	mov    QWORD PTR [rbx+0x300],rax
    2312:	mov    rdi,rbx
    2315:	call   10f0 <ngx_http_send_header@plt>
    231a:	cmp    rax,0xffffffffffffffff
    231e:	je     225b <free@plt+0x115b>
    2324:	test   rax,rax
    2327:	jg     225b <free@plt+0x115b>
    232d:	test   BYTE PTR [rbx+0x4bc],0x1
    2334:	jne    225b <free@plt+0x115b>
    233a:	mov    rdi,QWORD PTR [rbx+0x58]
    233e:	mov    esi,0x50
    2343:	call   10d0 <ngx_pcalloc@plt>
    2348:	test   rax,rax
    234b:	je     30cf <free@plt+0x1fcf>
    2351:	mov    rdx,QWORD PTR [rsp+0x48]
    2356:	mov    QWORD PTR [rax],rdx
    2359:	add    rdx,QWORD PTR [rsp+0x40]
    235e:	mov    QWORD PTR [rax+0x8],rdx
    2362:	or     BYTE PTR [rax+0x48],0x82
    2366:	mov    QWORD PTR [rsp+0x30],rax
    236b:	mov    QWORD PTR [rsp+0x38],0x0
    2374:	lea    rsi,[rsp+0x30]
    2379:	mov    rdi,rbx
    237c:	call   1020 <ngx_http_output_filter@plt>
    2381:	jmp    225b <free@plt+0x115b>
    2386:	mov    ecx,0x6
    238b:	lea    rdx,[rip+0x1c94]        # 4026 <free@plt+0x2f26>
    2392:	mov    rdi,QWORD PTR [rsp+0x60]
    2397:	mov    rsi,QWORD PTR [rsp+0x68]
    239c:	call   1a44 <free@plt+0x944>
    23a1:	test   rax,rax
    23a4:	je     25b4 <free@plt+0x14b4>
    23aa:	mov    eax,0x190
    23af:	cmp    QWORD PTR [rip+0x4249],0x1        # 6600 <ngx_modules+0x480>
    23b7:	jne    225b <free@plt+0x115b>
    23bd:	mov    rax,QWORD PTR [rip+0x4284]        # 6648 <ngx_modules+0x4c8>
    23c4:	test   rax,rax
    23c7:	je     3025 <free@plt+0x1f25>
    23cd:	mov    eax,0x190
    23d2:	cmp    QWORD PTR [rsp+0x50],0x300
    23db:	jne    225b <free@plt+0x115b>
    23e1:	mov    esi,0x180
    23e6:	mov    rdi,rbx
    23e9:	call   1b93 <free@plt+0xa93>
    23ee:	mov    r14,rax
    23f1:	test   rax,rax
    23f4:	je     302f <free@plt+0x1f2f>
    23fa:	mov    ecx,0x180
    23ff:	mov    rdx,rax
    2402:	mov    rdi,QWORD PTR [rsp+0x50]
    2407:	mov    rsi,QWORD PTR [rsp+0x58]
    240c:	call   1c04 <free@plt+0xb04>
    2411:	mov    rdx,rax
    2414:	mov    eax,0x190
    2419:	test   rdx,rdx
    241c:	jne    225b <free@plt+0x115b>
    2422:	mov    rax,QWORD PTR [rip+0x421f]        # 6648 <ngx_modules+0x4c8>
    2429:	cmp    rax,r14
    242c:	je     2448 <free@plt+0x1348>
    242e:	mov    QWORD PTR [rsp+0x40],0x7
    2437:	lea    rax,[rip+0x1bef]        # 402d <free@plt+0x2f2d>
    243e:	mov    QWORD PTR [rsp+0x48],rax
    2443:	jmp    22e2 <free@plt+0x11e2>
    2448:	mov    rdx,QWORD PTR [rip+0x41f9]        # 6648 <ngx_modules+0x4c8>
    244f:	movabs rax,0x34544b4341544c43
    2459:	cmp    QWORD PTR [rdx+0x38],rax
    245d:	jne    242e <free@plt+0x132e>
    245f:	mov    rax,QWORD PTR [rip+0x41e2]        # 6648 <ngx_modules+0x4c8>
    2466:	cmp    QWORD PTR [rax+0x40],0x491
    246e:	jne    242e <free@plt+0x132e>
    2470:	mov    esi,0x128
    2475:	mov    rdi,rbx
    2478:	call   1b93 <free@plt+0xa93>
    247d:	mov    r15,rax
    2480:	test   rax,rax
    2483:	je     25aa <free@plt+0x14aa>
    2489:	mov    rsi,rax
    248c:	mov    QWORD PTR [rax],0x0
    2493:	mov    QWORD PTR [rax+0x120],0x0
    249e:	lea    rdi,[rax+0x8]
    24a2:	and    rdi,0xfffffffffffffff8
    24a6:	mov    rcx,rax
    24a9:	sub    rcx,rdi
    24ac:	add    ecx,0x128
    24b2:	shr    ecx,0x3
    24b5:	mov    ecx,ecx
    24b7:	mov    eax,0x0
    24bc:	rep stos QWORD PTR es:[rdi],rax
    24bf:	movabs rax,0x344e4f4341454243
    24c9:	mov    QWORD PTR [r15+0x30],rax
    24cd:	add    rsi,0x38
    24d1:	mov    edx,0x8
    24d6:	mov    edi,0x13e
    24db:	mov    eax,0x0
    24e0:	call   1040 <syscall@plt>
    24e5:	cmp    QWORD PTR [r15+0x38],0x0
    24ea:	jne    24fa <free@plt+0x13fa>
    24ec:	movabs rax,0x9e3779b97f4a7c15
    24f6:	mov    QWORD PTR [r15+0x38],rax
    24fa:	mov    rdi,QWORD PTR [r15+0x38]
    24fe:	mov    r14,rdi
    2501:	mov    QWORD PTR [rsp],rdi
    2505:	lea    rdx,[rip+0xfffffffffffffc8d]        # 2199 <free@plt+0x1099>
    250c:	mov    QWORD PTR [rsp+0x8],rdx
    2511:	mov    rbp,QWORD PTR [rip+0x40f8]        # 6610 <ngx_modules+0x490>
    2518:	mov    QWORD PTR [rsp+0x10],rbp
    251d:	mov    QWORD PTR [rsp+0x18],rdi
    2522:	mov    rax,rdi
    2525:	rol    rax,0x11
    2529:	xor    rax,rdx
    252c:	mov    QWORD PTR [r15+0x40],rax
    2530:	mov    rdx,rsp
    2533:	mov    ecx,0x2
    2538:	mov    rsi,rdi
    253b:	lea    rdi,[rip+0xfffffffffffffc57]        # 2199 <free@plt+0x1099>
    2542:	call   115b <free@plt+0x5b>
    2547:	xor    rax,rbp
    254a:	mov    QWORD PTR [r15+0x48],rax
    254e:	lea    rdx,[rsp+0x10]
    2553:	mov    ecx,0x2
    2558:	mov    rsi,r14
    255b:	lea    rdi,[rip+0xfffffffffffffc37]        # 2199 <free@plt+0x1099>
    2562:	call   115b <free@plt+0x5b>
    2567:	xor    rax,QWORD PTR [rip+0x409a]        # 6608 <ngx_modules+0x488>
    256e:	mov    QWORD PTR [r15+0x50],rax
    2572:	mov    rdi,r15
    2575:	call   121b <free@plt+0x11b>
    257a:	mov    QWORD PTR [r15+0x58],rax
    257e:	mov    QWORD PTR [rip+0x40bb],r15        # 6640 <ngx_modules+0x4c0>
    2585:	mov    QWORD PTR [rip+0x4070],0x2        # 6600 <ngx_modules+0x480>
    2590:	mov    QWORD PTR [rsp+0x40],0x7
    2599:	lea    rax,[rip+0x1a95]        # 4035 <free@plt+0x2f35>
    25a0:	mov    QWORD PTR [rsp+0x48],rax
    25a5:	jmp    22e2 <free@plt+0x11e2>
    25aa:	mov    eax,0x1f4
    25af:	jmp    225b <free@plt+0x115b>
    25b4:	mov    ecx,0xa
    25b9:	lea    rdx,[rip+0x1a7d]        # 403d <free@plt+0x2f3d>
    25c0:	mov    rdi,QWORD PTR [rsp+0x60]
    25c5:	mov    rsi,QWORD PTR [rsp+0x68]
    25ca:	call   1a44 <free@plt+0x944>
    25cf:	test   rax,rax
    25d2:	je     277d <free@plt+0x167d>
    25d8:	mov    eax,0x190
    25dd:	cmp    QWORD PTR [rip+0x401b],0x2        # 6600 <ngx_modules+0x480>
    25e5:	jne    225b <free@plt+0x115b>
    25eb:	mov    rdi,QWORD PTR [rip+0x404e]        # 6640 <ngx_modules+0x4c0>
    25f2:	call   12c4 <free@plt+0x1c4>
    25f7:	mov    rdx,rax
    25fa:	mov    eax,0x190
    25ff:	test   rdx,rdx
    2602:	je     225b <free@plt+0x115b>
    2608:	cmp    QWORD PTR [rsp+0x50],0x0
    260e:	jne    225b <free@plt+0x115b>
    2614:	mov    esi,0xf8
    2619:	mov    rdi,rbx
    261c:	call   1b93 <free@plt+0xa93>
    2621:	mov    rsi,rax
    2624:	mov    r15,rax
    2627:	test   rax,rax
    262a:	je     2773 <free@plt+0x1673>
    2630:	mov    QWORD PTR [rax],0x0
    2637:	mov    QWORD PTR [rax+0xf0],0x0
    2642:	lea    rdi,[rax+0x8]
    2646:	and    rdi,0xfffffffffffffff8
    264a:	mov    rcx,rax
    264d:	sub    rcx,rdi
    2650:	add    ecx,0xf8
    2656:	shr    ecx,0x3
    2659:	mov    ecx,ecx
    265b:	mov    eax,0x0
    2660:	rep stos QWORD PTR es:[rdi],rax
    2663:	movabs rax,0x34524744454c4c43
    266d:	mov    QWORD PTR [rsi+0x28],rax
    2671:	lea    rsi,[rsi+0x30]
    2675:	mov    edx,0x8
    267a:	mov    edi,0x13e
    267f:	mov    eax,0x0
    2684:	call   1040 <syscall@plt>
    2689:	cmp    QWORD PTR [r15+0x30],0x0
    268e:	jne    269e <free@plt+0x159e>
    2690:	movabs rax,0x9e3779b97f4a7c14
    269a:	mov    QWORD PTR [r15+0x30],rax
    269e:	mov    rax,QWORD PTR [rip+0x3f9b]        # 6640 <ngx_modules+0x4c0>
    26a5:	mov    rax,QWORD PTR [rax+0x38]
    26a9:	mov    r14,r15
    26ac:	mov    QWORD PTR [r15+0x38],rax
    26b0:	mov    r15,QWORD PTR [rbx+0x8]
    26b4:	mov    rax,QWORD PTR [r14+0x30]
    26b8:	mov    QWORD PTR [rsp],rax
    26bc:	mov    rdx,QWORD PTR [rip+0x3f7d]        # 6640 <ngx_modules+0x4c0>
    26c3:	mov    rdx,QWORD PTR [rdx+0x38]
    26c7:	mov    QWORD PTR [rsp+0x8],rdx
    26cc:	mov    QWORD PTR [rsp+0x10],r15
    26d1:	lea    rsi,[rip+0xfffffffffffffac1]        # 2199 <free@plt+0x1099>
    26d8:	mov    QWORD PTR [rsp+0x18],rsi
    26dd:	mov    rdx,QWORD PTR [rip+0x3f5c]        # 6640 <ngx_modules+0x4c0>
    26e4:	mov    rdx,QWORD PTR [rdx+0x38]
    26e8:	mov    QWORD PTR [rsp+0x20],rdx
    26ed:	mov    QWORD PTR [rsp+0x28],rax
    26f2:	mov    rbp,QWORD PTR [rip+0x3f17]        # 6610 <ngx_modules+0x490>
    26f9:	mov    r12,QWORD PTR [rip+0x3f08]        # 6608 <ngx_modules+0x488>
    2700:	mov    rdx,rsp
    2703:	mov    ecx,0x2
    2708:	mov    rsi,rbp
    270b:	mov    rdi,r12
    270e:	call   115b <free@plt+0x5b>
    2713:	xor    rax,r15
    2716:	mov    QWORD PTR [r14+0x40],rax
    271a:	lea    rdx,[rsp+0x10]
    271f:	mov    ecx,0x4
    2724:	mov    rsi,rbp
    2727:	mov    rdi,r12
    272a:	call   115b <free@plt+0x5b>
    272f:	mov    QWORD PTR [r14+0x48],rax
    2733:	mov    QWORD PTR [r14+0x50],0x1
    273b:	mov    rdi,r14
    273e:	call   126b <free@plt+0x16b>
    2743:	mov    QWORD PTR [r14+0x58],rax
    2747:	mov    QWORD PTR [rip+0x3eea],r14        # 6638 <ngx_modules+0x4b8>
    274e:	mov    QWORD PTR [rip+0x3ea7],0x3        # 6600 <ngx_modules+0x480>
    2759:	mov    QWORD PTR [rsp+0x40],0x7
    2762:	lea    rax,[rip+0x18df]        # 4048 <free@plt+0x2f48>
    2769:	mov    QWORD PTR [rsp+0x48],rax
    276e:	jmp    22e2 <free@plt+0x11e2>
    2773:	mov    eax,0x1f4
    2778:	jmp    225b <free@plt+0x115b>
    277d:	mov    ecx,0x6
    2782:	lea    rdx,[rip+0x18c7]        # 4050 <free@plt+0x2f50>
    2789:	mov    rdi,QWORD PTR [rsp+0x60]
    278e:	mov    rsi,QWORD PTR [rsp+0x68]
    2793:	call   1a44 <free@plt+0x944>
    2798:	test   rax,rax
    279b:	je     2953 <free@plt+0x1853>
    27a1:	cmp    QWORD PTR [rip+0x3e57],0x3        # 6600 <ngx_modules+0x480>
    27a9:	jne    3039 <free@plt+0x1f39>
    27af:	mov    rdi,QWORD PTR [rip+0x3e8a]        # 6640 <ngx_modules+0x4c0>
    27b6:	call   12c4 <free@plt+0x1c4>
    27bb:	test   rax,rax
    27be:	je     3043 <free@plt+0x1f43>
    27c4:	lea    rax,[rip+0x3a37]        # 6202 <ngx_modules+0x82>
    27cb:	lea    rdx,[rip+0x1885]        # 4057 <free@plt+0x2f57>
    27d2:	cmp    rdx,rax
    27d5:	jae    27eb <free@plt+0x16eb>
    27d7:	lea    rdx,[rax-0x2]
    27db:	lea    rax,[rip+0x1875]        # 4057 <free@plt+0x2f57>
    27e2:	cmp    rdx,rax
    27e5:	jb     294b <free@plt+0x184b>
    27eb:	lea    rax,[rip+0x1867]        # 4059 <free@plt+0x2f59>
    27f2:	lea    rdx,[rip+0x3a07]        # 6200 <ngx_modules+0x80>
    27f9:	cmp    rdx,rax
    27fc:	jae    2811 <free@plt+0x1711>
    27fe:	mov    rax,rdx
    2801:	lea    rdx,[rip+0x184f]        # 4057 <free@plt+0x2f57>
    2808:	cmp    rdx,rax
    280b:	jb     294b <free@plt+0x184b>
    2811:	mov    WORD PTR [rip+0x39e6],0x3d6e        # 6200 <ngx_modules+0x80>
    281a:	mov    rax,QWORD PTR [rip+0x3e1f]        # 6640 <ngx_modules+0x4c0>
    2821:	mov    rsi,QWORD PTR [rax+0x38]
    2825:	lea    rdi,[rip+0x39d6]        # 6202 <ngx_modules+0x82>
    282c:	call   1a85 <free@plt+0x985>
    2831:	lea    rdx,[rip+0x1822]        # 405a <free@plt+0x2f5a>
    2838:	cmp    rax,rdx
    283b:	jae    2851 <free@plt+0x1751>
    283d:	lea    rdx,[rax+0x3]
    2841:	lea    rcx,[rip+0x1812]        # 405a <free@plt+0x2f5a>
    2848:	cmp    rcx,rdx
    284b:	jb     294d <free@plt+0x184d>
    2851:	lea    rdx,[rip+0x1802]        # 405a <free@plt+0x2f5a>
    2858:	cmp    rdx,rax
    285b:	jae    286a <free@plt+0x176a>
    285d:	lea    rdx,[rdx+0x3]
    2861:	cmp    rax,rdx
    2864:	jb     294d <free@plt+0x184d>
    286a:	mov    WORD PTR [rax],0x6120
    286f:	mov    BYTE PTR [rax+0x2],0x3d
    2873:	lea    rdi,[rax+0x3]
    2877:	mov    rax,QWORD PTR [rip+0x3dc2]        # 6640 <ngx_modules+0x4c0>
    287e:	mov    rsi,QWORD PTR [rax+0x40]
    2882:	call   1a85 <free@plt+0x985>
    2887:	lea    rdx,[rip+0x17d0]        # 405e <free@plt+0x2f5e>
    288e:	cmp    rax,rdx
    2891:	jae    28a7 <free@plt+0x17a7>
    2893:	lea    rdx,[rax+0x3]
    2897:	lea    rcx,[rip+0x17c0]        # 405e <free@plt+0x2f5e>
    289e:	cmp    rcx,rdx
    28a1:	jb     294f <free@plt+0x184f>
    28a7:	lea    rdx,[rip+0x17b0]        # 405e <free@plt+0x2f5e>
    28ae:	cmp    rdx,rax
    28b1:	jae    28c0 <free@plt+0x17c0>
    28b3:	lea    rdx,[rdx+0x3]
    28b7:	cmp    rax,rdx
    28ba:	jb     294f <free@plt+0x184f>
    28c0:	mov    WORD PTR [rax],0x6520
    28c5:	mov    BYTE PTR [rax+0x2],0x3d
    28c9:	lea    rdi,[rax+0x3]
    28cd:	mov    rax,QWORD PTR [rip+0x3d6c]        # 6640 <ngx_modules+0x4c0>
    28d4:	mov    rsi,QWORD PTR [rax+0x48]
    28d8:	call   1a85 <free@plt+0x985>
    28dd:	lea    rdx,[rip+0x177e]        # 4062 <free@plt+0x2f62>
    28e4:	cmp    rax,rdx
    28e7:	jae    28f9 <free@plt+0x17f9>
    28e9:	lea    rdx,[rax+0x3]
    28ed:	lea    rcx,[rip+0x176e]        # 4062 <free@plt+0x2f62>
    28f4:	cmp    rcx,rdx
    28f7:	jb     2951 <free@plt+0x1851>
    28f9:	lea    rdx,[rip+0x1762]        # 4062 <free@plt+0x2f62>
    2900:	cmp    rdx,rax
    2903:	jae    290e <free@plt+0x180e>
    2905:	lea    rdx,[rdx+0x3]
    2909:	cmp    rax,rdx
    290c:	jb     2951 <free@plt+0x1851>
    290e:	mov    WORD PTR [rax],0x6b20
    2913:	mov    BYTE PTR [rax+0x2],0x3d
    2917:	lea    rdi,[rax+0x3]
    291b:	mov    rax,QWORD PTR [rip+0x3d1e]        # 6640 <ngx_modules+0x4c0>
    2922:	mov    rsi,QWORD PTR [rax+0x50]
    2926:	call   1a85 <free@plt+0x985>
    292b:	mov    BYTE PTR [rax],0xa
    292e:	lea    rdx,[rip+0x38cb]        # 6200 <ngx_modules+0x80>
    2935:	mov    QWORD PTR [rsp+0x48],rdx
    293a:	add    rax,0x1
    293e:	sub    rax,rdx
    2941:	mov    QWORD PTR [rsp+0x40],rax
    2946:	jmp    22e2 <free@plt+0x11e2>
    294b:	ud2
    294d:	ud2
    294f:	ud2
    2951:	ud2
    2953:	mov    ecx,0x6
    2958:	lea    rdx,[rip+0x1707]        # 4066 <free@plt+0x2f66>
    295f:	mov    rdi,QWORD PTR [rsp+0x60]
    2964:	mov    rsi,QWORD PTR [rsp+0x68]
    2969:	call   1a44 <free@plt+0x944>
    296e:	test   rax,rax
    2971:	je     2adc <free@plt+0x19dc>
    2977:	cmp    QWORD PTR [rip+0x3c81],0x3        # 6600 <ngx_modules+0x480>
    297f:	jne    304d <free@plt+0x1f4d>
    2985:	mov    rsi,QWORD PTR [rip+0x3cb4]        # 6640 <ngx_modules+0x4c0>
    298c:	mov    rdi,QWORD PTR [rip+0x3ca5]        # 6638 <ngx_modules+0x4b8>
    2993:	mov    rdx,rbx
    2996:	call   12f8 <free@plt+0x1f8>
    299b:	test   rax,rax
    299e:	je     3057 <free@plt+0x1f57>
    29a4:	lea    rdx,[rip+0x3855]        # 6200 <ngx_modules+0x80>
    29ab:	lea    rax,[rip+0x16a5]        # 4057 <free@plt+0x2f57>
    29b2:	cmp    rdx,rax
    29b5:	jae    29cb <free@plt+0x18cb>
    29b7:	lea    rax,[rdx+0x2]
    29bb:	lea    rdx,[rip+0x1695]        # 4057 <free@plt+0x2f57>
    29c2:	cmp    rdx,rax
    29c5:	jb     2ad6 <free@plt+0x19d6>
    29cb:	lea    rax,[rip+0x382e]        # 6200 <ngx_modules+0x80>
    29d2:	lea    rdx,[rip+0x167e]        # 4057 <free@plt+0x2f57>
    29d9:	cmp    rdx,rax
    29dc:	jae    29f2 <free@plt+0x18f2>
    29de:	lea    rax,[rdx+0x2]
    29e2:	lea    rdx,[rip+0x3817]        # 6200 <ngx_modules+0x80>
    29e9:	cmp    rdx,rax
    29ec:	jb     2ad6 <free@plt+0x19d6>
    29f2:	mov    WORD PTR [rip+0x3805],0x3d6e        # 6200 <ngx_modules+0x80>
    29fb:	mov    rax,QWORD PTR [rip+0x3c36]        # 6638 <ngx_modules+0x4b8>
    2a02:	mov    rsi,QWORD PTR [rax+0x30]
    2a06:	lea    rdi,[rip+0x37f5]        # 6202 <ngx_modules+0x82>
    2a0d:	call   1a85 <free@plt+0x985>
    2a12:	lea    rdx,[rip+0x1654]        # 406d <free@plt+0x2f6d>
    2a19:	cmp    rax,rdx
    2a1c:	jae    2a32 <free@plt+0x1932>
    2a1e:	lea    rdx,[rax+0x3]
    2a22:	lea    rcx,[rip+0x1644]        # 406d <free@plt+0x2f6d>
    2a29:	cmp    rcx,rdx
    2a2c:	jb     2ad8 <free@plt+0x19d8>
    2a32:	lea    rdx,[rip+0x1634]        # 406d <free@plt+0x2f6d>
    2a39:	cmp    rdx,rax
    2a3c:	jae    2a4b <free@plt+0x194b>
    2a3e:	lea    rdx,[rdx+0x3]
    2a42:	cmp    rax,rdx
    2a45:	jb     2ad8 <free@plt+0x19d8>
    2a4b:	mov    WORD PTR [rax],0x6f20
    2a50:	mov    BYTE PTR [rax+0x2],0x3d
    2a54:	lea    rdi,[rax+0x3]
    2a58:	mov    rax,QWORD PTR [rip+0x3bd9]        # 6638 <ngx_modules+0x4b8>
    2a5f:	mov    rsi,QWORD PTR [rax+0x40]
    2a63:	call   1a85 <free@plt+0x985>
    2a68:	lea    rdx,[rip+0x1602]        # 4071 <free@plt+0x2f71>
    2a6f:	cmp    rax,rdx
    2a72:	jae    2a84 <free@plt+0x1984>
    2a74:	lea    rdx,[rax+0x3]
    2a78:	lea    rcx,[rip+0x15f2]        # 4071 <free@plt+0x2f71>
    2a7f:	cmp    rcx,rdx
    2a82:	jb     2ada <free@plt+0x19da>
    2a84:	lea    rdx,[rip+0x15e9]        # 4074 <free@plt+0x2f74>
    2a8b:	cmp    rax,rdx
    2a8e:	jae    2a99 <free@plt+0x1999>
    2a90:	lea    rdx,[rdx-0x3]
    2a94:	cmp    rdx,rax
    2a97:	jb     2ada <free@plt+0x19da>
    2a99:	mov    WORD PTR [rax],0x7420
    2a9e:	mov    BYTE PTR [rax+0x2],0x3d
    2aa2:	lea    rdi,[rax+0x3]
    2aa6:	mov    rax,QWORD PTR [rip+0x3b8b]        # 6638 <ngx_modules+0x4b8>
    2aad:	mov    rsi,QWORD PTR [rax+0x48]
    2ab1:	call   1a85 <free@plt+0x985>
    2ab6:	mov    BYTE PTR [rax],0xa
    2ab9:	lea    rdx,[rip+0x3740]        # 6200 <ngx_modules+0x80>
    2ac0:	mov    QWORD PTR [rsp+0x48],rdx
    2ac5:	add    rax,0x1
    2ac9:	sub    rax,rdx
    2acc:	mov    QWORD PTR [rsp+0x40],rax
    2ad1:	jmp    22e2 <free@plt+0x11e2>
    2ad6:	ud2
    2ad8:	ud2
    2ada:	ud2
    2adc:	mov    ecx,0x5
    2ae1:	lea    rdx,[rip+0x158d]        # 4075 <free@plt+0x2f75>
    2ae8:	mov    rdi,QWORD PTR [rsp+0x60]
    2aed:	mov    rsi,QWORD PTR [rsp+0x68]
    2af2:	call   1a44 <free@plt+0x944>
    2af7:	test   rax,rax
    2afa:	je     2bc7 <free@plt+0x1ac7>
    2b00:	mov    eax,0x190
    2b05:	cmp    QWORD PTR [rip+0x3af3],0x3        # 6600 <ngx_modules+0x480>
    2b0d:	jne    225b <free@plt+0x115b>
    2b13:	cmp    QWORD PTR [rsp+0x50],0x350
    2b1c:	jne    225b <free@plt+0x115b>
    2b22:	mov    esi,0x1a8
    2b27:	mov    rdi,rbx
    2b2a:	call   1b93 <free@plt+0xa93>
    2b2f:	mov    r15,rax
    2b32:	test   rax,rax
    2b35:	je     3061 <free@plt+0x1f61>
    2b3b:	mov    ecx,0x1a8
    2b40:	mov    rdx,rax
    2b43:	mov    rdi,QWORD PTR [rsp+0x50]
    2b48:	mov    rsi,QWORD PTR [rsp+0x58]
    2b4d:	call   1c04 <free@plt+0xb04>
    2b52:	mov    rdx,rax
    2b55:	mov    eax,0x190
    2b5a:	test   rdx,rdx
    2b5d:	jne    225b <free@plt+0x115b>
    2b63:	mov    rdx,QWORD PTR [rip+0x3ace]        # 6638 <ngx_modules+0x4b8>
    2b6a:	mov    rsi,QWORD PTR [rip+0x3acf]        # 6640 <ngx_modules+0x4c0>
    2b71:	mov    rcx,rbx
    2b74:	mov    rdi,r15
    2b77:	call   13fa <free@plt+0x2fa>
    2b7c:	test   rax,rax
    2b7f:	je     2bad <free@plt+0x1aad>
    2b81:	mov    QWORD PTR [rip+0x3aa8],r15        # 6630 <ngx_modules+0x4b0>
    2b88:	mov    QWORD PTR [rip+0x3a6d],0x4        # 6600 <ngx_modules+0x480>
    2b93:	mov    QWORD PTR [rsp+0x40],0x7
    2b9c:	lea    rax,[rip+0x14d8]        # 407b <free@plt+0x2f7b>
    2ba3:	mov    QWORD PTR [rsp+0x48],rax
    2ba8:	jmp    22e2 <free@plt+0x11e2>
    2bad:	mov    QWORD PTR [rsp+0x40],0x7
    2bb6:	lea    rax,[rip+0x1470]        # 402d <free@plt+0x2f2d>
    2bbd:	mov    QWORD PTR [rsp+0x48],rax
    2bc2:	jmp    22e2 <free@plt+0x11e2>
    2bc7:	mov    ecx,0x4
    2bcc:	lea    rdx,[rip+0x14b0]        # 4083 <free@plt+0x2f83>
    2bd3:	mov    rdi,QWORD PTR [rsp+0x60]
    2bd8:	mov    rsi,QWORD PTR [rsp+0x68]
    2bdd:	call   1a44 <free@plt+0x944>
    2be2:	test   rax,rax
    2be5:	je     2cb6 <free@plt+0x1bb6>
    2beb:	mov    eax,0x190
    2bf0:	cmp    QWORD PTR [rip+0x3a08],0x4        # 6600 <ngx_modules+0x480>
    2bf8:	jne    225b <free@plt+0x115b>
    2bfe:	cmp    QWORD PTR [rsp+0x50],0x1b0
    2c07:	jne    225b <free@plt+0x115b>
    2c0d:	mov    esi,0xd8
    2c12:	mov    rdi,rbx
    2c15:	call   1b93 <free@plt+0xa93>
    2c1a:	mov    r15,rax
    2c1d:	test   rax,rax
    2c20:	je     306b <free@plt+0x1f6b>
    2c26:	mov    ecx,0xd8
    2c2b:	mov    rdx,rax
    2c2e:	mov    rdi,QWORD PTR [rsp+0x50]
    2c33:	mov    rsi,QWORD PTR [rsp+0x58]
    2c38:	call   1c04 <free@plt+0xb04>
    2c3d:	mov    rdx,rax
    2c40:	mov    eax,0x190
    2c45:	test   rdx,rdx
    2c48:	jne    225b <free@plt+0x115b>
    2c4e:	mov    rcx,QWORD PTR [rip+0x39e3]        # 6638 <ngx_modules+0x4b8>
    2c55:	mov    rdx,QWORD PTR [rip+0x39e4]        # 6640 <ngx_modules+0x4c0>
    2c5c:	mov    rsi,QWORD PTR [rip+0x39cd]        # 6630 <ngx_modules+0x4b0>
    2c63:	mov    rdi,r15
    2c66:	call   1559 <free@plt+0x459>
    2c6b:	test   rax,rax
    2c6e:	je     2c9c <free@plt+0x1b9c>
    2c70:	mov    QWORD PTR [rip+0x39b1],r15        # 6628 <ngx_modules+0x4a8>
    2c77:	mov    QWORD PTR [rip+0x397e],0x5        # 6600 <ngx_modules+0x480>
    2c82:	mov    QWORD PTR [rsp+0x40],0x7
    2c8b:	lea    rax,[rip+0x13f6]        # 4088 <free@plt+0x2f88>
    2c92:	mov    QWORD PTR [rsp+0x48],rax
    2c97:	jmp    22e2 <free@plt+0x11e2>
    2c9c:	mov    QWORD PTR [rsp+0x40],0x7
    2ca5:	lea    rax,[rip+0x1381]        # 402d <free@plt+0x2f2d>
    2cac:	mov    QWORD PTR [rsp+0x48],rax
    2cb1:	jmp    22e2 <free@plt+0x11e2>
    2cb6:	mov    ecx,0x5
    2cbb:	lea    rdx,[rip+0x13ce]        # 4090 <free@plt+0x2f90>
    2cc2:	mov    rdi,QWORD PTR [rsp+0x60]
    2cc7:	mov    rsi,QWORD PTR [rsp+0x68]
    2ccc:	call   1a44 <free@plt+0x944>
    2cd1:	test   rax,rax
    2cd4:	je     2da7 <free@plt+0x1ca7>
    2cda:	mov    eax,0x190
    2cdf:	cmp    QWORD PTR [rip+0x3919],0x5        # 6600 <ngx_modules+0x480>
    2ce7:	jne    225b <free@plt+0x115b>
    2ced:	cmp    QWORD PTR [rsp+0x50],0x430
    2cf6:	jne    225b <free@plt+0x115b>
    2cfc:	mov    esi,0x218
    2d01:	mov    rdi,rbx
    2d04:	call   1b93 <free@plt+0xa93>
    2d09:	mov    r15,rax
    2d0c:	test   rax,rax
    2d0f:	je     3075 <free@plt+0x1f75>
    2d15:	mov    ecx,0x218
    2d1a:	mov    rdx,rax
    2d1d:	mov    rdi,QWORD PTR [rsp+0x50]
    2d22:	mov    rsi,QWORD PTR [rsp+0x58]
    2d27:	call   1c04 <free@plt+0xb04>
    2d2c:	test   rax,rax
    2d2f:	jne    307f <free@plt+0x1f7f>
    2d35:	mov    r8,QWORD PTR [rip+0x38fc]        # 6638 <ngx_modules+0x4b8>
    2d3c:	mov    rcx,QWORD PTR [rip+0x38fd]        # 6640 <ngx_modules+0x4c0>
    2d43:	mov    rdx,QWORD PTR [rip+0x38de]        # 6628 <ngx_modules+0x4a8>
    2d4a:	mov    rsi,QWORD PTR [rip+0x38df]        # 6630 <ngx_modules+0x4b0>
    2d51:	mov    r9,rbx
    2d54:	mov    rdi,r15
    2d57:	call   163e <free@plt+0x53e>
    2d5c:	test   rax,rax
    2d5f:	je     2d8d <free@plt+0x1c8d>
    2d61:	mov    QWORD PTR [rip+0x38b8],r15        # 6620 <ngx_modules+0x4a0>
    2d68:	mov    QWORD PTR [rip+0x388d],0x6        # 6600 <ngx_modules+0x480>
    2d73:	mov    QWORD PTR [rsp+0x40],0x8
    2d7c:	lea    rax,[rip+0x1313]        # 4096 <free@plt+0x2f96>
    2d83:	mov    QWORD PTR [rsp+0x48],rax
    2d88:	jmp    22e2 <free@plt+0x11e2>
    2d8d:	mov    QWORD PTR [rsp+0x40],0x7
    2d96:	lea    rax,[rip+0x1290]        # 402d <free@plt+0x2f2d>
    2d9d:	mov    QWORD PTR [rsp+0x48],rax
    2da2:	jmp    22e2 <free@plt+0x11e2>
    2da7:	mov    ecx,0x7
    2dac:	lea    rdx,[rip+0x12ec]        # 409f <free@plt+0x2f9f>
    2db3:	mov    rdi,QWORD PTR [rsp+0x60]
    2db8:	mov    rsi,QWORD PTR [rsp+0x68]
    2dbd:	call   1a44 <free@plt+0x944>
    2dc2:	test   rax,rax
    2dc5:	je     2e9c <free@plt+0x1d9c>
    2dcb:	mov    eax,0x190
    2dd0:	cmp    QWORD PTR [rip+0x3828],0x6        # 6600 <ngx_modules+0x480>
    2dd8:	jne    225b <free@plt+0x115b>
    2dde:	cmp    QWORD PTR [rsp+0x50],0x210
    2de7:	jne    225b <free@plt+0x115b>
    2ded:	mov    esi,0x108
    2df2:	mov    rdi,rbx
    2df5:	call   1b93 <free@plt+0xa93>
    2dfa:	mov    r15,rax
    2dfd:	test   rax,rax
    2e00:	je     3089 <free@plt+0x1f89>
    2e06:	mov    ecx,0x108
    2e0b:	mov    rdx,rax
    2e0e:	mov    rdi,QWORD PTR [rsp+0x50]
    2e13:	mov    rsi,QWORD PTR [rsp+0x58]
    2e18:	call   1c04 <free@plt+0xb04>
    2e1d:	test   rax,rax
    2e20:	jne    3093 <free@plt+0x1f93>
    2e26:	mov    r9,QWORD PTR [rip+0x380b]        # 6638 <ngx_modules+0x4b8>
    2e2d:	mov    r8,QWORD PTR [rip+0x380c]        # 6640 <ngx_modules+0x4c0>
    2e34:	mov    rcx,QWORD PTR [rip+0x37ed]        # 6628 <ngx_modules+0x4a8>
    2e3b:	mov    rdx,QWORD PTR [rip+0x37ee]        # 6630 <ngx_modules+0x4b0>
    2e42:	mov    rsi,QWORD PTR [rip+0x37d7]        # 6620 <ngx_modules+0x4a0>
    2e49:	mov    rdi,r15
    2e4c:	call   1929 <free@plt+0x829>
    2e51:	test   rax,rax
    2e54:	je     2e82 <free@plt+0x1d82>
    2e56:	mov    QWORD PTR [rip+0x37bb],r15        # 6618 <ngx_modules+0x498>
    2e5d:	mov    QWORD PTR [rip+0x3798],0x7        # 6600 <ngx_modules+0x480>
    2e68:	mov    QWORD PTR [rsp+0x40],0x8
    2e71:	lea    rax,[rip+0x122f]        # 40a7 <free@plt+0x2fa7>
    2e78:	mov    QWORD PTR [rsp+0x48],rax
    2e7d:	jmp    22e2 <free@plt+0x11e2>
    2e82:	mov    QWORD PTR [rsp+0x40],0x7
    2e8b:	lea    rax,[rip+0x119b]        # 402d <free@plt+0x2f2d>
    2e92:	mov    QWORD PTR [rsp+0x48],rax
    2e97:	jmp    22e2 <free@plt+0x11e2>
    2e9c:	mov    ecx,0x6
    2ea1:	lea    rdx,[rip+0x1208]        # 40b0 <free@plt+0x2fb0>
    2ea8:	mov    rdi,QWORD PTR [rsp+0x60]
    2ead:	mov    rsi,QWORD PTR [rsp+0x68]
    2eb2:	call   1a44 <free@plt+0x944>
    2eb7:	test   rax,rax
    2eba:	je     2fab <free@plt+0x1eab>
    2ec0:	cmp    QWORD PTR [rip+0x3738],0x7        # 6600 <ngx_modules+0x480>
    2ec8:	jne    309d <free@plt+0x1f9d>
    2ece:	mov    r8,QWORD PTR [rip+0x3763]        # 6638 <ngx_modules+0x4b8>
    2ed5:	mov    rcx,QWORD PTR [rip+0x3764]        # 6640 <ngx_modules+0x4c0>
    2edc:	mov    rdx,QWORD PTR [rip+0x3745]        # 6628 <ngx_modules+0x4a8>
    2ee3:	mov    rsi,QWORD PTR [rip+0x3746]        # 6630 <ngx_modules+0x4b0>
    2eea:	mov    rdi,QWORD PTR [rip+0x372f]        # 6620 <ngx_modules+0x4a0>
    2ef1:	mov    r9,rbx
    2ef4:	call   163e <free@plt+0x53e>
    2ef9:	test   rax,rax
    2efc:	je     30a7 <free@plt+0x1fa7>
    2f02:	mov    r9,QWORD PTR [rip+0x372f]        # 6638 <ngx_modules+0x4b8>
    2f09:	mov    r8,QWORD PTR [rip+0x3730]        # 6640 <ngx_modules+0x4c0>
    2f10:	mov    rcx,QWORD PTR [rip+0x3711]        # 6628 <ngx_modules+0x4a8>
    2f17:	mov    rdx,QWORD PTR [rip+0x3712]        # 6630 <ngx_modules+0x4b0>
    2f1e:	mov    rsi,QWORD PTR [rip+0x36fb]        # 6620 <ngx_modules+0x4a0>
    2f25:	mov    rdi,QWORD PTR [rip+0x36ec]        # 6618 <ngx_modules+0x498>
    2f2c:	call   1929 <free@plt+0x829>
    2f31:	test   rax,rax
    2f34:	je     30b1 <free@plt+0x1fb1>
    2f3a:	mov    rax,QWORD PTR [rip+0x36ef]        # 6630 <ngx_modules+0x4b0>
    2f41:	mov    rsi,QWORD PTR [rip+0x36e0]        # 6628 <ngx_modules+0x4a8>
    2f48:	mov    rcx,QWORD PTR [rip+0x36d1]        # 6620 <ngx_modules+0x4a0>
    2f4f:	mov    rdx,QWORD PTR [rip+0x36c2]        # 6618 <ngx_modules+0x498>
    2f56:	mov    rax,QWORD PTR [rax+0x60]
    2f5a:	xor    rax,QWORD PTR [rsi+0x50]
    2f5e:	xor    rax,QWORD PTR [rcx+0x70]
    2f62:	xor    rax,QWORD PTR [rdx+0x60]
    2f66:	cmp    rax,0x1
    2f6a:	ja     30bb <free@plt+0x1fbb>
    2f70:	mov    rdi,rbx
    2f73:	lea    rdx,[rip+0x2e86]        # 5e00 <free@plt+0x4d00>
    2f7a:	call   QWORD PTR [rdx+rax*8]
    2f7d:	test   rax,rax
    2f80:	jne    225b <free@plt+0x115b>
    2f86:	mov    QWORD PTR [rip+0x366f],0x8        # 6600 <ngx_modules+0x480>
    2f91:	mov    QWORD PTR [rsp+0x40],0xa
    2f9a:	lea    rax,[rip+0x1116]        # 40b7 <free@plt+0x2fb7>
    2fa1:	mov    QWORD PTR [rsp+0x48],rax
    2fa6:	jmp    22e2 <free@plt+0x11e2>
    2fab:	mov    ecx,0x6
    2fb0:	lea    rdx,[rip+0x110b]        # 40c2 <free@plt+0x2fc2>
    2fb7:	mov    rdi,QWORD PTR [rsp+0x60]
    2fbc:	mov    rsi,QWORD PTR [rsp+0x68]
    2fc1:	call   1a44 <free@plt+0x944>
    2fc6:	test   rax,rax
    2fc9:	je     22e2 <free@plt+0x11e2>
    2fcf:	mov    eax,0x193
    2fd4:	mov    rsi,QWORD PTR [rip+0x3205]        # 61e0 <ngx_modules+0x60>
    2fdb:	cmp    QWORD PTR [rbx+0x8],rsi
    2fdf:	jne    225b <free@plt+0x115b>
    2fe5:	cmp    QWORD PTR [rip+0x3613],0x7        # 6600 <ngx_modules+0x480>
    2fed:	jbe    30c5 <free@plt+0x1fc5>
    2ff3:	lea    rdx,[rsp+0x40]
    2ff8:	mov    rdi,QWORD PTR [rsp+0x50]
    2ffd:	mov    rsi,QWORD PTR [rsp+0x58]
    3002:	call   1cb0 <free@plt+0xbb0>
    3007:	test   rax,rax
    300a:	je     22e2 <free@plt+0x11e2>
    3010:	jmp    225b <free@plt+0x115b>
    3015:	mov    eax,0x195
    301a:	ret
    301b:	mov    eax,0x190
    3020:	jmp    225b <free@plt+0x115b>
    3025:	mov    eax,0x190
    302a:	jmp    225b <free@plt+0x115b>
    302f:	mov    eax,0x190
    3034:	jmp    225b <free@plt+0x115b>
    3039:	mov    eax,0x193
    303e:	jmp    225b <free@plt+0x115b>
    3043:	mov    eax,0x193
    3048:	jmp    225b <free@plt+0x115b>
    304d:	mov    eax,0x193
    3052:	jmp    225b <free@plt+0x115b>
    3057:	mov    eax,0x193
    305c:	jmp    225b <free@plt+0x115b>
    3061:	mov    eax,0x190
    3066:	jmp    225b <free@plt+0x115b>
    306b:	mov    eax,0x190
    3070:	jmp    225b <free@plt+0x115b>
    3075:	mov    eax,0x190
    307a:	jmp    225b <free@plt+0x115b>
    307f:	mov    eax,0x190
    3084:	jmp    225b <free@plt+0x115b>
    3089:	mov    eax,0x190
    308e:	jmp    225b <free@plt+0x115b>
    3093:	mov    eax,0x190
    3098:	jmp    225b <free@plt+0x115b>
    309d:	mov    eax,0x193
    30a2:	jmp    225b <free@plt+0x115b>
    30a7:	mov    eax,0x193
    30ac:	jmp    225b <free@plt+0x115b>
    30b1:	mov    eax,0x193
    30b6:	jmp    225b <free@plt+0x115b>
    30bb:	mov    eax,0x193
    30c0:	jmp    225b <free@plt+0x115b>
    30c5:	mov    eax,0x193
    30ca:	jmp    225b <free@plt+0x115b>
    30cf:	mov    eax,0x1f4
    30d4:	jmp    225b <free@plt+0x115b>
