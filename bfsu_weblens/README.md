# BFSU WebLens v3.2.11

**BFSU WebLens** is the web and news corpus collection component of **BFSU LexiScope**, developed by the BFSU Corpus Research Group. It is designed for corpus construction, web/news corpus collection, corpus-based discourse studies, translation and media research, and other research workflows that require traceable discovery, review, downloading and organization of web resources.

**BFSU WebLens / 北外 WebLens 网络语料采集工具** 是 **BFSU LexiScope** 的网络语料采集组件，由北外语料库团队开发，面向网页语料库建设、新闻语料采集、语料库话语研究、翻译研究、国际传播与传媒研究等场景。软件将搜索结果发现、结果筛选与整理、链接导入导出、网页正文下载、元信息保存和语料文本准备整合为一个可追溯的工作流程。

```text
检索设置 → Google / 百度结果采集 → 结果预览、去重与整理
→ 排序 / 抽样 / 人工编辑 → 结果导出 → 正文下载
→ 正文与元信息保存 → 后续语料清洗、标注与分析
```

---

## 1. Download / 下载

**Current source version / 当前源码版本：** `BFSU WebLens v3.2.11`

**Latest published Windows x64 package / 当前公开 Windows x64 发布包：** `BFSU_WebLens_v3.2.11_windows_x64.zip`

**BFSU iCloud Direct Download / 北外 iCloud 直接下载：**  
https://icloud.bfsu.edu.cn/f/418fbeab261c479b9009/

**Baidu Netdisk / 百度网盘：**  
https://pan.baidu.com/s/1A03r2ghy6Y6yihQ51Atncw?pwd=vynu

**Extraction Code / 提取码：** `vynu`

下载后请**完整解压 ZIP 文件**，然后从完整发布目录运行 `BFSU_WebLens.exe`。不要只单独移动 EXE 文件，否则浏览器组件、配置文件或运行依赖可能无法正常找到。

After downloading, **extract the complete ZIP package** and run `BFSU_WebLens.exe` from the extracted release folder. Do not move the EXE file out of the release directory by itself.

---

## 2. What is new / 主要更新

### v3.2.11

- 修复 Google 结果页 Published/发布时间识别：支持当前 Google Web 结果卡摘要前缀中的 `.YrbPuc` 时间节点，可读取如 `2 天前`、`5 天前`、`2026年4月17日`、`2025年10月9日` 等可见时间；同时补充相对/绝对日期回退模式；
- Selenium live-DOM 备用解析路径同步加入相同的 Google 发布时间节点，避免序列化 HTML 与浏览器 DOM 两条解析路径行为不一致；
- 保持“搜索结果采集”和“正文下载”两阶段完全独立：搜索阶段记录 Google 结果页显示的时间作为暂定值；正文下载后如果目标页面可靠解析出 `published_time`，页面级时间将覆盖搜索阶段的暂定值；
- 其余 Google 搜索、人工验证、News + `site:` 已知问题、翻页、下载器抓取方式和 Result Preview 行为保持 v3.2.10 不变。

### v3.2.10

- **功能基线回退到 v3.2.6。** v3.2.10 不合并 v3.2.7–v3.2.9 对 Google News、人工验证或浏览器状态管理所做的后续实验性修改；除下列界面与文档更新外，采集逻辑保持 v3.2.6 状态；
- 修正 Result Preview：明确保留 **Title / 标题 / 標題** 列，即使当前记录尚无标题，表头也保持可见；
- Result Preview 全部数据列使用可交互列宽，用户可直接拖动表头分隔线调整列宽；
- **Known issue / 已知问题：Google News + 站点/域名限定。** 在 Google News 检索中加入 `site:` 域名限制时，可能触发 Google 自身的人工验证与自动跳转机制；验证完成后，Google 可能把可见结果类型从“新闻”切换到“全部/网页”。这是已观察到的 Google 端验证/跳转行为，**不是 WebLens 检索式构造错误**。WebLens 不绕过或强制改写 Google 的验证机制；如果发生切换，请先在浏览器中手动返回“新闻”结果页，再确认继续采集；
- 同步更新 README、软件内置 User Guide / 使用说明、Parameter Guide / 参数说明和 About / 关于。

### v3.2.6

- 统一 Result Preview 的 **Source / 来源** 字段语义：自动 Google/百度抓取、普通文件导入、粘贴文本解析链接、以及手动导入保存的搜索结果 HTML，在正文下载前都只填写目标 URL 的**主域名（可注册域名）**；例如 `j.people.com.cn → people.com.cn`、`news.yahoo.co.jp → yahoo.co.jp`；
- `actual_domain` 继续保存更具体的实际主机名，例如 `j.people.com.cn`，因此主域名与子域信息不会混淆或丢失；
- 对 Google `/goto` 结果，如果跳转成功解析为真实 URL，会立即按真实目标更新 Source 主域名；保存的搜索结果页面若只有 `/goto`，可从 Google 显示 URL/breadcrumb 或唯一 `site:` 限定补出主域名；
- 正文下载成功后，如果页面元数据可靠识别出 `source_name`、publication、`site_name`、publisher 或 organization，Result Preview 的 Source 会用该人类可读来源名称更新；如果识别不到，则明确回退到目标最终 URL 的主域名；
- 正文下载生成的 per-page metadata / `content_metadata.xlsx` 同步采用相同规则：`source` 为“识别到的来源名称，否则主域名”，同时保留 publisher、publication、organization、site_name、source_name 等原始元数据字段；
- 正文下载断点续下从既有 `content_manifest.jsonl` 恢复成功记录时，同样可以把已保存的来源元数据补回 Result Preview；
- v3.2.5 的卡片级 Google 结果提取、`/goto → final URL → URL dedup` 主逻辑保持不变。

### v3.2.5

- 重构 Google 结果提取与 `/goto` 去重机制：恢复以 v3.1.9 为主干的“跳转解析 → 最终 URL 去重”思路，删除基于标题、来源、发布时间猜测 direct URL 与 `/goto` 是否属于同一新闻的启发式合并；
- Google 页面解析改为以**可见结果卡片**为单位，每张卡片只提取一个主要标题/结果链接，不再使用 `#rso a[href]` 之类会把 Translate、Read more、摘要内部链接一起抓入的宽泛选择器；
- 同一卡片如果同时提供真实外部 URL 与 Google `/goto`，优先使用真实外部 URL；只有没有真实外链时才保留该卡片的 `/goto` 作为回退；
- 自动采集继续尝试通过 Google `/goto` 跳转端点读取真实 `Location`，成功后替换为真实外链，并立即按规范化最终 URL 做页面级去重；Result Preview 只保留确定性的 URL 去重，不再根据标题/来源/时间推测新闻身份；
- 使用用户提供的刷新后 Google 页面结构回归：旧逻辑会从 9 个主要结果卡片抽取 31 条候选（含 Read more、Translate 等辅助 `/goto`），新逻辑只提取 9 个主要结果卡片；另用含 direct + `/goto` 的合成卡片验证“真实外链优先、每卡片一条”；
- v3.2.4 已修复的“重置采集清除结果语种与国家/地区”、固定 8 词分批、断点续爬、验证码人工确认、Delete all 和正文下载断点续下均保持不变。

### v3.2.4

- 根据实际结果文件进一步修复 Google News 重复记录：当同一新闻的真实外部 URL 与 `google.com/goto?...` 通过不同解析/事件阶段先后到达时，Result Preview 在最终加入 Item 前再次执行一对一校验，真实外链优先；
- 在页面结果送出前增加第二道 Google News 卡片级去重，防止后续跳转解析或备用路径重新引入 direct URL / `/goto` 成对记录；
- 标题比较增加 Unicode 兼容规范化和零宽字符清理，提高同一可见标题在不同 DOM 序列化路径中的匹配稳定性；
- 修复 **Reset collection / 重置采集** 未真正清除 Google“结果语种”和“国家/地区”多选项的问题；`apply_settings()` 现在明确使用待应用设置中的选中值，不再让旧界面选择覆盖默认值或导入状态；
- Result Preview 的 Delete all / 删除全部、固定 8 词 OR 分批、搜索断点续爬、人工验证显式确认以及正文下载断点续下逻辑保持不变。

### v3.2.3

- 修复 Google News 同一个可见结果卡片可能同时暴露真实外部 URL 与 `google.com/goto?...`，导致 Result Preview 把 10 条可见结果记录成约 20 条的问题；
- 新逻辑只在“真实外链 + `/goto`”被判断为同一新闻卡片时合并，**优先保留真实外部 URL**；两个不同的真实外部 URL 不会仅因标题相同而被合并；
- 如果某条新闻只有独立的 `/goto` 且没有匹配的真实外链，仍保留它作为安全回退，并继续允许后续跳转解析/正文下载补全最终 URL；
- `/goto` 成功解析为真实外链后，再执行一次 URL 去重，避免解析后与已经存在的真实结果重复；
- Result Preview 新增 **Delete all / 删除全部** 按钮，可一次删除当前预览中的所有 Item；该操作不重置检索设置、采集设置或采集断点，并进入撤销栈，可立即 Undo；
- 同步更新 User Guide / 使用说明、Parameter Guide / 参数说明、About / 关于和 README。

### v3.2.2

- Simplified human-verification handling. When Google or Baidu shows a verification page, WebLens now blocks the collection worker and waits for an explicit user confirmation.
- While the verification dialog remains open, WebLens does **not** inspect the browser page, refresh it, follow Next, restart the browser, restore a URL, or force a Google News/Web vertical.
- After the user completes verification and visually confirms that the desired result page is ready, clicking **Verification complete, continue** makes WebLens read and parse the page that is already open.
- Removed the v3.2.1 Google query/vertical integrity guard and automatic URL restoration logic. Google pagination again follows the search engine's own Next link without WebLens rewriting the query/vertical parameters.
- Google custom date restriction continues to use the normal `tbs=cdr:1,cd_min:...,cd_max:...` parameter together with `tbm=nws` for News. WebLens does not forcibly correct the browser if Google changes the interface after verification; the user can adjust the visible page before confirming continuation.
- 简化人工验证流程：Google 或百度出现验证码后，采集线程完全暂停，等待用户明确确认。
- 验证提示窗口保持打开期间，WebLens **不会检查浏览器页面，也不会刷新、翻页、重启、恢复 URL 或强制检查 Google News/Web 类型**。
- 用户在浏览器中完成验证并目视确认需要的结果页面已经正常显示后，点击 **“验证完成，继续采集”**，WebLens 才读取当前已经打开的页面并继续。
- 移除 v3.2.1 中较复杂的 Google 检索式/vertical 强制校验与自动 URL 恢复逻辑；下一页重新直接跟随搜索引擎自身的 Next 链接。
- Google 日期限定仍采用正常的 `tbs=cdr` 自定义日期参数；若验证后 Google 自己切换了界面或标签，用户可在确认继续前直接在浏览器中调整，WebLens 不再强制改写。

### v3.2.0

### Fixed eight-term OR batching / OR 检索固定 8 词自动分批

- Google 的 `OR` 与“多个严格短语 OR”模式不再把大量检索词一次性拼成长查询；
- 当非空检索词超过 8 个时，WebLens 在内部自动按 **最多 8 个一批**拆分并依次执行，例如 17 个词自动拆成 `8 + 8 + 1`；
- **8 是程序内部固定规则，不在界面中提供可修改参数**，避免过长 OR 查询降低 Google Web / Google News 检索稳定性；
- 每个批次继续使用同一站点/域名、语种、国家/地区、日期切片等限制，所有结果最终统一进行全局 URL 去重；
- 百度的多检索词模式继续采用逐条检索，多域名继续拆成独立任务，因此不会构造超长 OR 查询；
- 手动采集生成初始搜索 URL 时同样遵循上述任务拆分规则。

### Resumable search collection / 搜索结果断点续爬

- 工具栏将原“开始采集”区分为 **Start new collection / 开始新的采集** 和 **Continue previous collection / 继续上一采集**；
- 自动采集会记录当前搜索任务/OR 批次、日期切片、页码、当前页、上一页及下一页 URL 等 checkpoint；
- 人工停止、异常中断或程序保存当前结果时，checkpoint 与已采集结果同步写入结果文件；
- “继续上一采集”要求 Result Preview 中仍存在已采集链接，并会**从上一个结果页安全回退一页**重新开始，然后用 Result Preview 中现有 URL 做全局去重，再继续向后翻页；
- 回退一页可以补回停止瞬间尚未完全写入的尾部结果，同时避免重新加入已经存在的链接；
- 某个具体日期切片、Google OR 批次或百度词/域名任务为空时，只结束当前小任务，不会错误终止整个采集计划。

### Crawl state embedded in result files / 结果文件同步保存采集状态

WebLens 的 XLSX、CSV、TXT、DOCX 和 XML 结果文件现在都可以同步携带采集状态：

- XLSX 使用隐藏的 WebLens 状态工作表；
- CSV、TXT、DOCX 和 XML 使用各自格式可识别的 WebLens 状态标记；
- 重新导入含有 WebLens 采集状态的结果文件时，软件会恢复对应 Google/百度面板的结果、检索设置和断点位置；
- 如果导入的是旧版 WebLens 文件或第三方文件，且没有检测到采集状态，则**仍然只按普通链接/结果文件导入，不创建断点状态**；
- 正文下载原有的 `content_manifest.jsonl` 断点续下机制保持独立且完整保留。

### Reset collection / 重置采集

主工具栏“打开下载文件夹”右侧新增 **Reset collection / 重置采集**。该操作只针对当前 Google 或百度面板：

- 清空 Result Preview 和搜索采集 checkpoint；
- 清空检索词和站点/域名等当前任务输入；
- 将检索设置、采集设置、**结果语种与国家/地区的当前选择**恢复默认值；
- 将采集链接保存路径/格式和正文下载设置恢复默认值；
- **不会删除全局 Chrome / Edge / Selenium 配置，也不会删除磁盘上已经保存的结果文件或正文文件。**

---

## 2A. Changes retained from v3.1.9 / v3.1.9 已保留改进

### Human-verification workflow / 人工验证流程

> **Known issue / 已知问题：Google News + `site:` 域名限定**  
> 在 Google News 中加入站点/域名限制时，Google 自身的人工验证与自动跳转机制可能被触发；验证后 Google 可能把结果页从“新闻”切换到“全部/网页”。这是已观察到的 Google 端验证/跳转行为，不是 WebLens 的检索式构造错误。WebLens 不尝试绕过或强制改写 Google 的验证机制。若发生切换，请在浏览器中手动返回“新闻”结果页，再点击“验证完成，继续采集”。  
> When a Google News query includes a `site:` restriction, Google's own verification/redirect handling may be triggered and may return the visible result page to All/Web after verification. This is an observed Google-side behavior, not a WebLens query-construction error. Return to News manually before confirming continuation.

- Google 与百度检测到人工验证页面后，WebLens 会保持浏览器原样并完全暂停采集线程；
- 验证提示窗口关闭前，程序不轮询浏览器 DOM，不刷新、不翻页、不重启浏览器，也不打开或恢复任何搜索 URL；
- 用户应在浏览器中完成人工验证，并目视确认希望采集的结果页已经正常显示；若 Google 在验证后切换了“全部/新闻”标签或改变了日期条件，可在浏览器中先手动调整；
- 只有用户回到 WebLens 并点击 **“验证完成，继续采集”** 后，软件才直接读取当前页面并继续解析；
- WebLens 不再强制检查地址栏是否属于 News，也不自动恢复 `tbm=nws` 或其它参数。

When a verification page appears, WebLens now waits for explicit user confirmation. The browser is left untouched while the confirmation dialog remains open. After completing verification and visually checking the desired result page, the user clicks **Verification complete, continue** and WebLens parses the page already open in the browser without URL restoration or forced vertical checks.

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
- Google 的 OR 组合模式超过 8 个检索词时自动按内部固定规则拆成每批最多 8 个，批次大小不提供用户设置；
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

当 Google 或百度出现人工验证页面时，WebLens 会完全暂停采集并保持确认提示窗口打开。在用户明确点击“验证完成，继续采集”之前，软件不会检查浏览器页面，也不会刷新、翻页、重启或重新导航浏览器。用户应先在浏览器中完成验证并目视确认需要的结果页已经正常显示；如果 Google 切换了“全部/新闻”标签或日期条件，可先手动调整。点击确认后，WebLens 才直接读取当前已经打开的页面继续采集，不强制改写地址栏。

### 3.4 Google News direct URL recovery / Google News 真实链接解析

当前 Google 页面有时会把主要结果链接写成：

```text
https://www.google.com/goto?url=CAES...
```

v3.2.5 不再通过标题、来源或发布时间去猜 direct URL 与 `/goto` 是否属于同一新闻，而是把**可见结果卡片**作为采集单位。每张卡片只读取主要标题/结果链接，忽略 Translate、Read more、摘要内部链接和其它辅助锚点；如果卡片直接提供真实外部 URL，则优先使用真实外链；否则保留该卡片的 `/goto`。

自动采集随后尝试访问 Google `/goto` 跳转端点，但不进入新闻正文，只读取 HTTP `Location`。解析成功后把记录链接替换为真实外部 URL，并立即按规范化最终 URL 去重。只有 Google 没有返回可用目标时才保留原 `/goto` 作为回退；正文下载阶段仍保留最终 URL 补全机制。Result Preview 自身只做确定性的 URL 去重，不再做标题/来源/时间启发式合并。

### 3.5 Manual Collection / 手动采集

除 Selenium 自动采集外，WebLens 还支持**手动采集**：

1. 在 WebLens 中填写正常的 Google 或百度检索参数；
2. 由 WebLens 生成一个或多个初始检索链接；
3. 用户在自己的日常浏览器中打开链接，自行处理人工验证并手动翻页；
4. 将各页搜索结果保存为 `.html` 或 `.htm`；
5. 在 WebLens 的 Manual Collection 窗口中批量导入；
6. 软件自动解析结果、去重并追加到 Result Preview。

该模式**不依赖 Selenium、ChromeDriver 或 EdgeDriver**，适合搜索引擎验证频繁或研究者希望完全控制翻页过程的情况。Google OR 输入超过 8 个词时，手动采集也会自动生成对应的多个批次初始 URL。

---

## 4. Result Preview and result management / 结果预览与整理

Google 与百度均使用独立的结果列表。Result Preview 支持：

- 打开链接；
- 删除所选记录；
- **删除全部**：一次清空当前 Result Preview 中的所有 Item，不重置检索设置、采集设置或采集断点，并可通过撤销立即恢复；
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

导入时只要求 URL 存在。无论输入文件原来是否带有来源文本，WebLens 在导入阶段都会按 URL 将 Source 规范化为主域名；标题和日期可以暂时为空。正文下载成功后，如果目标网页能可靠识别出版物/站点/机构名称，则用识别名称更新 Source，否则继续保留主域名。

如果导入文件包含 WebLens v3.2.0 的采集状态，软件会恢复对应搜索引擎面板、Result Preview、原检索设置和可继续采集的 checkpoint；如果没有检测到 WebLens 采集状态，则仍按普通链接/结果文件导入，不创建新的搜索采集断点。

### Export / 导出

采集结果可导出为：

- XLSX
- CSV
- TXT
- DOCX
- XML

结果文件用于保存采集链接及相关检索、来源和下载状态信息，可作为网络语料库建设过程中的来源记录和数据整理表。对于自动采集任务，结果文件还可携带 WebLens 搜索采集 checkpoint，供后续“继续上一采集”恢复使用。

---

## 6. New collection, resume and reset / 新采集、继续采集与重置

### Start new collection / 开始新的采集

按当前面板设置开始一个全新的搜索采集任务，并建立新的采集状态。Result Preview 会从空列表开始。

### Continue previous collection / 继续上一采集

当当前 Result Preview 中仍有已有结果，且当前任务存在有效 checkpoint 时可用。WebLens 会从保存 checkpoint 的**上一个结果页**开始重跑，并将 Result Preview 中已经存在的 URL 预先加入全局去重集合，然后继续翻页、日期切片和后续关键词批次/百度任务。

如果从 WebLens 结果文件恢复任务，软件会先恢复与该断点对应的搜索参数；若文件没有 WebLens 采集状态，则只执行普通导入，不启用“继续上一采集”。

### Reset collection / 重置采集

用于明确开始另一项采集工作。它清空当前搜索引擎面板的结果、checkpoint 和任务参数，并把检索、采集、语种/地区、链接保存及正文下载设置恢复默认。浏览器/Selenium 全局配置以及已经写入磁盘的文件保持不变。

---

## 7. Content Download / 正文下载

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
- 最终 URL 与实际域名更新；
- Source / 来源补全：下载前统一为主域名，下载后优先使用可靠识别的来源/出版物/站点/机构名称，识别不到则保留主域名；
- 缺失标题和发布时间的补充；
- 下载状态、词数和质量信息回写；
- `content_manifest.jsonl` 断点续下。

正文下载过程中，成功项目即时写盘，并把可靠识别的来源名称（或主域名回退）、最终 URL、实际域名、标题和发布时间等信息同步用于结果记录。即使用户中途停止或发生异常，已经完成的正文文件和 checkpoint 仍然保留，后续可继续未完成部分。

---

## 8. Suggested corpus workflow / 推荐语料库工作流

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

## 9. Running from source / 源码运行

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

## 10. Maintenance / 维护

发布包和源码包包含 WebLens 自身的维护工具，可用于：

- 重置用户设置；
- 清理 WebLens 管理的便携浏览器和 WebDriver；
- 清理 WebLens 专用缓存；
- 执行发布版卸载辅助操作。

这些维护操作不会删除系统安装的 Chrome 或 Microsoft Edge。用户的语料输出和正文下载目录也不会被维护工具当作浏览器组件清除。

详细说明参见 `MAINTENANCE.md`。

---

## 11. Research use and published studies / 学术使用与成果反馈

如果您使用 **BFSU WebLens** 开展了研究，并发表了论文、著作、研究报告、语料库或其它学术成果，**欢迎通过邮件联系作者告知相关成果信息**。

在方便且符合作者授权、出版与链接使用要求的情况下，我们也希望将使用 BFSU WebLens 形成的相关论文和研究成果信息发布在项目介绍或项目成果页面中，作为软件实际应用案例，并方便其他研究者了解 WebLens 在语料库建设和语言研究中的使用情况。

联系时可提供论文题目、作者、期刊/出版社、年份、DOI 或公开链接等基本信息。

If you use **BFSU WebLens** in your research and publish an article, book, report, corpus or other academic output, you are very welcome to contact the author and let us know about the publication. Where appropriate and permitted, information about research produced with BFSU WebLens may be listed in the project description or a project publication page as examples of scholarly use.

**Contact / 联系方式：** djliu@bfsu.edu.cn

---

## 12. Notes on responsible use / 使用说明与责任提示

- WebLens 面向科研和语料库建设，不以高频、大规模自动访问为设计目标；
- 建议使用合理的翻页等待和访问频率；
- 出现搜索引擎人工验证时，应由用户自行完成验证，不建议尝试绕过网站访问控制；
- 用户应自行遵守目标网站的服务条款、robots/访问政策、版权要求、隐私要求、访问频率限制及相关法律法规；
- 自动抽取的正文、标题、发布时间及其它 metadata 可能存在误差，正式用于论文、语料库发布或统计分析前应进行必要的人工检查；
- WebLens 不保证第三方搜索引擎和网站页面结构长期不变，搜索引擎改版可能影响部分解析功能。

WebLens is intended for research-oriented, low-frequency and auditable collection. Users are responsible for complying with the terms, access policies, copyright requirements, privacy rules and applicable laws of the websites they access.

---

## 13. Project information / 项目信息

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

## 14. Recent version history / 近期版本记录

### v3.2.10

- 以 v3.2.6 为功能基线，不合并 v3.2.7–v3.2.9 的后续 Google News/验证实验性修改；
- Result Preview 明确保留“标题”列，并允许用户拖动全部列的表头分隔线调整列宽；
- README、使用说明、参数说明和关于新增 Google News + `site:` 域名限定的已知问题说明：可能触发 Google 自身人工验证/自动跳转，并在验证后切换到“全部/网页”；该现象属于 Google 端行为，不是 WebLens 检索式构造错误。

### v3.2.6

- 统一 Source / 来源字段：抓取、普通导入、粘贴链接和手动导入搜索结果 HTML 时只写主域名；Actual domain 保留实际主机名；
- 正文下载成功后，可靠识别到来源/出版物/站点/机构名称时更新 Source，识别不到则回退主域名；
- Google `/goto` 解析成功后按真实目标域名更新 Source；只保存 `/goto` 的搜索结果 HTML 可从显示 URL/breadcrumb 或唯一 site 限定补主域名；
- per-page metadata、content_metadata.xlsx、断点续下恢复与 Result Preview 使用一致的来源补全规则；
- v3.2.5 的 Google 卡片级提取与最终 URL 去重逻辑保持不变。

### v3.2.5

- Google 结果解析改为“一张可见结果卡片 → 一个主要结果链接”，移除会采集 Translate、Read more 等辅助锚点的宽泛 `#rso a[href]` 路径；
- direct URL 与 `/goto` 的处理回归“优先直接外链；否则解析 `/goto`；最后按规范化最终 URL 去重”的确定性流程；
- 删除基于标题、来源和发布时间的 direct/goto 启发式配对，以及 Result Preview 中对应的故事身份猜测；
- 用户提供的刷新后 Google HTML 从旧逻辑 31 条候选收敛为 9 个主要结果卡片；
- v3.2.4 的语种/国家地区重置修复及其它采集、断点和下载功能保持不变。

### v3.2.4

- 根据实际导出结果进一步加强 Google News 真实 URL / `/goto` 去重：页面输出前与 Result Preview 加入前各执行一次一对一校验，真实外链优先；
- 标题匹配增加 Unicode 兼容规范化和零宽字符清理；
- 修复“重置采集”后结果语种和国家/地区仍保持旧选择的问题；
- 其它采集、断点续爬、人工验证与正文下载逻辑保持不变。

### v3.2.3

- 修复 Google News 同一卡片“真实 URL + `/goto` URL”被重复记录的问题，一个可见新闻结果只保留一条记录并优先保存真实外链；
- 独立且无法匹配真实外链的 `/goto` 仍作为后备保留；
- `/goto` 解析后再次执行 URL 去重；
- Result Preview 新增“删除全部”，只删除当前结果项，不重置检索/采集设置或断点，并支持撤销；
- 更新使用说明、参数说明、关于和 README。

### v3.2.2

- 人工验证改为“用户明确确认后继续”的完全暂停流程；
- 验证提示窗口打开期间不检查、刷新或导航浏览器；
- 移除 Google query/vertical 强制校验和自动 URL 恢复；
- Google/Baidu 均在用户点击“验证完成，继续采集”后直接解析浏览器当前页面；
- 固定 8 词 OR 分批、搜索断点续爬、结果状态持久化和正文下载断点续下均保持不变。

### v3.2.0

- Google OR / 多个严格短语 OR 超过 8 个检索词时自动按固定内部规则分批，批次大小不暴露给用户修改；
- 新增搜索结果采集断点续爬，从上一结果页安全回退并依据 Result Preview 全局去重；
- XLSX、CSV、TXT、DOCX、XML 可同步保存和恢复 WebLens 搜索采集状态；
- 普通无状态文件继续按传统链接/结果导入，不创建采集状态；
- 新增“开始新的采集”“继续上一采集”和“重置采集”工作流；
- Google 和百度共用统一的采集状态/恢复框架；百度多词仍逐条执行，不构造超长 OR；
- 正文下载的 `content_manifest.jsonl` 断点续下逻辑保持不变。

### v3.1.9

- 修正 Google News 使用站点/域名限定时，人工验证后可能漂移到普通 Web 检索的问题，并增加 News vertical 恢复检查；
- OR 检索词与 `site:` 域名约束使用明确分组，避免布尔作用域歧义；
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
