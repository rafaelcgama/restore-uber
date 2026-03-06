"""
tests/test_utils.py

Unit tests for utils.utils:
  - write_file / open_file (JSON and TXT)
  - rename_file
  - remove_duplicates
  - normalize_string
  - get_folder_files
  - create_path

Uses tmp_path (pytest's built-in temporary directory fixture) — no permanent
files are created on disk.
"""
import json
import pytest
from pathlib import Path

from utils.utils import (
    write_file,
    open_file,
    rename_file,
    remove_duplicates,
    normalize_string,
    get_folder_files,
    create_path,
)


# ── write_file / open_file ────────────────────────────────────────────────────

class TestWriteAndOpenFileJSON:
    def test_write_creates_json_file(self, tmp_path):
        data = [{'name': 'Alice', 'position': 'Engineer'}]
        path = str(tmp_path / 'test.json')
        write_file(data, path)
        assert Path(path).exists()

    def test_written_json_is_parseable(self, tmp_path):
        data = [{'name': 'Alice', 'position': 'Engineer'}]
        path = str(tmp_path / 'test.json')
        write_file(data, path)
        with open(path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded == data

    def test_open_file_json_roundtrip(self, tmp_path):
        data = [{'a': 1}, {'b': 2}]
        path = str(tmp_path / 'rt.json')
        write_file(data, path)
        result = open_file(path)
        assert result == data

    def test_write_empty_list(self, tmp_path):
        path = str(tmp_path / 'empty.json')
        write_file([], path)
        assert open_file(path) == []

    def test_write_unicode_characters(self, tmp_path):
        data = [{'name': 'São Paulo', 'position': 'Engenheiro'}]
        path = str(tmp_path / 'unicode.json')
        write_file(data, path)
        result = open_file(path)
        assert result[0]['name'] == 'São Paulo'


class TestWriteAndOpenFileTXT:
    def test_write_txt_creates_file(self, tmp_path):
        path = str(tmp_path / 'test.txt')
        write_file('hello world', path)
        assert Path(path).exists()

    def test_open_txt_roundtrip(self, tmp_path):
        path = str(tmp_path / 'msg.txt')
        write_file('Hello $PERSON_NAME', path)
        result = open_file(path)
        assert result == 'Hello $PERSON_NAME'


# ── rename_file ───────────────────────────────────────────────────────────────

class TestRenameFile:
    def test_renames_and_writes_new_data(self, tmp_path):
        old_path = str(tmp_path / 'old.json')
        new_path = str(tmp_path / 'new.json')
        write_file([{'x': 1}], old_path)

        new_data = [{'x': 2}]
        rename_file(new_data, old_path, new_path)

        assert not Path(old_path).exists()
        assert Path(new_path).exists()
        assert open_file(new_path) == new_data

    def test_noop_when_old_path_missing(self, tmp_path):
        """Should not raise when the source file does not exist."""
        rename_file([], str(tmp_path / 'ghost.json'), str(tmp_path / 'dest.json'))
        assert not Path(tmp_path / 'dest.json').exists()


# ── remove_duplicates ─────────────────────────────────────────────────────────

class TestRemoveDuplicates:
    def test_removes_exact_duplicates(self):
        data = [
            {'name': 'Alice', 'position': 'Engineer'},
            {'name': 'Alice', 'position': 'Engineer'},
            {'name': 'Bob', 'position': 'Manager'},
        ]
        result = remove_duplicates(data)
        assert len(result) == 2

    def test_preserves_order(self):
        data = [{'name': 'B'}, {'name': 'A'}, {'name': 'B'}]
        result = remove_duplicates(data)
        assert [r['name'] for r in result] == ['B', 'A']

    def test_empty_list(self):
        assert remove_duplicates([]) == []

    def test_no_duplicates_unchanged(self):
        data = [{'name': 'Alice'}, {'name': 'Bob'}]
        result = remove_duplicates(data)
        assert len(result) == 2

    def test_all_duplicates_returns_one(self):
        data = [{'k': 'v'}, {'k': 'v'}, {'k': 'v'}]
        result = remove_duplicates(data)
        assert len(result) == 1


# ── normalize_string ──────────────────────────────────────────────────────────

class TestNormalizeString:
    def test_lowercases(self):
        assert normalize_string('HELLO') == 'hello'

    def test_strips_accents(self):
        assert normalize_string('São Paulo') == 'sao paulo'

    def test_strips_multiple_accents(self):
        assert normalize_string('Ñoño') == 'nono'

    def test_already_normalised(self):
        assert normalize_string('hello world') == 'hello world'

    def test_empty_string(self):
        assert normalize_string('') == ''


# ── get_folder_files ──────────────────────────────────────────────────────────

class TestGetFolderFiles:
    def test_returns_json_files(self, tmp_path):
        """Verify that .json files are found when filtering for 'json'.

        Note: get_folder_files matches 'file_type' as a substring of the full
        normalised path — not strictly as a file extension. Negative assertions
        ("this other file is NOT returned") are unreliable because the pytest
        temp directory path itself may contain the substring. We therefore only
        assert that the expected files ARE included.
        """
        (tmp_path / 'alice.json').write_text('[]')
        (tmp_path / 'bob.json').write_text('[]')
        result = get_folder_files(str(tmp_path), ['json'])
        basenames = [Path(p).name for p in result]
        assert 'alice.json' in basenames
        assert 'bob.json' in basenames

    def test_returns_txt_files(self, tmp_path):
        """Verify that .txt files are found when filtering for 'txt'.

        See test_returns_json_files for a note on why negative assertions are
        omitted.
        """
        (tmp_path / 'note.txt').write_text('hi')
        result = get_folder_files(str(tmp_path), ['txt'])
        basenames = [Path(p).name for p in result]
        assert 'note.txt' in basenames

    def test_returns_empty_for_nonexistent_folder(self, tmp_path):
        result = get_folder_files(str(tmp_path / 'ghost'), ['json'])
        assert result == []

    def test_returns_empty_for_empty_folder(self, tmp_path):
        result = get_folder_files(str(tmp_path), ['json'])
        assert result == []

    def test_multiple_extensions(self, tmp_path):
        (tmp_path / 'a.json').write_text('[]')
        (tmp_path / 'b.txt').write_text('hi')
        (tmp_path / 'c.csv').write_text('x,y')
        result = get_folder_files(str(tmp_path), ['json', 'txt'])
        basenames = [Path(p).name for p in result]
        assert 'a.json' in basenames
        assert 'b.txt' in basenames
        assert 'c.csv' not in basenames


# ── create_path ───────────────────────────────────────────────────────────────

class TestCreatePath:
    def test_includes_date_prefix(self, tmp_path):
        path = create_path(filename='data.json', folder=str(tmp_path))
        name = Path(path).name
        # Date prefix format: YYYY-MM-DD_data.json
        import re
        assert re.match(r'\d{4}-\d{2}-\d{2}_data\.json', name)

    def test_final_mode_strips_page_suffix(self, tmp_path):
        """In final mode the _page_N suffix should be removed."""
        path = create_path(
            filename='sf_uber_page_10.json',
            folder=str(tmp_path),
            final=True,
        )
        assert 'page' not in Path(path).name

    def test_final_mode_keeps_base_name(self, tmp_path):
        path = create_path(
            filename='sf_uber_page_10.json',
            folder=str(tmp_path),
            final=True,
        )
        assert 'sf_uber' in path

    def test_creates_folder_if_missing(self, tmp_path):
        new_folder = str(tmp_path / 'new_dir')
        create_path(filename='data.json', folder=new_folder)
        assert Path(new_folder).is_dir()
