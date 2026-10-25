# -*- coding: utf-8 -*-
"""原始数据的确认状态：把“用户确认过”从口头约定变成可检查的记录（报告目录下的 data_status.json）。

状态流转（只能往前走；文件内容变了会被 build.py 发现）：
  pending        还没处理 / 状态未知（默认）
  transcribed    AI 已从照片转写成 CSV，**等待用户核对**
  reviewed       用户已逐项核对并确认 —— 必须用 --confirmed-by 写明是谁、怎么确认的（最好引用用户原话）
  frozen         确认后冻结：记录 SHA-256，之后任何改动都会让 build.py 阻断
  used_in_report build.py 通过验收后自动标记

**不要伪造确认。**没有得到用户明确确认，就停在 transcribed；不知道就是 pending。

用法：
  python data_status.py add data/raw.csv --source "IMG_2034.jpg 表1"        # 登记为 transcribed
  python data_status.py review data/raw.csv --confirmed-by "用户：‘第4行改成-2.68，其余没问题’"
  python data_status.py freeze data/raw.csv
  python data_status.py show
  python data_status.py check            # 有未冻结或被改动的文件时退出码 2
"""
import argparse
import datetime
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import sha256  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ORDER = ['pending', 'transcribed', 'reviewed', 'frozen', 'used_in_report']
FILE = 'data_status.json'


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


def load(base='.'):
    p = os.path.join(base, FILE)
    if not os.path.exists(p):
        return None
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)


def save(data, base='.'):
    with io.open(os.path.join(base, FILE), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')


def key(path):
    return os.path.normpath(path).replace(os.sep, '/')


def check(base='.', allow_used=True):
    """返回问题列表（空 = 全部已冻结且未被改动）。供 build.py 调用。"""
    data = load(base)
    if data is None:
        return ['没有 %s：原始数据还没有登记确认状态（用 data_status.py add/review/freeze）' % FILE]
    files = data.get('files', {})
    if not files:
        return ['%s 里没有登记任何原始数据文件' % FILE]
    problems = []
    for name, info in sorted(files.items()):
        st = info.get('status', 'pending')
        p = os.path.join(base, name)
        if st not in ('frozen', 'used_in_report'):
            problems.append('%s 的状态是 %s，尚未冻结（需用户确认后 review → freeze）' % (name, st))
            continue
        if not os.path.exists(p):
            problems.append('%s 已冻结但文件不存在' % name)
        elif sha256(p) != info.get('sha256'):
            problems.append('%s 冻结后被修改过（SHA-256 不一致）：请让用户重新确认后再 freeze' % name)
    return problems


def mark_used(base='.'):
    data = load(base)
    if not data:
        return
    for info in data.get('files', {}).values():
        if info.get('status') == 'frozen':
            info['status'] = 'used_in_report'
            info.setdefault('history', []).append({'status': 'used_in_report', 'time': now()})
    save(data, base)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')
    sub.required = True
    s = sub.add_parser('add')
    s.add_argument('files', nargs='+')
    s.add_argument('--source', default='', help='来自哪张照片/哪个导出文件')
    s.add_argument('--status', choices=['pending', 'transcribed'], default='transcribed')
    s = sub.add_parser('review')
    s.add_argument('files', nargs='+')
    s.add_argument('--confirmed-by', required=True, help='谁、如何确认的（引用用户原话）；没有用户确认不要用这个命令')
    s = sub.add_parser('freeze')
    s.add_argument('files', nargs='+')
    sub.add_parser('show')
    sub.add_parser('check')
    a = ap.parse_args()

    data = load() or {'schema': 1, 'files': {}}
    files = data.setdefault('files', {})

    if a.cmd == 'add':
        for f in a.files:
            if not os.path.exists(f):
                raise SystemExit('文件不存在：%s' % f)
            k = key(f)
            info = files.get(k, {})
            if ORDER.index(info.get('status', 'pending')) > ORDER.index(a.status):
                print('%s 已是 %s，不降级' % (k, info['status']))
                continue
            info.update(status=a.status, source=a.source or info.get('source', ''))
            info.setdefault('history', []).append({'status': a.status, 'time': now()})
            files[k] = info
            print('%s → %s' % (k, a.status))
    elif a.cmd == 'review':
        if not a.confirmed_by.strip():
            raise SystemExit('--confirmed-by 不能为空')
        for f in a.files:
            k = key(f)
            if k not in files:
                raise SystemExit('%s 还没登记，先 add' % k)
            files[k].update(status='reviewed', confirmed_by=a.confirmed_by, reviewed_sha256=sha256(f))
            files[k].setdefault('history', []).append({'status': 'reviewed', 'time': now(), 'by': a.confirmed_by})
            print('%s → reviewed（%s）' % (k, a.confirmed_by))
    elif a.cmd == 'freeze':
        for f in a.files:
            k = key(f)
            info = files.get(k)
            if not info or info.get('status') not in ('reviewed', 'frozen', 'used_in_report'):
                raise SystemExit('%s 还没有经过用户确认（review），不能冻结' % k)
            if info.get('reviewed_sha256') and info['reviewed_sha256'] != sha256(f):
                raise SystemExit('%s 在用户确认之后又被改过，需要重新 review' % k)
            info.update(status='frozen', sha256=sha256(f))
            info.setdefault('history', []).append({'status': 'frozen', 'time': now()})
            print('%s → frozen（%s…）' % (k, info['sha256'][:12]))
    elif a.cmd == 'show':
        for k, info in sorted(files.items()):
            print('%-32s %-15s %s' % (k, info.get('status'), info.get('confirmed_by', '')))
        return
    elif a.cmd == 'check':
        probs = check()
        for p in probs:
            print('✘', p)
        print('全部已冻结' if not probs else '')
        sys.exit(2 if probs else 0)
    save(data)


if __name__ == '__main__':
    main()
