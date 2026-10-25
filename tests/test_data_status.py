# -*- coding: utf-8 -*-
"""数据确认状态：不能跳过用户确认，冻结后被改动要能发现。"""
import io
import os
import shutil
import tempfile
import unittest

from helpers import SCRIPTS, run

import data_status  # noqa: E402

DS = os.path.join(SCRIPTS, 'data_status.py')


class DataStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        io.open(os.path.join(self.tmp, 'raw.csv'), 'w', encoding='utf-8').write('x,y\n1,2\n')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ds(self, *args):
        return run([DS] + list(args), cwd=self.tmp)

    def test_missing_file_is_blocking(self):
        self.assertTrue(data_status.check(self.tmp))

    def test_cannot_freeze_without_review(self):
        self.assertEqual(self.ds('add', 'raw.csv')[0], 0)
        code, out = self.ds('freeze', 'raw.csv')
        self.assertNotEqual(code, 0, out)
        self.assertTrue(any('尚未冻结' in p for p in data_status.check(self.tmp)))

    def test_review_needs_confirmation_text(self):
        self.ds('add', 'raw.csv')
        code, _ = self.ds('review', 'raw.csv')            # 缺 --confirmed-by
        self.assertNotEqual(code, 0)

    def test_full_flow_and_tamper_detection(self):
        self.ds('add', 'raw.csv')
        self.assertEqual(self.ds('review', 'raw.csv', '--confirmed-by', '用户：没问题')[0], 0)
        self.assertEqual(self.ds('freeze', 'raw.csv')[0], 0)
        self.assertEqual(data_status.check(self.tmp), [])
        with io.open(os.path.join(self.tmp, 'raw.csv'), 'a', encoding='utf-8') as f:
            f.write('3,4\n')
        probs = data_status.check(self.tmp)
        self.assertTrue(any('SHA-256' in p for p in probs), probs)

    def test_mark_used(self):
        self.ds('add', 'raw.csv')
        self.ds('review', 'raw.csv', '--confirmed-by', '用户确认')
        self.ds('freeze', 'raw.csv')
        data_status.mark_used(self.tmp)
        self.assertEqual(data_status.load(self.tmp)['files']['raw.csv']['status'], 'used_in_report')
        self.assertEqual(data_status.check(self.tmp), [])


if __name__ == '__main__':
    unittest.main()
