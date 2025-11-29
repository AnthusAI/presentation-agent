import os
import json
import time
from datetime import datetime

class PresentationManager:
    def __init__(self, root_dir=None):
        if root_dir:
            self.root_dir = root_dir
        else:
            self.root_dir = os.environ.get('VIBE_PRESENT_ROOT', os.path.expanduser("~/.vibe_present"))
        
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def create_presentation(self, name, description=""):
        presentation_dir = os.path.join(self.root_dir, name)
        if os.path.exists(presentation_dir):
            raise ValueError(f"Presentation '{name}' already exists.")
        
        os.makedirs(presentation_dir)
        
        metadata = {
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        with open(os.path.join(presentation_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Create a default Marp deck
        with open(os.path.join(presentation_dir, "deck.marp.md"), "w") as f:
            f.write(f"""---
marp: true
theme: default
paginate: true
---

# {name}

{description}

---

# Slide 1

- Bullet 1
- Bullet 2
""")
        
        return metadata

    def list_presentations(self):
        presentations = []
        if not os.path.exists(self.root_dir):
            return []
            
        for name in os.listdir(self.root_dir):
            path = os.path.join(self.root_dir, name)
            if os.path.isdir(path):
                metadata_path = os.path.join(path, "metadata.json")
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                            presentations.append(metadata)
                    except json.JSONDecodeError:
                        continue
        
        # Sort by created_at desc
        presentations.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return presentations

    def get_presentation(self, name):
        path = os.path.join(self.root_dir, name)
        if not os.path.exists(path):
            return None
        
        metadata_path = os.path.join(path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                return json.load(f)
        return None

