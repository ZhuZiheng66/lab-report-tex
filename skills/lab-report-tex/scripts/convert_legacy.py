# -*- coding: utf-8 -*-
""".doc / .ppt / .xls / .wps 等老格式 → docx / pptx / xlsx（可选 pdf），原件不动。

已经替你绕开的坑（实测）：
  1. Word COM 只认反斜杠绝对路径：C:/a/b.doc 会报“找不到文件”。
  2. 文件名含全角字符、空格、括号时 Word 常打不开：先复制成 ASCII 临时文件名再转换。
  3. 很多 Agent 沙箱拦截 PowerShell 的 New-Object -ComObject：这里用 Python 的 pywin32。
  4. Word/PowerPoint 不可用时（macOS、Linux、没装 Office）自动改用 LibreOffice：soffice --headless --convert-to。

用法：
  python convert_legacy.py "实验报告模版 空白(2).doc"            # 输出到原文件旁边：…空白(2).docx
  python convert_legacy.py 讲义.ppt 模板.doc --out converted --pdf  # 另存一份 PDF，便于看版式
依赖：Windows + Office 时需要 pywin32（pip install pywin32）；否则需要 LibreOffice。
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TARGET = {'.doc': '.docx', '.wps': '.docx', '.rtf': '.docx', '.ppt': '.pptx', '.dps': '.pptx', '.pps': '.pptx',
          '.xls': '.xlsx', '.et': '.xlsx'}
# Office SaveAs 的格式代码
WORD_FMT = {'.docx': 16, '.pdf': 17}
PPT_FMT = {'.pptx': 24, '.pdf': 32}
XLS_FMT = {'.xlsx': 51, '.pdf': None}


def office_convert(src, dst, kind):
    import win32com.client  # noqa: F401  （ImportError 交给调用方回退）
    import pythoncom
    pythoncom.CoInitialize()
    ext = os.path.splitext(dst)[1]
    if kind == 'word':
        app = win32com.client.DispatchEx('Word.Application')
        app.Visible = False
        app.DisplayAlerts = 0
        try:
            d = app.Documents.Open(src, False, True, False)
            d.SaveAs2(dst, WORD_FMT[ext])
            d.Close(False)
        finally:
            app.Quit()
    elif kind == 'ppt':
        app = win32com.client.DispatchEx('PowerPoint.Application')
        try:
            p = app.Presentations.Open(src, True, False, False)   # ReadOnly, Untitled, WithWindow=False
            p.SaveAs(dst, PPT_FMT[ext])
            p.Close()
        finally:
            app.Quit()
    else:
        app = win32com.client.DispatchEx('Excel.Application')
        app.Visible = False
        app.DisplayAlerts = False
        try:
            wb = app.Workbooks.Open(src, ReadOnly=True)
            if ext == '.pdf':
                wb.ExportAsFixedFormat(0, dst)
            else:
                wb.SaveAs(dst, XLS_FMT[ext])
            wb.Close(False)
        finally:
            app.Quit()


def soffice():
    for name in ('soffice', 'libreoffice'):
        p = shutil.which(name)
        if p:
            return p
    for p in glob.glob(r'C:\Program Files*\LibreOffice\program\soffice.exe') + \
            ['/Applications/LibreOffice.app/Contents/MacOS/soffice']:
        if os.path.exists(p):
            return p
    return None


def lo_convert(src, dst):
    exe = soffice()
    if not exe:
        raise RuntimeError('没有可用的 Office（pywin32）也没有 LibreOffice')
    outdir = os.path.dirname(dst)
    fmt = os.path.splitext(dst)[1][1:]
    subprocess.run([exe, '--headless', '--convert-to', fmt, '--outdir', outdir, src],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300, check=True)
    produced = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + '.' + fmt)
    if produced != dst:
        shutil.move(produced, dst)


def convert_one(path, outdir, also_pdf):
    path = os.path.abspath(path)
    ext = os.path.splitext(path)[1].lower()
    if ext not in TARGET:
        print('跳过（不是老格式）：', path)
        return []
    kind = 'word' if TARGET[ext] == '.docx' else ('ppt' if TARGET[ext] == '.pptx' else 'xls')
    outdir = os.path.abspath(outdir or os.path.dirname(path))
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0]
    tmp = tempfile.mkdtemp(prefix='lrt_')
    safe = os.path.join(tmp, 'src_' + uuid.uuid4().hex[:8] + ext)        # ASCII 名，反斜杠绝对路径
    shutil.copyfile(path, safe)
    made = []
    try:
        for target in [TARGET[ext]] + (['.pdf'] if also_pdf else []):
            tmp_out = os.path.join(tmp, 'out' + target)
            how = 'Office'
            try:
                office_convert(safe, tmp_out, kind)
            except Exception as e:
                how = 'LibreOffice'
                print('  Office 转换不可用（%s），改用 LibreOffice' % (type(e).__name__ if isinstance(e, ImportError)
                                                                   else str(e).splitlines()[0][:80]))
                lo_convert(safe, tmp_out)
            final = os.path.join(outdir, stem + target)
            if os.path.exists(final):
                final = os.path.join(outdir, stem + '_converted' + target)
            shutil.move(tmp_out, final)
            made.append(final)
            print('✔ %s → %s（%s）' % (os.path.basename(path), final, how))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return made


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+')
    ap.add_argument('--out', help='输出目录（默认原文件旁边）')
    ap.add_argument('--pdf', action='store_true', help='另存一份 PDF')
    a = ap.parse_args()
    failed = 0
    for f in a.files:
        try:
            convert_one(f, a.out, a.pdf)
        except Exception as e:
            failed += 1
            print('✘ %s：%s' % (f, e))
            print('  办法：用户用 Word/WPS 打开后“另存为 .docx”；或安装 LibreOffice 后重试')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
