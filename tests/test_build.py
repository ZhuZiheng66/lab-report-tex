# -*- coding: utf-8 -*-
"""build.py：验收不通过时，正式输出目录里不能出现 PDF。需要本机有 XeLaTeX。"""
import io
import os
import shutil
import tempfile
import unittest

from helpers import HAS_LATEX, SCRIPTS, run

BUILD = os.path.join(SCRIPTS, 'build.py')
DS = os.path.join(SCRIPTS, 'data_status.py')

GOOD_BODY = r'''
\begin{labsection}{实验目的}
测量某个量。
\end{labsection}
\begin{labsection}{数据记录和处理}
结果 $k=\KVal$。
\end{labsection}
\labgrading{预习/20,操作及记录/40,数据处理与结果陈述/30,思考题/10}
'''


def report(body=GOOD_BODY, author='张三', extra_input=''):
    return r'''\documentclass{labreport}
\input{results.tex}
%s
\labset{
  school  = {测试大学},
  expname = {测试实验},
  author  = {%s},
  date    = {2026年10月1日},
}
\begin{document}
\makecover
%s
\end{document}
''' % (extra_input, author, body)


@unittest.skipUnless(HAS_LATEX, '本机没有 XeLaTeX/tectonic，跳过编译测试')
class BuildGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        w = lambda name, s: io.open(os.path.join(self.tmp, name), 'w', encoding='utf-8').write(s)  # noqa: E731
        w('raw.csv', 'x\n1\n')
        w('results.tex', '\\def\\KVal{1.234}%  test\n')
        run([DS, 'add', 'raw.csv'], cwd=self.tmp)
        run([DS, 'review', 'raw.csv', '--confirmed-by', '测试：模拟用户确认'], cwd=self.tmp)
        run([DS, 'freeze', 'raw.csv'], cwd=self.tmp)
        self.out = os.path.join(self.tmp, 'out')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self, tex, *extra):
        io.open(os.path.join(self.tmp, 'report.tex'), 'w', encoding='utf-8').write(tex)
        code, out = run([BUILD, 'report.tex', '--outdir', 'out', '--require', '实验目的,数据记录和处理,成绩评定']
                        + list(extra), cwd=self.tmp)
        pdfs = [f for f in os.listdir(self.out) if f.endswith('.pdf')] if os.path.isdir(self.out) else []
        return code, out, pdfs

    def assert_blocked(self, code, out, pdfs, reason, candidate=True):
        self.assertEqual(code, 2, out)
        self.assertEqual(pdfs, [], '验收失败却在正式目录输出了 PDF')
        self.assertIn(reason, out)
        if candidate:
            self.assertTrue(os.listdir(os.path.join(self.tmp, 'build', 'candidate')), '应该留下候选 PDF')

    def test_pass(self):
        code, out, pdfs = self.build(report())
        self.assertEqual(code, 0, out)
        self.assertEqual(pdfs, ['测试实验.pdf'])

    def test_missing_section(self):
        body = GOOD_BODY.replace('\\begin{labsection}{实验目的}\n测量某个量。\n\\end{labsection}', '')
        self.assert_blocked(*self.build(report(body)), reason='缺失')

    def test_todo(self):
        self.assert_blocked(*self.build(report(GOOD_BODY.replace('测量某个量。', '测量某个量。TODO'))), reason='TODO')

    def test_empty_cover_field(self):
        self.assert_blocked(*self.build(report(author='')), reason='封面信息为空')

    def test_hand_copied_number(self):
        self.assert_blocked(*self.build(report(GOOD_BODY.replace('$k=\\KVal$', '$k=1.234$'))), reason='手写了 1.234')

    def test_missing_input(self):
        code, out, pdfs = self.build(report(extra_input='\\input{tab/none.tex}'))
        self.assert_blocked(code, out, pdfs, reason='\\input 的文件不存在', candidate=False)
        self.assertIn('none.tex', out, '应给出缺失文件的路径')

    def test_unfrozen_data(self):
        with io.open(os.path.join(self.tmp, 'raw.csv'), 'a', encoding='utf-8') as f:
            f.write('2\n')
        self.assert_blocked(*self.build(report()), reason='SHA-256')

    def test_requirements_figure(self):
        io.open(os.path.join(self.tmp, 'requirements.md'), 'w', encoding='utf-8').write('- 图：fig/a.pdf\n- 表：tab/t.tex\n')
        code, out, pdfs = self.build(report())
        self.assert_blocked(code, out, pdfs, reason='需求清单要求的图不存在')
        self.assertIn('需求清单要求的表不存在', out)


if __name__ == '__main__':
    unittest.main()
