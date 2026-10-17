# -*- coding: utf-8 -*-
"""把 skill 安装到各个 Agent 的技能目录，或打包成 zip 供上传。

  python install.py                    # 自动：装到本机已存在的所有 Agent 技能目录
  python install.py --target claude    # 只装 Claude Code
  python install.py --target codex     # 只装 Codex CLI
  python install.py --target doubao    # 豆包工作（~/DoubaoWork/skills）
  python install.py --target workbuddy # WorkBuddy（~/.workbuddy/skills）
  python install.py --dest D:/my/skills   # 装到任意目录
  python install.py --zip              # 生成 dist/lab-report-tex.zip（WorkBuddy、豆包等平台上传用）
  python install.py --uninstall        # 从上述目录删除
"""
import argparse
import os
import shutil
import sys
import zipfile

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

NAME = 'lab-report-tex'
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'skills', NAME)
HOME = os.path.expanduser('~')
TARGETS = {
    'claude': os.path.join(HOME, '.claude', 'skills'),
    'codex': os.path.join(HOME, '.codex', 'skills'),
    'agents': os.path.join(HOME, '.agents', 'skills'),
    'doubao': os.path.join(HOME, 'DoubaoWork', 'skills'),       # 豆包工作（桌面版）
    'workbuddy': os.path.join(HOME, '.workbuddy', 'skills'),    # WorkBuddy
}
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', 'build', 'preview')


def install(dest_root):
    dst = os.path.join(dest_root, NAME)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dest_root, exist_ok=True)
    shutil.copytree(SRC, dst, ignore=IGNORE)
    print('✔ 已安装：', dst)


def uninstall(dest_root):
    dst = os.path.join(dest_root, NAME)
    if os.path.exists(dst):
        shutil.rmtree(dst)
        print('✔ 已删除：', dst)


def make_zip():
    # 两种布局：带一层文件夹（多数平台）和 SKILL.md 在根目录（部分平台要求，如阿里云百炼）
    _zip(NAME + '.zip', NAME)
    _zip(NAME + '-flat.zip', '')


def _zip(fname, prefix):
    os.makedirs(os.path.join(HERE, 'dist'), exist_ok=True)
    out = os.path.join(HERE, 'dist', fname)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(SRC):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', 'build', 'preview')]
            for f in files:
                if f.endswith('.pyc'):
                    continue
                p = os.path.join(root, f)
                z.write(p, os.path.join(prefix, os.path.relpath(p, SRC)).replace(os.sep, '/'))
    print('✔ 已打包：', out, '(%.0f KB)' % (os.path.getsize(out) / 1024))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--target', choices=list(TARGETS) + ['all'])
    ap.add_argument('--dest')
    ap.add_argument('--zip', action='store_true')
    ap.add_argument('--uninstall', action='store_true')
    a = ap.parse_args()

    if a.zip:
        make_zip()
        return
    if a.dest:
        roots = [a.dest]
    elif a.target == 'all':
        roots = list(TARGETS.values())
    elif a.target:
        roots = [TARGETS[a.target]]
    else:
        roots = [p for p in TARGETS.values() if os.path.isdir(os.path.dirname(p))]
        if not roots:
            print('没找到 ~/.claude、~/.codex、~/.agents，请用 --target 或 --dest 指定。')
            sys.exit(1)
    for r in roots:
        (uninstall if a.uninstall else install)(r)
    if not a.uninstall:
        print('\n下一步：python "%s" 检查 LaTeX 与 Python 环境' % os.path.join(SRC, 'scripts', 'check_env.py'))


if __name__ == '__main__':
    main()
