# BFSU WebLens 3.1.4

## v3.1.4 Windows build-runtime fix / Windows 打包运行时修复

Version 3.1.4 keeps all v3.0/v3.1 runtime features and fixes Windows build isolation after a real PyCharm/Conda build log showed that the private minimal build prefix was still re-adding the outer activated `bfsu_lexiscope` Conda environment to Qt DLL resolution. The Windows builder may be launched from an activated Conda terminal, but after `.venv_build_windows` is created all runtime probes, PyInstaller processes and smoke tests use only the private build prefix plus Windows system directories. The outer `CONDA_*`, `VIRTUAL_ENV`, `QT_*`, `PYTHON*`, and `BFSU_WEBLENS_BASE_PREFIX` values are removed from child processes. The slim builder continues to use `PySide6-Essentials` and a private Python 3.12 Conda prefix or isolated standard venv, without `--system-site-packages`.

3.1.4 保留 3.0/3.1 的全部运行功能，并根据真实 PyCharm/Conda 打包日志修复 Windows 构建隔离问题。此前虽然已经创建了最小私有构建环境，但 Qt DLL 探测逻辑又把外层已激活的 `bfsu_lexiscope` Conda 环境加入 DLL 搜索路径，导致两套 `Qt6Core.dll` 同时参与加载。新版允许用户继续在已经激活 Conda 的 PyCharm Terminal 中直接运行 `build_exe.bat`，但 `.venv_build_windows` 创建完成后，后续运行时检查、PyInstaller 和冻结程序测试只使用私有构建环境及 Windows 系统目录，并从子进程中清除外层 `CONDA_*`、`VIRTUAL_ENV`、`QT_*`、`PYTHON*` 和 `BFSU_WEBLENS_BASE_PREFIX`。Slim Build 继续使用 `PySide6-Essentials` 和独立的 Python 3.12 Conda prefix/标准 venv，不再使用 `--system-site-packages`。

## v3.1.0 Cross-platform release / Windows 与 macOS 跨平台发布

BFSU WebLens 3.1.0 keeps the v3.0 Manual Collection workflow and adds a reviewed Windows/macOS runtime and release-build system. Windows remains a portable ONEDIR application; frozen macOS builds store writable settings, downloaded browsers/drivers, output and content under `~/Library/Application Support/BFSU WebLens`, rather than modifying the signed `.app` bundle. Chrome for Testing and ChromeDriver selection now follows the running macOS architecture (`arm64` or `x86_64`), while installed Chrome/Edge discovery supports `/Applications` and `~/Applications`.

BFSU WebLens 3.1.0 保留 v3.0 的手动采集流程，并系统审查了 Windows/macOS 运行路径和发布构建逻辑。Windows 继续采用便携式 ONEDIR；macOS 冻结应用将可写设置、下载的浏览器/Driver、输出文件和正文数据存放到 `~/Library/Application Support/BFSU WebLens`，不修改签名后的 `.app`。Chrome for Testing 与 ChromeDriver 会按当前 Mac 架构自动选择 `arm64` 或 `x86_64` 版本，系统浏览器检测同时支持 `/Applications` 与 `~/Applications`。

## v3.0.0 Manual Collection / 手动采集

BFSU WebLens 3.0 adds a browser-independent manual search-result collection workflow alongside the existing Selenium automatic collector. The user first enters the normal Google/Baidu query parameters in WebLens, then chooses **Manual collection**. WebLens generates one or more initial search URLs using exactly the same query, site, date, language/region and Baidu sequential-term logic as automatic collection.

The user opens those URLs in any normal browser, handles verification and pagination manually, and saves each search-result page as `.html` or `.htm` (HTML-only is sufficient). The saved files can then be batch-imported from the Manual collection window. WebLens recovers the original saved-page URL when available, detects Google/Baidu result structure, extracts result title/link/source/time/snippet metadata, deduplicates links against the existing Result Preview and appends only new records. Imported manual results immediately use the same review, export and full-text download pipeline as automatically collected results.

Key points:

- Manual collection does **not** require Selenium, ChromeDriver or EdgeDriver.
- Automatic collection remains available and unchanged.
- Baidu multiple-term mode generates one initial URL per term; it does not use OR.
- Enabled date slicing can generate multiple initial URLs; `0` still means no slicing.
- The user controls pagination manually; WebLens does not calculate page offsets.
- Multiple saved HTML files can be selected at once, or all top-level `.html/.htm` pages in a folder can be imported.
- The same HTML files can be imported in multiple rounds; duplicate result URLs are skipped.
- Browser “Webpage, complete” companion resource folders are not recursively parsed, preventing iframe/resource HTML files from being mistaken for result pages.
- Search parameters remain editable even if the automatic browser environment is not configured; only **Start collection** is locked in that case.

### 手动采集工作流

WebLens 3.0 在原有 Selenium 自动采集之外增加“手动采集”模式。用户仍然在 Google 或百度面板中填写检索词、站点限定、日期、语种、国家/地区等参数，然后点击 **手动采集**。软件按照与自动采集完全一致的检索逻辑生成一个或多个搜索引擎初始链接。

用户把这些链接复制到自己的日常浏览器中打开，自行完成人机验证和翻页，并将每一页搜索结果保存为 HTML 文件。随后可在“手动采集”窗口中一次性选择多个 `.html/.htm` 文件，或者选择一个包含这些页面的文件夹。WebLens 自动识别 Google/百度结果页，解析标题、链接、来源、时间和摘要等信息，与当前结果预览中的 URL 去重后追加新记录。之后即可直接使用原有的结果整理、导出和正文自动下载功能。

该模式不依赖 Selenium 或 WebDriver，特别适合搜索引擎频繁出现人工验证、用户希望完全控制翻页节奏或需要利用自己的正常浏览器会话完成检索的场景。

## v2.5.3 backend-specific browser policy and Browser & Selenium layout fix

Browser selection now follows the distribution model of each browser instead of forcing one source policy onto both backends.

- **Chrome** defaults to **WebLens portable Chrome (Recommended)**. WebLens uses Chrome for Testing under `tools/browser`, can download it automatically, and pairs it with a matching ChromeDriver. System-installed Chrome remains an explicit **Not recommended** fallback.
- **Microsoft Edge** defaults to **System-installed Microsoft Edge (Recommended)**. Microsoft does not publish an official portable Edge ZIP comparable to Chrome for Testing, so WebLens detects the system Edge installation and prepares a matching EdgeDriver instead of asking for a portable Edge copy.
- **One-click configure Chrome & Edge** now always follows the recommended mixed policy: portable Chrome + system Edge.
- The Edge Browser source selector is fixed to the recommended system source; the independent browser button becomes **Detect system Edge**. Manual Edge executable selection remains available and is version-checked.
- Collection preflight still re-reads the actual Browser and WebDriver versions before every crawl.
- The Browser & Selenium dialog status/progress area has been moved out of the form grid. Long status messages now wrap in their own panel and can no longer overlap Page render wait or other controls at high Windows DPI scaling.


## v2.5.2 portable browser / WebDriver update

The application-wide **Browser & Selenium** dialog now provides **Update selected portable browser & WebDriver** in addition to one-click configuration. In the recommended portable-browser mode, the update action checks the vendor's current stable metadata before changing the WebLens-managed environment.

- Chrome: WebLens downloads the current official Chrome for Testing Stable ZIP into a new version directory under `tools/browser`, then downloads ChromeDriver for that exact browser version. The old portable browser is retained as a fallback; WebLens switches to the new version only after the browser and Driver have both been prepared and validated.
- Edge: a bundled portable Edge under `tools/browser` remains supported. WebLens can update EdgeDriver to the newest release compatible with that bundled Edge build. Microsoft does not publish an official portable Edge ZIP equivalent to Chrome for Testing, so WebLens does not silently replace a bundled Edge browser with an installer package. If the bundled Edge is older than current Stable, the dialog reports that limitation explicitly.
- System-installed browsers remain an explicit **Not recommended** opt-in and are not modified by this update command.
- When several WebLens portable Chrome versions coexist, WebLens now prefers the newest detected version rather than relying on folder/path ordering.

## v2.5.1 portable-browser-first policy

Browser collection is now isolated from the user's everyday browser by default. The application-wide **Browser & Selenium** setting has an explicit **Browser source** option:

- **WebLens portable browser (Recommended)** — the default. WebLens only uses browser executables under `tools/browser`. If portable Chrome is missing, One-click configuration downloads the official Chrome for Testing archive, extracts it into the WebLens `tools/browser` tree, detects its exact version, and then prepares a matching ChromeDriver. Existing system Chrome installations are ignored in this mode.
- **System-installed browser (Not recommended)** — an explicit opt-in fallback. When selected, WebLens can use Chrome/Edge already installed by the operating system. This mode is not recommended because normal browser auto-updates can independently change the browser version and require a new matching WebDriver.

Existing portable Edge copies under `tools/browser` are detected and preferred in portable mode. Microsoft does not publish an official Edge portable ZIP equivalent to Chrome for Testing, so WebLens does not silently substitute or modify a user's installed Edge. If no portable Edge is bundled, users can explicitly choose the not-recommended system-browser mode or manually supply a portable Edge executable.

Legacy settings are migrated safely: a system-browser path saved by an older WebLens release is ignored while the new default portable source is active. It becomes eligible only after the user explicitly selects the system-installed-browser option.

## v2.5.1 pasted-link intake and closed-loop browser/WebDriver setup

- Added **Paste links from text**. Paste arbitrary prose, HTML, Markdown or mixed text containing HTTP/HTTPS URLs; WebLens extracts unique links and appends them to the current Result Preview without replacing existing records. The dialog supports repeated paste/add operations.
- Fixed the browser-manager `NameError` caused by the missing `_browser_path_family_hint()` helper. Browser paths are now family-checked before configuration.
- Added **One-click configure Chrome & Edge** above the independent browser/Driver controls. In the default portable-browser mode, WebLens ignores system browser installations, reuses browser copies already under `tools/browser`, and downloads Chrome for Testing when portable Chrome is absent. Portable Edge under `tools/browser` is reused automatically; because Microsoft does not provide an equivalent official portable Edge ZIP, missing portable Edge is reported without modifying the user's installed Edge. Users can explicitly switch to the not-recommended system-browser source if needed.
- WebDriver downloads now stream with visible progress for resolution, download, extraction and version-compatibility validation.
- Manual Browser and WebDriver selection is validated immediately. A wrong browser family, unreadable version or browser/Driver build mismatch is rejected before it can be saved; collection preflight still re-checks compatibility before every crawl.


## v2.4.5 portable-browser discovery and collection preflight

- Browser discovery now prefers a system-installed Chrome/Edge, then automatically detects portable browser executables already bundled anywhere under the WebLens `tools` folder.
- When Chrome is absent, **Download recommended browser** can download the official Chrome for Testing ZIP, show configuration progress, extract it under `tools/browser`, and select the extracted executable automatically.
- Microsoft does not currently publish an equivalent official portable Edge ZIP. A portable Edge already placed under `tools` is still detected and configured automatically; otherwise WebLens opens Microsoft's official Edge download page.
- WebDriver management itself is unchanged. Before every crawl, however, WebLens re-reads the selected browser version and verifies the configured/cached Driver against it. A stale Driver saved for another browser version cannot be used to start collection.
- Google and Baidu now both default to **Date-slice step = 0**, meaning an enabled date range is sent as one unsliced search range unless the user explicitly chooses a positive slice size.


## v2.4.4 interface-density and high-DPI fixes

- Browser & Selenium settings now sizes itself to its actual controls instead of using a large fixed height, so rows stay compact at high DPI.
- Combo boxes, date edits and spin boxes now use explicit WebLens chevron icons, restoring clear drop-down/up/down indicators under the custom Qt theme.
- Browser/Driver recommendation and Driver-help prompts use a responsive two-column action layout instead of a QMessageBox single-row button bar, preventing clipped button labels on scaled displays.
- Help/About and content-download settings are constrained to the current screen's available logical geometry, and long form rows may wrap instead of forcing dialogs off-screen.
- Result sorting/sampling combo boxes no longer have restrictive maximum widths that could truncate translated labels.
- Application/bootstrap/build version strings are synchronized through package `__version__`.


## v2.4.3 fixes

- Fresh installations now start in English; User Guide, Parameter Guide, and About follow the selected interface language instead of showing English and Chinese together.
- About now identifies only Dr. Dingjia Liu as author and adds the BFSU Corpus Team official website, BFSUNLP GitHub page, and BFSU LexiScope project page.
- Google News 2026-style `a[jsname="YKoRaf"]` result cards using opaque `google.* /goto?url=CAES...` links are treated as real results rather than discarded as Google UI links. This fixes the post-verification `live_results > 0` / `parsed_candidates = 0` termination bug.
- When full-text downloading follows a Google News redirect successfully, WebLens replaces the stored redirect with the final destination URL and fills missing metadata where available.


## 2.4.2 human-verification live-DOM recovery fix

This maintenance release fixes a second post-CAPTCHA recovery race observed on Google. After a user completed human verification, the browser could already display a normal result page while WebLens continued to print "Still waiting for human verification". The cause was that the recovery loop still relied mainly on serialized HTML/result-card selectors; Google's live DOM can expose visible result headings before those older parser signatures are recognized.

Changes in 2.4.2:

- Verification recovery now gives priority to the browser's **live DOM**. Visible Google/Baidu result headings and principal result links override stale CAPTCHA strings/scripts left in the document.
- WebLens now reads `document.documentElement.outerHTML` at recovery time, with Selenium `page_source` only as a fallback, so the parser receives the same page the user is actually seeing.
- The wait heartbeat now reports diagnostic state (`live_results`, parsed candidates, explicit no-result state, `readyState`, and current URL) instead of the ambiguous generic "Still waiting" message.
- Google result parsing now additionally traces `#search/#rso` heading nodes to their surrounding result link so the post-verification readiness detector and record parser use compatible signals.
- No browser navigation is sent while human verification is active. Closing the WebLens notice does not force navigation; collection resumes automatically when the live result DOM is stable for two consecutive polls.


## 2.4.1 verification-resume fix

- Fixed a Google CAPTCHA recovery race: returning to a `/search` URL is no longer considered sufficient to resume parsing.
- After manual verification, WebLens waits for real result-card links (or an explicit no-result message) to be stable across two polls before continuing.
- This prevents a transient post-CAPTCHA search shell from being misclassified as an empty result page and terminating collection.


BFSU WebLens is the web/news corpus collection component of BFSU LexiScope. It collects search-engine result links with a real Chrome or Edge browser, supports result curation and sampling, downloads source webpages, extracts metadata, and prepares clean text for corpus construction.

## 1. PySide6 / Qt interface

Version 2.4 keeps the fixed warm-light BFSU EditTrac palette while using standard PySide6 controls and the system UI font.

- Main window: `QMainWindow`, native menus, `QToolBar`, `QSplitter`, `QFormLayout`, `QTableView`, standard dialogs and Qt background-thread signals.
- Google and Baidu are selected through a compact search-engine selector rather than full tab pages.
- Application-level commands appear only once in the main toolbar.
- Toolbar commands use orange-accent icons and bordered tool buttons so they are visually recognizable as actions.
- Query and site/domain text boxes show three text lines; scrollbars appear only when additional lines are entered.
- The site/domain label is split across two lines so the form remains readable at high DPI.
- Combo-box, spin-box and date controls use a quieter integrated subcontrol style rather than visually heavy arrow buttons.
- The left settings pane retains a readable minimum logical width and remains vertically scrollable at Windows 125–200% scaling.

## 2. Application-wide browser and Selenium settings

Open **Settings → Browser & Selenium… / 设置 → 浏览器与 Selenium…** once. Google, Baidu, future search engines and Selenium-based content downloading share the same configuration.

The global settings include:

- Chrome or Edge;
- detected local browser installations and versions;
- optional manually selected browser executable;
- matching ChromeDriver/EdgeDriver;
- automatic Driver detection/update;
- page-render wait, default **5000 ms**;
- **Do not show the collection browser window / 不显示采集浏览器界面**.

The settings dialog keeps labels and their controls on the same row. Browser installation/version entries are not intentionally wrapped onto a second line.

## 3. Browser/Driver readiness gate

Search collection is disabled until WebLens can confirm both:

1. a valid selected Chrome/Edge installation and version; and
2. a compatible WebDriver.

When the environment is not ready, WebLens displays an environment warning and disables search-collection controls and the Start action. The user can still import/export or inspect existing result data.

Browser preparation is backend-specific. For Chrome, WebLens can download the current Chrome for Testing Stable archive into `tools/browser` and prepare the exact matching ChromeDriver. For Edge, WebLens detects the system-installed Microsoft Edge by default and prepares a compatible EdgeDriver. If Edge is not installed, WebLens directs the user to the official Microsoft Edge download page rather than trying to create a non-existent portable Edge distribution.

## 4. Search-result collection model

Search-result collection is browser-only.

- Google/Baidu result-page collection has no Requests/HTTP backend.
- WebLens does not set a results-per-page value.
- WebLens does not set or enforce a maximum page count.
- Initial search URLs contain no WebLens-generated Google `num/start` or Baidu `rn/pn` pagination directives.
- Subsequent pages are reached only by following the search engine's own rendered **Next** link.
- The selected real browser's own User-Agent is used; WebLens does not force a fixed browser User-Agent for search collection.

Requests remains available only for downloading already collected destination webpages.

## 5. Date restriction is opt-in

Date restriction is **off by default**.

- When **Restrict collection by date / 限定爬取日期** is not checked, the start date, end date and date-slice controls are disabled and WebLens sends no Google/Baidu date-range parameter.
- When the user checks the option, the date controls become available and the chosen range is sent to the selected search engine.
- Google uses its custom-date parameter only in this enabled state.
- Baidu uses its date parameter only in this enabled state.
- Calendar popups have wider month/year navigation controls to avoid truncated `…` labels under display scaling.

The page-turn wait range is reused between result pages, between date slices and before the one retry after a transient page-load error.

## 6. Google result parsing improvements

Version 2.4 strengthens the Google browser path in several places:

- no accidental default restriction to “today” when the user has not enabled date filtering;
- after `document.readyState`, Selenium waits for a recognizable result container, terminal no-result state or verification state before parsing;
- result parsing recognizes multiple current Google Web/News title-link/card variants and retains conservative fallback extraction;
- search-engine navigation and page chrome are not treated as corpus results;
- a genuine empty page terminates the collection task;
- human verification pauses navigation until the user completes it manually.

## 7. Collected-link output

The left output group is explicitly named **Collected-link output / 采集链接保存**. The main path field is **Collected-link save location / 爬取链接保存位置**, making it clear that this file stores the collected result-link table rather than downloaded webpage contents.

Supported result exports remain XLSX, CSV, TXT, DOCX and XML.

## 8. Flexible URL import

**Import links / 导入链接** accepts both WebLens exports and user-created URL lists.

Supported workflows include:

- TXT/text file: one URL per line;
- headerless XLSX: URL in the first column, one per row, including the first row;
- headerless CSV: URL in the first column, one per row;
- CSV/TSV/text files containing URLs;
- WebLens XLSX/CSV/TXT/XML/DOCX exports with their existing metadata fields;
- an XLSX import template created through **File → Download import template / 文件 → 下载导入模板**.

Only the URL is required. A manually imported URL may have an empty title/source/date. It is still shown immediately in Result Preview, and successful target-page content downloading can supplement an empty title and publication time from extracted webpage metadata.

## 9. Result Preview

The table column order begins with:

**No. → Link → Collected time → Title → Source → Published time → …**

This makes URL-only imports usable even before metadata has been enriched.

Result tools retain open link, delete, sorting, sampling, selected/all content download and content-download settings. Sorting is consolidated into one selector.

## 10. Browser discovery and Driver management

### Windows

WebLens checks common Chrome/Edge Stable/Beta/Dev/Canary paths, Windows App Paths registry entries and `PATH`.

### macOS

WebLens checks `/Applications` and `~/Applications` for common Chrome/Edge channels and distinguishes Intel/Apple Silicon when selecting downloadable Drivers.

### Linux

Common Google Chrome, Chromium and Microsoft Edge executables available through `PATH` are detected.

WebLens no longer bundles a fixed Driver version. Compatible Drivers are detected in configured paths, WebLens cache, Selenium cache and `PATH`; a matching Driver can be downloaded from official vendor distribution endpoints.

## 11. Settings structure

```json
{
  "ui_lang": "en",
  "browser": {
    "fetch_backend": "selenium_chrome",
    "browser_binary_path": "...",
    "browser_driver_path": "...",
    "browser_wait_ms": 5000,
    "browser_headless": false
  },
  "google": {
    "date_filter_enabled": false
  },
  "baidu": {
    "date_filter_enabled": false
  }
}
```

Older untouched `3500 ms` render-wait defaults are migrated to `5000 ms` when settings are loaded.

## 12. Run from source

Python 3.10+ is recommended.

```text
pip install -r requirements.txt
python main.py
```

The entry point is `main.py`, which launches `bfsu_weblens.app`.

## 13. Windows package build

From the WebLens project directory:

```text
build_exe.bat
```

To rebuild the isolated build environment:

```text
build_exe.bat --fresh
```

## 14. Project layout

```text
BFSU_WebLens/
├─ main.py
├─ build_exe.bat
├─ build_macos_arm64.sh
├─ build_macos_intel.sh
├─ build_macos_common.sh
├─ build_probe.py
├─ clean_build.bat
├─ clean_build.sh
├─ run.bat
├─ requirements.txt
├─ requirements-build.txt
├─ config/
│  └─ default_settings.json
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
      ├─ main_window.py
      └─ theme.py
```

**BFSU Corpus Research Team / 北外语料库团队**

## 10. Version 2.4 interaction refinements

- The main title bar shows the full application version.
- Collection progress and task status are shown only in the bottom status bar; they no longer consume collector-panel space.
- Start collection and Stop collection use visually distinct toolbar treatments. Stop collection affects search collection only.
- Content controls are left-aligned in Result Preview. A separate **Stop download** button is enabled only while a content-download task is running.
- Start and end dates default to today when date restriction is off. Invalid saved ranges are normalized, and interactive date changes keep Start date ≤ End date.
- In the Chinese interface, Google language and country/region choices display `中文名称 (English name)`.
- User Guide, Parameter Guide and About use a full logo/header/content-card layout. All three present English first and Chinese second. About explicitly distinguishes Dr. Dingjia Liu's project-author/lead-developer role from OpenAI GPT's AI-assisted development role.
- Baidu restores a **Multiple terms (search one by one)** mode. Each non-empty input line is submitted as a separate Baidu search and fully paginated before the next term; WebLens never joins those terms with `OR`.


## Building releases / 发布打包

### Windows x64

Run `build_exe.bat`. The BAT file only launches `build_launcher.py`; the active virtualenv/Conda interpreter may be used as the bootstrap Python. If the bootstrap belongs to Conda, WebLens creates a separate private Conda prefix at `.venv_build_windows` with Python 3.12 and pip. Standard CPython/venv bootstraps create an isolated venv. Runtime and build dependencies are then installed only into this private environment.

It is safe to launch the BAT from a PyCharm terminal with `bfsu_lexiscope` already activated. The active environment is not inherited as the runtime of the build package: after the private environment is created, the builder removes outer Conda/venv/Python/Qt variables and rebuilds `PATH` from the private prefix and Windows system directories. No `--system-site-packages` mode is used.

PyInstaller uses `--onedir --contents-directory _internal`: `BFSU_WebLens.exe` stays at the top level and runtime files are placed under `_internal`. The builder validates `qwindows.dll`, runs the frozen application with external Python/Conda/Qt paths removed, creates `release/BFSU_WebLens_v<version>_windows_x64.zip`, and verifies the ZIP contents.

Build logs are written to both `build_logs/build_launcher.log` and `build_logs/build_windows.log`.

Run: `build_exe.bat`

### macOS Apple Silicon

Run on an Apple Silicon Mac with an arm64 Python/Conda environment: `./build_macos_arm64.sh --fresh`

The script builds an arm64 ONEDIR/windowed `.app`, creates a native `.icns`, performs ad-hoc code signing, runs a frozen Qt smoke test, and writes `release/BFSU_WebLens_v<version>_macos_arm64.zip` using `ditto` so macOS metadata is preserved.

### macOS Intel

Run on an Intel Mac, or with an x86_64/Rosetta Python environment on Apple Silicon: `./build_macos_intel.sh --fresh`

The source Python architecture is checked before the build. The release is written to `release/BFSU_WebLens_v<version>_macos_x86_64.zip`. The script deliberately fails early if the Python architecture does not match the requested target, because PyInstaller can only produce a valid target architecture when the Python environment and binary dependencies support it.

Python selection on macOS: `BFSU_WEBLENS_PYTHON` → active `VIRTUAL_ENV/bin/python` → active `CONDA_PREFIX/bin/python` → `python3` → `python`. Conda, standard `venv`, and ordinary Python installations are supported.

### Build safeguards

The build system incorporates safeguards learned from BFSU EditTrac packaging: isolated build virtual environments, PySide6-only Qt selection, dependency probing, source compilation, architecture validation, frozen-application smoke tests, exclusion of other Qt bindings, and release ZIP validation. On Windows, the script also locates the authoritative Qt plugin tree before packaging and installs a private `qwindows.dll` fallback only when PyInstaller did not expose the platform plugin in a standard `_internal` location. The smoke test is then launched with Conda/Qt environment variables cleared so it cannot accidentally succeed by loading Qt from the developer environment. On macOS, the release script verifies that `libqcocoa.dylib` is inside the `.app` and runs the frozen smoke test with external Qt/Python paths cleared. `clean_build.bat` and `./clean_build.sh` remove build intermediates while retaining `release/`.

## Windows slim build (v3.1.4)

The Windows release builder now uses a private minimal build environment and never exposes the whole development Conda environment through `--system-site-packages`. WebLens installs `PySide6-Essentials` rather than the full `PySide6`/Addons stack because the application uses only QtCore, QtGui and QtWidgets.

If the bootstrap Python belongs to Conda, the builder creates a private Conda prefix at `.venv_build_windows` with Python 3.12 and pip. If the bootstrap is standard CPython/venv, it creates a normal isolated `venv`. Both paths then install only `requirements.txt` and `requirements-build.txt`.

PyInstaller explicitly excludes unrelated scientific, ML, notebook and alternate Qt stacks. After packaging, unused Qt QML/translations/plugin payloads are pruned conservatively and the frozen `--qt-smoke-test` is run again. A bundle-size report is written to `build_logs/bundle_size_report.txt`; the release ZIP is created under `release/`.
