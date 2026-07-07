from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from core import model_manager as mm
from core.hardware import resolve_device
from core.utils import open_path, format_bytes


class ModelManagerDialog(tk.Toplevel):
    def __init__(self, master, settings: dict, log_callback=None):
        super().__init__(master)
        self.title('Model Manager')
        self.geometry('1060x620')
        self.settings = settings
        self.log_callback = log_callback or (lambda msg: None)
        self.q = queue.Queue()
        self.transient(master)
        self._build()
        self.refresh()
        self.after(200, self._poll)

    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill='x')
        ttk.Label(top, text='Model root:').pack(side='left')
        self.root_var = tk.StringVar(value=self.settings.get('model_root', 'models'))
        ttk.Entry(top, textvariable=self.root_var).pack(side='left', fill='x', expand=True, padx=6)
        ttk.Button(top, text='Browse', command=self._browse).pack(side='left')
        ttk.Button(top, text='Open Folder', command=lambda: open_path(self.root_var.get())).pack(side='left', padx=4)

        cols = ('name', 'type', 'exists', 'path', 'description')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', selectmode='browse')
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160 if c != 'description' else 240, anchor='w')
        self.tree.pack(fill='both', expand=True, padx=8, pady=6)

        bar = ttk.Frame(self, padding=8)
        bar.pack(fill='x')
        ttk.Button(bar, text='Refresh', command=self.refresh).pack(side='left')
        ttk.Button(bar, text='Download / Load Selected', command=self.download_selected).pack(side='left', padx=4)
        ttk.Button(bar, text='Delete Selected', command=self.delete_selected).pack(side='left', padx=4)
        ttk.Button(bar, text='Set as Default', command=self.set_default).pack(side='left', padx=4)
        ttk.Button(bar, text='Import Local Model', command=self.import_local).pack(side='left', padx=4)
        ttk.Button(bar, text='Test Selected', command=self.test_selected).pack(side='left', padx=4)
        ttk.Button(bar, text='Close', command=self.destroy).pack(side='right')

        self.status_var = tk.StringVar(value='Ready')
        self.pb = ttk.Progressbar(self, maximum=1.0)
        self.pb.pack(fill='x', padx=8, pady=(0, 4))
        ttk.Label(self, textvariable=self.status_var).pack(anchor='w', padx=8, pady=(0, 8))

    def _browse(self):
        p = filedialog.askdirectory()
        if p:
            self.root_var.set(p)
            self.settings['model_root'] = p
            self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in mm.list_status(self.root_var.get()):
            self.tree.insert('', 'end', values=(row['name'], row['type'], 'yes' if row['exists'] else 'no', row['path'], row['description']))
        self.status_var.set(f"Cache size: {format_bytes(mm.cache_size(self.root_var.get()))}")

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Model Manager', 'Please select a model first.')
            return None
        return self.tree.item(sel[0], 'values')

    def _run_bg(self, func, *args):
        def progress(msg, value=0.0):
            self.q.put(('progress', msg, value))
        def target():
            try:
                res = func(*args, progress=progress)
                self.q.put(('done', str(res), 1.0))
            except Exception as exc:
                self.q.put(('error', str(exc), 0.0))
        threading.Thread(target=target, daemon=True).start()

    def download_selected(self):
        row = self._selected()
        if not row: return
        name, typ = row[0], row[1]
        if typ == 'SentenceTransformer':
            device = resolve_device(self.settings.get('device', 'cpu'))
            self._run_bg(mm.download_sentence_model, name, self.root_var.get(), device)
        elif 'segmenter' in typ.lower():
            self._run_bg(mm.download_segmentation_model, name, self.root_var.get())
        else:
            messagebox.showinfo('Model Manager', 'This model type is not downloadable from this dialog.')

    def delete_selected(self):
        row = self._selected()
        if not row: return
        if not messagebox.askyesno('Delete model', f'Delete local model record for {row[0]}?'):
            return
        ok = mm.delete_sentence_model(row[0], self.root_var.get())
        self.log_callback(f'Delete model {row[0]}: {ok}')
        self.refresh()

    def set_default(self):
        row = self._selected()
        if not row: return
        if row[1] != 'SentenceTransformer':
            messagebox.showinfo('Default model', 'Only SentenceTransformer models can be set as the default alignment model.')
            return
        self.settings['default_embedding_model'] = row[0]
        self.settings['primary_transformer_model'] = row[0]
        self.settings['alignment_mode'] = 'primary'
        self.settings['use_secondary_transformer_model'] = False
        messagebox.showinfo('Default model', f'Set single-model Transformer alignment to: {row[0]}')

    def import_local(self):
        src = filedialog.askdirectory(title='Select local SentenceTransformer model folder')
        if not src: return
        name = simpledialog.askstring('Model Name', 'Name for this local model:', initialvalue=src.split('/')[-1])
        if not name: return
        try:
            dest = mm.import_local_model(src, name, self.root_var.get())
            messagebox.showinfo('Import', f'Imported to:\n{dest}')
            self.refresh()
        except Exception as exc:
            messagebox.showerror('Import failed', str(exc))

    def test_selected(self):
        row = self._selected()
        if not row: return
        if row[1] != 'SentenceTransformer':
            messagebox.showinfo('Test', 'Only SentenceTransformer quick test is implemented in this dialog. Use Download / Load Selected to validate segmenters.')
            return
        def test(name, root, device, progress=None):
            progress('Loading test model', 0.2)
            from core.embedding_models import EmbeddingModelManager
            mgr = EmbeddingModelManager(model_root=root, device=device, batch_size=2)
            emb = mgr.encode(['hello world', '你好世界'], name, 2)
            progress('Test encoding completed', 1.0)
            return f'Shape: {emb.shape}'
        self._run_bg(test, row[0], self.root_var.get(), resolve_device(self.settings.get('device', 'cpu')))

    def _poll(self):
        try:
            while True:
                kind, msg, val = self.q.get_nowait()
                self.status_var.set(msg)
                self.pb['value'] = val
                if kind == 'error':
                    messagebox.showerror('Model task failed', msg)
                if kind == 'done':
                    self.refresh()
        except queue.Empty:
            pass
        self.after(200, self._poll)
