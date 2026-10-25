# -*- coding: utf-8 -*-
"""可追溯元数据：每次生成表、图、结果宏时，把“由什么输入、哪个脚本、什么参数、何时”记进 results.meta.json。

只记录输入文件的路径和 SHA-256，不复制原始数据内容。
文件位置：当前工作目录（报告目录）下的 results.meta.json；可用环境变量 LAB_META 指定别的路径。

格式：
{
  "schema": 1,
  "entries": {
    "tab/t_ia.tex": [ {"script": "csv2tex.py", "argv": [...], "inputs": [{"path": "data/t_ia.csv", "sha256": "…"}],
                        "skill_version": "1.1.0", "git_commit": "a499627…", "time": "2026-10-25T12:00:00+08:00"} ],
    ...
  }
}
同一输出、同一脚本、同一参数再次生成时覆盖旧记录，不会无限增长。
"""
import datetime
import hashlib
import io
import json
import os
import subprocess

SKILL_VERSION = '1.1.0'
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


_git = None


def _git_info():
    """(commit, dirty)：skill 所在 git 仓库的 commit，以及脚本目录是否有未提交改动。
    装到 ~/.claude/skills 之类不是仓库的地方时为 (None, None)。"""
    global _git
    if _git is None:
        try:
            out = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=SCRIPTS_DIR, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, timeout=10)
            commit = out.stdout.decode().strip() if out.returncode == 0 else None
            dirty = None
            if commit:
                st = subprocess.run(['git', 'status', '--porcelain', '--', '.'], cwd=SCRIPTS_DIR,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
                dirty = bool(st.stdout.strip())
            _git = (commit, dirty)
        except Exception:
            _git = (None, None)
    return _git


def git_commit():
    return _git_info()[0]


def meta_path():
    return os.environ.get('LAB_META') or os.path.join(os.getcwd(), 'results.meta.json')


def _rel(p):
    p = os.path.abspath(p)
    base = os.path.dirname(os.path.abspath(meta_path()))
    try:
        r = os.path.relpath(p, base)
    except ValueError:          # Windows 上不同盘符
        return p.replace(os.sep, '/')
    return r.replace(os.sep, '/')


def record(output, inputs=(), script=None, argv=None, note=None):
    """记录一条生成信息。inputs 是文件路径列表（不存在的会标 missing）。失败时静默——元数据不能阻断主流程。"""
    try:
        import sys
        path = meta_path()
        data = {'schema': 1, 'entries': {}}
        if os.path.exists(path):
            with io.open(path, encoding='utf-8') as f:
                data = json.load(f)
        ins = []
        for p in inputs or ():
            if p and os.path.isfile(p):
                ins.append({'path': _rel(p), 'sha256': sha256(p)})
            elif p:
                ins.append({'path': _rel(p), 'sha256': None, 'missing': True})
        rec = {
            'script': script or os.path.basename(sys.argv[0]),
            'argv': list(argv if argv is not None else sys.argv[1:]),
            'inputs': ins,
            'skill_version': SKILL_VERSION,
            'git_commit': git_commit(),
            'git_dirty': _git_info()[1],      # True = 用未提交的脚本改动生成的
            'time': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        }
        if note:
            rec['note'] = note
        key = _rel(output)
        lst = [r for r in data.setdefault('entries', {}).get(key, [])
               if not (r.get('script') == rec['script'] and r.get('argv') == rec['argv']
                       and r.get('note') == rec.get('note'))]
        lst.append(rec)
        data['entries'][key] = lst
        with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')
    except Exception as e:  # pragma: no cover
        print('（未能写入 results.meta.json：%s）' % e)
