"""Import dialogs for Excel and XML metadata."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from excel_importer import ExcelImporter, ExcelPreview
from i18n import I18N
from models import MetadataProject
from xml_importer import XMLImporter, XMLImportPreview


class MappingDialog(tk.Toplevel):
    """A reusable mapping dialog for Excel columns or XML tags."""

    def __init__(
        self,
        master: tk.Misc,
        i18n: I18N,
        title: str,
        source_items: list[str],
        schema_fields: list[str],
        suggested_mapping: dict[str, str],
        allow_add_unknown: bool = True,
    ) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.result: tuple[dict[str, str], bool] | None = None
        self.vars: dict[str, tk.StringVar] = {}
        self.add_unknown_var = tk.BooleanVar(value=allow_add_unknown)
        self.title(title)
        self.geometry("720x480")
        self.transient(master)
        self.grab_set()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self, padding=8)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(frame, highlightthickness=0)
        inner = ttk.Frame(canvas)
        ysb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=ysb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))

        ttk.Label(inner, text=self.i18n.t("excel_columns") + " / XML Tags").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Label(inner, text=self.i18n.t("schema_fields")).grid(row=0, column=1, sticky="w", padx=4, pady=4)
        choices = [""] + schema_fields
        for row, item in enumerate(source_items, start=1):
            ttk.Label(inner, text=item).grid(row=row, column=0, sticky="w", padx=4, pady=2)
            var = tk.StringVar(value=suggested_mapping.get(item, ""))
            ttk.Combobox(inner, textvariable=var, values=choices, state="readonly").grid(row=row, column=1, sticky="ew", padx=4, pady=2)
            self.vars[item] = var
        inner.columnconfigure(1, weight=1)

        bottom = ttk.Frame(frame)
        bottom.grid(row=1, column=0, sticky="ew", pady=8)
        ttk.Checkbutton(bottom, text=self.i18n.t("add_to_schema"), variable=self.add_unknown_var).pack(side="left")
        ttk.Button(bottom, text=self.i18n.t("ok"), command=self._ok).pack(side="right", padx=4)
        ttk.Button(bottom, text=self.i18n.t("cancel"), command=self.destroy).pack(side="right", padx=4)

    def _ok(self) -> None:
        mapping = {k: v.get() for k, v in self.vars.items() if v.get()}
        self.result = (mapping, self.add_unknown_var.get())
        self.destroy()


class ExcelImportDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, i18n: I18N, project: MetadataProject, on_imported) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.project = project
        self.on_imported = on_imported
        self.importer = ExcelImporter()
        self.path: Path | None = None
        self.preview_data: ExcelPreview | None = None
        self.title(self.i18n.t("import_excel"))
        self.geometry("900x600")
        self.transient(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.grid(row=0, column=0, sticky="ew")
        self.file_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.file_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(top, text=self.i18n.t("select_file"), command=self.select_file).pack(side="left", padx=4)
        ttk.Button(top, text=self.i18n.t("mapping"), command=self.open_mapping).pack(side="left", padx=4)
        ttk.Button(top, text=self.i18n.t("import"), command=self.do_import).pack(side="left", padx=4)
        self.tree = ttk.Treeview(self, show="headings")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.mapping: dict[str, str] = {}
        self.add_unknown = False

    def select_file(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xlsm")])
        if not filename:
            return
        self.path = Path(filename)
        self.file_var.set(str(self.path))
        try:
            self.preview_data = self.importer.preview(self.path, self.project, max_rows=100)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.mapping = dict(self.preview_data.suggested_mapping)
        self._show_preview()

    def _show_preview(self) -> None:
        self.tree.delete(*self.tree.get_children())
        if not self.preview_data:
            return
        headers = self.preview_data.headers
        self.tree.configure(columns=headers)
        for h in headers:
            self.tree.heading(h, text=h)
            self.tree.column(h, width=130, stretch=True)
        for row in self.preview_data.rows[:100]:
            values = row + [""] * max(0, len(headers) - len(row))
            self.tree.insert("", "end", values=values[: len(headers)])

    def open_mapping(self) -> None:
        if not self.preview_data:
            return
        dlg = MappingDialog(
            self,
            self.i18n,
            self.i18n.t("mapping"),
            self.preview_data.headers,
            self.project.schema.field_ids(),
            self.mapping,
        )
        self.wait_window(dlg)
        if dlg.result:
            self.mapping, self.add_unknown = dlg.result

    def do_import(self) -> None:
        if not self.path:
            return
        try:
            count, errors = self.importer.import_file(self.path, self.project, self.mapping, self.add_unknown)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        messagebox.showinfo(self.i18n.t("success"), f"Imported {count} record(s), errors: {len(errors)}")
        self.on_imported()
        self.destroy()


class XMLImportDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, i18n: I18N, project: MetadataProject, on_imported) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.project = project
        self.on_imported = on_imported
        self.importer = XMLImporter()
        self.path: Path | None = None
        self.preview_data: XMLImportPreview | None = None
        self.mapping: dict[str, str] = {}
        self.add_unknown = False
        self.title(self.i18n.t("import_xml"))
        self.geometry("760x520")
        self.transient(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.grid(row=0, column=0, sticky="ew")
        self.file_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.file_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(top, text=self.i18n.t("select_file"), command=self.select_file).pack(side="left", padx=4)
        ttk.Button(top, text=self.i18n.t("mapping"), command=self.open_mapping).pack(side="left", padx=4)
        ttk.Button(top, text=self.i18n.t("import"), command=self.do_import).pack(side="left", padx=4)
        self.text = tk.Text(self, wrap="word")
        self.text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

    def select_file(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("XML", "*.xml"), ("All files", "*.*")])
        if not filename:
            return
        self.path = Path(filename)
        self.file_var.set(str(self.path))
        try:
            self.preview_data = self.importer.preview(self.path, self.project)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        self.mapping = dict(self.preview_data.suggested_mapping)
        self.text.delete("1.0", "end")
        self.text.insert("end", "Tags found:\n" + "\n".join(self.preview_data.tags))
        self.text.insert("end", "\n\nUnknown tags:\n" + "\n".join(self.preview_data.unknown_tags))

    def open_mapping(self) -> None:
        if not self.preview_data:
            return
        dlg = MappingDialog(
            self,
            self.i18n,
            self.i18n.t("mapping"),
            self.preview_data.tags,
            self.project.schema.field_ids(),
            self.mapping,
        )
        self.wait_window(dlg)
        if dlg.result:
            self.mapping, self.add_unknown = dlg.result

    def do_import(self) -> None:
        if not self.path:
            return
        try:
            count, logs = self.importer.import_file(self.path, self.project, self.mapping, self.add_unknown)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.i18n.t("error"), str(exc))
            return
        messagebox.showinfo(self.i18n.t("success"), f"Imported {count} record(s).\n" + "\n".join(logs))
        self.on_imported()
        self.destroy()
