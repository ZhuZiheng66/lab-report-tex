# -*- coding: utf-8 -*-
"""测试公用：路径、运行脚本、环境探测。"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'skills', 'lab-report-tex', 'scripts')
sys.path.insert(0, SCRIPTS)

HAS_LATEX = bool(shutil.which('xelatex') or shutil.which('tectonic'))


def has_module(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def run(args, cwd=None, env=None):
    """运行 python 脚本，返回 (退出码, 输出文本)。"""
    e = os.environ.copy()
    e.update(env or {})
    p = subprocess.run([sys.executable] + args, cwd=cwd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')
