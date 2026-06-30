# -*- coding: utf-8 -*-
"""Project management for .bfsu_prooflens files."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import APP_NAME, APP_VERSION, PROJECT_EXT, now_iso, read_json, write_json


class ProjectManager:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.project_path: str = ""
        self.data: dict[str, Any] = self.new_project_data(config=config or {}, project_name="Untitled")

    @staticmethod
    def new_project_data(config: dict[str, Any], project_name: str = "Untitled") -> dict[str, Any]:
        return {
            "software": APP_NAME,
            "version": APP_VERSION,
            "project_name": project_name,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "settings": config,
            "files": [],
        }

    def new_project(self, project_name: str = "Untitled", config: dict[str, Any] | None = None) -> dict[str, Any]:
        self.project_path = ""
        self.data = self.new_project_data(config or self.data.get("settings", {}), project_name=project_name)
        return self.data

    def open_project(self, path: str | Path) -> dict[str, Any]:
        p = Path(path)
        data = read_json(p, default=None)
        if not isinstance(data, dict):
            raise ValueError("项目文件不是有效 JSON。")
        data.setdefault("software", APP_NAME)
        data.setdefault("version", APP_VERSION)
        data.setdefault("files", [])
        data.setdefault("settings", {})
        self.project_path = str(p)
        self.data = data
        return self.data

    def save_project(self, path: str | Path | None = None) -> str:
        if path is not None:
            self.project_path = str(path)
        if not self.project_path:
            raise ValueError("未指定项目保存路径。")
        p = Path(self.project_path)
        if p.suffix.lower() != PROJECT_EXT:
            p = p.with_suffix(PROJECT_EXT)
            self.project_path = str(p)
        self.data["updated_at"] = now_iso()
        write_json(p, self.data)
        return str(p)

    def close_project(self) -> None:
        self.project_path = ""
        self.data = self.new_project_data(config=self.data.get("settings", {}), project_name="Untitled")

    def add_file(self, file_entry: dict[str, Any]) -> None:
        self.data.setdefault("files", []).append(file_entry)
        self.data["updated_at"] = now_iso()

    def find_file(self, file_id: str) -> dict[str, Any] | None:
        for item in self.data.get("files", []):
            if item.get("id") == file_id:
                return item
        return None

    def find_page(self, file_id: str, page_index: int) -> dict[str, Any] | None:
        f = self.find_file(file_id)
        if not f:
            return None
        pages = f.get("pages", [])
        if 0 <= page_index < len(pages):
            return pages[page_index]
        return None
