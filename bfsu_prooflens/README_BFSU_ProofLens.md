# Good News

## 版本更新 / Version Update

本版本推出 **BFSU ProofLens**，面向语料库建设、翻译研究、文献整理和文本数字化场景，提供 OCR 识别、大模型辅助校对、图像—文本对照检查、文件/页面管理和多格式导出等功能。用户可以导入 PDF、图片等材料，使用本地 RapidOCR 完成基础识别，也可以按需启用大模型进行 OCR 辅助识别与文本校对。软件支持逐页查看原图与识别文本，便于发现格式错误、错别字、乱码、段落断裂、错误换行、标点异常等 OCR 后常见问题。

This version introduces **BFSU ProofLens**, a desktop OCR and proofreading tool designed for corpus construction, translation studies, document digitization, and research data preparation. Users can import PDFs and image files, run local OCR through RapidOCR, and optionally use large language models for OCR enhancement and proofreading. The program provides a side-by-side image/text review interface, making it easier to detect formatting problems, typos, garbled characters, paragraph breaks, incorrect line breaks, punctuation errors, and other common OCR issues.

In short, OCR correction used to feel like reading messy output line by line; now, ProofLens helps users recognize, compare, revise, and export cleaner texts with a much smoother workflow.

简单来说，以前 OCR 校对往往像是在一堆乱码、错行和断段中“人工捞文本”；现在 ProofLens 可以帮助用户完成识别、对照、校对、整理和导出，让语料建设和文本数字化工作少一点折磨，多一点顺手。

---

# BFSU ProofLens / 北外 ProofLens OCR 识别与校对工具 v1.0

**BFSU ProofLens** is a Python desktop application for OCR recognition, LLM-assisted proofreading, page-level image/text comparison, and multi-format text export.

**BFSU ProofLens** 是一款面向语言学研究者、语料库建设者、翻译研究者和文本数字化工作者的 Python 桌面软件，核心工作流为：文件导入 → OCR 识别 → 图文对照 → 大模型辅助校对 → 人工修订 → 多格式导出。

---

## 0. Windows Executable Package with GUI / Windows x64 图形界面可执行程序

The Windows x64 executable package with GUI can be downloaded from Baidu Netdisk.

Windows x64 图形界面可执行程序可通过百度网盘下载。

**File / 文件名：** `BFSU_ProofLens.zip`

**Download Link / 下载链接：**

https://pan.baidu.com/s/1PYXgzVg17QT48PWGRNiumA

**Extraction Code / 提取码：** `48td`

---

## 1. Main Features / 主要功能

- Uses Python and tkinter/ttk for the desktop GUI.
- Supports PDF and common image input formats, including `.pdf`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, and `.tiff`.
- Uses **RapidOCR** as the local OCR backend.
- Checks OCR models before recognition and prepares/downloads required models when necessary.
- Supports optional LLM-assisted OCR and proofreading.
- Provides side-by-side page image and recognized text comparison.
- Supports proofreading of OCR problems such as wrong characters, garbled text, layout noise, broken paragraphs, incorrect line breaks, punctuation errors, and formatting problems.
- Supports file-level and page-level management in the file/page list.
- Allows users to select and delete an entire file or individual pages.
- Supports right-click deletion, bottom `+ / -` management buttons, and keyboard `Delete` deletion.
- Supports mouse wheel scrolling in scrollable windows and panels.
- Supports multiple recognition languages, including Simplified Chinese `zh_sim`, Traditional Chinese `zh_tr`, English and other available OCR language options.
- Allows users to manually select language combinations in Settings.
- Exports OCR and proofreading results to multiple formats: `.txt`, `.docx`, `.xlsx`, `.json`, `.xml`, and `.md`.
- Allows users to choose export content, such as OCR text, corrected text, or all available text fields.
- Supports exporting all results into one file or exporting each source file separately.
- When exporting separately, each source file is saved as `source_filename_ocr.ext`.
- Supports Chinese and English interface switching.
- Provides About and developer information pages.

---

## 2. Project Structure / 项目结构

A typical source-code structure is as follows:

```text
bfsu_prooflens/
    main.py
    requirements.txt
    build_exe.bat
    README.md
    assets/
        app.ico
        app.png
    config/
        default_config.json
    models/
        rapidocr/
    src/
        ui_main.py
        ui_settings.py
        rapid_ocr_backend.py
        llm_client.py
        export_utils.py
        i18n.py
        utils.py
        parallel_workers.py
        import_workers.py
```

The exact structure may vary between packaged and source-code versions. In the executable version, users normally only need to run `BFSU_ProofLens.exe`.

---

## 3. Installation from Source / 源码安装依赖

If you run the source-code version, install dependencies first:

```bash
cd bfsu_prooflens
pip install -r requirements.txt
```

Main dependencies may include:

- `rapidocr` for local OCR recognition;
- `onnxruntime` for OCR model inference;
- `pillow` for image processing;
- `pymupdf` / `fitz` for PDF page rendering;
- `python-docx` for Word export;
- `openpyxl` for Excel export;
- `openai` for optional LLM-assisted OCR and proofreading.

RapidOCR models may be prepared automatically when OCR is first used. If model download is required, please make sure the computer can access the relevant model source.

---

## 4. Run / 运行

### 4.1 Run the executable / 运行图形界面程序

Unzip `BFSU_ProofLens.zip`, then double-click:

```text
BFSU_ProofLens.exe
```

### 4.2 Run from source / 从源码运行

```bash
python main.py
```

---

## 5. Typical Workflow / 基本使用流程

### 5.1 Add Files / 添加文件

Open the program and add OCR source files.

Supported input files include:

```text
.pdf, .jpg, .jpeg, .png, .bmp, .webp, .tif, .tiff
```

PDF files are imported by page. Image files are imported as single-page documents.

---

### 5.2 Manage Files and Pages / 管理文件与页面

The file/page list supports both file-level and page-level operations.

Users can:

- select an entire file;
- select one or more pages;
- delete an entire file and all its pages;
- delete selected individual pages;
- use right-click menu operations;
- use the bottom `+` and `-` buttons;
- press the `Delete` key to remove selected files or pages.

When a page is deleted, the program automatically reorders the remaining pages.

---

### 5.3 Configure OCR / 设置 OCR

Open **Settings** to configure OCR-related options.

Users may select recognition languages, such as:

```text
zh_sim    Simplified Chinese / 简体中文
zh_tr     Traditional Chinese / 繁體中文
en        English / 英语
```

Traditional Chinese uses the non-political internal code `zh_tr`. It remains mapped to the appropriate Traditional Chinese OCR model in the backend.

Language combinations can be manually selected in Settings. The software does not need to provide every possible fixed mixed-language preset.

---

### 5.4 Run OCR / 执行 OCR 识别

After files are imported and OCR options are configured, run OCR recognition.

The program will:

1. check whether the required OCR backend is available;
2. check or prepare the relevant OCR model files;
3. show status prompts and progress information when models need to be prepared;
4. recognize the selected pages or files;
5. write OCR results into the page-level text area.

---

### 5.5 Review Image and Text / 图文对照校对

The main proofreading interface displays the original page image and recognized text side by side.

Users can:

- zoom or scroll the page image;
- inspect OCR text line by line;
- manually edit recognition results;
- compare the visual layout with the OCR output;
- correct missing characters, wrong characters, line breaks, paragraph breaks and formatting problems.

---

### 5.6 LLM-assisted OCR and Proofreading / 大模型辅助识别与校对

If the optional LLM function is enabled, users can configure:

- API Key;
- model name;
- API base URL;
- maximum input length or related request parameters.

The LLM can be used to assist with:

- OCR result correction;
- typo detection;
- garbled text repair;
- paragraph and line-break correction;
- punctuation normalization;
- format cleanup;
- proofreading suggestions.

All LLM suggestions should be reviewed by the user before being treated as final text.

---

### 5.7 Export / 导出

ProofLens supports exporting OCR and proofreading results to multiple formats:

```text
TXT   .txt
Word  .docx
Excel .xlsx
JSON  .json
XML   .xml
Markdown .md
```

During export, users can choose the content to export, for example:

- OCR text only;
- corrected/proofread text only;
- all available text fields.

The default option is to export all relevant content.

---

### 5.8 Export Each Source File Separately / 按源文件分别导出

Users can choose to export each source file into a separate output file.

When this option is enabled, the output naming rule is:

```text
source_filename_ocr.ext
```

For example:

```text
sample.pdf       → sample_ocr.docx
sample.jpg       → sample_ocr.txt
archive_page.png → archive_page_ocr.xlsx
```

If duplicated names are detected, the program automatically adds suffixes such as `_2` or `_3` to avoid overwriting files.

---

## 6. Output Data Structure / 输出内容结构

Exported records may include information such as:

```text
source_file      original source file name
page_index       page number
ocr_text         raw OCR result
corrected_text   manually revised or LLM-proofread text
notes            optional proofreading notes or comments
```

The exact fields may vary according to the selected export format and export-content options.

---

## 7. Notes / 注意事项

- OCR quality depends on image resolution, scan quality, font clarity and page layout.
- For best results, use clear scans or high-resolution images.
- Complex layouts, tables, vertical text, watermarks and handwritten text may require additional manual correction.
- The local RapidOCR function can work without using an LLM after the required OCR models are prepared.
- LLM-assisted functions require a valid API key or compatible API endpoint.
- API keys should not be shared publicly.
- OCR and LLM results should always be checked by the user, especially when the output is used for research data, publication, teaching materials or corpus construction.
- XML, JSON and Markdown files are saved in UTF-8 encoding.

---

## 8. PyInstaller Packaging / PyInstaller 打包建议

For Windows packaging, folder mode is recommended because OCR and model-related dependencies are usually more stable in `onedir` mode.

A minimal packaging command can be similar to:

```bat
if exist build rmdir /s /q build & if exist dist rmdir /s /q dist & if exist BFSU_ProofLens.spec del /q BFSU_ProofLens.spec & python -m venv .venv_build_min && .venv_build_min\Scripts\activate && python -m pip install -U pip && python -m pip install pyinstaller && python -m pip install -r requirements.txt && pyinstaller --noconfirm --clean --onedir --windowed --name "BFSU_ProofLens" --icon "assets\app.ico" --add-data "assets;assets" --add-data "config;config" --add-data "models;models" --hidden-import docx --hidden-import openpyxl --hidden-import lxml --hidden-import fitz --hidden-import rapidocr --hidden-import onnxruntime --hidden-import src.parallel_workers --hidden-import src.import_workers main.py
```

The generated executable is usually located at:

```text
dist\BFSU_ProofLens\BFSU_ProofLens.exe
```

---

## 9. Extending the Tool / 扩展建议

The software can be further extended in the following directions:

- batch OCR task queue;
- confidence-based OCR error highlighting;
- layout-aware OCR correction;
- TEI/XML corpus export;
- parallel text alignment after OCR;
- bilingual OCR and translation comparison;
- terminology-aware proofreading;
- corpus metadata integration;
- local LLM support for confidential materials;
- project-level OCR logs and quality reports.

---

## 10. About / 关于

**Software Name / 软件名称：** BFSU ProofLens / 北外 ProofLens OCR 识别与校对工具

**Version / 版本号：** V1.0

**Developer / 开发者：** Dr. Dingjia LIU / 刘鼎甲 博士

**Contact / 联系方式：** djliu@bfsu.edu.cn

Copyright © 2026 Dingjia LIU. All rights reserved.

ChatGPT 5.5 contributed to the development process by assisting with code generation, feature iteration, interaction logic refinement, documentation drafting and polishing. The overall design, research orientation, functional decisions, testing confirmation and final responsibility remain with the developer.

---

## 11. Disclaimer / 免责声明

BFSU ProofLens is designed as a research-support and document-processing tool. OCR and LLM-assisted proofreading results may contain errors and should not be treated as fully automatic final outputs. Users are responsible for checking, revising and confirming the exported text before academic, teaching, publication or corpus use.

BFSU ProofLens 是一款研究辅助与文档处理工具。OCR 识别和大模型辅助校对结果均可能存在错误，不应被视为完全自动生成的最终文本。用户在将结果用于论文写作、教学材料、出版物、语料库建设或其他正式用途前，应自行检查、修订并确认文本内容。
