from __future__ import annotations

import queue
import threading
import tkinter as tk
import uuid
from tkinter import messagebox, ttk

from .ai_client import AIClient, AISettings
from .i18n import I18n
from .models import RegexRule
from .ui_common import IconToplevel


class RegexLLMGeneratorDialog(IconToplevel):
    def __init__(
        self,
        master: tk.Misc,
        i18n: I18n,
        settings: AISettings,
        samples: list[tuple[str, str]],
    ) -> None:
        super().__init__(master)
        self.i18n = i18n
        self.settings = settings
        self.samples = samples
        self.result: RegexRule | None = None
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._cancelled = False
        self.source_var = tk.StringVar(value=i18n.t("regex_ai_no_sample"))
        self.title(i18n.t("regex_ai_generate"))
        self.geometry("700x500")
        self.minsize(600, 420)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        ttk.Label(root, text=self.i18n.t("regex_ai_requirement")).pack(anchor=tk.W)
        self.requirement = tk.Text(root, height=9, wrap=tk.WORD, padx=6, pady=6)
        self.requirement.pack(fill=tk.BOTH, expand=True, pady=(2, 10))

        ttk.Label(root, text=self.i18n.t("regex_ai_sample_file")).pack(anchor=tk.W)
        values = [self.i18n.t("regex_ai_no_sample")] + [label for label, _text in self.samples]
        ttk.Combobox(root, textvariable=self.source_var, values=values, state="readonly").pack(fill=tk.X, pady=(2, 8))
        ttk.Label(
            root,
            text=self.i18n.t("regex_ai_tip"),
            foreground="#4b6972",
            wraplength=650,
        ).pack(anchor=tk.W)

        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(12, 6))
        self.status = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.status).pack(anchor=tk.W)
        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X, pady=(10, 0))
        self.generate_button = ttk.Button(buttons, text=self.i18n.t("regex_ai_generate"), command=self._generate)
        self.generate_button.pack(side=tk.RIGHT)
        ttk.Button(buttons, text=self.i18n.t("cancel"), command=self._cancel).pack(side=tk.RIGHT, padx=6)

    def _sample_text(self) -> str:
        selected = self.source_var.get()
        for label, text in self.samples:
            if label == selected:
                return text
        return ""

    def _generate(self) -> None:
        requirement = self.requirement.get("1.0", "end-1c").strip()
        if not requirement:
            messagebox.showwarning(self.i18n.t("regex_ai_generate"), self.i18n.t("regex_ai_requirement_required"), parent=self)
            return
        if not self.settings.enabled or not self.settings.resolved_api_key():
            messagebox.showinfo(self.i18n.t("regex_ai_generate"), self.i18n.t("ai_disabled_message"), parent=self)
            return
        provider = "DeepSeek" if self.settings.provider == "deepseek" else "OpenAI"
        if self.settings.confirm_before_send and not messagebox.askyesno(
            self.i18n.t("regex_ai_generate"),
            self.i18n.t("regex_ai_send_confirm", provider=provider),
            parent=self,
        ):
            return
        self.generate_button.configure(state=tk.DISABLED)
        self.status.set(self.i18n.t("regex_ai_generating"))
        self.progress.start(10)
        sample = self._sample_text()

        def worker() -> None:
            proposal, warnings = AIClient(self.settings).generate_regex_rule(requirement, sample)
            self._queue.put(("result", (proposal, warnings)))

        threading.Thread(target=worker, daemon=True, name="clearlens-regex-generator").start()
        self.after(100, self._poll)

    def _poll(self) -> None:
        if self._cancelled or not self.winfo_exists():
            return
        try:
            _kind, payload = self._queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll)
            return
        self.progress.stop()
        self.generate_button.configure(state=tk.NORMAL)
        proposal, warnings = payload
        if proposal is None or warnings:
            messagebox.showerror(
                self.i18n.t("regex_ai_generate"),
                self.i18n.t("regex_ai_failed", error="; ".join(str(value) for value in warnings)),
                parent=self,
            )
            self.status.set("")
            return
        self.result = RegexRule(
            key=f"custom_{uuid.uuid4().hex[:12]}",
            name=proposal.name,
            pattern=proposal.pattern,
            replacement=proposal.replacement,
            flags=proposal.flags,
            enabled=True,
            description=proposal.description,
            category="custom",
            custom=True,
        )
        self.destroy()

    def _cancel(self) -> None:
        self._cancelled = True
        self.destroy()
