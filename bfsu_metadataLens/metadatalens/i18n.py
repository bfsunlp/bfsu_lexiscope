from __future__ import annotations

TEXT: dict[str, dict[str, str]] = {
    "zh_CN": {
        "app_title": "BFSU MetadataLens",
        "file": "文件", "schema": "规范", "records": "记录", "language": "语言", "settings": "设置", "view": "视图", "help": "帮助",
        "new_project": "新建项目", "open_project": "打开项目", "save": "保存项目", "save_as": "另存为", "close_project": "关闭项目", "exit": "退出",
        "overview": "项目概览", "schema_design": "元信息规范设计", "record_entry": "条目录入", "records_table": "记录总表", "import_export": "导入 / 导出",
        "project": "项目", "project_name": "项目名称", "corpus_type": "语料库类型", "schema_version": "规范版本", "field_count": "字段数量", "record_count": "记录数量",
        "template": "模板", "system_templates": "系统默认模板", "user_templates": "用户模板", "empty_schema": "空白规范", "template_manager": "模板库",
        "save_user_template": "保存为用户模板", "delete_user_template": "删除用户模板", "use_blank_schema": "不使用模板，创建空白规范",
        "system_readonly": "系统默认模板为只读模板，不能被覆盖或删除。创建项目时会复制一份到项目中，因此项目内部仍可自由修改规范。",
        "user_template_note": "用户模板保存在当前用户配置目录，可由用户创建、删除并在新项目中直接复用。",
        "select_template_details": "请选择一个模板；也可以勾选“创建空白规范”。系统模板与用户模板分开显示。",
        "blank_schema_details": "将创建一个不含字段的空白规范。建议随后进入“元信息规范设计”完成字段设计。",
        "untitled_project": "未命名元信息项目", "no_project_loaded": "尚未打开项目", "create_or_open_hint": "请新建项目或打开已有项目。", "not_saved_yet": "尚未保存",
        "create": "创建", "cancel": "取消", "ok": "确定", "open": "打开",
        "schema_help": "“规范设计”用于定义字段、格式、层级和校验规则；“条目录入”只负责填写具体元信息。两者功能明确分开。",
        "record_no_project_hint": "当前没有活动项目。请先新建或打开项目，再进行条目录入。",
        "record_details_hint": "新建或选择一条记录后，这里会显示该记录的完整元信息。",
        "record_table_details_hint": "在记录总表中选择一条或多条记录，可在这里查看完整信息或执行编辑、校验、复制和删除。",
        "schema_details_hint": "在左侧字段表中选择一个字段，可在这里查看字段格式、层级、必填状态和说明。",
        "overview_details": "项目概览用于快速查看字段数、记录数、必填字段、缺失值和当前大模型服务商。上方工具栏与左侧功能区提供完整工作流入口。",
        "io_details": "导入 / 导出页面集中管理 Excel/XML 导入、记录导出、规范导入导出、模板库和大模型设置。",
        "project_created_details": "项目已创建。建议先检查或设计元信息规范，再进行条目录入或批量导入。",
        "project_saved_details": "项目已保存：{path}",
        "group_project": "项目与模板", "group_schema": "规范设计", "group_records": "条目录入", "group_data": "导入与输出",
        "toolbar_new": "新建", "toolbar_open": "打开", "toolbar_save": "保存", "toolbar_schema": "规范设计", "toolbar_templates": "模板库", "toolbar_ai_schema": "AI设计规范",
        "toolbar_new_record": "新建记录", "toolbar_records": "记录总表", "toolbar_ai_extract": "AI识别元信息", "toolbar_import_excel": "导入Excel", "toolbar_import_xml": "导入XML", "toolbar_export": "导入/导出",
        "sidebar_new_project": "新建元信息项目", "sidebar_open_project": "打开已有项目", "sidebar_templates": "系统 / 用户模板库",
        "sidebar_schema_design": "设计元信息规范", "sidebar_import_schema": "导入外部规范", "sidebar_ai_schema": "大模型辅助设计规范",
        "sidebar_new_record": "新建元信息记录", "sidebar_records_table": "打开记录总表", "sidebar_ai_extract": "大模型识别当前记录",
        "sidebar_import_excel": "导入 Excel 元信息", "sidebar_import_xml": "导入 XML 元信息", "sidebar_import_export": "更多导入与导出",
        "provider_settings_short": "大模型设置",
        "field_id": "字段ID", "label_zh": "中文名称", "label_en": "英文名称", "xml_tag": "XML标签", "data_type": "数据类型", "level": "层级",
        "parent": "父级", "order": "顺序", "required": "必填", "repeatable": "可重复", "visible": "显示", "editable": "可编辑", "sensitive": "敏感字段",
        "controlled_values": "受控词表", "default_value": "默认值", "validation_rule": "校验规则", "example": "示例", "description_zh": "中文说明", "description_en": "英文说明",
        "description": "说明", "format_hint": "格式提示", "field_properties": "字段属性", "add_field": "新增字段", "delete_field": "删除字段", "delete_all": "全部删除",
        "select_all": "全选", "move_up": "上移", "move_down": "下移", "apply_field": "应用字段修改", "open_schema_tab": "打开规范设计",
        "confirm_delete_fields": "将删除选中的 {count} 个字段。是否继续？", "confirm_delete_all_fields": "将删除当前规范的全部 {count} 个字段。是否继续？",
        "fields_deleted": "已删除 {count} 个字段。", "field_id_required": "字段 ID 不能为空。", "fields_short": "字段",
        "new_record": "新建记录", "save_record": "保存当前记录", "validate_record": "校验当前记录", "delete_selected": "删除所选", "copy_record": "复制记录",
        "edit_selected": "编辑所选", "validate_selected": "校验所选", "previous_record": "上一条", "next_record": "下一条", "record_id": "记录ID", "record_type": "记录类型",
        "required_note": "带 * 的字段为必填字段；可重复字段可使用分号 ; 分隔多个值。", "yes_no": "是 / 否", "no_record_selected": "未选择记录",
        "record_position": "第 {current} / {total} 条", "record_saved_status": "记录已保存：{record_id}", "record_validation_ok": "当前记录校验通过。",
        "selected_records_validation_ok": "所选 {count} 条记录均通过校验。", "confirm_delete_records": "将删除所选 {count} 条记录。是否继续？",
        "multiple_records_selected": "已选择 {count} 条记录。可使用下方按钮批量校验或删除。",
        "search": "搜索", "search_records_placeholder": "搜索记录ID、标题、作者或任意字段…", "sort_by": "排序字段", "ascending": "升序", "descending": "降序",
        "import_excel": "导入 Excel", "import_xml": "导入 XML", "import_schema": "导入规范", "export": "导出", "export_xml": "导出记录 XML", "export_excel": "导出 Excel",
        "export_csv": "导出 CSV", "export_schema": "导出当前规范", "validate_schema": "校验当前规范", "schema_validation_ok": "当前元信息规范校验通过。",
        "excel_mapping_title": "Excel 字段映射", "xml_mapping_title": "XML 标签映射", "mapping_help": "请将来源列名 / XML 标签映射到当前规范字段。未映射项目默认忽略；也可选择把未知项加入当前规范。",
        "source_column_or_tag": "来源列名 / XML标签", "target_schema_field": "当前规范字段", "add_unknown_to_schema": "将未映射项自动加入当前规范",
        "import_result": "已导入 {count} 条记录；错误 {errors} 条。", "xml_import_result": "已导入 {count} 条记录。\n{logs}", "replace_schema_confirm": "导入规范将替换当前项目的规范字段定义。是否继续？",
        "export_done": "导出完成：{path}", "template_saved": "用户模板已保存：{path}", "confirm_delete_template": "确认删除用户模板“{name}”？",
        "io_import_title": "导入元信息与规范", "io_import_desc": "从 Excel 或 XML 导入已有元信息；也可导入独立 Schema XML 作为当前项目规范。",
        "io_export_title": "导出记录与规范", "io_export_desc": "将当前项目记录导出为 XML、Excel 或 CSV；规范可单独导出为 Schema XML。",
        "io_template_title": "模板与规范校验", "io_template_desc": "把当前规范保存为用户模板、管理系统/用户模板，并在导出或批量录入前检查规范有效性。",
        "io_ai_title": "大模型辅助", "io_ai_desc": "设置 OpenAI、DeepSeek、千问、Claude 或 Gemini，并使用 AI 识别元信息或辅助设计规范。",
        "provider_settings": "大模型接口设置", "provider": "服务商", "api_key": "API Key", "base_url": "API Base URL", "model": "模型",
        "max_source_chars": "最大文本字符数", "save_settings": "保存设置",
        "llm_note": "支持 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini。每个服务商单独保存 API Key、Base URL 与模型；项目 XML 不保存 API Key。",
        "provider_privacy_note": "只有在用户主动运行“大模型识别元信息”或“大模型辅助设计规范”时，程序才会把所选来源内容发送给当前服务商。",
        "ai_extract": "大模型识别元信息", "ai_schema": "大模型辅助设计规范", "generate_new_schema": "生成新规范", "extend_schema": "扩展当前规范", "requirements": "规范需求说明",
        "schema_requirements_placeholder": "请说明语料库类型、研究目标、需要的元信息层级、字段、受控词表、翻译/说话人/学习者/对齐等需求。",
        "requirements_required": "请先填写规范需求说明。", "source_file": "参考文件", "web_url": "网页 URL", "paste_text": "粘贴文本", "browse": "浏览",
        "overwrite": "覆盖已有字段值", "start": "开始", "apply_selected": "应用选中项", "apply_all": "应用全部", "confidence": "置信度", "evidence": "依据",
        "warnings": "提示 / 警告", "schema_field": "规范字段", "current_value": "当前值", "suggested_value": "建议值", "rationale": "设计理由",
        "no_source_selected": "请选择文件、填写网页 URL 或粘贴文本。", "working": "处理中…", "failed": "失败", "done": "完成", "no_warnings": "没有额外警告。",
        "select_items_first": "请先选择要应用的项目。", "ai_applied": "已应用 {count} 项。", "replace_ai_schema_confirm": "应用后将用 AI 生成的所选字段替换当前规范。是否继续？",
        "status_ready": "就绪", "saved_marker": "已保存", "unsaved_marker": "有未保存修改", "success": "完成", "warning": "警告", "error": "错误", "confirm": "确认", "details": "完整信息 / 详情",
        "detail_edit": "编辑当前", "detail_validate": "校验当前", "detail_copy": "复制记录", "detail_delete": "删除记录",
        "no_project": "请先新建或打开一个元信息项目。", "unsaved": "当前项目有未保存修改，是否先保存？",
        "metric_fields": "字段", "metric_records": "记录", "metric_required": "必填", "metric_repeatable": "可重复", "metric_missing": "缺失", "metric_provider": "服务商",
        "required_count": "必填字段", "repeatable_count": "可重复字段", "missing_required": "必填缺失", "field_count": "字段数量", "record_count": "记录数量",
        "workflow_heading": "BFSU MetadataLens 推荐工作流",
        "workflow_project": "1. 建立项目与选择模板", "workflow_project_desc": "从系统默认模板或用户模板开始，也可以使用空白规范。系统模板只读，但会复制到项目中供编辑。",
        "workflow_schema": "2. 单独设计元信息规范", "workflow_schema_desc": "先定义字段 ID、XML 标签、类型、层级、必填、可重复、受控词表、说明和校验规则，再进入条目录入。",
        "workflow_entry": "3. 手工录入与记录管理", "workflow_entry_desc": "条目录入页面按当前规范自动生成控件；记录总表用于检索、排序、批量选择、编辑、复制、删除和校验。",
        "workflow_import": "4. 批量导入与导出", "workflow_import_desc": "已有 Excel/XML 元信息可通过字段映射批量导入；记录可导出为 XML、Excel、CSV，规范可单独导出。",
        "workflow_ai": "5. 可选的大模型辅助", "workflow_ai_desc": "配置 OpenAI、DeepSeek、千问、Claude 或 Gemini 后，可从文件、PDF、图片、网页或粘贴文本识别元信息，也可生成/扩展规范。",
        "workflow_validate": "6. 校验后保存与交付", "workflow_validate_desc": "在批量录入或导出前检查 Schema 和记录，确认必填字段、数据类型、受控词表和正则规则符合要求。",
        "user_guide": "使用说明", "guide_subtitle": "语言学与语料库元信息规范设计、录入和管理工具",
        "guide_text": """BFSU MetadataLens 使用说明\n\n一、推荐工作顺序\n1. 新建项目：选择系统默认模板、用户模板或空白规范。\n2. 规范设计：在“元信息规范设计”页定义字段，不要把规范设计和条目录入混在一起。\n3. 条目录入：根据当前规范填写具体元信息记录。\n4. 记录总表：检索、排序、批量选择并检查已有记录。\n5. 导入 / 导出：通过字段映射导入 Excel/XML，或导出 XML/Excel/CSV。\n6. 可选 AI：配置服务商后使用 AI 识别元信息或辅助设计规范。\n7. 校验与保存：在正式交付前校验规范和记录并保存项目。\n\n二、规范设计\n每个字段可设置 field_id、中文/英文名称、XML 标签、数据类型、层级、父级、顺序、必填、可重复、默认值、受控词表、可见性、可编辑性、敏感字段标记、说明、示例和正则校验规则。右侧“格式提示”会根据字段类型自动说明推荐输入格式。\n\n三、模板库\n系统默认模板存放在程序 templates/system 中，程序只读；用户模板存放在当前用户配置目录。新建项目时两类模板分开显示。使用系统模板创建项目后，实际编辑的是项目中的副本，不会修改系统模板。\n\n四、大模型辅助\n支持 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini。API Key 仅保存在本机用户配置目录，不写入项目 XML。只有在用户主动启动 AI 功能时，所选来源内容才会发送给当前服务商。\n\n五、项目文件\n项目统一保存为 UTF-8 XML，包含 project_info、schema、records 和 relations。保存已有项目时会自动备份旧文件。""",
        "about": "关于 BFSU MetadataLens",
        "about_text": "",
        "file_name": "文件名",
    },
    "en_US": {
        "app_title": "BFSU MetadataLens",
        "file": "File", "schema": "Schema", "records": "Records", "language": "Language", "settings": "Settings", "view": "View", "help": "Help",
        "new_project": "New Project", "open_project": "Open Project", "save": "Save Project", "save_as": "Save As", "close_project": "Close Project", "exit": "Exit",
        "overview": "Project Overview", "schema_design": "Metadata Schema Design", "record_entry": "Metadata Entry", "records_table": "Records Table", "import_export": "Import / Export",
        "project": "Project", "project_name": "Project Name", "corpus_type": "Corpus Type", "schema_version": "Schema Version", "field_count": "Field Count", "record_count": "Record Count",
        "template": "Template", "system_templates": "System Templates", "user_templates": "User Templates", "empty_schema": "Empty Schema", "template_manager": "Template Library",
        "save_user_template": "Save as User Template", "delete_user_template": "Delete User Template", "use_blank_schema": "Create a blank schema without a template",
        "system_readonly": "System templates are read-only and cannot be overwritten or deleted. A copy is placed in each new project, so the project schema remains fully editable.",
        "user_template_note": "User templates are stored in the current user's configuration directory and can be created, deleted and reused directly in new projects.",
        "select_template_details": "Select a template, or choose to create a blank schema. System templates and user templates are shown separately.",
        "blank_schema_details": "Creates an empty schema with no fields. Continue in Metadata Schema Design to define fields before data entry.",
        "untitled_project": "Untitled Metadata Project", "no_project_loaded": "No project loaded", "create_or_open_hint": "Create a new project or open an existing project.", "not_saved_yet": "Not saved yet",
        "create": "Create", "cancel": "Cancel", "ok": "OK", "open": "Open",
        "schema_help": "Schema Design defines fields, formats, levels and validation rules; Metadata Entry only fills concrete records. The two workflows are deliberately separated.",
        "record_no_project_hint": "No active project. Create or open a project before entering metadata.",
        "record_details_hint": "Create or select a record to display its complete metadata here.",
        "record_table_details_hint": "Select one or more records in the table to inspect details or run edit, validation, copy and delete actions.",
        "schema_details_hint": "Select a field in the schema table to inspect its format, level, required status and description here.",
        "overview_details": "Project Overview summarizes fields, records, required fields, missing values and the active LLM provider. The top toolbar and left action panel expose the complete workflow.",
        "io_details": "Import / Export centralizes Excel/XML import, record export, schema import/export, template management and LLM settings.",
        "project_created_details": "Project created. Review or design the metadata schema before entering records or running a batch import.",
        "project_saved_details": "Project saved: {path}",
        "group_project": "Project & Templates", "group_schema": "Schema Design", "group_records": "Metadata Entry", "group_data": "Import & Output",
        "toolbar_new": "New", "toolbar_open": "Open", "toolbar_save": "Save", "toolbar_schema": "Schema Design", "toolbar_templates": "Templates", "toolbar_ai_schema": "AI Schema",
        "toolbar_new_record": "New Record", "toolbar_records": "Records", "toolbar_ai_extract": "AI Extract", "toolbar_import_excel": "Import Excel", "toolbar_import_xml": "Import XML", "toolbar_export": "Import/Export",
        "sidebar_new_project": "Create Metadata Project", "sidebar_open_project": "Open Existing Project", "sidebar_templates": "System / User Templates",
        "sidebar_schema_design": "Design Metadata Schema", "sidebar_import_schema": "Import External Schema", "sidebar_ai_schema": "AI-assisted Schema Design",
        "sidebar_new_record": "Create Metadata Record", "sidebar_records_table": "Open Records Table", "sidebar_ai_extract": "AI Extract Current Record",
        "sidebar_import_excel": "Import Excel Metadata", "sidebar_import_xml": "Import XML Metadata", "sidebar_import_export": "More Import & Export",
        "provider_settings_short": "LLM Settings",
        "field_id": "Field ID", "label_zh": "Chinese Label", "label_en": "English Label", "xml_tag": "XML Tag", "data_type": "Data Type", "level": "Level",
        "parent": "Parent", "order": "Order", "required": "Required", "repeatable": "Repeatable", "visible": "Visible", "editable": "Editable", "sensitive": "Sensitive",
        "controlled_values": "Controlled Values", "default_value": "Default Value", "validation_rule": "Validation Rule", "example": "Example", "description_zh": "Chinese Description", "description_en": "English Description",
        "description": "Description", "format_hint": "Format Hint", "field_properties": "Field Properties", "add_field": "Add Field", "delete_field": "Delete Field", "delete_all": "Delete All",
        "select_all": "Select All", "move_up": "Move Up", "move_down": "Move Down", "apply_field": "Apply Field Changes", "open_schema_tab": "Open Schema Design",
        "confirm_delete_fields": "Delete the {count} selected field(s)?", "confirm_delete_all_fields": "Delete all {count} fields in the current schema?",
        "fields_deleted": "Deleted {count} field(s).", "field_id_required": "Field ID is required.", "fields_short": "fields",
        "new_record": "New Record", "save_record": "Save Current Record", "validate_record": "Validate Current Record", "delete_selected": "Delete Selected", "copy_record": "Copy Record",
        "edit_selected": "Edit Selected", "validate_selected": "Validate Selected", "previous_record": "Previous", "next_record": "Next", "record_id": "Record ID", "record_type": "Record Type",
        "required_note": "Fields marked * are required; repeatable fields may contain multiple values separated with semicolons (;).", "yes_no": "Yes / No", "no_record_selected": "No record selected",
        "record_position": "Record {current} / {total}", "record_saved_status": "Record saved: {record_id}", "record_validation_ok": "The current record passed validation.",
        "selected_records_validation_ok": "All {count} selected records passed validation.", "confirm_delete_records": "Delete the {count} selected record(s)?",
        "multiple_records_selected": "{count} records selected. Use the detail actions for batch validation or deletion.",
        "search": "Search", "search_records_placeholder": "Search record ID, title, author or any field…", "sort_by": "Sort By", "ascending": "Ascending", "descending": "Descending",
        "import_excel": "Import Excel", "import_xml": "Import XML", "import_schema": "Import Schema", "export": "Export", "export_xml": "Export Records XML", "export_excel": "Export Excel",
        "export_csv": "Export CSV", "export_schema": "Export Current Schema", "validate_schema": "Validate Current Schema", "schema_validation_ok": "The current metadata schema passed validation.",
        "excel_mapping_title": "Excel Field Mapping", "xml_mapping_title": "XML Tag Mapping", "mapping_help": "Map each source column / XML tag to a field in the active schema. Unmapped items are ignored by default; you may also add unknown items to the current schema.",
        "source_column_or_tag": "Source Column / XML Tag", "target_schema_field": "Current Schema Field", "add_unknown_to_schema": "Automatically add unmapped items to the current schema",
        "import_result": "Imported {count} record(s); {errors} error(s).", "xml_import_result": "Imported {count} record(s).\n{logs}", "replace_schema_confirm": "Importing a schema will replace the current project's schema field definitions. Continue?",
        "export_done": "Export completed: {path}", "template_saved": "User template saved: {path}", "confirm_delete_template": "Delete user template “{name}”?",
        "io_import_title": "Import Metadata and Schemas", "io_import_desc": "Import existing metadata from Excel or XML, or import a standalone Schema XML as the current project schema.",
        "io_export_title": "Export Records and Schemas", "io_export_desc": "Export current records as XML, Excel or CSV. Export the schema separately as Schema XML.",
        "io_template_title": "Templates and Validation", "io_template_desc": "Save the current schema as a user template, manage system/user templates, and validate the schema before batch entry or export.",
        "io_ai_title": "LLM Assistance", "io_ai_desc": "Configure OpenAI, DeepSeek, Qwen, Claude or Gemini, then use AI for metadata extraction or schema generation/extension.",
        "provider_settings": "LLM Provider Settings", "provider": "Provider", "api_key": "API Key", "base_url": "API Base URL", "model": "Model",
        "max_source_chars": "Max Source Characters", "save_settings": "Save Settings",
        "llm_note": "Supports OpenAI, DeepSeek, Qwen, Claude and Gemini. Each provider has separate API Key, Base URL and model settings; API keys are never written to project XML.",
        "provider_privacy_note": "Source content is sent to the active provider only when the user explicitly runs AI Metadata Extraction or AI-assisted Schema Design.",
        "ai_extract": "AI Metadata Extraction", "ai_schema": "AI-assisted Schema Design", "generate_new_schema": "Generate New Schema", "extend_schema": "Extend Current Schema", "requirements": "Schema Requirements",
        "schema_requirements_placeholder": "Describe the corpus type, research goals, metadata levels, fields, controlled vocabularies, and translation/speaker/learner/alignment requirements.",
        "requirements_required": "Enter schema requirements first.", "source_file": "Reference File", "web_url": "Webpage URL", "paste_text": "Paste Text", "browse": "Browse",
        "overwrite": "Overwrite existing field values", "start": "Start", "apply_selected": "Apply Selected", "apply_all": "Apply All", "confidence": "Confidence", "evidence": "Evidence",
        "warnings": "Notes / Warnings", "schema_field": "Schema Field", "current_value": "Current Value", "suggested_value": "Suggested Value", "rationale": "Rationale",
        "no_source_selected": "Select a file, enter a webpage URL, or paste text.", "working": "Working…", "failed": "Failed", "done": "Done", "no_warnings": "No additional warnings.",
        "select_items_first": "Select the items to apply first.", "ai_applied": "Applied {count} item(s).", "replace_ai_schema_confirm": "Applying will replace the current schema with the selected AI-generated fields. Continue?",
        "status_ready": "Ready", "saved_marker": "Saved", "unsaved_marker": "Unsaved changes", "success": "Success", "warning": "Warning", "error": "Error", "confirm": "Confirm", "details": "Full Information / Details",
        "detail_edit": "Edit Current", "detail_validate": "Validate Current", "detail_copy": "Copy Record", "detail_delete": "Delete Record",
        "no_project": "Create or open a metadata project first.", "unsaved": "The current project has unsaved changes. Save first?",
        "metric_fields": "Fields", "metric_records": "Records", "metric_required": "Required", "metric_repeatable": "Repeatable", "metric_missing": "Missing", "metric_provider": "Provider",
        "required_count": "Required Fields", "repeatable_count": "Repeatable Fields", "missing_required": "Missing Required", "field_count": "Field Count", "record_count": "Record Count",
        "workflow_heading": "Recommended BFSU MetadataLens Workflow",
        "workflow_project": "1. Create a project and choose a template", "workflow_project_desc": "Start from a system template, a user template, or a blank schema. System templates are read-only but copied into each project for editing.",
        "workflow_schema": "2. Design the metadata schema separately", "workflow_schema_desc": "Define field IDs, XML tags, types, levels, required/repeatable flags, controlled values, descriptions and validation before entering records.",
        "workflow_entry": "3. Enter and manage records", "workflow_entry_desc": "Metadata Entry generates controls from the active schema; Records Table supports search, sorting, multiple selection, editing, copying, deletion and validation.",
        "workflow_import": "4. Batch import and export", "workflow_import_desc": "Existing Excel/XML metadata can be batch imported through field mapping; records can be exported to XML, Excel or CSV, and schemas can be exported separately.",
        "workflow_ai": "5. Optional LLM assistance", "workflow_ai_desc": "After configuring OpenAI, DeepSeek, Qwen, Claude or Gemini, extract metadata from files, PDFs, images, webpages or pasted text, or generate/extend schemas.",
        "workflow_validate": "6. Validate, save and deliver", "workflow_validate_desc": "Before batch entry or export, validate schemas and records to check required fields, data types, controlled vocabularies and regex rules.",
        "user_guide": "User Guide", "guide_subtitle": "Metadata schema design, entry and management for linguistic and corpus research",
        "guide_text": """BFSU MetadataLens User Guide\n\n1. Recommended workflow\n1) Create a project and choose a system template, user template, or blank schema.\n2) Use Metadata Schema Design to define fields. Do not mix schema design with record entry.\n3) Use Metadata Entry to fill concrete records generated from the current schema.\n4) Use Records Table for search, sorting, multiple selection and record management.\n5) Use Import / Export for mapped Excel/XML import and XML/Excel/CSV export.\n6) Optionally configure an LLM provider for metadata extraction or schema design.\n7) Validate the schema and records before final saving or delivery.\n\n2. Schema design\nEach field can define field_id, Chinese/English labels, XML tag, data type, level, parent, order, required/repeatable flags, default value, controlled vocabulary, visibility, editability, sensitive flag, descriptions, example and regex validation. The Format Hint panel explains the recommended input format for the selected data type.\n\n3. Template library\nSystem templates are stored under templates/system and are read-only. User templates are stored in the current user's configuration directory. The New Project dialog shows the two libraries separately. Creating a project from a system template copies the schema into the project; editing the project never modifies the bundled template.\n\n4. LLM assistance\nOpenAI, DeepSeek, Qwen, Claude and Gemini are supported. API keys are stored only in the local user configuration directory and are not written to project XML. Source content is sent to the provider only when an AI function is explicitly started.\n\n5. Project format\nProjects are stored as UTF-8 XML containing project_info, schema, records and relations. Existing project files are automatically backed up before overwrite.""",
        "about": "About BFSU MetadataLens",
        "about_text": "",
        "file_name": "File Name",
    },
}

# v3.2 additions and revised product copy.
TEXT["zh_CN"].update({
    "record_saved_button": "已保存",
    "stop": "停止",
    "stopping": "正在停止…",
    "cancelled": "已停止",
    "done_elapsed": "处理完成，用时 {seconds} 秒",
    "llm_error_title": "大模型接口错误",
    "ai_context_notice": "当前识别依据：项目“{project}” · 规范“{schema}” · {fields} 个字段。模型只会针对当前项目与当前规范中的字段提出建议。",
    "batch_ai_extract": "大模型批量识别元信息",
    "batch_ai_extract_short": "AI批量识别",
    "batch_ai_no_records": "当前项目没有可用于批量识别的记录。请先新建或导入记录。",
    "batch_ai_help": "为多条记录分配一个或多个参考文件，程序会逐条按照当前项目及当前元信息规范识别。识别结果先进入人工复核，不会自动写入；可逐字段、逐记录确认，也可一键应用全部结果。",
    "selected_records": "当前选中记录",
    "all_records": "全部记录",
    "batch_add_reference_files": "批量添加参考文件",
    "assign_files_to_selected": "将文件分配给所选记录",
    "clear_file_assignment": "清除文件分配",
    "start_batch": "开始批量识别",
    "batch_records_and_sources": "记录与参考文件",
    "reference_files": "参考文件",
    "status": "状态",
    "suggestion_count": "建议字段数",
    "review_ai_suggestions": "人工复核识别结果",
    "not_assigned": "未分配",
    "applied": "已应用",
    "review_pending": "待复核",
    "ready": "就绪",
    "waiting_for_file": "等待参考文件",
    "batch_file_mapping": "已为 {mapped} 条记录分配参考文件。",
    "batch_file_mapping_partial": "已完成部分匹配；仍有 {unmatched} 个文件未能自动匹配记录。请选中记录后使用“将文件分配给所选记录”。",
    "select_records_first": "请先在左侧记录列表中选择记录。",
    "file_record_count_mismatch": "所选记录数与所选文件数不一致。一次为多条记录分配文件时，请使文件数与记录数相同；如果只选中一条记录，可为该记录分配多个参考文件。",
    "multi_binary_reference_not_supported": "同一条记录目前不能同时提交多个需要直接上传给大模型的二进制/扫描文件。请改用可提取文本的文件，或每条记录只保留一个图片/扫描 PDF。",
    "batch_ai_need_files": "至少需要为一条目标记录分配参考文件后才能开始批量识别。",
    "batch_progress": "正在识别 {current} / {total}：{record_id}",
    "batch_failed_record": "记录 {record_id} 识别失败：{error}",
    "batch_done": "批量识别完成：成功 {success} 条，失败 {failed} 条。请逐条检查后应用。",
    "apply_selected_fields_current": "应用当前记录所选字段",
    "apply_current_result": "应用当前记录全部建议",
    "apply_all_batch_results": "一键应用全部识别结果",
    "confirm_apply_all_batch": "将把当前批量任务中尚未应用的全部识别建议写入相应记录。是否继续？",
    "batch_apply_done": "已应用 {records} 条记录，共 {fields} 个字段。",
    "batch_edit_field": "批量修改记录字段",
    "batch_edit_field_short": "批量修改字段",
    "batch_edit_no_records": "当前项目没有可批量修改的记录。",
    "batch_edit_help": "选择一个当前规范字段，并对当前选中记录或全部记录统一设置、追加或清空该字段。应用前可预览修改结果。",
    "batch_operation": "批量操作",
    "batch_op_set": "设置 / 替换",
    "batch_op_append": "追加",
    "batch_op_clear": "清空",
    "new_value": "新值",
    "preview_changes": "预览修改",
    "apply_batch_edit": "应用批量修改",
    "target_record_count": "目标记录：{count} 条",
    "batch_value_required": "“设置 / 替换”或“追加”操作需要填写新值。",
    "confirm_batch_edit": "将对 {count} 条记录的字段“{field}”执行“{operation}”。是否继续？",
    "batch_edit_done": "批量修改完成，共更新 {count} 条记录。",
    "about_subtitle": "面向语言学与语料库建设的元信息设计、录入与管理工具",
    "io_ai_desc": "配置 OpenAI、DeepSeek、千问 / Qwen、Claude 或 Gemini，可进行单条/批量元信息识别以及规范生成或扩展；所有结果均先供人工复核。",
    "workflow_ai_desc": "配置 OpenAI、DeepSeek、千问 / Qwen、Claude 或 Gemini 后，可对单条或多条记录从文件、PDF、图片、网页或文本中识别元信息，也可生成或扩展元信息规范。",
    "guide_text": """BFSU MetadataLens 使用说明\n\n1. 推荐工作流\n1）新建项目，并选择系统默认模板、用户模板或空白规范。\n2）进入“元信息规范设计”，先定义字段、格式、层级和校验规则。\n3）进入“条目录入”填写具体元信息；保存后按钮会显示“已保存”，再次修改任意字段后会恢复为“保存当前记录”。\n4）在“记录总表”中进行检索、排序、多选、复制、删除、校验，以及对某个字段进行批量修改。\n5）已有 Excel/XML 元信息可通过字段映射批量导入，记录可导出为 XML、Excel 或 CSV，规范可单独导出。\n6）可选配置大模型服务商。单条识别和批量识别都严格以当前项目信息与当前 Schema 字段为约束，结果先进入人工复核后再应用。批量识别支持为多条记录批量分配参考文件。\n7）规范和记录完成后执行校验，并保存统一 UTF-8 XML 项目文件。\n\n2. 元信息规范设计\n每个字段可定义 field_id、中英文名称、XML 标签、数据类型、层级、父级、顺序、必填/可重复、默认值、受控词表、显示、可编辑、敏感字段、说明、示例和正则校验。“格式提示”会根据字段数据类型、示例、校验规则和可重复状态给出录入提示。\n\n3. 模板库\n系统模板位于 templates/system，为只读模板；用户模板保存在当前用户配置目录。新建项目时两类模板分开显示。使用系统模板创建项目时，程序只复制 Schema 到项目中，因此项目内修改不会影响系统模板。\n\n4. 记录管理与批量修改\n条目录入用于编辑一条具体记录；记录总表适合批量管理。选择若干记录后，可对当前 Schema 中的某一字段统一设置、追加或清空，并在应用前预览。\n\n5. 大模型辅助\n支持 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini。API Key 仅保存在本地用户配置文件，不写入项目 XML。只有用户主动启动大模型功能时才发送参考内容。处理过程中会显示进度并禁用开始按钮，可随时点击“停止”；远程接口异常会给出可操作的错误提示。\n\n6. 项目格式\n项目统一保存为 UTF-8 XML，包含 project_info、schema、records 和 relations。覆盖已有项目文件前会自动创建备份。""",
    "about_text": """BFSU MetadataLens 是一款面向语言学研究、语料库建设与语料库翻译学研究的元信息制作、规范设计和统一管理工具。软件强调先设计元信息规范，再依据规范录入或导入具体记录，使语料库元信息在字段命名、数据类型、XML 标记、受控词表和校验规则方面保持一致。\n\n主要功能\n• 元信息规范设计：支持字段 ID、中英文标签、XML 标签、数据类型、层级、必填/可重复、默认值、受控词表、示例、说明及正则校验等属性，并提供针对不同字段格式的录入提示。\n• 多类语料库模板：提供单语、双语平行、多语平行、一本多译、可比、学习者和口语语料库等系统模板；系统模板只读，用户模板独立保存和管理。\n• 元信息条目录入与记录管理：根据当前规范动态生成录入表单，支持记录新增、编辑、复制、删除、检索、排序和校验。\n• 批量字段修改：可对选中记录或全部记录的指定字段统一设置、追加或清空，并在应用前预览。\n• 数据导入与导出：支持 Excel 和 XML 元信息导入及字段映射；支持记录导出为 XML、Excel、CSV，并可单独导入、导出元信息规范。\n• 大模型辅助：支持 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini，可依据当前项目信息和当前 Schema 对单条或多条记录识别元信息，也可生成或扩展 Schema。识别建议不会直接写入记录，用户可逐字段复核、逐记录应用或在确认后批量应用。\n• 处理控制与错误提示：大模型处理期间提供进度状态、重复操作保护和停止功能；远程接口、额度、鉴权、网络或返回格式异常会显示明确提示。\n• 项目保存与数据校验：项目统一保存为 UTF-8 XML；支持规范与记录校验，并在覆盖已有项目文件前自动备份。\n\n适用场景\nBFSU MetadataLens 可用于语言资源数据库、单语与多语语料库、平行与可比语料库、学习者语料库、口语语料库以及语料库翻译学项目的元信息规范制定、整理、录入、迁移和长期维护。\n\n开发者 / Developer\n刘鼎甲 博士 / Dr. Dingjia LIU\nBeijing Foreign Studies University\nEmail: djliu@bfsu.edu.cn\n\nVersion 3.2.0\nCopyright © 2026 Dingjia LIU. All rights reserved.""",
})

TEXT["en_US"].update({
    "record_saved_button": "Saved",
    "stop": "Stop",
    "stopping": "Stopping…",
    "cancelled": "Stopped",
    "done_elapsed": "Completed in {seconds} seconds",
    "llm_error_title": "LLM Provider Error",
    "ai_context_notice": "Current extraction context: project “{project}” · schema “{schema}” · {fields} fields. The model is constrained to the active project and current schema fields.",
    "batch_ai_extract": "Batch AI Metadata Extraction",
    "batch_ai_extract_short": "Batch AI Extract",
    "batch_ai_no_records": "The current project has no records for batch extraction. Create or import records first.",
    "batch_ai_help": "Assign one or more reference files to records and process them sequentially against the active project and schema. Suggestions are held for human review and are never written automatically; review by field or record, or apply all results after confirmation.",
    "selected_records": "Selected Records",
    "all_records": "All Records",
    "batch_add_reference_files": "Add Reference Files",
    "assign_files_to_selected": "Assign Files to Selected",
    "clear_file_assignment": "Clear File Assignment",
    "start_batch": "Start Batch Extraction",
    "batch_records_and_sources": "Records and Reference Files",
    "reference_files": "Reference Files",
    "status": "Status",
    "suggestion_count": "Suggested Fields",
    "review_ai_suggestions": "Review AI Suggestions",
    "not_assigned": "Not Assigned",
    "applied": "Applied",
    "review_pending": "Review Pending",
    "ready": "Ready",
    "waiting_for_file": "Waiting for Reference File",
    "batch_file_mapping": "Reference files assigned to {mapped} record(s).",
    "batch_file_mapping_partial": "Partial matching completed; {unmatched} file(s) could not be mapped automatically. Select records and use “Assign Files to Selected”.",
    "select_records_first": "Select one or more records in the left-hand list first.",
    "file_record_count_mismatch": "The number of selected records does not match the number of files. For multiple records, select the same number of files; a single record may receive multiple reference files.",
    "multi_binary_reference_not_supported": "A single record cannot currently submit multiple binary/scanned sources directly to an LLM. Use text-extractable files, or keep only one image/scanned PDF for that record.",
    "batch_ai_need_files": "Assign reference files to at least one target record before starting batch extraction.",
    "batch_progress": "Extracting {current} / {total}: {record_id}",
    "batch_failed_record": "Record {record_id} failed: {error}",
    "batch_done": "Batch extraction finished: {success} succeeded, {failed} failed. Review results before applying them.",
    "apply_selected_fields_current": "Apply Selected Fields to Current Record",
    "apply_current_result": "Apply All Suggestions to Current Record",
    "apply_all_batch_results": "Apply All Batch Results",
    "confirm_apply_all_batch": "This will write all unapplied suggestions in the current batch task to their records. Continue?",
    "batch_apply_done": "Applied {fields} field(s) across {records} record(s).",
    "batch_edit_field": "Batch Edit Record Field",
    "batch_edit_field_short": "Batch Edit Field",
    "batch_edit_no_records": "The current project has no records to batch edit.",
    "batch_edit_help": "Choose one field from the active schema and set, append to, or clear it across the selected records or all records. Preview the changes before applying them.",
    "batch_operation": "Batch Operation",
    "batch_op_set": "Set / Replace",
    "batch_op_append": "Append",
    "batch_op_clear": "Clear",
    "new_value": "New Value",
    "preview_changes": "Preview Changes",
    "apply_batch_edit": "Apply Batch Edit",
    "target_record_count": "Target records: {count}",
    "batch_value_required": "Set / Replace and Append operations require a new value.",
    "confirm_batch_edit": "Apply “{operation}” to field “{field}” for {count} record(s)?",
    "batch_edit_done": "Batch edit completed; {count} record(s) were updated.",
    "about_subtitle": "Metadata schema design, entry and management for linguistics and corpus construction",
    "io_ai_desc": "Configure OpenAI, DeepSeek, Qwen, Claude or Gemini for single/batch metadata extraction and schema generation/extension; all results are presented for human review first.",
    "workflow_ai_desc": "After configuring OpenAI, DeepSeek, Qwen, Claude or Gemini, extract metadata for one or many records from files, PDFs, images, webpages or text, or generate/extend metadata schemas.",
    "guide_text": """BFSU MetadataLens User Guide\n\n1. Recommended workflow\n1) Create a project and choose a system template, user template, or blank schema.\n2) Use Metadata Schema Design to define fields, formats, levels and validation rules before entering records.\n3) Use Metadata Entry for concrete records. After saving, the button changes to “Saved”; editing any value changes it back to “Save Current Record”.\n4) Use Records Table for search, sorting, multiple selection, copying, deletion, validation and batch editing of a chosen field.\n5) Import existing Excel/XML metadata through field mapping, and export records as XML, Excel or CSV; schemas can be exported separately.\n6) Optionally configure an LLM provider. Single and batch extraction are constrained by the active project information and schema fields. Suggestions are reviewed before they are written. Batch extraction supports assigning reference files to many records.\n7) Validate the schema and records, then save the unified UTF-8 XML project file.\n\n2. Metadata schema design\nA field can define field_id, Chinese/English labels, XML tag, data type, level, parent, order, required/repeatable flags, default value, controlled vocabulary, visibility, editability, sensitive flag, descriptions, example and regular-expression validation. Format Hint explains input expectations based on the selected data type, example, validation rule and repeatability.\n\n3. Template library\nSystem templates live under templates/system and are read-only. User templates are stored in the current user's configuration directory. The New Project dialog shows them separately. Creating a project from a system template copies its schema, so editing the project never modifies the bundled template.\n\n4. Record management and batch editing\nMetadata Entry edits one concrete record. Records Table is designed for batch management. After selecting records, a field in the current schema can be set/replaced, appended to or cleared, with a preview before application.\n\n5. LLM assistance\nOpenAI, DeepSeek, Qwen, Claude and Gemini are supported. API keys stay in the local user configuration and are never written to project XML. Reference content is sent only when the user explicitly starts an LLM task. Processing shows progress, disables the Start button, provides Stop, and reports actionable remote-provider errors.\n\n6. Project format\nProjects are stored as UTF-8 XML containing project_info, schema, records and relations. Existing project files are automatically backed up before overwrite.""",
    "about_text": """BFSU MetadataLens is a metadata creation, schema-design and management tool for linguistic research, corpus construction and corpus-based translation studies. Its workflow separates metadata specification from concrete record entry so that field naming, data types, XML tags, controlled vocabularies and validation rules remain consistent throughout a corpus project.\n\nCore capabilities\n• Metadata schema design: define field IDs, bilingual labels, XML tags, data types, levels, required/repeatable flags, defaults, controlled vocabularies, examples, descriptions and regular-expression validation, with format guidance for data entry.\n• Corpus-oriented templates: bundled system templates for monolingual, bilingual parallel, multilingual parallel, multiple-translations, comparable, learner and spoken corpora. System templates are read-only, while user templates are stored and managed separately.\n• Metadata entry and record management: dynamic forms generated from the active schema, with record creation, editing, copying, deletion, search, sorting and validation.\n• Batch field editing: set/replace, append to or clear one selected schema field across selected records or the complete record set, with preview before application.\n• Import and export: Excel/XML metadata import with field mapping; XML, Excel and CSV record export; standalone schema import/export.\n• LLM assistance: OpenAI, DeepSeek, Qwen, Claude and Gemini are supported for single-record and batch metadata extraction constrained by the active project and schema, as well as schema generation/extension. Suggestions are never written automatically: users may review individual fields, apply a record, or confirm a complete batch.\n• Processing control and error handling: LLM operations expose progress, prevent duplicate starts and can be stopped; authentication, quota, network, server and response-format failures are reported with actionable messages.\n• Project persistence and validation: projects are stored as unified UTF-8 XML, schemas and records can be validated, and existing project files are backed up before overwrite.\n\nTypical uses\nBFSU MetadataLens can support metadata specification, entry, migration and long-term maintenance for language-resource databases, monolingual and multilingual corpora, parallel and comparable corpora, learner corpora, spoken corpora and corpus-based translation studies.\n\nDeveloper\nDr. Dingjia LIU / 刘鼎甲 博士\nBeijing Foreign Studies University\nEmail: djliu@bfsu.edu.cn\n\nVersion 3.2.0\nCopyright © 2026 Dingjia LIU. All rights reserved.""",
})


# v3.3 first-launch, privacy, batch-new-record and help/about revisions.
TEXT["zh_CN"].update({
    "delete_all_keys": "删除所有 Key",
    "confirm_delete_all_keys": "将删除本机保存的 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini 的全部 API Key。此操作不会改变模型名称和 Base URL。是否继续？",
    "all_keys_deleted": "所有 API Key 已从当前用户的本地凭据文件中删除。",
    "llm_note": "支持 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini。模型名称和 Base URL 保存在本机用户设置中；API Key 单独保存在当前用户的本地凭据文件中，不写入项目 XML，也不写入软件安装目录。复制或打包软件目录不会携带 API Key。",
    "provider_privacy_note": "API Key 仅用于当前电脑、当前系统用户发起大模型请求。只有用户主动启动识别或规范设计时，所选参考内容才会发送给当前服务商。",
    "batch_ai_help_new": "批量识别默认用于新增元信息：每个参考文件作为一条待新增记录进行识别，不与当前项目中已有记录匹配。识别结果先保留在复核区，只有用户人工确认并点击应用后才写入项目。",
    "batch_new_records_and_sources": "待新增元信息与参考文件",
    "new_metadata_record": "待新增记录",
    "new_record_number": "新增记录 {number}",
    "remove_selected_batch_sources": "移除所选参考文件",
    "clear_all_batch_sources": "清空未应用参考文件",
    "confirm_clear_batch_sources": "将清除 {count} 个尚未应用的批量识别任务。是否继续？",
    "batch_waiting_files": "请先批量添加参考文件；每个文件默认生成一条新的元信息记录。",
    "batch_new_files_added": "已添加 {count} 个参考文件，共 {total} 条待新增记录。",
    "batch_ready_count": "当前有 {count} 条待新增记录。",
    "batch_ai_need_new_files": "请先添加至少一个参考文件。批量识别默认按“一个参考文件 → 一条新增元信息记录”处理。",
    "batch_progress_new": "正在识别 {current} / {total}：{file}",
    "batch_failed_file": "参考文件“{file}”识别失败。",
    "batch_done_new": "批量识别完成：成功 {success} 条，失败 {failed} 条。请逐条检查字段建议后再应用。",
    "apply_current_result_new": "应用当前新增记录",
    "apply_all_batch_results_new": "一键应用全部新增记录",
    "confirm_apply_all_batch_new": "将把 {count} 条尚未完全应用的识别结果写入当前项目，并作为新的元信息记录加入记录总表。是否继续？",
    "batch_apply_done_new": "已新增/更新 {records} 条记录，共应用 {fields} 个字段。",
    "batch_apply_note": "未点击“应用”前，批量识别结果不会写入当前项目。",
    "guide_subtitle": "语言学与语料库项目的元信息规范设计、录入、批量整理与大模型辅助",
    "guide_text": """BFSU MetadataLens 使用说明

一、开始使用
BFSU MetadataLens 用于设计语料库元信息规范、录入和维护元信息记录、批量导入既有数据，并在需要时使用大模型辅助识别元信息。软件第一次启动时默认使用英文界面；可通过“Language / 语言”菜单切换为中文。之后软件会记住当前用户选择的界面语言。

建议的基本顺序是：
1. 新建项目；
2. 选择系统模板、用户模板或空白规范；
3. 检查并完善“元信息规范设计”；
4. 录入新记录，或从 Excel/XML 批量导入；
5. 根据需要使用单条或批量大模型识别；
6. 在记录总表中检索、检查和批量修改；
7. 校验规范与记录；
8. 保存项目，并按需要导出 XML、Excel 或 CSV。

二、新建项目与模板
选择“文件 → 新建项目”或顶部“新建”。填写项目名称后选择模板。

系统默认模板与用户模板分开显示：
• 系统默认模板：随软件提供，只读，不允许覆盖或删除；
• 用户模板：由用户保存，存放在当前系统用户的配置目录，可重复使用和删除；
• 空白规范：不预置字段，适合完全自定义的项目。

系统模板包括单语、双语平行、多语平行、一本多译、可比、学习者和口语语料库。用系统模板创建项目时，软件会把模板复制到项目内部，因此修改当前项目的字段不会改变系统模板。

三、元信息规范设计
进入“元信息规范设计”后，先确定项目需要记录哪些信息。每个字段可以设置：
• 字段 ID：项目内部稳定使用的字段标识；
• 中文名称、英文名称；
• XML 标签；
• 数据类型：普通文本、整数、小数、日期、年份、布尔值、受控词表、长文本、语言代码、文件路径；
• 元信息层级：corpus、subcorpus、text、version、file、speaker、segment、alignment、relation、project；
• 父级与字段顺序；
• 必填、可重复、显示、可编辑、敏感字段；
• 默认值；
• 受控词表；
• 正则校验规则；
• 示例；
• 中文说明和英文说明。

选择字段后查看“格式提示”。例如 year 建议输入四位年份，date 建议使用 YYYY-MM-DD，language_code 建议使用 zh、en、zh-CN 等代码。可重复字段可以使用分号分隔多个值。

修改字段属性后点击“应用字段修改”。完成规范设计后建议执行“校验当前规范”，先解决重复字段 ID、非法数据类型、空 XML 标签或不完整受控词表等问题，再开始大量录入。

四、手工录入元信息
进入“条目录入”，点击“新建记录”。软件会按照当前 Schema 自动生成表单。

录入时请注意：
• 带 * 的字段为必填；
• 枚举字段应从受控词表中选择；
• 日期、年份、语言代码等字段按照字段下方提示填写；
• 可重复字段可使用分号分隔多个值；
• 长文本字段可直接录入摘要、备注或说明。

点击“保存当前记录”后，按钮会变为“已保存”。只要再次修改任何字段，按钮会恢复为“保存当前记录”，用于提醒当前表单仍有未保存改动。可使用“上一条 / 下一条”在记录间切换。

五、记录总表与批量修改
“记录总表”用于集中管理当前项目的全部记录。可以：
• 搜索 record_id、标题、作者或任意字段；
• 按指定字段升序或降序排列；
• 多选记录；
• 编辑、复制、删除和校验记录；
• 双击记录进入条目录入；
• 对多个记录或全部记录批量修改某个字段。

使用“批量修改字段”时，先选择目标范围和 Schema 字段，再选择操作：
• 设置 / 替换：统一改成新值；
• 追加：在原值基础上增加新值；
• 清空：删除该字段现有值。

正式应用前先查看预览，确认目标记录和修改结果无误。

六、导入 Excel 元信息
选择“导入 Excel”。软件读取工作表首行为列名，并尝试把列名与当前 Schema 的 field_id、XML 标签或中英文标签自动匹配。

在字段映射窗口中逐项检查：
• 已正确匹配的列可以保留；
• 不需要的列可以忽略；
• 如确有必要，可以把未知列加入当前 Schema。

批量导入前建议先完成 Schema 设计，避免导入后产生大量临时字段。导入完成后在记录总表抽查若干记录，并执行校验。

七、导入 XML 元信息
选择“导入 XML”。软件会扫描 XML 标签并提出字段映射建议。对于完整的 MetadataLens 项目 XML，可读取项目结构；对于一般 XML，则根据标签映射导入记录。

导入前检查当前 Schema 与目标 XML 是否一致。未知标签是否加入 Schema 应根据项目规范决定，不建议为了保留无关 XML 标签而随意扩充元信息规范。

八、大模型接口设置与 API Key
进入“大模型设置”，可分别配置 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini。每个服务商可单独填写 API Key、Base URL 和模型名称，并选择当前默认服务商。

API Key 的保存规则：
• API Key 只保存在当前操作系统用户的本地配置目录；
• API Key 不写入项目 XML；
• API Key 不写入软件源代码或安装目录；
• 复制、压缩或移动软件目录不会复制 API Key；
• 模型名称和 Base URL 与 API Key 分开保存；
• 可在“大模型设置”中点击“删除所有 Key”，一次清除本机保存的全部服务商 API Key。

只有用户主动启动大模型功能时，程序才会向当前服务商发送所选参考内容。

九、单条大模型识别元信息
在已有记录中使用“AI 识别元信息”时，大模型会同时参考：
• 当前项目名称、语料库类型等项目信息；
• 当前 Schema 名称、版本和完整字段定义；
• 当前记录已有字段值；
• 用户选择的文件、PDF、图片、网页或粘贴文本。

模型只能针对当前 Schema 中已经存在的字段提出建议。识别完成后请检查建议值、置信度和依据，再选择应用部分字段或全部字段。软件不会因为模型返回了额外字段而自动改变当前 Schema。

处理期间“开始”按钮会被冻结，并显示处理状态；需要终止时点击“停止”。如果出现 API Key、额度、模型名称、网络、超时或远程服务器错误，程序会给出提示。

十、批量大模型识别新增元信息
“AI 批量识别”默认用于新增记录，不需要预先在项目中建立空记录，也不会尝试把参考文件与当前数据库已有记录匹配。

操作步骤：
1. 打开“AI 批量识别”；
2. 点击“批量添加参考文件”；
3. 每个参考文件默认对应一条待新增元信息记录；
4. 点击“开始批量识别”；
5. 左侧逐条查看文件处理状态；
6. 右侧检查每个字段的建议值、置信度和来源依据；
7. 可以只应用当前记录中人工选中的字段；
8. 可以应用当前新增记录的全部建议；
9. 也可以在确认后“一键应用全部新增记录”。

在点击应用之前，识别结果只保留在批量复核窗口，不会进入项目记录。批量处理期间可以点击“停止”。如果个别文件失败，其它文件仍可继续处理，失败原因会单独显示。

十一、大模型辅助设计规范
“大模型辅助设计规范”用于生成新 Schema 或扩展当前 Schema。填写语料库类型、研究目的、元信息层级和字段要求后，可附加参考文件或样本文本。

AI 生成结果先以字段候选表显示，用户需要人工检查字段 ID、标签、数据类型、层级、受控词表和说明后再应用。生成新规范会替换当前 Schema，应特别谨慎；扩展当前规范更适合在已有规范基础上补充字段。

十二、校验、保存与导出
建议在以下节点执行校验：
• 完成 Schema 设计后；
• 批量导入数据后；
• 大规模手工录入后；
• 导出或交付项目前。

项目统一保存为 UTF-8 XML，包含 project_info、schema、records 和 relations。覆盖已有项目文件前会自动生成备份。

可导出：
• 记录 XML；
• Excel；
• CSV；
• 当前 Schema XML。

如果要在另一台电脑继续工作，只需复制项目 XML 和需要的用户模板。API Key 不会随软件或项目文件迁移，需要在新电脑上重新配置。""",
    "about_subtitle": "面向语言学与语料库建设的元信息规范设计、录入与管理工具",
    "about_text": """BFSU MetadataLens 是一款面向语言学研究、语料库建设、语言资源数据库建设和语料库翻译学研究的元信息制作与管理工具。

主要功能
• 元信息规范设计：创建和维护字段 ID、中英文名称、XML 标签、数据类型、元信息层级、必填/可重复属性、默认值、受控词表、说明、示例和校验规则。
• 语料库模板：提供单语、双语平行、多语平行、一本多译、可比、学习者和口语语料库系统模板，并支持独立的用户模板库。
• 元信息条目录入：根据当前 Schema 自动生成录入表单，支持记录新增、编辑、保存、复制、删除和校验。
• 记录管理：支持记录总表、全文字段搜索、排序、多选、批量校验，以及对选中记录或全部记录的指定字段进行批量设置、追加或清空。
• Excel/XML 导入：支持已有元信息的批量导入、预览和字段映射，并可选择处理未知字段。
• 数据导出：支持记录 XML、Excel、CSV 和独立 Schema XML 导出。
• 大模型辅助：支持 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini，可依据当前项目信息和当前 Schema 进行单条元信息识别、批量新增元信息识别，以及 Schema 生成或扩展。
• 人工复核：大模型识别结果不会自动写入项目，用户可逐字段检查、应用当前记录或在确认后批量应用。
• 任务控制：大模型运行时显示处理状态和进度，防止重复启动，并提供停止功能；远程接口错误会显示相应提示。
• 数据校验与项目保存：支持 Schema 和记录校验，项目统一保存为 UTF-8 XML，并在覆盖已有项目文件前创建备份。
• 本地凭据管理：API Key 只保存在当前操作系统用户的本地凭据文件中，不写入项目 XML，也不写入软件安装目录；可在设置中一键删除全部 API Key。

适用范围
适用于语言资源数据库、单语与多语语料库、平行语料库、可比语料库、学习者语料库、口语语料库以及语料库翻译学项目的元信息规范制定、数据录入、批量整理、迁移和长期维护。

开发者
刘鼎甲 博士
北京外国语大学
电子邮箱：djliu@bfsu.edu.cn

版本：3.3.0
Copyright © 2026 Dingjia LIU. All rights reserved.""",
})

TEXT["en_US"].update({
    "delete_all_keys": "Delete All Keys",
    "confirm_delete_all_keys": "Delete all locally saved API keys for OpenAI, DeepSeek, Qwen, Claude and Gemini? Model names and Base URLs will be kept.",
    "all_keys_deleted": "All API keys have been deleted from the current user's local credentials file.",
    "llm_note": "OpenAI, DeepSeek, Qwen, Claude and Gemini are supported. Model names and Base URLs are stored in per-user settings; API keys are stored separately in the current user's local credentials file. Keys are never written to project XML or the application/install directory, so copying or packaging the application folder does not copy API keys.",
    "provider_privacy_note": "API keys are used only by the current operating-system user to make LLM requests. Reference content is sent to the active provider only when the user explicitly starts an extraction or schema-design task.",
    "batch_ai_help_new": "Batch extraction creates new metadata by default: every reference file is treated as one pending new record. Files are not matched against existing project records. Results remain in the review window until the user explicitly applies them.",
    "batch_new_records_and_sources": "Pending New Metadata and Reference Files",
    "new_metadata_record": "Pending New Record",
    "new_record_number": "New Record {number}",
    "remove_selected_batch_sources": "Remove Selected Sources",
    "clear_all_batch_sources": "Clear Unapplied Sources",
    "confirm_clear_batch_sources": "Clear {count} unapplied batch task(s)?",
    "batch_waiting_files": "Add reference files first; each file creates one pending new metadata record by default.",
    "batch_new_files_added": "Added {count} reference file(s); {total} pending new record(s) in total.",
    "batch_ready_count": "{count} pending new record(s).",
    "batch_ai_need_new_files": "Add at least one reference file first. Batch extraction defaults to one reference file → one new metadata record.",
    "batch_progress_new": "Extracting {current} / {total}: {file}",
    "batch_failed_file": "Extraction failed for “{file}”.",
    "batch_done_new": "Batch extraction completed: {success} succeeded, {failed} failed. Review field suggestions before applying them.",
    "apply_current_result_new": "Apply Current New Record",
    "apply_all_batch_results_new": "Apply All New Records",
    "confirm_apply_all_batch_new": "Write the remaining suggestions for {count} batch result(s) to the current project as new metadata records?",
    "batch_apply_done_new": "Added/updated {records} record(s) and applied {fields} field(s).",
    "batch_apply_note": "Batch results are not written to the project until you click an Apply button.",
    "guide_subtitle": "Metadata schema design, entry, batch management and LLM assistance for linguistic and corpus projects",
    "guide_text": """BFSU MetadataLens User Guide

1. Getting started
BFSU MetadataLens is used to design corpus metadata schemas, enter and maintain metadata records, batch-import existing data, and optionally use LLMs to assist metadata extraction. The first launch uses English by default. Use the Language menu to switch to Chinese; the program remembers the language selected by the current user for later launches.

A recommended workflow is:
1) Create a project.
2) Choose a system template, a user template, or a blank schema.
3) Review and complete Metadata Schema Design.
4) Enter new records manually or import existing Excel/XML metadata.
5) Use single-record or batch LLM extraction when needed.
6) Review, search and batch-edit records in Records Table.
7) Validate the schema and records.
8) Save the project and export XML, Excel or CSV as required.

2. Creating a project and choosing a template
Choose File → New Project or the New button on the toolbar. Enter a project name and select a template.

Templates are separated into:
• System templates: bundled with the application, read-only, and cannot be overwritten or deleted.
• User templates: saved by the user in the current operating-system user's configuration directory and reusable across projects.
• Blank schema: starts with no fields and is suitable for a completely custom project.

Bundled system templates cover monolingual, bilingual parallel, multilingual parallel, multiple-translations, comparable, learner and spoken corpora. When a project is created from a system template, the schema is copied into the project, so editing project fields never changes the original system template.

3. Designing the metadata schema
Open Metadata Schema Design and decide which information the project needs to record. Each field can define:
• Field ID: the stable internal identifier used by the project.
• Chinese and English labels.
• XML tag.
• Data type: string, integer, float, date, year, boolean, enum, long text, language code or file path.
• Metadata level: corpus, subcorpus, text, version, file, speaker, segment, alignment, relation or project.
• Parent and display order.
• Required, repeatable, visible, editable and sensitive flags.
• Default value.
• Controlled vocabulary.
• Regular-expression validation.
• Example.
• Chinese and English descriptions.

Select a field and read Format Hint. For example, year expects a four-digit year, date recommends YYYY-MM-DD, and language_code recommends forms such as zh, en or zh-CN. Repeatable fields may contain multiple values separated by semicolons.

After changing field properties, click Apply Field Changes. When the schema is ready, run Validate Current Schema before entering large amounts of data. Resolve duplicate field IDs, invalid data types, empty XML tags and incomplete controlled vocabularies first.

4. Entering metadata manually
Open Metadata Entry and click New Record. The form is generated automatically from the active schema.

During entry:
• Fields marked * are required.
• Enum fields should use values from the controlled vocabulary.
• Follow the format hints for dates, years and language codes.
• Use semicolons for repeated values where appropriate.
• Long-text fields can contain abstracts, notes or descriptive text.

After clicking Save Current Record, the button changes to Saved. Editing any value changes the button back to Save Current Record, indicating that the form contains unsaved changes. Use Previous and Next to move between records.

5. Records Table and batch field editing
Records Table is the central place for managing all records in the project. It supports:
• Searching record_id, title, author or any field.
• Sorting by a selected field in ascending or descending order.
• Multiple selection.
• Editing, copying, deleting and validating records.
• Double-clicking a record to open it in Metadata Entry.
• Batch editing one field across selected records or all records.

For Batch Edit Field, choose the target records and schema field, then select an operation:
• Set / Replace: replace the field with a new value.
• Append: add a value to the existing value.
• Clear: remove the existing field value.

Always review the preview before applying the batch change.

6. Importing Excel metadata
Choose Import Excel. The first worksheet row is treated as column headers. MetadataLens attempts to match each column to the active schema by field_id, XML tag, Chinese label or English label.

Review the Field Mapping dialog:
• Keep mappings that are correct.
• Ignore columns that are not needed.
• Add unknown columns to the current schema only when they are genuinely part of the project's metadata specification.

For predictable data quality, complete the schema before large imports. After importing, inspect sample records in Records Table and run validation.

7. Importing XML metadata
Choose Import XML. MetadataLens scans XML tags and proposes mappings to the active schema. A complete MetadataLens project XML can be read as a project structure; more general XML is imported through tag mapping.

Check whether the current schema and the source XML represent the same metadata concepts. Add unknown XML tags to the schema only when they belong to the intended specification.

8. LLM provider settings and API keys
Open LLM Provider Settings to configure OpenAI, DeepSeek, Qwen, Claude and Gemini. Each provider has its own API key, Base URL and model name. Choose the active provider from the provider selector.

API-key rules:
• API keys are stored only in the current operating-system user's local configuration directory.
• API keys are not written to project XML.
• API keys are not written to source code or the application/install directory.
• Copying, zipping or moving the application folder does not copy API keys.
• Model names and Base URLs are stored separately from API keys.
• Use Delete All Keys to remove all locally stored provider API keys at once.

Reference content is sent to a provider only when the user explicitly starts an LLM task.

9. Single-record AI metadata extraction
When AI Metadata Extraction is used for an existing record, the request includes:
• The current project name, corpus type and project context.
• The current schema name, version and complete field definitions.
• Existing values in the current record.
• The selected file, PDF, image, webpage or pasted text.

The model is constrained to fields already defined in the active schema. After extraction, review the suggested value, confidence and evidence for each field, then apply selected fields or all fields. Extra fields returned by the model do not automatically modify the schema.

While a task is running, Start is disabled and processing status is shown. Use Stop to terminate processing. Authentication, quota, model-name, network, timeout and remote-server failures are reported to the user.

10. Batch AI extraction for new metadata
Batch AI Extraction creates new records by default. You do not need to create empty records beforehand, and reference files are not matched against existing project records.

Steps:
1) Open Batch AI Extraction.
2) Click Add Reference Files.
3) Each reference file becomes one pending new metadata record by default.
4) Click Start Batch Extraction.
5) Follow file status in the left-hand list.
6) Review each suggested field, confidence and evidence in the right-hand panel.
7) Apply only selected fields for the current pending record, if desired.
8) Apply all suggestions for the current pending record, or
9) Confirm Apply All New Records to write the whole reviewed batch.

Until an Apply button is used, batch results stay only in the review window and are not added to the project. Stop can be used during processing. A failure in one source file does not prevent successful results for other files from being reviewed and applied.

11. AI-assisted schema design
AI-assisted Schema Design can generate a new schema or extend the current schema. Describe the corpus type, research purpose, metadata levels and field requirements, and optionally provide a sample file or text.

The generated fields are presented for review before application. Check field IDs, labels, data types, levels, controlled vocabularies and descriptions carefully. Generating a new schema replaces the active schema and should be used cautiously; extending the schema is appropriate for adding fields to an established specification.

12. Validation, saving and export
Recommended validation points are:
• After completing schema design.
• After a batch import.
• After substantial manual entry.
• Before export or project delivery.

Projects are saved as unified UTF-8 XML containing project_info, schema, records and relations. Existing project files are automatically backed up before overwrite.

Available exports include:
• Records XML.
• Excel.
• CSV.
• Current Schema XML.

To continue work on another computer, copy the project XML and any user templates you need. API keys do not travel with the application or project file and must be configured again on the new computer.""",
    "about_subtitle": "Metadata schema design, entry and management for linguistics and corpus construction",
    "about_text": """BFSU MetadataLens is a metadata specification, entry and management tool for linguistic research, corpus construction, language-resource databases and corpus-based translation studies.

Core functions
• Metadata schema design: create and maintain field IDs, Chinese/English labels, XML tags, data types, metadata levels, required/repeatable flags, default values, controlled vocabularies, descriptions, examples and validation rules.
• Corpus templates: bundled system templates for monolingual, bilingual parallel, multilingual parallel, multiple-translations, comparable, learner and spoken corpora, plus a separate user-template library.
• Metadata entry: forms generated from the active schema, with record creation, editing, saving, copying, deletion and validation.
• Record management: Records Table with full-field search, sorting, multiple selection, batch validation and batch set/append/clear operations for a selected field across selected or all records.
• Excel/XML import: batch import of existing metadata with preview and field mapping, including optional handling of unknown fields.
• Data export: records XML, Excel, CSV and standalone Schema XML.
• LLM assistance: OpenAI, DeepSeek, Qwen, Claude and Gemini for project/schema-constrained single-record extraction, batch extraction that creates new metadata records, and schema generation or extension.
• Human review: LLM output is never written automatically. Users can review individual fields, apply a current record, or confirm an entire batch.
• Task control: LLM operations show status/progress, prevent duplicate starts and provide Stop; remote provider errors are reported to the user.
• Validation and project persistence: schema and record validation, unified UTF-8 XML project files, and automatic backup before overwriting an existing project.
• Local credential management: API keys are stored only in the current operating-system user's local credentials file, never in project XML or the application/install directory, and can be deleted together from Provider Settings.

Typical use
BFSU MetadataLens supports metadata specification, entry, batch organization, migration and long-term maintenance for language-resource databases, monolingual and multilingual corpora, parallel and comparable corpora, learner corpora, spoken corpora and corpus-based translation studies.

Developer
Dr. Dingjia LIU
Beijing Foreign Studies University
Email: djliu@bfsu.edu.cn

Version: 3.3.0
Copyright © 2026 Dingjia LIU. All rights reserved.""",
})


# v3.5 window-state stability, safe child-dialog restoration, and prior v3.4 workflow refinements.
TEXT["zh_CN"].update({
    "schema_name": "规范名称",
    "apply_schema_info": "应用规范信息",
    "schema_name_required": "规范名称不能为空。",
    "schema_info_saved": "规范信息已更新：{name}（版本 {version}）。",
    "apply_selected_template": "导入所选模板规范",
    "select_template_to_apply": "请先在“系统默认模板”或“用户模板”中选择一个模板。",
    "selected_template_summary": "已选择：{name} · 类型：{corpus} · {fields} 个字段",
    "select_template_first": "请先选择一个模板。",
    "apply_template_schema_confirm": "将把模板“{name}”的元信息规范复制到当前项目，并替换当前规范。已有记录不会被删除，但不在新规范中的旧字段值可能成为未定义字段。是否继续？",
    "template_applied": "已将模板“{name}”的规范导入当前项目。系统模板文件本身没有被修改。",
    "close": "关闭",
    "batch_import_urls_text": "从文本导入 URL 列表",
    "url_list_text_files": "URL 列表文本",
    "no_urls_found": "所选文本中没有找到 http:// 或 https:// URL。请检查文件内容。",
    "batch_urls_added": "已从文本加入 {count} 个 URL；当前共有 {total} 条待新增元信息。",
    "batch_waiting_files_or_urls": "请添加参考文件，或从文本导入 URL 列表；每个文件或 URL 默认生成一条新的元信息记录。",
    "batch_ai_need_new_sources": "请先添加至少一个参考文件或 URL。批量识别默认按“一个来源 → 一条新增元信息记录”处理。",
    "waiting_for_source": "等待来源",
    "reference_sources": "参考来源",
    "batch_new_records_and_sources": "待新增元信息与参考来源",
    "batch_failed_file": "参考来源“{file}”识别失败。",
    "batch_ai_help_new": "批量识别默认用于新增元信息：每个参考文件或 URL 都作为一条待新增记录独立识别，不与当前项目已有记录匹配。URL 可通过文本文件批量导入。识别结果先进入人工复核区，只有点击应用后才写入项目。",
    "guide_text": """BFSU MetadataLens 使用说明

一、开始一个新的元信息项目
1. 打开软件后，选择“文件 → 新建项目”或顶部“新建”。
2. 输入项目名称。
3. 选择系统默认模板、用户模板，或者建立空白规范。
4. 系统模板是只读模板。使用系统模板创建项目时，软件会把模板规范复制到当前项目中，因此后续修改不会改变软件自带模板。
5. 项目建立后建议先进入“元信息规范设计”，确认规范名称、字段及格式，再开始条目录入。

二、使用模板库
1. 在“元信息规范设计”页面点击“模板库”。
2. “系统默认模板”和“用户模板”分别显示。
3. 选中某个模板后，点击“导入所选模板规范”，可把该模板的规范复制到当前项目并替换当前规范。
4. 导入模板不会删除已有记录，但如果新规范不包含原记录中的某些旧字段，这些旧值可能变成未定义字段，因此有已有数据时请先保存项目。
5. 用户模板可以删除；系统默认模板不能覆盖或删除。

三、命名和编辑元信息规范
1. “元信息规范设计”顶部可直接填写“规范名称”和“规范版本”。
2. 修改后点击“应用规范信息”。即使最初使用系统模板，之后删除字段、重新设计字段，也可以把规范重新命名。
3. 在字段表中选择字段后，可修改字段 ID、中英文名称、XML 标签、数据类型、层级、父级、顺序、必填/可重复、默认值、受控词表、显示、可编辑、敏感字段、说明、示例和正则校验规则。
4. 修改字段后点击“应用字段修改”。
5. “格式提示”会根据数据类型、示例、正则规则和可重复状态提示推荐录入格式。
6. 完成设计后建议点击“校验当前规范”。

四、手工录入元信息
1. 点击“新建记录”建立一条空白记录。
2. “条目录入”页面会根据当前规范自动生成录入控件。
3. 带 * 的字段为必填字段；可重复字段可按提示输入多个值。
4. 点击“保存当前记录”后，按钮会显示“已保存”。
5. 再次修改任意字段后，按钮会恢复为“保存当前记录”，提醒当前表单有尚未保存的修改。
6. 可使用“上一条 / 下一条”连续检查记录。

五、记录总表与批量修改
1. “记录总表”可以按任意字段搜索、排序和多选记录。
2. 双击记录可进入条目录入页面继续编辑。
3. 可复制、删除或校验选中的记录。
4. “批量修改字段”允许对选中的记录或全部记录统一处理某一个字段。
5. 批量修改支持“设置/替换”“追加”“清空”，应用前会先显示预览。

六、导入既有 Excel 或 XML 元信息
1. 进入“导入 / 导出”，选择“导入 Excel”或“导入 XML”。
2. 软件先显示来源字段/标签，并尝试自动匹配当前规范字段。
3. 请检查字段映射；不需要的来源字段可不映射。
4. 如确实需要，也可把未知字段加入当前规范。
5. 完成导入后建议检查记录数量并执行校验。

七、大模型接口设置
1. 打开“大模型接口设置”。
2. 可分别配置 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini。
3. 每个服务商可填写 API Key、API Base URL 和模型名称，并选择当前使用的服务商。
4. API Key 只保存在当前电脑当前用户的本地凭据文件中，不写入项目 XML，也不写入软件安装目录。复制软件文件夹到另一台电脑不会带走 API Key。
5. 点击“删除所有 Key”可一次清除本机保存的全部大模型 API Key，而保留模型名称和 Base URL。

八、单条大模型识别元信息
1. 先建立或选择一条记录。
2. 点击“大模型识别元信息”。
3. 可选择参考文件、输入网页 URL 或粘贴文本。
4. 识别请求会同时参考当前项目的信息、当前规范及其完整字段定义、当前记录已有值。
5. 处理时会显示状态/进度，“开始”按钮会暂时禁用，并可点击“停止”。
6. 识别完成后逐项检查建议值、置信度和证据，再选择应用部分字段或全部字段。
7. 大模型返回的非当前规范字段不会直接写入当前记录。

九、批量大模型识别并新增元信息
批量识别默认用于“新增记录”，不要求先建立空记录，也不会把来源自动匹配到项目已有记录。

方法 A：批量添加本地文件
1. 打开“批量大模型识别元信息”。
2. 点击“批量添加参考文件”，一次选择多个文件。
3. 每个文件默认对应一条待新增元信息记录。

方法 B：从文本批量导入 URL
1. 准备 TXT、MD、CSV 或 TSV 文本，其中可以每行一个 URL，也可以在普通文本中包含 URL。
2. 点击“从文本导入 URL 列表”。
3. 软件提取其中唯一的 http:// 和 https:// 地址；每个 URL 默认对应一条待新增元信息记录。

开始识别后：
1. 左侧查看每个来源的状态。
2. 右侧逐条查看当前规范字段、建议值、置信度和证据。
3. 可只应用当前记录的选中字段，也可应用当前记录全部建议。
4. 确认无误后，也可“一键应用全部新增记录”。
5. 在点击“应用”之前，批量结果只保留在复核窗口中，不会写入项目。
6. 个别来源识别失败不会阻止其它成功结果继续复核和应用。

十、大模型辅助设计规范
1. 打开“大模型辅助设计规范”。
2. 选择“生成新规范”或“扩展当前规范”。
3. 描述语料库类型、研究目的、元信息层级、希望记录的字段及受控词表等要求。
4. 可附加参考文件、网页 URL 或示例文本。
5. 生成结果会先显示供人工检查，不会自动替换当前规范。
6. 应用前重点检查字段 ID、名称、类型、层级、受控词表和说明。

十一、保存、校验与导出
1. 建议在完成规范设计、批量导入、批量 AI 识别以及大量人工修改后执行校验。
2. 项目保存为统一 UTF-8 XML，包含项目信息、规范、记录和关系信息。
3. 覆盖已有项目文件前会自动建立备份。
4. 可导出记录 XML、Excel、CSV，也可以单独导出当前规范 XML。
5. 换电脑继续工作时，复制项目 XML 和需要的用户模板即可；API Key 需要在新电脑重新配置。""",
    "about_text": """BFSU MetadataLens 是面向语言学研究、语料库建设、语言资源数据库和语料库翻译研究的元信息规范设计、录入与管理工具。

主要功能
• 元信息规范设计：可建立和维护字段 ID、中英文名称、XML 标签、数据类型、元信息层级、必填/可重复属性、默认值、受控词表、说明、示例和校验规则，并可自由命名当前规范。
• 语料库模板：提供单语、双语平行、多语平行、一本多译、可比、学习者和口语语料库系统模板，并支持独立的用户模板库。模板库中的任意选中模板均可复制其规范到当前项目。
• 元信息条目录入：依据当前规范动态生成表单，支持记录新建、编辑、保存、复制、删除和校验。
• 记录管理与批量修改：支持全字段搜索、排序、多选，以及对选中或全部记录的指定字段进行统一设置、追加或清空。
• Excel/XML 导入：支持已有元信息批量导入、预览和字段映射。
• 数据与规范导出：支持记录 XML、Excel、CSV 和独立 Schema XML 导出。
• 大模型辅助：支持 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini，可依据当前项目与当前规范进行单条元信息识别、批量新增元信息识别，以及规范生成或扩展。
• 批量参考来源：批量 AI 可一次添加多个本地文件，也可从 TXT、MD、CSV 或 TSV 文本中导入 URL 列表，每个文件或 URL 默认作为一条待新增元信息记录。
• 人工复核：大模型结果不会自动写入项目，可逐字段、逐记录检查后应用，也可在确认后应用整个批次。
• 项目保存与校验：项目统一保存为 UTF-8 XML，可对规范和记录执行校验，并在覆盖已有项目文件前自动备份。
• 本地凭据：API Key 仅保存在当前操作系统用户的本地凭据文件中，不进入项目 XML 或软件安装目录，并可在大模型设置中一次清除全部 Key。

开发者
刘鼎甲 博士 / Dr. Dingjia LIU
北京外国语大学 / Beijing Foreign Studies University
Email: djliu@bfsu.edu.cn

版本：3.5.2
Copyright © 2026 Dingjia LIU. All rights reserved.""",
})

TEXT["en_US"].update({
    "schema_name": "Schema Name",
    "apply_schema_info": "Apply Schema Info",
    "schema_name_required": "Schema name cannot be empty.",
    "schema_info_saved": "Schema information updated: {name} (version {version}).",
    "apply_selected_template": "Import Selected Template Schema",
    "select_template_to_apply": "Select a template under System Templates or User Templates first.",
    "selected_template_summary": "Selected: {name} · Type: {corpus} · {fields} fields",
    "select_template_first": "Please select a template first.",
    "apply_template_schema_confirm": "The metadata schema from template “{name}” will be copied into the current project and replace the active schema. Existing records will not be deleted, but values for fields absent from the new schema may become undefined. Continue?",
    "template_applied": "The schema from template “{name}” has been imported into the current project. The template file itself was not modified.",
    "close": "Close",
    "batch_import_urls_text": "Import URL List from Text",
    "url_list_text_files": "URL List Text Files",
    "no_urls_found": "No http:// or https:// URLs were found in the selected text. Please check the file contents.",
    "batch_urls_added": "Added {count} URL(s) from text; {total} pending new metadata record(s) are now listed.",
    "batch_waiting_files_or_urls": "Add reference files or import a URL list from text. Each file or URL creates one pending new metadata record by default.",
    "batch_ai_need_new_sources": "Add at least one reference file or URL first. Batch extraction uses one source → one new metadata record by default.",
    "waiting_for_source": "Waiting for Source",
    "reference_sources": "Reference Source(s)",
    "batch_new_records_and_sources": "Pending New Metadata and Reference Sources",
    "batch_failed_file": "Reference source “{file}” failed.",
    "batch_ai_help_new": "Batch extraction creates new metadata by default: each reference file or URL is processed as an independent pending record and is not matched to existing project records. URLs can be imported in bulk from a text file. Results stay in the review area until you explicitly apply them.",
    "guide_text": """BFSU MetadataLens User Guide

1. Start a new metadata project
1) Choose File → New Project or the New button.
2) Enter a project name.
3) Choose a bundled system template, a user template, or a blank schema.
4) System templates are read-only. When a project is created from one, MetadataLens copies its schema into the project, so later editing never changes the bundled template.
5) After creating the project, open Metadata Schema Design and check the schema name, fields and formats before entering records.

2. Use the Template Library
1) Open Metadata Schema Design and click Template Library.
2) System Templates and User Templates are shown separately.
3) Select any template and click Import Selected Template Schema to copy its schema into the current project and replace the active schema.
4) Importing a template does not delete existing records. If the new schema does not contain some old fields, their existing values may become undefined, so save the project first when it already contains data.
5) User templates can be deleted; bundled system templates cannot be overwritten or deleted.

3. Name and edit a metadata schema
1) At the top of Metadata Schema Design, edit Schema Name and Schema Version.
2) Click Apply Schema Info. A schema can be renamed even if the project originally came from a system template or its fields have since been deleted and rebuilt.
3) Select a field to edit its field ID, bilingual labels, XML tag, data type, level, parent, order, required/repeatable flags, default value, controlled vocabulary, visibility, editability, sensitive flag, descriptions, example and regular-expression validation rule.
4) Click Apply Field Changes after editing a field.
5) Format Hint explains expected input according to data type, example, validation rule and repeatability.
6) Validate the schema after major changes.

4. Enter metadata manually
1) Click New Record.
2) Metadata Entry generates controls from the active schema.
3) Fields marked * are required; repeatable fields accept multiple values according to the on-screen hint.
4) Click Save Current Record. The button changes to Saved.
5) If any value is edited again, the button returns to Save Current Record so unsaved form changes are visible.
6) Use Previous / Next to review records sequentially.

5. Records Table and batch field editing
1) Records Table supports full-field search, sorting and multiple selection.
2) Double-click a record to continue editing it in Metadata Entry.
3) Selected records can be copied, deleted or validated.
4) Batch Edit Field can modify one schema field across selected records or all records.
5) Available batch operations are Set/Replace, Append and Clear, with a preview before application.

6. Import existing Excel or XML metadata
1) Open Import / Export and choose Import Excel or Import XML.
2) MetadataLens previews source columns/tags and suggests mappings to the active schema.
3) Review the mapping; source fields you do not need can remain unmapped.
4) Unknown fields can optionally be added to the active schema.
5) After import, check the record count and run validation.

7. Configure LLM providers
1) Open Provider Settings.
2) OpenAI, DeepSeek, Qwen, Claude and Gemini are configured separately.
3) Enter an API Key, API Base URL and model for each provider and choose the active provider.
4) API keys are stored only in the current operating-system user's local credentials file. They are not written to project XML or the application/install directory, so copying the application folder to another computer does not copy the keys.
5) Delete All Keys removes all locally stored provider keys while keeping model names and Base URLs.

8. Extract metadata for one record with an LLM
1) Create or select a record.
2) Open LLM Metadata Extraction.
3) Choose a reference file, enter a webpage URL, or paste text.
4) The request is constrained by the active project information, complete active schema, and existing values of the current record.
5) During processing, status/progress is shown, Start is disabled, and Stop is available.
6) Review suggested values, confidence and evidence, then apply selected fields or all suggestions.
7) Fields not present in the active schema are not written directly into the record.

9. Batch LLM extraction for new metadata records
Batch extraction creates new records by default. You do not need to create empty records first, and sources are not matched to existing project records.

Method A — add local files
1) Open Batch AI Metadata Extraction.
2) Click Add Reference Files and select multiple files.
3) Each file becomes one pending new metadata record by default.

Method B — import URLs from a text file
1) Prepare a TXT, MD, CSV or TSV file. It may contain one URL per line or URLs embedded in ordinary text.
2) Click Import URL List from Text.
3) MetadataLens extracts unique http:// and https:// addresses. Each URL becomes one pending new metadata record.

After starting extraction:
1) Follow the status of each source in the left list.
2) Review schema field, suggested value, confidence and evidence on the right.
3) Apply selected fields for the current pending record, or apply all suggestions for that record.
4) After review, use Apply All New Records if you want to commit the whole batch.
5) Until an Apply button is used, batch results remain only in the review window and are not written to the project.
6) Failure of one source does not prevent successful sources from being reviewed and applied.

10. AI-assisted schema design
1) Open AI-assisted Schema Design.
2) Choose Generate New Schema or Extend Current Schema.
3) Describe corpus type, research purpose, metadata levels, desired fields and controlled vocabularies.
4) Optionally attach a reference file, webpage URL or sample text.
5) Generated fields are shown for review before application and do not automatically replace the active schema.
6) Check field IDs, labels, types, levels, controlled vocabularies and descriptions before applying them.

11. Validation, saving and export
1) Validate after schema design, batch import, batch AI extraction, or substantial manual editing.
2) Projects are saved as unified UTF-8 XML containing project information, schema, records and relations.
3) An existing project file is backed up before overwrite.
4) Records can be exported as XML, Excel or CSV; the active schema can be exported separately as Schema XML.
5) To continue on another computer, copy the project XML and any user templates you need. API keys must be configured again on the new computer.""",
    "about_text": """BFSU MetadataLens is a metadata specification, entry and management tool for linguistic research, corpus construction, language-resource databases and corpus-based translation studies.

Core functions
• Metadata schema design: create and maintain field IDs, bilingual labels, XML tags, data types, metadata levels, required/repeatable flags, default values, controlled vocabularies, descriptions, examples and validation rules, with an editable schema name and version.
• Corpus templates: bundled system templates for monolingual, bilingual parallel, multilingual parallel, multiple-translations, comparable, learner and spoken corpora, plus a separate user-template library. The schema from any selected template can be copied into the active project.
• Metadata entry: forms generated from the active schema, with record creation, editing, saving, copying, deletion and validation.
• Record management and batch editing: full-field search, sorting, multiple selection, and set/replace, append or clear operations for one chosen schema field across selected or all records.
• Excel/XML import: batch import of existing metadata with preview and field mapping.
• Data and schema export: Records XML, Excel, CSV and standalone Schema XML.
• LLM assistance: OpenAI, DeepSeek, Qwen, Claude and Gemini for project/schema-constrained single-record extraction, batch extraction that creates new metadata records, and schema generation or extension.
• Batch reference sources: Batch AI can add multiple local files or import a URL list from TXT, MD, CSV or TSV text; each file or URL becomes one pending new metadata record by default.
• Human review: LLM output is not written automatically. Users can review individual fields, apply a current pending record, or confirm an entire batch.
• Project persistence and validation: unified UTF-8 XML project files, schema/record validation, and automatic backup before overwriting an existing project.
• Local credentials: API keys are stored only in the current operating-system user's local credentials file, never in project XML or the application/install directory, and all keys can be cleared from Provider Settings.

Developer
Dr. Dingjia LIU
Beijing Foreign Studies University
Email: djliu@bfsu.edu.cn

Version: 3.5.2
Copyright © 2026 Dingjia LIU. All rights reserved.""",
})

# v3.5.5 window-shell stability revision.  Keep the visible About text language-specific.
TEXT["zh_CN"].update({
    "about_text": """BFSU MetadataLens 是面向语言学研究、语料库建设、语言资源数据库和语料库翻译研究的元信息规范设计、录入与管理工具。

主要功能
• 元信息规范设计：建立和维护字段 ID、中英文名称、XML 标签、数据类型、元信息层级、必填/可重复属性、默认值、受控词表、说明、示例和校验规则，并可自由命名当前规范。
• 语料库模板：提供单语、双语平行、多语平行、一本多译、可比、学习者和口语语料库等系统模板，并支持独立的用户模板库。
• 元信息条目录入与记录管理：依据当前规范动态生成录入表单，支持记录新建、编辑、保存、复制、删除、检索、排序、校验和批量字段修改。
• 数据导入与导出：支持 Excel/XML 元信息导入、字段映射，以及记录 XML、Excel、CSV 和独立 Schema XML 导出。
• 大模型辅助：支持 OpenAI、DeepSeek、千问 / Qwen、Claude 和 Gemini，可依据当前项目信息和当前 Schema 进行单条元信息识别、批量新增元信息识别，以及 Schema 生成或扩展。
• 人工复核与处理控制：大模型识别结果在写入项目前可逐字段、逐记录复核；批量任务支持进度、停止和错误提示。
• 项目保存与校验：项目统一保存为 UTF-8 XML，可对规范与记录执行校验，并在覆盖已有项目文件前自动备份。
• 本地凭据：API Key 仅保存在当前操作系统用户的本地凭据文件中，不进入项目 XML 或软件安装目录，并可在大模型设置中一次清除全部 Key。

开发者与软件作者贡献
软件作者：刘鼎甲 博士 / Dr. Dingjia LIU
北京外国语大学 / Beijing Foreign Studies University
Email: djliu@bfsu.edu.cn

BFSU MetadataLens 由软件作者发起、总体设计并主导开发。软件作者负责确定软件定位、核心功能、总体架构、元信息 Schema 工作流、项目 XML 数据组织、模板体系、大模型辅助流程和主要交互逻辑，并直接参与和完成关键代码的开发、功能集成、测试、修订与版本发布。软件的功能取舍、技术判断、质量控制和最终责任均由软件作者承担。

ChatGPT 5.5 在开发过程中作为 AI 辅助开发工具参与，主要用于部分代码草拟、重构建议、问题排查、界面与文档文字整理以及迭代辅助。ChatGPT 5.5 的角色是辅助性的，不替代软件作者对软件的总体设计、关键代码开发、技术决策、测试确认和最终审核。

北外语料库团队
BFSU MetadataLens 是北外语料库工具生态的一部分。
北外语料库团队主页：https://corpus.bfsu.edu.cn/index.htm
BFSUNLP GitHub：https://github.com/bfsunlp
BFSU LexiScope GitHub：https://github.com/bfsunlp/bfsu_lexiscope
BFSU LexiScope 主页：https://corpus.bfsu.edu.cn/index.htm

版本：3.5.5
Copyright © 2026 Dingjia LIU. All rights reserved.""",
})

TEXT["en_US"].update({
    "about_text": """BFSU MetadataLens is a metadata specification, entry and management tool for linguistic research, corpus construction, language-resource databases and corpus-based translation studies.

Core functions
• Metadata schema design: create and maintain field IDs, bilingual labels, XML tags, data types, metadata levels, required/repeatable flags, default values, controlled vocabularies, descriptions, examples and validation rules, with an editable schema name and version.
• Corpus templates: bundled system templates for monolingual, bilingual parallel, multilingual parallel, multiple-translations, comparable, learner and spoken corpora, plus a separate user-template library.
• Metadata entry and record management: dynamic forms generated from the active schema, with record creation, editing, saving, copying, deletion, search, sorting, validation and batch field editing.
• Import and export: Excel/XML metadata import with field mapping; Records XML, Excel, CSV and standalone Schema XML export.
• LLM assistance: OpenAI, DeepSeek, Qwen, Claude and Gemini for project/schema-constrained single-record extraction, batch extraction that creates new metadata records, and schema generation or extension.
• Human review and task control: LLM suggestions can be reviewed field by field and record by record before being written; batch jobs provide progress, Stop and actionable error messages.
• Project persistence and validation: unified UTF-8 XML project files, schema/record validation, and automatic backup before overwriting an existing project.
• Local credentials: API keys are stored only in the current operating-system user's local credentials file, never in project XML or the application/install directory, and all keys can be cleared from Provider Settings.

Developer / software author and development contribution
Author: Dr. Dingjia LIU / 刘鼎甲 博士
Beijing Foreign Studies University
Email: djliu@bfsu.edu.cn

BFSU MetadataLens was initiated, architected and led by the software author. The author determined the product scope, core functions, overall architecture, metadata-schema workflow, project XML organization, template system, LLM-assisted workflow and principal interaction logic, and directly contributed to and implemented key code, feature integration, testing, revision and release work. Functional decisions, technical judgment, quality control and final responsibility remain with the software author.

ChatGPT 5.5 participated as an AI-assisted development tool. Its contribution mainly involved portions of code drafting, refactoring suggestions, debugging assistance, interface/document wording and iterative development support. Its role was assistive and did not replace the software author's overall design, key-code development, technical decisions, testing confirmation or final review.

BFSU Corpus Research Group
BFSU MetadataLens forms part of the broader BFSU corpus-tool ecosystem.
BFSU Corpus Research Group: https://corpus.bfsu.edu.cn/index.htm
BFSUNLP GitHub: https://github.com/bfsunlp
BFSU LexiScope GitHub: https://github.com/bfsunlp/bfsu_lexiscope
BFSU LexiScope homepage: https://corpus.bfsu.edu.cn/index.htm

Version: 3.5.5
Copyright © 2026 Dingjia LIU. All rights reserved.""",
})

class I18N:
    def __init__(self, language: str = "en_US") -> None:
        self.language = language if language in TEXT else "en_US"

    def set_language(self, language: str) -> None:
        if language in TEXT:
            self.language = language

    def t(self, key: str, **kwargs) -> str:
        text = TEXT.get(self.language, {}).get(key) or TEXT["en_US"].get(key) or key
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text
