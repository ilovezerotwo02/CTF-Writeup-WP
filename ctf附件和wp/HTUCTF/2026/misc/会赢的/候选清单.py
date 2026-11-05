# -*- coding: utf-8 -*-
"""生成 会赢的(34) 的已试/未试候选清单（本脚本不提交任何 flag）"""
import io, os

CUR = '\u2019'          # U+2019 弯引号（文件里的真实字节）
STR = "'"               # ASCII 直引号
p1c = '1' + CUR + 'd_w1n_y0u' + CUR + 'r3_7h3_ch4113n63r_'
p1s = "1'd_w1n_y0u'r3_7h3_ch4113n63r_"
p2  = '_my_4p0106135_f0r_f4111n6_70_3n73r741n_y0u_5ukun4-54m4'
p2u = p2.replace('-', '_')

out = io.StringIO()
w = out.write

w('# 会赢的(34) flag 候选清单\n\n')
w('两段原始数据（CRC/魔数级确认）：\n\n')
w('```\n')
w('p1 = %s   (30 字符 / 34 字节)\n' % p1c)
w('p2 = %s   (54 字符)\n' % p2)
w('```\n\n')
w('> p1 的撇号是 **U+2019**（不是 ASCII `\'`）；p2 的 `-` 是 ASCII U+002D\n')
w('> 平台 attempts 已达 **97**，下列「已试」均返回 WrongAnswer\n\n')

# ---------------- 已试过的 ----------------
w('## 一、已提交过且 WrongAnswer（不要再重复）\n\n')

w('### 批次1 try.py（16 条）\n\n')
tried = []
for p1, tag in ((p1c, '弯引号'), (p1s, '直引号')):
    for p2v, tag2 in ((p2, 'dash'), (p2u, 'dash换us')):
        for body, jt in ((p1 + p2v, '双下划线'), (p1[:-1] + p2v, '单下划线'),
                         (p1[:-1] + p2v[1:], '无下划线')):
            tried.append(('%s/%s/%s' % (tag, tag2, jt), body))
tried.append(('仅p2(去头_)', p2[1:]))
tried.append(('仅p2(带头_)', p2))
tried.append(('p2+p1', p2 + p1c))
tried.append(('p2[1:]+_+p1[:-1]', p2[1:] + '_' + p1c[:-1]))
for n, b in tried:
    w('| %s | `HTUCTF{%s}` |\n' % (n, b))
w('\n')

w('### 批次2 try2.py（28 条：首字母 {1,I} × 引号 {7种} × 接缝 {双,单}）\n\n')
w('引号种类：`’`(U+2019) `’`(U+2018) `\'`(U+0027) `ʼ`(U+02BC) `` ` ``(U+0060) '
  '空(无引号) `_`(U+005F)\n\n')
for I in ('1', 'I'):
    for qn, q in (('U+2019', '\u2019'), ('U+0027', "'"), ('U+02BC', '\u02bc'),
                  ('U+2018', '\u2018'), ('U+0060', '`'), ('none', ''), ('U+005F', '_')):
        pp = '%s%sd_w1n_y0u%sr3_7h3_ch4113n63r_' % (I, q, q)
        w('| I=%s q=%s 双下划线 | `HTUCTF{%s}` |\n' % (I, qn, pp + p2))
        w('| I=%s q=%s 单下划线 | `HTUCTF{%s}` |\n' % (I, qn, pp[:-1] + p2))
w('\n')

w('### 批次3 try3.py（约 21 条）\n\n')
for X in ('.', ',', '-', '!', ' ', '_', '?'):
    w('| 插 %r (保留p1尾_) | `HTUCTF{%s}` |\n' % (X, p1c + X + p2))
    w('| 插 %r (去p1尾_)   | `HTUCTF{%s}` |\n' % (X, p1c[:-1] + X + p2))
w('| 英文还原 双下划线 | `HTUCTF{I\'d_win_you%spre_the_challenger__my_apologies_for_failing_to_entertain_you_sukuna-sama}` |\n' % CUR)
w('| 英文还原 单下划线 | `HTUCTF{I\'d_win_you%spre_the_challenger_my_apologies_for_failing_to_entertain_you_sukuna-sama}` |\n' % CUR)
w('| 英文还原 首字母大写 双 | `HTUCTF{I\'d_win_you\'re_the_challenger__My_apologies_for_failing_to_entertain_you_Sukuna-sama}` |\n')
w('| 英文还原 首字母大写 单 | `HTUCTF{I\'d_win_you\'re_the_challenger_My_apologies_for_failing_to_entertain_you_Sukuna-sama}` |\n')
w('| 英文还原 全小写 双 | `HTUCTF{i\'d_win_you\'re_the_challenger__my_apologies_for_failing_to_entertain_you_sukuna-sama}` |\n')
w('| 仅p1(弯,带尾_) | `HTUCTF{%s}` |\n' % p1c)
w('| 仅p1(弯,去尾_) | `HTUCTF{%s}` |\n' % p1c[:-1])
w('\n')

w('### 批次4 try4.py（8 条，脚本执行中被中断，后半可能未真正发出）\n\n')
raw = '00GN10CNuV3a1VzX1BTef5WM0cjczcjbz8FM38lNuFTMxQjZfJHMm9VNzEjNwEDMwRzX512X'
b1 = 'MeKAmWRfdzFuX3kwdeKAmXIzXzdoM19jaDQxMTNuNjNyX2'
b2 = raw[::-1]
for n, b in (('flag.txt 原串', raw), ('flag.txt 反转串', b2), ('jpeg b64 原串', b1),
             ('b64_1+b64_2', b1 + b2), ('b64_2+b64_1', b2 + b1),
             ('中文 会赢的', '会赢的'), ('中文 五条悟赢了', '五条悟赢了')):
    w('| %s | `HTUCTF{%s}` |\n' % (n, b))
w('\n')

# ---------------- 未试过的 ----------------
w('## 二、尚未提交过的候选（按证据强度排序）\n\n')
w('> 以下均未提交，供手动挑选\n\n')

cands = [
    ('① 【已提交过，若题目 flag 已修正则首选重试】双下划线', p1c + p2),
    ('② 【已提交过】单下划线', p1c[:-1] + p2),
    ('③ 英文还原 + 下划线 + 全弯引号 + 双',
     'I%sd_win_you%sre_the_challenger__my_apologies_for_failing_to_entertain_you_sukuna-sama' % (CUR, CUR)),
    ('④ 英文还原 + 下划线 + 全弯引号 + 单',
     'I%sd_win_you%sre_the_challenger_my_apologies_for_failing_to_entertain_you_sukuna-sama' % (CUR, CUR)),
    ('⑤ 英文还原 + 真实空格 + 弯引号',
     'I%sd win you%sre the challenger my apologies for failing to entertain you sukuna-sama' % (CUR, CUR)),
    ('⑥ 英文还原 + 真实空格 + 直引号',
     "I'd win you're the challenger my apologies for failing to entertain you sukuna-sama"),
    ('⑦ 英文原句（带逗号，首字母大写）',
     "I'd win, you're the challenger, my apologies for failing to entertain you, Sukuna-sama"),
    ('⑧ 英文原句（句号+空格）',
     "I'd win. you're the challenger. My apologies for failing to entertain you, Sukuna-sama"),
    ('⑨ 双下划线 + 句末句号', p1c + p2 + '.'),
    ('⑩ 双下划线 + sama 大写', p1c + p2[:-4] + 'S4m4'),
    ('⑪ 双下划线 + 全大写', (p1c + p2).upper()),
    ('⑫ 逗号接缝 + 双下划线', p1c[:-1] + ',' + p2),
    ('⑬ 句号空格接缝', p1c[:-1] + '. _' + p2[1:]),
]
for i, (n, b) in enumerate(cands, 1):
    w('%d. **%s**\n' % (i, n))
    w('   ```\n   HTUCTF{%s}\n   ```\n' % b)

w('\n## 三、结论\n\n')
w('- 附件重新下载后 **md5 未变**（`7b9eb594f5ecd392f6019f0e66cb5c4c`，72846B），'
  'URL hash、题目描述、hints 均无变化\n')
w('- 文件层面已穷尽：JPEG 无 APPn/COM、zip extra 标准、注释后 0 多余字节、'
  '7z 内仅 1 个文件且 `unused_data=0`\n')
w('- 长度铁证：p1=30 字符 = `"I\'d win you\'re the challenger "`，'
  'p2=54 字符 = `" my apologies for failing to entertain you sukuna-sama"`，'
  '两段各带一个真实空格 → 接缝是两个空格位\n')

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '候选清单.md')
open(p, 'w', encoding='utf-8').write(out.getvalue())
print('written:', p, len(out.getvalue()), 'chars')
