"""Shared AI-SDLC gate logic, used by bin/sdlc, .claude/hooks and .githooks.

Stdlib only. A feature lives in sdlc/features/NNN-slug/ on branch feat/NNN-slug.
An approval is approvals/<gate>.json holding the sha256 of the gated file, so
editing an approved file silently re-opens its gate.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

GATES = ["intent", "spec", "plan", "merge", "release"]
GATE_FILES = {
    "intent": "intent.md",
    "spec": "spec.md",
    "plan": "plan.md",
    "merge": "summary.md",
    "release": "release.md",
}
MAX_LINES = 50
GATE_MARKER = re.compile(r"\[GATE\s+(\d{3}[a-z0-9-]*)\s+([a-z]+)\]")
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "var"}


class SdlcError(Exception):
    pass


# ---------- basics ----------

def root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and (Path(env) / "sdlc").is_dir():
        return Path(env)
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    return Path(out.stdout.strip()) if out.returncode == 0 else Path.cwd()


def git(*args: str, check: bool = True) -> str:
    out = subprocess.run(["git", *args], cwd=root(), capture_output=True, text=True)
    if check and out.returncode != 0:
        raise SdlcError(out.stderr.strip() or f"git {' '.join(args)} failed")
    return out.stdout.strip()


def git_ok(*args: str) -> bool:
    return subprocess.run(["git", *args], cwd=root(), capture_output=True).returncode == 0


def features_dir() -> Path:
    return root() / "sdlc" / "features"


def feature_dirs() -> list[Path]:
    return sorted(p for p in features_dir().glob("[0-9][0-9][0-9]-*") if p.is_dir())


def resolve(fid: str) -> Path:
    if not fid:
        raise SdlcError("no feature id given")
    matches = [p for p in feature_dirs() if p.name == fid or p.name.startswith(fid)]
    exact = [p for p in matches if p.name == fid]
    if exact:
        return exact[0]
    if len(matches) == 1:
        return matches[0]
    raise SdlcError(f"unknown or ambiguous feature id {fid!r}")


def line_count(text: str) -> int:
    return len(text.splitlines())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def who() -> str:
    return git("config", "user.name", check=False) or os.environ.get("USER", "unknown")


def now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def gate_file(fdir: Path, gate: str) -> Path:
    if gate not in GATES:
        raise SdlcError(f"unknown gate {gate!r}; expected one of {GATES}")
    return fdir / GATE_FILES[gate]


def tag_name(fid: str) -> str:
    return f"v0.{int(fid[:3])}.0"


# ---------- approvals ----------

def approval(fdir: Path, gate: str) -> dict | None:
    path = fdir / "approvals" / f"{gate}.json"
    return json.loads(path.read_text()) if path.exists() else None


def valid(fid: str, gate: str) -> bool:
    fdir = resolve(fid)
    data, path = approval(fdir, gate), gate_file(fdir, gate)
    return bool(data) and path.exists() and data.get("sha256") == sha256(path)


def decisions(fdir: Path) -> list[dict]:
    log = fdir / "approvals" / "log.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


def last_decision(fdir: Path, gate: str) -> dict | None:
    hits = [d for d in decisions(fdir) if d.get("gate") == gate]
    return hits[-1] if hits else None


def record(fid: str, gate: str, decision: str, notes: str = "", via: str = "cli") -> dict:
    """Record a human decision. decision: approve | changes | stop."""
    if decision not in ("approve", "changes", "stop"):
        raise SdlcError(f"unknown decision {decision!r}")
    fdir = resolve(fid)
    path = gate_file(fdir, gate)
    entry = {"gate": gate, "decision": decision, "notes": notes, "by": who(),
             "at": now(), "ts": time.time(), "via": via}
    if decision == "approve":
        if not path.exists():
            raise SdlcError(f"{path.name} does not exist yet")
        n = line_count(path.read_text())
        if n > MAX_LINES:
            raise SdlcError(f"{path.name} has {n} lines (max {MAX_LINES})")
        missing = [g for g in GATES[:GATES.index(gate)] if not valid(fdir.name, g)]
        if missing:
            raise SdlcError(f"earlier gates not approved: {', '.join(missing)}")
        entry.update(file=path.name, sha256=sha256(path))
        if gate == "merge":
            entry["commit"] = git("rev-parse", f"feat/{fdir.name}")
        if gate == "release":
            if git("rev-parse", "--abbrev-ref", "HEAD") != "main" or not merged(fdir.name):
                raise SdlcError("release is approved on main, after the merge")
            entry["commit"] = git("rev-parse", "HEAD")
    adir = fdir / "approvals"
    adir.mkdir(exist_ok=True)
    if decision == "approve":
        (adir / f"{gate}.json").write_text(json.dumps(entry, indent=2) + "\n")
    with open(adir / "log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def decide(answer: str) -> tuple[str, str]:
    """Map a gate-question answer to (decision, notes)."""
    a = answer.strip()
    low = a.lower()
    if low.startswith("approve"):
        return "approve", ""
    if low.startswith("stop"):
        return "stop", ""
    if low.startswith("request changes"):
        return "changes", a[len("request changes"):].strip(" :-")
    return "changes", a  # free text ("Other") = change notes


# ---------- stage machine ----------

def merged(fid: str) -> bool:
    if not git_ok("rev-parse", "--verify", "-q", f"refs/heads/feat/{fid}"):
        return True  # branch deleted after merge
    return git_ok("merge-base", "--is-ancestor", f"feat/{fid}", "main")


def tagged(fid: str) -> bool:
    return git_ok("rev-parse", "--verify", "-q", f"refs/tags/{tag_name(fid)}")


def stage(fid: str) -> tuple[str, str]:
    """Return (stage, detail). Stage is derived from files + approvals only."""
    fdir = resolve(fid)
    for gate in GATES:
        path = gate_file(fdir, gate)
        if valid(fdir.name, gate):
            if gate == "merge" and not merged(fdir.name):
                return "do-merge", (f"git switch main && git merge --no-ff "
                                    f"feat/{fdir.name} -m \"merge: {fdir.name}\"")
            if gate == "release" and not tagged(fdir.name):
                commit = approval(fdir, "release")["commit"]
                return "do-tag", f"git tag {tag_name(fdir.name)} {commit}"
            continue
        last = last_decision(fdir, gate)
        if not path.exists():
            if gate == "merge":
                return "build", "build + review until review.md is PASS and summary.md exists"
            return f"draft-{gate}", f"write {path.relative_to(root())}"
        if last and last["decision"] == "changes" and last["ts"] > path.stat().st_mtime:
            return f"revise-{gate}", f"changes requested: {last['notes'] or '(ask the human)'}"
        if approval(fdir, gate):
            return f"await-{gate}", f"{path.name} changed since approval; needs re-approval"
        return f"await-{gate}", f"{path.name} is ready for human approval"
    return "done", f"released as {tag_name(fdir.name)}"


def current_id() -> str | None:
    branch = git("rev-parse", "--abbrev-ref", "HEAD", check=False)
    if branch.startswith("feat/") and (features_dir() / branch[5:]).is_dir():
        return branch[5:]
    for fdir in reversed(feature_dirs()):
        if stage(fdir.name)[0] != "done":
            return fdir.name
    return None


def new(slug: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        raise SdlcError("slug must be kebab-case, e.g. due-dates")
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise SdlcError("start new features from main")
    if git("status", "--porcelain"):
        raise SdlcError("working tree is not clean; commit or stash first")
    open_ = [d.name for d in feature_dirs() if stage(d.name)[0] != "done"]
    if open_:
        raise SdlcError(f"feature still in flight: {open_[0]} (finish it first)")
    nums = [int(d.name[:3]) for d in feature_dirs()]
    fid = f"{max(nums, default=0) + 1:03d}-{slug}"
    git("switch", "-c", f"feat/{fid}")
    (features_dir() / fid / "approvals").mkdir(parents=True)
    return fid


# ---------- checks ----------

def long_md_files() -> list[tuple[Path, int]]:
    bad = []
    for path in root().rglob("*.md"):
        if SKIP_DIRS & set(path.relative_to(root()).parts):
            continue
        n = line_count(path.read_text(errors="replace"))
        if n > MAX_LINES:
            bad.append((path.relative_to(root()), n))
    return bad


def incoming_commit() -> str | None:
    """The commit being merged. pre-merge-commit only sees GIT_REFLOG_ACTION
    ("merge <ref>"); a merge concluded via `git commit` has MERGE_HEAD instead."""
    if git_ok("rev-parse", "--verify", "-q", "MERGE_HEAD"):
        return git("rev-parse", "MERGE_HEAD")
    m = re.fullmatch(r"merge (\S+)", os.environ.get("GIT_REFLOG_ACTION", "").strip())
    if m and git_ok("rev-parse", "--verify", "-q", f"{m.group(1)}^{{commit}}"):
        return git("rev-parse", f"{m.group(1)}^{{commit}}")
    return None


def verify_merge() -> None:
    """pre-merge-commit / pre-commit: a merge into main must be an approved feature branch."""
    if git("symbolic-ref", "--short", "-q", "HEAD", check=False) != "main":
        return
    if not git_ok("rev-parse", "--verify", "-q", "HEAD"):
        return  # first commit in the repo
    incoming = incoming_commit()
    if incoming is None:
        if os.environ.get("SDLC_HOOK") == "pre-commit":
            return  # ordinary commit, not concluding a merge
        raise SdlcError("cannot tell which branch is being merged")
    changed = git("diff", "--name-only", f"HEAD...{incoming}").splitlines()
    ids = {p.split("/")[2] for p in changed if p.startswith("sdlc/features/")}
    if len(ids) != 1:
        raise SdlcError("a merge into main must carry exactly one sdlc feature "
                        f"(found: {sorted(ids) or 'none'})")
    fid = ids.pop()
    raw = git("show", f"{incoming}:sdlc/features/{fid}/approvals/merge.json", check=False)
    if not raw:
        raise SdlcError(f"{fid}: no merge approval on the branch")
    approved = json.loads(raw)["commit"]
    if not git_ok("merge-base", "--is-ancestor", approved, incoming):
        raise SdlcError(f"{fid}: approved commit {approved[:8]} is not in the branch")
    after = git("diff", "--name-only", approved, incoming).splitlines()
    extra = [p for p in after if "/approvals/" not in p]
    if extra:
        raise SdlcError(f"{fid}: changed after merge approval: {', '.join(extra[:5])}")


# ---------- hook helpers ----------

def find_key(obj, key: str):
    """Depth-first search for a non-empty dict under `key` (also inside JSON strings)."""
    if isinstance(obj, dict):
        val = obj.get(key)
        if isinstance(val, dict) and val:
            return val
        for v in obj.values():
            hit = find_key(v, key)
            if hit:
                return hit
    elif isinstance(obj, list):
        for v in obj:
            hit = find_key(v, key)
            if hit:
                return hit
    elif isinstance(obj, str) and obj[:1] in "{[":
        try:
            return find_key(json.loads(obj), key)
        except ValueError:
            return None
    return None


def answers_from_text(text: str) -> dict:
    """Fallback for plain-text results like: "Question?"="Answer"."""
    return dict(re.findall(r'"([^"]+)"="([^"]*)"', text or ""))


def debug_log(name: str, payload: dict) -> None:
    try:
        d = root() / "var" / "hooks"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{name}.jsonl", "a") as f:
            f.write(json.dumps({"at": now(), **payload}, default=str) + "\n")
    except OSError:
        pass
