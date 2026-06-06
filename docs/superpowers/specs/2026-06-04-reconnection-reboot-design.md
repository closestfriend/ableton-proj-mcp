# Design — `ableton-proj-mcp` Reconnection Reboot (v0.2.0)

Date: 2026-06-04 · Status: approved (sections), pending spec review
Author context: Hunter is the original author (`github.com/closestfriend/ableton-proj-mcp`).
This is a hardening reboot of an already-shipped tool, validated by a multi-day, ~2,300-set
real-world reconnection (see `_ableton_consolidation/` on the exSSD: `README.md`,
`MCP_UPDATE_NOTES.md`, `WORKSPACE_PREP.md`, and the reference scripts).

## 1. Goal & scope

**Goal:** ship the *reconnection superpower* — let anyone go from "open a track, lose 30
minutes relinking" to "open it, hear it." The relink/collect pipeline that just rescued the
author's library, packaged so others can use it safely.

**v1 (laser-focused) includes:**
- Live-faithful sample resolution (replaces the naïve, over-reporting `_detect_missing_samples`)
- The reconnect pipeline: build cross-source index → match (name+size) → **relink** / **collect**
- Audio **and video** media (video was a silent gap in the original)
- Lifted 100-file cap; analyzer is a pure, uncapped parser
- Tests + CI + PyPI publish + the config/path fixes

**Deferred to later releases (YAGNI for v1):** dedupe keeper-review, migration/consolidation,
library-org tooling. (Prototyped in `_ableton_consolidation/` but not part of this release.)

## 2. Architecture — core + two thin frontends (approach B)

A pure, framework-free `core/` holds all `.als` logic and is the only thing that touches bytes.
`__main__.py` (MCP) and `cli.py` (CLI) are thin adapters: marshal args → call core → format out.

```
src/music_manager_mcp/
├─ core/
│  ├─ als_io.py     # integrity-critical read/write primitive (THE one write door)
│  ├─ analyzer.py   # AbletonAnalyzer (debugged EnhancedAbletonAnalyzer); pure parser, no cap
│  ├─ samples.py    # SampleResolver — Live-faithful per-ref status
│  ├─ index.py      # SampleIndex — name(+size,+crc)→[paths] master index over sources
│  └─ reconnect.py  # ReconnectEngine — relink() / collect(), idempotent, route writes via als_io
├─ __main__.py      # MCP server: read/analyze/PLAN tools only (never writes)
└─ cli.py           # `music-manager` CLI: the mutating batch (dry-run default + backups)
```

**Data model (dataclasses):** `SampleRef` (rtype, relpath, abspath, name, size, crc),
`ResolvedRef` (+status: ok_relative|ok_absolute|library|missing, resolved_path),
`ReconnectResult` (relinked, remaining, casualties, backup_path).

**Data flow (each stage a pure function over the prior — also the test seam):**
`analyze → resolve → build index → match → reconnect`.

### Core module responsibilities
- **`als_io.py`** — `read_als(path) → (root, declaration)`; `write_als(path, root, declaration,
  backup_dir)` enforcing the invariant: preserve original `<?xml…?>` declaration, recompress
  **only** via the `gzip` module, write temp + back up original, **validate** (gzip integrity +
  XML re-parse) before `os.replace`. Every mutation goes through this door.
- **`analyzer.py`** — `_get_sample_paths` returns full `SampleRef`s (incl. name/size/crc and
  **video** extensions); fix `_get_arrangement_length` (scope to arrangement or drop from
  completion heuristic), `_get_master_chain` (`is not None`); finish or honestly remove
  `_get_return_tracks`/`_detect_missing_plugins`. No 100-cap (lives at frontend iteration).
- **`samples.py`** — `SampleResolver`: resolve each ref relative-to-project → absolute →
  missing; classify library/factory (Ableton packs, `/Applications`, `Devices/`, presets).
- **`index.py`** — `SampleIndex`: build/persist `name(+size,+crc)→[paths]` over given source
  roots (audio+video); mount/path-translation hook (`/Users/wer → /Volumes/wer` lesson);
  size as the disambiguation key, crc as tiebreaker.
- **`reconnect.py`** — `ReconnectEngine.relink()` rewrites missing FileRef `Path` → found
  location; `.collect()` copies into `Samples/Imported/`, sets `RelativePathType=3` + relative
  path, keeps absolute as dual-path fallback. Both idempotent; both write via `als_io`.

## 3. Frontends

**MCP (`__main__.py`) — read / analyze / PLAN only, NEVER writes:**
- `analyze_projects(paths)` — on fixed core
- `scan_projects(directory, limit=None)` — cap is now an optional arg, no silent 100
- `resolve_samples(directory)` — NEW; replaces `find_missing_samples`; honest per-ref status
- `plan_reconnect(directory, sources[])` — NEW; **dry-run report only** — what relink/collect
  *would* do + casualties. The assistant can see/plan everything but cannot apply.
- Existing read tools (`find_recent`, `analyze_master_chains`, …) retained; cap lifted.

**CLI (`cli.py`, `music-manager`) — where mutation lives:**
- `analyze <paths…>` · `resolve <dir>` · `index <sources…> [-o index.json]`
- `reconnect <dir> --sources … --mode relink|collect [--dry-run|--apply] [--backup-dir …]
  [--verify]` — batch mutator. **`--dry-run` default**; `--apply` explicit. stdlib `argparse`
  (keeps deps at just `mcp`).

Safety model: **assistant (MCP) sees & plans; only the human (CLI) applies a write.**

## 4. Safety & error handling

**Mutation invariant (every write):** dry-run default; back up original first (never overwrite a
backup); write temp → validate (gzip integrity + XML re-parse + every rewritten target exists at
expected size) → `os.replace`; on any failure discard temp, leave original, record, continue —
**never a partial write**; idempotent (skip already-resolved refs).

**Failure modes:** source vanished at apply (mount dropped) → skip+report; **name matches but
size doesn't → never auto-pick, flag ambiguous**; corrupt `.als` → skip+report, don't crash the
batch; casualties (no match) → always reported, never silently dropped.

**No silent truncation:** reports distinguish **unique vs reference-instances**; name what was
skipped/capped/unfound. (Lessons: the silent 100-cap; the "342 instances looked scary" moment.)

**Collect-specific:** keep absolute path as dual-path fallback during cutover (Live loads if
*either* resolves); `--verify` confirms self-containment with sources unmounted before retiring
drives; never point a ref at an iCloud/evictable path — **localize instead** (the `.mp4` lesson).

**Reversibility:** every `--apply` writes a manifest; the per-`.als` backups are the undo.

## 5. Testing & release

**`tests/` (pytest):**
- `fixtures/` — tiny real `.als` files: collected/relative, missing/external, video-ref, minimal
- **`test_als_io_roundtrip.py`** — decompress→edit→recompress→re-parse integrity; the single
  guard against the corruption trap. Must never regress.
- `test_analyzer.py` (extraction + fixed bugs), `test_samples.py` (resolver classification),
  `test_index.py`/`test_reconnect.py` (name+size match, size-mismatch ambiguity, casualties;
  relink+collect assert rewrite + backup + validation + **idempotency** + **dry-run-writes-nothing**)

**CI:** `.github/workflows/ci.yml` — ruff + pytest on Python 3.10/3.11/3.12.

**Release:** bump to `0.2.0`; add `music-manager` CLI entry point + `[dev]` extra; **publish to
PyPI** so configs move to `uvx music-manager-mcp` (permanently kills local-path drift — the
ghost-path bug); **archive Gradio/demo cruft** (`app*.py`, `music_mcp*.py`, `style.css`, mockups,
`switch_version.py`) so the package surface is MCP + CLI core; retire print-style top-level
`test_*.py`; refresh README/QUICKSTART (reconnection workflow front-and-center; salvage
QUICKSTART text from the `to_sort` copy).

## 6. Key invariants (do NOT regress)
1. **gzip round-trip** via `als_io` only — preserve declaration, gzip module, temp+backup+validate.
2. **Dry-run default; --apply explicit; backups always.**
3. **Match by name+size; never relink a size-mismatch.**
4. **MCP never writes; CLI is the only mutator.**
5. **Honest counts** (unique vs instances; report skipped/unfound).

## 7. Sequencing note
Build & validate the **Collect limb first** on a small batch (relink + localize are already
proven in Live; collect-into-`Samples/Imported` is the one un-run path). The full library-wide
Collect is an operational run gated on disk space — it does NOT gate this release.

## 8. Open risks
- Collect disk duplication (validated separately; user-driven, dry-run shows footprint).
- Cross-platform paths (Windows) — out of scope for v1; macOS-first, note it.
- iCloud/dataless files — handle via localize + "materialized?" checks.
