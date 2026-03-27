import json
import os

import pytest

import app.core.history_manager as hm_module
from app.core.history_manager import HistoryManager
from app.models.clip_item import ClipItem


@pytest.fixture()
def manager(tmp_path, monkeypatch):
    """HistoryManager that reads/writes to a temp file instead of ~/.clipvault_history.json."""
    history_file = str(tmp_path / "history.json")
    monkeypatch.setattr(hm_module, "HISTORY_FILE", history_file)
    return HistoryManager()


class TestAdd:
    def test_add_new_item_returns_true(self, manager):
        assert manager.add("hello") is True

    def test_added_item_is_first(self, manager):
        manager.add("first")
        manager.add("second")
        assert manager.items[0].content == "second"

    def test_duplicate_text_returns_false(self, manager):
        manager.add("hello")
        assert manager.add("hello") is False

    def test_duplicate_promotes_to_top(self, manager):
        manager.add("a")
        manager.add("b")
        manager.add("a")   # duplicate — should promote "a" to top
        assert manager.items[0].content == "a"

    def test_pinned_duplicate_not_moved(self, manager):
        manager.add("pinned")
        manager.items[0].pinned = True
        manager.add("other")
        manager.add("pinned")  # duplicate of pinned — should NOT move it
        # pinned item stays wherever it is; return value is False
        pinned_positions = [i for i, item in enumerate(manager.items) if item.pinned]
        assert manager.items[pinned_positions[0]].content == "pinned"

    def test_image_and_text_same_content_are_distinct(self, manager):
        assert manager.add("data", "text") is True
        assert manager.add("data", "image") is True
        assert len(manager.items) == 2

    def test_max_history_respected(self, manager, monkeypatch):
        monkeypatch.setattr(hm_module, "MAX_HISTORY", 3)
        for i in range(5):
            manager.add(f"item{i}")
        unpinned = [i for i in manager.items if not i.pinned]
        assert len(unpinned) <= 3

    def test_pinned_items_survive_trim(self, manager, monkeypatch):
        monkeypatch.setattr(hm_module, "MAX_HISTORY", 2)
        manager.add("keep_me")
        manager.items[0].pinned = True
        for i in range(5):
            manager.add(f"flood{i}")
        contents = [i.content for i in manager.items]
        assert "keep_me" in contents


class TestTogglePin:
    def test_pin_unpinned_item(self, manager):
        manager.add("hello")
        item = manager.items[0]
        manager.toggle_pin(item)
        assert item.pinned is True

    def test_unpin_pinned_item(self, manager):
        manager.add("hello")
        item = manager.items[0]
        item.pinned = True
        manager.toggle_pin(item)
        assert item.pinned is False


class TestRemove:
    def test_remove_existing_item(self, manager):
        manager.add("hello")
        item = manager.items[0]
        manager.remove(item)
        assert item not in manager.items

    def test_remove_nonexistent_item_is_safe(self, manager):
        orphan = ClipItem("ghost")
        manager.remove(orphan)   # should not raise


class TestClearUnpinned:
    def test_clears_unpinned_only(self, manager):
        manager.add("keep")
        manager.items[0].pinned = True
        manager.add("remove_me")
        manager.clear_unpinned()
        assert len(manager.items) == 1
        assert manager.items[0].content == "keep"

    def test_all_unpinned_results_in_empty(self, manager):
        manager.add("a")
        manager.add("b")
        manager.clear_unpinned()
        assert manager.items == []


class TestSearch:
    def test_search_match(self, manager):
        manager.add("hello world")
        manager.add("foo bar")
        results = manager.search("hello")
        assert len(results) == 1
        assert results[0].content == "hello world"

    def test_search_case_insensitive(self, manager):
        manager.add("Hello World")
        assert len(manager.search("hello")) == 1

    def test_search_no_match(self, manager):
        manager.add("unrelated")
        assert manager.search("xyz") == []

    def test_search_empty_query_returns_all(self, manager):
        manager.add("a")
        manager.add("b")
        assert len(manager.search("")) == 2

    def test_image_items_excluded_from_text_search(self, manager):
        manager.add("somedata", "image")
        # image preview is "📷 Image"; searching for text not in that returns nothing
        assert manager.search("somedata") == []


class TestPersistence:
    def test_save_and_reload(self, tmp_path, monkeypatch):
        history_file = str(tmp_path / "history.json")
        monkeypatch.setattr(hm_module, "HISTORY_FILE", history_file)

        mgr1 = HistoryManager()
        mgr1.add("persist me")

        mgr2 = HistoryManager()
        assert len(mgr2.items) == 1
        assert mgr2.items[0].content == "persist me"

    def test_corrupt_file_results_in_empty(self, tmp_path, monkeypatch):
        history_file = str(tmp_path / "history.json")
        monkeypatch.setattr(hm_module, "HISTORY_FILE", history_file)
        with open(history_file, "w") as f:
            f.write("not valid json{{{")
        mgr = HistoryManager()
        assert mgr.items == []

    def test_missing_file_results_in_empty(self, tmp_path, monkeypatch):
        history_file = str(tmp_path / "nonexistent.json")
        monkeypatch.setattr(hm_module, "HISTORY_FILE", history_file)
        mgr = HistoryManager()
        assert mgr.items == []
