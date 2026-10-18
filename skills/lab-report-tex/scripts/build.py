# -*- coding: utf-8 -*-
"""编译报告 → 检查日志 → 按规则命名 → 生成逐页缩略图，一步完成。

用法：
  python build.py report.tex
  python build.py report.tex --name "{coursecode}-{group}-{author}-{expname}" --outdir ../成品
  python build.py report.tex --thumbs preview          # 每页一张 PNG + 一张总览 contact.png
  python build.py report.tex --require "实验目的,实验原理,实验仪器,实验内容,数据记录,结果陈述,思考题,成绩评定,原始数据"
--name 里的 {键} 取自 report.tex 中 \\labset{...} 的同名键（expname、author、group、coursecode 等），
也可以写死：--name "39-9-张三-霍尔效应及其应用"。

编译器按顺序尝试：latexmk -xelatex → xelatex（跑两遍）→ tectonic。
日志检查会列出：错误、缺字（Missing character，中文字体问题）、未定义引用、找不到的文件、明显的 Overfull。
另外核对内容：要求的章节是否齐全、顺序对不对；正文是否还有“……”/TODO/尖括号占位；封面关键信息是否为空。
退出码：0 成功；1 编译失败；2 编译成功但有需要处理的问题（缺字/未定义引用/内容核对）。
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')


def run(cmd, cwd):
    print('$', ' '.join(cmd))
    # 报告目录里没有 labreport.cls 时，用 skill 自带的那份。顺序：当前目录 → 原有/默认路径（空项）→ 模板目录。
    # 模板目录必须排最后：它里面也有 report.tex，排前面会把空白模板当成你的报告编译。
    env = os.environ.copy()
    env['TEXINPUTS'] = os.pathsep.join(['.', env.get('TEXINPUTS', ''), os.path.abspath(TEMPLATES)])
    p = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def compile_tex(tex, builddir, engine):
    cwd = os.path.dirname(os.path.abspath(tex)) or '.'
    base = os.path.basename(tex)
    os.makedirs(os.path.join(cwd, builddir), exist_ok=True)
    opts = ['-interaction=nonstopmode', '-halt-on-error', '-file-line-error']
    tried = []
    if engine in ('auto', 'latexmk') and shutil.which('latexmk') and (shutil.which('perl') or os.name != 'nt'):
        code, out = run(['latexmk', '-xelatex', '-outdir=' + builddir] + opts + [base], cwd)
        if code == 0 or engine == 'latexmk':
            return code, out
        tried.append('latexmk')
    if engine in ('auto', 'xelatex') and shutil.which('xelatex'):
        out = ''
        for _ in range(2):
            code, o = run(['xelatex', '-output-directory=' + builddir] + opts + [base], cwd)
            out += o
            if code:
                break
        return code, out
    if engine in ('auto', 'tectonic') and shutil.which('tectonic'):
        return run(['tectonic', '-X', 'compile', '--outdir', builddir, base], cwd)
    raise SystemExit('找不到 LaTeX 编译器（试过：%s）。先运行 scripts/check_env.py 看安装建议。'
                     % (', '.join(tried) or 'latexmk/xelatex/tectonic'))


def check_log(logpath):
    if not os.path.exists(logpath):
        return {}
    with io.open(logpath, encoding='utf-8', errors='replace') as f:
        log = f.read()
    found = {
        '错误': re.findall(r'^(?:! |.*:\d+: )(.*)$', log, re.M),
        '缺字（字体里没有这个字符，PDF 里会是空白）': sorted(set(re.findall(r'Missing character: There is no (.+?) in font', log))),
        '未定义引用': sorted(set(re.findall(r"Reference `([^']+)' on page", log))),
        '找不到文件': sorted(set(re.findall(r"File `([^']+)' not found", log))),
        '明显超出行宽 (>10pt)': [m for m in re.findall(r'Overfull \\hbox \((\d+\.\d+)pt too wide\)[^\n]*lines? (\d+)', log)
                              if float(m[0]) > 10],
    }
    return {k: v for k, v in found.items() if v}


def labset_keys(tex):
    with io.open(tex, encoding='utf-8') as f:
        src = f.read()
    src = re.sub(r'(?<!\\)%.*', '', src)
    keys = {}
    for block in re.findall(r'\\labset\{((?:[^{}]|\{[^{}]*\})*)\}', src):
        for k, v1, v2 in re.findall(r'(\w+)\s*=\s*(?:\{([^{}]*)\}|([^,{}\n]*))', block):
            keys[k] = (v1 or v2).strip()
    return keys


def thumbs(pdf, outdir):
    try:
        import fitz
    except ImportError:
        print('（没有 PyMuPDF，跳过缩略图：pip install pymupdf）')
        return
    from PIL import Image
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):        # 清掉上次的缩略图，避免页数变少后残留旧页
        if re.match(r'p\d+\.png$', f):
            os.remove(os.path.join(outdir, f))
    doc = fitz.open(pdf)
    ims = []
    for i, pg in enumerate(doc):
        p = os.path.join(outdir, 'p%02d.png' % (i + 1))
        pg.get_pixmap(dpi=110).save(p)
        ims.append(Image.open(p))
        text = pg.get_text().strip().replace('\n', ' ')
        print('  第 %d 页：%s' % (i + 1, (text[:40] or '(无文字，可能是照片页)')))
    # 总览图：一张图看全部页面，方便快速检查页序和空白页
    cols = min(4, len(ims))
    w = 360
    hs = [int(im.height * w / im.width) for im in ims]
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (w + 10) + 10, rows * (max(hs) + 10) + 10), 'white')
    for i, im in enumerate(ims):
        t = im.resize((w, hs[i]))
        x, y = 10 + (i % cols) * (w + 10), 10 + (i // cols) * (max(hs) + 10)
        sheet.paste(t, (x, y))
        sheet.paste(Image.new('RGB', (w, 1), 'gray'), (x, y + hs[i]))
    sheet.save(os.path.join(outdir, 'contact.png'))
    print('缩略图：%s（总览 contact.png）' % outdir)


def report_outline(tex):
    """按出现顺序列出报告的“块”：章节标题、教师评阅、评分栏、照片页标题。"""
    with io.open(tex, encoding='utf-8') as f:
        src = re.sub(r'(?<!\\)%.*', '', f.read())
    pat = re.compile(r'\\begin\{labsection\*?\}\{([^{}]*)\}|\\labcomment|\\labgrading|\\labphotos\{([^{}]*)\}')
    out = []
    for m in pat.finditer(src):
        t = m.group(0)
        if t.startswith('\\labcomment'):
            out.append('指导教师批阅意见')
        elif t.startswith('\\labgrading'):
            out.append('成绩评定')
        else:
            out.append((m.group(1) or m.group(2) or '照片').strip())
    return src, out


def check_content(tex, required):
    """交付前的内容核对：章节齐全且顺序对、没有遗留占位符。返回问题列表。"""
    src, outline = report_outline(tex)
    problems = []
    if required:
        pos = 0
        for item in required:
            hit = next((i for i in range(pos, len(outline)) if item in outline[i]), None)
            if hit is None:
                anywhere = any(item in o for o in outline)
                problems.append('要求的“%s”%s' % (item, '顺序不对' if anywhere else '缺失'))
            else:
                pos = hit + 1
    body = src.split('\\begin{document}', 1)[-1]
    for pat, what in ((r'……', '“……”占位'), (r'TODO|待补|待填|XXX', 'TODO/待补'), (r'<[^<>\n]{1,12}>', '尖括号占位')):
        n = len(re.findall(pat, body))
        if n:
            problems.append('正文还有 %d 处%s' % (n, what))
    keys = labset_keys(tex)
    empty = [k for k in ('expname', 'author', 'date') if not keys.get(k)]
    if empty:
        problems.append('封面信息为空：%s（不知道就问用户，不要编）' % ', '.join(empty))
    return outline, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tex', nargs='?', default='report.tex')
    ap.add_argument('--require', help='老师要求的章节顺序，逗号分隔，如 "实验目的,实验原理,…,成绩评定,原始数据"；'
                                      '检查缺失和顺序（包含匹配）')
    ap.add_argument('--name', help='输出文件名（不含 .pdf），可用 {expname} 等占位符')
    ap.add_argument('--outdir', default='.')
    ap.add_argument('--builddir', default='build')
    ap.add_argument('--thumbs', help='缩略图目录')
    ap.add_argument('--engine', choices=['auto', 'latexmk', 'xelatex', 'tectonic'], default='auto')
    a = ap.parse_args()

    code, out = compile_tex(a.tex, a.builddir, a.engine)
    cwd = os.path.dirname(os.path.abspath(a.tex))
    stem = os.path.splitext(os.path.basename(a.tex))[0]
    pdf = os.path.join(cwd, a.builddir, stem + '.pdf')
    issues = check_log(os.path.join(cwd, a.builddir, stem + '.log'))
    for k, v in issues.items():
        print('【%s】' % k)
        for item in v[:15]:
            print('   ', item)
    if code or not os.path.exists(pdf):
        print('编译失败。日志：%s' % os.path.join(cwd, a.builddir, stem + '.log'))
        print('\n'.join(out.splitlines()[-25:]))
        sys.exit(1)

    keys = labset_keys(a.tex)
    if a.name:
        try:
            name = a.name.format(**keys)
        except KeyError as e:
            raise SystemExit('--name 里的 %s 在 \\labset 里没有；现有键：%s' % (e, ', '.join(keys)))
    else:
        name = keys.get('expname') or stem
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    os.makedirs(a.outdir, exist_ok=True)
    final = os.path.join(a.outdir, name + '.pdf')
    shutil.copyfile(pdf, final)
    print('输出：%s（%.0f KB）' % (final, os.path.getsize(final) / 1024))
    print('提示：返工重编译后，聊天客户端里的 PDF 预览可能还是旧的。请关掉旧标签重开，'
          '或用 --name 换个文件名（如加 -v2）再给用户。')
    if a.thumbs:
        thumbs(final, a.thumbs)
    required = [s.strip() for s in re.split(r'[,，]', a.require or '') if s.strip()]
    outline, problems = check_content(a.tex, required)
    print('报告结构：' + ' → '.join(outline))
    if problems:
        print('【内容核对】')
        for p in problems:
            print('   ', p)
    bad = [k for k in issues if not k.startswith('明显')] + problems
    sys.exit(2 if bad else 0)


if __name__ == '__main__':
    main()
