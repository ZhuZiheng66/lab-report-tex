# -*- coding: utf-8 -*-
"""回归测试：重跑所有示例（analysis.py → build.py --require），任何一个失败就返回非 0。

  python tests/run_examples.py
改了 labreport.cls 或 scripts/ 下任何脚本后都跑一遍，再看各示例 preview/contact.png。
"""
import io
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'skills', 'lab-report-tex', 'scripts', 'build.py')
DEFAULT_REQUIRE = '实验目的,实验原理,实验仪器,实验内容与步骤,数据记录和处理,结果陈述,思考题,指导教师批阅意见,成绩评定,原始数据'


def require_of(d):
    """示例目录里有 requirements.md 就从中取 --require 的值。"""
    p = os.path.join(d, 'requirements.md')
    if os.path.exists(p):
        m = re.search(r'--require "([^"]+)"', io.open(p, encoding='utf-8').read())
        if m:
            return m.group(1)
    return DEFAULT_REQUIRE


def main():
    failed = []
    ex_root = os.path.join(ROOT, 'examples')
    for name in sorted(os.listdir(ex_root)):
        d = os.path.join(ex_root, name)
        if not os.path.exists(os.path.join(d, 'report.tex')):
            continue
        print('=== %s' % name)
        steps = []
        if os.path.exists(os.path.join(d, 'analysis.py')):
            steps.append([sys.executable, 'analysis.py'])
        steps.append([sys.executable, BUILD, 'report.tex', '--thumbs', 'preview', '--require', require_of(d)])
        for cmd in steps:
            p = subprocess.run(cmd, cwd=d, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = p.stdout.decode('utf-8', 'replace')
            if p.returncode:
                print('  ✘ %s（退出码 %d）' % (os.path.basename(cmd[1]), p.returncode))
                print('\n'.join('    ' + ln for ln in out.splitlines()[-15:]))
                failed.append(name)
                break
        else:
            pages = len([f for f in os.listdir(os.path.join(d, 'preview')) if re.match(r'p\d+\.png', f)])
            print('  ✔ 通过，%d 页' % pages)
    print('\n%s' % ('全部通过' if not failed else '失败：' + ', '.join(failed)))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
