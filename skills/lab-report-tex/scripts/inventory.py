# -*- coding: utf-8 -*-
"""材料盘点：扫描用户给的文件/文件夹，初步判断每个文件是什么（模板？要求？讲义？原始记录？……）。

用户往往把一堆东西一次性扔过来，文件名也不规范。这个脚本只做**第一轮粗分**：
按文件名关键词 + 文件内容片段打分，给出“类型猜测 + 依据 + 置信度”。之后 Agent 必须逐个打开确认
（照片一律要看图），再把《材料清单》给用户确认。规则见 references/intake.md。

用法：
  python inventory.py 素材文件夹                 # 打印 Markdown 表格
  python inventory.py a.pptx b.jpg 文件夹 --json  # 另输出 JSON（最后一行）
  python inventory.py 文件夹 --depth 3           # 递归深度（默认 2）
类型：template 报告模板 | requirement 老师要求/通知/评分细则 | handout 讲义/PPT | rules 不确定度/数据处理规则讲义
      raw_photo 原始记录照片/扫描件（待看图确认） | datafile 数据文件（仪器导出或已转写的 CSV/TXT） | spreadsheet 表格数据
      prep_quiz 预习材料（预习试卷/题目/预习报告）
      reference 参考报告（往届/同学/自己上一份） | archive 压缩包（需解压再盘点） | legacy 老格式 .doc/.ppt（需转换再看）
      unknown 看不出来
依赖：只用标准库；装了 PyMuPDF 时能读 PDF 文字，装了 Pillow 时给出图片尺寸。
"""
import argparse
import io
import json
import os
import re
import sys
import zipfile

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SKIP_DIRS = {'build', 'preview', '__pycache__', '.git', 'node_modules', 'dist'}
IMG = {'.jpg', '.jpeg', '.png', '.heic', '.webp', '.bmp', '.gif', '.tif', '.tiff'}
NAMES = {
    'template': '报告模板', 'requirement': '老师要求/通知', 'handout': '讲义/PPT', 'rules': '数据处理规则讲义',
    'raw_photo': '原始记录照片(待看图)', 'datafile': '数据文件', 'spreadsheet': '表格数据',
    'prep_quiz': '预习材料', 'reference': '参考报告', 'archive': '压缩包', 'legacy': '老格式文档',
    'unknown': '看不出来',
}

# 文件名关键词 → (类型, 分数)
NAME_RULES = [
    (r'模板|模版|空白|template', 'template', 5),
    (r'要求|通知|说明|规范|评分|细则|格式|须知|notice|requirement', 'requirement', 5),
    (r'讲义|课件|ppt|指导书|教案|handout|lecture', 'handout', 4),
    (r'不确定|有效数字|误差理论|数据处理方法', 'rules', 6),
    (r'原始|数据|记录|data|raw|IMG_|DSC|微信图片|mmexport|Screenshot|截图|屏幕', 'raw_photo', 2),
    (r'预习|题目|试卷|测验|quiz', 'prep_quiz', 15),
    (r'学长|学姐|同学|参考|范文|样例|往届|成品|报告', 'reference', 3),
]
# 内容关键词 → (类型, 分数)
TEXT_RULES = [
    (r'单选题|多选题|标准答案|学生答案|学生得分', 'prep_quiz', 8),
    (r'不确定度的?(?:评定|评估)|有效数字|修约规则|四舍六入', 'rules', 2),
    (r'命名|截止|格式要求|评分标准|扣分|请同学|务必|文件名', 'requirement', 3),
    (r'实验目的|实验原理|实验仪器|实验内容|注意事项|思考题', 'handout', 1),
]


def text_of(path, ext):
    """尽量取出前几千字文字；取不到返回 ''。"""
    try:
        if ext in ('.docx', '.pptx', '.xlsx'):
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
                if ext == '.docx':
                    parts = ['word/document.xml']
                elif ext == '.pptx':
                    parts = sorted((n for n in names if re.match(r'ppt/slides/slide\d+\.xml$', n)),
                                   key=lambda n: int(re.findall(r'\d+', n)[-1]))
                else:
                    parts = ['xl/sharedStrings.xml'] + [n for n in names if n.startswith('xl/worksheets/sheet')][:2]
                out = []
                for p in parts:
                    if p in names:
                        xml = z.read(p).decode('utf-8', 'replace')
                        out.append(' '.join(re.findall(r'<(?:w:t|a:t|t|v)[^>]*>([^<]*)</', xml)))
                return '\n'.join(out)[:8000]
        if ext == '.pdf':
            try:
                import fitz
            except ImportError:
                return ''
            doc = fitz.open(path)
            return '\n'.join(doc[i].get_text() for i in range(min(4, doc.page_count)))[:8000]
        if ext in ('.txt', '.csv', '.tsv', '.dat', '.md'):
            with io.open(path, encoding='utf-8', errors='replace') as f:
                return f.read(8000)
    except Exception:
        return ''
    return ''


def numeric_ratio(text):
    toks = [t for t in re.split(r'[\s,;	]+', text) if t]
    if not toks:
        return 0.0
    return sum(1 for t in toks if re.fullmatch(r'[-+]?\d+(\.\d+)?([eE][-+]?\d+)?', t)) / len(toks)


def classify(path):
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    score, why = {}, []

    def add(kind, pts, reason):
        score[kind] = score.get(kind, 0) + pts
        why.append(reason)

    for pat, kind, pts in NAME_RULES:
        if kind == 'raw_photo' and ext not in IMG and ext != '.pdf':
            continue
        if re.search(pat, name, re.I):
            add(kind, pts, '文件名含“%s”' % re.search(pat, name, re.I).group(0))

    extra = ''
    if ext in IMG:
        add('raw_photo', 4, '图片')
        try:
            from PIL import Image
            with Image.open(path) as im:
                extra = '%dx%d' % im.size
        except Exception:
            pass
    elif ext in ('.zip', '.rar', '.7z'):
        add('archive', 10, '压缩包')
        if ext == '.zip':
            try:
                with zipfile.ZipFile(path) as z:
                    n = [i for i in z.namelist() if not i.endswith('/')]
                    extra = '%d 个文件' % len(n)
            except Exception:
                pass
    elif ext in ('.doc', '.ppt', '.xls', '.wps', '.dps'):
        add('legacy', 3, '老格式，需另存为 docx/pptx/pdf 再读')
        if ext == '.ppt' or ext == '.dps':
            add('handout', 2, '演示文稿')
    else:
        text = text_of(path, ext)
        if text:
            for pat, kind, pts in TEXT_RULES:
                hits = set(re.findall(pat, text))
                if hits:
                    add(kind, pts * min(len(hits), 3), '内容有“%s”' % '、'.join(sorted(hits)[:3]))
            nr = numeric_ratio(text)
            filled = len(re.findall(r'\d+\.\d+', text))
            if ext == '.pptx':
                add('handout', 3, 'PPT')
            if ext in ('.txt', '.csv', '.tsv', '.dat'):
                if nr > 0.4:
                    add('datafile', 10, '%.0f%% 是数字' % (nr * 100))
                    if re.search(r'原始|raw', name, re.I):
                        why.append('文件名像原始记录的电子版')
            if ext == '.xlsx':
                add('spreadsheet', 4, 'Excel 表格')
            if ext in ('.docx', '.pdf') and re.search(r'实验报告|报告人|课程名称', text):
                # 模板和“已经写好的报告”有同样的框架，区别是有没有填内容：篇幅和数据量
                if len(text) > 1500 or filled > 8:   # 空白模板实测约 800 字、0 个小数
                    add('reference', 12, '是填好的报告（%d 字、%d 个小数）' % (len(text), filled))
                else:
                    add('template', 10, '有报告框架但几乎没填（%d 字）' % len(text))
            extra = '%d 字' % len(text)
        elif ext == '.pdf':
            add('unknown', 1, 'PDF 无可提取文字（可能是扫描件/照片，需看图）')
            add('raw_photo', 2, '可能是扫描件')

    if not score:
        return 'unknown', '低', '没有线索', extra
    ranked = sorted(score.items(), key=lambda kv: -kv[1])
    best, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0
    conf = '高' if top >= 8 and top >= 2 * second else ('中' if top >= 4 else '低')
    if best == 'raw_photo':
        conf = '待看图'
    alt = '；也可能是 %s' % NAMES[ranked[1][0]] if len(ranked) > 1 and ranked[1][1] >= top * 0.6 else ''
    return best, conf, '，'.join(dict.fromkeys(why)) + alt, extra


def walk(paths, depth):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        base = os.path.abspath(p).rstrip(os.sep).count(os.sep)
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            if os.path.abspath(root).count(os.sep) - base >= depth:
                dirs[:] = []
            for f in sorted(files):
                if f.startswith(('~$', '.')) or f in ('desktop.ini', 'Thumbs.db'):
                    continue
                yield os.path.join(root, f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--depth', type=int, default=2)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    rows = []
    for f in walk(a.paths, a.depth):
        kind, conf, why, extra = classify(f)
        rows.append(dict(file=f.replace(os.sep, '/'), kind=kind, label=NAMES[kind], confidence=conf,
                         reason=why, info=extra, size_kb=round(os.path.getsize(f) / 1024)))
    print('| # | 文件 | 初判 | 置信度 | 依据 | 信息 |')
    print('|---|---|---|---|---|---|')
    for i, r in enumerate(rows, 1):
        print('| %d | %s | %s | %s | %s | %s %dKB |' % (i, r['file'], r['label'], r['confidence'], r['reason'],
                                                        r['info'], r['size_kb']))
    kinds = {r['kind'] for r in rows}
    print()
    print('共 %d 个文件。下一步：逐个打开确认（照片必须看图），再把《材料清单》给用户确认。' % len(rows))
    for need, msg in (('template', '没发现报告模板 → 问用户有没有；没有就用 cover=simple 和常见章节顺序'),
                      ('handout', '没发现讲义/PPT → 问用户要；原理、步骤、思考题不能凭空写'),
                      ('raw_photo', '没发现原始记录照片 → 必须问用户要；没有原始数据不能开工'),
                      ('requirement', '没发现单独的老师要求 → 要求可能写在模板注释/讲义里，读的时候留意；或问用户')):
        if need not in kinds and not (need == 'raw_photo' and 'datafile' in kinds):
            print('  ⚠ ' + msg)
    if 'archive' in kinds:
        print('  ⚠ 有压缩包：解压到单独的新文件夹后再对它运行一次本脚本（中文 zip 文件名可能是 GBK 编码）')
    if 'legacy' in kinds:
        print('  ⚠ 有 .doc/.ppt 老格式：用 Word/WPS/LibreOffice 另存为 docx/pptx/pdf 后再读，原件不动')
    if a.json:
        print(json.dumps(rows, ensure_ascii=False))


if __name__ == '__main__':
    main()
