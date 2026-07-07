from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# The ProofLens v116 code uses a restrained native ttk/clam style, Microsoft YaHei UI,
# compact button padding, light neutral work areas (#f6f6f6) and muted grey hints.
# AlignLens keeps the same visual grammar while using the ProofLens icon palette
# (deep blue + orange) only for accents.
PROOFLENS_COLORS = {
    'bg': '#F0F0F0',
    'panel': '#FFFFFF',
    'panel2': '#F6F6F6',
    'deep': '#1F4E79',
    'blue': '#1F4E79',
    'red': '#1F4E79',       # compatibility alias used by older code
    'red2': '#173B5C',      # compatibility alias used by older code
    'gold': '#FF9800',
    'gold2': '#FFD28A',
    'text': '#222222',
    'muted': '#666666',
    'line': '#D9D9D9',
    'low': '#FFE1E6',
    'empty': '#FFF8D6',
    'ok': '#EAF4E4',
}


def apply_prooflens_theme(root: tk.Misc):
    """Apply a neutral ProofLens-consistent ttk style."""
    c = PROOFLENS_COLORS
    try:
        root.configure(bg=c['bg'])
    except Exception:
        pass
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        pass
    default_font = ('Microsoft YaHei UI', 9)
    try:
        root.option_add('*Font', default_font)
    except Exception:
        pass
    style.configure('.', font=default_font, background=c['bg'], foreground=c['text'])
    style.configure('TFrame', background=c['bg'])
    style.configure('TLabelframe', background=c['bg'], bordercolor=c['line'], relief='groove')
    style.configure('TLabelframe.Label', background=c['bg'], foreground=c['text'], font=default_font)
    style.configure('TLabel', background=c['bg'], foreground=c['text'])
    style.configure('Header.TLabel', background=c['panel2'], foreground=c['text'], font=('Microsoft YaHei UI', 10, 'bold'), padding=(8, 4))
    style.configure('Gold.TLabel', background=c['bg'], foreground=c['deep'], font=('Microsoft YaHei UI', 10, 'bold'))
    style.configure('Muted.TLabel', background=c['bg'], foreground=c['muted'])
    style.configure('TButton', padding=(8, 4), background=c['panel2'], foreground=c['text'], bordercolor=c['line'])
    style.configure('Tool.TButton', padding=(6, 3), background=c['panel2'], foreground=c['text'], bordercolor=c['line'])
    style.configure('Accent.TButton', padding=(8, 4), background=c['deep'], foreground='white', bordercolor=c['deep'])
    style.map('TButton', background=[('active', '#EAEAEA'), ('pressed', '#DDDDDD')], foreground=[('disabled', '#999999')])
    style.map('Accent.TButton', background=[('active', '#173B5C'), ('pressed', '#102B43')], foreground=[('active', 'white'), ('pressed', 'white')])
    style.configure('Status.TLabel', anchor=tk.W, background=c['bg'], foreground=c['muted'])
    style.configure('TNotebook', background=c['bg'], borderwidth=0)
    style.configure('TNotebook.Tab', background=c['panel2'], foreground=c['text'], padding=(12, 5), bordercolor=c['line'])
    style.map('TNotebook.Tab', background=[('selected', c['panel']), ('active', '#EAEAEA')], foreground=[('selected', c['deep']), ('active', c['text'])])
    style.configure('Treeview', background=c['panel'], fieldbackground=c['panel'], foreground=c['text'], rowheight=26, bordercolor=c['line'])
    style.configure('Treeview.Heading', background=c['panel2'], foreground=c['text'], font=('Microsoft YaHei UI', 9, 'bold'), bordercolor=c['line'])
    style.map('Treeview', background=[('selected', c['deep'])], foreground=[('selected', 'white')])
    style.configure('TEntry', fieldbackground='white', foreground=c['text'], bordercolor=c['line'])
    style.configure('Horizontal.TProgressbar', troughcolor=c['panel2'], background=c['gold'])


def configure_text_widget(widget: tk.Text):
    c = PROOFLENS_COLORS
    widget.configure(
        bg=c['panel'], fg=c['text'], insertbackground=c['deep'],
        selectbackground=c['gold2'], selectforeground=c['text'],
        relief='solid', borderwidth=1, padx=6, pady=4,
        font=('Microsoft YaHei UI', 10), wrap='word'
    )
