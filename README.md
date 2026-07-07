# BFSU LexiScope / 北外 LexiScope 语料库智能工具箱

**BFSU LexiScope** is a series of intelligent data processing and data analysis tools for corpus-based linguistic research, corpus construction, translation studies, language education research, and digital humanities.

**BFSU LexiScope / 北外 LexiScope** 是一套面向语料库研究的智能数据处理与数据分析系列工具，旨在为语料库建设、元信息整理、OCR 文本数字化、多语文本对齐、语料清洗、人工智能辅助校对、数据导入导出和后续统计分析提供统一、轻量、可扩展的桌面工具生态。

当前已发布的核心工具包括：

- **BFSU MetaTools / 语言学语料库元信息制作工具**
- **BFSU ProofLens / OCR 识别与校对工具**
- **BFSU AlignLens / 多语翻译对齐工具**

更多面向语料库数据处理、统计分析、可视化和智能标注的模块正在规划和开发中，敬请期待。

---

## 0. Project Vision / 项目愿景

BFSU LexiScope aims to provide a practical and research-oriented toolchain for corpus researchers. The project focuses on the full workflow of corpus-based research:

```text
data collection → metadata management → OCR/text digitization
→ multilingual text alignment → text cleaning → corpus organization
→ annotation → retrieval → statistical analysis → visualization
```

BFSU LexiScope 致力于为语言学、翻译学和语料库研究提供一套从“数据准备”到“数据分析”的工具链。它并不追求成为庞大的通用平台，而是希望围绕研究者的真实工作流程，提供一系列可以直接使用、便于打包、便于扩展、适合教学和科研场景的轻量级工具。

核心目标包括：

- 降低语料库建设中的重复性劳动；
- 提高文本数字化、元信息整理、多语文本对齐和语料清洗效率；
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

https://pan.baidu.com/s/19u46YGnbivyBOKmSPoYDcw?pwd=ztdx

**Extraction Code / 提取码：** `ztdx`

---

### 1.3 BFSU AlignLens / 多语翻译对齐工具

**BFSU AlignLens** is a multilingual translation alignment tool for multilingual-Chinese parallel corpus construction, corpus-based translation studies, translation teaching, multiple-translation research, and multilingual text data preparation. It supports file-level grouping, paragraph/sentence segmentation, Transformer-based alignment, LLM-assisted alignment and review, editable alignment correction, similarity-based quality checking, project-based persistence, and multi-format export.

**BFSU AlignLens / 多语翻译对齐工具** 面向多语—汉语平行语料库建设、语料库翻译学、翻译教学、一本多译研究和多语文本数据整理，主要用于完成多语文本的导入、分段、分句、自动对齐、人工校对、质量检查和格式化导出。其核心工作流为：

```text
文件导入 → 文件级配组 → 分段/分句 → Transformer 或 LLM 对齐
→ 对齐编辑器校对 → 完成确认 → 多格式导出
```

#### Main Features / 主要功能

- 支持 1 对 1 翻译对齐、一语多译对齐和多语平行文本对齐；
- 支持 TXT、Markdown、RTF、DOCX 等文本来源的导入和整理；
- 支持文件级配组，将同一序号的源语、译语或不同译本组织为独立 `set_xxx` 文件组；
- 支持简体中文、繁体中文、英语、德语、法语、西班牙语、俄语、日语、韩语等多语种分段与分句；
- 支持 Stanza、spaCy、HanLP、标点规则、行规则和自然段规则等分句/分段策略；
- 支持 Transformer 段落对齐和句子对齐；
- 默认采用高准确率 Transformer 配置，包括 LaBSE 与 multilingual-e5-base 双模型融合、full DP 搜索、较严格的低相似度惩罚和高置信度阈值；
- 支持 GPU 加速；在 CUDA 可用时自动使用 GPU，在 GPU 不可用时自动回退 CPU；
- 支持 LLM 段落对齐、LLM 句子对齐和 LLM 对齐检查建议；
- LLM 建议语种可在设置中选择，便于用户以中文、英文或其他支持语种查看问题说明和修改理由；
- 默认 OpenAI 模型为 `gpt-5.4-mini`，同时允许用户手动填写 GPT-5.5 或其他可用模型；
- 提供逐文件组独立的 Alignment Editor，对齐编辑器支持手动插入、删除、移动、合并、拆分、确认和备注；
- 支持低相似度行高亮、相似度重算、上一条/下一条待检查行导航；
- 支持将项目保存为 `.alignlens` 文件，便于后续继续编辑；
- 支持导出 Excel、TXT、TMX、XML、Word、JSON 和多语种多 TXT 文件；
- 支持批量分段、批量分句、批量 Transformer 对齐、批量 LLM 对齐和批量导出。

#### Download / 下载

**File / 文件名：** `BFSU_AlignLens.zip`

**Download Link / 下载链接：**

https://pan.baidu.com/s/1x9EgCOhf8MoRACkhL09Dog

**Extraction Code / 提取码：** `ihjx`

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

### 2.3 Corpus Analyzer / 语料库数据分析工具

Planned functions include:

- 高频词统计；
- 关键词分析；
- 搭配分析；
- 词丛 / lexical bundles 提取；
- 分布指标计算；
- 标准化频数；
- 统计检验；
- 可视化图表导出。

### 2.4 Corpus Visualizer / 语料库可视化工具

Planned functions include:

- 频数分布图；
- 堆叠柱状图；
- 热图；
- 对应分析图；
- 聚类图；
- 多维分析结果可视化；
- 适合论文发表的图表导出。

### 2.5 LLM Corpus Assistant / 大模型语料库助手

Planned functions include:

- 语料标注辅助；
- 分类体系生成；
- 标签一致性检查；
- 元信息补全；
- OCR 校对增强；
- 对齐质量检查；
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
4. Use BFSU AlignLens to segment and align multilingual or translated texts.
5. Export aligned files as Excel, TMX, XML, JSON or line-aligned TXT files.
6. Use BFSU MetaTools to create metadata schemas and records.
7. Link text files or aligned files with metadata records.
8. Use future LexiScope modules for cleaning, annotation, retrieval, statistics and visualization.
```

典型使用流程可以概括为：

```text
1. 使用 BFSU ProofLens 将扫描版 PDF 或图片转换为可编辑文本；
2. 通过人工或大模型辅助方式校对 OCR 结果；
3. 导出清理后的文本；
4. 使用 BFSU AlignLens 对多语文本、翻译文本或一本多译文本进行分段、分句和对齐；
5. 将对齐结果导出为 Excel、TMX、XML、JSON 或按语种行号对齐的 TXT 文件；
6. 使用 BFSU MetaTools 建立语料库元信息规范和记录；
7. 将文本文件或对齐文件与元信息记录关联；
8. 后续使用 LexiScope 系列工具完成清洗、标注、检索、统计和可视化分析。
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

For Windows distribution, `PyInstaller --onedir` mode is recommended because OCR, document processing, alignment and model-related dependencies are usually more stable in folder mode than in single-file mode.

Windows 打包建议使用 PyInstaller 的 `onedir` 文件夹模式。与单文件模式相比，文件夹模式对于 OCR、文档处理、文本对齐、模型文件和本地依赖库更加稳定。

A typical packaging command may look like:

```bat
python -m pip install -U pip
python -m pip install pyinstaller
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --onedir --windowed --name "BFSU_ToolName" --icon "assets\app.ico" main.py
```

Each subtool may require additional `--add-data`, `--collect-submodules` and `--hidden-import` options. For model-heavy tools such as ProofLens and AlignLens, large model folders are usually copied manually into the packaged folder after PyInstaller packaging.

不同子工具可能需要额外的 `--add-data`、`--collect-submodules` 和 `--hidden-import` 参数。对于 ProofLens 和 AlignLens 这类依赖模型的工具，较大的模型文件夹通常建议在 PyInstaller 打包完成后手动复制到打包目录中。

---

## 6. Data and Privacy / 数据与隐私

- Local functions run on the user's computer.
- Project files, metadata records, OCR results and alignment results are saved locally unless the user explicitly exports or uploads them.
- LLM-assisted functions are optional.
- If an API-based LLM is used, the selected text or prompt content may be sent to the configured API endpoint.
- Users should avoid uploading confidential, sensitive or unpublished data to external APIs unless they have permission to do so.
- API Keys should be stored locally and should not be committed to public repositories.

---

## 7. Notes / 注意事项

- BFSU LexiScope is a research-support toolkit, not a fully automatic replacement for expert judgment.
- OCR results, metadata extraction results, automatic alignment results and LLM suggestions should always be checked by the user.
- Users should verify exported texts, metadata and aligned files before using them in publications, teaching materials, corpus construction or statistical analysis.
- Some functions are still experimental and may change between versions.
- If a function has not yet been released, please treat its description as a development plan rather than a completed feature.

---

## 8. Roadmap / 发展路线

Planned development directions include:

- 完善 OCR 与校对工作流；
- 完善多语翻译对齐、对齐检查和语料导出工作流；
- 增强大模型辅助语料处理能力；
- 加入语料清洗和批处理工具；
- 加入分词、分句和基础统计功能；
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

BFSU LexiScope and its subtools are designed for research support, corpus construction and data processing. Automatically generated results, including OCR output, LLM-assisted proofreading, metadata extraction, automatic alignment and future statistical reports, may contain errors. Users are responsible for checking, revising and confirming all outputs before using them for academic publication, teaching, corpus release or formal research analysis.

BFSU LexiScope 及其子工具主要用于科研辅助、语料库建设和数据处理。自动生成结果，包括 OCR 文本、大模型辅助校对、元信息抽取、自动对齐结果以及未来的数据分析报告，均可能存在错误。用户在将相关结果用于论文发表、教学材料、语料库发布或正式研究分析前，应自行检查、修订并确认其准确性。
