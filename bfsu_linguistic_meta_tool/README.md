# Linguistic Metadata Tool / 语言学语料库元信息制作工具 v2.0

A cross-platform Python desktop application for creating, editing, importing, exporting and managing metadata for linguistic corpora, corpus construction projects and corpus translation studies.

本工具面向语言学研究者，核心工作流为：**项目文件管理 → 元信息规范 Schema 管理 → 元信息记录 Records 编辑 → Excel/XML 导入 → XML统一保存与导出**。

## 0. Windows Executable Package with GUI / Windows x64 图形界面可执行程序

The Windows x64 executable package with GUI can be downloaded from Baidu Netdisk.

Windows x64 图形界面可执行程序可通过百度网盘下载。

File / 文件名： bfsu_linguistic_meta_tool.zip

Download Link / 下载链接：
https://pan.baidu.com/s/1o_s_IJDF_xEKCuYAjJxfZg

Extraction Code / 提取码： vvmy

## 1. Main Features / 主要功能

- Uses Python 3.10+ and tkinter/ttk only for GUI.
- Separates metadata schema and metadata records.
- Saves the whole project in a unified UTF-8 XML format.
- Supports monolingual, bilingual parallel, multilingual parallel, multiple translations, comparable, learner and spoken corpus scenarios.
- Allows users to create, edit, import and export XML tag specifications.
- Imports existing Excel metadata with field mapping and preview.
- Imports existing XML metadata and maps unknown tags to the current schema.
- Exports records XML, schema XML, records CSV and records Excel.
- Supports Chinese and English interface switching.
- Provides project creation, project opening, project closing, Schema selection and bilingual interface switching.

## 2. Project Structure / 项目结构

```text
linguistic_metadata_tool/
    main.py
    models.py
    controllers.py
    xml_repository.py
    schema_manager.py
    excel_importer.py
    xml_importer.py
    validators.py
    i18n.py
    utils.py
    requirements.txt
    README.md
    views/
        __init__.py
        main_window.py
        schema_editor.py
        record_editor.py
        import_dialogs.py
    examples/
        sample_project.xml
        sample_metadata.xlsx
        monolingual_schema.xml
        bilingual_parallel_schema.xml
        multilingual_parallel_schema.xml
        multiple_translations_schema.xml
        learner_corpus_schema.xml
        spoken_corpus_schema.xml
```

## 3. Installation / 安装依赖

```bash
cd linguistic_metadata_tool
pip install -r requirements.txt
```

`openpyxl is used for Excel import/export; pypdf is used for local PDF text extraction; openai is used for optional AI-assisted metadata and Schema functions. If an optional dependency is missing, the related function will show a clear error message.

## 4. Run / 运行

```bash
python main.py
```

## 5. Typical Workflow / 基本使用流程

### 5.1 Create a Project / 新建项目

Schema files are loaded from the application-level `Schema/` folder at startup. System defaults and user-created Schema XML files should both be kept in this folder so that they appear directly in the new-project dialog.

程序启动时会从应用级 `Schema/` 文件夹读取 Schema。系统默认 Schema 与用户新增 Schema 均应保存在该文件夹中，这样在新建项目时可以直接选用。


1. Open the program.
2. Choose **File → New Project**.
3. Enter project name.
4. Select a Schema from the application-level `Schema/` folder.
5. The program creates a new project based on the selected Schema.

### 5.2 Edit Schema / 编辑元信息规范

1. Choose **Schema → Edit Tag Specification** or click the Schema node on the left project tree.
2. Add, delete, move or edit fields.
3. Each field supports:
   - `field_id`
   - Chinese/English labels
   - XML tag name
   - data type
   - required/repeatable flags
   - default value
   - controlled vocabulary
   - level
   - sensitivity marker
   - regex validation rule
4. Choose **Schema → Validate Current Schema** before importing or exporting records.

### 5.3 Add/Edit Records / 新建和编辑元信息记录

1. Choose **Records → New Record**.
2. The record editor dynamically generates form controls according to the current schema.
3. Required fields are marked with `*`.
4. Enum fields use dropdown boxes.
5. Boolean fields use checkboxes.
6. Long text fields use multi-line text boxes.
7. Click **Save Record** and then **Validate**.

### 5.4 Import Excel Metadata / 导入Excel元信息

1. Choose **File → Import Excel Metadata**.
2. Select an `.xlsx` file.
3. The first row is treated as column headers.
4. The dialog previews up to 100 rows.
5. Open **Mapping** to map Excel columns to schema fields.
6. Unknown columns may be ignored or added to the schema.
7. Import results will be merged into the current project.

### 5.5 Import XML Metadata / 导入XML元信息

1. Choose **File → Import XML Metadata**.
2. Select an XML file.
3. The dialog displays discovered XML tags.
4. Tags can be mapped to current schema fields.
5. Unknown tags can be preserved by adding them to the schema.
6. Complete `metadata_project` XML files are merged with the current project.

### 5.6 Export / 导出

- **File → Export Records XML**: export records only to XML.
- **Schema → Export Schema**: export only the schema as XML.
- **File → Export Records CSV**: export records to CSV.
- **File → Export Records Excel**: export records to Excel.

### 5.7 Close a Project / 关闭项目

Choose **File → Close Project** to close the current project. If the project contains unsaved changes, the program asks whether to save before closing.


### 5.8 AI-assisted Metadata Extraction and Schema Design / 大模型辅助元信息识别与Schema设计

1. Choose **Settings → ChatGPT API Key** to configure the optional API key, model name and API base URL. The key is stored only in the local user settings file and is not written into project XML.
2. In **Record Editor**, click **Upload/Paste Document to Extract Metadata** to extract metadata from text files, PDF files, screenshots/images, pasted text, webpages or HTML files. The extraction is strictly bound to the current project Schema and is applied only after user review.
3. Choose **Schema → AI-generate New Schema** to ask the model to draft a complete new Schema from user requirements and optional sample material. The result is shown as a field table before application.
4. Choose **Schema → AI-extend Current Schema** to ask the model to propose additional fields for the current Schema. Existing field definitions are not replaced unless the user explicitly enables replacement in the dialog.
5. See `docs/LLM_METADATA_PROMPT.md` for the internal JSON input/output contracts for both record extraction and Schema generation.

## 6. Unified XML Format / 统一XML结构

The project XML uses this general structure:

```xml
<metadata_project>
    <project_info>...</project_info>
    <schema>...</schema>
    <records>
        <record record_id="..." record_type="text">
            <field name="title" xml_tag="title">...</field>
        </record>
    </records>
    <relations>
        <relation relation_id="..." relation_type="translation">
            <source_record>...</source_record>
            <target_record>...</target_record>
            <description>...</description>
        </relation>
    </relations>
</metadata_project>
```

The `relations` section is reserved for source-text/translation-text, multilingual, multiple-translation and alignment relationships.

## 7. Notes / 注意事项

- XML files are saved as UTF-8.
- Existing project XML files are backed up automatically before overwrite.
- Large Excel files are imported row by row, while the GUI preview only shows the first 100 rows.
- Field values for repeatable fields can be entered using semicolon-separated values.
- Sensitive fields, such as learner age group or speaker ID, can be marked in the schema.

## 8. Extending the Tool / 扩展建议

The code is intentionally separated into modules:

- `models.py`: pure data models.
- `xml_repository.py`: XML persistence.
- `schema_manager.py`: schema creation/import/export.
- `excel_importer.py`: Excel import/export.
- `xml_importer.py`: XML import and tag mapping.
- `validators.py`: schema and record validation.
- `views/`: tkinter views only.
- `controllers.py`: application workflow and command handling.

This makes it straightforward to add TEI export, corpus-specific templates, batch editing, relation visualization, database storage, or controlled vocabulary management.


## 9. About / 关于

Software Name / 软件名称: Metadata Editing and Management Tool / 元信息制作工具

Version / 版本号: V1.0.0

Developer / 开发者: Dr. Dingjia LIU / 刘鼎甲 博士

Contact / 联系方式: djliu@bfsu.edu.cn

Copyright © 2026 Dingjia LIU. All rights reserved.

ChatGPT 5.5 contributed to the development process by assisting with code generation, feature iteration, interaction logic refinement, and documentation polishing. The overall design, research orientation, functional decisions, testing confirmation, and final responsibility remain with the developer.


## 10. Optional ChatGPT-assisted Metadata Extraction / 可选的大模型元信息自动识别

This updated version adds an optional LLM-assisted metadata extraction workflow. It does not change the main project workflow and does not force users to enable AI functions.

本更新版本增加了一个可选的大模型元信息识别流程，不改变原有主界面和项目工作流，也不会强制用户启用 AI 功能。

### 10.1 Set API Key / 设置 API Key

Open **Settings → ChatGPT API Key** and set:

- API Key
- Model name, default: `gpt-5.4-mini-2026-03-17`
- API Base URL, default: `https://api.openai.com/v1`
- Maximum source text characters

The API key is stored only in a local user settings file and is not written into project XML.

打开 **设置 → ChatGPT API Key**，可设置 API Key、模型名称、API Base URL 和最大文本长度。API Key 仅保存在本机用户设置文件中，不写入项目 XML。

### 10.2 Extract Metadata in Record Editor / 在编辑记录页面识别元信息

After a project is opened and a record is selected or created, open the **Record Editor** tab and click **Upload/Paste Document to Extract Metadata** / **上传/粘贴文档识别元信息**.

Supported inputs:

- Text files: `.txt`, `.md`, `.csv`, `.tsv`, `.json`, `.xml`
- PDF files: `.pdf`
- Screenshot/image files: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tif`, `.tiff`
- HTML files: `.html`, `.htm`
- Pasted text
- Webpage URL: `http://` or `https://`

The extraction is strictly bound to the active project Schema. The model is asked to return JSON only, using only field IDs already defined in the current Schema. The program validates and normalizes the returned JSON before applying it to the current record.

### 10.3 Prompt and JSON Contract / Prompt 与 JSON 输入输出格式

See `docs/LLM_METADATA_PROMPT.md` for the internal prompt contract and JSON input/output examples.
