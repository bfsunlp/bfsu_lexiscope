from __future__ import annotations

import sys
import threading
import time
from copy import deepcopy
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image

from .config import APP_NAME, APP_VERSION, PROVIDER_DEFAULTS, SettingsStore, app_root
from .excel_io import ExcelImporter
from .i18n import I18N
from .llm import (
    ExtractionResult,
    LLMCancelledError,
    SchemaGenerationResult,
    apply_extraction,
    apply_schema_generation,
    extract_metadata,
    friendly_llm_error,
    generate_schema,
    read_pasted_text,
    read_source_file,
    read_webpage,
)
from .models import DATA_TYPES, FIELD_LEVELS, MetadataField, MetadataProject, MetadataRecord, MetadataSchema
from .repository import XMLRepository
from .schema_manager import load_schema_xml, save_schema_xml
from .templates import TemplateItem, TemplateLibrary
from .utils import extract_http_urls, safe_read_text
from .ui.components import (
    body_label,
    card,
    heading_label,
    primary_button,
    quiet_button,
    secondary_button,
    style_tabview,
    surface_card,
)
from .ui.dpi import centre_dialog, safe_window_geometry
from .ui.theme import COLORS, apply_theme, configure_customtkinter, ctk_font
from .validators import validate_record, validate_schema
from .xml_io import XMLImporter


TYPE_HINTS_ZH = {
    "string": "普通文本；适合名称、标题、编号、机构等。",
    "integer": "整数，例如 1250。",
    "float": "数值，可含小数，例如 12.5。",
    "date": "日期，建议 YYYY-MM-DD，例如 2026-09-07。",
    "year": "四位年份 YYYY，例如 2026。",
    "boolean": "布尔值：是/否；项目 XML 中保存为 true/false。",
    "enum": "受控词表；请在“受控词表”中用分号分隔允许值。",
    "long_text": "较长文本，例如摘要、说明、备注或内容描述。",
    "language_code": "语言代码，建议 ISO 风格，如 zh、en、zh-CN。",
    "file_path": r"文件路径，例如 C:\corpus\text01.txt。",
}
TYPE_HINTS_EN = {
    "string": "Plain text for names, titles, identifiers, institutions, etc.",
    "integer": "Integer, e.g. 1250.",
    "float": "Number with optional decimal, e.g. 12.5.",
    "date": "Date; recommended YYYY-MM-DD, e.g. 2026-09-07.",
    "year": "Four-digit year YYYY, e.g. 2026.",
    "boolean": "Boolean yes/no; stored as true/false in project XML.",
    "enum": "Controlled vocabulary; separate allowed values with semicolons.",
    "long_text": "Long text such as an abstract, description or note.",
    "language_code": "ISO-style language code such as zh, en, zh-CN.",
    "file_path": r"File path, e.g. C:\corpus\text01.txt.",
}


def field_hint(field: MetadataField, lang: str) -> str:
    base = (TYPE_HINTS_ZH if lang.startswith("zh") else TYPE_HINTS_EN).get(field.data_type, "")
    extras: list[str] = []
    if field.example:
        extras.append(("示例" if lang.startswith("zh") else "Example") + f": {field.example}")
    if field.validation_rule:
        extras.append(("校验" if lang.startswith("zh") else "Validation") + f": {field.validation_rule}")
    if field.repeatable:
        extras.append("多个值用分号 ; 分隔" if lang.startswith("zh") else "Separate repeated values with semicolons (;)")
    if field.required:
        extras.append("必填字段" if lang.startswith("zh") else "Required field")
    return "  ".join([x for x in [base, *extras] if x])


class MetadataLensApp:
    """BFSU MetadataLens desktop application.

    The main window deliberately follows BFSU CiteLens' layout grammar:
    grouped top toolbar, light project/action sidebar, CTk segmented tabs,
    high-performance ttk data grids, lower details pane and fixed status bar.
    """

    TAB_KEYS = ("overview", "schema_design", "record_entry", "records_table", "import_export")

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.i18n = I18N(self.settings.language)
        self.repository = XMLRepository()
        self.excel = ExcelImporter()
        self.xml_importer = XMLImporter()
        self.templates = TemplateLibrary()

        self.project: MetadataProject | None = None
        self.current_record: MetadataRecord | None = None
        self.record_inputs: dict[str, object] = {}
        self.schema_vars: dict[str, tk.Variable] = {}
        self.schema_widgets: dict[str, object] = {}
        self.tabs: dict[str, ctk.CTkFrame] = {}
        self.tab_names: dict[str, str] = {}
        self.card_values: dict[str, ctk.CTkLabel] = {}
        self._dialog_stack: list[tk.Toplevel] = []
        self._sidebar_restore_width = max(460, int(self.settings.sidebar_width))
        self._details_restore_ratio = min(0.78, max(0.62, float(self.settings.list_pane_ratio)))
        self._pane_layout_attempts = 0
        self._record_form_loading = False
        self._record_form_dirty = False

        self.project_name_var = tk.StringVar(value=self.t("no_project_loaded"))
        self.project_path_var = tk.StringVar(value="")
        self.project_type_var = tk.StringVar(value="—")
        self.project_schema_var = tk.StringVar(value="—")
        self.project_records_var = tk.StringVar(value="0")
        self.project_fields_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar(value=self.t("status_ready"))
        self.provider_status_var = tk.StringVar(value="")
        self.record_position_var = tk.StringVar(value="")
        self.record_search_var = tk.StringVar(value="")
        self.record_sort_var = tk.StringVar(value="record_id")

        self._configure_root()
        self._build_ui()
        self.refresh_all()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def t(self, key: str, **kwargs) -> str:
        return self.i18n.t(key, **kwargs)

    # ------------------------------------------------------------------
    # Window shell — intentionally parallel to BFSU CiteLens
    # ------------------------------------------------------------------
    def _configure_root(self) -> None:
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        apply_theme(self.root)
        self.root.configure(fg_color=COLORS["background"])
        safe_window_geometry(
            self.root, self.settings.window_geometry, fallback=(1540, 940), minimum=(1180, 740), preserve_saved_position=False
        )
        self._apply_icon(self.root)
        # CustomTkinter can adjust the realized top-level size after Tk first
        # maps the window at high DPI. Re-centre once after realization so the
        # main window always opens in the middle of the primary work area.
        self.root.after(160, lambda: safe_window_geometry(
            self.root, self.root.geometry(), fallback=(1540, 940), minimum=(1180, 740), preserve_saved_position=False
        ))
        # Keep root-window mapping simple.  Child windows are intentionally
        # independent Toplevel windows (no native owner surgery, no repeated
        # Map/Unmap z-order manipulation), because those mechanisms can create
        # a Windows/CustomTkinter remap loop.  The operating system is allowed
        # to manage minimize/restore normally.
        self.root.bind("<Map>", lambda _e: self.root.after(120, self._set_initial_panes), add="+")

    def _apply_icon(self, window: tk.Misc) -> None:
        """Apply the MetadataLens icon to every application-owned window.

        Windows may reset a CTkToplevel icon when the native window handle is
        first mapped, so callers intentionally re-apply this helper after
        deiconify as well as during creation.
        """
        png = app_root() / "assets" / "app.png"
        ico = app_root() / "assets" / "app.ico"
        try:
            if png.exists():
                if not hasattr(self, "_icon_photo"):
                    self._icon_photo = tk.PhotoImage(file=str(png))
                window.iconphoto(True, self._icon_photo)
                # Keep a window-local reference too; this prevents a Toplevel
                # from losing its icon if Tk refreshes native window resources.
                setattr(window, "_metadatalens_icon_ref", self._icon_photo)
            if sys.platform.startswith("win") and ico.exists():
                try:
                    window.iconbitmap(str(ico))
                except tk.TclError:
                    window.iconbitmap(default=str(ico))
        except (tk.TclError, OSError):
            pass

    def _release_dialog_grab(self, dialog: tk.Misc) -> None:
        """Release an application-owned Tk grab defensively.

        MetadataLens does not use persistent grabs for its own dialogs.  This
        helper only protects against a grab that may have been acquired by a
        nested Tk control or platform dialog before a child window is closed.
        """
        try:
            current = self.root.grab_current()
        except tk.TclError:
            current = None
        if current is dialog:
            try:
                dialog.grab_release()
            except tk.TclError:
                pass

    def _release_application_grabs(self) -> None:
        """Release only grabs owned by MetadataLens child windows."""
        try:
            current = self.root.grab_current()
        except tk.TclError:
            return
        if current is None:
            return
        for dialog in list(self._dialog_stack):
            if current is dialog:
                try:
                    dialog.grab_release()
                except tk.TclError:
                    pass
                return

    def _present_dialog(
        self,
        dialog: tk.Toplevel,
        owner: tk.Misc,
        width: int,
        height: int,
    ) -> None:
        """Show one application child window using the native Tk shell.

        MetadataLens deliberately uses :class:`tkinter.Toplevel` for the OS
        window shell and CustomTkinter only for the *contents* of the dialog.
        This avoids a long-standing Windows interaction in CTkToplevel where
        title-bar refresh code can withdraw/remap a window during creation or
        after a resizable/title-bar update.  The visual design remains
        CustomTkinter because every control inside the shell is still CTk.

        The shell is created withdrawn, fully built, centred, then mapped once.
        A normal Tk ``transient`` relationship keeps it above its owner without
        a persistent grab, topmost flag, HWND manipulation, or focus loop.
        """
        try:
            if not dialog.winfo_exists():
                return
        except tk.TclError:
            return

        try:
            # Native ``tk.Toplevel`` geometry is not automatically scaled by
            # CustomTkinter.  At 150–225% Windows scaling, the CTk widgets
            # therefore request substantially more space than the old fixed
            # logical dialog size.  Measure the fully built widget tree before
            # the first map and make the opening size content-aware.
            dialog.update_idletasks()
            content_width = max(1, int(dialog.winfo_reqwidth()))
            content_height = max(1, int(dialog.winfo_reqheight()))
            requested_width = max(width, content_width + 48)
            requested_height = max(height, content_height + 56)

            centre_dialog(
                dialog,
                owner,
                requested_width,
                requested_height,
                minimum=(width, height),
            )
            dialog.deiconify()
            dialog.update_idletasks()

            # Some CTk controls finalize their requested dimensions only after
            # the native shell has been mapped. Measure once more, expanding
            # only when necessary. This is a one-time size correction, not a
            # visibility/z-order loop, so it preserves the v3.5.5 window
            # stability fix.
            realized_width = max(requested_width, int(dialog.winfo_reqwidth()) + 48)
            realized_height = max(requested_height, int(dialog.winfo_reqheight()) + 56)
            centre_dialog(
                dialog,
                owner,
                realized_width,
                realized_height,
                minimum=(width, height),
            )
            self._apply_icon(dialog)
            dialog.lift(owner)
            dialog.focus_set()
        except tk.TclError:
            return

        # Re-apply the application icon after CustomTkinter widgets have
        # finished their delayed initialization.  This changes only the icon;
        # it never changes visibility, geometry, ownership, or z-order.
        def reapply_icon_only() -> None:
            try:
                if dialog.winfo_exists():
                    self._apply_icon(dialog)
            except tk.TclError:
                pass

        try:
            dialog.after(260, reapply_icon_only)
        except tk.TclError:
            pass

    def _new_dialog(
        self,
        title: str,
        width: int,
        height: int,
        *,
        modal: bool = False,
        parent: tk.Misc | None = None,
    ) -> tk.Toplevel:
        """Create a stable application child window.

        The window shell is a standard ``tk.Toplevel`` rather than
        ``customtkinter.CTkToplevel``.  This is intentional: CTkToplevel 5.x on
        Windows performs internal withdraw/deiconify operations while changing
        title-bar state, and those operations can make a newly created dialog
        disappear behind its owner or remain withdrawn.  Using the native Tk
        shell removes that lifecycle interference while preserving the full
        CiteLens-style CustomTkinter UI inside the window.

        No persistent ``grab_set``, ``focus_force``, ``-topmost`` pulse, native
        HWND owner rewrite, or Map/Unmap re-raising is used.
        """
        owner = parent or self.root
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title(title)
        dialog.configure(bg=COLORS["background"])
        try:
            dialog.transient(owner)
        except tk.TclError:
            pass
        dialog.resizable(True, True)
        setattr(dialog, "_metadatalens_modal_hint", bool(modal))
        self._apply_icon(dialog)
        self._dialog_stack.append(dialog)

        def close_dialog() -> None:
            self._release_dialog_grab(dialog)
            try:
                dialog.destroy()
            except tk.TclError:
                pass

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.bind("<Escape>", lambda _e: close_dialog(), add="+")

        def forget(event=None) -> None:
            if event is not None and getattr(event, "widget", None) is not dialog:
                return
            self._release_dialog_grab(dialog)
            self._dialog_stack = [item for item in self._dialog_stack if item is not dialog]

        dialog.bind("<Destroy>", forget, add="+")

        # Build code in each dialog class runs synchronously before the event
        # loop becomes idle.  The user therefore never sees a half-built shell.
        dialog.after_idle(lambda: self._present_dialog(dialog, owner, width, height))
        return dialog

    def _build_ui(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.tabs.clear()
        self.tab_names.clear()
        self.card_values.clear()
        self.schema_vars.clear()
        self.schema_widgets.clear()
        self.record_inputs.clear()

        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()

        main_host = ctk.CTkFrame(self.root, fg_color=COLORS["background"], corner_radius=0)
        main_host.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))
        self.main_pane = ttk.Panedwindow(main_host, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        sidebar_host = card(self.main_pane, width=460)
        sidebar = ctk.CTkScrollableFrame(
            sidebar_host,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["blue2"],
            scrollbar_button_hover_color=COLORS["blue"],
        )
        sidebar.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        content = ctk.CTkFrame(self.main_pane, fg_color=COLORS["background"], corner_radius=0)
        self.main_pane.add(sidebar_host, weight=0)
        self.main_pane.add(content, weight=1)
        self.main_pane.bind("<Double-Button-1>", self._toggle_sidebar_pane, add="+")

        self._build_sidebar(sidebar)
        self._build_content(content)
        # PanedWindow sash positions are unreliable until the top-level window
        # has been mapped and CustomTkinter has completed DPI/layout passes.
        # Apply the initial positions more than once so the sidebar and the
        # upper tabbed workspace are visible on the very first launch.
        self._pane_layout_attempts = 0
        for delay in (0, 90, 220, 450, 800):
            self.root.after(delay, self._set_initial_panes)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)

        file_menu = tk.Menu(menu)
        file_menu.add_command(label=self.t("new_project"), command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label=self.t("open_project"), command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label=self.t("save"), command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label=self.t("save_as"), command=self.save_project_as)
        file_menu.add_command(label=self.t("close_project"), command=self.close_project)
        file_menu.add_separator()
        file_menu.add_command(label=self.t("import_excel"), command=self.import_excel)
        file_menu.add_command(label=self.t("import_xml"), command=self.import_xml)
        export_menu = tk.Menu(file_menu)
        export_menu.add_command(label=self.t("export_xml"), command=self.export_records_xml)
        export_menu.add_command(label=self.t("export_excel"), command=self.export_excel)
        export_menu.add_command(label=self.t("export_csv"), command=self.export_csv)
        export_menu.add_command(label=self.t("export_schema"), command=self.export_schema)
        file_menu.add_cascade(label=self.t("export"), menu=export_menu)
        file_menu.add_separator()
        file_menu.add_command(label=self.t("exit"), command=self.on_close)
        menu.add_cascade(label=self.t("file"), menu=file_menu)

        schema_menu = tk.Menu(menu)
        schema_menu.add_command(label=self.t("open_schema_tab"), command=lambda: self.show_tab("schema_design"))
        schema_menu.add_command(label=self.t("import_schema"), command=self.import_schema)
        schema_menu.add_command(label=self.t("export_schema"), command=self.export_schema)
        schema_menu.add_command(label=self.t("validate_schema"), command=self.validate_schema_action)
        schema_menu.add_separator()
        schema_menu.add_command(label=self.t("save_user_template"), command=self.save_user_template)
        schema_menu.add_command(label=self.t("template_manager"), command=self.open_template_manager)
        schema_menu.add_separator()
        schema_menu.add_command(label=self.t("ai_schema"), command=self.open_ai_schema)
        menu.add_cascade(label=self.t("schema"), menu=schema_menu)

        record_menu = tk.Menu(menu)
        record_menu.add_command(label=self.t("new_record"), command=self.new_record, accelerator="Ctrl+R")
        record_menu.add_command(label=self.t("save_record"), command=self.save_current_record)
        record_menu.add_command(label=self.t("validate_record"), command=self.validate_current_record)
        record_menu.add_separator()
        record_menu.add_command(label=self.t("ai_extract"), command=self.open_ai_extract)
        record_menu.add_command(label=self.t("batch_ai_extract"), command=self.open_batch_ai_extract)
        record_menu.add_command(label=self.t("batch_edit_field"), command=self.open_batch_edit)
        record_menu.add_command(label=self.t("records_table"), command=lambda: self.show_tab("records_table"))
        menu.add_cascade(label=self.t("records"), menu=record_menu)

        language_menu = tk.Menu(menu)
        self.language_menu_var = tk.StringVar(value=self.i18n.language)
        language_menu.add_radiobutton(label="中文", value="zh_CN", variable=self.language_menu_var, command=lambda: self.change_language("zh_CN"))
        language_menu.add_radiobutton(label="English", value="en_US", variable=self.language_menu_var, command=lambda: self.change_language("en_US"))
        menu.add_cascade(label=self.t("language"), menu=language_menu)

        settings_menu = tk.Menu(menu)
        settings_menu.add_command(label=self.t("provider_settings"), command=self.open_provider_settings)
        menu.add_cascade(label=self.t("settings"), menu=settings_menu)

        view_menu = tk.Menu(menu)
        view_menu.add_command(label=self.t("overview"), command=lambda: self.show_tab("overview"))
        view_menu.add_command(label=self.t("schema_design"), command=lambda: self.show_tab("schema_design"))
        view_menu.add_command(label=self.t("record_entry"), command=lambda: self.show_tab("record_entry"))
        view_menu.add_command(label=self.t("records_table"), command=lambda: self.show_tab("records_table"))
        view_menu.add_command(label=self.t("import_export"), command=lambda: self.show_tab("import_export"))
        menu.add_cascade(label=self.t("view"), menu=view_menu)

        help_menu = tk.Menu(menu)
        help_menu.add_command(label=self.t("user_guide"), command=self.show_user_guide)
        help_menu.add_command(label=self.t("about"), command=self.show_about)
        menu.add_cascade(label=self.t("help"), menu=help_menu)

        self.root.config(menu=menu)
        self.menu = menu
        self.root.bind_all("<Control-n>", lambda _e: self.new_project())
        self.root.bind_all("<Control-o>", lambda _e: self.open_project())
        self.root.bind_all("<Control-s>", lambda _e: self.save_project())
        self.root.bind_all("<Control-r>", lambda _e: self.new_record())

    def _build_toolbar(self) -> None:
        bar = ctk.CTkFrame(self.root, fg_color=COLORS["toolbar"], corner_radius=0, height=90)
        bar.pack(fill=tk.X, padx=0, pady=(0, 7))
        bar.pack_propagate(False)
        secondary_button(bar, text=self.t("provider_settings_short"), command=self.open_provider_settings, width=104, height=36).pack(side=tk.RIGHT, padx=8, pady=29)

        groups = (
            (
                "group_project",
                (
                    ("toolbar_new", self.new_project, True),
                    ("toolbar_open", self.open_project, False),
                    ("toolbar_save", self.save_project, False),
                ),
            ),
            (
                "group_schema",
                (
                    ("toolbar_schema", lambda: self.show_tab("schema_design"), True),
                    ("toolbar_templates", self.open_template_manager, False),
                    ("toolbar_ai_schema", self.open_ai_schema, False),
                ),
            ),
            (
                "group_records",
                (
                    ("toolbar_new_record", self.new_record, True),
                    ("toolbar_records", lambda: self.show_tab("records_table"), False),
                    ("toolbar_ai_extract", self.open_ai_extract, False),
                ),
            ),
            (
                "group_data",
                (
                    ("toolbar_import_excel", self.import_excel, False),
                    ("toolbar_import_xml", self.import_xml, False),
                    ("toolbar_export", lambda: self.show_tab("import_export"), False),
                ),
            ),
        )
        widths = {
            "toolbar_new": 92,
            "toolbar_open": 92,
            "toolbar_save": 92,
            "toolbar_schema": 112,
            "toolbar_templates": 112,
            "toolbar_ai_schema": 122,
            "toolbar_new_record": 104,
            "toolbar_records": 108,
            "toolbar_ai_extract": 126,
            "toolbar_import_excel": 110,
            "toolbar_import_xml": 106,
            "toolbar_export": 100,
        }
        for group_index, (title_key, actions) in enumerate(groups):
            group = ctk.CTkFrame(bar, fg_color="transparent", corner_radius=0)
            group.pack(side=tk.LEFT, fill=tk.Y, padx=(8 if group_index == 0 else 3, 3), pady=4)
            body_label(group, text=self.t(title_key), muted=True, font=ctk_font("small", semibold=True)).pack(fill=tk.X, padx=3, pady=(0, 1))
            row = ctk.CTkFrame(group, fg_color="transparent", corner_radius=0)
            row.pack(fill=tk.X)
            for key, command, primary in actions:
                factory = primary_button if primary else secondary_button
                factory(row, text=self.t(key), command=command, width=widths[key], height=36).pack(side=tk.LEFT, padx=2)

    def _build_sidebar(self, parent: ctk.CTkScrollableFrame) -> None:
        heading_label(parent, text=self.t("project")).pack(anchor=tk.W, padx=14, pady=(14, 7))
        body_label(parent, textvariable=self.project_name_var, semibold=True, font=ctk_font("subtitle", semibold=True), wraplength=385).pack(fill=tk.X, padx=14)
        body_label(parent, textvariable=self.project_path_var, muted=True, wraplength=385).pack(fill=tk.X, padx=14, pady=(3, 9))
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"], corner_radius=0).pack(fill=tk.X, padx=14, pady=4)

        for label_key, variable in (
            ("corpus_type", self.project_type_var),
            ("schema", self.project_schema_var),
            ("records", self.project_records_var),
            ("field_count", self.project_fields_var),
        ):
            body_label(parent, text=self.t(label_key), semibold=True, font=ctk_font("small", semibold=True)).pack(fill=tk.X, padx=14, pady=(8, 0))
            body_label(parent, textvariable=variable, wraplength=385).pack(fill=tk.X, padx=14)

        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"], corner_radius=0).pack(fill=tk.X, padx=14, pady=13)

        body_label(parent, text=self.t("group_project"), semibold=True, text_color=COLORS["navy"]).pack(fill=tk.X, padx=14, pady=(3, 2))
        primary_button(parent, text=self.t("sidebar_new_project"), command=self.new_project, height=48).pack(fill=tk.X, padx=14, pady=3)
        secondary_button(parent, text=self.t("sidebar_open_project"), command=self.open_project, height=46).pack(fill=tk.X, padx=14, pady=3)
        secondary_button(parent, text=self.t("sidebar_templates"), command=self.open_template_manager, height=46).pack(fill=tk.X, padx=14, pady=3)

        body_label(parent, text=self.t("group_schema"), semibold=True, text_color=COLORS["navy"]).pack(fill=tk.X, padx=14, pady=(12, 2))
        secondary_button(parent, text=self.t("sidebar_schema_design"), command=lambda: self.show_tab("schema_design"), height=46).pack(fill=tk.X, padx=14, pady=3)
        secondary_button(parent, text=self.t("sidebar_import_schema"), command=self.import_schema, height=46).pack(fill=tk.X, padx=14, pady=3)
        secondary_button(parent, text=self.t("sidebar_ai_schema"), command=self.open_ai_schema, height=48).pack(fill=tk.X, padx=14, pady=3)

        body_label(parent, text=self.t("group_records"), semibold=True, text_color=COLORS["navy"]).pack(fill=tk.X, padx=14, pady=(12, 2))
        secondary_button(parent, text=self.t("sidebar_new_record"), command=self.new_record, height=46).pack(fill=tk.X, padx=14, pady=3)
        secondary_button(parent, text=self.t("sidebar_records_table"), command=lambda: self.show_tab("records_table"), height=46).pack(fill=tk.X, padx=14, pady=3)
        secondary_button(parent, text=self.t("sidebar_ai_extract"), command=self.open_ai_extract, height=48).pack(fill=tk.X, padx=14, pady=3)

        body_label(parent, text=self.t("group_data"), semibold=True, text_color=COLORS["navy"]).pack(fill=tk.X, padx=14, pady=(12, 2))
        secondary_button(parent, text=self.t("sidebar_import_excel"), command=self.import_excel, height=46).pack(fill=tk.X, padx=14, pady=3)
        secondary_button(parent, text=self.t("sidebar_import_xml"), command=self.import_xml, height=46).pack(fill=tk.X, padx=14, pady=3)
        secondary_button(parent, text=self.t("sidebar_import_export"), command=lambda: self.show_tab("import_export"), height=46).pack(fill=tk.X, padx=14, pady=3)
        body_label(parent, text="BFSU LexiScope", muted=True, anchor="center").pack(fill=tk.X, pady=(22, 12))

    def _build_content(self, parent: ctk.CTkFrame) -> None:
        self.vertical_pane = ttk.Panedwindow(parent, orient=tk.VERTICAL)
        self.vertical_pane.pack(fill=tk.BOTH, expand=True)
        upper = ctk.CTkFrame(self.vertical_pane, fg_color=COLORS["background"], corner_radius=0)
        details_frame = card(self.vertical_pane)
        self.vertical_pane.add(upper, weight=4)
        self.vertical_pane.add(details_frame, weight=1)
        self.vertical_pane.bind("<Double-Button-1>", self._toggle_details_pane, add="+")

        self.notebook = ctk.CTkTabview(
            upper,
            fg_color=COLORS["background"],
            segmented_button_fg_color=COLORS["toolbar"],
            segmented_button_selected_color=COLORS["blue"],
            segmented_button_selected_hover_color=COLORS["blue2"],
            segmented_button_unselected_color=COLORS["toolbar"],
            segmented_button_unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._on_tab_changed,
        )
        style_tabview(self.notebook)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        for key in self.TAB_KEYS:
            name = self.t(key)
            tab = self.notebook.add(name)
            tab.configure(fg_color=COLORS["background"], corner_radius=0)
            self.tabs[key] = tab
            self.tab_names[key] = name

        self._build_overview_tab()
        self._build_schema_tab()
        self._build_record_tab()
        self._build_records_tab()
        self._build_io_tab()
        self.notebook.set(self.tab_names["overview"])

        body_label(details_frame, text=self.t("details"), semibold=True, text_color=COLORS["navy"]).pack(fill=tk.X, padx=10, pady=(7, 1))
        detail_body = ctk.CTkFrame(details_frame, fg_color="transparent", corner_radius=0)
        detail_body.pack(fill=tk.BOTH, expand=True, padx=7, pady=(0, 7))
        buttons = ctk.CTkFrame(detail_body, fg_color="transparent", corner_radius=0)
        buttons.pack(fill=tk.X, pady=(0, 6))
        primary_button(buttons, text=self.t("detail_edit"), command=self.edit_context_item, width=116, height=36).pack(side=tk.LEFT, padx=(0, 5))
        secondary_button(buttons, text=self.t("detail_validate"), command=self.validate_context_item, width=118, height=36).pack(side=tk.LEFT, padx=5)
        secondary_button(buttons, text=self.t("detail_copy"), command=self.copy_record, width=110, height=36).pack(side=tk.LEFT, padx=5)
        secondary_button(buttons, text=self.t("detail_delete"), command=self.delete_record, width=112, height=36).pack(side=tk.LEFT, padx=5)
        secondary_button(buttons, text=self.t("provider_settings_short"), command=self.open_provider_settings, width=120, height=36).pack(side=tk.RIGHT, padx=(5, 0))

        self.details_text = ctk.CTkTextbox(
            detail_body,
            height=130,
            wrap=tk.WORD,
            fg_color=COLORS["surface"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=5,
            font=ctk_font("body"),
            scrollbar_button_color=COLORS["blue2"],
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        self.details_text.configure(state=tk.DISABLED)

    def _build_statusbar(self) -> None:
        bar = ctk.CTkFrame(self.root, fg_color=COLORS["toolbar"], corner_radius=0, height=58)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)
        body_label(bar, textvariable=self.status_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8)
        body_label(bar, textvariable=self.provider_status_var, muted=True, anchor="e").pack(side=tk.RIGHT, padx=12, pady=8)

    def _set_initial_panes(self) -> None:
        """Keep both primary panes visible on first launch and rebuilds.

        Tk/ttk PanedWindow can report a temporary 1×1 size during early layout,
        especially with CustomTkinter and high Windows DPI scaling. Setting the
        sash at that moment can collapse one pane. This routine waits for usable
        dimensions and is intentionally idempotent so several scheduled calls
        converge on the same visible layout.
        """
        try:
            self.root.update_idletasks()
            width = int(self.main_pane.winfo_width())
            height = int(self.vertical_pane.winfo_height())
            self._pane_layout_attempts += 1
            if width < 900 or height < 520:
                if self._pane_layout_attempts < 10:
                    self.root.after(140, self._set_initial_panes)
                return

            sidebar_max = max(460, width - 820)
            sidebar_target = min(max(460, int(self._sidebar_restore_width)), sidebar_max)
            self.main_pane.sashpos(0, sidebar_target)

            ratio = min(0.78, max(0.62, float(self._details_restore_ratio)))
            upper_target = int(height * ratio)
            upper_min = min(460, max(360, height - 260))
            upper_max = max(upper_min, height - 210)
            upper_target = min(max(upper_min, upper_target), upper_max)
            self.vertical_pane.sashpos(0, upper_target)
        except (AttributeError, tk.TclError, ValueError):
            pass

    def _toggle_sidebar_pane(self, _event=None):
        try:
            current = self.main_pane.sashpos(0)
            if current > 100:
                self._sidebar_restore_width = current
                self.main_pane.sashpos(0, 10)
            else:
                width = max(1, self.main_pane.winfo_width())
                self.main_pane.sashpos(0, min(max(460, self._sidebar_restore_width), max(460, width - 820)))
        except (AttributeError, tk.TclError):
            pass
        return "break"

    def _toggle_details_pane(self, _event=None):
        try:
            height = max(1, self.vertical_pane.winfo_height())
            current = self.vertical_pane.sashpos(0)
            if current < height - 90:
                self._details_restore_ratio = min(0.78, max(0.62, current / height))
                self.vertical_pane.sashpos(0, height - 12)
            else:
                self.vertical_pane.sashpos(0, min(max(440, int(height * self._details_restore_ratio)), max(440, height - 210)))
        except (AttributeError, tk.TclError):
            pass
        return "break"

    # ------------------------------------------------------------------
    # Main tabs
    # ------------------------------------------------------------------
    def _build_overview_tab(self) -> None:
        tab = self.tabs["overview"]
        cards = ctk.CTkFrame(tab, fg_color="transparent", corner_radius=0)
        cards.pack(fill=tk.X, padx=7, pady=(5, 3))
        metrics = (
            ("metric_fields", "field_count"),
            ("metric_records", "record_count"),
            ("metric_required", "required_count"),
            ("metric_repeatable", "repeatable_count"),
            ("metric_missing", "missing_required"),
            ("metric_provider", "provider"),
        )
        for i, (metric, label_key) in enumerate(metrics):
            c = card(cards)
            c.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
            body_label(c, text=self.t(label_key), muted=True).pack(fill=tk.X, padx=14, pady=(12, 0))
            value = ctk.CTkLabel(c, text="0", text_color=COLORS["blue"], font=ctk_font("metric", semibold=True), anchor="w")
            value.pack(fill=tk.X, padx=14, pady=(1, 10))
            self.card_values[metric] = value
        for i in range(3):
            cards.columnconfigure(i, weight=1)

        guide = ctk.CTkScrollableFrame(
            tab,
            fg_color=COLORS["panel"],
            corner_radius=7,
            border_width=1,
            border_color=COLORS["border"],
            scrollbar_button_color=COLORS["blue2"],
            scrollbar_button_hover_color=COLORS["blue"],
        )
        guide.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 12))
        body_label(guide, text=self.t("workflow_heading"), semibold=True, font=ctk_font("subtitle", semibold=True)).pack(fill=tk.X, padx=16, pady=(14, 5))
        for title_key, description_key, command in (
            ("workflow_project", "workflow_project_desc", self.new_project),
            ("workflow_schema", "workflow_schema_desc", lambda: self.show_tab("schema_design")),
            ("workflow_entry", "workflow_entry_desc", lambda: self.show_tab("record_entry")),
            ("workflow_import", "workflow_import_desc", lambda: self.show_tab("import_export")),
            ("workflow_ai", "workflow_ai_desc", self.open_provider_settings),
            ("workflow_validate", "workflow_validate_desc", self.validate_schema_action),
        ):
            scope = surface_card(guide)
            scope.pack(fill=tk.X, padx=14, pady=6)
            body_label(scope, text=self.t(title_key), semibold=True, text_color=COLORS["navy"]).pack(fill=tk.X, padx=13, pady=(10, 2))
            body_label(scope, text=self.t(description_key), wraplength=930, muted=True).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(13, 6), pady=(0, 10))
            quiet_button(scope, text=self.t("open"), command=command, width=86, height=34).pack(side=tk.RIGHT, padx=12, pady=(0, 10))

    def _build_schema_tab(self) -> None:
        tab = self.tabs["schema_design"]
        controls = card(tab)
        controls.pack(fill=tk.X, padx=6, pady=(4, 4))

        identity = ctk.CTkFrame(controls, fg_color="transparent", corner_radius=0)
        identity.pack(fill=tk.X, padx=7, pady=(6, 2))
        body_label(identity, text=self.t("schema_name"), semibold=True).pack(side=tk.LEFT, padx=(3, 6))
        self.schema_name_var = tk.StringVar()
        ctk.CTkEntry(
            identity, textvariable=self.schema_name_var, width=330, height=36,
            fg_color=COLORS["surface"], border_color=COLORS["border"], font=ctk_font("body"),
        ).pack(side=tk.LEFT, padx=(0, 12), fill=tk.X, expand=True)
        body_label(identity, text=self.t("schema_version"), semibold=True).pack(side=tk.LEFT, padx=(3, 6))
        self.schema_version_var = tk.StringVar(value="1.0")
        ctk.CTkEntry(
            identity, textvariable=self.schema_version_var, width=105, height=36,
            fg_color=COLORS["surface"], border_color=COLORS["border"], font=ctk_font("body"),
        ).pack(side=tk.LEFT, padx=(0, 8))
        primary_button(identity, text=self.t("apply_schema_info"), command=self.apply_schema_identity, width=145, height=36).pack(side=tk.LEFT, padx=3)

        row1 = ctk.CTkFrame(controls, fg_color="transparent", corner_radius=0)
        row1.pack(fill=tk.X, padx=7, pady=(5, 2))
        primary_button(row1, text=self.t("add_field"), command=self.schema_add, width=106, height=36).pack(side=tk.LEFT, padx=3)
        secondary_button(row1, text=self.t("delete_field"), command=self.schema_delete, width=106, height=36).pack(side=tk.LEFT, padx=3)
        secondary_button(row1, text=self.t("select_all"), command=self.schema_select_all, width=92, height=36).pack(side=tk.LEFT, padx=3)
        secondary_button(row1, text=self.t("delete_all"), command=self.schema_delete_all, width=104, height=36).pack(side=tk.LEFT, padx=3)
        secondary_button(row1, text=self.t("move_up"), command=lambda: self.schema_move(-1), width=88, height=36).pack(side=tk.LEFT, padx=3)
        secondary_button(row1, text=self.t("move_down"), command=lambda: self.schema_move(1), width=88, height=36).pack(side=tk.LEFT, padx=3)
        primary_button(row1, text=self.t("ai_schema"), command=self.open_ai_schema, width=160, height=36).pack(side=tk.RIGHT, padx=3)

        row2 = ctk.CTkFrame(controls, fg_color="transparent", corner_radius=0)
        row2.pack(fill=tk.X, padx=7, pady=(0, 5))
        secondary_button(row2, text=self.t("import_schema"), command=self.import_schema, width=126, height=34).pack(side=tk.LEFT, padx=3)
        secondary_button(row2, text=self.t("export_schema"), command=self.export_schema, width=126, height=34).pack(side=tk.LEFT, padx=3)
        secondary_button(row2, text=self.t("validate_schema"), command=self.validate_schema_action, width=132, height=34).pack(side=tk.LEFT, padx=3)
        secondary_button(row2, text=self.t("save_user_template"), command=self.save_user_template, width=152, height=34).pack(side=tk.LEFT, padx=3)
        secondary_button(row2, text=self.t("template_manager"), command=self.open_template_manager, width=126, height=34).pack(side=tk.LEFT, padx=3)
        body_label(row2, text=self.t("schema_help"), muted=True, wraplength=530).pack(side=tk.RIGHT, padx=8)

        split = ttk.Panedwindow(tab, orient=tk.HORIZONTAL)
        split.pack(fill=tk.BOTH, expand=True, padx=6, pady=(2, 6))
        left = card(split)
        right_host = card(split)
        split.add(left, weight=3)
        split.add(right_host, weight=2)

        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)
        cols = ("field_id", "label_zh", "label_en", "xml_tag", "data_type", "required", "repeatable", "level")
        self.schema_tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="extended", style="MetadataLens.Treeview")
        widths = (150, 145, 165, 135, 105, 82, 90, 95)
        for c, w in zip(cols, widths):
            self.schema_tree.heading(c, text=self.t(c))
            self.schema_tree.column(c, width=w, stretch=True)
        sy = ttk.Scrollbar(left, orient="vertical", command=self.schema_tree.yview)
        sx = ttk.Scrollbar(left, orient="horizontal", command=self.schema_tree.xview)
        self.schema_tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.schema_tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        sy.grid(row=0, column=1, sticky="ns", pady=(8, 0), padx=(0, 8))
        sx.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))
        self.schema_tree.bind("<<TreeviewSelect>>", self.schema_on_select)
        self.schema_tree.bind("<Control-a>", lambda _e: (self.schema_select_all(), "break")[1])
        self.schema_tree.bind("<Delete>", lambda _e: self.schema_delete())

        form = ctk.CTkScrollableFrame(
            right_host,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["blue2"],
            scrollbar_button_hover_color=COLORS["blue"],
        )
        form.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        form.grid_columnconfigure(1, weight=1)
        body_label(form, text=self.t("field_properties"), semibold=True, font=ctk_font("subtitle", semibold=True), text_color=COLORS["navy"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8))

        fields = [
            "field_id", "label_zh", "label_en", "xml_tag", "data_type", "level",
            "parent", "order", "default_value", "controlled_values", "validation_rule", "example",
        ]
        row = 1
        for key in fields:
            body_label(form, text=self.t(key)).grid(row=row, column=0, sticky="w", padx=(14, 7), pady=5)
            var: tk.Variable = tk.IntVar(value=0) if key == "order" else tk.StringVar()
            self.schema_vars[key] = var
            if key == "data_type":
                widget = ctk.CTkComboBox(
                    form, variable=var, values=DATA_TYPES, state="readonly", command=lambda _=None: self.update_schema_hint(),
                    fg_color=COLORS["surface"], border_color=COLORS["border"], button_color=COLORS["blue2"], button_hover_color=COLORS["blue"],
                    font=ctk_font("body"), dropdown_font=ctk_font("body"), height=38,
                )
            elif key == "level":
                widget = ctk.CTkComboBox(
                    form, variable=var, values=FIELD_LEVELS, state="readonly",
                    fg_color=COLORS["surface"], border_color=COLORS["border"], button_color=COLORS["blue2"], button_hover_color=COLORS["blue"],
                    font=ctk_font("body"), dropdown_font=ctk_font("body"), height=38,
                )
            else:
                widget = ctk.CTkEntry(form, textvariable=var, fg_color=COLORS["surface"], border_color=COLORS["border"], font=ctk_font("body"), height=38)
            widget.grid(row=row, column=1, sticky="ew", padx=(7, 14), pady=5)
            self.schema_widgets[key] = widget
            row += 1

        checks = ctk.CTkFrame(form, fg_color="transparent", corner_radius=0)
        checks.grid(row=row, column=0, columnspan=2, sticky="ew", padx=14, pady=6)
        for key in ("required", "repeatable", "visible", "editable", "sensitive"):
            var = tk.BooleanVar(value=False)
            self.schema_vars[key] = var
            ctk.CTkCheckBox(
                checks, text=self.t(key), variable=var, command=self.update_schema_hint,
                fg_color=COLORS["blue"], hover_color=COLORS["blue2"], text_color=COLORS["text"], font=ctk_font("body"),
            ).pack(side=tk.LEFT, padx=(0, 14), pady=3)
        row += 1

        body_label(form, text=self.t("description_zh")).grid(row=row, column=0, sticky="nw", padx=(14, 7), pady=5)
        self.schema_desc_zh = ctk.CTkTextbox(form, height=88, fg_color=COLORS["surface"], border_width=1, border_color=COLORS["border"], font=ctk_font("body"))
        self.schema_desc_zh.grid(row=row, column=1, sticky="ew", padx=(7, 14), pady=5)
        row += 1
        body_label(form, text=self.t("description_en")).grid(row=row, column=0, sticky="nw", padx=(14, 7), pady=5)
        self.schema_desc_en = ctk.CTkTextbox(form, height=88, fg_color=COLORS["surface"], border_width=1, border_color=COLORS["border"], font=ctk_font("body"))
        self.schema_desc_en.grid(row=row, column=1, sticky="ew", padx=(7, 14), pady=5)
        row += 1

        hintbox = ctk.CTkFrame(form, fg_color=COLORS["toolbar"], corner_radius=6)
        hintbox.grid(row=row, column=0, columnspan=2, sticky="ew", padx=14, pady=8)
        hintbox.grid_columnconfigure(0, weight=1)
        self.schema_hint = body_label(hintbox, text=self.t("format_hint") + ": —", wraplength=520)
        self.schema_hint.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        row += 1
        primary_button(form, text=self.t("apply_field"), command=self.schema_apply, height=42).grid(row=row, column=0, columnspan=2, sticky="ew", padx=14, pady=(8, 16))

    def _build_record_tab(self) -> None:
        tab = self.tabs["record_entry"]
        controls = card(tab)
        controls.pack(fill=tk.X, padx=6, pady=(4, 4))
        row = ctk.CTkFrame(controls, fg_color="transparent", corner_radius=0)
        row.pack(fill=tk.X, padx=7, pady=6)
        primary_button(row, text=self.t("new_record"), command=self.new_record, width=112, height=36).pack(side=tk.LEFT, padx=3)
        self.save_record_button = secondary_button(row, text=self.t("save_record"), command=self.save_current_record, width=148, height=36)
        self.save_record_button.pack(side=tk.LEFT, padx=3)
        secondary_button(row, text=self.t("validate_record"), command=self.validate_current_record, width=142, height=36).pack(side=tk.LEFT, padx=3)
        secondary_button(row, text=self.t("previous_record"), command=lambda: self.navigate_record(-1), width=98, height=36).pack(side=tk.LEFT, padx=(14, 3))
        secondary_button(row, text=self.t("next_record"), command=lambda: self.navigate_record(1), width=98, height=36).pack(side=tk.LEFT, padx=3)
        body_label(row, textvariable=self.record_position_var, muted=True).pack(side=tk.LEFT, padx=8)
        primary_button(row, text=self.t("ai_extract"), command=self.open_ai_extract, width=174, height=36).pack(side=tk.RIGHT, padx=3)

        self.record_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=COLORS["panel"],
            corner_radius=7,
            border_width=1,
            border_color=COLORS["border"],
            scrollbar_button_color=COLORS["blue2"],
            scrollbar_button_hover_color=COLORS["blue"],
        )
        self.record_scroll.pack(fill=tk.BOTH, expand=True, padx=6, pady=(2, 6))
        self.record_scroll.grid_columnconfigure(1, weight=1)

    def _build_records_tab(self) -> None:
        tab = self.tabs["records_table"]
        controls = card(tab)
        controls.pack(fill=tk.X, padx=6, pady=(4, 4))
        sort_row = ctk.CTkFrame(controls, fg_color="transparent", corner_radius=0)
        sort_row.pack(fill=tk.X, padx=7, pady=(5, 2))
        body_label(sort_row, text=self.t("search"), semibold=True).pack(side=tk.LEFT, padx=(3, 6))
        self.record_search_var = tk.StringVar(value="")
        search = ctk.CTkEntry(
            sort_row, textvariable=self.record_search_var, width=260, height=36,
            fg_color=COLORS["surface"], border_color=COLORS["border"], font=ctk_font("body"),
            placeholder_text=self.t("search_records_placeholder"),
        )
        search.pack(side=tk.LEFT, padx=(0, 8), pady=3)
        self.record_search_var.trace_add("write", lambda *_: self.refresh_records_table())
        body_label(sort_row, text=self.t("sort_by"), semibold=True).pack(side=tk.LEFT, padx=(8, 6))
        self.record_sort_var = tk.StringVar(value="record_id")
        self.record_sort_combo = ctk.CTkComboBox(
            sort_row, variable=self.record_sort_var, values=["record_id", "record_type"], state="readonly", width=190, height=36,
            fg_color=COLORS["surface"], border_color=COLORS["border"], button_color=COLORS["blue2"], button_hover_color=COLORS["blue"],
            font=ctk_font("body"), dropdown_font=ctk_font("body"),
        )
        self.record_sort_combo.pack(side=tk.LEFT, padx=(0, 6), pady=3)
        secondary_button(sort_row, text=self.t("ascending"), command=lambda: self.sort_records(False), width=90, height=34).pack(side=tk.LEFT, padx=3)
        secondary_button(sort_row, text=self.t("descending"), command=lambda: self.sort_records(True), width=90, height=34).pack(side=tk.LEFT, padx=3)

        actions = ctk.CTkFrame(controls, fg_color="transparent", corner_radius=0)
        actions.pack(fill=tk.X, padx=7, pady=(0, 5))
        primary_button(actions, text=self.t("new_record"), command=self.new_record, width=108, height=34).pack(side=tk.LEFT, padx=3)
        secondary_button(actions, text=self.t("edit_selected"), command=self.open_selected_record, width=118, height=34).pack(side=tk.LEFT, padx=3)
        secondary_button(actions, text=self.t("validate_selected"), command=self.validate_selected_records, width=132, height=34).pack(side=tk.LEFT, padx=3)
        primary_button(actions, text=self.t("batch_ai_extract_short"), command=self.open_batch_ai_extract, width=148, height=34).pack(side=tk.LEFT, padx=(12, 3))
        secondary_button(actions, text=self.t("batch_edit_field_short"), command=self.open_batch_edit, width=126, height=34).pack(side=tk.LEFT, padx=3)
        secondary_button(actions, text=self.t("copy_record"), command=self.copy_record, width=112, height=34).pack(side=tk.RIGHT, padx=3)
        secondary_button(actions, text=self.t("delete_selected"), command=self.delete_record, width=116, height=34).pack(side=tk.RIGHT, padx=3)

        frame = card(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(2, 6))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.records_tree = ttk.Treeview(frame, show="headings", selectmode="extended", style="MetadataLens.Treeview")
        sy = ttk.Scrollbar(frame, orient="vertical", command=self.records_tree.yview)
        sx = ttk.Scrollbar(frame, orient="horizontal", command=self.records_tree.xview)
        self.records_tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.records_tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        sy.grid(row=0, column=1, sticky="ns", pady=(8, 0), padx=(0, 8))
        sx.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))
        self.records_tree.bind("<<TreeviewSelect>>", self._on_record_table_select)
        self.records_tree.bind("<Double-1>", self.open_selected_record)
        self.records_tree.bind("<Delete>", lambda _e: self.delete_record())

    def _build_io_tab(self) -> None:
        tab = self.tabs["import_export"]
        scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=COLORS["background"],
            corner_radius=0,
            scrollbar_button_color=COLORS["blue2"],
            scrollbar_button_hover_color=COLORS["blue"],
        )
        scroll.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 6))
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        groups = (
            (
                "io_import_title", "io_import_desc",
                (("import_excel", self.import_excel, True), ("import_xml", self.import_xml, False), ("import_schema", self.import_schema, False)),
            ),
            (
                "io_export_title", "io_export_desc",
                (("export_xml", self.export_records_xml, True), ("export_excel", self.export_excel, False), ("export_csv", self.export_csv, False), ("export_schema", self.export_schema, False)),
            ),
            (
                "io_template_title", "io_template_desc",
                (("save_user_template", self.save_user_template, True), ("template_manager", self.open_template_manager, False), ("validate_schema", self.validate_schema_action, False)),
            ),
            (
                "io_ai_title", "io_ai_desc",
                (("provider_settings", self.open_provider_settings, True), ("ai_extract", self.open_ai_extract, False), ("batch_ai_extract", self.open_batch_ai_extract, False), ("ai_schema", self.open_ai_schema, False)),
            ),
        )
        for i, (title_key, desc_key, actions) in enumerate(groups):
            box = card(scroll)
            box.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)
            body_label(box, text=self.t(title_key), semibold=True, font=ctk_font("subtitle", semibold=True), text_color=COLORS["navy"]).pack(fill=tk.X, padx=15, pady=(14, 3))
            body_label(box, text=self.t(desc_key), muted=True, wraplength=560).pack(fill=tk.X, padx=15, pady=(0, 10))
            action_frame = ctk.CTkFrame(box, fg_color="transparent", corner_radius=0)
            action_frame.pack(fill=tk.X, padx=12, pady=(0, 13))
            for key, command, primary in actions:
                factory = primary_button if primary else secondary_button
                factory(action_frame, text=self.t(key), command=command, height=38).pack(fill=tk.X, pady=4)

    # ------------------------------------------------------------------
    # Tab/navigation and details
    # ------------------------------------------------------------------
    def show_tab(self, key: str) -> None:
        if key != "overview" and not self.project:
            messagebox.showwarning(self.t("warning"), self.t("no_project"), parent=self.root)
            key = "overview"
        if key in self.tab_names:
            self.notebook.set(self.tab_names[key])
            self._on_tab_changed()

    def _on_tab_changed(self) -> None:
        try:
            selected = self.notebook.get()
        except Exception:
            return
        key = next((k for k, name in self.tab_names.items() if name == selected), "overview")
        if key == "overview":
            self._set_details(self.t("overview_details"))
        elif key == "schema_design":
            self._show_selected_field_details()
        elif key == "record_entry":
            self._show_current_record_details()
        elif key == "records_table":
            self._on_record_table_select()
        else:
            self._set_details(self.t("io_details"))

    def _set_details(self, text: str) -> None:
        self.details_text.configure(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", text)
        self.details_text.configure(state=tk.DISABLED)

    def _show_selected_field_details(self) -> None:
        if not self.project:
            self._set_details(self.t("no_project"))
            return
        selected = self.schema_tree.selection() if hasattr(self, "schema_tree") else ()
        if not selected:
            self._set_details(self.t("schema_details_hint"))
            return
        f = self.project.schema.get_field(selected[0])
        if not f:
            return
        lang = self.i18n.language
        desc = f.description_zh if lang.startswith("zh") else f.description_en
        lines = [
            f"{self.t('field_id')}: {f.field_id}",
            f"{self.t('xml_tag')}: {f.xml_tag}",
            f"{self.t('data_type')}: {f.data_type}",
            f"{self.t('level')}: {f.level}",
            f"{self.t('required')}: {'✓' if f.required else '—'}   {self.t('repeatable')}: {'✓' if f.repeatable else '—'}",
            f"{self.t('format_hint')}: {field_hint(f, lang)}",
        ]
        if desc:
            lines.append(f"{self.t('description')}: {desc}")
        self._set_details("\n".join(lines))

    def _show_current_record_details(self) -> None:
        if not self.current_record:
            self._set_details(self.t("record_details_hint"))
            return
        self._set_details(self._record_detail_text(self.current_record))

    def _record_detail_text(self, record: MetadataRecord) -> str:
        lines = [f"{self.t('record_id')}: {record.record_id}", f"{self.t('record_type')}: {record.record_type}"]
        if self.project:
            for f in self.project.schema.sorted_fields(visible_only=True):
                value = record.get_value(f.field_id)
                if value:
                    lines.append(f"{f.display_label(self.i18n.language)}: {value}")
        return "\n".join(lines)

    def edit_context_item(self) -> None:
        selected_name = self.notebook.get()
        if selected_name == self.tab_names.get("schema_design"):
            self.schema_on_select()
            return
        if selected_name == self.tab_names.get("records_table"):
            self.open_selected_record()
            return
        if self.current_record:
            self.show_tab("record_entry")

    def validate_context_item(self) -> None:
        selected_name = self.notebook.get()
        if selected_name == self.tab_names.get("schema_design"):
            self.validate_schema_action()
        elif selected_name == self.tab_names.get("records_table"):
            self.validate_selected_records()
        else:
            self.validate_current_record()

    # ------------------------------------------------------------------
    # Refresh / status
    # ------------------------------------------------------------------
    def refresh_all(self) -> None:
        self.templates.refresh()
        self.refresh_schema()
        self.refresh_record_form()
        self.refresh_records_table()
        self.refresh_overview()
        self._update_project_sidebar()
        self._update_statusbar()

    def refresh_overview(self) -> None:
        if not self.card_values:
            return
        if not self.project:
            for key in ("metric_fields", "metric_records", "metric_required", "metric_repeatable", "metric_missing"):
                self.card_values[key].configure(text="0")
            self.card_values["metric_provider"].configure(text=PROVIDER_DEFAULTS.get(self.settings.active_provider, {}).get("label", self.settings.active_provider))
            return
        schema = self.project.schema
        required = [f for f in schema.fields if f.required]
        repeatable = [f for f in schema.fields if f.repeatable]
        missing = 0
        for r in self.project.records:
            for f in required:
                if not any(v.strip() for v in r.get_values(f.field_id)):
                    missing += 1
        self.card_values["metric_fields"].configure(text=str(len(schema.fields)))
        self.card_values["metric_records"].configure(text=str(len(self.project.records)))
        self.card_values["metric_required"].configure(text=str(len(required)))
        self.card_values["metric_repeatable"].configure(text=str(len(repeatable)))
        self.card_values["metric_missing"].configure(text=str(missing))
        self.card_values["metric_provider"].configure(text=PROVIDER_DEFAULTS.get(self.settings.active_provider, {}).get("label", self.settings.active_provider))

    def _update_project_sidebar(self) -> None:
        if not self.project:
            self.project_name_var.set(self.t("no_project_loaded"))
            self.project_path_var.set(self.t("create_or_open_hint"))
            self.project_type_var.set("—")
            self.project_schema_var.set("—")
            self.project_records_var.set("0")
            self.project_fields_var.set("0")
            return
        p = self.project
        self.project_name_var.set(p.project_info.project_name + (" *" if p.dirty else ""))
        self.project_path_var.set(str(p.file_path) if p.file_path else self.t("not_saved_yet"))
        self.project_type_var.set(p.get_corpus_type_label(self.i18n.language))
        self.project_schema_var.set(p.schema.schema_name)
        self.project_records_var.set(str(len(p.records)))
        self.project_fields_var.set(str(len(p.schema.fields)))

    def _update_statusbar(self) -> None:
        provider = PROVIDER_DEFAULTS.get(self.settings.active_provider, {}).get("label", self.settings.active_provider)
        cfg = self.settings.provider(self.settings.active_provider)
        self.provider_status_var.set(f"{self.t('provider')}: {provider} · {cfg.model}")
        if not self.project:
            self.status_var.set(self.t("status_ready"))
        else:
            dirty = self.t("unsaved_marker") if self.project.dirty else self.t("saved_marker")
            self.status_var.set(f"{self.project.project_info.project_name} · {len(self.project.records)} {self.t('records')} · {len(self.project.schema.fields)} {self.t('fields_short')} · {dirty}")

    # ------------------------------------------------------------------
    # Project lifecycle
    # ------------------------------------------------------------------
    def _require_project(self) -> MetadataProject | None:
        if not self.project:
            messagebox.showwarning(self.t("warning"), self.t("no_project"), parent=self.root)
            return None
        return self.project

    def new_project(self) -> None:
        if not self._confirm_unsaved():
            return
        dlg = NewProjectDialog(self)
        self.root.wait_window(dlg.window)
        if not dlg.result:
            return
        name, item, blank = dlg.result
        if blank or item is None:
            schema = MetadataSchema(schema_name=self.t("empty_schema"))
            corpus_type = "custom"
        else:
            schema = self.templates.clone_schema(item)
            corpus_type = item.corpus_type
        self.project = self.repository.new_project(name, corpus_type, schema, self.i18n.language)
        self.current_record = None
        self.refresh_all()
        self.show_tab("overview")
        self._set_details(self.t("project_created_details"))

    def open_project(self) -> None:
        if not self._confirm_unsaved():
            return
        filename = filedialog.askopenfilename(parent=self.root, filetypes=[("MetadataLens Project XML", "*.xml"), ("All files", "*.*")])
        if not filename:
            return
        try:
            self.project = self.repository.load_project(Path(filename))
            self.current_record = self.project.records[0] if self.project.records else None
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)
            return
        # Interface language is an application/user preference, not a property
        # that should silently change when a project file is opened. This keeps
        # menus, User Guide and About in the same visible language.
        self.project.project_info.interface_language = self.i18n.language
        self.refresh_all()
        self.show_tab("overview")

    def save_project(self) -> None:
        if not self._require_project():
            return
        if self.current_record:
            self.save_current_record(silent=True)
        if self.project.file_path:
            self._save_to(self.project.file_path)
        else:
            self.save_project_as()

    def save_project_as(self) -> None:
        if not self._require_project():
            return
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".xml", filetypes=[("MetadataLens Project XML", "*.xml")])
        if filename:
            self._save_to(Path(filename))

    def _save_to(self, path: Path) -> None:
        try:
            self.repository.save_project(self.project, path)
            self.refresh_all()
            self._set_details(self.t("project_saved_details", path=path))
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def close_project(self) -> None:
        if not self._confirm_unsaved():
            return
        self.project = None
        self.current_record = None
        self.refresh_all()
        self.show_tab("overview")

    def _confirm_unsaved(self) -> bool:
        if not self.project or not self.project.dirty:
            return True
        ans = messagebox.askyesnocancel(self.t("confirm"), self.t("unsaved"), parent=self.root)
        if ans is None:
            return False
        if ans:
            self.save_project()
            return bool(self.project and not self.project.dirty)
        return True

    def on_close(self) -> None:
        if not self._confirm_unsaved():
            return
        try:
            self.settings.window_geometry = self.root.geometry()
            self.settings.sidebar_width = self.main_pane.sashpos(0)
            height = max(1, self.vertical_pane.winfo_height())
            self.settings.list_pane_ratio = min(0.90, max(0.45, self.vertical_pane.sashpos(0) / height))
            self.settings_store.save(self.settings)
        except Exception:
            pass
        self.root.destroy()

    # ------------------------------------------------------------------
    # Schema design
    # ------------------------------------------------------------------
    def refresh_schema(self) -> None:
        if not hasattr(self, "schema_tree"):
            return
        previous = self.schema_tree.selection()
        self.schema_tree.delete(*self.schema_tree.get_children())
        if not self.project:
            if hasattr(self, "schema_name_var"):
                self.schema_name_var.set("")
            if hasattr(self, "schema_version_var"):
                self.schema_version_var.set("")
            return
        if hasattr(self, "schema_name_var"):
            self.schema_name_var.set(self.project.schema.schema_name)
        if hasattr(self, "schema_version_var"):
            self.schema_version_var.set(self.project.schema.schema_version)
        for f in self.project.schema.sorted_fields():
            self.schema_tree.insert(
                "", "end", iid=f.field_id,
                values=(f.field_id, f.label_zh, f.label_en, f.xml_tag, f.data_type, "✓" if f.required else "", "✓" if f.repeatable else "", f.level),
            )
        if previous:
            valid = [x for x in previous if self.project.schema.get_field(x)]
            if valid:
                self.schema_tree.selection_set(valid)

    def apply_schema_identity(self) -> None:
        """Rename the active project schema and optionally edit its version."""
        if not self._require_project():
            return
        name = self.schema_name_var.get().strip() if hasattr(self, "schema_name_var") else ""
        if not name:
            messagebox.showerror(self.t("error"), self.t("schema_name_required"), parent=self.root)
            return
        version = self.schema_version_var.get().strip() if hasattr(self, "schema_version_var") else ""
        self.project.schema.schema_name = name
        self.project.schema.schema_version = version or "1.0"
        self.project.touch()
        self._update_project_sidebar()
        self._update_statusbar()
        self._set_details(self.t("schema_info_saved", name=name, version=self.project.schema.schema_version))

    def schema_on_select(self, _event=None) -> None:
        if not self.project:
            return
        selected = self.schema_tree.selection()
        if not selected:
            return
        f = self.project.schema.get_field(selected[0])
        if not f:
            return
        for key, var in self.schema_vars.items():
            if key == "controlled_values":
                var.set("; ".join(f.controlled_values))
            else:
                var.set(getattr(f, key, False if isinstance(var, tk.BooleanVar) else 0 if isinstance(var, tk.IntVar) else ""))
        self.schema_desc_zh.delete("1.0", "end")
        self.schema_desc_zh.insert("1.0", f.description_zh)
        self.schema_desc_en.delete("1.0", "end")
        self.schema_desc_en.insert("1.0", f.description_en)
        self.update_schema_hint(f)
        self._show_selected_field_details()

    def update_schema_hint(self, field: MetadataField | None = None) -> None:
        if not hasattr(self, "schema_hint"):
            return
        if field is None:
            data_type = str(self.schema_vars.get("data_type", tk.StringVar(value="string")).get() or "string")
            field = MetadataField(
                field_id="preview",
                data_type=data_type,
                repeatable=bool(self.schema_vars.get("repeatable", tk.BooleanVar()).get()),
                required=bool(self.schema_vars.get("required", tk.BooleanVar()).get()),
                example=str(self.schema_vars.get("example", tk.StringVar()).get()),
                validation_rule=str(self.schema_vars.get("validation_rule", tk.StringVar()).get()),
            )
        self.schema_hint.configure(text=self.t("format_hint") + ": " + field_hint(field, self.i18n.language))

    def schema_add(self) -> None:
        if not self._require_project():
            return
        base = "new_field"
        i = 1
        fid = base
        while self.project.schema.get_field(fid):
            i += 1
            fid = f"{base}_{i}"
        field = MetadataField(field_id=fid, label_zh="新字段", label_en="New Field", order=len(self.project.schema.fields) + 1)
        self.project.schema.add_field(field)
        self.project.touch()
        self.refresh_schema()
        self.schema_tree.selection_set(fid)
        self.schema_tree.see(fid)
        self.schema_on_select()
        self.refresh_overview()
        self._update_project_sidebar()

    def schema_select_all(self) -> None:
        children = self.schema_tree.get_children() if hasattr(self, "schema_tree") else ()
        if children:
            self.schema_tree.selection_set(children)

    def schema_delete(self) -> None:
        if not self._require_project():
            return
        ids = list(self.schema_tree.selection())
        if not ids:
            return
        if not messagebox.askyesno(self.t("confirm"), self.t("confirm_delete_fields", count=len(ids)), parent=self.root):
            return
        for fid in ids:
            self.project.schema.remove_field(fid)
        self.project.touch()
        self.refresh_all()
        self._set_details(self.t("fields_deleted", count=len(ids)))

    def schema_delete_all(self) -> None:
        if not self._require_project():
            return
        count = len(self.project.schema.fields)
        if not count:
            return
        if not messagebox.askyesno(self.t("confirm"), self.t("confirm_delete_all_fields", count=count), parent=self.root):
            return
        self.project.schema.fields.clear()
        self.project.touch()
        self.refresh_all()

    def schema_move(self, direction: int) -> None:
        if not self._require_project():
            return
        selected = self.schema_tree.selection()
        if not selected:
            return
        fid = selected[0]
        self.project.schema.move_field(fid, direction)
        self.project.touch()
        self.refresh_schema()
        if self.project.schema.get_field(fid):
            self.schema_tree.selection_set(fid)
            self.schema_tree.see(fid)

    def schema_apply(self) -> None:
        if not self._require_project():
            return
        fid = str(self.schema_vars["field_id"].get()).strip()
        if not fid:
            messagebox.showerror(self.t("error"), self.t("field_id_required"), parent=self.root)
            return
        old = self.schema_tree.selection()[0] if self.schema_tree.selection() else None
        values = [x.strip() for x in str(self.schema_vars["controlled_values"].get()).split(";") if x.strip()]
        old_field = self.project.schema.get_field(old) if old else None
        try:
            order = int(self.schema_vars["order"].get() or (old_field.order if old_field else len(self.project.schema.fields) + 1))
        except Exception:
            order = old_field.order if old_field else len(self.project.schema.fields) + 1
        field = MetadataField(
            field_id=fid,
            label_zh=str(self.schema_vars["label_zh"].get()).strip(),
            label_en=str(self.schema_vars["label_en"].get()).strip(),
            xml_tag=str(self.schema_vars["xml_tag"].get()).strip() or fid,
            data_type=str(self.schema_vars["data_type"].get()) or "string",
            required=bool(self.schema_vars["required"].get()),
            repeatable=bool(self.schema_vars["repeatable"].get()),
            default_value=str(self.schema_vars["default_value"].get()),
            controlled_values=values,
            description_zh=self.schema_desc_zh.get("1.0", "end").strip(),
            description_en=self.schema_desc_en.get("1.0", "end").strip(),
            example=str(self.schema_vars["example"].get()),
            level=str(self.schema_vars["level"].get()) or "text",
            parent=str(self.schema_vars["parent"].get()).strip(),
            order=order,
            visible=bool(self.schema_vars["visible"].get()),
            editable=bool(self.schema_vars["editable"].get()),
            sensitive=bool(self.schema_vars["sensitive"].get()),
            validation_rule=str(self.schema_vars["validation_rule"].get()),
        )
        if old and old != fid:
            self.project.schema.remove_field(old)
            for r in self.project.records:
                if old in r.fields and fid not in r.fields:
                    r.fields[fid] = r.fields.pop(old)
        try:
            self.project.schema.add_field(field, replace=True)
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)
            return
        self.project.schema.reindex()
        self.project.touch()
        self.refresh_all()
        self.schema_tree.selection_set(fid)
        self.schema_tree.see(fid)
        self.schema_on_select()

    # ------------------------------------------------------------------
    # Metadata entry / records
    # ------------------------------------------------------------------
    def _set_record_save_state(self, saved: bool) -> None:
        self._record_form_dirty = not saved
        if hasattr(self, "save_record_button"):
            self.save_record_button.configure(text=self.t("record_saved_button") if saved else self.t("save_record"))

    def _record_form_changed(self, *_args) -> None:
        if self._record_form_loading or not self.project:
            return
        self._set_record_save_state(False)

    def _bind_record_text_change(self, widget: ctk.CTkTextbox) -> None:
        for sequence in ("<KeyRelease>", "<<Paste>>", "<<Cut>>"):
            try:
                widget.bind(sequence, self._record_form_changed, add="+")
            except Exception:
                pass

    def refresh_record_form(self) -> None:
        if not hasattr(self, "record_scroll"):
            return
        self._record_form_loading = True
        for widget in self.record_scroll.winfo_children():
            widget.destroy()
        self.record_inputs = {}
        if not self.project:
            body_label(self.record_scroll, text=self.t("record_no_project_hint"), muted=True, wraplength=850).grid(row=0, column=0, sticky="w", padx=14, pady=16)
            self.record_position_var.set("")
            self._record_form_loading = False
            self._set_record_save_state(False)
            return

        record = self.current_record
        if record is None and self.project.records:
            record = self.project.records[0]
            self.current_record = record
        self.record_scroll.grid_columnconfigure(1, weight=1)

        body_label(self.record_scroll, text=self.t("record_id"), semibold=True).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        self.record_id_var = tk.StringVar(value=record.record_id if record else "")
        self.record_id_var.trace_add("write", self._record_form_changed)
        ctk.CTkEntry(self.record_scroll, textvariable=self.record_id_var, height=40, fg_color=COLORS["surface"], border_color=COLORS["border"], font=ctk_font("body")).grid(row=0, column=1, sticky="ew", padx=14, pady=(14, 6))

        body_label(self.record_scroll, text=self.t("record_type"), semibold=True).grid(row=1, column=0, sticky="w", padx=14, pady=6)
        self.record_type_var = tk.StringVar(value=record.record_type if record else "text")
        self.record_type_var.trace_add("write", self._record_form_changed)
        ctk.CTkEntry(self.record_scroll, textvariable=self.record_type_var, height=40, fg_color=COLORS["surface"], border_color=COLORS["border"], font=ctk_font("body")).grid(row=1, column=1, sticky="ew", padx=14, pady=6)

        row = 2
        for field in self.project.schema.sorted_fields(visible_only=True):
            label = field.display_label(self.i18n.language) + (" *" if field.required else "")
            body_label(self.record_scroll, text=label, semibold=field.required).grid(row=row, column=0, sticky="nw", padx=14, pady=(9, 2))
            value = record.get_value(field.field_id) if record else field.default_value
            if field.data_type == "long_text":
                widget = ctk.CTkTextbox(self.record_scroll, height=96, fg_color=COLORS["surface"], border_width=1, border_color=COLORS["border"], font=ctk_font("body"))
                widget.insert("1.0", value)
                if not field.editable:
                    widget.configure(state=tk.DISABLED)
                self.record_inputs[field.field_id] = widget
                self._bind_record_text_change(widget)
            elif field.data_type == "enum":
                var = tk.StringVar(value=value)
                var.trace_add("write", self._record_form_changed)
                widget = ctk.CTkComboBox(
                    self.record_scroll, variable=var, values=field.controlled_values or [""], state="readonly" if field.controlled_values else "normal",
                    height=40, fg_color=COLORS["surface"], border_color=COLORS["border"], button_color=COLORS["blue2"], button_hover_color=COLORS["blue"],
                    font=ctk_font("body"), dropdown_font=ctk_font("body"),
                )
                if not field.editable:
                    widget.configure(state="disabled")
                self.record_inputs[field.field_id] = var
            elif field.data_type == "boolean":
                var = tk.BooleanVar(value=str(value).lower() in {"true", "1", "yes", "是"})
                var.trace_add("write", self._record_form_changed)
                widget = ctk.CTkCheckBox(self.record_scroll, text=self.t("yes_no"), variable=var, fg_color=COLORS["blue"], hover_color=COLORS["blue2"], text_color=COLORS["text"], font=ctk_font("body"))
                if not field.editable:
                    widget.configure(state="disabled")
                self.record_inputs[field.field_id] = var
            else:
                var = tk.StringVar(value=value)
                var.trace_add("write", self._record_form_changed)
                widget = ctk.CTkEntry(self.record_scroll, textvariable=var, height=40, fg_color=COLORS["surface"], border_color=COLORS["border"], font=ctk_font("body"))
                if not field.editable:
                    widget.configure(state="disabled")
                self.record_inputs[field.field_id] = var
            widget.grid(row=row, column=1, sticky="ew", padx=14, pady=(9, 2))
            row += 1
            hint = field_hint(field, self.i18n.language)
            desc = field.description_zh if self.i18n.language.startswith("zh") else field.description_en
            if desc:
                hint = (desc + "  " + hint).strip()
            if hint:
                body_label(self.record_scroll, text=hint, muted=True, wraplength=900).grid(row=row, column=1, sticky="w", padx=14, pady=(0, 6))
                row += 1
        body_label(self.record_scroll, text=self.t("required_note"), muted=True).grid(row=row, column=0, columnspan=2, sticky="w", padx=14, pady=(8, 16))
        self._update_record_position()
        self._record_form_loading = False
        self._set_record_save_state(record is not None)

    def _update_record_position(self) -> None:
        if not self.project or not self.current_record or self.current_record not in self.project.records:
            self.record_position_var.set(self.t("no_record_selected"))
            return
        index = self.project.records.index(self.current_record) + 1
        self.record_position_var.set(self.t("record_position", current=index, total=len(self.project.records)))

    def new_record(self) -> None:
        if not self._require_project():
            return
        record = MetadataRecord()
        for f in self.project.schema.fields:
            if f.default_value:
                record.set_value(f.field_id, f.default_value)
        self.project.add_record(record)
        self.current_record = record
        self.refresh_all()
        self.show_tab("record_entry")
        self._show_current_record_details()

    def save_current_record(self, silent: bool = False) -> MetadataRecord | None:
        if not self._require_project():
            return None
        if not hasattr(self, "record_id_var"):
            return self.current_record
        if not self.current_record:
            self.current_record = self.project.add_record(MetadataRecord())
        record = self.current_record
        new_id = self.record_id_var.get().strip() or record.record_id
        if new_id != record.record_id and self.project.get_record(new_id):
            new_id = self.project.ensure_unique_record_id(new_id)
        old_id = record.record_id
        record.record_id = new_id
        record.record_type = self.record_type_var.get().strip() or "text"
        for field in self.project.schema.fields:
            source = self.record_inputs.get(field.field_id)
            if source is None:
                continue
            if isinstance(source, ctk.CTkTextbox):
                value = source.get("1.0", "end").strip()
            elif isinstance(source, tk.BooleanVar):
                value = "true" if source.get() else "false"
            else:
                value = str(source.get())
            record.set_value(field.field_id, [s.strip() for s in value.split(";") if s.strip()] if field.repeatable else value)
        self.project.touch()
        # If the record ID changed, relation endpoints should follow it.
        if old_id != new_id:
            for rel in self.project.relations:
                if rel.source_record == old_id:
                    rel.source_record = new_id
                if rel.target_record == old_id:
                    rel.target_record = new_id
        self.refresh_records_table()
        self.refresh_overview()
        self._update_project_sidebar()
        self._update_statusbar()
        self._show_current_record_details()
        self._set_record_save_state(True)
        if not silent:
            self.status_var.set(self.t("record_saved_status", record_id=record.record_id))
        return record

    def validate_current_record(self) -> None:
        record = self.save_current_record(silent=True)
        if not record or not self.project:
            return
        messages = validate_record(record, self.project.schema)
        text = self.t("record_validation_ok") if not messages else "\n".join(f"[{m.level}] {m.item}: {m.message}" for m in messages)
        self._set_details(text)
        messagebox.showinfo(self.t("details"), text, parent=self.root)

    def navigate_record(self, direction: int) -> None:
        if not self._require_project() or not self.project.records:
            return
        if self.current_record:
            self.save_current_record(silent=True)
        if self.current_record in self.project.records:
            index = self.project.records.index(self.current_record)
        else:
            index = 0
        index = min(max(0, index + direction), len(self.project.records) - 1)
        self.current_record = self.project.records[index]
        self.refresh_record_form()
        self._show_current_record_details()

    def refresh_records_table(self) -> None:
        if not hasattr(self, "records_tree"):
            return
        selected = set(self.records_tree.selection())
        self.records_tree.delete(*self.records_tree.get_children())
        if not self.project:
            self.records_tree.configure(columns=())
            if hasattr(self, "record_sort_combo"):
                self.record_sort_combo.configure(values=["record_id", "record_type"])
            return
        fields = ["record_id", "record_type"] + self.project.schema.field_ids()
        self.records_tree.configure(columns=fields)
        search_text = self.record_search_var.get().strip().lower() if hasattr(self, "record_search_var") else ""
        rows: list[tuple[MetadataRecord, dict[str, str]]] = []
        for record in self.project.records:
            row = record.to_flat_dict(self.project.schema)
            if search_text and search_text not in " ".join(str(v) for v in row.values()).lower():
                continue
            rows.append((record, row))
        sort_field = self.record_sort_var.get() if hasattr(self, "record_sort_var") else "record_id"
        reverse = bool(getattr(self, "_record_sort_reverse", False))
        rows.sort(key=lambda pair: str(pair[1].get(sort_field, "")).casefold(), reverse=reverse)

        for col in fields:
            field = self.project.schema.get_field(col)
            heading = self.t(col) if col in {"record_id", "record_type"} else (field.display_label(self.i18n.language) if field else col)
            self.records_tree.heading(col, text=heading, command=lambda c=col: self._sort_tree_column(c))
            width = 150
            if col in {"record_id", "record_type"}:
                width = 160
            elif field and field.data_type == "long_text":
                width = 280
            self.records_tree.column(col, width=width, stretch=False, anchor="w")
        for record, row in rows:
            self.records_tree.insert("", "end", iid=record.record_id, values=[row.get(c, "") for c in fields])
        restored = [iid for iid in selected if self.records_tree.exists(iid)]
        if restored:
            self.records_tree.selection_set(restored)
        if hasattr(self, "record_sort_combo"):
            self.record_sort_combo.configure(values=fields)
            if self.record_sort_var.get() not in fields:
                self.record_sort_var.set("record_id")

    def sort_records(self, reverse: bool) -> None:
        self._record_sort_reverse = reverse
        self.refresh_records_table()

    def _sort_tree_column(self, column: str) -> None:
        if self.record_sort_var.get() == column:
            self._record_sort_reverse = not bool(getattr(self, "_record_sort_reverse", False))
        else:
            self.record_sort_var.set(column)
            self._record_sort_reverse = False
        self.refresh_records_table()

    def _selected_records(self) -> list[MetadataRecord]:
        if not self.project or not hasattr(self, "records_tree"):
            return []
        return [r for iid in self.records_tree.selection() if (r := self.project.get_record(iid))]

    def _on_record_table_select(self, _event=None) -> None:
        records = self._selected_records()
        if not records:
            self._set_details(self.t("record_table_details_hint"))
            return
        if len(records) == 1:
            self._set_details(self._record_detail_text(records[0]))
        else:
            self._set_details(self.t("multiple_records_selected", count=len(records)))

    def open_selected_record(self, _event=None) -> None:
        records = self._selected_records()
        if not records:
            return
        self.current_record = records[0]
        self.refresh_record_form()
        self.show_tab("record_entry")
        self._show_current_record_details()

    def delete_record(self) -> None:
        if not self._require_project():
            return
        records = self._selected_records()
        if not records and self.current_record:
            records = [self.current_record]
        if not records:
            return
        if not messagebox.askyesno(self.t("confirm"), self.t("confirm_delete_records", count=len(records)), parent=self.root):
            return
        ids = {r.record_id for r in records}
        for record in list(records):
            self.project.remove_record(record.record_id)
        if self.current_record and self.current_record.record_id in ids:
            self.current_record = self.project.records[0] if self.project.records else None
        self.refresh_all()

    def copy_record(self) -> None:
        if not self._require_project():
            return
        records = self._selected_records()
        source = records[0] if records else self.current_record
        if not source:
            return
        copied = deepcopy(source)
        copied.record_id = self.project.ensure_unique_record_id(source.record_id + "_copy")
        self.project.add_record(copied)
        self.current_record = copied
        self.refresh_all()
        self.show_tab("record_entry")

    def validate_selected_records(self) -> None:
        if not self._require_project():
            return
        records = self._selected_records()
        if not records:
            return
        messages = []
        for record in records:
            messages.extend(validate_record(record, self.project.schema))
        text = self.t("selected_records_validation_ok", count=len(records)) if not messages else "\n".join(f"[{m.level}] {m.item}: {m.message}" for m in messages)
        self._set_details(text)
        messagebox.showinfo(self.t("details"), text, parent=self.root)

    # ------------------------------------------------------------------
    # Import / export / templates
    # ------------------------------------------------------------------
    def import_excel(self) -> None:
        if not self._require_project():
            return
        filename = filedialog.askopenfilename(parent=self.root, filetypes=[("Excel", "*.xlsx *.xlsm")])
        if not filename:
            return
        try:
            preview = self.excel.preview(Path(filename), self.project, max_rows=100)
            dlg = MappingDialog(self, preview.headers, preview.suggested_mapping, self.t("excel_mapping_title"))
            self.root.wait_window(dlg.window)
            if dlg.result is None:
                return
            mapping, add_unknown = dlg.result
            count, errors = self.excel.import_file(Path(filename), self.project, mapping, add_unknown)
            self.current_record = self.project.records[-1] if self.project.records else None
            self.refresh_all()
            messagebox.showinfo(self.t("success"), self.t("import_result", count=count, errors=len(errors)), parent=self.root)
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def import_xml(self) -> None:
        if not self._require_project():
            return
        filename = filedialog.askopenfilename(parent=self.root, filetypes=[("XML", "*.xml"), ("All files", "*.*")])
        if not filename:
            return
        try:
            preview = self.xml_importer.preview(Path(filename), self.project)
            dlg = MappingDialog(self, preview.tags, preview.suggested_mapping, self.t("xml_mapping_title"))
            self.root.wait_window(dlg.window)
            if dlg.result is None:
                return
            mapping, add_unknown = dlg.result
            count, logs = self.xml_importer.import_file(Path(filename), self.project, mapping, add_unknown)
            self.current_record = self.project.records[-1] if self.project.records else None
            self.refresh_all()
            messagebox.showinfo(self.t("success"), self.t("xml_import_result", count=count, logs="\n".join(logs)), parent=self.root)
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def import_schema(self) -> None:
        if not self._require_project():
            return
        filename = filedialog.askopenfilename(parent=self.root, filetypes=[("Schema XML", "*.xml"), ("All files", "*.*")])
        if not filename:
            return
        try:
            schema = load_schema_xml(Path(filename))
            if self.project.schema.fields and not messagebox.askyesno(self.t("confirm"), self.t("replace_schema_confirm"), parent=self.root):
                return
            self.project.schema = schema
            self.project.touch()
            self.refresh_all()
            self.show_tab("schema_design")
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def export_records_xml(self) -> None:
        if not self._require_project():
            return
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".xml", filetypes=[("XML", "*.xml")])
        if filename:
            try:
                self.repository.export_records_xml(self.project, Path(filename))
                messagebox.showinfo(self.t("success"), self.t("export_done", path=filename), parent=self.root)
            except Exception as exc:
                messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def export_excel(self) -> None:
        if not self._require_project():
            return
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if filename:
            try:
                self.excel.export_records_excel(self.project, Path(filename))
                messagebox.showinfo(self.t("success"), self.t("export_done", path=filename), parent=self.root)
            except Exception as exc:
                messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def export_csv(self) -> None:
        if not self._require_project():
            return
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if filename:
            try:
                self.excel.export_records_csv(self.project, Path(filename))
                messagebox.showinfo(self.t("success"), self.t("export_done", path=filename), parent=self.root)
            except Exception as exc:
                messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def export_schema(self) -> None:
        if not self._require_project():
            return
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".xml", filetypes=[("Schema XML", "*.xml")])
        if filename:
            try:
                save_schema_xml(self.project.schema, Path(filename))
                messagebox.showinfo(self.t("success"), self.t("export_done", path=filename), parent=self.root)
            except Exception as exc:
                messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def validate_schema_action(self) -> None:
        if not self._require_project():
            return
        messages = validate_schema(self.project.schema)
        text = self.t("schema_validation_ok") if not messages else "\n".join(f"[{m.level}] {m.item}: {m.message}" for m in messages)
        self._set_details(text)
        messagebox.showinfo(self.t("details"), text, parent=self.root)

    def save_user_template(self) -> None:
        if not self._require_project():
            return
        try:
            path = self.templates.save_user_template(deepcopy(self.project.schema), self.project.schema.schema_name)
            messagebox.showinfo(self.t("success"), self.t("template_saved", path=path), parent=self.root)
        except Exception as exc:
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)

    def open_template_manager(self) -> None:
        TemplateManagerDialog(self)

    # ------------------------------------------------------------------
    # AI / settings / language / help
    # ------------------------------------------------------------------
    def open_provider_settings(self) -> None:
        ProviderSettingsDialog(self)

    def open_ai_extract(self) -> None:
        if not self._require_project():
            return
        record = self.save_current_record(silent=True) if self.current_record else None
        if record is None:
            record = self.project.add_record(MetadataRecord())
            self.current_record = record
            self.refresh_record_form()
        AIExtractDialog(self, record)

    def open_batch_ai_extract(self) -> None:
        if not self._require_project():
            return
        BatchAIExtractDialog(self)

    def open_batch_edit(self) -> None:
        if not self._require_project():
            return
        if not self.project.records:
            messagebox.showwarning(self.t("warning"), self.t("batch_edit_no_records"), parent=self.root)
            return
        BatchEditDialog(self)

    def open_ai_schema(self) -> None:
        if self._require_project():
            AISchemaDialog(self)

    def change_language(self, lang: str) -> None:
        if lang not in {"zh_CN", "en_US"}:
            return
        self.i18n.set_language(lang)
        self.settings.language = lang
        if self.project:
            self.project.project_info.interface_language = lang
            self.project.touch()
        self.settings_store.save(self.settings)
        current_key = next((k for k, name in self.tab_names.items() if self.notebook.get() == name), "overview") if self.tab_names else "overview"
        self._build_ui()
        self.refresh_all()
        self.show_tab(current_key)

    def show_user_guide(self) -> None:
        GuideDialog(self)

    def show_about(self) -> None:
        AboutDialog(self)


class NewProjectDialog:
    def __init__(self, app: MetadataLensApp):
        self.app = app
        self.result: tuple[str, TemplateItem | None, bool] | None = None
        self.window = app._new_dialog(app.t("new_project"), 940, 740, modal=True)
        self._build()

    def _build(self) -> None:
        w = self.window
        w.grid_columnconfigure(0, weight=1)
        w.grid_rowconfigure(2, weight=1)
        top = ctk.CTkFrame(w, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        top.grid_columnconfigure(1, weight=1)
        body_label(top, text=self.app.t("project_name"), semibold=True).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.name = tk.StringVar(value=self.app.t("untitled_project"))
        ctk.CTkEntry(top, textvariable=self.name, height=40, font=ctk_font("body"), fg_color=COLORS["surface"], border_color=COLORS["border"]).grid(row=0, column=1, sticky="ew")

        self.blank_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            top, text=self.app.t("use_blank_schema"), variable=self.blank_var,
            command=self._blank_changed, fg_color=COLORS["blue"], hover_color=COLORS["blue2"], font=ctk_font("body"),
        ).grid(row=1, column=1, sticky="w", pady=(10, 0))

        tabs = ctk.CTkTabview(
            w, fg_color=COLORS["panel"], segmented_button_fg_color=COLORS["toolbar"],
            segmented_button_selected_color=COLORS["blue"], segmented_button_selected_hover_color=COLORS["blue2"],
            segmented_button_unselected_color=COLORS["toolbar"], segmented_button_unselected_hover_color=COLORS["border"],
        )
        style_tabview(tabs)
        tabs.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=18, pady=(0, 10))
        st = tabs.add(self.app.t("system_templates"))
        ut = tabs.add(self.app.t("user_templates"))
        self.listboxes: list[tk.Listbox] = []
        self.item_map: dict[tuple[int, int], TemplateItem] = {}
        for frame, items, system in ((st, self.app.templates.system, True), (ut, self.app.templates.user, False)):
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            lb = tk.Listbox(frame, exportselection=False, font=("Segoe UI", 12), selectmode="browse", relief="flat", highlightthickness=1, highlightbackground=COLORS["border"])
            lb.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            lb.bind("<<ListboxSelect>>", self._template_selected)
            self.listboxes.append(lb)
            for item in items:
                lb.insert("end", f"{item.name}    ·    {len(item.schema.fields)} {self.app.t('fields_short')}")
                self.item_map[(id(lb), lb.size() - 1)] = item
            note = self.app.t("system_readonly") if system else self.app.t("user_template_note")
            body_label(frame, text=note, muted=True, wraplength=700).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        self.detail_var = tk.StringVar(value=self.app.t("select_template_details"))
        if self.listboxes and self.listboxes[0].size() > 0:
            self.listboxes[0].selection_set(0)
            self.listboxes[0].activate(0)
            item = self.item_map.get((id(self.listboxes[0]), 0))
            if item:
                self.detail_var.set(
                    f"{self.app.t('template')}: {item.name}  ·  {self.app.t('corpus_type')}: {item.corpus_type}  ·  "
                    f"{self.app.t('field_count')}: {len(item.schema.fields)}  ·  {self.app.t('schema_version')}: {item.schema.schema_version}"
                )
        detail = card(w)
        detail.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 8))
        body_label(detail, textvariable=self.detail_var, wraplength=750).pack(fill=tk.X, padx=12, pady=10)

        bottom = ctk.CTkFrame(w, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="e", padx=18, pady=12)
        secondary_button(bottom, text=self.app.t("cancel"), command=w.destroy).pack(side="right", padx=5)
        primary_button(bottom, text=self.app.t("create"), command=self._ok).pack(side="right", padx=5)

    def _blank_changed(self) -> None:
        if self.blank_var.get():
            for lb in self.listboxes:
                lb.selection_clear(0, "end")
            self.detail_var.set(self.app.t("blank_schema_details"))

    def _template_selected(self, event=None) -> None:
        self.blank_var.set(False)
        source = getattr(event, "widget", None)
        if source is not None:
            for lb in self.listboxes:
                if lb is not source:
                    lb.selection_clear(0, "end")
        item = self._selected_item()
        if not item:
            return
        self.detail_var.set(
            f"{self.app.t('template')}: {item.name}  ·  {self.app.t('corpus_type')}: {item.corpus_type}  ·  "
            f"{self.app.t('field_count')}: {len(item.schema.fields)}  ·  {self.app.t('schema_version')}: {item.schema.schema_version}"
        )

    def _selected_item(self) -> TemplateItem | None:
        for lb in self.listboxes:
            sel = lb.curselection()
            if sel:
                return self.item_map.get((id(lb), sel[0]))
        return None

    def _ok(self) -> None:
        self.result = (self.name.get().strip() or self.app.t("untitled_project"), self._selected_item(), self.blank_var.get())
        self.window.destroy()



class MappingDialog:
    def __init__(self, app: MetadataLensApp, source_items: list[str], suggested: dict[str, str], title: str):
        self.app = app
        self.result: tuple[dict[str, str], bool] | None = None
        self.vars: dict[str, tk.StringVar] = {}
        self.window = app._new_dialog(title, 920, 740, modal=True)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        body_label(self.window, text=app.t("mapping_help"), muted=True, wraplength=730).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        scroll = ctk.CTkScrollableFrame(self.window, fg_color=COLORS["panel"], border_width=1, border_color=COLORS["border"])
        scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        scroll.grid_columnconfigure(1, weight=1)
        choices = [""] + app.project.schema.field_ids()
        body_label(scroll, text=app.t("source_column_or_tag"), semibold=True).grid(row=0, column=0, sticky="w", padx=7, pady=6)
        body_label(scroll, text=app.t("target_schema_field"), semibold=True).grid(row=0, column=1, sticky="w", padx=7, pady=6)
        for i, item in enumerate(source_items, start=1):
            body_label(scroll, text=item).grid(row=i, column=0, sticky="w", padx=7, pady=4)
            var = tk.StringVar(value=suggested.get(item, ""))
            ctk.CTkComboBox(
                scroll, variable=var, values=choices, state="readonly", height=36,
                fg_color=COLORS["surface"], border_color=COLORS["border"], button_color=COLORS["blue2"],
                font=ctk_font("body"), dropdown_font=ctk_font("body"),
            ).grid(row=i, column=1, sticky="ew", padx=7, pady=4)
            self.vars[item] = var
        bottom = ctk.CTkFrame(self.window, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=16, pady=12)
        self.add_unknown = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(bottom, text=app.t("add_unknown_to_schema"), variable=self.add_unknown, fg_color=COLORS["blue"], hover_color=COLORS["blue2"], font=ctk_font("body")).pack(side="left")
        secondary_button(bottom, text=app.t("cancel"), command=self.window.destroy).pack(side="right", padx=4)
        primary_button(bottom, text=app.t("ok"), command=self._ok).pack(side="right", padx=4)

    def _ok(self) -> None:
        self.result = ({k: v.get() for k, v in self.vars.items() if v.get()}, self.add_unknown.get())
        self.window.destroy()


class ProviderSettingsDialog:
    def __init__(self, app: MetadataLensApp):
        self.app = app
        self.window = app._new_dialog(app.t("provider_settings"), 1020, 840, modal=False)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(2, weight=1)
        heading_label(self.window, text=app.t("provider_settings")).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 2))
        body_label(self.window, text=app.t("llm_note"), muted=True, wraplength=810).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        tabs = ctk.CTkTabview(
            self.window, fg_color=COLORS["panel"], segmented_button_fg_color=COLORS["toolbar"], segmented_button_selected_color=COLORS["blue"],
            segmented_button_selected_hover_color=COLORS["blue2"], segmented_button_unselected_color=COLORS["toolbar"], segmented_button_unselected_hover_color=COLORS["border"],
        )
        style_tabview(tabs)
        tabs.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 10))
        self.vars: dict[str, dict[str, tk.StringVar]] = {}
        for key, meta in PROVIDER_DEFAULTS.items():
            tab = tabs.add(meta["label"])
            tab.grid_columnconfigure(1, weight=1)
            cfg = app.settings.provider(key)
            vars_ = {
                "api_key": tk.StringVar(value=cfg.api_key),
                "base_url": tk.StringVar(value=cfg.base_url),
                "model": tk.StringVar(value=cfg.model),
            }
            self.vars[key] = vars_
            for r, field_key in enumerate(("api_key", "base_url", "model")):
                body_label(tab, text=app.t(field_key), semibold=field_key == "model").grid(row=r, column=0, sticky="w", padx=14, pady=10)
                ctk.CTkEntry(
                    tab, textvariable=vars_[field_key], show="•" if field_key == "api_key" else "", height=40,
                    fg_color=COLORS["surface"], border_color=COLORS["border"], font=ctk_font("body"),
                ).grid(row=r, column=1, sticky="ew", padx=14, pady=10)
            body_label(tab, text=app.t("provider_privacy_note"), muted=True, wraplength=680).grid(row=3, column=0, columnspan=2, sticky="ew", padx=14, pady=(4, 12))

        footer = ctk.CTkFrame(self.window, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=18, pady=(4, 14))
        footer.grid_columnconfigure(0, weight=1)

        options = ctk.CTkFrame(footer, fg_color="transparent")
        options.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        body_label(options, text=app.t("provider"), semibold=True).pack(side="left")
        self.active = tk.StringVar(value=app.settings.active_provider)
        ctk.CTkComboBox(
            options, variable=self.active, values=list(PROVIDER_DEFAULTS), state="readonly", width=185, height=38,
            fg_color=COLORS["surface"], border_color=COLORS["border"], button_color=COLORS["blue2"], font=ctk_font("body"), dropdown_font=ctk_font("body"),
        ).pack(side="left", padx=8)
        body_label(options, text=app.t("max_source_chars")).pack(side="left", padx=(18, 4))
        self.max_chars = tk.StringVar(value=str(app.settings.max_source_chars))
        ctk.CTkEntry(
            options, textvariable=self.max_chars, width=120, height=38, font=ctk_font("body"),
            fg_color=COLORS["surface"], border_color=COLORS["border"],
        ).pack(side="left")

        actions = ctk.CTkFrame(footer, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew")
        secondary_button(
            actions,
            text=app.t("delete_all_keys"),
            command=self._delete_all_keys,
            fg_color="#FFF4F3",
            hover_color="#FBE3E1",
            text_color=COLORS["error"],
            border_color="#E7B8B4",
        ).pack(side="left", padx=(0, 5))
        secondary_button(actions, text=app.t("cancel"), command=self.window.destroy, width=110, height=40).pack(side="right", padx=5)
        primary_button(actions, text=app.t("save_settings"), command=self._save, width=145, height=40).pack(side="right", padx=5)

    def _save(self) -> None:
        for key, vars_ in self.vars.items():
            cfg = self.app.settings.provider(key)
            cfg.api_key = vars_["api_key"].get().strip()
            cfg.base_url = vars_["base_url"].get().strip()
            cfg.model = vars_["model"].get().strip()
        self.app.settings.active_provider = self.active.get()
        try:
            self.app.settings.max_source_chars = max(1000, int(self.max_chars.get()))
        except Exception:
            pass
        self.app.settings_store.save(self.app.settings)
        self.app.refresh_overview()
        self.app._update_statusbar()
        self.window.destroy()

    def _delete_all_keys(self) -> None:
        if not messagebox.askyesno(
            self.app.t("confirm"),
            self.app.t("confirm_delete_all_keys"),
            parent=self.window,
        ):
            return
        for vars_ in self.vars.values():
            vars_["api_key"].set("")
        for cfg in self.app.settings.providers.values():
            cfg.api_key = ""
        self.app.settings_store.delete_all_api_keys(self.app.settings)
        self.app._update_statusbar()
        messagebox.showinfo(
            self.app.t("success"),
            self.app.t("all_keys_deleted"),
            parent=self.window,
        )


class TemplateManagerDialog:
    """Browse system/user templates and apply the selected schema to the project."""

    def __init__(self, app: MetadataLensApp):
        self.app = app
        app.templates.refresh()
        self.window = app._new_dialog(app.t("template_manager"), 1120, 790, modal=False)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        self.selected_item: TemplateItem | None = None

        heading_label(self.window, text=app.t("template_manager")).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        tabs = ctk.CTkTabview(
            self.window, fg_color=COLORS["panel"], segmented_button_fg_color=COLORS["toolbar"], segmented_button_selected_color=COLORS["blue"],
            segmented_button_selected_hover_color=COLORS["blue2"], segmented_button_unselected_color=COLORS["toolbar"], segmented_button_unselected_hover_color=COLORS["border"],
        )
        style_tabview(tabs)
        tabs.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 8))

        self.user_tree = None
        self.user_items: list[TemplateItem] = []
        self.tree_items: dict[ttk.Treeview, list[TemplateItem]] = {}
        for name, items, source in (
            (app.t("system_templates"), app.templates.system, "system"),
            (app.t("user_templates"), app.templates.user, "user"),
        ):
            tab = tabs.add(name)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
            cols = ("name", "corpus", "fields", "version", "file")
            tree = ttk.Treeview(tab, columns=cols, show="headings", selectmode="browse", style="MetadataLens.Treeview")
            headings = {
                "name": app.t("template"),
                "corpus": app.t("corpus_type"),
                "fields": app.t("field_count"),
                "version": app.t("schema_version"),
                "file": app.t("file_name"),
            }
            widths = {"name": 205, "corpus": 160, "fields": 90, "version": 90, "file": 285}
            for c in cols:
                tree.heading(c, text=headings[c])
                tree.column(c, width=widths[c], stretch=True)
            tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            self.tree_items[tree] = list(items)
            for idx, item in enumerate(items):
                tree.insert("", "end", iid=str(idx), values=(item.name, item.corpus_type, len(item.schema.fields), item.schema.schema_version, item.path.name))
            tree.bind("<<TreeviewSelect>>", lambda _e, tr=tree: self._on_select(tr))
            if source == "system":
                body_label(tab, text=app.t("system_readonly"), muted=True, wraplength=820).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
            else:
                self.user_tree = tree
                self.user_items = list(items)
                controls = ctk.CTkFrame(tab, fg_color="transparent")
                controls.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
                body_label(controls, text=app.t("user_template_note"), muted=True, wraplength=650).pack(side="left", fill=tk.X, expand=True)
                secondary_button(controls, text=app.t("delete_user_template"), command=self._delete_user).pack(side="right", padx=(8, 0))

        footer = ctk.CTkFrame(self.window, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.selection_var = tk.StringVar(value=app.t("select_template_to_apply"))
        body_label(footer, textvariable=self.selection_var, muted=True, wraplength=570).pack(side="left", fill=tk.X, expand=True, padx=(2, 8))
        secondary_button(footer, text=app.t("close"), command=self.window.destroy, width=90, height=38).pack(side="right", padx=4)
        self.apply_btn = primary_button(
            footer, text=app.t("apply_selected_template"), command=self._apply_selected, width=210, height=38, state="disabled"
        )
        self.apply_btn.pack(side="right", padx=4)

    def _on_select(self, tree: ttk.Treeview) -> None:
        selected = tree.selection()
        items = self.tree_items.get(tree, [])
        if not selected:
            return
        try:
            item = items[int(selected[0])]
        except (ValueError, IndexError):
            return
        self.selected_item = item
        self.selection_var.set(
            self.app.t("selected_template_summary", name=item.name, corpus=item.corpus_type, fields=len(item.schema.fields))
        )
        self.apply_btn.configure(state="normal" if self.app.project else "disabled")

    def _apply_selected(self) -> None:
        item = self.selected_item
        if not item:
            messagebox.showwarning(self.app.t("warning"), self.app.t("select_template_first"), parent=self.window)
            return
        if not self.app.project:
            messagebox.showwarning(self.app.t("warning"), self.app.t("no_project"), parent=self.window)
            return
        if not messagebox.askyesno(
            self.app.t("confirm"),
            self.app.t("apply_template_schema_confirm", name=item.name),
            parent=self.window,
        ):
            return
        self.app.project.schema = self.app.templates.clone_schema(item)
        if item.corpus_type and item.corpus_type != "custom":
            self.app.project.project_info.corpus_type = item.corpus_type
        self.app.project.touch()
        self.app.current_record = self.app.project.records[0] if self.app.project.records else None
        self.app.refresh_all()
        self.app.show_tab("schema_design")
        self.app._set_details(self.app.t("template_applied", name=item.name))
        self.window.destroy()

    def _delete_user(self) -> None:
        if not self.user_tree:
            return
        selected = self.user_tree.selection()
        if not selected:
            return
        try:
            item = self.user_items[int(selected[0])]
        except (ValueError, IndexError):
            return
        if not messagebox.askyesno(self.app.t("confirm"), self.app.t("confirm_delete_template", name=item.name), parent=self.window):
            return
        try:
            self.app.templates.delete_user_template(item)
            self.window.destroy()
            TemplateManagerDialog(self.app)
        except Exception as exc:
            messagebox.showerror(self.app.t("error"), str(exc), parent=self.window)


class AIExtractDialog:
    def __init__(self, app: MetadataLensApp, record: MetadataRecord):
        self.app = app
        self.record = record
        self.result: ExtractionResult | None = None
        self.cancel_event: threading.Event | None = None
        self._job_id = 0
        self._started_at = 0.0
        self.window = app._new_dialog(app.t("ai_extract"), 1380, 920, modal=False)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(4, weight=1)
        self._build()

    def _build(self) -> None:
        top = card(self.window)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top.grid_columnconfigure(1, weight=1)
        self.file = tk.StringVar()
        self.url = tk.StringVar()
        body_label(top, text=self.app.t("source_file"), semibold=True).grid(row=0, column=0, sticky="w", padx=10, pady=6)
        ctk.CTkEntry(top, textvariable=self.file, height=38, font=ctk_font("body"), fg_color=COLORS["surface"], border_color=COLORS["border"]).grid(row=0, column=1, sticky="ew", padx=10, pady=6)
        secondary_button(top, text=self.app.t("browse"), command=self._browse, width=90, height=36).grid(row=0, column=2, padx=10, pady=6)
        body_label(top, text=self.app.t("web_url"), semibold=True).grid(row=1, column=0, sticky="w", padx=10, pady=6)
        ctk.CTkEntry(top, textvariable=self.url, height=38, font=ctk_font("body"), fg_color=COLORS["surface"], border_color=COLORS["border"]).grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=6)
        body_label(top, text=self.app.t("paste_text"), semibold=True).grid(row=2, column=0, sticky="nw", padx=10, pady=6)
        self.paste = ctk.CTkTextbox(top, height=100, font=ctk_font("body"), fg_color=COLORS["surface"], border_width=1, border_color=COLORS["border"])
        self.paste.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=6)

        actions = ctk.CTkFrame(self.window, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 2))
        self.overwrite = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(actions, text=self.app.t("overwrite"), variable=self.overwrite, fg_color=COLORS["blue"], hover_color=COLORS["blue2"], text_color=COLORS["text"], font=ctk_font("body")).pack(side="left")
        self.status = tk.StringVar(value=self.app.t("status_ready"))
        body_label(actions, textvariable=self.status, muted=True).pack(side="left", padx=14)
        self.stop_btn = secondary_button(actions, text=self.app.t("stop"), command=self._stop, width=100, height=36, state="disabled")
        self.stop_btn.pack(side="right", padx=4)
        self.start_btn = primary_button(actions, text=self.app.t("start"), command=self._start, width=110, height=36)
        self.start_btn.pack(side="right", padx=4)

        self.progress = ctk.CTkProgressBar(
            self.window, mode="indeterminate", height=8, corner_radius=4,
            fg_color=COLORS["toolbar"], progress_color=COLORS["cyan"],
        )
        self.progress.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 5))
        self.progress.set(0)

        context = card(self.window)
        context.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 5))
        body_label(
            context,
            text=self.app.t(
                "ai_context_notice",
                project=self.app.project.project_info.project_name,
                schema=self.app.project.schema.schema_name,
                fields=len(self.app.project.schema.fields),
            ),
            muted=True,
            wraplength=1100,
        ).pack(fill=tk.X, padx=10, pady=8)

        frame = card(self.window)
        frame.grid(row=4, column=0, sticky="nsew", padx=12, pady=6)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        cols = ("field", "current", "suggested", "confidence", "evidence")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="extended", style="MetadataLens.Treeview")
        headings = {
            "field": self.app.t("schema_field"), "current": self.app.t("current_value"), "suggested": self.app.t("suggested_value"),
            "confidence": self.app.t("confidence"), "evidence": self.app.t("evidence"),
        }
        for col, width in zip(cols, (190, 230, 280, 95, 420)):
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=width, stretch=True)
        sy = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        sx = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        sy.grid(row=0, column=1, sticky="ns", pady=(8, 0), padx=(0, 8))
        sx.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))

        warning_box = card(self.window)
        warning_box.grid(row=5, column=0, sticky="ew", padx=12, pady=(2, 6))
        body_label(warning_box, text=self.app.t("warnings"), semibold=True, text_color=COLORS["navy"]).pack(fill=tk.X, padx=10, pady=(8, 2))
        self.warning_text = ctk.CTkTextbox(warning_box, height=80, font=ctk_font("body"), fg_color=COLORS["surface"], border_width=1, border_color=COLORS["border"])
        self.warning_text.pack(fill=tk.X, padx=10, pady=(0, 8))

        bottom = ctk.CTkFrame(self.window, fg_color="transparent")
        bottom.grid(row=6, column=0, sticky="ew", padx=12, pady=10)
        secondary_button(bottom, text=self.app.t("apply_selected"), command=lambda: self._apply(True)).pack(side="right", padx=5)
        primary_button(bottom, text=self.app.t("apply_all"), command=lambda: self._apply(False)).pack(side="right", padx=5)

    def _browse(self) -> None:
        filename = filedialog.askopenfilename(parent=self.window, filetypes=[("Supported", "*.txt *.md *.csv *.tsv *.json *.xml *.html *.htm *.pdf *.jpg *.jpeg *.png *.webp *.bmp *.gif *.tif *.tiff"), ("All", "*.*")])
        if filename:
            self.file.set(filename)

    def _source(self):
        if self.file.get().strip():
            return read_source_file(Path(self.file.get().strip()), self.app.settings.max_source_chars)
        if self.url.get().strip():
            return read_webpage(self.url.get().strip(), self.app.settings.max_source_chars)
        text = self.paste.get("1.0", "end").strip()
        if text:
            return read_pasted_text(text, self.app.settings.max_source_chars)
        raise ValueError(self.app.t("no_source_selected"))

    def _set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")
        if running:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)

    def _start(self) -> None:
        try:
            source = self._source()
        except Exception as exc:
            messagebox.showerror(self.app.t("error"), str(exc), parent=self.window)
            return
        self._job_id += 1
        job_id = self._job_id
        self.cancel_event = threading.Event()
        self.result = None
        self._started_at = time.monotonic()
        self.status.set(self.app.t("working"))
        self.tree.delete(*self.tree.get_children())
        self.warning_text.delete("1.0", "end")
        self._set_running(True)

        def work() -> None:
            try:
                result = extract_metadata(self.app.settings, self.app.project, self.record, source, cancel_event=self.cancel_event)
            except LLMCancelledError:
                self.window.after(0, lambda: self._cancelled(job_id))
                return
            except Exception as exc:  # noqa: BLE001
                self.window.after(0, lambda e=exc: self._failed(job_id, e))
                return
            self.window.after(0, lambda r=result: self._done(job_id, r))

        threading.Thread(target=work, daemon=True).start()

    def _stop(self) -> None:
        if self.cancel_event:
            self.cancel_event.set()
        self.status.set(self.app.t("stopping"))
        self._set_running(False)
        self.status.set(self.app.t("cancelled"))

    def _cancelled(self, job_id: int) -> None:
        if job_id != self._job_id:
            return
        self._set_running(False)
        self.status.set(self.app.t("cancelled"))

    def _failed(self, job_id: int, exc: Exception) -> None:
        if job_id != self._job_id or (self.cancel_event and self.cancel_event.is_set()):
            return
        self._set_running(False)
        self.status.set(self.app.t("failed"))
        provider = self.app.settings.active_provider
        messagebox.showerror(self.app.t("llm_error_title"), friendly_llm_error(exc, provider, self.app.i18n.language), parent=self.window)

    def _done(self, job_id: int, result: ExtractionResult) -> None:
        if job_id != self._job_id or (self.cancel_event and self.cancel_event.is_set()):
            return
        self._set_running(False)
        self.result = result
        self.tree.delete(*self.tree.get_children())
        for fid, extracted in result.fields.items():
            field_def = self.app.project.schema.get_field(fid)
            label = field_def.display_label(self.app.i18n.language) if field_def else fid
            value = "; ".join(map(str, extracted.value)) if isinstance(extracted.value, list) else str(extracted.value)
            current = self.record.get_value(fid)
            self.tree.insert("", "end", iid=fid, values=(f"{label} ({fid})", current, value, f"{extracted.confidence:.2f}", extracted.evidence))
        self.warning_text.delete("1.0", "end")
        self.warning_text.insert("1.0", "\n".join(result.warnings) if result.warnings else self.app.t("no_warnings"))
        elapsed = max(0.0, time.monotonic() - self._started_at)
        self.status.set(self.app.t("done_elapsed", seconds=f"{elapsed:.1f}"))

    def _apply(self, selected: bool) -> None:
        if not self.result:
            return
        ids = set(self.tree.selection()) if selected else None
        if selected and not ids:
            messagebox.showwarning(self.app.t("warning"), self.app.t("select_items_first"), parent=self.window)
            return
        count = apply_extraction(self.app.project, self.record, self.result, overwrite=self.overwrite.get(), selected=ids)
        self.app.current_record = self.record
        self.app.refresh_all()
        messagebox.showinfo(self.app.t("success"), self.app.t("ai_applied", count=count), parent=self.window)


class BatchAIExtractDialog:
    """Batch metadata extraction for creating *new* metadata records.

    Every reference file is an independent pending record by default. Nothing
    is matched against existing project records, and nothing is written to the
    project until the user reviews and explicitly applies suggestions.
    """

    def __init__(self, app: MetadataLensApp):
        self.app = app
        self.window = app._new_dialog(app.t("batch_ai_extract"), 1540, 960, modal=False)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(3, weight=1)

        self.task_order: list[str] = []
        self.source_map: dict[str, list[Path]] = {}
        self.url_map: dict[str, str] = {}
        self.draft_records: dict[str, MetadataRecord] = {}
        self.results: dict[str, ExtractionResult] = {}
        self.applied_fields: dict[str, set[str]] = {}
        self.committed_records: dict[str, str] = {}
        self.failures: dict[str, str] = {}
        self.cancel_event: threading.Event | None = None
        self._job_id = 0
        self._running = False

        self._build()

    def _build(self) -> None:
        top = ctk.CTkFrame(self.window, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        heading_label(top, text=self.app.t("batch_ai_extract")).pack(fill=tk.X)
        body_label(top, text=self.app.t("batch_ai_help_new"), muted=True, wraplength=1280).pack(fill=tk.X, pady=(6, 3))
        if self.app.project:
            body_label(
                top,
                text=self.app.t(
                    "ai_context_notice",
                    project=self.app.project.project_info.project_name,
                    schema=self.app.project.schema.schema_name,
                    fields=len(self.app.project.schema.fields),
                ),
                muted=True,
                wraplength=1280,
            ).pack(fill=tk.X, pady=(0, 3))

        source_toolbar = ctk.CTkFrame(self.window, fg_color="transparent")
        source_toolbar.grid(row=1, column=0, sticky="ew", padx=12, pady=5)
        source_toolbar.grid_columnconfigure(0, weight=1)

        source_actions = ctk.CTkFrame(source_toolbar, fg_color="transparent")
        source_actions.grid(row=0, column=0, sticky="ew")
        primary_button(
            source_actions, text=self.app.t("batch_add_reference_files"), command=self._add_files, width=190, height=38
        ).pack(side=tk.LEFT, padx=4, pady=2)
        primary_button(
            source_actions, text=self.app.t("batch_import_urls_text"), command=self._add_urls_from_text, width=210, height=38
        ).pack(side=tk.LEFT, padx=4, pady=2)
        secondary_button(
            source_actions, text=self.app.t("remove_selected_batch_sources"), command=self._remove_selected, width=185, height=38
        ).pack(side=tk.LEFT, padx=4, pady=2)
        secondary_button(
            source_actions, text=self.app.t("clear_all_batch_sources"), command=self._clear_all, width=175, height=38
        ).pack(side=tk.LEFT, padx=4, pady=2)

        run_row = ctk.CTkFrame(source_toolbar, fg_color="transparent")
        run_row.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.status = tk.StringVar(value=self.app.t("batch_waiting_files_or_urls"))
        body_label(run_row, textvariable=self.status, muted=True, wraplength=850).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        self.stop_btn = secondary_button(run_row, text=self.app.t("stop"), command=self._stop, width=105, height=38, state="disabled")
        self.stop_btn.pack(side=tk.RIGHT, padx=4)
        self.start_btn = primary_button(run_row, text=self.app.t("start_batch"), command=self._start, width=185, height=38)
        self.start_btn.pack(side=tk.RIGHT, padx=4)

        self.progress = ctk.CTkProgressBar(self.window, mode="determinate", height=8, corner_radius=4, fg_color=COLORS["toolbar"], progress_color=COLORS["cyan"])
        self.progress.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 5))
        self.progress.set(0)

        split = ttk.Panedwindow(self.window, orient=tk.HORIZONTAL)
        split.grid(row=3, column=0, sticky="nsew", padx=12, pady=6)
        left = card(split)
        right = card(split)
        split.add(left, weight=2)
        split.add(right, weight=3)

        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)
        body_label(left, text=self.app.t("batch_new_records_and_sources"), semibold=True, text_color=COLORS["navy"]).grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 3))
        cols = ("task", "source", "status", "suggestions")
        self.record_tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="extended", style="MetadataLens.Treeview")
        headings = {
            "task": self.app.t("new_metadata_record"),
            "source": self.app.t("reference_sources"),
            "status": self.app.t("status"),
            "suggestions": self.app.t("suggestion_count"),
        }
        for col, width in zip(cols, (185, 360, 135, 105)):
            self.record_tree.heading(col, text=headings[col])
            self.record_tree.column(col, width=width, stretch=True)
        ry = ttk.Scrollbar(left, orient="vertical", command=self.record_tree.yview)
        rx = ttk.Scrollbar(left, orient="horizontal", command=self.record_tree.xview)
        self.record_tree.configure(yscrollcommand=ry.set, xscrollcommand=rx.set)
        self.record_tree.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        ry.grid(row=1, column=1, sticky="ns", padx=(0, 8), pady=(8, 0))
        rx.grid(row=2, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))
        self.record_tree.bind("<<TreeviewSelect>>", self._show_record_result)

        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        body_label(right, text=self.app.t("review_ai_suggestions"), semibold=True, text_color=COLORS["navy"]).grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 3))
        scols = ("field", "current", "suggested", "confidence", "evidence")
        self.suggestion_tree = ttk.Treeview(right, columns=scols, show="headings", selectmode="extended", style="MetadataLens.Treeview")
        sheadings = {
            "field": self.app.t("schema_field"),
            "current": self.app.t("current_value"),
            "suggested": self.app.t("suggested_value"),
            "confidence": self.app.t("confidence"),
            "evidence": self.app.t("evidence"),
        }
        for col, width in zip(scols, (185, 210, 250, 90, 360)):
            self.suggestion_tree.heading(col, text=sheadings[col])
            self.suggestion_tree.column(col, width=width, stretch=True)
        sy = ttk.Scrollbar(right, orient="vertical", command=self.suggestion_tree.yview)
        sx = ttk.Scrollbar(right, orient="horizontal", command=self.suggestion_tree.xview)
        self.suggestion_tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.suggestion_tree.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        sy.grid(row=1, column=1, sticky="ns", pady=(8, 0), padx=(0, 8))
        sx.grid(row=2, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))

        bottom = ctk.CTkFrame(self.window, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew", padx=12, pady=10)
        body_label(bottom, text=self.app.t("batch_apply_note"), muted=True).pack(side=tk.LEFT, padx=4)
        secondary_button(bottom, text=self.app.t("apply_selected_fields_current"), command=self._apply_selected_current, width=215, height=38).pack(side=tk.RIGHT, padx=4)
        secondary_button(bottom, text=self.app.t("apply_current_result_new"), command=self._apply_current, width=190, height=38).pack(side=tk.RIGHT, padx=4)
        primary_button(bottom, text=self.app.t("apply_all_batch_results_new"), command=self._apply_all_results, width=220, height=38).pack(side=tk.RIGHT, padx=4)

    def _choose_files(self) -> list[Path]:
        filenames = filedialog.askopenfilenames(
            parent=self.window,
            filetypes=[
                ("Supported", "*.txt *.md *.csv *.tsv *.json *.xml *.html *.htm *.pdf *.jpg *.jpeg *.png *.webp *.bmp *.gif *.tif *.tiff"),
                ("All", "*.*"),
            ],
        )
        return [Path(name) for name in filenames]

    def _new_task_id(self) -> str:
        index = len(self.task_order) + 1
        while f"new_{index:04d}" in self.task_order:
            index += 1
        return f"new_{index:04d}"

    def _add_files(self) -> None:
        paths = self._choose_files()
        if not paths:
            return
        existing = {str(paths_[0].resolve()) for paths_ in self.source_map.values() if paths_}
        added = 0
        for path in paths:
            key = str(path.resolve())
            if key in existing:
                continue
            task_id = self._new_task_id()
            self.task_order.append(task_id)
            self.source_map[task_id] = [path]
            # Temporary record: intentionally not added to the project yet.
            self.draft_records[task_id] = MetadataRecord(record_id=path.stem or task_id)
            existing.add(key)
            added += 1
        self._refresh_record_tree()
        self.status.set(self.app.t("batch_new_files_added", count=added, total=len(self.task_order)))

    def _add_urls_from_text(self) -> None:
        """Create one pending metadata record per unique URL found in a text file."""
        filename = filedialog.askopenfilename(
            parent=self.window,
            filetypes=[
                (self.app.t("url_list_text_files"), "*.txt *.md *.csv *.tsv"),
                ("Text", "*.txt"),
                ("All", "*.*"),
            ],
        )
        if not filename:
            return
        try:
            urls = extract_http_urls(safe_read_text(Path(filename)))
        except Exception as exc:
            messagebox.showerror(self.app.t("error"), str(exc), parent=self.window)
            return
        if not urls:
            messagebox.showwarning(self.app.t("warning"), self.app.t("no_urls_found"), parent=self.window)
            return

        existing_urls = set(self.url_map.values())
        added = 0
        for url in urls:
            if url in existing_urls:
                continue
            task_id = self._new_task_id()
            self.task_order.append(task_id)
            self.url_map[task_id] = url
            # The URL is source evidence, not an identifier. Keep a neutral
            # temporary ID; the model may suggest a record_id during review.
            self.draft_records[task_id] = MetadataRecord(record_id=task_id)
            existing_urls.add(url)
            added += 1
        self._refresh_record_tree()
        self.status.set(self.app.t("batch_urls_added", count=added, total=len(self.task_order)))

    def _remove_selected(self) -> None:
        if self._running:
            return
        selected = list(self.record_tree.selection())
        if not selected:
            return
        for task_id in selected:
            if task_id in self.committed_records:
                # Applied records are already part of the project; removing the
                # batch task must not delete user data.
                continue
            if task_id in self.task_order:
                self.task_order.remove(task_id)
            self.source_map.pop(task_id, None)
            self.url_map.pop(task_id, None)
            self.draft_records.pop(task_id, None)
            self.results.pop(task_id, None)
            self.applied_fields.pop(task_id, None)
            self.failures.pop(task_id, None)
        self._refresh_record_tree()
        self.status.set(self.app.t("batch_waiting_files_or_urls") if not self.task_order else self.app.t("batch_ready_count", count=len(self.task_order)))

    def _clear_all(self) -> None:
        if self._running:
            return
        removable = [task_id for task_id in self.task_order if task_id not in self.committed_records]
        if not removable:
            return
        if not messagebox.askyesno(self.app.t("confirm"), self.app.t("confirm_clear_batch_sources", count=len(removable)), parent=self.window):
            return
        for task_id in removable:
            self.task_order.remove(task_id)
            self.source_map.pop(task_id, None)
            self.url_map.pop(task_id, None)
            self.draft_records.pop(task_id, None)
            self.results.pop(task_id, None)
            self.applied_fields.pop(task_id, None)
            self.failures.pop(task_id, None)
        self._refresh_record_tree()
        self.status.set(self.app.t("batch_waiting_files_or_urls"))

    def _task_label(self, task_id: str) -> str:
        if task_id in self.committed_records:
            return self.committed_records[task_id]
        try:
            number = self.task_order.index(task_id) + 1
        except ValueError:
            number = 0
        return self.app.t("new_record_number", number=number)

    def _source_display(self, task_id: str) -> str:
        url = self.url_map.get(task_id, "")
        if url:
            return url
        paths = self.source_map.get(task_id, [])
        return "; ".join(path.name for path in paths) if paths else self.app.t("not_assigned")

    def _record_status(self, task_id: str) -> str:
        if task_id in self.failures:
            return self.app.t("failed")
        result = self.results.get(task_id)
        if result:
            applied = self.applied_fields.get(task_id, set())
            if result.fields and set(result.fields).issubset(applied):
                return self.app.t("applied")
            return self.app.t("review_pending")
        return self.app.t("ready") if (self.source_map.get(task_id) or self.url_map.get(task_id)) else self.app.t("waiting_for_source")

    def _refresh_record_tree(self) -> None:
        if not hasattr(self, "record_tree"):
            return
        selected = set(self.record_tree.selection())
        self.record_tree.delete(*self.record_tree.get_children())
        for task_id in self.task_order:
            result = self.results.get(task_id)
            self.record_tree.insert(
                "",
                "end",
                iid=task_id,
                values=(self._task_label(task_id), self._source_display(task_id), self._record_status(task_id), len(result.fields) if result else 0),
            )
        restored = [task_id for task_id in selected if self.record_tree.exists(task_id)]
        if restored:
            self.record_tree.selection_set(restored)
        elif self.task_order:
            first = self.task_order[0]
            if self.record_tree.exists(first):
                self.record_tree.selection_set(first)
        self._show_record_result()

    def _combine_source(self, task_id: str):
        url = self.url_map.get(task_id, "").strip()
        if url:
            return read_webpage(url, self.app.settings.max_source_chars)
        paths = self.source_map.get(task_id, [])
        payloads = [read_source_file(path, self.app.settings.max_source_chars) for path in paths]
        if len(payloads) == 1:
            return payloads[0]
        if any(payload.is_image or payload.is_pdf_file_input for payload in payloads):
            raise ValueError(self.app.t("multi_binary_reference_not_supported"))
        combined = []
        warnings: list[str] = []
        for payload in payloads:
            combined.append(f"\n[REFERENCE FILE: {payload.file_name}]\n{payload.text}")
            warnings.extend(payload.warnings)
        source = read_pasted_text("\n".join(combined), self.app.settings.max_source_chars)
        source.source_kind = "multiple_reference_files"
        source.file_name = "; ".join(path.name for path in paths)
        source.warnings = warnings + source.warnings
        return source

    def _set_running(self, running: bool) -> None:
        self._running = running
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def _start(self) -> None:
        tasks = [task_id for task_id in self.task_order if self.source_map.get(task_id) or self.url_map.get(task_id)]
        if not tasks:
            messagebox.showwarning(self.app.t("warning"), self.app.t("batch_ai_need_new_sources"), parent=self.window)
            return
        self._job_id += 1
        job_id = self._job_id
        self.cancel_event = threading.Event()
        for task_id in tasks:
            self.results.pop(task_id, None)
            self.failures.pop(task_id, None)
            # A deliberate rerun produces a fresh review cycle. If this task
            # has already created a project record, applying the new result
            # updates that same record rather than creating a duplicate.
            self.applied_fields.pop(task_id, None)
        self._set_running(True)
        self.progress.set(0)
        self.status.set(self.app.t("batch_progress_new", current=0, total=len(tasks), file="—"))
        self._refresh_record_tree()

        def work() -> None:
            failed_count = 0
            for index, task_id in enumerate(tasks, 1):
                if self.cancel_event and self.cancel_event.is_set():
                    self.window.after(0, lambda: self._batch_cancelled(job_id))
                    return
                try:
                    source = self._combine_source(task_id)
                    draft = self.draft_records.setdefault(task_id, MetadataRecord(record_id=task_id))
                    result = extract_metadata(self.app.settings, self.app.project, draft, source, cancel_event=self.cancel_event)
                except LLMCancelledError:
                    self.window.after(0, lambda: self._batch_cancelled(job_id))
                    return
                except Exception as exc:  # noqa: BLE001
                    failed_count += 1
                    self.window.after(0, lambda e=exc, tid=task_id, i=index, total=len(tasks): self._batch_failed(job_id, tid, e, i, total))
                    continue
                self.window.after(0, lambda tid=task_id, r=result, i=index, total=len(tasks): self._batch_item_done(job_id, tid, r, i, total))
            self.window.after(0, lambda f=failed_count: self._batch_done(job_id, len(tasks), f))

        threading.Thread(target=work, daemon=True).start()

    def _stop(self) -> None:
        if self.cancel_event:
            self.cancel_event.set()
        self._job_id += 1
        self._set_running(False)
        self.status.set(self.app.t("cancelled"))

    def _batch_cancelled(self, job_id: int) -> None:
        if job_id != self._job_id:
            return
        self._set_running(False)
        self.status.set(self.app.t("cancelled"))

    def _batch_failed(self, job_id: int, task_id: str, exc: Exception, current: int, total: int) -> None:
        if job_id != self._job_id or (self.cancel_event and self.cancel_event.is_set()):
            return
        provider = self.app.settings.active_provider
        friendly = friendly_llm_error(exc, provider, self.app.i18n.language)
        self.failures[task_id] = friendly
        self.progress.set(current / max(1, total))
        file_name = self._source_display(task_id)
        self.status.set(self.app.t("batch_failed_file", file=file_name))
        self._refresh_record_tree()

    def _batch_item_done(self, job_id: int, task_id: str, result: ExtractionResult, current: int, total: int) -> None:
        if job_id != self._job_id or (self.cancel_event and self.cancel_event.is_set()):
            return
        self.results[task_id] = result
        self.failures.pop(task_id, None)
        self.progress.set(current / max(1, total))
        self.status.set(self.app.t("batch_progress_new", current=current, total=total, file=self._source_display(task_id)))
        self._refresh_record_tree()
        if self.record_tree.exists(task_id):
            self.record_tree.selection_set(task_id)
            self.record_tree.see(task_id)
            self._show_record_result()

    def _batch_done(self, job_id: int, total: int, failed_count: int) -> None:
        if job_id != self._job_id or (self.cancel_event and self.cancel_event.is_set()):
            return
        self._set_running(False)
        self.progress.set(1)
        success = max(0, total - failed_count)
        self.status.set(self.app.t("batch_done_new", success=success, failed=failed_count))
        if failed_count and self.failures:
            lines = [f"{self._source_display(task_id)}: {error}" for task_id, error in list(self.failures.items())[:8]]
            if len(self.failures) > 8:
                lines.append(f"… +{len(self.failures) - 8}")
            messagebox.showerror(self.app.t("llm_error_title"), "\n\n".join(lines), parent=self.window)

    def _current_task_id(self) -> str | None:
        selected = self.record_tree.selection()
        return selected[0] if selected else None

    def _current_applied_record(self, task_id: str) -> MetadataRecord | None:
        rid = self.committed_records.get(task_id)
        return self.app.project.get_record(rid) if rid and self.app.project else None

    def _show_record_result(self, _event=None) -> None:
        self.suggestion_tree.delete(*self.suggestion_tree.get_children())
        task_id = self._current_task_id()
        if not task_id:
            return
        result = self.results.get(task_id)
        if not result:
            return
        record = self._current_applied_record(task_id) or self.draft_records.get(task_id)
        applied = self.applied_fields.get(task_id, set())
        for fid, item in result.fields.items():
            field = self.app.project.schema.get_field(fid) if self.app.project else None
            label = field.display_label(self.app.i18n.language) if field else fid
            value = item.value
            suggested = "; ".join(str(x) for x in value) if isinstance(value, list) else str(value)
            current = record.get_value(fid) if record else ""
            prefix = "✓ " if fid in applied else ""
            self.suggestion_tree.insert(
                "", "end", iid=fid,
                values=(prefix + label, current, suggested, f"{item.confidence:.2f}", item.evidence),
            )
        children = self.suggestion_tree.get_children()
        if children:
            self.suggestion_tree.selection_set(children)

    def _ensure_committed(self, task_id: str) -> MetadataRecord:
        existing = self._current_applied_record(task_id)
        if existing:
            return existing
        result = self.results.get(task_id)
        draft = self.draft_records.get(task_id) or MetadataRecord()
        candidate = (result.record_id.strip() if result and result.record_id.strip() else draft.record_id.strip()) or None
        record = MetadataRecord(
            record_id=self.app.project.ensure_unique_record_id(candidate),
            record_type=(result.record_type.strip() if result and result.record_type.strip() else draft.record_type or "text"),
        )
        self.app.project.add_record(record)
        self.committed_records[task_id] = record.record_id
        return record

    def _apply_selected_current(self) -> None:
        task_id = self._current_task_id()
        if not task_id or task_id not in self.results:
            return
        selected = set(self.suggestion_tree.selection())
        if not selected:
            messagebox.showwarning(self.app.t("warning"), self.app.t("select_items_first"), parent=self.window)
            return
        self._apply_task(task_id, selected)

    def _apply_current(self) -> None:
        task_id = self._current_task_id()
        if not task_id or task_id not in self.results:
            return
        self._apply_task(task_id, set(self.results[task_id].fields))

    def _apply_task(self, task_id: str, fields: set[str]) -> tuple[int, bool]:
        result = self.results.get(task_id)
        if not result or not fields:
            return 0, False
        record = self._ensure_committed(task_id)
        remaining = fields - self.applied_fields.get(task_id, set())
        if not remaining:
            return 0, False
        count = apply_extraction(self.app.project, record, result, overwrite=True, selected=remaining)
        if count:
            self.applied_fields.setdefault(task_id, set()).update(remaining)
            self.app.current_record = record
            self.app.refresh_all()
            self._refresh_record_tree()
            if self.record_tree.exists(task_id):
                self.record_tree.selection_set(task_id)
            self._show_record_result()
        return count, True

    def _apply_all_results(self) -> None:
        pending = [task_id for task_id in self.task_order if task_id in self.results and set(self.results[task_id].fields) - self.applied_fields.get(task_id, set())]
        if not pending:
            return
        if not messagebox.askyesno(self.app.t("confirm"), self.app.t("confirm_apply_all_batch_new", count=len(pending)), parent=self.window):
            return
        records = 0
        fields = 0
        for task_id in pending:
            remaining = set(self.results[task_id].fields) - self.applied_fields.get(task_id, set())
            count, applied = self._apply_task(task_id, remaining)
            fields += count
            if applied:
                records += 1
        self.app.refresh_all()
        messagebox.showinfo(self.app.t("success"), self.app.t("batch_apply_done_new", records=records, fields=fields), parent=self.window)


class BatchEditDialog:
    """Batch-edit one field across selected records or the whole project."""

    def __init__(self, app: MetadataLensApp):
        self.app = app
        self.initial_selected = app._selected_records()
        self.target_mode = tk.StringVar(value="selected" if self.initial_selected else "all")
        self.window = app._new_dialog(app.t("batch_edit_field"), 1120, 820, modal=False)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(3, weight=1)
        self._field_map: dict[str, str] = {}
        self._operation_map: dict[str, str] = {
            app.t("batch_op_set"): "set",
            app.t("batch_op_append"): "append",
            app.t("batch_op_clear"): "clear",
        }
        self._build()
        self._refresh_preview()

    def _target_records(self) -> list[MetadataRecord]:
        if self.target_mode.get() == "selected" and self.initial_selected:
            return list(self.initial_selected)
        return list(self.app.project.records)

    def _build(self) -> None:
        top = card(self.window)
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=14)
        body_label(top, text=self.app.t("batch_edit_help"), muted=True, wraplength=910).pack(fill=tk.X, padx=12, pady=(10, 6))
        target = ctk.CTkFrame(top, fg_color="transparent")
        target.pack(fill=tk.X, padx=10, pady=(0, 8))
        ctk.CTkRadioButton(target, text=self.app.t("selected_records"), variable=self.target_mode, value="selected", command=self._refresh_preview, fg_color=COLORS["blue"], hover_color=COLORS["blue2"], text_color=COLORS["text"], font=ctk_font("body"), state="normal" if self.initial_selected else "disabled").pack(side=tk.LEFT, padx=(0, 12))
        ctk.CTkRadioButton(target, text=self.app.t("all_records"), variable=self.target_mode, value="all", command=self._refresh_preview, fg_color=COLORS["blue"], hover_color=COLORS["blue2"], text_color=COLORS["text"], font=ctk_font("body")).pack(side=tk.LEFT)
        self.target_count = tk.StringVar()
        body_label(target, textvariable=self.target_count, muted=True).pack(side=tk.RIGHT)

        form = card(self.window)
        form.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        form.grid_columnconfigure(1, weight=1)
        body_label(form, text=self.app.t("schema_field"), semibold=True).grid(row=0, column=0, sticky="w", padx=12, pady=8)
        values: list[str] = []
        for field_def in self.app.project.schema.sorted_fields(visible_only=True):
            label = f"{field_def.display_label(self.app.i18n.language)} ({field_def.field_id})"
            values.append(label)
            self._field_map[label] = field_def.field_id
        self.field_var = tk.StringVar(value=values[0] if values else "")
        self.field_combo = ctk.CTkComboBox(form, variable=self.field_var, values=values or [""], state="readonly", height=38, fg_color=COLORS["surface"], border_color=COLORS["border"], button_color=COLORS["blue2"], font=ctk_font("body"), dropdown_font=ctk_font("body"), command=lambda _v: self._refresh_preview())
        self.field_combo.grid(row=0, column=1, sticky="ew", padx=12, pady=8)

        body_label(form, text=self.app.t("batch_operation"), semibold=True).grid(row=1, column=0, sticky="w", padx=12, pady=8)
        self.operation_var = tk.StringVar(value=self.app.t("batch_op_set"))
        ctk.CTkComboBox(form, variable=self.operation_var, values=list(self._operation_map), state="readonly", height=38, fg_color=COLORS["surface"], border_color=COLORS["border"], button_color=COLORS["blue2"], font=ctk_font("body"), dropdown_font=ctk_font("body"), command=lambda _v: self._refresh_preview()).grid(row=1, column=1, sticky="ew", padx=12, pady=8)

        body_label(form, text=self.app.t("new_value"), semibold=True).grid(row=2, column=0, sticky="nw", padx=12, pady=8)
        self.value_box = ctk.CTkTextbox(form, height=90, font=ctk_font("body"), fg_color=COLORS["surface"], border_width=1, border_color=COLORS["border"])
        self.value_box.grid(row=2, column=1, sticky="ew", padx=12, pady=8)
        secondary_button(form, text=self.app.t("preview_changes"), command=self._refresh_preview, width=140, height=34).grid(row=3, column=1, sticky="e", padx=12, pady=(0, 10))

        frame = card(self.window)
        frame.grid(row=3, column=0, sticky="nsew", padx=14, pady=6)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        cols = ("record", "current", "new")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", style="MetadataLens.Treeview")
        for col, title, width in (("record", self.app.t("record_id"), 190), ("current", self.app.t("current_value"), 340), ("new", self.app.t("new_value"), 340)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, stretch=True)
        sy = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sy.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        sy.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)

        bottom = ctk.CTkFrame(self.window, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="e", padx=14, pady=12)
        secondary_button(bottom, text=self.app.t("cancel"), command=self.window.destroy, width=105).pack(side=tk.RIGHT, padx=5)
        primary_button(bottom, text=self.app.t("apply_batch_edit"), command=self._apply, width=150).pack(side=tk.RIGHT, padx=5)

    def _field_id(self) -> str:
        return self._field_map.get(self.field_var.get(), "")

    def _operation(self) -> str:
        return self._operation_map.get(self.operation_var.get(), "set")

    def _input_value(self) -> str:
        return self.value_box.get("1.0", "end").strip()

    def _new_display(self, record: MetadataRecord, field_def: MetadataField, operation: str, value: str) -> str:
        current = record.get_value(field_def.field_id)
        if operation == "clear":
            return ""
        if operation == "set":
            return value
        if not value:
            return current
        if field_def.repeatable:
            existing = record.get_values(field_def.field_id)
            additions = [part.strip() for part in value.split(";") if part.strip()]
            return "; ".join(existing + additions)
        return (current + "; " + value).strip("; ") if current else value

    def _refresh_preview(self) -> None:
        if not hasattr(self, "tree"):
            return
        self.tree.delete(*self.tree.get_children())
        records = self._target_records()
        self.target_count.set(self.app.t("target_record_count", count=len(records)))
        fid = self._field_id()
        field_def = self.app.project.schema.get_field(fid) if fid else None
        if not field_def:
            return
        operation = self._operation()
        value = self._input_value()
        for record in records[:1000]:
            self.tree.insert("", "end", iid=record.record_id, values=(record.record_id, record.get_value(fid), self._new_display(record, field_def, operation, value)))

    def _apply(self) -> None:
        records = self._target_records()
        fid = self._field_id()
        field_def = self.app.project.schema.get_field(fid) if fid else None
        if not records or not field_def:
            return
        operation = self._operation()
        value = self._input_value()
        if operation != "clear" and not value:
            messagebox.showwarning(self.app.t("warning"), self.app.t("batch_value_required"), parent=self.window)
            return
        if not messagebox.askyesno(self.app.t("confirm"), self.app.t("confirm_batch_edit", count=len(records), field=field_def.display_label(self.app.i18n.language), operation=self.operation_var.get()), parent=self.window):
            return
        changed = 0
        for record in records:
            if operation == "clear":
                record.set_value(fid, "")
            elif operation == "set":
                if field_def.repeatable:
                    record.set_value(fid, [part.strip() for part in value.split(";") if part.strip()])
                else:
                    record.set_value(fid, value)
            else:
                if field_def.repeatable:
                    existing = record.get_values(fid)
                    additions = [part.strip() for part in value.split(";") if part.strip()]
                    record.set_value(fid, existing + additions)
                else:
                    current = record.get_value(fid)
                    record.set_value(fid, (current + "; " + value).strip("; ") if current else value)
            changed += 1
        if changed:
            self.app.project.touch()
        self.app.refresh_all()
        messagebox.showinfo(self.app.t("success"), self.app.t("batch_edit_done", count=changed), parent=self.window)
        self.window.destroy()


class AISchemaDialog:
    def __init__(self, app: MetadataLensApp):
        self.app = app
        self.result: SchemaGenerationResult | None = None
        self.mode = tk.StringVar(value="extend_current_schema")
        self.cancel_event = threading.Event()
        self._job_id = 0
        self._started_at = 0.0
        self.window = app._new_dialog(app.t("ai_schema"), 1420, 950, modal=False)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(5, weight=1)
        self._build()

    def _build(self) -> None:
        mode = ctk.CTkFrame(self.window, fg_color="transparent")
        mode.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        ctk.CTkRadioButton(mode, text=self.app.t("generate_new_schema"), variable=self.mode, value="generate_new_schema", fg_color=COLORS["blue"], hover_color=COLORS["blue2"], font=ctk_font("body")).pack(side="left", padx=8)
        ctk.CTkRadioButton(mode, text=self.app.t("extend_schema"), variable=self.mode, value="extend_current_schema", fg_color=COLORS["blue"], hover_color=COLORS["blue2"], font=ctk_font("body")).pack(side="left", padx=8)

        context = self.app.project
        context_text = self.app.t(
            "ai_context_notice",
            project=context.project_info.project_name,
            schema=context.schema.schema_name,
            fields=len(context.schema.fields),
        )
        body_label(self.window, text=context_text, muted=True, wraplength=1160).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 5))

        req = card(self.window)
        req.grid(row=2, column=0, sticky="ew", padx=12, pady=6)
        req.grid_columnconfigure(0, weight=1)
        body_label(req, text=self.app.t("requirements"), semibold=True, text_color=COLORS["navy"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))
        self.text = ctk.CTkTextbox(req, height=112, font=ctk_font("body"), fg_color=COLORS["surface"], border_width=1, border_color=COLORS["border"])
        self.text.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.text.insert("1.0", self.app.t("schema_requirements_placeholder"))

        src = card(self.window)
        src.grid(row=3, column=0, sticky="ew", padx=12, pady=6)
        src.grid_columnconfigure(1, weight=1)
        self.file = tk.StringVar()
        self.url = tk.StringVar()
        body_label(src, text=self.app.t("source_file")).grid(row=0, column=0, sticky="w", padx=8, pady=5)
        ctk.CTkEntry(src, textvariable=self.file, height=38, font=ctk_font("body"), fg_color=COLORS["surface"], border_color=COLORS["border"]).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        secondary_button(src, text=self.app.t("browse"), command=self._browse, width=90, height=36).grid(row=0, column=2, padx=8, pady=5)
        body_label(src, text=self.app.t("web_url")).grid(row=1, column=0, sticky="w", padx=8, pady=5)
        ctk.CTkEntry(src, textvariable=self.url, height=38, font=ctk_font("body"), fg_color=COLORS["surface"], border_color=COLORS["border"]).grid(row=1, column=1, columnspan=2, sticky="ew", padx=8, pady=5)
        body_label(src, text=self.app.t("paste_text")).grid(row=2, column=0, sticky="nw", padx=8, pady=5)
        self.source_text = ctk.CTkTextbox(src, height=72, font=ctk_font("body"), fg_color=COLORS["surface"], border_width=1, border_color=COLORS["border"])
        self.source_text.grid(row=2, column=1, columnspan=2, sticky="ew", padx=8, pady=5)

        actions = ctk.CTkFrame(self.window, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", padx=12, pady=6)
        self.status = tk.StringVar(value=self.app.t("status_ready"))
        body_label(actions, textvariable=self.status, muted=True).pack(side="left")
        self.progress = ctk.CTkProgressBar(actions, width=220, height=10, mode="indeterminate", progress_color=COLORS["blue"])
        self.progress.pack(side="left", padx=16)
        self.progress.set(0)
        self.stop_btn = secondary_button(actions, text=self.app.t("stop"), command=self._stop, width=90, height=36)
        self.stop_btn.pack(side="right", padx=(5, 0))
        self.stop_btn.configure(state="disabled")
        self.start_btn = primary_button(actions, text=self.app.t("start"), command=self._start, width=110, height=36)
        self.start_btn.pack(side="right", padx=5)

        frame = card(self.window)
        frame.grid(row=5, column=0, sticky="nsew", padx=12, pady=6)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        cols = ("field_id", "label_zh", "label_en", "data_type", "required", "repeatable", "level", "confidence", "rationale")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="extended", style="MetadataLens.Treeview")
        widths = (150, 130, 165, 100, 80, 90, 90, 90, 360)
        for c, width in zip(cols, widths):
            self.tree.heading(c, text=self.app.t(c) if c in {"field_id", "label_zh", "label_en", "data_type", "required", "repeatable", "level", "confidence"} else self.app.t("rationale"))
            self.tree.column(c, width=width, stretch=True)
        sy = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        sx = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        sy.grid(row=0, column=1, sticky="ns", pady=(8, 0), padx=(0, 8))
        sx.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))

        bottom = ctk.CTkFrame(self.window, fg_color="transparent")
        bottom.grid(row=6, column=0, sticky="ew", padx=12, pady=10)
        secondary_button(bottom, text=self.app.t("apply_selected"), command=lambda: self._apply(True)).pack(side="right", padx=5)
        primary_button(bottom, text=self.app.t("apply_all"), command=lambda: self._apply(False)).pack(side="right", padx=5)

    def _browse(self) -> None:
        filename = filedialog.askopenfilename(parent=self.window, filetypes=[("Supported", "*.txt *.md *.csv *.tsv *.json *.xml *.html *.htm *.pdf *.jpg *.jpeg *.png *.webp *.bmp *.gif *.tif *.tiff"), ("All", "*.*")])
        if filename:
            self.file.set(filename)

    def _source(self):
        if self.file.get().strip():
            return read_source_file(Path(self.file.get().strip()), self.app.settings.max_source_chars)
        if self.url.get().strip():
            return read_webpage(self.url.get().strip(), self.app.settings.max_source_chars)
        return read_pasted_text(self.source_text.get("1.0", "end").strip(), self.app.settings.max_source_chars)

    def _set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")
        if running:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)

    def _start(self) -> None:
        requirements = self.text.get("1.0", "end").strip()
        if not requirements:
            messagebox.showwarning(self.app.t("warning"), self.app.t("requirements_required"), parent=self.window)
            return
        try:
            source = self._source()
        except Exception as exc:
            messagebox.showerror(self.app.t("error"), str(exc), parent=self.window)
            return
        self.result = None
        self.cancel_event = threading.Event()
        self._job_id += 1
        job_id = self._job_id
        self._started_at = time.monotonic()
        self.status.set(self.app.t("working"))
        self.tree.delete(*self.tree.get_children())
        self._set_running(True)

        def work() -> None:
            try:
                result = generate_schema(
                    self.app.settings,
                    self.app.project,
                    requirements,
                    source,
                    self.mode.get(),
                    cancel_event=self.cancel_event,
                )
            except Exception as exc:
                self.window.after(0, lambda e=exc, j=job_id: self._failed(e, j))
                return
            self.window.after(0, lambda r=result, j=job_id: self._done(r, j))

        threading.Thread(target=work, daemon=True).start()

    def _stop(self) -> None:
        self.cancel_event.set()
        self._job_id += 1
        self.status.set(self.app.t("cancelled"))
        self._set_running(False)

    def _failed(self, exc: Exception, job_id: int) -> None:
        if job_id != self._job_id:
            return
        self._set_running(False)
        if isinstance(exc, LLMCancelledError):
            self.status.set(self.app.t("cancelled"))
            return
        self.status.set(self.app.t("failed"))
        messagebox.showerror(
            self.app.t("llm_error_title"),
            friendly_llm_error(exc, self.app.settings.active_provider, self.app.i18n.language),
            parent=self.window,
        )

    def _done(self, result: SchemaGenerationResult, job_id: int) -> None:
        if job_id != self._job_id or self.cancel_event.is_set():
            return
        self._set_running(False)
        self.result = result
        self.tree.delete(*self.tree.get_children())
        for candidate in result.candidates:
            f = candidate.field
            self.tree.insert(
                "", "end", iid=f.field_id,
                values=(f.field_id, f.label_zh, f.label_en, f.data_type, "✓" if f.required else "", "✓" if f.repeatable else "", f.level, f"{candidate.confidence:.2f}", candidate.rationale),
            )
        elapsed = max(0.0, time.monotonic() - self._started_at)
        status = self.app.t("done_elapsed", seconds=f"{elapsed:.1f}")
        if result.warnings:
            status += " · " + "; ".join(result.warnings)
        self.status.set(status)

    def _apply(self, selected: bool) -> None:
        if not self.result:
            return
        ids = set(self.tree.selection()) if selected else None
        if selected and not ids:
            messagebox.showwarning(self.app.t("warning"), self.app.t("select_items_first"), parent=self.window)
            return
        if self.mode.get() == "generate_new_schema" and not messagebox.askyesno(self.app.t("confirm"), self.app.t("replace_ai_schema_confirm"), parent=self.window):
            return
        count = apply_schema_generation(self.app.project, self.result, mode=self.mode.get(), selected=ids, replace_existing=False)
        self.app.refresh_all()
        self.app.show_tab("schema_design")
        messagebox.showinfo(self.app.t("success"), self.app.t("ai_applied", count=count), parent=self.window)

class GuideDialog:
    def __init__(self, app: MetadataLensApp):
        self.app = app
        self.window = app._new_dialog(app.t("user_guide"), 1040, 840, modal=False)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self.window, fg_color=COLORS["navy"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(header, text="BFSU MetadataLens", text_color="#FFFFFF", font=ctk_font("heading", semibold=True), anchor="w").pack(fill=tk.X, padx=20, pady=(15, 2))
        ctk.CTkLabel(header, text=app.t("guide_subtitle"), text_color="#DCE7EB", font=ctk_font("body"), anchor="w").pack(fill=tk.X, padx=20, pady=(0, 14))
        text = ctk.CTkTextbox(self.window, wrap=tk.WORD, font=ctk_font("body"), fg_color=COLORS["panel"], border_width=1, border_color=COLORS["border"])
        text.grid(row=1, column=0, sticky="nsew", padx=14, pady=14)
        text.insert("1.0", app.t("guide_text"))
        text.configure(state=tk.DISABLED)


class AboutDialog:
    def __init__(self, app: MetadataLensApp):
        self.app = app
        self.icon_image = None
        self.window = app._new_dialog(app.t("about"), 1040, 840, modal=False)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.window, fg_color=COLORS["navy"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        icon_path = app_root() / "assets" / "app.png"
        if icon_path.exists():
            try:
                image = Image.open(icon_path).convert("RGBA")
                self.icon_image = ctk.CTkImage(light_image=image, dark_image=image, size=(96, 96))
                ctk.CTkLabel(header, text="", image=self.icon_image).grid(row=0, column=0, rowspan=3, padx=(22, 16), pady=18, sticky="w")
            except Exception:
                self.icon_image = None

        ctk.CTkLabel(header, text="BFSU MetadataLens", text_color="#FFFFFF", font=ctk_font("brand", semibold=True), anchor="w").grid(row=0, column=1, sticky="sw", padx=(0, 20), pady=(18, 1))
        ctk.CTkLabel(header, text=f"Version {APP_VERSION}", text_color="#DCE7EB", font=ctk_font("subtitle", semibold=True), anchor="w").grid(row=1, column=1, sticky="w", padx=(0, 20), pady=1)
        ctk.CTkLabel(header, text=app.t("about_subtitle"), text_color="#DCE7EB", font=ctk_font("body"), anchor="w").grid(row=2, column=1, sticky="nw", padx=(0, 20), pady=(1, 18))

        text = ctk.CTkTextbox(
            self.window,
            wrap=tk.WORD,
            font=ctk_font("body"),
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
        )
        text.grid(row=1, column=0, sticky="nsew", padx=14, pady=14)
        text.insert("1.0", app.t("about_text"))
        text.configure(state=tk.DISABLED)

def run() -> None:
    configure_customtkinter()
    root = ctk.CTk()
    MetadataLensApp(root)
    root.mainloop()
