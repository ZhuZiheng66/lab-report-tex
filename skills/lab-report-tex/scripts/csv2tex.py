# -*- coding: utf-8 -*-
"""CSV → LaTeX 表格片段（配合 labreport.cls 的 \\labtable）。

单元格按原样的字符串输出，**不做数值格式化**：0.40 不会变成 0.4，原始数据的有效数字保持不变。

**默认安全转义**：表题、表头、数据里的 \\ { } $ & % # _ ^ ~ 都会被转义成普通字符，
所以 CSV 里的任何内容都不会破坏 LaTeX 结构或注入命令。负数自动排成真正的减号 $-1.23$。

用法：
  python csv2tex.py data/t2.csv --caption "不同灯丝电流下的阳极电流" --label tab:ia --out tab/t2.tex
  python csv2tex.py data/instr.csv --style grid --cols "l X X" --out tab/instr.tex
  然后在正文里 \\input{tab/t2.tex}
选项：
  --style booktabs|grid   三线表（默认）或全框线表
  --cols "c c c"          列格式；含 X 时用 tabularx 撑满行宽
  --transpose             行列互换（测量点多、量少时把表横过来）
  --font small|footnotesize|scriptsize
  --math-shorthand        把表头里的 I_{f}、T^{2}、√U_{a} 这类简写排成数学式（花括号里只允许字母数字，其余照常转义）
  --raw-latex             ⚠ 表题和表头按 LaTeX 原样输出（可写 $I_\\mathrm{f}$/A）。只用于你自己写的、可信的
                          表头；不要对来源不明的 CSV 使用——里面的任意 LaTeX 命令都会被执行。数据单元格始终转义。
"""
import argparse
import csv
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import record  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ESCAPE = {
    '\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '$': r'\$', '&': r'\&', '%': r'\%',
    '#': r'\#', '_': r'\_', '^': r'\textasciicircum{}', '~': r'\textasciitilde{}',
}
NEG = re.compile(r'[-−]\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')
# 简写：符号 + 下标/上标，花括号内容只允许安全字符
SHORT = re.compile(r'(√)?([A-Za-z\u0370-\u03ff\u00b5]{1,4}\d*)((?:[_^](?:\{[A-Za-z0-9.+\-]{1,12}\}|[A-Za-z0-9]))+)')
GREEK = {'μ': r'\mu ', 'Ω': r'\Omega ', 'α': r'\alpha ', 'β': r'\beta ', 'λ': r'\lambda ', 'θ': r'\theta ',
         'Δ': r'\Delta ', 'ρ': r'\rho ', 'ω': r'\omega ', 'φ': r'\varphi ', 'ε': r'\varepsilon ', 'σ': r'\sigma '}


def escape(s):
    return ''.join(ESCAPE.get(ch, ch) for ch in s)


def cell(s, shorthand=False):
    """普通文本 → 安全的 LaTeX。"""
    s = s.strip()
    if NEG.fullmatch(s):                        # 负数用真正的减号
        return '$-' + s[1:] + '$'
    if not shorthand:
        return escape(s)
    out, pos = [], 0
    for m in SHORT.finditer(s):
        out.append(escape(s[pos:m.start()]))
        base = m.group(2)
        for k, v in GREEK.items():
            base = base.replace(k, v)
        math = base + m.group(3)
        out.append('$\\sqrt{%s}$' % math if m.group(1) else '$%s$' % math)
        pos = m.end()
    out.append(escape(s[pos:]))
    return ''.join(out)


def safe_label(lab):
    if not re.fullmatch(r'[A-Za-z0-9:_.\-]+', lab):
        raise SystemExit('--label 只能用字母、数字和 : _ . -，例如 tab:ia')
    return lab


def build(rows, caption, label=None, style='booktabs', cols=None, transpose=False, font='small',
          raw_latex=False, shorthand=False, source=''):
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        raise SystemExit('CSV 是空的')
    if not raw_latex:
        for h in rows[0]:
            if re.search(r'_[A-Za-z]{2,}', h):
                print('⚠ 表头“%s”像程序变量名（含 _），会原样印出下划线。请把表头写成要显示的样子，'
                      '如 Db(0)/cm；需要下标时用 --math-shorthand（D_{b0}/cm）' % h, file=sys.stderr)
    if transpose:
        rows = [list(c) for c in zip(*rows)]
    ncol = max(len(r) for r in rows)
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    cols = cols.split() if cols else ['c'] * ncol
    if len(cols) != ncol:
        raise SystemExit('--cols 给了 %d 列，CSV 有 %d 列' % (len(cols), ncol))
    bad = [c for c in cols if not re.fullmatch(r'[lcrX]|p\{\d+(\.\d+)?(cm|mm|em)\}', c)]
    if bad:
        raise SystemExit('--cols 只能用 l c r X 或 p{3cm}：%s' % bad)
    use_x = 'X' in cols
    cols = [r'>{\centering\arraybackslash}X' if c == 'X' else c for c in cols]
    grid = style == 'grid'
    spec = ('|' + '|'.join(cols) + '|') if grid else ''.join(cols)
    env = 'tabularx' if use_x else 'tabular'
    head = r'\begin{tabularx}{\linewidth}{%s}' % spec if use_x else r'\begin{tabular}{%s}' % spec
    top, mid, bot = (r'\hline', r'\hline', r'\hline') if grid else (r'\toprule', r'\midrule', r'\bottomrule')

    hcell = (lambda c: c.strip()) if raw_latex else (lambda c: cell(c, shorthand))
    body = [head, top, ' & '.join(hcell(c) for c in rows[0]) + r' \\', mid]
    for r in rows[1:]:
        body.append(' & '.join(cell(c) for c in r) + r' \\' + (r' \hline' if grid else ''))
    if grid:
        body[-1] = body[-1][:-len(r' \hline')]
    body += [bot, r'\end{%s}' % env]

    cap = caption if raw_latex else escape(caption)
    lab = '[%s]' % safe_label(label) if label else ''
    if font not in ('small', 'footnotesize', 'scriptsize', 'normalsize'):
        raise SystemExit('--font 只能是 small / footnotesize / scriptsize / normalsize')
    fnt = '' if font == 'small' else '\\' + font + ' '
    src = re.sub(r'[\r\n]', ' ', source)
    return ('%% 由 csv2tex.py 从 %s 生成，改数据请改 CSV 后重新生成\n\\labtable{%s}%s{%s\n%s}\n'
            % (src, cap, lab, fnt, '\n'.join(body)), len(rows), ncol)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv')
    ap.add_argument('--caption', required=True)
    ap.add_argument('--label')
    ap.add_argument('--style', choices=['booktabs', 'grid'], default='booktabs')
    ap.add_argument('--cols', help='列格式，空格分隔，如 "c c c" 或 "l X X"')
    ap.add_argument('--transpose', action='store_true')
    ap.add_argument('--font', default='small')
    ap.add_argument('--math-shorthand', action='store_true')
    ap.add_argument('--raw-latex', action='store_true', help='⚠ 表题和表头按 LaTeX 原样输出（仅限可信内容）')
    ap.add_argument('--out', help='输出 .tex；不给就打印')
    a = ap.parse_args()

    with io.open(a.csv, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    tex, nr, nc = build(rows, a.caption, a.label, a.style, a.cols, a.transpose, a.font,
                        a.raw_latex, a.math_shorthand, os.path.basename(a.csv))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with io.open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(tex)
        record(a.out, [a.csv], script='csv2tex.py')
        print('SAVED', a.out, '(%d 行 × %d 列)' % (nr, nc))
    else:
        print(tex)


if __name__ == '__main__':
    main()
