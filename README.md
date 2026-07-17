# BFSU LexiScope / 北外 LexiScope 语料库智能工具箱

**BFSU LexiScope** is a series of intelligent data processing and data analysis tools for corpus-based linguistic research, corpus construction, translation studies, language education research, and digital humanities.

**BFSU LexiScope / 北外 LexiScope** 是一套面向语料库研究的智能数据处理与数据分析系列工具，旨在为语料库建设、元信息整理、OCR 文本数字化、多语文本对齐、语料清洗、人工智能辅助校对、数据导入导出和后续统计分析提供统一、轻量、可扩展的桌面工具生态。

当前已发布的核心工具包括： 
 
- **BFSU MetaTools / 语言学语料库元信息制作工具**
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


### 1.4 BFSU WebLens v1.2.8 / 网络语料检索与网页下载工具

**BFSU WebLens v1.2.8** is a conservative web-search, URL discovery, source-page downloading, and multilingual text-extraction tool for corpus construction and web-based discourse research. It is designed for researchers who need low-frequency, auditable collection rather than high-frequency crawling. WebLens provides separated Google and Baidu workflows, traceable query metadata, result preview and sampling, source-page downloading, multilingual encoding repair, clean-text output, and breakpoint continuation for content downloads.

**BFSU WebLens v1.2.8 / 网络语料检索与网页下载工具** 面向网络语料库建设、新闻语料采集、语料库话语研究、国际传播研究、翻译与传媒研究中的网页材料准备。它不是高频爬虫，而是一款强调低频、保守、可审计和可追溯的网络语料发现与正文下载工具，重点解决搜索结果 URL 获取、查询过程记录、网页正文抽取、多语种编码修复、语料文本保存以及来源元信息导出等问题。其核心工作流为：

```text
检索设置 → Google / 百度低频检索 → URL 结果预览与去重
→ 抽样、排序或人工编辑 → 多格式导出 → 正文下载
→ 多语种编码修复与正文清洗 → 语料 TXT 与 metadata 保存
```

#### Interface and Interaction / 界面与交互

- 保留传统桌面软件布局和传统菜单栏，Google / 百度标签页、左侧设置区、右侧结果预览区和日志区的整体工作流不变；
- 主界面和应用内对话框优先采用 **CustomTkinter**，框架、分组面板、按钮、输入框、下拉框、复选框、多行文本框、进度条、标签页、可拖动分栏和日期控件均使用 CTk 风格；
- 仅传统菜单、结果 `Treeview`、多选 `Listbox` 等 CustomTkinter 无直接替代的组件继续使用 Tk/ttk，并统一应用 LexiScope 配色和 DPI 指标；
- 界面配色、边框、圆角、字体节奏、控件高度和布局间距与 **BFSU ClearLens / LexiScope** 视觉风格保持一致；
- 左侧设置栏采用可滚动 CTk 面板。鼠标位于设置区任意位置时均可直接使用滚轮，包括检索词文本框、域名输入框以及语种和国家/地区列表；
- Google / 百度标签压缩并放置在左上角，为结果预览和日志区域保留更多垂直空间；
- 启动时适当增加左侧设置区宽度，减少按钮、标签和输入控件显示不完整的问题；
- Result Preview 工具栏划分为带边框的 **记录操作、排序、采样、正文下载** 四个功能区，避免不同用途的按钮混排；
- 顶部工具栏提供 **Open downloads / 打开下载文件夹**，可创建并打开当前面板所设置的正文下载目录；
- 重新绘制与 ClearLens 一致的 WebLens 高清图标，并提供 16–256 px 多分辨率 ICO 和专用小尺寸 PNG，提高 Windows 标题栏与任务栏图标清晰度；
- 关于、说明、设置、正文下载设置和日期选择等窗口均使用统一图标和 CTk 风格。

#### Windows 11 DPI and Window Positioning / Windows 11 缩放与窗口定位

- 在创建界面前启用 Windows 11 每显示器 DPI 感知，适配高分辨率显示器和 125%、150%、175%、200%、225% 等缩放比例；
- 原生菜单和 Treeview 使用 DPI 适配后的字体与行高；
- 主窗口和各子窗口会根据 Windows 可用工作区自动限制初始尺寸，避免打开后只显示局部；
- v1.2.8 修正了窗口反复自动回到启动位置的问题：主窗口仅在启动时定位一次，后台任务轮询不再重复调用居中函数，因此用户可以自由拖动窗口；
- 窗口定位区分 CustomTkinter 逻辑尺寸与显示器物理像素，并扣除 Windows 任务栏占用区域，避免窗口右侧或底部藏到桌面之外。

#### Search and Collection / 检索与采集

- Google 和百度采用独立面板，两个搜索引擎的设置、日志、结果预览、采样、导出和正文下载互不混合；
- Google 支持普通网页检索与 Google News 检索；
- Google 支持单词、任一词 / OR、全部词、精确短语、任一精确短语 / OR 和原始检索式等查询辅助模式；
- Google 支持结果语种、国家/地区、站点/域名以及日期范围限定；
- Google 的 **Results per page / 每页结果数** 默认值为 **10**，并写入 `config/default_settings.json`；旧版仍保留原默认值 50 的设置会自动迁移为 10；
- 百度支持百度网页、百度资讯和百度资讯媒体网站；
- 百度通过 `site:{domain}` 限定来源网站，通过 `gpc=stf=...|stftype=2` 与 `tfflag=1` 实现日期范围过滤，并可使用 `medium=1` 筛选媒体资讯结果；
- Google 与百度均支持多行站点/域名限定，每行可填写一个域名、域名后缀或 `site:` 表达式；
- 支持 requests、Selenium Chrome 和 Selenium Edge 等检索方式，并提供页面延时、切片延时、错误冷却和浏览器定期重启等参数；
- 默认采用较长的低频访问延时，便于降低访问压力并提高页面加载完整性；
- 当 Selenium 遇到 Google 人机验证页面时，WebLens 会保留当前浏览器并暂停自动翻页，允许用户手动完成验证；验证页面消失后可继续解析和采集；
- 支持连续无新增页面自动停止，避免 Home、Map 等重复导航链接导致任务无法结束。

#### Result Management and Export / 结果管理与导出

- 支持搜索结果预览、去重、排序、人工编辑、撤销、重做和恢复初始采集结果；
- 支持简单随机抽样、系统抽样以及按来源分层抽样；
- 支持导入已有链接，并对导入或采集结果执行正文下载；
- 支持导出 XLSX、CSV、TXT、DOCX 和 XML；
- 元信息字段尽量保存查询词、标题、URL、摘要、来源域名、作者、出版机构、地点、发布时间、抓取时间、日期切片和搜索引擎等信息；
- XLSX 适合用作网络语料库建设日志和来源元信息表。

#### Content Download and Text Extraction / 正文下载与文本抽取

- 正文下载模式可选 requests、Selenium 或混合模式；
- 支持多线程、失败重试、单条任务超时、停止下载、同域名串行控制和下载进度显示；
- 支持正文下载断点续传：成功记录即时写入 `content_manifest.jsonl`，重新选择同一下载目录和同一批 URL 时会跳过已完成项目；
- 断点续传仅用于正文下载，不用于搜索结果采集，避免软件在用户不知情的情况下继续访问搜索引擎；
- 多语种正文抽取采用分层降级策略，包括原始字节保存、编码自动检测、乱码修复、`newspaper3k`、站点模板、`article/main/content` 候选区、可见文本抽取和 clean TXT 输出；
- 对中文新闻网页和常见 mojibake 乱码进行了增强兼容；
- 下载结果可保存正文文本、原始页面、下载状态和对应 metadata，便于后续导入 BFSU ClearLens、MetaTools 或其它语料库处理流程。

#### Packaging / 打包结构

WebLens 采用 PyInstaller `onedir` 发布结构。普通用户应完整解压后，从发布目录运行 `BFSU_WebLens.exe`，不要单独移动 EXE 文件。

```text
BFSU_WebLens/
  BFSU_WebLens.exe
  README.md
  requirements.txt
  config/
  assets/
  preinstall/
  _internal/
```

`requirements.txt` 明确包含 `customtkinter` 和 `pillow`；打包脚本会收集 CustomTkinter、图标资源、配置文件、Selenium 支持和正文抽取依赖。

#### Download / 下载

**Current Release / 当前版本：** `BFSU WebLens v1.2.8`

**File / 文件名：** `BFSU_WebLens_v1.2.8.zip`

**Baidu Netdisk / 百度网盘：**

https://pan.baidu.com/s/1UXTRIJpFbXJnMCHMTxbWPA?pwd=kvst

**Extraction Code / 提取码：** `kvst`

#### Notes / 使用提示

- 下载后请完整解压，并保持主程序、`_internal`、`assets`、`config` 和其它配套文件的相对位置不变；
- 如果使用 Selenium Chrome 或 Selenium Edge，可根据发布包说明准备兼容的浏览器和驱动；
- 如果只使用 requests 后端，通常不需要安装额外浏览器；
- WebLens 仅用于合法、低频、研究导向的网页发现和语料准备；
- 用户应自行遵守目标网站的服务条款、robots/访问政策、版权、隐私、访问频率限制以及相关法律法规。

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
1. Use BFSU WebLens to discover web/news URLs, archive source pages, extract multilingual text, and export search/download metadata.
2. Use BFSU ProofLens to convert scanned PDFs or images into editable text and review OCR output.
3. Import web, OCR, converted, or transcribed text into BFSU ClearLens for deterministic cleaning, regular-expression processing, encoding conversion, and optional guarded LLM review.
4. Inspect the cumulative working result, then explicitly save the cleaned files and cleaning logs.
5. Use BFSU AlignLens to segment and align multilingual or translated texts.
6. Export aligned files as Excel, TMX, XML, JSON, or line-aligned TXT files.
7. Use BFSU MetaTools to create metadata schemas and records.
8. Link web texts, OCR texts, cleaned texts, or aligned files with metadata records.
9. Use future LexiScope modules for annotation, retrieval, statistics, and visualization.
```

典型使用流程可以概括为：

```text
1. 使用 BFSU WebLens 发现网络新闻或网页 URL，保存来源页面，抽取多语种文本，并导出检索与下载元信息；
2. 使用 BFSU ProofLens 将扫描版 PDF 或图片转换为可编辑文本，并校对 OCR 结果；
3. 将网页文本、OCR 文本、格式转换文本或人工转写文本导入 BFSU ClearLens，执行确定性整理、正则处理、编码转换和可选的受控大模型校对；
4. 检查依次叠加的当前工作结果，再显式保存整理后的文件和整理日志；
5. 使用 BFSU AlignLens 对多语文本、翻译文本或一本多译文本进行分段、分句和对齐；
6. 将对齐结果导出为 Excel、TMX、XML、JSON 或按语种行号对齐的 TXT 文件；
7. 使用 BFSU MetaTools 建立语料库元信息规范和记录；
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
