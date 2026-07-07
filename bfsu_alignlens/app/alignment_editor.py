from __future__ import annotations

import bisect
import math
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.datatypes import AlignmentUnit
from core.utils import UndoRedoStack
from core.language_registry import column_display_name
from core.exporters import export_excel, export_line_txt, export_tmx, export_xml, export_word, export_json
from core.multi_txt_exporter import export_multi_txt, MultiTxtOptions
from core.llm_checker import row_signature as llm_row_signature
from app.theme import PROOFLENS_COLORS, configure_text_widget


class WrappingToolbar(ttk.Frame):
    """A small responsive toolbar that wraps buttons as the window narrows."""
    def __init__(self, master, pad_x: int = 2, pad_y: int = 2):
        super().__init__(master)
        self.pad_x = pad_x
        self.pad_y = pad_y
        self.widgets: List[ttk.Button] = []
        self._layout_after: Optional[str] = None
        self.bind('<Configure>', lambda e: self._schedule_layout())

    def add_button(self, text: str, command, style: str | None = None) -> ttk.Button:
        btn = ttk.Button(self, text=text, command=command)
        if style:
            btn.configure(style=style)
        self.widgets.append(btn)
        self._schedule_layout()
        return btn

    def _schedule_layout(self):
        if self._layout_after:
            try:
                self.after_cancel(self._layout_after)
            except Exception:
                pass
        self._layout_after = self.after(20, self._layout)

    def _layout(self):
        width = max(self.winfo_width(), 200)
        row = 0
        col = 0
        used = 0
        for btn in self.widgets:
            btn.grid_forget()
        for btn in self.widgets:
            req = max(btn.winfo_reqwidth(), 70) + self.pad_x * 2
            if col and used + req > width:
                row += 1
                col = 0
                used = 0
            btn.grid(row=row, column=col, padx=self.pad_x, pady=self.pad_y, sticky='w')
            used += req
            col += 1
        for c in range(max(col, 1)):
            self.grid_columnconfigure(c, weight=0)



class AlignmentEditorFrame(ttk.Frame):
    """Virtualized multi-column alignment editor.

    Older versions created a real Text widget for every visible and invisible
    alignment cell. Large corpora could therefore create thousands of Tk widgets
    and make scrolling/window resizing extremely slow. This editor keeps all
    alignment data in memory, but only creates Text widgets for rows currently
    visible in the canvas plus a small buffer above and below the viewport.
    """

    def __init__(self, master, app_state, callbacks: dict):
        super().__init__(master)
        self.app_state = app_state
        self.callbacks = callbacks
        self.t = callbacks.get('t', lambda key, **kwargs: key.format(**kwargs) if kwargs else key)
        self.column_keys: List[str] = []
        self.cell_widgets: Dict[Tuple[int, str], tk.Text] = {}
        self.selected_cell: Optional[Tuple[int, str]] = None
        self.row_y: Dict[int, int] = {}
        self.row_tops: List[int] = []
        self.row_heights: List[int] = []
        self.total_width = 1000
        self.total_height = 100
        self.row_no_w = max(44, int(self.app_state.settings.get('editor_row_no_width', 64) or 64))
        self.sim_w = max(64, int(self.app_state.settings.get('editor_similarity_width', 92) or 92))
        self.status_w = max(92, int(self.app_state.settings.get('editor_status_width', 150) or 150))
        self.meta_w = self.row_no_w + self.status_w
        self.col_w = 360
        self.header_h = 42
        self._redraw_after: Optional[str] = None
        self._render_after: Optional[str] = None
        self._last_canvas_width = 0
        self._active_text_widget: Optional[tk.Text] = None
        self._resize_meta: Optional[str] = None
        self.undo = UndoRedoStack(100)
        self._restoring_undo = False
        self._build()

    def _build(self):
        info = ttk.Frame(self)
        info.pack(fill='x', padx=4, pady=(4, 0))
        self.group_info_var = tk.StringVar(value=self._group_info_text())
        ttk.Label(info, textvariable=self.group_info_var, style='Gold.TLabel').pack(side='left', fill='x', expand=True)
        ttk.Button(info, text=self.t('open_group'), command=self.callbacks.get('open_group')).pack(side='right', padx=2)
        ttk.Button(info, text=self.t('close_group'), command=self.callbacks.get('close_group')).pack(side='right', padx=2)
        ttk.Button(info, text=self.t('complete_alignment'), command=self.callbacks.get('complete_group'), style='Accent.TButton').pack(side='right', padx=2)

        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=4, pady=(4, 2))
        self.toolbar_buttons: List[ttk.Button] = []

        align_bar = WrappingToolbar(toolbar)
        align_bar.pack(fill='x', anchor='w')
        align_buttons = [
            (self.t('manual_paragraph_alignment'), self.callbacks.get('manual_paragraph_align')),
            (self.t('manual_sentence_alignment'), self.callbacks.get('manual_sentence_align')),
            (self.t('paragraph_alignment'), self.callbacks.get('paragraph_align')),
            (self.t('sentence_alignment'), self.callbacks.get('sentence_align')),
            (self.t('recompute_similarity'), self.callbacks.get('recompute_similarity')),
            (self.t('recompute_current_similarity'), self.callbacks.get('recompute_current_similarity')),
            (self.t('llm_paragraph_alignment'), self.callbacks.get('llm_paragraph_align')),
            (self.t('llm_sentence_alignment'), self.callbacks.get('llm_sentence_align')),
            (self.t('llm_validate_editor'), self.callbacks.get('llm_check_current')),
            (self.t('check_low_similarity_rows'), self.callbacks.get('check_low_similarity')),
            (self.t('prev_highlight'), self.goto_prev_highlight),
            (self.t('next_highlight'), self.goto_next_highlight),
        ]
        for text, cmd in align_buttons:
            self.toolbar_buttons.append(align_bar.add_button(text, cmd, style='Accent.TButton' if text in {self.t('paragraph_alignment'), self.t('sentence_alignment')} else None))

        edit_bar = WrappingToolbar(toolbar)
        edit_bar.pack(fill='x', anchor='w')
        edit_buttons = [
            (self.t('insert_blank_row'), self.insert_blank),
            (self.t('delete_row_title'), self.delete_rows),
            (self.t('move_row_up'), lambda: self.move_rows(-1)),
            (self.t('move_row_down'), lambda: self.move_rows(1)),
            (self.t('move_cell_up'), lambda: self.move_cell(-1)),
            (self.t('move_cell_down'), lambda: self.move_cell(1)),
            (self.t('merge_cell_up'), lambda: self.merge_cell(-1)),
            (self.t('merge_cell_down'), lambda: self.merge_cell(1)),
            (self.t('split_cell_at_cursor'), self.split_cell),
            (self.t('mark_confirmed'), self.mark_confirmed),
            (self.t('mark_review'), self.mark_needs_review),
            (self.t('note_title'), self.add_note),
            (self.t('export'), self.export_dialog),
            (self.t('multi_txt'), self.export_multi_txt_dialog),
        ]
        for text, cmd in edit_buttons:
            self.toolbar_buttons.append(edit_bar.add_button(text, cmd))

        self.main_pane = ttk.PanedWindow(self, orient='horizontal')
        self.main_pane.pack(fill='both', expand=True, padx=4, pady=4)
        left = ttk.Frame(self.main_pane)
        right = ttk.Frame(self.main_pane, width=260)
        self.main_pane.add(left, weight=10)
        self.main_pane.add(right, weight=1)

        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(left, bg=PROOFLENS_COLORS['panel2'], highlightthickness=0)
        self.vbar = ttk.Scrollbar(left, orient='vertical', command=self._yview)
        self.hbar = ttk.Scrollbar(left, orient='horizontal', command=self._xview)
        self.canvas.configure(yscrollcommand=self._on_yscroll, xscrollcommand=self.hbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.vbar.grid(row=0, column=1, sticky='ns')
        self.hbar.grid(row=1, column=0, sticky='ew')
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind('<MouseWheel>', self._mousewheel)
        self.canvas.bind('<Button-4>', self._mousewheel)
        self.canvas.bind('<Button-5>', self._mousewheel)
        self.canvas.bind('<ButtonPress-1>', self._canvas_button_press)
        self.canvas.bind('<B1-Motion>', self._canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self._canvas_button_release)
        self.canvas.bind('<Motion>', self._canvas_motion)

        ttk.Label(right, text=self.t('llm_suggestions'), style='Gold.TLabel').pack(anchor='w')
        suggestion_frame = ttk.Frame(right)
        suggestion_frame.pack(fill='both', expand=True, pady=4)
        suggestion_frame.grid_rowconfigure(0, weight=1)
        suggestion_frame.grid_columnconfigure(0, weight=1)
        self.suggestion_tree = ttk.Treeview(suggestion_frame, columns=('row', 'severity', 'issue', 'operation', 'confidence'), show='headings', height=8)
        self.suggestion_vbar = ttk.Scrollbar(suggestion_frame, orient='vertical', command=self.suggestion_tree.yview)
        self.suggestion_tree.configure(yscrollcommand=self.suggestion_vbar.set)
        for c, h, w in [('row', self.t('row_no'), 48), ('severity', self.t('severity'), 70), ('issue', self.t('issue'), 90), ('operation', self.t('operation'), 90), ('confidence', self.t('confidence'), 55)]:
            self.suggestion_tree.heading(c, text=h)
            self.suggestion_tree.column(c, width=w, anchor='w')
        self.suggestion_tree.grid(row=0, column=0, sticky='nsew')
        self.suggestion_vbar.grid(row=0, column=1, sticky='ns')
        self.suggestion_tree.bind('<MouseWheel>', lambda e: (self.suggestion_tree.yview_scroll(int(-1*(e.delta/120)), 'units'), 'break')[-1])
        self.suggestion_tree.bind('<Button-4>', lambda e: (self.suggestion_tree.yview_scroll(-1, 'units'), 'break')[-1])
        self.suggestion_tree.bind('<Button-5>', lambda e: (self.suggestion_tree.yview_scroll(1, 'units'), 'break')[-1])
        self.suggestion_tree.bind('<<TreeviewSelect>>', lambda e: self._show_selected_suggestion_detail())
        self.suggestion_tree.bind('<Double-1>', lambda e: (self.jump_to_selected_suggestion(), 'break')[-1])
        btns = ttk.Frame(right)
        btns.pack(fill='x')
        self.toolbar_buttons.append(ttk.Button(btns, text=self.t('apply_current_suggestion'), command=self.apply_suggestion))
        self.toolbar_buttons[-1].pack(side='left')
        self.toolbar_buttons.append(ttk.Button(btns, text=self.t('apply_all_suggestions'), command=self.apply_all_suggestions))
        self.toolbar_buttons[-1].pack(side='left', padx=4)
        self.toolbar_buttons.append(ttk.Button(btns, text=self.t('ignore_current_suggestion'), command=self.ignore_suggestion))
        self.toolbar_buttons[-1].pack(side='left', padx=4)
        self.toolbar_buttons.append(ttk.Button(btns, text=self.t('ignore_all_suggestions'), command=self.ignore_all_suggestions))
        self.toolbar_buttons[-1].pack(side='left', padx=4)
        detail_frame = ttk.Frame(right)
        detail_frame.pack(fill='x', pady=6)
        detail_frame.grid_rowconfigure(0, weight=1)
        detail_frame.grid_columnconfigure(0, weight=1)
        self.suggestion_text = tk.Text(detail_frame, height=9, wrap='word')
        configure_text_widget(self.suggestion_text)
        self.suggestion_text_vbar = ttk.Scrollbar(detail_frame, orient='vertical', command=self.suggestion_text.yview)
        self.suggestion_text.configure(yscrollcommand=self.suggestion_text_vbar.set)
        self.suggestion_text.grid(row=0, column=0, sticky='nsew')
        self.suggestion_text_vbar.grid(row=0, column=1, sticky='ns')
        self.suggestion_text.bind('<MouseWheel>', lambda e: (self.suggestion_text.yview_scroll(int(-1*(e.delta/120)), 'units'), 'break')[-1])
        self.suggestion_text.bind('<Button-4>', lambda e: (self.suggestion_text.yview_scroll(-1, 'units'), 'break')[-1])
        self.suggestion_text.bind('<Button-5>', lambda e: (self.suggestion_text.yview_scroll(1, 'units'), 'break')[-1])

        self.busy = False
        self.menu = tk.Menu(self, tearoff=0)
        for label, cmd in [
            (self.t('edit_cell'), self.edit_cell),
            (self.t('move_cell_up'), lambda: self.move_cell(-1)),
            (self.t('move_cell_down'), lambda: self.move_cell(1)),
            (self.t('clear_cell'), self.clear_cell),
            (self.t('merge_cell_up'), lambda: self.merge_cell(-1)),
            (self.t('merge_cell_down'), lambda: self.merge_cell(1)),
            (self.t('split_cell_at_cursor'), self.split_cell),
            (self.t('insert_blank_row'), self.insert_blank),
            (self.t('delete_row_title'), self.delete_rows),
            (self.t('mark_confirmed'), self.mark_confirmed),
            (self.t('note_title'), self.add_note),
        ]:
            self.menu.add_command(label=label, command=cmd)

    def _group_info_text(self) -> str:
        gid = getattr(self.app_state, 'group_id', '') or self.app_state.settings.get('current_group_id', '') or ''
        files = [getattr(f, 'filename', '') for f in getattr(self.app_state, 'files', []) if getattr(f, 'group_id', gid) == gid or len(getattr(self.app_state, 'files', [])) <= 8]
        level = self.app_state.settings.get('alignment_unit', 'sentence')
        if self.app_state.alignments:
            level = getattr(self.app_state.alignments[0], 'alignment_level', level) or level
        title = self.t('current_text_group', group=gid or '-')
        if files:
            title += '  |  ' + ' ; '.join(files[:4])
            if len(files) > 4:
                title += f' ... (+{len(files)-4})'
        title += '  |  ' + (self.t('paragraph') if level == 'paragraph' else self.t('sentence'))
        return title

    def update_group_info(self):
        if hasattr(self, 'group_info_var'):
            self.group_info_var.set(self._group_info_text())

    def _notify_changed(self):
        cb = self.callbacks.get('on_editor_changed')
        if callable(cb):
            try:
                cb(self)
            except Exception:
                pass

    def set_busy(self, busy: bool):
        self._sync_all_widgets()
        self.busy = bool(busy)
        state = 'disabled' if self.busy else 'normal'
        for btn in getattr(self, 'toolbar_buttons', []):
            try:
                btn.configure(state=state)
            except Exception:
                pass
        for w in list(self.cell_widgets.values()):
            try:
                w.configure(state=state)
            except Exception:
                pass

    def _editing_allowed(self) -> bool:
        return not getattr(self, 'busy', False)

    def _ensure_selected_cell(self) -> bool:
        # Prefer the widget that currently owns the insertion cursor.  This makes
        # toolbar buttons act on the cell where the user is actually editing,
        # even when a previous selected_cell value still exists.
        focus = self.focus_get()
        for key, widget in self.cell_widgets.items():
            if widget == focus:
                self.selected_cell = key
                return True
        if self.selected_cell:
            row, col = self.selected_cell
            if 1 <= row <= len(self.app_state.alignments) and col in self.column_keys:
                return True
        if self.app_state.alignments and self.column_keys:
            self.selected_cell = (1, self.column_keys[0])
            return True
        return False

    def _meta_resize_hit(self, event) -> Optional[str]:
        if event.y > self.header_h:
            return None
        x = int(self.canvas.canvasx(event.x))
        boundaries = [
            ('row_no', self.row_no_w),
            ('status', self.row_no_w + self.status_w),
        ]
        for name, bx in boundaries:
            if abs(x - bx) <= 6:
                return name
        return None

    def _canvas_motion(self, event):
        hit = self._meta_resize_hit(event)
        try:
            self.canvas.configure(cursor='sb_h_double_arrow' if hit else '')
        except Exception:
            pass

    def _canvas_button_press(self, event):
        hit = self._meta_resize_hit(event)
        if hit:
            self._resize_meta = hit
            return 'break'
        return None

    def _canvas_drag(self, event):
        if not self._resize_meta:
            return None
        x = max(0, int(self.canvas.canvasx(event.x)))
        if self._resize_meta == 'row_no':
            self.app_state.settings['editor_row_no_width'] = max(44, min(180, x))
        elif self._resize_meta == 'status':
            row_w = int(self.app_state.settings.get('editor_row_no_width', self.row_no_w) or self.row_no_w)
            self.app_state.settings['editor_status_width'] = max(92, min(320, x - row_w))
        self._redraw_debounced()
        return 'break'

    def _canvas_button_release(self, event):
        if self._resize_meta:
            self._resize_meta = None
            cb = self.callbacks.get('save_settings')
            if cb:
                cb()
            self.refresh()
            return 'break'
        return None

    def _on_canvas_configure(self, event):
        new_width = max(int(event.width), 200)
        # Avoid a full layout recomputation for tiny resize noise.
        if abs(new_width - self._last_canvas_width) < 18:
            self._schedule_render()
            return
        self._last_canvas_width = new_width
        self._redraw_debounced()

    def _yview(self, *args):
        self.canvas.yview(*args)
        self._schedule_render()

    def _xview(self, *args):
        self.canvas.xview(*args)
        self._schedule_render()

    def _on_yscroll(self, first, last):
        self.vbar.set(first, last)
        self._schedule_render()

    def _mousewheel(self, event):
        if not self.winfo_ismapped():
            return 'break'
        if getattr(event, 'num', None) == 4:
            delta = -3
        elif getattr(event, 'num', None) == 5:
            delta = 3
        else:
            delta = int(-1 * (event.delta / 120)) if event.delta else 0
        if delta:
            self.canvas.yview_scroll(delta, 'units')
            self._schedule_render()
        return 'break'

    def _redraw_debounced(self):
        if self._redraw_after:
            try:
                self.after_cancel(self._redraw_after)
            except Exception:
                pass
        self._redraw_after = self.after(120, self.refresh)

    def _schedule_render(self):
        if self._render_after:
            try:
                self.after_cancel(self._render_after)
            except Exception:
                pass
        self._render_after = self.after(35, self._render_visible)

    def _infer_columns(self) -> List[str]:
        cols: List[str] = []
        defs = {d.get('column_key'): dict(d) for d in (self.app_state.settings.get('file_columns', []) or []) if d.get('column_key')}
        files = self.app_state.files
        tmp = dict(defs)
        if files:
            def rec_col(f):
                return f.column_key or (f'source_{f.lang}' if f.alignment_role == 'source' else f'target_{int(f.target_index or 1):02d}_{f.lang}')
            for f in files:
                tmp[rec_col(f)] = {
                    'alignment_role': f.alignment_role,
                    'target_index': int(f.target_index or 1),
                }
        if tmp:
            def k(col):
                d = tmp[col]
                return (0 if d.get('alignment_role') == 'source' else 1, int(d.get('target_index') or 1), col)
            cols = sorted(tmp.keys(), key=k)
        for u in self.app_state.alignments:
            for c in u.segments.keys():
                if c not in cols:
                    cols.append(c)
        return cols

    def _source_column(self) -> str:
        defs = {d.get('column_key'): dict(d) for d in (self.app_state.settings.get('file_columns', []) or []) if d.get('column_key')}
        for col in self.column_keys:
            if defs.get(col, {}).get('alignment_role') == 'source' or col.startswith('source_'):
                return col
        return self.column_keys[0] if self.column_keys else ''

    def _target_columns(self) -> List[str]:
        src = self._source_column()
        return [c for c in self.column_keys if c and c != src]

    def _compute_layout(self):
        self.row_y.clear()
        self.row_tops.clear()
        self.row_heights.clear()
        width = max(self.canvas.winfo_width(), 1000)
        self.row_no_w = max(44, int(self.app_state.settings.get('editor_row_no_width', 64) or 64))
        self.sim_w = max(64, int(self.app_state.settings.get('editor_similarity_width', 92) or 92))
        self.status_w = max(92, int(self.app_state.settings.get('editor_status_width', 150) or 150))
        self.meta_w = self.row_no_w + self.status_w
        target_count = len(self._target_columns())
        text_available = width - self.meta_w - target_count * self.sim_w - 20
        self.col_w = max(360, int(text_available / max(len(self.column_keys), 1)))
        self.header_h = 42
        self.total_width = self.meta_w + len(self.column_keys) * self.col_w + target_count * self.sim_w + 12
        char_per_line = max(18, int(self.col_w / 13))
        y = self.header_h
        for idx, unit in enumerate(self.app_state.alignments, 1):
            unit.row_id = idx
            texts = [unit.segments.get(col, '') for col in self.column_keys]
            if texts:
                line_counts = [max(2, math.ceil(len(t) / char_per_line) + t.count('\n')) for t in texts]
                row_h = min(360, max(58, max(line_counts) * 23 + 18))
            else:
                row_h = 58
            self.row_y[idx] = y
            self.row_tops.append(y)
            self.row_heights.append(row_h)
            y += row_h
        self.total_height = max(y + 10, self.header_h + 80)
        self.canvas.configure(scrollregion=(0, 0, self.total_width, self.total_height))

    def refresh(self, sync_widgets: bool = True):
        if sync_widgets:
            self._sync_all_widgets()
        self.update_group_info()
        self.column_keys = self._infer_columns()
        for w in list(self.cell_widgets.values()):
            try:
                w.destroy()
            except Exception:
                pass
        self.cell_widgets.clear()
        self.canvas.delete('all')
        if not self.column_keys:
            self.total_width = max(self.canvas.winfo_width(), 1000)
            self.total_height = 120
            self.canvas.configure(scrollregion=(0, 0, self.total_width, self.total_height))
            self.canvas.create_text(30, 30, anchor='nw', text=self.t('no_alignment_rows_hint'), fill=PROOFLENS_COLORS['muted'], font=('Microsoft YaHei UI', 12), tags=('grid',))
            self.refresh_suggestions()
            return
        self._compute_layout()
        self._render_visible()
        self.refresh_suggestions()

    def _discard_cell_widgets(self):
        for w in list(self.cell_widgets.values()):
            try:
                w.destroy()
            except Exception:
                pass
        self.cell_widgets.clear()

    def _refresh_after_structure_change(self):
        # Row operations already synchronized old widgets before changing the
        # data model.  Do not sync again here: old virtualized widgets are keyed
        # by old row numbers and would overwrite the newly inserted/moved rows.
        self._discard_cell_widgets()
        self.refresh(sync_widgets=False)
        self._notify_changed()

    def _visible_row_bounds(self) -> tuple[int, int]:
        n = len(self.app_state.alignments)
        if not n:
            return 0, -1
        top = max(0, int(self.canvas.canvasy(0)))
        bottom = top + max(1, self.canvas.winfo_height())
        buffer_rows = int(self.app_state.settings.get('virtual_editor_buffer_rows', 4) or 4)
        pixel_buffer = max(260, buffer_rows * 64)
        start = max(0, bisect.bisect_right(self.row_tops, top - pixel_buffer) - 1)
        while start > 0 and self.row_tops[start] + self.row_heights[start] > top - pixel_buffer:
            start -= 1
        end = min(n - 1, bisect.bisect_right(self.row_tops, bottom + pixel_buffer))
        return start, end

    def _is_highlighted_row(self, unit: AlignmentUnit) -> bool:
        if unit.confirmed:
            return False
        threshold = float(self.app_state.settings.get('paragraph_min_similarity_threshold', 0.50) if getattr(unit, 'alignment_level', 'sentence') == 'paragraph' else self.app_state.settings.get('min_similarity_threshold', 0.65))
        vals = list((unit.similarities or {}).values())
        if vals and any(float(v) < threshold for v in vals):
            return True
        if not vals and unit.similarity is not None and float(unit.similarity or 0.0) < threshold:
            return True
        if not vals and unit.issue_type == 'low_similarity':
            return True
        if unit.status in {'llm_low_confidence'}:
            return True
        return False

    def _display_status(self, status: str) -> str:
        if not status:
            return ''
        return self.t('status_' + status) if self.t('status_' + status) != 'status_' + status else status

    def _row_color(self, unit: AlignmentUnit) -> str:
        if unit.confirmed:
            return PROOFLENS_COLORS['ok']
        if self._is_highlighted_row(unit):
            return PROOFLENS_COLORS['low']
        if 'empty' in (unit.status or '') or 'residual' in (unit.status or ''):
            return PROOFLENS_COLORS['empty']
        return PROOFLENS_COLORS['panel']

    def _render_visible(self):
        if not self.column_keys:
            return
        start, end = self._visible_row_bounds()
        visible_keys = {(row + 1, col) for row in range(start, end + 1) for col in self.column_keys}
        for key, widget in list(self.cell_widgets.items()):
            if key not in visible_keys:
                try:
                    row, col = key
                    self._save_cell_from_widget(row, col)
                    widget.destroy()
                except Exception:
                    pass
                self.cell_widgets.pop(key, None)
        self.canvas.delete('grid')
        self._draw_header()
        if end < start:
            return
        for row0 in range(start, end + 1):
            unit = self.app_state.alignments[row0]
            row_no = row0 + 1
            y = self.row_tops[row0]
            row_h = self.row_heights[row0]
            tag_color = self._row_color(unit)
            # Read-only metadata columns: row number and editing/review status.
            # Similarity is displayed next to each target/translation column.
            x0 = 0
            self.canvas.create_rectangle(x0, y, x0 + self.row_no_w, y + row_h, fill=tag_color, outline=PROOFLENS_COLORS['line'], tags=('grid',))
            self.canvas.create_text(x0 + 10, y + 8, anchor='nw', text=str(row_no), fill=PROOFLENS_COLORS['deep'], font=('Microsoft YaHei UI', 10, 'bold'), tags=('grid',))
            x0 += self.row_no_w
            self.canvas.create_rectangle(x0, y, x0 + self.status_w, y + row_h, fill=tag_color, outline=PROOFLENS_COLORS['line'], tags=('grid',))
            self.canvas.create_text(x0 + 8, y + 8, anchor='nw', text=self._display_status(str(unit.status or ''))[:24], fill=PROOFLENS_COLORS['muted'], font=('Microsoft YaHei UI', 9), tags=('grid',))
            x = self.meta_w
            source_col = self._source_column()
            for col in self.column_keys:
                self.canvas.create_rectangle(x, y, x + self.col_w, y + row_h, fill=tag_color, outline=PROOFLENS_COLORS['line'], tags=('grid',))
                txt = self.cell_widgets.get((row_no, col))
                if txt is None or not txt.winfo_exists():
                    txt = tk.Text(self.canvas, wrap='word', undo=True, height=1, width=1)
                    configure_text_widget(txt)
                    txt.insert('1.0', unit.segments.get(col, ''))
                    if getattr(self, 'busy', False):
                        txt.configure(state='disabled')
                    self._bind_cell(txt, row_no, col)
                    self.cell_widgets[(row_no, col)] = txt
                self.canvas.create_window(x + 4, y + 4, width=self.col_w - 8, height=row_h - 8, window=txt, anchor='nw', tags=('grid',))
                x += self.col_w
                if col != source_col:
                    self.canvas.create_rectangle(x, y, x + self.sim_w, y + row_h, fill=tag_color, outline=PROOFLENS_COLORS['line'], tags=('grid',))
                    score = (unit.similarities or {}).get(col, unit.similarity if len(self._target_columns()) == 1 else None)
                    sim_text = '' if score is None else f'{float(score):.4f}'
                    self.canvas.create_text(x + 8, y + 8, anchor='nw', text=sim_text, fill=PROOFLENS_COLORS['deep'], font=('Microsoft YaHei UI', 9), tags=('grid',))
                    x += self.sim_w

    def _draw_header(self):
        self.canvas.create_rectangle(0, 0, self.total_width, self.header_h, fill=PROOFLENS_COLORS['deep'], outline=PROOFLENS_COLORS['deep'], tags=('grid',))
        x = 0
        for title, width in [(self.t('row_no'), self.row_no_w), (self.t('edit_status'), self.status_w)]:
            self.canvas.create_rectangle(x, 0, x + width, self.header_h, fill=PROOFLENS_COLORS['deep'], outline=PROOFLENS_COLORS['line'], tags=('grid',))
            self.canvas.create_text(x + 8, 13, anchor='nw', text=title, fill='white', font=('Microsoft YaHei UI', 10, 'bold'), tags=('grid',))
            x += width
        source_col = self._source_column()
        for col in self.column_keys:
            title = column_display_name(col, self.app_state.files, self.app_state.settings.get('gui_language', 'zh_sim'))
            self.canvas.create_rectangle(x, 0, x + self.col_w, self.header_h, fill=PROOFLENS_COLORS['deep'], outline=PROOFLENS_COLORS['line'], tags=('grid',))
            self.canvas.create_text(x + 8, 13, anchor='nw', text=title, fill='white', font=('Microsoft YaHei UI', 10, 'bold'), tags=('grid',))
            x += self.col_w
            if col != source_col:
                self.canvas.create_rectangle(x, 0, x + self.sim_w, self.header_h, fill=PROOFLENS_COLORS['deep'], outline=PROOFLENS_COLORS['line'], tags=('grid',))
                self.canvas.create_text(x + 8, 13, anchor='nw', text=self.t('similarity'), fill='white', font=('Microsoft YaHei UI', 10, 'bold'), tags=('grid',))
                x += self.sim_w

    def _bind_cell(self, txt: tk.Text, row: int, col: str):
        try:
            setattr(txt, '_alignlens_row', row)
            setattr(txt, '_alignlens_col', col)
        except Exception:
            pass
        txt.bind('<FocusOut>', lambda e, r=row, c=col: self._save_cell_from_widget(r, c))
        txt.bind('<FocusIn>', lambda e, r=row, c=col: self._select_cell(r, c, txt))
        txt.bind('<Button-1>', lambda e, r=row, c=col, w=txt: self._select_cell(r, c, w))
        txt.bind('<ButtonRelease-1>', lambda e, r=row, c=col, w=txt: self._select_cell(r, c, w))
        txt.bind('<Button-3>', lambda e, r=row, c=col: self._popup_cell(e, r, c))
        txt.bind('<Control-Up>', lambda e, r=row, c=col: self.move_cell(-1, r, c))
        txt.bind('<Control-Down>', lambda e, r=row, c=col: self.move_cell(1, r, c))
        txt.bind('<Control-z>', lambda e: (self.undo_action(), 'break')[-1])
        txt.bind('<Control-y>', lambda e: (self.redo_action(), 'break')[-1])
        txt.bind('<MouseWheel>', self._mousewheel)
        txt.bind('<Button-4>', self._mousewheel)
        txt.bind('<Button-5>', self._mousewheel)

    def _select_cell(self, row: int, col: str, widget: Optional[tk.Text] = None):
        self.selected_cell = (row, col)
        if widget is not None:
            self._active_text_widget = widget
            try:
                setattr(widget, '_alignlens_row', row)
                setattr(widget, '_alignlens_col', col)
            except Exception:
                pass

    def current_cell(self) -> Optional[Tuple[int, str]]:
        """Return the cell that currently owns keyboard focus.

        Virtualized Text widgets can be recreated while scrolling, so toolbar
        commands should not rely only on a stale selected_cell tuple.  This
        method first checks the real focused Text widget, then the last active
        widget, then falls back to selected_cell.
        """
        try:
            focus = self.focus_get()
        except Exception:
            focus = None
        for widget in (focus, self._active_text_widget):
            if isinstance(widget, tk.Text):
                try:
                    row = int(getattr(widget, '_alignlens_row'))
                    col = str(getattr(widget, '_alignlens_col'))
                    if 1 <= row <= len(self.app_state.alignments) and col in self.column_keys:
                        self.selected_cell = (row, col)
                        self._active_text_widget = widget
                        return self.selected_cell
                except Exception:
                    pass
        if self.selected_cell:
            row, col = self.selected_cell
            if 1 <= int(row) <= len(self.app_state.alignments) and col in self.column_keys:
                return self.selected_cell
        return None

    def _popup_cell(self, event, row: int, col: str):
        self._select_cell(row, col)
        self.menu.tk_popup(event.x_root, event.y_root)

    def _scroll_to_row(self, row: int):
        if not (1 <= row <= len(self.row_tops)):
            return
        y = self.row_tops[row - 1]
        visible_h = max(1, self.canvas.winfo_height())
        denom = max(self.total_height - visible_h, 1)
        self.canvas.yview_moveto(max(0.0, min(1.0, y / denom)))
        self._render_visible()

    def _unit(self, row: int) -> Optional[AlignmentUnit]:
        if 1 <= row <= len(self.app_state.alignments):
            return self.app_state.alignments[row - 1]
        return None

    def _snapshot(self) -> dict:
        return {
            'alignments': [u.to_dict() for u in self.app_state.alignments],
            'suggestions': [dict(s) for s in getattr(self.app_state, 'llm_suggestions', [])],
            'selected_cell': self.selected_cell,
        }

    def _restore_snapshot(self, snap: dict):
        self._restoring_undo = True
        try:
            self.app_state.alignments = [AlignmentUnit.from_dict(x) for x in snap.get('alignments', [])]
            if hasattr(self.app_state, 'llm_suggestions'):
                self.app_state.llm_suggestions = [dict(s) for s in snap.get('suggestions', [])]
            self.selected_cell = tuple(snap.get('selected_cell')) if snap.get('selected_cell') else None
            self._discard_cell_widgets()
            self.refresh(sync_widgets=False)
            self.refresh_suggestions()
        finally:
            self._restoring_undo = False
        self._notify_changed()

    def _push_undo_snapshot(self) -> None:
        if self._restoring_undo:
            return
        self.undo.push(self._snapshot())

    def _save_cell_from_widget(self, row: int, col: str):
        unit = self._unit(row)
        w = self.cell_widgets.get((row, col))
        if unit and w and w.winfo_exists():
            new_text = w.get('1.0', 'end').strip()
            if unit.segments.get(col, '') != new_text:
                self._push_undo_snapshot()
                unit.segments[col] = new_text
                unit.confirmed = False
                if unit.status not in {'needs_review', 'empty_or_residual'}:
                    unit.status = 'manual_edited'
                self._notify_changed()

    def _sync_all_widgets(self):
        for (row, col), w in list(self.cell_widgets.items()):
            if w.winfo_exists():
                self._save_cell_from_widget(row, col)

    def _focused_text_widget(self) -> Optional[tk.Text]:
        focus = self.focus_get()
        if isinstance(focus, tk.Text):
            return focus
        if self._active_text_widget is not None and self._active_text_widget.winfo_exists():
            return self._active_text_widget
        return None

    def undo_action(self) -> bool:
        if not self._editing_allowed():
            return False
        # Save the focused cell first so a direct text edit becomes an editor-level operation.
        self._sync_all_widgets()
        snap = self.undo.undo(self._snapshot())
        if not snap:
            return False
        self._restore_snapshot(snap)
        return True

    def redo_action(self) -> bool:
        if not self._editing_allowed():
            return False
        self._sync_all_widgets()
        snap = self.undo.redo(self._snapshot())
        if not snap:
            return False
        self._restore_snapshot(snap)
        return True

    def text_undo(self) -> bool:
        return self.undo_action()

    def text_redo(self) -> bool:
        return self.redo_action()

    def _push(self):
        if not self._editing_allowed():
            return False
        self._sync_all_widgets()
        self._push_undo_snapshot()
        return True

    def selected_units(self) -> List[AlignmentUnit]:
        self._ensure_selected_cell()
        if self.selected_cell:
            u = self._unit(self.selected_cell[0])
            return [u] if u else []
        return []

    def edit_cell(self):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        row, col = self.selected_cell
        self._scroll_to_row(row)
        def focus():
            w = self.cell_widgets.get((row, col))
            if w and w.winfo_exists():
                w.focus_set()
        self.after_idle(focus)

    def clear_cell(self):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        row, col = self.selected_cell
        u = self._unit(row)
        if not u:
            return
        self._push()
        u.segments[col] = ''
        u.status = 'manual_cell_clear'
        self._refresh_after_structure_change()

    def move_cell(self, delta: int, row: Optional[int] = None, col: Optional[str] = None):
        if not self._editing_allowed():
            return
        if row is None or col is None:
            if not self._ensure_selected_cell():
                return
            row, col = self.selected_cell
        if not col or row is None:
            return
        target = row + delta
        if not (1 <= target <= len(self.app_state.alignments)):
            return
        self._push()
        a = self.app_state.alignments[row - 1]
        b = self.app_state.alignments[target - 1]
        a.segments[col], b.segments[col] = b.segments.get(col, ''), a.segments.get(col, '')
        a.status = b.status = 'manual_cell_moved'
        self.selected_cell = (target, col)
        self._refresh_after_structure_change()
        self._scroll_to_row(target)

    def merge_cell(self, delta: int):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        row, col = self.selected_cell
        other = row + delta
        if not (1 <= other <= len(self.app_state.alignments)):
            return
        self._push()
        cur = self.app_state.alignments[row - 1]
        oth = self.app_state.alignments[other - 1]
        if delta < 0:
            oth.segments[col] = ' '.join(x for x in [oth.segments.get(col, ''), cur.segments.get(col, '')] if x).strip()
            cur.segments[col] = ''
            self.selected_cell = (other, col)
        else:
            cur.segments[col] = ' '.join(x for x in [cur.segments.get(col, ''), oth.segments.get(col, '')] if x).strip()
            oth.segments[col] = ''
        cur.status = oth.status = 'manual_cell_merged'
        self._refresh_after_structure_change()

    def split_cell(self):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        row, col = self.selected_cell
        u = self._unit(row)
        if not u:
            return
        w = self.cell_widgets.get((row, col))
        if w and w.winfo_exists():
            try:
                cursor = w.index('insert')
                left = w.get('1.0', cursor).rstrip()
                right = w.get(cursor, 'end').strip()
            except Exception:
                text = u.segments.get(col, '')
                left, right = text, ''
        else:
            text = u.segments.get(col, '')
            left, right = text, ''
        if not left or not right:
            messagebox.showwarning(self.t('split_cell_title'), self.t('split_cell_need_cursor'))
            return
        if not self._push():
            return
        u.segments[col] = left
        u.confirmed = False
        u.status = 'manual_split'
        u.issue_type = ''
        # Insert a new whole alignment row immediately after the current row.
        # Other source/translation columns intentionally remain blank so the
        # split does not push existing aligned content into the wrong row.
        new_unit = AlignmentUnit(0, u.group_id, {c: '' for c in self.column_keys}, similarity=0.0, similarities={}, status='manual_split', issue_type='', alignment_level=getattr(u, 'alignment_level', 'sentence'), positions={c: [] for c in self.column_keys})
        new_unit.segments[col] = right
        self.app_state.alignments.insert(row, new_unit)
        self._renumber()
        self.selected_cell = (row + 1, col)
        self._refresh_after_structure_change()
        self._scroll_to_row(row + 1)

    def insert_blank(self):
        if not self._editing_allowed():
            return
        self._ensure_selected_cell()
        if not self._push():
            return
        idx = self.selected_cell[0] - 1 if self.selected_cell else len(self.app_state.alignments)
        gid = self.app_state.alignments[idx].group_id if 0 <= idx < len(self.app_state.alignments) else 'set_001'
        self.app_state.alignments.insert(idx, AlignmentUnit(0, gid, {c: '' for c in self.column_keys}, status='manual_blank', alignment_level=self.app_state.settings.get('alignment_unit', 'sentence'), positions={c: [] for c in self.column_keys}))
        self._renumber()
        if self.column_keys:
            self.selected_cell = (idx + 1, self.selected_cell[1] if self.selected_cell and self.selected_cell[1] in self.column_keys else self.column_keys[0])
        self._refresh_after_structure_change()
        self._scroll_to_row(idx + 1)

    def delete_rows(self):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        row, _ = self.selected_cell
        if not messagebox.askyesno(self.t('delete_row_title'), self.t('delete_row_confirm', row=row)):
            return
        self._push()
        self.app_state.alignments.pop(row - 1)
        self.selected_cell = None
        self._renumber()
        self._refresh_after_structure_change()

    def move_rows(self, delta: int):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        row, col = self.selected_cell
        target = row + delta
        if not (1 <= target <= len(self.app_state.alignments)):
            return
        self._push()
        self.app_state.alignments[row - 1], self.app_state.alignments[target - 1] = self.app_state.alignments[target - 1], self.app_state.alignments[row - 1]
        self._renumber()
        self.selected_cell = (target, col)
        self._refresh_after_structure_change()
        self._scroll_to_row(target)

    def merge_previous(self):
        self.merge_cell(-1)

    def merge_next(self):
        self.merge_cell(1)

    def _renumber(self):
        for i, u in enumerate(self.app_state.alignments, 1):
            u.row_id = i

    def mark_confirmed(self):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        self._push()
        u = self._unit(self.selected_cell[0])
        if u:
            u.confirmed = True
            u.status = 'confirmed'
        self.refresh()
        self._notify_changed()

    def mark_needs_review(self):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        self._push()
        u = self._unit(self.selected_cell[0])
        if u:
            u.confirmed = False
            u.status = 'needs_review'
        self._refresh_after_structure_change()

    def add_note(self):
        if not self._editing_allowed() or not self._ensure_selected_cell():
            return
        u = self._unit(self.selected_cell[0])
        if not u:
            return
        val = simpledialog.askstring(self.t('note_title'), self.t('note_prompt'), initialvalue=u.note)
        if val is None:
            return
        self._push()
        u.note = val
        self._refresh_after_structure_change()

    def _current_group_id(self) -> str:
        return getattr(self.app_state, 'group_id', '') or self.app_state.settings.get('current_group_id', '') or ''

    def _current_group_suggestion_indices(self) -> List[int]:
        gid = self._current_group_id()
        return [i for i, s in enumerate(self.app_state.llm_suggestions) if not gid or not s.get('group_id') or s.get('group_id') == gid]

    def _suggestion_current_row(self, s: Dict) -> Optional[int]:
        """Resolve a pending LLM suggestion after row insert/delete/merge/move.

        Suggestions are created with the original row number plus a stable row
        unit_id and a compact text signature.  Row numbers can change after the
        user applies earlier suggestions, so we resolve by unit_id first, then
        by matching the original signature near the old row, and only finally by
        the current row number if it still exists.
        """
        anchor_uid = str(s.get('anchor_uid') or '').strip()
        if anchor_uid:
            for idx, u in enumerate(self.app_state.alignments, 1):
                if str(getattr(u, 'unit_id', '') or '') == anchor_uid:
                    s['current_row_id'] = idx
                    return idx
        sig = str(s.get('anchor_signature') or '').strip()
        src = self._source_column()
        targets = self._target_columns()
        if sig:
            candidates = []
            for idx, u in enumerate(self.app_state.alignments, 1):
                if llm_row_signature(u, src, targets) == sig:
                    candidates.append(idx)
            if candidates:
                old = int(s.get('current_row_id') or s.get('row_id') or 0)
                idx = min(candidates, key=lambda x: abs(x - old)) if old else candidates[0]
                s['current_row_id'] = idx
                return idx
        try:
            row = int(s.get('current_row_id') or s.get('row_id') or 0)
        except Exception:
            row = 0
        if 1 <= row <= len(self.app_state.alignments):
            # Last fallback: use row number, but mark it as row-number fallback
            # so the user knows this is less certain.
            s['current_row_id'] = row
            s.setdefault('resolution_note', 'resolved_by_row_number')
            return row
        s['status'] = 'stale'
        return None

    def refresh_suggestions(self):
        self.suggestion_tree.delete(*self.suggestion_tree.get_children())
        for i in self._current_group_suggestion_indices():
            s = self.app_state.llm_suggestions[i]
            cur = self._suggestion_current_row(s)
            row_label = cur if cur is not None else f"{s.get('row_id', '')}*"
            op = s.get('suggested_operation')
            if s.get('status') == 'stale':
                op = f"{op} / stale"
            self.suggestion_tree.insert('', 'end', iid=str(i), values=(row_label, s.get('severity'), s.get('issue_type'), op, s.get('confidence')))

    def _show_selected_suggestion_detail(self):
        sel = self.suggestion_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
            s = self.app_state.llm_suggestions[idx]
        except Exception:
            return
        cur = self._suggestion_current_row(s)
        lines = [
            f"{self.t('row_no')}: {s.get('row_id', '')}",
            f"Current row: {cur if cur is not None else 'stale'}",
            f"{self.t('issue')}: {s.get('issue_type', '')}",
            f"{self.t('operation')}: {s.get('suggested_operation', '')}",
            f"{self.t('confidence')}: {s.get('confidence', '')}",
        ]
        if s.get('batch_no'):
            lines.append(f"Batch: {s.get('batch_no')}")
        if s.get('relative_row_id'):
            lines.append(f"Relative row in batch: {s.get('relative_row_id')}")
        if s.get('column_key'):
            lines.append(f"Column: {s.get('column_key')}")
        if s.get('problem'):
            lines.append('')
            lines.append(str(s.get('problem')))
        if s.get('reason'):
            lines.append('')
            lines.append(str(s.get('reason')))
        self.suggestion_text.delete('1.0', 'end')
        self.suggestion_text.insert('1.0', '\n'.join(lines))

    def jump_to_selected_suggestion(self):
        """Double-click action: jump to and display the row referenced by the selected LLM suggestion.

        The suggestion may have been created before row operations changed the
        table.  We reuse the stable-id/signature resolver and then scroll the
        virtual editor to the current row.
        """
        sel = self.suggestion_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
            s = self.app_state.llm_suggestions[idx]
        except Exception:
            return
        row = self._suggestion_current_row(s)
        if row is None:
            self._show_selected_suggestion_detail()
            return
        col = str(s.get('column_key') or '')
        if col not in self.column_keys:
            col = self._source_column() if self._source_column() in self.column_keys else (self.column_keys[0] if self.column_keys else '')
        if col:
            self.selected_cell = (row, col)
        self._scroll_to_row(row)
        self.after_idle(lambda r=row, c=col: self._focus_cell_after_jump(r, c))
        self._show_selected_suggestion_detail()

    def _focus_cell_after_jump(self, row: int, col: str):
        key = (row, col)
        widget = self.cell_widgets.get(key)
        if widget is not None:
            try:
                widget.focus_set()
                widget.mark_set('insert', '1.0')
                self._select_cell(row, col, widget)
            except Exception:
                pass

    def _source_and_targets(self) -> Tuple[str, List[str]]:
        src = self._source_column()
        return src, [c for c in self.column_keys if c != src]

    def _append_note(self, unit: AlignmentUnit, text: str):
        if not text:
            return
        unit.note = (unit.note + '\n' if unit.note else '') + text

    def _suggestion_note(self, s: Dict) -> str:
        problem = str(s.get('problem') or '').strip()
        reason = str(s.get('reason') or '').strip()
        op = str(s.get('suggested_operation') or '').strip()
        bits = []
        if problem:
            bits.append(problem)
        if reason:
            bits.append('Reason: ' + reason)
        if op:
            bits.append('Operation: ' + op)
        return 'LLM: ' + ' / '.join(bits) if bits else 'LLM suggestion applied.'

    def _split_text_at_sentence_boundary(self, text: str) -> Tuple[str, str]:
        text = (text or '').strip()
        if not text:
            return '', ''
        # Prefer the first clear sentence-final punctuation that leaves content
        # on both sides.  This avoids LLM-generated replacement text while still
        # allowing a safe, user-reviewable split operation.
        pattern = re.compile(r"([。！？!?；;]|(?<![A-Z])\.(?=\s+[A-Z0-9“\"'\(\[]|\s*$))")
        for m in pattern.finditer(text):
            cut = m.end()
            left = text[:cut].strip()
            right = text[cut:].strip()
            if len(left) >= 2 and len(right) >= 2:
                return left, right
        # Fallback: split near the middle at whitespace, then comma-like marks.
        mid = max(1, len(text) // 2)
        candidates = [i for i, ch in enumerate(text) if ch.isspace() or ch in ',，、:：']
        if candidates:
            cut = min(candidates, key=lambda i: abs(i - mid)) + 1
            left = text[:cut].strip()
            right = text[cut:].strip()
            if left and right:
                return left, right
        return text, ''

    def _split_column_into_new_row(self, row: int, col: str, note: str = '') -> bool:
        if not (1 <= row <= len(self.app_state.alignments)) or col not in self.column_keys:
            return False
        unit = self.app_state.alignments[row - 1]
        left, right = self._split_text_at_sentence_boundary(unit.segments.get(col, ''))
        if not right:
            self._append_note(unit, note or f'LLM suggested splitting {col}, but no safe automatic sentence boundary was found.')
            unit.status = 'needs_review'
            unit.issue_type = 'split_manual_check'
            unit.confirmed = False
            return True
        unit.segments[col] = left
        unit.status = 'manual_split'
        unit.issue_type = 'llm_split_applied'
        unit.confirmed = False
        if note:
            self._append_note(unit, note)
        new_unit = AlignmentUnit(
            0, unit.group_id, {c: '' for c in self.column_keys},
            similarity=0.0, similarities={}, status='manual_split', issue_type='llm_split_applied',
            alignment_level=getattr(unit, 'alignment_level', 'sentence'),
            positions={c: [] for c in self.column_keys},
        )
        new_unit.segments[col] = right
        self.app_state.alignments.insert(row, new_unit)
        self.selected_cell = (row + 1, col)
        return True

    def _execute_suggestion(self, s: Dict) -> bool:
        row = self._suggestion_current_row(s)
        if row is None or not (1 <= row <= len(self.app_state.alignments)):
            s['status'] = 'stale'
            return False
        op = str(s.get('suggested_operation') or 'no_action').lower()
        unit = self.app_state.alignments[row - 1]
        note = self._suggestion_note(s)
        src, targets = self._source_and_targets()
        requested_col = str(s.get('column_key') or '').strip()
        changed = False
        if op in {'mark_needs_review', 'manual_check'}:
            unit.confirmed = False
            unit.status = 'needs_review'
            unit.issue_type = str(s.get('issue_type') or 'llm_review')
            self._append_note(unit, note)
            changed = True
        elif op in {'confirm_row', 'mark_confirmed'}:
            # Confirmation is intentionally conservative: it records the LLM
            # rationale, but the row remains user-reviewable unless the user
            # later marks it confirmed manually.
            unit.confirmed = False
            unit.status = 'llm_confirm_suggested'
            self._append_note(unit, note)
            changed = True
        elif op in {'merge_with_previous', 'merge_previous'} and row > 1:
            prev = self.app_state.alignments[row - 2]
            for col in self.column_keys:
                prev.segments[col] = ' '.join(x for x in [prev.segments.get(col, ''), unit.segments.get(col, '')] if x).strip()
            prev.status = 'manual_cell_merged'
            prev.issue_type = str(s.get('issue_type') or 'llm_merge_applied')
            prev.confirmed = False
            self._append_note(prev, note)
            self.app_state.alignments.pop(row - 1)
            self.selected_cell = (row - 1, requested_col if requested_col in self.column_keys else (src or self.column_keys[0]))
            changed = True
        elif op in {'merge_with_next', 'merge_next'} and row < len(self.app_state.alignments):
            nxt = self.app_state.alignments[row]
            for col in self.column_keys:
                unit.segments[col] = ' '.join(x for x in [unit.segments.get(col, ''), nxt.segments.get(col, '')] if x).strip()
            unit.status = 'manual_cell_merged'
            unit.issue_type = str(s.get('issue_type') or 'llm_merge_applied')
            unit.confirmed = False
            self._append_note(unit, note)
            self.app_state.alignments.pop(row)
            self.selected_cell = (row, requested_col if requested_col in self.column_keys else (src or self.column_keys[0]))
            changed = True
        elif op in {'move_target_up', 'move_target_down', 'move_source_up', 'move_source_down', 'move_cell_up', 'move_cell_down'}:
            delta = -1 if op.endswith('_up') else 1
            other = row + delta
            if 1 <= other <= len(self.app_state.alignments):
                if op.startswith('move_source'):
                    cols = [src]
                elif requested_col and requested_col in self.column_keys:
                    cols = [requested_col]
                elif op.startswith('move_cell') and requested_col and requested_col in self.column_keys:
                    cols = [requested_col]
                else:
                    cols = targets
                other_unit = self.app_state.alignments[other - 1]
                for col in cols:
                    unit.segments[col], other_unit.segments[col] = other_unit.segments.get(col, ''), unit.segments.get(col, '')
                unit.status = other_unit.status = 'manual_cell_moved'
                unit.issue_type = other_unit.issue_type = str(s.get('issue_type') or 'llm_move_applied')
                unit.confirmed = other_unit.confirmed = False
                self._append_note(unit, note)
                self._append_note(other_unit, note)
                self.selected_cell = (other, cols[0] if cols else (requested_col or src))
                changed = True
        elif op in {'split_source', 'split_target', 'split_cell'}:
            if op == 'split_source':
                col = src
            elif requested_col and requested_col in self.column_keys:
                col = requested_col
            elif op == 'split_target' and targets:
                col = targets[0]
            else:
                col = requested_col if requested_col in self.column_keys else (src or (self.column_keys[0] if self.column_keys else ''))
            changed = self._split_column_into_new_row(row, col, note)
        elif op in {'add_note', 'no_action'}:
            self._append_note(unit, note)
            if op != 'no_action':
                unit.status = 'needs_review'
                unit.issue_type = str(s.get('issue_type') or 'llm_note')
                unit.confirmed = False
            changed = True
        else:
            self._append_note(unit, note)
            unit.status = 'needs_review'
            unit.issue_type = str(s.get('issue_type') or 'llm_unknown_operation')
            unit.confirmed = False
            changed = True
        if changed:
            self._renumber()
        return changed

    def apply_suggestion(self):
        sel = self.suggestion_tree.selection()
        if not sel:
            return
        if not self._editing_allowed():
            return
        idx = int(sel[0])
        s = self.app_state.llm_suggestions[idx]
        self.suggestion_text.delete('1.0', 'end')
        self.suggestion_text.insert('1.0', s.get('problem', '') + '\n\n' + s.get('suggested_operation', ''))
        self._push()
        if self._execute_suggestion(s):
            self.app_state.llm_suggestions.pop(idx)
            self._refresh_after_structure_change()
        else:
            s['status'] = 'stale'
            messagebox.showwarning(self.t('llm_validate_editor'), 'This suggestion is stale because its original row has changed or was removed. Please run LLM validation again.')
        self.refresh_suggestions()

    def apply_all_suggestions(self):
        indices = self._current_group_suggestion_indices()
        if not indices or not self._editing_allowed():
            return
        if not messagebox.askyesno(self.t('llm_validate_editor'), self.t('confirm_apply_all_llm_suggestions')):
            return
        self._push()
        selected = []
        for i in indices:
            if i < len(self.app_state.llm_suggestions):
                sug = self.app_state.llm_suggestions[i]
                cur = self._suggestion_current_row(sug)
                selected.append((i, sug, cur))
        applied_indices = []
        for i, sug, cur in sorted(selected, key=lambda x: int(x[2] or -1), reverse=True):
            if cur is None:
                sug['status'] = 'stale'
                continue
            if self._execute_suggestion(sug):
                applied_indices.append(i)
        for i in sorted(applied_indices, reverse=True):
            if i < len(self.app_state.llm_suggestions):
                self.app_state.llm_suggestions.pop(i)
        self._refresh_after_structure_change()
        self.refresh_suggestions()

    def ignore_suggestion(self):
        sel = self.suggestion_tree.selection()
        if not sel:
            return
        self.app_state.llm_suggestions.pop(int(sel[0]))
        self.refresh_suggestions()

    def ignore_all_suggestions(self):
        for i in sorted(self._current_group_suggestion_indices(), reverse=True):
            if i < len(self.app_state.llm_suggestions):
                self.app_state.llm_suggestions.pop(i)
        self.refresh_suggestions()

    def _highlight_rows(self) -> List[int]:
        return [i for i, u in enumerate(self.app_state.alignments, 1) if self._is_highlighted_row(u)]

    def _goto_highlight(self, direction: int):
        rows = self._highlight_rows()
        if not rows:
            messagebox.showinfo(self.t('alignment_title'), self.t('no_low_similarity'))
            return
        cur = self.selected_cell[0] if self.selected_cell else 0
        if direction > 0:
            candidates = [r for r in rows if r > cur]
            target = candidates[0] if candidates else rows[0]
        else:
            candidates = [r for r in rows if r < cur]
            target = candidates[-1] if candidates else rows[-1]
        col = self.selected_cell[1] if self.selected_cell and self.selected_cell[1] in self.column_keys else (self.column_keys[0] if self.column_keys else '')
        if col:
            self.selected_cell = (target, col)
        self._scroll_to_row(target)

    def goto_next_highlight(self):
        self._goto_highlight(1)

    def goto_prev_highlight(self):
        self._goto_highlight(-1)

    def scroll_to_group(self, group_id: str):
        for idx, unit in enumerate(self.app_state.alignments, 1):
            if unit.group_id == group_id:
                if self.column_keys:
                    self.selected_cell = (idx, self.column_keys[0])
                self._scroll_to_row(idx)
                return

    def export_dialog(self):
        self._sync_all_widgets()
        if not self.app_state.alignments:
            messagebox.showwarning(self.t('export'), self.t('export_no_rows'))
            return
        path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[(self.t('excel'), '*.xlsx'), (self.t('txt'), '*.txt'), ('TMX', '*.tmx'), ('XML', '*.xml'), (self.t('word'), '*.docx'), (self.t('json'), '*.json')])
        if not path:
            return
        try:
            ext = Path(path).suffix.lower()
            if ext == '.xlsx':
                export_excel(self.app_state.alignments, path)
            elif ext == '.txt':
                export_line_txt(self.app_state.alignments, path)
            elif ext == '.tmx':
                export_tmx(self.app_state.alignments, path)
            elif ext == '.xml':
                export_xml(self.app_state.alignments, path)
            elif ext == '.docx':
                export_word(self.app_state.alignments, path)
            elif ext == '.json':
                export_json(self.app_state.alignments, path)
            else:
                export_excel(self.app_state.alignments, path)
            messagebox.showinfo(self.t('export_complete'), self.t('exported', path=path))
        except Exception as exc:
            messagebox.showerror(self.t('export_failed_title'), str(exc))

    def export_multi_txt_dialog(self):
        self._sync_all_widgets()
        if not self.app_state.alignments:
            messagebox.showwarning(self.t('multi_txt'), self.t('export_no_rows'))
            return
        folder = filedialog.askdirectory(title=self.t('select_folder'))
        if not folder:
            return
        try:
            export_multi_txt(
                self.app_state.alignments,
                folder,
                MultiTxtOptions(
                    one_file_per_language=bool(self.app_state.settings.get('output_one_txt_per_language', True)),
                    include_line_numbers=bool(self.app_state.settings.get('output_line_numbers', True)),
                    missing_placeholder=self.app_state.settings.get('missing_cell_placeholder', ''),
                    create_subfolders=bool(self.app_state.settings.get('create_subfolder_for_each_set', True)),
                ),
                project_name=self.app_state.project_name if hasattr(self.app_state, 'project_name') else 'alignlens',
            )
            messagebox.showinfo(self.t('multi_txt'), self.t('exported_to', path=folder))
        except Exception as exc:
            messagebox.showerror(self.t('multi_txt_failed'), str(exc))
