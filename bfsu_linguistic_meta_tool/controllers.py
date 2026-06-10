"""Application controller layer.

The controller connects views to business logic and persistence. GUI widgets do
not directly read/write XML or Excel; they delegate to this module.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tkinter as tk
import sys
from tkinter import filedialog, messagebox, ttk

from excel_importer import ExcelImporter
from i18n import I18N
from models import MetadataProject, MetadataRecord, MetadataSchema
from schema_manager import load_schema_xml, save_schema_xml
from validators import validate_record, validate_schema
from views.import_dialogs import ExcelImportDialog, XMLImportDialog
from views.ai_dialogs import APISettingsDialog, LLMMetadataDialog, LLMSchemaDialog
from llm_metadata import AppSettingsStore
from utils import slugify
from xml_repository import XMLRepository


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = app_base_dir()
SCHEMA_DIR = APP_DIR / "Schema"


def ensure_schema_library() -> Path:
    """Create/return the application-level Schema library folder.

    All bundled and user-created schema files live under APP_DIR/Schema.
    Root-level schema XML files are intentionally ignored to avoid duplicate root-level defaults.
    """
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    return SCHEMA_DIR


class SchemaLibrary:
    """In-memory cache for the application-level Schema/ folder."""

    def __init__(self) -> None:
        self.items: list[tuple[str, Path, MetadataSchema, str]] = []
        self.refresh()

    def refresh(self) -> None:
        ensure_schema_library()
        self.items.clear()
        for path in sorted(SCHEMA_DIR.glob("*.xml")):
            try:
                schema = load_schema_xml(path)
            except Exception:
                continue
            corpus_type = infer_corpus_type_from_schema(path, schema)
            display = f"{schema.schema_name} — {path.name}"
            self.items.append((display, path, schema, corpus_type))


def save_schema_to_library(schema: MetadataSchema, preferred_name: str | None = None) -> Path:
    ensure_schema_library()
    stem = slugify(preferred_name or schema.schema_name or "custom_schema", fallback="custom_schema")
    if not stem.endswith("schema"):
        stem = f"{stem}_schema"
    path = SCHEMA_DIR / f"{stem}.xml"
    if path.exists():
        path = SCHEMA_DIR / f"{stem}_{len(list(SCHEMA_DIR.glob(stem + '*.xml'))) + 1}.xml"
    save_schema_xml(schema, path)
    return path


def infer_corpus_type_from_schema(path: Path, schema: MetadataSchema) -> str:
    """Infer a compatible internal corpus_type from the selected Schema file."""
    text = f"{schema.schema_name} {path.stem}".lower()
    for candidate in (
        "multiple_translations",
        "multilingual_parallel",
        "bilingual_parallel",
        "monolingual",
        "comparable",
        "learner",
        "spoken",
    ):
        if candidate in text:
            return candidate
    return "custom"


class NewProjectDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, i18n: I18N, schema_library: SchemaLibrary | None = None) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.schema_library = schema_library or SchemaLibrary()
        self.result: tuple[str, MetadataSchema | None, Path | None, str] | None = None
        self.schema_items: list[tuple[str, MetadataSchema | None, Path | None, str]] = []
        self.title(i18n.t("new_project"))
        self.geometry("520x220")
        self.resizable(True, False)
        self.transient(master)
        self.grab_set()
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text=i18n.t("project_name")).grid(row=0, column=0, sticky="w", padx=12, pady=12)
        self.name_var = tk.StringVar(value="Untitled Metadata Project")
        ttk.Entry(self, textvariable=self.name_var).grid(row=0, column=1, sticky="ew", padx=12, pady=12)
        ttk.Label(self, text=i18n.t("schema_select")).grid(row=1, column=0, sticky="w", padx=12, pady=12)
        self.schema_var = tk.StringVar()
        self.schema_combo = ttk.Combobox(self, textvariable=self.schema_var, state="readonly")
        self.schema_combo.grid(row=1, column=1, sticky="ew", padx=12, pady=12)
        bottom = ttk.Frame(self)
        bottom.grid(row=2, column=0, columnspan=2, sticky="e", padx=12, pady=12)
        ttk.Button(bottom, text=i18n.t("create"), command=self._ok).pack(side="right", padx=4)
        ttk.Button(bottom, text=i18n.t("cancel"), command=self.destroy).pack(side="right", padx=4)
        self._load_schema_items()

    def _load_schema_items(self) -> None:
        self.schema_items.clear()
        for display, path, schema, corpus_type in self.schema_library.items:
            self.schema_items.append((display, schema, path, corpus_type))
        if not self.schema_items:
            self.schema_items.append((self.i18n.t("empty_schema"), None, None, "custom"))
        values = [item[0] for item in self.schema_items]
        self.schema_combo.configure(values=values)
        self.schema_var.set(values[0])

    def _ok(self) -> None:
        name = self.name_var.get().strip() or "Untitled Metadata Project"
        selected = self.schema_var.get()
        for display, schema, path, corpus_type in self.schema_items:
            if display == selected:
                self.result = (name, deepcopy(schema) if schema else None, path, corpus_type)
                break
        if self.result is None:
            self.result = (name, None, None, "custom")
        self.destroy()


class MetadataController:
    def __init__(self, root: tk.Tk, window, i18n: I18N) -> None:
        self.root = root
        self.window = window
        self.i18n = i18n
        self.repository = XMLRepository()
        self.excel = ExcelImporter()
        self.settings_store = AppSettingsStore()
        self.schema_library = SchemaLibrary()
        self.project: MetadataProject | None = None
        ensure_schema_library()
        self.window.set_controller(self)
        self.window.clear_project()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _require_project(self) -> MetadataProject | None:
        if self.project is None:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("no_active_project"))
            return None
        return self.project

    def new_project(self) -> None:
        if not self._confirm_unsaved():
            return
        self.schema_library.refresh()
        dlg = NewProjectDialog(self.root, self.i18n, self.schema_library)
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        name, schema, schema_path, corpus_type = dlg.result
        schema = schema if schema else MetadataSchema(schema_name=self.i18n.t("empty_schema"))
        self.project = self.repository.new_project(name, corpus_type, schema, self.i18n.language)
        self.window.load_project(self.project)
        schema_label = schema_path.name if schema_path else self.i18n.t("empty_schema")
        self.window.log(f"New project: {name} | Schema: {schema_label}")

    def open_project(self) -> None:
        if not self._confirm_unsaved():
            return
        filename = filedialog.askopenfilename(filetypes=[("*.xml", "*.xml"), ("*.*", "*.*")])
        if not filename:
            return
        try:
            self.project = self.repository.load_project(Path(filename))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.i18n.set_language(self.project.project_info.interface_language)
        self.window.load_project(self.project)
        self.window.refresh_language()
        self.window.log(f"Opened: {filename}")

    def save_project(self) -> None:
        project = self._require_project()
        if not project:
            return
        if project.file_path:
            self._save_to(project.file_path)
        else:
            self.save_project_as()

    def save_project_as(self) -> None:
        project = self._require_project()
        if not project:
            return
        filename = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("*.xml", "*.xml")])
        if filename:
            self._save_to(Path(filename))

    def _save_to(self, path: Path) -> None:
        project = self._require_project()
        if not project:
            return
        try:
            self.repository.save_project(project, path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), f"{path}\n{exc}")
            return
        self.window.update_status()
        self.window.log(f"Saved: {path}")

    def export_xml(self) -> None:
        self.export_records_xml()

    def export_records_xml(self) -> None:
        project = self._require_project()
        if not project:
            return
        filename = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("*.xml", "*.xml")])
        if not filename:
            return
        try:
            self.repository.export_records_xml(project, Path(filename))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.window.log(f"Records XML exported: {filename}")


    def save_schema_to_library(self) -> None:
        project = self._require_project()
        if not project:
            return
        try:
            path = save_schema_to_library(project.schema, project.schema.schema_name)
            self.schema_library.refresh()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.window.log(f"Schema saved to library: {path}")
        messagebox.showinfo(self.i18n.t("success"), self.i18n.t("schema_saved_to_library", path=path))

    def export_schema(self) -> None:
        project = self._require_project()
        if not project:
            return
        ensure_schema_library()
        default_name = slugify(project.schema.schema_name or "custom_schema", fallback="custom_schema") + ".xml"
        filename = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("*.xml", "*.xml")],
            initialdir=str(SCHEMA_DIR),
            initialfile=default_name,
        )
        if not filename:
            return
        try:
            self.repository.export_schema(project, Path(filename))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.schema_library.refresh()
        self.window.log(f"Schema exported: {filename}")

    def export_records_csv(self) -> None:
        project = self._require_project()
        if not project:
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("*.csv", "*.csv")])
        if not filename:
            return
        try:
            self.excel.export_records_csv(project, Path(filename))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.window.log(f"Records CSV exported: {filename}")

    def export_records_excel(self) -> None:
        project = self._require_project()
        if not project:
            return
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("*.xlsx", "*.xlsx")])
        if not filename:
            return
        try:
            self.excel.export_records_excel(project, Path(filename))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.window.log(f"Records Excel exported: {filename}")

    def import_excel(self) -> None:
        project = self._require_project()
        if not project:
            return
        ExcelImportDialog(self.root, self.i18n, project, self._after_import)

    def import_xml(self) -> None:
        project = self._require_project()
        if not project:
            return
        XMLImportDialog(self.root, self.i18n, project, self._after_import)

    def import_schema(self) -> None:
        project = self._require_project()
        if not project:
            return
        filename = filedialog.askopenfilename(filetypes=[("*.xml", "*.xml"), ("*.*", "*.*")])
        if not filename:
            return
        try:
            schema = load_schema_xml(Path(filename))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        project.schema = schema
        project.touch()
        try:
            saved_path = save_schema_to_library(schema, Path(filename).stem)
            self.schema_library.refresh()
            self.window.log(f"Schema saved to library: {saved_path}")
        except Exception as exc:  # noqa: BLE001
            self.window.log(f"Schema library save failed: {exc}")
        self.window.load_project(project)
        self.window.log(f"Schema imported: {filename}")

    def new_schema(self) -> None:
        project = self._require_project()
        if not project:
            return
        if messagebox.askyesno(self.i18n.t("confirm"), self.i18n.t("replace_with_empty_schema")):
            project.schema = MetadataSchema(schema_name=self.i18n.t("empty_schema"))
            project.touch()
            self.window.load_project(project)

    def validate_schema(self) -> None:
        project = self._require_project()
        if not project:
            return
        messages = validate_schema(project.schema)
        self.window.show_validation_messages(messages)
        messagebox.showinfo(self.i18n.t("message"), self.i18n.t("schema_valid") if not messages else self.i18n.t("validation_failed"))

    def new_record(self) -> None:
        project = self._require_project()
        if not project:
            return
        record = MetadataRecord()
        for field in project.schema.fields:
            if field.default_value:
                record.set_value(field.field_id, field.default_value)
        project.add_record(record)
        self.window.load_project(project)
        self.window.records_tree.selection_set(record.record_id)
        self.window.notebook.select(self.window.record_edit_tab)

    def delete_selected_record(self) -> None:
        project = self._require_project()
        if not project:
            return
        rid = self.window.selected_record_id()
        if not rid:
            return
        if not messagebox.askyesno(self.i18n.t("confirm"), f"Delete record {rid}?"):
            return
        project.remove_record(rid)
        self.window.load_project(project)

    def copy_selected_record(self) -> None:
        project = self._require_project()
        if not project:
            return
        rid = self.window.selected_record_id()
        if not rid:
            return
        record = project.get_record(rid)
        if not record:
            return
        copied = deepcopy(record)
        copied.record_id = project.ensure_unique_record_id(f"{record.record_id}_copy")
        project.add_record(copied)
        self.window.load_project(project)
        self.window.records_tree.selection_set(copied.record_id)

    def validate_selected_record(self) -> None:
        project = self._require_project()
        if not project:
            return
        rid = self.window.selected_record_id()
        if not rid:
            return
        record = project.get_record(rid)
        if not record:
            return
        self.window.show_validation_messages(validate_record(record, project.schema))

    def open_ai_settings(self) -> None:
        APISettingsDialog(self.root, self.i18n, self.settings_store)

    def recognize_metadata_for_current_record(self) -> None:
        project = self._require_project()
        if not project:
            return
        self.window.notebook.select(self.window.record_edit_tab)
        record = self.window.record_editor.save_current()
        if not record:
            record = MetadataRecord()
            project.add_record(record)
        self.window.records_tree.selection_set(record.record_id)

        def _after_applied(updated_record: MetadataRecord) -> None:
            project.touch()
            self.window.refresh_records()
            self.window.records_tree.selection_set(updated_record.record_id)
            self.window.record_editor.load_record(updated_record)
            self.window.update_status()
            self.window.log(f"AI metadata suggestions applied to record: {updated_record.record_id}")

        LLMMetadataDialog(self.root, self.i18n, project, record, _after_applied)


    def design_schema_with_ai(self, mode: str = "extend_current_schema") -> None:
        project = self._require_project()
        if not project:
            return

        def _after_schema_applied(updated_project: MetadataProject) -> None:
            updated_project.touch()
            try:
                saved_path = save_schema_to_library(updated_project.schema, updated_project.schema.schema_name)
                self.schema_library.refresh()
                self.window.log(f"AI schema saved to library: {saved_path}")
            except Exception as exc:  # noqa: BLE001
                self.window.log(f"AI schema library save failed: {exc}")
            self.window.load_project(updated_project)
            self.window.notebook.select(self.window.schema_tab)
            self.window.update_status()
            self.window.log(f"AI schema suggestions applied: {updated_project.schema.schema_name}")

        LLMSchemaDialog(self.root, self.i18n, project, _after_schema_applied, mode=mode)

    def _after_import(self) -> None:
        project = self._require_project()
        if not project:
            return
        project.touch()
        self.window.load_project(project)
        self.window.update_status()

    def change_language(self, language: str) -> None:
        self.i18n.set_language(language)
        if self.project:
            self.project.project_info.interface_language = language
            self.project.touch()
        self.window.refresh_language()
        self.window.update_status()

    def close_project(self) -> None:
        if self.project is None:
            self.window.clear_project()
            return
        project_name = self.project.project_info.project_name
        if not self._confirm_unsaved():
            return
        self.project = None
        self.window.clear_project()
        self.window.log(f"Closed project: {project_name}")

    def show_guide(self) -> None:
        guide = (
            "1. Create or open a metadata project.\n"
            "2. Edit the schema first: fields, XML tags, required flags and controlled vocabularies.\n"
            "3. Add records manually or import Excel/XML metadata.\n"
            "4. Optional: set ChatGPT API Key in Settings, then use AI-assisted metadata extraction in the Record Editor.\n"
            "5. Optional: use Schema → AI-generate New Schema or AI-extend Current Schema, review suggestions, and apply selected fields.\n"
            "6. Validate schema/records before exporting.\n"
            "7. Save the project as unified UTF-8 XML."
        )
        messagebox.showinfo(self.i18n.t("user_guide"), guide)

    def show_about(self) -> None:
        messagebox.showinfo(self.i18n.t("about"), self.i18n.t("about_text"))

    def close(self) -> None:
        if self._confirm_unsaved():
            self.root.destroy()

    def _confirm_unsaved(self) -> bool:
        if not self.project or not self.project.dirty:
            return True
        ans = messagebox.askyesnocancel(self.i18n.t("confirm"), self.i18n.t("unsaved_prompt"))
        if ans is None:
            return False
        if ans:
            self.save_project()
            return bool(self.project and not self.project.dirty)
        return True
