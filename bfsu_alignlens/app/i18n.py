from __future__ import annotations

from typing import Any, Dict

SUPPORTED_UI_LANGS = ("zh_sim", "zh_tra", "en")

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "BFSU AlignLens",
        "file": "File", "edit": "Edit", "alignment": "Alignment", "view": "View", "tools": "Tools", "help": "Help",
        "new_project": "New Project", "open_project": "Open Project", "save_project": "Save Project", "save_project_as": "Save Project As",
        "import_alignment_files": "Import Alignment Files...", "add_to_current_column": "Add to Current Column", "export": "Export", "exit": "Exit",
        "undo": "Undo", "redo": "Redo", "delete_selected_files": "Delete Selected Files", "delete_all_files": "Delete All Files",
        "move_file_up": "Move File Up", "move_file_down": "Move File Down", "move_file_top": "Move File to Top", "move_file_bottom": "Move File to Bottom",
        "merge": "Merge", "split": "Split", "mark_confirmed": "Mark as Confirmed", "mark_review": "Mark as Needs Review",
        "insert_blank_row": "Insert Blank Row", "move_row_up": "Move Row Up", "move_row_down": "Move Row Down", "move_cell_up": "Move Cell Up", "move_cell_down": "Move Cell Down", "merge_cell_up": "Merge Cell Up", "merge_cell_down": "Merge Cell Down", "edit_cell": "Edit Cell", "clear_cell": "Clear Cell",
        "segment_texts_only": "Segment Texts Only", "manual_alignment_mode": "Manual Alignment Mode", "run_transformer_alignment": "Run Transformer Alignment",
        "run_llm_alignment": "Run LLM Alignment", "realign_current_group": "Re-align Current Group", "check_low_similarity_rows": "Check Low Similarity Rows", "recompute_similarity": "Recompute Similarity", "prev_highlight": "Previous Highlight", "next_highlight": "Next Highlight",
        "alignment_parameters": "Alignment Parameters", "model_settings": "Model Settings", "file_manager": "File Manager", "alignment_editor": "Alignment Editor",
        "llm_suggestions": "LLM Suggestions", "log_panel": "Log Panel", "ui_language": "Interface Language", "model_manager": "Model Manager",
        "batch_alignment": "Batch Alignment", "align_current_group": "Align Current File Group", "segment_current_group": "Segment Current File Group", "validate_project": "Validate Project", "check_file_pairing": "Check File Pairing", "auto_sort_files": "Auto Sort Files",
        "statistics": "Statistics", "export_log": "Export Log", "clear_cache": "Clear Cache", "reset_default_settings": "Reset Default Settings", "reset_settings_title": "Reset Settings", "reset_settings_confirm": "Reset all user settings to software defaults? Current project data will not be deleted.", "reset_settings_done": "Default settings have been restored.", "about": "About",
        "project": "Project:", "save": "Save", "settings": "Settings", "cpu_light": "CPU Light", "cancel_task": "Cancel Task", "ready": "Ready",
        "discard_project_title": "New Project", "discard_project_message": "Discard current project state? Unsaved changes will be lost.",
        "open_project_failed": "Open project failed", "save_project_failed": "Save project failed",
        "segment_title": "Segment", "import_files_first": "Please import files first.", "alignment_title": "Alignment",
        "llm_alignment_title": "LLM Alignment", "set_openai_key_first": "Please set the OpenAI API Key in Settings > LLM first.",
        "llm_check_title": "LLM Check", "select_rows_first": "Please select one or more rows.", "no_low_similarity": "No low-similarity rows found.", "no_current_group": "Please select a file group first.", "current_group_aligned": "Current file group aligned: {group}",
        "task_error": "Task error", "task_failed": "Task failed", "cpu_light_title": "CPU Light Mode",
        "cpu_light_applied": "CPU light settings applied: MiniLM, max_window=2, batch_size=16, CPU, residual matching off.",
        "language_title": "Language", "language_set": "Interface language has been set to: {lang}", "validate_title": "Validate Project",
        "validation_passed": "Project validation passed.", "stats_title": "Statistics", "export_excel": "Export Excel", "exported_to": "Exported to {path}",
        "export_failed": "Export failed", "clear_cache_title": "Clear Cache", "clear_cache_message": "Large model cache is stored under the configured models folder. Use Tools > Model Manager to inspect or delete local model folders. HuggingFace shared cache fragments are not deleted automatically for safety.",
        "user_guide_title": "User Guide", "user_guide_message": "README.md is included in the source package.",

        "add": "Add", "delete": "Delete", "up": "Up", "down": "Down", "sort": "Sort", "preview": "Preview",
        "group": "Group", "filename": "Filename", "size": "Size", "status": "Status", "note": "Note", "path": "Path",
        "add_file_title": "Add Files", "column_not_ready": "This column is not ready. Please use File > Import Alignment Files... to create source/target columns first.",
        "add_to_column": "Add to {column}", "supported_files": "Supported files", "all_files": "All files",
        "delete_files_title": "Delete Files", "remove_files_confirm": "Remove {count} file(s) from the current project? The original files will not be deleted from disk.",
        "auto_sort_title": "Auto Sort", "auto_sort_confirm": "Auto sort will change file-level alignment order. Continue?",
        "modify_language_title": "Change Language", "modify_language_prompt": "Enter or select the language name, e.g. English, Deutsch, Simplified Chinese:",
        "note_title": "Note", "note_prompt": "Note:", "add_file_to_column": "Add Files to This Column", "delete_selected": "Delete Selected", "move_up": "Move Up", "move_down": "Move Down", "move_top": "Move to Top", "move_bottom": "Move to Bottom",
        "open_file": "Open File", "open_folder": "Open Containing Folder", "preview_text": "Preview Text", "change_language": "Change Language", "change_note": "Change Note", "reload": "Reload",
        "delete_all": "Delete All", "save_file_alignment": "Save File-level Alignment", "check_pairing": "Check Pairing", "segment": "Segment", "align": "Align",
        "file_manager_hint": "Use \"Import Alignment Files...\" to create source and target columns.", "select_folder": "Select Folder",
        "preview_title": "Preview - {filename}", "file_order_updated": "File-level alignment order updated.", "change_group_title": "Change Group ID",
        "pairing_ok_title": "Pairing Check", "pairing_ok": "All columns have the same number of files. No obvious file-level alignment issue was found.",
        "pairing_mismatch_title": "Pairing Check", "pairing_mismatch": "File counts are inconsistent across columns:\n\n{msg}",
        "file_count_status": "Files: {files} | Columns: {columns} | Selected: {selected} | Count mismatch: {mismatch}", "duplicate_files_skipped": "Skipped {count} duplicate file(s).", "yes": "Yes", "no": "No", "file_properties": "File Properties",

        "no_alignment_rows_hint": "Please import files and run segmentation or alignment first.", "row_no": "No.", "similarity": "Similarity", "edit_status": "Edit Status", "apply": "Apply", "ignore": "Ignore",
        "split_cell_title": "Split Cell", "split_cell_prompt": "Place the cursor where the cell should be split.", "split_cell_at_cursor": "Split Cell at Cursor", "split_cell_need_cursor": "Please place the cursor inside a cell, not at the beginning or end.", "delete_row_title": "Delete Row", "delete_row_confirm": "Delete row {row}?",
        "export_no_rows": "No alignment rows to export.", "excel": "Excel", "txt": "TXT", "word": "Word", "json": "JSON",
        "export_complete": "Export Complete", "exported": "Exported:\n{path}", "export_failed_title": "Export failed", "multi_txt": "Multi TXT", "multi_txt_failed": "Multi TXT failed",

        "wizard_title": "Import Alignment Files", "language": "Language:", "import_files": "Import Files", "import_folder": "Import Folder", "folder_recursive_title": "Import Folder", "folder_recursive_prompt": "Import supported text files in subfolders recursively?",
        "choose_mode": "Choose alignment mode", "alignment_mode": "Alignment Mode", "mode_1_to_1": "1-to-1 translation: one source text + one target text",
        "mode_1_to_n": "One source with multiple translations (1-to-N): one source text + multiple target versions", "mode_multilingual": "Multilingual parallel: one source text + target texts in multiple languages",
        "target_column_count": "Number of target/version columns:", "mode_hint": "After confirming the mode, this window will open one source pane and one pane for each target/version. Please complete file-level ordering here before importing into the main window.",
        "confirm_mode_import": "Confirm Mode and Start Import", "current_mode": "Current mode: {mode}", "back_mode": "Back to Mode Selection", "add_target_pane": "Add Target Pane", "remove_target_pane": "Remove Last Target Pane", "confirm_import_main": "Import into Main Window",
        "source": "Source", "target": "Target", "target_version": "Version {n}", "wizard_bottom_hint": "Tip: You can naturally sort or drag files in each pane. After importing, files with the same row number will automatically form set_001, set_002, and so on.",
        "mode_label_1_to_1": "1-to-1 Translation", "mode_label_1_to_n": "One Source with Multiple Translations", "mode_label_multilingual": "Multilingual Parallel",
        "incomplete_files_title": "Incomplete Files", "incomplete_files_message": "The following panes have no imported files:\n{items}",
        "inconsistent_file_counts_title": "Inconsistent File Counts", "inconsistent_file_counts_message": "File counts are inconsistent across panes; there may be missing or extra translations. Continue anyway?\n\n{msg}", "import_failed": "Import Failed",

        "about_title": "About BFSU AlignLens", "about_subtitle": "Multilingual Translation Alignment Tool", "about_line1": "An intelligent alignment tool for corpus-based translation studies, multilingual parallel corpus construction, and translation teaching.",
        "about_line2": "It supports 1-to-1 translation, one-source multiple translations, multilingual parallel text import, Transformer alignment, LLM direct alignment, and human revision.",
        "about_toolkit": "Part of the BFSU LexiScope Toolkit", "about_style": "Visual style aligned with BFSU ProofLens", "author": "Author: Dingjia LIU", "bfsu": "Beijing Foreign Studies University", "version": "Version: 1.2.2 Refined ProofLens-consistent Unified LLM Edition", "close": "Close",
    },
}

TRANSLATIONS["zh_sim"] = {
    "app_title": "BFSU AlignLens", "file": "文件", "edit": "编辑", "alignment": "对齐", "view": "视图", "tools": "工具", "help": "帮助",
    "new_project": "新建项目", "open_project": "打开项目", "save_project": "保存项目", "save_project_as": "项目另存为",
    "import_alignment_files": "导入对齐文件...", "add_to_current_column": "向当前栏添加文件", "export": "导出", "exit": "退出",
    "undo": "撤销", "redo": "重做", "delete_selected_files": "删除所选文件", "delete_all_files": "删除全部文件",
    "move_file_up": "文件上移", "move_file_down": "文件下移", "move_file_top": "移到顶部", "move_file_bottom": "移到底部",
    "merge": "合并", "split": "拆分", "mark_confirmed": "标记为已确认", "mark_review": "标记为待检查",
    "insert_blank_row": "插入空行", "move_row_up": "行上移", "move_row_down": "行下移", "move_cell_up": "单元格上移", "move_cell_down": "单元格下移", "merge_cell_up": "合并上方单元格", "merge_cell_down": "合并下方单元格", "edit_cell": "编辑单元格", "clear_cell": "清空单元格",
    "segment_texts_only": "仅自动分句", "manual_alignment_mode": "手动对齐模式", "run_transformer_alignment": "运行 Transformer 对齐",
    "run_llm_alignment": "运行 LLM 对齐", "realign_current_group": "重新对齐当前组", "check_low_similarity_rows": "检查低相似度行", "recompute_similarity": "重新计算相似度", "prev_highlight": "上一处高亮", "next_highlight": "下一处高亮",
    "alignment_parameters": "对齐参数", "model_settings": "模型设置", "file_manager": "文件管理", "alignment_editor": "对齐编辑器",
    "llm_suggestions": "LLM 建议", "log_panel": "日志面板", "ui_language": "界面语言", "model_manager": "模型管理",
    "batch_alignment": "批量对齐", "align_current_group": "对齐当前序号文件组", "segment_current_group": "分句当前序号文件组", "validate_project": "校验项目", "check_file_pairing": "检查文件配对", "auto_sort_files": "自动排序文件",
    "statistics": "统计", "export_log": "导出日志", "clear_cache": "清理缓存", "reset_default_settings": "重置默认设置", "reset_settings_title": "重置设置", "reset_settings_confirm": "是否将所有用户设置恢复为软件默认值？当前项目数据不会被删除。", "reset_settings_done": "已恢复默认设置。", "about": "关于",
    "project": "项目：", "save": "保存", "settings": "设置", "cpu_light": "CPU 轻量模式", "cancel_task": "取消任务", "ready": "就绪",
    "discard_project_title": "新建项目", "discard_project_message": "放弃当前项目状态？未保存的修改将会丢失。",
    "open_project_failed": "打开项目失败", "save_project_failed": "保存项目失败",
    "segment_title": "分句", "import_files_first": "请先导入文件。", "alignment_title": "对齐",
    "llm_alignment_title": "LLM 对齐", "set_openai_key_first": "请先在 设置 > LLM 中设置 OpenAI API Key。",
    "llm_check_title": "LLM 检查", "select_rows_first": "请先选择一行或多行。", "no_low_similarity": "没有发现低相似度行。", "no_current_group": "请先选择一个文件组。", "current_group_aligned": "当前文件组已对齐：{group}",
    "task_error": "任务错误", "task_failed": "任务失败", "cpu_light_title": "CPU 轻量模式",
    "cpu_light_applied": "已应用 CPU 轻量设置：MiniLM、max_window=2、batch_size=16、CPU、关闭残留匹配。",
    "language_title": "语言", "language_set": "界面语言已设置为：{lang}", "validate_title": "校验项目",
    "validation_passed": "项目校验通过。", "stats_title": "统计", "export_excel": "导出 Excel", "exported_to": "已导出到 {path}",
    "export_failed": "导出失败", "clear_cache_title": "清理缓存", "clear_cache_message": "大型模型缓存位于设置的 models 文件夹中。可使用 工具 > 模型管理 查看或删除本地模型文件夹。为保证安全，HuggingFace 共享缓存片段不会自动删除。",
    "user_guide_title": "用户指南", "user_guide_message": "源码包中已包含 README.md。",

    "add": "添加", "delete": "删除", "up": "上移", "down": "下移", "sort": "排序", "preview": "预览",
    "group": "组", "filename": "文件名", "size": "大小", "status": "状态", "note": "备注", "path": "路径",
    "add_file_title": "添加文件", "column_not_ready": "本栏还没有栏位信息，请先通过“文件 > 导入对齐文件...”创建源语/译语栏。",
    "add_to_column": "添加到 {column}", "supported_files": "支持的文件", "all_files": "所有文件",
    "delete_files_title": "删除文件", "remove_files_confirm": "从当前项目移除 {count} 个文件？原始文件不会从硬盘删除。",
    "auto_sort_title": "自动排序", "auto_sort_confirm": "自动排序会改变文件级对齐顺序。继续吗？",
    "modify_language_title": "修改语种", "modify_language_prompt": "请输入或选择语种原名（如 English、Deutsch、简体中文）：",
    "note_title": "备注", "note_prompt": "备注：", "add_file_to_column": "添加文件到本栏", "delete_selected": "删除所选", "move_up": "上移", "move_down": "下移", "move_top": "置顶", "move_bottom": "置底",
    "open_file": "打开文件", "open_folder": "打开所在文件夹", "preview_text": "预览文本", "change_language": "修改语种", "change_note": "修改备注", "reload": "重新读取",
    "delete_all": "删除全部", "save_file_alignment": "保存文件级对齐", "check_pairing": "检查配对", "segment": "分句", "align": "对齐",
    "file_manager_hint": "请通过“导入对齐文件...”创建源语和译语栏。", "select_folder": "选择文件夹",
    "preview_title": "预览 - {filename}", "file_order_updated": "文件级对齐顺序已更新。", "change_group_title": "修改组号",
    "pairing_ok_title": "配对检查", "pairing_ok": "各栏文件数量一致，文件级对齐没有明显问题。",
    "pairing_mismatch_title": "配对检查", "pairing_mismatch": "各栏文件数量不一致：\n\n{msg}",
    "file_count_status": "文件数: {files} | 栏数: {columns} | 已选: {selected} | 文件数量不齐: {mismatch}", "duplicate_files_skipped": "已自动略过 {count} 个重复文件。", "yes": "是", "no": "否", "file_properties": "文件属性",

    "no_alignment_rows_hint": "请先导入文件并执行分句或对齐。", "row_no": "行号", "similarity": "相似度", "edit_status": "编辑状态", "apply": "应用", "ignore": "忽略",
    "split_cell_title": "拆分单元格", "split_cell_prompt": "请将光标放在需要拆分的位置。", "split_cell_at_cursor": "按光标拆分单元格", "split_cell_need_cursor": "请将光标放在单元格中间位置，不能在开头或结尾。", "delete_row_title": "删除行", "delete_row_confirm": "删除第 {row} 行？",
    "export_no_rows": "没有可导出的对齐行。", "excel": "Excel", "txt": "TXT", "word": "Word", "json": "JSON",
    "export_complete": "导出完成", "exported": "已导出：\n{path}", "export_failed_title": "导出失败", "multi_txt": "多套 TXT", "multi_txt_failed": "多套 TXT 导出失败",

    "wizard_title": "导入对齐文件", "language": "语种：", "import_files": "导入文件", "import_folder": "导入文件夹", "folder_recursive_title": "导入文件夹", "folder_recursive_prompt": "是否递归导入子文件夹中的文本文件？",
    "choose_mode": "请选择对齐模式", "alignment_mode": "对齐模式", "mode_1_to_1": "1 对 1 翻译：一个源语文本 + 一个译语文本",
    "mode_1_to_n": "一语多译（1 对 N）：一个源语文本 + 多个译本", "mode_multilingual": "多语平行：一个源语文本 + 多个不同语种译文",
    "target_column_count": "译语/译本栏数量：", "mode_hint": "确认模式后，会在同一窗口中水平打开“源语”和各个“译语/译本”的文件列表子窗口。请先在这里完成文件级对齐排序，再导入到主界面。",
    "confirm_mode_import": "确认模式并开始导入", "current_mode": "当前模式：{mode}", "back_mode": "返回重选模式", "add_target_pane": "增加译本栏", "remove_target_pane": "删除最后译本栏", "confirm_import_main": "确认导入到主窗口",
    "source": "源语", "target": "译语", "target_version": "译本 {n}", "wizard_bottom_hint": "提示：每一栏内可先自然排序，也可拖动文件调整顺序。确认导入后，同一行序号会自动组成 set_001、set_002…… 的文件级对齐组。",
    "mode_label_1_to_1": "1 对 1 翻译", "mode_label_1_to_n": "一语多译（1 对 N）", "mode_label_multilingual": "多语平行",
    "incomplete_files_title": "文件不完整", "incomplete_files_message": "以下栏还没有导入文件：\n{items}",
    "inconsistent_file_counts_title": "文件数量不一致", "inconsistent_file_counts_message": "各栏文件数量不一致，可能存在缺译或多译。仍然继续导入吗？\n\n{msg}", "import_failed": "导入失败",

    "about_title": "关于 BFSU AlignLens", "about_subtitle": "多语种翻译对齐工具", "about_line1": "面向语料库翻译学、多语平行语料库建设与翻译教学的智能对齐工具。",
    "about_line2": "支持 1 对 1 翻译、一语多译、多语平行文本导入、Transformer 对齐、LLM 直接对齐与人工校对。",
    "about_toolkit": "BFSU LexiScope 工具箱组件", "about_style": "界面风格与 BFSU ProofLens 保持一致", "author": "作者：Dingjia LIU / 刘鼎甲", "bfsu": "北京外国语大学", "version": "版本：1.2.2 ProofLens 一致风格统一 LLM 精修版", "close": "关闭",
}
TRANSLATIONS["zh_tra"] = TRANSLATIONS["zh_sim"].copy()
TRANSLATIONS["zh_tra"].update({
    "duplicate_files_skipped": "已自動略過 {count} 個重複文件。",
    "reset_default_settings": "重置預設設定", "reset_settings_title": "重置設定", "reset_settings_confirm": "是否將所有使用者設定恢復為軟體預設值？當前專案資料不會被刪除。", "reset_settings_done": "已恢復預設設定。",
    "align_current_group": "對齊當前序號文件組", "segment_current_group": "分句當前序號文件組", "no_current_group": "請先選擇一個文件組。", "current_group_aligned": "當前文件組已對齊：{group}",
    "split_cell_at_cursor": "按游標拆分單元格", "split_cell_need_cursor": "請將游標放在單元格中間位置，不能在開頭或結尾。", "recompute_similarity": "重新計算相似度", "prev_highlight": "上一處高亮", "next_highlight": "下一處高亮",
    "about_line1": "面向語料庫翻譯學、多語平行語料庫建設與翻譯教學的智能對齊工具。",
    "about_line2": "支持 1 對 1 翻譯、一語多譯、多語平行文本導入、Transformer 對齊、LLM 直接對齊與人工校對。",
    "close": "關閉",
    "language_set": "介面語言已設定為：{lang}",
})


TRANSLATIONS['en'].update({
    'segmentation_manual_table_created': 'Segmentation-only manual alignment table created.',
    'cancel': 'Cancel',
    'paragraph': 'Paragraph', 'sentence': 'Sentence',
    'paragraph_alignment': 'Run Paragraph Alignment',
    'sentence_alignment': 'Run Sentence Alignment',
    'open_current_group_editor': 'Open Current File Group in Editor',
    'current_group_opened': 'Opened current file group in editor: {group}',
    'manual_table_opened': 'Opened manual alignment table for {group}.',
    'no_existing_alignment_for_group': 'No existing alignment rows for {group}. Please segment or align this group first.',
    'transformer_alignment_completed': 'Transformer {level} alignment completed: {rows} rows. Rows needing review: {low}.',
    'position_info': 'Position',
    'severity': 'Severity', 'issue': 'Issue', 'operation': 'Operation', 'confidence': 'Conf.',
    'settings_tab_general': 'General', 'settings_tab_file_import': 'File Import', 'settings_tab_segmentation': 'Segmentation',
    'settings_tab_transformer': 'Transformer Alignment', 'settings_tab_model_management': 'Model Management',
    'settings_tab_performance': 'GPU / Performance', 'settings_tab_llm': 'LLM', 'settings_tab_export': 'Export',
    'editor_row_no_width': 'Editor row-number column width', 'editor_position_width': 'Editor position column width',
    'editor_similarity_width': 'Editor similarity column width', 'editor_status_width': 'Editor status column width',
    'alignment_unit': 'Default alignment unit', 'use_paragraph_alignment_for_sentence': 'Use paragraph alignment as anchors for sentence alignment',
    'transformer_model_strategy': 'Transformer model strategy',
    'primary_transformer_model': 'Primary Transformer model', 'secondary_transformer_model': 'Secondary Transformer model',
    'sentence_max_merge_units': 'Sentence alignment max merge units',
    'sentence_strict_fine_alignment': 'Fine sentence alignment mode',
    'sentence_allow_2_to_2': 'Allow 2:2 sentence merge',
    'sentence_merge_penalty': 'Sentence merge penalty',
    'use_secondary_transformer_model': 'Fuse secondary model', 'custom_embedding_model': 'Custom model',
    'dp_search_mode': 'DP search mode', 'large_doc_threshold': 'Large document threshold (source × target units)',
    'dp_band_size': 'Banded DP size', 'dp_cpu_workers': 'CPU math/DP thread hint (0=auto)',
    'include_position_info': 'Include sentence/paragraph position information in exports',
    'status_needs_review': 'Needs review', 'status_low_similarity': 'Low similarity', 'status_llm_low_confidence': 'LLM low confidence',
    'status_auto_high_confidence': 'High confidence', 'status_empty_or_residual': 'Empty/residual', 'status_source_residual': 'Source residual',
    'status_target_residual': 'Target residual', 'status_manual_unconfirmed': 'Manual/unconfirmed', 'status_manual_split': 'Manual split',
    'status_manual_blank': 'Manual blank', 'status_manual_cell_moved': 'Cell moved', 'status_manual_cell_merged': 'Cell merged',
    'status_manual_cell_clear': 'Cell cleared', 'status_manual_edited': 'Manual edited', 'status_confirmed': 'Confirmed',
    'status_llm_suggested': 'LLM suggested',
})

TRANSLATIONS['zh_sim'].update({
    'segmentation_manual_table_created': '已创建仅分句/分段的手动对齐表。',
    'cancel': '取消',
    'paragraph': '段落', 'sentence': '句子',
    'paragraph_alignment': '运行段落对齐',
    'sentence_alignment': '运行句子对齐',
    'open_current_group_editor': '打开当前序号文件组到编辑器',
    'current_group_opened': '已在编辑器中打开当前文件组：{group}',
    'manual_table_opened': '已为 {group} 打开手动对齐表。',
    'no_existing_alignment_for_group': '{group} 尚无已有对齐行，请先分句/分段或运行对齐。',
    'transformer_alignment_completed': 'Transformer {level}对齐完成：{rows} 行；需检查行：{low}。',
    'position_info': '位置信息',
    'severity': '严重度', 'issue': '问题', 'operation': '操作', 'confidence': '置信度',
    'settings_tab_general': '通用设置', 'settings_tab_file_import': '文件导入设置', 'settings_tab_segmentation': '分句/分段设置',
    'settings_tab_transformer': 'Transformer 对齐设置', 'settings_tab_model_management': '模型管理设置',
    'settings_tab_performance': 'GPU / 性能设置', 'settings_tab_llm': 'LLM 设置', 'settings_tab_export': '导出设置',
    'editor_row_no_width': '编辑器行号列宽', 'editor_position_width': '编辑器位置信息列宽',
    'editor_similarity_width': '编辑器相似度列宽', 'editor_status_width': '编辑器状态列宽',
    'alignment_unit': '默认对齐单位', 'use_paragraph_alignment_for_sentence': '句子对齐时使用段落对齐结果作为锚点',
    'transformer_model_strategy': 'Transformer 模型策略',
    'primary_transformer_model': '主 Transformer 模型', 'secondary_transformer_model': '辅助 Transformer 模型',
    'sentence_max_merge_units': '句对齐最大合并句数',
    'sentence_strict_fine_alignment': '精细句对齐模式',
    'sentence_allow_2_to_2': '允许 2:2 句子合并',
    'sentence_merge_penalty': '句子合并惩罚',
    'use_secondary_transformer_model': '启用双模型融合', 'custom_embedding_model': '自定义模型',
    'dp_search_mode': '动态规划搜索模式', 'large_doc_threshold': '大文件阈值（源语 × 目标单位数）',
    'dp_band_size': 'Banded DP 带宽', 'dp_cpu_workers': 'CPU 数学/DP 线程提示（0=自动）',
    'include_position_info': '导出时保留句子/段落位置信息',
    'status_needs_review': '待检查', 'status_low_similarity': '低相似度', 'status_llm_low_confidence': 'LLM 低置信度',
    'status_auto_high_confidence': '高置信度', 'status_empty_or_residual': '空缺/残留', 'status_source_residual': '源语残留',
    'status_target_residual': '译语残留', 'status_manual_unconfirmed': '手动未确认', 'status_manual_split': '手动拆分',
    'status_manual_blank': '手动空行', 'status_manual_cell_moved': '单元格移动', 'status_manual_cell_merged': '单元格合并',
    'status_manual_cell_clear': '单元格清空', 'status_manual_edited': '手动编辑', 'status_confirmed': '已确认',
    'status_llm_suggested': 'LLM 已建议',
})

TRANSLATIONS['zh_tra'].update({
    'segmentation_manual_table_created': '已建立僅分句/分段的手動對齊表。',
    'cancel': '取消',
    'paragraph': '段落', 'sentence': '句子',
    'paragraph_alignment': '運行段落對齊',
    'sentence_alignment': '運行句子對齊',
    'open_current_group_editor': '打開當前序號文件組到編輯器',
    'current_group_opened': '已在編輯器中打開當前文件組：{group}',
    'manual_table_opened': '已為 {group} 打開手動對齊表。',
    'no_existing_alignment_for_group': '{group} 尚無已有對齊行，請先分句/分段或運行對齊。',
    'transformer_alignment_completed': 'Transformer {level}對齊完成：{rows} 行；需檢查行：{low}。',
    'position_info': '位置信息',
    'severity': '嚴重度', 'issue': '問題', 'operation': '操作', 'confidence': '置信度',
    'settings_tab_general': '通用設定', 'settings_tab_file_import': '文件導入設定', 'settings_tab_segmentation': '分句/分段設定',
    'settings_tab_transformer': 'Transformer 對齊設定', 'settings_tab_model_management': '模型管理設定',
    'settings_tab_performance': 'GPU / 性能設定', 'settings_tab_llm': 'LLM 設定', 'settings_tab_export': '導出設定',
    'editor_row_no_width': '編輯器行號列寬', 'editor_position_width': '編輯器位置信息列寬',
    'editor_similarity_width': '編輯器相似度列寬', 'editor_status_width': '編輯器狀態列寬',
    'alignment_unit': '預設對齊單位', 'use_paragraph_alignment_for_sentence': '句子對齊時使用段落對齊結果作為錨點',
    'transformer_model_strategy': 'Transformer 模型策略',
    'primary_transformer_model': '主 Transformer 模型', 'secondary_transformer_model': '輔助 Transformer 模型',
    'sentence_max_merge_units': '句對齊最大合併句數',
    'sentence_strict_fine_alignment': '精細句對齊模式',
    'sentence_allow_2_to_2': '允許 2:2 句子合併',
    'sentence_merge_penalty': '句子合併懲罰',
    'use_secondary_transformer_model': '啟用雙模型融合', 'custom_embedding_model': '自訂模型',
    'dp_search_mode': '動態規劃搜尋模式', 'large_doc_threshold': '大文件閾值（源語 × 目標單位數）',
    'dp_band_size': 'Banded DP 帶寬', 'dp_cpu_workers': 'CPU 數學/DP 線程提示（0=自動）',
    'include_position_info': '導出時保留句子/段落位置信息',
    'status_needs_review': '待檢查', 'status_low_similarity': '低相似度', 'status_llm_low_confidence': 'LLM 低置信度',
    'status_auto_high_confidence': '高置信度', 'status_empty_or_residual': '空缺/殘留', 'status_source_residual': '源語殘留',
    'status_target_residual': '譯語殘留', 'status_manual_unconfirmed': '手動未確認', 'status_manual_split': '手動拆分',
    'status_manual_blank': '手動空行', 'status_manual_cell_moved': '單元格移動', 'status_manual_cell_merged': '單元格合併',
    'status_manual_cell_clear': '單元格清空', 'status_manual_edited': '手動編輯', 'status_confirmed': '已確認',
    'status_llm_suggested': 'LLM 已建議',
})

# Round 6 UI refinements
TRANSLATIONS['en'].update({
    'segment_paragraph': 'Segment paragraphs',
    'segment_sentence': 'Segment sentences',
    'segment_current_group': 'Segment',
    'align_current_group': 'Open Current File Group in Editor',
    'paragraph_alignment': 'Transformer paragraph alignment',
    'sentence_alignment': 'Transformer sentence alignment',
    'llm_paragraph_alignment': 'LLM paragraph alignment',
    'llm_sentence_alignment': 'LLM sentence alignment',
    'batch_paragraph_alignment': 'Batch paragraph alignment',
    'batch_sentence_alignment': 'Batch sentence alignment',
    'check_low_similarity_rows': 'Mark low-similarity rows',
    'low_similarity_marked': 'Low-similarity check completed: {count} row(s) highlighted; {changed} row(s) newly marked.',
    'stats_chart_title': 'Alignment statistics overview',
    'cpu_auto_hint': 'If CUDA is unavailable, AlignLens automatically falls back to CPU mode and writes a diagnostic message to the log panel.',
    'use_segmentation_gpu': 'Use GPU for segmentation models when available',
    'segmentation_device': 'Segmentation model device',
    'segmentation_gpu_enabled': 'Segmentation models will prefer GPU device {device}; they will fall back to CPU if the selected model cannot use GPU.',
    'segmentation_cpu_fallback': 'Segmentation models will use CPU mode. Reason: {reason}.',
    'editor_row_no_width': 'Editor row-number column width',
    'editor_similarity_width': 'Editor similarity column width',
    'editor_status_width': 'Editor status column width',
})
TRANSLATIONS['zh_sim'].update({
    'segment_paragraph': '分段',
    'segment_sentence': '分句',
    'segment_current_group': '分句',
    'align_current_group': '打开当前文件组',
    'paragraph_alignment': 'Transformer 段落对齐',
    'sentence_alignment': 'Transformer 句子对齐',
    'llm_paragraph_alignment': 'LLM 段落对齐',
    'llm_sentence_alignment': 'LLM 句子对齐',
    'batch_paragraph_alignment': '批量段落对齐',
    'batch_sentence_alignment': '批量句子对齐',
    'check_low_similarity_rows': '标记低相似度行',
    'low_similarity_marked': '低相似度检查完成：共高亮 {count} 行；新标记 {changed} 行。',
    'stats_chart_title': '对齐统计概览',
    'cpu_auto_hint': '如果当前电脑或环境不支持 CUDA/GPU，AlignLens 会自动使用 CPU 模式，并在日志面板中提示原因。',
    'use_segmentation_gpu': '可用时分句模型使用 GPU',
    'segmentation_device': '分句模型设备',
    'segmentation_gpu_enabled': '分句模型将优先使用 GPU 设备 {device}；如具体模型无法使用 GPU，将自动退回 CPU。',
    'segmentation_cpu_fallback': '分句模型将使用 CPU 模式。原因：{reason}。',
    'editor_row_no_width': '编辑器行号列宽',
    'editor_similarity_width': '编辑器相似度列宽',
    'editor_status_width': '编辑器状态列宽',
})
TRANSLATIONS['zh_tra'].update({
    'segment_paragraph': '分段',
    'segment_sentence': '分句',
    'segment_current_group': '分句',
    'align_current_group': '打開當前文件組',
    'paragraph_alignment': 'Transformer 段落對齊',
    'sentence_alignment': 'Transformer 句子對齊',
    'llm_paragraph_alignment': 'LLM 段落對齊',
    'llm_sentence_alignment': 'LLM 句子對齊',
    'batch_paragraph_alignment': '批量段落對齊',
    'batch_sentence_alignment': '批量句子對齊',
    'check_low_similarity_rows': '標記低相似度行',
    'low_similarity_marked': '低相似度檢查完成：共高亮 {count} 行；新標記 {changed} 行。',
    'stats_chart_title': '對齊統計概覽',
    'cpu_auto_hint': '如果當前電腦或環境不支持 CUDA/GPU，AlignLens 會自動使用 CPU 模式，並在日誌面板中提示原因。',
    'use_segmentation_gpu': '可用時分句模型使用 GPU',
    'segmentation_device': '分句模型設備',
    'segmentation_gpu_enabled': '分句模型將優先使用 GPU 設備 {device}；如具體模型無法使用 GPU，將自動退回 CPU。',
    'segmentation_cpu_fallback': '分句模型將使用 CPU 模式。原因：{reason}。',
    'editor_row_no_width': '編輯器行號列寬',
    'editor_similarity_width': '編輯器相似度列寬',
    'editor_status_width': '編輯器狀態列寬',
})

def normalize_lang(lang: str | None) -> str:
    lang = lang or "zh_sim"
    return lang if lang in TRANSLATIONS else "zh_sim"


class I18N:
    def __init__(self, lang: str = "zh_sim") -> None:
        self.lang = normalize_lang(lang)

    def set_lang(self, lang: str) -> None:
        self.lang = normalize_lang(lang)

    def t(self, key: str, **kwargs: Any) -> str:
        text = TRANSLATIONS.get(self.lang, {}).get(key)
        if text is None:
            text = TRANSLATIONS["en"].get(key, key)
        try:
            return text.format(**kwargs)
        except Exception:
            return text

# Round 7 refinements
TRANSLATIONS['en'].update({
    'manual_paragraph_alignment': 'Manual paragraph alignment',
    'manual_sentence_alignment': 'Manual sentence alignment',
    'recompute_current_similarity': 'Recompute current-row similarity',
    'current_row_similarity_recomputed': 'Similarity recomputed for row {row}.',
    'apply_current_suggestion': 'Apply current',
    'apply_all_suggestions': 'Apply all',
    'ignore_current_suggestion': 'Ignore current',
    'ignore_all_suggestions': 'Ignore all',
    'sentence_similarity_threshold': 'Sentence similarity threshold',
    'paragraph_similarity_threshold': 'Paragraph similarity threshold',
})
TRANSLATIONS['zh_sim'].update({
    'manual_paragraph_alignment': '手动段落对齐',
    'manual_sentence_alignment': '手动句子对齐',
    'recompute_current_similarity': '重算当前行相似度',
    'current_row_similarity_recomputed': '已重新计算第 {row} 行相似度。',
    'apply_current_suggestion': '应用当前',
    'apply_all_suggestions': '全部应用',
    'ignore_current_suggestion': '忽略当前',
    'ignore_all_suggestions': '全部忽略',
    'sentence_similarity_threshold': '句子相似度阈值',
    'paragraph_similarity_threshold': '段落相似度阈值',
})
TRANSLATIONS['zh_tra'].update({
    'manual_paragraph_alignment': '手動段落對齊',
    'manual_sentence_alignment': '手動句子對齊',
    'recompute_current_similarity': '重算當前行相似度',
    'current_row_similarity_recomputed': '已重新計算第 {row} 行相似度。',
    'apply_current_suggestion': '應用當前',
    'apply_all_suggestions': '全部應用',
    'ignore_current_suggestion': '忽略當前',
    'ignore_all_suggestions': '全部忽略',
    'sentence_similarity_threshold': '句子相似度閾值',
    'paragraph_similarity_threshold': '段落相似度閾值',
})

# Round 10: group-tab editor workflow and project-state labels
TRANSLATIONS['en'].update({
    'open_group_first': 'Please open a file group editor first.',
    'open_group': 'Open File Group',
    'close_group': 'Close File Group',
    'complete_alignment': 'Complete Alignment',
    'current_text_group': 'Current text group: {group}',
    'select_group_to_open': 'Select a file group to open:',
    'unsegmented_group_prompt': '{group} has no segmentation or alignment result yet. Choose what to do now:',
    'confirm_realign_completed': 'The following completed file group(s) will be overwritten by automatic alignment: {groups}. Continue?',
    'group_completed': 'File group completed: {group}',
    'status_imported': 'Imported',
    'status_unread': 'Not read',
    'status_read': 'Read',
    'status_segmented': 'Segmented',
    'status_segmented_cached': 'Segmented (cache)',
    'status_segmented_sentence': 'Sentence segmented',
    'status_segmented_paragraph': 'Paragraph segmented',
    'status_aligning': 'Aligning',
    'status_aligned_sentence': 'Sentence aligned',
    'status_aligned_paragraph': 'Paragraph aligned',
    'status_editing': 'Editing alignment',
    'status_completed': 'Completed',
})
TRANSLATIONS['zh_sim'].update({
    'open_group_first': '请先打开一个文件组的对齐编辑器。',
    'open_group': '打开文件组',
    'close_group': '关闭文件组',
    'complete_alignment': '完成对齐',
    'current_text_group': '当前文本组：{group}',
    'select_group_to_open': '请选择要打开的文件组：',
    'unsegmented_group_prompt': '{group} 还没有分句、分段或对齐结果。请选择下一步操作：',
    'confirm_realign_completed': '以下已完成文件组将被自动对齐结果覆盖：{groups}。是否继续？',
    'group_completed': '文件组已完成对齐：{group}',
    'status_imported': '已导入',
    'status_unread': '未读取',
    'status_read': '已读取',
    'status_segmented': '已分句',
    'status_segmented_cached': '已分句（缓存）',
    'status_segmented_sentence': '已分句',
    'status_segmented_paragraph': '已分段',
    'status_aligning': '正在对齐',
    'status_aligned_sentence': '句子已对齐',
    'status_aligned_paragraph': '段落已对齐',
    'status_editing': '对齐编辑中',
    'status_completed': '对齐已完成',
})
TRANSLATIONS['zh_tra'].update({
    'open_group_first': '請先打開一個文件組的對齊編輯器。',
    'open_group': '打開文件組',
    'close_group': '關閉文件組',
    'complete_alignment': '完成對齊',
    'current_text_group': '當前文本組：{group}',
    'select_group_to_open': '請選擇要打開的文件組：',
    'unsegmented_group_prompt': '{group} 還沒有分句、分段或對齊結果。請選擇下一步操作：',
    'confirm_realign_completed': '以下已完成文件組將被自動對齊結果覆蓋：{groups}。是否繼續？',
    'group_completed': '文件組已完成對齊：{group}',
    'status_imported': '已導入',
    'status_unread': '未讀取',
    'status_read': '已讀取',
    'status_segmented': '已分句',
    'status_segmented_cached': '已分句（快取）',
    'status_segmented_sentence': '已分句',
    'status_segmented_paragraph': '已分段',
    'status_aligning': '正在對齊',
    'status_aligned_sentence': '句子已對齊',
    'status_aligned_paragraph': '段落已對齊',
    'status_editing': '對齊編輯中',
    'status_completed': '對齊已完成',
})

# Round 11: batch workflows and clearer menu placement
TRANSLATIONS['en'].update({
    'batch_export': 'Batch Export...',
    'batch_export_intro': 'Export every file group that has been segmented or aligned. Each group can be written to its own file, or exported as line-aligned TXT files by language/version.',
    'batch_export_mode': 'Batch export mode',
    'batch_export_group_files': 'One output file for each file group',
    'batch_export_language_txt': 'Line-aligned TXT files by language/version',
    'batch_export_no_rows': 'No segmented or aligned file groups are available for batch export.',
    'batch_export_done': 'Batch export completed: {count} file(s) written to {folder}.',
    'export_format': 'Export format',
    'output_line_numbers': 'Include line numbers',
    'create_subfolder_for_each_set': 'Create a subfolder for each file group',
    'select_export_folder': 'Select export folder',
    'browse': 'Browse...',
    'batch_segment_paragraph': 'Batch segment paragraphs',
    'batch_segment_sentence': 'Batch segment sentences',
    'batch_transformer_paragraph_alignment': 'Batch Transformer paragraph alignment',
    'batch_transformer_sentence_alignment': 'Batch Transformer sentence alignment',
    'batch_llm_paragraph_alignment': 'Batch LLM paragraph alignment',
    'batch_llm_sentence_alignment': 'Batch LLM sentence alignment',
})
TRANSLATIONS['zh_sim'].update({
    'batch_export': '批量导出...',
    'batch_export_intro': '导出所有已经分句、分段或对齐过的文件组。可为每个文件组分别生成一个文件，也可按语言/译本输出按行对齐的 TXT 文件。',
    'batch_export_mode': '批量导出模式',
    'batch_export_group_files': '每个文件组单独导出一个结果文件',
    'batch_export_language_txt': '按语言/译本导出按行对齐的 TXT 文件',
    'batch_export_no_rows': '当前没有可批量导出的分句、分段或对齐文件组。',
    'batch_export_done': '批量导出完成：已向 {folder} 写入 {count} 个文件。',
    'export_format': '导出格式',
    'output_line_numbers': '保留行号',
    'create_subfolder_for_each_set': '每个文件组创建独立子文件夹',
    'select_export_folder': '选择导出文件夹',
    'browse': '浏览...',
    'batch_segment_paragraph': '批量分段',
    'batch_segment_sentence': '批量分句',
    'batch_transformer_paragraph_alignment': '批量 Transformer 段对齐',
    'batch_transformer_sentence_alignment': '批量 Transformer 句对齐',
    'batch_llm_paragraph_alignment': '批量 LLM 段对齐',
    'batch_llm_sentence_alignment': '批量 LLM 句对齐',
})
TRANSLATIONS['zh_tra'].update({
    'batch_export': '批量導出...',
    'batch_export_intro': '導出所有已經分句、分段或對齊過的文件組。可為每個文件組分別生成一個文件，也可按語言/譯本輸出按行對齊的 TXT 文件。',
    'batch_export_mode': '批量導出模式',
    'batch_export_group_files': '每個文件組單獨導出一個結果文件',
    'batch_export_language_txt': '按語言/譯本導出按行對齊的 TXT 文件',
    'batch_export_no_rows': '當前沒有可批量導出的分句、分段或對齊文件組。',
    'batch_export_done': '批量導出完成：已向 {folder} 寫入 {count} 個文件。',
    'export_format': '導出格式',
    'output_line_numbers': '保留行號',
    'create_subfolder_for_each_set': '每個文件組建立獨立子文件夾',
    'select_export_folder': '選擇導出文件夾',
    'browse': '瀏覽...',
    'batch_segment_paragraph': '批量分段',
    'batch_segment_sentence': '批量分句',
    'batch_transformer_paragraph_alignment': '批量 Transformer 段對齊',
    'batch_transformer_sentence_alignment': '批量 Transformer 句對齊',
    'batch_llm_paragraph_alignment': '批量 LLM 段對齊',
    'batch_llm_sentence_alignment': '批量 LLM 句對齊',
})

# Round 13: project-closing workflow, exit-save prompt, user-facing About, and LLM default cleanup
TRANSLATIONS['en'].update({
    'close_project': 'Close Project',
    'project_closed': 'Project closed.',
    'new_project_created': 'New project created.',
    'unsaved_project_title': 'Unsaved Project',
    'unsaved_project_message': 'The current project has unsaved changes. Do you want to save it before continuing?',
    'about_subtitle': 'Multilingual text segmentation, alignment, checking and export',
    'about_full': '''BFSU AlignLens is a desktop tool for building and checking multilingual parallel texts.

It is designed for users who need to align source texts with translations, compare multiple translations of the same source text, prepare research corpora, inspect sentence or paragraph correspondence, and export cleaner line-aligned data for later analysis.

Main workflow
• Import source and target files as numbered file groups.
• Segment texts by paragraph or sentence with language-specific segmentation settings.
• Run Transformer or LLM-assisted paragraph/sentence alignment.
• Review the result in a file-group editor, adjust rows and cells manually, recalculate similarity, and mark low-similarity rows.
• Mark a file group as completed after proofreading.
• Export one group, multiple groups, or language/version-specific TXT files with line alignment.

Useful features
• Supports 1-to-1 translation, one-source multiple translations, and multilingual parallel texts.
• Handles paragraph segmentation, sentence segmentation, conservative paragraph alignment, Transformer sentence alignment, LLM paragraph alignment and LLM sentence alignment.
• Uses language-specific segmenters where available and falls back to rule-based segmentation when needed.
• Supports GPU acceleration for Transformer alignment and supported segmentation models; CPU fallback is automatic.
• Stores all LLM prompts in the root Prompt.md file so advanced users can inspect and adjust prompt behaviour.
• Keeps file-group states in the project file so users can continue unfinished work later.

Recommended use
AlignLens is suitable for corpus-based translation studies, multilingual corpus construction, translation teaching, translated text comparison, bilingual data preparation, and research-oriented alignment revision. Automatic alignment and LLM suggestions should be treated as draft results and checked by the user before formal research, teaching, publication or corpus release.

Author
Dingjia LIU / 刘鼎甲
Beijing Foreign Studies University
Email: djliu@bfsu.edu.cn

Version
BFSU AlignLens v1.3 Round 21

Copyright © 2026 Dingjia LIU. All rights reserved.''',
})

TRANSLATIONS['zh_sim'].update({
    'close_project': '关闭项目',
    'project_closed': '项目已关闭。',
    'new_project_created': '已新建项目。',
    'unsaved_project_title': '项目尚未保存',
    'unsaved_project_message': '当前项目有未保存的修改。继续之前是否保存项目？',
    'about_subtitle': '多语文本分段、分句、对齐、检查与导出工具',
    'about_full': '''BFSU AlignLens 是一款面向多语平行文本建设与翻译对齐检查的桌面工具。

它适合需要处理源文本与译文对齐、一语多译比较、多语平行语料整理、句段对应检查和按行导出研究数据的用户。软件的目标不是替代人工判断，而是帮助用户更快完成导入、分段、分句、自动对齐、人工修订、质量检查和批量导出。

主要流程
• 按文件组导入源语和译语文本。
• 根据语种设置进行自然段分段或句子分句。
• 使用 Transformer 或 LLM 进行段落/句子对齐。
• 在文件组对齐编辑器中检查结果，手动调整行和单元格，重新计算相似度，并标记低相似度行。
• 校对完成后，将当前文件组标记为“完成对齐”。
• 可导出单个文件组、多个文件组，也可按语种/译本导出按行对应的 TXT 文件。

主要功能
• 支持 1 对 1 翻译、一语多译和多语平行文本。
• 支持分段、分句、保守段落对齐、Transformer 句子对齐、LLM 段落对齐和 LLM 句子对齐。
• 尽量根据语种调用相应分句器；模型不可用时自动退回规则分句。
• Transformer 对齐和支持 GPU 的分句模型可使用 GPU 加速；不支持 GPU 时自动使用 CPU。
• 软件根目录下的 Prompt.md 集中保存所有 LLM 提示词，便于用户查看和按需调整。
• 文件组状态会保存到项目文件中，便于用户分批继续处理大型语料。

适用场景
AlignLens 可用于语料库翻译学研究、多语平行语料库建设、翻译教学、译本比较、双语数据整理和研究型对齐校订。自动对齐和 LLM 建议均应视为辅助结果，正式用于研究、教学、出版或语料库发布前，仍需用户检查确认。

作者
Dingjia LIU / 刘鼎甲
北京外国语大学
邮箱：djliu@bfsu.edu.cn

版本
BFSU AlignLens v1.3 Round 21

Copyright © 2026 Dingjia LIU. All rights reserved.''',
})

TRANSLATIONS['zh_tra'].update({
    'close_project': '關閉專案',
    'project_closed': '專案已關閉。',
    'new_project_created': '已新建專案。',
    'unsaved_project_title': '專案尚未保存',
    'unsaved_project_message': '當前專案有未保存的修改。繼續之前是否保存專案？',
    'about_subtitle': '多語文本分段、分句、對齊、檢查與導出工具',
    'about_full': '''BFSU AlignLens 是一款面向多語平行文本建設與翻譯對齊檢查的桌面工具。

它適合需要處理源文本與譯文對齊、一語多譯比較、多語平行語料整理、句段對應檢查和按行導出研究數據的使用者。軟體的目標不是替代人工判斷，而是幫助使用者更快完成導入、分段、分句、自動對齊、人工修訂、質量檢查和批量導出。

主要流程
• 按文件組導入源語和譯語文本。
• 根據語種設定進行自然段分段或句子分句。
• 使用 Transformer 或 LLM 進行段落/句子對齊。
• 在文件組對齊編輯器中檢查結果，手動調整行和單元格，重新計算相似度，並標記低相似度行。
• 校對完成後，將當前文件組標記為「完成對齊」。
• 可導出單個文件組、多個文件組，也可按語種/譯本導出按行對應的 TXT 文件。

主要功能
• 支持 1 對 1 翻譯、一語多譯和多語平行文本。
• 支持分段、分句、保守段落對齊、Transformer 句子對齊、LLM 段落對齊和 LLM 句子對齊。
• 盡量根據語種調用相應分句器；模型不可用時自動退回規則分句。
• Transformer 對齊和支持 GPU 的分句模型可使用 GPU 加速；不支持 GPU 時自動使用 CPU。
• 軟體根目錄下的 Prompt.md 集中保存所有 LLM 提示詞，便於使用者查看和按需調整。
• 文件組狀態會保存到專案文件中，便於使用者分批繼續處理大型語料。

適用場景
AlignLens 可用於語料庫翻譯學研究、多語平行語料庫建設、翻譯教學、譯本比較、雙語數據整理和研究型對齊校訂。自動對齊和 LLM 建議均應視為輔助結果，正式用於研究、教學、出版或語料庫發布前，仍需使用者檢查確認。

作者
Dingjia LIU / 劉鼎甲
北京外國語大學
郵箱：djliu@bfsu.edu.cn

版本
BFSU AlignLens v1.3 Round 21

Copyright © 2026 Dingjia LIU. All rights reserved.''',
})

# Round 14: conservative LLM validation and batch sentence alignment scope
TRANSLATIONS['en'].update({
    'llm_validate_editor': 'Validate Current Editor with LLM',
    'llm_validating_editor': 'Validating current alignment editor with LLM',
    'llm_validation_completed': 'LLM validation completed',
    'llm_suggestions_received': 'LLM suggestions received: {count}',
    'confirm_apply_all_llm_suggestions': 'Apply all pending LLM suggestions for this file group? Structural row/cell operations may change the alignment table. Original source files will not be modified.',
    'batch_sentence_realign_choice': 'Batch sentence alignment: choose Yes to re-align all file groups, No to skip file groups that already have sentence alignment, or Cancel to stop.',
    'no_unaligned_groups': 'No unaligned file groups were found. Existing sentence-aligned groups were skipped.',
})
TRANSLATIONS['zh_sim'].update({
    'llm_validate_editor': 'LLM验证当前编辑器',
    'llm_validating_editor': '正在用 LLM 验证当前对齐编辑器',
    'llm_validation_completed': 'LLM 验证已完成',
    'llm_suggestions_received': '收到 LLM 建议：{count} 条',
    'confirm_apply_all_llm_suggestions': '是否应用当前文件组的全部 LLM 建议？这些结构性行/单元格操作可能改变对齐表，但不会修改原始源文件。',
    'batch_sentence_realign_choice': '批量句对齐：选择“是”将重新对齐全部文件组，选择“否”将略过已经句对齐的文件组，选择“取消”停止操作。',
    'no_unaligned_groups': '没有发现未句对齐的文件组；已句对齐的文件组已略过。',
})
TRANSLATIONS['zh_tra'].update({
    'llm_validate_editor': 'LLM 驗證當前編輯器',
    'llm_validating_editor': '正在用 LLM 驗證當前對齊編輯器',
    'llm_validation_completed': 'LLM 驗證已完成',
    'llm_suggestions_received': '收到 LLM 建議：{count} 條',
    'confirm_apply_all_llm_suggestions': '是否應用當前文件組的全部 LLM 建議？這些結構性行/單元格操作可能改變對齊表，但不會修改原始源文件。',
    'batch_sentence_realign_choice': '批量句對齊：選擇「是」將重新對齊全部文件組，選擇「否」將略過已經句對齊的文件組，選擇「取消」停止操作。',
    'no_unaligned_groups': '沒有發現未句對齊的文件組；已句對齊的文件組已略過。',
})

# Round 15 hotfix translations
TRANSLATIONS['en'].update({
    'undo_applied': 'Undo applied in the current alignment editor.',
    'redo_applied': 'Redo applied in the current alignment editor.',
    'task_started': 'Task started...',
    'task_cancelled': 'Task cancelled. Current results will be ignored if the worker returns later.',
})
TRANSLATIONS['zh_sim'].update({
    'undo_applied': '已在当前对齐编辑器中撤销。',
    'redo_applied': '已在当前对齐编辑器中重做。',
    'task_started': '任务已启动……',
    'task_cancelled': '任务已取消。后台任务稍后返回的结果将被忽略。',
})
TRANSLATIONS['zh_tra'].update({
    'undo_applied': '已在當前對齊編輯器中撤銷。',
    'redo_applied': '已在當前對齊編輯器中重做。',
    'task_started': '任務已啟動……',
    'task_cancelled': '任務已取消。後台任務稍後返回的結果將被忽略。',
})

# Round 25: fused Transformer defaults, configurable LLM suggestion language, and GPT-5.5 acknowledgement/disclaimer
TRANSLATIONS['en'].update({
    'llm_suggestion_language': 'LLM suggestion language',
    'about_full': '''BFSU AlignLens is a desktop tool for building and checking multilingual parallel texts.

It is designed for users who need to align source texts with translations, compare multiple translations of the same source text, prepare research corpora, inspect sentence or paragraph correspondence, and export cleaner line-aligned data for later analysis.

Main workflow
• Import source and target files as numbered file groups.
• Segment texts by paragraph or sentence with language-specific segmentation settings.
• Run Transformer or LLM-assisted paragraph/sentence alignment.
• Review the result in a file-group editor, adjust rows and cells manually, recalculate similarity, and mark low-similarity rows.
• Mark a file group as completed after proofreading.
• Export one group, multiple groups, or language/version-specific TXT files with line alignment.

Useful features
• Supports 1-to-1 translation, one-source multiple translations, and multilingual parallel texts.
• Uses the Round 25 default Transformer profile: fused LaBSE + multilingual-e5-base, full DP search, max sentence merge units = 3, high-confidence threshold = 0.70, and low-similarity forced-match penalty = 0.25.
• Allows the language of LLM review suggestions to be selected in Settings > LLM.
• Keeps gpt-5.4-mini as the default OpenAI model while allowing users to enter GPT-5.5 or other model names available to their own accounts.
• Stores all LLM prompts in the root Prompt.md file so advanced users can inspect and adjust prompt behaviour.
• Supports GPU acceleration for Transformer alignment and supported segmentation models; CPU fallback is automatic.

GPT-5.5 acknowledgement and disclaimer
This version was developed and revised with assistance from GPT-5.5 Thinking for code generation, debugging, documentation and interface text. GPT-5.5 and other LLM outputs are assistive only. Automatic alignment, similarity scores and LLM suggestions may be incomplete or wrong, and they must be checked by the user before use in research, teaching, publication, legal, administrative or corpus-release contexts. The author and software do not guarantee the accuracy, completeness or fitness of LLM-generated suggestions.

Author
Dingjia LIU / 刘鼎甲
Beijing Foreign Studies University
Email: djliu@bfsu.edu.cn

Version
BFSU AlignLens v1.3 Round 25

Copyright © 2026 Dingjia LIU. All rights reserved.''',
})
TRANSLATIONS['zh_sim'].update({
    'llm_suggestion_language': 'LLM 建议语种',
    'about_full': '''BFSU AlignLens 是一款面向多语平行文本建设与翻译对齐检查的桌面工具。

它适合需要处理源文本与译文对齐、一语多译比较、多语平行语料整理、句段对应检查和按行导出研究数据的用户。软件的目标不是替代人工判断，而是帮助用户更快完成导入、分段、分句、自动对齐、人工修订、质量检查和批量导出。

主要流程
• 按文件组导入源语和译语文本。
• 根据语种设置进行自然段分段或句子分句。
• 使用 Transformer 或 LLM 进行段落/句子对齐。
• 在文件组对齐编辑器中检查结果，手动调整行和单元格，重新计算相似度，并标记低相似度行。
• 校对完成后，将当前文件组标记为“完成对齐”。
• 可导出单个文件组、多个文件组，也可按语种/译本导出按行对应的 TXT 文件。

主要功能
• 支持 1 对 1 翻译、一语多译和多语平行文本。
• 默认采用 Round 25 Transformer 参数：LaBSE + multilingual-e5-base 双模型融合、full DP、句对齐最大合并句数 3、高置信度阈值 0.70、低相似度强制匹配惩罚 0.25。
• 可在“设置 > LLM 设置”中指定 LLM 检查建议的输出语种。
• 继续以 gpt-5.4-mini 作为默认 OpenAI 模型；如用户账号支持，也可以自行填写 GPT-5.5 或其他模型名称。
• 软件根目录下的 Prompt.md 集中保存所有 LLM 提示词，便于用户查看和按需调整。
• Transformer 对齐和支持 GPU 的分句模型可使用 GPU 加速；不支持 GPU 时自动使用 CPU。

GPT-5.5 参与和免责说明
本版本在代码生成、调试、文档整理和界面文字修订过程中使用了 GPT-5.5 Thinking 辅助。GPT-5.5 和其他大模型输出仅作为辅助建议；自动对齐、相似度分数和 LLM 建议都可能存在遗漏或错误。用于研究、教学、出版、法律、行政或语料库正式发布前，用户必须自行检查确认。作者和软件不保证 LLM 生成建议的准确性、完整性或特定用途适用性。

作者
Dingjia LIU / 刘鼎甲
北京外国语大学
邮箱：djliu@bfsu.edu.cn

版本
BFSU AlignLens v1.3 Round 25

Copyright © 2026 Dingjia LIU. All rights reserved.''',
})
TRANSLATIONS['zh_tra'].update({
    'llm_suggestion_language': 'LLM 建議語種',
    'about_full': '''BFSU AlignLens 是一款面向多語平行文本建設與翻譯對齊檢查的桌面工具。

它適合需要處理源文本與譯文對齊、一語多譯比較、多語平行語料整理、句段對應檢查和按行導出研究數據的使用者。軟體的目標不是替代人工判斷，而是幫助使用者更快完成導入、分段、分句、自動對齊、人工修訂、質量檢查和批量導出。

主要流程
• 按文件組導入源語和譯語文本。
• 根據語種設定進行自然段分段或句子分句。
• 使用 Transformer 或 LLM 進行段落/句子對齊。
• 在文件組對齊編輯器中檢查結果，手動調整行和單元格，重新計算相似度，並標記低相似度行。
• 校對完成後，將當前文件組標記為「完成對齊」。
• 可導出單個文件組、多個文件組，也可按語種/譯本導出按行對應的 TXT 文件。

主要功能
• 支援 1 對 1 翻譯、一語多譯和多語平行文本。
• 預設採用 Round 25 Transformer 參數：LaBSE + multilingual-e5-base 雙模型融合、full DP、句對齊最大合併句數 3、高置信度閾值 0.70、低相似度強制匹配懲罰 0.25。
• 可在「設定 > LLM 設定」中指定 LLM 檢查建議的輸出語種。
• 繼續以 gpt-5.4-mini 作為預設 OpenAI 模型；如使用者帳號支援，也可以自行填寫 GPT-5.5 或其他模型名稱。
• 軟體根目錄下的 Prompt.md 集中保存所有 LLM 提示詞，便於使用者查看和按需調整。
• Transformer 對齊和支援 GPU 的分句模型可使用 GPU 加速；不支援 GPU 時自動使用 CPU。

GPT-5.5 參與和免責說明
本版本在代碼生成、調試、文檔整理和界面文字修訂過程中使用了 GPT-5.5 Thinking 輔助。GPT-5.5 和其他大模型輸出僅作為輔助建議；自動對齊、相似度分數和 LLM 建議都可能存在遺漏或錯誤。用於研究、教學、出版、法律、行政或語料庫正式發布前，使用者必須自行檢查確認。作者和軟體不保證 LLM 生成建議的準確性、完整性或特定用途適用性。

作者
Dingjia LIU / 劉鼎甲
北京外國語大學
郵箱：djliu@bfsu.edu.cn

版本
BFSU AlignLens v1.3 Round 25

Copyright © 2026 Dingjia LIU. All rights reserved.''',
})
