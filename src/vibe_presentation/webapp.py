import os
import json
import time
import threading
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file, send_from_directory
from vibe_presentation.manager import PresentationManager
from vibe_presentation.session_service import SessionService
from vibe_presentation.preferences import PreferencesManager

app = Flask(__name__)

# Global service instance (single user for now)
current_service = None

@app.route('/')
def index():
    return render_template('chat.html')

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
    manager = PresentationManager()
    presentations = manager.list_presentations()
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
        return jsonify({"message": "Deleted", "name": name})
    except FileNotFoundError:
        return jsonify({"error": "Presentation not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def list_templates():
    manager = PresentationManager()
    templates = manager.list_templates()
    return jsonify(templates)

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

@app.route('/events')
def events():
    def stream():
        events_queue = []
        
        def listener(event_type, data):
            events_queue.append((event_type, data))
            
        if current_service:
            current_service.subscribe(listener)
            
        # Keep connection open and yield events
        # We check queue every 0.1s
        while True:
            while events_queue:
                event_type, data = events_queue.pop(0)
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            time.sleep(0.1)
            
    return Response(stream_with_context(stream()), mimetype='text/event-stream')
