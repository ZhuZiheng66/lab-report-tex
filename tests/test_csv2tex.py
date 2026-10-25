# -*- coding: utf-8 -*-
"""csv2tex 默认必须安全转义表题、表头、数据单元格。"""
import io
import json
import os
import shutil
import tempfile
import unittest

from helpers import SCRIPTS, run

import csv2tex  # noqa: E402

NASTY = r'a_b {c} $d$ ^e \input{x} 50% #1 & ~f'


def is_safe(tex_fragment):
    """转义后不能残留未转义的特殊字符（\\开头的转义序列除外）。"""
    s = tex_fragment
    for esc in (r'\textbackslash{}', r'\textasciicircum{}', r'\textasciitilde{}', r'\{', r'\}', r'\$', r'\&',
                r'\%', r'\#', r'\_'):
        s = s.replace(esc, '')
    return not any(ch in s for ch in '\\{}$&%#_^~')


class Escape(unittest.TestCase):
    def test_escape_function(self):
        self.assertTrue(is_safe(csv2tex.escape(NASTY)))
        self.assertIn(r'\textbackslash{}input\{x\}', csv2tex.escape(NASTY))

    def test_caption_header_and_cells(self):
        rows = [[NASTY, 'I_{f}/A'], [NASTY, '0.40'], ['-1.25', '2^3']]
        tex, _, _ = csv2tex.build(rows, caption=NASTY)
        cap = tex.split('\\labtable{', 1)[1].split('}[', 1)[0].split('}{', 1)[0]
        # 表题
        self.assertIn(csv2tex.escape(NASTY), tex.split('\n')[1])
        self.assertNotIn(r'\input{x}', tex)
        lines = tex.splitlines()
        header = next(l for l in lines if 'I' in l and '&' in l)
        data = [l for l in lines if '0.40' in l][0]
        for part in header.rstrip(' \\').split(' & ') + data.rstrip(' \\').split(' & '):
            self.assertTrue(is_safe(part), part)
        self.assertIn('0.40', data, '数值的有效数字被改动')
        self.assertIn('$-1.25$', tex, '负数应排成数学减号')
        self.assertTrue(cap)

    def test_raw_latex_only_header_and_caption(self):
        rows = [['$I_\\mathrm{f}$/A'], ['$x$']]
        tex, _, _ = csv2tex.build(rows, caption='$\\lg I$', raw_latex=True)
        self.assertIn('$I_\\mathrm{f}$/A', tex)
        self.assertIn('{$\\lg I$}', tex)
        self.assertIn(r'\$x\$', tex, '数据单元格在 --raw-latex 下也必须转义')

    def test_math_shorthand_is_safe(self):
        out = csv2tex.cell('I_{f}/A √U_{a} x_{\\evil}', shorthand=True)
        self.assertIn('$I_{f}$', out)
        self.assertIn('$\\sqrt{U_{a}}$', out)
        self.assertNotIn('\\evil}', out.replace('\\textbackslash{}evil\\}', ''))

    def test_bad_label_and_cols_rejected(self):
        with self.assertRaises(SystemExit):
            csv2tex.build([['a'], ['1']], 'c', label='x}\\input{y')
        with self.assertRaises(SystemExit):
            csv2tex.build([['a'], ['1']], 'c', cols='c}\\input{y')

    def test_cli_writes_meta(self):
        tmp = tempfile.mkdtemp()
        try:
            p = os.path.join(tmp, 'd.csv')
            io.open(p, 'w', encoding='utf-8').write('h\n1\n')
            code, out = run([os.path.join(SCRIPTS, 'csv2tex.py'), 'd.csv', '--caption', 'c', '--out', 'tab/t.tex'],
                            cwd=tmp)
            self.assertEqual(code, 0, out)
            meta = json.load(io.open(os.path.join(tmp, 'results.meta.json'), encoding='utf-8'))
            rec = meta['entries']['tab/t.tex'][-1]
            self.assertEqual(rec['inputs'][0]['path'], 'd.csv')
            self.assertEqual(len(rec['inputs'][0]['sha256']), 64)
            for k in ('script', 'argv', 'skill_version', 'time'):
                self.assertIn(k, rec)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
