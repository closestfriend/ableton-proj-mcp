# Configuration Notes

## Safety Settings

Located at the top of `music_mcp.py`:

```python
MAX_FILES_TO_SCAN = 100  # Stop after this many .als files
MAX_FILE_SIZE_MB = 50    # Skip files larger than this
SCAN_DEPTH = 3           # Only go 3 folders deep
```

### When to Adjust

**Increase MAX_FILES_TO_SCAN if:**
- You have more than 100 projects in a folder
- Getting "Hit safety limit" messages
- Want to scan your entire collection at once

**Increase MAX_FILE_SIZE_MB if:**
- You regularly work on huge projects with lots of samples
- Getting "File too large" errors
- Your projects are typically 50MB+

**Increase SCAN_DEPTH if:**
- Your projects are nested more than 3 folders deep
- Missing projects you know exist
- Have a complex folder structure

### Example Settings

**Conservative** (for huge libraries):
```python
MAX_FILES_TO_SCAN = 50
MAX_FILE_SIZE_MB = 30
SCAN_DEPTH = 2
```

**Aggressive** (for complete scanning):
```python
MAX_FILES_TO_SCAN = 500
MAX_FILE_SIZE_MB = 200
SCAN_DEPTH = 5
```

**Balanced** (default):
```python
MAX_FILES_TO_SCAN = 100
MAX_FILE_SIZE_MB = 50
SCAN_DEPTH = 3
```

## Auto-Skipped Folders

The scanner automatically skips these common heavy folders:
- `Backup`
- `Samples`
- `Presets`
- `Library`
- `Cache`
- `Recordings`
- `Rendered`

This prevents scanning thousands of sample files or auto-backups.

### To Add More Skip Folders

In `music_mcp.py`, find this line and add your folders:

```python
dirs[:] = [d for d in dirs if d not in [
    'Backup', 'Samples', 'Presets', 'Library', 
    'Cache', 'Recordings', 'Rendered',
    'YOUR_FOLDER_HERE'  # Add here
]]
```

## Performance Tips

1. **Scan specific folders first**: `/WERK/Current` instead of `/WERK`
2. **Use find_recent**: Faster than full scan + sort
3. **Analyze in batches**: Max 20 projects at a time
4. **Skip backups**: Point to working projects, not backup drives

## Your Project Structure

Common patterns to optimize for:

### Pattern 1: Flat structure
```
/Music/Projects/
  ├── Project1.als
  ├── Project2.als
  └── Project3.als
```
**Best setting**: `SCAN_DEPTH = 1`

### Pattern 2: Year-based
```
/Music/Projects/
  ├── 2024/
  │   ├── Q1/
  │   │   └── Project1.als
  │   └── Q2/
  │       └── Project2.als
  └── 2025/
      └── Project3.als
```
**Best setting**: `SCAN_DEPTH = 3`

### Pattern 3: Complex organization
```
/WERK/
  ├── Active/
  │   ├── Client Work/
  │   │   └── Project.als
  │   └── Personal/
  │       └── Project.als
  └── Archive/
      └── Old/
          └── Project.als
```
**Best setting**: `SCAN_DEPTH = 4+`

---

After changing settings, restart Claude Desktop for changes to take effect.
