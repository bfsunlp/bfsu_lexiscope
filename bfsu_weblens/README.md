# BFSU WebLens v3.1.4

**BFSU WebLens** is a web and news corpus collection tool developed by the **BFSU Corpus Research Team** as part of **BFSU LexiScope**. It integrates search-result collection, manual result-page import, URL intake, result curation, sampling, webpage downloading, metadata extraction, and corpus-oriented text preparation in one desktop application.

WebLens is designed for corpus construction rather than general-purpose web crawling. It supports both automated and human-controlled workflows so that users can continue building corpora even when search engines require manual verification or when automated pagination is undesirable.

Author: **Dr. Dingjia Liu**  
Project: **BFSU LexiScope / BFSU Corpus Research Team**

---

# English

## 1. Download

### Direct download

**BFSU WebLens v3.1.4 for Windows x64**  
https://icloud.bfsu.edu.cn/f/0caa3e3134124f098fc2/

### Baidu Netdisk

File: **BFSU_WebLens_v3.1.4_windows_x64.zip**  
Link: https://pan.baidu.com/s/1diktKNs9tonYpYkfO9mzDg?pwd=si5e  
Extraction code: **si5e**

The Windows release uses an **ONEDIR** layout: `BFSU_WebLens.exe` is placed at the top level and runtime files are stored under `_internal`.

---

## 2. Main features

### 2.1 Automatic Google and Baidu collection

WebLens can collect Google and Baidu search-result links through a real Chrome or Edge browser controlled by Selenium.

Main controls include:

- search terms and query modes;
- Google Web / Google News;
- Baidu Web / Baidu News-related search modes;
- site/domain restriction;
- language and country/region restriction where supported by the search engine;
- optional date restriction;
- configurable page and slice delays;
- manual handling of human-verification pages;
- automatic continuation after verification when a valid result page is detected.

WebLens does not force a fixed search-result page size or maximum page count. Pagination follows the search engine's own rendered **Next** link.

The default date-slice value for both Google and Baidu is **0**, meaning that the selected date range is submitted as one search interval. A value greater than 0 enables date slicing.

### 2.2 Manual Collection

Version 3.0 introduced a browser-independent **Manual Collection** workflow.

WebLens can generate one or more search-engine URLs from the parameters currently entered in the Google or Baidu panel. Users can then:

1. copy the generated URL(s) into any normal browser;
2. complete verification manually if required;
3. turn pages manually;
4. save each search-result page as `.html` or `.htm`;
5. batch-import the saved pages into WebLens.

WebLens parses the saved Google/Baidu result pages, extracts candidate result links and available metadata, removes duplicates, and appends new records to **Result Preview**.

This mode does **not** require Selenium or WebDriver and is particularly useful when search engines frequently trigger human verification.

### 2.3 Paste links from text

Users can paste arbitrary text containing one or more HTTP/HTTPS links directly into WebLens.

Supported input can include:

- plain text;
- copied webpage text;
- HTML fragments;
- Markdown links;
- multiple URLs mixed with ordinary prose.

Parsed links are deduplicated and **appended** to the existing Result Preview rather than replacing current records. The operation can be repeated multiple times.

### 2.4 Import existing link files

WebLens can import user-created URL lists and WebLens exports.

Supported formats include:

- TXT;
- CSV / TSV;
- XLSX;
- XML;
- DOCX.

Only a URL is required. Missing title, source, publication time, and other metadata can be supplemented later when the destination page is downloaded successfully.

### 2.5 Result Preview and corpus-oriented curation

Collected or imported records are displayed in **Result Preview** for review before full-text downloading.

Available operations include:

- open link;
- delete selected records;
- sorting;
- undo / redo / reset where applicable;
- simple random sampling;
- systematic sampling;
- source-stratified sampling;
- selected/all content download;
- export of the curated result set.

This allows users to treat search-engine output as a candidate corpus pool rather than downloading every result automatically.

### 2.6 Webpage content downloading

After result curation, WebLens can download destination webpages and prepare corpus-ready content.

The downloader supports:

- HTTP/Requests downloading where appropriate;
- Selenium fallback for pages that cannot be retrieved reliably through Requests;
- title extraction;
- author extraction where available;
- publisher/source information where available;
- publication time extraction where available;
- final URL recovery after redirects;
- cleaned main-text extraction;
- metadata export for corpus management.

Google News opaque redirect URLs are retained as valid search results and are replaced by the final destination URL when the target page is successfully resolved.

### 2.7 Export

Collected and curated records can be exported for corpus construction and further analysis. Supported output formats include common spreadsheet, text, document, and structured-data formats such as XLSX, CSV, TXT, DOCX, and XML.

---

## 3. Browser and WebDriver management

Open **Settings → Browser & Selenium** to configure the application-wide browser environment.

### Chrome

The recommended Chrome workflow is isolated from the user's everyday browser:

- WebLens uses a portable **Chrome for Testing** copy under `tools/browser`;
- if no portable Chrome is available, WebLens can download and extract one automatically;
- the exact browser version is detected;
- a matching ChromeDriver is detected or downloaded;
- Browser/Driver compatibility is checked before collection starts.

Users can explicitly choose an already installed system Chrome, but this mode is marked **Not recommended** because normal browser auto-updates can independently change the browser version.

### Microsoft Edge

Because Microsoft does not provide a Chrome-for-Testing-style portable Edge ZIP, WebLens uses the **system-installed Microsoft Edge** as the recommended Edge browser and prepares a compatible EdgeDriver.

### One-click configuration and updates

The Browser & Selenium dialog provides:

- one-click Chrome/Edge configuration;
- independent Browser detection/configuration;
- independent WebDriver detection/update;
- manual Browser selection;
- manual WebDriver selection;
- Browser/Driver compatibility testing;
- update of the WebLens-managed portable Chrome and matching ChromeDriver.

Browser and Driver versions are rechecked before automated collection starts.

---

## 4. Human verification

WebLens does not attempt to bypass search-engine verification mechanisms.

When a verification page appears:

1. WebLens pauses automated navigation;
2. the user completes the verification in the visible browser;
3. WebLens monitors the live result DOM;
4. collection resumes only after a stable result page or explicit no-result state is detected.

The Manual Collection workflow provides an alternative when users prefer to manage search, verification, and pagination entirely by themselves.

---

## 5. Cross-platform support

### Windows

Windows is the primary packaged release platform. The release uses a portable **PyInstaller ONEDIR** layout.

Writable program data, downloaded browser components, drivers, output, and settings are kept outside `_internal` so the application can remain portable and maintainable.

### macOS

The codebase and build system support:

- Apple Silicon (`arm64`);
- Intel (`x86_64`).

On macOS, writable application data is stored under:

```text
~/Library/Application Support/BFSU WebLens
```

Build scripts are included for both Apple Silicon and Intel. Chrome for Testing / ChromeDriver selection follows the target architecture.

Current download links above provide the **Windows x64 release**. macOS users can build the application from source with the supplied scripts.

---

## 6. Interface and language

WebLens uses a PySide6 desktop interface with a restrained warm-light visual theme and Windows high-DPI support.

The interface supports:

- English;
- Simplified Chinese;
- Traditional Chinese.

A fresh installation defaults to **English**. User Guide, Parameter Guide, and About follow the current interface language.

---

## 7. Run from source

Python 3.10+ is supported; Python 3.12 is recommended for release builds.

```text
pip install -r requirements.txt
python main.py
```

The application entry point is `main.py`.

---

## 8. Building releases

### Windows x64

Run:

```text
build_exe.bat
```

The current Windows build system:

- creates a private minimal build environment;
- uses `PySide6-Essentials` rather than the full PySide6 Addons stack;
- keeps the developer Conda environment out of the frozen runtime;
- excludes unrelated scientific, ML, notebook, and alternate Qt stacks;
- produces an ONEDIR package with `_internal`;
- performs Qt runtime and frozen-application smoke tests;
- writes build logs and a bundle-size report;
- automatically compresses the finished application to `release/`.

Typical output:

```text
dist/
└─ BFSU_WebLens/
   ├─ BFSU_WebLens.exe
   └─ _internal/

release/
└─ BFSU_WebLens_v3.1.4_windows_x64.zip
```

### macOS Apple Silicon

```text
./build_macos_arm64.sh --fresh
```

### macOS Intel

```text
./build_macos_intel.sh --fresh
```

See `BUILDING.md` for detailed release-build notes.

---

## 9. Version history

### v3.1.4 — Windows clean-room build isolation

- Fixed Qt DLL contamination when the build BAT was launched from a PyCharm terminal with an activated Conda environment.
- After the private build environment is created, Qt/Python/Conda variables from the outer environment are removed from build subprocesses.
- Preserved the minimal Windows build strategy introduced in v3.1.3.

### v3.1.3 — Slim Windows build

- Reworked the Windows release builder to avoid multi-gigabyte packages.
- Removed `--system-site-packages` from the release build path.
- Switched the GUI dependency to `PySide6-Essentials` because WebLens uses QtCore, QtGui, and QtWidgets rather than the full Addons stack.
- Added large-module exclusions, conservative Qt payload pruning, frozen smoke tests, and `bundle_size_report.txt`.

### v3.1.2 — Windows runtime selection and Qt diagnostics

- Improved selection of the bootstrap Python/Conda runtime.
- Added stronger Qt runtime probing and DLL diagnostics.
- Improved handling of Conda-based Windows build environments.

### v3.1.1 — Reworked Windows build pipeline

- Moved complex Windows build logic from BAT into Python build tooling.
- Added persistent build logs and automatic release ZIP verification.
- Improved reproducibility of PyInstaller ONEDIR builds.

### v3.1.0 — Cross-platform Windows/macOS support

- Reviewed platform-dependent modules for Windows and macOS.
- Added macOS writable application-data paths.
- Added Apple Silicon and Intel build scripts.
- Added architecture-aware Chrome for Testing and Driver handling.
- Improved Qt plugin checks for Windows and macOS packaged applications.

### v3.0.0 — Manual Collection

- Added generation of Google/Baidu search URLs from current query parameters.
- Added batch import of manually saved search-result HTML pages.
- Added parsing, deduplication, and appending of imported results to Result Preview.
- Manual Collection works without Selenium or WebDriver.

### v2.5.x — Browser environment and flexible URL intake

- Added paste-from-text URL extraction.
- Added one-click Browser/WebDriver configuration and download progress.
- Added portable-Chrome-first isolation from the user's everyday Chrome installation.
- Added Browser/Driver version validation and collection preflight checks.
- Added update support for WebLens-managed portable Chrome and matching ChromeDriver.
- Changed Edge to use the system-installed browser by default because no official portable Edge ZIP equivalent is available.

### v2.4.x — Verification recovery, parsing, and interface refinement

- Improved recovery after Google human verification using the live browser DOM.
- Fixed Google News result parsing for newer `YKoRaf` result structures and opaque `/goto` redirects.
- Improved high-DPI layout, combo-box arrows, dialog sizing, and button visibility.
- Localized User Guide, Parameter Guide, and About according to the current interface language.

---

## 10. Project structure

```text
BFSU_WebLens/
├─ main.py
├─ build_exe.bat
├─ build_macos_arm64.sh
├─ build_macos_intel.sh
├─ build_macos_common.sh
├─ build_launcher.py
├─ build_windows.py
├─ build_probe.py
├─ clean_build.bat
├─ clean_build.sh
├─ requirements.txt
├─ requirements-build.txt
├─ BUILDING.md
├─ config/
├─ assets/
├─ tools/
└─ bfsu_weblens/
   ├─ app.py
   ├─ browser_manager.py
   ├─ collector.py
   ├─ content_downloader.py
   ├─ data.py
   ├─ exporter.py
   ├─ importer.py
   ├─ manual_collection.py
   ├─ platform_paths.py
   ├─ resources.py
   └─ ui/
```

---

# 中文

## 1. 下载

### 直接下载

**BFSU WebLens v3.1.4 Windows x64**  
https://icloud.bfsu.edu.cn/f/0caa3e3134124f098fc2/

### 百度网盘

文件：**BFSU_WebLens_v3.1.4_windows_x64.zip**  
链接：https://pan.baidu.com/s/1diktKNs9tonYpYkfO9mzDg?pwd=si5e  
提取码：**si5e**

Windows 发布版采用 **ONEDIR** 结构：`BFSU_WebLens.exe` 位于软件目录最外层，运行依赖集中放置在 `_internal` 目录中。

---

## 2. 主要功能

### 2.1 Google 与百度自动采集

WebLens 可以通过真实的 Chrome 或 Edge 浏览器，由 Selenium 控制完成 Google 和百度搜索结果链接采集。

主要支持：

- 检索词与不同检索模式；
- Google 网页与 Google 新闻；
- 百度网页及新闻相关检索模式；
- 站点/域名限定；
- 搜索引擎支持范围内的语种和国家/地区限定；
- 可选日期范围限制；
- 页面等待与日期切片等待；
- 人工完成人机验证；
- 验证通过后自动识别有效结果页并继续采集。

WebLens 不强制设置每页结果数量，也不设定固定最大页数。翻页只跟随搜索引擎页面实际显示的 **下一页** 链接。

Google 与百度的日期切片默认值均为 **0**，表示将整个日期范围作为一次检索区间；设置为大于 0 的数值后才启用日期分片。

### 2.2 手动采集

v3.0 增加了独立于 Selenium 的 **手动采集** 模式。

WebLens 可以根据当前 Google 或百度面板中填写的参数生成一个或多个搜索链接。用户随后可以：

1. 将生成的链接复制到任意普通浏览器；
2. 根据需要手动完成人机验证；
3. 手动翻页；
4. 将每一页搜索结果保存为 `.html` 或 `.htm`；
5. 将保存的页面批量导入 WebLens。

WebLens 会解析保存的 Google/百度搜索结果页面，抽取候选链接以及页面中能够识别的标题、来源、时间、摘要等信息，与现有 **Result Preview** 结果去重后，只追加新的记录。

这一模式**不需要 Selenium 或 WebDriver**，尤其适合搜索引擎频繁触发人工验证，或者用户希望完全控制检索和翻页过程的情况。

### 2.3 粘贴文本自动解析链接

用户可以直接向 WebLens 粘贴包含一个或多个 HTTP/HTTPS 链接的文本。

支持的输入包括：

- 普通文本；
- 从网页复制的混合文字；
- HTML 片段；
- Markdown 链接；
- 正文与多个 URL 混合的文本。

WebLens 会自动提取并去重链接，然后**追加**到当前 Result Preview 的末尾，不覆盖已有结果。用户可以多次粘贴、多次追加。

### 2.4 导入已有链接文件

WebLens 可以导入用户自己制作的链接列表，也可以重新导入 WebLens 导出的结果文件。

支持：

- TXT；
- CSV / TSV；
- XLSX；
- XML；
- DOCX。

导入时只要求 URL 必须存在。标题、来源、发布时间等字段即使为空，也可以在后续成功下载目标网页后继续补充。

### 2.5 Result Preview 与语料候选集整理

所有自动采集、手动采集、文本粘贴或文件导入得到的记录都会进入 **Result Preview**，供用户在下载正文前进行筛选和整理。

主要操作包括：

- 打开链接；
- 删除记录；
- 排序；
- 在适用位置撤销、重做、重置；
- 简单随机抽样；
- 系统抽样；
- 按来源分层抽样；
- 下载所选正文或全部正文；
- 导出整理后的结果集。

因此，WebLens 将搜索引擎结果视为**语料候选池**，用户可以先整理、抽样，再决定哪些网页进入最终语料库。

### 2.6 网页正文下载与元数据整理

完成结果筛选后，WebLens 可以继续下载目标网页并整理语料库所需内容。

正文下载支持：

- 在适合的网页上使用 Requests；
- Requests 无法可靠下载时使用 Selenium 作为后备；
- 标题抽取；
- 可获得时抽取作者；
- 可获得时抽取出版机构/来源；
- 可获得时抽取发布时间；
- 跳转后的最终 URL 识别；
- 网页主体正文清理；
- 元数据导出与语料管理。

对于 Google News 使用的 `/goto` 不透明跳转链接，WebLens 会先将其保留为有效搜索结果；当目标网页能够成功解析时，再用最终目标 URL 替换跳转地址。

### 2.7 导出

采集和整理后的结果可以导出，用于后续语料库建设和分析。支持 XLSX、CSV、TXT、DOCX、XML 等常见格式。

---

## 3. Browser 与 WebDriver 管理

通过 **Settings → Browser & Selenium / 设置 → Browser & Selenium** 可以统一配置浏览器环境。

### Chrome

Chrome 默认采用与用户日常浏览器相隔离的方案：

- WebLens 使用 `tools/browser` 下的便携版 **Chrome for Testing**；
- 如果软件内部尚未准备 Chrome，可以自动下载并解压；
- 自动读取实际浏览器版本；
- 自动检测或下载匹配的 ChromeDriver；
- 开始采集前再次检查 Browser 与 Driver 的兼容性。

用户仍然可以主动选择系统中已经安装的 Chrome，但界面会标记为 **Not recommended / 不推荐**，因为日常 Chrome 自动升级可能独立改变版本，从而影响 Driver 匹配。

### Microsoft Edge

微软目前没有提供与 Chrome for Testing 对等的官方便携 Edge ZIP，因此 WebLens 默认使用**系统已经安装的 Microsoft Edge**，并自动准备与之兼容的 EdgeDriver。

### 一键配置与更新

Browser & Selenium 窗口支持：

- Chrome/Edge 一键配置；
- 浏览器独立检测/配置；
- WebDriver 独立检测/更新；
- 手动选择 Browser；
- 手动选择 WebDriver；
- Browser/Driver 版本匹配测试；
- 更新 WebLens 内置便携 Chrome 与相匹配的 ChromeDriver。

每次自动采集开始前都会再次核对 Browser 与 Driver 版本。

---

## 4. 人机验证

WebLens 不尝试绕过搜索引擎的人机验证机制。

出现验证页面时：

1. WebLens 暂停自动导航；
2. 用户在实际浏览器窗口中手动完成验证；
3. WebLens 持续检查当前浏览器的 live DOM；
4. 只有检测到稳定的搜索结果页或明确的无结果状态后才恢复采集。

如果用户希望完全自行控制检索、验证和翻页，可以直接使用“手动采集”模式。

---

## 5. Windows 与 macOS 支持

### Windows

Windows 是目前主要提供打包下载的发布平台。Windows 发布版采用便携式 **PyInstaller ONEDIR** 结构。

设置、下载的浏览器组件、Driver、输出文件等可写内容不会塞进 `_internal`，便于软件维护和升级。

### macOS

当前代码与构建系统同时支持：

- Apple Silicon (`arm64`)；
- Intel (`x86_64`)。

macOS 上的可写程序数据统一放在：

```text
~/Library/Application Support/BFSU WebLens
```

项目中提供 Apple Silicon 和 Intel 的独立构建脚本，Chrome for Testing / ChromeDriver 也会根据目标架构选择相应版本。

本 README 上方的公开下载链接目前提供的是 **Windows x64 发布版**；macOS 用户可以使用项目自带脚本从源码构建。

---

## 6. 界面与语言

WebLens 使用 PySide6 桌面界面，采用简洁的暖色浅色主题，并针对 Windows 高 DPI 缩放进行了适配。

界面支持：

- English；
- 简体中文；
- 繁體中文。

首次安装默认使用 **English**。User Guide、Parameter Guide 和 About 会跟随当前界面语言显示。

---

## 7. 从源码运行

支持 Python 3.10+；发布打包推荐 Python 3.12。

```text
pip install -r requirements.txt
python main.py
```

程序入口为 `main.py`。

---

## 8. 发布打包

### Windows x64

运行：

```text
build_exe.bat
```

当前 Windows 构建系统会：

- 创建独立、最小化的构建环境；
- 使用 `PySide6-Essentials`，避免打入不需要的完整 Qt Addons；
- 隔离开发环境中的 Conda / Qt DLL；
- 排除无关的科学计算、机器学习、Notebook 和其他 Qt 绑定；
- 使用 ONEDIR + `_internal` 结构；
- 执行 Qt Runtime 和冻结程序 smoke test；
- 自动生成构建日志和体积报告；
- 自动将最终软件压缩到 `release/` 目录。

典型输出：

```text
dist/
└─ BFSU_WebLens/
   ├─ BFSU_WebLens.exe
   └─ _internal/

release/
└─ BFSU_WebLens_v3.1.4_windows_x64.zip
```

### macOS Apple Silicon

```text
./build_macos_arm64.sh --fresh
```

### macOS Intel

```text
./build_macos_intel.sh --fresh
```

更详细的构建说明见 `BUILDING.md`。

---

## 9. 版本修订历史

### v3.1.4 — Windows clean-room 构建隔离

- 修复在 PyCharm Terminal 中已激活 Conda 环境时，外层 Qt DLL 污染私有构建环境的问题。
- 私有构建环境创建完成后，后续 PyInstaller、Qt 检查和冻结程序测试不再继承外层 Conda/Python/Qt 环境变量。
- 保留 v3.1.3 的最小化打包策略。

### v3.1.3 — Windows Slim Build

- 重构 Windows 打包体系，解决发布包体积达到数 GB 的问题。
- 发布构建不再使用 `--system-site-packages`。
- GUI 依赖改用 `PySide6-Essentials`，因为 WebLens 主要使用 QtCore、QtGui、QtWidgets。
- 增加大型无关模块排除、Qt 安全裁剪、冻结程序 smoke test 和 `bundle_size_report.txt`。

### v3.1.2 — Windows Runtime 选择与 Qt 诊断

- 改进 Windows 打包时对 Python/Conda Runtime 的选择。
- 加强 Qt Runtime 探测和 DLL 诊断信息。
- 改进 Conda 环境下的构建兼容性。

### v3.1.1 — Windows 打包流程重构

- 将复杂的 Windows 构建逻辑从 BAT 转移到 Python 构建工具中。
- 增加完整构建日志和 release ZIP 自动校验。
- 提高 PyInstaller ONEDIR 构建的可重复性。

### v3.1.0 — Windows/macOS 跨平台支持

- 系统审查 Windows 与 macOS 的平台相关模块。
- 增加 macOS 可写程序目录管理。
- 增加 Apple Silicon 和 Intel 两套构建脚本。
- 增加按架构选择 Chrome for Testing 和 Driver 的逻辑。
- 加强 Windows/macOS 打包后的 Qt 插件检查。

### v3.0.0 — 手动采集

- 根据当前 Google/百度检索参数生成一个或多个搜索链接。
- 支持批量导入用户手动保存的搜索结果 HTML。
- 自动解析、去重并将结果追加到 Result Preview。
- 手动采集无需 Selenium 或 WebDriver。

### v2.5.x — 浏览器环境与灵活链接导入

- 增加“粘贴文本解析链接”。
- 增加 Browser/WebDriver 一键配置和下载进度。
- Chrome 默认改为 WebLens 管理的便携版本，减少对用户日常浏览器的影响。
- 增加 Browser/Driver 版本匹配和采集前预检。
- 支持更新 WebLens 内置便携 Chrome 和匹配的 ChromeDriver。
- Edge 因无官方便携 ZIP，改为默认使用系统已安装的 Edge。

### v2.4.x — 人机验证恢复、结果解析与界面优化

- 加强 Google 人机验证后的 live DOM 恢复逻辑。
- 修复新版 Google News `YKoRaf` 结果结构及 `/goto` 跳转链接解析。
- 优化高 DPI 下的窗口尺寸、下拉箭头、按钮显示和布局密度。
- User Guide、Parameter Guide、About 改为跟随当前界面语言。

---

## 10. 项目结构

```text
BFSU_WebLens/
├─ main.py
├─ build_exe.bat
├─ build_macos_arm64.sh
├─ build_macos_intel.sh
├─ build_macos_common.sh
├─ build_launcher.py
├─ build_windows.py
├─ build_probe.py
├─ clean_build.bat
├─ clean_build.sh
├─ requirements.txt
├─ requirements-build.txt
├─ BUILDING.md
├─ config/
├─ assets/
├─ tools/
└─ bfsu_weblens/
   ├─ app.py
   ├─ browser_manager.py
   ├─ collector.py
   ├─ content_downloader.py
   ├─ data.py
   ├─ exporter.py
   ├─ importer.py
   ├─ manual_collection.py
   ├─ platform_paths.py
   ├─ resources.py
   └─ ui/
```

---

**BFSU Corpus Research Team / 北外语料库团队**  
**BFSU LexiScope — Corpus construction and linguistic data tools**
