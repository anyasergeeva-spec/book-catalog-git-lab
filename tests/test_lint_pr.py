import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lint_pr import check_card, check_changes

CARD = '# Книга\n\n- **Автор или авторы:** Автор\n- **Год выпуска:** 2026\n\n## Описание\n\nТекст.\n'


class CardTests(unittest.TestCase):
    def test_example_passes(self):
        self.assertEqual(check_card(CARD), [])

    def test_missing_fields_are_reported(self):
        self.assertEqual(len(check_card('текст')), 4)

    def test_empty_description_and_bad_year(self):
        self.assertEqual(len(check_card(CARD.replace('2026', 'год').replace('Текст.', ''))), 2)


class ChangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        (self.root / 'README').write_text('base')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD')
        (self.root / 'books').mkdir()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'candidate')
        return self.git('rev-parse', 'HEAD')

    def test_new_card(self):
        (self.root / 'books' / 'student.md').write_text(CARD)
        head = self.commit()
        self.assertEqual(check_changes(self.root, self.base, head), [])

    def test_extra_file_rejected(self):
        (self.root / 'books' / 'student.md').write_text(CARD)
        (self.root / 'other').write_text('extra')
        self.assertTrue(check_changes(self.root, self.base, self.commit()))

    def test_symlink_rejected(self):
        (self.root / 'books' / 'student.md').symlink_to('../README')
        self.assertTrue(check_changes(self.root, self.base, self.commit()))


if __name__ == '__main__':
    unittest.main()
