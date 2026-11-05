
cachebroker:     file format elf64-x86-64


Disassembly of section .init:

0000000000001000 <_init>:
    1000:	push   rax
    1001:	pop    rax
    1002:	ret

Disassembly of section .plt:

0000000000001010 <connect@plt-0x10>:
    1010:	push   QWORD PTR [rip+0x5eea]        # 6f00 <_fini+0x2dde>
    1016:	jmp    QWORD PTR [rip+0x5eec]        # 6f08 <_fini+0x2de6>
    101c:	nop    DWORD PTR [rax+0x0]

0000000000001020 <connect@plt>:
    1020:	jmp    QWORD PTR [rip+0x5eea]        # 6f10 <connect>
    1026:	push   0x0
    102b:	jmp    1010 <_init+0x10>

0000000000001030 <syscall@plt>:
    1030:	jmp    QWORD PTR [rip+0x5ee2]        # 6f18 <syscall>
    1036:	push   0x1
    103b:	jmp    1010 <_init+0x10>

0000000000001040 <prctl@plt>:
    1040:	jmp    QWORD PTR [rip+0x5eda]        # 6f20 <prctl>
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

0000000000001100 <listen@plt>:
    1100:	jmp    QWORD PTR [rip+0x5e7a]        # 6f80 <listen>
    1106:	push   0xe
    110b:	jmp    1010 <_init+0x10>

0000000000001110 <fork@plt>:
    1110:	jmp    QWORD PTR [rip+0x5e72]        # 6f88 <fork>
    1116:	push   0xf
    111b:	jmp    1010 <_init+0x10>

0000000000001120 <ntohs@plt>:
    1120:	jmp    QWORD PTR [rip+0x5e6a]        # 6f90 <ntohs>
    1126:	push   0x10
    112b:	jmp    1010 <_init+0x10>

0000000000001130 <poll@plt>:
    1130:	jmp    QWORD PTR [rip+0x5e62]        # 6f98 <poll>
    1136:	push   0x11
    113b:	jmp    1010 <_init+0x10>

0000000000001140 <__errno_location@plt>:
    1140:	jmp    QWORD PTR [rip+0x5e5a]        # 6fa0 <__errno_location>
    1146:	push   0x12
    114b:	jmp    1010 <_init+0x10>

0000000000001150 <getrandom@plt>:
    1150:	jmp    QWORD PTR [rip+0x5e52]        # 6fa8 <getrandom>
    1156:	push   0x13
    115b:	jmp    1010 <_init+0x10>

0000000000001160 <_exit@plt>:
    1160:	jmp    QWORD PTR [rip+0x5e4a]        # 6fb0 <_exit>
    1166:	push   0x14
    116b:	jmp    1010 <_init+0x10>

0000000000001170 <__libc_start_main@plt>:
    1170:	jmp    QWORD PTR [rip+0x5e42]        # 6fb8 <__libc_start_main>
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

0000000000002000 <.text>:
    2000:	push   rbx
    2001:	mov    esi,0x1
    2006:	mov    edi,0x11
    200b:	add    rsp,0xffffffffffffff80
    200f:	call   10d0 <signal@plt>
    2014:	xor    edx,edx
    2016:	mov    esi,0x1
    201b:	mov    edi,0x1
    2020:	call   1050 <socket@plt>
    2025:	test   eax,eax
    2027:	js     207b <free@plt+0xedb>
    2029:	lea    rdi,[rip+0x30a0]        # 50d0 <_fini+0xfae>
    2030:	mov    ebx,eax
    2032:	call   10f0 <unlink@plt>
    2037:	movdqa xmm0,XMMWORD PTR [rip+0x3091]        # 50d0 <_fini+0xfae>
    203f:	xor    eax,eax
    2041:	mov    ecx,0x51
    2046:	lea    rdi,[rsp+0x2d]
    204b:	lea    rsi,[rsp+0x10]
    2050:	mov    edx,0x6e
    2055:	mov    WORD PTR [rsp+0x10],0x1
    205c:	rep stos BYTE PTR es:[rdi],al
    205e:	movups XMMWORD PTR [rsp+0x12],xmm0
    2063:	movdqu xmm0,XMMWORD PTR [rip+0x3070]        # 50db <_fini+0xfb9>
    206b:	mov    edi,ebx
    206d:	movups XMMWORD PTR [rsp+0x1d],xmm0
    2072:	call   10b0 <bind@plt>
    2077:	test   eax,eax
    2079:	je     2086 <free@plt+0xee6>
    207b:	sub    rsp,0xffffffffffffff80
    207f:	mov    eax,0x1
    2084:	pop    rbx
    2085:	ret
    2086:	mov    esi,0x1b6
    208b:	lea    rdi,[rip+0x303e]        # 50d0 <_fini+0xfae>
    2092:	call   1060 <chmod@plt>
    2097:	test   eax,eax
    2099:	jne    207b <free@plt+0xedb>
    209b:	mov    esi,0x20
    20a0:	mov    edi,ebx
    20a2:	call   1100 <listen@plt>
    20a7:	test   eax,eax
    20a9:	jne    207b <free@plt+0xedb>
    20ab:	mov    edi,0x3e9
    20b0:	call   10c0 <setgid@plt>
    20b5:	test   eax,eax
    20b7:	jne    207b <free@plt+0xedb>
    20b9:	mov    edi,0x3e9
    20be:	call   1180 <setuid@plt>
    20c3:	test   eax,eax
    20c5:	jne    207b <free@plt+0xedb>
    20c7:	xor    edx,edx
    20c9:	xor    esi,esi
    20cb:	mov    edi,ebx
    20cd:	call   1080 <accept@plt>
    20d2:	test   eax,eax
    20d4:	jns    20e2 <free@plt+0xf42>
    20d6:	call   1140 <__errno_location@plt>
    20db:	cmp    DWORD PTR [rax],0x4
    20de:	jne    207b <free@plt+0xedb>
    20e0:	jmp    20c7 <free@plt+0xf27>
    20e2:	mov    DWORD PTR [rsp+0xc],eax
    20e6:	call   1110 <fork@plt>
    20eb:	test   eax,eax
    20ed:	je     20fa <free@plt+0xf5a>
    20ef:	mov    edi,DWORD PTR [rsp+0xc]
    20f3:	call   1190 <close@plt>
    20f8:	jmp    20c7 <free@plt+0xf27>
    20fa:	mov    edi,ebx
    20fc:	call   1190 <close@plt>
    2101:	mov    edi,DWORD PTR [rsp+0xc]
    2105:	call   26b0 <free@plt+0x1510>
    210a:	xor    rbp,rbp
    210d:	mov    rdi,rsp
    2110:	lea    rsi,[rip+0x4c21]        # 6d38 <_fini+0x2c16>
    2117:	and    rsp,0xfffffffffffffff0
    211b:	call   2120 <free@plt+0xf80>
    2120:	mov    esi,DWORD PTR [rdi]
    2122:	lea    rdx,[rdi+0x8]
    2126:	lea    r8,[rip+0x1ff5]        # 4122 <_fini>
    212d:	xor    r9d,r9d
    2130:	lea    rcx,[rip+0xffffffffffffeec9]        # 1000 <_init>
    2137:	lea    rdi,[rip+0xfffffffffffffec2]        # 2000 <free@plt+0xe60>
    213e:	jmp    1170 <__libc_start_main@plt>
    2143:	cs nop WORD PTR [rax+rax*1+0x0]
    214d:	nop    DWORD PTR [rax]
    2150:	lea    rdi,[rip+0x4eb9]        # 7010 <_fini+0x2eee>
    2157:	lea    rax,[rip+0x4eb2]        # 7010 <_fini+0x2eee>
    215e:	cmp    rax,rdi
    2161:	je     2178 <free@plt+0xfd8>
    2163:	mov    rax,QWORD PTR [rip+0x4e86]        # 6ff0 <_ITM_deregisterTMCloneTable>
    216a:	test   rax,rax
    216d:	je     2178 <free@plt+0xfd8>
    216f:	jmp    rax
    2171:	nop    DWORD PTR [rax+0x0]
    2178:	ret
    2179:	nop    DWORD PTR [rax+0x0]
    2180:	lea    rdi,[rip+0x4e89]        # 7010 <_fini+0x2eee>
    2187:	lea    rsi,[rip+0x4e82]        # 7010 <_fini+0x2eee>
    218e:	sub    rsi,rdi
    2191:	mov    rax,rsi
    2194:	shr    rsi,0x3f
    2198:	sar    rax,0x3
    219c:	add    rsi,rax
    219f:	sar    rsi,1
    21a2:	je     21b8 <free@plt+0x1018>
    21a4:	mov    rax,QWORD PTR [rip+0x4e3d]        # 6fe8 <_ITM_registerTMCloneTable>
    21ab:	test   rax,rax
    21ae:	je     21b8 <free@plt+0x1018>
    21b0:	jmp    rax
    21b2:	nop    WORD PTR [rax+rax*1+0x0]
    21b8:	ret
    21b9:	nop    DWORD PTR [rax+0x0]
    21c0:	cmp    BYTE PTR [rip+0x4e59],0x0        # 7020 <_fini+0x2efe>
    21c7:	jne    2210 <free@plt+0x1070>
    21c9:	push   rbp
    21ca:	cmp    QWORD PTR [rip+0x4e06],0x0        # 6fd8 <__cxa_finalize>
    21d2:	mov    rbp,rsp
    21d5:	je     21e4 <free@plt+0x1044>
    21d7:	mov    rdi,QWORD PTR [rip+0x4e22]        # 7000 <_fini+0x2ede>
    21de:	call   QWORD PTR [rip+0x4df4]        # 6fd8 <__cxa_finalize>
    21e4:	call   2150 <free@plt+0xfb0>
    21e9:	cmp    QWORD PTR [rip+0x4def],0x0        # 6fe0 <__deregister_frame_info>
    21f1:	je     2200 <free@plt+0x1060>
    21f3:	lea    rdi,[rip+0x2fb6]        # 51b0 <_fini+0x108e>
    21fa:	call   QWORD PTR [rip+0x4de0]        # 6fe0 <__deregister_frame_info>
    2200:	mov    BYTE PTR [rip+0x4e19],0x1        # 7020 <_fini+0x2efe>
    2207:	pop    rbp
    2208:	ret
    2209:	nop    DWORD PTR [rax+0x0]
    2210:	ret
    2211:	nop    DWORD PTR [rax+0x0]
    2215:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2220:	cmp    QWORD PTR [rip+0x4dd0],0x0        # 6ff8 <__register_frame_info>
    2228:	je     2250 <free@plt+0x10b0>
    222a:	push   rbp
    222b:	lea    rsi,[rip+0x4e0e]        # 7040 <_fini+0x2f1e>
    2232:	lea    rdi,[rip+0x2f77]        # 51b0 <_fini+0x108e>
    2239:	mov    rbp,rsp
    223c:	call   QWORD PTR [rip+0x4db6]        # 6ff8 <__register_frame_info>
    2242:	pop    rbp
    2243:	jmp    2180 <free@plt+0xfe0>
    2248:	nop    DWORD PTR [rax+rax*1+0x0]
    2250:	jmp    2180 <free@plt+0xfe0>
    2255:	cs nop WORD PTR [rax+rax*1+0x0]
    225f:	nop
    2260:	mov    rax,rdi
    2263:	push   r14
    2265:	mov    r11,rdi
    2268:	movabs r10,0xbf58476d1ce4e5b9
    2272:	push   r13
    2274:	xor    rax,rcx
    2277:	xor    edi,edi
    2279:	movabs r9,0x94d049bb133111eb
    2283:	push   r12
    2285:	mov    r12,rsi
    2288:	mov    rsi,rdx
    228b:	movabs rdx,0x9e3779b97f4a7c15
    2295:	xor    rax,rdx
    2298:	push   rbp
    2299:	lea    r13,[rsi+rcx*8]
    229d:	mov    r8,r12
    22a0:	mov    rdx,rax
    22a3:	push   rbx
    22a4:	mov    ecx,0x11
    22a9:	movabs rbp,0x517cc1b727220a95
    22b3:	movabs rbx,0x6a09e667f3bcc909
    22bd:	shr    rdx,0x1e
    22c1:	xor    rdx,rax
    22c4:	imul   rdx,r10
    22c8:	mov    rax,rdx
    22cb:	shr    rax,0x1b
    22cf:	xor    rax,rdx
    22d2:	imul   rax,r9
    22d6:	mov    rdx,rax
    22d9:	shr    rdx,0x1f
    22dd:	xor    rdx,rax
    22e0:	mov    r14,QWORD PTR [rsi]
    22e3:	add    rsi,0x8
    22e7:	add    r14,r8
    22ea:	add    r8,rbp
    22ed:	mov    rax,r14
    22f0:	shr    rax,0x1e
    22f4:	xor    rax,r14
    22f7:	imul   rax,r10
    22fb:	mov    r14,rax
    22fe:	shr    r14,0x1b
    2302:	xor    rax,r14
    2305:	imul   rax,r9
    2309:	mov    r14,rax
    230c:	shr    r14,0x1f
    2310:	xor    rax,r14
    2313:	xor    rax,rdx
    2316:	mov    rdx,r11
    2319:	rol    rax,cl
    231c:	xor    rdx,rdi
    231f:	add    ecx,0xb
    2322:	add    rdi,rbx
    2325:	add    rdx,rax
    2328:	cmp    r13,rsi
    232b:	jne    22e0 <free@plt+0x1140>
    232d:	movabs rax,0xa54ff53a5f1d36f1
    2337:	xor    r12,rdx
    233a:	pop    rbx
    233b:	pop    rbp
    233c:	xor    r12,rax
    233f:	mov    rdx,r12
    2342:	shr    rdx,0x1e
    2346:	xor    rdx,r12
    2349:	pop    r12
    234b:	pop    r13
    234d:	imul   rdx,r10
    2351:	pop    r14
    2353:	mov    rax,rdx
    2356:	shr    rax,0x1b
    235a:	xor    rdx,rax
    235d:	imul   rdx,r9
    2361:	mov    rax,rdx
    2364:	shr    rax,0x1f
    2368:	xor    rax,rdx
    236b:	ret
    236c:	nop    DWORD PTR [rax+0x0]
    2370:	sub    rsp,0x48
    2374:	mov    rax,QWORD PTR [rdi+0x30]
    2378:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    237d:	mov    ecx,0x7
    2382:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    2387:	movdqu xmm2,XMMWORD PTR [rdi]
    238b:	mov    rdx,rsp
    238e:	mov    rsi,QWORD PTR [rip+0x4cf3]        # 7088 <_fini+0x2f66>
    2395:	mov    rdi,QWORD PTR [rip+0x4cfc]        # 7098 <_fini+0x2f76>
    239c:	mov    QWORD PTR [rsp+0x30],rax
    23a1:	movaps XMMWORD PTR [rsp],xmm2
    23a5:	movaps XMMWORD PTR [rsp+0x10],xmm1
    23aa:	movaps XMMWORD PTR [rsp+0x20],xmm0
    23af:	call   2260 <free@plt+0x10c0>
    23b4:	add    rsp,0x48
    23b8:	ret
    23b9:	nop    DWORD PTR [rax+0x0]
    23c0:	sub    rsp,0x48
    23c4:	mov    rax,QWORD PTR [rdi+0x30]
    23c8:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    23cd:	mov    ecx,0x7
    23d2:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    23d7:	movdqu xmm2,XMMWORD PTR [rdi]
    23db:	mov    rdx,rsp
    23de:	mov    rsi,QWORD PTR [rip+0x4ca3]        # 7088 <_fini+0x2f66>
    23e5:	mov    rdi,QWORD PTR [rip+0x4cac]        # 7098 <_fini+0x2f76>
    23ec:	mov    QWORD PTR [rsp+0x30],rax
    23f1:	movabs rax,0x243f6a8885a308d3
    23fb:	movaps XMMWORD PTR [rsp],xmm2
    23ff:	xor    rdi,rax
    2402:	movaps XMMWORD PTR [rsp+0x10],xmm1
    2407:	movaps XMMWORD PTR [rsp+0x20],xmm0
    240c:	call   2260 <free@plt+0x10c0>
    2411:	add    rsp,0x48
    2415:	ret
    2416:	cs nop WORD PTR [rax+rax*1+0x0]
    2420:	sub    rsp,0x48
    2424:	mov    rax,QWORD PTR [rdi+0x30]
    2428:	movdqu xmm1,XMMWORD PTR [rdi+0x10]
    242d:	mov    ecx,0x7
    2432:	movdqu xmm0,XMMWORD PTR [rdi+0x20]
    2437:	movdqu xmm2,XMMWORD PTR [rdi]
    243b:	mov    rdx,rsp
    243e:	mov    rsi,QWORD PTR [rip+0x4c43]        # 7088 <_fini+0x2f66>
    2445:	mov    rdi,QWORD PTR [rip+0x4c44]        # 7090 <_fini+0x2f6e>
    244c:	mov    QWORD PTR [rsp+0x30],rax
    2451:	movaps XMMWORD PTR [rsp],xmm2
    2455:	movaps XMMWORD PTR [rsp+0x10],xmm1
    245a:	movaps XMMWORD PTR [rsp+0x20],xmm0
    245f:	call   2260 <free@plt+0x10c0>
    2464:	add    rsp,0x48
    2468:	ret
    2469:	nop    DWORD PTR [rax+0x0]
    2470:	sub    rsp,0x48
    2474:	movdqu xmm2,XMMWORD PTR [rdi+0x10]
    2479:	movdqu xmm1,XMMWORD PTR [rdi+0x20]
    247e:	movabs rax,0x13198a2e03707344
    2488:	movdqu xmm0,XMMWORD PTR [rdi+0x30]
    248d:	movdqu xmm3,XMMWORD PTR [rdi]
    2491:	mov    rdx,rsp
    2494:	mov    ecx,0x8
    2499:	mov    rsi,QWORD PTR [rip+0x4be8]        # 7088 <_fini+0x2f66>
    24a0:	mov    rdi,QWORD PTR [rip+0x4be9]        # 7090 <_fini+0x2f6e>
    24a7:	movaps XMMWORD PTR [rsp+0x10],xmm2
    24ac:	movaps XMMWORD PTR [rsp],xmm3
    24b0:	xor    rdi,rax
    24b3:	movaps XMMWORD PTR [rsp+0x20],xmm1
    24b8:	movaps XMMWORD PTR [rsp+0x30],xmm0
    24bd:	call   2260 <free@plt+0x10c0>
    24c2:	add    rsp,0x48
    24c6:	ret
    24c7:	nop    WORD PTR [rax+rax*1+0x0]
    24d0:	sub    rsp,0x48
    24d4:	movdqu xmm2,XMMWORD PTR [rdi+0x10]
    24d9:	movdqu xmm1,XMMWORD PTR [rdi+0x20]
    24de:	mov    ecx,0x8
    24e3:	movdqu xmm0,XMMWORD PTR [rdi+0x30]
    24e8:	movdqu xmm3,XMMWORD PTR [rdi]
    24ec:	mov    rdx,rsp
    24ef:	mov    rsi,QWORD PTR [rip+0x4b8a]        # 7080 <_fini+0x2f5e>
    24f6:	mov    rdi,QWORD PTR [rip+0x4b8b]        # 7088 <_fini+0x2f66>
    24fd:	movaps XMMWORD PTR [rsp+0x10],xmm2
    2502:	movaps XMMWORD PTR [rsp],xmm3
    2506:	movaps XMMWORD PTR [rsp+0x20],xmm1
    250b:	movaps XMMWORD PTR [rsp+0x30],xmm0
    2510:	call   2260 <free@plt+0x10c0>
    2515:	add    rsp,0x48
    2519:	ret
    251a:	nop    WORD PTR [rax+rax*1+0x0]
    2520:	sub    rsp,0x48
    2524:	movdqu xmm2,XMMWORD PTR [rdi+0x10]
    2529:	movdqu xmm1,XMMWORD PTR [rdi+0x20]
    252e:	movabs rax,0x3c6ef372fe94f82b
    2538:	movdqu xmm0,XMMWORD PTR [rdi+0x30]
    253d:	movdqu xmm3,XMMWORD PTR [rdi]
    2541:	mov    rdx,rsp
    2544:	mov    ecx,0x8
    2549:	mov    rsi,QWORD PTR [rip+0x4b30]        # 7080 <_fini+0x2f5e>
    2550:	mov    rdi,QWORD PTR [rip+0x4b31]        # 7088 <_fini+0x2f66>
    2557:	movaps XMMWORD PTR [rsp+0x10],xmm2
    255c:	movaps XMMWORD PTR [rsp],xmm3
    2560:	xor    rdi,rax
    2563:	movaps XMMWORD PTR [rsp+0x20],xmm1
    2568:	movaps XMMWORD PTR [rsp+0x30],xmm0
    256d:	call   2260 <free@plt+0x10c0>
    2572:	add    rsp,0x48
    2576:	ret
    2577:	nop    WORD PTR [rax+rax*1+0x0]
    2580:	sub    rsp,0x18
    2584:	mov    DWORD PTR [rsp+0xc],edi
    2588:	mov    eax,DWORD PTR [rsp+0xc]
    258c:	cmp    eax,0xffffffff
    258f:	je     2596 <free@plt+0x13f6>
    2591:	add    rsp,0x18
    2595:	ret
    2596:	mov    edi,0x1
    259b:	call   1160 <_exit@plt>
    25a0:	push   r12
    25a2:	mov    r12d,edi
    25a5:	push   rbp
    25a6:	mov    rbp,rsi
    25a9:	push   rbx
    25aa:	mov    rbx,rdx
    25ad:	nop    DWORD PTR [rax]
    25b0:	mov    rdx,rbx
    25b3:	mov    rsi,rbp
    25b6:	mov    edi,r12d
    25b9:	call   10a0 <write@plt>
    25be:	test   rax,rax
    25c1:	jle    25d0 <free@plt+0x1430>
    25c3:	add    rbp,rax
    25c6:	sub    rbx,rax
    25c9:	jne    25b0 <free@plt+0x1410>
    25cb:	pop    rbx
    25cc:	pop    rbp
    25cd:	pop    r12
    25cf:	ret
    25d0:	xor    edi,edi
    25d2:	call   1160 <_exit@plt>
    25d7:	nop    WORD PTR [rax+rax*1+0x0]
    25e0:	push   r13
    25e2:	mov    ecx,0x1
    25e7:	push   r12
    25e9:	mov    r12,rdx
    25ec:	push   rbp
    25ed:	mov    rbp,rdi
    25f0:	push   rbx
    25f1:	xor    ebx,ebx
    25f3:	sub    rsp,0x38
    25f7:	mov    rdi,QWORD PTR [rip+0x4a82]        # 7080 <_fini+0x2f5e>
    25fe:	mov    QWORD PTR [rsp+0x8],rsi
    2603:	lea    rdx,[rsp+0x8]
    2608:	mov    rsi,rbp
    260b:	call   2260 <free@plt+0x10c0>
    2610:	movq   xmm0,rax
    2615:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2620:	mov    ecx,0x3
    2625:	lea    rdx,[rsp+0x10]
    262a:	movhps xmm0,QWORD PTR [r12+rbx*1]
    262f:	mov    rsi,QWORD PTR [rip+0x4a52]        # 7088 <_fini+0x2f66>
    2636:	mov    rdi,QWORD PTR [rip+0x4a43]        # 7080 <_fini+0x2f5e>
    263d:	mov    QWORD PTR [rsp+0x20],rbx
    2642:	add    rbx,0x8
    2646:	movaps XMMWORD PTR [rsp+0x10],xmm0
    264b:	xor    rdi,rbp
    264e:	call   2260 <free@plt+0x10c0>
    2653:	movq   xmm0,rax
    2658:	cmp    rbx,0xa8
    265f:	jne    2620 <free@plt+0x1480>
    2661:	add    rsp,0x38
    2665:	pop    rbx
    2666:	pop    rbp
    2667:	pop    r12
    2669:	pop    r13
    266b:	ret
    266c:	nop    DWORD PTR [rax+0x0]
    2670:	push   rbp
    2671:	mov    rbp,rdi
    2674:	push   rbx
    2675:	mov    ebx,0x8
    267a:	sub    rsp,0x8
    267e:	xchg   ax,ax
    2680:	xor    edx,edx
    2682:	mov    rsi,rbx
    2685:	mov    rdi,rbp
    2688:	call   1150 <getrandom@plt>
    268d:	test   rax,rax
    2690:	jle    26a1 <free@plt+0x1501>
    2692:	add    rbp,rax
    2695:	sub    rbx,rax
    2698:	jne    2680 <free@plt+0x14e0>
    269a:	add    rsp,0x8
    269e:	pop    rbx
    269f:	pop    rbp
    26a0:	ret
    26a1:	mov    edi,0x1
    26a6:	call   1160 <_exit@plt>
    26ab:	nop    DWORD PTR [rax+rax*1+0x0]
    26b0:	push   r15
    26b2:	push   r14
    26b4:	push   r13
    26b6:	push   r12
    26b8:	push   rbp
    26b9:	push   rbx
    26ba:	mov    ebx,edi
    26bc:	mov    edi,0x1c20
    26c1:	sub    rsp,0x8d8
    26c8:	call   1070 <alarm@plt>
    26cd:	lea    rdi,[rip+0x49c4]        # 7098 <_fini+0x2f76>
    26d4:	call   2670 <free@plt+0x14d0>
    26d9:	lea    rdi,[rip+0x49b0]        # 7090 <_fini+0x2f6e>
    26e0:	call   2670 <free@plt+0x14d0>
    26e5:	lea    rdi,[rip+0x499c]        # 7088 <_fini+0x2f66>
    26ec:	call   2670 <free@plt+0x14d0>
    26f1:	mov    rax,QWORD PTR [rip+0x49a0]        # 7098 <_fini+0x2f76>
    26f8:	test   rax,rax
    26fb:	jne    270e <free@plt+0x156e>
    26fd:	movabs rax,0x6a09e667f3bcc909
    2707:	mov    QWORD PTR [rip+0x498a],rax        # 7098 <_fini+0x2f76>
    270e:	mov    rax,QWORD PTR [rip+0x497b]        # 7090 <_fini+0x2f6e>
    2715:	test   rax,rax
    2718:	jne    272b <free@plt+0x158b>
    271a:	movabs rax,0xbb67ae8584caa73b
    2724:	mov    QWORD PTR [rip+0x4965],rax        # 7090 <_fini+0x2f6e>
    272b:	mov    rax,QWORD PTR [rip+0x4956]        # 7088 <_fini+0x2f66>
    2732:	test   rax,rax
    2735:	jne    2748 <free@plt+0x15a8>
    2737:	movabs rax,0x3c6ef372fe94f82b
    2741:	mov    QWORD PTR [rip+0x4940],rax        # 7088 <_fini+0x2f66>
    2748:	mov    rsi,QWORD PTR [rip+0x4941]        # 7090 <_fini+0x2f6e>
    274f:	lea    rdx,[rsp+0x50]
    2754:	mov    ecx,0x2
    2759:	mov    rdi,QWORD PTR [rip+0x4928]        # 7088 <_fini+0x2f66>
    2760:	lea    rax,[rip+0x1899]        # 4000 <free@plt+0x2e60>
    2767:	lea    rbp,[rsp+0xd0]
    276f:	mov    QWORD PTR [rsp+0x50],rax
    2774:	movabs rax,0x4f524b4559313233
    277e:	mov    QWORD PTR [rsp+0x58],rax
    2783:	call   2260 <free@plt+0x10c0>
    2788:	xor    r8d,r8d
    278b:	xor    edx,edx
    278d:	mov    esi,0x1
    2792:	mov    QWORD PTR [rip+0x48e7],rax        # 7080 <_fini+0x2f5e>
    2799:	movabs rax,0x400000020
    27a3:	movabs rcx,0x14201000015
    27ad:	mov    edi,0x26
    27b2:	mov    QWORD PTR [rsp+0xd0],rax
    27ba:	movabs rax,0xc000003e00010015
    27c4:	mov    QWORD PTR [rsp+0xd8],rax
    27cc:	movabs rax,0x8000000000000006
    27d6:	mov    QWORD PTR [rsp+0xe0],rax
    27de:	movabs rax,0x3b01000015
    27e8:	mov    QWORD PTR [rsp+0xf0],rax
    27f0:	movabs rax,0x5000100000006
    27fa:	mov    QWORD PTR [rsp+0xf8],rax
    2802:	mov    QWORD PTR [rsp+0x108],rax
    280a:	movabs rax,0x7fff000000000006
    2814:	mov    QWORD PTR [rsp+0x100],rcx
    281c:	xor    ecx,ecx
    281e:	mov    QWORD PTR [rsp+0x110],rax
    2826:	xor    eax,eax
    2828:	mov    QWORD PTR [rsp+0xe8],0x20
    2834:	mov    QWORD PTR [rsp+0xa0],0x9
    2840:	mov    QWORD PTR [rsp+0xa8],rbp
    2848:	call   1040 <prctl@plt>
    284d:	test   eax,eax
    284f:	je     285b <free@plt+0x16bb>
    2851:	mov    edi,0x1
    2856:	call   1160 <_exit@plt>
    285b:	lea    rax,[rsp+0xa0]
    2863:	xor    edx,edx
    2865:	mov    esi,0x1
    286a:	mov    edi,0x13d
    286f:	mov    QWORD PTR [rsp+0x8],rax
    2874:	mov    rcx,rax
    2877:	xor    eax,eax
    2879:	call   1030 <syscall@plt>
    287e:	test   rax,rax
    2881:	jne    2851 <free@plt+0x16b1>
    2883:	xchg   ax,ax
    2885:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2890:	mov    r12d,0x2
    2896:	lea    r13,[rsp+0x4e]
    289b:	nop    DWORD PTR [rax+rax*1+0x0]
    28a0:	mov    rdx,r12
    28a3:	mov    rsi,r13
    28a6:	mov    edi,ebx
    28a8:	call   10e0 <read@plt>
    28ad:	test   rax,rax
    28b0:	jle    2970 <free@plt+0x17d0>
    28b6:	add    r13,rax
    28b9:	sub    r12,rax
    28bc:	jne    28a0 <free@plt+0x1700>
    28be:	movzx  edi,WORD PTR [rsp+0x4e]
    28c3:	call   1120 <ntohs@plt>
    28c8:	movzx  r13d,ax
    28cc:	lea    rax,[r13-0x1]
    28d0:	cmp    rax,0x7ff
    28d6:	ja     2970 <free@plt+0x17d0>
    28dc:	mov    r14,r13
    28df:	mov    r12,rbp
    28e2:	nop    DWORD PTR [rax]
    28e5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    28f0:	mov    rdx,r14
    28f3:	mov    rsi,r12
    28f6:	mov    edi,ebx
    28f8:	call   10e0 <read@plt>
    28fd:	test   rax,rax
    2900:	jle    2970 <free@plt+0x17d0>
    2902:	add    r12,rax
    2905:	sub    r14,rax
    2908:	jne    28f0 <free@plt+0x1750>
    290a:	cmp    r13,0x3
    290e:	je     29b0 <free@plt+0x1810>
    2914:	cmp    r13,0x2
    2918:	je     2a20 <free@plt+0x1880>
    291e:	cmp    r13,0x92
    2925:	jne    2980 <free@plt+0x17e0>
    2927:	mov    r12d,0x4
    292d:	lea    r13,[rip+0x275c]        # 5090 <_fini+0xf6e>
    2934:	cmp    BYTE PTR [rsp+0xd0],0x41
    293c:	je     2d9e <free@plt+0x1bfe>
    2942:	nop    DWORD PTR [rax]
    2945:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2950:	mov    rdx,r12
    2953:	mov    rsi,r13
    2956:	mov    edi,ebx
    2958:	call   10a0 <write@plt>
    295d:	test   rax,rax
    2960:	jle    2970 <free@plt+0x17d0>
    2962:	add    r13,rax
    2965:	sub    r12,rax
    2968:	jne    2950 <free@plt+0x17b0>
    296a:	jmp    2890 <free@plt+0x16f0>
    296f:	nop
    2970:	xor    edi,edi
    2972:	call   1160 <_exit@plt>
    2977:	nop    WORD PTR [rax+rax*1+0x0]
    2980:	cmp    r13,0xc2
    2987:	jne    2ad6 <free@plt+0x1936>
    298d:	cmp    BYTE PTR [rsp+0xd0],0x61
    2995:	je     30be <free@plt+0x1f1e>
    299b:	nop    DWORD PTR [rax+rax*1+0x0]
    29a0:	mov    r12d,0x4
    29a6:	lea    r13,[rip+0x26e3]        # 5090 <_fini+0xf6e>
    29ad:	jmp    2950 <free@plt+0x17b0>
    29af:	nop
    29b0:	movzx  eax,BYTE PTR [rsp+0xd0]
    29b8:	cmp    al,0x4e
    29ba:	je     2c56 <free@plt+0x1ab6>
    29c0:	cmp    al,0x4c
    29c2:	jne    2b46 <free@plt+0x19a6>
    29c8:	movzx  eax,BYTE PTR [rsp+0xd1]
    29d0:	cmp    al,0x7
    29d2:	ja     29a0 <free@plt+0x1800>
    29d4:	movzx  edx,BYTE PTR [rsp+0xd2]
    29dc:	cmp    dl,0x7
    29df:	ja     29a0 <free@plt+0x1800>
    29e1:	lea    rcx,[rip+0x4a38]        # 7420 <_fini+0x32fe>
    29e8:	mov    rax,QWORD PTR [rcx+rax*8]
    29ec:	test   rax,rax
    29ef:	je     29a0 <free@plt+0x1800>
    29f1:	lea    rcx,[rip+0x49e8]        # 73e0 <_fini+0x32be>
    29f8:	cmp    QWORD PTR [rcx+rdx*8],0x0
    29fd:	jne    29a0 <free@plt+0x1800>
    29ff:	mov    QWORD PTR [rcx+rdx*8],rax
    2a03:	lea    rsi,[rip+0x25fd]        # 5007 <_fini+0xee5>
    2a0a:	mov    edx,0x7
    2a0f:	mov    edi,ebx
    2a11:	call   25a0 <free@plt+0x1400>
    2a16:	jmp    2890 <free@plt+0x16f0>
    2a1b:	nop    DWORD PTR [rax+rax*1+0x0]
    2a20:	movzx  eax,BYTE PTR [rsp+0xd0]
    2a28:	cmp    al,0x50
    2a2a:	je     2d09 <free@plt+0x1b69>
    2a30:	cmp    al,0x58
    2a32:	je     306f <free@plt+0x1ecf>
    2a38:	cmp    al,0x70
    2a3a:	je     31ba <free@plt+0x201a>
    2a40:	cmp    al,0x78
    2a42:	je     2a85 <free@plt+0x18e5>
    2a44:	cmp    al,0x47
    2a46:	je     37dc <free@plt+0x263c>
    2a4c:	cmp    al,0x49
    2a4e:	je     3876 <free@plt+0x26d6>
    2a54:	cmp    al,0x4a
    2a56:	jne    389f <free@plt+0x26ff>
    2a5c:	movzx  eax,BYTE PTR [rsp+0xd1]
    2a64:	cmp    al,0x3
    2a66:	ja     29a0 <free@plt+0x1800>
    2a6c:	lea    r12,[rip+0x484d]        # 72c0 <_fini+0x319e>
    2a73:	mov    rdi,QWORD PTR [r12+rax*8]
    2a77:	test   rdi,rdi
    2a7a:	jne    3093 <free@plt+0x1ef3>
    2a80:	jmp    29a0 <free@plt+0x1800>
    2a85:	movzx  eax,BYTE PTR [rsp+0xd1]
    2a8d:	cmp    al,0x7
    2a8f:	ja     29a0 <free@plt+0x1800>
    2a95:	lea    r13,[rip+0x48c4]        # 7360 <_fini+0x323e>
    2a9c:	mov    rdi,QWORD PTR [r13+rax*8+0x0]
    2aa1:	test   rdi,rdi
    2aa4:	je     29a0 <free@plt+0x1800>
    2aaa:	call   11a0 <free@plt>
    2aaf:	xor    esi,esi
    2ab1:	mov    edx,0x8
    2ab6:	mov    edi,ebx
    2ab8:	movzx  eax,BYTE PTR [rsp+0xd1]
    2ac0:	mov    QWORD PTR [r13+rax*8+0x0],rsi
    2ac5:	lea    rsi,[rip+0x2543]        # 500f <_fini+0xeed>
    2acc:	call   25a0 <free@plt+0x1400>
    2ad1:	jmp    2890 <free@plt+0x16f0>
    2ad6:	cmp    r13,0x162
    2add:	je     358c <free@plt+0x23ec>
    2ae3:	cmp    r13,0xb2
    2aea:	jne    2d3e <free@plt+0x1b9e>
    2af0:	cmp    BYTE PTR [rsp+0xd0],0x59
    2af8:	jne    29a0 <free@plt+0x1800>
    2afe:	movzx  eax,BYTE PTR [rsp+0xd1]
    2b06:	cmp    al,0x3
    2b08:	ja     29a0 <free@plt+0x1800>
    2b0e:	lea    rdx,[rip+0x472b]        # 7240 <_fini+0x311e>
    2b15:	mov    rdx,QWORD PTR [rdx+rax*8]
    2b19:	test   rdx,rdx
    2b1c:	je     29a0 <free@plt+0x1800>
    2b22:	lea    r8,[rip+0x46f7]        # 7220 <_fini+0x30fe>
    2b29:	cmp    QWORD PTR [r8+rax*8],0x0
    2b2e:	jne    29a0 <free@plt+0x1800>
    2b34:	lea    rsi,[rsp+0xd2]
    2b3c:	mov    ecx,0x2c
    2b41:	jmp    2de1 <free@plt+0x1c41>
    2b46:	cmp    al,0x6e
    2b48:	je     3106 <free@plt+0x1f66>
    2b4e:	cmp    al,0x6c
    2b50:	jne    2bb5 <free@plt+0x1a15>
    2b52:	movzx  eax,BYTE PTR [rsp+0xd1]
    2b5a:	cmp    al,0x7
    2b5c:	ja     29a0 <free@plt+0x1800>
    2b62:	movzx  edx,BYTE PTR [rsp+0xd2]
    2b6a:	cmp    dl,0x7
    2b6d:	ja     29a0 <free@plt+0x1800>
    2b73:	lea    rcx,[rip+0x47e6]        # 7360 <_fini+0x323e>
    2b7a:	mov    rcx,QWORD PTR [rcx+rax*8]
    2b7e:	test   rcx,rcx
    2b81:	je     29a0 <free@plt+0x1800>
    2b87:	lea    rax,[rip+0x4792]        # 7320 <_fini+0x31fe>
    2b8e:	cmp    QWORD PTR [rax+rdx*8],0x0
    2b93:	jne    29a0 <free@plt+0x1800>
    2b99:	mov    QWORD PTR [rax+rdx*8],rcx
    2b9d:	lea    rsi,[rip+0x2463]        # 5007 <_fini+0xee5>
    2ba4:	mov    edx,0x7
    2ba9:	mov    edi,ebx
    2bab:	call   25a0 <free@plt+0x1400>
    2bb0:	jmp    2890 <free@plt+0x16f0>
    2bb5:	cmp    al,0x42
    2bb7:	je     34d4 <free@plt+0x2334>
    2bbd:	cmp    al,0x56
    2bbf:	jne    321c <free@plt+0x207c>
    2bc5:	movzx  eax,BYTE PTR [rsp+0xd1]
    2bcd:	cmp    al,0x7
    2bcf:	ja     29a0 <free@plt+0x1800>
    2bd5:	movzx  edx,BYTE PTR [rsp+0xd2]
    2bdd:	cmp    dl,0x7
    2be0:	ja     29a0 <free@plt+0x1800>
    2be6:	lea    rcx,[rip+0x47b3]        # 73a0 <_fini+0x327e>
    2bed:	cmp    QWORD PTR [rcx+rax*8],0x0
    2bf2:	je     29a0 <free@plt+0x1800>
    2bf8:	lea    rcx,[rip+0x46e1]        # 72e0 <_fini+0x31be>
    2bff:	cmp    QWORD PTR [rcx+rdx*8],0x0
    2c04:	je     29a0 <free@plt+0x1800>
    2c0a:	lea    rcx,[rip+0x47cf]        # 73e0 <_fini+0x32be>
    2c11:	mov    r13,QWORD PTR [rcx+rax*8]
    2c15:	lea    rax,[rip+0x4704]        # 7320 <_fini+0x31fe>
    2c1c:	mov    r12,QWORD PTR [rax+rdx*8]
    2c20:	test   r13,r13
    2c23:	je     2c3e <free@plt+0x1a9e>
    2c25:	test   r12,r12
    2c28:	je     2c3e <free@plt+0x1a9e>
    2c2a:	movabs rax,0x3445424f52504c43
    2c34:	cmp    QWORD PTR [r13+0x0],rax
    2c38:	je     3af0 <free@plt+0x2950>
    2c3e:	mov    edx,0x4
    2c43:	lea    rsi,[rip+0x2446]        # 5090 <_fini+0xf6e>
    2c4a:	mov    edi,ebx
    2c4c:	call   25a0 <free@plt+0x1400>
    2c51:	jmp    2890 <free@plt+0x16f0>
    2c56:	movzx  r12d,BYTE PTR [rsp+0xd1]
    2c5f:	cmp    r12b,0x7
    2c63:	ja     29a0 <free@plt+0x1800>
    2c69:	cmp    BYTE PTR [rsp+0xd2],0x2
    2c71:	ja     29a0 <free@plt+0x1800>
    2c77:	lea    r14,[rip+0x47a2]        # 7420 <_fini+0x32fe>
    2c7e:	movzx  eax,r12b
    2c82:	cmp    QWORD PTR [r14+rax*8],0x0
    2c87:	jne    29a0 <free@plt+0x1800>
    2c8d:	mov    esi,0x90
    2c92:	mov    edi,0x1
    2c97:	call   1090 <calloc@plt>
    2c9c:	mov    r13,rax
    2c9f:	test   rax,rax
    2ca2:	je     2851 <free@plt+0x16b1>
    2ca8:	movabs rax,0x3445424f52504c43
    2cb2:	lea    rdi,[r13+0x10]
    2cb6:	mov    QWORD PTR [r13+0x0],rax
    2cba:	movzx  eax,BYTE PTR [rsp+0xd2]
    2cc2:	mov    QWORD PTR [r13+0x8],rax
    2cc6:	call   2670 <free@plt+0x14d0>
    2ccb:	mov    rax,QWORD PTR [rip+0x43b6]        # 7088 <_fini+0x2f66>
    2cd2:	mov    QWORD PTR [r13+0x30],0x1
    2cda:	mov    rdi,r13
    2cdd:	xor    rax,r13
    2ce0:	mov    QWORD PTR [r13+0x18],rax
    2ce4:	call   2370 <free@plt+0x11d0>
    2ce9:	mov    edx,0x6
    2cee:	mov    edi,ebx
    2cf0:	mov    QWORD PTR [r14+r12*8],r13
    2cf4:	mov    QWORD PTR [r13+0x38],rax
    2cf8:	lea    rsi,[rip+0x2301]        # 5000 <_fini+0xede>
    2cff:	call   25a0 <free@plt+0x1400>
    2d04:	jmp    2890 <free@plt+0x16f0>
    2d09:	movzx  eax,BYTE PTR [rsp+0xd1]
    2d11:	cmp    al,0x7
    2d13:	ja     29a0 <free@plt+0x1800>
    2d19:	lea    rcx,[rip+0x46c0]        # 73e0 <_fini+0x32be>
    2d20:	mov    rsi,QWORD PTR [rcx+rax*8]
    2d24:	test   rsi,rsi
    2d27:	je     29a0 <free@plt+0x1800>
    2d2d:	mov    edx,0x40
    2d32:	mov    edi,ebx
    2d34:	call   25a0 <free@plt+0x1400>
    2d39:	jmp    2890 <free@plt+0x16f0>
    2d3e:	cmp    r13,0xf2
    2d45:	jne    2e0a <free@plt+0x1c6a>
    2d4b:	cmp    BYTE PTR [rsp+0xd0],0x46
    2d53:	jne    29a0 <free@plt+0x1800>
    2d59:	movzx  eax,BYTE PTR [rsp+0xd1]
    2d61:	cmp    al,0x7
    2d63:	ja     29a0 <free@plt+0x1800>
    2d69:	lea    rdx,[rip+0x4430]        # 71a0 <_fini+0x307e>
    2d70:	mov    rdx,QWORD PTR [rdx+rax*8]
    2d74:	test   rdx,rdx
    2d77:	je     29a0 <free@plt+0x1800>
    2d7d:	lea    r8,[rip+0x43dc]        # 7160 <_fini+0x303e>
    2d84:	cmp    QWORD PTR [r8+rax*8],0x0
    2d89:	jne    29a0 <free@plt+0x1800>
    2d8f:	lea    rsi,[rsp+0xd2]
    2d97:	mov    ecx,0x3c
    2d9c:	jmp    2de1 <free@plt+0x1c41>
    2d9e:	movzx  eax,BYTE PTR [rsp+0xd1]
    2da6:	cmp    al,0x7
    2da8:	ja     2950 <free@plt+0x17b0>
    2dae:	lea    rdx,[rip+0x462b]        # 73e0 <_fini+0x32be>
    2db5:	mov    rdx,QWORD PTR [rdx+rax*8]
    2db9:	test   rdx,rdx
    2dbc:	je     2950 <free@plt+0x17b0>
    2dc2:	lea    r8,[rip+0x45d7]        # 73a0 <_fini+0x327e>
    2dc9:	cmp    QWORD PTR [r8+rax*8],0x0
    2dce:	jne    2950 <free@plt+0x17b0>
    2dd4:	lea    rsi,[rsp+0xd2]
    2ddc:	mov    ecx,0x24
    2de1:	mov    rdi,rdx
    2de4:	rep movs DWORD PTR es:[rdi],DWORD PTR ds:[rsi]
    2de6:	movzx  eax,BYTE PTR [rsp+0xd1]
    2dee:	lea    rsi,[rip+0x2223]        # 5018 <_fini+0xef6>
    2df5:	mov    edi,ebx
    2df7:	mov    QWORD PTR [r8+rax*8],rdx
    2dfb:	mov    edx,0x9
    2e00:	call   25a0 <free@plt+0x1400>
    2e05:	jmp    2890 <free@plt+0x16f0>
    2e0a:	cmp    r13,0x132
    2e11:	jne    2e9f <free@plt+0x1cff>
    2e17:	cmp    BYTE PTR [rsp+0xd0],0x66
    2e1f:	jne    29a0 <free@plt+0x1800>
    2e25:	movzx  eax,BYTE PTR [rsp+0xd1]
    2e2d:	cmp    al,0x7
    2e2f:	ja     29a0 <free@plt+0x1800>
    2e35:	lea    rdx,[rip+0x42a4]        # 70e0 <_fini+0x2fbe>
    2e3c:	mov    rdx,QWORD PTR [rdx+rax*8]
    2e40:	test   rdx,rdx
    2e43:	je     29a0 <free@plt+0x1800>
    2e49:	lea    r8,[rip+0x4250]        # 70a0 <_fini+0x2f7e>
    2e50:	cmp    QWORD PTR [r8+rax*8],0x0
    2e55:	jne    29a0 <free@plt+0x1800>
    2e5b:	mov    rax,QWORD PTR [rsp+0xd2]
    2e63:	lea    rdi,[rdx+0x8]
    2e67:	lea    rsi,[rsp+0xd2]
    2e6f:	and    rdi,0xfffffffffffffff8
    2e73:	mov    QWORD PTR [rdx],rax
    2e76:	mov    rax,QWORD PTR [rsp+0x1fa]
    2e7e:	mov    QWORD PTR [rdx+0x128],rax
    2e85:	mov    rax,rdx
    2e88:	sub    rax,rdi
    2e8b:	lea    ecx,[rax+0x130]
    2e91:	sub    rsi,rax
    2e94:	shr    ecx,0x3
    2e97:	rep movs QWORD PTR es:[rdi],QWORD PTR ds:[rsi]
    2e9a:	jmp    2de6 <free@plt+0x1c46>
    2e9f:	cmp    r13,0xb
    2ea3:	jne    31e3 <free@plt+0x2043>
    2ea9:	cmp    BYTE PTR [rsp+0xd0],0x43
    2eb1:	jne    29a0 <free@plt+0x1800>
    2eb7:	movzx  eax,BYTE PTR [rsp+0xd1]
    2ebf:	cmp    al,0x3
    2ec1:	ja     29a0 <free@plt+0x1800>
    2ec7:	movzx  edx,BYTE PTR [rsp+0xd2]
    2ecf:	cmp    dl,0x3
    2ed2:	ja     29a0 <free@plt+0x1800>
    2ed8:	lea    rcx,[rip+0x43a1]        # 7280 <_fini+0x315e>
    2edf:	cmp    QWORD PTR [rcx+rax*8],0x0
    2ee4:	je     29a0 <free@plt+0x1800>
    2eea:	lea    rcx,[rip+0x432f]        # 7220 <_fini+0x30fe>
    2ef1:	cmp    QWORD PTR [rcx+rdx*8],0x0
    2ef6:	je     29a0 <free@plt+0x1800>
    2efc:	lea    rcx,[rip+0x439d]        # 72a0 <_fini+0x317e>
    2f03:	lea    rdi,[rsp+0x60]
    2f08:	mov    r13,QWORD PTR [rcx+rax*8]
    2f0c:	lea    rax,[rip+0x432d]        # 7240 <_fini+0x311e>
    2f13:	mov    ecx,0x8
    2f18:	mov    QWORD PTR [rsp+0x10],rdi
    2f1d:	mov    r15,QWORD PTR [rax+rdx*8]
    2f21:	xor    eax,eax
    2f23:	rep stos DWORD PTR es:[rdi],eax
    2f25:	lea    rdi,[rsp+0x80]
    2f2d:	mov    ecx,0x8
    2f32:	mov    QWORD PTR [rsp+0x18],rdi
    2f37:	rep stos DWORD PTR es:[rdi],eax
    2f39:	test   r13,r13
    2f3c:	je     2f57 <free@plt+0x1db7>
    2f3e:	test   r15,r15
    2f41:	je     2f57 <free@plt+0x1db7>
    2f43:	movabs rax,0x3454494d52455043
    2f4d:	cmp    QWORD PTR [r13+0x0],rax
    2f51:	je     3c17 <free@plt+0x2a77>
    2f57:	xor    r12d,r12d
    2f5a:	mov    QWORD PTR [rsp+0x28],r15
    2f5f:	mov    QWORD PTR [rsp+0x30],r14
    2f64:	mov    DWORD PTR [rsp+0x3c],ebx
    2f68:	mov    QWORD PTR [rsp+0x20],r13
    2f6d:	xor    r13d,r13d
    2f70:	movzx  edx,BYTE PTR [rbp+r13*2+0x3]
    2f76:	movzx  eax,BYTE PTR [rbp+r13*2+0x4]
    2f7c:	mov    ecx,edx
    2f7e:	or     ecx,eax
    2f80:	cmp    cl,0x7
    2f83:	ja     2fa5 <free@plt+0x1e05>
    2f85:	lea    rcx,[rip+0x41d4]        # 7160 <_fini+0x303e>
    2f8c:	cmp    QWORD PTR [rcx+rdx*8],0x0
    2f91:	je     2fa5 <free@plt+0x1e05>
    2f93:	lea    rcx,[rip+0x4106]        # 70a0 <_fini+0x2f7e>
    2f9a:	cmp    QWORD PTR [rcx+rax*8],0x0
    2f9f:	jne    3a76 <free@plt+0x28d6>
    2fa5:	xor    r12d,r12d
    2fa8:	add    r13,0x1
    2fac:	cmp    r13,0x4
    2fb0:	jne    2f70 <free@plt+0x1dd0>
    2fb2:	mov    r13,QWORD PTR [rsp+0x20]
    2fb7:	mov    r15,QWORD PTR [rsp+0x28]
    2fbc:	mov    r14,QWORD PTR [rsp+0x30]
    2fc1:	mov    ebx,DWORD PTR [rsp+0x3c]
    2fc5:	test   r12d,r12d
    2fc8:	je     3057 <free@plt+0x1eb7>
    2fce:	mov    rax,QWORD PTR [rip+0x40ab]        # 7080 <_fini+0x2f5e>
    2fd5:	mov    r12,QWORD PTR [rsp+0x10]
    2fda:	mov    QWORD PTR [rsp+0xa0],rax
    2fe2:	mov    rax,QWORD PTR [r12+r14*8]
    2fe6:	mov    rcx,QWORD PTR [rsp+0x18]
    2feb:	mov    rsi,QWORD PTR [rip+0x4096]        # 7088 <_fini+0x2f66>
    2ff2:	mov    rdx,QWORD PTR [rax+0x30]
    2ff6:	mov    rdi,QWORD PTR [rip+0x4083]        # 7080 <_fini+0x2f5e>
    2ffd:	mov    QWORD PTR [rsp+0xa8],rdx
    3005:	mov    rdx,QWORD PTR [rax+0x10]
    3009:	xor    rdi,r14
    300c:	mov    QWORD PTR [rsp+0xb0],rdx
    3014:	mov    rdx,QWORD PTR [rcx+r14*8]
    3018:	add    r14,0x1
    301c:	mov    rcx,QWORD PTR [rdx+0x10]
    3020:	mov    QWORD PTR [rsp+0xc8],rdx
    3028:	mov    rdx,QWORD PTR [rsp+0x8]
    302d:	mov    QWORD PTR [rsp+0xc0],rax
    3035:	mov    QWORD PTR [rsp+0xb8],rcx
    303d:	mov    ecx,0x6
    3042:	call   2260 <free@plt+0x10c0>
    3047:	cmp    r14,0x4
    304b:	jne    2fda <free@plt+0x1e3a>
    304d:	cmp    QWORD PTR [r13+0x28],rax
    3051:	je     3cdd <free@plt+0x2b3d>
    3057:	mov    edx,0x7
    305c:	lea    rsi,[rip+0x1fff]        # 5062 <_fini+0xf40>
    3063:	mov    edi,ebx
    3065:	call   25a0 <free@plt+0x1400>
    306a:	jmp    2890 <free@plt+0x16f0>
    306f:	movzx  eax,BYTE PTR [rsp+0xd1]
    3077:	cmp    al,0x7
    3079:	ja     29a0 <free@plt+0x1800>
    307f:	lea    r12,[rip+0x439a]        # 7420 <_fini+0x32fe>
    3086:	mov    rdi,QWORD PTR [r12+rax*8]
    308a:	test   rdi,rdi
    308d:	je     29a0 <free@plt+0x1800>
    3093:	call   11a0 <free@plt>
    3098:	xor    edx,edx
    309a:	lea    rsi,[rip+0x1f6e]        # 500f <_fini+0xeed>
    30a1:	mov    edi,ebx
    30a3:	movzx  eax,BYTE PTR [rsp+0xd1]
    30ab:	mov    QWORD PTR [r12+rax*8],rdx
    30af:	mov    edx,0x8
    30b4:	call   25a0 <free@plt+0x1400>
    30b9:	jmp    2890 <free@plt+0x16f0>
    30be:	movzx  eax,BYTE PTR [rsp+0xd1]
    30c6:	cmp    al,0x7
    30c8:	ja     29a0 <free@plt+0x1800>
    30ce:	lea    rdx,[rip+0x424b]        # 7320 <_fini+0x31fe>
    30d5:	mov    rdx,QWORD PTR [rdx+rax*8]
    30d9:	test   rdx,rdx
    30dc:	je     29a0 <free@plt+0x1800>
    30e2:	lea    r8,[rip+0x41f7]        # 72e0 <_fini+0x31be>
    30e9:	cmp    QWORD PTR [r8+rax*8],0x0
    30ee:	jne    29a0 <free@plt+0x1800>
    30f4:	lea    rsi,[rsp+0xd2]
    30fc:	mov    ecx,0x30
    3101:	jmp    2de1 <free@plt+0x1c41>
    3106:	movzx  r12d,BYTE PTR [rsp+0xd1]
    310f:	cmp    r12b,0x7
    3113:	ja     29a0 <free@plt+0x1800>
    3119:	cmp    BYTE PTR [rsp+0xd2],0x2
    3121:	ja     29a0 <free@plt+0x1800>
    3127:	lea    r13,[rip+0x4232]        # 7360 <_fini+0x323e>
    312e:	movzx  eax,r12b
    3132:	cmp    QWORD PTR [r13+rax*8+0x0],0x0
    3138:	jne    29a0 <free@plt+0x1800>
    313e:	mov    esi,0xc0
    3143:	mov    edi,0x1
    3148:	call   1090 <calloc@plt>
    314d:	mov    r14,rax
    3150:	test   rax,rax
    3153:	je     2851 <free@plt+0x16b1>
    3159:	movabs rax,0x3454524550414c43
    3163:	lea    rdi,[r14+0x10]
    3167:	mov    QWORD PTR [r14],rax
    316a:	movzx  eax,BYTE PTR [rsp+0xd2]
    3172:	mov    QWORD PTR [r14+0x8],rax
    3176:	call   2670 <free@plt+0x14d0>
    317b:	mov    rax,QWORD PTR [rip+0x3f06]        # 7088 <_fini+0x2f66>
    3182:	mov    QWORD PTR [r14+0x30],0x1
    318a:	mov    rdi,r14
    318d:	xor    rax,r14
    3190:	mov    QWORD PTR [r14+0x18],rax
    3194:	call   23c0 <free@plt+0x1220>
    3199:	mov    edx,0x9
    319e:	mov    edi,ebx
    31a0:	lea    rsi,[rip+0x1e7b]        # 5022 <_fini+0xf00>
    31a7:	mov    QWORD PTR [r14+0x38],rax
    31ab:	mov    QWORD PTR [r13+r12*8+0x0],r14
    31b0:	call   25a0 <free@plt+0x1400>
    31b5:	jmp    2890 <free@plt+0x16f0>
    31ba:	movzx  eax,BYTE PTR [rsp+0xd1]
    31c2:	cmp    al,0x7
    31c4:	ja     29a0 <free@plt+0x1800>
    31ca:	lea    rdx,[rip+0x414f]        # 7320 <_fini+0x31fe>
    31d1:	mov    rsi,QWORD PTR [rdx+rax*8]
    31d5:	test   rsi,rsi
    31d8:	jne    2d2d <free@plt+0x1b8d>
    31de:	jmp    29a0 <free@plt+0x1800>
    31e3:	cmp    r13,0x5
    31e7:	jne    29a0 <free@plt+0x1800>
    31ed:	cmp    DWORD PTR [rbp+0x0],0x474e4950
    31f4:	jne    29a0 <free@plt+0x1800>
    31fa:	cmp    BYTE PTR [rbp+0x4],0xa
    31fe:	jne    29a0 <free@plt+0x1800>
    3204:	mov    edx,0x5
    3209:	lea    rsi,[rip+0x1e6b]        # 507b <_fini+0xf59>
    3210:	mov    edi,ebx
    3212:	call   25a0 <free@plt+0x1400>
    3217:	jmp    2890 <free@plt+0x16f0>
    321c:	cmp    al,0x48
    321e:	jne    3283 <free@plt+0x20e3>
    3220:	movzx  eax,BYTE PTR [rsp+0xd1]
    3228:	cmp    al,0x3
    322a:	ja     29a0 <free@plt+0x1800>
    3230:	movzx  edx,BYTE PTR [rsp+0xd2]
    3238:	cmp    dl,0x3
    323b:	ja     29a0 <free@plt+0x1800>
    3241:	lea    rcx,[rip+0x4078]        # 72c0 <_fini+0x319e>
    3248:	mov    rax,QWORD PTR [rcx+rax*8]
    324c:	test   rax,rax
    324f:	je     29a0 <free@plt+0x1800>
    3255:	lea    rcx,[rip+0x4044]        # 72a0 <_fini+0x317e>
    325c:	cmp    QWORD PTR [rcx+rdx*8],0x0
    3261:	jne    29a0 <free@plt+0x1800>
    3267:	mov    QWORD PTR [rcx+rdx*8],rax
    326b:	lea    rsi,[rip+0x1dc9]        # 503b <_fini+0xf19>
    3272:	mov    edx,0x5
    3277:	mov    edi,ebx
    3279:	call   25a0 <free@plt+0x1400>
    327e:	jmp    2890 <free@plt+0x16f0>
    3283:	cmp    al,0x4f
    3285:	je     3614 <free@plt+0x2474>
    328b:	cmp    al,0x44
    328d:	je     3660 <free@plt+0x24c0>
    3293:	cmp    al,0x53
    3295:	je     335b <free@plt+0x21bb>
    329b:	cmp    al,0x54
    329d:	jne    3302 <free@plt+0x2162>
    329f:	movzx  eax,BYTE PTR [rsp+0xd1]
    32a7:	cmp    al,0x7
    32a9:	ja     29a0 <free@plt+0x1800>
    32af:	movzx  edx,BYTE PTR [rsp+0xd2]
    32b7:	cmp    dl,0x7
    32ba:	ja     29a0 <free@plt+0x1800>
    32c0:	lea    rcx,[rip+0x3f19]        # 71e0 <_fini+0x30be>
    32c7:	mov    rax,QWORD PTR [rcx+rax*8]
    32cb:	test   rax,rax
    32ce:	je     29a0 <free@plt+0x1800>
    32d4:	lea    rcx,[rip+0x3ec5]        # 71a0 <_fini+0x307e>
    32db:	cmp    QWORD PTR [rcx+rdx*8],0x0
    32e0:	jne    29a0 <free@plt+0x1800>
    32e6:	mov    QWORD PTR [rcx+rdx*8],rax
    32ea:	lea    rsi,[rip+0x1d60]        # 5051 <_fini+0xf2f>
    32f1:	mov    edx,0x9
    32f6:	mov    edi,ebx
    32f8:	call   25a0 <free@plt+0x1400>
    32fd:	jmp    2890 <free@plt+0x16f0>
    3302:	cmp    al,0x73
    3304:	je     3729 <free@plt+0x2589>
    330a:	cmp    al,0x74
    330c:	jne    3423 <free@plt+0x2283>
    3312:	movzx  eax,BYTE PTR [rsp+0xd1]
    331a:	cmp    al,0x7
    331c:	ja     29a0 <free@plt+0x1800>
    3322:	movzx  edx,BYTE PTR [rsp+0xd2]
    332a:	cmp    dl,0x7
    332d:	ja     29a0 <free@plt+0x1800>
    3333:	lea    rcx,[rip+0x3de6]        # 7120 <_fini+0x2ffe>
    333a:	mov    rax,QWORD PTR [rcx+rax*8]
    333e:	test   rax,rax
    3341:	je     29a0 <free@plt+0x1800>
    3347:	lea    rcx,[rip+0x3d92]        # 70e0 <_fini+0x2fbe>
    334e:	cmp    QWORD PTR [rcx+rdx*8],0x0
    3353:	jne    29a0 <free@plt+0x1800>
    3359:	jmp    32e6 <free@plt+0x2146>
    335b:	movzx  r12d,BYTE PTR [rsp+0xd1]
    3364:	cmp    r12b,0x7
    3368:	ja     29a0 <free@plt+0x1800>
    336e:	cmp    BYTE PTR [rsp+0xd2],0x3
    3376:	ja     29a0 <free@plt+0x1800>
    337c:	lea    r14,[rip+0x3e5d]        # 71e0 <_fini+0x30be>
    3383:	movzx  eax,r12b
    3387:	cmp    QWORD PTR [r14+rax*8],0x0
    338c:	jne    29a0 <free@plt+0x1800>
    3392:	mov    esi,0xf0
    3397:	mov    edi,0x1
    339c:	call   1090 <calloc@plt>
    33a1:	mov    r13,rax
    33a4:	test   rax,rax
    33a7:	je     2851 <free@plt+0x16b1>
    33ad:	movabs rax,0x3444524148534c43
    33b7:	lea    rdi,[r13+0x10]
    33bb:	mov    QWORD PTR [r13+0x0],rax
    33bf:	movzx  eax,BYTE PTR [rsp+0xd2]
    33c7:	mov    QWORD PTR [r13+0x8],rax
    33cb:	call   2670 <free@plt+0x14d0>
    33d0:	mov    rax,QWORD PTR [rip+0x3cb1]        # 7088 <_fini+0x2f66>
    33d7:	mov    rsi,QWORD PTR [r13+0x8]
    33db:	lea    rdx,[r13+0x48]
    33df:	mov    rdi,QWORD PTR [r13+0x10]
    33e3:	xor    rax,r13
    33e6:	mov    QWORD PTR [r13+0x18],rax
    33ea:	call   25e0 <free@plt+0x1440>
    33ef:	mov    QWORD PTR [r13+0x38],0x1
    33f7:	mov    rdi,r13
    33fa:	mov    QWORD PTR [r13+0x30],rax
    33fe:	call   24d0 <free@plt+0x1330>
    3403:	mov    edx,0x6
    3408:	mov    edi,ebx
    340a:	mov    QWORD PTR [r14+r12*8],r13
    340e:	mov    QWORD PTR [r13+0x40],rax
    3412:	lea    rsi,[rip+0x1c31]        # 504a <_fini+0xf28>
    3419:	call   25a0 <free@plt+0x1400>
    341e:	jmp    2890 <free@plt+0x16f0>
    3423:	cmp    al,0x45
    3425:	jne    29a0 <free@plt+0x1800>
    342b:	movzx  eax,BYTE PTR [rsp+0xd1]
    3433:	cmp    al,0x7
    3435:	ja     29a0 <free@plt+0x1800>
    343b:	movzx  edx,BYTE PTR [rsp+0xd2]
    3443:	cmp    dl,0x7
    3446:	ja     29a0 <free@plt+0x1800>
    344c:	lea    rcx,[rip+0x3d8d]        # 71e0 <_fini+0x30be>
    3453:	mov    r13,QWORD PTR [rcx+rax*8]
    3457:	test   r13,r13
    345a:	je     29a0 <free@plt+0x1800>
    3460:	lea    rax,[rip+0x3cb9]        # 7120 <_fini+0x2ffe>
    3467:	mov    r12,QWORD PTR [rax+rdx*8]
    346b:	test   r12,r12
    346e:	je     29a0 <free@plt+0x1800>
    3474:	mov    rax,QWORD PTR [r12+0x8]
    3479:	cmp    QWORD PTR [r13+0x8],rax
    347d:	jne    29a0 <free@plt+0x1800>
    3483:	mov    rax,QWORD PTR [rip+0x3bfe]        # 7088 <_fini+0x2f66>
    348a:	mov    rdi,r13
    348d:	xor    rax,r12
    3490:	mov    QWORD PTR [r13+0x20],rax
    3494:	mov    rax,QWORD PTR [r12+0x10]
    3499:	mov    QWORD PTR [r13+0x28],rax
    349d:	mov    rax,QWORD PTR [rip+0x3be4]        # 7088 <_fini+0x2f66>
    34a4:	xor    rax,r13
    34a7:	mov    QWORD PTR [r12+0x20],rax
    34ac:	mov    rax,QWORD PTR [r13+0x10]
    34b0:	mov    QWORD PTR [r12+0x28],rax
    34b5:	mov    rax,QWORD PTR [r13+0x30]
    34b9:	mov    QWORD PTR [r12+0x30],rax
    34be:	call   24d0 <free@plt+0x1330>
    34c3:	mov    rdi,r12
    34c6:	mov    QWORD PTR [r13+0x40],rax
    34ca:	call   2520 <free@plt+0x1380>
    34cf:	jmp    370c <free@plt+0x256c>
    34d4:	movzx  eax,BYTE PTR [rsp+0xd1]
    34dc:	cmp    al,0x7
    34de:	ja     29a0 <free@plt+0x1800>
    34e4:	movzx  edx,BYTE PTR [rsp+0xd2]
    34ec:	cmp    dl,0x7
    34ef:	ja     29a0 <free@plt+0x1800>
    34f5:	lea    rcx,[rip+0x3f24]        # 7420 <_fini+0x32fe>
    34fc:	mov    r12,QWORD PTR [rcx+rax*8]
    3500:	test   r12,r12
    3503:	je     29a0 <free@plt+0x1800>
    3509:	lea    rax,[rip+0x3e50]        # 7360 <_fini+0x323e>
    3510:	mov    r13,QWORD PTR [rax+rdx*8]
    3514:	test   r13,r13
    3517:	je     29a0 <free@plt+0x1800>
    351d:	mov    rax,QWORD PTR [r13+0x8]
    3521:	cmp    QWORD PTR [r12+0x8],rax
    3526:	jne    29a0 <free@plt+0x1800>
    352c:	mov    rax,QWORD PTR [r13+0x10]
    3530:	mov    rdi,r12
    3533:	mov    QWORD PTR [r12+0x20],rax
    3538:	mov    rax,QWORD PTR [rip+0x3b49]        # 7088 <_fini+0x2f66>
    353f:	xor    rax,r13
    3542:	mov    QWORD PTR [r12+0x28],rax
    3547:	mov    rax,QWORD PTR [r12+0x10]
    354c:	mov    QWORD PTR [r13+0x20],rax
    3550:	mov    rax,QWORD PTR [rip+0x3b31]        # 7088 <_fini+0x2f66>
    3557:	xor    rax,r12
    355a:	mov    QWORD PTR [r13+0x28],rax
    355e:	call   2370 <free@plt+0x11d0>
    3563:	mov    rdi,r13
    3566:	mov    QWORD PTR [r12+0x38],rax
    356b:	call   23c0 <free@plt+0x1220>
    3570:	mov    edx,0x6
    3575:	lea    rsi,[rip+0x1ab0]        # 502c <_fini+0xf0a>
    357c:	mov    edi,ebx
    357e:	mov    QWORD PTR [r13+0x38],rax
    3582:	call   25a0 <free@plt+0x1400>
    3587:	jmp    2890 <free@plt+0x16f0>
    358c:	cmp    BYTE PTR [rsp+0xd0],0x4b
    3594:	jne    29a0 <free@plt+0x1800>
    359a:	movzx  eax,BYTE PTR [rsp+0xd1]
    35a2:	cmp    al,0x3
    35a4:	ja     29a0 <free@plt+0x1800>
    35aa:	lea    rdx,[rip+0x3cef]        # 72a0 <_fini+0x317e>
    35b1:	mov    rdx,QWORD PTR [rdx+rax*8]
    35b5:	test   rdx,rdx
    35b8:	je     29a0 <free@plt+0x1800>
    35be:	lea    r8,[rip+0x3cbb]        # 7280 <_fini+0x315e>
    35c5:	cmp    QWORD PTR [r8+rax*8],0x0
    35ca:	jne    29a0 <free@plt+0x1800>
    35d0:	mov    rax,QWORD PTR [rsp+0xd2]
    35d8:	lea    rdi,[rdx+0x8]
    35dc:	lea    rsi,[rsp+0xd2]
    35e4:	and    rdi,0xfffffffffffffff8
    35e8:	mov    QWORD PTR [rdx],rax
    35eb:	mov    rax,QWORD PTR [rsp+0x22a]
    35f3:	mov    QWORD PTR [rdx+0x158],rax
    35fa:	mov    rax,rdx
    35fd:	sub    rax,rdi
    3600:	lea    ecx,[rax+0x160]
    3606:	sub    rsi,rax
    3609:	shr    ecx,0x3
    360c:	rep movs QWORD PTR es:[rdi],QWORD PTR ds:[rsi]
    360f:	jmp    2de6 <free@plt+0x1c46>
    3614:	movzx  eax,BYTE PTR [rsp+0xd1]
    361c:	cmp    al,0x3
    361e:	ja     29a0 <free@plt+0x1800>
    3624:	movzx  edx,BYTE PTR [rsp+0xd2]
    362c:	cmp    dl,0x3
    362f:	ja     29a0 <free@plt+0x1800>
    3635:	lea    rcx,[rip+0x3c24]        # 7260 <_fini+0x313e>
    363c:	mov    rax,QWORD PTR [rcx+rax*8]
    3640:	test   rax,rax
    3643:	je     29a0 <free@plt+0x1800>
    3649:	lea    rcx,[rip+0x3bf0]        # 7240 <_fini+0x311e>
    3650:	cmp    QWORD PTR [rcx+rdx*8],0x0
    3655:	jne    29a0 <free@plt+0x1800>
    365b:	jmp    3267 <free@plt+0x20c7>
    3660:	movzx  eax,BYTE PTR [rsp+0xd1]
    3668:	cmp    al,0x3
    366a:	ja     29a0 <free@plt+0x1800>
    3670:	movzx  edx,BYTE PTR [rsp+0xd2]
    3678:	cmp    dl,0x3
    367b:	ja     29a0 <free@plt+0x1800>
    3681:	lea    rcx,[rip+0x3c38]        # 72c0 <_fini+0x319e>
    3688:	mov    r13,QWORD PTR [rcx+rax*8]
    368c:	test   r13,r13
    368f:	je     29a0 <free@plt+0x1800>
    3695:	lea    rax,[rip+0x3bc4]        # 7260 <_fini+0x313e>
    369c:	mov    r12,QWORD PTR [rax+rdx*8]
    36a0:	test   r12,r12
    36a3:	je     29a0 <free@plt+0x1800>
    36a9:	mov    rax,QWORD PTR [rip+0x39d8]        # 7088 <_fini+0x2f66>
    36b0:	lea    rcx,[rip+0xffffffffffffeec9]        # 2580 <free@plt+0x13e0>
    36b7:	mov    rdi,r13
    36ba:	xor    rax,r12
    36bd:	mov    QWORD PTR [r13+0x18],rax
    36c1:	mov    rax,QWORD PTR [r12+0x8]
    36c6:	mov    QWORD PTR [r13+0x20],rax
    36ca:	mov    rax,QWORD PTR [rip+0x39b7]        # 7088 <_fini+0x2f66>
    36d1:	xor    rax,r13
    36d4:	mov    QWORD PTR [r12+0x18],rax
    36d9:	mov    rax,QWORD PTR [rip+0x39b0]        # 7090 <_fini+0x2f6e>
    36e0:	mov    rdx,QWORD PTR [r13+0x8]
    36e4:	xor    rax,rcx
    36e7:	xor    rax,r12
    36ea:	mov    QWORD PTR [r12+0x20],rdx
    36ef:	xor    rax,rdx
    36f2:	rol    rax,0x13
    36f6:	mov    QWORD PTR [r12+0x28],rax
    36fb:	call   2420 <free@plt+0x1280>
    3700:	mov    rdi,r12
    3703:	mov    QWORD PTR [r13+0x38],rax
    3707:	call   2470 <free@plt+0x12d0>
    370c:	mov    QWORD PTR [r12+0x40],rax
    3711:	mov    edx,0x6
    3716:	lea    rsi,[rip+0x190f]        # 502c <_fini+0xf0a>
    371d:	mov    edi,ebx
    371f:	call   25a0 <free@plt+0x1400>
    3724:	jmp    2890 <free@plt+0x16f0>
    3729:	movzx  r12d,BYTE PTR [rsp+0xd1]
    3732:	cmp    r12b,0x7
    3736:	ja     29a0 <free@plt+0x1800>
    373c:	cmp    BYTE PTR [rsp+0xd2],0x3
    3744:	ja     29a0 <free@plt+0x1800>
    374a:	lea    r14,[rip+0x39cf]        # 7120 <_fini+0x2ffe>
    3751:	movzx  eax,r12b
    3755:	cmp    QWORD PTR [r14+rax*8],0x0
    375a:	jne    29a0 <free@plt+0x1800>
    3760:	mov    esi,0x130
    3765:	mov    edi,0x1
    376a:	call   1090 <calloc@plt>
    376f:	mov    r13,rax
    3772:	test   rax,rax
    3775:	je     2851 <free@plt+0x16b1>
    377b:	movabs rax,0x34504d4154534c43
    3785:	lea    rdi,[r13+0x10]
    3789:	mov    QWORD PTR [r13+0x0],rax
    378d:	movzx  eax,BYTE PTR [rsp+0xd2]
    3795:	mov    QWORD PTR [r13+0x8],rax
    3799:	call   2670 <free@plt+0x14d0>
    379e:	mov    rax,QWORD PTR [rip+0x38e3]        # 7088 <_fini+0x2f66>
    37a5:	mov    QWORD PTR [r13+0x38],0x1
    37ad:	mov    rdi,r13
    37b0:	xor    rax,r13
    37b3:	mov    QWORD PTR [r13+0x18],rax
    37b7:	call   2520 <free@plt+0x1380>
    37bc:	mov    edx,0x6
    37c1:	mov    edi,ebx
    37c3:	mov    QWORD PTR [r14+r12*8],r13
    37c7:	mov    QWORD PTR [r13+0x40],rax
    37cb:	lea    rsi,[rip+0x1889]        # 505b <_fini+0xf39>
    37d2:	call   25a0 <free@plt+0x1400>
    37d7:	jmp    2890 <free@plt+0x16f0>
    37dc:	movzx  r12d,BYTE PTR [rsp+0xd1]
    37e5:	cmp    r12b,0x3
    37e9:	ja     29a0 <free@plt+0x1800>
    37ef:	lea    r13,[rip+0x3aca]        # 72c0 <_fini+0x319e>
    37f6:	movzx  eax,r12b
    37fa:	cmp    QWORD PTR [r13+rax*8+0x0],0x0
    3800:	jne    29a0 <free@plt+0x1800>
    3806:	mov    esi,0x160
    380b:	mov    edi,0x1
    3810:	call   1090 <calloc@plt>
    3815:	mov    r14,rax
    3818:	test   rax,rax
    381b:	je     2851 <free@plt+0x16b1>
    3821:	movabs rax,0x3454494d52455043
    382b:	lea    rdi,[r14+0x8]
    382f:	mov    QWORD PTR [r14],rax
    3832:	call   2670 <free@plt+0x14d0>
    3837:	mov    rax,QWORD PTR [rip+0x384a]        # 7088 <_fini+0x2f66>
    383e:	mov    QWORD PTR [r14+0x30],0x1
    3846:	mov    rdi,r14
    3849:	xor    rax,r14
    384c:	mov    QWORD PTR [r14+0x10],rax
    3850:	call   2420 <free@plt+0x1280>
    3855:	mov    edx,0x7
    385a:	mov    edi,ebx
    385c:	lea    rsi,[rip+0x17d0]        # 5033 <_fini+0xf11>
    3863:	mov    QWORD PTR [r14+0x38],rax
    3867:	mov    QWORD PTR [r13+r12*8+0x0],r14
    386c:	call   25a0 <free@plt+0x1400>
    3871:	jmp    2890 <free@plt+0x16f0>
    3876:	movzx  eax,BYTE PTR [rsp+0xd1]
    387e:	cmp    al,0x3
    3880:	ja     29a0 <free@plt+0x1800>
    3886:	lea    rdx,[rip+0x3a13]        # 72a0 <_fini+0x317e>
    388d:	mov    rsi,QWORD PTR [rdx+rax*8]
    3891:	test   rsi,rsi
    3894:	jne    2d2d <free@plt+0x1b8d>
    389a:	jmp    29a0 <free@plt+0x1800>
    389f:	cmp    al,0x4d
    38a1:	jne    3940 <free@plt+0x27a0>
    38a7:	movzx  r12d,BYTE PTR [rsp+0xd1]
    38b0:	cmp    r12b,0x3
    38b4:	ja     29a0 <free@plt+0x1800>
    38ba:	lea    r14,[rip+0x399f]        # 7260 <_fini+0x313e>
    38c1:	movzx  eax,r12b
    38c5:	cmp    QWORD PTR [r14+rax*8],0x0
    38ca:	jne    29a0 <free@plt+0x1800>
    38d0:	mov    esi,0xb0
    38d5:	mov    edi,0x1
    38da:	call   1090 <calloc@plt>
    38df:	mov    r13,rax
    38e2:	test   rax,rax
    38e5:	je     2851 <free@plt+0x16b1>
    38eb:	movabs rax,0x34455441444e414d
    38f5:	lea    rdi,[r13+0x8]
    38f9:	mov    QWORD PTR [r13+0x0],rax
    38fd:	call   2670 <free@plt+0x14d0>
    3902:	mov    rax,QWORD PTR [rip+0x377f]        # 7088 <_fini+0x2f66>
    3909:	mov    QWORD PTR [r13+0x38],0x1
    3911:	mov    rdi,r13
    3914:	xor    rax,r13
    3917:	mov    QWORD PTR [r13+0x10],rax
    391b:	call   2470 <free@plt+0x12d0>
    3920:	mov    edx,0x8
    3925:	mov    edi,ebx
    3927:	mov    QWORD PTR [r14+r12*8],r13
    392b:	mov    QWORD PTR [r13+0x40],rax
    392f:	lea    rsi,[rip+0x170b]        # 5041 <_fini+0xf1f>
    3936:	call   25a0 <free@plt+0x1400>
    393b:	jmp    2890 <free@plt+0x16f0>
    3940:	cmp    al,0x51
    3942:	je     39e7 <free@plt+0x2847>
    3948:	cmp    al,0x52
    394a:	jne    3975 <free@plt+0x27d5>
    394c:	movzx  eax,BYTE PTR [rsp+0xd1]
    3954:	cmp    al,0x3
    3956:	ja     29a0 <free@plt+0x1800>
    395c:	lea    r12,[rip+0x38fd]        # 7260 <_fini+0x313e>
    3963:	mov    rdi,QWORD PTR [r12+rax*8]
    3967:	test   rdi,rdi
    396a:	jne    3093 <free@plt+0x1ef3>
    3970:	jmp    29a0 <free@plt+0x1800>
    3975:	cmp    al,0x55
    3977:	je     3a1c <free@plt+0x287c>
    397d:	cmp    al,0x57
    397f:	je     39be <free@plt+0x281e>
    3981:	cmp    al,0x75
    3983:	jne    3a45 <free@plt+0x28a5>
    3989:	movzx  eax,BYTE PTR [rsp+0xd1]
    3991:	cmp    al,0x7
    3993:	ja     29a0 <free@plt+0x1800>
    3999:	lea    rdx,[rip+0x3740]        # 70e0 <_fini+0x2fbe>
    39a0:	mov    rsi,QWORD PTR [rdx+rax*8]
    39a4:	test   rsi,rsi
    39a7:	je     29a0 <free@plt+0x1800>
    39ad:	mov    edx,0x48
    39b2:	mov    edi,ebx
    39b4:	call   25a0 <free@plt+0x1400>
    39b9:	jmp    2890 <free@plt+0x16f0>
    39be:	movzx  eax,BYTE PTR [rsp+0xd1]
    39c6:	cmp    al,0x7
    39c8:	ja     29a0 <free@plt+0x1800>
    39ce:	lea    r12,[rip+0x380b]        # 71e0 <_fini+0x30be>
    39d5:	mov    rdi,QWORD PTR [r12+rax*8]
    39d9:	test   rdi,rdi
    39dc:	jne    3093 <free@plt+0x1ef3>
    39e2:	jmp    29a0 <free@plt+0x1800>
    39e7:	movzx  eax,BYTE PTR [rsp+0xd1]
    39ef:	cmp    al,0x3
    39f1:	ja     29a0 <free@plt+0x1800>
    39f7:	lea    rdx,[rip+0x3842]        # 7240 <_fini+0x311e>
    39fe:	mov    rsi,QWORD PTR [rdx+rax*8]
    3a02:	test   rsi,rsi
    3a05:	je     29a0 <free@plt+0x1800>
    3a0b:	mov    edx,0x50
    3a10:	mov    edi,ebx
    3a12:	call   25a0 <free@plt+0x1400>
    3a17:	jmp    2890 <free@plt+0x16f0>
    3a1c:	movzx  eax,BYTE PTR [rsp+0xd1]
    3a24:	cmp    al,0x7
    3a26:	ja     29a0 <free@plt+0x1800>
    3a2c:	lea    rdx,[rip+0x376d]        # 71a0 <_fini+0x307e>
    3a33:	mov    rsi,QWORD PTR [rdx+rax*8]
    3a37:	test   rsi,rsi
    3a3a:	jne    39ad <free@plt+0x280d>
    3a40:	jmp    29a0 <free@plt+0x1800>
    3a45:	cmp    al,0x77
    3a47:	jne    29a0 <free@plt+0x1800>
    3a4d:	movzx  eax,BYTE PTR [rsp+0xd1]
    3a55:	cmp    al,0x7
    3a57:	ja     29a0 <free@plt+0x1800>
    3a5d:	lea    r12,[rip+0x36bc]        # 7120 <_fini+0x2ffe>
    3a64:	mov    rdi,QWORD PTR [r12+rax*8]
    3a68:	test   rdi,rdi
    3a6b:	jne    3093 <free@plt+0x1ef3>
    3a71:	jmp    29a0 <free@plt+0x1800>
    3a76:	lea    rcx,[rip+0x3723]        # 71a0 <_fini+0x307e>
    3a7d:	mov    r14,QWORD PTR [rcx+rdx*8]
    3a81:	mov    rcx,QWORD PTR [rsp+0x10]
    3a86:	mov    QWORD PTR [rcx+r13*8],r14
    3a8a:	lea    rcx,[rip+0x364f]        # 70e0 <_fini+0x2fbe>
    3a91:	mov    r15,QWORD PTR [rcx+rax*8]
    3a95:	mov    rax,QWORD PTR [rsp+0x18]
    3a9a:	mov    QWORD PTR [rax+r13*8],r15
    3a9e:	test   r14,r14
    3aa1:	je     3abb <free@plt+0x291b>
    3aa3:	test   r15,r15
    3aa6:	je     3abb <free@plt+0x291b>
    3aa8:	movabs rax,0x3444524148534c43
    3ab2:	cmp    QWORD PTR [r14],rax
    3ab5:	je     3d8f <free@plt+0x2bef>
    3abb:	xor    r12d,r12d
    3abe:	xor    eax,eax
    3ac0:	cmp    rax,r13
    3ac3:	je     2fa8 <free@plt+0x1e08>
    3ac9:	mov    rcx,QWORD PTR [rsp+0x10]
    3ace:	cmp    r14,QWORD PTR [rcx+rax*8]
    3ad2:	je     3aeb <free@plt+0x294b>
    3ad4:	mov    rcx,QWORD PTR [rsp+0x18]
    3ad9:	xor    edx,edx
    3adb:	cmp    QWORD PTR [rcx+rax*8],r15
    3adf:	setne  dl
    3ae2:	and    r12d,edx
    3ae5:	add    rax,0x1
    3ae9:	jmp    3ac0 <free@plt+0x2920>
    3aeb:	xor    r12d,r12d
    3aee:	jmp    3ae5 <free@plt+0x2945>
    3af0:	movabs rax,0x3454524550414c43
    3afa:	cmp    QWORD PTR [r12],rax
    3afe:	jne    2c3e <free@plt+0x1a9e>
    3b04:	cmp    QWORD PTR [r13+0x30],0x1
    3b09:	jne    2c3e <free@plt+0x1a9e>
    3b0f:	cmp    QWORD PTR [r12+0x30],0x1
    3b15:	jne    2c3e <free@plt+0x1a9e>
    3b1b:	mov    r14,QWORD PTR [r13+0x8]
    3b1f:	cmp    r14,0x2
    3b23:	ja     2c3e <free@plt+0x1a9e>
    3b29:	cmp    r14,QWORD PTR [r12+0x8]
    3b2e:	jne    2c3e <free@plt+0x1a9e>
    3b34:	mov    rax,QWORD PTR [rip+0x354d]        # 7088 <_fini+0x2f66>
    3b3b:	xor    rax,r13
    3b3e:	cmp    QWORD PTR [r13+0x18],rax
    3b42:	jne    2c3e <free@plt+0x1a9e>
    3b48:	mov    rax,QWORD PTR [rip+0x3539]        # 7088 <_fini+0x2f66>
    3b4f:	xor    rax,r12
    3b52:	cmp    QWORD PTR [r12+0x18],rax
    3b57:	jne    2c3e <free@plt+0x1a9e>
    3b5d:	mov    rax,QWORD PTR [r12+0x10]
    3b62:	cmp    QWORD PTR [r13+0x20],rax
    3b66:	jne    2c3e <free@plt+0x1a9e>
    3b6c:	mov    rax,QWORD PTR [r13+0x10]
    3b70:	cmp    QWORD PTR [r12+0x20],rax
    3b75:	jne    2c3e <free@plt+0x1a9e>
    3b7b:	mov    rax,QWORD PTR [rip+0x3506]        # 7088 <_fini+0x2f66>
    3b82:	xor    rax,r12
    3b85:	cmp    QWORD PTR [r13+0x28],rax
    3b89:	jne    2c3e <free@plt+0x1a9e>
    3b8f:	mov    rax,QWORD PTR [rip+0x34f2]        # 7088 <_fini+0x2f66>
    3b96:	xor    rax,r13
    3b99:	cmp    QWORD PTR [r12+0x28],rax
    3b9e:	jne    2c3e <free@plt+0x1a9e>
    3ba4:	mov    r15,QWORD PTR [r13+0x38]
    3ba8:	mov    rdi,r13
    3bab:	call   2370 <free@plt+0x11d0>
    3bb0:	cmp    r15,rax
    3bb3:	jne    2c3e <free@plt+0x1a9e>
    3bb9:	mov    r15,QWORD PTR [r12+0x38]
    3bbe:	mov    rdi,r12
    3bc1:	call   23c0 <free@plt+0x1220>
    3bc6:	cmp    r15,rax
    3bc9:	jne    2c3e <free@plt+0x1a9e>
    3bcf:	test   r14,r14
    3bd2:	je     3c0e <free@plt+0x2a6e>
    3bd4:	sub    r14,0x1
    3bd8:	je     3e8d <free@plt+0x2ced>
    3bde:	mov    rax,QWORD PTR [rip+0x34ab]        # 7090 <_fini+0x2f6e>
    3be5:	xor    ecx,ecx
    3be7:	mov    rsi,QWORD PTR [rsp+0x8]
    3bec:	mov    edx,0x8
    3bf1:	mov    edi,ebx
    3bf3:	mov    QWORD PTR [rsp+0xa0],rax
    3bfb:	mov    QWORD PTR [r13+0x30],rcx
    3bff:	mov    QWORD PTR [r12+0x30],rcx
    3c04:	call   25a0 <free@plt+0x1400>
    3c09:	jmp    2890 <free@plt+0x16f0>
    3c0e:	mov    rax,QWORD PTR [rip+0x33f3]        # 7008 <_fini+0x2ee6>
    3c15:	jmp    3be5 <free@plt+0x2a45>
    3c17:	movabs rax,0x34455441444e414d
    3c21:	cmp    QWORD PTR [r15],rax
    3c24:	jne    2f57 <free@plt+0x1db7>
    3c2a:	cmp    QWORD PTR [r13+0x30],0x1
    3c2f:	jne    2f57 <free@plt+0x1db7>
    3c35:	cmp    QWORD PTR [r15+0x38],0x1
    3c3a:	jne    2f57 <free@plt+0x1db7>
    3c40:	mov    rax,QWORD PTR [rip+0x3441]        # 7088 <_fini+0x2f66>
    3c47:	xor    rax,r13
    3c4a:	cmp    QWORD PTR [r13+0x10],rax
    3c4e:	jne    2f57 <free@plt+0x1db7>
    3c54:	mov    rax,QWORD PTR [rip+0x342d]        # 7088 <_fini+0x2f66>
    3c5b:	xor    rax,r15
    3c5e:	cmp    QWORD PTR [r15+0x10],rax
    3c62:	jne    2f57 <free@plt+0x1db7>
    3c68:	mov    rax,QWORD PTR [rip+0x3419]        # 7088 <_fini+0x2f66>
    3c6f:	xor    rax,r15
    3c72:	cmp    QWORD PTR [r13+0x18],rax
    3c76:	jne    2f57 <free@plt+0x1db7>
    3c7c:	mov    rax,QWORD PTR [rip+0x3405]        # 7088 <_fini+0x2f66>
    3c83:	xor    rax,r13
    3c86:	cmp    QWORD PTR [r15+0x18],rax
    3c8a:	jne    2f57 <free@plt+0x1db7>
    3c90:	mov    rax,QWORD PTR [r15+0x8]
    3c94:	cmp    QWORD PTR [r13+0x20],rax
    3c98:	jne    2f57 <free@plt+0x1db7>
    3c9e:	mov    rax,QWORD PTR [r13+0x8]
    3ca2:	cmp    QWORD PTR [r15+0x20],rax
    3ca6:	jne    2f57 <free@plt+0x1db7>
    3cac:	mov    r12,QWORD PTR [r13+0x38]
    3cb0:	mov    rdi,r13
    3cb3:	call   2420 <free@plt+0x1280>
    3cb8:	cmp    r12,rax
    3cbb:	jne    2f57 <free@plt+0x1db7>
    3cc1:	mov    r12,QWORD PTR [r15+0x40]
    3cc5:	mov    rdi,r15
    3cc8:	call   2470 <free@plt+0x12d0>
    3ccd:	cmp    r12,rax
    3cd0:	sete   r12b
    3cd4:	movzx  r12d,r12b
    3cd8:	jmp    2f5a <free@plt+0x1dba>
    3cdd:	mov    r12,QWORD PTR [r15+0x30]
    3ce1:	mov    QWORD PTR [rsp+0xa0],rax
    3ce9:	mov    ecx,0x5
    3cee:	mov    QWORD PTR [rsp+0xa8],r13
    3cf6:	mov    rsi,QWORD PTR [rip+0x3383]        # 7080 <_fini+0x2f5e>
    3cfd:	mov    QWORD PTR [rsp+0xb0],r15
    3d05:	mov    rax,QWORD PTR [r13+0x8]
    3d09:	mov    rdi,QWORD PTR [rip+0x3380]        # 7090 <_fini+0x2f6e>
    3d10:	mov    rdx,QWORD PTR [rsp+0x8]
    3d15:	mov    QWORD PTR [rsp+0xb8],rax
    3d1d:	mov    rax,QWORD PTR [r15+0x8]
    3d21:	mov    QWORD PTR [rsp+0xc0],rax
    3d29:	mov    rax,QWORD PTR [rip+0x3358]        # 7088 <_fini+0x2f66>
    3d30:	xor    rdi,rax
    3d33:	call   2260 <free@plt+0x10c0>
    3d38:	cmp    r12,rax
    3d3b:	jne    3057 <free@plt+0x1eb7>
    3d41:	mov    rax,QWORD PTR [r13+0x8]
    3d45:	mov    rdx,QWORD PTR [rip+0x3344]        # 7090 <_fini+0x2f6e>
    3d4c:	xor    rax,r15
    3d4f:	xor    rax,rdx
    3d52:	mov    rdx,QWORD PTR [r15+0x28]
    3d56:	ror    rdx,0x13
    3d5a:	xor    rax,rdx
    3d5d:	mov    rdx,rax
    3d60:	shr    rdx,0x2f
    3d64:	je     3d73 <free@plt+0x2bd3>
    3d66:	cmp    rdx,0x1ffff
    3d6d:	jne    2970 <free@plt+0x17d0>
    3d73:	mov    edi,ebx
    3d75:	call   rax
    3d77:	mov    edx,0xa
    3d7c:	lea    rsi,[rip+0x12e7]        # 506a <_fini+0xf48>
    3d83:	mov    edi,ebx
    3d85:	call   25a0 <free@plt+0x1400>
    3d8a:	jmp    2890 <free@plt+0x16f0>
    3d8f:	movabs rax,0x34504d4154534c43
    3d99:	cmp    QWORD PTR [r15],rax
    3d9c:	jne    3abb <free@plt+0x291b>
    3da2:	cmp    QWORD PTR [r14+0x8],r13
    3da6:	jne    3abb <free@plt+0x291b>
    3dac:	cmp    QWORD PTR [r15+0x8],r13
    3db0:	jne    3abb <free@plt+0x291b>
    3db6:	cmp    QWORD PTR [r14+0x38],0x1
    3dbb:	jne    3abb <free@plt+0x291b>
    3dc1:	cmp    QWORD PTR [r15+0x38],0x1
    3dc6:	jne    3abb <free@plt+0x291b>
    3dcc:	mov    rax,QWORD PTR [rip+0x32b5]        # 7088 <_fini+0x2f66>
    3dd3:	xor    rax,r14
    3dd6:	cmp    QWORD PTR [r14+0x18],rax
    3dda:	jne    3abb <free@plt+0x291b>
    3de0:	mov    rax,QWORD PTR [rip+0x32a1]        # 7088 <_fini+0x2f66>
    3de7:	xor    rax,r15
    3dea:	cmp    QWORD PTR [r15+0x18],rax
    3dee:	jne    3abb <free@plt+0x291b>
    3df4:	mov    rax,QWORD PTR [rip+0x328d]        # 7088 <_fini+0x2f66>
    3dfb:	xor    rax,r15
    3dfe:	cmp    QWORD PTR [r14+0x20],rax
    3e02:	jne    3abb <free@plt+0x291b>
    3e08:	mov    rax,QWORD PTR [rip+0x3279]        # 7088 <_fini+0x2f66>
    3e0f:	xor    rax,r14
    3e12:	cmp    QWORD PTR [r15+0x20],rax
    3e16:	jne    3abb <free@plt+0x291b>
    3e1c:	mov    rax,QWORD PTR [r15+0x10]
    3e20:	cmp    QWORD PTR [r14+0x28],rax
    3e24:	jne    3abb <free@plt+0x291b>
    3e2a:	mov    rdi,QWORD PTR [r14+0x10]
    3e2e:	cmp    QWORD PTR [r15+0x28],rdi
    3e32:	jne    3abb <free@plt+0x291b>
    3e38:	mov    rbx,QWORD PTR [r14+0x30]
    3e3c:	lea    rdx,[r14+0x48]
    3e40:	mov    rsi,r13
    3e43:	call   25e0 <free@plt+0x1440>
    3e48:	cmp    rbx,rax
    3e4b:	jne    3abb <free@plt+0x291b>
    3e51:	cmp    rbx,QWORD PTR [r15+0x30]
    3e55:	jne    3abb <free@plt+0x291b>
    3e5b:	mov    rbx,QWORD PTR [r14+0x40]
    3e5f:	mov    rdi,r14
    3e62:	call   24d0 <free@plt+0x1330>
    3e67:	cmp    rbx,rax
    3e6a:	jne    3abb <free@plt+0x291b>
    3e70:	mov    rbx,QWORD PTR [r15+0x40]
    3e74:	mov    rdi,r15
    3e77:	call   2520 <free@plt+0x1380>
    3e7c:	cmp    rbx,rax
    3e7f:	sete   al
    3e82:	movzx  eax,al
    3e85:	and    r12d,eax
    3e88:	jmp    3abe <free@plt+0x291e>
    3e8d:	mov    rax,QWORD PTR [rip+0x31f4]        # 7088 <_fini+0x2f66>
    3e94:	jmp    3be5 <free@plt+0x2a45>
    3e99:	cs nop WORD PTR [rax+rax*1+0x0]
    3ea3:	cs nop WORD PTR [rax+rax*1+0x0]
    3ead:	cs nop WORD PTR [rax+rax*1+0x0]
    3eb7:	cs nop WORD PTR [rax+rax*1+0x0]
    3ec1:	cs nop WORD PTR [rax+rax*1+0x0]
    3ecb:	cs nop WORD PTR [rax+rax*1+0x0]
    3ed5:	cs nop WORD PTR [rax+rax*1+0x0]
    3edf:	cs nop WORD PTR [rax+rax*1+0x0]
    3ee9:	cs nop WORD PTR [rax+rax*1+0x0]
    3ef3:	cs nop WORD PTR [rax+rax*1+0x0]
    3efd:	cs nop WORD PTR [rax+rax*1+0x0]
    3f07:	cs nop WORD PTR [rax+rax*1+0x0]
    3f11:	cs nop WORD PTR [rax+rax*1+0x0]
    3f1b:	cs nop WORD PTR [rax+rax*1+0x0]
    3f25:	cs nop WORD PTR [rax+rax*1+0x0]
    3f2f:	cs nop WORD PTR [rax+rax*1+0x0]
    3f39:	cs nop WORD PTR [rax+rax*1+0x0]
    3f43:	cs nop WORD PTR [rax+rax*1+0x0]
    3f4d:	cs nop WORD PTR [rax+rax*1+0x0]
    3f57:	cs nop WORD PTR [rax+rax*1+0x0]
    3f61:	cs nop WORD PTR [rax+rax*1+0x0]
    3f6b:	cs nop WORD PTR [rax+rax*1+0x0]
    3f75:	cs nop WORD PTR [rax+rax*1+0x0]
    3f7f:	cs nop WORD PTR [rax+rax*1+0x0]
    3f89:	cs nop WORD PTR [rax+rax*1+0x0]
    3f93:	cs nop WORD PTR [rax+rax*1+0x0]
    3f9d:	cs nop WORD PTR [rax+rax*1+0x0]
    3fa7:	cs nop WORD PTR [rax+rax*1+0x0]
    3fb1:	cs nop WORD PTR [rax+rax*1+0x0]
    3fbb:	cs nop WORD PTR [rax+rax*1+0x0]
    3fc5:	cs nop WORD PTR [rax+rax*1+0x0]
    3fcf:	cs nop WORD PTR [rax+rax*1+0x0]
    3fd9:	cs nop WORD PTR [rax+rax*1+0x0]
    3fe3:	cs nop WORD PTR [rax+rax*1+0x0]
    3fed:	cs nop WORD PTR [rax+rax*1+0x0]
    3ff7:	nop    WORD PTR [rax+rax*1+0x0]
    4000:	push   r15
    4002:	xor    edx,edx
    4004:	mov    esi,0x1
    4009:	push   r14
    400b:	push   r13
    400d:	mov    r13d,edi
    4010:	mov    edi,0x1
    4015:	push   r12
    4017:	push   rbp
    4018:	push   rbx
    4019:	sub    rsp,0x1088
    4020:	call   1050 <socket@plt>
    4025:	test   eax,eax
    4027:	js     40ca <free@plt+0x2f2a>
    402d:	movdqa xmm0,XMMWORD PTR [rip+0x107b]        # 50b0 <_fini+0xf8e>
    4035:	mov    ebx,eax
    4037:	mov    ecx,0x52
    403c:	xor    eax,eax
    403e:	lea    rdi,[rsp+0x2c]
    4043:	lea    rsi,[rsp+0x10]
    4048:	mov    edx,0x6e
    404d:	mov    WORD PTR [rsp+0x10],0x1
    4054:	rep stos BYTE PTR es:[rdi],al
    4056:	movups XMMWORD PTR [rsp+0x12],xmm0
    405b:	movdqu xmm0,XMMWORD PTR [rip+0x1057]        # 50ba <_fini+0xf98>
    4063:	mov    edi,ebx
    4065:	movups XMMWORD PTR [rsp+0x1c],xmm0
    406a:	call   1020 <connect@plt>
    406f:	test   eax,eax
    4071:	jne    40ca <free@plt+0x2f2a>
    4073:	mov    edx,0x10
    4078:	lea    rsi,[rip+0x1021]        # 50a0 <_fini+0xf7e>
    407f:	mov    edi,ebx
    4081:	call   25a0 <free@plt+0x1400>
    4086:	xor    eax,eax
    4088:	mov    DWORD PTR [rsp],r13d
    408c:	mov    QWORD PTR [rsp+0x6],rax
    4091:	mov    WORD PTR [rsp+0xe],0x0
    4098:	mov    WORD PTR [rsp+0x4],0x1
    409f:	mov    DWORD PTR [rsp+0x8],ebx
    40a3:	mov    WORD PTR [rsp+0xc],0x1
    40aa:	mov    edx,0xffffffff
    40af:	mov    esi,0x2
    40b4:	mov    rdi,rsp
    40b7:	call   1130 <poll@plt>
    40bc:	test   eax,eax
    40be:	jg     40d1 <free@plt+0x2f31>
    40c0:	call   1140 <__errno_location@plt>
    40c5:	cmp    DWORD PTR [rax],0x4
    40c8:	je     40aa <free@plt+0x2f0a>
    40ca:	xor    edi,edi
    40cc:	call   1160 <_exit@plt>
    40d1:	xor    ebp,ebp
    40d3:	test   BYTE PTR [rsp+rbp*8+0x6],0x19
    40d8:	je     4111 <free@plt+0x2f71>
    40da:	mov    edi,DWORD PTR [rsp+rbp*8]
    40dd:	test   rbp,rbp
    40e0:	mov    r15d,ebx
    40e3:	mov    edx,0x1000
    40e8:	lea    rsi,[rsp+0x80]
    40f0:	cmovne r15d,r13d
    40f4:	call   10e0 <read@plt>
    40f9:	test   rax,rax
    40fc:	jle    40ca <free@plt+0x2f2a>
    40fe:	mov    rdx,rax
    4101:	lea    rsi,[rsp+0x80]
    4109:	mov    edi,r15d
    410c:	call   25a0 <free@plt+0x1400>
    4111:	lea    rax,[rbp+0x1]
    4115:	mov    ebp,0x1
    411a:	cmp    rax,0x2
    411e:	je     40aa <free@plt+0x2f0a>
    4120:	jmp    40d3 <free@plt+0x2f33>

Disassembly of section .fini:

0000000000004122 <_fini>:
    4122:	push   rax
    4123:	pop    rax
    4124:	ret
