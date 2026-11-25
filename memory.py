import json
import os
import re

DATA_DIR = "data"
MEMORY_FILE = os.path.join(DATA_DIR, "projects.json")

class ProjectMemory:
    """Simple persistent JSON memory for project plans and change history."""
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

    def _load(self):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _key(self, name):
        return re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip()).lower()

    def list_projects(self):
        return sorted(self._load().keys())

    def get_project(self, name):
        return self._load().get(name)

    def save_project(self, name, project):
        data = self._load()
        data[name] = project
        self._save(data)

    def delete_project(self, name):
        data = self._load()
        data.pop(name, None)
        self._save(data)
