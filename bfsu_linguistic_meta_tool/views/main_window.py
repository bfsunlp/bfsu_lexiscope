"""Main tkinter window view."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from i18n import I18N
from models import MetadataProject
from views.record_editor import RecordEditor
from views.schema_editor import SchemaEditor


class MainWindow:
    def __init__(self, root: tk.Tk, i18n: I18N) -> None:
        self.root = root
        self.i18n = i18n
        self.controller = None
        self.project: MetadataProject | None = None
        self.project_active = False
        self.log_visible = True
        self._build_style()
        self._build()
        self.refresh_language()

    def set_controller(self, controller) -> None:
        self.controller = controller
        # 菜单第一次创建时 controller 还是 None。
        # 注入 controller 后必须重新构建菜单，否则菜单命令仍然是空命令。
        self.build_menus()

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=25)
        style.configure("TButton", padding=(8, 4))

    def _build(self) -> None:
        self.root.title(self.i18n.t("app.title"))
        self.root.geometry("1280x760")
        self.root.minsize(980, 600)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.menu_bar = tk.Menu(self.root)
        self.root.configure(menu=self.menu_bar)

        self.main_pane = ttk.PanedWindow(self.root, orient="horizontal")
        self.main_pane.grid(row=0, column=0, sticky="nsew")

        self.left_frame = ttk.Frame(self.main_pane, padding=4)
        self.center_frame = ttk.Frame(self.main_pane, padding=4)
        self.right_frame = ttk.Frame(self.main_pane, padding=4)
        self.main_pane.add(self.left_frame, weight=1)
        self.main_pane.add(self.center_frame, weight=4)
        self.main_pane.add(self.right_frame, weight=1)

        self.left_frame.columnconfigure(0, weight=1)
        self.left_frame.rowconfigure(0, weight=1)
        self.project_tree = ttk.Treeview(self.left_frame, show="tree")
        self.project_tree.grid(row=0, column=0, sticky="nsew")
        self.project_tree.bind("<<TreeviewSelect>>", self._on_nav_select)

        self.center_frame.columnconfigure(0, weight=1)
        self.center_frame.rowconfigure(0, weight=1)
        self.notebook = ttk.Notebook(self.center_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.records_tab = ttk.Frame(self.notebook)
        self.record_edit_tab = ttk.Frame(self.notebook)
        self.schema_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.records_tab, text="Records")
        self.notebook.add(self.record_edit_tab, text="Record Editor")
        self.notebook.add(self.schema_tab, text="Schema")

        self._build_records_table()
        self.record_editor = RecordEditor(
            self.record_edit_tab,
            self.i18n,
            on_change=self._mark_changed,
            on_validate=self.show_validation_messages,
            on_auto_fill=lambda: self.controller and self.controller.recognize_metadata_for_current_record(),
        )
        self.record_editor.pack(fill="both", expand=True)
        self.schema_editor = SchemaEditor(self.schema_tab, self.i18n, on_change=self._mark_changed)
        self.schema_editor.pack(fill="both", expand=True)

        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(1, weight=1)
        self.details_label = ttk.Label(self.right_frame, text="Details")
        self.details_label.grid(row=0, column=0, sticky="w")
        self.details_text = tk.Text(self.right_frame, height=20, wrap="word")
        self.details_text.grid(row=1, column=0, sticky="nsew", pady=(4, 4))

        bottom = ttk.Frame(self.root)
        bottom.grid(row=1, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(bottom, textvariable=self.status_var, anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew", padx=6)
        self.log_text = tk.Text(bottom, height=5, wrap="word")
        self.log_text.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))

    def _build_records_table(self) -> None:
        self.records_tab.columnconfigure(0, weight=1)
        self.records_tab.rowconfigure(1, weight=1)
        toolbar = ttk.Frame(self.records_tab)
        toolbar.grid(row=0, column=0, sticky="ew")
        self.new_record_btn = ttk.Button(toolbar, command=lambda: self.controller and self.controller.new_record())
        self.delete_record_btn = ttk.Button(toolbar, command=lambda: self.controller and self.controller.delete_selected_record())
        self.copy_record_btn = ttk.Button(toolbar, command=lambda: self.controller and self.controller.copy_selected_record())
        self.refresh_btn = ttk.Button(toolbar, command=self.refresh_records)
        for b in (self.new_record_btn, self.delete_record_btn, self.copy_record_btn, self.refresh_btn):
            b.pack(side="left", padx=2, pady=2)
        self.records_tree = ttk.Treeview(self.records_tab, show="headings", selectmode="browse")
        ysb = ttk.Scrollbar(self.records_tab, orient="vertical", command=self.records_tree.yview)
        xsb = ttk.Scrollbar(self.records_tab, orient="horizontal", command=self.records_tree.xview)
        self.records_tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.records_tree.grid(row=1, column=0, sticky="nsew")
        ysb.grid(row=1, column=1, sticky="ns")
        xsb.grid(row=2, column=0, sticky="ew")
        self.records_tree.bind("<<TreeviewSelect>>", self._on_record_select)

    def build_menus(self) -> None:
        self.menu_bar.delete(0, "end")
        c = self.controller
        active_state = "normal" if self.project_active else "disabled"

        file_menu = tk.Menu(self.menu_bar, tearoff=False)
        file_menu.add_command(label=self.i18n.t("new_project"), command=c.new_project if c else None)
        file_menu.add_command(label=self.i18n.t("open_project"), command=c.open_project if c else None)
        file_menu.add_command(label=self.i18n.t("close_project"), command=c.close_project if c else None, state=active_state)
        file_menu.add_separator()
        file_menu.add_command(label=self.i18n.t("save"), command=c.save_project if c else None, state=active_state)
        file_menu.add_command(label=self.i18n.t("save_as"), command=c.save_project_as if c else None, state=active_state)
        file_menu.add_separator()
        file_menu.add_command(label=self.i18n.t("import_excel"), command=c.import_excel if c else None, state=active_state)
        file_menu.add_command(label=self.i18n.t("import_xml"), command=c.import_xml if c else None, state=active_state)
        file_menu.add_separator()
        file_menu.add_command(label=self.i18n.t("export_xml"), command=c.export_records_xml if c else None, state=active_state)
        file_menu.add_command(label=self.i18n.t("export_records_csv"), command=c.export_records_csv if c else None, state=active_state)
        file_menu.add_command(label=self.i18n.t("export_records_excel"), command=c.export_records_excel if c else None, state=active_state)
        file_menu.add_separator()
        file_menu.add_command(label=self.i18n.t("exit"), command=c.close if c else self.root.destroy)
        self.menu_bar.add_cascade(label=self.i18n.t("file"), menu=file_menu)

        schema_menu = tk.Menu(self.menu_bar, tearoff=False)
        schema_menu.add_command(label=self.i18n.t("new_schema"), command=c.new_schema if c else None, state=active_state)
        schema_menu.add_command(label=self.i18n.t("ai_generate_new_schema"), command=lambda: c.design_schema_with_ai("generate_new_schema") if c else None, state=active_state)
        schema_menu.add_command(label=self.i18n.t("ai_extend_current_schema"), command=lambda: c.design_schema_with_ai("extend_current_schema") if c else None, state=active_state)
        schema_menu.add_separator()
        schema_menu.add_command(label=self.i18n.t("edit_schema"), command=lambda: self.notebook.select(self.schema_tab), state=active_state)
        schema_menu.add_command(label=self.i18n.t("import_schema"), command=c.import_schema if c else None, state=active_state)
        schema_menu.add_command(label=self.i18n.t("export_schema"), command=c.export_schema if c else None, state=active_state)
        schema_menu.add_command(label=self.i18n.t("save_schema_to_library"), command=c.save_schema_to_library if c else None, state=active_state)
        schema_menu.add_command(label=self.i18n.t("validate_schema"), command=c.validate_schema if c else None, state=active_state)
        self.menu_bar.add_cascade(label=self.i18n.t("schema"), menu=schema_menu, state=active_state)

        records_menu = tk.Menu(self.menu_bar, tearoff=False)
        records_menu.add_command(label=self.i18n.t("new_record"), command=c.new_record if c else None, state=active_state)
        records_menu.add_command(label=self.i18n.t("delete_record"), command=c.delete_selected_record if c else None, state=active_state)
        records_menu.add_command(label=self.i18n.t("copy_record"), command=c.copy_selected_record if c else None, state=active_state)
        records_menu.add_command(label=self.i18n.t("validate_record"), command=c.validate_selected_record if c else None, state=active_state)
        self.menu_bar.add_cascade(label=self.i18n.t("records"), menu=records_menu, state=active_state)

        lang_menu = tk.Menu(self.menu_bar, tearoff=False)
        lang_menu.add_command(label="中文", command=lambda: c.change_language("zh_CN") if c else None)
        lang_menu.add_command(label="English", command=lambda: c.change_language("en_US") if c else None)
        self.menu_bar.add_cascade(label=self.i18n.t("language"), menu=lang_menu)

        settings_menu = tk.Menu(self.menu_bar, tearoff=False)
        settings_menu.add_command(label=self.i18n.t("chatgpt_api_key"), command=c.open_ai_settings if c else None)
        self.menu_bar.add_cascade(label=self.i18n.t("settings"), menu=settings_menu)

        view_menu = tk.Menu(self.menu_bar, tearoff=False)
        view_menu.add_command(label=self.i18n.t("maximize"), command=self.maximize)
        view_menu.add_command(label=self.i18n.t("restore"), command=self.restore_window)
        view_menu.add_command(label=self.i18n.t("toggle_log"), command=self.toggle_log)
        self.menu_bar.add_cascade(label=self.i18n.t("view"), menu=view_menu)

        help_menu = tk.Menu(self.menu_bar, tearoff=False)
        help_menu.add_command(label=self.i18n.t("user_guide"), command=c.show_guide if c else None)
        help_menu.add_command(label=self.i18n.t("about"), command=c.show_about if c else None)
        self.menu_bar.add_cascade(label=self.i18n.t("help"), menu=help_menu)

    def set_project_active(self, active: bool) -> None:
        self.project_active = active
        tab_state = "normal" if active else "disabled"
        for tab in (self.records_tab, self.record_edit_tab, self.schema_tab):
            try:
                self.notebook.tab(tab, state=tab_state)
            except tk.TclError:
                pass
        button_state = "normal" if active else "disabled"
        for btn in (self.new_record_btn, self.delete_record_btn, self.copy_record_btn, self.refresh_btn):
            btn.configure(state=button_state)
        self.record_editor.set_enabled(active)
        self.schema_editor.set_enabled(active)
        self.details_text.configure(state="normal" if active else "disabled")
        try:
            self.project_tree.state(["!disabled"] if active else ["disabled"])
            self.records_tree.state(["!disabled"] if active else ["disabled"])
        except tk.TclError:
            pass
        self.build_menus()

    def clear_project(self) -> None:
        self.project = None
        self.project_tree.delete(*self.project_tree.get_children())
        self.records_tree.delete(*self.records_tree.get_children())
        self.records_tree.configure(columns=())
        self.schema_editor.clear()
        self.record_editor.clear()
        self.set_project_active(False)
        self.show_text("")
        self.update_status()

    def refresh_language(self) -> None:
        self.root.title(self.i18n.t("app.title"))
        self.details_label.configure(text=self.i18n.t("field_details"))
        self.new_record_btn.configure(text=self.i18n.t("new_record"))
        self.delete_record_btn.configure(text=self.i18n.t("delete_record"))
        self.copy_record_btn.configure(text=self.i18n.t("copy_record"))
        self.refresh_btn.configure(text=self.i18n.t("refresh"))
        self.notebook.tab(self.records_tab, text=self.i18n.t("records"))
        self.notebook.tab(self.record_edit_tab, text=self.i18n.t("record_editor_tab"))
        self.notebook.tab(self.schema_tab, text=self.i18n.t("schema"))
        self.record_editor.refresh_language()
        self.schema_editor.refresh_language()
        self.refresh_project_tree()
        self.refresh_records()
        self.update_status()
        self.build_menus()

    def load_project(self, project: MetadataProject) -> None:
        self.project = project
        self.set_project_active(True)
        self.schema_editor.load_schema(project.schema)
        self.record_editor.load_project(project)
        self.refresh_project_tree()
        self.refresh_records()
        self.update_status()

    def refresh_project_tree(self) -> None:
        self.project_tree.delete(*self.project_tree.get_children())
        if not self.project:
            return
        root = self.project_tree.insert("", "end", iid="project", text=self.i18n.t("project"), open=True)
        self.project_tree.insert(root, "end", iid="project_info", text=self.i18n.t("project_info"))
        self.project_tree.insert(root, "end", iid="schema", text=f"{self.i18n.t('schema')} ({len(self.project.schema.fields)})")
        self.project_tree.insert(root, "end", iid="records", text=f"{self.i18n.t('records')} ({len(self.project.records)})")
        self.project_tree.insert(root, "end", iid="relations", text=f"{self.i18n.t('relations')} ({len(self.project.relations)})")

    def _measure_text(self, text: object) -> int:
        try:
            return tkfont.nametofont("TkDefaultFont").measure(str(text))
        except tk.TclError:
            return len(str(text)) * 10

    def refresh_records(self) -> None:
        self.records_tree.delete(*self.records_tree.get_children())
        if not self.project:
            self.records_tree.configure(columns=())
            self.refresh_project_tree()
            return
        schema_fields = self.project.schema.field_ids()
        fields = ["record_id", "record_type"] + schema_fields
        self.records_tree.configure(columns=fields)
        heading_texts: dict[str, str] = {
            "record_id": self.i18n.t("record_id"),
            "record_type": self.i18n.t("record_type"),
        }
        for field_id in schema_fields:
            field = self.project.schema.get_field(field_id)
            heading_texts[field_id] = field.display_label(self.i18n.language) if field else field_id
        rows = [record.to_flat_dict(self.project.schema) for record in self.project.records]
        for field_id in fields:
            header = heading_texts.get(field_id, field_id)
            self.records_tree.heading(field_id, text=header)
            width = self._measure_text(header) + 36
            for row in rows[:50]:
                width = max(width, min(self._measure_text(row.get(field_id, "")) + 30, 320))
            width = max(90, min(width, 420))
            self.records_tree.column(field_id, width=width, minwidth=width, stretch=False, anchor="w")
        for record, row in zip(self.project.records, rows):
            self.records_tree.insert("", "end", iid=record.record_id, values=[row.get(f, "") for f in fields])
        self.refresh_project_tree()

    def selected_record_id(self) -> str | None:
        sel = self.records_tree.selection()
        return sel[0] if sel else None

    def _on_record_select(self, _event=None) -> None:
        if not self.project or not self.project_active:
            return
        rid = self.selected_record_id()
        record = self.project.get_record(rid) if rid else None
        self.record_editor.load_record(record)
        if record:
            self.show_text("\n".join([f"{k}: {record.get_value(k)}" for k in record.fields]))

    def _on_nav_select(self, _event=None) -> None:
        if not self.project or not self.project_active:
            return
        sel = self.project_tree.selection()
        if not sel:
            return
        item = sel[0]
        if item == "schema":
            self.notebook.select(self.schema_tab)
        elif item == "records":
            self.notebook.select(self.records_tab)
        elif item == "project_info" and self.project:
            p = self.project.project_info
            self.show_text(f"{p.project_name}\n{p.corpus_type}\n{p.created_at}\n{p.updated_at}")

    def show_text(self, text: str) -> None:
        current_state = str(self.details_text.cget("state"))
        if current_state == "disabled":
            self.details_text.configure(state="normal")
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", text)
        if current_state == "disabled":
            self.details_text.configure(state="disabled")

    def show_validation_messages(self, messages) -> None:
        if not messages:
            self.show_text(self.i18n.t("record_valid"))
        else:
            self.show_text("\n".join(f"[{m.level}] {m.item}: {m.message}" for m in messages))

    def log(self, message: str) -> None:
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def update_status(self) -> None:
        if not self.project:
            self.status_var.set(self.i18n.t("status.ready"))
            return
        suffix = " *" if self.project.dirty else ""
        path = str(self.project.file_path) if self.project.file_path else ""
        self.status_var.set(f"{self.project.project_info.project_name}{suffix}  {path}")

    def _mark_changed(self) -> None:
        if self.project:
            self.project.touch()
        self.refresh_records()
        self.update_status()

    def toggle_log(self) -> None:
        self.log_visible = not self.log_visible
        if self.log_visible:
            self.log_text.grid()
        else:
            self.log_text.grid_remove()

    def maximize(self) -> None:
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.attributes("-zoomed", True)

    def restore_window(self) -> None:
        try:
            self.root.state("normal")
        except tk.TclError:
            self.root.attributes("-zoomed", False)
        self.root.geometry("1280x760")
