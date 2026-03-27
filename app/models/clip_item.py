from datetime import datetime
from app.shared.constants import MAX_TEXT_PREVIEW


class ClipItem:
    def __init__(self, content, kind="text", timestamp=None, pinned=False):
        self.content   = content          # str for text, base64 str for image
        self.kind      = kind             # "text" | "image"
        self.timestamp = timestamp or datetime.now().isoformat()
        self.pinned    = pinned

    def to_dict(self):
        return {
            "content":   self.content,
            "kind":      self.kind,
            "timestamp": self.timestamp,
            "pinned":    self.pinned,
        }

    @staticmethod
    def from_dict(d):
        return ClipItem(d["content"], d["kind"], d["timestamp"], d.get("pinned", False))

    def preview_text(self):
        if self.kind == "image":
            return "📷 Image"
        t = self.content.strip().replace("\n", " ")
        return t[:MAX_TEXT_PREVIEW] + ("…" if len(t) > MAX_TEXT_PREVIEW else "")

    def time_label(self):
        try:
            dt = datetime.fromisoformat(self.timestamp)
            delta = datetime.now() - dt
            s = int(delta.total_seconds())
            if s < 60:    return "Just now"
            if s < 3600:  return f"{s // 60}m ago"
            if s < 86400: return f"{s // 3600}h ago"
            return dt.strftime("%b %d")
        except Exception:
            return ""
