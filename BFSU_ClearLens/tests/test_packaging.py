from __future__ import annotations

import unittest
import runpy
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_windows_build_uses_isolated_onedir_layout(self) -> None:
        script = (ROOT / "build_clearlens.bat").read_text(encoding="utf-8")
        for required in (
            "virtual_env",
            "--onedir",
            '--contents-directory "_internal"',
            "BFSU_ClearLens.exe",
            "assets config samples",
            "README.md technical_readme.md RELEASE_NOTES.md requirements.txt",
            "--collect-all customtkinter",
        ):
            self.assertIn(required, script)
        self.assertNotIn("--add-data", script)
        self.assertNotIn("--manifest", script)
        self.assertFalse((ROOT / "assets" / "windows_dpi.manifest").exists())
        main_source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertNotIn("enable_windows_high_dpi", main_source)

    def test_customtkinter_root_preserves_drag_and_drop(self) -> None:
        source = (ROOT / "clearlens" / "window.py").read_text(encoding="utf-8")
        self.assertIn("import customtkinter as ctk", source)
        self.assertIn("class ApplicationWindow(ctk.CTk, TkinterDnD.DnDWrapper)", source)
        self.assertIn("self.TkdndVersion = TkinterDnD._require(self)", source)
        self.assertIn('ctk.set_appearance_mode("light")', source)
        self.assertNotIn("tkinter_unblur", source)
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        self.assertIn("class ClearLensApp(ApplicationWindow)", app_source)
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("customtkinter==5.2.2", requirements)
        self.assertNotIn("tkinter-unblur", requirements)

    def test_review_double_click_navigates_instead_of_accepting(self) -> None:
        source = (ROOT / "clearlens" / "ui_ai_review.py").read_text(encoding="utf-8")
        self.assertIn('self.tree.bind("<Double-1>", self._navigate_selected)', source)
        self.assertNotIn('self.tree.bind("<Double-1>", lambda _event: self._accept_selected())', source)

    def test_v143_navigation_log_and_workspace_controls_are_wired(self) -> None:
        source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        for required in (
            "TextLineNumbers",
            'self.diff_tree.bind("<Double-1>", self._on_diff_double_click)',
            'self.after_text.bind("<Button-3>", self._show_editor_context_menu)',
            'text=t("undo_selected_log")',
            'orientation="vertical"',
            'self.vertical_pane.set_ratio(0.36)',
            'button_colors("danger")',
        ):
            self.assertIn(required, source)
        self.assertNotIn("def _build_action_group", source)

    def test_v150_uses_customtkinter_with_native_data_controls(self) -> None:
        source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        for required in (
            'self.geometry("1280x800")',
            'self.minsize(1000, 650)',
            "ctk.CTkScrollableFrame(",
            "ctk.CTkCheckBox(",
            "ctk.CTkTabview(",
            "CTkSplitPane(",
            "EditorTextbox(",
            "DpiAwareTreeview(",
        ):
            self.assertIn(required, source)
        for removed in ("ui_scale_percent", "def set_ui_scale", "_ui_px", "_sidebar_ratio", "ttk.Button", "ttk.Checkbutton", "tk.PanedWindow"):
            self.assertNotIn(removed, source)
        settings_source = (ROOT / "clearlens" / "ui_settings.py").read_text(encoding="utf-8")
        self.assertNotIn('"display.ui_scale_percent"', settings_source)
        self.assertIn("ctk.CTkTabview", settings_source)
        defaults = (ROOT / "config" / "default_settings.json").read_text(encoding="utf-8")
        self.assertNotIn('"display"', defaults)
        common_source = (ROOT / "clearlens" / "ui_common.py").read_text(encoding="utf-8")
        self.assertIn("class DpiAwareTreeview(ttk.Treeview)", common_source)
        self.assertIn("GetDpiForWindow", common_source)
        self.assertTrue((ROOT / "assets" / "clearlens_theme.json").exists())

    def test_v151_split_panes_fill_allocated_bounds_and_menus_follow_dpi(self) -> None:
        common_source = (ROOT / "clearlens" / "ui_common.py").read_text(encoding="utf-8")
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        for required in (
            "tk.Place.place_configure(self.first",
            "tk.Place.place_configure(\n                self.second",
            "self.first.pack_propagate(False)",
            "self.second.pack_propagate(False)",
            "class DpiAwareMenu(tk.Menu)",
            "tkfont.Font(root=master",
            "self._menu_font.configure",
            "_window_scale(self._dpi_window)",
        ):
            self.assertIn(required, common_source)
        self.assertIn("DpiAwareMenu(self)", app_source)
        self.assertIn("DpiAwareMenu(menubar, tearoff=False)", app_source)
        self.assertNotIn("tk.Menu(", app_source)
        self.assertNotIn("tkfont.Font(master=", common_source)

    def test_v153_toolbar_tasks_encoding_and_manual_editing_are_wired(self) -> None:
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        dialogs_source = (ROOT / "clearlens" / "ui_dialogs.py").read_text(encoding="utf-8")
        for required in (
            'height=80',
            't("toolbar_reset_current")',
            't("toolbar_reset_all")',
            'self.vertical_pane.set_ratio(0.36)',
            'self._set_task_ui_busy(True)',
            'self._set_task_ui_busy(False)',
            'self._refresh_file_row(index)',
            'self.progress_summary',
            'EncodingSelectDialog(self, self.i18n, READ_ENCODINGS',
        ):
            self.assertIn(required, app_source)
        self.assertIn("class EncodingSelectDialog(IconToplevel)", dialogs_source)
        self.assertNotIn("simpledialog.askstring", app_source)
        modified_source = app_source.split("def _on_after_modified", 1)[1].split("def _commit_manual_history", 1)[0]
        self.assertNotIn("_refresh_file_list", modified_source)

    def test_v154_queue_tasks_shortcuts_and_layout_are_wired(self) -> None:
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        common_source = (ROOT / "clearlens" / "ui_common.py").read_text(encoding="utf-8")
        text_source = (ROOT / "clearlens" / "ui_text.py").read_text(encoding="utf-8")
        for required in (
            't("toolbar_clear_all")',
            't("toolbar_reset_selected")',
            't("toolbar_rule_selected")',
            't("toolbar_llm_selected")',
            'columns = ("number", "name", "encoding", "confidence", "characters", "status")',
            'self.file_tree.bind("<Delete>", self._delete_selected_from_queue)',
            'task_label=self.i18n.t("import_task")',
            'elif kind == "preview_result"',
            'self.i18n.t("unsaved_exit_confirm", count=unsaved_count)',
        ):
            self.assertIn(required, app_source)
        shortcut_block = app_source.split("def _bind_shortcuts", 1)[1].split("def _enable_drop", 1)[0]
        self.assertNotIn('\"<Delete>\":', shortcut_block)
        self.assertIn("self.ratio = self.initial_ratio", common_source)
        self.assertIn("self.position / total", common_source)
        self.assertIn("if before == after:", text_source)

    def test_v155_llm_find_workspace_and_large_markup_controls_are_wired(self) -> None:
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        dialogs_source = (ROOT / "clearlens" / "ui_dialogs.py").read_text(encoding="utf-8")
        common_source = (ROOT / "clearlens" / "ui_common.py").read_text(encoding="utf-8")
        for required in (
            't("toolbar_open_output")',
            'file_menu.add_command(label=t("new_session"), command=self.new_session)',
            'def _preflight_ai_request(',
            'self._preflight_ai_request(indices, custom_rules=instructions)',
            'for position, (index, source_text) in enumerate(jobs, 1):',
            'compact_markup_preview_chars',
            'self._schedule_selected_preview()',
            'FindReplaceDialog(self, self.i18n, get_text, set_text, highlight_matches)',
        ):
            self.assertIn(required, app_source)
        for required in ('def _find_next(', 'def _find_all(', 'replace_count_message', 'find_count_message'):
            self.assertIn(required, dialogs_source)
        self.assertIn("def set_wrap_mode", common_source)

    def test_v156_full_preview_virtualized_editors_and_rule_rebuild_are_wired(self) -> None:
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        text_source = (ROOT / "clearlens" / "ui_text.py").read_text(encoding="utf-8")
        common_source = (ROOT / "clearlens" / "ui_common.py").read_text(encoding="utf-8")
        dialogs_source = (ROOT / "clearlens" / "ui_dialogs.py").read_text(encoding="utf-8")
        for required in (
            "rendered, result = clean_text(source",
            "first_line_difference(source, rendered)",
            "return min(configured, compact_limit, 12000)",
            "self.after_text.reset_undo()",
            "self._preview_token = None",
            'before_start_line=int(payload["before_start_line"])',
        ):
            self.assertIn(required, app_source)
        self.assertIn("longest > 6000", app_source)
        self.assertIn("self._redraw_after_id", text_source)
        self.assertIn('dlineinfo(f"{displayed_line}.0")', text_source)
        self.assertIn("def displayed_line_number", common_source)
        self.assertIn("CTkScrollableFrame(root", dialogs_source)
        self.assertLess(dialogs_source.index("buttons.pack(side=tk.BOTTOM"), dialogs_source.index("form.pack(fill=tk.BOTH"))

    def test_v157_atomic_llm_chunks_and_progress_are_wired(self) -> None:
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        ai_source = (ROOT / "clearlens" / "ai_client.py").read_text(encoding="utf-8")
        chunk_source = (ROOT / "clearlens" / "llm_chunks.py").read_text(encoding="utf-8")
        defaults = (ROOT / "config" / "default_settings.json").read_text(encoding="utf-8")
        for required in (
            "build_document_chunks",
            "source_hash",
            "locate_chunk_fragment",
            "Return only lines that need a change",
            "return [], warnings",
        ):
            self.assertIn(required, ai_source)
        for required in ("core_start_offset", "core_end_offset", "overlap_lines", "blake2s"):
            self.assertIn(required, chunk_source)
        self.assertIn('"chunk_overlap_lines": 2', defaults)
        self.assertIn('"ai_processing_chunk"', app_source)
        self.assertIn("estimate_chunk_count", app_source)

    def test_v158_deepseek_strict_tool_and_item_level_fallback_are_wired(self) -> None:
        ai_source = (ROOT / "clearlens" / "ai_client.py").read_text(encoding="utf-8")
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        for required in (
            '"name": "submit_atomic_edits"',
            '"strict": True',
            '"response_format": {"type": "json_object"}',
            "_parse_deepseek_edit_batch",
            "_normalize_deepseek_edit_payload",
            '"replace", "replacement", "substitute"',
            '"ai_provider_items_rejected:"',
            "ai_response_no_valid_items:",
        ):
            self.assertIn(required, ai_source)
        self.assertIn('base_warning.startswith("ai_provider_items_rejected:")', app_source)
        self.assertIn('base_warning.startswith("ai_response_no_valid_items:")', app_source)

    def test_v159_preview_multirule_and_complex_edits_are_wired(self) -> None:
        ai_source = (ROOT / "clearlens" / "ai_client.py").read_text(encoding="utf-8")
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        for required in (
            "def _compute_local_preview(",
            "preview_input, rendered, result",
            'custom_rules=llm_instructions',
            '"llm_rule_count": len(llm_instructions)',
            '"preview_llm_complete"',
        ):
            self.assertIn(required, app_source)
        for required in (
            "for rule_number, rule in enumerate(rendered_rules, 1):",
            "_flatten_provider_edits",
            '"case_conversion"',
            '"composite"',
            "_literal_rule_specs",
            "text=original,",
        ):
            self.assertIn(required, ai_source)

    def test_v1510_provider_location_rebinding_is_wired(self) -> None:
        ai_source = (ROOT / "clearlens" / "ai_client.py").read_text(encoding="utf-8")
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        chunk_source = (ROOT / "clearlens" / "llm_chunks.py").read_text(encoding="utf-8")
        for required in (
            "AIProviderEditBatch",
            "_resolve_chunk_edit_detailed",
            "ai_chunk_locations_repaired:",
            "ai_chunk_fragments_ambiguous:",
            "The application owns request identity",
        ):
            self.assertIn(required, ai_source)
        self.assertIn("locate_chunk_fragment_candidates", chunk_source)
        self.assertIn('base_warning.startswith("ai_chunk_locations_repaired:")', app_source)
        self.assertEqual(
            (ROOT / "clearlens" / "__init__.py").read_text(encoding="utf-8").strip(),
            '__version__ = "1.5.11"',
        )

    def test_v1511_preview_watchdog_icons_and_adaptive_llm_are_wired(self) -> None:
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        ai_source = (ROOT / "clearlens" / "ai_client.py").read_text(encoding="utf-8")
        ui_source = (ROOT / "clearlens" / "ui_common.py").read_text(encoding="utf-8")
        settings_source = (ROOT / "clearlens" / "ui_settings.py").read_text(encoding="utf-8")
        for required in (
            "_preview_snapshot_identity",
            "_preview_snapshot_matches",
            "_schedule_task_watchdog",
            'elif kind == "ai_activity"',
            "ai_waiting_response",
        ):
            self.assertIn(required, app_source)
        for required in (
            "adaptive_chunking",
            "ai_adaptive_retry:",
            "request_timeout_seconds",
            "max_length=5000",
            '"maxItems": 5000',
        ):
            self.assertIn(required, ai_source)
        self.assertIn('self.bind("<Map>"', ui_source)
        self.assertIn('t("request_timeout_seconds")', settings_source)
        self.assertIn('t("adaptive_chunking")', settings_source)

    def test_all_toplevels_use_the_shared_icon_base(self) -> None:
        for path in (ROOT / "clearlens").glob("ui_*.py"):
            if path.name == "ui_common.py":
                continue
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("(tk.Toplevel)", source, path.name)
        app_source = (ROOT / "clearlens" / "app.py").read_text(encoding="utf-8")
        self.assertIn("apply_window_icon(self, default=True)", app_source)

    def test_frozen_resources_prefer_the_executable_directory(self) -> None:
        original_executable = sys.executable
        had_frozen = hasattr(sys, "frozen")
        original_frozen = getattr(sys, "frozen", None)
        had_meipass = hasattr(sys, "_MEIPASS")
        original_meipass = getattr(sys, "_MEIPASS", None)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                internal = root / "_internal"
                external_icon = root / "assets" / "app.png"
                internal_icon = internal / "assets" / "app.png"
                external_icon.parent.mkdir(parents=True)
                internal_icon.parent.mkdir(parents=True)
                external_icon.write_bytes(b"external")
                internal_icon.write_bytes(b"internal")
                sys.executable = str(root / "BFSU_ClearLens.exe")
                sys.frozen = True  # type: ignore[attr-defined]
                sys._MEIPASS = str(internal)  # type: ignore[attr-defined]

                namespace = runpy.run_path(str(ROOT / "clearlens" / "config.py"))

                self.assertEqual(namespace["resource_path"]("assets/app.png"), external_icon)
        finally:
            sys.executable = original_executable
            if had_frozen:
                sys.frozen = original_frozen  # type: ignore[attr-defined]
            elif hasattr(sys, "frozen"):
                del sys.frozen  # type: ignore[attr-defined]
            if had_meipass:
                sys._MEIPASS = original_meipass  # type: ignore[attr-defined]
            elif hasattr(sys, "_MEIPASS"):
                del sys._MEIPASS  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
