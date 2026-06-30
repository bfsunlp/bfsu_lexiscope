# BFSU ProofLens

**BFSU ProofLens** 是一款图形界面的多语种 OCR 识别与智能校对软件，适合处理扫描件、图片、PDF 文档、语料库材料和教学资料。

## 主要功能

- 导入 PDF、JPG、PNG、TIFF、BMP、WebP 等文件；
- 逐页显示原始图像，并在右侧编辑 OCR 文本；
- 支持本地 RapidOCR 高质量识别；
- 新增 EasyOCR 快速识别，适合演示和快速草稿 OCR；
- 可选使用 ChatGPT / OpenAI 进行 LLM OCR 或 OCR 校对；
- 支持预先选择语种，也支持多语混排提示；
- 自动生成疑似错误和修订建议，可逐条接受、拒绝或全部接受；
- 支持保存项目，便于之后继续校对；
- 支持导出 TXT、DOCX、XLSX、JSON、XML、Markdown。

## 界面语言

软件默认使用英文界面。可在菜单栏中选择：

`Settings` → `Language` → `English` / `简体中文` / `繁體中文`

切换后会立即刷新界面，并自动记住用户选择。下次启动时会继续使用上一次选择的界面语言。

## 基本使用流程

1. 打开软件后，点击 **Open Files / 打开文件** 导入图片或 PDF。
2. 在工具栏中选择 OCR 语种预设，例如 `zh_en_mixed` 或 `multi_mixed`。
3. 勾选或取消 **Mixed-language / 多语混排**。
4. 点击 **Run OCR / OCR识别** 执行默认本地 OCR；演示时可点击 **Fast OCR / 快速OCR** 使用 EasyOCR。
5. 在右侧文本框中人工校对文本。
6. 如需使用大模型校对，请先进入 **Settings / 设置**，关闭仅本地模式并启用 ChatGPT / OpenAI。
7. 点击 **LLM Proofread / LLM校对** 获取修订建议。
8. 校对完成后，点击 **Export / 导出**，选择导出范围和格式。

## 进度条与处理状态

识别和大模型校对运行时，主界面底部会显示：

- 当前任务，例如 RapidOCR、EasyOCR、LLM OCR、LLM Proofreading；
- 当前处理的文件名；
- 动态进度条；
- 当前任务状态提示。

软件在识别过程中不会锁死主界面。你仍然可以查看当前页面和状态，但同一时间只允许运行一个 OCR 或 LLM 任务，以避免重复调用和结果覆盖。

左侧文件/页面列表会显示处理标记：

- `⏳` 表示处理中；
- `✅` 表示已完成；
- `❌` 表示当前页处理失败；
- `⚠` 表示文件中有页面处理失败；
- 文件名后面的 `[完成页数/总页数]` 可用于查看整体处理进度。


## 文件/页面管理

左侧 **Files / Pages** 区域现在支持更完整的文件与页面管理：

- 右键文件或页面，可选择 **Open / 打开**、**Open source file location / 打开源文件位置**、**Add file(s) / 增加文件**、**Add page(s) to selected file / 增加页面到所选文件**、**Delete / 删除**；
- 左侧列表下方的 **+** 按钮可增加文件；当已有文件或页面被选中时，也可选择把导入内容追加为该文件的新页面；
- 左侧列表下方的 **−** 按钮可删除当前选中的文件或页面；
- 删除文件会删除该文件下所有页面；删除页面后软件会自动重新编号页面。

## 语种选择说明

工具栏中的语种预设用于告诉 OCR 和 LLM 当前材料的大致语种范围。常用选项包括：

- `zh_en_mixed`：中文 + 英文混排；
- `zh`：中文；
- `en`：英文；
- `ja`：日文；
- `ko`：韩文；
- `fr`：法文；
- `de`：德文；
- `es`：西班牙文；
- `ru`：俄文；
- `multi_mixed`：多语混排提示。

多语混排识别效果取决于 OCR 模型本身。RapidOCR 更适合正式、高质量识别；EasyOCR 更适合演示、快速预览和草稿识别。对于复杂版面或多语混排材料，建议结合 LLM 校对功能进行复核。


## 快速 OCR / EasyOCR

本版本新增 **EasyOCR 快速识别模式**。它主要用于软件演示、课堂展示和快速预览，通常启动和单页处理体验比完整 RapidOCR 流程更轻便。

使用方式：

- 点击工具栏 **Fast OCR / 快速OCR**，识别当前页；
- 或使用菜单 `OCR` → `Fast OCR (EasyOCR)`，选择当前页、当前文件或整个项目；
- 也可以在 `Settings / Preferences` 中把 **OCR backend** 改为 `easyocr`，之后普通 **Run OCR** 就会使用 EasyOCR。

建议：正式语料建设、论文材料整理或高质量批量转写仍优先使用 RapidOCR；演示和快速草稿转写优先使用 EasyOCR。

## 隐私提示

默认情况下，软件启用“仅本地模式”，不会调用外部大模型 API。若开启 ChatGPT / OpenAI 功能，当前页面图像或 OCR 文本可能会发送到外部 API。涉密或敏感文件建议仅使用本地 OCR，例如 RapidOCR 或 EasyOCR。

## 技术文档

开发、依赖安装、命令行运行和 PyInstaller 打包说明请见：

`technical_readme.md`

## 批量处理与加速选项

本版本增加了批量处理和可选并行加速。除工具栏的当前页操作外，也可以通过菜单执行批量任务：

- `OCR` → `Run OCR on Current File`：识别当前文件的全部页面；
- `OCR` → `Run OCR on Whole Project`：识别项目中的全部页面；
- `OCR` → `Fast OCR (EasyOCR)`：使用 EasyOCR 快速识别当前页、当前文件或整个项目；
- `LLM` → `LLM OCR on Current File`：对当前文件逐页调用 LLM OCR；
- `LLM` → `LLM Proofread Current File`：对当前文件逐页调用 LLM 校对。

在 `Settings / Preferences` 中可以调整：

- **OCR backend**：可选择 `rapidocr`、`easyocr`、`llm_ocr` 或 `hybrid`；
- **OCR parallel backend**：建议默认使用 `thread`；`process` 可能在 CPU OCR 中更快，但内存占用更高，GPU 模式不建议使用；
- **Max OCR workers**：默认 1。大 PDF 或多图片批量处理可尝试 2–4；
- **EasyOCR light/demo mode**：推荐开启。该模式使用单缓存任务，降低模型重复加载和机器负载；
- **Max LLM concurrent requests**：默认 1。若 API 限额允许，可尝试 2–4。

建议先用默认设置确认功能稳定，再逐步提高并行数。

## PDF 导入响应速度说明

V1.0.4 起，PDF 导入和页面渲染已经改为后台任务。导入大 PDF 时，主界面底部会显示当前文件和当前页渲染进度，窗口不应再出现长时间假死。

如演示电脑性能较弱，可在 `Settings / Preferences` 中把 **PDF rendering DPI** 从 200 调低到 150，或把 **Preview max side** 保持在 1400 左右，以减轻预览渲染压力。

## OCR 模型下载策略

RapidOCR 和 EasyOCR 都可能在首次使用某些语种时下载识别模型。V1.0.4 增加了 **OCR model download policy**：

- `ask`：默认。每次会话首次使用 OCR 时询问是否允许下载缺失模型；
- `auto`：允许自动下载缺失模型；
- `manual`：不允许自动下载，只使用本地已有模型。

如果演示现场网络不稳定，建议提前在联网环境下运行一次所需 OCR 引擎和语种，或把策略设为 `manual` 并准备好本地模型目录。

## V1.0.5 PDF 导入修复说明

如果打开 PDF 后显示已导入页面但窗口仍然“未响应”，通常不是 OCR 引擎本身的问题，而是 PDF 页面图像过大或 PyMuPDF 渲染阶段仍然占用系统资源。V1.0.5 将 PDF / 图片导入进一步改为独立进程处理，并在导入时预先生成较小的预览图：

- 原始页面图像仍用于 OCR，保证识别质量；
- 主界面预览使用 `preview_path` 小图，减少 Tkinter 主线程解码大图的压力；
- 大 PDF 不再默认展开过多页面节点，避免页面树刷新过慢；
- 修复程序自动选择导入后第一页时可能触发重复 Treeview 选择事件的问题。

## OCR 模型下载建议

RapidOCR 和 EasyOCR 都可能在首次使用某个语种时下载模型。建议在演示前提前运行一次对应 OCR 引擎完成模型下载，避免现场等待。

可在 `Settings / Preferences` 中设置 **OCR model download policy**：

- `ask`：默认，首次使用时询问是否允许下载；
- `auto`：自动允许下载；
- `manual`：不自动下载，仅使用本地已有模型。

演示电脑联网不稳定时，建议提前下载模型，现场改为 `manual`。

## V1.0.6 PDF 打开后未响应修复

本版进一步修复“PDF 页面已经导入、状态栏显示 Complete，但主界面随后未响应”的问题：

- 导入完成后的页面树刷新和第一页选择被拆分为延迟执行，避免在同一个 UI 回调中集中执行太多操作；
- 图像预览改为异步加载：后台线程负责读取、缩放预览图，主线程只负责最终显示；
- 状态栏刷新不再调用 `update_idletasks()`，降低 Tkinter 回调重入导致的未响应风险；
- 默认 **Preview max side** 调整为 1400 像素，更适合低配置电脑和演示环境；
- `Settings / Preferences` 设置窗口各选项卡已增加垂直滚动条，底部 **Save / Cancel** 按钮固定显示。

如果仍然遇到 PDF 打开较慢，可在 `Settings / Preferences` 中继续降低 **PDF rendering DPI** 或 **Preview max side**。

## V1.0.7 识别与 LLM 报错提示改进

如果点击 **Run OCR**、**LLM OCR** 或 **LLM Proofread** 后任务失败，本版会在弹窗中显示具体错误详情，例如：

- 当前 Python 环境未安装 RapidOCR / EasyOCR；
- RapidOCR 版本 API 不兼容；
- OCR 模型未下载且下载策略设为 `manual`；
- OpenAI API Key 为空；
- 未安装 `openai` 包；
- LLM 设置中禁止发送图像或文本；
- API 模型名称、网络或权限错误。

RapidOCR 兼容性也做了增强：新版同时兼容 RapidOCR 2.x 的 `ocr()` 调用方式和 RapidOCR 3.x 的 `predict()` 调用方式。若正式识别仍失败，建议先尝试工具栏的 **Fast OCR / 快速OCR**，确认图像导入流程正常，再检查 RapidOCR 安装和模型下载。

LLM 功能使用前请确认：

1. `Settings / Preferences` 中已关闭 **Local-only mode**；
2. 已启用 **ChatGPT / OpenAI**；
3. 已填写 API Key，或设置了 `OPENAI_API_KEY` 环境变量；
4. LLM OCR 需要启用 **Allow sending images to API**；
5. LLM Proofread 需要启用 **Allow sending OCR text to API**。

## V1.0.8 Notes

This version improves three OCR/proofreading behaviors for GUI users:

- Text-based PDF files now use the embedded PDF text layer by default when it is available. This is faster than image OCR and better preserves paragraphs. Turn this off in **Settings → OCR → Prefer embedded PDF text layer** if you need image-based OCR.
- OCR output now has a **text layout** option. Use `paragraph` for readable paragraph reconstruction, or `line` if you want to preserve one OCR block/line per line.
- LLM Proofread now always analyzes the current text editor content. If the model finds no concrete error, the suggestion panel will still show an informational result instead of appearing empty.

If RapidOCR reports that no model hosting platform is available, open **Settings → OCR** and try:

1. keep **RapidOCR model source** as `bos` or change it to `modelscope`;
2. keep **Disable RapidOCR model source check** enabled;
3. or use **Fast OCR (EasyOCR)** / embedded PDF text layer for demonstration.

## V1.0.11 Notes

This version further improves OCR proofreading and RapidOCR stability:

- **LLM Proofread** now uses a stronger OCR-specific proofreading prompt covering typos, garbled text, encoding noise, hard line breaks, hyphenation, paragraph reflow, whitespace, punctuation, language confusion, duplicate text, headers/footers, and table/list format issues.
- If the LLM returns JSON inside Markdown or with extra explanatory text, ProofLens now extracts and parses the JSON automatically.
- If the LLM returns plain text instead of JSON, ProofLens no longer treats it as unusable. It converts recoverable bullet points or Original/Suggested fragments into reviewable suggestion items.
- A local safety check also detects common OCR/PDF text-layer problems such as `�`, `￾`, invisible control characters, English line-break hyphenation, repeated spaces, and hard-wrapped paragraphs.
- RapidOCR now starts with safer Windows CPU defaults: oneDNN/MKLDNN and PIR runtime paths are disabled by default. If RapidOCR still fails, the app can automatically fall back to EasyOCR so demonstrations can continue.

For presentation/demo computers, the recommended stable settings are:

1. **OCR backend**: `rapidocr` or `easyocr`;
2. **Automatically fall back to EasyOCR if RapidOCR fails**: enabled;
3. **Disable RapidOCR oneDNN/MKLDNN CPU kernels**: enabled;
4. **Disable RapidOCR PIR runtime path**: enabled;
5. **OCR text layout**: `paragraph`.


## V1.0.11 Notes

This version improves LLM proofreading result recovery. If the model returns plain text, Markdown bullets, arrow-style corrections, or an empty/non-standard response instead of strict JSON, ProofLens will try one automatic JSON repair pass and then surface the recovered feedback in the suggestion panel. Suggestion Detail now uses a scrollable window so long LLM feedback can be read directly.

A new LLM setting is available: **Auto-repair non-JSON LLM proofreading responses**. It is enabled by default.

## V1.0.11 GUI Notes

This version adds explicit UI language variants and file/page management improvements:

- UI language choices are now **English**, **简体中文**, and **繁體中文**. Legacy `zh` settings are normalized to `zh_cn`.
- The left file/page tree supports a right-click context menu for opening, locating source files, adding files, appending pages, and deleting files/pages.
- The file/page tree now has **+** and **−** buttons for quick add/delete operations.


## V1.0.13 更新：文件/页面树删除修正

- 修正点击文件节点后自动跳转并改选第一页的问题：现在单击文件节点会显示第一页预览，但仍保留整个文件节点的选中状态。
- 删除文件时会删除该文件下全部页面；删除单页时只删除所选页面，并自动重排剩余页码。
- 右键菜单会保留已有多选：在多选范围内右键删除时，不会丢失之前选中的多个文件/页面。
- 键盘 `Delete` / 小键盘 `Delete` 与底部 `−` 按钮调用同一删除逻辑。

## V1.0.12 更新：RapidOCR、文件/页面删除与 zh_tr

- 默认本地 OCR 后端改为 `rapidocr`，移除 PaddleOCR 依赖；`requirements.txt` 改为 `rapidocr` + `onnxruntime`。
- OCR 启动前会检查 RapidOCR 识别模型，并在缺少模型时触发 RapidOCR 的自动模型准备/下载流程；界面进度条会显示模型检查和准备状态。
- 文件/页面列表支持扩展选择：可选择整个文件删除，也可选择单页删除；`−` 按钮、右键删除和键盘 `Delete` 均可使用。
- 支持识别语种新增 `zh_tr`（繁體中文）。语言预设仅新增单独的 `zh_tr`，不新增“繁體中文+English”混合预设；需要混合时请在设置中手动勾选 `zh_tr` 和 `en`。


## V1.0.14 更新：滚轮兼容与按源文件分别导出

- 所有主要带滚动条的区域统一接入鼠标中键滚轮支持，包括文件/页面树、图像预览、文本编辑器、设置窗口、修订建议表、建议详情窗口和关于窗口。
- 导出设置中新增“按源文件分别导出为 源文件名_ocr”选项。启用后，导出路径选择改为文件夹选择，并按每个源文件分别生成 `原文件名_ocr` 文件，扩展名随所选格式自动变化。
