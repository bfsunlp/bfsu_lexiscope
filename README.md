# BFSU LexiScope / 北外 LexiScope 语料库智能工具箱

**BFSU LexiScope** is a series of intelligent data processing and data analysis tools for corpus-based linguistic research, corpus construction, translation studies, language education research, and digital humanities.

**BFSU LexiScope / 北外 LexiScope** 是一套面向语料库研究的智能数据处理与数据分析系列工具，旨在为语料库建设、元信息整理、OCR 文本数字化、多语文本对齐、语料清洗、人工智能辅助校对、数据导入导出和后续统计分析提供统一、轻量、可扩展的桌面工具生态。

当前已发布的核心工具包括： 
 
- **BFSU MetadataLens / 元信息规范设计与管理工具**
- **BFSU ProofLens / OCR 识别与校对工具**
- **BFSU AlignLens / 多语翻译对齐工具**
- **BFSU WebLens / 网络语料检索与网页下载工具**
- **BFSU ClearLens / BFSU 文本整理器**

更多面向语料库采集、数据处理、统计分析、可视化和智能标注的模块正在规划和开发中，敬请期待。

---

## 0. Project Vision / 项目愿景

BFSU LexiScope aims to provide a practical and research-oriented toolchain for corpus researchers. The project focuses on the full workflow of corpus-based research:

```text
web discovery / data collection → URL and source-page archiving
→ metadata management → OCR/text digitization → text cleaning
→ multilingual text alignment → corpus organization
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

### 1.1 BFSU MetadataLens v3.5.5 / 元信息规范设计与管理工具

**BFSU MetadataLens** is a metadata schema design, entry, batch-processing, import/export and LLM-assisted metadata management tool for linguistic research, corpus construction, language-resource databases, and corpus-based translation studies. It separates **metadata schema design** from **metadata record entry**, allowing researchers to define reusable metadata specifications first and then create, review, import, edit, validate and export records under a controlled schema.

**BFSU MetadataLens / 元信息规范设计与管理工具** 面向语言学研究、语料库建设、语言资源数据库建设和语料库翻译学研究，用于元信息规范设计、条目录入、批量整理、导入导出、校验以及大模型辅助元信息识别。软件将 **“元信息规范设计”** 与 **“元信息条目录入”** 明确分开，使研究者能够先建立统一、可复用、可校验的元信息 Schema，再在规范约束下录入、导入、复核和管理具体记录。其核心工作流为：

```text
项目创建 → 选择或设计元信息规范 → 条目录入 / Excel/XML 导入
→ 批量字段整理 → 大模型辅助识别与人工复核
→ Schema / Records 校验 → XML 统一保存 → Excel / CSV / XML 导出
```

#### Main Features / 主要功能

- 支持单语、双语平行、多语平行、一本多译、可比语料、学习者语料和口语语料等系统模板；
- 系统模板与用户模板分开管理，系统模板只读，用户可以导入模板规范、重新设计并自行命名 Schema；
- 支持 Field ID、XML Tag、数据类型、元信息层级、必填、可重复、受控词表、正则校验、示例及中英文说明等字段属性；
- 条目录入界面根据当前 Schema 自动生成，支持保存状态提示、记录校验、上一条/下一条和人工编辑；
- 支持记录总表搜索、排序、多选、复制、删除和批量字段修改；
- 支持 Excel 元信息导入、字段映射和预览；
- 支持 XML 项目、Records XML 和一般 XML 文档导入及标签映射；
- 支持 Records XML、Schema XML、Excel 和 CSV 导出；
- 支持 OpenAI、DeepSeek、Qwen、Claude 和 Gemini；
- 支持单条大模型元信息识别，以及从多个本地文件或文本中的 URL 列表批量识别**新增元信息记录**；
- 大模型结果先进入人工复核流程，用户可逐字段确认、逐记录应用或一键应用全部确认结果；
- 大模型识别严格参考当前项目、当前 Schema 和当前记录信息，不允许模型任意创建当前 Schema 之外的字段；
- API Key 只保存在当前系统用户的本地配置目录，不写入项目 XML，也不会随软件发布目录复制；
- 项目统一保存为 UTF-8 XML，并支持覆盖前自动备份；
- 中英文界面、用户手册和 About 随当前界面语言切换。

#### Download / 下载

**Current Release / 当前版本：** `BFSU MetadataLens v3.5.5`

**File / 文件名：** `BFSU_MetadataLens v3.5.5.zip`

**Direct Download / 直接下载：**  
https://icloud.bfsu.edu.cn/seafhttp/f/0a5706e5f2b74eb1af69/?op=view

**Baidu Netdisk / 百度网盘：**  
https://pan.baidu.com/s/1GeVCqrM6Hi1UgILYgkdNhQ?pwd=5pty

**Extraction Code / 提取码：** `5pty`

#### Notes / 使用提示

- 请下载完整 ZIP 压缩包并完整解压后运行，不要只单独移动 EXE 文件；
- 用户模板和 API Key 保存在当前系统用户配置目录中，与软件发布目录分离；
- 大模型功能为可选功能，远程识别结果应在写入项目之前由用户人工检查确认；
- 具体使用方法、Schema 字段说明、批量识别流程和项目 XML 结构请参阅 MetadataLens 目录中的独立 README。

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
- 繁体中文采用项目统一内部代码 `zh_tra`；
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


### 1.4 BFSU WebLens v3.1.4 / 网络语料检索、手动采集与网页下载工具

**BFSU WebLens v3.1.4** is a corpus-oriented web and news collection tool for corpus construction, web discourse research, translation studies, media studies, and multilingual data preparation. It integrates automatic search collection, manual search-page collection, link import, result review, sampling, source-page downloading, metadata extraction, and multilingual clean-text output in a single desktop workflow. WebLens supports both Google and Baidu, while keeping search discovery, result management, and content downloading logically separated.

**BFSU WebLens v3.1.4 / 网络语料检索、手动采集与网页下载工具** 面向网络语料库建设、新闻语料采集、语料库话语研究、国际传播研究、翻译研究和多语种网络数据准备，将搜索结果发现、手动搜索页采集、链接导入、结果整理、抽样、网页正文下载、元信息提取和多语种正文保存整合为统一工作流。软件支持 Google 与百度，并将“搜索结果采集”“结果管理”和“正文下载”相互分离，便于研究者控制采集过程并保留检索依据。

其核心工作流为：

```text
检索参数设置
→ 自动采集 或 手动生成搜索链接并保存搜索结果 HTML
→ 导入并解析搜索结果页
→ Result Preview 去重、排序、抽样与人工编辑
→ 正文下载与最终 URL 解析
→ 正文清洗、元信息补全
→ TXT / XLSX / CSV / DOCX / XML 等格式导出
```

#### Main Features / 主要功能

- 支持 **Google Web、Google News、百度网页、百度资讯/新闻** 等检索场景；
- 支持关键词、精确短语、OR、原始检索式、站点/域名、语种、国家/地区、日期范围等检索条件；
- Google 与百度的日期切片默认值均为 `0`，表示不切片；用户需要时可按指定天数拆分日期范围；
- 自动采集模式通过 Chrome 或 Edge 浏览器执行，并在开始采集前检查 Browser 与 WebDriver 的实际版本及兼容性；
- Chrome 默认采用 **WebLens 内置便携版 Chrome for Testing**，与用户日常 Chrome 环境隔离；Microsoft Edge 默认使用系统安装版本；
- Browser & Selenium 设置支持浏览器检测、便携 Chrome 下载与更新、Driver 检测/更新、手动路径选择、版本匹配校验和配置进度显示；
- 支持用户主动更新 WebLens 内置便携 Chrome 及其匹配 WebDriver；
- 当 Google 或百度出现人工验证时，自动采集可以暂停导航，让用户在当前浏览器窗口中手动完成验证，再继续采集；
- 新增 **Manual Collection / 手动采集**：根据当前 Google 或百度检索参数生成一个或多个搜索引擎 URL，用户可在普通浏览器中手动搜索、翻页并保存结果页 HTML，再由 WebLens 批量导入和解析其中的真实结果链接；
- 手动采集支持批量导入 `.html/.htm` 文件或整个文件夹中的保存页，并自动追加到现有 Result Preview，不覆盖已有结果；
- 支持 **Paste links from text / 从文本粘贴链接**：用户可一次或多次粘贴包含一个或多个 `http://` / `https://` 链接的普通文本、Markdown 或 HTML，软件自动提取、去重并追加到结果列表；
- 支持导入已有链接文件，并将导入结果直接用于后续正文下载；
- Result Preview 支持去重、删除、排序、撤销、重做、重置、简单随机抽样、系统抽样和按来源分层抽样；
- 支持 XLSX、CSV、TXT、DOCX 和 XML 等结果导出；
- 正文下载支持浏览器后端、并发控制、停止、重试、断点续传、最终跳转 URL 更新和下载进度显示；
- 对 Google News 当前使用的 `/goto` 跳转结果进行识别，并在正文下载成功后用最终目标 URL 更新记录；
- 支持网页标题、来源、发布时间、作者、机构、地点、摘要、原始搜索 URL、检索词、搜索引擎、日期范围等语料库建设相关元信息；
- 多语种正文抽取采用分层降级策略，并支持编码检测、乱码修复、正文候选区识别、可见文本抽取和 clean TXT 输出；
- 英文、简体中文、繁体中文界面可切换；User Guide、Parameter Guide 和 About 随当前界面语言切换；
- 支持 Windows 11 高 DPI 缩放；
- 源码层面已加强 **Windows 与 macOS** 兼容，提供 Windows x64、macOS Apple Silicon 和 macOS Intel 的构建脚本；
- Windows 发布版采用 PyInstaller `onedir` 结构，主程序位于外层，运行依赖位于 `_internal`，并使用独立最小构建环境控制发布包体积。

#### Automatic and Manual Collection / 自动与手动采集

WebLens v3.x provides two parallel collection routes:

```text
Automatic Collection
WebLens → Browser/Selenium → Google/Baidu → automatic pagination
→ Result Preview → content download
```

```text
Manual Collection
WebLens → generate search URLs → user searches in a normal browser
→ manually page and save result HTML
→ WebLens imports/parses saved HTML
→ Result Preview → content download
```

手动模式不依赖 Selenium 环境，因此即使自动模式因人机验证、浏览器环境或 Driver 问题暂时无法工作，用户仍可使用相同检索参数生成搜索链接，并通过保存搜索结果 HTML 完成结果采集。

#### Download / 下载

**Current Release / 当前版本：** `BFSU WebLens v3.1.4`

**File / 文件名：** `BFSU_WebLens_v3.1.4_windows_x64.zip`

**Direct Download / 直接下载：**  
https://icloud.bfsu.edu.cn/f/0caa3e3134124f098fc2/

**Baidu Netdisk / 百度网盘：**  
https://pan.baidu.com/s/1diktKNs9tonYpYkfO9mzDg?pwd=si5e

**Extraction Code / 提取码：** `si5e`

#### Notes / 使用提示

- 当前公开下载包为 **Windows x64** 版；
- 下载后请完整解压整个发布目录，不要只单独移动 `BFSU_WebLens.exe`；
- Windows 发布版采用 `onedir` 结构，主程序位于外层，Python、Qt 和其他运行依赖位于 `_internal`；
- Chrome 自动采集默认使用 WebLens 管理的便携 Chrome，以尽量避免影响用户已有浏览器环境；
- Microsoft Edge 默认使用系统安装版，并在采集前检查 Edge 与 EdgeDriver 版本匹配；
- macOS Apple Silicon 和 Intel 已提供源码构建脚本，具体构建方式请参阅 WebLens 目录中的独立 README 与 BUILDING 文档；
- 自动采集和手动采集均应遵守目标网站的服务条款、访问政策、版权、隐私和相关法律法规；
- WebLens 面向科研和语料库建设场景，不建议用于高频、无控制的大规模自动访问。

---

### 1.5 BFSU ClearLens v1.5.11 / BFSU 文本整理器

**BFSU ClearLens** is a batch text organization, deterministic cleaning, encoding-conversion, and optional LLM-assisted review tool in the BFSU LexiScope framework. It is designed for text produced by OCR, web-content extraction, corpus collection, document conversion, and manual transcription. ClearLens imports text-bearing files and outputs organized text; it does not perform OCR, crawl websites, extract metadata, or split files.

**BFSU ClearLens / BFSU 文本整理器** 面向 OCR 后文本、网页正文抽取结果、语料采集文件、格式转换文档和人工转写材料，主要用于批量文本整理、确定性降噪、编码转换、正则处理以及可选的大模型辅助校对。它只负责导入文本并输出整理后的文本，不执行 OCR、不抓取网页、不提取元信息，也不拆分文件。其核心工作流为：

```text
文件或文件夹导入 → 规则预览 → 确定性整理或大模型辅助处理
→ 人工对照与校对 → 编码准备 → 显式保存 → 整理日志导出
```

#### Main Features / 主要功能

- 支持单文件、多文件、文件夹递归和拖放导入，并提供文件队列增删、右键菜单和快捷键；
- 文件发现、解码和批处理在后台运行，提供进度条、强制中止以及多进程/多线程设置；
- 支持换行符、BOM、Unicode 规范化、乱码修复、HTML 实体还原、控制字符、零宽字符和双向控制字符处理；
- 支持清除行首/行尾空白、重复空格、制表符、异常汉字间空格、全部空行和连续空行；
- 支持相邻重复行、全文重复行、重复段落、异常符号行、重复短页眉页脚、OCR 占位符和重复标点处理；
- 支持去除 Emoji，以及 JavaScript、CSS、`noscript`、`template` 等网页代码块；
- 支持段内强制换行重排、英文断行连字符修复和段首缩进整理；
- 支持全角与半角互转、繁简转换以及中文标点与半角标点转换；
- 支持 UTF-8、UTF-16、UTF-32、GB18030、GBK、Big5、Shift-JIS、CP949、CP1252、Latin-1、ASCII 等编码间的严格转换；
- 支持内置及自定义正则规则库、规则测试，并可让大模型根据自然语言需求提出正则表达式方案；
- 支持将当前选项、自定义正则和大模型自然语言规则保存为独立 JSON 整理方案，便于重复使用；
- 支持 OpenAI / ChatGPT 与 DeepSeek。大模型可执行受本机无损校验约束的安全整理，也可提出逐条或批量同意、拒绝的校对建议；
- v1.5.11 增强长文本和密集修改兼容性：支持更大的模型输出容量、自适应分片、结构校验，以及在输出截断、JSON 不兼容或 `too many edits` 时自动缩小片段并重试；
- 大模型任务运行时持续显示当前文件、当前片段、等待时长、超时阈值和重试状态，并允许用户随时中止，避免长时间运行时缺少反馈；
- 自动整理采用文件级事务保护：只有全部片段完整通过本机校验后才写入结果，发生超时、截断或结构不兼容时不会保存半截文本；
- 规则、大模型、转码和人工编辑始终以上一次处理后的当前文本为输入，所有操作依次叠加；只有撤回、重做或恢复原文会还原状态；
- 处理结果先保留在内存中。选择输出目录不会自动写出，只有“保存”“另存为”或“全部保存”才生成结果文件；
- 支持稳定的可编辑预览快照、紧凑的清洗前后对照、差异视图、人工编辑、查找替换、字符统计、整理日志和最近 50 项单文件/多文件撤回重做；
- 软件主窗口及各设置、规则、查找、统计、校对等子窗口统一使用 BFSU ClearLens 主图标；
- 支持选择独立输出目录、保护源文件、保留原目录结构、合并选中文件和合并全部文件；
- 用户设置、自定义正则规则和大模型自然语言规则分别保存在 `%APPDATA%\BFSU_ClearLens` 下的 `settings.json`、`regex_rules.json` 和 `llm_rules.json` 中，更新或替换软件目录时通常可继续沿用；
- API 密钥默认只在当前会话中使用；仅在用户明确启用本机保存时写入本机设置，且不会导出到整理方案。

#### Download / 下载

**File / 文件名：** `BFSU_ClearLens_v1.5.11.zip`

**Windows Executable / Windows 可执行版：**

https://pan.baidu.com/s/1DW9fLMpsL9Mn23fyXc5cTg?pwd=g6zx

**Extraction Code / 提取码：** `g6zx`

#### Notes / 使用提示

- 当前发布版本为 **v1.5.11**。普通用户下载并解压后，应从完整发布目录运行 `BFSU_ClearLens.exe`，不要只移动 EXE 文件；
- `assets`、`config`、`samples`、README 和依赖说明与 EXE 位于同级目录，Python 与第三方运行依赖位于 `_internal`；
- 用户设置和自定义规则默认保存在 `%APPDATA%\BFSU_ClearLens`，升级软件前可直接备份该目录；
- 建议先选择与源文件目录分开的输出目录，检查规则预览和差异视图后再执行批处理；
- 转码命令只在内存中登记目标编码并严格校验，仍需使用保存命令才会写出转换后的文件；
- 大模型功能完全可选。涉及词句或语义的建议应由用户逐条核对，任何远程模型建议都不应视为绝对正确。

---

## 2. Planned Tools / 规划中工具

The following modules are planned or under consideration. They have not yet been fully implemented. Please stay tuned.

以下模块仍在规划或开发中，尚未完整发布，敬请期待。

### 2.1 Corpus Segmenter / 分词、分句与基础统计工具

Planned functions include:

- 中英文分词；
- 分句；
- 字数、词数、句数统计；
- 批量文件统计；
- 多语种基础文本指标；
- Excel 日志导出。

### 2.2 Corpus Analyzer / 语料库数据分析工具

Planned functions include:

- 高频词统计；
- 关键词分析；
- 搭配分析；
- 词丛 / lexical bundles 提取；
- 分布指标计算；
- 标准化频数；
- 统计检验；
- 可视化图表导出。

### 2.3 Corpus Visualizer / 语料库可视化工具

Planned functions include:

- 频数分布图；
- 堆叠柱状图；
- 热图；
- 对应分析图；
- 聚类图；
- 多维分析结果可视化；
- 适合论文发表的图表导出。

### 2.4 LLM Corpus Assistant / 大模型语料库助手

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
1. Use BFSU WebLens to discover web/news URLs through automatic or manual collection, import saved search-result pages or pasted links, download source pages, extract multilingual text, and export search/download metadata.
2. Use BFSU ProofLens to convert scanned PDFs or images into editable text and review OCR output.
3. Import web, OCR, converted, or transcribed text into BFSU ClearLens for deterministic cleaning, regular-expression processing, encoding conversion, and optional guarded LLM review.
4. Inspect the cumulative working result, then explicitly save the cleaned files and cleaning logs.
5. Use BFSU AlignLens to segment and align multilingual or translated texts.
6. Export aligned files as Excel, TMX, XML, JSON, or line-aligned TXT files.
7. Use BFSU MetadataLens to design metadata schemas, create records, and manage corpus metadata.
8. Link web texts, OCR texts, cleaned texts, or aligned files with metadata records.
9. Use future LexiScope modules for annotation, retrieval, statistics, and visualization.
```

典型使用流程可以概括为：

```text
1. 使用 BFSU WebLens 通过自动采集或手动采集发现网络新闻或网页 URL，也可导入保存的搜索结果页或粘贴链接，随后下载来源页面、抽取多语种文本，并导出检索与下载元信息；
2. 使用 BFSU ProofLens 将扫描版 PDF 或图片转换为可编辑文本，并校对 OCR 结果；
3. 将网页文本、OCR 文本、格式转换文本或人工转写文本导入 BFSU ClearLens，执行确定性整理、正则处理、编码转换和可选的受控大模型校对；
4. 检查依次叠加的当前工作结果，再显式保存整理后的文件和整理日志；
5. 使用 BFSU AlignLens 对多语文本、翻译文本或一本多译文本进行分段、分句和对齐；
6. 将对齐结果导出为 Excel、TMX、XML、JSON 或按语种行号对齐的 TXT 文件；
7. 使用 BFSU MetadataLens 设计语料库元信息规范、建立记录并统一管理语料库元信息；
8. 将网页文本、OCR 文本、整理后文本或对齐文件与元信息记录关联；
9. 后续使用 LexiScope 系列工具完成标注、检索、统计和可视化分析。
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

Each subtool may require additional `--add-data`, `--collect-submodules` and `--hidden-import` options. For model-heavy tools such as ProofLens and AlignLens, large model folders are usually copied manually into the packaged folder after PyInstaller packaging. ClearLens uses an `onedir` layout in which runtime dependencies remain in `_internal`, while `assets`, `config`, `samples` and documentation remain beside the executable.

不同子工具可能需要额外的 `--add-data`、`--collect-submodules` 和 `--hidden-import` 参数。对于 ProofLens 和 AlignLens 这类依赖模型的工具，较大的模型文件夹通常建议在 PyInstaller 打包完成后手动复制到打包目录中。ClearLens 采用 `onedir` 结构：运行依赖放在 `_internal`，`assets`、`config`、`samples` 和说明文档与 EXE 同级。

---

## 6. Data and Privacy / 数据与隐私

- Local functions run on the user's computer.
- Project files, metadata records, OCR results, ClearLens working texts and alignment results remain local unless the user explicitly saves, exports or uploads them.
- LLM-assisted functions are optional.
- If an API-based LLM is used, the selected text or prompt content may be sent to the configured API endpoint.
- Users should avoid uploading confidential, sensitive or unpublished data to external APIs unless they have permission to do so.
- API Keys should be stored locally and should not be committed to public repositories.
- In ClearLens, selecting an output folder or running a cleaning command does not save a result file; only explicit save commands write the current working text to disk.

---

## 7. Notes / 注意事项

- BFSU LexiScope is a research-support toolkit, not a fully automatic replacement for expert judgment.
- OCR results, metadata extraction results, cleaned texts, automatic alignment results and LLM suggestions should always be checked by the user.
- Users should verify exported texts, metadata and aligned files before using them in publications, teaching materials, corpus construction or statistical analysis.
- Some functions are still experimental and may change between versions.
- If a function has not yet been released, please treat its description as a development plan rather than a completed feature.

---

## 8. Roadmap / 发展路线

Planned development directions include:

- 完善 WebLens 网络语料采集、正文下载、多语种清洗和来源元信息追踪工作流；
- 完善 OCR 与校对工作流；
- 完善多语翻译对齐、对齐检查和语料导出工作流；
- 增强大模型辅助语料处理能力；
- 持续完善 ClearLens 的确定性规则、格式兼容、大模型安全校对和批量输出工作流；
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

BFSU LexiScope and its subtools are designed for research support, corpus construction and data processing. Automatically generated results, including OCR output, deterministic or LLM-assisted text cleaning, LLM-assisted proofreading, metadata extraction, automatic alignment and future statistical reports, may contain errors. Users are responsible for checking, revising and confirming all outputs before using them for academic publication, teaching, corpus release or formal research analysis.

BFSU LexiScope 及其子工具主要用于科研辅助、语料库建设和数据处理。自动生成结果，包括 OCR 文本、确定性或大模型辅助文本整理、大模型校对建议、元信息抽取、自动对齐结果以及未来的数据分析报告，均可能存在错误。用户在将相关结果用于论文发表、教学材料、语料库发布或正式研究分析前，应自行检查、修订并确认其准确性。
