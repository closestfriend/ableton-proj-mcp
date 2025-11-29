#!/usr/bin/env python3
"""
Ableton Project Manager - Gradio Interface
Beautiful UI for the Ableton MCP Server
"""

import gradio as gr
import os
from pathlib import Path
from music_mcp import SafeAbletonProject, safe_scan_directory
import plotly.graph_objects as go
from datetime import datetime
from huggingface_hub import InferenceClient

# Custom CSS matching the mockup
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Space+Mono:wght@400;700&family=Cormorant+Garamond:wght@300;400&display=swap');

.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: linear-gradient(135deg, #e8e8e8 0%, #f5f5f5 100%) !important;
}

.header {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.5rem;
    font-weight: 300;
    letter-spacing: -0.02em;
    color: #2a2a2a;
    margin-bottom: 0.5rem;
}

.subtitle {
    font-size: 0.875rem;
    color: #888;
    font-weight: 300;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 2rem;
    border-bottom: 1px solid rgba(0,0,0,0.08);
    padding-bottom: 1rem;
}

.input-section {
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 12px !important;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04) !important;
}

.projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.project-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    position: relative;
}

.project-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, rgba(100, 100, 120, 0.3) 0%, rgba(100, 100, 120, 0) 100%);
}

.project-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
    border-color: rgba(100, 100, 120, 0.2);
}

.project-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.25rem;
    font-weight: 400;
    color: #2a2a2a;
    margin-bottom: 0.75rem;
    letter-spacing: -0.01em;
}

.project-meta {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin-bottom: 1rem;
}

.meta-item {
    display: flex;
    flex-direction: column;
}

.meta-label {
    font-size: 0.65rem;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.25rem;
    font-weight: 500;
}

.meta-value {
    font-family: 'Space Mono', monospace;
    font-size: 0.875rem;
    color: #4a4a5a;
}

.project-plugins {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.plugins-label {
    font-size: 0.65rem;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.plugin-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.plugin-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(100, 100, 120, 0.08);
    border-radius: 6px;
    font-size: 0.7rem;
    color: #5a5a6a;
    font-weight: 400;
    letter-spacing: 0.02em;
}

.stats-section {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04);
    margin-top: 2rem;
}

.stats-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.5rem;
    font-weight: 400;
    color: #2a2a2a;
    margin-bottom: 1.5rem;
    letter-spacing: -0.01em;
}

/* Swiss grid lines */
.grid-line {
    position: fixed;
    pointer-events: none;
    opacity: 0.03;
    z-index: 0;
}

.grid-line-vertical {
    width: 1px;
    height: 100%;
    background: #000;
    top: 0;
}

.grid-line-horizontal {
    height: 1px;
    width: 100%;
    background: #000;
    left: 0;
}

/* AI Assistant Section */
.chatbot-section {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04);
    margin-top: 2rem;
}

.chat-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.5rem;
    font-weight: 400;
    color: #2a2a2a;
    margin-bottom: 1.5rem;
    letter-spacing: -0.01em;
}
"""

def generate_project_card_html(project, analyzed=False):
    """Generate HTML for a single project card"""
    # Get plugin summary
    plugin_html = ""
    if analyzed and project.plugin_count > 0:
        # Count instances of each plugin
        plugin_counts = {}
        for _, plugin_name in project.plugins:
            plugin_counts[plugin_name] = plugin_counts.get(plugin_name, 0) + 1
        
        plugin_tags = []
        for plugin, count in list(plugin_counts.items())[:5]:  # Show top 5
            display = f"{plugin} × {count}" if count > 1 else plugin
            plugin_tags.append(f'<span class="plugin-tag" style="padding: 0.25rem 0.75rem; background: rgba(100, 100, 120, 0.08); border-radius: 6px; font-size: 0.7rem; color: #5a5a6a; margin-right: 0.5rem; margin-bottom: 0.5rem; display: inline-block;">{display}</span>')

        plugin_html = f"""
        <div class="project-plugins" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(0, 0, 0, 0.06);">
            <div class="plugins-label" style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; font-weight: 500;">Plugins</div>
            <div class="plugin-tags" style="display: flex; flex-wrap: wrap;">
                {''.join(plugin_tags)}
            </div>
        </div>
        """
    
    # Build meta values
    bpm_value = f"{project.bpm} BPM" if analyzed and project.bpm else "—"
    tracks_value = f"{project.track_count} Total" if analyzed else "—"
    
    return f"""
    <div class="project-card">
        <h3 class="project-title">{project.filename.replace('.als', '')}</h3>
        <div class="project-meta">
            <div class="meta-item">
                <span class="meta-label">Tempo</span>
                <span class="meta-value">{bpm_value}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Tracks</span>
                <span class="meta-value">{tracks_value}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Modified</span>
                <span class="meta-value">{project.last_modified}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Size</span>
                <span class="meta-value">{project.size_mb} MB</span>
            </div>
        </div>
        {plugin_html}
    </div>
    """

def scan_and_display(directory, analyze_all=False):
    """Scan directory and return HTML grid of projects"""
    if not directory or not os.path.exists(directory):
        return "<p style='color: #999; text-align: center; padding: 2rem;'>Please enter a valid directory path</p>", None, []

    try:
        projects, hit_limit = safe_scan_directory(directory)

        if not projects:
            return "<p style='color: #999; text-align: center; padding: 2rem;'>No Ableton projects found in this directory</p>", None, []

        # Optionally analyze all projects
        if analyze_all and len(projects) <= 20:
            for proj in projects:
                proj.analyze()

        # Generate cards
        cards = [generate_project_card_html(proj, analyze_all) for proj in projects]

        html = f'<div class="projects-grid">{"".join(cards)}</div>'

        # Generate BPM chart if analyzed
        chart = None
        if analyze_all:
            chart = create_bpm_chart(projects)

        return html, chart, projects

    except Exception as e:
        return f"<p style='color: #ff6b6b; padding: 2rem;'>Error: {str(e)}</p>", None, []

def create_bpm_chart(projects):
    """Create a BPM distribution chart using Plotly"""
    # Filter projects with BPM data
    bpms = [p.bpm for p in projects if p.bpm is not None]
    
    if not bpms:
        return None
    
    # Create histogram
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=bpms,
        nbinsx=20,
        marker=dict(
            color='rgba(100, 100, 120, 0.6)',
            line=dict(color='rgba(100, 100, 120, 0.8)', width=1)
        ),
        hovertemplate='BPM Range: %{x}<br>Projects: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="BPM Distribution",
            font=dict(family="Cormorant Garamond", size=20, color="#2a2a2a"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="BPM",
        yaxis_title="Number of Projects",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", size=12, color="#666"),
        margin=dict(t=60, b=40, l=40, r=40),
        hovermode='x unified',
        showlegend=False
    )
    
    # Update axes styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.05)',
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.05)',
        zeroline=False
    )
    
    return fig

def find_recent_projects(directory, limit=10):
    """Find and display recent projects"""
    if not directory or not os.path.exists(directory):
        return "<p style='color: #999; text-align: center; padding: 2rem;'>Please enter a valid directory path</p>"

    try:
        projects, _ = safe_scan_directory(directory)

        if not projects:
            return "<p style='color: #999; text-align: center; padding: 2rem;'>No projects found</p>"

        # Sort by modification time
        projects.sort(key=lambda p: os.path.getmtime(p.filepath), reverse=True)
        recent = projects[:limit]

        # Analyze the recent projects
        for proj in recent:
            proj.analyze()

        cards = [generate_project_card_html(proj, True) for proj in recent]
        return f'<div class="projects-grid">{"".join(cards)}</div>'

    except Exception as e:
        return f"<p style='color: #ff6b6b; padding: 2rem;'>Error: {str(e)}</p>"

def handle_uploaded_files(files, analyze_all=False):
    """Handle uploaded .als files and display analysis"""
    if not files or len(files) == 0:
        return "<p style='color: #999; text-align: center; padding: 2rem;'>Please upload some .als files</p>", None, []

    try:
        projects = []

        # In Gradio 6, files is a list of file paths (strings)
        # Handle both single file and list of files
        file_list = files if isinstance(files, list) else [files]

        # Process each uploaded file
        for file_path in file_list:
            try:
                # file_path is the path to the uploaded file
                if not file_path:
                    continue

                print(f"Processing file: {file_path}")
                proj = SafeAbletonProject(file_path)

                # Analyze if requested
                if analyze_all:
                    print(f"Analyzing: {file_path}")
                    proj.analyze()

                projects.append(proj)
                print(f"Successfully processed: {proj.filename}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                import traceback
                traceback.print_exc()
                continue

        if not projects:
            return "<p style='color: #999; text-align: center; padding: 2rem;'>No valid Ableton projects found in uploads</p>", None, []

        print(f"Total projects processed: {len(projects)}")

        # Generate cards
        cards = [generate_project_card_html(proj, analyze_all) for proj in projects]
        html = f'<div class="projects-grid">{"".join(cards)}</div>'

        # Generate BPM chart if analyzed
        chart = None
        if analyze_all:
            chart = create_bpm_chart(projects)

        return html, chart, projects

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<p style='color: #ff6b6b; padding: 2rem;'>Error: {str(e)}</p>", None, []

def load_example_projects(analyze_all=False):
    """Load pre-packaged example projects"""
    # Check if examples directory exists
    examples_dir = os.path.join(os.path.dirname(__file__), "examples")

    if not os.path.exists(examples_dir):
        return """
        <div style='text-align: center; padding: 3rem; color: #666;'>
            <h3 style='font-family: "Cormorant Garamond"; margin-bottom: 1rem;'>No Example Projects Found</h3>
            <p>To use example projects, create an <code>examples/</code> directory and add .als files.</p>
            <p style='margin-top: 1rem; font-size: 0.9em;'>For now, try uploading your own files or scanning a local directory!</p>
        </div>
        """, None, []

    try:
        projects, _ = safe_scan_directory(examples_dir)

        if not projects:
            return "<p style='color: #999; text-align: center; padding: 2rem;'>No example projects found in examples/ directory</p>", None, []

        # Analyze all example projects
        if analyze_all:
            for proj in projects:
                proj.analyze()

        # Generate cards
        cards = [generate_project_card_html(proj, analyze_all) for proj in projects]
        html = f'<div class="projects-grid">{"".join(cards)}</div>'

        # Generate BPM chart if analyzed
        chart = None
        if analyze_all:
            chart = create_bpm_chart(projects)

        return html, chart, projects

    except Exception as e:
        return f"<p style='color: #ff6b6b; padding: 2rem;'>Error: {str(e)}</p>", None, []

def format_projects_as_context(projects):
    """Format project data as context for Claude"""
    if not projects:
        return "No projects have been scanned yet."

    context_parts = ["You are analyzing Ableton Live projects. Here's the data:\n"]

    for i, proj in enumerate(projects, 1):
        # Get plugin summary
        plugin_summary = "None"
        if proj.plugin_count > 0:
            plugin_counts = {}
            for _, plugin_name in proj.plugins:
                plugin_counts[plugin_name] = plugin_counts.get(plugin_name, 0) + 1

            plugin_list = [f"{plugin} (×{count})" if count > 1 else plugin
                          for plugin, count in list(plugin_counts.items())[:10]]
            plugin_summary = ", ".join(plugin_list)

        # Calculate days since modification
        try:
            mod_time = os.path.getmtime(proj.filepath)
            days_ago = (datetime.now().timestamp() - mod_time) / 86400
            if days_ago < 1:
                time_ago = "today"
            elif days_ago < 2:
                time_ago = "yesterday"
            else:
                time_ago = f"{int(days_ago)} days ago"
        except:
            time_ago = proj.last_modified

        context_parts.append(f"""
Project {i}: "{proj.filename.replace('.als', '')}"
- BPM: {proj.bpm if proj.bpm else 'Unknown'}
- Tracks: {proj.track_count} total ({proj.audio_track_count} audio, {proj.midi_track_count} MIDI)
- Plugins: {plugin_summary}
- Modified: {time_ago}
- Size: {proj.size_mb} MB
- Path: {proj.filepath}
""")

    context_parts.append("\nBased on this data, answer the user's question with specific recommendations and reasoning.")
    return "".join(context_parts)

def chat_with_claude(message, chat_history, projects_data):
    """Send message to HuggingFace model with project context"""

    # Check if API token exists
    api_token = os.environ.get("HF_TOKEN")
    if not api_token:
        error_msg = """To use the AI assistant, you need to set up your HuggingFace token:

1. Get your token from https://huggingface.co/settings/tokens
2. Set the environment variable:
   export HF_TOKEN='your-token-here'
3. Restart the app

The AI assistant will analyze your projects and provide personalized recommendations."""
        chat_history.append((message, error_msg))
        return chat_history

    # Check if projects have been scanned
    if not projects_data or len(projects_data) == 0:
        chat_history.append((message, "Please scan a directory first so I can analyze your projects."))
        return chat_history

    try:
        # Initialize HuggingFace client
        client = InferenceClient(token=api_token)

        # Format context
        context = format_projects_as_context(projects_data)

        # Build conversation history
        messages = []

        # Add system message with context
        messages.append({
            "role": "system",
            "content": str(f"{context}\n\nYou are an AI assistant helping musicians analyze their Ableton Live projects. Provide specific, data-driven recommendations based on the project information above.")
        })

        # Add conversation history
        for user_msg, assistant_msg in chat_history:
            if user_msg and assistant_msg:  # Skip empty messages
                messages.append({"role": "user", "content": str(user_msg)})
                messages.append({"role": "assistant", "content": str(assistant_msg)})

        # Add current message
        messages.append({
            "role": "user",
            "content": str(message)
        })

        # Call HuggingFace API
        # Using Qwen2.5-72B-Instruct - excellent for reasoning tasks
        response = client.chat_completion(
            messages=messages,
            model="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=1024,
            temperature=0.7
        )

        # Extract response text
        assistant_message = response.choices[0].message.content

        # Add to chat history
        chat_history.append((message, str(assistant_message)))

        return chat_history

    except Exception as e:
        error_msg = f"Error: {str(e)}\n\nPlease check your HF_TOKEN and try again. Make sure you have access to the model."
        chat_history.append((message, error_msg))
        return chat_history

# Build the Gradio interface
with gr.Blocks(title="Ableton Project Manager") as demo:
    # State management
    projects_state = gr.State([])

    # Swiss grid lines
    gr.HTML("""
        <div class="grid-line grid-line-vertical" style="left: 20%;"></div>
        <div class="grid-line grid-line-vertical" style="left: 40%;"></div>
        <div class="grid-line grid-line-vertical" style="left: 60%;"></div>
        <div class="grid-line grid-line-vertical" style="left: 80%;"></div>
        <div class="grid-line grid-line-horizontal" style="top: 33%;"></div>
        <div class="grid-line grid-line-horizontal" style="top: 66%;"></div>
    """)

    # Header
    gr.HTML('<h1 class="header">Ableton Project Manager</h1>')
    gr.HTML('<p class="subtitle">MCP Server · Project Analysis & Discovery</p>')

    # Tabbed interface for different input methods
    with gr.Tabs():
        # Tab 1: Scan Local Directory
        with gr.Tab("📁 Scan Local Directory"):
            with gr.Group(elem_classes="input-section"):
                with gr.Row():
                    directory_input = gr.Textbox(
                        label="Project Directory",
                        placeholder="~/Music/Ableton/Projects",
                        value=os.path.expanduser("~/Music/Ableton"),
                        scale=3
                    )
                    local_analyze_checkbox = gr.Checkbox(
                        label="Deep Analysis (slower, includes BPM/plugins)",
                        value=False,
                        scale=1
                    )

                with gr.Row():
                    scan_btn = gr.Button("Scan Projects", variant="primary")
                    recent_btn = gr.Button("Find Recent (10)", variant="secondary")

        # Tab 2: Upload Files
        with gr.Tab("📤 Upload Files"):
            with gr.Group(elem_classes="input-section"):
                gr.Markdown("""
                ### Upload Your Ableton Projects
                Drag and drop your .als files here to analyze them instantly.
                Perfect for testing without local setup!
                """)

                upload_files = gr.File(
                    file_count="multiple",
                    file_types=[".als"],
                    label="Drop .als files here",
                    height=200
                )

                upload_analyze_checkbox = gr.Checkbox(
                    label="Deep Analysis (includes BPM/plugins)",
                    value=True
                )

                upload_btn = gr.Button("Analyze Uploaded Files", variant="primary", size="lg")

        # Tab 3: Example Projects
        with gr.Tab("✨ Example Projects"):
            with gr.Group(elem_classes="input-section"):
                gr.Markdown("""
                ### Try Pre-Loaded Examples
                Instantly explore curated Ableton projects to see how the analysis works.
                No upload or local files needed!
                """)

                examples_analyze_checkbox = gr.Checkbox(
                    label="Deep Analysis (includes BPM/plugins)",
                    value=True
                )

                examples_btn = gr.Button("Load Example Projects", variant="primary", size="lg")

    # Projects output (shared across all tabs)
    projects_output = gr.HTML()

    # AI Assistant section
    with gr.Group(elem_classes="chatbot-section"):
        gr.HTML('<h2 class="chat-title">AI Assistant</h2>')
        chatbot = gr.Chatbot(
            label="Ask about your projects",
            height=400,
            show_label=False
        )
        with gr.Row():
            chat_input = gr.Textbox(
                placeholder="Ask about your projects... (e.g., 'Which project should I finish first?')",
                show_label=False,
                scale=4
            )
            chat_btn = gr.Button("Send", variant="primary", scale=1)

    # Stats section
    with gr.Group(elem_classes="stats-section", visible=False) as stats_group:
        gr.HTML('<h2 class="stats-title">Project Distribution</h2>')
        bpm_chart = gr.Plot()

    # Event handlers
    def scan_with_chart(directory, analyze):
        html, chart, projects = scan_and_display(directory, analyze)
        if chart:
            return html, chart, gr.update(visible=True), projects
        return html, None, gr.update(visible=False), projects

    def upload_with_chart(files, analyze):
        html, chart, projects = handle_uploaded_files(files, analyze)
        if chart:
            return html, chart, gr.update(visible=True), projects
        return html, None, gr.update(visible=False), projects

    def examples_with_chart(analyze):
        html, chart, projects = load_example_projects(analyze)
        if chart:
            return html, chart, gr.update(visible=True), projects
        return html, None, gr.update(visible=False), projects

    # Local directory scan handlers
    scan_btn.click(
        scan_with_chart,
        inputs=[directory_input, local_analyze_checkbox],
        outputs=[projects_output, bpm_chart, stats_group, projects_state]
    )

    recent_btn.click(
        find_recent_projects,
        inputs=[directory_input],
        outputs=[projects_output]
    )

    # Upload handlers
    upload_btn.click(
        upload_with_chart,
        inputs=[upload_files, upload_analyze_checkbox],
        outputs=[projects_output, bpm_chart, stats_group, projects_state]
    )

    # Examples handler
    examples_btn.click(
        examples_with_chart,
        inputs=[examples_analyze_checkbox],
        outputs=[projects_output, bpm_chart, stats_group, projects_state]
    )

    # Chat event handler
    def handle_chat(message, history, projects):
        if not message.strip():
            return history, ""
        new_history = chat_with_claude(message, history, projects)
        return new_history, ""

    chat_btn.click(
        handle_chat,
        inputs=[chat_input, chatbot, projects_state],
        outputs=[chatbot, chat_input]
    )

    chat_input.submit(
        handle_chat,
        inputs=[chat_input, chatbot, projects_state],
        outputs=[chatbot, chat_input]
    )
    
    # Footer
    gr.HTML("""
        <div style="text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid rgba(0,0,0,0.08);">
            <p style="font-size: 0.75rem; color: #999; letter-spacing: 0.05em; text-transform: uppercase;">
                Built with MCP · Gradio 6 · Plotly
            </p>
        </div>
    """)

if __name__ == "__main__":
    demo.launch(share=False, mcp_server=True)
