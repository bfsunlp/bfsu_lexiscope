# BFSU WebLens v1.2.8

**BFSU WebLens** is a desktop component of the **BFSU LexiScope** toolkit. It is designed for corpus researchers who need low-frequency, auditable search-result discovery, URL collection, source-page downloading, and multilingual text cleaning.

Author and project lead: **Dr. Liu Dingjia / 刘鼎甲 博士, Beijing Foreign Studies University**. Email: **djliu@bfsu.edu.cn**. ChatGPT assisted with requirement analysis, prototyping, code generation, refactoring, testing strategy, documentation drafting, and debugging suggestions. The software concept, corpus workflow, naming, parameter strategy, and final use decisions are directed by Liu Dingjia.

## Download

The packaged Windows release can be downloaded from Baidu Netdisk:

- **Shared file:** `BFSU_WebLens_v1.2.8.zip`
- **Download link:** https://pan.baidu.com/s/1UXTRIJpFbXJnMCHMTxbWPA?pwd=kvst
- **Extraction code:** `kvst`

The download contains the packaged BFSU WebLens v1.2.8 release. After downloading, extract the complete archive and keep the executable together with its accompanying folders and files.

## 1. Design principles

WebLens is not a high-frequency scraper. It is intended as a conservative research assistant for building traceable URL lists and downloading already collected pages for later corpus processing.

The software follows five principles:

1. **Separated engines**: Google and Baidu are separate panels with separate settings, logs, previews, exports, and download actions.
2. **Auditability**: generated search URLs, query expressions, date windows, site limits, engine metadata, and source metadata are exported whenever possible.
3. **Conservative access**: default delays are intentionally long, and users can increase them for unstable networks or restrictive sites.
4. **Multilingual downloading**: content extraction does not rely on one package only; it uses encoding repair, newspaper3k, site templates, article/main/content candidates, visible text fallback, and clean TXT output.
5. **Limited checkpointing**: search-result crawling is deliberately not resumed after forced closure. Breakpoint continuation applies only to content downloading after URLs have already been crawled or imported.



### v1.2.8 window-position fix
- The main window is fitted to the Windows usable work area only once during startup. The background event-queue poller no longer re-centers the window, so users can freely drag it to any position.
- Window clamping now distinguishes CustomTkinter logical dimensions from physical monitor pixels and uses the Windows monitor work area, excluding the taskbar. This prevents the right and bottom edges from opening outside the visible desktop at high DPI.

### v1.2.8 interface refinements
- Google **Results per page** now defaults to **10** and is also recorded in `config/default_settings.json`. Existing installations that still contain the previous shipped default of 50 are migrated to 10.
- The initial settings pane is wider, while the engine tabs are compact and aligned to the upper-left.
- The top action bar includes **Open downloads**, which creates and opens the active panel's content download folder.
- Result Preview actions are divided into bordered Records, Sort, Sampling, and Content download groups so every button remains visible and its purpose is clear.

## 2. What changed in v1.2.8

- The **traditional WebLens layout and traditional native menu bar are retained**. The search-engine tabs, left settings column, right result preview, log area, and existing collection workflow remain in their established positions.
- Visual controls now **prefer CustomTkinter throughout**: frames, section cards, buttons, entries, comboboxes, checkboxes, text areas, progress bars, tab controls, draggable split panes, date controls, and application dialogs. Native Tk/ttk is retained only where CTk has no direct equivalent, chiefly the menu system, result Treeview, and multi-select Listbox.
- Spacing, control heights, typography, surface colors, borders, corner radii, and toolbar rhythm now follow the **BFSU ClearLens / LexiScope** visual system more closely, with less crowded labels and inputs.
- The left settings column uses a CTk scrollable frame. The wheel scrolls the complete settings column whenever the pointer is inside it, including over query/domain text boxes and language/country multi-select lists.
- Windows 11 per-monitor DPI awareness is enabled before the GUI is created. Native menu and Treeview metrics are DPI-aware, and the main window plus every application dialog is clamped and centered within the usable screen area so it does not open partially off-screen.
- The WebLens icon has been redrawn to match ClearLens: **navy background, teal magnifying lens, white web globe, and BFSU identity**. Dedicated small-size PNGs and a multi-resolution 16–256 px ICO improve taskbar and title-bar clarity.
- The About, guide, settings, download-settings, and date-picker windows use the same CTk styling and apply the product icon consistently.
- Author information remains explicit: **Dr. Liu Dingjia / 刘鼎甲 博士**, **djliu@bfsu.edu.cn**.
- `requirements.txt` explicitly includes `customtkinter` and `pillow`; `build_exe.bat` continues to collect CustomTkinter and the complete assets directory.

## 2. What changed in v1.2.4

- The **Site/domain filters** field in both Google and Baidu panels is now a **multi-line input box**.
- Users can enter one domain or suffix per line, such as:

```text
people.com.cn
xinhuanet.com
.gov.cn
.edu.cn
site:thepaper.cn
```

- The backend still accepts semicolon-separated values for compatibility with earlier settings.
- Help/About/User Guide/Parameter Guide have been expanded and synchronized.
- `build_exe.bat` now builds from an isolated local virtual environment `.venv_build`, so the released desktop app is less affected by packages installed in the user's daily Python/Conda environment.
- The script still keeps important runtime components: `assets`, `tools`, README, requirements, Selenium support, newspaper3k, openpyxl, python-docx, charset repair, and multilingual extraction dependencies. It builds a PyInstaller **onedir** package with this intended layout:

```text
dist/
  BFSU_WebLens/
    BFSU_WebLens.exe
    README.md
    requirements.txt
    _internal/
      assets/
      tools/
      ...dependencies...
```

The executable is placed at the outer level; dependencies and resources are placed in `_internal`.

## 3. Engine panels

### 3.1 Google panel

The Google panel supports:

- Google Web search.
- Google News vertical search.
- Query-helper modes:
  - Single term.
  - Any term / OR.
  - All terms.
  - Exact phrase.
  - Any exact phrase / OR.
  - Raw Google query.
- Result-language restriction through Google `lr`.
- Country/region restriction through Google `cr`.
- Site/domain filtering through `site:` syntax and local URL filtering.
- Date slicing with configurable day step.
- Conservative page/slice/error delays.
- Requests or Selenium Chrome/Edge backend.
- Selenium browser restart every N pages. Google default: `4`.

### 3.2 Baidu panel

The Baidu panel supports:

- Baidu Web search.
- Baidu News/Information search.
- Baidu News - media sites using the observed `medium=1` filter.
- Baidu sort options where Baidu respects the parameter.
- Site/domain filtering by inserting `site:{domain}` into Baidu `wd`.
- Date filtering using observed Baidu `gpc=stf=...|stftype=2` and `tfflag=1` parameters.
- Requests-first workflow, with Selenium available if needed.

The Baidu panel intentionally does **not** include:

- Google-style language restriction.
- Google-style country/region restriction.
- Google Any/OR helper modes.
- Bing controls.

## 4. Important default values

| Parameter | Google default | Baidu default | Meaning |
|---|---:|---:|---|
| Day step | 7 | 0 | Number of days per date slice. `0` means no slicing. |
| Max pages per slice | 30 | 100 | Maximum search-result pages requested inside each date slice. |
| Stop after no-new pages | 1 | 1 | Stop the current slice after N consecutive pages add no new valid links. |
| Browser restart every N pages | 4 | 0 | Selenium search-session browser reset interval. `0` disables page-count reset. |
| Page delay | 30,000–90,000 ms | 30,000–90,000 ms | Random wait between search-result pages. |
| Content fetch mode | mixed | mixed | Requests first + Selenium fallback. |
| Content retry count | 1 | 1 | Retry failed content URLs before marking failure. |
| Single content task timeout | 300 s | 300 s | Hard GUI-level timeout for one content URL. |
| Resume content downloads | enabled | enabled | Skip already successful content URLs based on manifest. |

## 5. Parameter guide

### Panel

Choose the engine workflow. Google and Baidu results do not share one preview table. Sampling, export, and content download actions apply to the active panel only.

### Query mode

Google includes helper modes for OR and exact phrase OR. Baidu removes those helper modes because Baidu query behavior is less stable with complex Boolean expressions. Raw query mode remains available for expert users.

### Search terms / phrases

Enter topic words or phrases. One item per line is recommended. In raw query mode, WebLens treats the text as the query expression.

### Site/domain filters

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
- **Raw query caution**: if raw query already contains `site:`, leave this field empty to avoid duplicate constraints.

For strict source-specific corpora, run separate tasks for each domain when possible, because search engines may handle complex `site:a OR site:b` expressions differently.

### Search vertical

- Google Web: ordinary search-result pages.
- Google News: adds `tbm=nws`.
- Baidu Web: uses `tn=baidu`.
- Baidu News/Information: uses `tn=news&cl=2`.
- Baidu News - media sites: adds `medium=1`.

### Baidu sort

- Focus/relevance: observed `rtt=1` behavior.
- Time: observed time-sort behavior where Baidu respects it.

Baidu may change its behavior, so WebLens always records `search_url` for verification.

### Language and country/region restrictions

These are Google-only controls.

- `lr` restricts result document language, for example `lang_en`.
- `cr` restricts Google's country/region result collection, for example `countryUS`.

These are search constraints, not final truth about outlet location, author nationality, or document quality.

### Date range and day step

Start date and End date define the total search window.

Day step controls slicing:

- `0`: no slicing; search the full date window as one slice.
- `1`: daily slices.
- `7`: weekly slices.

Smaller slices reduce truncation bias for popular topics but increase request count and runtime.

### Max pages per slice

Maximum pages requested within one date slice. If day step is small, this value applies separately to each slice.

### Stop after no-new pages

Stops a slice after N consecutive pages add no new valid URLs after filtering and deduplication. Default is `1`.

### Fetch backend

- Requests: faster and lighter, but cannot execute JavaScript.
- Selenium Chrome/Edge: opens a real browser; useful for rendered pages, debugging, captcha/redirect diagnosis, and pages where requests returns incomplete HTML.

### Browser restart every N pages

Only affects Selenium search-result crawling.

- `0`: do not automatically restart by page count.
- Google default: `4`.
- Baidu default: `0`.

### Delays

- Page delay: wait between result pages.
- Slice delay: wait between date slices.
- Error cooldown: wait after temporary failures.

All values are milliseconds. Defaults are conservative to reduce access pressure and improve reproducibility.

### Output format

XLSX is recommended for research logging. CSV, TXT, DOCX, and XML are also available.

## 6. Content download guide

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

### Breakpoint continuation

If the software or computer is force-closed during content downloading:

1. Restart WebLens.
2. Load/crawl/import the same links.
3. Select the same content download folder.
4. Start content download again.

WebLens reads `content_manifest.jsonl` and skips URLs already marked successful. Failed, timed-out, or unfinished URLs are attempted again.

This feature applies **only to content downloading**. Search-result crawling is not resumed automatically.

## 7. Multilingual extraction strategy

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

## 8. Desktop build

Use Windows command prompt or PowerShell in the project directory:

```bat
build_exe.bat
```

The script now creates and uses a local build-only virtual environment:

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

Important components are kept in the release: `assets`, `tools`, Selenium support, newspaper3k, openpyxl, python-docx, charset detection/repair, and multilingual text extraction dependencies. For release, zip the entire `dist\BFSU_WebLens` folder. Do not move `BFSU_WebLens.exe` away from `_internal`, because the executable depends on files inside `_internal`.

## 9. Compliance and disclaimer

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


### Selenium packaging fix in v1.2.4

The build script now explicitly collects Selenium's dynamically imported browser-driver modules, including `selenium.webdriver.chrome.webdriver` and the Edge equivalents. If an older packaged desktop build reports `No module named 'selenium.webdriver.chrome.webdriver'`, rebuild with:

```bat
build_exe.bat --fresh
```

Then redistribute the entire `dist\BFSU_WebLens` folder. Do not copy only the executable, because Selenium, browser-driver helpers, resources, and Python libraries are stored under `_internal`.

# BFSU WebLens v1.2.8 中文说明

BFSU WebLens 是 **BFSU LexiScope** 工具箱的桌面组件，面向语料库研究中的低频、可审计网页检索、新闻检索、URL 发现和正文下载。

作者与项目主导：**刘鼎甲，北京外国语大学**。ChatGPT 参与需求分析、原型设计、代码生成、重构、测试思路、文档起草和调试建议。软件构想、语料库工作流、命名、参数策略和最终使用决策由刘鼎甲主导。

## 软件下载

Windows 发布版可通过百度网盘下载：

- **分享文件：** `BFSU_WebLens_v1.2.8.zip`
- **下载链接：** https://pan.baidu.com/s/1UXTRIJpFbXJnMCHMTxbWPA?pwd=kvst
- **提取码：** `kvst`

下载后请完整解压压缩包，并保持主程序、`_internal` 目录及其它配套文件的相对位置不变，避免只复制或移动可执行文件而导致程序无法正常运行。


### v1.2.8 窗口位置修复
- 主窗口只在启动阶段按照 Windows 可用工作区定位一次；后台事件队列不再反复居中窗口，因此用户拖动窗口后不会自动弹回原位置。
- 窗口定位会区分 CustomTkinter 的逻辑尺寸与显示器物理像素，并使用扣除任务栏后的 Windows 工作区，避免高 DPI 缩放下右侧和底部藏到桌面之外。

### v1.2.8 界面细化
- Google 的“每页结果数”默认值改为 **10**，并写入 `config/default_settings.json`；旧版中仍为原默认值 50 的设置会自动迁移为 10。
- 软件启动时左侧设置区更宽；Google/百度标签压缩并移至左上角。
- 顶部操作栏新增“打开下载文件夹”，可创建并打开当前面板的正文下载目录。
- 结果预览工具按“记录操作、排序、采样、正文下载”划分为带边框的功能区，避免按钮混杂或显示不全。

## 1. v1.2.8 界面重构

- **保留 WebLens 原有传统布局与传统菜单栏**，Google/百度标签页、左侧设定栏、右侧结果预览和日志区域的位置及工作流程不变。
- 框架、分组面板、按钮、输入框、下拉框、复选框、多行文本框、进度条、标签页、可拖动分栏、日期控件和应用内对话框均优先采用 **CustomTkinter**。仅传统菜单、结果 Treeview、多选 Listbox 等 CTk 无直接替代的组件保留原生 Tk/ttk。
- 间距、控件高度、字体节奏、表面配色、边框和圆角进一步与 **BFSU ClearLens / LexiScope** 统一，避免标签与输入区过于拥挤。
- 左侧设定栏改用 CTk 滚动框；鼠标位于设定栏任意区域时均可平滑滚动，包括检索词、域名文本框以及语种/国家地区多选列表。
- 启用 Windows 11 每显示器 DPI 感知；原生菜单与 Treeview 采用 DPI 适配指标；主窗口及所有应用内子窗口会根据屏幕可用区域自动限制尺寸并居中，避免打开后只显示局部。
- 图标按 ClearLens 风格重新绘制：深蓝背景、青绿色放大镜、白色网络地球和 BFSU 标识；提供专用小尺寸 PNG 与 16–256 px 多分辨率 ICO，提高任务栏和标题栏清晰度。
- 关于、说明、设置、正文下载设置和日期选择窗口均统一采用 CTk 风格，并应用产品图标。
- 作者信息：**Dr. Liu Dingjia / 刘鼎甲 博士**，邮箱 **djliu@bfsu.edu.cn**。

## 1. v1.2.4 主要变化

- Google 和百度面板中的 **站点/域名限定** 改为多行输入框。
- 支持每行填写一个来源域名或域名后缀，例如：

```text
people.com.cn
xinhuanet.com
.gov.cn
.edu.cn
site:thepaper.cn
```

- 后端继续兼容英文分号分隔的旧设置。
- 扩写 About、User Guide、Parameter Guide 和 README。
- 检查并优化 `build_exe.bat`，用于通过本地 `.venv_build` 虚拟环境构建 PyInstaller onedir 桌面版，减少日常 Python/Conda 环境对发布包的干扰，同时保留 Selenium、newspaper3k、openpyxl、python-docx、编码修复、多语种抽取、assets 和 tools 等关键组件。

## 2. Google 面板

Google 面板支持网页检索和新闻检索，支持检索辅助模式、语种限定、国家/地区限定、站点/域名限定、日期切片、保守延时和 Selenium 浏览器模式。

## 3. 百度面板

百度面板支持百度网页、百度资讯、百度资讯媒体网站。百度通过 `wd` 中的 `site:{domain}` 实现站点限定，通过观察到的 `gpc/tfflag` 实现日期范围过滤，通过 `medium=1` 实现媒体资讯过滤。百度面板不显示 Google 专用语种/国家地区控件和 Google 风格 OR 辅助模式。

## 4. 站点/域名限定

现在是多行输入框。建议每行一个域名、后缀或 `site:` 表达式。

- Google：写入 `site:` 查询约束，并在解析后本地过滤 URL。
- 百度：写入 `wd` 中的 `site:{domain}`，并在解析后本地过滤 URL。
- 如果原始查询式已经写了 `site:`，这里应留空。
- 如果要做严格来源语料库，建议对重点域名单独分批采集。

## 5. 正文下载断点续传

正文下载支持 manifest 断点续传。每条成功下载会立即写入 `content_manifest.jsonl`。软件或电脑强制关闭后，重新选择同一下载文件夹并下载同一批链接时，已成功 URL 会跳过，失败或未完成 URL 会继续尝试。

该机制只用于正文下载，不用于搜索结果爬取。

## 6. 桌面版打包

运行：

```bat
build_exe.bat
```

打包脚本会创建并使用本地构建虚拟环境：

```text
.venv_build
```

这样可以避免把日常 Python、Anaconda 或 PyCharm 环境中的无关包带入发布版。依赖变化较大时，可运行：

```bat
build_exe.bat --fresh
```

该命令会删除旧的 `.venv_build` 并重新安装 `requirements.txt`。输出结构：

```text
dist\BFSU_WebLens\BFSU_WebLens.exe
dist\BFSU_WebLens\_internal\...
```

关键组件会保留：`assets`、`tools`、Selenium、newspaper3k、openpyxl、python-docx、编码检测/修复与多语种正文抽取依赖。发布时压缩整个 `dist\BFSU_WebLens` 文件夹。不要把 exe 单独拿出来运行。

## 7. 免责声明

本工具仅用于合法、低频、研究导向的网页发现和语料准备。用户应遵守网站服务条款、robots/访问政策、版权、隐私、单位管理规定、访问频率限制和适用法律。软件不保证检索结果完整、搜索引擎行为稳定、元信息完全准确、所有来源均可干净抽取，也不保证下载内容具有再发布或再分发权利。正式研究、发表或共享数据前，请使用保守延时、抽样核查、保留来源 URL，并复核输出结果。


### v1.2.4 Selenium 打包修复

打包脚本现在会显式收集 Selenium 动态导入的浏览器驱动模块，包括 `selenium.webdriver.chrome.webdriver` 以及 Edge 对应模块。如果旧的桌面版运行时报 `No module named 'selenium.webdriver.chrome.webdriver'`，请使用以下命令重新构建：

```bat
build_exe.bat --fresh
```

发布时请压缩并分发整个 `dist\BFSU_WebLens` 文件夹，不要只复制 exe。Selenium、浏览器驱动辅助模块、资源文件和 Python 依赖都位于 `_internal` 中。

## Manual Google verification waiting / Google 验证码手动等待

When the Selenium Chrome/Edge backend reaches a Google human-verification page, WebLens no longer ends the crawl immediately. It preserves the current browser window and pauses all crawler navigation. While verification remains visible, WebLens does not refresh the page, request another URL, paginate, or restart the browser. The user can complete the verification manually in the browser. WebLens checks the currently displayed page at a short interval without navigating; after the normal search page remains visible, WebLens refreshes the current page once and resumes parsing and crawling automatically. If verification appears again after the refresh or later in the task, the same waiting procedure is entered again. The Stop button remains effective during the wait.

当 Selenium Chrome/Edge 后端进入 Google 真人验证页面时，WebLens 不再立即结束采集任务，而是保留当前浏览器窗口并暂停所有采集导航。验证未通过期间，程序不会刷新页面、请求其他 URL、翻页或重启浏览器。用户可直接在浏览器中手动完成验证。WebLens 会以较短间隔读取当前页面状态，但不会触发导航；确认正常搜索结果页已经稳定显示后，程序会自动刷新当前页一次，并继续解析和采集。如果刷新后或后续采集过程中再次出现验证页，程序会再次进入相同的等待状态。等待期间“停止”按钮仍然有效。

