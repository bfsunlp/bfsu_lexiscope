# BFSU LexiScope / 北外 LexiScope 语料库智能工具箱

**BFSU LexiScope** is a series of intelligent data processing and data analysis tools for corpus-based linguistic research, corpus construction, translation studies, language education research, and digital humanities.

**BFSU LexiScope / 北外 LexiScope** 是一套面向语料库研究的智能数据处理与数据分析系列工具，旨在为语料库建设、元信息整理、OCR 文本数字化、语料清洗、人工智能辅助校对、数据导入导出和后续统计分析提供统一、轻量、可扩展的桌面工具生态。

当前已发布的核心工具包括：

- **BFSU MetaTools / 语言学语料库元信息制作工具**
- **BFSU ProofLens / OCR 识别与校对工具**

更多面向语料库数据处理、统计分析、可视化和智能标注的模块正在规划和开发中，敬请期待。

---

## 0. Project Vision / 项目愿景

BFSU LexiScope aims to provide a practical and research-oriented toolchain for corpus researchers. The project focuses on the full workflow of corpus-based research:

```text
data collection → metadata management → OCR/text digitization → text cleaning
→ corpus organization → annotation → retrieval → statistical analysis → visualization
```

BFSU LexiScope 致力于为语言学、翻译学和语料库研究提供一套从“数据准备”到“数据分析”的工具链。它并不追求成为庞大的通用平台，而是希望围绕研究者的真实工作流程，提供一系列可以直接使用、便于打包、便于扩展、适合教学和科研场景的轻量级工具。

核心目标包括：

- 降低语料库建设中的重复性劳动；
- 提高文本数字化、元信息整理和语料清洗效率；
- 支持大模型辅助的数据处理与人工复核；
- 提供适合语言学研究者使用的图形界面；
- 保持数据格式透明、可导出、可复用；
- 为后续语料检索、标注、统计分析和可视化提供基础。

---

## 1. Current Tools / 当前工具

### 1.1 BFSU MetaTools / 语言学语料库元信息制作工具

**BFSU MetaTools** is a metadata editing and management tool for linguistic corpora. It supports project creation, metadata schema management, record editing, Excel/XML import, XML-based unified storage, multi-format export, and optional LLM-assisted metadata extraction.

**BFSU MetaTools / 语言学语料库元信息制作工具** 面向语言学研究者、语料库建设者和翻译研究者，主要用于创建、编辑、导入、导出和管理语料库元信息。其核心工作流为：

```text
项目文件管理 → 元信息规范 Schema 管理 → 元信息记录 Records 编辑
→ Excel/XML 导入 → XML 统一保存与导出
```

#### Main Features / 主要功能

- 支持单语、双语平行、多语平行、一本多译、可比语料、学习者语料、口语语料等场景；
- 支持自定义元信息 Schema；
- 支持 Excel 元信息导入、字段映射和预览；
- 支持 XML 元信息导入与标签映射；
- 支持记录 XML、Schema XML、CSV、Excel 等格式导出；
- 支持中英文界面切换；
- 支持大模型辅助识别标题、作者、年份、语种、文类等元信息；
- 支持大模型辅助生成或扩展 Schema；
- API Key 仅保存在本地用户设置文件中，不写入项目 XML。

#### Download / 下载

**File / 文件名：** `bfsu_linguistic_meta_tool.zip`

**Download Link / 下载链接：**

https://pan.baidu.com/s/1PO5hpRC0RogPcWPALNEjQw

**Extraction Code / 提取码：** `9kst`

---

### 1.2 BFSU ProofLens / OCR 识别与校对工具

**BFSU ProofLens** is an OCR recognition and proofreading tool for corpus construction, text digitization, document processing, translation studies, and research data preparation. It supports image/PDF import, RapidOCR-based local OCR, LLM-assisted proofreading, page-level image/text comparison, file/page management, and multi-format export.

**BFSU ProofLens / OCR 识别与校对工具** 面向语料库建设、文本数字化、翻译研究、文献整理和研究数据准备，主要用于将 PDF、图片等材料转换为可编辑文本，并通过图文对照和大模型辅助校对提高文本质量。其核心工作流为：

```text
文件导入 → OCR 识别 → 图文对照 → 大模型辅助校对
→ 人工修订 → 多格式导出
```

#### Main Features / 主要功能

- 支持 PDF 和常见图片格式导入；
- 使用 RapidOCR 作为本地 OCR 后端；
- 识别前检查 OCR 模型，并在需要时自动准备或下载模型；
- 支持 OCR 原文与修改后文本的对照处理；
- 支持大模型辅助校对错别字、乱码、段落断裂、错误换行、标点异常和格式问题；
- 支持文件级和页面级管理；
- 支持选中整个文件删除，也支持选中单页删除；
- 支持右键菜单、底部 `+ / -` 按钮和键盘 `Delete` 删除；
- 支持所有主要滚动区域的鼠标中键滚轮滚动；
- 支持简体中文、繁体中文、英语等识别语言设置；
- 繁体中文采用非政治化内部代码 `zh_tr`；
- 支持导出为 TXT、DOCX、XLSX、JSON、XML、Markdown；
- 支持合并导出，也支持按源文件分别导出为 `源文件名_ocr.ext`。

#### Download / 下载

**File / 文件名：** `BFSU_ProofLens.zip`

**Download Link / 下载链接：**

https://pan.baidu.com/s/1PYXgzVg17QT48PWGRNiumA

**Extraction Code / 提取码：** `48td`

---

## 2. Planned Tools / 规划中工具

The following modules are planned or under consideration. They have not yet been fully implemented. Please stay tuned.

以下模块仍在规划或开发中，尚未完整发布，敬请期待。

### 2.1 Corpus Cleaner / 语料清洗工具

Planned functions include:

- 批量文本清洗；
- 编码修复；
- 空行、重复行、异常符号处理；
- 段落重排；
- OCR 噪音清理；
- 正则规则库；
- 清洗前后对比预览；
- 清洗日志导出。

### 2.2 Corpus Segmenter / 分词、分句与基础统计工具

Planned functions include:

- 中英文分词；
- 分句；
- 字数、词数、句数统计；
- 批量文件统计；
- 多语种基础文本指标；
- Excel 日志导出。

### 2.3 Corpus Aligner / 平行语料对齐工具

Planned functions include:

- 双语句对齐；
- 多语平行文本对齐；
- 相似度辅助检查；
- 人工调整对齐结果；
- Excel / XML / TMX 导出。

### 2.4 Corpus Analyzer / 语料库数据分析工具

Planned functions include:

- 高频词统计；
- 关键词分析；
- 搭配分析；
- 词丛 / lexical bundles 提取；
- 分布指标计算；
- 标准化频数；
- 统计检验；
- 可视化图表导出。

### 2.5 Corpus Visualizer / 语料库可视化工具

Planned functions include:

- 频数分布图；
- 堆叠柱状图；
- 热图；
- 对应分析图；
- 聚类图；
- 多维分析结果可视化；
- 适合论文发表的图表导出。

### 2.6 LLM Corpus Assistant / 大模型语料库助手

Planned functions include:

- 语料标注辅助；
- 分类体系生成；
- 标签一致性检查；
- 元信息补全；
- OCR 校对增强；
- 文献与语料说明生成；
- 研究报告草稿生成；
- 人机协同复核流程。

---

## 3. Recommended Workflow / 推荐工作流

A typical BFSU LexiScope workflow may look like this:

```text
1. Use BFSU ProofLens to convert scanned PDFs or images into editable text.
2. Proofread OCR results manually or with LLM assistance.
3. Export clean text files.
4. Use BFSU MetaTools to create metadata schemas and records.
5. Link text files with metadata records.
6. Use future LexiScope modules for cleaning, segmentation, annotation and analysis.
```

典型使用流程可以概括为：

```text
1. 使用 BFSU ProofLens 将扫描版 PDF 或图片转换为可编辑文本；
2. 通过人工或大模型辅助方式校对 OCR 结果；
3. 导出清理后的文本；
4. 使用 BFSU MetaTools 建立语料库元信息规范和记录；
5. 将文本文件与元信息记录关联；
6. 后续使用 LexiScope 系列工具完成清洗、分词、标注、统计和可视化分析。
```

---

## 4. Installation / 安装与运行

For ordinary users, it is recommended to download the Windows executable packages of each tool and run the `.exe` files directly.

普通用户建议直接下载各工具的 Windows 图形界面版本，解压后运行 `.exe` 文件即可。

For source-code users:

```bash
git clone <repository-url>
cd BFSU_lexiscope
pip install -r requirements.txt
```

Then run the target tool, for example:

```bash
python main.py
```

Different tools may have their own dependency files and running instructions. Please refer to the README file inside each tool folder.

不同子工具可能具有各自的依赖文件和运行说明，请以各工具目录下的 README 为准。

---

## 5. Packaging / 打包说明

For Windows distribution, `PyInstaller --onedir` mode is recommended because OCR, document processing and model-related dependencies are usually more stable in folder mode than in single-file mode.

Windows 打包建议使用 PyInstaller 的 `onedir` 文件夹模式。与单文件模式相比，文件夹模式对于 OCR、文档处理、模型文件和本地依赖库更加稳定。

A typical packaging command may look like:

```bat
python -m pip install -U pip
python -m pip install pyinstaller
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --onedir --windowed --name "BFSU_ToolName" --icon "assets\app.ico" main.py
```

Each subtool may require additional `--add-data` and `--hidden-import` options.

---

## 6. Data and Privacy / 数据与隐私

- Local functions run on the user's computer.
- Project files, metadata records and OCR results are saved locally unless the user explicitly exports or uploads them.
- LLM-assisted functions are optional.
- If an API-based LLM is used, the selected text or prompt content may be sent to the configured API endpoint.
- Users should avoid uploading confidential, sensitive or unpublished data to external APIs unless they have permission to do so.
- API Keys should be stored locally and should not be committed to public repositories.

---

## 7. Notes / 注意事项

- BFSU LexiScope is a research-support toolkit, not a fully automatic replacement for expert judgment.
- OCR results, metadata extraction results and LLM suggestions should always be checked by the user.
- Users should verify exported texts before using them in publications, teaching materials, corpus construction or statistical analysis.
- Some functions are still experimental and may change between versions.
- If a function has not yet been released, please treat its description as a development plan rather than a completed feature.

---

## 8. Roadmap / 发展路线

Planned development directions include:

- 完善 OCR 与校对工作流；
- 增强大模型辅助语料处理能力；
- 加入语料清洗和批处理工具；
- 加入分词、分句和基础统计功能；
- 加入平行语料对齐工具；
- 加入词频、关键词、搭配和语块分析；
- 加入论文级图表导出；
- 加入项目级日志和质量报告；
- 逐步形成覆盖“语料准备—语料管理—语料分析”的完整工具链。

---

## 9. About / 关于

**Project Name / 项目名称：** BFSU LexiScope / 北外 LexiScope 语料库智能工具箱

**Full Description / 完整说明：** A series of intelligent data processing and data analysis tools for corpus-based research.

**中文说明：** 面向语料库研究的智能数据处理和数据分析系列工具。

**Developer / 开发者：** Dr. Dingjia LIU / 刘鼎甲 博士

**Contact / 联系方式：** djliu@bfsu.edu.cn

Copyright © 2026 Dingjia LIU. All rights reserved.

ChatGPT 5.5 contributed to the development process by assisting with code generation, feature iteration, interaction logic refinement, README drafting and documentation polishing. The overall design, research orientation, functional decisions, testing confirmation and final responsibility remain with the developer.

---

## 10. Disclaimer / 免责声明

BFSU LexiScope and its subtools are designed for research support, corpus construction and data processing. Automatically generated results, including OCR output, LLM-assisted proofreading, metadata extraction and future statistical reports, may contain errors. Users are responsible for checking, revising and confirming all outputs before using them for academic publication, teaching, corpus release or formal research analysis.

BFSU LexiScope 及其子工具主要用于科研辅助、语料库建设和数据处理。自动生成结果，包括 OCR 文本、大模型辅助校对、元信息抽取以及未来的数据分析报告，均可能存在错误。用户在将相关结果用于论文发表、教学材料、语料库发布或正式研究分析前，应自行检查、修订并确认其准确性。
