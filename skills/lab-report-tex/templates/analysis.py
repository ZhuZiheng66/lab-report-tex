# -*- coding: utf-8 -*-
"""本次实验的计算脚本骨架：原始数据 CSV → 派生 CSV → 表格 / 图 / 结果宏。

复制到工作目录后改 TODO 处。运行：python analysis.py
完整实例见仓库 examples/work-function/analysis.py。
原则：所有中间量都打印出来；正文里的数字只从 results.tex 的宏和 tab/*.tex 来。
"""
import csv
import io
import json
import os
import subprocess
import sys

SKILL = os.environ.get('LAB_SKILL_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '_skill')
SK = os.path.join(SKILL, 'scripts')   # TODO：改成 skill 的实际路径，或设置环境变量 LAB_SKILL_DIR
sys.path.insert(0, SK)
from texmacros import num, write_macros  # noqa: E402,F401
from uncert import rounded  # noqa: E402,F401

os.chdir(os.path.dirname(os.path.abspath(__file__)))
MAC = 'results.tex'


def read(path):
    with io.open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write(path, header, rows):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')    # 固定 LF，重跑结果才逐字节一致
        w.writerow(header)
        w.writerows(rows)


def tool(script, *args):
    """调用 skill 脚本，打印输出并返回（fit_plot.py 最后一行是 JSON 结果）。"""
    out = subprocess.run([sys.executable, os.path.join(SK, script)] + list(args),
                         stdout=subprocess.PIPE, check=True).stdout.decode('utf-8')
    print(out.rstrip())
    return out


# TODO 1：读原始数据（照片转写、用户确认过的 CSV，数值保持原样字符串）
# raw = read('data/raw.csv')

# TODO 2：数据记录表
# tool('csv2tex.py', 'data/raw.csv', '--caption', '……', '--label', 'tab:raw', '--out', 'tab/t1.tex')

# TODO 3：换算列写成派生 CSV（保留合适的小数位），再作图拟合
# write('data/derived.csv', ['x', 'y'], [[...], ...])
# out = tool('fit_plot.py', 'data/derived.csv', '--x', 'x', '--y', 'y',
#            '--xlabel', '$x$/单位', '--ylabel', '$y$/单位', '--out', 'fig/fig1.pdf',
#            '--macros', MAC, '--name', 'Fit')
# fit = json.loads(out.strip().splitlines()[-1])

# TODO 4：由拟合结果算最终量和不确定度，修约后写宏
# val, u = ..., ...
# v, uu, rel = rounded(val, u)
# write_macros(MAC, [('XVal', str(v)), ('XU', str(uu)), ('XRel', '%.2g' % rel)], source='analysis.py',
#              inputs=['data/raw.csv'])     # inputs 会以 SHA-256 记进 results.meta.json
# 表头/表题写了 LaTeX（$I_\mathrm{f}$/A）时，csv2tex 要显式加 '--raw-latex'（只用于自己写的可信表头）
