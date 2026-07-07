# BFSU AlignLens / 北外 AlignLens 多语翻译对齐工具

**中文**

**BFSU AlignLens** 是一款面向多语—汉语平行语料库建设、语料库翻译学、翻译教学、一本多译研究和多语文本数据整理的 Windows 桌面软件。软件支持文件级配组、语种级分段/分句、Transformer 段落与句子对齐、LLM 辅助段落与句子对齐、可编辑对齐校对、低相似度高亮、逐组独立导出和项目化保存。

**English**

**BFSU AlignLens** is a Windows desktop application for multilingual-Chinese parallel corpus construction, corpus-based translation studies, translation teaching, multiple-translation research, and multilingual text data preparation. It supports file-level grouping, language-specific paragraph and sentence segmentation, Transformer-based paragraph and sentence alignment, LLM-assisted paragraph and sentence alignment, editable alignment review, low-similarity highlighting, group-level export, and project-based persistence.

---

## 1. Windows 图形界面版下载 / Windows GUI Download

**中文**

Windows 图形界面版已经打包为压缩包，下载后解压即可运行。

- 文件名：`BFSU_AlignLens.zip`
- 下载链接：https://pan.baidu.com/s/1x9EgCOhf8MoRACkhL09Dog
- 提取码：`ihjx`

解压后，双击运行：

```text
BFSU_AlignLens.exe
```

**English**

The Windows GUI edition is distributed as a zipped folder. Download, unzip, and run the executable directly.

- File name: `BFSU_AlignLens.zip`
- Download link: https://pan.baidu.com/s/1x9EgCOhf8MoRACkhL09Dog
- Extraction code: `ihjx`

After unzipping, double-click:

```text
BFSU_AlignLens.exe
```

---

## 2. 核心工作流 / Core Workflow

**中文**

BFSU AlignLens 的基本流程为：

```text
新建或打开项目
↓
导入待对齐文件
↓
按对齐模式完成文件级配组
↓
分段或分句
↓
使用 Transformer 或 LLM 进行段落/句子对齐
↓
在对齐编辑器中人工检查、修改和确认
↓
导出 Excel、TXT、TMX、XML、Word、JSON 或多套 TXT 文件
```

软件支持一对一翻译、一源多译和多语平行文本对齐。用户可以先完成文件级分组，再对每一个 `set_xxx` 文件组分别分段、分句、对齐、校对和导出。

**English**

The typical BFSU AlignLens workflow is:

```text
Create or open a project
↓
Import files for alignment
↓
Group files according to the selected alignment mode
↓
Segment paragraphs or sentences
↓
Run Transformer or LLM paragraph/sentence alignment
↓
Review, edit, and confirm results in the Alignment Editor
↓
Export to Excel, TXT, TMX, XML, Word, JSON, or multi-TXT files
```

The software supports one-to-one translation alignment, one-source-multiple-translations alignment, and multilingual parallel alignment. Users can process each `set_xxx` file group independently from segmentation to export.

---

## 3. 主要功能 / Main Features

**中文**

- 基于 Python 与 tkinter/ttk 构建 Windows 桌面图形界面。
- 界面风格与 BFSU ProofLens 保持一致，包括浅色界面、紧凑工具栏、标签页、日志窗口和图标风格。
- 支持一对一翻译、一源多译、多语平行三类导入模式。
- 支持多列文件管理器，用于文件级配组、排序、拖动重排和预览。
- 删除文件后保留空栏目，避免用户重新创建对齐模式。
- 自动跳过重复导入的文件。
- 记录界面语言、源语、译语、译本数量、模型选择、分段/分句设置和导出偏好。
- 支持段落分段和句子分句两个独立操作。
- 支持 `zh_sim`、`zh_tra`、`en`、`de`、`fr`、`es`、`ru`、`ja`、`ko`、`pt`、`it`、`nl`、`ar`、`tr`、`vi`、`th`、`pl`、`sv` 等语种配置。
- 支持 Stanza、spaCy、HanLP、标点规则、行切分、段落切分等分段/分句策略。
- Transformer 对齐可在 CUDA 可用时使用 GPU，并在 GPU 不可用时自动回退 CPU。
- 神经分句模型可优先使用 GPU，并在加载失败或无 GPU 时自动回退。
- 支持 Transformer 段落对齐和 Transformer 句子对齐。
- 支持 LLM 段落对齐和 LLM 句子对齐。
- 支持自然段保守对齐和句级语义对齐。
- 支持细粒度句子对齐控制，在不改变分句结果的前提下减少过度合并。
- 支持 full DP、banded DP 和 automatic DP 搜索模式。
- 支持设置大文件阈值和 banded DP 带宽。
- 支持主 Transformer 模型、辅助 Transformer 模型和双模型融合对齐。
- 默认 Transformer 精准配置采用 `sentence-transformers/LaBSE` 与 `intfloat/multilingual-e5-base` 双模型融合、full DP、batch size 32、max window 5、句对齐最大合并句数 3、高置信度阈值 0.70、低相似度强制匹配惩罚 0.25，并启用残差匹配。
- 每个 `set_xxx` 文件组使用独立的 Alignment Editor 标签页。
- 初始界面不显示 Alignment Editor，只有打开文件组后才创建编辑器标签页。
- 每个编辑器标签页可单独关闭。
- 对齐编辑器中显示当前文件组、源语文件名、译语文件名和相似度列。
- 支持行级和单元格级手动编辑，包括插入空行、删除行、移动行、移动单元格、合并单元格、按光标拆分单元格、标记已确认、标记需检查和添加备注。
- 支持重算全部相似度或仅重算当前行相似度。
- 根据阈值标记低相似度行，并提供上一条/下一条高亮行跳转。
- 支持 LLM 检查建议，并提供应用当前建议、应用全部建议、忽略当前建议和忽略全部建议。
- LLM 检查采用保守策略：检查当前编辑器上下文，只返回结构性修改建议，不直接改写源语或译语文本。
- 可在设置中选择 LLM 检查建议的语种，便于用户阅读 `problem` 和 `reason` 字段。
- OpenAI 模型默认使用 `gpt-5.4-mini`，同时允许用户填写 GPT-5.5 或其他可用模型名称。
- 所有 LLM 提示词集中保存在根目录 `Prompt.md`，便于用户检查和调整。
- 当前编辑器支持独立撤销/重做，保留 100 步操作历史。
- 支持取消后台任务，取消后迟到的后台结果不会写回界面。
- 记录文件组状态，包括已导入、已分段、已分句、正在对齐、段落已对齐、句子已对齐、编辑中和已完成。
- 支持完成对齐确认，并在自动重跑可能覆盖已完成结果时提示用户确认。
- 支持从当前编辑器逐组独立导出。
- 支持批量分段、批量分句、批量 Transformer 对齐、批量 LLM 对齐和批量导出。
- 支持 Excel、TXT、TMX、XML、Word、JSON 和多套 TXT 导出。
- `.alignlens` 项目文件使用 UTF-8 JSON 保存。
- 软件日志写入 `log/alignlens.log`。

**English**

- Built as a Windows desktop GUI with Python and tkinter/ttk.
- Follows the visual style of BFSU ProofLens, including a light interface, compact toolbar, tabbed panels, log panel, and icon style.
- Supports one-to-one translation, one-source-multiple-translations, and multilingual parallel import modes.
- Provides a multi-column File Manager for file-level grouping, sorting, drag-and-drop reordering, and preview.
- Keeps empty columns after files are deleted, so the alignment mode does not need to be recreated.
- Automatically skips duplicate file imports.
- Records user preferences such as interface language, source language, target languages, target count, model choices, segmentation settings, and export options.
- Supports paragraph segmentation and sentence segmentation as separate operations.
- Supports language profiles for `zh_sim`, `zh_tra`, `en`, `de`, `fr`, `es`, `ru`, `ja`, `ko`, `pt`, `it`, `nl`, `ar`, `tr`, `vi`, `th`, `pl`, and `sv`.
- Supports Stanza, spaCy, HanLP, punctuation-based, line-based, and paragraph-based segmentation strategies.
- Uses GPU for Transformer alignment when CUDA is available and automatically falls back to CPU when GPU is unavailable.
- Neural segmentation models try to use GPU first and fall back when GPU or model loading is unavailable.
- Supports Transformer paragraph alignment and Transformer sentence alignment.
- Supports LLM paragraph alignment and LLM sentence alignment.
- Supports conservative natural-paragraph alignment and sentence-level semantic alignment.
- Provides fine-grained sentence alignment controls to reduce over-merged alignment cells without changing segmentation results.
- Supports full DP, banded DP, and automatic DP search modes.
- Allows users to configure the large-document threshold and banded DP size.
- Supports a primary Transformer model, a secondary Transformer model, and fused dual-model alignment.
- The default high-accuracy Transformer profile uses fused `sentence-transformers/LaBSE` and `intfloat/multilingual-e5-base`, full DP, batch size 32, max window 5, sentence max merge units 3, high-confidence threshold 0.70, low-similarity forced-match penalty 0.25, and residual matching.
- Uses one independent Alignment Editor tab for each `set_xxx` file group.
- Does not show the Alignment Editor on startup; editor tabs are created only after file groups are opened.
- Each editor tab can be closed independently.
- The editor displays the current file group, source file name, target file names, and similarity columns.
- Supports row-level and cell-level editing, including inserting blank rows, deleting rows, moving rows, moving cells, merging cells, splitting cells at cursor, marking confirmed, marking needs review, and adding notes.
- Supports recomputing all similarities or only the current row similarity.
- Marks low-similarity rows according to configurable thresholds and provides previous/next highlighted-row navigation.
- Supports LLM review suggestions with apply current, apply all, ignore current, and ignore all operations.
- LLM review is conservative: it checks the current editor context, returns structural suggestions only, and does not directly rewrite source or target text.
- The language of LLM review suggestions can be selected in Settings, making the `problem` and `reason` fields easier to read.
- The OpenAI model defaults to `gpt-5.4-mini`, while users may enter GPT-5.5 or any other model name available to them.
- All LLM prompts are stored in the root `Prompt.md` file for inspection and tuning.
- Each editor keeps an independent 100-step undo/redo history.
- Background tasks can be cancelled; late results from cancelled workers are ignored.
- File group states are recorded, including imported, paragraph segmented, sentence segmented, aligning, paragraph aligned, sentence aligned, editing, and completed.
- Completed alignment confirmation is supported, and the software warns users before automatic realignment overwrites reviewed results.
- Supports independent group-level export from the active editor.
- Supports batch paragraph segmentation, batch sentence segmentation, batch Transformer alignment, batch LLM alignment, and batch export.
- Supports Excel, TXT, TMX, XML, Word, JSON, and multi-TXT export.
- `.alignlens` project files are saved as UTF-8 JSON.
- Logs are written to `log/alignlens.log`.

---

## 4. 分段与分句 / Segmentation

**中文**

BFSU AlignLens 将分段/分句与对齐分离。用户可以先按语种选择合适的分段/分句策略，再选择 Transformer 或 LLM 对齐。当前可用策略包括：

```text
auto
stanza
spacy
hanlp
punctuation
line
paragraph
none
```

神经分句模型会优先尝试使用 GPU。若当前环境不支持 CUDA、模型未安装或加载失败，软件会自动回退到 CPU 或规则分句策略，并在日志中提示。

**English**

BFSU AlignLens separates segmentation from alignment. Users can first choose language-specific segmentation strategies and then run Transformer or LLM alignment. Available strategies include:

```text
auto
stanza
spacy
hanlp
punctuation
line
paragraph
none
```

Neural segmenters try to use GPU first. If CUDA is unavailable, a model is missing, or model loading fails, the software automatically falls back to CPU or rule-based segmentation and writes a diagnostic message to the log.

---

## 5. Transformer 对齐 / Transformer Alignment

**中文**

Transformer 对齐用于根据跨语语义相似度进行段落或句子对齐。软件支持单模型和双模型融合策略，用户可以在设置中调整模型、batch size、DP 搜索方式、句子合并窗口、相似度阈值和惩罚项。

默认精准配置如下：

```text
Transformer 模型策略：fused
主 Transformer 模型：sentence-transformers/LaBSE
辅助 Transformer 模型：intfloat/multilingual-e5-base
动态规划搜索模式：full
大文件阈值：2000000
Banded DP 带宽：240
Batch size：32
Max window：5
句对齐最大合并句数：3
精细句对齐模式：启用
允许 2:2 句子合并：启用
句子合并惩罚：0.25
Skip penalty：-0.3
Empty penalty：-0.3
Low-similarity forced-match penalty：0.25
Length penalty weight：0.02
Paragraph distance penalty：0.04
High confidence threshold：0.7
Residual matching：启用
```

**English**

Transformer alignment uses cross-lingual semantic similarity to align paragraphs or sentences. The software supports both single-model and fused dual-model strategies. Users can configure model choices, batch size, DP search mode, sentence merge windows, similarity thresholds, and penalties.

The default high-accuracy profile is:

```text
Transformer model strategy: fused
Primary Transformer model: sentence-transformers/LaBSE
Secondary Transformer model: intfloat/multilingual-e5-base
Dynamic programming search mode: full
Large document threshold: 2000000
Banded DP size: 240
Batch size: 32
Max window: 5
Sentence max merge units: 3
Fine sentence alignment mode: enabled
Allow 2:2 sentence merge: enabled
Sentence merge penalty: 0.25
Skip penalty: -0.3
Empty penalty: -0.3
Low-similarity forced-match penalty: 0.25
Length penalty weight: 0.02
Paragraph distance penalty: 0.04
High confidence threshold: 0.7
Residual matching: enabled
```

---

## 6. LLM 对齐与检查 / LLM Alignment and Review

**中文**

LLM 功能为可选功能，需要用户自行配置 API Key 或兼容接口。软件支持 LLM 段落对齐、LLM 句子对齐和 LLM 对齐检查建议。LLM 检查不直接替换文本，而是给出需要用户确认的结构性建议。

用户可在设置中配置：

```text
OpenAI API Key
OpenAI Model
Temperature
Max Tokens
Timeout
Batch Size
LLM 建议语种
```

默认模型为 `gpt-5.4-mini`。模型名称保持可编辑，用户可以根据自己的接口权限改为 GPT-5.5 或其他可用模型。LLM 建议语种可由用户指定，便于以中文、英文或其他支持语种阅读检查意见。

**English**

LLM features are optional and require a user-provided API key or compatible endpoint. The software supports LLM paragraph alignment, LLM sentence alignment, and LLM review suggestions. LLM review does not directly replace text; it returns structural suggestions that must be confirmed by the user.

Users can configure:

```text
OpenAI API Key
OpenAI Model
Temperature
Max Tokens
Timeout
Batch Size
LLM suggestion language
```

The default model is `gpt-5.4-mini`. The model field remains editable, so users may enter GPT-5.5 or another available model depending on their account and endpoint. The LLM suggestion language can be specified so that review comments can be read in Chinese, English, or another supported language.

---

## 7. GPU 与 CPU 行为 / GPU and CPU Behavior

**中文**

软件启动时会检测 PyTorch、CUDA 运行环境和 `torch.cuda.is_available()`。如果 CUDA 可用，Transformer 对齐默认使用 GPU；如果 CUDA 或 GPU 不可用，软件自动回退到 CPU，并在日志中记录原因。

默认打包脚本会按 `requirements.txt` 安装依赖。如 `requirements.txt` 使用 CUDA 版 PyTorch，则打包结果会包含对应的 CUDA PyTorch 运行库。目标机器仍需安装可用的 NVIDIA 驱动。大型模型文件不会默认打包，需要用户在打包后手动复制到 `models` 文件夹。

**English**

At startup, the software checks PyTorch, the CUDA runtime, and `torch.cuda.is_available()`. If CUDA is available, Transformer alignment uses GPU by default. If CUDA or GPU is unavailable, the software falls back to CPU and records the reason in the log.

The default packaging script installs dependencies from `requirements.txt`. If `requirements.txt` specifies a CUDA-enabled PyTorch build, the packaged application will include the corresponding CUDA PyTorch runtime libraries. The target machine still needs a working NVIDIA driver. Large model files are not bundled by default and should be copied manually into the `models` folder after packaging.

---

## 8. 项目文件 / Project Files

**中文**

BFSU AlignLens 使用 `.alignlens` 项目文件保存工作状态，项目文件为 UTF-8 JSON 格式，通常包括：

```text
项目名称
文件列表
文件组编号
文件组状态
段落切分结果
句子切分结果
对齐结果
LLM 建议
设置项
模型与分句偏好
```

项目文件用于保留完整工作状态，便于用户之后继续编辑和导出。

**English**

BFSU AlignLens saves working states in `.alignlens` project files. Project files use UTF-8 JSON and may include:

```text
project name
file list
file group IDs
file group states
paragraph segments
sentence segments
alignment rows
LLM suggestions
settings
model and segmentation preferences
```

Project files preserve the working state so that users can continue editing and exporting later.

---

## 9. 导出格式 / Export Formats

**中文**

软件支持从当前文件组独立导出，也支持批量导出所有已分段或已对齐的文件组。支持格式包括：

```text
Excel  .xlsx
TXT    .txt
TMX    .tmx
XML    .xml
Word   .docx
JSON   .json
多套 TXT 输出
```

多套 TXT 输出适合平行语料库建设：每个语种或译本可输出为独立 TXT 文件，按行号保持对齐。

**English**

The software supports independent export from the active file group and batch export for all segmented or aligned groups. Supported formats include:

```text
Excel  .xlsx
TXT    .txt
TMX    .tmx
XML    .xml
Word   .docx
JSON   .json
Multi-TXT output
```

Multi-TXT output is suitable for parallel corpus construction: each language or translation version can be exported as a separate TXT file while preserving line-based alignment.

---

## 10. 源码运行 / Run from Source

**中文**

推荐环境：

```text
Windows 11
Python 3.10 或 Python 3.11
NVIDIA GPU 可选
CUDA-enabled PyTorch 可选，但建议用于大型对齐任务
```

创建并激活虚拟环境：

```bat
cd bfsu_alignlens
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
```

安装依赖：

```bat
python -m pip install -r requirements.txt
```

CPU-only 环境可使用：

```bat
python -m pip install -r requirements_cpu.txt
```

运行源码版：

```bat
python main.py
```

**English**

Recommended environment:

```text
Windows 11
Python 3.10 or Python 3.11
NVIDIA GPU optional
CUDA-enabled PyTorch optional but recommended for large alignment tasks
```

Create and activate a virtual environment:

```bat
cd bfsu_alignlens
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
```

Install dependencies:

```bat
python -m pip install -r requirements.txt
```

For CPU-only environments, use:

```bat
python -m pip install -r requirements_cpu.txt
```

Run from source:

```bat
python main.py
```

---

## 11. PyInstaller 打包 / PyInstaller Packaging

**中文**

Windows 打包建议使用文件夹模式，便于处理 Transformer、Stanza、spaCy、HanLP、OpenAI SDK 等依赖。项目提供的打包脚本为：

```bat
build_alignlens.bat
```

打包脚本会创建 one-folder 程序目录，复制 `assets/`、`config/`、`locales/`、`Prompt.md`、`README.md` 等资源，并在可执行程序同级目录创建 `models/`、`log/` 和 `exports/` 文件夹。大型模型文件默认不打包，用户可在打包完成后手动复制到：

```text
dist\BFSU_AlignLens\models
```

生成的可执行文件通常位于：

```text
dist\BFSU_AlignLens\BFSU_AlignLens.exe
```

**English**

For Windows packaging, folder mode is recommended because it is more stable for dependencies such as Transformer models, Stanza, spaCy, HanLP, and the OpenAI SDK. The provided packaging script is:

```bat
build_alignlens.bat
```

The script creates a one-folder application directory, copies resources such as `assets/`, `config/`, `locales/`, `Prompt.md`, and `README.md`, and creates `models/`, `log/`, and `exports/` folders beside the executable. Large model files are not bundled by default. After packaging, copy local models manually into:

```text
dist\BFSU_AlignLens\models
```

The generated executable is usually located at:

```text
dist\BFSU_AlignLens\BFSU_AlignLens.exe
```

---

## 12. 模型管理 / Model Management

**中文**

模型文件优先保存到配置的 `models` 目录。模型管理主要包括：

```text
SentenceTransformer models
Stanza segmenter models
spaCy language pipelines
HanLP segmentation models
```

部分模型会使用自身缓存机制，例如 HuggingFace、Stanza、spaCy 或 HanLP 的默认缓存目录。BFSU AlignLens 会尽量检测本地模型，并在可行时提供下载和管理入口。

**English**

Model files are stored under the configured `models` directory when possible. Model management covers:

```text
SentenceTransformer models
Stanza segmenter models
spaCy language pipelines
HanLP segmentation models
```

Some model families use their own cache mechanisms, such as HuggingFace, Stanza, spaCy, or HanLP default cache directories. BFSU AlignLens tries to detect local models and provides download or management helpers where feasible.

---

## 13. 注意事项 / Notes

**中文**

- 对齐质量取决于分段/分句质量、源译文本对应程度、译文完整性和模型选择。
- 段落对齐偏保守，不会主动大规模合并自然段。
- 句子对齐通常更精细，但长文本或大幅改写文本仍需要人工检查。
- full DP 更全面，但在大型文件上可能较慢。
- banded DP 更快，但假设源语和译语大体保持相同顺序。
- LLM 对齐和 LLM 检查只能作为辅助，正式使用前必须人工确认。
- API Key 不应公开分享或提交到公共代码仓库。
- 项目文件与文本文件均按 UTF-8 保存和读取。
- 导出结果用于论文、教学、出版或正式语料库建设前，应再次检查并记录处理流程。

**English**

- Alignment quality depends on segmentation quality, source-target correspondence, translation completeness, and model choice.
- Paragraph alignment is conservative and does not aggressively merge natural paragraphs.
- Sentence alignment is usually more fine-grained, but long or heavily rewritten texts still require manual review.
- Full DP is more exhaustive but may be slower for large files.
- Banded DP is faster but assumes that source and target texts are broadly in the same order.
- LLM alignment and review are assistive only and must be manually confirmed before formal use.
- API keys should not be shared publicly or committed to public repositories.
- Project and text files are saved and read in UTF-8.
- Exported results should be checked and documented before being used for academic writing, teaching, publication, or formal corpus construction.

---

## 14. 扩展方向 / Future Extensions

**中文**

未来可继续扩展以下功能：

- 外部分句表导入；
- TEI/XML 语料库导出；
- 段落/句子对齐质量评估报告；
- 双语术语敏感的对齐检查；
- 编辑单元格可视化 diff；
- 对齐置信度校准；
- 面向涉密材料的本地 LLM 支持；
- 与 BFSU LexiScope 工具链的元信息管理衔接；
- 与 BFSU ProofLens 的 OCR 到对齐工作流衔接。

**English**

Possible future extensions include:

- external segment-table import;
- TEI/XML corpus export;
- paragraph/sentence alignment quality reports;
- bilingual terminology-aware alignment checking;
- visual diff for edited cells;
- alignment confidence calibration;
- local LLM support for confidential materials;
- metadata integration with the BFSU LexiScope toolchain;
- OCR-to-alignment workflow integration with BFSU ProofLens.

---

## 15. 关于 / About

**中文**

**软件名称：** BFSU AlignLens / 北外 AlignLens 多语翻译对齐工具  
**版本号：** v1.3  
**开发者：** 刘鼎甲 博士 / Dr. Dingjia LIU  
**单位：** 北京外国语大学 / Beijing Foreign Studies University  
**联系方式：** djliu@bfsu.edu.cn

刘鼎甲博士为北京外国语大学副教授、硕士生导师，主要从事语料库语言学、语料库翻译学、计算语言学、多语平行语料库建设、译者风格、翻译共性及人工智能辅助语料加工等方向研究。BFSU AlignLens 面向需要建设、检查、修订和导出多语对齐文本的用户，服务于科研、教学和语料库建设场景。

GPT-5.5 Thinking 参与了本软件相关代码生成、调试、文档撰写、界面文字整理和打包脚本检查工作。软件总体设计、研究定位、功能取舍、测试确认和最终责任均由开发者负责。GPT/LLM 输出仅作为辅助建议，正式使用前应由用户自行核查。

Copyright © 2026 Dingjia LIU. All rights reserved.

**English**

**Software Name:** BFSU AlignLens / BFSU Multilingual Translation Alignment Tool  
**Version:** v1.3  
**Developer:** Dr. Dingjia LIU / 刘鼎甲 博士  
**Affiliation:** Beijing Foreign Studies University / 北京外国语大学  
**Contact:** djliu@bfsu.edu.cn

Dr. Dingjia LIU is an associate professor and researcher at Beijing Foreign Studies University. His research interests include corpus linguistics, corpus-based translation studies, computational linguistics, multilingual parallel corpus construction, translation universals, translator style, and AI-assisted corpus processing. BFSU AlignLens is designed for users who need to build, inspect, revise, and export multilingual aligned texts for research, teaching, and corpus construction.

GPT-5.5 Thinking assisted with code generation, debugging, documentation, interface wording, and packaging-script review for this software. The overall design, research orientation, feature decisions, testing confirmation, and final responsibility remain with the developer. GPT/LLM outputs are assistive only and should be checked by users before formal use.

Copyright © 2026 Dingjia LIU. All rights reserved.

---

## 16. 免责声明 / Disclaimer

**中文**

BFSU AlignLens 是一款研究辅助与语料库建设工具。Transformer 和 LLM 对齐结果均可能存在错误，不应被视为完全自动生成的最终语料成果。用户在将结果用于论文写作、教学材料、出版物、语料库建设或其他正式用途前，应自行检查、修订、确认并记录处理过程。

本软件不保证自动对齐结果的完整性、准确性或适用于所有文本类型。因模型输出、API 调用、第三方依赖、用户配置、数据质量或误操作导致的结果偏差，应由用户结合具体研究和使用场景自行判断和承担相应责任。

**English**

BFSU AlignLens is a research-support and corpus-construction tool. Transformer and LLM alignment results may contain errors and should not be treated as fully automatic final corpus outputs. Before using exported results for academic writing, teaching materials, publication, corpus construction, or any other formal purpose, users should check, revise, confirm, and document their workflow.

The software does not guarantee that automatic alignment results are complete, accurate, or suitable for all text types. Users are responsible for evaluating result reliability in relation to model outputs, API calls, third-party dependencies, configuration choices, data quality, and possible operational errors.
