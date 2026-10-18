# -*- coding: utf-8 -*-
"""CSV → LaTeX 表格片段（配合 labreport.cls 的 \\labtable）。

单元格按原样的字符串输出，**不做数值格式化**：0.40 不会变成 0.4，原始数据的有效数字保持不变。

用法：
  python csv2tex.py data/t2.csv --caption "不同灯丝电流下的阳极电流" --label tab:ia --out tab/t2.tex
  python csv2tex.py data/instr.csv --style grid --cols "l X X" --out tab/instr.tex
  然后在正文里 \\input{tab/t2.tex}

表头写法（CSV 第一行）：
  · 直接写 LaTeX：$I_\\mathrm{f}$/A、$\\sqrt{U_a}$/$\\sqrt{\\mathrm{V}}$ —— 含 $ 或 \\ 的单元格原样输出
  · 简写也可以：I_{f}/A、U_{a}/V、T/10^{3}K —— 自动把 X_{..} / X^{..} 包进数学模式
选项：
  --style booktabs|grid   三线表（默认）或全框线表
  --cols "c c c"          列格式；含 X 时用 tabularx 撑满行宽
  --transpose             行列互换（测量点多、量少时把表横过来）
  --font small|footnotesize|scriptsize
"""
import argparse
import csv
import io
import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SPECIAL = {'%': r'\%', '&': r'\&', '#': r'\#', '~': r'\textasciitilde{}'}
SUBSUP = re.compile(r'([A-Za-z0-9\u0370-\u03ff\u00b5]+(?:[_^]\{[^{}]*\}|[_^][A-Za-z0-9])+)')
SQRT = re.compile(r'√([A-Za-zͰ-Ͽ]+(?:[_^]\{[^{}]*\}|[_^][A-Za-z0-9])*)')
GREEK = {'μ': r'\mu ', 'Ω': r'\Omega ', 'α': r'\alpha ', 'β': r'\beta ', 'λ': r'\lambda ', 'θ': r'\theta ',
         'Δ': r'\Delta ', 'ρ': r'\rho ', 'ω': r'\omega ', 'φ': r'\varphi ', 'ε': r'\varepsilon '}


def cell(s):
    s = s.strip()
    if '$' in s or '\\' in s:
        return s
    if re.fullmatch(r'-\d[\d.]*', s):          # 负数用真正的减号
        return '$' + s + '$'
    out = ''.join(SPECIAL.get(ch, ch) for ch in s)

    def greek(t):
        for k, v in GREEK.items():
            t = t.replace(k, v)
        return t
    # √U_{a} → $\sqrt{U_{a}}$；其余 X_{..} / X^{..} → $X_{..}$（只处理数学模式之外的部分）
    out = SQRT.sub(lambda m: '$\\sqrt{%s}$' % greek(m.group(1)), out)
    parts = out.split('$')
    for i in range(0, len(parts), 2):
        parts[i] = SUBSUP.sub(lambda m: '$' + greek(m.group(1)) + '$', parts[i])
    return '$'.join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv')
    ap.add_argument('--caption', required=True)
    ap.add_argument('--label')
    ap.add_argument('--style', choices=['booktabs', 'grid'], default='booktabs')
    ap.add_argument('--cols', help='列格式，空格分隔，如 "c c c" 或 "l X X"')
    ap.add_argument('--transpose', action='store_true')
    ap.add_argument('--font', default='small')
    ap.add_argument('--out', help='输出 .tex；不给就打印')
    a = ap.parse_args()

    with io.open(a.csv, encoding='utf-8-sig') as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
    for h in rows[0]:
        if '$' not in h and '\\' not in h and re.search(r'_[A-Za-z]{2,}', h):
            print('⚠ 表头“%s”像程序变量名，“_”后面会被当成下标印出来。请把 CSV 表头直接写成要显示的样子，'
                  '如 Db(0)/cm 或 $D_{b0}$/cm' % h, file=sys.stderr)
    if a.transpose:
        rows = [list(c) for c in zip(*rows)]
    ncol = max(len(r) for r in rows)
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    cols = a.cols.split() if a.cols else ['c'] * ncol
    if len(cols) != ncol:
        raise SystemExit('--cols 给了 %d 列，CSV 有 %d 列' % (len(cols), ncol))
    use_x = any(c == 'X' for c in cols)
    cols = [r'>{\centering\arraybackslash}X' if c == 'X' else c for c in cols]
    grid = a.style == 'grid'
    spec = ('|' + '|'.join(cols) + '|') if grid else ''.join(cols)
    env = 'tabularx' if use_x else 'tabular'
    head = r'\begin{tabularx}{\linewidth}{%s}' % spec if use_x else r'\begin{tabular}{%s}' % spec
    top, mid, bot = (r'\hline', r'\hline', r'\hline') if grid else (r'\toprule', r'\midrule', r'\bottomrule')

    body = [head, top, ' & '.join(cell(c) for c in rows[0]) + r' \\', mid]
    for r in rows[1:]:
        body.append(' & '.join(cell(c) for c in r) + r' \\' + (r' \hline' if grid else ''))
    if grid:
        body[-1] = body[-1][:-len(r' \hline')]
    body += [bot, r'\end{%s}' % env]

    lab = '[%s]' % a.label if a.label else ''
    font = '' if a.font == 'small' else '\\' + a.font + ' '
    tex = '%% 由 csv2tex.py 从 %s 生成，改数据请改 CSV 后重新生成\n\\labtable{%s}%s{%s\n%s}\n' % (
        os.path.basename(a.csv), a.caption, lab, font, '\n'.join(body))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with io.open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(tex)
        print('SAVED', a.out, '(%d 行 × %d 列)' % (len(rows), ncol))
    else:
        print(tex)


if __name__ == '__main__':
    main()
