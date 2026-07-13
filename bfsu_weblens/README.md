# BFSU WebLens v1.2.4

**BFSU WebLens** is a desktop component of the **BFSU LexiScope** toolkit. It is designed for corpus researchers who need low-frequency, auditable search-result discovery, URL collection, source-page downloading, and multilingual text cleaning.

Author and project lead: **Liu Dingjia, Beijing Foreign Studies University**. ChatGPT assisted with requirement analysis, prototyping, code generation, refactoring, testing strategy, documentation drafting, and debugging suggestions. The software concept, corpus workflow, naming, parameter strategy, and final use decisions are directed by Liu Dingjia.

---

## English README

### 1. Project positioning

BFSU WebLens is designed for corpus-oriented web data preparation. It helps users discover search results from Google and Baidu, inspect and edit URL lists, export structured search metadata, and download source pages into raw HTML, raw text, clean text, and metadata files.

WebLens is **not** a high-frequency crawler. It is intended as a conservative research assistant for traceable URL discovery and source-page archiving. The default delays are intentionally long so that users can run small, documented, and reproducible collection tasks.

WebLens follows five design principles:

1. **Separated engines**: Google and Baidu are implemented as separate panels with separate settings, logs, result previews, exports, and download actions.
2. **Auditability**: query expressions, generated search URLs, date windows, site limits, engine metadata, result metadata, and content metadata are retained whenever possible.
3. **Conservative access**: page delays, slice delays, browser restart intervals, and stop conditions are configurable and intentionally conservative by default.
4. **Multilingual downloading**: content extraction does not depend on one parser only. It uses encoding detection, mojibake repair, newspaper3k, known-site templates, article/main/content candidates, visible-text fallback, and clean TXT output.
5. **Limited checkpointing**: search-result crawling is deliberately not resumed after forced closure. Breakpoint continuation is available only for content downloading after URLs have already been crawled or imported.

---

### 2. Windows executable download

A pre-built Windows desktop package is available for users who do not want to configure Python manually.

**Baidu Netdisk download**

```text
File: BFSU_WebLens.zip
Link: https://pan.baidu.com/s/1UFnlZqa8PsA3TDZDqQfe0g
Extraction code: s4mp
```

Recommended use:

1. Download `BFSU_WebLens.zip` from the link above.
2. Extract the whole zip package to a local folder, for example:

```text
D:\BFSU_LexiScope\BFSU_WebLens\
```

3. Run:

```text
BFSU_WebLens.exe
```

4. Do **not** move `BFSU_WebLens.exe` away from its folder. The executable depends on files stored under `_internal`.
5. If Windows SmartScreen or antivirus software warns about an unsigned executable, verify that the package comes from the official shared link before allowing it to run.
6. If Selenium mode is used, make sure Chrome or Edge is installed. The Windows executable package includes a `preinstall` folder at the software root. It contains two browser installers prepared for the bundled WebDriver/Selenium environment:

```text
preinstall/
  google-chrome-beta-150-0-7871-46.msi
  microsoft-edge-150-0-4078-48.msi
```

   Users who plan to use Selenium Chrome or Selenium Edge are strongly advised to install these two packages first, unless their system already has a compatible browser major version. The bundled browser drivers are intended to match these browser builds as closely as possible. Installing them helps avoid common Selenium errors caused by Chrome/Edge and WebDriver major-version mismatch.
7. Use the default installation location when installing the browsers if possible. If Chrome or Edge is installed in a non-standard path, set **Driver path** and **Browser binary path** manually in WebLens. The driver path should normally point to `tools/chromedriver.exe` or `tools/msedgedriver.exe`; the browser binary path should point to `chrome.exe` or `msedge.exe`.
8. Users who only use the Requests backend do not need these browsers for ordinary content downloading. They are mainly needed for Selenium search-result crawling, JavaScript-rendered pages, debugging, and pages where Requests cannot obtain complete HTML.
9. If Windows SmartScreen or antivirus software warns about the browser installers or the unsigned WebLens executable, verify that the files come from the official shared package before allowing them to run.

Expected desktop package structure:

```text
BFSU_WebLens/
  BFSU_WebLens.exe
  README.md
  requirements.txt
  preinstall/
    google-chrome-beta-150-0-7871-46.msi
    microsoft-edge-150-0-4078-48.msi
  _internal/
    assets/
    tools/
    ...runtime dependencies...
```

The Windows executable package is the recommended option for ordinary users. Developers who need to inspect or modify the source code may use the source-code workflow described below.

---

### 3. Main functions

WebLens currently provides two independent engine panels.

#### 3.1 Google panel

The Google panel supports:

- Google Web search.
- Google News search.
- Query-helper modes:
  - Single term.
  - Any term / OR.
  - All terms.
  - Exact phrase.
  - Any exact phrase / OR.
  - Raw Google query.
- Result-language restriction through Google `lr`.
- Country/region restriction through Google `cr`.
- Multi-line site/domain filtering through `site:` syntax and local URL filtering.
- Date range and date slicing.
- Requests, Selenium Chrome, or Selenium Edge backend.
- Configurable page delay, slice delay, error cooldown, and browser restart interval.
- Independent result preview, sampling, editing, exporting, and content downloading.

#### 3.2 Baidu panel

The Baidu panel supports:

- Baidu Web search.
- Baidu News/Information search.
- Baidu News - media sites, using the observed `medium=1` filter.
- Baidu sorting options where Baidu respects the parameter.
- Multi-line site/domain filtering by inserting `site:{domain}` into Baidu `wd` and applying local URL filtering.
- Date filtering using observed Baidu `gpc=stf=...|stftype=2` and `tfflag=1` parameters.
- Requests-first workflow, with Selenium available when requests cannot retrieve or render the needed content.

The Baidu panel intentionally does **not** include Google-style language restriction, Google-style country/region restriction, Google Any/OR helper modes, or Bing controls.

---

### 4. What changed in v1.2.4

- The **Site/domain filters** field in both Google and Baidu panels is now a **multi-line input box**.
- Users can enter one domain, suffix, or `site:` expression per line.
- The backend still accepts semicolon-separated values for compatibility with earlier settings.
- `build_exe.bat` now builds from an isolated local virtual environment `.venv_build`.
- The PyInstaller desktop build uses **onedir** mode and places runtime dependencies under `_internal`.
- Selenium packaging has been fixed by explicitly collecting dynamically imported Selenium browser-driver modules, including Chrome and Edge modules.
- Help, About, User Guide, Parameter Guide, and README content have been expanded.
- The Windows executable download information has been added to this README.

Example site/domain field:

```text
people.com.cn
xinhuanet.com
.gov.cn
.edu.cn
site:thepaper.cn
```

---

### 5. Important default values

| Parameter | Google default | Baidu default | Meaning |
|---|---:|---:|---|
| Day step | 7 | 0 | Number of days per date slice. `0` means no slicing. |
| Max pages per slice | 30 | 100 | Maximum search-result pages requested inside each date slice. |
| Stop after no-new pages | 1 | 1 | Stop the current slice after N consecutive pages add no new valid links. |
| Browser restart every N pages | 4 | 0 | Selenium search-session browser reset interval. `0` disables page-count reset. |
| Page delay | 30,000–90,000 ms | 30,000–90,000 ms | Random wait between search-result pages. |
| Content fetch mode | mixed | mixed | Requests first + Selenium fallback. |
| Content retry count | 1 | 1 | Retry failed content URLs before marking failure. |
| Single content task timeout | 300 s | 300 s | GUI-level hard timeout for one content URL. |
| Resume content downloads | enabled | enabled | Skip already successful content URLs based on manifest. |

---

### 6. Parameter guide

#### Panel

Choose the engine workflow. Google and Baidu results do not share one preview table. Sampling, export, and content download actions apply to the active panel only.

#### Query mode

Google includes helper modes for OR and exact phrase OR. Baidu removes these helper modes because Baidu query behavior is less stable with complex Boolean expressions. Raw query mode remains available for expert users.

#### Search terms / phrases

Enter topic words or phrases. One item per line is recommended. In raw query mode, WebLens treats the text as the query expression.

#### Site/domain filters

This is a multi-line field. Put one domain, suffix, or `site:` expression per line.

Examples:

```text
people.com.cn
xinhuanet.com
.gov
.edu.cn
site:thepaper.cn
```

How WebLens uses this field:

- **Google**: adds `site:` constraints to the query and applies local URL filtering after parsing.
- **Baidu**: inserts `site:{domain}` into the Baidu `wd` query and applies local URL filtering after parsing.
- **Domain suffixes**: `.gov`, `.edu.cn`, `.gov.cn` match hosts ending with those suffixes.
- **Raw query caution**: if the raw query already contains `site:`, leave this field empty to avoid duplicate constraints.

For strict source-specific corpora, run separate tasks for each domain when possible, because search engines may handle complex multi-site expressions differently.

#### Search vertical

- Google Web: ordinary Google search-result pages.
- Google News: adds the news vertical parameter.
- Baidu Web: uses Baidu ordinary web search.
- Baidu News/Information: uses Baidu information/news search.
- Baidu News - media sites: applies the observed Baidu media-site filter.

#### Baidu sort

- Focus/relevance: observed `rtt=1` behavior.
- Time: observed time-sort behavior where Baidu respects it.

Baidu may change its behavior, so WebLens records `search_url` for verification.

#### Language and country/region restrictions

These are Google-only controls.

- `lr` restricts result document language, for example `lang_en`.
- `cr` restricts Google's country/region result collection, for example `countryUS`.

These are search constraints, not final truth about outlet location, author nationality, or document quality.

#### Date range and day step

Start date and End date define the total search window.

Day step controls slicing:

- `0`: no slicing; search the full date window as one slice.
- `1`: daily slices.
- `7`: weekly slices.

Smaller slices reduce truncation bias for popular topics but increase request count and runtime.

#### Max pages per slice

Maximum pages requested within one date slice. If day step is small, this value applies separately to each slice.

#### Stop after no-new pages

Stops a slice after N consecutive pages add no new valid URLs after filtering and deduplication. Default is `1`.

#### Fetch backend

- Requests: faster and lighter, but cannot execute JavaScript.
- Selenium Chrome/Edge: opens a real browser; useful for rendered pages, debugging, redirect diagnosis, and pages where requests returns incomplete HTML.

#### Browser restart every N pages

Only affects Selenium search-result crawling.

- `0`: do not automatically restart by page count.
- Google default: `4`.
- Baidu default: `0`.

#### Delays

- Page delay: wait between result pages.
- Slice delay: wait between date slices.
- Error cooldown: wait after temporary failures.

All values are milliseconds. Defaults are conservative to reduce access pressure and improve reproducibility.

#### Output format

XLSX is recommended for research logging. CSV, TXT, DOCX, and XML are also available.

---

### 7. Content download guide

After crawling or importing links, use **Download selected content** or **Download all content**.

Content download settings include:

- Content folder.
- Content threads.
- Content fetch mode.
- Content page delay.
- Content receive/render wait.
- Cleaning scheme.
- Retry failed content N times.
- Single content task timeout seconds.
- Resume content downloads.
- Domain lock timeout.

Downloaded content is saved to subfolders such as:

```text
content_downloads/
  raw_html/
  raw_text/
  clean_text/
  metadata/
  content_manifest.jsonl
  content_metadata.xlsx
```

#### Breakpoint continuation for content downloads

If the software or computer is force-closed during content downloading:

1. Restart WebLens.
2. Load, crawl, or import the same links.
3. Select the same content download folder.
4. Start content download again.

WebLens reads `content_manifest.jsonl` and skips URLs already marked successful. Failed, timed-out, or unfinished URLs are attempted again.

This feature applies **only to content downloading**. Search-result crawling is not resumed automatically.

---

### 8. Multilingual extraction strategy

WebLens does not assume that every page is English or that `newspaper3k` can parse every site. The download pipeline uses layered fallback:

1. Preserve raw bytes when available.
2. Detect declared and apparent encoding.
3. Repair common mojibake, especially UTF-8 text wrongly decoded as Latin-1.
4. Try `newspaper3k` if available.
5. Use built-in source templates for known news sites.
6. Extract from `article`, `main`, `content`, `post`, `story`, or similar candidate containers.
7. Fall back to visible-text extraction.
8. Save clean TXT and metadata even when extraction is imperfect.

This improves Chinese pages returned by Baidu and also helps other non-English sources where specialized extractors fail.

---

### 9. Source-code installation and desktop build

Developers can run the software from source or rebuild the desktop package.

Create a Python environment and install dependencies:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

To build the Windows desktop package, use Windows Command Prompt or PowerShell in the project directory:

```bat
build_exe.bat
```

The build script creates and uses a local build-only virtual environment:

```text
.venv_build
```

This keeps the PyInstaller build independent from the user's normal Python, Anaconda, or PyCharm environment and reduces accidental dependency bloat. To recreate the build environment from scratch after changing dependencies, run:

```bat
build_exe.bat --fresh
```

The script installs `requirements.txt` inside `.venv_build`, then uses PyInstaller onedir mode with `_internal` as the dependency/resource folder:

```bat
--onedir --contents-directory "_internal"
```

Target output:

```text
dist\BFSU_WebLens\BFSU_WebLens.exe
dist\BFSU_WebLens\_internal\...
```

Important components are kept in the release: `assets`, `tools`, `preinstall`, Selenium support, newspaper3k, openpyxl, python-docx, charset detection/repair, and multilingual text extraction dependencies. The `preinstall` folder should include the Chrome Beta and Microsoft Edge MSI installers used to match the bundled WebDriver/Selenium setup. For release, zip the entire `dist\BFSU_WebLens` folder. Do not move `BFSU_WebLens.exe` away from `_internal`, because the executable depends on files inside `_internal`.

#### Selenium packaging fix in v1.2.4

The build script explicitly collects Selenium's dynamically imported browser-driver modules, including `selenium.webdriver.chrome.webdriver` and the Edge equivalents. If an older packaged desktop build reports `No module named 'selenium.webdriver.chrome.webdriver'`, rebuild with:

```bat
build_exe.bat --fresh
```

Then redistribute the entire `dist\BFSU_WebLens` folder. Do not copy only the executable.

---

### 10. Compliance and disclaimer

BFSU WebLens is intended for lawful, modest, research-oriented web discovery and corpus preparation. Users are responsible for respecting:

- Website terms of service.
- Robots/access policies.
- Copyright and database rights.
- Privacy and personal data rules.
- Institutional requirements.
- Rate limits and technical access controls.
- Applicable laws and regulations.

The software does not guarantee complete retrieval, stable search-engine behavior, exact metadata, successful extraction from every source, or rights clearance for downloaded content. Search engines and news sites may change layout or impose access controls at any time. Use conservative delays, review samples, retain source URLs, and verify outputs before analysis, redistribution, or publication.

---

# BFSU WebLens v1.2.4 中文说明

**BFSU WebLens** 是 **BFSU LexiScope** 工具箱的桌面组件，面向语料库研究中的低频、可审计网页检索、新闻检索、URL 发现、来源网页下载和多语种文本清理。

作者与项目主导：**刘鼎甲，北京外国语大学**。ChatGPT 参与需求分析、原型设计、代码生成、重构、测试思路、文档起草和调试建议。软件构想、语料库工作流、命名、参数策略和最终使用决策由刘鼎甲主导。

---

## 1. 项目定位

BFSU WebLens 服务于语料库研究中的网络文本准备工作。它可以帮助用户从 Google 和百度发现检索结果，检查和编辑 URL 列表，导出结构化检索元信息，并将来源网页下载为 raw HTML、raw text、clean text 和 metadata 文件。

WebLens **不是高频爬虫工具**。它的定位是保守、低频、可追溯的研究辅助工具，用于建立可审计的 URL 清单和网页存档。软件默认延时较长，目的是鼓励用户进行小规模、可记录、可复核的采集。

WebLens 遵循五项设计原则：

1. **引擎分离**：Google 和百度拥有独立面板、独立设置、独立日志、独立预览、独立导出和独立下载入口。
2. **可审计性**：尽可能记录检索式、生成的搜索 URL、日期窗口、站点限定、搜索引擎元信息、结果元信息和正文元信息。
3. **保守访问**：页面延时、切片延时、浏览器重启间隔和停止条件均可调，默认值偏保守。
4. **多语种下载**：正文抽取不依赖单一包，而是结合编码检测、乱码修复、newspaper3k、站点模板、article/main/content 候选区、可见文本降级抽取和 clean TXT 输出。
5. **有限断点续传**：搜索结果爬取在强制关闭后不会自动续爬；断点续传只适用于已经获得 URL 后的正文下载。

---

## 2. Windows 可执行版下载

对于不希望手动配置 Python 环境的用户，可以直接下载预构建的 Windows 桌面版。

**百度网盘下载**

```text
文件：BFSU_WebLens.zip
链接：https://pan.baidu.com/s/1UFnlZqa8PsA3TDZDqQfe0g
提取码：s4mp
```

推荐使用方式：

1. 从上方链接下载 `BFSU_WebLens.zip`。
2. 将整个压缩包完整解压到本地目录，例如：

```text
D:\BFSU_LexiScope\BFSU_WebLens\
```

3. 运行：

```text
BFSU_WebLens.exe
```

4. 不要将 `BFSU_WebLens.exe` 单独移动到其它目录。该 exe 依赖 `_internal` 文件夹中的资源和运行库。
5. 如果 Windows SmartScreen 或杀毒软件提示未签名程序，请确认压缩包来自官方分享链接后再决定是否允许运行。
6. 如需使用 Selenium 模式，请确保本机已安装 Chrome 或 Edge。Windows 可执行版的软件根目录中包含 `preinstall` 文件夹，里面放置了两个为当前内置 WebDriver/Selenium 环境准备的浏览器安装包：

```text
preinstall/
  google-chrome-beta-150-0-7871-46.msi
  microsoft-edge-150-0-4078-48.msi
```

   计划使用 Selenium Chrome 或 Selenium Edge 的用户，建议先安装这两个浏览器安装包，除非本机已经安装了兼容的浏览器主版本。内置的浏览器驱动主要用于适配这些浏览器版本，安装后可减少 Chrome/Edge 与 WebDriver 主版本不一致导致的 Selenium 启动错误。
7. 安装浏览器时建议使用默认安装路径。如果 Chrome 或 Edge 安装在非标准路径，请在 WebLens 中手动设置 **Driver path** 和 **Browser binary path**。Driver path 通常指向 `tools/chromedriver.exe` 或 `tools/msedgedriver.exe`；Browser binary path 应指向 `chrome.exe` 或 `msedge.exe`。
8. 如果只使用 Requests 后端，普通正文下载通常不需要安装这些浏览器。它们主要用于 Selenium 搜索结果爬取、JavaScript 渲染页面、调试页面加载过程，以及 Requests 无法获取完整 HTML 的网页。
9. 如果 Windows SmartScreen 或杀毒软件对浏览器安装包或未签名的 WebLens 可执行文件发出提示，请先确认文件来自官方分享包，再决定是否允许运行。

桌面版预期目录结构如下：

```text
BFSU_WebLens/
  BFSU_WebLens.exe
  README.md
  requirements.txt
  preinstall/
    google-chrome-beta-150-0-7871-46.msi
    microsoft-edge-150-0-4078-48.msi
  _internal/
    assets/
    tools/
    ...运行依赖...
```

普通用户建议优先使用 Windows 可执行版。需要查看或修改源代码的开发者可参考下文的源代码运行和打包方式。

---

## 3. 主要功能

WebLens 当前提供两个互相独立的搜索引擎面板。

### 3.1 Google 面板

Google 面板支持：

- Google 网页检索。
- Google 新闻检索。
- 检索辅助模式：
  - 单个检索词。
  - 任一词 / OR。
  - 所有词。
  - 严格短语。
  - 任一严格短语 / OR。
  - 原始 Google 检索式。
- 通过 Google `lr` 进行结果语种限定。
- 通过 Google `cr` 进行国家/地区结果限定。
- 通过多行 Site/domain filters 使用 `site:` 语法和本地 URL 过滤进行来源限定。
- 日期范围与日期切片。
- Requests、Selenium Chrome 或 Selenium Edge 后端。
- 可调页面延时、切片延时、错误冷却时间和浏览器重启间隔。
- 独立结果预览、采样、编辑、导出和正文下载。

### 3.2 百度面板

百度面板支持：

- 百度网页检索。
- 百度资讯检索。
- 百度资讯媒体网站检索，使用观察到的 `medium=1` 过滤条件。
- 百度排序选项，在百度实际接受参数时生效。
- 通过在百度 `wd` 中写入 `site:{domain}` 并结合本地 URL 过滤实现多行站点/域名限定。
- 使用观察到的百度 `gpc=stf=...|stftype=2` 与 `tfflag=1` 参数进行日期范围过滤。
- 默认 requests 优先；在 requests 无法获得或渲染所需内容时，可切换 Selenium。

百度面板有意不包含 Google 风格的语种限定、国家/地区限定、Any/OR 辅助模式和 Bing 控件。

---

## 4. v1.2.4 主要变化

- Google 和百度面板中的 **Site/domain filters / 站点与域名限定** 改为 **多行输入框**。
- 用户可以每行填写一个域名、域名后缀或 `site:` 表达式。
- 后端继续兼容早期设置中使用英文分号分隔的写法。
- `build_exe.bat` 现在从本地隔离虚拟环境 `.venv_build` 构建。
- PyInstaller 桌面版使用 **onedir** 模式，并将运行依赖放入 `_internal`。
- 显式收集 Selenium 动态导入的 Chrome 和 Edge 浏览器驱动模块，修复打包后 Selenium 模块缺失问题。
- Help、About、User Guide、Parameter Guide 和 README 均已扩写。
- 本 README 新增 Windows 可执行版下载信息。

站点/域名输入示例：

```text
people.com.cn
xinhuanet.com
.gov.cn
.edu.cn
site:thepaper.cn
```

---

## 5. 重要默认参数

| 参数 | Google 默认值 | 百度默认值 | 含义 |
|---|---:|---:|---|
| Day step / 日期步长 | 7 | 0 | 每个日期切片覆盖的天数。`0` 表示不切片。 |
| Max pages per slice / 每个切片最大页数 | 30 | 100 | 一个日期切片内最多请求的搜索结果页数。 |
| Stop after no-new pages / 连续无新增页停止 | 1 | 1 | 连续 N 页没有新增有效链接后停止当前切片。 |
| Browser restart every N pages / 每 N 页重启浏览器 | 4 | 0 | Selenium 搜索会话的浏览器重启间隔。`0` 表示不按页数自动重启。 |
| Page delay / 页面延时 | 30,000–90,000 ms | 30,000–90,000 ms | 搜索结果页之间的随机等待时间。 |
| Content fetch mode / 正文下载模式 | mixed | mixed | requests 优先，失败后 Selenium 降级。 |
| Content retry count / 正文失败重试次数 | 1 | 1 | 正文链接失败后再次尝试的次数。 |
| Single content task timeout / 单条正文任务超时 | 300 s | 300 s | 单个正文 URL 的 GUI 层超时上限。 |
| Resume content downloads / 正文断点续传 | 开启 | 开启 | 基于 manifest 跳过已经成功下载的 URL。 |

---

## 6. 参数说明

### Panel / 面板

选择搜索引擎工作流。Google 与百度结果不共用同一个预览表。采样、导出和正文下载只作用于当前面板。

### Query mode / 检索模式

Google 提供 OR 和严格短语 OR 等辅助模式。百度移除这些辅助模式，因为百度对复杂布尔检索式的行为不如 Google 稳定。高级用户仍可使用 Raw query / 原始检索式。

### Search terms / phrases / 检索词与短语

输入主题词或短语。建议每行一个项目。在原始检索式模式下，WebLens 会把输入文本视为完整检索式。

### Site/domain filters / 站点与域名限定

这是多行输入框。每行填写一个域名、后缀或 `site:` 表达式。

示例：

```text
people.com.cn
xinhuanet.com
.gov
.edu.cn
site:thepaper.cn
```

WebLens 的处理方式：

- **Google**：将 `site:` 约束加入查询式，并在解析搜索结果后进行本地 URL 过滤。
- **百度**：将 `site:{domain}` 写入百度 `wd` 查询词，并在解析搜索结果后进行本地 URL 过滤。
- **域名后缀**：`.gov`、`.edu.cn`、`.gov.cn` 匹配以这些后缀结尾的主机名。
- **原始检索式注意事项**：如果原始查询中已经包含 `site:`，建议此处留空，避免重复限定。

如果要建立严格来源语料库，建议尽量按重点域名单独分批采集，因为搜索引擎对复杂多站点表达式的处理可能不一致。

### Search vertical / 检索范围

- Google Web：普通 Google 网页结果。
- Google News：Google 新闻结果。
- Baidu Web：普通百度网页结果。
- Baidu News/Information：百度资讯结果。
- Baidu News - media sites：百度资讯中的媒体网站结果。

### Baidu sort / 百度排序

- Focus/relevance：观察到的 `rtt=1` 行为。
- Time：百度接受相关参数时的时间排序行为。

百度可能随时调整前端参数行为，因此 WebLens 会记录 `search_url` 以便复核。

### Language and country/region restrictions / 语种与国家地区限定

这是 Google 专用控制项。

- `lr` 限定结果文档语种，例如 `lang_en`。
- `cr` 限定 Google 的国家/地区结果集合，例如 `countryUS`。

这些只是搜索约束，不等同于媒体所在地、作者国籍或文档质量判断。

### Date range and day step / 日期范围与日期步长

Start date 和 End date 定义总检索时间窗口。

Day step 控制日期切片：

- `0`：不切片，将完整日期窗口作为一个切片。
- `1`：逐日切片。
- `7`：按周切片。

较小切片可以减少热门主题被搜索引擎结果上限截断的风险，但会增加请求次数和运行时间。

### Max pages per slice / 每个切片最大页数

一个日期切片内最多请求多少页。如果日期步长较小，该页数限制会分别作用于每个切片。

### Stop after no-new pages / 连续无新增页停止

在过滤和去重后，若连续 N 页没有新增有效 URL，则停止当前切片。默认值为 `1`。

### Fetch backend / 获取后端

- Requests：速度较快，资源占用小，但不能执行 JavaScript。
- Selenium Chrome/Edge：打开真实浏览器，适合渲染页面、调试跳转、诊断验证码或处理 requests 返回不完整 HTML 的情况。

### Browser restart every N pages / 每 N 页重启浏览器

仅影响 Selenium 搜索结果爬取。

- `0`：不按页数自动重启。
- Google 默认值：`4`。
- 百度默认值：`0`。

### Delays / 延时

- Page delay：搜索结果页之间的等待时间。
- Slice delay：日期切片之间的等待时间。
- Error cooldown：临时错误后的冷却等待时间。

所有值均为毫秒。默认值偏保守，以降低访问压力并提高可复核性。

### Output format / 输出格式

推荐使用 XLSX 作为研究日志格式。软件同时支持 CSV、TXT、DOCX 和 XML。

---

## 7. 正文下载说明

在爬取或导入链接后，可使用 **Download selected content / 下载选中内容** 或 **Download all content / 下载全部内容**。

正文下载设置包括：

- 内容下载文件夹。
- 正文下载线程数。
- 正文下载方式。
- 正文页面下载延时。
- 正文接收/渲染等待时间。
- 清洗方案。
- 失败内容重试次数。
- 单条内容任务超时秒数。
- 正文下载断点续传。
- 同域名锁超时。

下载内容会保存到类似以下结构的子文件夹中：

```text
content_downloads/
  raw_html/
  raw_text/
  clean_text/
  metadata/
  content_manifest.jsonl
  content_metadata.xlsx
```

### 正文下载断点续传

如果软件或电脑在正文下载过程中被强制关闭：

1. 重新启动 WebLens。
2. 加载、爬取或导入同一批链接。
3. 选择同一个正文下载文件夹。
4. 再次启动正文下载。

WebLens 会读取 `content_manifest.jsonl`，跳过已经成功下载的 URL。失败、超时或未完成的 URL 会重新尝试。

此功能 **只适用于正文下载**。搜索结果爬取不会自动断点续爬。

---

## 8. 多语种正文抽取策略

WebLens 不假设所有页面都是英文，也不假设 `newspaper3k` 能解析所有站点。下载管线采用多层降级策略：

1. 在可用时保留原始字节。
2. 检测页面声明编码和表观编码。
3. 修复常见 mojibake 乱码，尤其是 UTF-8 文本被误按 Latin-1 解码的情况。
4. 在可用时尝试 `newspaper3k`。
5. 使用内置新闻站点模板。
6. 从 `article`、`main`、`content`、`post`、`story` 等候选正文容器中抽取。
7. 降级为可见文本抽取。
8. 即使抽取不完美，也尽量保存 clean TXT 和 metadata。

这可以改善百度返回的中文新闻页，也有助于处理其它非英语来源中专业抽取器失效的页面。

---

## 9. 源代码运行与桌面版打包

开发者可从源代码运行或重新构建桌面版。

创建 Python 环境并安装依赖：

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

在项目目录中使用 Windows 命令提示符或 PowerShell 运行：

```bat
build_exe.bat
```

打包脚本会创建并使用本地构建专用虚拟环境：

```text
.venv_build
```

这样可以让 PyInstaller 构建过程不受用户日常 Python、Anaconda 或 PyCharm 环境影响，并减少意外依赖膨胀。依赖变化较大时，可运行：

```bat
build_exe.bat --fresh
```

该命令会重新创建 `.venv_build`。脚本会在 `.venv_build` 中安装 `requirements.txt`，然后使用 PyInstaller onedir 模式，并将 `_internal` 作为依赖和资源目录：

```bat
--onedir --contents-directory "_internal"
```

目标输出：

```text
dist\BFSU_WebLens\BFSU_WebLens.exe
dist\BFSU_WebLens\_internal\...
```

发布包中会保留重要组件：`assets`、`tools`、Selenium 支持、newspaper3k、openpyxl、python-docx、编码检测/修复和多语种正文抽取依赖。发布时请压缩整个 `dist\BFSU_WebLens` 文件夹。不要将 `BFSU_WebLens.exe` 从 `_internal` 旁边单独移走。

### v1.2.4 Selenium 打包修复

打包脚本会显式收集 Selenium 动态导入的浏览器驱动模块，包括 `selenium.webdriver.chrome.webdriver` 以及 Edge 对应模块。如果旧桌面版运行时报 `No module named 'selenium.webdriver.chrome.webdriver'`，请重新构建：

```bat
build_exe.bat --fresh
```

然后重新分发整个 `dist\BFSU_WebLens` 文件夹，不要只复制 exe。

---

## 10. 合规与免责声明

BFSU WebLens 仅用于合法、适度、研究导向的网页发现和语料准备。用户应自行遵守：

- 网站服务条款。
- robots 与访问政策。
- 版权和数据库权利。
- 隐私与个人数据规则。
- 所在机构的管理规定。
- 访问频率限制与技术访问控制。
- 适用法律法规。

软件不保证检索结果完整、搜索引擎行为稳定、元信息完全准确、每个来源都能成功抽取，也不保证下载内容具有再发布或再分发权利。搜索引擎和新闻网站可能随时修改页面结构或实施访问限制。正式研究、发表或共享数据前，请使用保守延时，抽样核查，保留来源 URL，并复核输出结果。
