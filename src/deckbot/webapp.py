import os
import json
import time
import threading
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file, send_from_directory
from deckbot.manager import PresentationManager
from deckbot.session_service import SessionService
from deckbot.preferences import PreferencesManager
from deckbot.state import StateManager

app = Flask(__name__)

# Global service instance (single user for now)
current_service = None

@app.route('/')
def index():
    import time
    return render_template('chat.html', cache_bust=int(time.time()))

@app.route('/api/serve-image')
def serve_image():
    path = request.args.get('path')
    if not path or not os.path.exists(path):
        return "Image not found", 404
    return send_file(path)

@app.route('/api/presentation/preview')
def preview_presentation():
    global current_service
    if not current_service:
        return "No presentation loaded", 400
        
    pres_dir = current_service.agent.presentation_dir
    html_path = os.path.join(pres_dir, "deck.marp.html")
    
    if not os.path.exists(html_path):
        return "<h1>Presentation not compiled yet.</h1><p>Ask the agent to 'Show the deck' or 'Compile'.</p>"
    
    # Modify HTML to fix image paths before serving
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Replace relative image paths with API endpoint
    # images/file.png -> /api/presentation/images/file.png
    import re
    html_content = re.sub(
        r'(src|href)="images/([^"]+)"',
        r'\1="/api/presentation/images/\2"',
        html_content
    )
    html_content = re.sub(
        r'url\(&quot;images/([^&]+)&quot;\)',
        r'url(&quot;/api/presentation/images/\1&quot;)',
        html_content
    )
    
    # Add script to override Marp's fullscreen behavior to work properly in iframe
    control_script = """
<script>
(function() {
    console.log('[Marp Override] Script loaded');
    
    // Check if we're in an iframe
    const inIframe = window.parent !== window;
    console.log('[Marp Override] In iframe:', inIframe);
    
    if (inIframe) {
        // Get reference to parent's sidebar element
        let parentSidebar = null;
        try {
            parentSidebar = window.parent.document.querySelector('.sidebar');
            console.log('[Marp Override] Found parent sidebar:', !!parentSidebar);
        } catch (e) {
            console.log('[Marp Override] Cannot access parent document (CORS?):', e.message);
        }
        
        // Override requestFullscreen methods IMMEDIATELY before Marp loads
        const originalRequestFullscreen = HTMLElement.prototype.requestFullscreen;
        const originalWebkitRequestFullscreen = HTMLElement.prototype.webkitRequestFullscreen;
        const originalExitFullscreen = Document.prototype.exitFullscreen;
        const originalWebkitExitFullscreen = Document.prototype.webkitExitFullscreen;
        
        // Override requestFullscreen to trigger on parent's sidebar
        HTMLElement.prototype.requestFullscreen = function() {
            console.log('[Marp Override] requestFullscreen() called on', this.tagName);
            console.log('[Marp Override] parentSidebar:', parentSidebar);
            console.log('[Marp Override] originalRequestFullscreen:', typeof originalRequestFullscreen);
            
            if (parentSidebar) {
                // We can access parent - call fullscreen directly (maintains user gesture)
                console.log('[Marp Override] Calling requestFullscreen on parent sidebar');
                console.log('[Marp Override] parentSidebar.requestFullscreen:', typeof parentSidebar.requestFullscreen);
                
                try {
                    // Check fullscreen capability
                    console.log('[Marp Override] document.fullscreenEnabled:', window.parent.document.fullscreenEnabled);
                    console.log('[Marp Override] Sidebar style.display:', window.parent.getComputedStyle(parentSidebar).display);
                    console.log('[Marp Override] Sidebar offsetWidth:', parentSidebar.offsetWidth);
                    console.log('[Marp Override] Sidebar offsetHeight:', parentSidebar.offsetHeight);
                    
                    const result = originalRequestFullscreen.call(parentSidebar);
                    console.log('[Marp Override] Call result:', result);
                    console.log('[Marp Override] Result is Promise:', result instanceof Promise);
                    
                    // Add multiple checks
                    setTimeout(() => {
                        console.log('[Marp Override] After 100ms - fullscreenElement:', window.parent.document.fullscreenElement);
                    }, 100);
                    
                    setTimeout(() => {
                        console.log('[Marp Override] After 1000ms - fullscreenElement:', window.parent.document.fullscreenElement);
                    }, 1000);
                    
                    if (result && result.then) {
                        result.then(() => {
                            console.log('[Marp Override] ✓✓✓ Fullscreen PROMISE RESOLVED ✓✓✓');
                        }).catch(err => {
                            console.error('[Marp Override] ✗✗✗ Fullscreen PROMISE REJECTED ✗✗✗');
                            console.error('[Marp Override] Error:', err);
                        });
                    }
                    
                    // Listen for fullscreenchange events
                    const fsChangeHandler = () => {
                        console.log('[Marp Override] fullscreenchange EVENT fired!');
                        console.log('[Marp Override] fullscreenElement is now:', window.parent.document.fullscreenElement);
                    };
                    window.parent.document.addEventListener('fullscreenchange', fsChangeHandler, { once: true });
                    window.parent.document.addEventListener('webkitfullscreenchange', fsChangeHandler, { once: true });
                    
                    return result;
                } catch (err) {
                    console.error('[Marp Override] Exception calling requestFullscreen:', err);
                    return Promise.reject(err);
                }
            } else {
                // Cannot access parent (CORS) - send message instead
                console.log('[Marp Override] Sending message to parent');
                window.parent.postMessage('marp:fullscreen', window.location.origin);
                return Promise.resolve();
            }
        };
        
        if (originalWebkitRequestFullscreen) {
            HTMLElement.prototype.webkitRequestFullscreen = function() {
                console.log('[Marp Override] webkitRequestFullscreen() called on', this.tagName);
                
                if (parentSidebar && parentSidebar.webkitRequestFullscreen) {
                    console.log('[Marp Override] Calling webkitRequestFullscreen on parent sidebar');
                    parentSidebar.webkitRequestFullscreen();
                } else {
                    window.parent.postMessage('marp:fullscreen', window.location.origin);
                }
            };
        }
        
        // Override exitFullscreen
        Document.prototype.exitFullscreen = function() {
            console.log('[Marp Override] exitFullscreen() called');
            
            try {
                if (originalExitFullscreen) {
                    return originalExitFullscreen.call(window.parent.document);
                }
            } catch (e) {
                window.parent.postMessage('marp:fullscreen', window.location.origin);
            }
            return Promise.resolve();
        };
        
        if (originalWebkitExitFullscreen) {
            Document.prototype.webkitExitFullscreen = function() {
                console.log('[Marp Override] webkitExitFullscreen() called');
                try {
                    if (window.parent.document.webkitExitFullscreen) {
                        window.parent.document.webkitExitFullscreen();
                    }
                } catch (e) {
                    window.parent.postMessage('marp:fullscreen', window.location.origin);
                }
            };
        }
        
        console.log('[Marp Override] Fullscreen API overridden');
    }
    
    // Intercept presenter mode button clicks
    document.addEventListener('click', function(e) {
        const target = e.target;
        if (target && target.hasAttribute && target.hasAttribute('data-bespoke-marp-osc')) {
            const action = target.getAttribute('data-bespoke-marp-osc');
            console.log('[Marp Override] OSC button clicked:', action);
            
            if (action === 'presenter' && inIframe) {
                console.log('[Marp Override] Preventing presenter mode, showing alert');
                e.preventDefault();
                e.stopPropagation();
                alert('Presenter view is not available in DeckBot. Use fullscreen mode instead (F key or fullscreen button).');
                return false;
            }
        }
    }, true);
    
    console.log('[Marp Override] Setup complete');
})();
</script>
"""
    
    # Insert script before closing body tag
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', control_script + '</body>')
    else:
        html_content += control_script
    
    return html_content

@app.route('/api/presentation/images/<path:filename>')
def serve_presentation_image(filename):
    global current_service
    if not current_service:
        return "No presentation loaded", 404
        
    pres_dir = current_service.agent.presentation_dir
    images_dir = os.path.join(pres_dir, "images")
    
    return send_from_directory(images_dir, filename)

@app.route('/api/presentations', methods=['GET'])
def list_presentations():
    import glob
    from datetime import datetime
    
    manager = PresentationManager()
    presentations = manager.list_presentations()
    
    # Enrich with slide count and last modified
    for pres in presentations:
        pres_dir = os.path.join(manager.root_dir, pres['name'])
        deck_path = os.path.join(pres_dir, 'deck.marp.md')
        
        # Get slide count
        if os.path.exists(deck_path):
            with open(deck_path, 'r') as f:
                content = f.read()
                # Count slides (separated by ---)
                slide_count = len(content.split('\n---\n'))
                pres['slide_count'] = slide_count
                
                # Get last modified
                mtime = os.path.getmtime(deck_path)
                pres['last_modified'] = datetime.fromtimestamp(mtime).isoformat()
        else:
            pres['slide_count'] = 0
            pres['last_modified'] = pres.get('created_at', '')
    
    return jsonify(presentations)

@app.route('/api/presentations/create', methods=['POST'])
def create_presentation():
    import subprocess
    
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    template = data.get('template')
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    manager = PresentationManager()
    try:
        manager.create_presentation(name, description, template=template)
        
        # Compile the presentation immediately so preview works
        presentation_dir = os.path.join(manager.root_dir, name)
        try:
            subprocess.run(
                ["npx", "@marp-team/marp-cli", "deck.marp.md", "--allow-local-files"],
                cwd=presentation_dir,
                check=True,
                capture_output=True
            )
        except Exception as e:
            # Don't fail creation if compilation fails, just log it
            print(f"Warning: Failed to compile presentation on creation: {e}")
        
        return jsonify({"message": "Created", "name": name})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/presentations/delete', methods=['POST'])
def delete_presentation():
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    manager = PresentationManager()
    try:
        manager.delete_presentation(name)
        
        # Clear state if we deleted the current presentation
        state_manager = StateManager()
        current = state_manager.get_current_presentation()
        if current == name:
            state_manager.clear_current_presentation()
            
        return jsonify({"message": "Deleted", "name": name})
    except FileNotFoundError:
        return jsonify({"error": "Presentation not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def list_templates():
    manager = PresentationManager()
    templates = manager.list_templates()
    
    # Enrich with slide count
    for template in templates:
        template_dir = os.path.join(manager.templates_dir, template['name'])
        deck_path = os.path.join(template_dir, 'deck.marp.md')
        
        # Get slide count
        if os.path.exists(deck_path):
            with open(deck_path, 'r') as f:
                content = f.read()
                # Count slides (separated by ---)
                slide_count = len(content.split('\n---\n'))
                template['slide_count'] = slide_count
        else:
            template['slide_count'] = 0
    
    return jsonify(templates)

@app.route('/api/templates/delete', methods=['POST'])
def delete_template():
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    manager = PresentationManager()
    try:
        manager.delete_template(name)
        return jsonify({"message": "Deleted", "name": name})
    except FileNotFoundError:
        return jsonify({"error": "Template not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/presentations/<name>/preview-slides')
def get_presentation_preview_slides(name):
    """Generate and return cached PNG previews of all slides for a presentation."""
    import subprocess
    import glob
    
    manager = PresentationManager()
    pres_dir = os.path.join(manager.root_dir, name)
    
    if not os.path.exists(pres_dir):
        return jsonify({"error": "Presentation not found"}), 404
    
    deck_path = os.path.join(pres_dir, "deck.marp.md")
    if not os.path.exists(deck_path):
        return jsonify({"error": "Presentation source not found"}), 404
    
    # Create cache directory
    cache_dir = os.path.join(pres_dir, ".previews")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Check if previews exist
    existing_previews = sorted(glob.glob(os.path.join(cache_dir, "slide.*.png")))
    
    # Check if deck was modified after previews were generated
    needs_regeneration = False
    if not existing_previews:
        needs_regeneration = True
    else:
        deck_mtime = os.path.getmtime(deck_path)
        preview_mtime = os.path.getmtime(existing_previews[0])
        if deck_mtime > preview_mtime:
            needs_regeneration = True
    
    if needs_regeneration:
        try:
            # Generate preview images using Marp CLI
            subprocess.run(
                [
                    'npx', '@marp-team/marp-cli',
                    'deck.marp.md',
                    '--images', 'png',
                    '--output', os.path.join('.previews', 'slide.png'),
                    '--allow-local-files'
                ],
                cwd=pres_dir,
                check=True,
                capture_output=True,
                timeout=30
            )
            
            # Refresh the list of previews
            existing_previews = sorted(glob.glob(os.path.join(cache_dir, "slide.*.png")))
            
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Preview generation timed out"}), 500
        except Exception as e:
            print(f"Error generating previews for {name}: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Return URLs for all preview images
    preview_urls = []
    for preview_path in existing_previews:
        filename = os.path.basename(preview_path)
        url = f"/api/presentations/{name}/.previews/{filename}"
        preview_urls.append(url)
    
    return jsonify({"previews": preview_urls})

@app.route('/api/presentations/<name>/.previews/<filename>')
def serve_presentation_preview(name, filename):
    """Serve a cached preview image for a presentation."""
    manager = PresentationManager()
    pres_dir = os.path.join(manager.root_dir, name)
    cache_dir = os.path.join(pres_dir, ".previews")
    
    return send_from_directory(cache_dir, filename)

@app.route('/api/templates/<name>/preview-slides')
def get_template_preview_slides(name):
    """Generate and return cached PNG previews of all slides for a template."""
    import subprocess
    import glob
    
    manager = PresentationManager()
    template_dir = os.path.join(manager.templates_dir, name)
    
    if not os.path.exists(template_dir):
        return jsonify({"error": "Template not found"}), 404
    
    deck_path = os.path.join(template_dir, "deck.marp.md")
    if not os.path.exists(deck_path):
        return jsonify({"error": "Template source not found"}), 404
    
    # Create cache directory
    cache_dir = os.path.join(template_dir, ".previews")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Check if previews exist
    existing_previews = sorted(glob.glob(os.path.join(cache_dir, "slide.*.png")))
    
    # Check if deck was modified after previews were generated
    needs_regeneration = False
    if not existing_previews:
        needs_regeneration = True
    else:
        deck_mtime = os.path.getmtime(deck_path)
        preview_mtime = os.path.getmtime(existing_previews[0])
        if deck_mtime > preview_mtime:
            needs_regeneration = True
    
    if needs_regeneration:
        try:
            # Generate preview images using Marp CLI
            subprocess.run(
                [
                    'npx', '@marp-team/marp-cli',
                    'deck.marp.md',
                    '--images', 'png',
                    '--output', os.path.join('.previews', 'slide.png'),
                    '--allow-local-files'
                ],
                cwd=template_dir,
                check=True,
                capture_output=True,
                timeout=30
            )
            
            # Refresh the list of previews
            existing_previews = sorted(glob.glob(os.path.join(cache_dir, "slide.*.png")))
            
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Preview generation timed out"}), 500
        except Exception as e:
            print(f"Error generating previews for template {name}: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Return URLs for all preview images
    preview_urls = []
    for preview_path in existing_previews:
        filename = os.path.basename(preview_path)
        url = f"/api/templates/{name}/.previews/{filename}"
        preview_urls.append(url)
    
    return jsonify({"previews": preview_urls})

@app.route('/api/templates/<name>/.previews/<filename>')
def serve_template_preview(name, filename):
    """Serve a cached preview image for a template."""
    manager = PresentationManager()
    template_dir = os.path.join(manager.templates_dir, name)
    cache_dir = os.path.join(template_dir, ".previews")
    
    return send_from_directory(cache_dir, filename)

@app.route('/api/layouts', methods=['GET'])
def get_layouts():
    """Get available layouts for the current presentation with metadata."""
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
    
    pres_dir = current_service.agent.presentation_dir
    layouts_path = os.path.join(pres_dir, "layouts.md")
    
    if not os.path.exists(layouts_path):
        return jsonify({"layouts": []})
    
    try:
        with open(layouts_path, "r") as f:
            content = f.read()
        
        import re
        
        # Split by --- to get individual slides
        slides = content.split('\n---\n')
        
        layouts = []
        for i, slide in enumerate(slides):
            # Look for layout name in HTML comment
            match = re.search(r'<!-- layout: ([\w-]+) -->', slide)
            if match:
                layout_name = match.group(1)
                # Skip front matter slide
                if slide.strip().startswith('---'):
                    continue
                
                # Parse metadata from HTML comments
                image_friendly = re.search(r'<!-- image-friendly: (true|false) -->', slide)
                aspect_ratio = re.search(r'<!-- recommended-aspect-ratio: ([\d:]+) -->', slide)
                image_position = re.search(r'<!-- image-position: ([\w-]+) -->', slide)
                description = re.search(r'<!-- description: (.+?) -->', slide)
                
                layouts.append({
                    "name": layout_name,
                    "content": slide.strip(),
                    "index": i,
                    "image_friendly": image_friendly.group(1) == "true" if image_friendly else False,
                    "recommended_aspect_ratio": aspect_ratio.group(1) if aspect_ratio else None,
                    "image_position": image_position.group(1) if image_position else None,
                    "description": description.group(1) if description else None
                })
        
        return jsonify({"layouts": layouts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    """Get all preferences."""
    prefs = PreferencesManager()
    return jsonify(prefs.get_all())

@app.route('/api/preferences/<key>', methods=['GET'])
def get_preference(key):
    """Get a specific preference."""
    prefs = PreferencesManager()
    value = prefs.get(key)
    if value is None:
        return jsonify({"error": "Preference not found"}), 404
    return jsonify({"key": key, "value": value})

@app.route('/api/preferences', methods=['POST'])
def set_preferences():
    """Set one or more preferences."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    prefs = PreferencesManager()
    prefs.update(data)
    return jsonify({"message": "Preferences updated", "preferences": prefs.get_all()})

@app.route('/api/preferences/<key>', methods=['POST'])
def set_preference(key):
    """Set a specific preference."""
    data = request.json
    if 'value' not in data:
        return jsonify({"error": "No value provided"}), 400
    
    prefs = PreferencesManager()
    prefs.set(key, data['value'])
    return jsonify({"message": "Preference updated", "key": key, "value": data['value']})

@app.route('/api/state/current-presentation', methods=['GET'])
def get_current_presentation_state():
    """Get the persisted current presentation name."""
    state_manager = StateManager()
    current_pres = state_manager.get_current_presentation()
    if not current_pres:
        return jsonify({"name": None})
        
    # Verify it still exists
    manager = PresentationManager()
    if not manager.get_presentation(current_pres):
        # Clean up if it was deleted outside of this session
        state_manager.clear_current_presentation()
        return jsonify({"name": None})
        
    return jsonify({"name": current_pres})

@app.route('/api/state/current-presentation', methods=['DELETE'])
def clear_current_presentation_state():
    """Clear the persisted current presentation state and unload service."""
    global current_service
    state_manager = StateManager()
    state_manager.clear_current_presentation()
    current_service = None
    return jsonify({"message": "State cleared"})

@app.route('/api/load', methods=['POST'])
def load_presentation():
    global current_service
    data = request.json
    name = data.get('name')
    manager = PresentationManager()
    presentation = manager.get_presentation(name)
    
    if not presentation:
        return jsonify({"error": "Presentation not found"}), 404
        
    current_service = SessionService(presentation)
    
    # Persist state
    state_manager = StateManager()
    state_manager.set_current_presentation(name)
    
    # Return history
    history = current_service.get_history()
    return jsonify({"message": "Loaded", "history": history, "presentation": presentation})

@app.route('/api/chat', methods=['POST'])
def chat():
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
        
    data = request.json
    user_input = data.get('message')
    
    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    # Use thread to not block
    def run_chat():
        current_service.send_message(user_input)
        
    threading.Thread(target=run_chat).start()
    
    return jsonify({"status": "processing"})

@app.route('/api/images/generate', methods=['POST'])
def generate_images():
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
        
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400
        
    def run_gen():
        current_service.generate_images(prompt)
        
    threading.Thread(target=run_gen).start()
    
    return jsonify({"message": "Image generation started"})

@app.route('/api/images/select', methods=['POST'])
def select_image():
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
        
    data = request.json
    index = data.get('index')
    filename = data.get('filename')  # Optional now
    
    if index is None:
        return jsonify({"error": "Index required"}), 400
    
    try:
        saved_path = current_service.select_image(index, filename)
        
        if not saved_path:
            return jsonify({"error": "Invalid selection"}), 400
        
        return jsonify({"path": saved_path, "filename": os.path.basename(saved_path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/layouts/select', methods=['POST'])
def select_layout():
    """Select a layout and notify the agent."""
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
    
    data = request.json
    layout_name = data.get('layout_name')
    
    if not layout_name:
        return jsonify({"error": "Layout name required"}), 400
    
    try:
        result = current_service.select_layout(layout_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/layouts/<layout_name>/preview')
def get_layout_preview(layout_name):
    """Generate and serve a preview image for a layout."""
    global current_service
    if not current_service:
        return "No presentation loaded", 404
    
    import subprocess
    import tempfile
    import hashlib
    
    pres_dir = current_service.agent.presentation_dir
    layouts_path = os.path.join(pres_dir, "layouts.md")
    
    if not os.path.exists(layouts_path):
        return "Layouts file not found", 404
    
    # Create cache directory for preview images
    cache_dir = os.path.join(pres_dir, ".layout-previews")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Generate cache key from layout name
    cache_key = hashlib.md5(layout_name.encode()).hexdigest()
    preview_path = os.path.join(cache_dir, f"{cache_key}.png")
    
    # Return cached preview if it exists
    if os.path.exists(preview_path):
        return send_file(preview_path, mimetype='image/png')
    
    try:
        # Read layouts file
        with open(layouts_path, "r") as f:
            content = f.read()
        
        # Extract the specific layout
        import re
        pattern = f'<!-- layout: {re.escape(layout_name)} -->.*?(?=\n---\n|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return "Layout not found", 404
        
        layout_content = match.group(0)
        
        # Extract front matter from layouts.md (CSS styles)
        front_matter = ""
        if content.startswith('---'):
            parts = content.split('\n---\n', 2)
            if len(parts) >= 2:
                front_matter = '---\n' + parts[1] + '\n---\n'
        
        # Create a temporary markdown file with just this layout
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(front_matter)
            tmp.write('\n')
            tmp.write(layout_content)
            tmp_path = tmp.name
        
        try:
            # Generate preview image using Marp CLI
            subprocess.run(
                [
                    'npx', '@marp-team/marp-cli',
                    tmp_path,
                    '--image', 'png',
                    '--output', preview_path,
                    '--allow-local-files'
                ],
                check=True,
                capture_output=True,
                timeout=10
            )
            
            # Marp CLI outputs slide-001.png, rename to our cache key
            generated_path = preview_path.replace('.png', '-001.png')
            if os.path.exists(generated_path):
                os.rename(generated_path, preview_path)
            
            if os.path.exists(preview_path):
                return send_file(preview_path, mimetype='image/png')
            else:
                return "Failed to generate preview", 500
                
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except subprocess.TimeoutExpired:
        return "Preview generation timed out", 500
    except Exception as e:
        print(f"Error generating preview for {layout_name}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/events')
def events():
    def stream():
        events_queue = []
        
        def listener(event_type, data):
            events_queue.append((event_type, data))
            
        # Track the service we are subscribed to
        last_service = None
            
        # Keep connection open and yield events
        # We check queue every 0.1s
        while True:
            # Check if service changed (dynamic subscription)
            global current_service
            if current_service != last_service:
                if current_service:
                    current_service.subscribe(listener)
                last_service = current_service

            while events_queue:
                event_type, data = events_queue.pop(0)
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            time.sleep(0.1)
            
    return Response(stream_with_context(stream()), mimetype='text/event-stream')

@app.route('/api/presentation/settings', methods=['GET'])
def get_presentation_settings():
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
    
    # Refresh metadata from file
    manager = PresentationManager()
    if not current_service.agent.context:
         return jsonify({"error": "Context not available"}), 500
         
    pres_name = current_service.agent.context['name']
    pres = manager.get_presentation(pres_name)
    
    if not pres:
        return jsonify({"error": "Presentation not found"}), 404
        
    return jsonify({
        "aspect_ratio": pres.get("aspect_ratio", "4:3"),
        "description": pres.get("description", ""),
    })

@app.route('/api/presentation/settings', methods=['POST'])
def set_presentation_settings():
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
        
    data = request.json
    aspect_ratio = data.get("aspect_ratio")
    
    if aspect_ratio:
        manager = PresentationManager()
        name = current_service.agent.context['name']
        try:
            manager.set_presentation_aspect_ratio(name, aspect_ratio)
            
            # Recompile
            import subprocess
            presentation_dir = current_service.agent.presentation_dir
            subprocess.run(["npx", "@marp-team/marp-cli", "deck.marp.md", "--allow-local-files"], cwd=presentation_dir, check=True)
            
        except Exception as e:
             return jsonify({"error": f"Settings saved but compile failed: {e}"}), 500
             
    return jsonify({"message": "Settings updated"})

@app.route('/api/presentation/save-as', methods=['POST'])
def save_presentation_as():
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
        
    data = request.json
    new_name = data.get("name")
    copy_images = data.get("copy_images", True)
    
    if not new_name:
        return jsonify({"error": "Name is required"}), 400
        
    manager = PresentationManager()
    source_name = current_service.agent.context['name']
    
    try:
        manager.duplicate_presentation(source_name, new_name, copy_images=copy_images)
        return jsonify({"message": "Presentation duplicated", "name": new_name})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/presentation/export-pdf', methods=['POST'])
def export_pdf():
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
        
    try:
        result = current_service.agent.tools.export_pdf()
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/presentation/files', methods=['GET'])
def get_presentation_files():
    """Get the file tree structure for the current presentation."""
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
    
    pres_dir = current_service.agent.presentation_dir
    
    def build_tree(path, base_path):
        """Recursively build file tree structure."""
        items = []
        try:
            entries = os.listdir(path)
            # Collect entries with their modification times
            entries_with_mtime = []
            for entry in entries:
                # Skip hidden files and cache directories
                if entry.startswith('.'):
                    continue
                    
                full_path = os.path.join(path, entry)
                rel_path = os.path.relpath(full_path, base_path)
                
                try:
                    mtime = os.path.getmtime(full_path)
                    entries_with_mtime.append((entry, full_path, rel_path, mtime))
                except OSError:
                    # Skip if we can't get mtime
                    continue
            
            # Sort by modification time (reverse chronological - most recent first)
            entries_with_mtime.sort(key=lambda x: x[3], reverse=True)
            
            for entry, full_path, rel_path, mtime in entries_with_mtime:
                from datetime import datetime
                mtime_iso = datetime.fromtimestamp(mtime).isoformat()
                
                if os.path.isdir(full_path):
                    children = build_tree(full_path, base_path)
                    items.append({
                        'name': entry,
                        'path': rel_path,
                        'type': 'folder',
                        'mtime': mtime_iso,
                        'children': children
                    })
                else:
                    # Determine file type
                    ext = os.path.splitext(entry)[1].lower()
                    file_type = 'file'
                    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']:
                        file_type = 'image'
                    elif ext in ['.md', '.markdown']:
                        file_type = 'markdown'
                    elif ext in ['.json']:
                        file_type = 'json'
                    elif ext in ['.html', '.css', '.js']:
                        file_type = 'code'
                    
                    items.append({
                        'name': entry,
                        'path': rel_path,
                        'type': file_type,
                        'mtime': mtime_iso
                    })
        except Exception as e:
            print(f"Error reading directory {path}: {e}")
            
        return items
    
    try:
        tree = build_tree(pres_dir, pres_dir)
        return jsonify({"files": tree})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/presentation/file-content', methods=['GET'])
def get_file_content():
    """Get the content of a specific file in the current presentation."""
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
    
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({"error": "Path parameter required"}), 400
    
    pres_dir = current_service.agent.presentation_dir
    full_path = os.path.join(pres_dir, file_path)
    
    # Security check: ensure path is within presentation directory
    if not os.path.abspath(full_path).startswith(os.path.abspath(pres_dir)):
        return jsonify({"error": "Invalid path"}), 403
    
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404
    
    if os.path.isdir(full_path):
        return jsonify({"error": "Path is a directory"}), 400
    
    try:
        # Determine if file is binary
        ext = os.path.splitext(file_path)[1].lower()
        is_image = ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
        
        if is_image:
            # For images, return a URL to serve the image
            return jsonify({
                "type": "image",
                "url": f"/api/presentation/file-serve?path={file_path}"
            })
        else:
            # For text files, read and return content
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Determine language for syntax highlighting
                language = 'text'
                if ext == '.md' or ext == '.markdown':
                    language = 'markdown'
                elif ext == '.json':
                    language = 'json'
                elif ext == '.html':
                    language = 'html'
                elif ext == '.css':
                    language = 'css'
                elif ext == '.js':
                    language = 'javascript'
                elif ext == '.py':
                    language = 'python'
                elif ext == '.yaml' or ext == '.yml':
                    language = 'yaml'
                
                return jsonify({
                    "type": "text",
                    "content": content,
                    "language": language
                })
            except UnicodeDecodeError:
                # If we can't decode as text, treat as binary
                return jsonify({
                    "type": "binary",
                    "message": "Binary file (cannot display)"
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/presentation/file-save', methods=['POST'])
def save_file():
    """Save content to a file in the current presentation and recompile."""
    global current_service
    if not current_service:
        return jsonify({"error": "No presentation loaded"}), 400
    
    data = request.json
    file_path = data.get('path')
    content = data.get('content')
    
    if not file_path:
        return jsonify({"error": "Path parameter required"}), 400
    
    if content is None:
        return jsonify({"error": "Content parameter required"}), 400
    
    pres_dir = current_service.agent.presentation_dir
    full_path = os.path.join(pres_dir, file_path)
    
    # Security check: ensure path is within presentation directory
    if not os.path.abspath(full_path).startswith(os.path.abspath(pres_dir)):
        return jsonify({"error": "Invalid path"}), 403
    
    if os.path.isdir(full_path):
        return jsonify({"error": "Path is a directory"}), 400
    
    try:
        # Write content to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Trigger Marp compilation
        import subprocess
        compile_result = {"success": True, "message": ""}
        try:
            result = subprocess.run(
                ["npx", "@marp-team/marp-cli", "deck.marp.md", "--allow-local-files"],
                cwd=pres_dir,
                check=True,
                capture_output=True,
                text=True
            )
            compile_result["message"] = "File saved and presentation recompiled successfully"
        except subprocess.CalledProcessError as e:
            compile_result["success"] = False
            compile_result["message"] = f"File saved but compilation failed: {e.stderr or str(e)}"
        except Exception as e:
            compile_result["success"] = False
            compile_result["message"] = f"File saved but compilation failed: {str(e)}"
        
        return jsonify({
            "success": True,
            "message": "File saved successfully",
            "compile": compile_result
        })
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

@app.route('/api/presentation/file-serve', methods=['GET'])
def serve_file():
    """Serve a file from the current presentation directory."""
    global current_service
    if not current_service:
        return "No presentation loaded", 404
    
    file_path = request.args.get('path')
    if not file_path:
        return "Path parameter required", 400
    
    pres_dir = current_service.agent.presentation_dir
    full_path = os.path.join(pres_dir, file_path)
    
    # Security check
    if not os.path.abspath(full_path).startswith(os.path.abspath(pres_dir)):
        return "Invalid path", 403
    
    if not os.path.exists(full_path):
        return "File not found", 404
    
    return send_file(full_path)
