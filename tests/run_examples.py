# -*- coding: utf-8 -*-
"""回归测试：把每个示例复制到临时目录，在那里跑 analysis.py → build.py，**不改动仓库里的任何文件**。

  python tests/run_examples.py            # 跑全部示例
  python tests/run_examples.py --keep     # 保留临时目录，便于查看 preview/contact.png
退出码：
  0 全部通过
  1 代码/示例出错（analysis.py、build.py、build_docx.py 失败，或仓库文件被改动）
  3 环境依赖缺失（缺 numpy/matplotlib/pillow）——不是代码问题，先按提示安装
没有 LaTeX 时只跑 Word 版（build_docx.py），没有 python-docx 时只跑 PDF 版。
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
BUILD_DOCX = os.path.join(ROOT, 'skills', 'lab-report-tex', 'scripts', 'build_docx.py')
SKIP = {'build', 'preview', '__pycache__'}
EXIT_OK, EXIT_FAIL, EXIT_ENV = 0, 1, 3


def missing_deps():
    """(必需但缺的, 可选但缺的)。Python 包是必需的；LaTeX 可选——没有时只跑 Word 版。"""
    need, optional = [], []
    for mod, pip in (('numpy', 'numpy'), ('matplotlib', 'matplotlib'), ('PIL', 'pillow')):
        try:
            importlib.import_module(mod)
        except ImportError:
            need.append('Python 包 %s（pip install %s）' % (mod, pip))
    try:
        importlib.import_module('docx')
    except ImportError:
        optional.append('python-docx（Word 版；pip install python-docx）')
    if not (shutil.which('xelatex') or shutil.which('tectonic')):
        optional.append('LaTeX 编译器 xelatex 或 tectonic（PDF 版；见 scripts/check_env.py）')
    return need, optional


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


def run_steps(steps, work, env):
    for c in steps:
        p = subprocess.run(c, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = p.stdout.decode('utf-8', 'replace')
        if p.returncode:
            return '%s 退出码 %d\n%s' % (os.path.basename(c[1]), p.returncode,
                                       '\n'.join('    ' + ln for ln in text.splitlines()[-20:]))
    return None


def run_one(src, workroot, latex=True, word=True):
    """在 workroot 下复制示例并运行，返回 (是否通过, 输出摘要, 工作目录)。"""
    name = os.path.basename(src)
    work = os.path.join(workroot, name)
    shutil.copytree(src, work, ignore=shutil.ignore_patterns(*SKIP))
    env = os.environ.copy()
    env['LAB_SKILL_DIR'] = os.path.join(ROOT, 'skills', 'lab-report-tex')
    req = require_of(work)
    msgs = []
    if os.path.exists(os.path.join(work, 'analysis.py')):
        err = run_steps([[sys.executable, os.path.join(work, 'analysis.py')]], work, env)
        if err:
            return False, err, work
    if latex and os.path.exists(os.path.join(work, 'report.tex')):
        cmd = [sys.executable, BUILD, os.path.join(work, 'report.tex'), '--thumbs', os.path.join(work, 'preview'),
               '--outdir', os.path.join(work, 'out')] + (['--require', req] if req else [])
        err = run_steps([cmd], work, env)
        if err:
            return False, err, work
        pdfs = [f for f in os.listdir(os.path.join(work, 'out')) if f.endswith('.pdf')]
        if not pdfs:
            return False, 'build.py 返回 0 但正式输出目录没有 PDF', work
        pages = len([f for f in os.listdir(os.path.join(work, 'preview')) if re.match(r'p\d+\.png', f)])
        msgs.append('PDF 版 %s，%d 页' % (pdfs[0], pages))
    elif os.path.exists(os.path.join(work, 'report.tex')):
        msgs.append('PDF 版跳过（没有 LaTeX）')
    if word and os.path.exists(os.path.join(work, 'report.md')):
        # 这个示例的 Word 版已经在 PDF 版之后跑过 build.py，数据状态会变成 used_in_report，同样合格
        cmd = [sys.executable, BUILD_DOCX, os.path.join(work, 'report.md'), '--outdir', os.path.join(work, 'out_docx')] \
            + (['--require', req] if req else [])
        err = run_steps([cmd], work, env)
        if err:
            return False, err, work
        docs = [f for f in os.listdir(os.path.join(work, 'out_docx')) if f.endswith('.docx')]
        if not docs:
            return False, 'build_docx.py 返回 0 但正式输出目录没有 .docx', work
        msgs.append('Word 版 %s' % docs[0])
    return True, '；'.join(msgs) or '无可运行的输出', work


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--keep', action='store_true', help='保留临时目录')
    a = ap.parse_args()

    need, optional = missing_deps()
    if need:
        print('【环境依赖缺失】以下依赖没有安装，这不是代码错误：')
        for m in need:
            print('  -', m)
        sys.exit(EXIT_ENV)
    for m in optional:
        print('（可选依赖没装，相应部分跳过：%s）' % m)
    latex = not any('LaTeX' in m for m in optional)
    word = not any('python-docx' in m for m in optional)

    before = fixture_hashes()
    tmp = tempfile.mkdtemp(prefix='lrt-examples-')
    failed = []
    try:
        for name in sorted(os.listdir(EXAMPLES)):
            src = os.path.join(EXAMPLES, name)
            if not (os.path.exists(os.path.join(src, 'report.tex')) or os.path.exists(os.path.join(src, 'report.md'))):
                continue
            print('=== %s' % name)
            ok, msg, work = run_one(src, tmp, latex, word)
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
