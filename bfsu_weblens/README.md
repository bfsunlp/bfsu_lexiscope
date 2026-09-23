# BFSU WebLens v3.1.9

**BFSU WebLens** is the web and news corpus collection component of **BFSU LexiScope**, developed by the BFSU Corpus Research Group. It is designed for corpus construction, web/news corpus collection, corpus-based discourse studies, translation and media research, and other research workflows that require traceable discovery, review, downloading and organization of web resources.

**BFSU WebLens / 北外 WebLens 网络语料采集工具** 是 **BFSU LexiScope** 的网络语料采集组件，由北外语料库团队开发，面向网页语料库建设、新闻语料采集、语料库话语研究、翻译研究、国际传播与传媒研究等场景。软件将搜索结果发现、结果筛选与整理、链接导入导出、网页正文下载、元信息保存和语料文本准备整合为一个可追溯的工作流程。

```text
检索设置 → Google / 百度结果采集 → 结果预览、去重与整理
→ 排序 / 抽样 / 人工编辑 → 结果导出 → 正文下载
→ 正文与元信息保存 → 后续语料清洗、标注与分析
```

---

## 1. Download / 下载

**Current Release / 当前版本：** `BFSU WebLens v3.1.9`

**Windows x64 package / Windows x64 发布包：** `BFSU_WebLens_v3.1.9_windows_x64.zip`

**Direct Download / 直接下载：**  
https://icloud.bfsu.edu.cn/f/606e7a47cbce4e758174/

**Baidu Netdisk / 百度网盘：**  
https://pan.baidu.com/s/1p-65itRM7KSX9x9xtsIrhQ?pwd=xiyx

**Extraction Code / 提取码：** `xiyx`

下载后请**完整解压 ZIP 文件**，然后从完整发布目录运行 `BFSU_WebLens.exe`。不要只单独移动 EXE 文件，否则浏览器组件、配置文件或运行依赖可能无法正常找到。

After downloading, **extract the complete ZIP package** and run `BFSU_WebLens.exe` from the extracted release folder. Do not move the EXE file out of the release directory by itself.

---

## 2. What is new in v3.1.9 / v3.1.9 主要更新

### Interruption-safe saving / 中断安全保存

- Google 和百度自动采集过程中，如果用户点击 **Stop / 停止采集** 或 **Stop All / 全部停止**，软件会自动把已经进入 Result Preview 的结果保存到当前设置的结果文件中；
- 如果采集因浏览器、网络或其它异常中断，已经采集到的链接也会在任务结束前保存；
- Worker 完全退出后还会进行一次最终检查，避免停止瞬间刚进入队列的结果丢失；
- 如果结果状态没有变化，不会无意义地重复重写大型结果文件。

Automatic Google/Baidu collection now preserves all results already collected when the user stops a task or when collection terminates because of a browser, network or other exception. A final save check is performed after the worker has actually stopped so late queued records are not lost.

### Interface units, publication dates and project naming / 参数单位、发布时间与项目名称

- **Page-turn wait range / 翻页等待范围** 改为以“秒”为界面输入单位，更符合用户对等待时间的直观理解；内部仍转换为毫秒，并在设定范围内按毫秒粒度随机取值；
- Result Preview 的 `Published / 发布时间` 统一显示为 **DD-MM-YYYY（日-月-年）**，点击该表头时按解析后的实际日期排序，不再按文本字面顺序排序；
- README、软件 About 及相关帮助文本中的团队官方名称统一为 **BFSU Corpus Research Group / 北外语料库团队**。

### Content-download persistence and resume / 正文下载保存与断点续下

- 正文下载正常结束、人工停止、全部停止或异常退出时，当前下载状态会写回结果文件；
- 已经获得的最终 URL、正文状态、词数、质量信息以及正文和 metadata 路径会尽量保留；
- 原有的 **Content Download 断点续下功能完整保留**；
- 成功下载的项目会逐条记录到 `content_manifest.jsonl` 并保存正文文件；
- 再次选择同一下载目录继续任务时，只跳过已经成功且文件仍然存在的项目，未完成、失败或中途停止的项目会继续尝试。

The existing content-download checkpoint mechanism is preserved. Successfully downloaded items remain recorded item by item, while unfinished, failed or stopped items can be resumed later without restarting completed downloads.

---

## 3. Main Features / 主要功能

### 3.1 Google and Baidu collection / Google 与百度采集

- 支持 **Google Web** 与 **Google News**；
- 支持 **百度网页、百度资讯和媒体网站资讯**；
- Google 支持单个检索词、OR、全部词、精确短语、多个精确短语以及原始检索式等模式；
- Google 可按语种、国家/地区、站点/域名和日期范围限定；
- 百度的多个检索词和多个站点/域名按独立任务展开，完整任务逻辑为 **检索词 × 域名 × 日期切片**，不会自动用 OR 合并不同任务；
- 日期限定默认关闭，仅在用户主动启用后向搜索引擎发送日期范围；
- 不人为设置每页结果数，也不设置固定最大页数，而是跟随搜索引擎页面自身的 **Next / 下一页**；
- 对采集结果进行全局 URL 去重；
- 左侧 **Page-turn wait range / 翻页等待范围** 统一以“秒”为用户输入单位；保存到配置和传入采集器时自动换算为毫秒，实际等待仍在两个毫秒端点之间随机取值。

WebLens supports Google Web/News and Baidu Web/News/Media workflows. Date filtering is opt-in, and pagination follows the search engine's own rendered Next link rather than WebLens-generated page offsets.

### 3.2 One-click browser setup / 一键浏览器配置

自动采集使用真实 Chrome 或 Microsoft Edge 浏览器。首次使用时，如果自动采集环境尚未准备好，可直接使用主界面的：

**One-click setup Chrome & Edge / 一键配置 Chrome 与 Edge**

该功能会：

- 为 WebLens 准备独立的 **Chrome for Testing**；
- 自动准备与 Chrome 版本匹配的 ChromeDriver；
- 检测 Windows 系统已经安装的 Microsoft Edge；
- 自动准备匹配的 EdgeDriver；
- 至少一种浏览器环境可用后自动保存可用配置。

更详细的浏览器路径、Driver、页面渲染等待时间和浏览器显示方式仍可在：

**Settings → Browser & Selenium / 设置 → 浏览器与 Selenium**

中单独调整。

Manual collection does not require Selenium or WebDriver.

### 3.3 Human verification / 人工验证

当 Google 或百度出现人工验证页面时，WebLens 会暂停自动导航，不强制刷新、不自动翻页，也不会在验证期间重新打开搜索页。用户可直接在浏览器窗口中完成验证；验证结束后，WebLens 等待真实搜索结果 DOM 稳定，再从当前页面继续采集。

### 3.4 Google News direct URL recovery / Google News 真实链接解析

当前 Google News 有时会把新闻结果写成：

```text
https://www.google.com/goto?url=CAES...
```

WebLens 会在自动采集阶段尝试向 Google 获取该跳转链接的真实目标地址，并把 Reuters、BBC、CNN 或其它来源网站的**真实外部 URL**直接保存到 Result Preview。

如果某次无法取得真实目标地址，则保留原 `/goto` 链接作为安全回退；正文下载成功后仍可根据最终跳转结果再次更新为真实 URL。

### 3.5 Manual Collection / 手动采集

除 Selenium 自动采集外，WebLens 还支持**手动采集**：

1. 在 WebLens 中填写正常的 Google 或百度检索参数；
2. 由 WebLens 生成一个或多个初始检索链接；
3. 用户在自己的日常浏览器中打开链接，自行处理人工验证并手动翻页；
4. 将各页搜索结果保存为 `.html` 或 `.htm`；
5. 在 WebLens 的 Manual Collection 窗口中批量导入；
6. 软件自动解析结果、去重并追加到 Result Preview。

该模式**不依赖 Selenium、ChromeDriver 或 EdgeDriver**，适合搜索引擎验证频繁或研究者希望完全控制翻页过程的情况。

---

## 4. Result Preview and result management / 结果预览与整理

Google 与百度均使用独立的结果列表。Result Preview 支持：

- 打开链接；
- 删除记录；
- 撤销、重做与恢复当前结果的原始顺序；
- 简单随机抽样；
- 系统抽样；
- 按来源分层抽样；
- 导入已有 URL；
- 从普通文本、HTML 或 Markdown 中粘贴并抽取链接；
- 对选中记录或全部记录执行正文下载。

### Column-header sorting / 点击表头排序

结果表格可直接点击表头排序：

- 第一次点击按该列正序排列；
- 再次点击同一表头切换为逆序；
- 支持 Link、Collected time、Title、Source、Published time、Content status、Word count、Quality 等字段；
- `Published / 发布时间` 在 Result Preview 中统一显示为 **DD-MM-YYYY（日-月-年）**；原始发布时间文本仍保存在记录中，不因界面格式化而改写；
- Published 排序会先解析 ISO 日期、中文年月日、英文月份日期、搜索引擎相对时间（如 `3 hours ago`、`2天前`）等常见形式，再按实际日期先后排序，不再按字符串字面顺序排序；无法可靠解析的日期保留原文并排在可解析日期之后；
- 空值始终排在末尾；
- 词数和质量值按数值而不是字符串排序；
- 表格最左侧的 `1..N` 为固定显示序号，不作为数据字段保存，也不会随记录排序而移动；
- **Original order / 原始顺序** 可恢复当前仍保留记录的采集或导入顺序，不会把已经删除或抽样移除的记录重新加入。

---

## 5. Import and Export / 导入与导出

### Import / 导入

支持将已有 URL 列表导入 Result Preview：

- TXT：每行一个 URL；
- 无表头 XLSX：第一列为 URL；
- 无表头 CSV：第一列为 URL；
- CSV / TSV / 文本文件中的 URL；
- WebLens 已导出的 XLSX、CSV、TXT、XML、DOCX；
- 通过 **File → Download import template / 文件 → 下载导入模板** 创建的 XLSX 模板。

导入时只要求 URL 存在，标题、来源和日期可以暂时为空。正文下载成功后可进一步补全部分网页元信息。

### Export / 导出

采集结果可导出为：

- XLSX
- CSV
- TXT
- DOCX
- XML

结果文件用于保存采集链接及相关检索、来源和下载状态信息，可作为网络语料库建设过程中的来源记录和数据整理表。

---

## 6. Content Download / 正文下载

正文下载与搜索结果采集相互独立。用户可以先整理 Result Preview，再选择需要的记录下载正文。

主要功能包括：

- **Requests、Selenium、Mixed / 混合模式**；
- 下载选中记录或全部记录；
- 多线程下载；
- 失败重试；
- 单条任务超时；
- 同域名访问控制；
- 独立的 **Stop download / 停止下载**；
- 正文文本保存；
- 网页 metadata 保存；
- 最终 URL 更新；
- 缺失标题和发布时间的补充；
- 下载状态、词数和质量信息回写；
- `content_manifest.jsonl` 断点续下。

正文下载过程中，成功项目即时写盘。即使用户中途停止或发生异常，已经完成的正文文件和 checkpoint 仍然保留，后续可继续未完成部分。

---

## 7. Suggested corpus workflow / 推荐语料库工作流

WebLens 的定位不是单纯的网页爬虫，而是语料库建设前端的数据采集和来源整理工具。一个典型工作流可以是：

```text
BFSU WebLens
网络 / 新闻检索 → URL 与来源信息整理 → 正文下载
        ↓
BFSU ClearLens
正文清洗、编码统一、规则处理与人工复核
        ↓
BFSU MetadataLens
语料库元信息规范与记录管理
        ↓
后续语料检索、标注、统计分析与研究
```

WebLens is intended to make web-derived corpus data more traceable and reusable by preserving the connection among queries, result URLs, source webpages, downloaded texts and metadata.

---

## 8. Running from source / 源码运行

Python 3.10+ is recommended.

```text
pip install -r requirements.txt
python main.py
```

The application entry point is `main.py`.

### Windows build / Windows 打包

```text
build_exe.bat
```

To rebuild the isolated build environment:

```text
build_exe.bat --fresh
```

The project also contains macOS build scripts for Apple Silicon and Intel environments. Please refer to `BUILDING.md` for release-build details.

---

## 9. Maintenance / 维护

发布包和源码包包含 WebLens 自身的维护工具，可用于：

- 重置用户设置；
- 清理 WebLens 管理的便携浏览器和 WebDriver；
- 清理 WebLens 专用缓存；
- 执行发布版卸载辅助操作。

这些维护操作不会删除系统安装的 Chrome 或 Microsoft Edge。用户的语料输出和正文下载目录也不会被维护工具当作浏览器组件清除。

详细说明参见 `MAINTENANCE.md`。

---

## 10. Research use and published studies / 学术使用与成果反馈

如果您使用 **BFSU WebLens** 开展了研究，并发表了论文、著作、研究报告、语料库或其它学术成果，**欢迎通过邮件联系作者告知相关成果信息**。

在方便且符合作者授权、出版与链接使用要求的情况下，我们也希望将使用 BFSU WebLens 形成的相关论文和研究成果信息发布在项目介绍或项目成果页面中，作为软件实际应用案例，并方便其他研究者了解 WebLens 在语料库建设和语言研究中的使用情况。

联系时可提供论文题目、作者、期刊/出版社、年份、DOI 或公开链接等基本信息。

If you use **BFSU WebLens** in your research and publish an article, book, report, corpus or other academic output, you are very welcome to contact the author and let us know about the publication. Where appropriate and permitted, information about research produced with BFSU WebLens may be listed in the project description or a project publication page as examples of scholarly use.

**Contact / 联系方式：** djliu@bfsu.edu.cn

---

## 11. Notes on responsible use / 使用说明与责任提示

- WebLens 面向科研和语料库建设，不以高频、大规模自动访问为设计目标；
- 建议使用合理的翻页等待和访问频率；
- 出现搜索引擎人工验证时，应由用户自行完成验证，不建议尝试绕过网站访问控制；
- 用户应自行遵守目标网站的服务条款、robots/访问政策、版权要求、隐私要求、访问频率限制及相关法律法规；
- 自动抽取的正文、标题、发布时间及其它 metadata 可能存在误差，正式用于论文、语料库发布或统计分析前应进行必要的人工检查；
- WebLens 不保证第三方搜索引擎和网站页面结构长期不变，搜索引擎改版可能影响部分解析功能。

WebLens is intended for research-oriented, low-frequency and auditable collection. Users are responsible for complying with the terms, access policies, copyright requirements, privacy rules and applicable laws of the websites they access.

---

## 12. Project information / 项目信息

**Project / 项目：** BFSU LexiScope  
**Component / 工具：** BFSU WebLens  
**Developer / 开发者：** Dr. Dingjia LIU / 刘鼎甲 博士  
**Team / 团队：** BFSU Corpus Research Group / 北外语料库团队  
**Contact / 联系方式：** djliu@bfsu.edu.cn  
**BFSU Corpus Research Group / 北外语料库团队：** https://corpus.bfsu.edu.cn/  
**BFSUNLP GitHub：** https://github.com/bfsunlp  
**BFSU LexiScope：** https://github.com/bfsunlp/bfsu_lexiscope

OpenAI ChatGPT assisted parts of the development process, including code generation, feature iteration, testing support and documentation drafting. The overall software design, research orientation, functional decisions, testing confirmation and final responsibility remain with the developer.

Copyright © 2026 Dingjia LIU. All rights reserved.

---

## 13. Recent version history / 近期版本记录

### v3.1.9

- 采集任务人工停止或异常终止时自动保存已采集结果；
- 正文下载停止或异常时保存当前结果状态；
- 保留并强化正文下载断点续下机制；
- 统一使用 **BFSU Corpus Research Group / 北外语料库团队** 官方名称；
- 翻页等待范围改为界面按秒设置、内部按毫秒随机等待；
- Result Preview 的 Published 时间统一为 DD-MM-YYYY 显示，并改为实际日期排序。

### v3.1.8

- 首次运行增加 Chrome 与 Edge 一键配置；
- Result Preview 改为点击表头正序/逆序排序；
- 移除冗余 No. 数据列，固定使用表格左侧显示序号；
- 增加 Original order / 原始顺序恢复。

### v3.1.7

- 自动解析 Google News `google.* /goto?url=CAES...` 跳转地址，并在可用时直接保存真实外部 URL。

### v3.1.6

- 百度多检索词、多域名与日期切片按独立任务展开；
- 增加设置重置、Web 组件清理和卸载维护工具。

### v3.0.0

- 增加 Manual Collection / 手动采集工作流，可在普通浏览器中保存搜索结果 HTML 后批量导入，无需 Selenium。

---

**BFSU Corpus Research Group / 北外语料库团队**
