"""Verify pinned upstream bytes or explicitly reviewed source patches.

The original lock is the trust anchor; this module never writes or enrolls files.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit


LOCK = '.codex/upstream-lock.json'
LEDGER = '.codex/upstream-patches.json'


def _digest(value, length=64):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-fA-F]{' + str(length) + '}', value) is not None


def _safe_source(root, name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name or ':' in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
        return False
    target = root
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            return False
    return target.resolve().is_relative_to(root)


def _issue_url(value):
    if not isinstance(value, str) or not value.strip() or any(c.isspace() for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except ValueError:
        return False


def verify_upstream(root, pristine=False) -> list[str]:
    """Return integrity errors, accepting exact reviewed patches unless pristine.

    An absent ledger means no approved patches, for existing pristine checkouts.
    A present ledger is fully validated, including records for unchanged sources.
    """
    root = Path(root).resolve()
    errors = []

    def read_json(name):
        try:
            return json.loads((root / name).read_text(encoding='utf-8'))
        except FileNotFoundError:
            errors.append('MISSING ' + name)
        except (ValueError, OSError) as exc:
            errors.append('INVALID_JSON ' + name + ': ' + str(exc))
        return None

    lock = read_json(LOCK)
    if not isinstance(lock, dict) or not isinstance(lock.get('files'), dict):
        return errors or ['INVALID_BASELINE ' + LOCK]
    baseline = lock['files']
    safe_baseline = {}
    for name, digest in baseline.items():
        if not _safe_source(root, name):
            errors.append('INVALID_BASELINE_PATH ' + str(name))
        elif not _digest(digest):
            errors.append('INVALID_BASELINE_HASH ' + name)
        else:
            safe_baseline[name] = digest.lower()

    patches = {}
    ledger_path = root / LEDGER
    if ledger_path.exists() or ledger_path.is_symlink():
        ledger = read_json(LEDGER)
        if not isinstance(ledger, dict):
            errors.append('INVALID_PATCH_LEDGER ' + LEDGER)
        else:
            if type(ledger.get('schema_version')) is not int or ledger['schema_version'] != 1:
                errors.append('INVALID_PATCH_SCHEMA ' + LEDGER)
            commit = lock.get('commit')
            if not _digest(commit, 40) or ledger.get('baseline_commit') != commit:
                errors.append('PATCH_BASELINE_COMMIT_MISMATCH ' + LEDGER)
            records = ledger.get('patches')
            if not isinstance(records, list):
                errors.append('INVALID_PATCH_RECORDS ' + LEDGER)
            else:
                seen = set()
                for index, record in enumerate(records):
                    label = f'{LEDGER}[{index}]'
                    if not isinstance(record, dict):
                        errors.append('INVALID_PATCH_RECORD ' + label)
                        continue
                    name = record.get('path')
                    if not _safe_source(root, name):
                        errors.append('INVALID_PATCH_PATH ' + label)
                        continue
                    before = len(errors)
                    if name in seen:
                        errors.append('DUPLICATE_PATCH_PATH ' + name)
                    seen.add(name)
                    if name not in baseline:
                        errors.append('UNKNOWN_PATCH_PATH ' + name)
                    original = record.get('original_sha256')
                    patched = record.get('patched_sha256')
                    if not _digest(original):
                        errors.append('INVALID_PATCH_ORIGINAL_HASH ' + name)
                    elif original.lower() != safe_baseline.get(name):
                        errors.append('PATCH_BASELINE_HASH_MISMATCH ' + name)
                    if not _digest(patched):
                        errors.append('INVALID_PATCH_HASH ' + name)
                    urls = record.get('issue_urls')
                    if not isinstance(urls, list) or not urls or not all(_issue_url(url) for url in urls):
                        errors.append('INVALID_PATCH_ISSUES ' + name)
                    rationale = record.get('rationale')
                    if not isinstance(rationale, str) or not rationale.strip():
                        errors.append('INVALID_PATCH_RATIONALE ' + name)
                    if len(errors) == before:
                        patches[name] = patched.lower()

    for name, original in safe_baseline.items():
        path = root / name
        if not path.is_file():
            errors.append('UPSTREAM_MISSING ' + name)
            continue
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            errors.append('UPSTREAM_UNREADABLE ' + name + ': ' + str(exc))
            continue
        if actual != original and (pristine or actual != patches.get(name)):
            errors.append('UPSTREAM_CHANGED ' + name)
    return errors
