# -*- coding: utf-8 -*-
"""回归测试：把每个示例复制到临时目录，在那里跑 analysis.py → build.py，**不改动仓库里的任何文件**。

  python tests/run_examples.py            # 跑全部示例
  python tests/run_examples.py --keep     # 保留临时目录，便于查看 preview/contact.png
退出码：
  0 全部通过
  1 代码/示例出错（analysis.py 或 build.py 失败，或仓库文件被改动）
  3 环境依赖缺失（缺 Python 包或 LaTeX 编译器）——不是代码问题，先按提示安装
"""
import argparse
import hashlib
import importlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(ROOT, 'examples')
BUILD = os.path.join(ROOT, 'skills', 'lab-report-tex', 'scripts', 'build.py')
SKIP = {'build', 'preview', '__pycache__'}
EXIT_OK, EXIT_FAIL, EXIT_ENV = 0, 1, 3


def missing_deps():
    miss = []
    for mod, pip in (('numpy', 'numpy'), ('matplotlib', 'matplotlib'), ('PIL', 'pillow')):
        try:
            importlib.import_module(mod)
        except ImportError:
            miss.append('Python 包 %s（pip install %s）' % (mod, pip))
    if not (shutil.which('xelatex') or shutil.which('tectonic')):
        miss.append('LaTeX 编译器 xelatex 或 tectonic（见 skills/lab-report-tex/scripts/check_env.py）')
    return miss


def fixture_hashes(root=EXAMPLES):
    """examples/ 下所有受版本控制的文件（跳过 build/ preview/）的 SHA-256。"""
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            p = os.path.join(base, f)
            with open(p, 'rb') as fh:
                out[os.path.relpath(p, root)] = hashlib.sha256(fh.read()).hexdigest()
    return out


def require_of(d):
    p = os.path.join(d, 'requirements.md')
    if os.path.exists(p):
        m = re.search(r'--require "([^"]+)"', io.open(p, encoding='utf-8').read())
        if m:
            return m.group(1)
    return None


def run_one(src, workroot):
    """在 workroot 下复制示例并运行，返回 (是否通过, 输出摘要, 工作目录)。"""
    name = os.path.basename(src)
    work = os.path.join(workroot, name)
    shutil.copytree(src, work, ignore=shutil.ignore_patterns(*SKIP))
    env = os.environ.copy()
    env['LAB_SKILL_DIR'] = os.path.join(ROOT, 'skills', 'lab-report-tex')
    steps = []
    if os.path.exists(os.path.join(work, 'analysis.py')):
        steps.append([sys.executable, os.path.join(work, 'analysis.py')])
    cmd = [sys.executable, BUILD, os.path.join(work, 'report.tex'), '--thumbs', os.path.join(work, 'preview'),
           '--outdir', os.path.join(work, 'out')]
    req = require_of(work)
    if req:
        cmd += ['--require', req]
    steps.append(cmd)
    for c in steps:
        p = subprocess.run(c, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = p.stdout.decode('utf-8', 'replace')
        if p.returncode:
            return False, '%s 退出码 %d\n%s' % (os.path.basename(c[1]), p.returncode,
                                              '\n'.join('    ' + ln for ln in text.splitlines()[-20:])), work
    pdfs = [f for f in os.listdir(os.path.join(work, 'out')) if f.endswith('.pdf')]
    if not pdfs:
        return False, 'build.py 返回 0 但正式输出目录没有 PDF', work
    pages = len([f for f in os.listdir(os.path.join(work, 'preview')) if re.match(r'p\d+\.png', f)])
    return True, '%s，%d 页' % (pdfs[0], pages), work


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--keep', action='store_true', help='保留临时目录')
    a = ap.parse_args()

    miss = missing_deps()
    if miss:
        print('【环境依赖缺失】以下依赖没有安装，这不是代码错误：')
        for m in miss:
            print('  -', m)
        sys.exit(EXIT_ENV)

    before = fixture_hashes()
    tmp = tempfile.mkdtemp(prefix='lrt-examples-')
    failed = []
    try:
        for name in sorted(os.listdir(EXAMPLES)):
            src = os.path.join(EXAMPLES, name)
            if not os.path.exists(os.path.join(src, 'report.tex')):
                continue
            print('=== %s' % name)
            ok, msg, work = run_one(src, tmp)
            print('  %s %s' % ('✔' if ok else '✘', msg))
            if ok and a.keep:
                print('    总览图：%s' % os.path.join(work, 'preview', 'contact.png'))
            if not ok:
                failed.append(name)
    finally:
        if a.keep:
            print('临时目录已保留：%s' % tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    after = fixture_hashes()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    if changed:
        print('✘ 测试改动了仓库里的示例文件（不应发生）：')
        for k in changed:
            print('   ', k)
        failed.append('fixtures')
    print('\n%s' % ('全部通过（仓库文件未被改动）' if not failed else '失败：' + ', '.join(failed)))
    sys.exit(EXIT_FAIL if failed else EXIT_OK)


if __name__ == '__main__':
    main()
