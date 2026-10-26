# -*- coding: utf-8 -*-
"""检查本机能不能编译报告：Python 依赖、LaTeX 编译器、宏包、中文字体。缺什么就给出安装建议。

用法：python check_env.py
"""
import importlib
import os
import platform
import shutil
import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PY_MODS = [('numpy', True), ('matplotlib', True), ('PIL', True), ('fitz', False), ('docx', False)]
if os.name == 'nt':
    PY_MODS.append(('win32com', False))
OPTIONAL_USE = {'fitz': '缩略图、PDF 转图', 'docx': '解析 Word 模板 read_template.py', 'win32com': '转换 .doc/.ppt'}
PKGS = ['ctex', 'xeCJK', 'fontspec', 'tcolorbox', 'siunitx', 'booktabs', 'tabularx', 'makecell',
        'caption', 'pgfkeys', 'etoolbox', 'fancyhdr', 'hyperref', 'geometry', 'amsmath']
OK, NO, WARN = '✔', '✘', '!'


def main():
    bad = 0
    print('系统：%s %s；Python %s' % (platform.system(), platform.release(), sys.version.split()[0]))
    print('\n[Python 依赖]')
    for m, need in PY_MODS:
        try:
            importlib.import_module(m)
            print(' ', OK, m)
        except ImportError:
            print(' ', NO if need else WARN, m, '' if need else '（可选：%s）' % OPTIONAL_USE.get(m, ''))
            bad += need
    print('  安装（用运行本脚本的同一个解释器）：%s -m pip install numpy matplotlib pillow pymupdf python-docx%s'
          % (sys.executable, ' pywin32' if os.name == 'nt' else ''))

    print('\n[LaTeX 编译器]（可选：PDF 版排版最好；没有也能用 Word 版）')
    engines = {e: shutil.which(e) for e in ('xelatex', 'latexmk', 'perl', 'tectonic', 'kpsewhich')}
    for e, p in engines.items():
        print(' ', OK if p else '-', e, p or '')
    has_latex = bool(engines['xelatex'] or engines['tectonic'])
    try:
        importlib.import_module('docx')
        has_word = True
    except ImportError:
        has_word = False
    if not has_latex and not has_word:
        bad += 1
    if not has_latex:
        sysname = platform.system()
        print('  ! 没有 XeLaTeX：可以先用 Word 版（build_docx.py）。想要排版更好的 PDF，再装 LaTeX：')
        if sysname == 'Windows':
            print('    · MiKTeX（小，缺宏包时自动下载）：winget install MiKTeX.MiKTeX')
            print('    · 或 TeX Live（完整，约 8GB）：https://tug.org/texlive/')
        elif sysname == 'Darwin':
            print('    · brew install --cask mactex-no-gui   或   brew install tectonic')
        else:
            print('    · sudo apt install texlive-xetex texlive-lang-chinese texlive-latex-extra latexmk')
            print('    · 或单文件编译器：https://tectonic-typesetting.github.io')
        print('    · 实在装不了：把整个报告文件夹打包上传 Overleaf，编译器选 XeLaTeX')
    elif engines['latexmk'] and not engines['perl'] and os.name == 'nt':
        print('  ! latexmk 需要 Perl（MiKTeX 下常缺）；build.py 会自动改用 xelatex 跑两遍，不影响使用')

    if engines['kpsewhich']:
        print('\n[宏包]')
        missing = []
        for p in PKGS:
            name = p + ('.cls' if p == 'ctexart' else '.sty')
            try:
                r = subprocess.run(['kpsewhich', name], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30)
                found = bool(r.stdout.strip())
            except Exception:
                found = False
            if not found:
                missing.append(p)
        if missing:
            print(' ', WARN, '没找到：', ', '.join(missing))
            print('    MiKTeX 会在首次编译时自动安装；TeX Live：tlmgr install ' + ' '.join(missing))
        else:
            print(' ', OK, '全部找到（%d 个）' % len(PKGS))

    print('\n[中文字体]')
    try:
        from matplotlib import font_manager
        have = {f.name for f in font_manager.fontManager.ttflist}
        cjk = [f for f in ('SimSun', 'SimHei', 'KaiTi', 'FangSong', 'Songti SC', 'PingFang SC',
                           'Noto Serif CJK SC', 'Noto Sans CJK SC', 'Source Han Serif SC', 'FandolSong')
               if f in have]
        print(' ', OK if cjk else WARN, '、'.join(cjk) or '没找到常见中文字体（ctex 会退回 Fandol 字体，可用但不如宋体）')
        print(' ', OK if 'Times New Roman' in have else WARN, 'Times New Roman',
              '' if 'Times New Roman' in have else '（没有时西文用 TeX Gyre Termes）')
    except ImportError:
        print('  （需要 matplotlib 才能检查字体）')

    modes = (['PDF 版（LaTeX，推荐）'] if has_latex else []) + (['Word 版'] if has_word else [])
    if not bad:
        print('\n结论：可以开始 ✔  可用：%s' % ' + '.join(modes))
    else:
        print('\n结论：还缺 %d 项必需环境，见上方 ✘%s' % (
            bad, '' if modes else '（LaTeX 和 python-docx 至少装一个：pip install python-docx 最快）'))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
