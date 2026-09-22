"""Temporary, canonical source fixtures for board integration tests."""
import hashlib


def story(root, epic='combat', name='story-001.md', status='Ready', kind='Logic',
          estimate='4h', label='战斗 Combat', prefix='', suffix='', crlf=False):
    path = root / 'production' / 'epics' / epic / name
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (f'# Story 001: 跳跃 Jump\n\n{prefix}> **Epic**: {label}\n'
            f'> **Status**: {status}\n> **Layer**: Core\n> **Type**: {kind}\n'
            f'> **Estimate**: {estimate}\n> **Manifest Version**: 2026-09-21\n'
            f'> **Last Updated**: 2026-09-21\n{suffix}\n## Context\n'
            '**Status**: Not yet created\n')
    path.write_bytes(text.replace('\n', '\r\n').encode() if crlf else text.encode())
    return path


def sprint(root, text):
    path = root / 'production/sprint-status.yaml'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def file_hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}
