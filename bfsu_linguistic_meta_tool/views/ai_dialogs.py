"""Dialogs for ChatGPT API settings and metadata extraction."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from i18n import I18N
from llm_metadata import (
    AppSettingsStore,
    ExtractionResult,
    ExtractionWorker,
    LLMSettings,
    SchemaGenerationResult,
    SchemaGenerationWorker,
    apply_extraction_to_record,
    apply_schema_generation_to_project,
    read_pasted_text,
    read_source_file,
    read_webpage,
)
from models import MetadataProject, MetadataRecord


class APISettingsDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, i18n: I18N, store: AppSettingsStore) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.store = store
        self.settings = store.load()
        self.title(i18n.t("ai_settings"))
        self.geometry("620x260")
        self.resizable(True, False)
        self.transient(master)
        self.grab_set()
        self.columnconfigure(1, weight=1)
        self._build()

    def _build(self) -> None:
        pad = {"padx": 12, "pady": 6}
        ttk.Label(self, text=self.i18n.t("chatgpt_api_key")).grid(row=0, column=0, sticky="w", **pad)
        self.key_var = tk.StringVar(value=self.settings.api_key)
        self.key_entry = ttk.Entry(self, textvariable=self.key_var, show="*")
        self.key_entry.grid(row=0, column=1, sticky="ew", **pad)
        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text=self.i18n.t("show_key"), variable=self.show_key_var, command=self._toggle_key).grid(row=0, column=2, sticky="w", **pad)

        ttk.Label(self, text=self.i18n.t("ai_model")).grid(row=1, column=0, sticky="w", **pad)
        self.model_var = tk.StringVar(value=self.settings.model)
        ttk.Entry(self, textvariable=self.model_var).grid(row=1, column=1, columnspan=2, sticky="ew", **pad)

        ttk.Label(self, text=self.i18n.t("api_base_url")).grid(row=2, column=0, sticky="w", **pad)
        self.base_url_var = tk.StringVar(value=self.settings.base_url)
        ttk.Entry(self, textvariable=self.base_url_var).grid(row=2, column=1, columnspan=2, sticky="ew", **pad)

        ttk.Label(self, text=self.i18n.t("max_source_chars")).grid(row=3, column=0, sticky="w", **pad)
        self.max_chars_var = tk.IntVar(value=self.settings.max_source_chars)
        ttk.Entry(self, textvariable=self.max_chars_var).grid(row=3, column=1, columnspan=2, sticky="ew", **pad)

        note = ttk.Label(self, text=self.i18n.t("api_key_note"), wraplength=560, foreground="#666666")
        note.grid(row=4, column=0, columnspan=3, sticky="ew", padx=12, pady=(8, 2))

        bottom = ttk.Frame(self)
        bottom.grid(row=5, column=0, columnspan=3, sticky="e", padx=12, pady=12)
        ttk.Button(bottom, text=self.i18n.t("save"), command=self._save).pack(side="right", padx=4)
        ttk.Button(bottom, text=self.i18n.t("cancel"), command=self.destroy).pack(side="right", padx=4)

    def _toggle_key(self) -> None:
        self.key_entry.configure(show="" if self.show_key_var.get() else "*")

    def _save(self) -> None:
        try:
            max_chars = int(self.max_chars_var.get())
        except Exception:  # noqa: BLE001
            max_chars = 60000
        settings = LLMSettings(
            api_key=self.key_var.get().strip(),
            model=self.model_var.get().strip() or "gpt-5.4-mini-2026-03-17",
            base_url=self.base_url_var.get().strip().rstrip("/") or "https://api.openai.com/v1",
            max_source_chars=max(1000, max_chars),
        )
        self.store.save(settings)
        messagebox.showinfo(self.i18n.t("success"), self.i18n.t("api_key_saved"))
        self.destroy()


class LLMMetadataDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, i18n: I18N, project: MetadataProject, record: MetadataRecord, on_applied) -> None:  # noqa: ANN001
        super().__init__(master)
        self.i18n = i18n
        self.project = project
        self.record = record
        self.on_applied = on_applied
        self.store = AppSettingsStore()
        self.settings = self.store.load()
        self.result: ExtractionResult | None = None
        self.title(i18n.t("ai_extract_metadata"))
        self.geometry("980x680")
        self.transient(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._build()
        if not self.settings.is_configured:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("api_key_required"))

    def _build(self) -> None:
        top = ttk.LabelFrame(self, text=self.i18n.t("input_source"), padding=8)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text=self.i18n.t("select_file")).grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.file_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.file_var).grid(row=0, column=1, sticky="ew", padx=4, pady=3)
        ttk.Button(top, text=self.i18n.t("browse"), command=self.select_file).grid(row=0, column=2, sticky="w", padx=4, pady=3)

        ttk.Label(top, text=self.i18n.t("webpage_url")).grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.url_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.url_var).grid(row=1, column=1, columnspan=2, sticky="ew", padx=4, pady=3)

        ttk.Label(top, text=self.i18n.t("paste_text")).grid(row=2, column=0, sticky="nw", padx=4, pady=3)
        self.pasted_text = tk.Text(top, height=6, wrap="word")
        self.pasted_text.grid(row=2, column=1, columnspan=2, sticky="ew", padx=4, pady=3)

        actions = ttk.Frame(self)
        actions.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(actions, text=self.i18n.t("overwrite_existing"), variable=self.overwrite_var).pack(side="left", padx=4)
        self.status_var = tk.StringVar(value=self.i18n.t("ai_waiting"))
        ttk.Label(actions, textvariable=self.status_var).pack(side="left", padx=16)
        self.extract_btn = ttk.Button(actions, text=self.i18n.t("start_ai_extract"), command=self.start_extract)
        self.apply_all_btn = ttk.Button(actions, text=self.i18n.t("apply_all_suggestions"), command=lambda: self.apply_result(selected_only=False), state="disabled")
        self.apply_selected_btn = ttk.Button(actions, text=self.i18n.t("apply_selected_suggestions"), command=lambda: self.apply_result(selected_only=True), state="disabled")
        self.close_btn = ttk.Button(actions, text=self.i18n.t("close"), command=self.destroy)
        for b in (self.close_btn, self.apply_selected_btn, self.apply_all_btn, self.extract_btn):
            b.pack(side="right", padx=4)

        mid = ttk.Frame(self)
        mid.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        mid.columnconfigure(0, weight=1)
        mid.rowconfigure(0, weight=1)
        columns = ("field_id", "label", "current", "suggested", "confidence", "evidence")
        self.tree = ttk.Treeview(mid, columns=columns, show="headings", selectmode="extended")
        headings = {
            "field_id": "field_id",
            "label": self.i18n.t("schema_fields"),
            "current": self.i18n.t("current_value"),
            "suggested": self.i18n.t("suggested_value"),
            "confidence": self.i18n.t("confidence"),
            "evidence": self.i18n.t("evidence"),
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=130 if col != "evidence" else 320, stretch=True, anchor="w")
        ysb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(mid, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")

        bottom = ttk.LabelFrame(self, text=self.i18n.t("warnings"), padding=4)
        bottom.grid(row=3, column=0, sticky="ew", padx=8, pady=8)
        bottom.columnconfigure(0, weight=1)
        self.warning_text = tk.Text(bottom, height=6, wrap="word")
        self.warning_text.grid(row=0, column=0, sticky="ew")

    def select_file(self) -> None:
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Supported", "*.txt *.md *.csv *.tsv *.json *.xml *.html *.htm *.pdf *.jpg *.jpeg *.png *.webp *.bmp *.gif *.tif *.tiff"),
                ("Text", "*.txt *.md *.csv *.tsv *.json *.xml"),
                ("PDF", "*.pdf"),
                ("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tif *.tiff"),
                ("HTML", "*.html *.htm"),
                ("All files", "*.*"),
            ]
        )
        if filename:
            self.file_var.set(filename)

    def _make_source(self):  # noqa: ANN202
        max_chars = self.settings.max_source_chars
        if self.file_var.get().strip():
            return read_source_file(Path(self.file_var.get().strip()), max_chars=max_chars)
        if self.url_var.get().strip():
            return read_webpage(self.url_var.get().strip(), max_chars=max_chars)
        pasted = self.pasted_text.get("1.0", "end").strip()
        if pasted:
            return read_pasted_text(pasted, max_chars=max_chars)
        raise ValueError(self.i18n.t("no_input_source"))

    def start_extract(self) -> None:
        self.settings = self.store.load()
        if not self.settings.is_configured:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("api_key_required"))
            APISettingsDialog(self, self.i18n, self.store)
            return
        try:
            source = self._make_source()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.extract_btn.configure(state="disabled")
        self.apply_all_btn.configure(state="disabled")
        self.apply_selected_btn.configure(state="disabled")
        self.status_var.set(self.i18n.t("ai_extracting"))
        self.warning_text.delete("1.0", "end")
        self.tree.delete(*self.tree.get_children())
        ExtractionWorker(self.settings, self.project, self.record, source, self._worker_callback).start()

    def _worker_callback(self, result: ExtractionResult | None, error: Exception | None) -> None:
        self.after(0, lambda: self._finish_extract(result, error))

    def _finish_extract(self, result: ExtractionResult | None, error: Exception | None) -> None:
        self.extract_btn.configure(state="normal")
        if error:
            self.status_var.set(self.i18n.t("ai_failed"))
            messagebox.showerror(self.i18n.t("error"), str(error))
            return
        self.result = result
        self.populate_result()
        self.status_var.set(self.i18n.t("ai_done"))
        self.apply_all_btn.configure(state="normal" if result and result.fields else "disabled")
        self.apply_selected_btn.configure(state="normal" if result and result.fields else "disabled")

    def populate_result(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.warning_text.delete("1.0", "end")
        if not self.result:
            return
        for field_id, extracted in self.result.fields.items():
            field = self.project.schema.get_field(field_id)
            label = field.display_label(self.i18n.language) if field else field_id
            current = self.record.get_value(field_id)
            value = extracted.value
            if isinstance(value, list):
                value_text = "; ".join(str(x) for x in value)
            else:
                value_text = str(value)
            self.tree.insert(
                "",
                "end",
                iid=field_id,
                values=(field_id, label, current, value_text, f"{extracted.confidence:.2f}", extracted.evidence),
            )
        warnings = list(self.result.warnings)
        if self.result.unmapped_candidates:
            warnings.append(self.i18n.t("unmapped_candidates") + ":")
            for item in self.result.unmapped_candidates[:20]:
                warnings.append(f"- {item.get('label', '')}: {item.get('value', '')}")
        self.warning_text.insert("1.0", "\n".join(warnings))

    def apply_result(self, selected_only: bool = False) -> None:
        if not self.result:
            return
        selected = set(self.tree.selection()) if selected_only else None
        if selected_only and not selected:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("select_suggestions_first"))
            return
        count = apply_extraction_to_record(self.project, self.record, self.result, overwrite=self.overwrite_var.get(), selected_field_ids=selected)
        messagebox.showinfo(self.i18n.t("success"), self.i18n.t("ai_applied", count=count))
        if self.on_applied:
            self.on_applied(self.record)


class LLMSchemaDialog(tk.Toplevel):
    """AI-assisted schema generation and extension dialog.

    The model never writes directly to the project. Suggestions are shown in a
    table first, and the user decides whether to apply all or selected fields.
    """

    def __init__(self, master: tk.Misc, i18n: I18N, project: MetadataProject, on_applied, mode: str = "extend_current_schema") -> None:  # noqa: ANN001
        super().__init__(master)
        self.i18n = i18n
        self.project = project
        self.on_applied = on_applied
        self.mode = mode if mode in {"generate_new_schema", "extend_current_schema"} else "extend_current_schema"
        self.store = AppSettingsStore()
        self.settings = self.store.load()
        self.result: SchemaGenerationResult | None = None
        self.title(self.i18n.t("ai_schema_title"))
        self.geometry("1100x740")
        self.transient(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._build()
        if not self.settings.is_configured:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("api_key_required"))

    def _build(self) -> None:
        mode_frame = ttk.LabelFrame(self, text=self.i18n.t("ai_schema_mode"), padding=8)
        mode_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.mode_var = tk.StringVar(value=self.mode)
        ttk.Radiobutton(mode_frame, text=self.i18n.t("ai_generate_new_schema"), value="generate_new_schema", variable=self.mode_var).pack(side="left", padx=8)
        ttk.Radiobutton(mode_frame, text=self.i18n.t("ai_extend_current_schema"), value="extend_current_schema", variable=self.mode_var).pack(side="left", padx=8)
        self.replace_existing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(mode_frame, text=self.i18n.t("allow_replace_existing_fields"), variable=self.replace_existing_var).pack(side="right", padx=8)

        req = ttk.LabelFrame(self, text=self.i18n.t("schema_requirements"), padding=8)
        req.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        req.columnconfigure(0, weight=1)
        self.requirements_text = tk.Text(req, height=5, wrap="word")
        self.requirements_text.grid(row=0, column=0, sticky="ew")
        self.requirements_text.insert("1.0", self.i18n.t("schema_requirements_placeholder"))

        top = ttk.LabelFrame(self, text=self.i18n.t("optional_reference_source"), padding=8)
        top.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text=self.i18n.t("select_file")).grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.file_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.file_var).grid(row=0, column=1, sticky="ew", padx=4, pady=3)
        ttk.Button(top, text=self.i18n.t("browse"), command=self.select_file).grid(row=0, column=2, sticky="w", padx=4, pady=3)
        ttk.Label(top, text=self.i18n.t("webpage_url")).grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.url_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.url_var).grid(row=1, column=1, columnspan=2, sticky="ew", padx=4, pady=3)
        ttk.Label(top, text=self.i18n.t("paste_text")).grid(row=2, column=0, sticky="nw", padx=4, pady=3)
        self.pasted_text = tk.Text(top, height=4, wrap="word")
        self.pasted_text.grid(row=2, column=1, columnspan=2, sticky="ew", padx=4, pady=3)

        mid = ttk.Frame(self)
        mid.grid(row=3, column=0, sticky="nsew", padx=8, pady=4)
        mid.columnconfigure(0, weight=1)
        mid.rowconfigure(0, weight=1)
        columns = ("action", "field_id", "label_zh", "label_en", "data_type", "required", "repeatable", "level", "controlled_values", "confidence", "rationale")
        self.tree = ttk.Treeview(mid, columns=columns, show="headings", selectmode="extended")
        widths = {
            "action": 90,
            "field_id": 150,
            "label_zh": 130,
            "label_en": 160,
            "data_type": 100,
            "required": 80,
            "repeatable": 80,
            "level": 90,
            "controlled_values": 220,
            "confidence": 90,
            "rationale": 360,
        }
        for col in columns:
            self.tree.heading(col, text=self.i18n.t(col) if col in {"required", "repeatable", "level", "controlled_values"} else col)
            self.tree.column(col, width=widths.get(col, 120), stretch=True, anchor="w")
        ysb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(mid, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")

        actions = ttk.Frame(self)
        actions.grid(row=4, column=0, sticky="ew", padx=8, pady=4)
        self.status_var = tk.StringVar(value=self.i18n.t("ai_waiting"))
        ttk.Label(actions, textvariable=self.status_var).pack(side="left", padx=4)
        self.start_btn = ttk.Button(actions, text=self.i18n.t("start_ai_schema"), command=self.start_generate)
        self.apply_all_btn = ttk.Button(actions, text=self.i18n.t("apply_all_suggestions"), command=lambda: self.apply_schema(selected_only=False), state="disabled")
        self.apply_selected_btn = ttk.Button(actions, text=self.i18n.t("apply_selected_suggestions"), command=lambda: self.apply_schema(selected_only=True), state="disabled")
        self.close_btn = ttk.Button(actions, text=self.i18n.t("close"), command=self.destroy)
        for b in (self.close_btn, self.apply_selected_btn, self.apply_all_btn, self.start_btn):
            b.pack(side="right", padx=4)

        bottom = ttk.LabelFrame(self, text=self.i18n.t("warnings"), padding=4)
        bottom.grid(row=5, column=0, sticky="ew", padx=8, pady=8)
        bottom.columnconfigure(0, weight=1)
        self.warning_text = tk.Text(bottom, height=5, wrap="word")
        self.warning_text.grid(row=0, column=0, sticky="ew")

    def select_file(self) -> None:
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Supported", "*.txt *.md *.csv *.tsv *.json *.xml *.html *.htm *.pdf *.jpg *.jpeg *.png *.webp *.bmp *.gif *.tif *.tiff"),
                ("Text", "*.txt *.md *.csv *.tsv *.json *.xml"),
                ("PDF", "*.pdf"),
                ("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tif *.tiff"),
                ("HTML", "*.html *.htm"),
                ("All files", "*.*"),
            ]
        )
        if filename:
            self.file_var.set(filename)

    def _make_source(self):  # noqa: ANN202
        max_chars = self.settings.max_source_chars
        if self.file_var.get().strip():
            return read_source_file(Path(self.file_var.get().strip()), max_chars=max_chars)
        if self.url_var.get().strip():
            return read_webpage(self.url_var.get().strip(), max_chars=max_chars)
        pasted = self.pasted_text.get("1.0", "end").strip()
        if pasted:
            return read_pasted_text(pasted, max_chars=max_chars)
        return read_pasted_text("", max_chars=max_chars)

    def start_generate(self) -> None:
        self.settings = self.store.load()
        if not self.settings.is_configured:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("api_key_required"))
            APISettingsDialog(self, self.i18n, self.store)
            return
        requirements = self.requirements_text.get("1.0", "end").strip()
        if not requirements:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("schema_requirements_required"))
            return
        try:
            source = self._make_source()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.start_btn.configure(state="disabled")
        self.apply_all_btn.configure(state="disabled")
        self.apply_selected_btn.configure(state="disabled")
        self.status_var.set(self.i18n.t("ai_schema_generating"))
        self.warning_text.delete("1.0", "end")
        self.tree.delete(*self.tree.get_children())
        SchemaGenerationWorker(self.settings, self.project, self.mode_var.get(), requirements, source, self._worker_callback).start()

    def _worker_callback(self, result: SchemaGenerationResult | None, error: Exception | None) -> None:
        self.after(0, lambda: self._finish_generate(result, error))

    def _finish_generate(self, result: SchemaGenerationResult | None, error: Exception | None) -> None:
        self.start_btn.configure(state="normal")
        if error:
            self.status_var.set(self.i18n.t("ai_failed"))
            messagebox.showerror(self.i18n.t("error"), str(error))
            return
        self.result = result
        self.populate_result()
        self.status_var.set(self.i18n.t("ai_schema_done"))
        self.apply_all_btn.configure(state="normal" if result and result.candidates else "disabled")
        self.apply_selected_btn.configure(state="normal" if result and result.candidates else "disabled")

    def populate_result(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.warning_text.delete("1.0", "end")
        if not self.result:
            return
        for candidate in self.result.candidates:
            f = candidate.field
            controlled = "; ".join(f.controlled_values)
            self.tree.insert(
                "",
                "end",
                iid=f.field_id,
                values=(
                    candidate.action,
                    f.field_id,
                    f.label_zh,
                    f.label_en,
                    f.data_type,
                    "✓" if f.required else "",
                    "✓" if f.repeatable else "",
                    f.level,
                    controlled,
                    f"{candidate.confidence:.2f}",
                    candidate.rationale,
                ),
            )
        warnings = list(self.result.warnings)
        if self.result.mode == "generate_new_schema":
            warnings.insert(0, self.i18n.t("generate_schema_warning"))
        self.warning_text.insert("1.0", "\n".join(warnings))

    def apply_schema(self, selected_only: bool = False) -> None:
        if not self.result:
            return
        selected = set(self.tree.selection()) if selected_only else None
        if selected_only and not selected:
            messagebox.showwarning(self.i18n.t("warning"), self.i18n.t("select_suggestions_first"))
            return
        if self.result.mode == "generate_new_schema":
            if not messagebox.askyesno(self.i18n.t("confirm"), self.i18n.t("confirm_replace_schema")):
                return
        count = apply_schema_generation_to_project(
            self.project,
            self.result,
            selected_field_ids=selected,
            replace_existing=self.replace_existing_var.get(),
        )
        messagebox.showinfo(self.i18n.t("success"), self.i18n.t("ai_schema_applied", count=count))
        if self.on_applied:
            self.on_applied(self.project)
