import json
import os

from app.models.clip_item import ClipItem
from app.shared.constants import HISTORY_FILE, MAX_HISTORY


class HistoryManager:
    def __init__(self):
        self.items: list[ClipItem] = []
        self.load()

    def load(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r") as f:
                    data = json.load(f)
                self.items = [ClipItem.from_dict(d) for d in data]
        except Exception:
            self.items = []

    def save(self):
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump([i.to_dict() for i in self.items], f, indent=2)
        except Exception:
            pass

    def add(self, content, kind="text"):
        for item in self.items:
            if item.kind == kind and item.content == content:
                if not item.pinned:
                    self.items.remove(item)
                    self.items.insert(0, item)
                    self.save()
                return False

        item     = ClipItem(content, kind)
        pinned   = [i for i in self.items if i.pinned]
        unpinned = [i for i in self.items if not i.pinned]
        unpinned = unpinned[: MAX_HISTORY - 1]
        self.items = [item] + unpinned + pinned
        self.save()
        return True

    def toggle_pin(self, item):
        item.pinned = not item.pinned
        self.save()

    def remove(self, item):
        if item in self.items:
            self.items.remove(item)
            self.save()

    def clear_unpinned(self):
        self.items = [i for i in self.items if i.pinned]
        self.save()

    def search(self, query):
        q = query.lower()
        return [i for i in self.items if q in i.preview_text().lower()]
