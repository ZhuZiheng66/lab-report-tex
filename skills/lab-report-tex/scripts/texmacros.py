# -*- coding: utf-8 -*-
"""把计算结果写成 LaTeX 宏，正文用 \\RichK 这类宏引用，避免手抄数字出错。

文件格式：每行一个 `\\def\\Name{值}%  来源说明`。同名宏再次写入时替换原行，可反复运行脚本。
在 report.tex 里 `\\input{results.tex}`，正文写 `$k=\\num{\\RichK}$`。
"""
import io
import os
import re

NAME_RE = re.compile(r'^[A-Za-z]+$')


def num(x, digits=4):
    """有效数字格式，交给 siunitx \\num 排版（-2.646e4 → −2.646×10⁴）。"""
    if isinstance(x, str):
        return x
    if x == 0:
        return '0'
    if abs(x) < 1e-3 or abs(x) >= 1e4:
        return '%.*e' % (digits - 1, x)
    return '%.*g' % (digits, x)


def write_macros(path, macros, source=''):
    """macros: [(name, value_str)]；按名字更新到 path。"""
    lines = []
    if os.path.exists(path):
        with io.open(path, encoding='utf-8') as f:
            lines = f.read().splitlines()
    for name, value in macros:
        if not NAME_RE.match(name):
            raise SystemExit('宏名只能用英文字母（LaTeX 限制）：%r' % name)
        new = '\\def\\%s{%s}%%  %s' % (name, value, source)
        pat = re.compile(r'^\\def\\%s\{' % name)
        for i, ln in enumerate(lines):
            if pat.match(ln):
                lines[i] = new
                break
        else:
            lines.append(new)
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
