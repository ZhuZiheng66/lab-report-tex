# -*- coding: utf-8 -*-
"""跑完 tests/run_examples.py 后，examples/ 下所有文件的 SHA-256 必须不变；没有 LaTeX 也能跑 Word 版。较慢（约 1~2 分钟）。"""
import os
import shutil
import tempfile
import unittest

from helpers import HAS_LATEX, ROOT, has_module, run

import importlib.util

spec = importlib.util.spec_from_file_location('run_examples', os.path.join(ROOT, 'tests', 'run_examples.py'))
run_examples = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_examples)
SCRIPT = os.path.join(ROOT, 'tests', 'run_examples.py')


@unittest.skipUnless(HAS_LATEX and has_module('matplotlib') and has_module('numpy'), '环境依赖缺失，跳过')
class ExamplesDoNotTouchRepo(unittest.TestCase):
    def test_fixture_hashes_unchanged(self):
        before = run_examples.fixture_hashes()
        self.assertTrue(before)
        code, out = run([SCRIPT])
        after = run_examples.fixture_hashes()
        changed = [k for k in set(before) | set(after) if before.get(k) != after.get(k)]
        self.assertEqual(changed, [], '示例文件被改动：%s' % changed)
        self.assertEqual(code, 0, out)


@unittest.skipUnless(has_module('matplotlib') and has_module('docx'), '环境依赖缺失，跳过')
class WithoutLatex(unittest.TestCase):
    def test_word_version_runs_without_latex(self):
        """PATH 里没有 LaTeX：PDF 版跳过，Word 版照常生成，整体通过。"""
        code, out = run([SCRIPT], env={'PATH': ''})
        self.assertEqual(code, 0, out)
        self.assertIn('PDF 版跳过', out)
        self.assertIn('Word 版', out)


class EnvExitCode(unittest.TestCase):
    def test_missing_python_dependency_exit_code(self):
        """缺必需的 Python 包（用一个会报 ImportError 的假 numpy 模拟）：退出码 3，提示“环境依赖缺失”。"""
        tmp = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmp, 'numpy.py'), 'w') as f:
                f.write('raise ImportError("模拟没装 numpy")\n')
            code, out = run([SCRIPT], env={'PYTHONPATH': tmp})
            self.assertEqual(code, 3, out)
            self.assertIn('环境依赖缺失', out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
