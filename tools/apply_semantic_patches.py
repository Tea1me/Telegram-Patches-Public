#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from dataclasses import dataclass


HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


@dataclass
class Hunk:
    path: str
    old_start: int
    new_start: int
    old_count: int
    new_count: int
    lines: list[str]

    def old_lines(self) -> list[str]:
        result: list[str] = []
        for line in self.lines:
            prefix = line[0]
            if prefix in (" ", "-"):
                result.append(line[1:].rstrip("\n"))
            elif prefix in ("+", "\\"):
                pass
            else:
                raise RuntimeError(f"Unexpected hunk line: {line!r}")
        return result

    def new_text(self) -> str:
        out: list[str] = []
        for line in self.lines:
            prefix = line[0]
            if prefix in (" ", "+"):
                out.append(line[1:])
            elif prefix in ("-", "\\"):
                pass
            else:
                raise RuntimeError(f"Unexpected hunk line: {line!r}")
        return "".join(out)


def run(args: list[str], cwd: Path, capture: bool = False) -> str:
    print("+", " ".join(args))
    p = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    if p.returncode != 0:
        if capture and p.stdout:
            print(p.stdout)
        raise RuntimeError(
            f"Command failed ({p.returncode}): {' '.join(args)}"
        )
    return (p.stdout or "").strip()


def normalize_lf(data: bytes) -> str:
    return (
        data.decode("utf-8-sig")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def normalize_code_line(line: str) -> str:
    # Keep leading whitespace exact because indentation is meaningful
    # for our audit. Ignore only trailing horizontal whitespace.
    return line.rstrip(" \t")


def parse_patch(path: Path) -> list[Hunk]:
    text = normalize_lf(path.read_bytes())
    lines = text.splitlines(keepends=True)

    target_path: str | None = None
    current: Hunk | None = None
    hunks: list[Hunk] = []

    def finish() -> None:
        nonlocal current
        if current is None:
            return

        old_actual = sum(
            1 for line in current.lines
            if line and line[0] in (" ", "-")
        )
        new_actual = sum(
            1 for line in current.lines
            if line and line[0] in (" ", "+")
        )

        if old_actual != current.old_count or new_actual != current.new_count:
            raise RuntimeError(
                f"{path.name}: malformed hunk in {current.path}: "
                f"header {current.old_count}/{current.new_count}, "
                f"body {old_actual}/{new_actual}"
            )

        hunks.append(current)
        current = None

    for raw in lines:
        if raw.startswith("diff --git "):
            finish()
            target_path = None
            continue

        if current is None and raw.startswith("+++ b/"):
            target_path = raw[6:].rstrip("\n")
            continue

        match = HUNK_RE.match(raw)
        if match:
            finish()

            if not target_path:
                raise RuntimeError(
                    f"{path.name}: hunk before target file header"
                )

            current = Hunk(
                path=target_path,
                old_start=int(match.group("old_start")),
                new_start=int(match.group("new_start")),
                old_count=int(match.group("old_count") or "1"),
                new_count=int(match.group("new_count") or "1"),
                lines=[],
            )
            continue

        if current is not None:
            if raw.startswith((" ", "+", "-", "\\")):
                current.lines.append(raw)
            elif raw.strip() == "":
                finish()
            else:
                raise RuntimeError(
                    f"{path.name}: unexpected line inside hunk: {raw!r}"
                )

    finish()

    if not hunks:
        raise RuntimeError(f"{path.name}: no hunks parsed")

    return hunks


def excerpt(lines: list[str], center: int, radius: int = 10) -> str:
    lo = max(1, center - radius)
    hi = min(len(lines), center + radius)

    return "\n".join(
        f"{n:6d}: {lines[n - 1]}"
        for n in range(lo, hi + 1)
    )


def contiguous_matches(
    source_lines: list[str],
    expected_lines: list[str],
) -> list[tuple[int, int]]:
    """
    Strict line-by-line matching, ignoring only trailing spaces/tabs.
    Returns [start, end) line-index spans.
    """
    expected = [normalize_code_line(x) for x in expected_lines]
    source = [normalize_code_line(x) for x in source_lines]

    width = len(expected)
    result: list[tuple[int, int]] = []

    if width == 0:
        return result

    for start in range(0, len(source) - width + 1):
        if source[start:start + width] == expected:
            result.append((start, start + width))

    return result


def blank_tolerant_matches(
    source_lines: list[str],
    expected_lines: list[str],
) -> list[tuple[int, int]]:
    """
    Fallback:
    - code lines must still match exactly after trimming only trailing
      horizontal whitespace;
    - pure blank lines may be inserted/removed between code lines;
    - no nonblank source line may be skipped.

    This is intentionally much stricter than a fuzzy patch matcher.
    """
    expected_nonblank = [
        normalize_code_line(line)
        for line in expected_lines
        if normalize_code_line(line) != ""
    ]

    if not expected_nonblank:
        return []

    source_norm = [normalize_code_line(line) for line in source_lines]
    result: list[tuple[int, int]] = []

    for start in range(len(source_norm)):
        if source_norm[start] != expected_nonblank[0]:
            continue

        src = start
        exp = 0
        last_match = start
        failed = False

        while exp < len(expected_nonblank):
            wanted = expected_nonblank[exp]

            if src >= len(source_norm):
                failed = True
                break

            current = source_norm[src]

            if current == wanted:
                last_match = src
                exp += 1
                src += 1
                continue

            if current == "":
                src += 1
                continue

            failed = True
            break

        if not failed and exp == len(expected_nonblank):
            result.append((start, last_match + 1))

    # Deduplicate identical spans.
    return sorted(set(result))


def nearest_diagnostic(
    source_lines: list[str],
    expected_lines: list[str],
    expected_start: int,
) -> str:
    expected_nonblank = [
        normalize_code_line(line)
        for line in expected_lines
        if normalize_code_line(line) != ""
    ]

    first = expected_nonblank[0] if expected_nonblank else ""

    candidates = [
        i + 1
        for i, line in enumerate(source_lines)
        if normalize_code_line(line) == first
    ]

    out = [
        f"Expected first code line: {first!r}",
        f"Candidate line(s) for first code line: {candidates or 'none'}",
        "",
        "Source around hunk's declared location:",
        "-" * 72,
        excerpt(source_lines, expected_start),
        "-" * 72,
    ]

    if candidates:
        nearest = min(candidates, key=lambda n: abs(n - expected_start))
        out.extend([
            "",
            f"Source around nearest first-line candidate ({nearest}):",
            "-" * 72,
            excerpt(source_lines, nearest),
            "-" * 72,
        ])

    return "\n".join(out)


def apply_hunk(repo: Path, patch_name: str, hunk: Hunk) -> None:
    target = repo / hunk.path

    if not target.is_file():
        raise RuntimeError(
            f"{patch_name}: target missing: {hunk.path}"
        )

    text = normalize_lf(target.read_bytes())

    # Keep line endings so we can reconstruct exact spans.
    source_keep = text.splitlines(keepends=True)
    source_plain = [
        line[:-1] if line.endswith("\n") else line
        for line in source_keep
    ]

    expected = hunk.old_lines()

    matches = contiguous_matches(source_plain, expected)
    mode = "strict-lines"

    if not matches:
        matches = blank_tolerant_matches(source_plain, expected)
        mode = "blank-tolerant"

    if len(matches) != 1:
        print()
        print("=" * 72)
        print("STRICT TRANSFORM FAILED")
        print("=" * 72)
        print("Patch:", patch_name)
        print("File :", hunk.path)
        print("Declared hunk line:", hunk.old_start)
        print("Match mode:", mode)
        print("Matches:", len(matches))
        print()
        print("Expected OLD lines:")
        print("-" * 72)

        for index, line in enumerate(expected, start=1):
            print(f"{index:4d}: {line!r}")

        print("-" * 72)
        print()
        print(
            nearest_diagnostic(
                source_plain,
                expected,
                hunk.old_start,
            )
        )

        raise RuntimeError(
            f"{patch_name}: normalized old block must resolve to exactly "
            f"one span in {hunk.path}; found {len(matches)}"
        )

    start, end = matches[0]

    print(
        f"  {hunk.path}: "
        f"declared@{hunk.old_start}, "
        f"matched@{start + 1}-{end}, "
        f"mode={mode}"
    )

    new_text = hunk.new_text()

    before = "".join(source_keep[:start])
    after = "".join(source_keep[end:])

    updated = before + new_text + after

    target.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )


def subject_for(path: Path) -> str:
    subject = re.sub(r"^\d+-", "", path.stem)
    subject = re.sub(r"-v\d+(?:\.\d+)*$", "", subject)
    return subject.replace("-", " ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--patch-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    patch_dir = args.patch_dir.resolve()
    manifest = args.manifest.resolve()

    patch_files = sorted(
        patch_dir.glob("[0-9][0-9][0-9][0-9]-*.patch")
    )

    if len(patch_files) != 11:
        raise RuntimeError(
            f"Expected 11 input patches, found {len(patch_files)}"
        )

    run(["git", "config", "user.name", "Telegram Patch Bot"], repo)
    run(["git", "config", "user.email", "actions@github.com"], repo)
    run(["git", "config", "core.autocrlf", "false"], repo)
    run(["git", "config", "core.eol", "lf"], repo)

    if run(["git", "status", "--porcelain"], repo, capture=True):
        raise RuntimeError("Repo is dirty before transforms")

    base_sha = run(
        ["git", "rev-parse", "HEAD"],
        repo,
        capture=True,
    )

    manifest_lines = [
        f"Base commit: {base_sha}",
        "",
        "Input transformations:",
    ]

    for index, patch_file in enumerate(patch_files, 1):
        print()
        print("=" * 72)
        print(f"TRANSFORM {index}/11: {patch_file.name}")
        print("=" * 72)

        sha = hashlib.sha256(patch_file.read_bytes()).hexdigest()
        hunks = parse_patch(patch_file)

        for hunk in hunks:
            apply_hunk(repo, patch_file.name, hunk)

        run(["git", "diff", "--check"], repo)
        run(["git", "add", "-A"], repo)

        staged = run(
            ["git", "diff", "--cached", "--name-only"],
            repo,
            capture=True,
        )

        if not staged:
            raise RuntimeError(
                f"{patch_file.name}: no staged changes"
            )

        run(
            [
                "git",
                "commit",
                "-m",
                f"Patched: {subject_for(patch_file)}",
            ],
            repo,
        )

        commit = run(
            ["git", "rev-parse", "HEAD"],
            repo,
            capture=True,
        )

        manifest_lines += [
            "",
            patch_file.name,
            f"Input SHA256: {sha}",
            f"Generated commit: {commit}",
        ]

    if run(["git", "status", "--porcelain"], repo, capture=True):
        raise RuntimeError("Repo dirty after transforms")

    manifest.write_text(
        "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print()
    print("=" * 72)
    print("GENERATED COMMIT HISTORY")
    print("=" * 72)

    run(
        [
            "git",
            "log",
            "--oneline",
            "--reverse",
            f"{base_sha}..HEAD",
        ],
        repo,
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise
