# -*- coding: utf-8 -*-
"""不确定度与有效数字（国内大学物理实验通用规则；以课程讲义为准）。

规则摘要：
  单次测量只算 B 类：u_B = Δ仪/√3（均匀分布）
  多次测量：u_A = s/√n（s 为贝塞尔公式标准偏差），u = √(u_A² + u_B²)
  不确定度保留 1~2 位（首位为 1、2 时留 2 位），只进不舍；测量值末位与不确定度末位对齐，“四舍六入五凑偶”
  结果写成 x = (值 ± u) 单位 (P=0.683)

子命令：
  mean  多次测量：python uncert.py mean 12.01 12.03 11.99 --delta 0.02 --unit mm
  diff  逐差法：  python uncert.py diff 12.2 16.7 21.3 26.1 30.9 36.0 41.0 47.0 52.0 --delta 0.1 --unit V
        相邻间隔数 gap 默认 n//2；结果 = 各差值平均 / gap；
        u_A 来自差值的标准偏差；u_B：每个差值含两次读数，u_B(差)=√2·Δ/√3，再除以 gap
  fmt   只做修约：  python uncert.py fmt 5.2513 0.1049 --unit eV
公共选项：
  --macros results.tex --name W   把结果写成宏：\\W → 5.25(11)，\\WVal → 5.25，\\WU → 0.11，\\WRel → 2.0
                                  正文用 \\SI{\\WVal \\pm \\WU}{\\electronvolt} 或 $(\\WVal\\pm\\WU)$ eV
"""
import argparse
import decimal
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texmacros import write_macros  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def round_u(u):
    """不确定度修约：首位 1、2 留两位，否则一位；只进不舍。返回 (修约后的 u, 小数位数)。"""
    if u <= 0:
        return 0.0, 0
    e = math.floor(math.log10(u))
    first = int(u / 10 ** e)
    keep = 2 if first in (1, 2) else 1
    dec = -(e - keep + 1)
    q = 10 ** (-dec)
    ur = math.ceil(round(u / q, 9)) * q
    # 进位后可能多出一位（例如 0.0299→0.030），再规整一次
    e2 = math.floor(math.log10(ur))
    if e2 > e:
        dec -= 1
    return ur, dec


def round_even(x, dec):
    return decimal.Decimal(repr(x)).quantize(decimal.Decimal(1).scaleb(-dec), rounding=decimal.ROUND_HALF_EVEN)


def rounded(x, u):
    ur, dec = round_u(u)
    xs, us = round_even(x, dec), round_even(ur, dec)
    rel = abs(u / x) * 100 if x else float('nan')
    return xs, us, rel


def fmt(x, u, unit=''):
    xs, us, rel = rounded(x, u)
    return '(%s ± %s) %s (P=0.683)，相对不确定度 %.2g%%' % (xs, us, unit, rel)


def emit(a, x, u):
    print('结果：', fmt(x, u, a.unit))
    xs, us, rel = rounded(x, u)
    print('LaTeX：$(%s \\pm %s)$\\,%s' % (xs, us, a.unit))
    if a.macros:
        if not a.name:
            raise SystemExit('--macros 需要同时给 --name')
        n = a.name
        write_macros(a.macros, [(n + 'Val', str(xs)), (n + 'U', str(us)), (n + 'Rel', '%.2g' % rel)],
                     'uncert.py %s' % a.cmd)
        print('已写入宏 \\%sVal \\%sU \\%sRel → %s' % (n, n, n, a.macros))


def cmd_mean(a):
    v = a.values
    n = len(v)
    m = statistics.mean(v)
    s = statistics.stdev(v) if n > 1 else 0.0
    ua = s / math.sqrt(n) if n > 1 else 0.0
    ub = a.delta / math.sqrt(3) if a.delta else 0.0
    u = math.hypot(ua, ub)
    print('n=%d  平均=%.6g  s=%.4g  u_A=s/√n=%.4g  u_B=Δ/√3=%.4g  u=√(u_A²+u_B²)=%.4g' % (n, m, s, ua, ub, u))
    emit(a, m, u)


def cmd_diff(a):
    v = a.values
    n = len(v)
    gap = a.gap or n // 2
    d = [v[i + gap] - v[i] for i in range(n - gap)]
    m = len(d)
    step = sum(d) / m / gap
    print('逐差：' + '，'.join('(x%d-x%d)=%.4g' % (i + gap + 1, i + 1, x) for i, x in enumerate(d)))
    print('结果 = Σ差 / (%d×%d) = %.6g / %d = %.6g' % (m, gap, sum(d), m * gap, step))
    sd = statistics.stdev(d) if m > 1 else 0.0
    ua = sd / math.sqrt(m) / gap if m > 1 else 0.0
    ub = (math.sqrt(2) * a.delta / math.sqrt(3) / gap) if a.delta else 0.0
    u = math.hypot(ua, ub)
    print('差值标准偏差 s=%.4g；u_A=s/(√%d·%d)=%.4g；u_B=√2·Δ/(√3·%d)=%.4g；u=%.4g' % (sd, m, gap, ua, gap, ub, u))
    if n - gap > gap:
        print('注意：差值有重叠（%d 个差值并不独立）时 u_A 只是估计，报告里写清用法。' % m)
    emit(a, step, u)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')
    sub.required = True

    def common(s):
        s.add_argument('--unit', default='')
        s.add_argument('--macros', help='写入宏的 .tex 文件')
        s.add_argument('--name', help='宏名前缀（只用英文字母）')

    for name in ('mean', 'diff'):
        s = sub.add_parser(name)
        s.add_argument('values', type=float, nargs='+')
        s.add_argument('--delta', type=float, default=0.0, help='仪器误差限 Δ仪')
        common(s)
        if name == 'diff':
            s.add_argument('--gap', type=int, help='逐差间隔，默认 n//2')
        s.set_defaults(fn=cmd_mean if name == 'mean' else cmd_diff)
    s = sub.add_parser('fmt')
    s.add_argument('x', type=float)
    s.add_argument('u', type=float)
    common(s)
    s.set_defaults(fn=lambda a: emit(a, a.x, a.u))
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
