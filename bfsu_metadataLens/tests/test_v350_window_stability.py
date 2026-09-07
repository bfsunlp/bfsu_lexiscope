from pathlib import Path

from metadatalens.config import APP_VERSION


def _app_source() -> str:
    return (Path(__file__).resolve().parents[1] / "metadatalens" / "app.py").read_text(encoding="utf-8")


def test_v355_version():
    assert APP_VERSION == "3.5.5"


def test_application_dialogs_do_not_use_persistent_grabs_topmost_or_force_focus():
    source = _app_source()
    assert ".grab_set(" not in source
    assert 'attributes("-topmost", True)' not in source
    assert 'attributes("-topmost", False)' not in source
    assert "dialog.focus_force()" not in source


def test_dialog_manager_does_not_rewrite_native_windows_ownership_or_zorder():
    source = _app_source()
    assert "ctypes.windll.user32" not in source
    assert "SetWindowLongPtrW" not in source
    assert "user32.SetWindowPos" not in source
    assert "user32.ShowWindow" not in source
    assert "user32.BringWindowToTop" not in source
    assert "user32.SetForegroundWindow" not in source


def test_dialog_shell_is_native_tk_not_ctktoplevel():
    source = _app_source()
    assert "dialog = tk.Toplevel(self.root)" in source
    assert "dialog = ctk.CTkToplevel(" not in source
    assert "self._dialog_stack: list[tk.Toplevel]" in source


def test_dialog_uses_standard_transient_relationship_without_map_unmap_loops():
    source = _app_source()
    assert "dialog.transient(owner)" in source
    assert 'dialog.bind("<Map>"' not in source
    assert 'dialog.bind("<Unmap>"' not in source
    assert "_restore_application_windows" not in source


def test_dialog_is_built_while_withdrawn_then_presented_once():
    source = _app_source()
    assert "dialog.withdraw()" in source
    assert "dialog.after_idle(lambda: self._present_dialog(dialog, owner, width, height))" in source
    assert source.count("dialog.deiconify()") == 1
    assert "dialog.lift(owner)" in source
    assert source.count("dialog.focus_set()") == 1


def test_delayed_dialog_action_only_reapplies_icon():
    source = _app_source()
    assert "def reapply_icon_only" in source
    assert "dialog.after(260, reapply_icon_only)" in source
    assert "for delay in (45, 140, 320)" not in source


def test_dialog_first_open_size_is_content_aware():
    source = _app_source()
    assert "content_width = max(1, int(dialog.winfo_reqwidth()))" in source
    assert "content_height = max(1, int(dialog.winfo_reqheight()))" in source
    assert "requested_width = max(width, content_width + 48)" in source
    assert "requested_height = max(height, content_height + 56)" in source
    assert "realized_width = max(requested_width, int(dialog.winfo_reqwidth()) + 48)" in source
    assert "realized_height = max(requested_height, int(dialog.winfo_reqheight()) + 56)" in source


def test_major_dialogs_have_roomy_recommended_sizes():
    source = _app_source()
    expected = [
        'app._new_dialog(app.t("new_project"), 940, 740, modal=True)',
        'app._new_dialog(app.t("provider_settings"), 1020, 840, modal=False)',
        'app._new_dialog(app.t("template_manager"), 1120, 790, modal=False)',
        'app._new_dialog(app.t("ai_extract"), 1380, 920, modal=False)',
        'app._new_dialog(app.t("batch_ai_extract"), 1540, 960, modal=False)',
        'app._new_dialog(app.t("batch_edit_field"), 1120, 820, modal=False)',
        'app._new_dialog(app.t("ai_schema"), 1420, 950, modal=False)',
        'app._new_dialog(app.t("user_guide"), 1040, 840, modal=False)',
        'app._new_dialog(app.t("about"), 1040, 840, modal=False)',
    ]
    for line in expected:
        assert line in source
