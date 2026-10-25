# -*- coding: utf-8 -*-
"""install.py 不能静默删除用户已有内容。"""
import os
import shutil
import tempfile
import unittest

from helpers import ROOT, run

INSTALL = os.path.join(ROOT, 'install.py')


class InstallSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dest = os.path.join(self.tmp, 'skills')
        self.backups = os.path.join(self.tmp, 'backups')
        self.existing = os.path.join(self.dest, 'lab-report-tex')
        os.makedirs(self.existing)
        self.sentinel = os.path.join(self.existing, 'MY_NOTES.txt')
        with open(self.sentinel, 'w') as f:
            f.write('user content')
        self.env = {'LAB_REPORT_TEX_BACKUP_DIR': self.backups}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_default_refuses_to_overwrite(self):
        code, out = run([INSTALL, '--dest', self.dest], env=self.env)
        self.assertNotEqual(code, 0, out)
        self.assertTrue(os.path.exists(self.sentinel), '默认安装删掉了已有文件')
        self.assertFalse(os.path.exists(os.path.join(self.existing, 'SKILL.md')))
        self.assertIn('--force', out)

    def test_force_backs_up_first(self):
        code, out = run([INSTALL, '--dest', self.dest, '--force'], env=self.env)
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.exists(os.path.join(self.existing, 'SKILL.md')))
        saved = [os.path.join(r, f) for r, _, fs in os.walk(self.backups) for f in fs if f == 'MY_NOTES.txt']
        self.assertEqual(len(saved), 1, '覆盖前没有备份')
        self.assertIn(os.path.dirname(saved[0]), out.replace('/', os.sep), '没有输出备份的实际路径')
        # 备份不能放在 skills 目录里（会被 Agent 当成第二个技能）
        self.assertFalse(os.path.commonpath([saved[0], self.dest]) == self.dest)

    def test_uninstall_requires_yes(self):
        code, out = run([INSTALL, '--dest', self.dest, '--uninstall'], env=self.env)
        self.assertNotEqual(code, 0, out)
        self.assertTrue(os.path.exists(self.sentinel))
        code, out = run([INSTALL, '--dest', self.dest, '--uninstall', '--yes'], env=self.env)
        self.assertEqual(code, 0, out)
        self.assertFalse(os.path.exists(self.existing))
        saved = [f for r, _, fs in os.walk(self.backups) for f in fs if f == 'MY_NOTES.txt']
        self.assertEqual(len(saved), 1, '卸载前没有备份')

    def test_fresh_install(self):
        dest2 = os.path.join(self.tmp, 'fresh')
        code, out = run([INSTALL, '--dest', dest2], env=self.env)
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.exists(os.path.join(dest2, 'lab-report-tex', 'SKILL.md')))


if __name__ == '__main__':
    unittest.main()
