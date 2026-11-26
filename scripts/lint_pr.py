"""Проверка предложенной карточки без выполнения кода из PR."""

import argparse
import re
import subprocess
from pathlib import Path


def check_card(text: str) -> list[str]:
    errors = []
    if not re.search(r'^#\s+\S.+$', text, re.M):
        errors.append('Добавьте название книги заголовком «# Название книги».')
    if not re.search(r'^-\s+\*\*Автор или авторы:\*\*\s+\S.+$', text, re.M):
        errors.append('Укажите автора в строке «- **Автор или авторы:** ...».')
    if not re.search(r'^-\s+\*\*Год выпуска:\*\*\s+\d{4}\s*$', text, re.M):
        errors.append('Укажите год четырьмя цифрами в строке «- **Год выпуска:** ...».')
    description = re.search(r'^##\s+Описание\s*\n(.*?)(?=^#{1,2}\s|\Z)', text, re.M | re.S)
    if not description or not description.group(1).strip():
        errors.append('Добавьте текст после заголовка «## Описание».')
    return errors


def check_changes(root: Path, base: str, head: str) -> list[str]:
    result = subprocess.run(['git', 'diff', '--name-status', '--no-renames', '-z',
                             f'{base}...{head}', '--'], cwd=root, capture_output=True)
    if result.returncode:
        return ['Не удалось сравнить изменения PR с основной веткой.']
    fields = result.stdout.rstrip(b'\0').split(b'\0') if result.stdout else []
    if len(fields) != 2 or fields[0] != b'A':
        return ['PR должен добавлять ровно один новый файл карточки, не изменяя другие файлы.']
    try:
        path = fields[1].decode('utf-8')
    except UnicodeDecodeError:
        return ['Имя файла должно быть в кодировке UTF-8.']
    if not re.fullmatch(r'books/[^/]+\.md', path, re.I):
        return ['Добавьте карточку как Markdown-файл непосредственно в папку books/, например books/login.md.']
    candidate = root / path
    if candidate.is_symlink() or not candidate.is_file():
        return ['Карточка должна быть обычным файлом, а не ссылкой.']
    if candidate.stat().st_size > 65536:
        return ['Карточка слишком велика: предел — 64 КБ.']
    try:
        text = candidate.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return ['Не удалось прочитать карточку как текст UTF-8.']
    return check_card(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('base')
    parser.add_argument('head')
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    errors = check_changes(args.candidate, args.base, args.head)
    for error in errors:
        print(f'::error::{error}')
    if not errors:
        print('Карточка прошла проверку.')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
