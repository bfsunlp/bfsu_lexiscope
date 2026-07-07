from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from typing import Dict, List, Optional

from core.datatypes import FileRecord
from core.document_reader import SUPPORTED_EXTENSIONS, read_document, text_stats
from core.segmenter import split_text
from core.segmentation_profiles import describe_profile
from core.language_registry import display_name, column_display_name, language_options, code_from_display
from core.utils import format_bytes, natural_key, open_path, normalized_file_key
from app.theme import PROOFLENS_COLORS


class FileColumnPanel(ttk.LabelFrame):
    def __init__(self, master, manager: 'FileManagerFrame', column_key: str):
        self.manager = manager
        self.column_key = column_key
        super().__init__(master, text=self._title(), padding=5)
        self.drag_item: Optional[str] = None
        self._build()

    def _title(self) -> str:
        return column_display_name(self.column_key, self.manager.app_state.files, self.manager.ui_lang)

    def _build(self):
        top = ttk.Frame(self); top.pack(fill='x')
        ttk.Button(top, text='+', width=3, command=self.add_files, style='Accent.TButton').pack(side='left', padx=1)
        ttk.Button(top, text='-', width=3, command=self.delete_selected).pack(side='left', padx=1)
        ttk.Button(top, text='↑', width=3, command=lambda: self.move_selected(-1)).pack(side='left', padx=1)
        ttk.Button(top, text='↓', width=3, command=lambda: self.move_selected(1)).pack(side='left', padx=1)
        ttk.Button(top, text=self.manager.t('sort'), command=self.auto_sort).pack(side='left', padx=1)
        ttk.Button(top, text=self.manager.t('preview'), command=self.preview).pack(side='left', padx=1)

        cols = ('no','group','filename','size','segmenter','status','note')
        tree_wrap = ttk.Frame(self)
        tree_wrap.pack(fill='both', expand=True, pady=(4, 0))
        tree_wrap.grid_rowconfigure(0, weight=1)
        tree_wrap.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_wrap, columns=cols, show='headings', selectmode='extended', height=16)
        self.tree_vscroll = ttk.Scrollbar(tree_wrap, orient='vertical', command=self.tree.yview)
        self.tree_hscroll = ttk.Scrollbar(tree_wrap, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.tree_vscroll.set, xscrollcommand=self.tree_hscroll.set)
        for c, h, w in [('no','#',46), ('group',self.manager.t('group'),82), ('filename',self.manager.t('filename'),280), ('size',self.manager.t('size'),82), ('segmenter',self.manager.t('segmenter'),150), ('status',self.manager.t('status'),100), ('note',self.manager.t('note'),180)]:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, minwidth=40, anchor='w', stretch=False)
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.tree_vscroll.grid(row=0, column=1, sticky='ns')
        self.tree_hscroll.grid(row=1, column=0, sticky='ew')
        self.tree.bind('<Button-1>', lambda e: self.manager.set_active_column(self.column_key))
        self.tree.bind('<Delete>', lambda e: self.delete_selected())
        self.tree.bind('<Control-Up>', lambda e: self.move_selected(-1))
        self.tree.bind('<Control-Down>', lambda e: self.move_selected(1))
        self.tree.bind('<Control-Home>', lambda e: self.move_top())
        self.tree.bind('<Control-End>', lambda e: self.move_bottom())
        self.tree.bind('<Double-1>', self._edit)
        self.tree.bind('<Button-3>', self._popup)
        self.tree.bind('<ButtonPress-1>', self._drag_start, add='+')
        self.tree.bind('<ButtonRelease-1>', self._drag_drop)
        self.menu = tk.Menu(self, tearoff=0)
        for label, cmd in [
            (self.manager.t('add_file_to_column'), self.add_files), (self.manager.t('delete_selected'), self.delete_selected), (self.manager.t('move_up'), lambda: self.move_selected(-1)),
            (self.manager.t('move_down'), lambda: self.move_selected(1)), (self.manager.t('move_top'), self.move_top), (self.manager.t('move_bottom'), self.move_bottom), (self.manager.t('auto_sort_title'), self.auto_sort),
            (self.manager.t('open_file'), self.open_file), (self.manager.t('open_folder'), self.open_folder), (self.manager.t('preview_text'), self.preview), (self.manager.t('preview_segmentation'), self.preview_segmentation), (self.manager.t('change_language'), self.modify_language),
            (self.manager.t('change_note'), self.modify_note), (self.manager.t('reload'), self.reload_selected),
            (self.manager.t('open_current_group_editor'), self.align_current_group),
        ]:
            self.menu.add_command(label=label, command=cmd)

    def records(self) -> List[FileRecord]:
        return sorted([f for f in self.manager.app_state.files if self.manager.record_column_key(f) == self.column_key], key=lambda f: f.sort_order)

    def refresh(self):
        self.configure(text=self._title())
        self.tree.delete(*self.tree.get_children())
        for i, rec in enumerate(self.records(), 1):
            seg_label = rec.segmentation_engine or describe_profile(self.manager.app_state.settings, rec.lang or 'en', 'sentence')
            self.tree.insert('', 'end', iid=rec.file_id, values=(i, rec.group_id, rec.filename, format_bytes(rec.size), seg_label, self.manager.display_record_status(rec), rec.note))

    def selected_records(self) -> List[FileRecord]:
        ids = set(self.tree.selection())
        return [f for f in self.records() if f.file_id in ids]

    def add_files(self):
        recs = self.records()
        sample = recs[0] if recs else None
        coldef = self.manager.column_def(self.column_key)
        if not sample and not coldef:
            messagebox.showinfo(self.manager.t('add_file_title'), self.manager.t('column_not_ready'))
            return
        paths = filedialog.askopenfilenames(title=self.manager.t('add_to_column', column=self._title()), filetypes=[(self.manager.t('supported_files'), ' '.join('*'+x for x in SUPPORTED_EXTENSIONS)), (self.manager.t('all_files'), '*.*')])
        if not paths: return
        clean_paths, skipped = self.manager.filter_new_paths(list(paths))
        if skipped:
            self.manager.callbacks.get('log', print)(self.manager.t('duplicate_files_skipped', count=skipped))
        if not clean_paths:
            return
        self.manager._snapshot()
        current = self.records()
        lang = sample.lang if sample else coldef.get('lang', '')
        role = sample.alignment_role if sample else coldef.get('alignment_role', 'target')
        role_label = sample.role_label if sample else coldef.get('role_label', '')
        target_index = int(sample.target_index if sample else coldef.get('target_index', 1) or 1)
        for p in sorted(clean_paths, key=natural_key):
            try:
                rec = FileRecord.from_path(
                    p, lang=lang, group_id=f'set_{len(current)+1:03d}', sort_order=len(current)+1,
                    alignment_role=role, role_label=role_label, column_key=self.column_key, target_index=target_index,
                )
                rec.status = 'imported'
                self.manager.app_state.files.append(rec)
                current.append(rec)
            except Exception as exc:
                self.manager.callbacks.get('log', print)(f'Add file failed: {p}: {exc}')
        self.manager.remember_columns_from_files()
        self.manager.regenerate_groups_by_position(); self.manager.refresh()

    def delete_selected(self):
        ids = {r.file_id for r in self.selected_records()}
        if not ids: return
        if self.manager.app_state.settings.get('confirm_delete', True) and not messagebox.askyesno(self.manager.t('delete_files_title'), self.manager.t('remove_files_confirm', count=len(ids))):
            return
        self.manager._snapshot()
        self.manager.app_state.files = [f for f in self.manager.app_state.files if f.file_id not in ids]
        for fid in ids:
            self.manager.app_state.segments_by_file.pop(fid, None)
            self.manager.app_state.paragraph_segments_by_file.pop(fid, None)
        self.manager.regenerate_groups_by_position(); self.manager.refresh()

    def move_selected(self, delta: int):
        ids = [r.file_id for r in self.selected_records()]
        if not ids: return
        self.manager._snapshot()
        recs = self.records(); selected = set(ids)
        if delta < 0:
            for i in range(1, len(recs)):
                if recs[i].file_id in selected and recs[i-1].file_id not in selected:
                    recs[i-1].sort_order, recs[i].sort_order = recs[i].sort_order, recs[i-1].sort_order
        else:
            for i in range(len(recs)-2, -1, -1):
                if recs[i].file_id in selected and recs[i+1].file_id not in selected:
                    recs[i+1].sort_order, recs[i].sort_order = recs[i].sort_order, recs[i+1].sort_order
        self.manager.regenerate_groups_by_position(); self.manager.refresh(); self._restore(ids)

    def move_top(self):
        ids = [r.file_id for r in self.selected_records()]
        if not ids: return
        self.manager._snapshot(); recs = self.records(); sel = [r for r in recs if r.file_id in ids]; rest = [r for r in recs if r.file_id not in ids]
        for i, r in enumerate(sel + rest, 1): r.sort_order = i
        self.manager.regenerate_groups_by_position(); self.manager.refresh(); self._restore(ids)

    def move_bottom(self):
        ids = [r.file_id for r in self.selected_records()]
        if not ids: return
        self.manager._snapshot(); recs = self.records(); sel = [r for r in recs if r.file_id in ids]; rest = [r for r in recs if r.file_id not in ids]
        for i, r in enumerate(rest + sel, 1): r.sort_order = i
        self.manager.regenerate_groups_by_position(); self.manager.refresh(); self._restore(ids)

    def auto_sort(self):
        if not messagebox.askyesno(self.manager.t('auto_sort_title'), self.manager.t('auto_sort_confirm')):
            return
        self.manager._snapshot()
        for i, rec in enumerate(sorted(self.records(), key=lambda f: natural_key(f.filename)), 1):
            rec.sort_order = i
        self.manager.regenerate_groups_by_position(); self.manager.refresh()

    def modify_language(self):
        recs = self.selected_records()
        if not recs: return
        val = simpledialog.askstring(self.manager.t('modify_language_title'), self.manager.t('modify_language_prompt'), initialvalue=display_name(recs[0].lang, self.manager.ui_lang, with_code=False))
        if not val: return
        code = code_from_display(val)
        self.manager._snapshot()
        for r in recs: r.lang = code
        # keep column key stable during manual edits to avoid losing columns
        self.manager.refresh()

    def modify_note(self):
        recs = self.selected_records()
        if not recs: return
        val = simpledialog.askstring(self.manager.t('note_title'), self.manager.t('note_prompt'), initialvalue=recs[0].note)
        if val is None: return
        self.manager._snapshot()
        for r in recs: r.note = val
        self.manager.refresh()

    def preview(self):
        recs = self.selected_records()
        if not recs: return
        self.manager.preview_record(recs[0])

    def preview_segmentation(self):
        """Preview sentence segmentation for the currently selected file.

        The context menu is built inside FileColumnPanel, so the command must
        exist on the panel itself instead of only on FileManagerFrame.  Without
        this proxy, refreshing the file manager after import raises an
        AttributeError and leaves newly imported records invisible.
        """
        recs = self.selected_records()
        if not recs:
            return
        self.manager.preview_segmentation_record(recs[0])

    def reload_selected(self):
        recs = self.selected_records()
        if not recs: return
        self.manager._snapshot()
        for r in recs: self.manager._read_record(r)
        self.manager.refresh()

    def open_file(self):
        recs = self.selected_records()
        if recs: open_path(recs[0].path)

    def open_folder(self):
        recs = self.selected_records()
        if recs: open_path(str(Path(recs[0].path).parent))

    def _restore(self, ids):
        if self.column_key in self.manager.panels:
            panel = self.manager.panels[self.column_key]
            for fid in ids:
                if panel.tree.exists(fid): panel.tree.selection_add(fid)

    def _edit(self, event):
        col = self.tree.identify_column(event.x)
        iid = self.tree.identify_row(event.y)
        if not iid: return
        if iid not in self.tree.selection():
            self.tree.selection_set(iid)
        if col in {'#6'}:
            self.modify_note()
        elif col == '#2':
            self.manager.edit_group_id(iid)
        elif col in {'#7'}:
            self.modify_note()
        else:
            self.align_current_group()

    def align_current_group(self):
        self.manager.align_current_selected_group()

    def _popup(self, event):
        self.manager.set_active_column(self.column_key)
        iid = self.tree.identify_row(event.y)
        if iid and iid not in self.tree.selection(): self.tree.selection_set(iid)
        self.menu.tk_popup(event.x_root, event.y_root)

    def _drag_start(self, event):
        self.manager.set_active_column(self.column_key)
        self.drag_item = self.tree.identify_row(event.y)

    def _drag_drop(self, event):
        target = self.tree.identify_row(event.y)
        if not self.drag_item or not target or self.drag_item == target: return
        recs = self.records()
        ids = [r.file_id for r in recs]
        if self.drag_item not in ids or target not in ids: return
        old, new = ids.index(self.drag_item), ids.index(target)
        self.manager._snapshot()
        rec = recs.pop(old); recs.insert(new, rec)
        for i, r in enumerate(recs, 1): r.sort_order = i
        self.manager.regenerate_groups_by_position(); self.manager.refresh()
        if self.column_key in self.manager.panels and self.manager.panels[self.column_key].tree.exists(rec.file_id):
            self.manager.panels[self.column_key].tree.selection_set(rec.file_id)
        self.drag_item = None


class FileManagerFrame(ttk.Frame):
    def __init__(self, master, app_state, callbacks: dict):
        super().__init__(master)
        self.app_state = app_state
        self.callbacks = callbacks
        self.t = callbacks.get('t', lambda key, **kwargs: key.format(**kwargs) if kwargs else key)
        self.ui_lang = self.app_state.settings.get('gui_language', 'zh_sim')
        self.active_column_key: str = ''
        self.panels: Dict[str, FileColumnPanel] = {}
        self._build()

    def _build(self):
        toolbar = ttk.Frame(self); toolbar.pack(fill='x', padx=4, pady=4)
        ttk.Button(toolbar, text=self.t('import_alignment_files'), command=self.callbacks.get('import_wizard'), style='Accent.TButton').pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('add_to_current_column'), command=self.add_files).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('delete_selected'), command=self.delete_selected).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('delete_all'), command=self.delete_all).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('move_up'), command=lambda: self.move_selected(-1)).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('move_down'), command=lambda: self.move_selected(1)).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('save_file_alignment'), command=self.regenerate_groups_by_position).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('check_pairing'), command=self.check_pairing).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('segment_paragraph'), command=self.start_paragraph_segmentation).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('segment_sentence'), command=self.start_sentence_segmentation).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('preview_segmentation'), command=self.preview_segmentation).pack(side='left', padx=2)
        ttk.Button(toolbar, text=self.t('open_current_group_editor'), command=self.align_current_selected_group).pack(side='left', padx=2)

        self.paned = ttk.PanedWindow(self, orient='horizontal')
        self.paned.pack(fill='both', expand=True, padx=4, pady=4)
        self.status_var = tk.StringVar(value=self.t('file_manager_hint'))
        ttk.Label(self, textvariable=self.status_var, anchor='w').pack(fill='x', padx=4, pady=(0,4))
        self._last_column_order: List[str] = []

    def _balance_panes(self):
        """Distribute visible file columns across the available width.

        Users can still drag the PanedWindow sashes afterward to set custom
        widths. Rebalancing is only triggered when the column layout changes.
        """
        try:
            panes = list(self.paned.panes())
            count = len(panes)
            if count <= 1:
                return
            width = max(self.paned.winfo_width(), self.winfo_width(), 900)
            for i in range(count - 1):
                self.paned.sashpos(i, int(width * (i + 1) / count))
        except Exception:
            pass

    def record_column_key(self, rec: FileRecord) -> str:
        if rec.column_key:
            return rec.column_key
        return f"source_{rec.lang}" if rec.alignment_role == 'source' else f"target_{rec.target_index:02d}_{rec.lang}"

    def column_def(self, column_key: str) -> dict:
        for d in self.app_state.settings.get('file_columns', []) or []:
            if d.get('column_key') == column_key:
                return dict(d)
        for f in self.app_state.files:
            if self.record_column_key(f) == column_key:
                return {
                    'column_key': column_key,
                    'lang': f.lang,
                    'alignment_role': f.alignment_role,
                    'role_label': f.role_label,
                    'target_index': int(f.target_index or 1),
                }
        if column_key.startswith('source_'):
            return {'column_key': column_key, 'lang': column_key.replace('source_', ''), 'alignment_role': 'source', 'role_label': self.t('source'), 'target_index': 0}
        if column_key.startswith('target_'):
            parts = column_key.split('_', 2)
            idx = int(parts[1]) if len(parts) >= 3 and parts[1].isdigit() else 1
            lang = parts[-1] if len(parts) >= 3 else ''
            return {'column_key': column_key, 'lang': lang, 'alignment_role': 'target', 'role_label': self.t('target_version', n=idx), 'target_index': idx}
        return {}

    def remember_columns_from_files(self):
        defs: Dict[str, dict] = {d.get('column_key'): dict(d) for d in (self.app_state.settings.get('file_columns', []) or []) if d.get('column_key')}
        for f in self.app_state.files:
            key = self.record_column_key(f)
            defs[key] = {
                'column_key': key,
                'lang': f.lang,
                'alignment_role': f.alignment_role,
                'role_label': f.role_label,
                'target_index': int(f.target_index or 1),
            }
        self.app_state.settings['file_columns'] = list(defs.values())

    def set_column_defs(self, column_defs: List[dict]):
        if column_defs:
            # Keep exactly the user-selected mode columns.  Empty panes therefore
            # stay visible even after the last file in that column is deleted.
            self.app_state.settings['file_columns'] = [dict(d) for d in column_defs if d.get('column_key')]
        else:
            self.remember_columns_from_files()

    def column_order(self) -> List[str]:
        cols: Dict[str, dict] = {}
        for d in self.app_state.settings.get('file_columns', []) or []:
            if d.get('column_key'):
                cols[d['column_key']] = dict(d)
        for f in self.app_state.files:
            key = self.record_column_key(f)
            cols[key] = {
                'column_key': key,
                'lang': f.lang,
                'alignment_role': f.alignment_role,
                'role_label': f.role_label,
                'target_index': int(f.target_index or 1),
            }
        def key(k: str):
            d = cols[k]
            return (0 if d.get('alignment_role') == 'source' else 1, int(d.get('target_index') or 1), k)
        return sorted(cols.keys(), key=key)

    def refresh(self):
        self.ui_lang = self.app_state.settings.get('gui_language', 'zh_sim')
        order = self.column_order()
        existing = set(self.panels)
        needed = set(order)
        layout_changed = order != self._last_column_order

        for k in existing - needed:
            panel = self.panels.pop(k, None)
            if panel is not None:
                try:
                    self.paned.forget(panel)
                except Exception:
                    pass
                panel.destroy()

        # Rebuild pane order. ttk.PanedWindow sashes are draggable, so users can
        # manually assign different widths to source/translation columns.
        for pane in list(self.paned.panes()):
            try:
                self.paned.forget(pane)
            except Exception:
                pass

        for key in order:
            panel = self.panels.get(key)
            if panel is None:
                panel = FileColumnPanel(self.paned, self, key)
                self.panels[key] = panel
                layout_changed = True
            self.paned.add(panel, weight=1)
            panel.refresh()

        if self.active_column_key not in needed:
            self.active_column_key = order[0] if order else ''
        self._last_column_order = list(order)
        self._update_status()
        if layout_changed:
            self.after_idle(self._balance_panes)

    def set_active_column(self, key: str):
        self.active_column_key = key

    def active_panel(self) -> Optional[FileColumnPanel]:
        if self.active_column_key in self.panels:
            return self.panels[self.active_column_key]
        if self.panels:
            return next(iter(self.panels.values()))
        return None

    def _snapshot(self):
        self.callbacks.get('push_undo', lambda: None)()

    def imported_path_keys(self) -> set[str]:
        return {normalized_file_key(f.path) for f in self.app_state.files if getattr(f, 'path', '')}

    def filter_new_paths(self, paths: List[str]) -> tuple[List[str], int]:
        """Return paths not already imported; repeated selections are skipped."""
        existing = self.imported_path_keys()
        seen = set(existing)
        clean: List[str] = []
        skipped = 0
        for p in paths:
            if not p:
                continue
            try:
                if Path(p).suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                key = normalized_file_key(p)
            except Exception:
                skipped += 1
                continue
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            clean.append(p)
        return clean, skipped

    def _read_record(self, rec: FileRecord):
        try:
            rec.text = read_document(rec.path, preserve_paragraphs=self.app_state.settings.get('preserve_paragraphs', True), remove_excessive_spaces=self.app_state.settings.get('remove_excessive_spaces', True))
            rec.char_count, rec.paragraph_count = text_stats(rec.text)
            rec.status = 'read'
        except Exception as exc:
            rec.status = 'read_failed'; rec.note = str(exc)
        return rec

    def add_files(self):
        panel = self.active_panel()
        if panel: panel.add_files()
        else: self.callbacks.get('import_wizard', lambda: None)()

    def add_folder(self):
        panel = self.active_panel()
        if not panel:
            self.callbacks.get('import_wizard', lambda: None)(); return
        folder = filedialog.askdirectory(title=self.t('select_folder'))
        if not folder: return
        paths = [str(p) for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
        sample = panel.records()[0] if panel.records() else None
        coldef = self.column_def(panel.column_key)
        if not sample and not coldef:
            return
        clean_paths, skipped = self.filter_new_paths(paths)
        if skipped:
            self.callbacks.get('log', print)(self.t('duplicate_files_skipped', count=skipped))
        if not clean_paths:
            return
        panel.manager._snapshot()
        current = panel.records()
        for p in sorted(clean_paths, key=natural_key):
            rec = FileRecord.from_path(
                p,
                sample.lang if sample else coldef.get('lang', ''),
                sort_order=len(current)+1,
                alignment_role=sample.alignment_role if sample else coldef.get('alignment_role', 'target'),
                role_label=sample.role_label if sample else coldef.get('role_label', ''),
                column_key=panel.column_key,
                target_index=sample.target_index if sample else int(coldef.get('target_index', 1) or 1),
            )
            rec.status = 'imported'
            self.app_state.files.append(rec)
            current.append(rec)
        self.remember_columns_from_files(); self.regenerate_groups_by_position(); self.refresh()

    def selected_records(self) -> List[FileRecord]:
        out: List[FileRecord] = []
        for p in self.panels.values(): out.extend(p.selected_records())
        return out

    def selected_group_id(self) -> str:
        recs = self.selected_records()
        if recs:
            return recs[0].group_id
        panel = self.active_panel()
        if panel:
            recs = panel.records()
            if recs:
                return recs[0].group_id
        return ''

    def group_status(self, group_id: str) -> str:
        statuses = self.app_state.settings.get('group_statuses', {}) or {}
        return str(statuses.get(group_id, ''))

    def status_label(self, status: str) -> str:
        if not status:
            return ''
        val = self.t('status_' + status)
        return val if val != 'status_' + status else status

    def display_record_status(self, rec: FileRecord) -> str:
        return self.status_label(self.group_status(rec.group_id) or rec.status)

    def align_current_selected_group(self):
        gid = self.selected_group_id()
        cb = self.callbacks.get('align_current_group')
        if callable(cb):
            cb(gid)

    def delete_selected(self):
        ids = {r.file_id for r in self.selected_records()}
        if not ids: return
        if self.app_state.settings.get('confirm_delete', True) and not messagebox.askyesno(self.t('delete_files_title'), self.t('remove_files_confirm', count=len(ids))):
            return
        self._snapshot(); self.app_state.files = [f for f in self.app_state.files if f.file_id not in ids]
        for fid in ids:
            self.app_state.segments_by_file.pop(fid, None)
            self.app_state.paragraph_segments_by_file.pop(fid, None)
        self.regenerate_groups_by_position(); self.refresh()

    def delete_all(self):
        if not self.app_state.files: return
        if not messagebox.askyesno(self.t('delete_all'), self.t('remove_files_confirm', count=len(self.app_state.files))):
            return
        self._snapshot(); self.app_state.files.clear(); self.app_state.segments_by_file.clear(); self.app_state.paragraph_segments_by_file.clear(); self.app_state.alignments.clear(); self.app_state.paragraph_alignments.clear(); self.app_state.settings['file_columns'] = []; self.app_state.settings['group_statuses'] = {}
        self.refresh(); self.callbacks.get('refresh_alignment', lambda: None)()

    def move_selected(self, delta: int):
        panel = self.active_panel()
        if panel: panel.move_selected(delta)

    def move_top(self):
        panel = self.active_panel()
        if panel: panel.move_top()

    def move_bottom(self):
        panel = self.active_panel()
        if panel: panel.move_bottom()

    def auto_sort(self):
        panel = self.active_panel()
        if panel: panel.auto_sort()

    def start_segmentation(self):
        return self.start_sentence_segmentation()

    def start_sentence_segmentation(self):
        gid = self.selected_group_id()
        cb = self.callbacks.get('segment_sentence_group') or self.callbacks.get('segment_current_group') or self.callbacks.get('segment_files')
        if callable(cb):
            cb(gid)

    def start_paragraph_segmentation(self):
        gid = self.selected_group_id()
        cb = self.callbacks.get('segment_paragraph_group') or self.callbacks.get('segment_current_group') or self.callbacks.get('segment_files')
        if callable(cb):
            cb(gid)

    def preview_record(self, rec: FileRecord):
        top = tk.Toplevel(self); top.title(self.t('preview_title', filename=rec.filename)); top.geometry('860x640')
        txt = tk.Text(top, wrap='word', font=('Microsoft YaHei UI', 10), bg=PROOFLENS_COLORS['panel'], fg=PROOFLENS_COLORS['text'])
        txt.pack(fill='both', expand=True, padx=8, pady=8)
        if not rec.text:
            try:
                rec.text = read_document(rec.path, preserve_paragraphs=self.app_state.settings.get('preserve_paragraphs', True), remove_excessive_spaces=self.app_state.settings.get('remove_excessive_spaces', True))
                rec.char_count, rec.paragraph_count = text_stats(rec.text)
                rec.status = 'read'
            except Exception as exc:
                rec.status = 'read_failed'
                rec.note = str(exc)
        txt.insert('1.0', rec.text or '(No text loaded)')

    def preview_text(self):
        recs = self.selected_records()
        if recs: self.preview_record(recs[0])

    def preview_segmentation_record(self, rec: FileRecord):
        if not rec.text:
            self._read_record(rec)
        top = tk.Toplevel(self)
        top.title(self.t('segmentation_preview_title', filename=rec.filename))
        top.geometry('980x700')
        top.grid_rowconfigure(1, weight=1)
        top.grid_columnconfigure(0, weight=1)
        ttk.Label(top, text=self.t('segmentation_preview_hint', segmenter=describe_profile(self.app_state.settings, rec.lang or 'en', 'sentence'))).grid(row=0, column=0, sticky='ew', padx=8, pady=6)
        wrap = ttk.PanedWindow(top, orient='horizontal')
        wrap.grid(row=1, column=0, sticky='nsew', padx=8, pady=4)
        left = ttk.Frame(wrap); right = ttk.Frame(wrap)
        wrap.add(left, weight=1); wrap.add(right, weight=1)
        ttk.Label(left, text=self.t('original_text')).pack(anchor='w')
        ttk.Label(right, text=self.t('segmented_text')).pack(anchor='w')
        raw = tk.Text(left, wrap='word')
        segtxt = tk.Text(right, wrap='word')
        raw.pack(fill='both', expand=True)
        segtxt.pack(fill='both', expand=True)
        raw.insert('1.0', rec.text or '')
        try:
            segs = split_text(rec.text or '', rec.lang or 'en', rec.file_id, mode='auto', settings=self.app_state.settings)
            segtxt.insert('1.0', '\n'.join(f'{i+1}. {s.text}' for i, s in enumerate(segs)))
        except Exception as exc:
            segtxt.insert('1.0', self.t('segmentation_failed_detail', error=str(exc)))
        bar = ttk.Frame(top)
        bar.grid(row=2, column=0, sticky='ew', padx=8, pady=8)
        def save_segments():
            try:
                segs = split_text(raw.get('1.0', 'end-1c'), rec.lang or 'en', rec.file_id, mode='auto', settings=self.app_state.settings)
                self.app_state.segments_by_file[rec.file_id] = segs
                rec.text = raw.get('1.0', 'end-1c')
                rec.sentence_count = len(segs)
                rec.segmentation_engine = describe_profile(self.app_state.settings, rec.lang or 'en', 'sentence')
                rec.segmentation_model = rec.segmentation_engine
                rec.segmentation_level = 'sentence'
                rec.status = 'segmented'
                self.refresh()
                top.destroy()
            except Exception as exc:
                messagebox.showerror(self.t('segmentation_failed'), str(exc))
        ttk.Button(bar, text=self.t('save_segmentation'), command=save_segments).pack(side='left')
        ttk.Button(bar, text=self.t('close'), command=top.destroy).pack(side='right')

    def preview_segmentation(self):
        recs = self.selected_records()
        if recs:
            self.preview_segmentation_record(recs[0])

    def regenerate_groups_by_position(self):
        cols = self.column_order()
        max_len = 0
        by_col = {}
        for col in cols:
            recs = sorted([f for f in self.app_state.files if self.record_column_key(f) == col], key=lambda f: f.sort_order)
            by_col[col] = recs
            max_len = max(max_len, len(recs))
            for i, r in enumerate(recs, 1): r.sort_order = i
        for i in range(max_len):
            gid = f'set_{i+1:03d}'
            for col in cols:
                if i < len(by_col[col]): by_col[col][i].group_id = gid
        self.callbacks.get('log', print)(self.t('file_order_updated'))
        self._update_status()

    def edit_group_id(self, fid: str):
        rec = next((f for f in self.app_state.files if f.file_id == fid), None)
        if not rec: return
        val = simpledialog.askstring(self.t('change_group_title'), 'Group ID:', initialvalue=rec.group_id)
        if val is None: return
        self._snapshot(); rec.group_id = val; self.refresh()

    def check_pairing(self):
        cols = self.column_order()
        by_col = {c: [f for f in self.app_state.files if self.record_column_key(f) == c] for c in cols}
        counts = {column_display_name(c, self.app_state.files, self.ui_lang): len(v) for c, v in by_col.items()}
        if len(set(counts.values())) <= 1:
            messagebox.showinfo(self.t('pairing_ok_title'), self.t('pairing_ok'))
        else:
            msg = '\n'.join(f'{k}: {v}' for k, v in counts.items())
            messagebox.showwarning(self.t('pairing_mismatch_title'), self.t('pairing_mismatch', msg=msg))
        self._update_status()

    def _pairing_mismatch(self):
        counts = [len([f for f in self.app_state.files if self.record_column_key(f) == c]) for c in self.column_order()]
        return len(set(counts)) > 1 if counts else False

    def _update_status(self):
        cols = self.column_order()
        files = len(self.app_state.files)
        selected = len(self.selected_records()) if self.panels else 0
        self.status_var.set(self.t('file_count_status', files=files, columns=len(cols), selected=selected, mismatch=self.t('yes') if self._pairing_mismatch() else self.t('no')))

    # Compatibility methods used by legacy menus/settings.
    def modify_language(self):
        panel = self.active_panel()
        if panel: panel.modify_language()

    def modify_group(self):
        recs = self.selected_records()
        if recs: self.edit_group_id(recs[0].file_id)

    def generate_groups(self):
        self.regenerate_groups_by_position(); self.refresh(); self.check_pairing()

    def reload_selected(self):
        recs = self.selected_records(); self._snapshot()
        for r in recs: self._read_record(r)
        self.refresh()

    def delete_current_language(self):
        recs = self.selected_records()
        if not recs: return
        lang = recs[0].lang
        self._snapshot(); self.app_state.files = [f for f in self.app_state.files if f.lang != lang]; self.regenerate_groups_by_position(); self.refresh()

    def delete_current_group(self):
        recs = self.selected_records()
        if not recs: return
        gid = recs[0].group_id
        self._snapshot(); self.app_state.files = [f for f in self.app_state.files if f.group_id != gid]; self.regenerate_groups_by_position(); self.refresh()

    def delete_failed(self):
        self._snapshot(); self.app_state.files = [f for f in self.app_state.files if 'failed' not in f.status]; self.regenerate_groups_by_position(); self.refresh()

    def delete_unspecified(self):
        self._snapshot(); self.app_state.files = [f for f in self.app_state.files if f.lang]; self.regenerate_groups_by_position(); self.refresh()

    def sort_by_column(self, column: str):
        self.auto_sort()

    def open_file(self):
        recs = self.selected_records()
        if recs: open_path(recs[0].path)

    def open_folder(self):
        recs = self.selected_records()
        if recs: open_path(str(Path(recs[0].path).parent))

    def file_properties(self):
        recs = self.selected_records()
        if recs: messagebox.showinfo(self.t('file_properties'), '\n'.join(f'{k}: {v}' for k,v in recs[0].to_dict().items() if k != 'text'))
