from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from core.datatypes import AlignmentUnit, FileRecord, Segment
from core.utils import UndoRedoStack, resource_path, safe_json_load, safe_json_dump, ensure_dirs, now_str, normalized_file_key
from core.document_reader import read_document, text_stats
from core.segmenter import split_text
from core.segmentation_profiles import all_default_profiles, describe_profile, profile_for_language
from core.aligner import AlignmentParams, align_bilingual_transformer, align_bilingual_transformer_within_paragraphs, combine_multilingual_by_pivot, manual_align_by_index, compute_alignment_similarities, deduplicate_alignment_units
from core.embedding_models import EmbeddingModelManager
from core.llm_aligner import OpenAILLMClient, llm_align_bilingual
from core.llm_checker import llm_check_rows
from core.project_io import save_project, load_project
from core.statistics import compute_statistics
from core.exporters import export_by_extension
from core.multi_txt_exporter import export_multi_txt, MultiTxtOptions
from core.task_runner import TaskRunner
from core.hardware import get_hardware_info, format_hardware_message, resolve_device
from core.language_registry import LANGUAGE_CODES, display_name, column_display_name

from app.log_panel import LogPanel, setup_logging
from app.file_manager import FileManagerFrame
from app.alignment_editor import AlignmentEditorFrame
from app.settings_dialog import SettingsDialog
from app.model_manager_dialog import ModelManagerDialog
from app.about_dialog import AboutDialog
from app.wizard import ImportWizard
from app.theme import apply_prooflens_theme
from app.i18n import I18N


@dataclass
class AppState:
    project_name: str = 'Untitled AlignLens Project'
    project_path: str = ''
    files: List[FileRecord] = field(default_factory=list)
    segments_by_file: Dict[str, List[Segment]] = field(default_factory=dict)
    paragraph_segments_by_file: Dict[str, List[Segment]] = field(default_factory=dict)
    alignments: List[AlignmentUnit] = field(default_factory=list)
    paragraph_alignments: List[AlignmentUnit] = field(default_factory=list)
    llm_suggestions: List[Dict] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)


class GroupEditorState:
    """Lightweight view-state for one set_xxx editor tab.

    The tab edits only one file group. Rows are synchronized back to the
    project-level AppState by MainWindow when the tab changes, closes, exports,
    or the project is saved.
    """
    def __init__(self, parent: AppState, group_id: str, rows: List[AlignmentUnit]):
        self._parent = parent
        self.group_id = group_id
        self.project_name = parent.project_name
        self.project_path = parent.project_path
        self.files = [f for f in parent.files if f.group_id == group_id]
        self.segments_by_file = parent.segments_by_file
        self.paragraph_segments_by_file = parent.paragraph_segments_by_file
        self.alignments = rows
        self.paragraph_alignments = [u for u in parent.paragraph_alignments if u.group_id == group_id]
        self.llm_suggestions = parent.llm_suggestions
        self.settings = parent.settings

    def refresh_from_parent(self):
        self.project_name = self._parent.project_name
        self.project_path = self._parent.project_path
        self.files = [f for f in self._parent.files if f.group_id == self.group_id]
        self.segments_by_file = self._parent.segments_by_file
        self.paragraph_segments_by_file = self._parent.paragraph_segments_by_file
        self.paragraph_alignments = [u for u in self._parent.paragraph_alignments if u.group_id == self.group_id]


DEFAULT_SETTINGS = {
    'created_time': '',
    'gui_language': 'zh_sim',
    'theme': 'prooflens',
    'default_project_folder': '',
    'autosave_interval': 0,
    'show_similarity': True,
    'min_similarity_threshold': 0.55,
    'paragraph_min_similarity_threshold': 0.50,
    'high_confidence_threshold': 0.70,
    'low_similarity_match_penalty': 0.25,
    'sentence_max_merge_units': 3,
    'sentence_allow_2_to_2': True,
    'sentence_merge_penalty': 0.25,
    'sentence_strict_fine_alignment': True,
    'preserve_paragraphs': True,
    'remove_excessive_spaces': True,
    'duplicate_file_handling': 'skip',
    'auto_sort_after_import': False,
    'confirm_delete': True,
    'confirm_reorder': True,
    'segmentation_mode': 'auto',
    'paragraph_aware': True,
    'split_by_line': False,
    'split_by_paragraph': False,
    'alignment_mode': 'fused',
    'custom_embedding_model': '',
    'batch_size': 32,
    'max_window': 5,
    'skip_penalty': -0.30,
    'empty_penalty': -0.30,
    'length_penalty_weight': 0.02,
    'paragraph_distance_penalty': 0.04,
    'residual_matching': True,
    'allow_cross_paragraph': True,
    'device': 'auto',
    'use_segmentation_gpu': True,
    'segmentation_device': 'auto',
    'model_root': '',
    'default_embedding_model': 'sentence-transformers/LaBSE',
    'openai_api_key': '',
    'save_api_key': False,
    'openai_model': 'gpt-5.4-mini',
    'llm_suggestion_language': 'zh_sim',
    'strict_json_mode': True,
    'llm_retry_times': 1,
    'llm_temperature': 0.0,
    'llm_max_tokens': 3000,
    'llm_batch_size': 40,
    'llm_timeout': 90,
    'llm_safe_mode': True,
    'llm_min_confidence': 0.75,
    'llm_verify_with_transformer': True,
    'llm_auto_apply_structural_suggestions': False,
    'default_export_format': 'xlsx',
    'create_subfolder_for_each_set': True,
    'output_one_txt_per_language': True,
    'output_line_numbers': True,
    'missing_cell_placeholder': '',
    'sentence_merge_separator': ' ',
    'virtual_editor_buffer_rows': 4,
    'last_source_lang': 'zh_sim',
    'last_target_langs': ['en'],
    'last_alignment_project_mode': '1_to_1',
    'last_target_count': 1,
    'alignment_project_mode': '1_to_1',
    'file_columns': [],
    'current_group_id': '',
    'group_statuses': {},
    'large_doc_threshold': 2000000,
    'dp_band_size': 240,
    'dp_search_mode': 'full',
    'alignment_unit': 'sentence',
    'use_paragraph_alignment_for_sentence': False,
    'primary_transformer_model': 'sentence-transformers/LaBSE',
    'secondary_transformer_model': 'intfloat/multilingual-e5-base',
    'use_secondary_transformer_model': True,
    'dp_cpu_workers': 0,
    'editor_row_no_width': 64,
    'editor_similarity_width': 92,
    'editor_status_width': 150,
    'segmentation_profiles': all_default_profiles(),
    'default_sentence_segmenter': 'auto',
    'fallback_segmenter': 'punctuation',
    'segmentation_cache_enabled': True,
    'alignment_precision_defaults_version': 'round25',
}



class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.logger = setup_logging()
        self.title('BFSU AlignLens')
        self.geometry('1360x860')
        self.minsize(1100, 700)
        self.state_data = AppState(settings=self._load_settings())
        self._dirty = False
        self.i18n = I18N(self.state_data.settings.get('gui_language', 'zh_sim'))
        self.t = self.i18n.t
        if not self.state_data.settings.get('created_time'):
            self.state_data.settings['created_time'] = now_str()
        self.undo = UndoRedoStack(100)
        self.task_runner = TaskRunner()
        self._task_cancelled = False
        self._setup_icon()
        self._apply_theme()
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self.after(200, self._poll_tasks)
        self.log('BFSU AlignLens started.')
        self._show_gpu_startup_info()
        self._update_window_title()

    def _setup_icon(self):
        ico = resource_path('assets', 'app.ico')
        png = resource_path('assets', 'app.png')
        try:
            if ico.exists():
                self.iconbitmap(str(ico))
            elif png.exists():
                self._icon_img = tk.PhotoImage(file=str(png)); self.iconphoto(True, self._icon_img)
        except Exception:
            pass

    def _apply_precision_defaults(self, settings: dict) -> dict:
        """Apply current accuracy-oriented Transformer/LLM defaults once per settings source."""
        if settings.get('alignment_precision_defaults_version') != 'round25':
            settings.update({
                'alignment_mode': 'fused',
                'primary_transformer_model': 'sentence-transformers/LaBSE',
                'secondary_transformer_model': 'intfloat/multilingual-e5-base',
                'use_secondary_transformer_model': True,
                'default_embedding_model': 'sentence-transformers/LaBSE',
                'dp_search_mode': 'full',
                'large_doc_threshold': 2000000,
                'dp_band_size': 240,
                'batch_size': 32,
                'max_window': 5,
                'min_similarity_threshold': 0.55,
                'high_confidence_threshold': 0.70,
                'skip_penalty': -0.30,
                'empty_penalty': -0.30,
                'low_similarity_match_penalty': 0.25,
                'sentence_max_merge_units': 3,
                'sentence_allow_2_to_2': True,
                'sentence_merge_penalty': 0.25,
                'sentence_strict_fine_alignment': True,
                'length_penalty_weight': 0.02,
                'paragraph_distance_penalty': 0.04,
                'residual_matching': True,
                'allow_cross_paragraph': True,
                'llm_suggestion_language': settings.get('llm_suggestion_language') or settings.get('gui_language', 'zh_sim'),
                'openai_model': settings.get('openai_model') or 'gpt-5.4-mini',
                'strict_json_mode': bool(settings.get('strict_json_mode', True)),
                'llm_retry_times': int(settings.get('llm_retry_times', 1) or 1),
                'alignment_precision_defaults_version': 'round25',
            })
        return settings

    def _load_settings(self):
        cfg = resource_path('config', 'default_settings.json')
        settings = dict(DEFAULT_SETTINGS)
        settings.update(safe_json_load(cfg, {}))
        if not settings.get('model_root'):
            settings['model_root'] = str(resource_path('models'))
        if not settings.get('default_project_folder'):
            settings['default_project_folder'] = str(resource_path())
        # Merge new language-specific segmenter defaults without overwriting user choices.
        profiles = all_default_profiles()
        profiles.update(settings.get('segmentation_profiles') or {})
        settings['segmentation_profiles'] = profiles
        self._apply_precision_defaults(settings)
        return settings

    def _save_settings(self):
        cfg = resource_path('config', 'default_settings.json')
        data = dict(self.state_data.settings)
        if not data.get('save_api_key'):
            data['openai_api_key'] = ''
        # Project-specific transient layout state should be saved inside
        # .alignlens project files, not as the global application default.
        data.pop('file_columns', None)
        data.pop('current_group_id', None)
        safe_json_dump(data, cfg)

    def _apply_theme(self):
        apply_prooflens_theme(self)

    def _build_menu(self):
        t = self.t
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        filem = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label=t('file'), menu=filem)
        filem.add_command(label=t('new_project'), command=self.new_project, accelerator='Ctrl+N')
        filem.add_command(label=t('open_project'), command=self.open_project, accelerator='Ctrl+O')
        filem.add_command(label=t('save_project'), command=self.save_project, accelerator='Ctrl+S')
        filem.add_command(label=t('save_project_as'), command=self.save_project_as)
        filem.add_command(label=t('close_project'), command=self.close_project)
        filem.add_separator()
        filem.add_command(label=t('import_alignment_files'), command=self.import_wizard)
        filem.add_command(label=t('add_to_current_column'), command=lambda: self.file_manager.add_files())
        filem.add_separator()
        filem.add_command(label=t('export'), command=self.export_active_editor, accelerator='Ctrl+E')
        filem.add_command(label=t('batch_export'), command=self.batch_export_dialog)
        filem.add_command(label=t('exit'), command=self.on_close)

        edit = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label=t('edit'), menu=edit)
        edit.add_command(label=t('undo'), command=self.undo_action, accelerator='Ctrl+Z')
        edit.add_command(label=t('redo'), command=self.redo_action, accelerator='Ctrl+Y')
        edit.add_separator()
        edit.add_command(label=t('import_alignment_files'), command=self.import_wizard)
        edit.add_command(label=t('delete_selected_files'), command=lambda: self.file_manager.delete_selected(), accelerator='Delete')
        edit.add_command(label=t('delete_all_files'), command=lambda: self.file_manager.delete_all())
        edit.add_separator()
        edit.add_command(label=t('move_file_up'), command=lambda: self.file_manager.move_selected(-1))
        edit.add_command(label=t('move_file_down'), command=lambda: self.file_manager.move_selected(1))
        edit.add_command(label=t('move_file_top'), command=lambda: self.file_manager.move_top())
        edit.add_command(label=t('move_file_bottom'), command=lambda: self.file_manager.move_bottom())
        edit.add_separator()
        edit.add_command(label=t('merge'), command=lambda: self._editor_call('merge_previous'), accelerator='Ctrl+M')
        edit.add_command(label=t('split'), command=lambda: self._editor_call('split_cell'))
        edit.add_command(label=t('mark_confirmed'), command=lambda: self._editor_call('mark_confirmed'), accelerator='Ctrl+Enter')
        edit.add_command(label=t('mark_review'), command=lambda: self._editor_call('mark_needs_review'))

        align = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label=t('alignment'), menu=align)
        align.add_command(label=t('segment_paragraph'), command=lambda: self.segment_only(unit_level='paragraph'))
        align.add_command(label=t('segment_sentence'), command=lambda: self.segment_only(unit_level='sentence'))
        align.add_separator()
        align.add_command(label=t('paragraph_alignment'), command=self.run_paragraph_alignment)
        align.add_command(label=t('sentence_alignment'), command=self.run_sentence_alignment, accelerator='F5')
        align.add_separator()
        align.add_command(label=t('llm_paragraph_alignment'), command=lambda: self.run_llm_alignment(unit_level='paragraph'))
        align.add_command(label=t('llm_sentence_alignment'), command=lambda: self.run_llm_alignment(unit_level='sentence'))
        align.add_separator()
        align.add_command(label=t('batch_segment_paragraph'), command=lambda: self.segment_only(batch=True, unit_level='paragraph'))
        align.add_command(label=t('batch_segment_sentence'), command=lambda: self.segment_only(batch=True, unit_level='sentence'))
        align.add_command(label=t('batch_transformer_paragraph_alignment'), command=lambda: self.run_paragraph_alignment(batch=True))
        align.add_command(label=t('batch_transformer_sentence_alignment'), command=lambda: self.run_sentence_alignment(batch=True))
        align.add_command(label=t('batch_llm_paragraph_alignment'), command=lambda: self.run_llm_alignment(batch=True, unit_level='paragraph'))
        align.add_command(label=t('batch_llm_sentence_alignment'), command=lambda: self.run_llm_alignment(batch=True, unit_level='sentence'))
        align.add_separator()
        align.add_command(label=t('open_current_group_editor'), command=self.open_current_group_editor)
        align.add_command(label=t('check_low_similarity_rows'), command=self.check_low_similarity_rows, accelerator='F7')

        view = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label=t('view'), menu=view)
        view.add_command(label=t('file_manager'), command=lambda: self.notebook.select(self.file_manager))
        view.add_command(label=t('alignment_editor'), command=self.open_current_group_editor)
        view.add_command(label=t('llm_suggestions'), command=self.llm_validate_current_editor)
        view.add_command(label=t('log_panel'), command=self.toggle_log_panel)
        langmenu = tk.Menu(view, tearoff=0); view.add_cascade(label=t('ui_language'), menu=langmenu)
        for lang in ['zh_sim','zh_tra','en']:
            langmenu.add_command(label=display_name(lang, lang, with_code=False), command=lambda l=lang: self.set_gui_language(l))

        tools = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label=t('tools'), menu=tools)
        tools.add_command(label=t('settings'), command=self.open_settings)
        tools.add_command(label=t('model_manager'), command=self.open_model_manager)
        tools.add_separator()
        tools.add_command(label=t('validate_project'), command=self.validate_project)
        tools.add_command(label=t('check_file_pairing'), command=lambda: self.file_manager.check_pairing())
        tools.add_command(label=t('auto_sort_files'), command=lambda: self.file_manager.auto_sort())
        tools.add_command(label=t('statistics'), command=self.show_statistics)
        tools.add_command(label=t('export_log'), command=self.export_log)
        tools.add_command(label=t('clear_cache'), command=self.clear_cache_hint)
        tools.add_separator()
        tools.add_command(label=t('reset_default_settings'), command=self.reset_default_settings)

        helpm = tk.Menu(menubar, tearoff=0); menubar.add_cascade(label=t('help'), menu=helpm)
        helpm.add_command(label=t('about'), command=lambda: AboutDialog(self, self.i18n))

    def _build_ui(self):
        t = self.t
        top = ttk.Frame(self, padding=4); top.pack(fill='x')
        ttk.Label(top, text=t('project')).pack(side='left')
        self.project_var = tk.StringVar(value=self.state_data.project_name)
        self.project_entry = ttk.Entry(top, textvariable=self.project_var, width=40)
        self.project_entry.pack(side='left', padx=4)
        self.project_entry.bind('<KeyRelease>', lambda e: self._mark_dirty())
        ttk.Button(top, text=t('save'), command=self.save_project).pack(side='left')
        ttk.Button(top, text=t('settings'), command=self.open_settings).pack(side='left', padx=4)
        ttk.Button(top, text=t('cancel_task'), command=self.cancel_all_tasks).pack(side='left', padx=4)
        self.progress = ttk.Progressbar(top, maximum=1.0, length=240); self.progress.pack(side='right', padx=6)
        self.status_var = tk.StringVar(value=t('ready')); ttk.Label(top, textvariable=self.status_var, style='Status.TLabel').pack(side='right')

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        callbacks = {
            'push_undo': self.push_undo,
            'log': self.log,
            't': self.t,
            'segment_files': self.segment_only,
            'segment_current_group': self.segment_current_group,
            'segment_sentence_group': lambda gid='': self.segment_only(group_id=gid, batch=False, unit_level='sentence'),
            'segment_paragraph_group': lambda gid='': self.segment_only(group_id=gid, batch=False, unit_level='paragraph'),
            'start_alignment': self.run_sentence_alignment,
            'align_current_group': self.open_group_editor,
            'refresh_alignment': lambda: [ed.refresh() for ed in getattr(self, 'alignment_editors', {}).values()],
            'import_wizard': self.import_wizard,
        }
        self.file_manager = FileManagerFrame(self.notebook, self.state_data, callbacks)
        self.alignment_editors: Dict[str, AlignmentEditorFrame] = {}
        self.alignment_editor = None
        self.notebook.add(self.file_manager, text=self.t('file_manager'))
        self.notebook.bind('<<NotebookTabChanged>>', self._on_notebook_tab_changed)
        self.file_manager.refresh()
        self.log_panel = LogPanel(self)
        self.log_panel.pack(fill='x', side='bottom')
        self._log_panel_visible = True
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def _rebuild_interface(self):
        """Rebuild visible widgets after a UI-language change without resetting project data."""
        try:
            self.config(menu='')
        except Exception:
            pass
        for child in list(self.winfo_children()):
            child.destroy()
        self._apply_theme()
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()

    def _bind_shortcuts(self):
        self.bind('<Control-s>', lambda e: self.save_project())
        self.bind('<Control-o>', lambda e: self.open_project())
        self.bind('<Control-n>', lambda e: self.new_project())
        self.bind('<Control-w>', lambda e: self.close_project())
        self.bind('<Control-z>', lambda e: self.undo_action())
        self.bind('<Control-y>', lambda e: self.redo_action())
        self.bind('<Control-e>', lambda e: self.export_active_editor())
        self.bind('<Control-m>', lambda e: self._editor_call('merge_previous'))
        self.bind('<Control-Shift-M>', lambda e: self._editor_call('merge_next'))
        self.bind('<Control-Return>', lambda e: self._editor_call('mark_confirmed'))
        self.bind('<F5>', lambda e: self.run_sentence_alignment())
        self.bind('<F6>', lambda e: self.llm_check_current_row())
        self.bind('<F7>', lambda e: self.check_low_similarity_rows())

    def _editor_callbacks(self, group_id: str) -> dict:
        return {
            'push_undo': self.push_undo,
            'log': self.log,
            't': self.t,
            'manual_paragraph_align': lambda gid=group_id: self.segment_only(group_id=gid, unit_level='paragraph'),
            'manual_sentence_align': lambda gid=group_id: self.segment_only(group_id=gid, unit_level='sentence'),
            'segment_only': self.segment_only,
            'llm_paragraph_align': lambda gid=group_id: self.run_llm_alignment(group_id=gid, unit_level='paragraph'),
            'llm_sentence_align': lambda gid=group_id: self.run_llm_alignment(group_id=gid, unit_level='sentence'),
            'llm_check_current': self.llm_validate_current_editor,
            'check_low_similarity': self.check_low_similarity_rows,
            'recompute_similarity': self.recompute_similarity,
            'recompute_current_similarity': self.recompute_current_similarity,
            'paragraph_align': lambda gid=group_id: self.run_paragraph_alignment(group_id=gid),
            'sentence_align': lambda gid=group_id: self.run_sentence_alignment(group_id=gid),
            'save_settings': self._save_settings,
            'on_editor_changed': self._on_editor_changed,
            'close_group': lambda gid=group_id: self.close_group_editor(gid),
            'open_group': self.choose_open_group_editor,
            'complete_group': lambda gid=group_id: self.complete_group_alignment(gid),
        }

    def _active_alignment_editor(self):
        current = None
        try:
            current = self.notebook.nametowidget(self.notebook.select())
        except Exception:
            current = None
        if current in getattr(self, 'alignment_editors', {}).values():
            self.alignment_editor = current
            return current
        return None

    def _editor_call(self, method: str, *args, **kwargs):
        ed = self._active_alignment_editor()
        if not ed:
            messagebox.showwarning(self.t('alignment_editor'), self.t('open_group_first'))
            return None
        fn = getattr(ed, method, None)
        if callable(fn):
            return fn(*args, **kwargs)
        return None

    def _update_window_title(self):
        mark = ' *' if getattr(self, '_dirty', False) else ''
        name = self.state_data.project_name or 'Untitled AlignLens Project'
        self.title(f'BFSU AlignLens - {name}{mark}')

    def _mark_dirty(self):
        self._dirty = True
        self._update_window_title()

    def _mark_clean(self):
        self._dirty = False
        self._update_window_title()

    def _has_project_content(self):
        return bool(self.state_data.files or self.state_data.segments_by_file or self.state_data.paragraph_segments_by_file or self.state_data.alignments or self.state_data.paragraph_alignments or self.state_data.project_path)

    def _confirm_save_if_needed(self) -> bool:
        if not getattr(self, '_dirty', False):
            return True
        answer = messagebox.askyesnocancel(self.t('unsaved_project_title'), self.t('unsaved_project_message'))
        if answer is None:
            return False
        if answer:
            return bool(self.save_project())
        return True

    def _reset_project_state(self):
        settings = self.state_data.settings
        settings['file_columns'] = []
        settings['current_group_id'] = ''
        settings['group_statuses'] = {}
        self._close_all_editors(sync=False)
        self.state_data = AppState(settings=settings)
        self.state_data.project_name = 'Untitled AlignLens Project'
        self.project_var.set(self.state_data.project_name)
        self.file_manager.app_state = self.state_data
        self.file_manager.refresh()
        self.notebook.select(self.file_manager)
        self.undo = UndoRedoStack(50)
        self._mark_clean()

    def export_active_editor(self):
        return self._editor_call('export_dialog')

    def _collect_batch_export_rows(self) -> Dict[str, List[AlignmentUnit]]:
        """Collect every segmented or aligned group without changing editor state unnecessarily."""
        self._sync_all_group_editors()
        by_group: Dict[str, List[AlignmentUnit]] = {}
        for u in self.state_data.alignments:
            if u.group_id:
                by_group.setdefault(u.group_id, []).append(u)
        for gid in self._available_group_ids():
            if by_group.get(gid):
                continue
            level = ''
            if any(f.group_id == gid and f.file_id in self.state_data.segments_by_file for f in self.state_data.files):
                level = 'sentence'
            elif any(f.group_id == gid and f.file_id in self.state_data.paragraph_segments_by_file for f in self.state_data.files):
                level = 'paragraph'
            if level:
                rows = self._build_manual_alignments([gid], unit_level=level)
                if rows:
                    by_group[gid] = rows
        for gid, rows in by_group.items():
            for i, u in enumerate(rows, 1):
                u.group_id = gid
                u.row_id = i
        return by_group

    def batch_export_dialog(self):
        rows_by_group = self._collect_batch_export_rows()
        if not rows_by_group:
            messagebox.showwarning(self.t('batch_export'), self.t('batch_export_no_rows'))
            return
        top = tk.Toplevel(self)
        top.title(self.t('batch_export'))
        top.geometry('560x360')
        top.transient(self)
        top.grab_set()
        mode_var = tk.StringVar(value='group_files')
        fmt_var = tk.StringVar(value=str(self.state_data.settings.get('default_export_format', 'xlsx')).lower())
        line_no_var = tk.BooleanVar(value=bool(self.state_data.settings.get('output_line_numbers', True)))
        subfolder_var = tk.BooleanVar(value=bool(self.state_data.settings.get('create_subfolder_for_each_set', True)))
        output_var = tk.StringVar(value='')
        frame = ttk.Frame(top, padding=14)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=self.t('batch_export_intro'), wraplength=510).pack(anchor='w', pady=(0, 10))
        modes = ttk.LabelFrame(frame, text=self.t('batch_export_mode'), padding=8)
        modes.pack(fill='x', pady=4)
        ttk.Radiobutton(modes, text=self.t('batch_export_group_files'), variable=mode_var, value='group_files').pack(anchor='w', pady=2)
        ttk.Radiobutton(modes, text=self.t('batch_export_language_txt'), variable=mode_var, value='language_txt').pack(anchor='w', pady=2)
        opts = ttk.Frame(frame)
        opts.pack(fill='x', pady=8)
        ttk.Label(opts, text=self.t('export_format')).grid(row=0, column=0, sticky='w')
        ttk.Combobox(opts, textvariable=fmt_var, values=['xlsx', 'txt', 'docx', 'json', 'xml', 'tmx'], state='readonly', width=10).grid(row=0, column=1, sticky='w', padx=6)
        ttk.Checkbutton(opts, text=self.t('output_line_numbers'), variable=line_no_var).grid(row=1, column=0, columnspan=2, sticky='w', pady=3)
        ttk.Checkbutton(opts, text=self.t('create_subfolder_for_each_set'), variable=subfolder_var).grid(row=2, column=0, columnspan=2, sticky='w', pady=3)
        out = ttk.Frame(frame)
        out.pack(fill='x', pady=6)
        ttk.Entry(out, textvariable=output_var).pack(side='left', fill='x', expand=True)
        def choose_dir():
            d = filedialog.askdirectory(title=self.t('select_export_folder'))
            if d:
                output_var.set(d)
        ttk.Button(out, text=self.t('browse'), command=choose_dir).pack(side='left', padx=4)
        btns = ttk.Frame(frame)
        btns.pack(fill='x', pady=12)
        def do_export():
            outdir = output_var.get().strip()
            if not outdir:
                choose_dir(); outdir = output_var.get().strip()
            if not outdir:
                return
            try:
                written = self._run_batch_export(rows_by_group, outdir, mode_var.get(), fmt_var.get(), line_no_var.get(), subfolder_var.get())
                self.state_data.settings['default_export_format'] = fmt_var.get()
                self.state_data.settings['output_line_numbers'] = bool(line_no_var.get())
                self.state_data.settings['create_subfolder_for_each_set'] = bool(subfolder_var.get())
                self._save_settings()
                top.destroy()
                messagebox.showinfo(self.t('batch_export'), self.t('batch_export_done', count=len(written), folder=outdir))
            except Exception as exc:
                messagebox.showerror(self.t('export_failed'), str(exc))
        ttk.Button(btns, text=self.t('export'), command=do_export, style='Accent.TButton').pack(side='left')
        ttk.Button(btns, text=self.t('cancel'), command=top.destroy).pack(side='right')

    def _safe_export_name(self, text: str) -> str:
        bad = '<>:"/\\|?*'
        out = ''.join('_' if c in bad else c for c in (text or 'set'))
        return out.strip(' .') or 'set'

    def _run_batch_export(self, rows_by_group: Dict[str, List[AlignmentUnit]], output_dir: str, mode: str, fmt: str, include_line_numbers: bool, create_subfolders: bool) -> List[Path]:
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        written: List[Path] = []
        if mode == 'language_txt':
            all_rows: List[AlignmentUnit] = []
            for gid in sorted(rows_by_group):
                all_rows.extend(rows_by_group[gid])
            options = MultiTxtOptions(
                include_line_numbers=include_line_numbers,
                include_header=False,
                include_similarity=False,
                include_status=False,
                include_note=False,
                create_subfolders=create_subfolders,
                one_file_per_language=True,
                one_aligned_file=False,
                write_index=True,
                missing_placeholder=str(self.state_data.settings.get('missing_cell_placeholder', '')),
            )
            return export_multi_txt(all_rows, str(root), options, project_name=self.state_data.project_name)
        ext = '.' + (fmt or 'xlsx').lstrip('.').lower()
        for gid in sorted(rows_by_group):
            rows = rows_by_group[gid]
            folder = root / gid if create_subfolders else root
            folder.mkdir(parents=True, exist_ok=True)
            base = self._safe_export_name(gid)
            path = folder / f'{base}_aligned{ext}'
            n = 2
            while path.exists():
                path = folder / f'{base}_aligned_{n}{ext}'
                n += 1
            export_by_extension(rows, str(path))
            written.append(path)
        return written

    def _on_notebook_tab_changed(self, event=None):
        ed = self._active_alignment_editor()
        if ed is not None:
            self.state_data.settings['current_group_id'] = getattr(ed.app_state, 'group_id', self.state_data.settings.get('current_group_id', ''))

    def _sync_group_editor(self, editor=None):
        editor = editor or self._active_alignment_editor()
        if not editor:
            return
        try:
            editor._sync_all_widgets()
        except Exception:
            pass
        gid = getattr(editor.app_state, 'group_id', '')
        if not gid:
            return
        rows = list(editor.app_state.alignments)
        for i, u in enumerate(rows, 1):
            u.group_id = gid
            u.row_id = i
        self.state_data.alignments = [u for u in self.state_data.alignments if u.group_id != gid] + rows
        for i, u in enumerate(self.state_data.alignments, 1):
            u.row_id = i
        if rows and getattr(rows[0], 'alignment_level', 'sentence') == 'paragraph':
            self.state_data.paragraph_alignments = [u for u in self.state_data.paragraph_alignments if u.group_id != gid] + list(rows)
            for i, u in enumerate(self.state_data.paragraph_alignments, 1):
                u.row_id = i

    def _sync_all_group_editors(self):
        for ed in list(getattr(self, 'alignment_editors', {}).values()):
            self._sync_group_editor(ed)

    def _on_editor_changed(self, editor):
        gid = getattr(editor.app_state, 'group_id', '')
        if gid:
            if self._group_status(gid) != 'aligning':
                self._set_group_status(gid, 'editing', refresh=False)
            self._sync_group_editor(editor)
            self._mark_dirty()
            if hasattr(self, 'file_manager'):
                self.file_manager.refresh()

    def _group_rows(self, group_id: str) -> List[AlignmentUnit]:
        return [u for u in self.state_data.alignments if u.group_id == group_id]

    def _group_files(self, group_id: str) -> List[FileRecord]:
        return [f for f in self.state_data.files if f.group_id == group_id]

    def _group_status(self, group_id: str) -> str:
        statuses = self.state_data.settings.setdefault('group_statuses', {})
        return str(statuses.get(group_id, ''))

    def _set_group_status(self, group_id: str, status: str, refresh: bool = True):
        if not group_id:
            return
        old_status = self.state_data.settings.setdefault('group_statuses', {}).get(group_id)
        self.state_data.settings.setdefault('group_statuses', {})[group_id] = status
        for rec in self.state_data.files:
            if rec.group_id == group_id:
                rec.status = status
        if old_status != status:
            self._mark_dirty()
        if refresh and hasattr(self, 'file_manager'):
            self.file_manager.refresh()

    def _reload_group_editor(self, group_id: str):
        ed = getattr(self, 'alignment_editors', {}).get(group_id)
        if not ed:
            return
        rows = self._group_rows(group_id)
        ed.app_state.alignments = rows
        ed.app_state.refresh_from_parent()
        ed.refresh(sync_widgets=False)
        self.notebook.tab(ed, text=self._editor_tab_title(group_id))

    def _editor_tab_title(self, group_id: str) -> str:
        return f"{self.t('alignment_editor')} · {group_id}"

    def _open_editor_tab_for_group(self, group_id: str):
        if not group_id:
            messagebox.showwarning(self.t('alignment_title'), self.t('no_current_group'))
            return None
        self.state_data.settings['current_group_id'] = group_id
        if group_id in getattr(self, 'alignment_editors', {}):
            ed = self.alignment_editors[group_id]
            ed.app_state.refresh_from_parent()
            ed.update_group_info()
            self.notebook.select(ed)
            self.alignment_editor = ed
            return ed
        rows = self._group_rows(group_id)
        proxy = GroupEditorState(self.state_data, group_id, rows)
        ed = AlignmentEditorFrame(self.notebook, proxy, self._editor_callbacks(group_id))
        self.alignment_editors[group_id] = ed
        self.notebook.add(ed, text=self._editor_tab_title(group_id))
        self.notebook.select(ed)
        self.alignment_editor = ed
        ed.refresh(sync_widgets=False)
        self.log(self.t('current_group_opened', group=group_id))
        return ed

    def close_group_editor(self, group_id: str = '', sync: bool = True):
        ed = None
        if group_id:
            ed = getattr(self, 'alignment_editors', {}).get(group_id)
        if ed is None:
            ed = self._active_alignment_editor()
            group_id = getattr(ed.app_state, 'group_id', '') if ed else group_id
        if not ed:
            return
        if sync:
            self._sync_group_editor(ed)
        try:
            self.notebook.forget(ed)
        except Exception:
            pass
        try:
            ed.destroy()
        except Exception:
            pass
        self.alignment_editors.pop(group_id, None)
        self.alignment_editor = None
        self.notebook.select(self.file_manager)

    def choose_open_group_editor(self):
        ids = self._available_group_ids()
        if not ids:
            messagebox.showwarning(self.t('alignment_title'), self.t('import_files_first'))
            return
        top = tk.Toplevel(self)
        top.title(self.t('open_group'))
        top.geometry('360x420')
        ttk.Label(top, text=self.t('select_group_to_open')).pack(anchor='w', padx=10, pady=8)
        lb = tk.Listbox(top)
        lb.pack(fill='both', expand=True, padx=10, pady=4)
        for gid in ids:
            label = f"{gid}  -  {self.t('status_' + self._group_status(gid)) if self._group_status(gid) else self.t('status_imported')}"
            lb.insert('end', label)
        def do_open():
            sel = lb.curselection()
            if not sel:
                return
            gid = ids[int(sel[0])]
            top.destroy()
            self.open_group_editor(gid)
        ttk.Button(top, text=self.t('open_group'), command=do_open, style='Accent.TButton').pack(side='left', padx=10, pady=10)
        ttk.Button(top, text=self.t('close'), command=top.destroy).pack(side='right', padx=10, pady=10)

    def complete_group_alignment(self, group_id: str = ''):
        gid = group_id or self._current_group_id()
        ed = getattr(self, 'alignment_editors', {}).get(gid) or self._active_alignment_editor()
        if ed:
            self._sync_group_editor(ed)
        self._set_group_status(gid, 'completed')
        self.log(self.t('group_completed', group=gid))
        messagebox.showinfo(self.t('complete_alignment'), self.t('group_completed', group=gid))

    def _close_all_editors(self, sync: bool = False):
        for gid in list(getattr(self, 'alignment_editors', {}).keys()):
            self.close_group_editor(gid, sync=sync)

    def _show_gpu_startup_info(self):
        info = get_hardware_info()
        self.log(format_hardware_message(info))
        seg_gpu_enabled = bool(self.state_data.settings.get('use_segmentation_gpu', True))
        seg_requested = self.state_data.settings.get('segmentation_device') or self.state_data.settings.get('device') or 'auto'
        seg_device = resolve_device(seg_requested) if seg_gpu_enabled else 'cpu'
        if seg_device.startswith('cuda'):
            self.log(self.t('segmentation_gpu_enabled', device=seg_device))
        else:
            reason = 'CUDA/GPU unavailable' if seg_gpu_enabled else 'segmentation GPU disabled'
            self.log(self.t('segmentation_cpu_fallback', reason=reason))

    def log(self, msg: str):
        self.log_panel.log(msg)

    def push_undo(self):
        self.undo.push(self._snapshot())
        self._mark_dirty()

    def _snapshot(self):
        return {
            'files': [f.to_dict() for f in self.state_data.files],
            'segments_by_file': {k: [s.to_dict() for s in v] for k, v in self.state_data.segments_by_file.items()},
            'paragraph_segments_by_file': {k: [s.to_dict() for s in v] for k, v in self.state_data.paragraph_segments_by_file.items()},
            'alignments': [a.to_dict() for a in self.state_data.alignments],
            'paragraph_alignments': [a.to_dict() for a in self.state_data.paragraph_alignments],
            'suggestions': list(self.state_data.llm_suggestions),
        }

    def _restore_snapshot(self, snap):
        self.state_data.files = [FileRecord.from_dict(x) for x in snap.get('files', [])]
        self.state_data.segments_by_file = {k: [Segment.from_dict(s) for s in v] for k, v in snap.get('segments_by_file', {}).items()}
        self.state_data.paragraph_segments_by_file = {k: [Segment.from_dict(s) for s in v] for k, v in snap.get('paragraph_segments_by_file', {}).items()}
        self.state_data.alignments = [AlignmentUnit.from_dict(x) for x in snap.get('alignments', [])]
        self.state_data.paragraph_alignments = [AlignmentUnit.from_dict(x) for x in snap.get('paragraph_alignments', [])]
        self.state_data.llm_suggestions = snap.get('suggestions', [])
        self._normalize_similarity_status()
        self._close_all_editors(); self.file_manager.refresh()

    def undo_action(self):
        ed = self._active_alignment_editor()
        if not ed:
            messagebox.showwarning(self.t('alignment_editor'), self.t('open_group_first'))
            return
        if ed.undo_action():
            self._sync_group_editor(ed)
            self._mark_dirty()
            self.log(self.t('undo_applied'))

    def redo_action(self):
        ed = self._active_alignment_editor()
        if not ed:
            messagebox.showwarning(self.t('alignment_editor'), self.t('open_group_first'))
            return
        if ed.redo_action():
            self._sync_group_editor(ed)
            self._mark_dirty()
            self.log(self.t('redo_applied'))

    def new_project(self):
        if not self._confirm_save_if_needed():
            return
        self._reset_project_state()
        self.log(self.t('new_project_created'))

    def close_project(self):
        if not self._has_project_content():
            self._reset_project_state()
            return
        if not self._confirm_save_if_needed():
            return
        self._reset_project_state()
        self.log(self.t('project_closed'))

    def open_project(self):
        if not self._confirm_save_if_needed():
            return
        path = filedialog.askopenfilename(filetypes=[('AlignLens Project','*.alignlens'),('JSON','*.json'),('All','*.*')])
        if not path: return
        try:
            self._close_all_editors(sync=False)
            data = load_project(path)
            self.state_data.project_path = path
            loaded_name = (data.get('project_name') or '').strip()
            if not loaded_name or loaded_name == 'Untitled AlignLens Project':
                loaded_name = Path(path).stem
            self.state_data.project_name = loaded_name
            self.state_data.files = data.get('files', [])
            self.state_data.segments_by_file = data.get('segments_by_file', {})
            self.state_data.paragraph_segments_by_file = data.get('paragraph_segments_by_file', {})
            self.state_data.alignments = data.get('alignments', [])
            self.state_data.paragraph_alignments = data.get('paragraph_alignments', [])
            self.state_data.llm_suggestions = data.get('llm_suggestions', [])
            self.state_data.settings.update(data.get('settings', {}))
            self._apply_precision_defaults(self.state_data.settings)
            self._save_settings()
            self._normalize_similarity_status()
            if not self.state_data.settings.get('file_columns') and hasattr(self.file_manager, 'remember_columns_from_files'):
                self.file_manager.remember_columns_from_files()
            self.project_var.set(self.state_data.project_name)
            try:
                self.project_entry.delete(0, tk.END)
                self.project_entry.insert(0, self.state_data.project_name)
            except Exception:
                pass
            self.file_manager.app_state = self.state_data
            self.file_manager.refresh()
            self._mark_clean()
            try:
                self.update_idletasks()
            except Exception:
                pass
            self.log(f'Project opened: {path}')
        except Exception as exc:
            messagebox.showerror(self.t('open_project_failed'), str(exc))

    def save_project(self):
        self.state_data.project_name = self.project_var.get().strip() or 'Untitled AlignLens Project'
        if not self.state_data.project_path:
            return self.save_project_as()
        try:
            self._sync_all_group_editors()
            save_project(self.state_data.project_path, self.state_data.project_name, self.state_data.files, self.state_data.segments_by_file, self.state_data.alignments, self.state_data.settings, self.state_data.llm_suggestions, self.state_data.paragraph_segments_by_file, self.state_data.paragraph_alignments)
            self._save_settings(); self._mark_clean(); self.log(f'Project saved: {self.state_data.project_path}')
            return True
        except Exception as exc:
            messagebox.showerror(self.t('save_project_failed'), str(exc))
            return False

    def save_project_as(self):
        path = filedialog.asksaveasfilename(defaultextension='.alignlens', filetypes=[('AlignLens Project','*.alignlens'),('All','*.*')])
        if not path:
            return False
        self.state_data.project_path = path
        return self.save_project()

    def import_wizard(self):
        def add_records(records, mode='1_to_1', column_defs=None):
            column_defs = column_defs or []
            existing = {normalized_file_key(f.path) for f in self.state_data.files if getattr(f, 'path', '')}
            clean = []
            skipped = 0
            for rec in records:
                key = normalized_file_key(rec.path)
                if key in existing:
                    skipped += 1
                    continue
                clean.append(rec)
            if skipped:
                self.log(self.t('duplicate_files_skipped', count=skipped))
            self.push_undo()
            self.state_data.settings['alignment_project_mode'] = mode
            self.state_data.settings['last_alignment_project_mode'] = mode
            self.state_data.settings['last_target_count'] = len([d for d in column_defs if d.get('alignment_role') == 'target']) or 1
            src_lang = next((d.get('lang') for d in column_defs if d.get('alignment_role') == 'source'), None)
            tgt_langs = [d.get('lang') for d in column_defs if d.get('alignment_role') == 'target' and d.get('lang')]
            if src_lang:
                self.state_data.settings['last_source_lang'] = src_lang
            if tgt_langs:
                self.state_data.settings['last_target_langs'] = tgt_langs
            if hasattr(self.file_manager, 'set_column_defs'):
                self.file_manager.set_column_defs(column_defs)
            if clean:
                self.state_data.files.extend(clean)
                if hasattr(self.file_manager, 'regenerate_groups_by_position'):
                    self.file_manager.regenerate_groups_by_position()
            self._save_settings()
            self._close_all_editors(); self.file_manager.refresh()
            self.notebook.select(self.file_manager)
            self.log(f'Imported {len(clean)} file(s) through mode-first import wizard. Mode={mode}')
        ImportWizard(self, add_records, ui_lang=self.state_data.settings.get('gui_language', 'zh_sim'), existing_paths=[f.path for f in self.state_data.files])

    def _files_for_groups(self, group_ids: Optional[List[str]] = None) -> List[FileRecord]:
        if not group_ids:
            return list(self.state_data.files)
        wanted = set(group_ids)
        return [f for f in self.state_data.files if f.group_id in wanted]

    def _available_group_ids(self) -> List[str]:
        ids: List[str] = []
        for f in sorted(self.state_data.files, key=lambda r: (r.sort_order, r.group_id)):
            if f.group_id not in ids:
                ids.append(f.group_id)
        return ids

    def _current_group_id(self) -> str:
        gid = ''
        if hasattr(self, 'file_manager'):
            try:
                gid = self.file_manager.selected_group_id()
            except Exception:
                gid = ''
        if not gid:
            gid = self.state_data.settings.get('current_group_id', '')
        if not gid:
            ids = self._available_group_ids()
            gid = ids[0] if ids else ''
        if gid:
            self.state_data.settings['current_group_id'] = gid
        return gid

    def _segment_worker(self, group_ids: Optional[List[str]] = None, unit_level: str = '', progress=None, cancel_event=None):
        unit_level = (unit_level or self.state_data.settings.get('alignment_unit', 'sentence') or 'sentence').lower()
        use_paragraph = unit_level == 'paragraph'
        segments_by_file = dict(self.state_data.paragraph_segments_by_file if use_paragraph else self.state_data.segments_by_file)
        files = self._files_for_groups(group_ids)
        total = max(len(files), 1)
        for idx, rec in enumerate(files, 1):
            if cancel_event and cancel_event.is_set():
                break
            if progress: progress(f'Reading and segmenting {rec.filename}', idx/total*0.8)
            try:
                planned_segmenter = 'paragraph' if use_paragraph else describe_profile(self.state_data.settings, rec.lang or 'en', 'sentence')
                if self.state_data.settings.get('segmentation_cache_enabled', True) and rec.file_id in segments_by_file and rec.segmentation_level == unit_level and rec.segmentation_engine == planned_segmenter:
                    rec.status = 'segmented_cached'
                    continue
                if not rec.text:
                    rec.text = read_document(rec.path, preserve_paragraphs=self.state_data.settings.get('preserve_paragraphs', True), remove_excessive_spaces=self.state_data.settings.get('remove_excessive_spaces', True))
                    rec.char_count, rec.paragraph_count = text_stats(rec.text)
                seg_mode = 'paragraph' if use_paragraph else self.state_data.settings.get('segmentation_mode', 'auto')
                segs = split_text(
                    rec.text, rec.lang or 'en', rec.file_id,
                    mode=seg_mode,
                    paragraph_aware=True if use_paragraph else bool(self.state_data.settings.get('paragraph_aware', True)),
                    split_by_line=False if use_paragraph else bool(self.state_data.settings.get('split_by_line', False)),
                    split_by_paragraph=True if use_paragraph else bool(self.state_data.settings.get('split_by_paragraph', False)),
                    settings=self.state_data.settings,
                )
                segments_by_file[rec.file_id] = segs
                rec.sentence_count = len(segs)
                rec.segmentation_level = unit_level
                rec.segmentation_engine = planned_segmenter
                rec.segmentation_model = rec.segmentation_engine
                rec.status = 'segmented'
            except Exception as exc:
                rec.status = 'segmentation_failed'; rec.note = str(exc)
        if progress: progress('Segmentation completed', 1.0)
        return ('segments', segments_by_file, group_ids, unit_level)

    def segment_current_group(self, group_id: str = ''):
        return self.segment_only(group_id=group_id or self._current_group_id(), batch=False)

    def segment_only(self, group_id: str = '', batch: bool = False, unit_level: str = ''):
        if not self.state_data.files:
            messagebox.showwarning(self.t('segment_title'), self.t('import_files_first')); return
        group_ids = None if batch else [group_id or self._current_group_id()]
        if not batch and not group_ids[0]:
            messagebox.showwarning(self.t('segment_title'), self.t('no_current_group')); return
        level = unit_level or self.state_data.settings.get('alignment_unit', 'sentence')
        self.push_undo(); self._start_task(lambda progress=None, cancel_event=None: self._segment_worker(group_ids=group_ids, unit_level=level, progress=progress, cancel_event=cancel_event), on_done=self._on_segments_done)

    def _replace_visible_alignments(self, rows: List[AlignmentUnit], group_ids: Optional[List[str]] = None, unit_level: str = 'sentence'):
        rows = deduplicate_alignment_units(rows)
        wanted = set(group_ids or [])
        if wanted:
            preserved = [u for u in self.state_data.alignments if u.group_id not in wanted]
            merged = preserved + rows
        else:
            merged = rows
        for i, u in enumerate(merged, 1):
            u.row_id = i
        self.state_data.alignments = merged
        return merged

    def _replace_paragraph_alignments(self, rows: List[AlignmentUnit], group_ids: Optional[List[str]] = None):
        rows = deduplicate_alignment_units(rows)
        wanted = set(group_ids or [])
        if wanted:
            preserved = [u for u in self.state_data.paragraph_alignments if u.group_id not in wanted]
            merged = preserved + rows
        else:
            merged = rows
        for i, u in enumerate(merged, 1):
            u.row_id = i
        self.state_data.paragraph_alignments = merged
        return merged

    def _on_segments_done(self, result):
        _, segs, group_ids, unit_level = result
        if unit_level == 'paragraph':
            self.state_data.paragraph_segments_by_file = segs
            rows = self._build_manual_alignments(group_ids, unit_level='paragraph')
            self._replace_paragraph_alignments(rows, group_ids)
            self._replace_visible_alignments(rows, group_ids, unit_level='paragraph')
            status = 'segmented_paragraph'
        else:
            self.state_data.segments_by_file = segs
            rows = self._build_manual_alignments(group_ids, unit_level='sentence')
            self._replace_visible_alignments(rows, group_ids, unit_level='sentence')
            status = 'segmented_sentence'
        if group_ids and group_ids[0]:
            gid = group_ids[0]
            self.state_data.settings['current_group_id'] = gid
            self._set_group_status(gid, status, refresh=False)
            self._reload_group_editor(gid)
            self._open_editor_tab_for_group(gid)
        self.file_manager.refresh()
        self.log(self.t('segmentation_manual_table_created'))

    def _record_column_key(self, rec: FileRecord) -> str:
        if rec.column_key:
            return rec.column_key
        return f"source_{rec.lang or 'unknown'}" if rec.alignment_role == 'source' else f"target_{int(rec.target_index or 1):02d}_{rec.lang or 'unknown'}"

    def _group_segments(self, group_ids: Optional[List[str]] = None, unit_level: str = 'sentence') -> Dict[str, Dict[str, List[Segment]]]:
        grouped: Dict[str, Dict[str, List[Segment]]] = {}
        source_map = self.state_data.paragraph_segments_by_file if (unit_level or 'sentence') == 'paragraph' else self.state_data.segments_by_file
        wanted = set(group_ids or [])
        for rec in sorted(self.state_data.files, key=lambda f: (f.group_id, f.sort_order, f.target_index)):
            if wanted and rec.group_id not in wanted:
                continue
            if rec.file_id not in source_map:
                continue
            key = self._record_column_key(rec)
            grouped.setdefault(rec.group_id, {}).setdefault(key, []).extend(source_map[rec.file_id])
        return grouped

    def _build_manual_alignments(self, group_ids: Optional[List[str]] = None, unit_level: str = 'sentence') -> List[AlignmentUnit]:
        rows = []
        for gid, lang_map in self._group_segments(group_ids, unit_level=unit_level).items():
            source_lang = self._choose_source_lang(list(lang_map.keys()))
            rows.extend(manual_align_by_index(lang_map, gid, source_lang, level=unit_level))
        for i, u in enumerate(rows, 1):
            u.row_id = i
        return rows

    def _choose_source_lang(self, langs: List[str]) -> str:
        for lang in langs:
            if lang.startswith('source_'):
                return lang
        for pref in ['zh_sim', 'zh_tra', 'en', 'de', 'fr', 'es', 'ru', 'ja']:
            if pref in langs:
                return pref
        return langs[0] if langs else 'source'

    def _alignment_columns(self) -> List[str]:
        cols: List[str] = []
        defs = {d.get('column_key'): dict(d) for d in (self.state_data.settings.get('file_columns', []) or []) if d.get('column_key')}
        if defs:
            def keyfunc(col):
                d = defs[col]
                return (0 if d.get('alignment_role') == 'source' else 1, int(d.get('target_index') or 1), col)
            cols.extend(sorted(defs.keys(), key=keyfunc))
        for f in self.state_data.files:
            col = self._record_column_key(f)
            if col not in cols:
                cols.append(col)
        for u in self.state_data.alignments:
            for col in u.segments.keys():
                if col not in cols:
                    cols.append(col)
        return cols

    def _source_column(self, cols: Optional[List[str]] = None) -> str:
        cols = cols or self._alignment_columns()
        defs = {d.get('column_key'): dict(d) for d in (self.state_data.settings.get('file_columns', []) or []) if d.get('column_key')}
        for col in cols:
            if defs.get(col, {}).get('alignment_role') == 'source' or col.startswith('source_'):
                return col
        return self._choose_source_lang(cols)

    def _target_columns(self, cols: Optional[List[str]] = None) -> List[str]:
        cols = cols or self._alignment_columns()
        src = self._source_column(cols)
        return [c for c in cols if c != src]

    def _threshold_for_level(self, level: str = 'sentence') -> float:
        if (level or 'sentence').lower() == 'paragraph':
            return float(self.state_data.settings.get('paragraph_min_similarity_threshold', 0.50) or 0.50)
        return float(self.state_data.settings.get('min_similarity_threshold', 0.55) or 0.55)

    def _row_has_low_similarity(self, unit: AlignmentUnit, threshold: Optional[float] = None) -> bool:
        threshold = self._threshold_for_level(getattr(unit, 'alignment_level', 'sentence')) if threshold is None else float(threshold)
        # Residual/empty rows are not low similarity in the strict numerical
        # sense, but they must still be reviewed; _row_needs_alignment_review()
        # handles those.
        if 'empty' in (unit.status or '') or 'residual' in (unit.status or '') or 'residual' in (unit.issue_type or ''):
            return False
        vals = list((unit.similarities or {}).values())
        if vals:
            return any(float(v) < threshold for v in vals)
        if unit.similarity is not None:
            return float(unit.similarity or 0.0) < threshold
        return unit.issue_type == 'low_similarity' or unit.status == 'low_similarity'

    def _row_needs_alignment_review(self, unit: AlignmentUnit, threshold: Optional[float] = None) -> bool:
        if unit.confirmed:
            return False
        status = unit.status or ''
        issue = unit.issue_type or ''
        if 'empty' in status or 'residual' in status or 'residual' in issue:
            return True
        if status == 'needs_review':
            return True
        return self._row_has_low_similarity(unit, threshold)

    def _normalize_similarity_status(self, rows: Optional[List[AlignmentUnit]] = None) -> int:
        rows = rows if rows is not None else self.state_data.alignments
        changed = 0
        for u in rows:
            if u.confirmed:
                continue
            if self._row_has_low_similarity(u):
                if u.status != 'needs_review' or u.issue_type != 'low_similarity':
                    u.status = 'needs_review'
                    u.issue_type = 'low_similarity'
                    changed += 1
            elif u.issue_type == 'low_similarity':
                u.issue_type = ''
                if u.status == 'needs_review':
                    u.status = 'auto_high_confidence' if float(u.similarity or 0.0) >= float(self.state_data.settings.get('high_confidence_threshold', 0.70)) else 'needs_review'
                    changed += 1
        return changed

    def _params(self) -> AlignmentParams:
        s = self.state_data.settings
        return AlignmentParams(
            max_window=int(s.get('max_window', 5)), skip_penalty=float(s.get('skip_penalty', -0.30)),
            empty_penalty=float(s.get('empty_penalty', -0.30)), length_penalty_weight=float(s.get('length_penalty_weight', 0.02)),
            paragraph_distance_penalty=float(s.get('paragraph_distance_penalty', 0.04)),
            min_similarity_threshold=float(s.get('min_similarity_threshold', 0.55)),
            high_confidence_threshold=float(s.get('high_confidence_threshold', 0.70)),
            low_similarity_match_penalty=float(s.get('low_similarity_match_penalty', 0.25)),
            sentence_max_merge_units=int(s.get('sentence_max_merge_units', 3) or 3),
            sentence_allow_2_to_2=bool(s.get('sentence_allow_2_to_2', True)),
            sentence_merge_penalty=float(s.get('sentence_merge_penalty', 0.25) or 0.25),
            sentence_strict_fine_alignment=bool(s.get('sentence_strict_fine_alignment', True)),
            allow_cross_paragraph=bool(s.get('allow_cross_paragraph', True)), residual_matching=bool(s.get('residual_matching', True)),
            batch_size=int(s.get('batch_size', 32)), device=s.get('device', 'auto'), model_mode=s.get('alignment_mode', 'fused'),
            custom_model=s.get('custom_embedding_model') or s.get('default_embedding_model', ''),
            primary_model=s.get('primary_transformer_model') or s.get('default_embedding_model', ''),
            secondary_model=s.get('secondary_transformer_model') or 'intfloat/multilingual-e5-base',
            use_secondary_model=bool(s.get('use_secondary_transformer_model', True)),
            dp_cpu_workers=int(s.get('dp_cpu_workers', 0) or 0),
            large_doc_threshold=int(s.get('large_doc_threshold', 2000000)),
            dp_band_size=int(s.get('dp_band_size', 240)),
            dp_search_mode=s.get('dp_search_mode', 'full'),
            alignment_level=s.get('alignment_unit', 'sentence'),
        )

    def _params_for_level(self, unit_level: str) -> AlignmentParams:
        params = self._params()
        unit_level = (unit_level or 'sentence').lower()
        params.alignment_level = unit_level
        if unit_level == 'paragraph':
            # Conservative natural-paragraph alignment: never merge paragraphs.
            # Lower threshold reflects that paragraph embeddings cover more text
            # and are naturally less sharply comparable than sentence embeddings.
            params.max_window = 1
            params.allow_cross_paragraph = False
            params.min_similarity_threshold = float(self.state_data.settings.get('paragraph_min_similarity_threshold', 0.50) or 0.50)
            params.high_confidence_threshold = max(params.min_similarity_threshold + 0.15, min(float(self.state_data.settings.get('high_confidence_threshold', 0.70) or 0.70), 0.78))
        else:
            params.min_similarity_threshold = float(self.state_data.settings.get('min_similarity_threshold', 0.55) or 0.55)
            # Sentence alignment uses existing sentence segments as-is but
            # prevents DP from merging too many of them into one large cell.
            params.max_window = min(int(params.max_window or 1), max(1, int(self.state_data.settings.get('sentence_max_merge_units', 3) or 3)))
        return params

    def _align_worker(self, group_ids: Optional[List[str]] = None, unit_level: str = '', within_paragraphs: bool = False, progress=None, cancel_event=None):
        unit_level = (unit_level or self.state_data.settings.get('alignment_unit', 'sentence') or 'sentence').lower()
        files = self._files_for_groups(group_ids)
        seg_store = self.state_data.paragraph_segments_by_file if unit_level == 'paragraph' else self.state_data.segments_by_file
        # Keep sentence and paragraph segment stores strictly separated.  Older
        # projects or stale caches may contain a file id in the wrong store; in
        # that case rebuild the requested level instead of aligning paragraph
        # units as if they were sentences.
        if any(f.file_id not in seg_store or (getattr(f, 'segmentation_level', '') and f.segmentation_level != unit_level) for f in files):
            seg_result = self._segment_worker(group_ids=group_ids, unit_level=unit_level, progress=progress, cancel_event=cancel_event)
            if isinstance(seg_result, tuple) and seg_result[0] == 'segments':
                if unit_level == 'paragraph':
                    self.state_data.paragraph_segments_by_file = seg_result[1]
                else:
                    self.state_data.segments_by_file = seg_result[1]
        grouped = self._group_segments(group_ids, unit_level=unit_level)
        all_rows: List[AlignmentUnit] = []
        params = self._params_for_level(unit_level)
        embedder = EmbeddingModelManager(model_root=self.state_data.settings.get('model_root'), device=params.device, batch_size=params.batch_size)
        groups = list(grouped.items())
        for gidx, (gid, lang_map) in enumerate(groups, 1):
            if cancel_event and cancel_event.is_set(): break
            langs = list(lang_map.keys())
            if len(langs) < 2:
                all_rows.extend(manual_align_by_index(lang_map, gid, self._choose_source_lang(langs), level=unit_level))
                continue
            src_lang = self._choose_source_lang(langs)
            src_segments = lang_map[src_lang]
            target_results = {}
            for tgt_lang in [l for l in langs if l != src_lang]:
                def p(msg, val, gid=gid, tgt=tgt_lang):
                    if progress:
                        progress(f'{gid} {src_lang}->{tgt}: {msg}', (gidx-1)/max(len(groups),1) + val/max(len(groups),1))
                if unit_level == 'sentence' and within_paragraphs and self.state_data.paragraph_alignments:
                    para_rows = [u for u in self.state_data.paragraph_alignments if u.group_id == gid]
                    target_results[tgt_lang] = align_bilingual_transformer_within_paragraphs(src_segments, lang_map[tgt_lang], para_rows, src_lang, tgt_lang, gid, params, embedder, p)
                else:
                    target_results[tgt_lang] = align_bilingual_transformer(src_segments, lang_map[tgt_lang], src_lang, tgt_lang, gid, params, embedder, p)
            if len(target_results) == 1:
                all_rows.extend(next(iter(target_results.values())))
            else:
                all_rows.extend(combine_multilingual_by_pivot(src_lang, target_results, gid))
        all_rows = deduplicate_alignment_units(all_rows)
        for i, u in enumerate(all_rows, 1):
            u.row_id = i
        return ('alignments', all_rows, group_ids, unit_level)

    def align_current_group(self, group_id: str = ''):
        # Kept for legacy shortcuts: this still runs Transformer alignment.
        return self.run_transformer_alignment(group_id=group_id or self._current_group_id(), batch=False)

    def _ask_unsegmented_group_action(self, group_id: str) -> str:
        top = tk.Toplevel(self)
        top.title(self.t('open_group'))
        top.geometry('520x260')
        top.resizable(False, False)
        result = {'value': ''}
        ttk.Label(top, text=self.t('unsegmented_group_prompt', group=group_id), wraplength=480).pack(fill='x', padx=14, pady=(14, 8))
        btns = ttk.Frame(top); btns.pack(fill='both', expand=True, padx=14, pady=8)
        actions = [
            ('segment_paragraph', 'segment_paragraph'),
            ('segment_sentence', 'segment_sentence'),
            ('paragraph_alignment', 'paragraph_align'),
            ('sentence_alignment', 'sentence_align'),
        ]
        def choose(v):
            result['value'] = v
            top.destroy()
        for key, val in actions:
            ttk.Button(btns, text=self.t(key), command=lambda v=val: choose(v)).pack(fill='x', pady=3)
        ttk.Button(top, text=self.t('cancel'), command=top.destroy).pack(pady=(0, 12))
        top.transient(self); top.grab_set(); self.wait_window(top)
        return result['value']

    def open_group_editor(self, group_id: str = ''):
        gid = group_id or self._current_group_id()
        if not gid:
            messagebox.showwarning(self.t('alignment_title'), self.t('no_current_group')); return
        self.state_data.settings['current_group_id'] = gid
        existing = self._group_rows(gid)
        if existing:
            return self._open_editor_tab_for_group(gid)
        sentence_segmented = any(f.group_id == gid and f.file_id in self.state_data.segments_by_file for f in self.state_data.files)
        paragraph_segmented = any(f.group_id == gid and f.file_id in self.state_data.paragraph_segments_by_file for f in self.state_data.files)
        if sentence_segmented or paragraph_segmented:
            level = 'sentence' if sentence_segmented else 'paragraph'
            self.push_undo()
            rows = self._build_manual_alignments([gid], unit_level=level)
            if level == 'paragraph':
                self._replace_paragraph_alignments(rows, [gid])
            self._replace_visible_alignments(rows, [gid], unit_level=level)
            self._set_group_status(gid, 'editing', refresh=False)
            ed = self._open_editor_tab_for_group(gid)
            self.file_manager.refresh()
            self.log(self.t('manual_table_opened', group=gid))
            return ed
        action = self._ask_unsegmented_group_action(gid)
        if action == 'segment_sentence':
            return self.segment_only(group_id=gid, unit_level='sentence')
        if action == 'segment_paragraph':
            return self.segment_only(group_id=gid, unit_level='paragraph')
        if action == 'sentence_align':
            return self.run_sentence_alignment(group_id=gid)
        if action == 'paragraph_align':
            return self.run_paragraph_alignment(group_id=gid)
        self.log(self.t('no_existing_alignment_for_group', group=gid))

    def open_current_group_editor(self):
        return self.open_group_editor(self._current_group_id())

    def run_batch_transformer_alignment(self):
        return self.run_transformer_alignment(batch=True)

    def _confirm_overwrite_completed_groups(self, group_ids: Optional[List[str]]) -> bool:
        ids = group_ids or self._available_group_ids()
        completed = [gid for gid in ids if self._group_status(gid) == 'completed']
        if not completed:
            return True
        msg = self.t('confirm_realign_completed', groups=', '.join(completed[:8]))
        return messagebox.askyesno(self.t('alignment_title'), msg)

    def run_transformer_alignment(self, group_id: str = '', batch: bool = False, unit_level: str = '', within_paragraphs: bool = False, group_ids_override: Optional[List[str]] = None):
        if not self.state_data.files:
            messagebox.showwarning(self.t('alignment_title'), self.t('import_files_first')); return
        group_ids = group_ids_override if group_ids_override is not None else (None if batch else [group_id or self._current_group_id()])
        if batch and group_ids_override is None and (unit_level or 'sentence').lower() == 'sentence':
            group_ids = self._choose_batch_sentence_groups('sentence')
            if group_ids is None:
                return
            if not group_ids:
                return
        if not batch and not group_ids[0]:
            messagebox.showwarning(self.t('alignment_title'), self.t('no_current_group')); return
        if not self._confirm_overwrite_completed_groups(group_ids):
            return
        level = unit_level or self.state_data.settings.get('alignment_unit', 'sentence')
        for gid in (group_ids or self._available_group_ids()):
            self._set_group_status(gid, 'aligning', refresh=False)
        self.file_manager.refresh()
        self.push_undo(); self._start_task(lambda progress=None, cancel_event=None: self._align_worker(group_ids=group_ids, unit_level=level, within_paragraphs=within_paragraphs, progress=progress, cancel_event=cancel_event), on_done=self._on_alignments_done)

    def _on_alignments_done(self, result):
        if len(result) >= 4:
            _, rows, group_ids, unit_level = result
        else:
            _, rows, group_ids = result
            unit_level = 'sentence'
        self._normalize_similarity_status(rows)
        if unit_level == 'paragraph':
            self._replace_paragraph_alignments(rows, group_ids)
        rows = self._replace_visible_alignments(rows, group_ids, unit_level=unit_level)
        if group_ids and len(group_ids) == 1 and group_ids[0]:
            gid = group_ids[0]
            self.state_data.settings['current_group_id'] = gid
            self._set_group_status(gid, 'aligned_paragraph' if unit_level == 'paragraph' else 'aligned_sentence', refresh=False)
            self._reload_group_editor(gid)
            self._open_editor_tab_for_group(gid)
            self.log(self.t('current_group_aligned', group=gid))
        else:
            for gid in (group_ids or self._available_group_ids()):
                self._set_group_status(gid, 'aligned_paragraph' if unit_level == 'paragraph' else 'aligned_sentence', refresh=False)
                self._reload_group_editor(gid)
        self.file_manager.refresh()
        review_count = sum(1 for u in rows if self._row_needs_alignment_review(u))
        low_count = sum(1 for u in rows if self._row_has_low_similarity(u))
        residual_count = sum(1 for u in rows if (('residual' in (u.status or '')) or ('residual' in (u.issue_type or '')) or ('empty' in (u.status or ''))))
        self.log(self.t('transformer_alignment_completed', rows=len(rows), low=review_count, level=self.t('paragraph') if unit_level == 'paragraph' else self.t('sentence')) + f' (low_similarity={low_count}, residual/empty={residual_count})')

    def _has_alignment_for_group(self, group_id: str, unit_level: str = 'sentence') -> bool:
        level = (unit_level or 'sentence').lower()
        for u in self.state_data.alignments:
            if u.group_id == group_id and (getattr(u, 'alignment_level', 'sentence') or 'sentence') == level:
                return True
        if level == 'paragraph':
            return any(u.group_id == group_id for u in self.state_data.paragraph_alignments)
        return False

    def _choose_batch_sentence_groups(self, unit_level: str = 'sentence') -> Optional[List[str]]:
        groups = self._available_group_ids()
        if not groups:
            return []
        if (unit_level or 'sentence').lower() != 'sentence':
            return groups
        msg = self.t('batch_sentence_realign_choice')
        ans = messagebox.askyesnocancel(self.t('batch_transformer_sentence_alignment'), msg)
        if ans is None:
            return None
        if ans is True:
            return groups
        todo = [gid for gid in groups if not self._has_alignment_for_group(gid, 'sentence') and self._group_status(gid) not in {'aligned_sentence', 'completed'}]
        if not todo:
            messagebox.showinfo(self.t('batch_transformer_sentence_alignment'), self.t('no_unaligned_groups'))
            return []
        return todo

    def run_paragraph_alignment(self, group_id: str = '', batch: bool = False):
        return self.run_transformer_alignment(group_id=group_id or self._current_group_id(), batch=batch, unit_level='paragraph', within_paragraphs=False)

    def run_sentence_alignment(self, group_id: str = '', batch: bool = False):
        # Sentence alignment is independent from paragraph alignment. Both modes
        # segment directly from source texts and run Transformer alignment at
        # their own unit level.
        group_ids = None
        if batch:
            group_ids = self._choose_batch_sentence_groups('sentence')
            if group_ids is None:
                return
            if not group_ids:
                return
        return self.run_transformer_alignment(group_id=group_id or self._current_group_id(), batch=batch, unit_level='sentence', within_paragraphs=False, group_ids_override=group_ids)


    def _llm_worker(self, group_ids: Optional[List[str]] = None, unit_level: str = 'sentence', progress=None, cancel_event=None):
        unit_level = (unit_level or 'sentence').lower()
        files = self._files_for_groups(group_ids)
        seg_store = self.state_data.paragraph_segments_by_file if unit_level == 'paragraph' else self.state_data.segments_by_file
        # Keep sentence and paragraph segment stores strictly separated.  Older
        # projects or stale caches may contain a file id in the wrong store; in
        # that case rebuild the requested level instead of aligning paragraph
        # units as if they were sentences.
        if any(f.file_id not in seg_store or (getattr(f, 'segmentation_level', '') and f.segmentation_level != unit_level) for f in files):
            seg_result = self._segment_worker(group_ids=group_ids, unit_level=unit_level, progress=progress, cancel_event=cancel_event)
            if isinstance(seg_result, tuple) and seg_result[0] == 'segments':
                if unit_level == 'paragraph':
                    self.state_data.paragraph_segments_by_file = seg_result[1]
                else:
                    self.state_data.segments_by_file = seg_result[1]
        s = self.state_data.settings
        client = OpenAILLMClient(
            s.get('openai_api_key',''),
            s.get('openai_model','gpt-5.4-mini'),
            float(s.get('llm_temperature',0)),
            int(s.get('llm_timeout',90)),
            int(s.get('llm_max_tokens',3000)),
            strict_json=bool(s.get('strict_json_mode', True)),
            retry_times=int(s.get('llm_retry_times', 1) or 1),
        )
        rows = []
        verify_with_transformer = bool(s.get('llm_verify_with_transformer', True))
        params = self._params_for_level(unit_level)
        embedder = EmbeddingModelManager(model_root=self.state_data.settings.get('model_root'), device=params.device, batch_size=params.batch_size) if verify_with_transformer else None
        groups = list(self._group_segments(group_ids, unit_level=unit_level).items())
        for gidx, (gid, lang_map) in enumerate(groups, 1):
            if cancel_event and cancel_event.is_set(): break
            langs = list(lang_map.keys())
            if len(langs) < 2:
                rows.extend(manual_align_by_index(lang_map, gid, self._choose_source_lang(langs), level=unit_level)); continue
            src_lang = self._choose_source_lang(langs)
            first_tgt = [l for l in langs if l != src_lang][0]
            if progress: progress(f'LLM aligning {gid}: {src_lang}->{first_tgt}', gidx/max(len(groups),1))
            group_rows = llm_align_bilingual(
                lang_map[src_lang], lang_map[first_tgt], src_lang, first_tgt, gid, client,
                int(s.get('llm_batch_size', 40)), float(s.get('llm_min_confidence', 0.75) or 0.75),
                max_merge_units=int(s.get('sentence_max_merge_units', 3) or 3) if unit_level == 'sentence' else 1,
                allow_2_to_2=bool(s.get('sentence_allow_2_to_2', True)) if unit_level == 'sentence' else False,
            )
            # For additional language/translation columns, add by index as a safe scaffold.
            if len(langs) > 2:
                extra = [l for l in langs if l not in {src_lang, first_tgt}]
                for u in group_rows:
                    for lang in extra:
                        idx = (u.source_ids[0]-1) if u.source_ids else u.row_id-1
                        u.segments[lang] = lang_map[lang][idx].text if 0 <= idx < len(lang_map[lang]) else ''
            if verify_with_transformer and embedder is not None and group_rows:
                targets = [l for l in langs if l != src_lang]
                group_rows = compute_alignment_similarities(group_rows, src_lang, targets, params, embedder, progress)
                for u in group_rows:
                    if (u.status or '').startswith('llm_') and self._row_has_low_similarity(u):
                        u.status = 'needs_review'
                        u.issue_type = 'llm_transformer_conflict'
                        u.note = ((u.note + '\n') if u.note else '') + 'LLM alignment requires review: Transformer similarity is below threshold.'
            rows.extend(group_rows)
        for i, u in enumerate(rows, 1): u.row_id = i
        for u in rows:
            u.alignment_level = unit_level
        return ('alignments', rows, group_ids, unit_level)

    def run_llm_alignment(self, group_id: str = '', batch: bool = False, unit_level: str = 'sentence'):
        if not self.state_data.files:
            messagebox.showwarning(self.t('llm_alignment_title'), self.t('import_files_first')); return
        if not self.state_data.settings.get('openai_api_key'):
            self.open_settings();
            if not self.state_data.settings.get('openai_api_key'):
                messagebox.showwarning(self.t('llm_alignment_title'), self.t('set_openai_key_first')); return
        group_ids = None if batch else [group_id or self._current_group_id()]
        if batch and (unit_level or 'sentence').lower() == 'sentence':
            group_ids = self._choose_batch_sentence_groups('sentence')
            if group_ids is None:
                return
            if not group_ids:
                return
        if not batch and not group_ids[0]:
            messagebox.showwarning(self.t('llm_alignment_title'), self.t('no_current_group')); return
        if not self._confirm_overwrite_completed_groups(group_ids):
            return
        for gid in (group_ids or self._available_group_ids()):
            self._set_group_status(gid, 'aligning', refresh=False)
        self.file_manager.refresh()
        self.push_undo(); self._start_task(lambda progress=None, cancel_event=None: self._llm_worker(group_ids=group_ids, unit_level=unit_level, progress=progress, cancel_event=cancel_event), on_done=self._on_alignments_done)

    def _recompute_similarity_worker(self, rows_data: List[dict], source_col: str, target_cols: List[str], level: str = 'sentence', progress=None, cancel_event=None):
        rows = [AlignmentUnit.from_dict(x) for x in rows_data]
        if cancel_event and cancel_event.is_set():
            return ('similarities', [u.to_dict() for u in rows])
        params = self._params_for_level(level or (getattr(rows[0], 'alignment_level', 'sentence') if rows else 'sentence'))
        embedder = EmbeddingModelManager(model_root=self.state_data.settings.get('model_root'), device=params.device, batch_size=params.batch_size)
        rows = compute_alignment_similarities(rows, source_col, target_cols, params, embedder, progress)
        return ('similarities', [u.to_dict() for u in rows])

    def recompute_similarity(self):
        ed = self._active_alignment_editor()
        if not ed or not ed.app_state.alignments:
            messagebox.showwarning(self.t('alignment_title'), self.t('export_no_rows')); return
        ed._sync_all_widgets()
        self.push_undo()
        rows_data = [u.to_dict() for u in ed.app_state.alignments]
        source_col = ed._source_column()
        target_cols = ed._target_columns()
        level = getattr(ed.app_state.alignments[0], 'alignment_level', 'sentence') if ed.app_state.alignments else 'sentence'
        current = ed.current_cell() if hasattr(ed, 'current_cell') else getattr(ed, 'selected_cell', None)
        keep_row = int(current[0]) if current else None
        keep_col = str(current[1]) if current else (target_cols[0] if target_cols else source_col)
        self._start_task(lambda progress=None, cancel_event=None: self._recompute_similarity_worker(rows_data, source_col, target_cols, level, progress, cancel_event), on_done=lambda result, ed=ed, keep_row=keep_row, keep_col=keep_col: self._on_similarity_done(result, ed, keep_row, keep_col))

    def recompute_current_similarity(self):
        ed = self._active_alignment_editor()
        if not ed or not ed.app_state.alignments:
            messagebox.showwarning(self.t('alignment_title'), self.t('export_no_rows')); return
        current = ed.current_cell() if hasattr(ed, 'current_cell') else getattr(ed, 'selected_cell', None)
        if not current and not ed._ensure_selected_cell():
            messagebox.showwarning(self.t('alignment_title'), self.t('select_rows_first')); return
        current = current or ed.selected_cell
        row_no, keep_col = int(current[0]), str(current[1])
        if not (1 <= row_no <= len(ed.app_state.alignments)):
            return
        ed._sync_all_widgets()
        self.push_undo()
        rows_data = [ed.app_state.alignments[row_no - 1].to_dict()]
        source_col = ed._source_column()
        target_cols = ed._target_columns()
        level = getattr(ed.app_state.alignments[row_no - 1], 'alignment_level', 'sentence')
        self._start_task(lambda progress=None, cancel_event=None: self._recompute_similarity_worker(rows_data, source_col, target_cols, level, progress, cancel_event), on_done=lambda result, row_no=row_no, keep_col=keep_col, ed=ed: self._on_current_similarity_done(result, row_no, ed, keep_col))

    def _on_current_similarity_done(self, result, row_no: int, ed=None, keep_col: str = ''):
        ed = ed or self._active_alignment_editor()
        if not ed:
            return
        _, rows_data = result
        if rows_data and 1 <= row_no <= len(ed.app_state.alignments):
            ed.app_state.alignments[row_no - 1] = AlignmentUnit.from_dict(rows_data[0])
            ed.app_state.alignments[row_no - 1].row_id = row_no
        changed = self._normalize_similarity_status([ed.app_state.alignments[row_no - 1]]) if 1 <= row_no <= len(ed.app_state.alignments) else 0
        self._sync_group_editor(ed)
        if keep_col and keep_col in ed.column_keys:
            ed.selected_cell = (row_no, keep_col)
        ed.refresh(sync_widgets=False)
        self.notebook.select(ed)
        ed.after_idle(lambda r=row_no, c=keep_col: (ed._scroll_to_row(r), setattr(ed, 'selected_cell', (r, c)) if c else None))
        self.log(self.t('current_row_similarity_recomputed', row=row_no))

    def _on_similarity_done(self, result, ed=None, keep_row: Optional[int] = None, keep_col: str = ''):
        ed = ed or self._active_alignment_editor()
        if not ed:
            return
        _, rows_data = result
        ed.app_state.alignments = [AlignmentUnit.from_dict(x) for x in rows_data]
        changed = self._normalize_similarity_status(ed.app_state.alignments)
        self._sync_group_editor(ed)
        if keep_row and keep_col and keep_col in getattr(ed, 'column_keys', []):
            ed.selected_cell = (keep_row, keep_col)
        ed.refresh(sync_widgets=False); self.notebook.select(ed)
        if keep_row:
            ed.after_idle(lambda r=keep_row, c=keep_col: (ed._scroll_to_row(r), setattr(ed, 'selected_cell', (r, c)) if c else None))
        low_count = sum(1 for u in ed.app_state.alignments if self._row_has_low_similarity(u))
        self.log(f'Similarity recomputed for {len(ed.app_state.alignments)} rows. Low-similarity rows marked: {low_count}.')

    def check_low_similarity_rows(self):
        ed = self._active_alignment_editor()
        if not ed or not ed.app_state.alignments:
            messagebox.showwarning(self.t('alignment_title'), self.t('export_no_rows')); return
        ed._sync_all_widgets()
        changed = self._normalize_similarity_status(ed.app_state.alignments)
        self._sync_group_editor(ed)
        low_count = sum(1 for u in ed.app_state.alignments if self._row_has_low_similarity(u))
        ed.refresh(sync_widgets=False); self.notebook.select(ed)
        messagebox.showinfo(self.t('check_low_similarity_rows'), self.t('low_similarity_marked', count=low_count, changed=changed))
        self.log(self.t('low_similarity_marked', count=low_count, changed=changed))

    def _llm_check_worker(self, rows_data: List[dict], source_col: str, target_cols: List[str], group_id: str, progress=None, cancel_event=None):
        """Run LLM-only alignment validation for the active editor.

        Round 17 intentionally removes the earlier Transformer-similarity
        recomputation and deterministic low-similarity precheck from LLM
        validation.  The LLM now checks segmentation, minimal alignment unit,
        row order and source-target correspondence from the current editor
        text and returns executable structural suggestions plus reasons.
        """
        s = self.state_data.settings
        client = OpenAILLMClient(
            s.get('openai_api_key',''),
            s.get('openai_model','gpt-5.4-mini'),
            float(s.get('llm_temperature',0)),
            int(s.get('llm_timeout',90)),
            int(s.get('llm_max_tokens',3000)),
            strict_json=bool(s.get('strict_json_mode', True)),
            retry_times=int(s.get('llm_retry_times', 1) or 1),
        )
        rows = [AlignmentUnit.from_dict(x) for x in rows_data]
        if progress:
            progress(self.t('llm_validating_editor'), 0.05)
        if cancel_event is not None and cancel_event.is_set():
            return ('suggestions', [], group_id, [x.to_dict() for x in rows])
        suggestion_lang = s.get('llm_suggestion_language') or s.get('gui_language', 'zh_sim')
        if suggestion_lang == 'auto':
            suggestion_lang = s.get('gui_language', 'zh_sim')
        suggestions = llm_check_rows(
            rows, client, source_col=source_col, target_cols=target_cols,
            batch_size=int(s.get('llm_batch_size', 40) or 40),
            min_confidence=float(s.get('llm_min_confidence', 0.75) or 0.75),
            progress=lambda msg, val: progress(msg, 0.05 + 0.90 * float(val or 0.0)) if progress else None,
            cancel_event=cancel_event,
            global_context=True,
            suggestion_language=suggestion_lang,
        )
        if cancel_event is not None and cancel_event.is_set():
            return ('suggestions', [], group_id, [x.to_dict() for x in rows])
        for sug in suggestions:
            if not sug.group_id:
                sug.group_id = group_id
        if progress:
            progress(self.t('llm_validation_completed'), 1.0)
        return ('suggestions', [x.to_dict() for x in suggestions], group_id, [x.to_dict() for x in rows])

    def llm_validate_current_editor(self):
        ed = self._active_alignment_editor()
        if not ed or not ed.app_state.alignments:
            messagebox.showwarning(self.t('llm_check_title'), self.t('export_no_rows')); return
        if not self.state_data.settings.get('openai_api_key'):
            self.open_settings()
            if not self.state_data.settings.get('openai_api_key'):
                messagebox.showwarning(self.t('llm_check_title'), self.t('set_openai_key_first')); return
        ed._sync_all_widgets()
        group_id = getattr(ed.app_state, 'group_id', '') or self._current_group_id()
        source_col = ed._source_column()
        target_cols = ed._target_columns()
        rows_data = [u.to_dict() for u in ed.app_state.alignments]
        # Start a fresh validation pass for this editor: clear old suggestions once,
        # then append every batch/result from the current task.
        self.state_data.llm_suggestions[:] = [x for x in self.state_data.llm_suggestions if x.get('group_id') != group_id]
        ed.app_state.llm_suggestions = self.state_data.llm_suggestions
        ed.refresh_suggestions()
        self._start_task(lambda progress=None, cancel_event=None: self._llm_check_worker(rows_data, source_col, target_cols, group_id, progress, cancel_event), on_done=lambda result, ed=ed: self._on_suggestions_done(result, ed))

    def llm_check_current_row(self):
        # Round 14: legacy shortcut now validates the entire current editor, not only the selected row.
        return self.llm_validate_current_editor()

    def llm_check_low_rows(self):
        return self.llm_validate_current_editor()

    def _on_suggestions_done(self, result, ed=None):
        if not result:
            return
        suggestions = []
        group_id = ''
        updated_rows = None
        if isinstance(result, tuple):
            if len(result) >= 2:
                suggestions = result[1] or []
            if len(result) >= 3:
                group_id = result[2] or ''
            if len(result) >= 4:
                updated_rows = result[3]
        else:
            suggestions = result or []
        group_id = group_id or (getattr(ed.app_state, 'group_id', '') if ed else self._current_group_id())
        if ed is not None and updated_rows:
            try:
                ed.app_state.alignments = [AlignmentUnit.from_dict(x) for x in updated_rows]
            except Exception:
                pass
        for s in suggestions:
            s.setdefault('group_id', group_id)
        # Round 16: suggestions from all LLM batches must accumulate.  Old
        # suggestions are cleared once when validation starts, not here; this
        # also makes the callback safe if future workers stream partial batches.
        existing = {
            (str(x.get('anchor_uid') or ''), int(x.get('row_id') or 0), str(x.get('column_key') or ''), str(x.get('issue_type') or ''), str(x.get('suggested_operation') or ''), str(x.get('problem') or ''))
            for x in self.state_data.llm_suggestions
            if x.get('group_id') == group_id
        }
        for s in suggestions:
            key = (str(s.get('anchor_uid') or ''), int(s.get('row_id') or 0), str(s.get('column_key') or ''), str(s.get('issue_type') or ''), str(s.get('suggested_operation') or ''), str(s.get('problem') or ''))
            if key not in existing:
                self.state_data.llm_suggestions.append(s)
                existing.add(key)
        if ed is not None:
            ed.app_state.llm_suggestions = self.state_data.llm_suggestions
        byrow = {}
        for s in suggestions:
            byrow.setdefault(int(s.get('row_id') or 0), []).append(s)
        target_rows = ed.app_state.alignments if ed else [u for u in self.state_data.alignments if u.group_id == group_id]
        for u in target_rows:
            if u.row_id in byrow:
                u.status = 'llm_suggested'
                u.confirmed = False
                u.llm_suggestion = '; '.join(x.get('problem','') for x in byrow[u.row_id])
        visible_count = len([x for x in self.state_data.llm_suggestions if not group_id or x.get('group_id') == group_id])
        added_count = 0
        if ed:
            self._sync_group_editor(ed)
            ed.refresh(sync_widgets=False)
            ed.refresh_suggestions()
            self.notebook.select(ed)
            visible_count = len(ed._current_group_suggestion_indices()) if hasattr(ed, '_current_group_suggestion_indices') else visible_count
        self._mark_dirty()
        # Count the suggestions actually visible for this file group, rather than
        # only the raw suggestions returned by the last worker callback.
        self.log(self.t('llm_suggestions_received', count=visible_count))

    def _start_task(self, func, on_done):
        self.current_done_callback = on_done
        self._task_cancelled = False
        try:
            ed = self._active_alignment_editor()
            if ed:
                ed.set_busy(True)
            self.task_runner.run(func)
            self.status_var.set(self.t('task_started'))
            self.progress['value'] = 0
        except Exception as exc:
            ed = self._active_alignment_editor()
            if ed:
                ed.set_busy(False)
            messagebox.showerror(self.t('task_error'), str(exc))

    def cancel_all_tasks(self):
        self._task_cancelled = True
        self.current_done_callback = None
        try:
            self.task_runner.cancel()
        except Exception:
            pass
        # Replace the runner so the UI can start a new task immediately.
        # Python cannot safely kill a running thread, but late messages from the
        # old runner are no longer polled or applied.
        self.task_runner = TaskRunner()
        for ed in list(getattr(self, 'alignment_editors', {}).values()):
            try:
                ed.set_busy(False)
            except Exception:
                pass
        self.status_var.set(self.t('task_cancelled'))
        self.progress['value'] = 0
        self.log(self.t('task_cancelled'))

    def _poll_tasks(self):
        for msg in self.task_runner.poll():
            if msg.kind == 'progress':
                if not getattr(self, '_task_cancelled', False):
                    self.status_var.set(msg.message); self.progress['value'] = msg.progress
            elif msg.kind == 'done':
                for ed in list(getattr(self, 'alignment_editors', {}).values()):
                    try:
                        ed.set_busy(False)
                    except Exception:
                        pass
                if getattr(self, '_task_cancelled', False):
                    self.status_var.set(self.t('task_cancelled')); self.progress['value'] = 0
                    self.current_done_callback = None
                    continue
                self.status_var.set(self.t('ready')); self.progress['value'] = 1.0
                cb = getattr(self, 'current_done_callback', None)
                if cb:
                    try:
                        cb(msg.result)
                    except Exception as exc:
                        import traceback
                        tb = traceback.format_exc()
                        self.log(tb)
                        self.status_var.set(self.t('task_failed'))
                        messagebox.showerror(self.t('task_failed'), str(exc))
                self.current_done_callback = None
            elif msg.kind == 'error':
                for ed in list(getattr(self, 'alignment_editors', {}).values()):
                    try:
                        ed.set_busy(False)
                    except Exception:
                        pass
                if getattr(self, '_task_cancelled', False):
                    self.status_var.set(self.t('task_cancelled')); self.progress['value'] = 0
                    self.current_done_callback = None
                    continue
                self.status_var.set(self.t('task_failed')); self.log(msg.message); messagebox.showerror(self.t('task_failed'), msg.error)
                self.current_done_callback = None
            elif msg.kind == 'log':
                self.log(msg.message)
        self.after(200, self._poll_tasks)

    def toggle_log_panel(self):
        if not hasattr(self, 'log_panel'):
            return
        if getattr(self, '_log_panel_visible', True):
            self.log_panel.pack_forget()
            self._log_panel_visible = False
        else:
            self.log_panel.pack(fill='x', side='bottom')
            self._log_panel_visible = True
            try:
                self.log_panel.text.focus_set()
            except Exception:
                pass

    def reset_default_settings(self):
        if not messagebox.askyesno(self.t('reset_settings_title'), self.t('reset_settings_confirm')):
            return
        keep_created = self.state_data.settings.get('created_time') or now_str()
        self.state_data.settings.clear()
        self.state_data.settings.update(dict(DEFAULT_SETTINGS))
        self.state_data.settings['created_time'] = keep_created
        self.state_data.settings['model_root'] = str(resource_path('models'))
        self.state_data.settings['default_project_folder'] = str(resource_path())
        self._save_settings()
        self.i18n.set_lang(self.state_data.settings.get('gui_language', 'zh_sim'))
        self.t = self.i18n.t
        self._rebuild_interface()
        messagebox.showinfo(self.t('reset_settings_title'), self.t('reset_settings_done'))

    def open_settings(self):
        SettingsDialog(self, self.state_data.settings, self._update_settings)

    def _update_settings(self, settings):
        self.state_data.settings.update(settings)
        self._save_settings(); self._apply_theme(); self.log('Settings updated.')

    def open_model_manager(self):
        ModelManagerDialog(self, self.state_data.settings, self.log)

    def set_gui_language(self, lang):
        if lang == self.state_data.settings.get('gui_language'):
            return
        self.state_data.settings['gui_language'] = lang
        self._save_settings()
        self.i18n.set_lang(lang)
        self.t = self.i18n.t
        self._rebuild_interface()
        messagebox.showinfo(self.t('language_title'), self.t('language_set', lang=display_name(lang, lang, with_code=False)))

    def validate_project(self):
        problems = []
        if not self.state_data.files: problems.append('No imported files.')
        if any(not f.lang for f in self.state_data.files): problems.append('Some files have no language code.')
        if any('failed' in f.status for f in self.state_data.files): problems.append('Some files failed to read or segment.')
        groups = {}
        for f in self.state_data.files: groups.setdefault(f.group_id, set()).add(self._record_column_key(f))
        for gid, langs in groups.items():
            if len(langs) < 2: problems.append(f'{gid} has fewer than two languages.')
        messagebox.showinfo(self.t('validate_title'), '\n'.join(problems) if problems else self.t('validation_passed'))

    def show_statistics(self):
        stats = compute_statistics(self.state_data.files, self.state_data.segments_by_file, self.state_data.alignments, float(self.state_data.settings.get('min_similarity_threshold', 0.55)))
        top = tk.Toplevel(self); top.title(self.t('stats_title')); top.geometry('820x640')
        canvas = tk.Canvas(top, height=260, bg='white', highlightthickness=0)
        canvas.pack(fill='x', padx=10, pady=(10, 4))
        items = [
            (self.t('file_manager'), int(stats.get('file_count', 0))),
            (self.t('group'), int(stats.get('group_count', 0))),
            (self.t('sentence'), int(stats.get('sentence_count', 0))),
            (self.t('alignment_editor'), int(stats.get('alignment_unit_count', 0))),
            (self.t('check_low_similarity_rows'), int(stats.get('low_similarity_rows', 0))),
            (self.t('status_confirmed'), int(round(float(stats.get('confirmed_ratio', 0)) * max(int(stats.get('alignment_unit_count', 0)), 1)))),
        ]
        maxv = max([v for _, v in items] or [1]) or 1
        left, top_y, bar_h, gap = 150, 28, 24, 13
        canvas.create_text(12, 8, anchor='nw', text=self.t('stats_chart_title'), font=('Microsoft YaHei UI', 11, 'bold'), fill='#4A2C2A')
        for idx, (label, value) in enumerate(items):
            y = top_y + idx * (bar_h + gap)
            canvas.create_text(12, y + 3, anchor='nw', text=label, font=('Microsoft YaHei UI', 9), fill='#4A2C2A')
            w = int((canvas.winfo_reqwidth() - left - 80) * value / maxv)
            w = max(w, 3 if value else 0)
            canvas.create_rectangle(left, y, left + w, y + bar_h, fill='#D95C5C', outline='')
            canvas.create_text(left + w + 8, y + 3, anchor='nw', text=str(value), font=('Microsoft YaHei UI', 9), fill='#4A2C2A')
        txt = tk.Text(top, wrap='word', height=14)
        txt.pack(fill='both', expand=True, padx=10, pady=4)
        txt.insert('1.0', json.dumps(stats, ensure_ascii=False, indent=2))
        txt.configure(state='disabled')
        ttk.Button(top, text=self.t('export_excel'), command=lambda: self._export_stats(stats)).pack(pady=8)

    def _export_stats(self, stats):
        path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel','*.xlsx')])
        if not path: return
        try:
            from openpyxl import Workbook
            wb = Workbook(); ws = wb.active; ws.title = 'summary'
            ws.append(['metric', 'value'])
            for k, v in stats.items():
                if k != 'languages':
                    ws.append([k, json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v])
            ws2 = wb.create_sheet('languages')
            ws2.append(['language', 'files', 'chars', 'sentences'])
            for lang, vals in (stats.get('languages') or {}).items():
                ws2.append([lang, vals.get('files', 0), vals.get('chars', 0), vals.get('sentences', 0)])
            wb.save(path); messagebox.showinfo(self.t('stats_title'), self.t('exported_to', path=path))
        except Exception as exc: messagebox.showerror(self.t('export_failed'), str(exc))

    def export_log(self):
        src = resource_path('log','alignlens.log')
        dst = filedialog.asksaveasfilename(defaultextension='.log', filetypes=[('Log','*.log'),('Text','*.txt')])
        if dst and src.exists():
            Path(dst).write_text(src.read_text(encoding='utf-8', errors='replace'), encoding='utf-8')

    def clear_cache_hint(self):
        messagebox.showinfo(self.t('clear_cache_title'), self.t('clear_cache_message'))

    def open_readme(self):
        readme = resource_path('README.md')
        if readme.exists():
            try:
                from core.utils import open_path
                open_path(str(readme))
            except Exception:
                pass
        else:
            messagebox.showinfo(self.t('user_guide_title'), self.t('user_guide_message'))

    def on_close(self):
        if not self._confirm_save_if_needed():
            return
        self._save_settings()
        self.destroy()


def main():
    app = MainWindow()
    app.mainloop()
