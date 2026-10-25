# -*- coding: utf-8 -*-
"""编译报告并做交付验收：**全部检查通过后**才把 PDF 放到正式输出目录。

流程：预检（数据状态、\\input 文件、需求清单里的图表）→ 编译 → 日志检查 → 内容检查 → 通过才交付
  · 任何一项不通过：PDF 只留在 <builddir>/candidate/<名字>.candidate.pdf，正式输出目录里不会出现 PDF，退出码 2。
  · 全部通过：复制到 --outdir/<名字>.pdf，并把 data_status.json 里冻结的数据标记为 used_in_report，退出码 0。

用法：
  python build.py report.tex
  python build.py report.tex --name "{coursecode}-{group}-{author}-{expname}" --outdir ../成品
  python build.py report.tex --thumbs preview          # 每页一张 PNG + 一张总览 contact.png
  python build.py report.tex --require "实验目的,实验原理,实验仪器,实验内容,数据记录,结果陈述,思考题,成绩评定,原始数据"
--name 里的 {键} 取自 report.tex 中 \\labset{...} 的同名键（expname、author、group、coursecode 等）。
--require 不给时，从同目录 requirements.md 里的 `--require "…"` 行读取。

检查项：
  数据状态   data_status.json 存在，且所有原始数据都已 frozen、文件未被改动（--allow-unfrozen 可降级为警告）
  输入文件   report.tex 里 \\input{…} 的文件都存在
  需求清单   requirements.md 中“- 图：fig/x.pdf”“- 表：tab/x.tex”列出的文件存在，且被 report.tex 引用
  编译日志   错误、缺字、未定义引用、找不到的文件（超宽行只提示）
  PDF        确实生成
  内容       章节齐全且顺序对；无“……”/TODO/尖括号占位；封面 expname/author/date 不为空；
             正文没有手抄 results.tex 里已有的计算结果（应写宏）；
             确属有意的字面数字（如测量设定点），在该行末尾写 `% lrt:literal（原因）` 豁免
退出码：0 通过并已交付；1 编译失败；2 编译成功但验收不通过（只有候选 PDF）；3 环境缺失（没有 LaTeX 编译器）。
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_status  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
EXIT_OK, EXIT_COMPILE, EXIT_CHECK, EXIT_ENV = 0, 1, 2, 3


class EnvMissing(Exception):
    pass


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
    raise EnvMissing('找不到 LaTeX 编译器（试过：%s）。先运行 scripts/check_env.py 看安装建议。'
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


def strip_comments(src):
    return re.sub(r'(?<!\\)%.*', '', src)


def read_tex(tex):
    with io.open(tex, encoding='utf-8') as f:
        return f.read()


def labset_keys(tex):
    src = strip_comments(read_tex(tex))
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
    if not ims:
        return
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
    src = strip_comments(read_tex(tex))
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


# ---------------- 预检 ----------------

def check_inputs(tex):
    """\\input{…} / \\include{…} 的文件是否存在（\\InputIfFileExists 是可选的，不查）。"""
    base = os.path.dirname(os.path.abspath(tex))
    src = strip_comments(read_tex(tex))
    problems = []
    for name in re.findall(r'\\(?:input|include)\{([^{}]+)\}', src):
        p = os.path.join(base, name)
        if not (os.path.exists(p) or os.path.exists(p + '.tex')):
            problems.append('\\input 的文件不存在：%s' % os.path.normpath(p))
    return problems


def parse_requirements(path):
    """从 requirements.md 读：--require 章节串、要求的图文件、要求的表文件。"""
    if not os.path.exists(path):
        return None, [], []
    text = io.open(path, encoding='utf-8').read()
    m = re.search(r'--require\s+"([^"]+)"', text)
    figs = re.findall(r'^\s*[-*]\s*(?:\[[ xX]\]\s*)?图\s*[：:]\s*`?([^\s`]+)`?', text, re.M)
    tabs = re.findall(r'^\s*[-*]\s*(?:\[[ xX]\]\s*)?表\s*[：:]\s*`?([^\s`]+)`?', text, re.M)
    return (m.group(1) if m else None), figs, tabs


def check_requirements(tex, figs, tabs):
    base = os.path.dirname(os.path.abspath(tex))
    src = strip_comments(read_tex(tex))
    problems = []

    def norm(s):
        return os.path.splitext(s.replace('\\', '/').lstrip('./'))[0]
    used_figs = {norm(x) for x in re.findall(r'\\(?:labfig(?:\[[^\]]*\])?|includegraphics(?:\[[^\]]*\])?)\{([^{}]+)\}', src)}
    for args in re.findall(r'\\labfigs\{([^{}]+)\}\{[^{}]*\}\{[^{}]*\}\{([^{}]+)\}', src):
        used_figs |= {norm(x) for x in args}
    used_inputs = {norm(x) for x in re.findall(r'\\input\{([^{}]+)\}', src)}
    for f in figs:
        p = os.path.join(base, f)
        if not os.path.exists(p):
            problems.append('需求清单要求的图不存在：%s' % os.path.normpath(p))
        elif norm(f) not in used_figs:
            problems.append('需求清单要求的图没有被 report.tex 引用：%s' % f)
    for t in tabs:
        p = os.path.join(base, t)
        if not (os.path.exists(p) or os.path.exists(p + '.tex')):
            problems.append('需求清单要求的表不存在：%s' % os.path.normpath(p))
        elif norm(t) not in used_inputs:
            problems.append('需求清单要求的表没有被 report.tex \\input：%s' % t)
    return problems


# ---------------- 内容检查 ----------------

def macro_values(tex):
    """results.tex 等宏文件里的数值：{值: 宏名}。只取带小数点、≥3 位有效数字的，避免误报 1、10 这类常见数。"""
    base = os.path.dirname(os.path.abspath(tex))
    vals = {}
    src = strip_comments(read_tex(tex))
    for name in re.findall(r'\\(?:input|InputIfFileExists)\{([^{}]+)\}', src):
        p = os.path.join(base, name)
        p = p if os.path.exists(p) else p + '.tex'
        if not os.path.exists(p):
            continue
        for mac, val in re.findall(r'^\\def\\([A-Za-z]+)\{([^{}]*)\}', io.open(p, encoding='utf-8').read(), re.M):
            v = val.strip().lstrip('+-')
            m = re.fullmatch(r'(\d*\.\d+)(?:[eE][-+]?\d+)?', v)
            if m and len(re.sub(r'^[0.]+', '', m.group(1).replace('.', ''))) >= 3:
                vals.setdefault(m.group(1), mac)
    return vals


def check_content(tex, required):
    """章节齐全且顺序对、没有遗留占位符、封面不空、没有手抄计算结果。返回 (outline, 问题列表)。"""
    src, outline = report_outline(tex)
    problems = []
    if required:
        pos = 0
        for item in required:
            hit = next((i for i in range(pos, len(outline)) if item in outline[i]), None)
            if hit is None:
                anywhere = any(item in o for o in outline)
                problems.append('要求的章节“%s”%s' % (item, '顺序不对' if anywhere else '缺失'))
            else:
                pos = hit + 1
    raw = read_tex(tex)
    start = raw.find('\\begin{document}')
    lines = raw.splitlines()
    first = raw[:start].count('\n') if start >= 0 else 0
    for pat, what in ((r'……', '“……”占位'), (r'TODO|待补|待填|XXX', 'TODO/待补'), (r'<[^<>\n]{1,12}>', '尖括号占位')):
        hits = [i + 1 for i in range(first, len(lines)) if re.search(pat, strip_comments(lines[i]))]
        if hits:
            problems.append('正文还有%s：report.tex 第 %s 行' % (what, '、'.join(map(str, hits[:8]))))
    keys = labset_keys(tex)
    empty = [k for k in ('expname', 'author', 'date') if not keys.get(k)]
    if empty:
        problems.append('封面信息为空：%s（不知道就问用户，不要编）' % ', '.join(empty))
    vals = macro_values(tex)
    if vals:
        for i in range(first, len(lines)):
            if 'lrt:literal' in lines[i]:      # 行尾写 % lrt:literal（原因） 表示这里的字面数字是有意的（如测量设定点）
                continue
            body = strip_comments(lines[i])
            body = re.sub(r'\\[A-Za-z]+', ' ', body)          # 去掉宏名，只看字面数字
            for numtxt in re.findall(r'(?<![\d.])(\d*\.\d+)(?![\d.])', body):
                if numtxt in vals:
                    problems.append('report.tex 第 %d 行手写了 %s，与宏 \\%s 的值相同：请改用宏，避免手抄'
                                    % (i + 1, numtxt, vals[numtxt]))
    return outline, problems


def output_name(tex, pattern, stem):
    keys = labset_keys(tex)
    if pattern:
        try:
            name = pattern.format(**keys)
        except KeyError as e:
            raise SystemExit('--name 里的 %s 在 \\labset 里没有；现有键：%s' % (e, ', '.join(keys)))
    else:
        name = keys.get('expname') or stem
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tex', nargs='?', default='report.tex')
    ap.add_argument('--require', help='老师要求的章节顺序，逗号分隔；不给则读 requirements.md')
    ap.add_argument('--requirements', help='需求清单路径（默认 report.tex 同目录的 requirements.md）')
    ap.add_argument('--name', help='输出文件名（不含 .pdf），可用 {expname} 等占位符')
    ap.add_argument('--outdir', default='.')
    ap.add_argument('--builddir', default='build')
    ap.add_argument('--thumbs', help='缩略图目录')
    ap.add_argument('--engine', choices=['auto', 'latexmk', 'xelatex', 'tectonic'], default='auto')
    ap.add_argument('--allow-unfrozen', action='store_true',
                    help='原始数据未冻结时只警告不阻断（仅用于草稿；交付前必须完成用户确认）')
    a = ap.parse_args()

    tex = os.path.abspath(a.tex)
    cwd = os.path.dirname(tex)
    stem = os.path.splitext(os.path.basename(tex))[0]
    if not os.path.exists(tex):
        print('✘ 找不到 %s' % tex)
        sys.exit(EXIT_CHECK)

    # ---- 预检 ----
    problems, warnings = [], []
    req_path = a.requirements or os.path.join(cwd, 'requirements.md')
    req_sections, req_figs, req_tabs = parse_requirements(req_path)
    required = [s.strip() for s in re.split(r'[,，]', a.require or req_sections or '') if s.strip()]
    ds = data_status.check(cwd)
    (warnings if a.allow_unfrozen else problems).extend('数据状态：' + p for p in ds)
    missing_inputs = check_inputs(tex)
    problems += missing_inputs
    problems += check_requirements(tex, req_figs, req_tabs)
    if missing_inputs:          # 缺 \input 文件必然编译失败：直接报原因和路径，不浪费一次编译
        print('✘ 预检未通过，未编译，没有输出 PDF：')
        for p in problems:
            print('   -', p)
        sys.exit(EXIT_CHECK)

    # ---- 编译 ----
    builddir = os.path.join(cwd, a.builddir)
    try:
        code, out = compile_tex(tex, a.builddir, a.engine)
    except EnvMissing as e:
        print('【环境缺失】%s' % e)
        sys.exit(EXIT_ENV)
    pdf = os.path.join(builddir, stem + '.pdf')
    logpath = os.path.join(builddir, stem + '.log')
    issues = check_log(logpath)
    for k, v in issues.items():
        print('【%s】' % k)
        for item in v[:15]:
            print('   ', item)
    if code or not os.path.exists(pdf):
        print('✘ 编译失败，没有生成 PDF。日志：%s' % logpath)
        print('\n'.join(out.splitlines()[-25:]))
        sys.exit(EXIT_COMPILE)
    for k, v in issues.items():
        if not k.startswith('明显'):
            problems.append('编译日志有“%s”：%s（见 %s）' % (k, '、'.join(map(str, v[:5])), logpath))

    # ---- 内容 ----
    outline, cproblems = check_content(tex, required)
    problems += cproblems
    print('报告结构：' + ' → '.join(outline))

    name = output_name(tex, a.name, stem)
    if problems:
        cand_dir = os.path.join(builddir, 'candidate')
        os.makedirs(cand_dir, exist_ok=True)
        cand = os.path.join(cand_dir, name + '.candidate.pdf')
        shutil.copyfile(pdf, cand)
        print('\n✘ 验收未通过（%d 项），没有输出正式 PDF：' % len(problems))
        for p in problems:
            print('   -', p)
        for w in warnings:
            print('   ! 警告：', w)
        print('候选 PDF（仅供检查，不是交付结果）：%s' % cand)
        if a.thumbs:
            thumbs(cand, a.thumbs)
        sys.exit(EXIT_CHECK)

    os.makedirs(a.outdir, exist_ok=True)
    final = os.path.abspath(os.path.join(a.outdir, name + '.pdf'))
    shutil.copyfile(pdf, final)
    for w in warnings:
        print('! 警告：', w)
    if not warnings:
        data_status.mark_used(cwd)
    print('✔ 验收通过，输出：%s（%.0f KB）' % (final, os.path.getsize(final) / 1024))
    print('提示：返工重编译后，聊天客户端里的 PDF 预览可能还是旧的。请关掉旧标签重开，'
          '或用 --name 换个文件名（如加 -v2）再给用户。')
    if a.thumbs:
        thumbs(final, a.thumbs)
    sys.exit(EXIT_OK)


if __name__ == '__main__':
    main()
