#!/usr/bin/env python3
"""Translate Codex hook events to unchanged CCGS scripts (Python 3.10+).

This is a reviewed, optional project hook, not a sandbox/security boundary.
No input command is ever executed: only fixed, repository-owned scripts run.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude/hooks"
LIFECYCLE = {
    "SessionStart": ("session-start.sh", "detect-gaps.sh"),
    "PreCompact": ("pre-compact.sh",),
    "PostCompact": ("post-compact.sh",),
    "Stop": ("session-stop.sh",),
    "SubagentStart": ("log-agent.sh",),
    "SubagentStop": ("log-agent-stop.sh",),
}
EVENTS = set(LIFECYCLE) | {"PreToolUse", "PostToolUse", "UserPromptSubmit"}
CONTEXT_EVENTS = {"SessionStart", "UserPromptSubmit", "SubagentStart", "PreToolUse", "PostToolUse"}


class BridgeError(ValueError):
    pass


def required_string(value, label):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise BridgeError(f"{label} must be a nonempty string without NUL")
    return value


def run_script(name, payload):
    """Fixed argv; JSON travels only through stdin, never shell interpolation."""
    path = SCRIPTS / name
    if not path.is_file():
        raise BridgeError(f"Missing upstream hook: {name}")
    try:
        result = subprocess.run(
            ["bash", str(path)], cwd=ROOT, input=json.dumps(payload, ensure_ascii=False),
            capture_output=True, text=True, timeout=20, encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BridgeError(f"Could not run {name}: {exc}") from exc
    # Many original scripts deliberately send advisory warnings to stderr at exit 0.
    message = "\n".join(x.strip() for x in (result.stdout, result.stderr) if x.strip())
    if result.returncode and not message:
        message = f"{name} failed with exit {result.returncode}"
    return result.returncode, message


def project_path(path, cwd):
    path = required_string(path, "file path").replace("\\", "/")
    resolved = (Path(cwd) / path).resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise BridgeError("File path is outside this bridge's repository; validate in its owning project") from exc


def patch_paths(command, cwd):
    lines = command.strip().splitlines()
    if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise BridgeError("apply_patch tool_input.command must contain a complete raw patch")
    paths = []
    operation = None
    for line in lines[1:-1]:
        match = re.match(r"^\*\*\* (Add File|Update File|Delete File|Move to): (.+)$", line)
        if match:
            kind, path = match.groups()
            if kind == "Move to" and operation != "Update File":
                raise BridgeError("Patch Move to requires a preceding Update File")
            if kind != "Move to":
                operation = kind
            paths.append(project_path(path, cwd))
        elif line.startswith("*** ") and line != "*** End of File":
            raise BridgeError("Unsupported or malformed patch header")
    if not paths:
        raise BridgeError("Patch contains no file operations")
    return list(dict.fromkeys(paths))


def rule_context(paths):
    selected = []
    for rule in sorted((ROOT / ".claude/rules").glob("*.md")):
        text = rule.read_text(encoding="utf-8")
        # Upstream metadata uses a simple quoted paths list; bodies remain verbatim.
        header = text.split("---", 2)[1] if text.startswith("---\n") else ""
        patterns = re.findall(r'^\s+-\s+[\"\']([^\"\']+)[\"\']\s*$', header, re.MULTILINE)
        if not patterns or any(fnmatch.fnmatchcase(path, pattern) for path in paths for pattern in patterns):
            selected.append(f"Applicable original rule: {rule.relative_to(ROOT)}\n{text}")
    return "\n\n".join(selected)


def denied(payload, command):
    settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    tool = payload["tool_name"]
    for entry in settings.get("permissions", {}).get("deny", []):
        match = re.fullmatch(r"([^()]+)\((.*)\)", entry)
        if not match:
            continue
        name, pattern = match.groups()
        if name == "Bash" and tool == "Bash":
            # Claude deny patterns use * as wildcard, not fnmatch character classes.
            regex = re.escape(pattern).replace(r"\*", ".*")
            if re.fullmatch(regex, command.lstrip(), re.DOTALL):
                return f"Original repository deny rule matched: {entry}"
        elif name == "Read" and tool == "Read":
            path = required_string(payload["tool_input"].get("file_path"), "tool_input.file_path").replace("\\", "/")
            if fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(path, pattern.removeprefix("**/")):
                return f"Original repository deny rule matched: {entry}"
    return ""


def checkpoint_path(payload):
    session = payload.get("session_id", "unspecified")
    required_string(session, "session_id")
    key = hashlib.sha256(session.encode()).hexdigest()[:24]
    return ROOT / "production/session-state" / f"codex-checkpoint-{key}.md"


def write_checkpoint(payload, text):
    target = checkpoint_path(payload)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Each session gets its own atomic snapshot; active.md stays owned by the agent.
    fd, temporary = tempfile.mkstemp(prefix=".codex-checkpoint-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text + "\n")
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target.relative_to(ROOT).as_posix()


def recovery_context(payload):
    chunks = []
    for path in (ROOT / "production/session-state/active.md", checkpoint_path(payload)):
        if path.is_file():
            chunks.append(f"Recovery file: {path.relative_to(ROOT)}\n{path.read_text(encoding='utf-8')}")
    if chunks:
        chunks.insert(0, "Restore context from these file-backed notes; verify the working tree before continuing.")
    return "\n\n".join(chunks)


def output(event, messages, failure=False):
    text = "\n\n".join(message for message in messages if message)
    result = {}
    if text and event in CONTEXT_EVENTS:
        result["hookSpecificOutput"] = {"hookEventName": event, "additionalContext": text}
    elif text:
        result["systemMessage"] = text
    if failure:
        if event == "PreToolUse":
            result.setdefault("hookSpecificOutput", {"hookEventName": event}).update(
                permissionDecision="deny", permissionDecisionReason=text)
        elif event in {"PostToolUse", "UserPromptSubmit", "Stop", "SubagentStop"}:
            result.update(decision="block", reason=text)
        elif event in {"SessionStart", "PreCompact", "PostCompact"}:
            result.update({"continue": False, "stopReason": text})
    return result


def dispatch(event, payload):
    if event not in EVENTS:
        raise BridgeError(f"Unsupported hook event: {event}")
    if not isinstance(payload, dict):
        raise BridgeError("Hook input must be one JSON object")
    if payload.get("hook_event_name", event) != event:
        raise BridgeError("hook_event_name does not match bridge event argument")
    messages = []
    failed = False
    jobs = []
    if event in {"PreToolUse", "PostToolUse"}:
        tool = required_string(payload.get("tool_name"), "tool_name")
        arguments = payload.get("tool_input")
        if not isinstance(arguments, dict):
            raise BridgeError("tool_input must be an object")
        command = ""
        if tool in {"Bash", "apply_patch"}:
            command = required_string(arguments.get("command"), "tool_input.command")
        if event == "PreToolUse":
            reason = denied(payload, command)
            if reason:
                return output(event, [reason], True), 2
        if tool == "Bash" and event == "PreToolUse":
            for verb, script in (("commit", "validate-commit.sh"), ("push", "validate-push.sh")):
                if re.match(r"^git\s+" + verb + r"(?:\s|$)", command):
                    jobs.append((script, payload))
        elif tool == "apply_patch" or tool in {"Write", "Edit"}:
            cwd = required_string(payload.get("cwd", str(ROOT)), "cwd")
            paths = patch_paths(command, cwd) if tool == "apply_patch" else [project_path(arguments.get("file_path"), cwd)]
            if event == "PreToolUse":
                messages.append(rule_context(paths))
            else:
                for path in paths:
                    translated = {**payload, "tool_name": "Edit", "tool_input": {"file_path": path}}
                    if re.search(r"(^|/)assets/", path):
                        jobs.append(("validate-assets.sh", translated))
                    if re.search(r"(^|/)\.claude/skills/", path):
                        jobs.append(("validate-skill-change.sh", translated))
    else:
        if event in {"SubagentStart", "SubagentStop"}:
            required_string(payload.get("agent_type", "unknown"), "agent_type")
        jobs = [(script, payload) for script in LIFECYCLE.get(event, ())]
    for script, translated in jobs:
        code, message = run_script(script, translated)
        messages.append(message)
        failed = failed or code != 0
    if event == "PreCompact":
        path = write_checkpoint(payload, "\n\n".join(messages))
        notice = f"Saved CCGS recovery checkpoint to {path}. SessionStart/UserPromptSubmit restores it."
        messages = [notice, *messages] if failed else [notice]
    if event in {"SessionStart", "UserPromptSubmit"}:
        messages.append(recovery_context(payload))
    return output(event, messages, failed), 2 if failed else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    event = argv[0] if len(argv) == 1 else "Unknown"
    try:
        payload = json.load(sys.stdin)
        result, code = dispatch(event, payload)
    except (BridgeError, OSError, ValueError, TypeError, KeyError) as exc:
        result = output(event, [f"CCGS hook bridge error: {exc}"], True)
        code = 2
    print(json.dumps(result, ensure_ascii=False))
    if code:
        print(result.get("reason") or result.get("stopReason") or result.get("hookSpecificOutput", {}).get("permissionDecisionReason") or result.get("systemMessage") or "CCGS hook failed", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
