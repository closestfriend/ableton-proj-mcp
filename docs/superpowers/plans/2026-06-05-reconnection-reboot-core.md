# Reconnection Reboot — Plan 1: Core Library

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pure, framework-free `core/` of the reconnection reboot — the only code that touches `.als` bytes — fully unit-tested, with the gzip-safety invariant guarded by a regression test.

**Architecture:** A `src/music_manager_mcp/core/` package: `als_io` (the single safe read/write door), `models` (dataclasses), `analyzer` (debugged parser), `samples` (Live-faithful resolver), `index` (name+size source index), `reconnect` (relink/collect engine). Each module is a pure function/class over the prior's output. No `mcp`/CLI imports anywhere in `core/`.

**Tech Stack:** Python 3.10+, stdlib only (`gzip`, `xml.etree.ElementTree`, `hashlib`, `dataclasses`, `pathlib`, `shutil`). Tests: `pytest`. Reference implementations (validated on ~2,300 real sets) live on the exSSD at `/Volumes/2025_exSSD_2tb/_ableton_consolidation/`: `inventory.py`, `sample_index.py`, `reconnect_match.py`, `relink_engine.py`, `localize_wer.py`.

**Working branch:** `reboot` (already created off `main`).

---

## File structure (this plan)

```
src/music_manager_mcp/
├─ core/
│  ├─ __init__.py        # re-exports public classes
│  ├─ als_io.py          # read_als / write_als — the ONE write door (gzip-safe + validate)
│  ├─ models.py          # SampleRef, ResolvedRef, ReconnectResult dataclasses
│  ├─ analyzer.py        # AbletonAnalyzer (debugged); SampleRef extraction incl. video/size/crc
│  ├─ samples.py         # SampleResolver — relative→absolute→missing, library filter
│  ├─ index.py           # SampleIndex — name(+size)→[paths] over source roots (audio+video)
│  └─ reconnect.py       # ReconnectEngine.relink() / .collect()
tests/
├─ conftest.py           # fixture-builder: make_als(...) writes tiny gzipped .als
├─ test_als_io.py
├─ test_analyzer.py
├─ test_samples.py
├─ test_index.py
└─ test_reconnect.py
pyproject.toml           # add [project.optional-dependencies] dev = ["pytest"]
```

**Media constants** (used across modules): audio = `.wav .aif .aiff .mp3 .m4a .flac .ogg .wave`; video = `.mp4 .mov .m4v .avi .webm .mkv .mpg .mpeg`. Define once in `core/models.py` as `AUDIO_EXTS`, `VIDEO_EXTS`, `MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS`.

---

## Task 1: Workspace setup & test scaffold

**Files:**
- Create: `src/music_manager_mcp/core/__init__.py` (empty for now)
- Create: `tests/conftest.py`
- Modify: `pyproject.toml` (add dev extra)
- Move: top-level Gradio/demo files → `archive/`

- [ ] **Step 1: Archive demo cruft so the package surface is clean**

```bash
cd /Users/hnsk/ableton-proj-mcp
git checkout reboot
mkdir -p archive
git mv app.py app_local.py music_mcp.py music_mcp_enhanced.py style.css \
       apm-mockup.html switch_version.py requirements-gradio.txt \
       Gradio_design_guide.txt example_config.json archive/ 2>/dev/null || true
# top-level print-style tests are superseded by tests/
git mv test_analyzer.py test_chat_integration.py test_gradio_setup.py archive/ 2>/dev/null || true
# stray top-level duplicate of the packaged analyzer (the packaged one in src/ is canonical)
git rm -q enhanced_analyzer.py 2>/dev/null || true
mkdir -p src/music_manager_mcp/core tests
```

- [ ] **Step 2: Add the dev extra to `pyproject.toml`**

Add this block (the project already uses hatchling + `mcp>=1.0.0`):

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
```

- [ ] **Step 3: Create the fixture-builder `tests/conftest.py`**

Real `.als` files are large; tests use tiny synthetic ones with the exact `FileRef` shape Live writes.

```python
import gzip, os
import xml.etree.ElementTree as ET
import pytest

DECL = b'<?xml version="1.0" encoding="UTF-8"?>'

def _fileref(rtype, relpath, abspath, name, size=0, crc=0):
    """Build a <SampleRef><FileRef>…</FileRef></SampleRef> element like Live's."""
    sr = ET.Element("SampleRef")
    fr = ET.SubElement(sr, "FileRef")
    ET.SubElement(fr, "RelativePathType").set("Value", str(rtype))
    ET.SubElement(fr, "RelativePath").set("Value", relpath)
    ET.SubElement(fr, "Path").set("Value", abspath)
    ET.SubElement(fr, "Type").set("Value", "2")
    ET.SubElement(fr, "OriginalFileSize").set("Value", str(size))
    ET.SubElement(fr, "OriginalCrc").set("Value", str(crc))
    return sr

def make_als(path, filerefs=(), bpm=120.0):
    """Write a minimal gzipped .als with the given FileRefs. filerefs: list of dicts
    with keys rtype, relpath, abspath, name, size, crc."""
    root = ET.Element("Ableton")
    live = ET.SubElement(root, "LiveSet")
    tempo = ET.SubElement(ET.SubElement(live, "Tempo"), "Manual")
    tempo.set("Value", str(bpm))
    tracks = ET.SubElement(live, "Tracks")
    for fr in filerefs:
        at = ET.SubElement(tracks, "AudioTrack")
        at.append(_fileref(fr["rtype"], fr["relpath"], fr["abspath"],
                           fr["name"], fr.get("size", 0), fr.get("crc", 0)))
    body = ET.tostring(root, encoding="unicode")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(gzip.compress(DECL + b"\n" + body.encode("utf-8")))
    return path

@pytest.fixture
def make_als_fixture():
    return make_als
```

- [ ] **Step 4: Verify pytest collects (no tests yet → exit 5 is fine)**

Run: `cd /Users/hnsk/ableton-proj-mcp && uv run --extra dev pytest -q`
Expected: "no tests ran" (exit code 5) — confirms pytest + conftest import cleanly.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: archive demo cruft, add pytest scaffold + fixture builder"
```

---

## Task 2: `core/als_io.py` — the safe read/write door (THE critical primitive)

**Files:**
- Create: `src/music_manager_mcp/core/als_io.py`
- Test: `tests/test_als_io.py`

This is the single most important module: every mutation in the system goes through `write_als`, which enforces the gzip-safety invariant proven in `relink_engine.py`/`localize_wer.py`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_als_io.py
import gzip, os
import xml.etree.ElementTree as ET
import pytest
from music_manager_mcp.core import als_io

def test_read_als_returns_root_and_declaration(make_als_fixture, tmp_path):
    p = make_als_fixture(str(tmp_path / "x.als"),
                         [{"rtype": 3, "relpath": "Samples/Imported/a.wav",
                           "abspath": "/old/a.wav", "name": "a.wav", "size": 10}])
    root, decl = als_io.read_als(p)
    assert root.tag == "Ableton"
    assert decl.startswith('<?xml')

def test_roundtrip_preserves_structure_and_stays_parseable(make_als_fixture, tmp_path):
    p = make_als_fixture(str(tmp_path / "x.als"),
                         [{"rtype": 3, "relpath": "Samples/Imported/a.wav",
                           "abspath": "/old/a.wav", "name": "a.wav", "size": 10}])
    root, decl = als_io.read_als(p)
    # mutate a Path value
    pe = root.find(".//FileRef/Path")
    pe.set("Value", "/new/a.wav")
    backup_dir = str(tmp_path / "bak")
    als_io.write_als(p, root, decl, backup_dir)
    # reopens cleanly and reflects the change
    root2, _ = als_io.read_als(p)
    assert root2.find(".//FileRef/Path").get("Value") == "/new/a.wav"
    # original was backed up
    assert os.path.exists(os.path.join(backup_dir, "x.als"))

def test_write_validates_before_replacing(make_als_fixture, tmp_path, monkeypatch):
    """If validation fails, the original file must be left untouched."""
    p = make_als_fixture(str(tmp_path / "x.als"),
                         [{"rtype": 0, "relpath": "", "abspath": "/old/a.wav",
                           "name": "a.wav"}])
    root, decl = als_io.read_als(p)
    before = open(p, "rb").read()
    # force the validation re-read to fail
    monkeypatch.setattr(als_io, "_validate", lambda tmp: (_ for _ in ()).throw(ValueError("boom")))
    with pytest.raises(als_io.AlsWriteError):
        als_io.write_als(p, root, decl, str(tmp_path / "bak"))
    assert open(p, "rb").read() == before  # untouched
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --extra dev pytest tests/test_als_io.py -v`
Expected: FAIL — `ModuleNotFoundError: music_manager_mcp.core.als_io`

- [ ] **Step 3: Implement `core/als_io.py`**

```python
"""The single safe door for reading/writing .als (gzipped XML). Every mutation
in the system goes through write_als, which enforces: preserve the original XML
declaration, recompress only via the gzip module, back up the original, write to
a temp file, validate (gzip integrity + XML re-parse), then atomically replace."""
import gzip, os, re, shutil
import xml.etree.ElementTree as ET

_DECL_RE = re.compile(rb'^\s*<\?xml[^>]*\?>')
_DEFAULT_DECL = '<?xml version="1.0" encoding="UTF-8"?>'

class AlsWriteError(Exception):
    pass

def read_als(path):
    """Return (xml_root, declaration_str). Parses raw bytes so the encoding
    declaration is honored."""
    raw = gzip.open(path, "rb").read()
    m = _DECL_RE.match(raw)
    decl = m.group(0).decode("utf-8") if m else _DEFAULT_DECL
    return ET.fromstring(raw), decl

def _validate(tmp_path):
    """Raise if the written file isn't valid gzip+XML."""
    ET.fromstring(gzip.open(tmp_path, "rb").read())

def write_als(path, root, declaration, backup_dir):
    """Recompress root, validate, then atomically replace `path`. Backs up the
    original to backup_dir (mirroring its basename) first. Raises AlsWriteError on
    any failure, leaving the original untouched."""
    os.makedirs(backup_dir, exist_ok=True)
    backup = os.path.join(backup_dir, os.path.basename(path))
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
    body = ET.tostring(root, encoding="unicode")
    new_bytes = gzip.compress((declaration + "\n" + body).encode("utf-8"))
    tmp = path + ".alstmp"
    with open(tmp, "wb") as f:
        f.write(new_bytes)
    try:
        _validate(tmp)
    except Exception as e:
        os.remove(tmp)
        raise AlsWriteError(f"validation failed for {path}: {e}") from e
    os.replace(tmp, path)
    return backup
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run --extra dev pytest tests/test_als_io.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/music_manager_mcp/core/als_io.py tests/test_als_io.py
git commit -m "feat(core): als_io safe read/write with gzip+XML validation"
```

---

## Task 3: `core/models.py` — data model + media constants

**Files:**
- Create: `src/music_manager_mcp/core/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
from music_manager_mcp.core import models

def test_media_extensions_cover_audio_and_video():
    assert ".wav" in models.AUDIO_EXTS
    assert ".mp4" in models.VIDEO_EXTS
    assert models.MEDIA_EXTS == models.AUDIO_EXTS | models.VIDEO_EXTS

def test_sampleref_basename_and_is_media():
    r = models.SampleRef(rtype=3, relpath="Samples/Imported/Kick.WAV",
                         abspath="/x/Kick.WAV", name="Kick.WAV", size=12, crc=7)
    assert r.basename_lower == "kick.wav"
    assert r.is_media is True
    p = models.SampleRef(rtype=5, relpath="Devices/EQ Eight", abspath="/app/EQ Eight",
                         name="EQ Eight", size=0, crc=0)
    assert p.is_media is False
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --extra dev pytest tests/test_models.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `core/models.py`**

```python
"""Data model + media extension constants for the core."""
import os
from dataclasses import dataclass, field
from typing import Optional, List

AUDIO_EXTS = {".wav", ".aif", ".aiff", ".mp3", ".m4a", ".flac", ".ogg", ".wave"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".webm", ".mkv", ".mpg", ".mpeg"}
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS

@dataclass
class SampleRef:
    """One FileRef in a project, as extracted from the .als."""
    rtype: int            # RelativePathType: 0 missing,1 external,2 library,3 project,5 core-lib
    relpath: str          # RelativePath value
    abspath: str          # Path value (often stale)
    name: str             # basename of relpath or abspath
    size: int = 0         # OriginalFileSize
    crc: int = 0          # OriginalCrc

    @property
    def basename_lower(self):
        return os.path.basename(self.name).lower()

    @property
    def ext(self):
        return os.path.splitext(self.name)[1].lower()

    @property
    def is_media(self):
        return self.ext in MEDIA_EXTS

@dataclass
class ResolvedRef:
    """A SampleRef plus how it resolves."""
    ref: SampleRef
    status: str           # ok_relative | ok_absolute | library | missing
    resolved_path: Optional[str] = None

@dataclass
class ReconnectResult:
    """Outcome of relink/collect on a single project."""
    als: str
    relinked: int = 0
    remaining: List[str] = field(default_factory=list)   # unique unfound basenames
    backup: Optional[str] = None
    status: str = "ok"    # ok | no_change | error:<msg>
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run --extra dev pytest tests/test_models.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/music_manager_mcp/core/models.py tests/test_models.py
git commit -m "feat(core): data model + audio/video media constants"
```

---

## Task 4: `core/analyzer.py` — debugged parser with full SampleRef extraction

**Files:**
- Create: `src/music_manager_mcp/core/analyzer.py` (ported from `src/music_manager_mcp/enhanced_analyzer.py`)
- Test: `tests/test_analyzer.py`

The existing `enhanced_analyzer.py` stays for now (the MCP frontend still imports it; Plan 2 swaps it). This task extracts the *correct* sample logic into the core. We only port what v1 needs: BPM, track counts, and **full FileRef extraction** (the part that was buggy).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_analyzer.py
from music_manager_mcp.core.analyzer import AbletonAnalyzer

def test_extracts_full_sample_refs_with_size_and_video(make_als_fixture, tmp_path):
    p = make_als_fixture(str(tmp_path / "x.als"), [
        {"rtype": 3, "relpath": "Samples/Imported/kick.wav",
         "abspath": "/old/kick.wav", "name": "kick.wav", "size": 111, "crc": 9},
        {"rtype": 0, "relpath": "", "abspath": "/Users/x/clip.mp4",
         "name": "clip.mp4", "size": 222, "crc": 0},
    ])
    refs = AbletonAnalyzer(p).sample_refs()
    by_name = {r.name: r for r in refs}
    assert by_name["kick.wav"].rtype == 3
    assert by_name["kick.wav"].relpath == "Samples/Imported/kick.wav"
    assert by_name["kick.wav"].size == 111 and by_name["kick.wav"].crc == 9
    assert by_name["clip.mp4"].is_media is True          # video included
    assert by_name["clip.mp4"].abspath == "/Users/x/clip.mp4"

def test_bpm(make_als_fixture, tmp_path):
    p = make_als_fixture(str(tmp_path / "x.als"), [], bpm=174.0)
    assert AbletonAnalyzer(p).bpm() == 174.0

def test_skips_empty_filerefs(make_als_fixture, tmp_path):
    p = make_als_fixture(str(tmp_path / "x.als"),
                         [{"rtype": 0, "relpath": "", "abspath": "", "name": ""}])
    assert AbletonAnalyzer(p).sample_refs() == []
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --extra dev pytest tests/test_analyzer.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `core/analyzer.py`**

Port pattern from `sample_index.py` (FileRef field extraction) and the existing analyzer's BPM/track methods. Reuse `als_io.read_als` so parsing is consistent.

```python
"""Pure .als parser. v1 surface: bpm, track counts, and full FileRef extraction.
Uncapped — a thin batch loop in the frontends decides any limit."""
import os
from . import als_io
from .models import SampleRef

class AbletonAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        self._root = None

    @property
    def root(self):
        if self._root is None:
            self._root, _ = als_io.read_als(self.filepath)
        return self._root

    def bpm(self):
        t = self.root.find(".//Tempo/Manual")
        if t is not None and "Value" in t.attrib:
            return float(t.attrib["Value"])
        return 120.0

    def track_counts(self):
        a = len(self.root.findall(".//AudioTrack"))
        m = len(self.root.findall(".//MidiTrack"))
        return {"audio": a, "midi": m, "total": a + m}

    def sample_refs(self):
        """All FileRefs as SampleRef records (incl. video). Empty placeholders
        (no relpath and no abspath) are skipped."""
        out = []
        for fr in self.root.findall(".//FileRef"):
            rel = _attr(fr, "RelativePath")
            ab = _attr(fr, "Path")
            if not (rel or ab):
                continue
            try:
                rtype = int(_attr(fr, "RelativePathType") or 0)
            except ValueError:
                rtype = 0
            out.append(SampleRef(
                rtype=rtype, relpath=rel, abspath=ab,
                name=os.path.basename(rel or ab),
                size=_int(_attr(fr, "OriginalFileSize")),
                crc=_int(_attr(fr, "OriginalCrc")),
            ))
        return out

def _attr(el, tag):
    c = el.find(tag)
    return c.attrib.get("Value", "") if c is not None else ""

def _int(s):
    try:
        return int(s or 0)
    except ValueError:
        return 0
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run --extra dev pytest tests/test_analyzer.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/music_manager_mcp/core/analyzer.py tests/test_analyzer.py
git commit -m "feat(core): analyzer with full FileRef extraction (size/crc/video)"
```

---

## Task 5: `core/samples.py` — Live-faithful SampleResolver

**Files:**
- Create: `src/music_manager_mcp/core/samples.py`
- Test: `tests/test_samples.py`

Replaces the naïve `_detect_missing_samples`. Resolution order (how Live does it):
relative-to-project → absolute → missing. Library/factory refs are classified out.
Ported from `sample_index.py` (`is_factory`, `abs_exists`, relative resolution).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_samples.py
import os
from music_manager_mcp.core.samples import SampleResolver
from music_manager_mcp.core.models import SampleRef

def test_resolves_relative_when_collected(tmp_path):
    proj = tmp_path / "Song Project"
    samp = proj / "Samples" / "Imported"
    samp.mkdir(parents=True)
    (samp / "kick.wav").write_bytes(b"x")
    ref = SampleRef(3, "Samples/Imported/kick.wav", "/STALE/kick.wav", "kick.wav", 1)
    r = SampleResolver().resolve(ref, str(proj))
    assert r.status == "ok_relative"
    assert r.resolved_path.endswith("Samples/Imported/kick.wav")

def test_resolves_absolute_when_present(tmp_path):
    f = tmp_path / "loose.wav"; f.write_bytes(b"x")
    ref = SampleRef(0, "", str(f), "loose.wav", 1)
    r = SampleResolver().resolve(ref, str(tmp_path / "Song Project"))
    assert r.status == "ok_absolute"

def test_missing_when_neither_resolves(tmp_path):
    ref = SampleRef(0, "", "/nope/x.wav", "x.wav", 1)
    r = SampleResolver().resolve(ref, str(tmp_path / "P"))
    assert r.status == "missing"

def test_library_refs_classified_out():
    ref = SampleRef(5, "Devices/Audio Effects/EQ Eight",
                    "/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/Core Library/Devices/EQ Eight",
                    "EQ Eight")
    r = SampleResolver().resolve(ref, "/whatever")
    assert r.status == "library"
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --extra dev pytest tests/test_samples.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `core/samples.py`**

```python
"""Live-faithful sample resolution: relative-to-project → absolute → missing,
with library/factory classification. Mount-availability is checked once per
volume to avoid stalls on unmounted /Volumes paths."""
import os
from .models import ResolvedRef

_LIBRARY_HINTS = ("/applications/", "core library", "/factory packs/",
                  "user library", "ableton live ", "/packs/", "max for live")

class SampleResolver:
    def __init__(self):
        self._vol_avail = {}

    def _abs_exists(self, p):
        if not p:
            return False
        if p.startswith("/Volumes/"):
            vol = "/Volumes/" + p.split("/")[2] if len(p.split("/")) > 2 else p
            if vol not in self._vol_avail:
                self._vol_avail[vol] = os.path.exists(vol)   # stat mount point only
            return self._vol_avail[vol] and os.path.exists(p)
        return os.path.exists(p)

    @staticmethod
    def _is_library(ref):
        pl = (ref.abspath or "").lower()
        return ref.rtype == 5 or ref.relpath.startswith("Devices/") \
            or any(h in pl for h in _LIBRARY_HINTS)

    def resolve(self, ref, project_dir):
        if self._is_library(ref):
            return ResolvedRef(ref, "library")
        if ref.relpath:
            rp = os.path.normpath(os.path.join(project_dir, ref.relpath))
            if os.path.exists(rp):
                return ResolvedRef(ref, "ok_relative", rp)
        if self._abs_exists(ref.abspath):
            return ResolvedRef(ref, "ok_absolute", ref.abspath)
        return ResolvedRef(ref, "missing")
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run --extra dev pytest tests/test_samples.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/music_manager_mcp/core/samples.py tests/test_samples.py
git commit -m "feat(core): Live-faithful SampleResolver (replaces naive missing check)"
```

---

## Task 6: `core/index.py` — SampleIndex (name+size → paths)

**Files:**
- Create: `src/music_manager_mcp/core/index.py`
- Test: `tests/test_index.py`

Ported from `reconnect_match.py`. Builds `name(lower) → [(size, path)]` over source
roots (audio+video), with a path-translation hook for network mounts. `match(name, size)`
returns the best path: exact (name+size) first, else any name match (lower confidence),
**never a size-mismatch as exact**.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_index.py
from music_manager_mcp.core.index import SampleIndex

def test_builds_and_exact_matches_by_name_and_size(tmp_path):
    a = tmp_path / "driveA"; a.mkdir()
    (a / "kick.wav").write_bytes(b"1234567890")   # 10 bytes
    idx = SampleIndex()
    idx.add_root(str(a))
    m = idx.match("kick.wav", 10)
    assert m is not None and m.path.endswith("driveA/kick.wav") and m.exact is True

def test_size_mismatch_is_not_exact(tmp_path):
    a = tmp_path / "driveA"; a.mkdir()
    (a / "kick.wav").write_bytes(b"123")           # 3 bytes
    idx = SampleIndex(); idx.add_root(str(a))
    m = idx.match("kick.wav", 999)                 # different size
    assert m is None or m.exact is False           # never claim exact

def test_no_match_returns_none(tmp_path):
    idx = SampleIndex(); idx.add_root(str(tmp_path))
    assert idx.match("ghost.wav", 1) is None

def test_path_translation_hook(tmp_path):
    a = tmp_path / "Volumes" / "wer"; a.mkdir(parents=True)
    (a / "x.wav").write_bytes(b"xx")
    idx = SampleIndex(translate=lambda p: p)  # identity here; real use maps /Users/wer→/Volumes/wer
    idx.add_root(str(a))
    assert idx.match("x.wav", 2) is not None
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --extra dev pytest tests/test_index.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `core/index.py`**

```python
"""Master source index: name(lower) → [(size, path)] over source roots (audio+video).
match() prefers exact name+size; falls back to name-only (flagged non-exact); never
returns a size-mismatch as exact."""
import os
from collections import defaultdict
from dataclasses import dataclass
from .models import MEDIA_EXTS

@dataclass
class Match:
    path: str
    size: int
    exact: bool

class SampleIndex:
    def __init__(self, translate=None):
        self._by_name = defaultdict(list)   # name -> [(size, path)]
        self._translate = translate or (lambda p: p)

    def add_root(self, root):
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if os.path.splitext(fn)[1].lower() not in MEDIA_EXTS:
                    continue
                p = self._translate(os.path.join(dirpath, fn))
                try:
                    sz = os.path.getsize(os.path.join(dirpath, fn))
                except OSError:
                    sz = 0
                self._by_name[fn.lower()].append((sz, p))

    def add_entry(self, name, size, path):
        self._by_name[os.path.basename(name).lower()].append((int(size or 0), self._translate(path)))

    def match(self, name, size):
        cands = self._by_name.get(os.path.basename(name).lower(), [])
        if not cands:
            return None
        if size:
            for sz, path in cands:
                if sz == size:
                    return Match(path, sz, True)
        # name-only fallback (lower confidence) — only when no size to check
        if not size:
            sz, path = cands[0]
            return Match(path, sz, False)
        return None   # had a size, nothing matched it → not exact, no guess
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run --extra dev pytest tests/test_index.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/music_manager_mcp/core/index.py tests/test_index.py
git commit -m "feat(core): SampleIndex name+size matching (audio+video)"
```

---

## Task 7: `core/reconnect.py` — ReconnectEngine (relink + collect)

**Files:**
- Create: `src/music_manager_mcp/core/reconnect.py`
- Test: `tests/test_reconnect.py`

The engine. Both modes route every write through `als_io.write_als`. Ported from
`relink_engine.py` (relink) and `localize_wer.py` (the collect/copy variant).
Contract: dry-run does no writes; relink rewrites the `Path` of missing media refs to
the matched location; collect copies into `<project>/Samples/Imported/` and sets a
project-relative `RelativePathType=3` ref while keeping the absolute path as fallback;
both are idempotent (already-resolving refs are skipped); name+size match only.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reconnect.py
import os, gzip
import xml.etree.ElementTree as ET
from music_manager_mcp.core.reconnect import ReconnectEngine
from music_manager_mcp.core.index import SampleIndex
from music_manager_mcp.core.analyzer import AbletonAnalyzer

def _setup(make_als, tmp_path, size=10):
    proj = tmp_path / "Song Project"; proj.mkdir(parents=True)
    als = make_als(str(proj / "Song.als"),
                   [{"rtype": 0, "relpath": "", "abspath": "/STALE/kick.wav",
                     "name": "kick.wav", "size": size}])
    src = tmp_path / "driveA"; src.mkdir()
    (src / "kick.wav").write_bytes(b"x" * size)   # exact size match
    idx = SampleIndex(); idx.add_root(str(src))
    return als, idx, proj

def test_dry_run_writes_nothing(make_als_fixture, tmp_path):
    als, idx, _ = _setup(make_als_fixture, tmp_path)
    before = open(als, "rb").read()
    res = ReconnectEngine(idx, backup_dir=str(tmp_path / "bak")).relink(als, dry_run=True)
    assert res.relinked == 1
    assert open(als, "rb").read() == before   # unchanged

def test_relink_rewrites_path_and_backs_up(make_als_fixture, tmp_path):
    als, idx, _ = _setup(make_als_fixture, tmp_path)
    res = ReconnectEngine(idx, backup_dir=str(tmp_path / "bak")).relink(als, dry_run=False)
    assert res.relinked == 1 and res.backup
    newpath = AbletonAnalyzer(als).sample_refs()[0].abspath
    assert newpath.endswith("driveA/kick.wav") and os.path.exists(newpath)

def test_relink_idempotent(make_als_fixture, tmp_path):
    als, idx, _ = _setup(make_als_fixture, tmp_path)
    eng = ReconnectEngine(idx, backup_dir=str(tmp_path / "bak"))
    eng.relink(als, dry_run=False)
    res2 = eng.relink(als, dry_run=False)        # already resolves now
    assert res2.relinked == 0 and res2.status == "no_change"

def test_size_mismatch_is_not_relinked(make_als_fixture, tmp_path):
    als, idx, _ = _setup(make_als_fixture, tmp_path, size=10)
    # project expects a DIFFERENT size than the file on the drive
    proj = os.path.dirname(als)
    res = ReconnectEngine(idx, backup_dir=str(tmp_path / "bak")) \
        .relink(als, dry_run=False, expected_size_override=99999)
    assert res.relinked == 0
    assert "kick.wav" in res.remaining

def test_collect_copies_into_project_and_sets_relative(make_als_fixture, tmp_path):
    als, idx, proj = _setup(make_als_fixture, tmp_path)
    res = ReconnectEngine(idx, backup_dir=str(tmp_path / "bak")).collect(als, dry_run=False)
    assert res.relinked == 1
    ref = AbletonAnalyzer(als).sample_refs()[0]
    assert ref.rtype == 3 and ref.relpath.startswith("Samples/Imported/")
    assert os.path.exists(os.path.join(proj, "Samples", "Imported", "kick.wav"))
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --extra dev pytest tests/test_reconnect.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `core/reconnect.py`**

```python
"""ReconnectEngine: relink (rewrite Path to a matched source) and collect (copy into
the project + relative ref). Every write goes through als_io. Idempotent; name+size
match only; dry-run does no writes."""
import os, shutil
from . import als_io
from .analyzer import _attr
from .samples import SampleResolver
from .models import ReconnectResult, MEDIA_EXTS

class ReconnectEngine:
    def __init__(self, index, backup_dir):
        self.index = index
        self.backup_dir = backup_dir
        self.resolver = SampleResolver()

    def _missing_media_filerefs(self, root, project_dir):
        """Yield (FileRef element, name, size) for media refs that don't resolve."""
        from .models import SampleRef
        for fr in root.findall(".//FileRef"):
            rel = _attr(fr, "RelativePath"); ab = _attr(fr, "Path")
            if not (rel or ab):
                continue
            name = os.path.basename(rel or ab)
            if os.path.splitext(name)[1].lower() not in MEDIA_EXTS:
                continue
            try:
                rtype = int(_attr(fr, "RelativePathType") or 0)
            except ValueError:
                rtype = 0
            try:
                size = int(_attr(fr, "OriginalFileSize") or 0)
            except ValueError:
                size = 0
            ref = SampleRef(rtype, rel, ab, name, size)
            if self.resolver.resolve(ref, project_dir).status != "missing":
                continue
            yield fr, name, size

    def relink(self, als, dry_run=True, expected_size_override=None):
        root, decl = als_io.read_als(als)
        project_dir = os.path.dirname(als)
        n = 0; remaining = []
        for fr, name, size in self._missing_media_filerefs(root, project_dir):
            want = expected_size_override if expected_size_override is not None else size
            m = self.index.match(name, want)
            if not m or (want and not m.exact):
                remaining.append(name); continue
            _set_path(fr, m.path)
            n += 1
        return self._finish(als, root, decl, n, remaining, dry_run)

    def collect(self, als, dry_run=True):
        root, decl = als_io.read_als(als)
        project_dir = os.path.dirname(als)
        dest_dir = os.path.join(project_dir, "Samples", "Imported")
        n = 0; remaining = []
        for fr, name, size in self._missing_media_filerefs(root, project_dir):
            m = self.index.match(name, size)
            if not m or (size and not m.exact):
                remaining.append(name); continue
            if not dry_run:
                os.makedirs(dest_dir, exist_ok=True)
                dest = os.path.join(dest_dir, name)
                if not os.path.exists(dest):
                    shutil.copy2(m.path, dest)
            _set_collected(fr, name)            # rtype=3 + relative, keep abs fallback
            n += 1
        return self._finish(als, root, decl, n, remaining, dry_run)

    def _finish(self, als, root, decl, n, remaining, dry_run):
        uniq = sorted(set(remaining))
        if n == 0:
            return ReconnectResult(als, 0, uniq, None, "no_change")
        if dry_run:
            return ReconnectResult(als, n, uniq, None, "ok")
        backup = als_io.write_als(als, root, decl, self.backup_dir)
        return ReconnectResult(als, n, uniq, backup, "ok")

def _set_path(fr, new_abs):
    pe = fr.find("Path")
    if pe is None:
        import xml.etree.ElementTree as ET
        pe = ET.SubElement(fr, "Path")
    pe.set("Value", new_abs)

def _set_collected(fr, name):
    import xml.etree.ElementTree as ET
    def child(tag):
        c = fr.find(tag)
        if c is None:
            c = ET.SubElement(fr, tag)
        return c
    child("RelativePathType").set("Value", "3")
    child("RelativePath").set("Value", f"Samples/Imported/{name}")
    # absolute Path left as-is = dual-path fallback during cutover
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run --extra dev pytest tests/test_reconnect.py -v`
Expected: 5 passed.

- [ ] **Step 5: Wire `core/__init__.py` re-exports + full suite**

```python
# src/music_manager_mcp/core/__init__.py
from .analyzer import AbletonAnalyzer
from .samples import SampleResolver
from .index import SampleIndex
from .reconnect import ReconnectEngine
from .models import SampleRef, ResolvedRef, ReconnectResult
from .als_io import read_als, write_als, AlsWriteError
```

Run: `uv run --extra dev pytest -q`
Expected: all tests pass (als_io 3, models 2, analyzer 3, samples 4, index 4, reconnect 5).

- [ ] **Step 6: Commit**

```bash
git add src/music_manager_mcp/core/ tests/test_reconnect.py
git commit -m "feat(core): ReconnectEngine relink + collect (idempotent, dry-run, safe gzip)"
```

---

## Self-Review

**Spec coverage (against the design spec §2 core):** als_io ✓ (Task 2), analyzer w/ full FileRef incl. size/crc/video ✓ (Task 4), SampleResolver Live-faithful ✓ (Task 5), SampleIndex name+size audio+video ✓ (Task 6), ReconnectEngine relink+collect ✓ (Task 7), data model ✓ (Task 3). The gzip round-trip integrity test (spec §5) ✓ (Task 2). Idempotency + dry-run-writes-nothing + size-mismatch-never-relinked (spec §4) ✓ (Task 7 tests). The cap-lift (§4) is a frontend concern → Plan 2. Frontends, CI, PyPI, archive → Plan 2.

**Placeholder scan:** No TBD/TODO; every step has complete code + exact commands. The analyzer port (Task 4) intentionally implements only the v1 surface (bpm/tracks/sample_refs); other legacy methods stay in the un-touched `enhanced_analyzer.py` until Plan 2 retires it — this is explicit, not a placeholder.

**Type consistency:** `SampleRef`/`ResolvedRef`/`ReconnectResult` (Task 3) used consistently in Tasks 4–7. `_attr` defined in analyzer (Task 4) and imported by reconnect (Task 7). `Match` (Task 6) `.path/.size/.exact` used consistently in reconnect (Task 7). `als_io.read_als/write_als` signatures stable across Tasks 2/4/7.

---

## Plan 2 preview (written next, after Core is built/reviewed)
Frontends + release: MCP `resolve_samples` + `plan_reconnect` tools (read/plan, no writes) + lift the `MAX_FILES_TO_SCAN=100` cap; the `music-manager` argparse CLI (`analyze`/`resolve`/`index`/`reconnect --dry-run|--apply`); retire `enhanced_analyzer.py`; `.github/workflows/ci.yml` (ruff+pytest 3.10–3.12); version→`0.2.0`, CLI entry point, README/QUICKSTART, publish to PyPI.
