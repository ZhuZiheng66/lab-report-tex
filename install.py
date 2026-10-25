# -*- coding: utf-8 -*-
"""把 skill 安装到各个 Agent 的技能目录，或打包成 zip 供上传。

  python install.py                    # 自动：装到本机已存在的所有 Agent 技能目录
  python install.py --target claude    # 只装 Claude Code
  python install.py --target codex     # 只装 Codex CLI
  python install.py --target doubao    # 豆包工作（~/DoubaoWork/skills）
  python install.py --target workbuddy # WorkBuddy（~/.workbuddy/skills）
  python install.py --dest D:/my/skills   # 装到任意目录
  python install.py --zip              # 生成 dist/lab-report-tex.zip（WorkBuddy、豆包等平台上传用）

安全规则（不会静默删除你的东西）：
  · 目标位置已经有 lab-report-tex 时，默认**拒绝安装**并说明原因；加 --force 才覆盖。
  · 覆盖或卸载前，旧目录会先完整移动到备份目录：~/.lab-report-tex/backups/<时间戳>-<位置>/
    （可用环境变量 LAB_REPORT_TEX_BACKUP_DIR 改位置；备份不放在 skills 目录里，免得被 Agent 当成第二个技能加载）
  · --uninstall 需要再加 --yes 才会执行，同样先备份。
退出码：0 成功；1 有目标被拒绝或失败；2 参数错误。
"""
import argparse
import datetime
import os
import re
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


def backup_root():
    return os.environ.get('LAB_REPORT_TEX_BACKUP_DIR') or os.path.join(HOME, '.lab-report-tex', 'backups')


def backup(dst):
    """把已有目录整个移到带时间戳的备份目录，返回备份路径。"""
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    where = re.sub(r'[^A-Za-z0-9._-]+', '_', os.path.dirname(os.path.abspath(dst)))[-60:]
    bdir = os.path.join(backup_root(), '%s-%s' % (stamp, where))
    os.makedirs(bdir, exist_ok=True)
    target = os.path.join(bdir, os.path.basename(dst))
    shutil.move(dst, target)
    return target


def install(dest_root, force=False):
    dst = os.path.abspath(os.path.join(dest_root, NAME))
    if os.path.exists(dst):
        if not force:
            print('✘ 已存在，未改动：%s\n  如果确定要用新版本覆盖，加 --force（旧目录会先备份）' % dst)
            return False
        b = backup(dst)
        print('  旧版本已备份到：%s' % b)
    os.makedirs(dest_root, exist_ok=True)
    shutil.copytree(SRC, dst, ignore=IGNORE)
    print('✔ 已安装：%s' % dst)
    return True


def uninstall(dest_root, yes=False):
    dst = os.path.abspath(os.path.join(dest_root, NAME))
    if not os.path.exists(dst):
        print('- 没有安装：%s' % dst)
        return True
    if not yes:
        print('✘ 将要删除 %s\n  确认的话加 --yes 再运行（会先备份）' % dst)
        return False
    b = backup(dst)
    print('✔ 已卸载：%s\n  原目录已移到：%s' % (dst, b))
    return True


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
    ap.add_argument('--force', action='store_true', help='目标已存在时覆盖（先备份）')
    ap.add_argument('--uninstall', action='store_true')
    ap.add_argument('--yes', action='store_true', help='确认卸载')
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
            print('没找到 ~/.claude、~/.codex、~/.agents 等目录，请用 --target 或 --dest 指定。')
            sys.exit(2)
    ok = True
    for r in roots:
        ok &= uninstall(r, a.yes) if a.uninstall else install(r, a.force)
    if not a.uninstall and ok:
        print('\n下一步：python "%s" 检查 LaTeX 与 Python 环境' % os.path.join(SRC, 'scripts', 'check_env.py'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
