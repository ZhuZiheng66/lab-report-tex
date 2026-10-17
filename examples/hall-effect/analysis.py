# -*- coding: utf-8 -*-
"""霍尔效应及其应用：对称测量法 → VH；两条输出特性直线；螺线管轴向 B-x 分布；中心点 B 的不确定度。

  python analysis.py
  python ../../skills/lab-report-tex/scripts/build.py report.tex --thumbs preview --require "<见 requirements.md>"
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
KH = 177.0      # mV/(mA·T)，原始记录表 3 表头
IS_X = 3.00     # mA，B-x 测量时的工作电流


def read(path):
    with io.open(path, encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def write(path, rows):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(rows)


def tool(script, *args):
    out = subprocess.run([sys.executable, os.path.join(SK, script)] + list(args),
                         stdout=subprocess.PIPE, check=True).stdout.decode('utf-8')
    print(out.rstrip())
    return out


def vh(v1, v2, v3, v4):
    return (float(v1) - float(v2) + float(v3) - float(v4)) / 4


VHEAD = ['$V_1$/mV', '$V_2$/mV', '$V_3$/mV', '$V_4$/mV', '$V_H$/mV']
tables = {}
for key, src, head, cap in (
        ('is', 'data/raw_is.csv', '$I_s$/mA', '$V_H$-$I_s$ 关系测量数据（$I_m=0.300$\\,A）'),
        ('im', 'data/raw_im.csv', '$I_m$/A', '$V_H$-$I_m$ 关系测量数据（$I_s=3.00$\\,mA）')):
    raw = read(src)[1:]
    rows = [r + ['%.3f' % vh(*r[1:5])] for r in raw]
    tables[key] = rows
    write('data/t_%s.csv' % key, [[head] + VHEAD] + rows)
    tool('csv2tex.py', 'data/t_%s.csv' % key, '--caption', cap, '--label', 'tab:' + key, '--out', 'tab/t_%s.tex' % key)
    write('data/fit_%s.csv' % key, [['x', 'y']] + [[r[0], r[5]] for r in rows])

raw = read('data/raw_x.csv')[1:]
xrows = []
for r in raw:
    v = vh(*r[1:5])
    xrows.append(r + ['%.3f' % v, '%.3f' % (v / (KH * IS_X) * 1e3)])
write('data/t_x.csv', [['$X$/mm'] + VHEAD + ['$B$/mT']] + xrows)
tool('csv2tex.py', 'data/t_x.csv', '--caption',
     '螺线管轴向磁场分布（$I_s=3.00$\\,mA，$I_m=0.300$\\,A，$K_H=177$\\,mV/(mA$\\cdot$T)）',
     '--label', 'tab:x', '--out', 'tab/t_x.tex')
write('data/fit_x.csv', [['x', 'B']] + [[r[0], r[6]] for r in xrows])

# 图与拟合
tool('fit_plot.py', 'data/fit_is.csv', '--x', 'x', '--y', 'y', '--xlabel', '$I_s$/mA', '--ylabel', '$V_H$/mV',
     '--out', 'fig/vh_is.pdf', '--macros', MAC, '--name', 'FitIs')
tool('fit_plot.py', 'data/fit_im.csv', '--x', 'x', '--y', 'y', '--xlabel', '$I_m$/A', '--ylabel', '$V_H$/mV',
     '--out', 'fig/vh_im.pdf', '--macros', MAC, '--name', 'FitIm')
out = tool('fit_plot.py', 'data/fit_x.csv', '--x', 'x', '--y', 'B', '--mode', 'curve',
           '--xlabel', '$X$/mm', '--ylabel', '$B$/mT', '--out', 'fig/b_x.pdf', '--size', '5.6,3.4')
dist = json.loads(out.strip().splitlines()[-1])

# 中心点（B 最大处）及其不确定度：V1~V4 单次测量，只计 B 类
imax = max(range(len(xrows)), key=lambda i: float(xrows[i][6]))
c = xrows[imax]
V = float(c[5])
d_v = 0.005 * V + 0.01                     # 数字毫伏表：0.5%×读数 + 1 个字（按说明书估计）
u_vh = math.sqrt(4 * (d_v / math.sqrt(3)) ** 2) / 4
rel_vh = u_vh / V
rel_kh = 0.02 / math.sqrt(3)               # KH 标称误差 ±2%，均匀分布
d_is = 0.005 * IS_X + 0.01                 # 工作电流：0.5%×读数 + 1 个字
rel_is = d_is / math.sqrt(3) / IS_X
rel_b = math.sqrt(rel_vh ** 2 + rel_kh ** 2 + rel_is ** 2)
B = V / (KH * IS_X) * 1e3
Bs, uBs, relB = rounded(B, B * rel_b)
print('中心 X=%s mm：VH=%.3f mV，u(VH)=%.4f mV；u(B)/B=√(%.4f²+%.4f²+%.4f²)=%.4f → B=(%s±%s) mT'
      % (c[0], V, u_vh, rel_vh, rel_kh, rel_is, rel_b, Bs, uBs))

ends = (float(xrows[0][6]), float(xrows[-1][6]))
write_macros(MAC, [
    ('KH', '%g' % KH), ('XC', c[0]), ('VHC', c[5]), ('DV', '%.3f' % d_v), ('UVH', '%.3f' % u_vh),
    ('RelVH', '%.1f' % (rel_vh * 100)), ('RelKH', '%.1f' % (rel_kh * 100)), ('RelIs', '%.1f' % (rel_is * 100)),
    ('RelB', '%.1f' % (rel_b * 100)), ('BVal', str(Bs)), ('BU', str(uBs)),
    ('BLeft', xrows[0][6]), ('BRight', xrows[-1][6]), ('XLeft', xrows[0][0]), ('XRight', xrows[-1][0]),
    ('EndRatio', '%.1f' % (max(ends) / min(ends))),
    # 计算示例用的原始读数
    ('ExIs', tables['is'][-1][0]), ('ExVa', tables['is'][-1][1]), ('ExVb', tables['is'][-1][2]),
    ('ExVc', tables['is'][-1][3]), ('ExVd', tables['is'][-1][4]), ('ExVH', tables['is'][-1][5]),
    ('ExSum', '%.2f' % (4 * float(tables['is'][-1][5]))),
], 'analysis.py')

os.makedirs('raw', exist_ok=True)
if not os.path.exists('raw/raw1.jpg'):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (1654, 2339), (245, 245, 245))
    d = ImageDraw.Draw(im)
    d.rectangle([60, 60, 1594, 2279], outline=(160, 160, 160), width=6)
    d.line([60, 60, 1594, 2279], fill=(200, 200, 200), width=4)
    d.line([1594, 60, 60, 2279], fill=(200, 200, 200), width=4)
    im.save('raw/raw1.jpg', quality=85)
print('完成')
