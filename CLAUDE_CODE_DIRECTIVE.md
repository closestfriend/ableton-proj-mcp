# Claude Code Directive: Add AI Assistant to Gradio App

## Context
We have a beautiful Gradio app (`app.py`) for analyzing Ableton Live projects. It currently:
- Scans directories for .als files
- Analyzes BPM, track counts, plugin usage
- Displays data in frosted glass cards with Swiss design aesthetic
- Shows BPM distribution chart with Plotly

**Goal:** Add Claude API integration so users can ask questions about their projects and get AI-powered recommendations.

## What to Implement

### 1. Add Anthropic SDK Dependency
Update `requirements-gradio.txt` to include:
```
anthropic>=0.40.0
```

### 2. Add Chat Interface to UI

In `app.py`, after the existing projects_output and before the stats section, add:

- A new section with class "stats-section" for the AI assistant
- A `gr.Chatbot()` component styled to match our aesthetic
- A `gr.Textbox()` for user questions (placeholder: "Ask about your projects...")
- A `gr.Button()` to submit questions
- State management to track scanned projects data

### 3. Create Claude API Integration Function

Add a new function `chat_with_claude(message, chat_history, projects_data)` that:

1. Takes the user's question + current projects data
2. Formats a prompt for Claude that includes:
   - All scanned project metadata as context
   - User's question
   - Instructions to analyze and provide recommendations
3. Calls the Anthropic API (model: `claude-sonnet-4-20250514`)
4. Returns Claude's response

**API Call Structure:**
```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Build context from projects
context = format_projects_as_context(projects_data)

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": f"{context}\n\nUser question: {message}"}
    ]
)
```

### 4. Context Formatting Function

Add `format_projects_as_context(projects)` that creates a clean text summary:

```
You are analyzing Ableton Live projects. Here's the data:

Project 1: "Dark Techno Idea"
- BPM: 138
- Tracks: 12 total (8 audio, 4 MIDI)
- Plugins: Serum (7), Valhalla, FabFilter
- Modified: 2 days ago
- Size: 8.4 MB

Project 2: "Bass Experiment"
...

Based on this data, answer the user's question with specific recommendations and reasoning.
```

### 5. Wire Up the Chat Interface

Connect the chat button to trigger:
1. Get the latest projects data from state
2. Call `chat_with_claude()`
3. Update the chatbot component with the response
4. Maintain conversation history

### 6. Add State Management

Use `gr.State()` to store:
- Current scanned projects data
- Whether projects have been analyzed

Update the scan button click handler to also populate this state.

### 7. Error Handling

Handle cases where:
- No projects have been scanned yet (show friendly message)
- API key is missing (show setup instructions)
- API call fails (show error, don't crash)

### 8. Styling Consistency

The chat interface should match our aesthetic:
- Use same color palette (#5a5a6a, #4a4a5a)
- Frosted glass background
- Cormorant Garamond headers
- Space Mono for code/data references

Add CSS for `.chatbot-section` that matches `.stats-section`.

## Example User Flows

**Flow 1: Project Recommendation**
1. User scans directory with deep analysis
2. User asks: "Which project should I finish first?"
3. Claude analyzes track counts, plugins, BPM, modification dates
4. Responds with specific recommendation and reasoning

**Flow 2: Creative Advice**
1. User scans projects
2. User asks: "What BPM range am I most comfortable in?"
3. Claude analyzes BPM distribution
4. Provides insights about user's style preferences

**Flow 3: Technical Query**
1. User asks: "Which projects use the most CPU-heavy plugins?"
2. Claude identifies projects with lots of Serum/Omnisphere instances
3. Suggests which to bounce/freeze tracks in

## Technical Requirements

- Keep all existing functionality intact
- Don't modify the current scan/analyze features
- Add the chat as a new section below projects display
- API key should come from environment variable `ANTHROPIC_API_KEY`
- Gracefully degrade if API key is missing (show setup message)
- Preserve all existing CSS and styling

## Success Criteria

✓ Users can scan projects (existing functionality)
✓ Users can ask questions about their projects
✓ Claude receives full project context
✓ Responses are displayed in a styled chatbot
✓ Conversation history is maintained
✓ Error cases are handled gracefully
✓ Design aesthetic is preserved

## Files to Modify

1. `app.py` - Add chat interface and API integration
2. `requirements-gradio.txt` - Add anthropic SDK

## Testing

After implementation, test:
1. Scan a directory
2. Ask: "What's my average BPM?"
3. Ask: "Which project has the most plugins?"
4. Ask: "Recommend a project to work on based on the data"

All should work with Claude providing contextual, data-driven responses.

## Notes

- This makes the app a true "MCP in Action" submission
- Demonstrates agentic behavior (reasoning about user's creative work)
- Shows LLM integration with real-world data
- Maintains the beautiful Swiss design aesthetic
- Adds significant value beyond just data display

---

**Priority:** Implement cleanly and maintain existing code quality. The goal is to enhance, not replace, the current beautiful interface.
