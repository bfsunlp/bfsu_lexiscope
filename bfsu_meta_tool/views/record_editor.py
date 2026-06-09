"""Record editor view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from i18n import I18N
from models import MetadataProject, MetadataRecord
from validators import validate_record


class RecordEditor(ttk.Frame):
    """Dynamic record editor generated from the active schema."""

    def __init__(self, master: tk.Misc, i18n: I18N, on_change=None, on_validate=None) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.on_change = on_change
        self.on_validate = on_validate
        self.project: MetadataProject | None = None
        self.current_record: MetadataRecord | None = None
        self.inputs: dict[str, object] = {}
        self.enabled = False
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.save_btn = ttk.Button(toolbar, command=self.save_current)
        self.validate_btn = ttk.Button(toolbar, command=self.validate_current)
        self.save_btn.pack(side="left", padx=2)
        self.validate_btn.pack(side="left", padx=2)

        container = ttk.Frame(self)
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(container, highlightthickness=0)
        self.form_frame = ttk.Frame(self.canvas)
        ysb = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=ysb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.form_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.canvas_window, width=e.width))
        self.refresh_language()
        self.set_enabled(False)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        state = "normal" if enabled else "disabled"
        self.save_btn.configure(state=state)
        self.validate_btn.configure(state=state)
        self._set_children_state(self.form_frame, enabled)

    def _set_children_state(self, widget: tk.Widget, enabled: bool) -> None:
        for child in widget.winfo_children():
            try:
                child.configure(state="normal" if enabled else "disabled")
            except tk.TclError:
                pass
            self._set_children_state(child, enabled)

    def clear(self) -> None:
        self.project = None
        self.current_record = None
        self.inputs.clear()
        for child in self.form_frame.winfo_children():
            child.destroy()
        self.set_enabled(False)

    def refresh_language(self) -> None:
        self.save_btn.configure(text=self.i18n.t("save_record"))
        self.validate_btn.configure(text=self.i18n.t("validate"))

    def load_project(self, project: MetadataProject) -> None:
        self.project = project
        self.set_enabled(True)
        self.load_record(project.records[0] if project.records else None)

    def load_record(self, record: MetadataRecord | None) -> None:
        self.current_record = record
        self._build_form()

    def _build_form(self) -> None:
        for child in self.form_frame.winfo_children():
            child.destroy()
        self.inputs.clear()
        if not self.project or not self.enabled:
            return
        row = 0
        ttk.Label(self.form_frame, text=self.i18n.t("record_id")).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        self.record_id_var = tk.StringVar(value=self.current_record.record_id if self.current_record else "")
        ttk.Entry(self.form_frame, textvariable=self.record_id_var).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        row += 1
        ttk.Label(self.form_frame, text=self.i18n.t("record_type")).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        self.record_type_var = tk.StringVar(value=self.current_record.record_type if self.current_record else "text")
        ttk.Entry(self.form_frame, textvariable=self.record_type_var).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        row += 1
        self.form_frame.columnconfigure(1, weight=1)
        lang = self.i18n.language
        for field in self.project.schema.sorted_fields(visible_only=True):
            label = field.display_label(lang) + (" *" if field.required else "")
            ttk.Label(self.form_frame, text=label).grid(row=row, column=0, sticky="nw", padx=8, pady=4)
            values = self.current_record.get_values(field.field_id) if self.current_record else []
            value = "; ".join(values) if values else field.default_value
            if field.data_type == "long_text":
                widget = tk.Text(self.form_frame, height=4, wrap="word")
                widget.insert("1.0", value)
                widget.configure(state="normal" if field.editable else "disabled")
            elif field.data_type == "enum":
                var = tk.StringVar(value=value)
                widget = ttk.Combobox(self.form_frame, textvariable=var, values=field.controlled_values, state="readonly" if field.controlled_values else "normal")
                self.inputs[field.field_id] = var
            elif field.data_type == "boolean":
                var = tk.BooleanVar(value=str(value).lower() in {"true", "1", "yes", "是"})
                widget = ttk.Checkbutton(self.form_frame, variable=var)
                self.inputs[field.field_id] = var
            else:
                var = tk.StringVar(value=value)
                widget = ttk.Entry(self.form_frame, textvariable=var)
                if not field.editable:
                    widget.configure(state="disabled")
                self.inputs[field.field_id] = var
            widget.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
            if field.data_type == "long_text":
                self.inputs[field.field_id] = widget
            if field.description_zh or field.description_en:
                desc = field.description_zh if lang.startswith("zh") else field.description_en
                ttk.Label(self.form_frame, text=desc, foreground="#666666", wraplength=520).grid(row=row + 1, column=1, sticky="w", padx=8, pady=(0, 4))
                row += 1
            row += 1

    def save_current(self) -> MetadataRecord | None:
        if not self.project or not self.enabled:
            return None
        if not self.current_record:
            self.current_record = MetadataRecord()
            self.project.add_record(self.current_record)
        new_id = self.record_id_var.get().strip() or self.current_record.record_id
        if new_id != self.current_record.record_id and self.project.get_record(new_id):
            new_id = self.project.ensure_unique_record_id(new_id)
        self.current_record.record_id = new_id
        self.current_record.record_type = self.record_type_var.get().strip() or "text"
        for field in self.project.schema.fields:
            widget_or_var = self.inputs.get(field.field_id)
            if widget_or_var is None:
                continue
            if isinstance(widget_or_var, tk.Text):
                value = widget_or_var.get("1.0", "end").strip()
            elif isinstance(widget_or_var, tk.BooleanVar):
                value = "true" if widget_or_var.get() else "false"
            else:
                value = str(widget_or_var.get())  # type: ignore[attr-defined]
            if field.repeatable and ";" in value:
                self.current_record.set_value(field.field_id, [x.strip() for x in value.split(";")])
            else:
                self.current_record.set_value(field.field_id, value)
        self.project.touch()
        if self.on_change:
            self.on_change()
        return self.current_record

    def validate_current(self) -> None:
        record = self.save_current()
        if not record or not self.project:
            return
        messages = validate_record(record, self.project.schema)
        if self.on_validate:
            self.on_validate(messages)
