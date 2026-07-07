from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Callable, Dict, List

from core.datatypes import FileRecord
from core.document_reader import SUPPORTED_EXTENSIONS
from core.language_registry import code_from_display, native_name, language_options
from core.utils import natural_key, format_bytes, normalized_file_key
from app.theme import PROOFLENS_COLORS
from app.i18n import I18N


class ImportColumnPane(ttk.LabelFrame):
    def __init__(self, master, title: str, role: str, target_index: int, ui_lang: str = 'zh_sim', i18n: I18N | None = None, initial_lang: str | None = None):
        super().__init__(master, text=title, padding=6)
        self.role = role
        self.target_index = target_index
        self.role_label = title
        self.ui_lang = ui_lang
        self.i18n = i18n or I18N(ui_lang)
        self.t = self.i18n.t
        self.paths: List[str] = []
        self.lang_var = tk.StringVar(value=native_name(initial_lang or ('zh_sim' if role == 'source' else 'en'), with_code=False))
        self._drag_item = None
        self._build()

    def _build(self):
        top = ttk.Frame(self); top.pack(fill='x')
        ttk.Label(top, text=self.t('language')).pack(side='left')
        self.lang_combo = ttk.Combobox(top, textvariable=self.lang_var, values=language_options(self.ui_lang, with_code=False, native=True), width=18, state='readonly')
        self.lang_combo.pack(side='left', padx=4)
        ttk.Button(top, text=self.t('import_files'), command=self.add_files, style='Accent.TButton').pack(side='left', padx=2)
        ttk.Button(top, text=self.t('import_folder'), command=self.add_folder).pack(side='left', padx=2)

        btn = ttk.Frame(self); btn.pack(fill='x', pady=4)
        for text, cmd in [(self.t('delete'), self.delete_selected), (self.t('up'), lambda: self.move_selected(-1)), (self.t('down'), lambda: self.move_selected(1)), (self.t('move_top'), self.move_top), (self.t('move_bottom'), self.move_bottom), (self.t('sort'), self.auto_sort)]:
            ttk.Button(btn, text=text, command=cmd).pack(side='left', padx=1)

        cols = ('no','filename','size','path')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', selectmode='extended', height=13)
        for c, h, w in [('no','#',46), ('filename',self.t('filename'),210), ('size',self.t('size'),70), ('path',self.t('path'),320)]:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor='w')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Delete>', lambda e: self.delete_selected())
        self.tree.bind('<Control-Up>', lambda e: self.move_selected(-1))
        self.tree.bind('<Control-Down>', lambda e: self.move_selected(1))
        self.tree.bind('<ButtonPress-1>', self._drag_start)
        self.tree.bind('<ButtonRelease-1>', self._drag_drop)
        self.menu = tk.Menu(self, tearoff=0)
        for label, cmd in [(self.t('import_files'), self.add_files), (self.t('import_folder'), self.add_folder), (self.t('delete'), self.delete_selected), (self.t('up'), lambda: self.move_selected(-1)), (self.t('down'), lambda: self.move_selected(1)), (self.t('auto_sort_title'), self.auto_sort)]:
            self.menu.add_command(label=label, command=cmd)
        self.tree.bind('<Button-3>', self._popup)

    def lang_code(self) -> str:
        val = code_from_display(self.lang_var.get())
        return val or ('zh_sim' if self.role == 'source' else 'en')

    def column_key(self) -> str:
        lang = self.lang_code()
        return f'source_{lang}' if self.role == 'source' else f'target_{self.target_index:02d}_{lang}'

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title=self.t('add_to_column', column=self.role_label),
            filetypes=[(self.t('supported_files'), ' '.join('*'+x for x in SUPPORTED_EXTENSIONS)), (self.t('all_files'), '*.*')]
        )
        self._add_paths(list(paths))

    def add_folder(self):
        folder = filedialog.askdirectory(title=self.t('select_folder'))
        if not folder:
            return
        recursive = messagebox.askyesno(self.t('folder_recursive_title'), self.t('folder_recursive_prompt'))
        paths: List[str] = []
        if recursive:
            iterator = Path(folder).rglob('*')
        else:
            iterator = Path(folder).iterdir()
        for p in iterator:
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                paths.append(str(p))
        self._add_paths(paths)

    def _add_paths(self, paths: List[str]):
        top = self.winfo_toplevel()
        # Only compare against files already in the main project and against
        # the current pane.  Earlier versions also compared with other import
        # panes, which could show "skipped duplicate" even when the main File
        # Manager was empty.  Different columns may legitimately contain the
        # same physical file during testing or special corpus workflows.
        existing = {normalized_file_key(p) for p in self.paths}
        if hasattr(top, 'existing_path_keys'):
            existing.update(getattr(top, 'existing_path_keys', set()) or set())
        clean: List[str] = []
        skipped = 0
        for p in paths:
            if not p or Path(p).suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            key = normalized_file_key(p)
            if key in existing:
                skipped += 1
                continue
            existing.add(key)
            clean.append(p)
        clean.sort(key=natural_key)
        self.paths.extend(clean)
        if skipped and hasattr(top, 'log_duplicate_skip'):
            top.log_duplicate_skip(skipped)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(self.paths, 1):
            try:
                size = format_bytes(Path(p).stat().st_size)
            except Exception:
                size = ''
            self.tree.insert('', 'end', iid=str(i-1), values=(i, Path(p).name, size, p))

    def selected_indices(self) -> List[int]:
        out = []
        for x in self.tree.selection():
            try:
                out.append(int(x))
            except Exception:
                pass
        return sorted(set(out))

    def delete_selected(self):
        ids = self.selected_indices()
        if not ids: return
        self.paths = [p for i, p in enumerate(self.paths) if i not in set(ids)]
        self.refresh()

    def move_selected(self, delta: int):
        ids = self.selected_indices()
        if not ids: return
        selected = set(ids)
        if delta < 0:
            rng = range(1, len(self.paths))
            for i in rng:
                if i in selected and i-1 not in selected:
                    self.paths[i-1], self.paths[i] = self.paths[i], self.paths[i-1]
                    selected.remove(i); selected.add(i-1)
        else:
            rng = range(len(self.paths)-2, -1, -1)
            for i in rng:
                if i in selected and i+1 not in selected:
                    self.paths[i+1], self.paths[i] = self.paths[i], self.paths[i+1]
                    selected.remove(i); selected.add(i+1)
        self.refresh()
        for i in selected:
            if self.tree.exists(str(i)):
                self.tree.selection_add(str(i))

    def move_top(self):
        ids = self.selected_indices()
        if not ids: return
        s = set(ids); chosen = [p for i,p in enumerate(self.paths) if i in s]; rest = [p for i,p in enumerate(self.paths) if i not in s]
        self.paths = chosen + rest; self.refresh()

    def move_bottom(self):
        ids = self.selected_indices()
        if not ids: return
        s = set(ids); chosen = [p for i,p in enumerate(self.paths) if i in s]; rest = [p for i,p in enumerate(self.paths) if i not in s]
        self.paths = rest + chosen; self.refresh()

    def auto_sort(self):
        self.paths.sort(key=natural_key); self.refresh()

    def _drag_start(self, event):
        self._drag_item = self.tree.identify_row(event.y)

    def _drag_drop(self, event):
        target = self.tree.identify_row(event.y)
        if self._drag_item is None or not target or self._drag_item == target:
            return
        old = int(self._drag_item); new = int(target)
        item = self.paths.pop(old); self.paths.insert(new, item)
        self.refresh(); self.tree.selection_set(str(new)); self._drag_item = None

    def _popup(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and iid not in self.tree.selection():
            self.tree.selection_set(iid)
        self.menu.tk_popup(event.x_root, event.y_root)


class ImportWizard(tk.Toplevel):
    """Mode-first import assistant.

    It opens one pane for the source text and one pane for every translation column.
    Users align files at file level before the records enter the main File Manager.
    """
    def __init__(self, master, on_confirm: Callable[[List[FileRecord], str], None], ui_lang: str = 'zh_sim', existing_paths: List[str] | None = None):
        super().__init__(master)
        self.i18n = I18N(ui_lang)
        self.t = self.i18n.t
        self.title(self.t('wizard_title'))
        self.geometry('1280x760')
        self.minsize(1080, 640)
        self.transient(master)
        self.on_confirm = on_confirm
        self.ui_lang = ui_lang
        self.existing_path_keys = {normalized_file_key(p) for p in (existing_paths or []) if p}
        settings = getattr(master, 'state_data', None).settings if hasattr(getattr(master, 'state_data', None), 'settings') else {}
        self.mode_var = tk.StringVar(value=settings.get('last_alignment_project_mode') or settings.get('alignment_project_mode') or '1_to_1')
        self.target_count_var = tk.IntVar(value=int(settings.get('last_target_count') or len(settings.get('last_target_langs') or ['en']) or 1))
        self.panes: List[ImportColumnPane] = []
        self.configure(bg=PROOFLENS_COLORS['bg'])
        self._build_mode_page()

    def all_path_keys(self, exclude: ImportColumnPane | None = None) -> set[str]:
        keys = set(self.existing_path_keys)
        for pane in self.panes:
            if pane is exclude:
                continue
            keys.update(normalized_file_key(p) for p in pane.paths)
        return keys

    def log_duplicate_skip(self, count: int) -> None:
        try:
            master_log = getattr(self.master, 'log', None)
            if callable(master_log):
                master_log(self.t('duplicate_files_skipped', count=count))
        except Exception:
            pass

    def _build_mode_page(self):
        for w in self.winfo_children(): w.destroy()
        frame = ttk.Frame(self, padding=24); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=self.t('choose_mode'), style='Gold.TLabel', font=('Microsoft YaHei UI', 16, 'bold')).pack(anchor='w', pady=(0, 14))
        modes = ttk.LabelFrame(frame, text=self.t('alignment_mode'), padding=12); modes.pack(fill='x')
        ttk.Radiobutton(modes, text=self.t('mode_1_to_1'), variable=self.mode_var, value='1_to_1', command=self._sync_count).pack(anchor='w', pady=4)
        ttk.Radiobutton(modes, text=self.t('mode_1_to_n'), variable=self.mode_var, value='1_to_n', command=self._sync_count).pack(anchor='w', pady=4)
        ttk.Radiobutton(modes, text=self.t('mode_multilingual'), variable=self.mode_var, value='multilingual', command=self._sync_count).pack(anchor='w', pady=4)
        count = ttk.Frame(frame); count.pack(fill='x', pady=18)
        ttk.Label(count, text=self.t('target_column_count')).pack(side='left')
        ttk.Spinbox(count, from_=1, to=8, textvariable=self.target_count_var, width=6).pack(side='left', padx=4)
        ttk.Label(frame, text=self.t('mode_hint'), wraplength=920).pack(anchor='w', pady=10)
        ttk.Button(frame, text=self.t('confirm_mode_import'), command=self._build_import_page, style='Accent.TButton').pack(anchor='e', pady=20)

    def _sync_count(self):
        if self.mode_var.get() == '1_to_1':
            self.target_count_var.set(1)
        elif self.target_count_var.get() < 2:
            self.target_count_var.set(2)

    def _build_import_page(self):
        self._sync_count()
        for w in self.winfo_children(): w.destroy()
        top = ttk.Frame(self, padding=(10, 8)); top.pack(fill='x')
        ttk.Label(top, text=self.t('current_mode', mode=self._mode_label()), style='Gold.TLabel').pack(side='left')
        ttk.Button(top, text=self.t('back_mode'), command=self._build_mode_page).pack(side='right', padx=3)
        if self.mode_var.get() != '1_to_1':
            ttk.Button(top, text=self.t('add_target_pane'), command=self.add_target_pane).pack(side='right', padx=3)
            ttk.Button(top, text=self.t('remove_target_pane'), command=self.remove_target_pane).pack(side='right', padx=3)
        ttk.Button(top, text=self.t('confirm_import_main'), command=self.confirm, style='Accent.TButton').pack(side='right', padx=3)

        self.container = ttk.PanedWindow(self, orient='horizontal')
        self.container.pack(fill='both', expand=True, padx=8, pady=8)
        self.panes = []
        self._add_pane(self.t('source'), 'source', 0)
        for i in range(1, self.target_count_var.get()+1):
            label = self.t('target') if self.mode_var.get() == '1_to_1' else self.t('target_version', n=i)
            self._add_pane(label, 'target', i)
        bottom = ttk.Label(self, text=self.t('wizard_bottom_hint'), anchor='w')
        bottom.pack(fill='x', padx=10, pady=(0, 8))

    def _mode_label(self):
        return {'1_to_1': self.t('mode_label_1_to_1'), '1_to_n': self.t('mode_label_1_to_n'), 'multilingual': self.t('mode_label_multilingual')}[self.mode_var.get()]

    def _add_pane(self, title: str, role: str, target_index: int):
        settings = getattr(self.master, 'state_data', None).settings if hasattr(getattr(self.master, 'state_data', None), 'settings') else {}
        if role == 'source':
            initial_lang = settings.get('last_source_lang', 'zh_sim')
        else:
            last_targets = settings.get('last_target_langs') or ['en']
            initial_lang = last_targets[min(max(target_index - 1, 0), len(last_targets) - 1)] if last_targets else 'en'
        pane = ImportColumnPane(self.container, title, role, target_index, self.ui_lang, self.i18n, initial_lang=initial_lang)
        self.container.add(pane, weight=1)
        self.panes.append(pane)

    def add_target_pane(self):
        idx = len([p for p in self.panes if p.role == 'target']) + 1
        self._add_pane(self.t('target_version', n=idx), 'target', idx)
        self.target_count_var.set(idx)

    def remove_target_pane(self):
        targets = [p for p in self.panes if p.role == 'target']
        if len(targets) <= 1:
            return
        pane = targets[-1]
        self.panes.remove(pane)
        pane.destroy()
        self.target_count_var.set(len(targets)-1)

    def confirm(self):
        if not self.panes:
            return
        empty = [p.role_label for p in self.panes if not p.paths]
        if empty:
            messagebox.showwarning(self.t('incomplete_files_title'), self.t('incomplete_files_message', items='\n'.join(empty)))
            return
        counts = {p.role_label: len(p.paths) for p in self.panes}
        if len(set(counts.values())) > 1:
            msg = '\n'.join(f'{k}: {v}' for k, v in counts.items())
            if not messagebox.askyesno(self.t('inconsistent_file_counts_title'), self.t('inconsistent_file_counts_message', msg=msg)):
                return
        column_defs = [
            {
                'column_key': p.column_key(),
                'lang': p.lang_code(),
                'alignment_role': p.role,
                'role_label': p.role_label,
                'target_index': int(p.target_index or 0),
            }
            for p in self.panes
        ]
        records: List[FileRecord] = []
        # At confirmation, skip only files that already exist in the main
        # project.  Do not treat two different import columns as duplicates.
        existing_main = set(self.existing_path_keys)
        skipped = 0
        max_len = max(len(p.paths) for p in self.panes)
        for row_idx in range(max_len):
            gid = f'set_{row_idx+1:03d}'
            for pane in self.panes:
                if row_idx >= len(pane.paths):
                    continue
                path = pane.paths[row_idx]
                key = normalized_file_key(path)
                if key in existing_main:
                    skipped += 1
                    continue
                try:
                    rec = FileRecord.from_path(
                        path,
                        lang=pane.lang_code(),
                        group_id=gid,
                        sort_order=row_idx + 1,
                        alignment_role=pane.role,
                        role_label=pane.role_label,
                        column_key=pane.column_key(),
                        target_index=pane.target_index,
                    )
                    # Large files are loaded lazily in the background during segmentation/alignment.
                    rec.status = 'imported'
                    records.append(rec)
                except Exception as exc:
                    messagebox.showerror(self.t('import_failed'), f'{path}\n\n{exc}')
        if skipped:
            self.log_duplicate_skip(skipped)
        self.on_confirm(records, self.mode_var.get(), column_defs)
        self.destroy()
