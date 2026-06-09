"""Schema editor view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from i18n import I18N
from models import DATA_TYPES, FIELD_LEVELS, MetadataField, MetadataSchema


class SchemaEditor(ttk.Frame):
    """Table-like editor for metadata schema fields."""

    COLUMNS = [
        "field_id",
        "label_zh",
        "label_en",
        "xml_tag",
        "data_type",
        "required",
        "repeatable",
        "level",
        "controlled_values",
        "sensitive",
    ]

    def __init__(self, master: tk.Misc, i18n: I18N, on_change=None) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.on_change = on_change
        self.schema: MetadataSchema | None = None
        self.enabled = False
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.add_btn = ttk.Button(toolbar, command=self.add_field)
        self.del_btn = ttk.Button(toolbar, command=self.delete_selected)
        self.up_btn = ttk.Button(toolbar, command=lambda: self.move_selected(-1))
        self.down_btn = ttk.Button(toolbar, command=lambda: self.move_selected(1))
        self.apply_btn = ttk.Button(toolbar, command=self.apply_selected)
        for btn in (self.add_btn, self.del_btn, self.up_btn, self.down_btn, self.apply_btn):
            btn.pack(side="left", padx=2)

        self.tree = ttk.Treeview(self, columns=self.COLUMNS, show="headings", selectmode="browse", height=12)
        ysb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(4, 0), pady=(0, 4))
        ysb.grid(row=1, column=1, sticky="ns", pady=(0, 4))
        xsb.grid(row=2, column=0, sticky="ew", padx=4)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        detail = ttk.LabelFrame(self, text="Field")
        detail.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        for i in range(4):
            detail.columnconfigure(i, weight=1)
        self.vars: dict[str, tk.Variable] = {}
        fields = [
            ("field_id", tk.StringVar()), ("label_zh", tk.StringVar()), ("label_en", tk.StringVar()), ("xml_tag", tk.StringVar()),
            ("data_type", tk.StringVar()), ("level", tk.StringVar()), ("parent", tk.StringVar()), ("order", tk.IntVar(value=0)),
            ("required", tk.BooleanVar()), ("repeatable", tk.BooleanVar()), ("visible", tk.BooleanVar(value=True)), ("editable", tk.BooleanVar(value=True)),
            ("sensitive", tk.BooleanVar()), ("default_value", tk.StringVar()), ("controlled_values", tk.StringVar()),
            ("validation_rule", tk.StringVar()), ("example", tk.StringVar()),
        ]
        for key, var in fields:
            self.vars[key] = var

        row = 0
        for idx, key in enumerate(["field_id", "label_zh", "label_en", "xml_tag", "data_type", "level", "parent", "order"]):
            ttk.Label(detail, text=key).grid(row=row, column=(idx % 4) * 2, sticky="w", padx=4, pady=2)
            if key == "data_type":
                widget = ttk.Combobox(detail, textvariable=self.vars[key], values=DATA_TYPES, state="readonly")
            elif key == "level":
                widget = ttk.Combobox(detail, textvariable=self.vars[key], values=FIELD_LEVELS, state="readonly")
            else:
                widget = ttk.Entry(detail, textvariable=self.vars[key])
            widget.grid(row=row, column=(idx % 4) * 2 + 1, sticky="ew", padx=4, pady=2)
            if idx % 4 == 3:
                row += 1
        for idx, key in enumerate(["required", "repeatable", "visible", "editable", "sensitive"]):
            ttk.Checkbutton(detail, text=key, variable=self.vars[key]).grid(row=row, column=idx, sticky="w", padx=4, pady=2)
        row += 1
        for key in ["default_value", "controlled_values", "validation_rule", "example"]:
            ttk.Label(detail, text=key).grid(row=row, column=0, sticky="w", padx=4, pady=2)
            ttk.Entry(detail, textvariable=self.vars[key]).grid(row=row, column=1, columnspan=7, sticky="ew", padx=4, pady=2)
            row += 1
        ttk.Label(detail, text="description_zh").grid(row=row, column=0, sticky="nw", padx=4, pady=2)
        self.desc_zh = tk.Text(detail, height=3, wrap="word")
        self.desc_zh.grid(row=row, column=1, columnspan=7, sticky="ew", padx=4, pady=2)
        row += 1
        ttk.Label(detail, text="description_en").grid(row=row, column=0, sticky="nw", padx=4, pady=2)
        self.desc_en = tk.Text(detail, height=3, wrap="word")
        self.desc_en.grid(row=row, column=1, columnspan=7, sticky="ew", padx=4, pady=2)

        self.refresh_language()
        self.set_enabled(False)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        state = "normal" if enabled else "disabled"
        for btn in (self.add_btn, self.del_btn, self.up_btn, self.down_btn, self.apply_btn):
            btn.configure(state=state)
        try:
            self.tree.state(["!disabled"] if enabled else ["disabled"])
        except tk.TclError:
            pass
        self._set_children_state(self, enabled)
        if not enabled:
            self.tree.delete(*self.tree.get_children())
            self._clear_form()

    def _set_children_state(self, widget: tk.Widget, enabled: bool) -> None:
        for child in widget.winfo_children():
            if child in {self.tree, self.add_btn, self.del_btn, self.up_btn, self.down_btn, self.apply_btn}:
                continue
            try:
                if isinstance(child, ttk.Combobox):
                    child.configure(state="readonly" if enabled else "disabled")
                else:
                    child.configure(state="normal" if enabled else "disabled")
            except tk.TclError:
                pass
            self._set_children_state(child, enabled)

    def clear(self) -> None:
        self.schema = None
        self.set_enabled(False)

    def _clear_form(self) -> None:
        for key, var in self.vars.items():
            if isinstance(var, tk.BooleanVar):
                var.set(False)
            elif isinstance(var, tk.IntVar):
                var.set(0)
            else:
                var.set("")
        self.desc_zh.configure(state="normal")
        self.desc_zh.delete("1.0", "end")
        self.desc_en.configure(state="normal")
        self.desc_en.delete("1.0", "end")
        if not self.enabled:
            self.desc_zh.configure(state="disabled")
            self.desc_en.configure(state="disabled")

    def refresh_language(self) -> None:
        self.add_btn.configure(text=self.i18n.t("add"))
        self.del_btn.configure(text=self.i18n.t("delete"))
        self.up_btn.configure(text=self.i18n.t("move_up"))
        self.down_btn.configure(text=self.i18n.t("move_down"))
        self.apply_btn.configure(text=self.i18n.t("apply"))
        for col in self.COLUMNS:
            self.tree.heading(col, text=self.i18n.t(col))
            width = 160 if col in {"field_id", "label_zh", "label_en", "xml_tag", "controlled_values"} else 110
            self.tree.column(col, width=width, stretch=True)

    def load_schema(self, schema: MetadataSchema) -> None:
        self.schema = schema
        self.set_enabled(True)
        self.refresh_table()

    def refresh_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        if not self.schema or not self.enabled:
            return
        for f in self.schema.sorted_fields():
            values = [
                f.field_id,
                f.label_zh,
                f.label_en,
                f.xml_tag,
                f.data_type,
                "✓" if f.required else "",
                "✓" if f.repeatable else "",
                f.level,
                "; ".join(f.controlled_values),
                "✓" if f.sensitive else "",
            ]
            self.tree.insert("", "end", iid=f.field_id, values=values)

    def on_select(self, _event=None) -> None:
        if not self.schema or not self.enabled:
            return
        sel = self.tree.selection()
        if not sel:
            return
        field = self.schema.get_field(sel[0])
        if not field:
            return
        for key, var in self.vars.items():
            if key == "controlled_values":
                var.set("; ".join(field.controlled_values))
            else:
                value = getattr(field, key, "")
                var.set(value)
        self.desc_zh.configure(state="normal")
        self.desc_en.configure(state="normal")
        self.desc_zh.delete("1.0", "end")
        self.desc_zh.insert("1.0", field.description_zh)
        self.desc_en.delete("1.0", "end")
        self.desc_en.insert("1.0", field.description_en)

    def _field_from_form(self) -> MetadataField:
        controlled = [x.strip() for x in self.vars["controlled_values"].get().split(";") if x.strip()]
        return MetadataField(
            field_id=str(self.vars["field_id"].get()).strip(),
            label_zh=str(self.vars["label_zh"].get()).strip(),
            label_en=str(self.vars["label_en"].get()).strip(),
            xml_tag=str(self.vars["xml_tag"].get()).strip(),
            data_type=str(self.vars["data_type"].get()).strip() or "string",
            required=bool(self.vars["required"].get()),
            repeatable=bool(self.vars["repeatable"].get()),
            default_value=str(self.vars["default_value"].get()),
            controlled_values=controlled,
            description_zh=self.desc_zh.get("1.0", "end").strip(),
            description_en=self.desc_en.get("1.0", "end").strip(),
            example=str(self.vars["example"].get()),
            level=str(self.vars["level"].get()).strip() or "text",
            parent=str(self.vars["parent"].get()).strip(),
            order=int(self.vars["order"].get() or 0),
            visible=bool(self.vars["visible"].get()),
            editable=bool(self.vars["editable"].get()),
            sensitive=bool(self.vars["sensitive"].get()),
            validation_rule=str(self.vars["validation_rule"].get()),
        )

    def add_field(self) -> None:
        if not self.schema or not self.enabled:
            return
        new_id = f"new_field_{len(self.schema.fields) + 1}"
        field = MetadataField(field_id=new_id, label_zh="新字段", label_en="New Field", order=len(self.schema.fields) + 1)
        self.schema.add_field(field)
        self.refresh_table()
        self.tree.selection_set(new_id)
        self.on_select()
        self._changed()

    def delete_selected(self) -> None:
        if not self.schema or not self.enabled:
            return
        sel = self.tree.selection()
        if not sel:
            return
        self.schema.remove_field(sel[0])
        self.refresh_table()
        self._changed()

    def move_selected(self, direction: int) -> None:
        if not self.schema or not self.enabled:
            return
        sel = self.tree.selection()
        if not sel:
            return
        self.schema.move_field(sel[0], direction)
        self.refresh_table()
        self.tree.selection_set(sel[0])
        self._changed()

    def apply_selected(self) -> None:
        if not self.schema or not self.enabled:
            return
        field = self._field_from_form()
        if not field.field_id:
            messagebox.showerror(self.i18n.t("error"), "field_id is required")
            return
        old_sel = self.tree.selection()
        if old_sel and old_sel[0] != field.field_id:
            self.schema.remove_field(old_sel[0])
        self.schema.add_field(field, replace=True)
        self.schema.reindex()
        self.refresh_table()
        self.tree.selection_set(field.field_id)
        self._changed()

    def _changed(self) -> None:
        if self.on_change:
            self.on_change()
