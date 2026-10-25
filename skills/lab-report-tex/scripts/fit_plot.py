# -*- coding: utf-8 -*-
"""实验数据作图 + 拟合（实验报告用）。

用法：
  python fit_plot.py data.csv --x Is --y VH --xlabel "$I_s$/mA" --ylabel "$V_H$/mV" --out fig/fig1.pdf
  python fit_plot.py data.csv --x sqrtUa --y lgIa --group If --group-label "$I_f$={}A" --out fig/fig1.pdf
  python fit_plot.py data.csv --x UG2 --y IP --mode curve --mark-peaks --out fig/fh.pdf
  python fit_plot.py loop.csv --x H --y B --mode line --out fig/hysteresis.pdf      # 磁滞回线：按记录顺序连线
  python fit_plot.py spec.txt --x 0 --y 1 --mode line --no-markers --mark-peaks 5 --out fig/spec.pdf   # 仪器导出的光谱
  python fit_plot.py iv.csv --x U --y I --mode curve --logy --out fig/iv.pdf       # PN 结伏安特性（半对数）
模式 --mode：
  fit     数据点 + 最小二乘直线（默认），打印 k、b、r、u(k)、u(b)
  origin  过原点拟合 y=kx
  poly    多项式拟合（--deg N，默认 2），打印各项系数
  curve   按 x 排序后连线（装了 scipy 时为样条光滑曲线），不拟合：特性曲线、分布曲线、谐振曲线
  line    按数据原有顺序连线，不排序：回线、往返测量、时序
  scatter 只画点
其它选项：
  --group COL     按 COL 分组，每组各画一条（多组曲线 / 多组拟合）
  --mark-peaks [N] 标出局部极大值（N>0 时只标最高的 N 个），打印峰位；--mark-valleys 同理标极小值
  --logx/--logy   对数坐标     --no-markers  不画数据点标记（导出的密集数据用）
  --extend-to-zero 拟合线延长到 x=0（外延法）
  --hline Y / --vline X  画参考线（如理论值、零点），可多次给
  --macros F --name P   把拟合结果写成宏 \\PK \\PB \\PR \\PUK \\PUB（分组时为 \\PKa \\PKb …）
  --digits N      写宏时保留的有效数字（默认 4）
输入：CSV（逗号）或 TXT（空白/制表符/分号分隔，仪器导出常见）；--x/--y 可写列名或列序号（从 0 开始，无表头时用）。
输出 .pdf 为矢量图（推荐用于 LaTeX），.png 为 300 dpi 位图。图题不画在图里，由 LaTeX 的 \\labfig 负责。
结果以 JSON 打印在最后一行。
"""
import argparse
import csv
import io
import json
import logging
import math
import os
import re
import string
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import record  # noqa: E402
from texmacros import num, write_macros  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 西文 Times 风格；中文找系统里有的宋体/黑体（Windows / macOS / Linux 各自的名字）
CJK_CANDIDATES = ['SimSun', 'Songti SC', 'STSong', 'Noto Serif CJK SC', 'Source Han Serif SC',
                  'SimHei', 'PingFang SC', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Microsoft YaHei']
_have = {f.name for f in font_manager.fontManager.ttflist}
CJK = [f for f in CJK_CANDIDATES if f in _have]
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'TeX Gyre Termes', 'DejaVu Serif'] + CJK
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['pdf.fonttype'] = 42
logging.getLogger('fontTools').setLevel(logging.ERROR)  # 嵌入中文字体时的子集化噪音
ZH = FontProperties(family=CJK or ['DejaVu Sans'], size=10)
MARKERS = ['o', 's', '^', 'v', 'D', 'x', '+', '*']


def has_cjk(text):
    return any('一' <= ch <= '鿿' for ch in text)


def label_kw(text):
    return {'fontproperties': ZH} if has_cjk(text) else {'fontsize': 10}


def read_rows(path):
    """返回 (表头或 None, 行列表)。支持逗号 CSV 和空白/制表符/分号分隔的 TXT。"""
    with io.open(path, encoding='utf-8-sig', errors='replace') as f:
        text = f.read()
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith('#')]
    sample = '\n'.join(lines[:20])
    if ',' in sample:
        rows = list(csv.reader(lines))
    elif ';' in sample:
        rows = [ln.split(';') for ln in lines]
    else:
        rows = [re.split(r'[\s\t]+', ln.strip()) for ln in lines]
    rows = [[c.strip() for c in r] for r in rows]

    def isnum(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
    # 跳过仪器导出文件开头的说明行：找到第一行“全是数字”的位置，它前一行若非数字则当表头
    first = next((i for i, r in enumerate(rows) if r and all(isnum(c) for c in r if c)), None)
    if first is None:
        raise SystemExit('%s 里没找到数值行' % path)
    header = rows[first - 1] if first > 0 and not all(isnum(c) for c in rows[first - 1] if c) else None
    data = [r for r in rows[first:] if r and all(isnum(c) for c in r if c)]
    return header, data


def col_index(header, name):
    if header and name in header:
        return header.index(name)
    if re.fullmatch(r'\d+', name):
        return int(name)
    raise SystemExit('没有列 %r。现有列：%s（无表头时用列序号 0、1、2…）' % (name, header))


def load(path, xc, yc, gc=None):
    header, rows = read_rows(path)
    ix, iy = col_index(header, xc), col_index(header, yc)
    ig = col_index(header, gc) if gc else None
    groups = {}
    for r in rows:
        if max(ix, iy) >= len(r) or not r[ix] or not r[iy]:
            continue
        g = r[ig] if ig is not None else ''
        groups.setdefault(g, []).append((float(r[ix]), float(r[iy])))
    return [(g, np.array([p[0] for p in pts]), np.array([p[1] for p in pts])) for g, pts in groups.items()]


def linfit(x, y, origin=False):
    n = len(x)
    if origin:
        k = float((x * y).sum() / (x * x).sum())
        res = y - k * x
        uk = math.sqrt((res ** 2).sum() / (n - 1) / (x * x).sum()) if n > 1 else 0.0
        return dict(k=k, b=0.0, r=float(np.corrcoef(x, y)[0, 1]), u_k=uk, u_b=0.0, n=n)
    k, b = np.polyfit(x, y, 1)
    res = y - (k * x + b)
    s = math.sqrt((res ** 2).sum() / (n - 2)) if n > 2 else 0.0
    sxx = ((x - x.mean()) ** 2).sum()
    uk = s / math.sqrt(sxx) if sxx else 0.0
    ub = uk * math.sqrt((x * x).mean())
    r = float(np.corrcoef(x, y)[0, 1]) if np.std(y) > 0 else float('nan')
    return dict(k=float(k), b=float(b), r=r, u_k=uk, u_b=ub, n=n)


def extrema(xs, ys, top, sign=1):
    idx = [j for j in range(1, len(ys) - 1)
           if sign * ys[j] >= sign * ys[j - 1] and sign * ys[j] > sign * ys[j + 1]]
    if top and top > 0:
        idx = sorted(sorted(idx, key=lambda j: -sign * ys[j])[:top])
    return idx


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv')
    ap.add_argument('--x', required=True)
    ap.add_argument('--y', required=True)
    ap.add_argument('--group')
    ap.add_argument('--group-label', default='{}', help='图例格式，{} 换成组值，如 "$I_f$={}A"')
    ap.add_argument('--xlabel')
    ap.add_argument('--ylabel')
    ap.add_argument('--mode', choices=['fit', 'origin', 'poly', 'curve', 'line', 'scatter'], default='fit')
    ap.add_argument('--deg', type=int, default=2)
    ap.add_argument('--mark-peaks', nargs='?', const=0, type=int)
    ap.add_argument('--mark-valleys', nargs='?', const=0, type=int)
    ap.add_argument('--logx', action='store_true')
    ap.add_argument('--logy', action='store_true')
    ap.add_argument('--no-markers', action='store_true')
    ap.add_argument('--extend-to-zero', action='store_true', help='拟合线延长到 x=0（外延法）')
    ap.add_argument('--hline', type=float, action='append', default=[])
    ap.add_argument('--vline', type=float, action='append', default=[])
    ap.add_argument('--out', required=True)
    ap.add_argument('--size', default='5.2,3.6', help='英寸，宽,高')
    ap.add_argument('--macros')
    ap.add_argument('--name')
    ap.add_argument('--digits', type=int, default=4)
    a = ap.parse_args()

    data = load(a.csv, a.x, a.y, a.group)
    w, h = (float(v) for v in a.size.split(','))
    fig, ax = plt.subplots(figsize=(w, h))
    results = []
    many = len(data) > 1
    for i, (g, x, y) in enumerate(data):
        mk = MARKERS[i % len(MARKERS)] if many else '+'
        lab = a.group_label.format(g) if many else '数据点'
        if a.no_markers:
            color = ax.plot([], [])[0].get_color() if many else 'k'
        else:
            pts = ax.plot(x, y, mk, ms=5 if many else 7, mew=1.1, ls='none',
                          mfc='none', color=None if many else 'k', label=lab)[0]
            color = pts.get_color()
        res = {'group': g} if a.group else {}
        res['n'] = len(x)
        if a.mode in ('fit', 'origin'):
            res.update(linfit(x, y, a.mode == 'origin'))
            x0 = 0 if (a.mode == 'origin' or a.extend_to_zero) else x.min()
            xx = np.linspace(min(x0, x.min()), x.max(), 100)
            ax.plot(xx, res['k'] * xx + res['b'], '-', lw=1, color=color,
                    label=None if many else '拟合直线')
            print('%sk = %.6g  b = %.6g  r = %.6f  u(k) = %.3g  u(b) = %.3g  n = %d'
                  % ('[%s] ' % g if g else '', res['k'], res['b'], res['r'], res['u_k'], res['u_b'], res['n']))
        elif a.mode == 'poly':
            c = np.polyfit(x, y, a.deg)
            yfit = np.polyval(c, x)
            ss = ((y - y.mean()) ** 2).sum()
            res['coef'] = [float(v) for v in c]   # 从最高次到常数项
            res['R2'] = float(1 - ((y - yfit) ** 2).sum() / ss) if ss else float('nan')
            xx = np.linspace(x.min(), x.max(), 300)
            ax.plot(xx, np.polyval(c, xx), '-', lw=1, color=color, label=None if many else '%d 次拟合' % a.deg)
            print('%s系数(高→低) = %s  R² = %.6f' % ('[%s] ' % g if g else '',
                                                 ', '.join('%.6g' % v for v in c), res['R2']))
        elif a.mode in ('curve', 'line'):
            if a.mode == 'curve':
                order = np.argsort(x, kind='stable')
                xs, ys = x[order], y[order]
            else:
                xs, ys = x, y
            drawn = False
            if a.mode == 'curve' and len(xs) >= 4 and len(set(xs)) == len(xs) and not a.no_markers:
                try:
                    from scipy.interpolate import make_interp_spline
                    xx = np.linspace(xs.min(), xs.max(), 400)
                    ax.plot(xx, make_interp_spline(xs, ys, k=3)(xx), '-', lw=1, color=color)
                    drawn = True
                except Exception:
                    pass
            if not drawn:
                ax.plot(xs, ys, '-', lw=0.8 if a.no_markers else 1, color=color,
                        label=lab if a.no_markers and many else None)
            for flag, sign, key, off in ((a.mark_peaks, 1, 'peaks', 6), (a.mark_valleys, -1, 'valleys', -12)):
                if flag is None:
                    continue
                idx = extrema(xs, ys, flag, sign)
                for j in idx:
                    ax.annotate('%g' % xs[j], (xs[j], ys[j]), textcoords='offset points', xytext=(0, off),
                                ha='center', fontsize=8)
                res[key + '_x'] = [float(xs[j]) for j in idx]
                res[key + '_y'] = [float(ys[j]) for j in idx]
                print('%s%s：x=%s' % ('[%s] ' % g if g else '', '峰位' if sign > 0 else '谷位', res[key + '_x']))
        res.update(xmin=float(x.min()), xmax=float(x.max()), ymin=float(y.min()), ymax=float(y.max()),
                   x_at_ymax=float(x[int(np.argmax(y))]))
        results.append(res)

    for v in a.hline:
        ax.axhline(v, ls='--', lw=0.7, color='gray')
    for v in a.vline:
        ax.axvline(v, ls='--', lw=0.7, color='gray')
    if a.logx:
        ax.set_xscale('log')
    if a.logy:
        ax.set_yscale('log')
    xl, yl = a.xlabel or a.x, a.ylabel or a.y
    ax.set_xlabel(xl, **label_kw(xl))
    ax.set_ylabel(yl, **label_kw(yl))
    ax.grid(True, ls=':', lw=0.5)
    labels = ax.get_legend_handles_labels()[1]
    if labels and (many or len(labels) > 1):
        prop = ZH if any(has_cjk(t) for t in labels) else {'size': 9}
        if many:   # 多组时图例放到图外右侧，避免压住数据点
            ax.legend(frameon=False, prop=prop, loc='upper left', bbox_to_anchor=(1.01, 1))
        else:
            ax.legend(frameon=False, prop=prop)
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fig.savefig(a.out, facecolor='white', dpi=300)
    record(a.out, [a.csv], script='fit_plot.py')
    print('SAVED', a.out)

    if a.macros and a.mode in ('fit', 'origin'):
        if not a.name:
            raise SystemExit('--macros 需要同时给 --name')
        ms = []
        for i, r in enumerate(results):
            suf = string.ascii_lowercase[i] if many else ''
            for key, mac in (('k', 'K'), ('b', 'B'), ('r', 'R'), ('u_k', 'UK'), ('u_b', 'UB')):
                if key == 'r':     # 相关系数按固定 4 位小数（0.999999 → 1.0000，而不是 1）
                    ms.append((a.name + mac + suf, '%.4f' % r[key]))
                    continue
                d = 2 if key.startswith('u_') else a.digits
                ms.append((a.name + mac + suf, num(r[key], d)))
        write_macros(a.macros, ms, 'fit_plot.py %s %s~%s' % (os.path.basename(a.csv), a.y, a.x), inputs=[a.csv])
        print('已写入 %d 个宏 → %s（%s）' % (len(ms), a.macros, '，'.join(m for m, _ in ms[:5]) + ' …'))
    elif a.macros:
        print('（%s 模式不写宏；需要的数值请从下面 JSON 取，在 analysis.py 里修约后写宏）' % a.mode)
    print(json.dumps(results if many else results[0], ensure_ascii=False))


if __name__ == '__main__':
    main()
