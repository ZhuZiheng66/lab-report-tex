# -*- coding: utf-8 -*-
"""跑完 tests/run_examples.py 后，examples/ 下所有文件的 SHA-256 必须不变。较慢（约 1~2 分钟）。"""
import os
import unittest

from helpers import HAS_LATEX, ROOT, has_module, run

import importlib.util

spec = importlib.util.spec_from_file_location('run_examples', os.path.join(ROOT, 'tests', 'run_examples.py'))
run_examples = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_examples)


@unittest.skipUnless(HAS_LATEX and has_module('matplotlib') and has_module('numpy'), '环境依赖缺失，跳过')
class ExamplesDoNotTouchRepo(unittest.TestCase):
    def test_fixture_hashes_unchanged(self):
        before = run_examples.fixture_hashes()
        self.assertTrue(before)
        code, out = run([os.path.join(ROOT, 'tests', 'run_examples.py')])
        after = run_examples.fixture_hashes()
        changed = [k for k in set(before) | set(after) if before.get(k) != after.get(k)]
        self.assertEqual(changed, [], '示例文件被改动：%s' % changed)
        self.assertEqual(code, 0, out)


class EnvExitCode(unittest.TestCase):
    def test_missing_dependency_exit_code(self):
        """模拟缺 LaTeX：PATH 置空时应以退出码 3 报“环境依赖缺失”，而不是代码错误。"""
        code, out = run([os.path.join(ROOT, 'tests', 'run_examples.py')], env={'PATH': ''})
        self.assertEqual(code, 3, out)
        self.assertIn('环境依赖缺失', out)


if __name__ == '__main__':
    unittest.main()
