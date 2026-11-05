
cachevault:     file format elf64-x86-64


Disassembly of section .init:

0000000000001000 <_init>:
    1000:	push   rax
    1001:	pop    rax
    1002:	ret

Disassembly of section .plt:

0000000000001010 <syscall@plt-0x10>:
    1010:	push   QWORD PTR [rip+0x5eea]        # 6f00 <_fini+0x29ec>
    1016:	jmp    QWORD PTR [rip+0x5eec]        # 6f08 <_fini+0x29f4>
    101c:	nop    DWORD PTR [rax+0x0]

0000000000001020 <syscall@plt>:
    1020:	jmp    QWORD PTR [rip+0x5eea]        # 6f10 <syscall>
    1026:	push   0x0
    102b:	jmp    1010 <_init+0x10>

0000000000001030 <prctl@plt>:
    1030:	jmp    QWORD PTR [rip+0x5ee2]        # 6f18 <prctl>
    1036:	push   0x1
    103b:	jmp    1010 <_init+0x10>

0000000000001040 <dup2@plt>:
    1040:	jmp    QWORD PTR [rip+0x5eda]        # 6f20 <dup2>
    1046:	push   0x2
    104b:	jmp    1010 <_init+0x10>

0000000000001050 <socket@plt>:
    1050:	jmp    QWORD PTR [rip+0x5ed2]        # 6f28 <socket>
    1056:	push   0x3
    105b:	jmp    1010 <_init+0x10>

0000000000001060 <chmod@plt>:
    1060:	jmp    QWORD PTR [rip+0x5eca]        # 6f30 <chmod>
    1066:	push   0x4
    106b:	jmp    1010 <_init+0x10>

0000000000001070 <alarm@plt>:
    1070:	jmp    QWORD PTR [rip+0x5ec2]        # 6f38 <alarm>
    1076:	push   0x5
    107b:	jmp    1010 <_init+0x10>

0000000000001080 <accept@plt>:
    1080:	jmp    QWORD PTR [rip+0x5eba]        # 6f40 <accept>
    1086:	push   0x6
    108b:	jmp    1010 <_init+0x10>

0000000000001090 <calloc@plt>:
    1090:	jmp    QWORD PTR [rip+0x5eb2]        # 6f48 <calloc>
    1096:	push   0x7
    109b:	jmp    1010 <_init+0x10>

00000000000010a0 <write@plt>:
    10a0:	jmp    QWORD PTR [rip+0x5eaa]        # 6f50 <write>
    10a6:	push   0x8
    10ab:	jmp    1010 <_init+0x10>

00000000000010b0 <bind@plt>:
    10b0:	jmp    QWORD PTR [rip+0x5ea2]        # 6f58 <bind>
    10b6:	push   0x9
    10bb:	jmp    1010 <_init+0x10>

00000000000010c0 <setgid@plt>:
    10c0:	jmp    QWORD PTR [rip+0x5e9a]        # 6f60 <setgid>
    10c6:	push   0xa
    10cb:	jmp    1010 <_init+0x10>

00000000000010d0 <signal@plt>:
    10d0:	jmp    QWORD PTR [rip+0x5e92]        # 6f68 <signal>
    10d6:	push   0xb
    10db:	jmp    1010 <_init+0x10>

00000000000010e0 <read@plt>:
    10e0:	jmp    QWORD PTR [rip+0x5e8a]        # 6f70 <read>
    10e6:	push   0xc
    10eb:	jmp    1010 <_init+0x10>

00000000000010f0 <unlink@plt>:
    10f0:	jmp    QWORD PTR [rip+0x5e82]        # 6f78 <unlink>
    10f6:	push   0xd
    10fb:	jmp    1010 <_init+0x10>

0000000000001100 <memcmp@plt>:
    1100:	jmp    QWORD PTR [rip+0x5e7a]        # 6f80 <memcmp>
    1106:	push   0xe
    110b:	jmp    1010 <_init+0x10>

0000000000001110 <listen@plt>:
    1110:	jmp    QWORD PTR [rip+0x5e72]        # 6f88 <listen>
    1116:	push   0xf
    111b:	jmp    1010 <_init+0x10>

0000000000001120 <fork@plt>:
    1120:	jmp    QWORD PTR [rip+0x5e6a]        # 6f90 <fork>
    1126:	push   0x10
    112b:	jmp    1010 <_init+0x10>

0000000000001130 <__errno_location@plt>:
    1130:	jmp    QWORD PTR [rip+0x5e62]        # 6f98 <__errno_location>
    1136:	push   0x11
    113b:	jmp    1010 <_init+0x10>

0000000000001140 <getrandom@plt>:
    1140:	jmp    QWORD PTR [rip+0x5e5a]        # 6fa0 <getrandom>
    1146:	push   0x12
    114b:	jmp    1010 <_init+0x10>

0000000000001150 <_exit@plt>:
    1150:	jmp    QWORD PTR [rip+0x5e52]        # 6fa8 <_exit>
    1156:	push   0x13
    115b:	jmp    1010 <_init+0x10>

0000000000001160 <__libc_start_main@plt>:
    1160:	jmp    QWORD PTR [rip+0x5e4a]        # 6fb0 <__libc_start_main>
    1166:	push   0x14
    116b:	jmp    1010 <_init+0x10>

0000000000001170 <open@plt>:
    1170:	jmp    QWORD PTR [rip+0x5e42]        # 6fb8 <open>
    1176:	push   0x15
    117b:	jmp    1010 <_init+0x10>

0000000000001180 <setuid@plt>:
    1180:	jmp    QWORD PTR [rip+0x5e3a]        # 6fc0 <setuid>
    1186:	push   0x16
    118b:	jmp    1010 <_init+0x10>

0000000000001190 <close@plt>:
    1190:	jmp    QWORD PTR [rip+0x5e32]        # 6fc8 <close>
    1196:	push   0x17
    119b:	jmp    1010 <_init+0x10>

00000000000011a0 <free@plt>:
    11a0:	jmp    QWORD PTR [rip+0x5e2a]        # 6fd0 <free>
    11a6:	push   0x18
    11ab:	jmp    1010 <_init+0x10>

Disassembly of section .text:

00000000000011b0 <.text>:
    11b0:	push   rbx
    11b1:	mov    esi,0x1
    11b6:	mov    edi,0x11
    11bb:	add    rsp,0xffffffffffffff80
    11bf:	call   10d0 <signal@plt>
    11c4:	xor    edx,edx
    11c6:	mov    esi,0x1
    11cb:	mov    edi,0x1
    11d0:	call   1050 <socket@plt>
    11d5:	test   eax,eax
    11d7:	js     122b <free@plt+0x8b>
    11d9:	lea    rdi,[rip+0x3f60]        # 5140 <_fini+0xc2c>
    11e0:	mov    ebx,eax
    11e2:	call   10f0 <unlink@plt>
    11e7:	movdqa xmm0,XMMWORD PTR [rip+0x3f51]        # 5140 <_fini+0xc2c>
    11ef:	xor    eax,eax
    11f1:	mov    ecx,0x52
    11f6:	lea    rdi,[rsp+0x2c]
    11fb:	lea    rsi,[rsp+0x10]
    1200:	mov    edx,0x6e
    1205:	mov    WORD PTR [rsp+0x10],0x1
    120c:	rep stos BYTE PTR es:[rdi],al
    120e:	movups XMMWORD PTR [rsp+0x12],xmm0
    1213:	movdqu xmm0,XMMWORD PTR [rip+0x3f2f]        # 514a <_fini+0xc36>
    121b:	mov    edi,ebx
    121d:	movups XMMWORD PTR [rsp+0x1c],xmm0
    1222:	call   10b0 <bind@plt>
    1227:	test   eax,eax
    1229:	je     1236 <free@plt+0x96>
    122b:	sub    rsp,0xffffffffffffff80
    122f:	mov    eax,0x1
    1234:	pop    rbx
    1235:	ret
    1236:	mov    esi,0x1b6
    123b:	lea    rdi,[rip+0x3efe]        # 5140 <_fini+0xc2c>
    1242:	call   1060 <chmod@plt>
    1247:	test   eax,eax
    1249:	jne    122b <free@plt+0x8b>
    124b:	mov    esi,0x20
    1250:	mov    edi,ebx
    1252:	call   1110 <listen@plt>
    1257:	test   eax,eax
    1259:	jne    122b <free@plt+0x8b>
    125b:	mov    edi,0x3ea
    1260:	call   10c0 <setgid@plt>
    1265:	test   eax,eax
    1267:	jne    122b <free@plt+0x8b>
    1269:	mov    edi,0x3ea
    126e:	call   1180 <setuid@plt>
    1273:	test   eax,eax
    1275:	jne    122b <free@plt+0x8b>
    1277:	xor    edx,edx
    1279:	xor    esi,esi
    127b:	mov    edi,ebx
    127d:	call   1080 <accept@plt>
    1282:	test   eax,eax
    1284:	jns    1292 <free@plt+0xf2>
    1286:	call   1130 <__errno_location@plt>
    128b:	cmp    DWORD PTR [rax],0x4
    128e:	jne    122b <free@plt+0x8b>
    1290:	jmp    1277 <free@plt+0xd7>
    1292:	mov    DWORD PTR [rsp+0xc],eax
    1296:	call   1120 <fork@plt>
    129b:	test   eax,eax
    129d:	je     12aa <free@plt+0x10a>
    129f:	mov    edi,DWORD PTR [rsp+0xc]
    12a3:	call   1190 <close@plt>
    12a8:	jmp    1277 <free@plt+0xd7>
    12aa:	mov    edi,ebx
    12ac:	call   1190 <close@plt>
    12b1:	mov    edi,DWORD PTR [rsp+0xc]
    12b5:	call   1ab0 <free@plt+0x910>
    12ba:	xor    rbp,rbp
    12bd:	mov    rdi,rsp
    12c0:	lea    rsi,[rip+0x5a71]        # 6d38 <_fini+0x2824>
    12c7:	and    rsp,0xfffffffffffffff0
    12cb:	call   12d0 <free@plt+0x130>
    12d0:	mov    esi,DWORD PTR [rdi]
    12d2:	lea    rdx,[rdi+0x8]
    12d6:	lea    r8,[rip+0x3237]        # 4514 <_fini>
    12dd:	xor    r9d,r9d
    12e0:	lea    rcx,[rip+0xfffffffffffffd19]        # 1000 <_init>
    12e7:	lea    rdi,[rip+0xfffffffffffffec2]        # 11b0 <free@plt+0x10>
    12ee:	jmp    1160 <__libc_start_main@plt>
    12f3:	cs nop WORD PTR [rax+rax*1+0x0]
    12fd:	nop    DWORD PTR [rax]
    1300:	lea    rdi,[rip+0x5d01]        # 7008 <_fini+0x2af4>
    1307:	lea    rax,[rip+0x5cfa]        # 7008 <_fini+0x2af4>
    130e:	cmp    rax,rdi
    1311:	je     1328 <free@plt+0x188>
    1313:	mov    rax,QWORD PTR [rip+0x5cd6]        # 6ff0 <_ITM_deregisterTMCloneTable>
    131a:	test   rax,rax
    131d:	je     1328 <free@plt+0x188>
    131f:	jmp    rax
    1321:	nop    DWORD PTR [rax+0x0]
    1328:	ret
    1329:	nop    DWORD PTR [rax+0x0]
    1330:	lea    rdi,[rip+0x5cd1]        # 7008 <_fini+0x2af4>
    1337:	lea    rsi,[rip+0x5cca]        # 7008 <_fini+0x2af4>
    133e:	sub    rsi,rdi
    1341:	mov    rax,rsi
    1344:	shr    rsi,0x3f
    1348:	sar    rax,0x3
    134c:	add    rsi,rax
    134f:	sar    rsi,1
    1352:	je     1368 <free@plt+0x1c8>
    1354:	mov    rax,QWORD PTR [rip+0x5c8d]        # 6fe8 <_ITM_registerTMCloneTable>
    135b:	test   rax,rax
    135e:	je     1368 <free@plt+0x1c8>
    1360:	jmp    rax
    1362:	nop    WORD PTR [rax+rax*1+0x0]
    1368:	ret
    1369:	nop    DWORD PTR [rax+0x0]
    1370:	cmp    BYTE PTR [rip+0x5ca9],0x0        # 7020 <_fini+0x2b0c>
    1377:	jne    13c0 <free@plt+0x220>
    1379:	push   rbp
    137a:	cmp    QWORD PTR [rip+0x5c56],0x0        # 6fd8 <__cxa_finalize>
    1382:	mov    rbp,rsp
    1385:	je     1394 <free@plt+0x1f4>
    1387:	mov    rdi,QWORD PTR [rip+0x5c72]        # 7000 <_fini+0x2aec>
    138e:	call   QWORD PTR [rip+0x5c44]        # 6fd8 <__cxa_finalize>
    1394:	call   1300 <free@plt+0x160>
    1399:	cmp    QWORD PTR [rip+0x5c3f],0x0        # 6fe0 <__deregister_frame_info>
    13a1:	je     13b0 <free@plt+0x210>
    13a3:	lea    rdi,[rip+0x3ea6]        # 5250 <_fini+0xd3c>
    13aa:	call   QWORD PTR [rip+0x5c30]        # 6fe0 <__deregister_frame_info>
    13b0:	mov    BYTE PTR [rip+0x5c69],0x1        # 7020 <_fini+0x2b0c>
    13b7:	pop    rbp
    13b8:	ret
    13b9:	nop    DWORD PTR [rax+0x0]
    13c0:	ret
    13c1:	nop    DWORD PTR [rax+0x0]
    13c5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    13d0:	cmp    QWORD PTR [rip+0x5c20],0x0        # 6ff8 <__register_frame_info>
    13d8:	je     1400 <free@plt+0x260>
    13da:	push   rbp
    13db:	lea    rsi,[rip+0x5c5e]        # 7040 <_fini+0x2b2c>
    13e2:	lea    rdi,[rip+0x3e67]        # 5250 <_fini+0xd3c>
    13e9:	mov    rbp,rsp
    13ec:	call   QWORD PTR [rip+0x5c06]        # 6ff8 <__register_frame_info>
    13f2:	pop    rbp
    13f3:	jmp    1330 <free@plt+0x190>
    13f8:	nop    DWORD PTR [rax+rax*1+0x0]
    1400:	jmp    1330 <free@plt+0x190>
    1405:	cs nop WORD PTR [rax+rax*1+0x0]
    140f:	nop
    1410:	mov    rax,rdi
    1413:	push   r14
    1415:	mov    r11,rdi
    1418:	movabs r10,0xbf58476d1ce4e5b9
    1422:	push   r13
    1424:	xor    rax,rcx
    1427:	xor    edi,edi
    1429:	movabs r9,0x94d049bb133111eb
    1433:	push   r12
    1435:	mov    r12,rsi
    1438:	mov    rsi,rdx
    143b:	movabs rdx,0x9e3779b97f4a7c15
    1445:	xor    rax,rdx
    1448:	push   rbp
    1449:	lea    r13,[rsi+rcx*8]
    144d:	mov    r8,r12
    1450:	mov    rdx,rax
    1453:	push   rbx
    1454:	mov    ecx,0x11
    1459:	movabs rbp,0x517cc1b727220a95
    1463:	movabs rbx,0x6a09e667f3bcc909
    146d:	shr    rdx,0x1e
    1471:	xor    rdx,rax
    1474:	imul   rdx,r10
    1478:	mov    rax,rdx
    147b:	shr    rax,0x1b
    147f:	xor    rax,rdx
    1482:	imul   rax,r9
    1486:	mov    rdx,rax
    1489:	shr    rdx,0x1f
    148d:	xor    rdx,rax
    1490:	mov    r14,QWORD PTR [rsi]
    1493:	add    rsi,0x8
    1497:	add    r14,r8
    149a:	add    r8,rbp
    149d:	mov    rax,r14
    14a0:	shr    rax,0x1e
    14a4:	xor    rax,r14
    14a7:	imul   rax,r10
    14ab:	mov    r14,rax
    14ae:	shr    r14,0x1b
    14b2:	xor    rax,r14
    14b5:	imul   rax,r9
    14b9:	mov    r14,rax
    14bc:	shr    r14,0x1f
    14c0:	xor    rax,r14
    14c3:	xor    rax,rdx
    14c6:	mov    rdx,r11
    14c9:	rol    rax,cl
    14cc:	xor    rdx,rdi
    14cf:	add    ecx,0xb
    14d2:	add    rdi,rbx
    14d5:	add    rdx,rax
    14d8:	cmp    r13,rsi
    14db:	jne    1490 <free@plt+0x2f0>
    14dd:	movabs rax,0xa54ff53a5f1d36f1
    14e7:	xor    r12,rdx
    14ea:	pop    rbx
    14eb:	pop    rbp
    14ec:	xor    r12,rax
    14ef:	mov    rdx,r12
    14f2:	shr    rdx,0x1e
    14f6:	xor    rdx,r12
    14f9:	pop    r12
    14fb:	pop    r13
    14fd:	imul   rdx,r10
    1501:	pop    r14
    1503:	mov    rax,rdx
    1506:	shr    rax,0x1b
    150a:	xor    rdx,rax
    150d:	imul   rdx,r9
    1511:	mov    rax,rdx
    1514:	shr    rax,0x1f
    1518:	xor    rax,rdx
    151b:	ret
    151c:	nop    DWORD PTR [rax+0x0]
    1520:	sub    rsp,0x48
    1524:	mov    rax,QWORD PTR [rdi+0x30]
    1528:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    152d:	mov    ecx,0x7
    1532:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    1537:	movdqu xmm2,XMMWORD PTR [rdi]
    153b:	mov    rdx,rsp
    153e:	mov    QWORD PTR [rsp+0x30],rax
    1543:	mov    rax,QWORD PTR [rip+0x6156]        # 76a0 <_fini+0x318c>
    154a:	movaps XMMWORD PTR [rsp],xmm2
    154e:	mov    rsi,QWORD PTR [rax+0xd8]
    1555:	mov    rdi,QWORD PTR [rax+0xf0]
    155c:	movaps XMMWORD PTR [rsp+0x10],xmm1
    1561:	movaps XMMWORD PTR [rsp+0x20],xmm0
    1566:	call   1410 <free@plt+0x270>
    156b:	add    rsp,0x48
    156f:	ret
    1570:	sub    rsp,0x48
    1574:	mov    rax,QWORD PTR [rdi+0x30]
    1578:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    157d:	mov    ecx,0x7
    1582:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    1587:	movdqu xmm2,XMMWORD PTR [rdi]
    158b:	mov    rdx,rsp
    158e:	movabs rdi,0x243f6a8885a308d3
    1598:	mov    QWORD PTR [rsp+0x30],rax
    159d:	mov    rax,QWORD PTR [rip+0x60fc]        # 76a0 <_fini+0x318c>
    15a4:	movaps XMMWORD PTR [rsp],xmm2
    15a8:	mov    rsi,QWORD PTR [rax+0xd8]
    15af:	xor    rdi,QWORD PTR [rax+0xf0]
    15b6:	movaps XMMWORD PTR [rsp+0x10],xmm1
    15bb:	movaps XMMWORD PTR [rsp+0x20],xmm0
    15c0:	call   1410 <free@plt+0x270>
    15c5:	add    rsp,0x48
    15c9:	ret
    15ca:	nop    WORD PTR [rax+rax*1+0x0]
    15d0:	sub    rsp,0x48
    15d4:	mov    rax,QWORD PTR [rip+0x60c5]        # 76a0 <_fini+0x318c>
    15db:	movdqu xmm2,XMMWORD PTR [rdi+0x10]
    15e0:	mov    ecx,0x8
    15e5:	movdqu xmm1,XMMWORD PTR [rdi+0x20]
    15ea:	movdqu xmm0,XMMWORD PTR [rdi+0x30]
    15ef:	mov    rdx,rsp
    15f2:	movdqu xmm3,XMMWORD PTR [rdi]
    15f6:	mov    rsi,QWORD PTR [rax+0xe0]
    15fd:	movaps XMMWORD PTR [rsp+0x10],xmm2
    1602:	mov    rdi,QWORD PTR [rax+0xd8]
    1609:	movaps XMMWORD PTR [rsp+0x20],xmm1
    160e:	movaps XMMWORD PTR [rsp],xmm3
    1612:	movaps XMMWORD PTR [rsp+0x30],xmm0
    1617:	call   1410 <free@plt+0x270>
    161c:	add    rsp,0x48
    1620:	ret
    1621:	nop    DWORD PTR [rax+0x0]
    1625:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1630:	sub    rsp,0x48
    1634:	mov    rax,QWORD PTR [rdi+0x30]
    1638:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    163d:	mov    ecx,0x7
    1642:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    1647:	movdqu xmm2,XMMWORD PTR [rdi]
    164b:	mov    rdx,rsp
    164e:	movabs rdi,0x243f6a8885a308d3
    1658:	mov    QWORD PTR [rsp+0x30],rax
    165d:	mov    rax,QWORD PTR [rip+0x603c]        # 76a0 <_fini+0x318c>
    1664:	movaps XMMWORD PTR [rsp],xmm2
    1668:	mov    rsi,QWORD PTR [rax+0xe0]
    166f:	xor    rdi,QWORD PTR [rax+0xd8]
    1676:	movaps XMMWORD PTR [rsp+0x10],xmm1
    167b:	movaps XMMWORD PTR [rsp+0x20],xmm0
    1680:	call   1410 <free@plt+0x270>
    1685:	add    rsp,0x48
    1689:	ret
    168a:	nop    WORD PTR [rax+rax*1+0x0]
    1690:	sub    rsp,0x48
    1694:	mov    rax,QWORD PTR [rdi+0x30]
    1698:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    169d:	mov    ecx,0x7
    16a2:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    16a7:	movdqu xmm2,XMMWORD PTR [rdi]
    16ab:	mov    rdx,rsp
    16ae:	mov    QWORD PTR [rsp+0x30],rax
    16b3:	mov    rax,QWORD PTR [rip+0x5fe6]        # 76a0 <_fini+0x318c>
    16ba:	movaps XMMWORD PTR [rsp],xmm2
    16be:	mov    rsi,QWORD PTR [rax+0xd8]
    16c5:	mov    rdi,QWORD PTR [rax+0xe0]
    16cc:	movaps XMMWORD PTR [rsp+0x10],xmm1
    16d1:	movaps XMMWORD PTR [rsp+0x20],xmm0
    16d6:	call   1410 <free@plt+0x270>
    16db:	add    rsp,0x48
    16df:	ret
    16e0:	sub    rsp,0x48
    16e4:	mov    rax,QWORD PTR [rip+0x5fb5]        # 76a0 <_fini+0x318c>
    16eb:	movdqu xmm2,XMMWORD PTR [rdi+0x10]
    16f0:	mov    ecx,0x8
    16f5:	movdqu xmm1,XMMWORD PTR [rdi+0x20]
    16fa:	movdqu xmm0,XMMWORD PTR [rdi+0x30]
    16ff:	mov    rdx,rsp
    1702:	movdqu xmm3,XMMWORD PTR [rdi]
    1706:	mov    rsi,QWORD PTR [rax+0xe8]
    170d:	movaps XMMWORD PTR [rsp+0x10],xmm2
    1712:	movabs rdi,0x13198a2e03707344
    171c:	xor    rdi,QWORD PTR [rax+0xe0]
    1723:	movaps XMMWORD PTR [rsp+0x20],xmm1
    1728:	movaps XMMWORD PTR [rsp],xmm3
    172c:	movaps XMMWORD PTR [rsp+0x30],xmm0
    1731:	call   1410 <free@plt+0x270>
    1736:	add    rsp,0x48
    173a:	ret
    173b:	nop    DWORD PTR [rax+rax*1+0x0]
    1740:	sub    rsp,0x48
    1744:	mov    rax,QWORD PTR [rdi+0x30]
    1748:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    174d:	mov    ecx,0x7
    1752:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    1757:	movdqu xmm2,XMMWORD PTR [rdi]
    175b:	mov    rdx,rsp
    175e:	mov    QWORD PTR [rsp+0x30],rax
    1763:	mov    rax,QWORD PTR [rip+0x5f36]        # 76a0 <_fini+0x318c>
    176a:	movaps XMMWORD PTR [rsp],xmm2
    176e:	mov    rsi,QWORD PTR [rax+0xe0]
    1775:	mov    rdi,QWORD PTR [rax+0xe8]
    177c:	movaps XMMWORD PTR [rsp+0x10],xmm1
    1781:	movaps XMMWORD PTR [rsp+0x20],xmm0
    1786:	call   1410 <free@plt+0x270>
    178b:	add    rsp,0x48
    178f:	ret
    1790:	sub    rsp,0x48
    1794:	mov    rax,QWORD PTR [rdi+0x30]
    1798:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    179d:	mov    ecx,0x7
    17a2:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    17a7:	movdqu xmm2,XMMWORD PTR [rdi]
    17ab:	mov    rdx,rsp
    17ae:	movabs rdi,0x3c6ef372fe94f82b
    17b8:	mov    QWORD PTR [rsp+0x30],rax
    17bd:	mov    rax,QWORD PTR [rip+0x5edc]        # 76a0 <_fini+0x318c>
    17c4:	movaps XMMWORD PTR [rsp],xmm2
    17c8:	mov    rsi,QWORD PTR [rax+0xe0]
    17cf:	xor    rdi,QWORD PTR [rax+0xe8]
    17d6:	movaps XMMWORD PTR [rsp+0x10],xmm1
    17db:	movaps XMMWORD PTR [rsp+0x20],xmm0
    17e0:	call   1410 <free@plt+0x270>
    17e5:	add    rsp,0x48
    17e9:	ret
    17ea:	nop    WORD PTR [rax+rax*1+0x0]
    17f0:	sub    rsp,0x18
    17f4:	xor    rdi,QWORD PTR [rdi+0x8]
    17f8:	mov    QWORD PTR [rsp+0x8],rdi
    17fd:	mov    rax,QWORD PTR [rsp+0x8]
    1802:	cmp    rax,0xffffffffffffffff
    1806:	je     180d <free@plt+0x66d>
    1808:	add    rsp,0x18
    180c:	ret
    180d:	mov    edi,0x1
    1812:	call   1150 <_exit@plt>
    1817:	nop    WORD PTR [rax+rax*1+0x0]
    1820:	push   r14
    1822:	mov    ecx,0x1
    1827:	xor    r14d,r14d
    182a:	push   r13
    182c:	push   r12
    182e:	mov    r12,rdx
    1831:	push   rbp
    1832:	mov    rbp,rdi
    1835:	push   rbx
    1836:	sub    rsp,0x30
    183a:	mov    r13,QWORD PTR [rip+0x5e5f]        # 76a0 <_fini+0x318c>
    1841:	mov    QWORD PTR [rsp+0x8],rsi
    1846:	lea    rdx,[rsp+0x8]
    184b:	mov    rsi,rdi
    184e:	mov    rbx,QWORD PTR [r13+0xe8]
    1855:	mov    rdi,rbx
    1858:	xor    rbx,rbp
    185b:	lea    rbp,[rsp+0x10]
    1860:	call   1410 <free@plt+0x270>
    1865:	mov    r13,QWORD PTR [r13+0xd8]
    186c:	movq   xmm0,rax
    1871:	nop    DWORD PTR [rax+0x0]
    1875:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1880:	mov    ecx,0x3
    1885:	mov    rdx,rbp
    1888:	mov    rsi,r13
    188b:	mov    rdi,rbx
    188e:	movhps xmm0,QWORD PTR [r12+r14*1]
    1893:	mov    QWORD PTR [rsp+0x20],r14
    1898:	add    r14,0x8
    189c:	movaps XMMWORD PTR [rsp+0x10],xmm0
    18a1:	call   1410 <free@plt+0x270>
    18a6:	movq   xmm0,rax
    18ab:	cmp    r14,0x100
    18b2:	jne    1880 <free@plt+0x6e0>
    18b4:	add    rsp,0x30
    18b8:	pop    rbx
    18b9:	pop    rbp
    18ba:	pop    r12
    18bc:	pop    r13
    18be:	pop    r14
    18c0:	ret
    18c1:	nop    DWORD PTR [rax+0x0]
    18c5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    18d0:	movzx  eax,dil
    18d4:	push   rbp
    18d5:	mov    r10d,ecx
    18d8:	movzx  r11d,dl
    18dc:	shl    rax,0x20
    18e0:	push   rbx
    18e1:	movzx  ebx,sil
    18e5:	shl    r11,0x30
    18e9:	or     rax,0x34524c43
    18ef:	shl    rbx,0x28
    18f3:	xor    edx,edx
    18f5:	mov    rsi,r8
    18f8:	mov    rcx,rax
    18fb:	shl    r10,0x20
    18ff:	movabs rdi,0xffff00ffffffffff
    1909:	movabs r8,0xffffffff00000000
    1913:	and    rcx,rdi
    1916:	sub    rsp,0x118
    191d:	movabs rdi,0xff00ffffffffffff
    1927:	or     rcx,rbx
    192a:	and    rcx,rdi
    192d:	movabs rdi,0xffffffffffffff
    1937:	or     rcx,r11
    193a:	and    rcx,rdi
    193d:	mov    edi,r9d
    1940:	mov    rax,rcx
    1943:	mov    rcx,rdx
    1946:	and    rcx,r8
    1949:	mov    QWORD PTR [rsp],rax
    194d:	or     rcx,rdi
    1950:	mov    ecx,ecx
    1952:	or     rcx,r10
    1955:	mov    QWORD PTR [rsp+0x8],rcx
    195a:	test   r9d,r9d
    195d:	jne    19a0 <free@plt+0x800>
    195f:	lea    ebx,[r9+0x10]
    1963:	mov    rbp,rsp
    1966:	cs nop WORD PTR [rax+rax*1+0x0]
    1970:	mov    rdx,rbx
    1973:	mov    rsi,rbp
    1976:	mov    edi,0x1
    197b:	call   10a0 <write@plt>
    1980:	test   rax,rax
    1983:	jle    19d0 <free@plt+0x830>
    1985:	add    rbp,rax
    1988:	sub    rbx,rax
    198b:	jne    1970 <free@plt+0x7d0>
    198d:	add    rsp,0x118
    1994:	pop    rbx
    1995:	pop    rbp
    1996:	ret
    1997:	nop    WORD PTR [rax+rax*1+0x0]
    19a0:	mov    ecx,r9d
    19a3:	lea    rdi,[rsp+0x10]
    19a8:	xor    eax,eax
    19aa:	shr    ecx,0x3
    19ad:	rep movs QWORD PTR es:[rdi],QWORD PTR ds:[rsi]
    19b0:	test   r9b,0x4
    19b4:	jne    1a00 <free@plt+0x860>
    19b6:	test   r9b,0x2
    19ba:	jne    19e0 <free@plt+0x840>
    19bc:	test   r9b,0x1
    19c0:	je     195f <free@plt+0x7bf>
    19c2:	movzx  edx,BYTE PTR [rsi+rax*1]
    19c6:	mov    BYTE PTR [rdi+rax*1],dl
    19c9:	jmp    195f <free@plt+0x7bf>
    19cb:	nop    DWORD PTR [rax+rax*1+0x0]
    19d0:	xor    edi,edi
    19d2:	call   1150 <_exit@plt>
    19d7:	nop    WORD PTR [rax+rax*1+0x0]
    19e0:	movzx  edx,WORD PTR [rsi+rax*1]
    19e4:	mov    WORD PTR [rdi+rax*1],dx
    19e8:	add    rax,0x2
    19ec:	test   r9b,0x1
    19f0:	je     195f <free@plt+0x7bf>
    19f6:	jmp    19c2 <free@plt+0x822>
    19f8:	nop    DWORD PTR [rax+rax*1+0x0]
    1a00:	mov    eax,DWORD PTR [rsi]
    1a02:	mov    DWORD PTR [rdi],eax
    1a04:	mov    eax,0x4
    1a09:	test   r9b,0x2
    1a0d:	je     19bc <free@plt+0x81c>
    1a0f:	jmp    19e0 <free@plt+0x840>
    1a11:	nop    DWORD PTR [rax+0x0]
    1a15:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1a20:	push   rbp
    1a21:	mov    rbp,rdi
    1a24:	push   rbx
    1a25:	mov    rbx,rsi
    1a28:	sub    rsp,0x8
    1a2c:	nop    DWORD PTR [rax+0x0]
    1a30:	xor    edi,edi
    1a32:	mov    rdx,rbx
    1a35:	mov    rsi,rbp
    1a38:	call   10e0 <read@plt>
    1a3d:	test   rax,rax
    1a40:	jle    1a60 <free@plt+0x8c0>
    1a42:	add    rbp,rax
    1a45:	sub    rbx,rax
    1a48:	jne    1a30 <free@plt+0x890>
    1a4a:	add    rsp,0x8
    1a4e:	mov    eax,0x1
    1a53:	pop    rbx
    1a54:	pop    rbp
    1a55:	ret
    1a56:	cs nop WORD PTR [rax+rax*1+0x0]
    1a60:	add    rsp,0x8
    1a64:	xor    eax,eax
    1a66:	pop    rbx
    1a67:	pop    rbp
    1a68:	ret
    1a69:	nop    DWORD PTR [rax+0x0]
    1a70:	push   rbp
    1a71:	mov    rbp,rdi
    1a74:	push   rbx
    1a75:	mov    ebx,0x8
    1a7a:	sub    rsp,0x8
    1a7e:	xchg   ax,ax
    1a80:	xor    edx,edx
    1a82:	mov    rsi,rbx
    1a85:	mov    rdi,rbp
    1a88:	call   1140 <getrandom@plt>
    1a8d:	test   rax,rax
    1a90:	jle    1aa1 <free@plt+0x901>
    1a92:	add    rbp,rax
    1a95:	sub    rbx,rax
    1a98:	jne    1a80 <free@plt+0x8e0>
    1a9a:	add    rsp,0x8
    1a9e:	pop    rbx
    1a9f:	pop    rbp
    1aa0:	ret
    1aa1:	mov    edi,0x1
    1aa6:	call   1150 <_exit@plt>
    1aab:	nop    DWORD PTR [rax+rax*1+0x0]
    1ab0:	push   r15
    1ab2:	xor    esi,esi
    1ab4:	push   r14
    1ab6:	push   r13
    1ab8:	push   r12
    1aba:	push   rbp
    1abb:	push   rbx
    1abc:	mov    ebx,edi
    1abe:	sub    rsp,0x758
    1ac5:	call   1040 <dup2@plt>
    1aca:	test   eax,eax
    1acc:	js     1ade <free@plt+0x93e>
    1ace:	mov    esi,0x1
    1ad3:	mov    edi,ebx
    1ad5:	call   1040 <dup2@plt>
    1ada:	test   eax,eax
    1adc:	jns    1ae8 <free@plt+0x948>
    1ade:	mov    edi,0x1
    1ae3:	call   1150 <_exit@plt>
    1ae8:	mov    esi,0x2
    1aed:	mov    edi,ebx
    1aef:	call   1040 <dup2@plt>
    1af4:	test   eax,eax
    1af6:	js     1ade <free@plt+0x93e>
    1af8:	cmp    ebx,0x2
    1afb:	jg     1b3b <free@plt+0x99b>
    1afd:	mov    edi,0x1c20
    1b02:	call   1070 <alarm@plt>
    1b07:	mov    esi,0x10
    1b0c:	lea    rdi,[rsp+0x60]
    1b11:	call   1a20 <free@plt+0x880>
    1b16:	test   eax,eax
    1b18:	je     1b34 <free@plt+0x994>
    1b1a:	mov    edx,0x10
    1b1f:	lea    rsi,[rip+0x360a]        # 5130 <_fini+0xc1c>
    1b26:	lea    rdi,[rsp+0x60]
    1b2b:	call   1100 <memcmp@plt>
    1b30:	test   eax,eax
    1b32:	je     1b44 <free@plt+0x9a4>
    1b34:	xor    edi,edi
    1b36:	call   1150 <_exit@plt>
    1b3b:	mov    edi,ebx
    1b3d:	call   1190 <close@plt>
    1b42:	jmp    1afd <free@plt+0x95d>
    1b44:	mov    esi,0x80000
    1b49:	lea    rdi,[rip+0x34b0]        # 5000 <_fini+0xaec>
    1b50:	xor    eax,eax
    1b52:	call   1170 <open@plt>
    1b57:	mov    ebx,eax
    1b59:	test   eax,eax
    1b5b:	js     1ade <free@plt+0x93e>
    1b5d:	cmp    eax,0x7
    1b60:	je     1b7d <free@plt+0x9dd>
    1b62:	mov    esi,0x7
    1b67:	mov    edi,eax
    1b69:	call   1040 <dup2@plt>
    1b6e:	test   eax,eax
    1b70:	js     1ade <free@plt+0x93e>
    1b76:	mov    edi,ebx
    1b78:	call   1190 <close@plt>
    1b7d:	mov    esi,0xf8
    1b82:	mov    edi,0x1
    1b87:	call   1090 <calloc@plt>
    1b8c:	mov    QWORD PTR [rip+0x5b0d],rax        # 76a0 <_fini+0x318c>
    1b93:	test   rax,rax
    1b96:	je     1ade <free@plt+0x93e>
    1b9c:	mov    rdi,rax
    1b9f:	call   1a70 <free@plt+0x8d0>
    1ba4:	mov    ecx,0x2
    1ba9:	lea    rdx,[rsp+0x70]
    1bae:	mov    rbx,QWORD PTR [rip+0x5aeb]        # 76a0 <_fini+0x318c>
    1bb5:	movabs rsi,0x6a09e667f3bcc909
    1bbf:	mov    r14,QWORD PTR [rbx]
    1bc2:	movq   xmm0,rbx
    1bc7:	movhps xmm0,QWORD PTR [rip+0x5162]        # 6d30 <_fini+0x281c>
    1bce:	movups XMMWORD PTR [rbx+0x8],xmm0
    1bd2:	movaps XMMWORD PTR [rsp+0x70],xmm0
    1bd7:	mov    rdi,r14
    1bda:	call   1410 <free@plt+0x270>
    1bdf:	mov    ecx,0x2
    1be4:	lea    rdx,[rsp+0x70]
    1be9:	mov    rdi,r14
    1bec:	mov    QWORD PTR [rbx+0xd8],rax
    1bf3:	movabs rsi,0xbb67ae8584caa73b
    1bfd:	call   1410 <free@plt+0x270>
    1c02:	mov    ecx,0x2
    1c07:	lea    rdx,[rsp+0x70]
    1c0c:	mov    rdi,r14
    1c0f:	mov    QWORD PTR [rbx+0xe0],rax
    1c16:	movabs rsi,0x3c6ef372fe94f82b
    1c20:	call   1410 <free@plt+0x270>
    1c25:	mov    ecx,0x2
    1c2a:	lea    rdx,[rsp+0x70]
    1c2f:	mov    rdi,r14
    1c32:	mov    QWORD PTR [rbx+0xe8],rax
    1c39:	movabs rsi,0xa54ff53a5f1d36f1
    1c43:	call   1410 <free@plt+0x270>
    1c48:	xor    r8d,r8d
    1c4b:	xor    edx,edx
    1c4d:	mov    esi,0x1
    1c52:	mov    QWORD PTR [rbx+0xf0],rax
    1c59:	mov    eax,0x20000001
    1c5e:	mov    edi,0x26
    1c63:	movabs rcx,0x14201000015
    1c6d:	shl    rax,0x5
    1c71:	mov    QWORD PTR [rsp+0x100],rcx
    1c79:	movabs rcx,0x201000015
    1c83:	mov    QWORD PTR [rsp+0xd0],rax
    1c8b:	movabs rax,0xc000003e00010015
    1c95:	mov    QWORD PTR [rsp+0xd8],rax
    1c9d:	movabs rax,0x8000000000000006
    1ca7:	mov    QWORD PTR [rsp+0xe0],rax
    1caf:	movabs rax,0x3b01000015
    1cb9:	mov    QWORD PTR [rsp+0xf0],rax
    1cc1:	movabs rax,0x5000100000006
    1ccb:	mov    QWORD PTR [rsp+0xf8],rax
    1cd3:	mov    QWORD PTR [rsp+0x108],rax
    1cdb:	mov    QWORD PTR [rsp+0x110],rcx
    1ce3:	movabs rcx,0x10101000015
    1ced:	mov    QWORD PTR [rsp+0x118],rax
    1cf5:	mov    QWORD PTR [rsp+0x128],rax
    1cfd:	mov    QWORD PTR [rsp+0x138],rax
    1d05:	movabs rax,0x7fff000000000006
    1d0f:	mov    QWORD PTR [rsp+0x120],rcx
    1d17:	movabs rcx,0x1b501000015
    1d21:	mov    QWORD PTR [rsp+0x140],rax
    1d29:	lea    rax,[rsp+0xd0]
    1d31:	mov    QWORD PTR [rsp+0x130],rcx
    1d39:	mov    r13,rax
    1d3c:	xor    ecx,ecx
    1d3e:	mov    QWORD PTR [rsp+0xb8],rax
    1d46:	xor    eax,eax
    1d48:	mov    QWORD PTR [rsp+0xe8],0x20
    1d54:	mov    QWORD PTR [rsp+0xb0],0xf
    1d60:	call   1030 <prctl@plt>
    1d65:	test   eax,eax
    1d67:	jne    1ade <free@plt+0x93e>
    1d6d:	lea    rax,[rsp+0xb0]
    1d75:	xor    edx,edx
    1d77:	mov    esi,0x1
    1d7c:	mov    edi,0x13d
    1d81:	mov    QWORD PTR [rsp+0x10],rax
    1d86:	mov    rcx,rax
    1d89:	xor    eax,eax
    1d8b:	call   1020 <syscall@plt>
    1d90:	test   rax,rax
    1d93:	jne    1ade <free@plt+0x93e>
    1d99:	mov    r9d,0x9
    1d9f:	xor    ecx,ecx
    1da1:	xor    edx,edx
    1da3:	xor    esi,esi
    1da5:	lea    r8,[rip+0x336c]        # 5118 <_fini+0xc04>
    1dac:	mov    edi,0x70
    1db1:	lea    rbx,[rip+0x3268]        # 5020 <_fini+0xb0c>
    1db8:	call   18d0 <free@plt+0x730>
    1dbd:	mov    esi,0x10
    1dc2:	lea    rdi,[rsp+0x80]
    1dca:	call   1a20 <free@plt+0x880>
    1dcf:	mov    edx,eax
    1dd1:	test   eax,eax
    1dd3:	je     1b34 <free@plt+0x994>
    1dd9:	cmp    DWORD PTR [rsp+0x80],0x34564c43
    1de4:	jne    1b34 <free@plt+0x994>
    1dea:	cmp    BYTE PTR [rsp+0x87],0x0
    1df2:	jne    1b34 <free@plt+0x994>
    1df8:	mov    esi,DWORD PTR [rsp+0x88]
    1dff:	cmp    esi,0x600
    1e05:	ja     1b34 <free@plt+0x994>
    1e0b:	mov    r10d,DWORD PTR [rsp+0x8c]
    1e13:	cmp    DWORD PTR [rip+0x5266],r10d        # 7080 <_fini+0x2b6c>
    1e1a:	jae    1b34 <free@plt+0x994>
    1e20:	test   esi,esi
    1e22:	je     1e47 <free@plt+0xca7>
    1e24:	lea    rdi,[rsp+0x150]
    1e2c:	mov    DWORD PTR [rsp],eax
    1e2f:	call   1a20 <free@plt+0x880>
    1e34:	test   eax,eax
    1e36:	je     1b34 <free@plt+0x994>
    1e3c:	mov    r10d,DWORD PTR [rsp+0x8c]
    1e44:	mov    edx,DWORD PTR [rsp]
    1e47:	movzx  ecx,BYTE PTR [rsp+0x84]
    1e4f:	mov    DWORD PTR [rip+0x522a],r10d        # 7080 <_fini+0x2b6c>
    1e56:	movzx  r9d,BYTE PTR [rsp+0x85]
    1e5f:	movzx  r11d,BYTE PTR [rsp+0x86]
    1e68:	lea    eax,[rcx-0x1]
    1e6b:	cmp    al,0xc
    1e6d:	ja     28a3 <free@plt+0x1703>
    1e73:	movzx  eax,al
    1e76:	movsxd rax,DWORD PTR [rbx+rax*4]
    1e7a:	add    rax,rbx
    1e7d:	jmp    rax
    1e7f:	cmp    r9b,0x7
    1e83:	ja     1eab <free@plt+0xd0b>
    1e85:	movzx  edx,r9b
    1e89:	lea    rax,[rip+0x56d0]        # 7560 <_fini+0x304c>
    1e90:	mov    r8,QWORD PTR [rax+rdx*8]
    1e94:	test   r8,r8
    1e97:	je     1eab <free@plt+0xd0b>
    1e99:	lea    rax,[rip+0x5680]        # 7520 <_fini+0x300c>
    1ea0:	cmp    QWORD PTR [rax+rdx*8],0x0
    1ea5:	je     3f21 <free@plt+0x2d81>
    1eab:	movzx  esi,r9b
    1eaf:	movzx  edx,r11b
    1eb3:	xor    r9d,r9d
    1eb6:	xor    r8d,r8d
    1eb9:	mov    ecx,r10d
    1ebc:	mov    edi,0xe1
    1ec1:	call   18d0 <free@plt+0x730>
    1ec6:	jmp    1dbd <free@plt+0xc1d>
    1ecb:	cmp    r9b,0x7
    1ecf:	ja     1eab <free@plt+0xd0b>
    1ed1:	lea    rax,[rip+0x56c8]        # 75a0 <_fini+0x308c>
    1ed8:	movzx  edx,r9b
    1edc:	movzx  esi,r9b
    1ee0:	mov    rdi,QWORD PTR [rax+rdx*8]
    1ee4:	test   rdi,rdi
    1ee7:	je     1eab <free@plt+0xd0b>
    1ee9:	cmp    DWORD PTR [rsp+0x88],0x0
    1ef1:	jne    1eab <free@plt+0xd0b>
    1ef3:	mov    QWORD PTR [rsp+0x18],rdx
    1ef8:	xor    ebp,ebp
    1efa:	mov    DWORD PTR [rsp+0x8],esi
    1efe:	mov    DWORD PTR [rsp+0x20],r10d
    1f03:	mov    BYTE PTR [rsp],r11b
    1f07:	call   11a0 <free@plt>
    1f0c:	mov    rdx,QWORD PTR [rsp+0x18]
    1f11:	xor    r9d,r9d
    1f14:	xor    r8d,r8d
    1f17:	lea    rax,[rip+0x5682]        # 75a0 <_fini+0x308c>
    1f1e:	mov    ecx,DWORD PTR [rsp+0x20]
    1f22:	mov    esi,DWORD PTR [rsp+0x8]
    1f26:	mov    edi,0x8b
    1f2b:	mov    QWORD PTR [rax+rdx*8],rbp
    1f2f:	movzx  edx,BYTE PTR [rsp]
    1f33:	call   18d0 <free@plt+0x730>
    1f38:	jmp    1dbd <free@plt+0xc1d>
    1f3d:	cmp    r9b,0x7
    1f41:	ja     1eab <free@plt+0xd0b>
    1f47:	movzx  eax,r9b
    1f4b:	lea    rdx,[rip+0x560e]        # 7560 <_fini+0x304c>
    1f52:	movzx  esi,r9b
    1f56:	mov    r8,QWORD PTR [rdx+rax*8]
    1f5a:	test   r8,r8
    1f5d:	je     1eab <free@plt+0xd0b>
    1f63:	cmp    DWORD PTR [rsp+0x88],0x0
    1f6b:	jne    1eab <free@plt+0xd0b>
    1f71:	movzx  edx,r11b
    1f75:	mov    r9d,0x40
    1f7b:	mov    ecx,r10d
    1f7e:	mov    edi,0x8a
    1f83:	call   18d0 <free@plt+0x730>
    1f88:	jmp    1dbd <free@plt+0xc1d>
    1f8d:	mov    eax,r9d
    1f90:	or     eax,r11d
    1f93:	cmp    al,0x7
    1f95:	ja     1eab <free@plt+0xd0b>
    1f9b:	movzx  eax,r9b
    1f9f:	lea    rdx,[rip+0x55fa]        # 75a0 <_fini+0x308c>
    1fa6:	movzx  esi,r9b
    1faa:	mov    rax,QWORD PTR [rdx+rax*8]
    1fae:	test   rax,rax
    1fb1:	je     1eab <free@plt+0xd0b>
    1fb7:	lea    rdx,[rip+0x55a2]        # 7560 <_fini+0x304c>
    1fbe:	movzx  ecx,r11b
    1fc2:	cmp    QWORD PTR [rdx+rcx*8],0x0
    1fc7:	jne    1eab <free@plt+0xd0b>
    1fcd:	cmp    DWORD PTR [rsp+0x88],0x0
    1fd5:	jne    1eab <free@plt+0xd0b>
    1fdb:	mov    QWORD PTR [rdx+rcx*8],rax
    1fdf:	xor    r9d,r9d
    1fe2:	xor    r8d,r8d
    1fe5:	mov    ecx,r10d
    1fe8:	movzx  edx,r11b
    1fec:	mov    edi,0x89
    1ff1:	call   18d0 <free@plt+0x730>
    1ff6:	jmp    1dbd <free@plt+0xc1d>
    1ffb:	cmp    r9b,0x7
    1fff:	ja     1eab <free@plt+0xd0b>
    2005:	movzx  r8d,r9b
    2009:	lea    rax,[rip+0x5590]        # 75a0 <_fini+0x308c>
    2010:	movzx  r15d,r9b
    2014:	cmp    QWORD PTR [rax+r8*8],0x0
    2019:	jne    1eab <free@plt+0xd0b>
    201f:	cmp    DWORD PTR [rsp+0x88],0x1
    2027:	jne    1eab <free@plt+0xd0b>
    202d:	movzx  ecx,BYTE PTR [rsp+0x150]
    2035:	cmp    cl,0x2
    2038:	ja     1eab <free@plt+0xd0b>
    203e:	mov    esi,0xd0
    2043:	mov    edi,0x1
    2048:	mov    DWORD PTR [rsp+0x8],r10d
    204d:	mov    BYTE PTR [rsp],r11b
    2051:	mov    BYTE PTR [rsp+0x18],cl
    2055:	mov    QWORD PTR [rsp+0x20],r8
    205a:	call   1090 <calloc@plt>
    205f:	mov    rdx,rax
    2062:	test   rax,rax
    2065:	je     1ade <free@plt+0x93e>
    206b:	mov    r10d,DWORD PTR [rsp+0x8]
    2070:	movzx  ecx,BYTE PTR [rsp+0x18]
    2075:	lea    rdi,[rdx+0x10]
    2079:	movabs rax,0x3454504345524d56
    2083:	mov    rbp,QWORD PTR [rsp+0x20]
    2088:	movzx  r14d,BYTE PTR [rsp]
    208d:	mov    QWORD PTR [rdx],rax
    2090:	mov    DWORD PTR [rsp+0x18],r10d
    2095:	mov    QWORD PTR [rsp+0x20],rdx
    209a:	mov    QWORD PTR [rdx+0x8],rcx
    209e:	mov    ecx,0x8
    20a3:	xor    edx,edx
    20a5:	mov    rsi,rcx
    20a8:	mov    QWORD PTR [rsp+0x8],rcx
    20ad:	mov    QWORD PTR [rsp],rdi
    20b1:	call   1140 <getrandom@plt>
    20b6:	test   rax,rax
    20b9:	jle    1ade <free@plt+0x93e>
    20bf:	mov    rdi,QWORD PTR [rsp]
    20c3:	mov    rcx,QWORD PTR [rsp+0x8]
    20c8:	add    rdi,rax
    20cb:	sub    rcx,rax
    20ce:	jne    20a3 <free@plt+0xf03>
    20d0:	mov    rdx,QWORD PTR [rsp+0x20]
    20d5:	mov    r10d,DWORD PTR [rsp+0x18]
    20da:	mov    BYTE PTR [rsp+0x30],r14b
    20df:	mov    rax,QWORD PTR [rip+0x55ba]        # 76a0 <_fini+0x318c>
    20e6:	mov    QWORD PTR [rsp+0x28],rbp
    20eb:	mov    rdi,rdx
    20ee:	mov    QWORD PTR [rsp],rdx
    20f2:	mov    rcx,QWORD PTR [rax+0xd8]
    20f9:	mov    QWORD PTR [rdx+0x30],0x1
    2101:	mov    DWORD PTR [rsp+0x8],r10d
    2106:	xor    rcx,rdx
    2109:	mov    QWORD PTR [rdx+0x18],rcx
    210d:	call   1570 <free@plt+0x3d0>
    2112:	mov    rdx,QWORD PTR [rsp]
    2116:	mov    ecx,DWORD PTR [rsp+0x8]
    211a:	xor    r9d,r9d
    211d:	xor    r8d,r8d
    2120:	mov    esi,r15d
    2123:	mov    edi,0x88
    2128:	mov    QWORD PTR [rdx+0x38],rax
    212c:	lea    rax,[rip+0x546d]        # 75a0 <_fini+0x308c>
    2133:	mov    QWORD PTR [rax+rbp*8],rdx
    2137:	movzx  edx,r14b
    213b:	call   18d0 <free@plt+0x730>
    2140:	jmp    1dbd <free@plt+0xc1d>
    2145:	cmp    r9b,0x7
    2149:	ja     1eab <free@plt+0xd0b>
    214f:	movzx  edx,r9b
    2153:	lea    rax,[rip+0x54c6]        # 7620 <_fini+0x310c>
    215a:	mov    r8,QWORD PTR [rax+rdx*8]
    215e:	test   r8,r8
    2161:	je     1eab <free@plt+0xd0b>
    2167:	lea    rax,[rip+0x5472]        # 75e0 <_fini+0x30cc>
    216e:	cmp    QWORD PTR [rax+rdx*8],0x0
    2173:	jne    1eab <free@plt+0xd0b>
    2179:	cmp    DWORD PTR [rsp+0x88],0xa0
    2184:	jne    1eab <free@plt+0xd0b>
    218a:	mov    rdi,r8
    218d:	lea    rsi,[rsp+0x150]
    2195:	mov    ecx,0x28
    219a:	rep movs DWORD PTR es:[rdi],DWORD PTR ds:[rsi]
    219c:	lea    rax,[rip+0x543d]        # 75e0 <_fini+0x30cc>
    21a3:	movzx  esi,r9b
    21a7:	mov    ecx,r10d
    21aa:	mov    QWORD PTR [rax+rdx*8],r8
    21ae:	xor    r9d,r9d
    21b1:	movzx  edx,r11b
    21b5:	xor    r8d,r8d
    21b8:	mov    edi,0x87
    21bd:	call   18d0 <free@plt+0x730>
    21c2:	jmp    1dbd <free@plt+0xc1d>
    21c7:	cmp    r9b,0x7
    21cb:	ja     1eab <free@plt+0xd0b>
    21d1:	lea    rax,[rip+0x5488]        # 7660 <_fini+0x314c>
    21d8:	movzx  edx,r9b
    21dc:	movzx  esi,r9b
    21e0:	mov    rdi,QWORD PTR [rax+rdx*8]
    21e4:	test   rdi,rdi
    21e7:	je     1eab <free@plt+0xd0b>
    21ed:	cmp    DWORD PTR [rsp+0x88],0x0
    21f5:	jne    1eab <free@plt+0xd0b>
    21fb:	mov    QWORD PTR [rsp+0x18],rdx
    2200:	xor    r12d,r12d
    2203:	mov    DWORD PTR [rsp+0x8],esi
    2207:	mov    DWORD PTR [rsp+0x20],r10d
    220c:	mov    BYTE PTR [rsp],r11b
    2210:	call   11a0 <free@plt>
    2215:	mov    rdx,QWORD PTR [rsp+0x18]
    221a:	xor    r9d,r9d
    221d:	xor    r8d,r8d
    2220:	lea    rax,[rip+0x5439]        # 7660 <_fini+0x314c>
    2227:	mov    ecx,DWORD PTR [rsp+0x20]
    222b:	mov    esi,DWORD PTR [rsp+0x8]
    222f:	mov    edi,0x86
    2234:	mov    QWORD PTR [rax+rdx*8],r12
    2238:	movzx  edx,BYTE PTR [rsp]
    223c:	call   18d0 <free@plt+0x730>
    2241:	jmp    1dbd <free@plt+0xc1d>
    2246:	cmp    r9b,0x7
    224a:	ja     1eab <free@plt+0xd0b>
    2250:	movzx  eax,r9b
    2254:	lea    rdx,[rip+0x53c5]        # 7620 <_fini+0x310c>
    225b:	movzx  esi,r9b
    225f:	mov    r8,QWORD PTR [rdx+rax*8]
    2263:	test   r8,r8
    2266:	je     1eab <free@plt+0xd0b>
    226c:	cmp    DWORD PTR [rsp+0x88],0x0
    2274:	jne    1eab <free@plt+0xd0b>
    227a:	movzx  edx,r11b
    227e:	mov    r9d,0x40
    2284:	mov    ecx,r10d
    2287:	mov    edi,0x85
    228c:	call   18d0 <free@plt+0x730>
    2291:	jmp    1dbd <free@plt+0xc1d>
    2296:	mov    eax,r9d
    2299:	or     eax,r11d
    229c:	cmp    al,0x7
    229e:	ja     1eab <free@plt+0xd0b>
    22a4:	movzx  eax,r9b
    22a8:	lea    rdx,[rip+0x53b1]        # 7660 <_fini+0x314c>
    22af:	movzx  esi,r9b
    22b3:	mov    rax,QWORD PTR [rdx+rax*8]
    22b7:	test   rax,rax
    22ba:	je     1eab <free@plt+0xd0b>
    22c0:	lea    rdx,[rip+0x5359]        # 7620 <_fini+0x310c>
    22c7:	movzx  ecx,r11b
    22cb:	cmp    QWORD PTR [rdx+rcx*8],0x0
    22d0:	jne    1eab <free@plt+0xd0b>
    22d6:	cmp    DWORD PTR [rsp+0x88],0x0
    22de:	jne    1eab <free@plt+0xd0b>
    22e4:	mov    QWORD PTR [rdx+rcx*8],rax
    22e8:	xor    r9d,r9d
    22eb:	xor    r8d,r8d
    22ee:	mov    ecx,r10d
    22f1:	movzx  edx,r11b
    22f5:	mov    edi,0x84
    22fa:	call   18d0 <free@plt+0x730>
    22ff:	jmp    1dbd <free@plt+0xc1d>
    2304:	cmp    r9b,0x7
    2308:	ja     1eab <free@plt+0xd0b>
    230e:	movzx  r8d,r9b
    2312:	lea    rax,[rip+0x5347]        # 7660 <_fini+0x314c>
    2319:	movzx  r15d,r9b
    231d:	cmp    QWORD PTR [rax+r8*8],0x0
    2322:	jne    1eab <free@plt+0xd0b>
    2328:	cmp    DWORD PTR [rsp+0x88],0x1
    2330:	jne    1eab <free@plt+0xd0b>
    2336:	movzx  ecx,BYTE PTR [rsp+0x150]
    233e:	cmp    cl,0x2
    2341:	ja     1eab <free@plt+0xd0b>
    2347:	mov    esi,0xa0
    234c:	mov    edi,0x1
    2351:	mov    DWORD PTR [rsp+0x8],r10d
    2356:	mov    BYTE PTR [rsp],r11b
    235a:	mov    BYTE PTR [rsp+0x18],cl
    235e:	mov    QWORD PTR [rsp+0x20],r8
    2363:	call   1090 <calloc@plt>
    2368:	mov    rdx,rax
    236b:	test   rax,rax
    236e:	je     1ade <free@plt+0x93e>
    2374:	mov    r10d,DWORD PTR [rsp+0x8]
    2379:	movzx  ecx,BYTE PTR [rsp+0x18]
    237e:	lea    rdi,[rdx+0x10]
    2382:	movabs rax,0x344e454b4f544d56
    238c:	mov    rbp,QWORD PTR [rsp+0x20]
    2391:	movzx  r14d,BYTE PTR [rsp]
    2396:	mov    QWORD PTR [rdx],rax
    2399:	mov    DWORD PTR [rsp+0x18],r10d
    239e:	mov    QWORD PTR [rsp+0x20],rdx
    23a3:	mov    QWORD PTR [rdx+0x8],rcx
    23a7:	mov    ecx,0x8
    23ac:	xor    edx,edx
    23ae:	mov    rsi,rcx
    23b1:	mov    QWORD PTR [rsp+0x8],rcx
    23b6:	mov    QWORD PTR [rsp],rdi
    23ba:	call   1140 <getrandom@plt>
    23bf:	test   rax,rax
    23c2:	jle    1ade <free@plt+0x93e>
    23c8:	mov    rdi,QWORD PTR [rsp]
    23cc:	mov    rcx,QWORD PTR [rsp+0x8]
    23d1:	add    rdi,rax
    23d4:	sub    rcx,rax
    23d7:	jne    23ac <free@plt+0x120c>
    23d9:	mov    rdx,QWORD PTR [rsp+0x20]
    23de:	mov    r10d,DWORD PTR [rsp+0x18]
    23e3:	mov    BYTE PTR [rsp+0x30],r14b
    23e8:	mov    rax,QWORD PTR [rip+0x52b1]        # 76a0 <_fini+0x318c>
    23ef:	mov    QWORD PTR [rsp+0x28],rbp
    23f4:	mov    rdi,rdx
    23f7:	mov    QWORD PTR [rsp],rdx
    23fb:	mov    rcx,QWORD PTR [rax+0xd8]
    2402:	mov    QWORD PTR [rdx+0x30],0x1
    240a:	mov    DWORD PTR [rsp+0x8],r10d
    240f:	xor    rcx,rdx
    2412:	mov    QWORD PTR [rdx+0x18],rcx
    2416:	call   1520 <free@plt+0x380>
    241b:	mov    rdx,QWORD PTR [rsp]
    241f:	mov    ecx,DWORD PTR [rsp+0x8]
    2423:	xor    r9d,r9d
    2426:	xor    r8d,r8d
    2429:	mov    esi,r15d
    242c:	mov    edi,0x83
    2431:	mov    QWORD PTR [rdx+0x38],rax
    2435:	lea    rax,[rip+0x5224]        # 7660 <_fini+0x314c>
    243c:	mov    QWORD PTR [rax+rbp*8],rdx
    2440:	movzx  edx,r14b
    2444:	call   18d0 <free@plt+0x730>
    2449:	jmp    1dbd <free@plt+0xc1d>
    244e:	cmp    DWORD PTR [rsp+0x88],0x8
    2456:	jne    1eab <free@plt+0xd0b>
    245c:	mov    rax,QWORD PTR [rip+0x523d]        # 76a0 <_fini+0x318c>
    2463:	mov    DWORD PTR [rsp],r10d
    2467:	movzx  r14d,r11b
    246b:	movzx  r15d,r9b
    246f:	movabs rcx,0x243f6a8885a308d3
    2479:	mov    rdx,QWORD PTR [rax+0x10]
    247d:	mov    QWORD PTR [rsp+0xd8],rcx
    2485:	mov    ecx,0x2
    248a:	mov    QWORD PTR [rsp+0xd0],rdx
    2492:	mov    rsi,QWORD PTR [rax+0x8]
    2496:	mov    rdx,r13
    2499:	mov    rdi,QWORD PTR [rax]
    249c:	call   1410 <free@plt+0x270>
    24a1:	cmp    QWORD PTR [rsp+0x150],rax
    24a9:	je     3f6f <free@plt+0x2dcf>
    24af:	mov    ecx,DWORD PTR [rsp]
    24b2:	xor    r9d,r9d
    24b5:	xor    r8d,r8d
    24b8:	mov    edx,r14d
    24bb:	mov    esi,r15d
    24be:	mov    edi,0xe3
    24c3:	call   18d0 <free@plt+0x730>
    24c8:	jmp    1dbd <free@plt+0xc1d>
    24cd:	mov    eax,r9d
    24d0:	or     eax,r11d
    24d3:	cmp    al,0x7
    24d5:	ja     1eab <free@plt+0xd0b>
    24db:	movzx  eax,r9b
    24df:	lea    rdx,[rip+0x517a]        # 7660 <_fini+0x314c>
    24e6:	movzx  esi,r9b
    24ea:	mov    rdx,QWORD PTR [rdx+rax*8]
    24ee:	test   rdx,rdx
    24f1:	je     1eab <free@plt+0xd0b>
    24f7:	movzx  eax,r11b
    24fb:	lea    rcx,[rip+0x509e]        # 75a0 <_fini+0x308c>
    2502:	movzx  r14d,r11b
    2506:	mov    rcx,QWORD PTR [rcx+rax*8]
    250a:	test   rcx,rcx
    250d:	je     1eab <free@plt+0xd0b>
    2513:	cmp    DWORD PTR [rsp+0x88],0x0
    251b:	jne    1eab <free@plt+0xd0b>
    2521:	mov    rax,QWORD PTR [rcx+0x8]
    2525:	cmp    QWORD PTR [rdx+0x8],rax
    2529:	jne    1eab <free@plt+0xd0b>
    252f:	mov    rax,QWORD PTR [rcx+0x10]
    2533:	mov    DWORD PTR [rsp+0x18],esi
    2537:	mov    DWORD PTR [rsp+0x20],r10d
    253c:	mov    QWORD PTR [rdx+0x20],rax
    2540:	mov    rax,QWORD PTR [rip+0x5159]        # 76a0 <_fini+0x318c>
    2547:	mov    QWORD PTR [rsp+0x8],rcx
    254c:	mov    rdi,QWORD PTR [rax+0xd8]
    2553:	mov    QWORD PTR [rsp],rdx
    2557:	xor    rdi,rcx
    255a:	mov    QWORD PTR [rdx+0x28],rdi
    255e:	mov    rdi,QWORD PTR [rdx+0x10]
    2562:	mov    QWORD PTR [rcx+0x20],rdi
    2566:	mov    rsi,QWORD PTR [rax+0xd8]
    256d:	mov    rdi,rdx
    2570:	xor    rsi,rdx
    2573:	mov    QWORD PTR [rcx+0x28],rsi
    2577:	call   1520 <free@plt+0x380>
    257c:	mov    rdx,QWORD PTR [rsp]
    2580:	mov    rcx,QWORD PTR [rsp+0x8]
    2585:	mov    QWORD PTR [rdx+0x38],rax
    2589:	mov    rdi,rcx
    258c:	mov    QWORD PTR [rsp],rcx
    2590:	call   1570 <free@plt+0x3d0>
    2595:	mov    rcx,QWORD PTR [rsp]
    2599:	mov    esi,DWORD PTR [rsp+0x18]
    259d:	xor    r9d,r9d
    25a0:	xor    r8d,r8d
    25a3:	mov    edx,r14d
    25a6:	mov    edi,0x8d
    25ab:	mov    QWORD PTR [rcx+0x38],rax
    25af:	mov    ecx,DWORD PTR [rsp+0x20]
    25b3:	call   18d0 <free@plt+0x730>
    25b8:	jmp    1dbd <free@plt+0xc1d>
    25bd:	mov    eax,r9d
    25c0:	or     eax,r11d
    25c3:	cmp    al,0x7
    25c5:	ja     1eab <free@plt+0xd0b>
    25cb:	movzx  eax,r9b
    25cf:	lea    rcx,[rip+0x500a]        # 75e0 <_fini+0x30cc>
    25d6:	mov    DWORD PTR [rsp+0x18],eax
    25da:	movzx  eax,r9b
    25de:	cmp    QWORD PTR [rcx+rax*8],0x0
    25e3:	je     1eab <free@plt+0xd0b>
    25e9:	movzx  ecx,r11b
    25ed:	movzx  edi,r11b
    25f1:	mov    DWORD PTR [rsp+0x20],ecx
    25f5:	lea    rcx,[rip+0x4f24]        # 7520 <_fini+0x300c>
    25fc:	cmp    QWORD PTR [rcx+rdi*8],0x0
    2601:	je     1eab <free@plt+0xd0b>
    2607:	mov    esi,DWORD PTR [rsp+0x88]
    260e:	lea    ecx,[rsi-0x1]
    2611:	cmp    ecx,0x10e
    2617:	ja     1eab <free@plt+0xd0b>
    261d:	mov    ecx,esi
    261f:	and    ecx,0xf
    2622:	mov    DWORD PTR [rsp+0x8],ecx
    2626:	jne    1eab <free@plt+0xd0b>
    262c:	lea    rcx,[rip+0x4fed]        # 7620 <_fini+0x310c>
    2633:	mov    rcx,QWORD PTR [rcx+rax*8]
    2637:	lea    rax,[rip+0x4f22]        # 7560 <_fini+0x304c>
    263e:	mov    rax,QWORD PTR [rax+rdi*8]
    2642:	mov    rbp,rax
    2645:	test   rcx,rcx
    2648:	je     1eab <free@plt+0xd0b>
    264e:	test   rax,rax
    2651:	je     1eab <free@plt+0xd0b>
    2657:	movabs rax,0x344e454b4f544d56
    2661:	cmp    QWORD PTR [rcx],rax
    2664:	jne    1eab <free@plt+0xd0b>
    266a:	movabs rax,0x3454504345524d56
    2674:	cmp    QWORD PTR [rbp+0x0],rax
    2678:	jne    1eab <free@plt+0xd0b>
    267e:	mov    rax,QWORD PTR [rcx+0x8]
    2682:	mov    QWORD PTR [rsp+0x30],rax
    2687:	cmp    rax,0x2
    268b:	ja     1eab <free@plt+0xd0b>
    2691:	cmp    rax,QWORD PTR [rbp+0x8]
    2695:	jne    1eab <free@plt+0xd0b>
    269b:	cmp    QWORD PTR [rcx+0x30],0x1
    26a0:	jne    1eab <free@plt+0xd0b>
    26a6:	cmp    QWORD PTR [rbp+0x30],0x1
    26ab:	jne    1eab <free@plt+0xd0b>
    26b1:	mov    rax,QWORD PTR [rip+0x4fe8]        # 76a0 <_fini+0x318c>
    26b8:	mov    rdi,rcx
    26bb:	mov    QWORD PTR [rsp+0x38],rax
    26c0:	mov    rax,QWORD PTR [rax+0xd8]
    26c7:	xor    rdi,rax
    26ca:	cmp    QWORD PTR [rcx+0x18],rdi
    26ce:	jne    1eab <free@plt+0xd0b>
    26d4:	xor    rax,rbp
    26d7:	cmp    QWORD PTR [rbp+0x18],rax
    26db:	jne    1eab <free@plt+0xd0b>
    26e1:	mov    r14,QWORD PTR [rbp+0x10]
    26e5:	cmp    QWORD PTR [rcx+0x20],r14
    26e9:	jne    1eab <free@plt+0xd0b>
    26ef:	mov    r15,QWORD PTR [rcx+0x10]
    26f3:	cmp    QWORD PTR [rbp+0x20],r15
    26f7:	jne    1eab <free@plt+0xd0b>
    26fd:	cmp    rax,QWORD PTR [rcx+0x28]
    2701:	jne    1eab <free@plt+0xd0b>
    2707:	cmp    rdi,QWORD PTR [rbp+0x28]
    270b:	jne    1eab <free@plt+0xd0b>
    2711:	mov    r14,QWORD PTR [rcx+0x38]
    2715:	mov    rdi,rcx
    2718:	mov    DWORD PTR [rsp+0x54],r10d
    271d:	mov    DWORD PTR [rsp+0x48],esi
    2721:	mov    BYTE PTR [rsp+0x40],r11b
    2726:	mov    BYTE PTR [rsp+0x28],r9b
    272b:	mov    QWORD PTR [rsp],rcx
    272f:	mov    DWORD PTR [rsp+0x58],edx
    2733:	call   1520 <free@plt+0x380>
    2738:	mov    rcx,QWORD PTR [rsp]
    273c:	movzx  r9d,BYTE PTR [rsp+0x28]
    2742:	cmp    r14,rax
    2745:	movzx  r11d,BYTE PTR [rsp+0x40]
    274b:	mov    esi,DWORD PTR [rsp+0x48]
    274f:	mov    r10d,DWORD PTR [rsp+0x54]
    2754:	jne    1eab <free@plt+0xd0b>
    275a:	mov    r14,QWORD PTR [rbp+0x38]
    275e:	mov    rdi,rbp
    2761:	mov    QWORD PTR [rsp+0x48],rcx
    2766:	mov    BYTE PTR [rsp+0x28],r11b
    276b:	mov    BYTE PTR [rsp],r9b
    276f:	mov    DWORD PTR [rsp+0x40],esi
    2773:	call   1570 <free@plt+0x3d0>
    2778:	movzx  r9d,BYTE PTR [rsp]
    277d:	movzx  r11d,BYTE PTR [rsp+0x28]
    2783:	cmp    r14,rax
    2786:	mov    rcx,QWORD PTR [rsp+0x48]
    278b:	mov    r10d,DWORD PTR [rsp+0x54]
    2790:	mov    edx,DWORD PTR [rsp+0x58]
    2794:	jne    1eab <free@plt+0xd0b>
    279a:	mov    eax,DWORD PTR [rsp+0x40]
    279e:	mov    r14d,DWORD PTR [rsp+0x30]
    27a3:	mov    BYTE PTR [rsp],0x0
    27a7:	mov    r15d,r10d
    27aa:	xor    esi,esi
    27ac:	mov    r10d,r9d
    27af:	xor    edi,edi
    27b1:	mov    r9d,edx
    27b4:	shr    eax,0x4
    27b7:	sub    r14d,0x3
    27bb:	mov    QWORD PTR [rsp+0x28],rax
    27c0:	lea    rax,[rsp+0x150]
    27c8:	mov    QWORD PTR [rsp+0x30],rax
    27cd:	mov    r8,rax
    27d0:	mov    eax,0x6d
    27d5:	movzx  edx,WORD PTR [r8]
    27d9:	mul    dil
    27dc:	rol    dx,0x8
    27e0:	xor    edx,eax
    27e2:	xor    dx,0x4b27
    27e7:	cmp    WORD PTR [r8+0x2],dx
    27ec:	jne    4062 <free@plt+0x2ec2>
    27f2:	or     esi,DWORD PTR [r8+0x4]
    27f6:	jne    4057 <free@plt+0x2eb7>
    27fc:	movzx  eax,BYTE PTR [r8]
    2800:	cmp    al,0x67
    2802:	je     2824 <free@plt+0x1684>
    2804:	ja     3f97 <free@plt+0x2df7>
    280a:	cmp    al,0x41
    280c:	je     3fc6 <free@plt+0x2e26>
    2812:	cmp    al,0x53
    2814:	jne    400b <free@plt+0x2e6b>
    281a:	cmp    BYTE PTR [rsp],0x17
    281e:	jg     406d <free@plt+0x2ecd>
    2824:	xor    esi,esi
    2826:	add    rdi,0x1
    282a:	add    r8,0x10
    282e:	cmp    rdi,QWORD PTR [rsp+0x28]
    2833:	jb     27d0 <free@plt+0x1630>
    2835:	mov    r9d,r10d
    2838:	mov    rax,QWORD PTR [rsp+0x30]
    283d:	mov    r10d,r15d
    2840:	cmp    DWORD PTR [rsp+0x8],0x1
    2845:	jne    1eab <free@plt+0xd0b>
    284b:	and    sil,0x1
    284f:	je     1eab <free@plt+0xd0b>
    2855:	mov    r8,QWORD PTR [rsp+0x28]
    285a:	xor    esi,esi
    285c:	xor    r11d,r11d
    285f:	xor    edx,edx
    2861:	jmp    2892 <free@plt+0x16f2>
    2863:	cmp    dil,0x53
    2867:	je     3fab <free@plt+0x2e0b>
    286d:	cmp    dil,0x67
    2871:	je     3fbd <free@plt+0x2e1d>
    2877:	cmp    dil,0x8b
    287b:	je     4016 <free@plt+0x2e76>
    2881:	add    rdx,0x1
    2885:	add    rax,0x10
    2889:	cmp    rdx,r8
    288c:	jae    4016 <free@plt+0x2e76>
    2892:	movzx  edi,BYTE PTR [rax]
    2895:	cmp    dil,0x41
    2899:	jne    2863 <free@plt+0x16c3>
    289b:	movsx  edi,BYTE PTR [rax+0x1]
    289f:	add    esi,edi
    28a1:	jmp    2881 <free@plt+0x16e1>
    28a3:	cmp    DWORD PTR [rip+0x47da],0x0        # 7084 <_fini+0x2b70>
    28aa:	jne    28c8 <free@plt+0x1728>
    28ac:	xor    r9d,r9d
    28af:	xor    r8d,r8d
    28b2:	mov    ecx,r10d
    28b5:	xor    edx,edx
    28b7:	xor    esi,esi
    28b9:	mov    edi,0xe2
    28be:	call   18d0 <free@plt+0x730>
    28c3:	jmp    1dbd <free@plt+0xc1d>
    28c8:	sub    ecx,0x10
    28cb:	cmp    cl,0x30
    28ce:	ja     1eab <free@plt+0xd0b>
    28d4:	lea    rdx,[rip+0x2779]        # 5054 <_fini+0xb40>
    28db:	movzx  ecx,cl
    28de:	movsxd rax,DWORD PTR [rdx+rcx*4]
    28e2:	add    rax,rdx
    28e5:	jmp    rax
    28e7:	cmp    DWORD PTR [rsp+0x88],0xc
    28ef:	jne    1eab <free@plt+0xd0b>
    28f5:	movd   xmm0,DWORD PTR [rsp+0x150]
    28fe:	movdqa xmm3,xmm0
    2902:	psrld  xmm3,0x10
    2907:	movdqa xmm1,xmm3
    290b:	por    xmm1,xmm0
    290f:	movdqa xmm4,xmm1
    2913:	psrld  xmm4,0x8
    2918:	por    xmm1,xmm4
    291c:	movd   DWORD PTR [rsp+0x5c],xmm1
    2922:	cmp    BYTE PTR [rsp+0x5c],0x7
    2927:	ja     1eab <free@plt+0xd0b>
    292d:	movd   eax,xmm0
    2931:	lea    rcx,[rip+0x4b28]        # 7460 <_fini+0x2f4c>
    2938:	movzx  edx,al
    293b:	cmp    QWORD PTR [rcx+rdx*8],0x0
    2940:	je     1eab <free@plt+0xd0b>
    2946:	movzx  esi,ah
    2949:	lea    rcx,[rip+0x4a50]        # 73a0 <_fini+0x2e8c>
    2950:	cmp    QWORD PTR [rcx+rsi*8],0x0
    2955:	je     1eab <free@plt+0xd0b>
    295b:	mov    ecx,eax
    295d:	lea    rdi,[rip+0x497c]        # 72e0 <_fini+0x2dcc>
    2964:	shr    ecx,0x10
    2967:	movzx  ecx,cl
    296a:	cmp    QWORD PTR [rdi+rcx*8],0x0
    296f:	je     1eab <free@plt+0xd0b>
    2975:	shr    eax,0x18
    2978:	lea    rdi,[rip+0x48a1]        # 7220 <_fini+0x2d0c>
    297f:	cmp    QWORD PTR [rdi+rax*8],0x0
    2984:	je     1eab <free@plt+0xd0b>
    298a:	lea    rdi,[rip+0x4b0f]        # 74a0 <_fini+0x2f8c>
    2991:	mov    r8,QWORD PTR [rdi+rdx*8]
    2995:	lea    rdx,[rip+0x4a44]        # 73e0 <_fini+0x2ecc>
    299c:	lea    rdi,[rsp+0x90]
    29a4:	mov    rsi,QWORD PTR [rdx+rsi*8]
    29a8:	lea    rdx,[rip+0x4971]        # 7320 <_fini+0x2e0c>
    29af:	mov    QWORD PTR [rsp+0x18],rdi
    29b4:	mov    r14,QWORD PTR [rdx+rcx*8]
    29b8:	lea    rdx,[rip+0x48a1]        # 7260 <_fini+0x2d4c>
    29bf:	mov    ecx,0x8
    29c4:	mov    rax,QWORD PTR [rdx+rax*8]
    29c8:	mov    r15,rsi
    29cb:	mov    rbp,r14
    29ce:	mov    QWORD PTR [rsp],rax
    29d2:	xor    eax,eax
    29d4:	test   r8,r8
    29d7:	rep stos DWORD PTR es:[rdi],eax
    29d9:	mov    rdi,QWORD PTR [rsp+0x10]
    29de:	mov    ecx,0x8
    29e3:	setne  dl
    29e6:	test   rsi,rsi
    29e9:	rep stos DWORD PTR es:[rdi],eax
    29eb:	setne  al
    29ee:	test   dl,al
    29f0:	je     2a0a <free@plt+0x186a>
    29f2:	test   r14,r14
    29f5:	je     2a0a <free@plt+0x186a>
    29f7:	movabs rax,0x3454454b43495443
    2a01:	cmp    QWORD PTR [r8],rax
    2a04:	je     4083 <free@plt+0x2ee3>
    2a0a:	xor    ecx,ecx
    2a0c:	mov    BYTE PTR [rsp+0x8],r9b
    2a11:	xor    esi,esi
    2a13:	mov    BYTE PTR [rsp+0x20],r11b
    2a18:	mov    DWORD PTR [rsp+0x28],r10d
    2a1d:	movzx  edx,BYTE PTR [rsp+rsi*2+0x154]
    2a25:	movzx  eax,BYTE PTR [rsp+rsi*2+0x155]
    2a2d:	mov    edi,edx
    2a2f:	or     edi,eax
    2a31:	cmp    dil,0x7
    2a35:	ja     2a57 <free@plt+0x18b7>
    2a37:	lea    rdi,[rip+0x4722]        # 7160 <_fini+0x2c4c>
    2a3e:	cmp    QWORD PTR [rdi+rdx*8],0x0
    2a43:	je     2a57 <free@plt+0x18b7>
    2a45:	lea    rdi,[rip+0x4654]        # 70a0 <_fini+0x2b8c>
    2a4c:	cmp    QWORD PTR [rdi+rax*8],0x0
    2a51:	jne    4318 <free@plt+0x3178>
    2a57:	xor    ecx,ecx
    2a59:	add    rsi,0x1
    2a5d:	cmp    rsi,0x4
    2a61:	jne    2a1d <free@plt+0x187d>
    2a63:	movzx  r9d,BYTE PTR [rsp+0x8]
    2a69:	movzx  r11d,BYTE PTR [rsp+0x20]
    2a6f:	mov    r10d,DWORD PTR [rsp+0x28]
    2a74:	test   ecx,ecx
    2a76:	je     44b2 <free@plt+0x3312>
    2a7c:	mov    rax,QWORD PTR [rip+0x4c1d]        # 76a0 <_fini+0x318c>
    2a83:	xor    r8d,r8d
    2a86:	mov    rcx,QWORD PTR [rax+0xe8]
    2a8d:	mov    rsi,QWORD PTR [rax+0xd8]
    2a94:	mov    r14,rax
    2a97:	mov    r15,rcx
    2a9a:	mov    rdx,rcx
    2a9d:	mov    rax,QWORD PTR [rsp+0x18]
    2aa2:	mov    rcx,QWORD PTR [rsp+0x10]
    2aa7:	mov    rdi,r15
    2aaa:	movq   xmm0,rdx
    2aaf:	xor    rdi,r8
    2ab2:	mov    rdx,r13
    2ab5:	mov    DWORD PTR [rsp+0x38],r10d
    2aba:	mov    rax,QWORD PTR [rax+r8*8]
    2abe:	mov    rcx,QWORD PTR [rcx+r8*8]
    2ac2:	mov    BYTE PTR [rsp+0x30],r11b
    2ac7:	mov    BYTE PTR [rsp+0x28],r9b
    2acc:	movq   xmm1,QWORD PTR [rax+0x10]
    2ad1:	mov    QWORD PTR [rsp+0x8],rcx
    2ad6:	movhps xmm1,QWORD PTR [rcx+0x10]
    2ada:	mov    ecx,0x6
    2adf:	movhps xmm0,QWORD PTR [rax+0x30]
    2ae3:	mov    QWORD PTR [rsp+0x20],r8
    2ae8:	movaps XMMWORD PTR [rsp+0xd0],xmm0
    2af0:	movq   xmm0,rax
    2af5:	movhps xmm0,QWORD PTR [rsp+0x8]
    2afa:	movaps XMMWORD PTR [rsp+0xe0],xmm1
    2b02:	mov    QWORD PTR [rsp+0x8],rsi
    2b07:	movaps XMMWORD PTR [rsp+0xf0],xmm0
    2b0f:	call   1410 <free@plt+0x270>
    2b14:	mov    r8,QWORD PTR [rsp+0x20]
    2b19:	mov    rsi,QWORD PTR [rsp+0x8]
    2b1e:	movzx  r9d,BYTE PTR [rsp+0x28]
    2b24:	movzx  r11d,BYTE PTR [rsp+0x30]
    2b2a:	mov    rdx,rax
    2b2d:	add    r8,0x1
    2b31:	mov    r10d,DWORD PTR [rsp+0x38]
    2b36:	cmp    r8,0x4
    2b3a:	jne    2a9d <free@plt+0x18fd>
    2b40:	mov    rcx,QWORD PTR [rsp]
    2b44:	mov    rax,r14
    2b47:	cmp    QWORD PTR [rcx+0x30],rdx
    2b4b:	jne    44b2 <free@plt+0x3312>
    2b51:	mov    r8,QWORD PTR [rsp+0x18]
    2b56:	lea    rdx,[rbp+0x40]
    2b5a:	lea    r15,[rbp+0x440]
    2b61:	mov    rcx,QWORD PTR [r8]
    2b64:	add    r8,0x8
    2b68:	mov    rdi,QWORD PTR [rcx+0x40]
    2b6c:	lea    rsi,[rcx+0x40]
    2b70:	mov    QWORD PTR [rdx],rdi
    2b73:	mov    rcx,QWORD PTR [rcx+0x138]
    2b7a:	lea    rdi,[rdx+0x8]
    2b7e:	and    rdi,0xfffffffffffffff8
    2b82:	mov    QWORD PTR [rdx+0xf8],rcx
    2b89:	mov    rcx,rdx
    2b8c:	add    rdx,0x100
    2b93:	sub    rcx,rdi
    2b96:	sub    rsi,rcx
    2b99:	add    ecx,0x100
    2b9f:	shr    ecx,0x3
    2ba2:	rep movs QWORD PTR es:[rdi],QWORD PTR ds:[rsi]
    2ba5:	cmp    r15,rdx
    2ba8:	jne    2b61 <free@plt+0x19c1>
    2baa:	mov    rcx,QWORD PTR [rsp]
    2bae:	mov    rdx,QWORD PTR [rbp+0x8]
    2bb2:	xor    rdx,rcx
    2bb5:	xor    rdx,QWORD PTR [rax+0xe0]
    2bbc:	mov    rax,rdx
    2bbf:	mov    rdx,QWORD PTR [rcx+0x28]
    2bc3:	ror    rdx,0x15
    2bc7:	xor    rax,rdx
    2bca:	mov    rdx,rax
    2bcd:	shr    rdx,0x2f
    2bd1:	je     2be0 <free@plt+0x1a40>
    2bd3:	cmp    rdx,0x1ffff
    2bda:	jne    1b34 <free@plt+0x994>
    2be0:	mov    BYTE PTR [rsp],r9b
    2be4:	mov    rdi,rbp
    2be7:	mov    DWORD PTR [rsp+0x18],r10d
    2bec:	mov    BYTE PTR [rsp+0x8],r11b
    2bf1:	call   rax
    2bf3:	movzx  edx,BYTE PTR [rsp+0x8]
    2bf8:	movzx  esi,BYTE PTR [rsp]
    2bfc:	xor    r9d,r9d
    2bff:	mov    ecx,DWORD PTR [rsp+0x18]
    2c03:	xor    r8d,r8d
    2c06:	mov    edi,0xc0
    2c0b:	call   18d0 <free@plt+0x730>
    2c10:	jmp    1dbd <free@plt+0xc1d>
    2c15:	mov    eax,r9d
    2c18:	or     eax,r11d
    2c1b:	cmp    al,0x7
    2c1d:	ja     1eab <free@plt+0xd0b>
    2c23:	movzx  eax,r9b
    2c27:	lea    rdx,[rip+0x45b2]        # 71e0 <_fini+0x2ccc>
    2c2e:	movzx  esi,r9b
    2c32:	mov    rcx,QWORD PTR [rdx+rax*8]
    2c36:	test   rcx,rcx
    2c39:	je     1eab <free@plt+0xd0b>
    2c3f:	movzx  eax,r11b
    2c43:	lea    rdx,[rip+0x44d6]        # 7120 <_fini+0x2c0c>
    2c4a:	movzx  r14d,r11b
    2c4e:	mov    rdx,QWORD PTR [rdx+rax*8]
    2c52:	test   rdx,rdx
    2c55:	je     1eab <free@plt+0xd0b>
    2c5b:	cmp    DWORD PTR [rsp+0x88],0x0
    2c63:	jne    1eab <free@plt+0xd0b>
    2c69:	mov    rax,QWORD PTR [rdx+0x8]
    2c6d:	cmp    QWORD PTR [rcx+0x8],rax
    2c71:	jne    1eab <free@plt+0xd0b>
    2c77:	mov    rax,QWORD PTR [rip+0x4a22]        # 76a0 <_fini+0x318c>
    2c7e:	mov    DWORD PTR [rsp+0x18],esi
    2c82:	mov    DWORD PTR [rsp+0x20],r10d
    2c87:	mov    rdi,QWORD PTR [rax+0xd8]
    2c8e:	mov    QWORD PTR [rsp+0x8],rdx
    2c93:	mov    QWORD PTR [rsp],rcx
    2c97:	xor    rdi,rdx
    2c9a:	mov    QWORD PTR [rcx+0x20],rdi
    2c9e:	mov    rdi,QWORD PTR [rdx+0x10]
    2ca2:	mov    QWORD PTR [rcx+0x28],rdi
    2ca6:	mov    rsi,QWORD PTR [rax+0xd8]
    2cad:	mov    rdi,rcx
    2cb0:	xor    rsi,rcx
    2cb3:	mov    QWORD PTR [rdx+0x20],rsi
    2cb7:	mov    rax,QWORD PTR [rcx+0x10]
    2cbb:	mov    QWORD PTR [rdx+0x28],rax
    2cbf:	mov    rax,QWORD PTR [rcx+0x30]
    2cc3:	mov    QWORD PTR [rdx+0x30],rax
    2cc7:	call   1740 <free@plt+0x5a0>
    2ccc:	mov    rcx,QWORD PTR [rsp]
    2cd0:	mov    rdx,QWORD PTR [rsp+0x8]
    2cd5:	mov    QWORD PTR [rcx+0x38],rax
    2cd9:	mov    rdi,rdx
    2cdc:	mov    QWORD PTR [rsp],rdx
    2ce0:	call   1790 <free@plt+0x5f0>
    2ce5:	mov    rdx,QWORD PTR [rsp]
    2ce9:	mov    ecx,DWORD PTR [rsp+0x20]
    2ced:	xor    r9d,r9d
    2cf0:	mov    esi,DWORD PTR [rsp+0x18]
    2cf4:	xor    r8d,r8d
    2cf7:	mov    edi,0xba
    2cfc:	mov    QWORD PTR [rdx+0x38],rax
    2d00:	mov    edx,r14d
    2d03:	call   18d0 <free@plt+0x730>
    2d08:	jmp    1dbd <free@plt+0xc1d>
    2d0d:	cmp    r9b,0x7
    2d11:	ja     1eab <free@plt+0xd0b>
    2d17:	movzx  r8d,r9b
    2d1b:	lea    rax,[rip+0x43be]        # 70e0 <_fini+0x2bcc>
    2d22:	mov    rdx,QWORD PTR [rax+r8*8]
    2d26:	test   rdx,rdx
    2d29:	je     1eab <free@plt+0xd0b>
    2d2f:	lea    rax,[rip+0x436a]        # 70a0 <_fini+0x2b8c>
    2d36:	cmp    QWORD PTR [rax+r8*8],0x0
    2d3b:	jne    1eab <free@plt+0xd0b>
    2d41:	cmp    DWORD PTR [rsp+0x88],0x98
    2d4c:	jne    1eab <free@plt+0xd0b>
    2d52:	mov    rdi,rdx
    2d55:	lea    rsi,[rsp+0x150]
    2d5d:	mov    ecx,0x26
    2d62:	rep movs DWORD PTR es:[rdi],DWORD PTR ds:[rsi]
    2d64:	lea    rax,[rip+0x4335]        # 70a0 <_fini+0x2b8c>
    2d6b:	movzx  esi,r9b
    2d6f:	mov    ecx,r10d
    2d72:	mov    QWORD PTR [rax+r8*8],rdx
    2d76:	xor    r9d,r9d
    2d79:	movzx  edx,r11b
    2d7d:	xor    r8d,r8d
    2d80:	mov    edi,0xb9
    2d85:	call   18d0 <free@plt+0x730>
    2d8a:	jmp    1dbd <free@plt+0xc1d>
    2d8f:	cmp    r9b,0x7
    2d93:	ja     1eab <free@plt+0xd0b>
    2d99:	movzx  eax,r9b
    2d9d:	lea    rdx,[rip+0x433c]        # 70e0 <_fini+0x2bcc>
    2da4:	movzx  esi,r9b
    2da8:	mov    r8,QWORD PTR [rdx+rax*8]
    2dac:	test   r8,r8
    2daf:	je     1eab <free@plt+0xd0b>
    2db5:	cmp    DWORD PTR [rsp+0x88],0x0
    2dbd:	jne    1eab <free@plt+0xd0b>
    2dc3:	movzx  edx,r11b
    2dc7:	mov    r9d,0x40
    2dcd:	mov    ecx,r10d
    2dd0:	mov    edi,0xb8
    2dd5:	call   18d0 <free@plt+0x730>
    2dda:	jmp    1dbd <free@plt+0xc1d>
    2ddf:	cmp    r9b,0x7
    2de3:	ja     1eab <free@plt+0xd0b>
    2de9:	lea    rax,[rip+0x4330]        # 7120 <_fini+0x2c0c>
    2df0:	movzx  edx,r9b
    2df4:	movzx  esi,r9b
    2df8:	mov    rdi,QWORD PTR [rax+rdx*8]
    2dfc:	test   rdi,rdi
    2dff:	je     1eab <free@plt+0xd0b>
    2e05:	cmp    DWORD PTR [rsp+0x88],0x0
    2e0d:	jne    1eab <free@plt+0xd0b>
    2e13:	mov    QWORD PTR [rsp+0x18],rdx
    2e18:	mov    DWORD PTR [rsp+0x20],esi
    2e1c:	mov    DWORD PTR [rsp+0x8],r10d
    2e21:	mov    BYTE PTR [rsp],r11b
    2e25:	call   11a0 <free@plt>
    2e2a:	mov    rdx,QWORD PTR [rsp+0x18]
    2e2f:	xor    ecx,ecx
    2e31:	mov    esi,DWORD PTR [rsp+0x20]
    2e35:	lea    rax,[rip+0x42e4]        # 7120 <_fini+0x2c0c>
    2e3c:	xor    r9d,r9d
    2e3f:	xor    r8d,r8d
    2e42:	mov    edi,0xb7
    2e47:	mov    QWORD PTR [rax+rdx*8],rcx
    2e4b:	movzx  edx,BYTE PTR [rsp]
    2e4f:	mov    ecx,DWORD PTR [rsp+0x8]
    2e53:	call   18d0 <free@plt+0x730>
    2e58:	jmp    1dbd <free@plt+0xc1d>
    2e5d:	mov    eax,r9d
    2e60:	or     eax,r11d
    2e63:	cmp    al,0x7
    2e65:	ja     1eab <free@plt+0xd0b>
    2e6b:	movzx  eax,r9b
    2e6f:	lea    rdx,[rip+0x42aa]        # 7120 <_fini+0x2c0c>
    2e76:	movzx  esi,r9b
    2e7a:	mov    rcx,QWORD PTR [rdx+rax*8]
    2e7e:	test   rcx,rcx
    2e81:	je     1eab <free@plt+0xd0b>
    2e87:	lea    rax,[rip+0x4252]        # 70e0 <_fini+0x2bcc>
    2e8e:	movzx  edx,r11b
    2e92:	cmp    QWORD PTR [rax+rdx*8],0x0
    2e97:	jne    1eab <free@plt+0xd0b>
    2e9d:	cmp    DWORD PTR [rsp+0x88],0x0
    2ea5:	jne    1eab <free@plt+0xd0b>
    2eab:	mov    QWORD PTR [rax+rdx*8],rcx
    2eaf:	xor    r9d,r9d
    2eb2:	xor    r8d,r8d
    2eb5:	mov    ecx,r10d
    2eb8:	movzx  edx,r11b
    2ebc:	mov    edi,0xb6
    2ec1:	call   18d0 <free@plt+0x730>
    2ec6:	jmp    1dbd <free@plt+0xc1d>
    2ecb:	cmp    r9b,0x7
    2ecf:	ja     1eab <free@plt+0xd0b>
    2ed5:	movzx  r14d,r9b
    2ed9:	lea    r15,[rip+0x4240]        # 7120 <_fini+0x2c0c>
    2ee0:	movzx  ebp,r9b
    2ee4:	cmp    QWORD PTR [r15+r14*8],0x0
    2ee9:	jne    1eab <free@plt+0xd0b>
    2eef:	cmp    r11b,0x3
    2ef3:	ja     1eab <free@plt+0xd0b>
    2ef9:	cmp    DWORD PTR [rsp+0x88],0x0
    2f01:	jne    1eab <free@plt+0xd0b>
    2f07:	mov    esi,0x98
    2f0c:	mov    edi,0x1
    2f11:	mov    DWORD PTR [rsp+0x18],r10d
    2f16:	mov    BYTE PTR [rsp],r11b
    2f1a:	call   1090 <calloc@plt>
    2f1f:	mov    rdx,rax
    2f22:	test   rax,rax
    2f25:	je     1ade <free@plt+0x93e>
    2f2b:	movabs rax,0x344c414553564c43
    2f35:	lea    rdi,[rdx+0x10]
    2f39:	mov    QWORD PTR [rdx],rax
    2f3c:	movzx  eax,BYTE PTR [rsp]
    2f40:	mov    QWORD PTR [rsp],rdx
    2f44:	mov    QWORD PTR [rdx+0x8],rax
    2f48:	mov    BYTE PTR [rsp+0x8],al
    2f4c:	call   1a70 <free@plt+0x8d0>
    2f51:	mov    rax,QWORD PTR [rip+0x4748]        # 76a0 <_fini+0x318c>
    2f58:	mov    rdx,QWORD PTR [rsp]
    2f5c:	mov    rcx,QWORD PTR [rax+0xd8]
    2f63:	mov    rdi,rdx
    2f66:	xor    rcx,rdx
    2f69:	mov    QWORD PTR [rdx+0x18],rcx
    2f6d:	call   1790 <free@plt+0x5f0>
    2f72:	mov    rdx,QWORD PTR [rsp]
    2f76:	mov    ecx,DWORD PTR [rsp+0x18]
    2f7a:	xor    r9d,r9d
    2f7d:	xor    r8d,r8d
    2f80:	mov    esi,ebp
    2f82:	mov    edi,0xb5
    2f87:	mov    QWORD PTR [rdx+0x38],rax
    2f8b:	mov    QWORD PTR [r15+r14*8],rdx
    2f8f:	movzx  edx,BYTE PTR [rsp+0x8]
    2f94:	call   18d0 <free@plt+0x730>
    2f99:	jmp    1dbd <free@plt+0xc1d>
    2f9e:	cmp    r9b,0x7
    2fa2:	ja     1eab <free@plt+0xd0b>
    2fa8:	movzx  ecx,r9b
    2fac:	lea    rax,[rip+0x41ed]        # 71a0 <_fini+0x2c8c>
    2fb3:	mov    r8,QWORD PTR [rax+rcx*8]
    2fb7:	mov    r15,rcx
    2fba:	test   r8,r8
    2fbd:	je     1eab <free@plt+0xd0b>
    2fc3:	lea    rax,[rip+0x4196]        # 7160 <_fini+0x2c4c>
    2fca:	cmp    QWORD PTR [rax+rcx*8],0x0
    2fcf:	jne    1eab <free@plt+0xd0b>
    2fd5:	cmp    DWORD PTR [rsp+0x88],0x140
    2fe0:	jne    1eab <free@plt+0xd0b>
    2fe6:	mov    rdx,QWORD PTR [rsp+0x150]
    2fee:	lea    rdi,[r8+0x8]
    2ff2:	lea    rax,[rsp+0x150]
    2ffa:	and    rdi,0xfffffffffffffff8
    2ffe:	mov    QWORD PTR [r8],rdx
    3001:	mov    rdx,QWORD PTR [rsp+0x288]
    3009:	mov    QWORD PTR [r8+0x138],rdx
    3010:	mov    rdx,r8
    3013:	sub    rdx,rdi
    3016:	sub    rax,rdx
    3019:	lea    ecx,[rdx+0x140]
    301f:	movzx  edx,r11b
    3023:	mov    rsi,rax
    3026:	shr    ecx,0x3
    3029:	lea    rax,[rip+0x4130]        # 7160 <_fini+0x2c4c>
    3030:	rep movs QWORD PTR es:[rdi],QWORD PTR ds:[rsi]
    3033:	mov    QWORD PTR [rax+r15*8],r8
    3037:	movzx  esi,r9b
    303b:	xor    r8d,r8d
    303e:	xor    r9d,r9d
    3041:	mov    ecx,r10d
    3044:	mov    edi,0xb4
    3049:	call   18d0 <free@plt+0x730>
    304e:	jmp    1dbd <free@plt+0xc1d>
    3053:	cmp    r9b,0x7
    3057:	ja     1eab <free@plt+0xd0b>
    305d:	movzx  eax,r9b
    3061:	lea    rdx,[rip+0x4138]        # 71a0 <_fini+0x2c8c>
    3068:	movzx  esi,r9b
    306c:	mov    r8,QWORD PTR [rdx+rax*8]
    3070:	test   r8,r8
    3073:	je     1eab <free@plt+0xd0b>
    3079:	cmp    DWORD PTR [rsp+0x88],0x0
    3081:	jne    1eab <free@plt+0xd0b>
    3087:	movzx  edx,r11b
    308b:	mov    r9d,0x40
    3091:	mov    ecx,r10d
    3094:	mov    edi,0xb3
    3099:	call   18d0 <free@plt+0x730>
    309e:	jmp    1dbd <free@plt+0xc1d>
    30a3:	cmp    r9b,0x7
    30a7:	ja     1eab <free@plt+0xd0b>
    30ad:	lea    rax,[rip+0x412c]        # 71e0 <_fini+0x2ccc>
    30b4:	movzx  edx,r9b
    30b8:	movzx  esi,r9b
    30bc:	mov    rdi,QWORD PTR [rax+rdx*8]
    30c0:	test   rdi,rdi
    30c3:	je     1eab <free@plt+0xd0b>
    30c9:	cmp    DWORD PTR [rsp+0x88],0x0
    30d1:	jne    1eab <free@plt+0xd0b>
    30d7:	mov    QWORD PTR [rsp+0x18],rdx
    30dc:	mov    DWORD PTR [rsp+0x20],esi
    30e0:	mov    DWORD PTR [rsp+0x8],r10d
    30e5:	mov    BYTE PTR [rsp],r11b
    30e9:	call   11a0 <free@plt>
    30ee:	mov    rdx,QWORD PTR [rsp+0x18]
    30f3:	xor    esi,esi
    30f5:	mov    ecx,DWORD PTR [rsp+0x8]
    30f9:	lea    rax,[rip+0x40e0]        # 71e0 <_fini+0x2ccc>
    3100:	xor    r9d,r9d
    3103:	xor    r8d,r8d
    3106:	mov    edi,0xb2
    310b:	mov    QWORD PTR [rax+rdx*8],rsi
    310f:	movzx  edx,BYTE PTR [rsp]
    3113:	mov    esi,DWORD PTR [rsp+0x20]
    3117:	call   18d0 <free@plt+0x730>
    311c:	jmp    1dbd <free@plt+0xc1d>
    3121:	mov    eax,r9d
    3124:	or     eax,r11d
    3127:	cmp    al,0x7
    3129:	ja     1eab <free@plt+0xd0b>
    312f:	movzx  eax,r9b
    3133:	lea    rdx,[rip+0x40a6]        # 71e0 <_fini+0x2ccc>
    313a:	movzx  esi,r9b
    313e:	mov    rcx,QWORD PTR [rdx+rax*8]
    3142:	test   rcx,rcx
    3145:	je     1eab <free@plt+0xd0b>
    314b:	lea    rax,[rip+0x404e]        # 71a0 <_fini+0x2c8c>
    3152:	movzx  edx,r11b
    3156:	cmp    QWORD PTR [rax+rdx*8],0x0
    315b:	jne    1eab <free@plt+0xd0b>
    3161:	cmp    DWORD PTR [rsp+0x88],0x0
    3169:	jne    1eab <free@plt+0xd0b>
    316f:	mov    QWORD PTR [rax+rdx*8],rcx
    3173:	xor    r9d,r9d
    3176:	xor    r8d,r8d
    3179:	mov    ecx,r10d
    317c:	movzx  edx,r11b
    3180:	mov    edi,0xb1
    3185:	call   18d0 <free@plt+0x730>
    318a:	jmp    1dbd <free@plt+0xc1d>
    318f:	cmp    r9b,0x7
    3193:	ja     1eab <free@plt+0xd0b>
    3199:	movzx  r14d,r9b
    319d:	lea    r15,[rip+0x403c]        # 71e0 <_fini+0x2ccc>
    31a4:	movzx  ebp,r9b
    31a8:	cmp    QWORD PTR [r15+r14*8],0x0
    31ad:	jne    1eab <free@plt+0xd0b>
    31b3:	cmp    r11b,0x3
    31b7:	ja     1eab <free@plt+0xd0b>
    31bd:	cmp    DWORD PTR [rsp+0x88],0x0
    31c5:	jne    1eab <free@plt+0xd0b>
    31cb:	mov    esi,0x140
    31d0:	mov    edi,0x1
    31d5:	mov    DWORD PTR [rsp+0x18],r10d
    31da:	mov    BYTE PTR [rsp],r11b
    31de:	call   1090 <calloc@plt>
    31e3:	mov    rcx,rax
    31e6:	test   rax,rax
    31e9:	je     1ade <free@plt+0x93e>
    31ef:	movabs rax,0x344b4e5548434c43
    31f9:	lea    rdi,[rcx+0x10]
    31fd:	mov    QWORD PTR [rcx],rax
    3200:	movzx  eax,BYTE PTR [rsp]
    3204:	mov    QWORD PTR [rsp],rcx
    3208:	mov    QWORD PTR [rcx+0x8],rax
    320c:	mov    BYTE PTR [rsp+0x8],al
    3210:	call   1a70 <free@plt+0x8d0>
    3215:	mov    rax,QWORD PTR [rip+0x4484]        # 76a0 <_fini+0x318c>
    321c:	mov    rcx,QWORD PTR [rsp]
    3220:	mov    rdx,QWORD PTR [rax+0xd8]
    3227:	mov    rsi,QWORD PTR [rcx+0x8]
    322b:	mov    rdi,QWORD PTR [rcx+0x10]
    322f:	xor    rdx,rcx
    3232:	mov    QWORD PTR [rcx+0x18],rdx
    3236:	lea    rdx,[rcx+0x40]
    323a:	call   1820 <free@plt+0x680>
    323f:	mov    rcx,QWORD PTR [rsp]
    3243:	mov    QWORD PTR [rcx+0x30],rax
    3247:	mov    rdi,rcx
    324a:	call   1740 <free@plt+0x5a0>
    324f:	mov    rcx,QWORD PTR [rsp]
    3253:	movzx  edx,BYTE PTR [rsp+0x8]
    3258:	mov    esi,ebp
    325a:	xor    r9d,r9d
    325d:	xor    r8d,r8d
    3260:	mov    edi,0xb0
    3265:	mov    QWORD PTR [rcx+0x38],rax
    3269:	mov    QWORD PTR [r15+r14*8],rcx
    326d:	mov    ecx,DWORD PTR [rsp+0x18]
    3271:	call   18d0 <free@plt+0x730>
    3276:	jmp    1dbd <free@plt+0xc1d>
    327b:	mov    eax,r9d
    327e:	or     eax,r11d
    3281:	cmp    al,0x7
    3283:	ja     1eab <free@plt+0xd0b>
    3289:	movzx  eax,r9b
    328d:	lea    rdx,[rip+0x40cc]        # 7360 <_fini+0x2e4c>
    3294:	movzx  esi,r9b
    3298:	mov    rcx,QWORD PTR [rdx+rax*8]
    329c:	test   rcx,rcx
    329f:	je     1eab <free@plt+0xd0b>
    32a5:	movzx  eax,r11b
    32a9:	lea    rdx,[rip+0x3ff0]        # 72a0 <_fini+0x2d8c>
    32b0:	movzx  r15d,r11b
    32b4:	mov    rdx,QWORD PTR [rdx+rax*8]
    32b8:	test   rdx,rdx
    32bb:	je     1eab <free@plt+0xd0b>
    32c1:	cmp    DWORD PTR [rsp+0x88],0x0
    32c9:	jne    1eab <free@plt+0xd0b>
    32cf:	mov    rax,QWORD PTR [rip+0x43ca]        # 76a0 <_fini+0x318c>
    32d6:	lea    r14,[rip+0xffffffffffffe513]        # 17f0 <free@plt+0x650>
    32dd:	mov    DWORD PTR [rsp+0x20],esi
    32e1:	mov    DWORD PTR [rsp+0x18],r10d
    32e6:	mov    rdi,QWORD PTR [rax+0xd8]
    32ed:	mov    QWORD PTR [rsp+0x8],rdx
    32f2:	mov    QWORD PTR [rsp],rcx
    32f6:	xor    rdi,rdx
    32f9:	mov    QWORD PTR [rcx+0x18],rdi
    32fd:	mov    rdi,QWORD PTR [rdx+0x8]
    3301:	mov    QWORD PTR [rcx+0x20],rdi
    3305:	mov    rdi,QWORD PTR [rax+0xd8]
    330c:	xor    rdi,rcx
    330f:	mov    QWORD PTR [rdx+0x18],rdi
    3313:	mov    rdi,QWORD PTR [rcx+0x8]
    3317:	mov    QWORD PTR [rdx+0x20],rdi
    331b:	xor    r14,QWORD PTR [rax+0xe0]
    3322:	mov    rax,r14
    3325:	xor    rax,rdx
    3328:	xor    rax,rdi
    332b:	mov    rdi,rcx
    332e:	rol    rax,0x15
    3332:	mov    QWORD PTR [rdx+0x28],rax
    3336:	call   1690 <free@plt+0x4f0>
    333b:	mov    rcx,QWORD PTR [rsp]
    333f:	mov    rdx,QWORD PTR [rsp+0x8]
    3344:	mov    QWORD PTR [rcx+0x38],rax
    3348:	mov    rdi,rdx
    334b:	mov    QWORD PTR [rsp],rdx
    334f:	call   16e0 <free@plt+0x540>
    3354:	mov    rdx,QWORD PTR [rsp]
    3358:	mov    ecx,DWORD PTR [rsp+0x18]
    335c:	xor    r9d,r9d
    335f:	mov    esi,DWORD PTR [rsp+0x20]
    3363:	xor    r8d,r8d
    3366:	mov    edi,0xac
    336b:	mov    QWORD PTR [rdx+0x40],rax
    336f:	mov    edx,r15d
    3372:	call   18d0 <free@plt+0x730>
    3377:	jmp    1dbd <free@plt+0xc1d>
    337c:	cmp    r9b,0x7
    3380:	ja     1eab <free@plt+0xd0b>
    3386:	movzx  ecx,r9b
    338a:	lea    rax,[rip+0x3ecf]        # 7260 <_fini+0x2d4c>
    3391:	mov    r8,QWORD PTR [rax+rcx*8]
    3395:	mov    r14,rcx
    3398:	test   r8,r8
    339b:	je     1eab <free@plt+0xd0b>
    33a1:	lea    rax,[rip+0x3e78]        # 7220 <_fini+0x2d0c>
    33a8:	cmp    QWORD PTR [rax+rcx*8],0x0
    33ad:	jne    1eab <free@plt+0xd0b>
    33b3:	cmp    DWORD PTR [rsp+0x88],0x190
    33be:	jne    1eab <free@plt+0xd0b>
    33c4:	mov    rdx,QWORD PTR [rsp+0x150]
    33cc:	lea    rdi,[r8+0x8]
    33d0:	lea    rax,[rsp+0x150]
    33d8:	and    rdi,0xfffffffffffffff8
    33dc:	mov    QWORD PTR [r8],rdx
    33df:	mov    rdx,QWORD PTR [rsp+0x2d8]
    33e7:	mov    QWORD PTR [r8+0x188],rdx
    33ee:	mov    rdx,r8
    33f1:	sub    rdx,rdi
    33f4:	sub    rax,rdx
    33f7:	lea    ecx,[rdx+0x190]
    33fd:	movzx  edx,r11b
    3401:	mov    rsi,rax
    3404:	shr    ecx,0x3
    3407:	lea    rax,[rip+0x3e12]        # 7220 <_fini+0x2d0c>
    340e:	rep movs QWORD PTR es:[rdi],QWORD PTR ds:[rsi]
    3411:	mov    QWORD PTR [rax+r14*8],r8
    3415:	movzx  esi,r9b
    3419:	xor    r8d,r8d
    341c:	xor    r9d,r9d
    341f:	mov    ecx,r10d
    3422:	mov    edi,0xab
    3427:	call   18d0 <free@plt+0x730>
    342c:	jmp    1dbd <free@plt+0xc1d>
    3431:	cmp    r9b,0x7
    3435:	ja     1eab <free@plt+0xd0b>
    343b:	movzx  eax,r9b
    343f:	lea    rdx,[rip+0x3e1a]        # 7260 <_fini+0x2d4c>
    3446:	movzx  esi,r9b
    344a:	mov    r8,QWORD PTR [rdx+rax*8]
    344e:	test   r8,r8
    3451:	je     1eab <free@plt+0xd0b>
    3457:	cmp    DWORD PTR [rsp+0x88],0x0
    345f:	jne    1eab <free@plt+0xd0b>
    3465:	movzx  edx,r11b
    3469:	mov    r9d,0x50
    346f:	mov    ecx,r10d
    3472:	mov    edi,0xaa
    3477:	call   18d0 <free@plt+0x730>
    347c:	jmp    1dbd <free@plt+0xc1d>
    3481:	cmp    r9b,0x7
    3485:	ja     1eab <free@plt+0xd0b>
    348b:	lea    rax,[rip+0x3e0e]        # 72a0 <_fini+0x2d8c>
    3492:	movzx  edx,r9b
    3496:	movzx  esi,r9b
    349a:	mov    rdi,QWORD PTR [rax+rdx*8]
    349e:	test   rdi,rdi
    34a1:	je     1eab <free@plt+0xd0b>
    34a7:	cmp    DWORD PTR [rsp+0x88],0x0
    34af:	jne    1eab <free@plt+0xd0b>
    34b5:	mov    QWORD PTR [rsp+0x18],rdx
    34ba:	mov    DWORD PTR [rsp+0x20],esi
    34be:	mov    DWORD PTR [rsp+0x8],r10d
    34c3:	mov    BYTE PTR [rsp],r11b
    34c7:	call   11a0 <free@plt>
    34cc:	mov    rdx,QWORD PTR [rsp+0x18]
    34d1:	xor    edi,edi
    34d3:	mov    ecx,DWORD PTR [rsp+0x8]
    34d7:	lea    rax,[rip+0x3dc2]        # 72a0 <_fini+0x2d8c>
    34de:	mov    esi,DWORD PTR [rsp+0x20]
    34e2:	xor    r9d,r9d
    34e5:	xor    r8d,r8d
    34e8:	mov    QWORD PTR [rax+rdx*8],rdi
    34ec:	movzx  edx,BYTE PTR [rsp]
    34f0:	mov    edi,0xa9
    34f5:	call   18d0 <free@plt+0x730>
    34fa:	jmp    1dbd <free@plt+0xc1d>
    34ff:	mov    eax,r9d
    3502:	or     eax,r11d
    3505:	cmp    al,0x7
    3507:	ja     1eab <free@plt+0xd0b>
    350d:	movzx  eax,r9b
    3511:	lea    rdx,[rip+0x3d88]        # 72a0 <_fini+0x2d8c>
    3518:	movzx  esi,r9b
    351c:	mov    rcx,QWORD PTR [rdx+rax*8]
    3520:	test   rcx,rcx
    3523:	je     1eab <free@plt+0xd0b>
    3529:	lea    rax,[rip+0x3d30]        # 7260 <_fini+0x2d4c>
    3530:	movzx  edx,r11b
    3534:	cmp    QWORD PTR [rax+rdx*8],0x0
    3539:	jne    1eab <free@plt+0xd0b>
    353f:	cmp    DWORD PTR [rsp+0x88],0x0
    3547:	jne    1eab <free@plt+0xd0b>
    354d:	mov    QWORD PTR [rax+rdx*8],rcx
    3551:	xor    r9d,r9d
    3554:	xor    r8d,r8d
    3557:	mov    ecx,r10d
    355a:	movzx  edx,r11b
    355e:	mov    edi,0xa8
    3563:	call   18d0 <free@plt+0x730>
    3568:	jmp    1dbd <free@plt+0xc1d>
    356d:	cmp    r9b,0x7
    3571:	ja     1eab <free@plt+0xd0b>
    3577:	movzx  r14d,r9b
    357b:	lea    r15,[rip+0x3d1e]        # 72a0 <_fini+0x2d8c>
    3582:	movzx  ebp,r9b
    3586:	cmp    QWORD PTR [r15+r14*8],0x0
    358b:	jne    1eab <free@plt+0xd0b>
    3591:	cmp    DWORD PTR [rsp+0x88],0x0
    3599:	jne    1eab <free@plt+0xd0b>
    359f:	mov    esi,0x190
    35a4:	mov    edi,0x1
    35a9:	mov    DWORD PTR [rsp+0x18],r10d
    35ae:	mov    BYTE PTR [rsp+0x8],r11b
    35b3:	call   1090 <calloc@plt>
    35b8:	mov    rdx,rax
    35bb:	test   rax,rax
    35be:	je     1ade <free@plt+0x93e>
    35c4:	movabs rax,0x344e414c50564c43
    35ce:	lea    rdi,[rdx+0x8]
    35d2:	mov    QWORD PTR [rsp],rdx
    35d6:	mov    QWORD PTR [rdx],rax
    35d9:	call   1a70 <free@plt+0x8d0>
    35de:	mov    rax,QWORD PTR [rip+0x40bb]        # 76a0 <_fini+0x318c>
    35e5:	mov    rdx,QWORD PTR [rsp]
    35e9:	mov    rcx,QWORD PTR [rax+0xd8]
    35f0:	mov    QWORD PTR [rdx+0x38],0x1
    35f8:	mov    rdi,rdx
    35fb:	xor    rcx,rdx
    35fe:	mov    QWORD PTR [rdx+0x10],rcx
    3602:	call   16e0 <free@plt+0x540>
    3607:	mov    rdx,QWORD PTR [rsp]
    360b:	mov    ecx,DWORD PTR [rsp+0x18]
    360f:	xor    r9d,r9d
    3612:	xor    r8d,r8d
    3615:	mov    esi,ebp
    3617:	mov    edi,0xa7
    361c:	mov    QWORD PTR [rdx+0x40],rax
    3620:	mov    QWORD PTR [r15+r14*8],rdx
    3624:	movzx  edx,BYTE PTR [rsp+0x8]
    3629:	call   18d0 <free@plt+0x730>
    362e:	jmp    1dbd <free@plt+0xc1d>
    3633:	cmp    r9b,0x7
    3637:	ja     1eab <free@plt+0xd0b>
    363d:	movzx  ecx,r9b
    3641:	lea    rax,[rip+0x3cd8]        # 7320 <_fini+0x2e0c>
    3648:	mov    r8,QWORD PTR [rax+rcx*8]
    364c:	mov    r15,rcx
    364f:	test   r8,r8
    3652:	je     1eab <free@plt+0xd0b>
    3658:	lea    rax,[rip+0x3c81]        # 72e0 <_fini+0x2dcc>
    365f:	cmp    QWORD PTR [rax+rcx*8],0x0
    3664:	jne    1eab <free@plt+0xd0b>
    366a:	cmp    DWORD PTR [rsp+0x88],0x440
    3675:	jne    1eab <free@plt+0xd0b>
    367b:	mov    rdx,QWORD PTR [rsp+0x150]
    3683:	lea    rdi,[r8+0x8]
    3687:	lea    rax,[rsp+0x150]
    368f:	and    rdi,0xfffffffffffffff8
    3693:	mov    QWORD PTR [r8],rdx
    3696:	mov    rdx,QWORD PTR [rsp+0x588]
    369e:	mov    QWORD PTR [r8+0x438],rdx
    36a5:	mov    rdx,r8
    36a8:	sub    rdx,rdi
    36ab:	sub    rax,rdx
    36ae:	lea    ecx,[rdx+0x440]
    36b4:	movzx  edx,r11b
    36b8:	mov    rsi,rax
    36bb:	shr    ecx,0x3
    36be:	lea    rax,[rip+0x3c1b]        # 72e0 <_fini+0x2dcc>
    36c5:	rep movs QWORD PTR es:[rdi],QWORD PTR ds:[rsi]
    36c8:	mov    QWORD PTR [rax+r15*8],r8
    36cc:	movzx  esi,r9b
    36d0:	xor    r8d,r8d
    36d3:	xor    r9d,r9d
    36d6:	mov    ecx,r10d
    36d9:	mov    edi,0xa4
    36de:	call   18d0 <free@plt+0x730>
    36e3:	jmp    1dbd <free@plt+0xc1d>
    36e8:	cmp    r9b,0x7
    36ec:	ja     1eab <free@plt+0xd0b>
    36f2:	movzx  eax,r9b
    36f6:	lea    rdx,[rip+0x3c23]        # 7320 <_fini+0x2e0c>
    36fd:	movzx  esi,r9b
    3701:	mov    r8,QWORD PTR [rdx+rax*8]
    3705:	test   r8,r8
    3708:	je     1eab <free@plt+0xd0b>
    370e:	cmp    DWORD PTR [rsp+0x88],0x0
    3716:	jne    1eab <free@plt+0xd0b>
    371c:	movzx  edx,r11b
    3720:	mov    r9d,0x40
    3726:	mov    ecx,r10d
    3729:	mov    edi,0xa3
    372e:	call   18d0 <free@plt+0x730>
    3733:	jmp    1dbd <free@plt+0xc1d>
    3738:	cmp    r9b,0x7
    373c:	ja     1eab <free@plt+0xd0b>
    3742:	lea    rax,[rip+0x3c17]        # 7360 <_fini+0x2e4c>
    3749:	movzx  edx,r9b
    374d:	movzx  esi,r9b
    3751:	mov    rdi,QWORD PTR [rax+rdx*8]
    3755:	test   rdi,rdi
    3758:	je     1eab <free@plt+0xd0b>
    375e:	cmp    DWORD PTR [rsp+0x88],0x0
    3766:	jne    1eab <free@plt+0xd0b>
    376c:	mov    QWORD PTR [rsp+0x18],rdx
    3771:	mov    DWORD PTR [rsp+0x20],esi
    3775:	mov    DWORD PTR [rsp+0x8],r10d
    377a:	mov    BYTE PTR [rsp],r11b
    377e:	call   11a0 <free@plt>
    3783:	mov    rdx,QWORD PTR [rsp+0x18]
    3788:	xor    r8d,r8d
    378b:	xor    r9d,r9d
    378e:	lea    rax,[rip+0x3bcb]        # 7360 <_fini+0x2e4c>
    3795:	mov    ecx,DWORD PTR [rsp+0x8]
    3799:	mov    esi,DWORD PTR [rsp+0x20]
    379d:	mov    edi,0xa2
    37a2:	mov    QWORD PTR [rax+rdx*8],r8
    37a6:	movzx  edx,BYTE PTR [rsp]
    37aa:	xor    r8d,r8d
    37ad:	call   18d0 <free@plt+0x730>
    37b2:	jmp    1dbd <free@plt+0xc1d>
    37b7:	mov    eax,r9d
    37ba:	or     eax,r11d
    37bd:	cmp    al,0x7
    37bf:	ja     1eab <free@plt+0xd0b>
    37c5:	movzx  eax,r9b
    37c9:	lea    rdx,[rip+0x3b90]        # 7360 <_fini+0x2e4c>
    37d0:	movzx  esi,r9b
    37d4:	mov    rcx,QWORD PTR [rdx+rax*8]
    37d8:	test   rcx,rcx
    37db:	je     1eab <free@plt+0xd0b>
    37e1:	lea    rax,[rip+0x3b38]        # 7320 <_fini+0x2e0c>
    37e8:	movzx  edx,r11b
    37ec:	cmp    QWORD PTR [rax+rdx*8],0x0
    37f1:	jne    1eab <free@plt+0xd0b>
    37f7:	cmp    DWORD PTR [rsp+0x88],0x0
    37ff:	jne    1eab <free@plt+0xd0b>
    3805:	mov    QWORD PTR [rax+rdx*8],rcx
    3809:	xor    r9d,r9d
    380c:	xor    r8d,r8d
    380f:	mov    ecx,r10d
    3812:	movzx  edx,r11b
    3816:	mov    edi,0xa1
    381b:	call   18d0 <free@plt+0x730>
    3820:	jmp    1dbd <free@plt+0xc1d>
    3825:	cmp    r9b,0x7
    3829:	ja     1eab <free@plt+0xd0b>
    382f:	movzx  r14d,r9b
    3833:	lea    r15,[rip+0x3b26]        # 7360 <_fini+0x2e4c>
    383a:	movzx  ebp,r9b
    383e:	cmp    QWORD PTR [r15+r14*8],0x0
    3843:	jne    1eab <free@plt+0xd0b>
    3849:	cmp    DWORD PTR [rsp+0x88],0x0
    3851:	jne    1eab <free@plt+0xd0b>
    3857:	mov    esi,0x440
    385c:	mov    edi,0x1
    3861:	mov    DWORD PTR [rsp+0x18],r10d
    3866:	mov    BYTE PTR [rsp+0x8],r11b
    386b:	call   1090 <calloc@plt>
    3870:	mov    rdx,rax
    3873:	test   rax,rax
    3876:	je     1ade <free@plt+0x93e>
    387c:	movabs rax,0x34545845544e4f43
    3886:	lea    rdi,[rdx+0x8]
    388a:	mov    QWORD PTR [rsp],rdx
    388e:	mov    QWORD PTR [rdx],rax
    3891:	call   1a70 <free@plt+0x8d0>
    3896:	mov    rax,QWORD PTR [rip+0x3e03]        # 76a0 <_fini+0x318c>
    389d:	mov    rdx,QWORD PTR [rsp]
    38a1:	mov    rcx,QWORD PTR [rax+0xd8]
    38a8:	mov    QWORD PTR [rdx+0x30],0x1
    38b0:	mov    rdi,rdx
    38b3:	xor    rcx,rdx
    38b6:	mov    QWORD PTR [rdx+0x10],rcx
    38ba:	call   1690 <free@plt+0x4f0>
    38bf:	mov    rdx,QWORD PTR [rsp]
    38c3:	mov    ecx,DWORD PTR [rsp+0x18]
    38c7:	xor    r9d,r9d
    38ca:	xor    r8d,r8d
    38cd:	mov    esi,ebp
    38cf:	mov    edi,0xa0
    38d4:	mov    QWORD PTR [rdx+0x38],rax
    38d8:	mov    QWORD PTR [r15+r14*8],rdx
    38dc:	movzx  edx,BYTE PTR [rsp+0x8]
    38e1:	call   18d0 <free@plt+0x730>
    38e6:	jmp    1dbd <free@plt+0xc1d>
    38eb:	mov    eax,r9d
    38ee:	or     eax,r11d
    38f1:	cmp    al,0x7
    38f3:	ja     1eab <free@plt+0xd0b>
    38f9:	movzx  eax,r9b
    38fd:	lea    rdx,[rip+0x3bdc]        # 74e0 <_fini+0x2fcc>
    3904:	movzx  esi,r9b
    3908:	mov    rcx,QWORD PTR [rdx+rax*8]
    390c:	test   rcx,rcx
    390f:	je     1eab <free@plt+0xd0b>
    3915:	movzx  eax,r11b
    3919:	lea    rdx,[rip+0x3b00]        # 7420 <_fini+0x2f0c>
    3920:	movzx  r15d,r11b
    3924:	mov    rdx,QWORD PTR [rdx+rax*8]
    3928:	test   rdx,rdx
    392b:	je     1eab <free@plt+0xd0b>
    3931:	cmp    DWORD PTR [rsp+0x88],0x0
    3939:	jne    1eab <free@plt+0xd0b>
    393f:	mov    rax,QWORD PTR [rip+0x3d5a]        # 76a0 <_fini+0x318c>
    3946:	mov    DWORD PTR [rsp+0x20],esi
    394a:	mov    DWORD PTR [rsp+0x18],r10d
    394f:	mov    rdi,QWORD PTR [rax+0xd8]
    3956:	mov    QWORD PTR [rsp+0x8],rdx
    395b:	mov    QWORD PTR [rsp],rcx
    395f:	xor    rdi,rdx
    3962:	mov    QWORD PTR [rcx+0x20],rdi
    3966:	mov    rdi,QWORD PTR [rdx+0x8]
    396a:	mov    QWORD PTR [rcx+0x28],rdi
    396e:	mov    rdi,QWORD PTR [rax+0xd8]
    3975:	xor    rdi,rcx
    3978:	mov    QWORD PTR [rdx+0x18],rdi
    397c:	mov    rax,QWORD PTR [rcx+0x10]
    3980:	mov    rdi,rcx
    3983:	mov    QWORD PTR [rdx+0x20],rax
    3987:	call   15d0 <free@plt+0x430>
    398c:	mov    rcx,QWORD PTR [rsp]
    3990:	mov    rdx,QWORD PTR [rsp+0x8]
    3995:	mov    QWORD PTR [rcx+0x40],rax
    3999:	mov    rdi,rdx
    399c:	mov    QWORD PTR [rsp],rdx
    39a0:	call   1630 <free@plt+0x490>
    39a5:	mov    rdx,QWORD PTR [rsp]
    39a9:	mov    ecx,DWORD PTR [rsp+0x18]
    39ad:	xor    r9d,r9d
    39b0:	mov    esi,DWORD PTR [rsp+0x20]
    39b4:	xor    r8d,r8d
    39b7:	mov    edi,0x9a
    39bc:	mov    QWORD PTR [rdx+0x38],rax
    39c0:	mov    edx,r15d
    39c3:	call   18d0 <free@plt+0x730>
    39c8:	jmp    1dbd <free@plt+0xc1d>
    39cd:	cmp    r9b,0x7
    39d1:	ja     1eab <free@plt+0xd0b>
    39d7:	movzx  r8d,r9b
    39db:	lea    rax,[rip+0x39fe]        # 73e0 <_fini+0x2ecc>
    39e2:	mov    rdx,QWORD PTR [rax+r8*8]
    39e6:	test   rdx,rdx
    39e9:	je     1eab <free@plt+0xd0b>
    39ef:	lea    rax,[rip+0x39aa]        # 73a0 <_fini+0x2e8c>
    39f6:	cmp    QWORD PTR [rax+r8*8],0x0
    39fb:	jne    1eab <free@plt+0xd0b>
    3a01:	cmp    DWORD PTR [rsp+0x88],0xb0
    3a0c:	jne    1eab <free@plt+0xd0b>
    3a12:	mov    rdi,rdx
    3a15:	lea    rsi,[rsp+0x150]
    3a1d:	mov    ecx,0x2c
    3a22:	rep movs DWORD PTR es:[rdi],DWORD PTR ds:[rsi]
    3a24:	lea    rax,[rip+0x3975]        # 73a0 <_fini+0x2e8c>
    3a2b:	movzx  esi,r9b
    3a2f:	mov    ecx,r10d
    3a32:	mov    QWORD PTR [rax+r8*8],rdx
    3a36:	xor    r9d,r9d
    3a39:	movzx  edx,r11b
    3a3d:	xor    r8d,r8d
    3a40:	mov    edi,0x99
    3a45:	call   18d0 <free@plt+0x730>
    3a4a:	jmp    1dbd <free@plt+0xc1d>
    3a4f:	cmp    r9b,0x7
    3a53:	ja     1eab <free@plt+0xd0b>
    3a59:	movzx  eax,r9b
    3a5d:	lea    rdx,[rip+0x397c]        # 73e0 <_fini+0x2ecc>
    3a64:	movzx  esi,r9b
    3a68:	mov    r8,QWORD PTR [rdx+rax*8]
    3a6c:	test   r8,r8
    3a6f:	je     1eab <free@plt+0xd0b>
    3a75:	cmp    DWORD PTR [rsp+0x88],0x0
    3a7d:	jne    1eab <free@plt+0xd0b>
    3a83:	movzx  edx,r11b
    3a87:	mov    r9d,0x40
    3a8d:	mov    ecx,r10d
    3a90:	mov    edi,0x98
    3a95:	call   18d0 <free@plt+0x730>
    3a9a:	jmp    1dbd <free@plt+0xc1d>
    3a9f:	cmp    r9b,0x7
    3aa3:	ja     1eab <free@plt+0xd0b>
    3aa9:	lea    rax,[rip+0x3970]        # 7420 <_fini+0x2f0c>
    3ab0:	movzx  edx,r9b
    3ab4:	movzx  esi,r9b
    3ab8:	mov    rdi,QWORD PTR [rax+rdx*8]
    3abc:	test   rdi,rdi
    3abf:	je     1eab <free@plt+0xd0b>
    3ac5:	cmp    DWORD PTR [rsp+0x88],0x0
    3acd:	jne    1eab <free@plt+0xd0b>
    3ad3:	mov    QWORD PTR [rsp+0x18],rdx
    3ad8:	mov    DWORD PTR [rsp+0x20],esi
    3adc:	mov    DWORD PTR [rsp+0x8],r10d
    3ae1:	mov    BYTE PTR [rsp],r11b
    3ae5:	call   11a0 <free@plt>
    3aea:	mov    rdx,QWORD PTR [rsp+0x18]
    3aef:	xor    r9d,r9d
    3af2:	xor    r8d,r8d
    3af5:	lea    rax,[rip+0x3924]        # 7420 <_fini+0x2f0c>
    3afc:	mov    ecx,DWORD PTR [rsp+0x8]
    3b00:	mov    esi,DWORD PTR [rsp+0x20]
    3b04:	mov    edi,0x97
    3b09:	mov    QWORD PTR [rax+rdx*8],r9
    3b0d:	movzx  edx,BYTE PTR [rsp]
    3b11:	xor    r9d,r9d
    3b14:	call   18d0 <free@plt+0x730>
    3b19:	jmp    1dbd <free@plt+0xc1d>
    3b1e:	mov    eax,r9d
    3b21:	or     eax,r11d
    3b24:	cmp    al,0x7
    3b26:	ja     1eab <free@plt+0xd0b>
    3b2c:	movzx  eax,r9b
    3b30:	lea    rdx,[rip+0x38e9]        # 7420 <_fini+0x2f0c>
    3b37:	movzx  esi,r9b
    3b3b:	mov    rcx,QWORD PTR [rdx+rax*8]
    3b3f:	test   rcx,rcx
    3b42:	je     1eab <free@plt+0xd0b>
    3b48:	lea    rax,[rip+0x3891]        # 73e0 <_fini+0x2ecc>
    3b4f:	movzx  edx,r11b
    3b53:	cmp    QWORD PTR [rax+rdx*8],0x0
    3b58:	jne    1eab <free@plt+0xd0b>
    3b5e:	cmp    DWORD PTR [rsp+0x88],0x0
    3b66:	jne    1eab <free@plt+0xd0b>
    3b6c:	mov    QWORD PTR [rax+rdx*8],rcx
    3b70:	xor    r9d,r9d
    3b73:	xor    r8d,r8d
    3b76:	mov    ecx,r10d
    3b79:	movzx  edx,r11b
    3b7d:	mov    edi,0x96
    3b82:	call   18d0 <free@plt+0x730>
    3b87:	jmp    1dbd <free@plt+0xc1d>
    3b8c:	cmp    r9b,0x7
    3b90:	ja     1eab <free@plt+0xd0b>
    3b96:	movzx  r14d,r9b
    3b9a:	lea    r15,[rip+0x387f]        # 7420 <_fini+0x2f0c>
    3ba1:	movzx  ebp,r9b
    3ba5:	cmp    QWORD PTR [r15+r14*8],0x0
    3baa:	jne    1eab <free@plt+0xd0b>
    3bb0:	cmp    DWORD PTR [rsp+0x88],0x0
    3bb8:	jne    1eab <free@plt+0xd0b>
    3bbe:	mov    esi,0xb0
    3bc3:	mov    edi,0x1
    3bc8:	mov    DWORD PTR [rsp+0x18],r10d
    3bcd:	mov    BYTE PTR [rsp+0x8],r11b
    3bd2:	call   1090 <calloc@plt>
    3bd7:	mov    rdx,rax
    3bda:	test   rax,rax
    3bdd:	je     1ade <free@plt+0x93e>
    3be3:	movabs rax,0x34444552434c4156
    3bed:	lea    rdi,[rdx+0x8]
    3bf1:	mov    QWORD PTR [rsp],rdx
    3bf5:	mov    QWORD PTR [rdx],rax
    3bf8:	call   1a70 <free@plt+0x8d0>
    3bfd:	mov    rax,QWORD PTR [rip+0x3a9c]        # 76a0 <_fini+0x318c>
    3c04:	mov    rdx,QWORD PTR [rsp]
    3c08:	mov    rcx,QWORD PTR [rax+0xd8]
    3c0f:	mov    QWORD PTR [rdx+0x30],0x1
    3c17:	mov    rdi,rdx
    3c1a:	xor    rcx,rdx
    3c1d:	mov    QWORD PTR [rdx+0x10],rcx
    3c21:	call   1630 <free@plt+0x490>
    3c26:	mov    rdx,QWORD PTR [rsp]
    3c2a:	mov    ecx,DWORD PTR [rsp+0x18]
    3c2e:	xor    r9d,r9d
    3c31:	xor    r8d,r8d
    3c34:	mov    esi,ebp
    3c36:	mov    edi,0x95
    3c3b:	mov    QWORD PTR [rdx+0x38],rax
    3c3f:	mov    QWORD PTR [r15+r14*8],rdx
    3c43:	movzx  edx,BYTE PTR [rsp+0x8]
    3c48:	call   18d0 <free@plt+0x730>
    3c4d:	jmp    1dbd <free@plt+0xc1d>
    3c52:	cmp    r9b,0x7
    3c56:	ja     1eab <free@plt+0xd0b>
    3c5c:	movzx  ecx,r9b
    3c60:	lea    rax,[rip+0x3839]        # 74a0 <_fini+0x2f8c>
    3c67:	mov    r8,QWORD PTR [rax+rcx*8]
    3c6b:	mov    r15,rcx
    3c6e:	test   r8,r8
    3c71:	je     1eab <free@plt+0xd0b>
    3c77:	lea    rax,[rip+0x37e2]        # 7460 <_fini+0x2f4c>
    3c7e:	cmp    QWORD PTR [rax+rcx*8],0x0
    3c83:	jne    1eab <free@plt+0xd0b>
    3c89:	cmp    DWORD PTR [rsp+0x88],0x150
    3c94:	jne    1eab <free@plt+0xd0b>
    3c9a:	mov    rdx,QWORD PTR [rsp+0x150]
    3ca2:	lea    rdi,[r8+0x8]
    3ca6:	lea    rax,[rsp+0x150]
    3cae:	and    rdi,0xfffffffffffffff8
    3cb2:	mov    QWORD PTR [r8],rdx
    3cb5:	mov    rdx,QWORD PTR [rsp+0x298]
    3cbd:	mov    QWORD PTR [r8+0x148],rdx
    3cc4:	mov    rdx,r8
    3cc7:	sub    rdx,rdi
    3cca:	sub    rax,rdx
    3ccd:	lea    ecx,[rdx+0x150]
    3cd3:	movzx  edx,r11b
    3cd7:	mov    rsi,rax
    3cda:	shr    ecx,0x3
    3cdd:	lea    rax,[rip+0x377c]        # 7460 <_fini+0x2f4c>
    3ce4:	rep movs QWORD PTR es:[rdi],QWORD PTR ds:[rsi]
    3ce7:	mov    QWORD PTR [rax+r15*8],r8
    3ceb:	movzx  esi,r9b
    3cef:	xor    r8d,r8d
    3cf2:	xor    r9d,r9d
    3cf5:	mov    ecx,r10d
    3cf8:	mov    edi,0x94
    3cfd:	call   18d0 <free@plt+0x730>
    3d02:	jmp    1dbd <free@plt+0xc1d>
    3d07:	cmp    r9b,0x7
    3d0b:	ja     1eab <free@plt+0xd0b>
    3d11:	movzx  eax,r9b
    3d15:	lea    rdx,[rip+0x3784]        # 74a0 <_fini+0x2f8c>
    3d1c:	movzx  esi,r9b
    3d20:	mov    r8,QWORD PTR [rdx+rax*8]
    3d24:	test   r8,r8
    3d27:	je     1eab <free@plt+0xd0b>
    3d2d:	cmp    DWORD PTR [rsp+0x88],0x0
    3d35:	jne    1eab <free@plt+0xd0b>
    3d3b:	movzx  edx,r11b
    3d3f:	mov    r9d,0x48
    3d45:	mov    ecx,r10d
    3d48:	mov    edi,0x93
    3d4d:	call   18d0 <free@plt+0x730>
    3d52:	jmp    1dbd <free@plt+0xc1d>
    3d57:	cmp    r9b,0x7
    3d5b:	ja     1eab <free@plt+0xd0b>
    3d61:	lea    rax,[rip+0x3778]        # 74e0 <_fini+0x2fcc>
    3d68:	movzx  edx,r9b
    3d6c:	movzx  esi,r9b
    3d70:	mov    rdi,QWORD PTR [rax+rdx*8]
    3d74:	test   rdi,rdi
    3d77:	je     1eab <free@plt+0xd0b>
    3d7d:	cmp    DWORD PTR [rsp+0x88],0x0
    3d85:	jne    1eab <free@plt+0xd0b>
    3d8b:	mov    DWORD PTR [rsp+0x8],r10d
    3d90:	mov    QWORD PTR [rsp+0x18],rdx
    3d95:	mov    DWORD PTR [rsp+0x20],esi
    3d99:	mov    BYTE PTR [rsp],r11b
    3d9d:	call   11a0 <free@plt>
    3da2:	mov    rdx,QWORD PTR [rsp+0x18]
    3da7:	xor    r10d,r10d
    3daa:	xor    r9d,r9d
    3dad:	mov    ecx,DWORD PTR [rsp+0x8]
    3db1:	mov    esi,DWORD PTR [rsp+0x20]
    3db5:	xor    r8d,r8d
    3db8:	mov    edi,0x92
    3dbd:	lea    rax,[rip+0x371c]        # 74e0 <_fini+0x2fcc>
    3dc4:	mov    QWORD PTR [rax+rdx*8],r10
    3dc8:	movzx  edx,BYTE PTR [rsp]
    3dcc:	call   18d0 <free@plt+0x730>
    3dd1:	jmp    1dbd <free@plt+0xc1d>
    3dd6:	mov    eax,r9d
    3dd9:	or     eax,r11d
    3ddc:	cmp    al,0x7
    3dde:	ja     1eab <free@plt+0xd0b>
    3de4:	movzx  eax,r9b
    3de8:	lea    rdx,[rip+0x36f1]        # 74e0 <_fini+0x2fcc>
    3def:	movzx  esi,r9b
    3df3:	mov    rcx,QWORD PTR [rdx+rax*8]
    3df7:	test   rcx,rcx
    3dfa:	je     1eab <free@plt+0xd0b>
    3e00:	lea    rax,[rip+0x3699]        # 74a0 <_fini+0x2f8c>
    3e07:	movzx  edx,r11b
    3e0b:	cmp    QWORD PTR [rax+rdx*8],0x0
    3e10:	jne    1eab <free@plt+0xd0b>
    3e16:	cmp    DWORD PTR [rsp+0x88],0x0
    3e1e:	jne    1eab <free@plt+0xd0b>
    3e24:	mov    QWORD PTR [rax+rdx*8],rcx
    3e28:	xor    r9d,r9d
    3e2b:	xor    r8d,r8d
    3e2e:	mov    ecx,r10d
    3e31:	movzx  edx,r11b
    3e35:	mov    edi,0x91
    3e3a:	call   18d0 <free@plt+0x730>
    3e3f:	jmp    1dbd <free@plt+0xc1d>
    3e44:	cmp    r9b,0x7
    3e48:	ja     1eab <free@plt+0xd0b>
    3e4e:	movzx  eax,r9b
    3e52:	lea    rcx,[rip+0x3687]        # 74e0 <_fini+0x2fcc>
    3e59:	movzx  r14d,r9b
    3e5d:	mov    r15,rax
    3e60:	cmp    QWORD PTR [rcx+rax*8],0x0
    3e65:	jne    1eab <free@plt+0xd0b>
    3e6b:	cmp    DWORD PTR [rsp+0x88],0x8
    3e73:	jne    1eab <free@plt+0xd0b>
    3e79:	mov    esi,0x150
    3e7e:	mov    edi,0x1
    3e83:	mov    DWORD PTR [rsp+0x18],r10d
    3e88:	mov    BYTE PTR [rsp+0x8],r11b
    3e8d:	call   1090 <calloc@plt>
    3e92:	mov    rdx,rax
    3e95:	test   rax,rax
    3e98:	je     1ade <free@plt+0x93e>
    3e9e:	movabs rax,0x3454454b43495443
    3ea8:	lea    rdi,[rdx+0x10]
    3eac:	mov    QWORD PTR [rsp],rdx
    3eb0:	mov    QWORD PTR [rdx],rax
    3eb3:	mov    rax,QWORD PTR [rsp+0x150]
    3ebb:	mov    QWORD PTR [rdx+0x8],rax
    3ebf:	call   1a70 <free@plt+0x8d0>
    3ec4:	mov    rax,QWORD PTR [rip+0x37d5]        # 76a0 <_fini+0x318c>
    3ecb:	mov    rdx,QWORD PTR [rsp]
    3ecf:	mov    rcx,QWORD PTR [rax+0xd8]
    3ed6:	mov    QWORD PTR [rdx+0x38],0x1
    3ede:	mov    rdi,rdx
    3ee1:	xor    rcx,rdx
    3ee4:	mov    QWORD PTR [rdx+0x18],rcx
    3ee8:	call   15d0 <free@plt+0x430>
    3eed:	mov    rdx,QWORD PTR [rsp]
    3ef1:	mov    ecx,DWORD PTR [rsp+0x18]
    3ef5:	xor    r9d,r9d
    3ef8:	xor    r8d,r8d
    3efb:	mov    esi,r14d
    3efe:	mov    edi,0x90
    3f03:	mov    QWORD PTR [rdx+0x40],rax
    3f07:	lea    rax,[rip+0x35d2]        # 74e0 <_fini+0x2fcc>
    3f0e:	mov    QWORD PTR [rax+r15*8],rdx
    3f12:	movzx  edx,BYTE PTR [rsp+0x8]
    3f17:	call   18d0 <free@plt+0x730>
    3f1c:	jmp    1dbd <free@plt+0xc1d>
    3f21:	cmp    DWORD PTR [rsp+0x88],0xd0
    3f2c:	jne    1eab <free@plt+0xd0b>
    3f32:	mov    rdi,r8
    3f35:	lea    rsi,[rsp+0x150]
    3f3d:	mov    ecx,0x34
    3f42:	rep movs DWORD PTR es:[rdi],DWORD PTR ds:[rsi]
    3f44:	lea    rax,[rip+0x35d5]        # 7520 <_fini+0x300c>
    3f4b:	movzx  esi,r9b
    3f4f:	mov    ecx,r10d
    3f52:	mov    QWORD PTR [rax+rdx*8],r8
    3f56:	xor    r9d,r9d
    3f59:	movzx  edx,r11b
    3f5d:	xor    r8d,r8d
    3f60:	mov    edi,0x8c
    3f65:	call   18d0 <free@plt+0x730>
    3f6a:	jmp    1dbd <free@plt+0xc1d>
    3f6f:	mov    ecx,DWORD PTR [rsp]
    3f72:	xor    r9d,r9d
    3f75:	xor    r8d,r8d
    3f78:	mov    edx,r14d
    3f7b:	mov    esi,r15d
    3f7e:	mov    edi,0x81
    3f83:	mov    DWORD PTR [rip+0x30f7],0x1        # 7084 <_fini+0x2b70>
    3f8d:	call   18d0 <free@plt+0x730>
    3f92:	jmp    1dbd <free@plt+0xc1d>
    3f97:	cmp    al,0x79
    3f99:	je     3fe3 <free@plt+0x2e43>
    3f9b:	cmp    al,0x8b
    3f9d:	jne    404c <free@plt+0x2eac>
    3fa3:	mov    esi,r9d
    3fa6:	jmp    2826 <free@plt+0x1686>
    3fab:	mov    r14,QWORD PTR [rsp+0x38]
    3fb0:	movsxd rdi,esi
    3fb3:	mov    r11,QWORD PTR [r14+rdi*8+0x18]
    3fb8:	jmp    2881 <free@plt+0x16e1>
    3fbd:	xor    r11,QWORD PTR [rax+0x8]
    3fc1:	jmp    2881 <free@plt+0x16e1>
    3fc6:	movzx  edx,BYTE PTR [r8+0x1]
    3fcb:	add    BYTE PTR [rsp],dl
    3fce:	cmp    BYTE PTR [rsp],0x17
    3fd2:	jle    2824 <free@plt+0x1684>
    3fd8:	mov    r9d,r10d
    3fdb:	mov    r10d,r15d
    3fde:	jmp    1eab <free@plt+0xd0b>
    3fe3:	add    DWORD PTR [rsp+0x8],0x1
    3fe8:	cmp    DWORD PTR [rsp+0x8],0x1
    3fed:	ja     4078 <free@plt+0x2ed8>
    3ff3:	movsx  eax,BYTE PTR [rsp]
    3ff7:	cmp    eax,r14d
    3ffa:	je     2824 <free@plt+0x1684>
    4000:	mov    r9d,r10d
    4003:	mov    r10d,r15d
    4006:	jmp    1eab <free@plt+0xd0b>
    400b:	mov    r9d,r10d
    400e:	mov    r10d,r15d
    4011:	jmp    1eab <free@plt+0xd0b>
    4016:	mov    edx,DWORD PTR [rsp+0x20]
    401a:	mov    esi,DWORD PTR [rsp+0x18]
    401e:	mov    r8,r13
    4021:	mov    edi,0x80
    4026:	mov    QWORD PTR [rsp+0xd0],r11
    402e:	xor    r11d,r11d
    4031:	mov    r9d,0x8
    4037:	mov    QWORD PTR [rcx+0x30],r11
    403b:	mov    ecx,r10d
    403e:	mov    QWORD PTR [rbp+0x30],r11
    4042:	call   18d0 <free@plt+0x730>
    4047:	jmp    1dbd <free@plt+0xc1d>
    404c:	mov    r9d,r10d
    404f:	mov    r10d,r15d
    4052:	jmp    1eab <free@plt+0xd0b>
    4057:	mov    r9d,r10d
    405a:	mov    r10d,r15d
    405d:	jmp    1eab <free@plt+0xd0b>
    4062:	mov    r9d,r10d
    4065:	mov    r10d,r15d
    4068:	jmp    1eab <free@plt+0xd0b>
    406d:	mov    r9d,r10d
    4070:	mov    r10d,r15d
    4073:	jmp    1eab <free@plt+0xd0b>
    4078:	mov    r9d,r10d
    407b:	mov    r10d,r15d
    407e:	jmp    1eab <free@plt+0xd0b>
    4083:	movabs rax,0x34444552434c4156
    408d:	cmp    QWORD PTR [rsi],rax
    4090:	jne    2a0a <free@plt+0x186a>
    4096:	cmp    QWORD PTR [r8+0x38],0x1
    409b:	jne    2a0a <free@plt+0x186a>
    40a1:	cmp    QWORD PTR [rsi+0x30],0x1
    40a6:	jne    2a0a <free@plt+0x186a>
    40ac:	mov    rax,QWORD PTR [rip+0x35ed]        # 76a0 <_fini+0x318c>
    40b3:	mov    rax,QWORD PTR [rax+0xd8]
    40ba:	mov    QWORD PTR [rsp+0x8],rax
    40bf:	xor    rax,r8
    40c2:	cmp    QWORD PTR [r8+0x18],rax
    40c6:	jne    2a0a <free@plt+0x186a>
    40cc:	mov    rdx,QWORD PTR [rsp+0x8]
    40d1:	xor    rdx,rsi
    40d4:	cmp    QWORD PTR [rsi+0x10],rdx
    40d8:	jne    2a0a <free@plt+0x186a>
    40de:	cmp    rdx,QWORD PTR [r8+0x20]
    40e2:	jne    2a0a <free@plt+0x186a>
    40e8:	cmp    rax,QWORD PTR [rsi+0x18]
    40ec:	jne    2a0a <free@plt+0x186a>
    40f2:	mov    rax,QWORD PTR [rsi+0x8]
    40f6:	cmp    QWORD PTR [r8+0x28],rax
    40fa:	jne    2a0a <free@plt+0x186a>
    4100:	mov    rcx,QWORD PTR [r8+0x10]
    4104:	mov    QWORD PTR [rsp+0x20],rcx
    4109:	cmp    QWORD PTR [rsi+0x20],rcx
    410d:	jne    2a0a <free@plt+0x186a>
    4113:	mov    rcx,QWORD PTR [r14+0x8]
    4117:	mov    QWORD PTR [rsp+0x28],rcx
    411c:	cmp    QWORD PTR [rsi+0x28],rcx
    4120:	jne    2a0a <free@plt+0x186a>
    4126:	mov    r14,QWORD PTR [r8+0x30]
    412a:	movq   xmm5,rax
    412f:	mov    rdi,QWORD PTR [rsp+0x8]
    4134:	mov    rdx,r13
    4137:	movq   xmm0,rbp
    413c:	movhps xmm0,QWORD PTR [rsp+0x28]
    4141:	mov    ecx,0x4
    4146:	movaps XMMWORD PTR [rsp+0xd0],xmm0
    414e:	movq   xmm0,rsi
    4153:	mov    rsi,QWORD PTR [rsp+0x20]
    4158:	mov    DWORD PTR [rsp+0x48],r10d
    415d:	punpcklqdq xmm0,xmm5
    4161:	mov    BYTE PTR [rsp+0x40],r11b
    4166:	mov    BYTE PTR [rsp+0x38],r9b
    416b:	mov    QWORD PTR [rsp+0x30],r8
    4170:	movaps XMMWORD PTR [rsp+0xe0],xmm0
    4178:	call   1410 <free@plt+0x270>
    417d:	mov    r8,QWORD PTR [rsp+0x30]
    4182:	movzx  r9d,BYTE PTR [rsp+0x38]
    4188:	cmp    r14,rax
    418b:	movzx  r11d,BYTE PTR [rsp+0x40]
    4191:	mov    r10d,DWORD PTR [rsp+0x48]
    4196:	jne    2a0a <free@plt+0x186a>
    419c:	mov    r14,QWORD PTR [r8+0x40]
    41a0:	mov    rdi,r8
    41a3:	mov    DWORD PTR [rsp+0x40],r10d
    41a8:	mov    BYTE PTR [rsp+0x38],r11b
    41ad:	mov    BYTE PTR [rsp+0x30],r9b
    41b2:	call   15d0 <free@plt+0x430>
    41b7:	movzx  r9d,BYTE PTR [rsp+0x30]
    41bd:	movzx  r11d,BYTE PTR [rsp+0x38]
    41c3:	cmp    r14,rax
    41c6:	mov    r10d,DWORD PTR [rsp+0x40]
    41cb:	jne    2a0a <free@plt+0x186a>
    41d1:	mov    rdi,r15
    41d4:	mov    r15,QWORD PTR [r15+0x38]
    41d8:	call   1630 <free@plt+0x490>
    41dd:	movzx  r9d,BYTE PTR [rsp+0x30]
    41e3:	movzx  r11d,BYTE PTR [rsp+0x38]
    41e9:	cmp    r15,rax
    41ec:	mov    r10d,DWORD PTR [rsp+0x40]
    41f1:	jne    2a0a <free@plt+0x186a>
    41f7:	cmp    QWORD PTR [rsp],0x0
    41fc:	je     2a0a <free@plt+0x186a>
    4202:	movabs rax,0x34545845544e4f43
    420c:	cmp    QWORD PTR [rbp+0x0],rax
    4210:	jne    2a0a <free@plt+0x186a>
    4216:	movabs rax,0x344e414c50564c43
    4220:	mov    rcx,QWORD PTR [rsp]
    4224:	cmp    QWORD PTR [rcx],rax
    4227:	jne    2a0a <free@plt+0x186a>
    422d:	cmp    QWORD PTR [rbp+0x30],0x1
    4232:	jne    2a0a <free@plt+0x186a>
    4238:	cmp    QWORD PTR [rcx+0x38],0x1
    423d:	jne    2a0a <free@plt+0x186a>
    4243:	mov    rcx,QWORD PTR [rsp+0x8]
    4248:	mov    rdx,rbp
    424b:	xor    rdx,rcx
    424e:	cmp    QWORD PTR [rbp+0x10],rdx
    4252:	jne    2a0a <free@plt+0x186a>
    4258:	mov    rax,rcx
    425b:	mov    rcx,QWORD PTR [rsp]
    425f:	xor    rax,rcx
    4262:	cmp    QWORD PTR [rcx+0x10],rax
    4266:	jne    2a0a <free@plt+0x186a>
    426c:	cmp    rax,QWORD PTR [rbp+0x18]
    4270:	jne    2a0a <free@plt+0x186a>
    4276:	mov    rax,QWORD PTR [rsp]
    427a:	cmp    rdx,QWORD PTR [rax+0x18]
    427e:	jne    2a0a <free@plt+0x186a>
    4284:	mov    rcx,QWORD PTR [rsp]
    4288:	mov    rcx,QWORD PTR [rcx+0x8]
    428c:	cmp    QWORD PTR [rbp+0x20],rcx
    4290:	jne    2a0a <free@plt+0x186a>
    4296:	mov    rax,QWORD PTR [rsp]
    429a:	mov    rcx,QWORD PTR [rsp+0x28]
    429f:	cmp    rcx,QWORD PTR [rax+0x20]
    42a3:	jne    2a0a <free@plt+0x186a>
    42a9:	mov    rcx,QWORD PTR [rsp+0x20]
    42ae:	cmp    rcx,QWORD PTR [rbp+0x28]
    42b2:	jne    2a0a <free@plt+0x186a>
    42b8:	mov    r14,QWORD PTR [rbp+0x38]
    42bc:	mov    rdi,rbp
    42bf:	mov    DWORD PTR [rsp+0x28],r10d
    42c4:	mov    BYTE PTR [rsp+0x20],r11b
    42c9:	mov    BYTE PTR [rsp+0x8],r9b
    42ce:	call   1690 <free@plt+0x4f0>
    42d3:	movzx  r9d,BYTE PTR [rsp+0x8]
    42d9:	movzx  r11d,BYTE PTR [rsp+0x20]
    42df:	cmp    r14,rax
    42e2:	mov    r10d,DWORD PTR [rsp+0x28]
    42e7:	jne    2a0a <free@plt+0x186a>
    42ed:	mov    rdi,QWORD PTR [rsp]
    42f1:	mov    r15,QWORD PTR [rdi+0x40]
    42f5:	call   16e0 <free@plt+0x540>
    42fa:	xor    ecx,ecx
    42fc:	movzx  r9d,BYTE PTR [rsp+0x8]
    4302:	movzx  r11d,BYTE PTR [rsp+0x20]
    4308:	cmp    r15,rax
    430b:	mov    r10d,DWORD PTR [rsp+0x28]
    4310:	sete   cl
    4313:	jmp    2a0c <free@plt+0x186c>
    4318:	lea    rdi,[rip+0x2e81]        # 71a0 <_fini+0x2c8c>
    431f:	mov    r8,QWORD PTR [rdi+rdx*8]
    4323:	mov    rdx,QWORD PTR [rsp+0x18]
    4328:	mov    QWORD PTR [rdx+rsi*8],r8
    432c:	lea    rdx,[rip+0x2dad]        # 70e0 <_fini+0x2bcc>
    4333:	mov    r9,QWORD PTR [rdx+rax*8]
    4337:	mov    rax,QWORD PTR [rsp+0x10]
    433c:	mov    QWORD PTR [rax+rsi*8],r9
    4340:	test   r8,r8
    4343:	je     4359 <free@plt+0x31b9>
    4345:	test   r9,r9
    4348:	je     4359 <free@plt+0x31b9>
    434a:	movabs rax,0x344b4e5548434c43
    4354:	cmp    QWORD PTR [r8],rax
    4357:	je     438c <free@plt+0x31ec>
    4359:	xor    ecx,ecx
    435b:	xor    eax,eax
    435d:	cmp    rax,rsi
    4360:	je     2a59 <free@plt+0x18b9>
    4366:	mov    rdx,QWORD PTR [rsp+0x18]
    436b:	cmp    r8,QWORD PTR [rdx+rax*8]
    436f:	je     44d2 <free@plt+0x3332>
    4375:	mov    rdx,QWORD PTR [rsp+0x10]
    437a:	cmp    QWORD PTR [rdx+rax*8],r9
    437e:	setne  dl
    4381:	movzx  edx,dl
    4384:	and    ecx,edx
    4386:	add    rax,0x1
    438a:	jmp    435d <free@plt+0x31bd>
    438c:	movabs rax,0x344c414553564c43
    4396:	cmp    QWORD PTR [r9],rax
    4399:	jne    4359 <free@plt+0x31b9>
    439b:	cmp    QWORD PTR [r8+0x8],rsi
    439f:	jne    4359 <free@plt+0x31b9>
    43a1:	cmp    QWORD PTR [r9+0x8],rsi
    43a5:	jne    4359 <free@plt+0x31b9>
    43a7:	mov    rax,QWORD PTR [rip+0x32f2]        # 76a0 <_fini+0x318c>
    43ae:	mov    rdx,r8
    43b1:	mov    rax,QWORD PTR [rax+0xd8]
    43b8:	xor    rdx,rax
    43bb:	cmp    QWORD PTR [r8+0x18],rdx
    43bf:	jne    4359 <free@plt+0x31b9>
    43c1:	xor    rax,r9
    43c4:	cmp    QWORD PTR [r9+0x18],rax
    43c8:	jne    4359 <free@plt+0x31b9>
    43ca:	cmp    rax,QWORD PTR [r8+0x20]
    43ce:	jne    4359 <free@plt+0x31b9>
    43d0:	cmp    rdx,QWORD PTR [r9+0x20]
    43d4:	jne    4359 <free@plt+0x31b9>
    43d6:	mov    rax,QWORD PTR [r9+0x10]
    43da:	cmp    QWORD PTR [r8+0x28],rax
    43de:	jne    4359 <free@plt+0x31b9>
    43e4:	mov    rdi,QWORD PTR [r8+0x10]
    43e8:	cmp    QWORD PTR [r9+0x28],rdi
    43ec:	jne    4359 <free@plt+0x31b9>
    43f2:	mov    r10,QWORD PTR [r8+0x30]
    43f6:	lea    rdx,[r8+0x40]
    43fa:	mov    DWORD PTR [rsp+0x54],ecx
    43fe:	mov    QWORD PTR [rsp+0x48],r9
    4403:	mov    QWORD PTR [rsp+0x40],r10
    4408:	mov    QWORD PTR [rsp+0x38],r8
    440d:	mov    QWORD PTR [rsp+0x30],rsi
    4412:	call   1820 <free@plt+0x680>
    4417:	mov    r10,QWORD PTR [rsp+0x40]
    441c:	mov    rsi,QWORD PTR [rsp+0x30]
    4421:	mov    r8,QWORD PTR [rsp+0x38]
    4426:	mov    r9,QWORD PTR [rsp+0x48]
    442b:	cmp    r10,rax
    442e:	mov    ecx,DWORD PTR [rsp+0x54]
    4432:	jne    4359 <free@plt+0x31b9>
    4438:	cmp    r10,QWORD PTR [r9+0x30]
    443c:	jne    4359 <free@plt+0x31b9>
    4442:	mov    r14,QWORD PTR [r8+0x38]
    4446:	mov    rdi,r8
    4449:	mov    QWORD PTR [rsp+0x40],rsi
    444e:	mov    QWORD PTR [rsp+0x38],r9
    4453:	mov    QWORD PTR [rsp+0x30],r8
    4458:	mov    DWORD PTR [rsp+0x48],ecx
    445c:	call   1740 <free@plt+0x5a0>
    4461:	mov    r8,QWORD PTR [rsp+0x30]
    4466:	mov    r9,QWORD PTR [rsp+0x38]
    446b:	cmp    r14,rax
    446e:	mov    rsi,QWORD PTR [rsp+0x40]
    4473:	jne    4359 <free@plt+0x31b9>
    4479:	mov    r15,QWORD PTR [r9+0x38]
    447d:	mov    rdi,r9
    4480:	mov    QWORD PTR [rsp+0x38],r8
    4485:	mov    QWORD PTR [rsp+0x30],r9
    448a:	call   1790 <free@plt+0x5f0>
    448f:	mov    ecx,DWORD PTR [rsp+0x48]
    4493:	mov    r9,QWORD PTR [rsp+0x30]
    4498:	cmp    r15,rax
    449b:	mov    r8,QWORD PTR [rsp+0x38]
    44a0:	mov    rsi,QWORD PTR [rsp+0x40]
    44a5:	sete   al
    44a8:	movzx  eax,al
    44ab:	and    ecx,eax
    44ad:	jmp    435b <free@plt+0x31bb>
    44b2:	movzx  esi,r9b
    44b6:	movzx  edx,r11b
    44ba:	xor    r9d,r9d
    44bd:	xor    r8d,r8d
    44c0:	mov    ecx,r10d
    44c3:	mov    edi,0xe4
    44c8:	call   18d0 <free@plt+0x730>
    44cd:	jmp    1dbd <free@plt+0xc1d>
    44d2:	xor    ecx,ecx
    44d4:	jmp    4386 <free@plt+0x31e6>
    44d9:	nop    DWORD PTR [rax+0x0]
    44e0:	lea    rsp,[rdi+0x40]
    44e4:	ret
    44e5:	ud2
    44e7:	nop    WORD PTR [rax+rax*1+0x0]
    44f0:	pop    rdi
    44f1:	ret
    44f2:	ud2
    44f4:	nop
    44f5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    4500:	pop    rsi
    4501:	ret
    4502:	ud2
    4504:	nop
    4505:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    4510:	pop    rdx
    4511:	ret
    4512:	ud2

Disassembly of section .fini:

0000000000004514 <_fini>:
    4514:	push   rax
    4515:	pop    rax
    4516:	ret
