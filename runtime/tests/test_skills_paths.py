"""Tests for skills.paths -- path discovery and parsing."""

from __future__ import annotations

from pathlib import Path

from ailine_runtime.skills.paths import (
    default_skill_source_paths,
    find_repo_root,
    get_skill_source_paths,
    parse_skill_source_paths,
)


class TestFindRepoRoot:
    def test_finds_repo_root(self):
        root = find_repo_root()
        assert isinstance(root, Path)

    def test_with_explicit_start(self, tmp_path):
        """When start path has no docs/runtime, falls back to parents[4]."""
        root = find_repo_root(start=tmp_path / "deep" / "nested" / "file.py")
        assert isinstance(root, Path)


class TestDefaultSkillSourcePaths:
    def test_returns_existing_dirs(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        claude_skills = tmp_path / ".claude" / "skills"
        claude_skills.mkdir(parents=True)
        paths = default_skill_source_paths(repo_root=tmp_path)
        posix_paths = [p.replace("\\", "/") for p in paths]
        assert any("skills" in p for p in posix_paths)

    def test_returns_empty_when_no_dirs(self, tmp_path):
        paths = default_skill_source_paths(repo_root=tmp_path)
        assert paths == []


class TestParseSkillSourcePaths:
    def test_parses_comma_separated(self):
        paths = parse_skill_source_paths("/path/a,/path/b")
        assert paths == ["/path/a", "/path/b"]

    def test_normalizes_backslashes(self):
        paths = parse_skill_source_paths("C:\\path\\a,C:\\path\\b")
        assert paths == ["C:/path/a", "C:/path/b"]

    def test_strips_whitespace(self):
        paths = parse_skill_source_paths("  /path/a , /path/b  ")
        assert paths == ["/path/a", "/path/b"]

    def test_empty_returns_defaults(self, tmp_path):
        paths = parse_skill_source_paths("", repo_root=tmp_path)
        assert isinstance(paths, list)

    def test_none_returns_defaults(self, tmp_path):
        paths = parse_skill_source_paths(None, repo_root=tmp_path)
        assert isinstance(paths, list)

    def test_whitespace_only_returns_defaults(self, tmp_path):
        paths = parse_skill_source_paths("   ", repo_root=tmp_path)
        assert isinstance(paths, list)


class TestGetSkillSourcePaths:
    def test_returns_list(self):
        paths = get_skill_source_paths()
        assert isinstance(paths, list)
