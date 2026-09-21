"""Read current Markdown ADR evidence with bounded, hash-pinned content pages.

Ranges and pagination count Unicode characters, not tokens or UTF-8 bytes.
This is a conservative Markdown index, not an architecture approval engine.
"""
import hashlib
from pathlib import Path
import re

from .provenance import _safe_source

DEFAULT_LIMIT = 8000
MAX_LIMIT = 12000


def _plain(value):
    return value.strip().lstrip('> ').replace('**', '').replace('__', '').strip('`* _')


def _title(value):
    value = _plain(value)
    return re.sub(r'^\d+(?:\.\d+)*[.)]?\s+', '', value).strip().casefold()


def _status(value):
    value = _plain(value)
    if len(value) > 200:
        return None
    match = re.fullmatch(r'(Accepted|Proposed|Deprecated|Rejected|Superseded|Withdrawn)(?:\s+(?:by\b|on\b|[—–(]).*)?',
                         value, re.IGNORECASE)
    if not match:
        return None
    # Preserve superseding references and other source qualifiers.
    return match.group(1).capitalize() + value[len(match.group(1)):]


def _index(text):
    sections, declarations, stack = [], [], []
    fence = None
    pending_status = False
    offset = 0
    lines = text.splitlines(keepends=True)
    for line_no, line in enumerate(lines, 1):
        stripped = line.rstrip('\r\n')
        quote_prefix = re.match(r'^(?: {0,3}> ?)+', stripped)
        quote_depth = quote_prefix[0].count('>') if quote_prefix else 0
        fence_line = stripped[quote_prefix.end():] if quote_prefix else stripped
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', fence_line)
        if fence:
            # A quoted fence marker inside an unquoted fence is literal code.
            if (marker and quote_depth == fence[2] and marker[1][0] == fence[0]
                    and len(marker[1]) >= fence[1] and not marker[2].strip()):
                fence = None
            offset += len(line)
            continue
        if marker:
            fence = (marker[1][0], len(marker[1]), quote_depth)
            offset += len(line)
            continue
        heading = re.match(r'^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$', stripped)
        if heading:
            level, title = len(heading[1]), heading[2]
            while stack and sections[stack[-1]]['level'] >= level:
                previous = sections[stack.pop()]
                previous['end_char'], previous['end_line'] = offset, line_no - 1
            amendment = bool(re.search(r'\bamendments?\b', _title(title))) or any(
                sections[i]['amendment'] for i in stack)
            section = {'title': title, 'level': level, 'start_char': offset,
                       'end_char': len(text), 'start_line': line_no, 'end_line': len(lines),
                       'amendment': amendment}
            sections.append(section)
            stack.append(len(sections) - 1)
            pending_status = _title(title) == 'status' and not amendment
            if pending_status:
                declarations.append({'line': line_no, 'value': '', 'status': None})
        else:
            amendment = any(sections[i]['amendment'] for i in stack)
            plain = _plain(stripped)
            inline = re.match(r'^Status\s*:\s*(.*)$', plain, re.IGNORECASE)
            if not amendment and (inline or (pending_status and plain)):
                value = _plain(inline[1] if inline else plain)
                declaration = {'line': line_no, 'value': value[:200], 'status': _status(value)}
                if pending_status:
                    declarations[-1] = declaration
                else:
                    declarations.append(declaration)
                pending_status = False
        offset += len(line)
    return sections, declarations


def read_context(root, path, sections=(), metadata_only=False, offset=0,
                 limit=DEFAULT_LIMIT, expected_sha256=None):
    """Return index/status evidence plus at most limit selected body characters.

    Repeated section names select every matching heading, including children.
    All amendment sections are additionally included for conservative review.
    A missing requested section is explicit. Offsets refer to the concatenated,
    deduplicated selection; next pages must keep the same selection and hash.
    """
    root = Path(root).resolve()
    if not _safe_source(root, path):
        raise ValueError('UNSAFE_ADR_PATH ' + str(path))
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise ValueError('INVALID_ADR_PAGINATION: offset >= 0; limit 1..12000 characters')
    if expected_sha256 is not None and (not isinstance(expected_sha256, str) or
                                       not re.fullmatch(r'[0-9a-fA-F]{64}', expected_sha256)):
        raise ValueError('INVALID_ADR_HASH')
    raw = (root / path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256.lower():
        raise ValueError('ADR_CHANGED: restart metadata and targeted reads from the current source')
    text = raw.decode('utf-8')
    index, declarations = _index(text)
    values = {d['status'] for d in declarations}
    if not declarations:
        status, state = None, 'missing'
    elif len(values) > 1 or len({d['value'].casefold() for d in declarations}) > 1:
        status, state = None, 'ambiguous'
    elif None in values:
        status, state = None, 'unrecognized'
    else:
        status, state = next(iter(values)), 'known'
    requested = list(sections)
    if any(not isinstance(s, str) or not s.strip() for s in requested):
        raise ValueError('INVALID_ADR_SECTION')
    names = {_title(s) for s in requested}
    missing = [s for s in requested if not any(_title(r['title']) == _title(s) for r in index)]
    ranges = [(s['start_char'], s['end_char']) for s in index
              if _title(s['title']) in names or s['amendment']] if requested else [(0, len(text))]
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    total = sum(end - start for start, end in merged)
    if offset > total:
        raise ValueError('INVALID_ADR_PAGINATION: offset exceeds selected content')
    # Slice only the requested page, including huge single-line sections.
    chunks, position, remaining = [], 0, 0 if metadata_only else limit
    for start, end in merged:
        length = end - start
        skip = max(0, offset - position)
        if skip < length and remaining:
            chunk = text[start + skip:min(end, start + skip + remaining)]
            chunks.append(chunk)
            remaining -= len(chunk)
        position += length
    content = ''.join(chunks)
    more = not metadata_only and offset + len(content) < total
    return {'source': path, 'sha256': digest, 'status': status, 'status_state': state,
            'status_declarations': declarations, 'sections': index,
            'missing_sections': missing, 'selected_ranges': merged,
            'content': content, 'offset': offset, 'limit': limit,
            'next_offset': offset + len(content) if more else None,
            'more': more, 'total_chars': total, 'metadata_only': metadata_only}
