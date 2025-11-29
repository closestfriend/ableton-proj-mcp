# Demo Data Strategy for Judges

## Problem
Judges won't have Ableton projects to scan in the HuggingFace Space.

## Solution: Include Sample Projects

### 1. Create Sample Projects Folder
```
/sample-projects/
  ├── Dark_Techno_Idea.als
  ├── Bass_Experiment.als  
  ├── Ambient_Sketch_003.als
  ├── Club_Track_Draft.als
```

### 2. Modify app.py to:
- Add "Try Demo Projects" button
- Auto-load demo on first visit
- Show banner: "Viewing demo projects. Upload your own Ableton directory to analyze your music."

### 3. Sample Project Requirements
- **Small file sizes** (< 5MB each to keep Space lightweight)
- **Varied BPMs** (80, 128, 140, 160) to show chart
- **Different plugin counts** to show analysis depth
- **Recent modification dates** to demonstrate "find recent" feature

### 4. Where to Get Sample Projects
Options:
1. Use YOUR actual projects (safest - you own them)
2. Create minimal test projects in Ableton
3. Use open-source/CC0 Ableton projects if available

### 5. README Documentation
Add section:
```markdown
## For Judges / Demo

This Space includes sample Ableton projects for demonstration.

**Try It:**
1. Click "🎵 Try Demo Projects" 
2. Enable "Deep Analysis" to see BPM/plugin data
3. Ask the AI: "Which project should I finish first?"

**With Your Own Projects:**
Enter your Ableton projects directory path (requires local deployment)
```

## Implementation Steps

1. Export 3-4 small Ableton projects
2. Add to `/sample-projects/` folder in repo
3. Update `app.py` with demo button
4. Test that demo loads instantly
5. Record demo video showing both modes

## Expected Judge Experience

✅ **Immediate functionality** - Demo loads on visit
✅ **See all features** - Scan, analyze, chat, visualization
✅ **Understand value** - Works with real .als files
✅ **Optional deep dive** - Can test with their own projects (if they have Ableton)

This approach lets judges fully evaluate your submission without needing Ableton!
