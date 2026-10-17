# -*- coding: utf-8 -*-
"""金属电子逸出功的测定：从原始数据 CSV 一路算到 LaTeX 宏、表格和图。

  python analysis.py        # 生成 data/*.csv、tab/*.tex、fig/*.pdf、results.tex
  python ../../skills/lab-report-tex/scripts/build.py report.tex --thumbs preview

正文里所有数字都来自 results.tex 的宏或 tab/ 下自动生成的表格，改了原始数据只需重跑这两条命令。
"""
import csv
import io
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, '..', '..', 'skills', 'lab-report-tex', 'scripts')
sys.path.insert(0, SK)
from texmacros import num, write_macros  # noqa: E402
from uncert import rounded  # noqa: E402

os.chdir(HERE)
MAC = 'results.tex'
KB_LN10_E = 1.380649e-23 * math.log(10) / 1.602176634e-19   # k_B·ln10/e，单位 V/K


def read(path):
    with io.open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write(path, header, rows):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def tool(script, *args):
    out = subprocess.run([sys.executable, os.path.join(SK, script)] + list(args),
                         stdout=subprocess.PIPE, check=True).stdout.decode('utf-8')
    print(out.rstrip())
    return out


raw = read('data/raw.csv')                       # 列：If/A, Ua/V, Ia/uA（照片逐格转写，原样保留）
temp = {r['If/A']: r['T/10^3K'] for r in read('data/t1_ift.csv')}
ifs = sorted({r['If/A'] for r in raw}, key=float)
uas = sorted({r['Ua/V'] for r in raw}, key=float)
ia = {(r['If/A'], r['Ua/V']): r['Ia/uA'] for r in raw}

# 表：原始阳极电流（宽表，数值原样）
write('data/t_ia.csv', ['$I_\\mathrm{f}$/A'] + uas, [[f] + [ia[f, u] for u in uas] for f in ifs])
tool('csv2tex.py', 'data/t_ia.csv', '--caption', '不同灯丝电流和阳极电压$U_a$/V下的阳极电流$I_a$/μA',
     '--label', 'tab:ia', '--out', 'tab/t_ia.tex')
write('data/t_ift.csv', ['$I_\\mathrm{f}$/A', '$T$/$10^3$K'], [[f, temp[f]] for f in ifs])
tool('csv2tex.py', 'data/t_ift.csv', '--caption', '灯丝电流与灯丝温度的对应关系', '--label', 'tab:ift',
     '--out', 'tab/t_ift.tex')

# 换算：√Ua、lgIa（长表，用于分组拟合；宽表用于报告）
long_rows = [[f, '%.4f' % math.sqrt(float(u)), '%.4f' % math.log10(float(ia[f, u]))] for f in ifs for u in uas]
write('data/lgia_long.csv', ['If', 'sqrtUa', 'lgIa'], long_rows)
write('data/t_lgia.csv', ['$I_\\mathrm{f}$/A'] + ['%g' % math.sqrt(float(u)) for u in uas],
      [[f] + ['%.4f' % math.log10(float(ia[f, u])) for u in uas] for f in ifs])
tool('csv2tex.py', 'data/t_lgia.csv', '--caption', '$\\lg(I_a/\\mu\\mathrm{A})$ 与 $\\sqrt{U_a/\\mathrm{V}}$（首行）',
     '--label', 'tab:lgia', '--out', 'tab/t_lgia.tex')

# 外延法：每个灯丝电流各拟合一条 lgIa-√Ua 直线，截距即 lgI0
out = tool('fit_plot.py', 'data/lgia_long.csv', '--x', 'sqrtUa', '--y', 'lgIa', '--group', 'If',
           '--group-label', '$I_f$={}A', '--xlabel', '$\\sqrt{U_a/\\mathrm{V}}$',
           '--ylabel', '$\\lg(I_a/\\mu\\mathrm{A})$', '--out', 'fig/lgia.pdf', '--size', '5.6,3.8',
           '--macros', MAC, '--name', 'Ext')
ext = json.loads(out.strip().splitlines()[-1])
rich = []
for f, r in zip(ifs, ext):
    T = float(temp[f]) * 1e3
    lgI0 = r['b']
    rich.append(dict(If=f, T=temp[f], k='%.4f' % r['k'], lgI0='%.4f' % lgI0, r='%.4f' % r['r'],
                     I0='%.3f' % 10 ** lgI0, y='%.4f' % (lgI0 - 2 * math.log10(T)), x='%.4f' % (1e4 / T)))
write('data/t_ext.csv', ['$I_\\mathrm{f}$/A', '斜率', '$\\lg(I_0/\\mu\\mathrm{A})$', '$r$', '$I_0$/μA'],
      [[d['If'], d['k'], d['lgI0'], d['r'], d['I0']] for d in rich])
tool('csv2tex.py', 'data/t_ext.csv', '--caption', '外延法拟合结果（$\\lg I_a=k\\sqrt{U_a}+\\lg I_0$）',
     '--label', 'tab:ext', '--out', 'tab/t_ext.tex')
write('data/rich.csv', ['$I_\\mathrm{f}$/A', '$T$/$10^3$K', '$\\lg(I_0/\\mu\\mathrm{A})$',
                        '$\\lg(I_0/T^2)$', '$(1/T)$/$10^{-4}$K$^{-1}$'],
      [[d['If'], d['T'], d['lgI0'], d['y'], d['x']] for d in rich])
tool('csv2tex.py', 'data/rich.csv', '--caption', '不同灯丝温度下的 $\\lg(I_0/T^2)$ 与 $1/T$',
     '--label', 'tab:rich', '--out', 'tab/t_rich.tex')
write('data/rich_fit.csv', ['x', 'y'], [[d['x'], d['y']] for d in rich])

# 理查逊直线：lg(I0/T²) - 1/T，横轴单位 10⁻⁴ K⁻¹，所以斜率要 ×10⁴ 换成 K
out = tool('fit_plot.py', 'data/rich_fit.csv', '--x', 'x', '--y', 'y',
           '--xlabel', '$(1/T)/10^{-4}\\mathrm{K}^{-1}$', '--ylabel', '$\\lg(I_0/T^2)$',
           '--out', 'fig/rich.pdf', '--macros', MAC, '--name', 'Rich')
fit = json.loads(out.strip().splitlines()[-1])
k, uk = fit['k'] * 1e4, fit['u_k'] * 1e4
V, uV = -k * KB_LN10_E, uk * KB_LN10_E
W0 = 4.54
Ws, uWs, rel = rounded(V, uV)
err = abs(float(Ws) - W0) / W0 * 100
print('k = %.4g K, u(k) = %.3g K → V = %.4f V, u(V) = %.4f V；W = (%s ± %s) eV，E = %.1f%%' % (k, uk, V, uV, Ws, uWs, err))
write_macros(MAC, [
    ('RichKK', num(k, 4)), ('RichUKK', num(uk, 2)), ('KbLnE', num(KB_LN10_E, 4)),
    ('Vraw', '%.3f' % V), ('uVraw', '%.3f' % uV),
    ('WVal', str(Ws)), ('WU', str(uWs)), ('WRel', '%.1f' % rel), ('WZero', '%.2f' % W0), ('WErr', '%.1f' % err),
    ('IzeroMin', rich[0]['I0']), ('IzeroMax', rich[-1]['I0']),
    ('ExtRmin', '%.4f' % ext[0]['r']), ('ExtRmax', '%.4f' % ext[-1]['r']),
], 'analysis.py')

# 原始数据照片页：仓库里不放真实手写照片，这里生成一张占位图演示排版
os.makedirs('raw', exist_ok=True)
if not os.path.exists('raw/raw1.jpg'):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (1654, 2339), (245, 245, 245))
    d = ImageDraw.Draw(im)
    d.rectangle([60, 60, 1594, 2279], outline=(160, 160, 160), width=6)
    d.line([60, 60, 1594, 2279], fill=(200, 200, 200), width=4)
    d.line([1594, 60, 60, 2279], fill=(200, 200, 200), width=4)
    im.save('raw/raw1.jpg', quality=85)
print('完成：results.tex、tab/*.tex、fig/*.pdf')
