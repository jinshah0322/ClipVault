from datetime import datetime, timedelta

import pytest

from app.models.clip_item import ClipItem
from app.shared.constants import MAX_TEXT_PREVIEW


class TestClipItemInit:
    def test_defaults(self):
        item = ClipItem("hello")
        assert item.content == "hello"
        assert item.kind == "text"
        assert item.pinned is False
        assert item.timestamp is not None

    def test_custom_fields(self):
        ts = "2024-01-01T12:00:00"
        item = ClipItem("data", kind="image", timestamp=ts, pinned=True)
        assert item.kind == "image"
        assert item.timestamp == ts
        assert item.pinned is True

    def test_timestamp_auto_set(self):
        before = datetime.now().isoformat()
        item = ClipItem("x")
        after = datetime.now().isoformat()
        assert before <= item.timestamp <= after


class TestClipItemSerialization:
    def test_to_dict(self):
        item = ClipItem("hello", kind="text", timestamp="2024-06-01T10:00:00", pinned=True)
        d = item.to_dict()
        assert d == {
            "content": "hello",
            "kind": "text",
            "timestamp": "2024-06-01T10:00:00",
            "pinned": True,
        }

    def test_from_dict_roundtrip(self):
        original = ClipItem("world", kind="text", timestamp="2024-06-01T10:00:00", pinned=False)
        restored = ClipItem.from_dict(original.to_dict())
        assert restored.content == original.content
        assert restored.kind == original.kind
        assert restored.timestamp == original.timestamp
        assert restored.pinned == original.pinned

    def test_from_dict_missing_pinned_defaults_false(self):
        d = {"content": "hi", "kind": "text", "timestamp": "2024-01-01T00:00:00"}
        item = ClipItem.from_dict(d)
        assert item.pinned is False


class TestClipItemPreviewText:
    def test_text_short(self):
        item = ClipItem("Hello world")
        assert item.preview_text() == "Hello world"

    def test_text_strips_newlines(self):
        item = ClipItem("line1\nline2\nline3")
        assert "\n" not in item.preview_text()
        assert "line1 line2 line3" == item.preview_text()

    def test_text_strips_leading_trailing_whitespace(self):
        item = ClipItem("  trimmed  ")
        assert item.preview_text() == "trimmed"

    def test_text_truncated_at_max(self):
        long_text = "a" * (MAX_TEXT_PREVIEW + 10)
        item = ClipItem(long_text)
        preview = item.preview_text()
        assert preview.endswith("…")
        assert len(preview) == MAX_TEXT_PREVIEW + 1  # content + ellipsis char

    def test_text_exactly_at_limit_no_ellipsis(self):
        text = "b" * MAX_TEXT_PREVIEW
        item = ClipItem(text)
        assert item.preview_text() == text
        assert not item.preview_text().endswith("…")

    def test_image_preview(self):
        item = ClipItem("base64data", kind="image")
        assert item.preview_text() == "📷 Image"


class TestClipItemTimeLabel:
    def _item_with_delta(self, seconds):
        ts = (datetime.now() - timedelta(seconds=seconds)).isoformat()
        return ClipItem("x", timestamp=ts)

    def test_just_now(self):
        assert self._item_with_delta(30).time_label() == "Just now"

    def test_minutes_ago(self):
        label = self._item_with_delta(150).time_label()   # 2m 30s
        assert label == "2m ago"

    def test_hours_ago(self):
        label = self._item_with_delta(7200).time_label()  # 2h
        assert label == "2h ago"

    def test_days_ago_shows_date(self):
        ts = (datetime.now() - timedelta(days=3)).isoformat()
        item = ClipItem("x", timestamp=ts)
        label = item.time_label()
        # Should be a month-day string like "Mar 24"
        assert len(label) > 0
        assert "ago" not in label

    def test_invalid_timestamp_returns_empty(self):
        item = ClipItem("x", timestamp="not-a-date")
        assert item.time_label() == ""
