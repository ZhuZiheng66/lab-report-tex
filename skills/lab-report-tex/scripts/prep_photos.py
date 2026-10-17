# -*- coding: utf-8 -*-
"""把原始数据 / 预习试卷照片整理成可直接放进 LaTeX 的图片：按 EXIF 转正、可再旋转、压缩。

LaTeX（xdvipdfmx）不认 EXIF 方向标记，手机竖拍的照片不处理会躺着，所以照片一律先过这一步。
只做旋转和等比缩放，**不改照片内容**（不裁剪、不调色、不修图）。

用法：
  python prep_photos.py 原始数据1.jpg 原始数据2.jpg@90 --out raw --prefix raw
  python prep_photos.py 扫描件.pdf --out raw --prefix scan        # PDF 每页转成一张 JPG
  · 文件名后加 @90 / @180 / @270 表示再顺时针旋转该角度
输出：raw/raw1.jpg raw/raw2.jpg …，并打印可以直接粘进 report.tex 的 \\labphotos{...}{...}
"""
import argparse
import os
import re
import sys

from PIL import Image, ImageOps

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def pdf_pages(path):
    try:
        import fitz
    except ImportError:
        raise SystemExit('处理 PDF 需要 PyMuPDF：pip install pymupdf')
    doc = fitz.open(path)
    for pg in doc:
        pix = pg.get_pixmap(dpi=200)
        yield Image.frombytes('RGB', (pix.width, pix.height), pix.samples)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('--out', default='raw')
    ap.add_argument('--prefix', default='raw')
    ap.add_argument('--max', type=int, default=2400, help='长边像素上限')
    ap.add_argument('--quality', type=int, default=88)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    made = []
    for spec in a.inputs:
        path, rot = spec, 0
        m = re.match(r'^(.*)@(90|180|270)$', spec)
        if m:
            path, rot = m.group(1), int(m.group(2))
        if path.lower().endswith('.pdf'):
            images = list(pdf_pages(path))
        else:
            images = [ImageOps.exif_transpose(Image.open(path))]
        for im in images:
            im = im.convert('RGB')
            if rot:
                im = im.rotate(-rot, expand=True)
            im.thumbnail((a.max, a.max), Image.LANCZOS)
            name = '%s%d.jpg' % (a.prefix, len(made) + 1)
            dst = os.path.join(a.out, name)
            im.save(dst, 'JPEG', quality=a.quality, optimize=True)
            note = '  ⚠ 横向，确认是否需要 @90/@270' if im.width > im.height else ''
            print('%s → %s  %dx%d%s' % (os.path.basename(path), dst, im.width, im.height, note))
            made.append(dst.replace(os.sep, '/'))
    print()
    print('\\labphotos{原始数据}{%s}' % ','.join(made))


if __name__ == '__main__':
    main()
