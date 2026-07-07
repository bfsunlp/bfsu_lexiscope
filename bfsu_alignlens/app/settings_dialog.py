from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict

from core.hardware import available_device_options, get_hardware_info, format_hardware_message
from core.utils import resource_path
from core.language_registry import LANGUAGES, display_name
from core.segmentation_profiles import all_default_profiles, profiles_from_settings, SPACY_MODEL_BY_LANG, stanza_lang_for


class SettingsDialog(tk.Toplevel):
    def __init__(self, master, settings: Dict, on_save=None):
        super().__init__(master)
        self.t = getattr(master, 't', lambda key, **kwargs: key.format(**kwargs) if kwargs else key)
        self.title(self.t('settings'))
        self.geometry('980x720')
        self.minsize(900, 620)
        self.settings = dict(settings)
        self.on_save = on_save
        self.vars: Dict[str, tk.Variable] = {}
        self.transient(master)
        self.grab_set()
        self._build()

    def var(self, key, default='', kind='str'):
        value = self.settings.get(key, default)
        if kind == 'bool':
            v = tk.BooleanVar(value=bool(value))
        elif kind == 'int':
            v = tk.IntVar(value=int(value or 0))
        elif kind == 'float':
            v = tk.DoubleVar(value=float(value or 0))
        else:
            v = tk.StringVar(value=str(value))
        self.vars[key] = v
        return v

    def row(self, parent, label, key, default='', kind='str', widget='entry', values=None):
        fr = ttk.Frame(parent)
        fr.pack(fill='x', pady=3)
        ttk.Label(fr, text=label, width=38).pack(side='left')
        v = self.var(key, default, kind)
        if widget == 'combo':
            cb = ttk.Combobox(fr, textvariable=v, values=values or [], state='readonly')
            cb.pack(side='left', fill='x', expand=True)
        elif widget == 'check':
            ttk.Checkbutton(fr, variable=v).pack(side='left')
        else:
            ttk.Entry(fr, textvariable=v).pack(side='left', fill='x', expand=True)
        return v

    def _build(self):
        # Keep Save/Cancel visible on every tab, even on smaller screens.
        # Packing the bottom bar first with side='bottom' prevents the large
        # notebook tabs from pushing it out of the visible area.
        bottom = ttk.Frame(self)
        bottom.pack(side='bottom', fill='x', padx=10, pady=(0, 10))
        ttk.Button(bottom, text=self.t('cancel'), command=self.destroy).pack(side='right', padx=4)
        ttk.Button(bottom, text=self.t('save'), command=self._save).pack(side='right', padx=4)
        nb = ttk.Notebook(self)
        nb.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        model_options = [
            'sentence-transformers/LaBSE',
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            'sentence-transformers/distiluse-base-multilingual-cased-v2',
            'intfloat/multilingual-e5-small',
            'intfloat/multilingual-e5-base',
        ]
        tabs = {}
        tab_names = [
            ('General', self.t('settings_tab_general')),
            ('File Import', self.t('settings_tab_file_import')),
            ('Segmentation', self.t('settings_tab_segmentation')),
            ('Transformer Alignment', self.t('settings_tab_transformer')),
            ('Model Management', self.t('settings_tab_model_management')),
            ('GPU / Performance', self.t('settings_tab_performance')),
            ('LLM', self.t('settings_tab_llm')),
            ('Export', self.t('settings_tab_export')),
        ]
        for name, label in tab_names:
            tab = ttk.Frame(nb, padding=12)
            nb.add(tab, text=label)
            tabs[name] = tab

        self.row(tabs['General'], 'GUI language', 'gui_language', 'en', widget='combo', values=['en', 'zh_sim', 'zh_tra'])
        self.row(tabs['General'], 'Default project folder', 'default_project_folder', str(resource_path()))
        self.row(tabs['General'], 'Autosave interval minutes', 'autosave_interval', 0, 'int')
        self.row(tabs['General'], 'Theme', 'theme', 'default', widget='combo', values=['default', 'clam', 'vista', 'xpnative'])
        self.row(tabs['General'], 'Show similarity score', 'show_similarity', True, 'bool', widget='check')
        self.row(tabs['General'], self.t('sentence_similarity_threshold'), 'min_similarity_threshold', 0.55, 'float')
        self.row(tabs['General'], self.t('paragraph_similarity_threshold'), 'paragraph_min_similarity_threshold', 0.50, 'float')
        self.row(tabs['General'], self.t('editor_row_no_width'), 'editor_row_no_width', 64, 'int')
        self.row(tabs['General'], self.t('editor_similarity_width'), 'editor_similarity_width', 92, 'int')
        self.row(tabs['General'], self.t('editor_status_width'), 'editor_status_width', 150, 'int')

        self.row(tabs['File Import'], 'Text encoding', 'default_encoding', 'utf-8', widget='combo', values=['utf-8'])
        self.row(tabs['File Import'], 'Preserve paragraph breaks', 'preserve_paragraphs', True, 'bool', widget='check')
        self.row(tabs['File Import'], 'Remove excessive spaces', 'remove_excessive_spaces', True, 'bool', widget='check')
        self.row(tabs['File Import'], 'Duplicate file handling', 'duplicate_file_handling', 'skip', widget='combo', values=['skip', 'overwrite', 'duplicate'])
        self.row(tabs['File Import'], 'Auto sort after import', 'auto_sort_after_import', False, 'bool', widget='check')
        self.row(tabs['File Import'], 'Confirm before deleting files', 'confirm_delete', True, 'bool', widget='check')
        self.row(tabs['File Import'], 'Confirm before reordering files', 'confirm_reorder', True, 'bool', widget='check')

        self.row(tabs['Segmentation'], self.t('alignment_unit'), 'alignment_unit', 'sentence', widget='combo', values=['sentence', 'paragraph'])
        self.row(tabs['Segmentation'], self.t('segmentation_mode'), 'segmentation_mode', 'auto', widget='combo', values=['auto', 'punctuation', 'stanza', 'hanlp', 'spacy', 'line', 'paragraph', 'none'])
        self.row(tabs['Segmentation'], 'Segment-only/manual after segmentation', 'segment_only_mode', False, 'bool', widget='check')
        self.row(tabs['Segmentation'], 'Paragraph-aware segmentation', 'paragraph_aware', True, 'bool', widget='check')
        self.row(tabs['Segmentation'], 'Split by line break', 'split_by_line', False, 'bool', widget='check')
        self.row(tabs['Segmentation'], 'Split by paragraph', 'split_by_paragraph', False, 'bool', widget='check')
        self.row(tabs['Segmentation'], 'Max sentence length', 'max_sentence_length', 1000, 'int')
        self.row(tabs['Segmentation'], 'Minimum sentence length', 'min_sentence_length', 1, 'int')
        self.row(tabs['Segmentation'], self.t('fallback_segmenter'), 'fallback_segmenter', 'punctuation', widget='combo', values=['punctuation', 'line', 'none'])
        self.row(tabs['Segmentation'], self.t('segmentation_cache_enabled'), 'segmentation_cache_enabled', True, 'bool', widget='check')
        ttk.Button(tabs['Segmentation'], text=self.t('language_segmenter_profiles'), command=self._open_segmentation_profiles).pack(anchor='w', pady=8)

        self.row(tabs['Transformer Alignment'], self.t('transformer_model_strategy'), 'alignment_mode', 'fused', widget='combo', values=['primary', 'labse', 'minilm', 'fused', 'custom'])
        self.row(tabs['Transformer Alignment'], self.t('primary_transformer_model'), 'primary_transformer_model', model_options[0], widget='combo', values=model_options)
        self.row(tabs['Transformer Alignment'], self.t('use_secondary_transformer_model'), 'use_secondary_transformer_model', True, 'bool', widget='check')
        self.row(tabs['Transformer Alignment'], self.t('secondary_transformer_model'), 'secondary_transformer_model', 'intfloat/multilingual-e5-base', widget='combo', values=model_options)
        self.row(tabs['Transformer Alignment'], self.t('custom_embedding_model'), 'custom_embedding_model', '')
        self.row(tabs['Transformer Alignment'], self.t('dp_search_mode'), 'dp_search_mode', 'full', widget='combo', values=['auto', 'full', 'banded'])
        self.row(tabs['Transformer Alignment'], self.t('large_doc_threshold'), 'large_doc_threshold', 2000000, 'int')
        self.row(tabs['Transformer Alignment'], self.t('dp_band_size'), 'dp_band_size', 240, 'int')
        self.row(tabs['Transformer Alignment'], 'Batch size', 'batch_size', 32, 'int')
        self.row(tabs['Transformer Alignment'], 'Max window', 'max_window', 5, 'int')
        self.row(tabs['Transformer Alignment'], self.t('sentence_max_merge_units'), 'sentence_max_merge_units', 3, 'int')
        self.row(tabs['Transformer Alignment'], self.t('sentence_strict_fine_alignment'), 'sentence_strict_fine_alignment', True, 'bool', widget='check')
        self.row(tabs['Transformer Alignment'], self.t('sentence_allow_2_to_2'), 'sentence_allow_2_to_2', True, 'bool', widget='check')
        self.row(tabs['Transformer Alignment'], self.t('sentence_merge_penalty'), 'sentence_merge_penalty', 0.25, 'float')
        self.row(tabs['Transformer Alignment'], 'Skip penalty', 'skip_penalty', -0.30, 'float')
        self.row(tabs['Transformer Alignment'], 'Empty penalty', 'empty_penalty', -0.30, 'float')
        self.row(tabs['Transformer Alignment'], 'Low-similarity forced-match penalty', 'low_similarity_match_penalty', 0.25, 'float')
        self.row(tabs['Transformer Alignment'], 'Length penalty weight', 'length_penalty_weight', 0.02, 'float')
        self.row(tabs['Transformer Alignment'], 'Paragraph distance penalty', 'paragraph_distance_penalty', 0.04, 'float')
        self.row(tabs['Transformer Alignment'], 'High confidence threshold', 'high_confidence_threshold', 0.70, 'float')
        self.row(tabs['Transformer Alignment'], 'Residual matching', 'residual_matching', True, 'bool', widget='check')
        self.row(tabs['Transformer Alignment'], 'Allow cross paragraph', 'allow_cross_paragraph', True, 'bool', widget='check')

        self.row(tabs['Model Management'], 'Model root folder', 'model_root', str(resource_path('models')))
        self.row(tabs['Model Management'], 'Download models locally', 'download_model_to_local', True, 'bool', widget='check')
        self.row(tabs['Model Management'], 'Default embedding model', 'default_embedding_model', 'sentence-transformers/LaBSE')
        self.row(tabs['Model Management'], 'Default segmentation model', 'default_segmentation_model', 'punctuation')
        ttk.Button(tabs['Model Management'], text='Browse model folder', command=self._browse_model_root).pack(anchor='w', pady=8)

        self.row(tabs['GPU / Performance'], 'Device', 'device', 'auto', widget='combo', values=available_device_options())
        self.row(tabs['GPU / Performance'], self.t('use_segmentation_gpu'), 'use_segmentation_gpu', True, 'bool', widget='check')
        self.row(tabs['GPU / Performance'], self.t('segmentation_device'), 'segmentation_device', 'auto', widget='combo', values=available_device_options())
        self.row(tabs['GPU / Performance'], 'Use fp16', 'use_fp16', False, 'bool', widget='check')
        self.row(tabs['GPU / Performance'], self.t('dp_cpu_workers'), 'dp_cpu_workers', 0, 'int')
        self.row(tabs['GPU / Performance'], 'Clear GPU cache after alignment', 'clear_gpu_cache_after_alignment', True, 'bool', widget='check')
        ttk.Button(tabs['GPU / Performance'], text='Show hardware info', command=self._show_hw).pack(anchor='w', pady=4)
        ttk.Label(tabs['GPU / Performance'], text=self.t('cpu_auto_hint'), wraplength=650).pack(anchor='w', pady=10)

        self.row(tabs['LLM'], 'OpenAI API Key', 'openai_api_key', '')
        self.row(tabs['LLM'], 'Save key locally', 'save_api_key', False, 'bool', widget='check')
        self.row(tabs['LLM'], 'Default model', 'openai_model', 'gpt-5.4-mini')
        self.row(tabs['LLM'], self.t('llm_suggestion_language'), 'llm_suggestion_language', self.settings.get('gui_language', 'zh_sim'), widget='combo', values=['auto'] + [x['code'] for x in LANGUAGES])
        self.row(tabs['LLM'], 'Temperature', 'llm_temperature', 0.0, 'float')
        self.row(tabs['LLM'], 'Max tokens', 'llm_max_tokens', 3000, 'int')
        self.row(tabs['LLM'], 'LLM batch size', 'llm_batch_size', 40, 'int')
        self.row(tabs['LLM'], 'LLM minimum confidence', 'llm_min_confidence', 0.75, 'float')
        self.row(tabs['LLM'], 'Safe suggestion-only mode', 'llm_safe_mode', True, 'bool', widget='check')
        self.row(tabs['LLM'], 'Verify LLM alignment with Transformer similarity', 'llm_verify_with_transformer', True, 'bool', widget='check')
        self.row(tabs['LLM'], 'Auto-apply structural suggestions', 'llm_auto_apply_structural_suggestions', False, 'bool', widget='check')
        self.row(tabs['LLM'], 'Strict JSON mode', 'strict_json_mode', True, 'bool', widget='check')
        self.row(tabs['LLM'], 'Retry times', 'llm_retry_times', 1, 'int')
        self.row(tabs['LLM'], 'Timeout seconds', 'llm_timeout', 90, 'int')

        self.row(tabs['Export'], 'Default export format', 'default_export_format', 'xlsx', widget='combo', values=['xlsx', 'txt', 'tmx', 'xml', 'docx', 'json'])
        self.row(tabs['Export'], 'Default multi-set TXT output', 'default_multi_txt_output', True, 'bool', widget='check')
        self.row(tabs['Export'], 'Create subfolder for each text set', 'create_subfolder_for_each_set', True, 'bool', widget='check')
        self.row(tabs['Export'], 'Output one TXT per language', 'output_one_txt_per_language', True, 'bool', widget='check')
        self.row(tabs['Export'], 'Output line numbers', 'output_line_numbers', True, 'bool', widget='check')
        self.row(tabs['Export'], 'Missing cell placeholder', 'missing_cell_placeholder', '')
        self.row(tabs['Export'], 'Sentence merge separator', 'sentence_merge_separator', ' ')
        self.row(tabs['Export'], 'Include similarity', 'include_similarity', True, 'bool', widget='check')
        self.row(tabs['Export'], 'Include LLM suggestions', 'include_llm_suggestions', True, 'bool', widget='check')



    def _open_segmentation_profiles(self):
        # Make sure current in-dialog values are visible to the profile editor.
        profiles = profiles_from_settings(self.settings)
        top = tk.Toplevel(self)
        top.title(self.t('language_segmenter_profiles'))
        top.geometry('920x560')
        top.transient(self)
        cols = ('lang', 'sentence_engine', 'stanza_lang', 'spacy_model', 'fallback')
        tree = ttk.Treeview(top, columns=cols, show='headings', selectmode='browse')
        headers = {
            'lang': self.t('language'),
            'sentence_engine': self.t('sentence_segmenter'),
            'stanza_lang': 'Stanza',
            'spacy_model': 'spaCy',
            'fallback': self.t('fallback_segmenter'),
        }
        widths = {'lang': 180, 'sentence_engine': 130, 'stanza_lang': 120, 'spacy_model': 180, 'fallback': 130}
        for c in cols:
            tree.heading(c, text=headers[c])
            tree.column(c, width=widths[c], anchor='w')
        tree.pack(fill='both', expand=True, padx=8, pady=8)
        for entry in LANGUAGES:
            code = entry['code']
            prof = profiles.get(code) or all_default_profiles().get(code, {})
            tree.insert('', 'end', iid=code, values=(
                f"{display_name(code, self.settings.get('gui_language', 'zh_sim'), with_code=True)}",
                prof.get('sentence_engine', 'auto'),
                prof.get('stanza_lang') or stanza_lang_for(code),
                prof.get('spacy_model') or SPACY_MODEL_BY_LANG.get(code, ''),
                prof.get('fallback_engine', 'punctuation'),
            ))
        editor = ttk.LabelFrame(top, text=self.t('edit_selected_profile'), padding=8)
        editor.pack(fill='x', padx=8, pady=(0, 8))
        engine_var = tk.StringVar(value='auto')
        stanza_var = tk.StringVar(value='')
        spacy_var = tk.StringVar(value='')
        fallback_var = tk.StringVar(value='punctuation')
        ttk.Label(editor, text=self.t('sentence_segmenter')).grid(row=0, column=0, sticky='w')
        ttk.Combobox(editor, textvariable=engine_var, values=['auto','stanza','spacy','hanlp','punctuation','line','none'], state='readonly', width=16).grid(row=0, column=1, sticky='w', padx=4)
        ttk.Label(editor, text='Stanza').grid(row=0, column=2, sticky='w')
        ttk.Entry(editor, textvariable=stanza_var, width=18).grid(row=0, column=3, sticky='w', padx=4)
        ttk.Label(editor, text='spaCy').grid(row=0, column=4, sticky='w')
        ttk.Entry(editor, textvariable=spacy_var, width=24).grid(row=0, column=5, sticky='w', padx=4)
        ttk.Label(editor, text=self.t('fallback_segmenter')).grid(row=1, column=0, sticky='w', pady=4)
        ttk.Combobox(editor, textvariable=fallback_var, values=['punctuation','line','none'], state='readonly', width=16).grid(row=1, column=1, sticky='w', padx=4)
        def load_selected(_=None):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], 'values')
            engine_var.set(vals[1]); stanza_var.set(vals[2]); spacy_var.set(vals[3]); fallback_var.set(vals[4])
        tree.bind('<<TreeviewSelect>>', load_selected)
        def apply_profile():
            sel = tree.selection()
            if not sel:
                return
            code = sel[0]
            profiles.setdefault(code, {})
            profiles[code].update({
                'language': code,
                'sentence_engine': engine_var.get(),
                'stanza_lang': stanza_var.get().strip() or stanza_lang_for(code),
                'spacy_model': spacy_var.get().strip(),
                'fallback_engine': fallback_var.get(),
            })
            tree.item(code, values=(tree.item(code, 'values')[0], engine_var.get(), stanza_var.get(), spacy_var.get(), fallback_var.get()))
        def reset_defaults():
            profiles.clear(); profiles.update(all_default_profiles())
            for item in tree.get_children():
                tree.delete(item)
            for entry in LANGUAGES:
                code = entry['code']; prof = profiles.get(code, {})
                tree.insert('', 'end', iid=code, values=(f"{display_name(code, self.settings.get('gui_language', 'zh_sim'), with_code=True)}", prof.get('sentence_engine', 'auto'), prof.get('stanza_lang') or stanza_lang_for(code), prof.get('spacy_model') or SPACY_MODEL_BY_LANG.get(code, ''), prof.get('fallback_engine', 'punctuation')))
        bar = ttk.Frame(top); bar.pack(fill='x', padx=8, pady=(0,8))
        ttk.Button(bar, text=self.t('apply'), command=apply_profile).pack(side='left')
        ttk.Button(bar, text=self.t('reset_defaults'), command=reset_defaults).pack(side='left', padx=4)
        def save_and_close():
            apply_profile()
            self.settings['segmentation_profiles'] = profiles
            top.destroy()
        ttk.Button(bar, text=self.t('save'), command=save_and_close).pack(side='right', padx=4)
        ttk.Button(bar, text=self.t('cancel'), command=top.destroy).pack(side='right')
        if tree.get_children():
            first = tree.get_children()[0]
            tree.selection_set(first); load_selected()

    def _browse_model_root(self):
        path = filedialog.askdirectory(title='Select model root folder')
        if path and 'model_root' in self.vars:
            self.vars['model_root'].set(path)

    def _show_hw(self):
        info = get_hardware_info()
        messagebox.showinfo('Hardware Info', format_hardware_message(info) + '\n\n' + '\n'.join(f'{k}: {v}' for k, v in info.items()))

    def _save(self):
        for k, v in self.vars.items():
            self.settings[k] = v.get()
        # Avoid saving API key unless explicitly requested.
        if not self.settings.get('save_api_key'):
            self.settings['openai_api_key'] = ''
        if self.on_save:
            self.on_save(self.settings)
        self.destroy()
