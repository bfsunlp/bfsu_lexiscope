# BFSU MetadataLens v3.3 Architecture / 架构说明

## 中文

BFSU MetadataLens v3.3 采用数据模型、持久化/导入导出服务、大模型服务和 CustomTkinter 界面分层的结构。核心目标是在保持统一 XML 项目格式和语料库元信息数据模型稳定的同时，让 Schema 设计、具体记录录入、批量处理和大模型辅助相互分工明确。

### 1. 核心模块

- `models.py`：GUI 无关的数据模型，包括 `MetadataSchema`、`MetadataField`、`MetadataRecord`、`MetadataProject` 和关系数据。
- `repository.py`：统一项目 XML 的读取、保存、自动备份以及记录/关系序列化。
- `schema_manager.py`：Schema XML 序列化、反序列化和 Schema 辅助函数。
- `templates.py`：系统模板与用户模板的分离、缓存和只读策略。系统模板永不由正常程序操作覆盖；新建项目时复制 Schema 后再编辑。
- `excel_io.py` / `xml_io.py`：Excel/XML 预览、字段映射、导入与导出。
- `validators.py`：Schema、记录和字段值校验。
- `llm.py`：统一 OpenAI、DeepSeek、Qwen、Claude 和 Gemini 的 Provider 服务层；负责来源读取、项目/Schema 约束 Prompt、单条/批量元信息识别、Schema 生成/扩展、取消检查、返回规范化和错误提示。
- `config.py`：应用名称/版本、用户设置目录、LLM Provider 默认配置、旧默认模型迁移和窗口布局持久化。
- `i18n.py`：中英文界面文案、帮助和 About 产品信息。

### 2. 界面层

- `app.py`：主窗口、CiteLens 风格分组工具栏、项目侧栏、分页工作区、详情面板、状态栏及全部功能窗口；同时实现批量 AI 识别、批量字段修改、进度/停止和人工复核流程。
- `ui/theme.py`：BFSU LexiScope/CiteLens 配色、字体、Treeview 样式和高 DPI 字体换算。
- `ui/components.py`：统一按钮、卡片、标题和 CTkTabview 样式；Provider 非活动页签使用明确的深色文字。
- `ui/dpi.py`：Windows DPI 感知、多显示器窗口定位和弹窗居中。

### 3. 关键设计原则

1. **规范与数据分离**：Schema Design 定义字段和规则，Metadata Entry 只录入具体记录。
2. **模板来源分离**：系统模板只读，用户模板独立保存在用户配置目录。
3. **大型列表优先响应速度**：主界面使用 CustomTkinter，大型 Schema/记录/AI 结果表继续采用统一主题的 `ttk.Treeview`。
4. **LLM 严格项目/Schema 约束**：每次元信息识别都携带项目基本信息、Schema 名称/版本/完整字段定义和当前记录已有值；非 Schema 字段不会被应用。
5. **LLM 网络任务不阻塞主线程**：远程调用在工作线程中运行，UI 显示进度、锁定 Start，并可停止当前任务；停止后旧任务结果被丢弃。
6. **批量 AI 先识别后审核**：批量任务只产生建议结果，用户按字段/记录审核后再写入，也可确认后一键应用剩余结果。
7. **批量字段修改可预览**：对所选/全部记录执行设置、追加或清空前先展示目标值。
8. **统一项目格式**：项目继续以 UTF-8 XML 保存，覆盖已有文件前自动备份。
9. **高 DPI 窗口一致性**：所有应用内弹窗统一图标，并在窗口显示前后重复居中计算，减少高缩放环境下的位置偏移。

---

## English

BFSU MetadataLens v3.3 separates data models, persistence/import-export services, LLM services and the CustomTkinter interface. The architecture preserves the unified XML project format while keeping schema design, record entry, batch processing and optional LLM assistance clearly separated.

### 1. Core modules

- `models.py`: GUI-independent schemas, fields, records, projects and relations.
- `repository.py`: unified XML project loading/saving, automatic backup and serialization.
- `schema_manager.py`: Schema XML serialization/deserialization and helpers.
- `templates.py`: separate system/user template libraries and read-only bundled-template policy.
- `excel_io.py` / `xml_io.py`: preview, mapping, import and export services.
- `validators.py`: schema, record and field-value validation.
- `llm.py`: provider-neutral OpenAI/DeepSeek/Qwen/Claude/Gemini layer for source reading, project/schema-bound prompting, metadata extraction, schema generation/extension, cancellation checks, normalization and friendly error reporting.
- `config.py`: application identity, provider defaults and migration, user settings and persistent layout.
- `i18n.py`: bilingual interface, guide and About product copy.

### 2. Interface layer

- `app.py`: CiteLens-style shell, workflow dialogs, batch AI extraction, batch field editing, progress/stop controls and review/application logic.
- `ui/theme.py`: BFSU LexiScope/CiteLens palette, typography, Treeview theme and high-DPI scaling.
- `ui/components.py`: shared controls and tab styling, including explicit dark text for inactive provider tabs.
- `ui/dpi.py`: DPI awareness, multi-monitor geometry and dialog centering.

### 3. Design principles

1. **Schema and data are separate**: Schema Design defines metadata structure; Metadata Entry edits concrete records.
2. **Template sources are separate**: bundled system templates are read-only; user templates live in a user-writable configuration directory.
3. **Large grids prioritize responsiveness**: CustomTkinter surrounds themed `ttk.Treeview` tables used for large schema/record/AI results.
4. **LLM extraction is project/schema-bound**: every request includes active project information, schema name/version/full field definitions and existing record values; non-schema fields are not applied.
5. **Remote work does not block Tk**: LLM calls run in worker threads with progress/status, Start locking, cancellation checks and stale-result rejection.
6. **Batch AI is review-first**: batch extraction produces suggestions only; users review fields/records before application or confirm application of all remaining results.
7. **Batch field editing is preview-first**: set/append/clear operations show their target result before application.
8. **One portable project format**: UTF-8 XML remains the persistence format, with backup before overwrite.
9. **High-DPI window consistency**: application child windows use native `tkinter.Toplevel` shells with CustomTkinter content. This isolates Windows window-lifecycle behavior from CTkToplevel title-bar redraws while preserving the CiteLens-style UI; dialogs share the application icon and are centered within the owner monitor work area.


## v3.3 Credential Storage / v3.3 凭据存储

API keys are stored only in the per-user `credentials.json` under the operating-system user configuration directory. Ordinary application settings in `settings.json`, project XML files, system/user templates and the application/install directory contain no API keys. Legacy v3.2 local keys are migrated out of `settings.json` on first load.

API Key 仅保存在操作系统当前用户配置目录下的 `credentials.json`。普通 `settings.json`、项目 XML、系统/用户模板以及软件安装目录均不保存 API Key。v3.2 的本地旧配置在首次读取时会自动迁移。

## v3.3 Batch Extraction / v3.3 批量识别

Batch AI extraction defaults to creating new metadata records. Each selected reference file is treated as one pending new record, is processed against the active project and schema, and remains outside the project until the user reviews and applies the result.

批量大模型识别默认创建新增元信息记录。每个参考文件作为一条待新增记录，识别时仍受当前项目和当前 Schema 约束；在用户人工复核并应用之前不会写入项目。
