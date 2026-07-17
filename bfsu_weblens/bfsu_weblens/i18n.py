# -*- coding: utf-8 -*-
"""Interface strings for BFSU WebLens."""
TEXTS = {
    "en": {
        "app_title": "BFSU WebLens",
        "subtitle": "Search-result discovery for corpus and web-news research",
        "google_tab": "Google",
        "baidu_tab": "Baidu (reserved)",
        "bing_tab": "Bing (reserved)",
        "reserved_hint": "This engine tab is reserved for future integration.",
        "query_settings": "Google Query Settings",
        "limit_settings": "Language and Region Restrictions",
        "crawl_settings": "Crawl Settings",
        "output_settings": "Output Settings",
        "query_mode": "Query mode",
        "search_vertical": "Search vertical",
        "url_mode": "Google URL mode",
        "query_terms": "Search terms / phrases",
        "query_help_link": "How to fill search terms...",
        "site_filters": "Site/domain filters",
        "site_help_link": "Site/domain help...",
        "result_languages": "Result languages",
        "country_regions": "Country/region restrictions",
        "clear_selection": "Clear",
        "safe": "SafeSearch",
        "filter": "Disable duplicate filtering",
        "start_date": "Start date",
        "end_date": "End date",
        "max_pages": "Max pages per slice",
        "day_step": "Day step",
        "per_page": "Results per page",
        "page_delay": "Page delay ms",
        "slice_delay": "Slice delay ms",
        "error_delay": "Error cooldown ms",
        "timeout": "Timeout seconds",
        "output_file": "Output file",
        "output_format": "Output format",
        "browse": "Browse",
        "start": "Start",
        "stop": "Stop",
        "export": "Export",
        "clear": "Clear",
        "open_output": "Open output",
        "preview": "Result Preview",
        "log": "Log",
        "status_ready": "Ready.",
        "status_running": "Running...",
        "status_stopped": "Stopped.",
        "status_done": "Done.",
        "status_exported": "Exported.",
        "menu_file": "File",
        "menu_view": "View",
        "menu_language": "Interface language",
        "menu_help": "Help",
        "menu_about": "About",
        "menu_exit": "Exit",
        "menu_export": "Export results",
        "validation_error": "Validation error",
        "invalid_query": "Please enter search terms or a raw Google query.",
        "invalid_date": "Start date cannot be later than end date.",
        "invalid_output": "Please choose an output file.",
        "invalid_numeric": "Please check numeric settings. Delays cannot be negative, and minimum values cannot exceed maximum values.",
        "no_records": "No records to export.",
        "select_output": "Select output file",
        "network_hint": "Google cannot be reached or the request timed out. This may be related to proxy, DNS, firewall, or country/IP access restrictions.",
        "confirm_stop": "Stop requested. The current page will finish first.",
        "finished_export": "Exported {n} unique records to {path}",
        "about": "BFSU WebLens\nPart of the BFSU LexiScope toolkit.\nDesigned for low-frequency, auditable URL discovery and corpus-oriented web/news collection.",
        "help_query_title": "Search-term input guide",
        "help_site_title": "Site/domain filter guide",
        "date_picker_title": "Select date",
        "today": "Today",
        "cancel": "Cancel",
        "apply": "Apply",
        "year": "Year",
        "month": "Month",
        "weekday_names": "Mon Tue Wed Thu Fri Sat Sun",
        "query_help_text": """Search-term modes:\n\n1. Single term\n   Enter one term, e.g.\n   github\n\n2. Any term, OR\n   Enter multiple terms, one per line or separated by semicolons. The query becomes term1 OR term2.\n   Example:\n   drought\n   water shortage\n   water resources\n\n3. All terms\n   All terms are joined with spaces. Google usually treats this as an AND-like query.\n   Example:\n   water resources China\n\n4. Exact phrase\n   The first term is quoted automatically.\n   Example input: water resources\n   Query sent to Google: \"water resources\"\n\n5. Any exact phrase, OR\n   Each line is quoted and joined with OR.\n   Example input:\n   water resources\n   water shortage\n   Query sent to Google: \"water resources\" OR \"water shortage\"\n\n6. Raw Google query\n   Use this when you want full control. Examples:\n   site:cnn.com (\"water resources\" OR drought OR \"water shortage\")\n   intitle:github security\n   github -basketball\n\nUse English uppercase OR for Boolean OR in raw Google queries.""",
        "site_help_text": """Site/domain filters restrict results by Google's site: operator and by local URL filtering.\n\nExamples:\n\n1. Single website\n   cnn.com\n   -> site:cnn.com\n\n2. Government top-level domain\n   .gov\n   -> site:.gov\n   Matches URLs whose host ends with .gov.\n\n3. Chinese education domains\n   .edu.cn\n   -> site:.edu.cn\n   Matches university/research domains ending in .edu.cn.\n\n4. Multiple filters\n   Put one per line or separate with semicolons:\n   .gov;.edu.cn\n   cnn.com\n\n5. Already using site: in raw query\n   If your raw query already contains site:, leave this field empty to avoid duplication.\n\nNote: site:.gov and cr=countryUS are different. site:.gov limits by domain suffix; cr=countryUS restricts by Google's country/region collection.""",
    },
    "zh_sim": {
        "app_title": "BFSU WebLens",
        "subtitle": "面向语料库与网络新闻研究的检索结果采集工具",
        "google_tab": "Google",
        "baidu_tab": "百度（预留）",
        "bing_tab": "Bing（预留）",
        "reserved_hint": "该搜索引擎选项卡为后续集成预留。",
        "query_settings": "Google 检索设置",
        "limit_settings": "语种与国家/地区限定",
        "crawl_settings": "采集设置",
        "output_settings": "输出设置",
        "query_mode": "检索模式",
        "search_vertical": "检索范围",
        "url_mode": "Google URL 模式",
        "query_terms": "检索词/短语",
        "query_help_link": "检索词填写说明...",
        "site_filters": "站点/域名限定",
        "site_help_link": "站点/域名填写说明...",
        "result_languages": "结果语种",
        "country_regions": "国家/地区限定",
        "clear_selection": "清空选择",
        "safe": "安全搜索",
        "filter": "关闭重复过滤",
        "start_date": "起始日期",
        "end_date": "结束日期",
        "max_pages": "每片最大页数",
        "day_step": "日期步长",
        "per_page": "每页结果数",
        "page_delay": "翻页等待 ms",
        "slice_delay": "切片等待 ms",
        "error_delay": "错误冷却 ms",
        "timeout": "超时秒数",
        "output_file": "输出文件",
        "output_format": "输出格式",
        "browse": "浏览",
        "start": "开始采集",
        "stop": "停止",
        "export": "导出",
        "clear": "清空",
        "open_output": "打开输出",
        "preview": "结果预览",
        "log": "日志",
        "status_ready": "就绪。",
        "status_running": "正在运行……",
        "status_stopped": "已停止。",
        "status_done": "完成。",
        "status_exported": "已导出。",
        "menu_file": "文件",
        "menu_view": "视图",
        "menu_language": "界面语言",
        "menu_help": "帮助",
        "menu_about": "关于",
        "menu_exit": "退出",
        "menu_export": "导出结果",
        "validation_error": "参数错误",
        "invalid_query": "请输入检索词、短语或原始 Google 查询式。",
        "invalid_date": "起始日期不能晚于结束日期。",
        "invalid_output": "请选择输出文件。",
        "invalid_numeric": "请检查数值设置。等待时间不能为负，且最小值不能大于最大值。",
        "no_records": "没有可导出的记录。",
        "select_output": "选择输出文件",
        "network_hint": "请求超时或无法访问 Google。可能与代理、DNS、防火墙或国家/IP 访问限制有关。",
        "confirm_stop": "已请求停止。当前页面完成后将停止。",
        "finished_export": "已导出 {n} 条唯一记录至 {path}",
        "about": "BFSU WebLens\nBFSU LexiScope 工具箱组件。\n用于低频、可审计、面向语料库研究的 URL 发现与网络/新闻采集。",
        "help_query_title": "检索词填写说明",
        "help_site_title": "站点/域名限定说明",
        "date_picker_title": "选择日期",
        "today": "今天",
        "cancel": "取消",
        "apply": "应用",
        "year": "年份",
        "month": "月份",
        "weekday_names": "一 二 三 四 五 六 日",
        "query_help_text": """检索词模式说明：\n\n1. 单个检索词\n   输入一个词或短语，例如：\n   github\n\n2. 多个检索词：OR\n   多个检索词可逐行输入，也可用英文分号分隔。系统会生成 term1 OR term2。\n   示例：\n   drought\n   water shortage\n   water resources\n\n3. 多个检索词：全部包含\n   多个词用空格连接，Google 通常按近似 AND 的方式处理。\n   示例：\n   water resources China\n\n4. 严格连续短语\n   系统会自动给第一个输入项加英文双引号。\n   输入：water resources\n   发送给 Google：\"water resources\"\n\n5. 多个严格短语：OR\n   每一行都会加双引号，并用 OR 连接。\n   输入：\n   water resources\n   water shortage\n   发送给 Google：\"water resources\" OR \"water shortage\"\n\n6. 原始 Google 查询式\n   适合高级用户完全控制查询式。示例：\n   site:cnn.com (\"water resources\" OR drought OR \"water shortage\")\n   intitle:github security\n   github -basketball\n\n注意：原始查询式中的 OR 要使用英文大写 OR。""",
        "site_help_text": """站点/域名限定会同时使用 Google 的 site: 操作符和本地 URL 过滤。\n\n示例：\n\n1. 限定单个网站\n   cnn.com\n   -> site:cnn.com\n\n2. 限定美国政府顶级域名\n   .gov\n   -> site:.gov\n   匹配主机名以 .gov 结尾的网址。\n\n3. 限定中国高校/科研机构域名\n   .edu.cn\n   -> site:.edu.cn\n   匹配以 .edu.cn 结尾的网址。\n\n4. 多个限定\n   可逐行填写，或用英文分号分隔：\n   .gov;.edu.cn\n   cnn.com\n\n5. 原始查询式中已经写了 site:\n   如果 raw query 已经包含 site:，请把这里留空，避免重复限定。\n\n注意：site:.gov 和 cr=countryUS 不是一回事。site:.gov 按域名后缀限定；cr=countryUS 是 Google 的国家/地区集合限定。""",
    },
    "zh_tra": {
        "app_title": "BFSU WebLens",
        "subtitle": "面向語料庫與網路新聞研究的檢索結果採集工具",
        "google_tab": "Google",
        "baidu_tab": "百度（預留）",
        "bing_tab": "Bing（預留）",
        "reserved_hint": "該搜尋引擎選項卡為後續整合預留。",
        "query_settings": "Google 檢索設定",
        "limit_settings": "語種與國家/地區限定",
        "crawl_settings": "採集設定",
        "output_settings": "輸出設定",
        "query_mode": "檢索模式",
        "search_vertical": "檢索範圍",
        "url_mode": "Google URL 模式",
        "query_terms": "檢索詞/短語",
        "query_help_link": "檢索詞填寫說明...",
        "site_filters": "站點/域名限定",
        "site_help_link": "站點/域名填寫說明...",
        "result_languages": "結果語種",
        "country_regions": "國家/地區限定",
        "clear_selection": "清空選擇",
        "safe": "安全搜尋",
        "filter": "關閉重複過濾",
        "start_date": "起始日期",
        "end_date": "結束日期",
        "max_pages": "每片最大頁數",
        "day_step": "日期步長",
        "per_page": "每頁結果數",
        "page_delay": "翻頁等待 ms",
        "slice_delay": "切片等待 ms",
        "error_delay": "錯誤冷卻 ms",
        "timeout": "逾時秒數",
        "output_file": "輸出檔案",
        "output_format": "輸出格式",
        "browse": "瀏覽",
        "start": "開始採集",
        "stop": "停止",
        "export": "匯出",
        "clear": "清空",
        "open_output": "打開輸出",
        "preview": "結果預覽",
        "log": "日誌",
        "status_ready": "就緒。",
        "status_running": "正在執行……",
        "status_stopped": "已停止。",
        "status_done": "完成。",
        "status_exported": "已匯出。",
        "menu_file": "檔案",
        "menu_view": "檢視",
        "menu_language": "介面語言",
        "menu_help": "說明",
        "menu_about": "關於",
        "menu_exit": "退出",
        "menu_export": "匯出結果",
        "validation_error": "參數錯誤",
        "invalid_query": "請輸入檢索詞、短語或原始 Google 查詢式。",
        "invalid_date": "起始日期不能晚於結束日期。",
        "invalid_output": "請選擇輸出檔案。",
        "invalid_numeric": "請檢查數值設定。等待時間不能為負，且最小值不能大於最大值。",
        "no_records": "沒有可匯出的記錄。",
        "select_output": "選擇輸出檔案",
        "network_hint": "請求逾時或無法訪問 Google。可能與代理、DNS、防火牆或國家/IP 訪問限制有關。",
        "confirm_stop": "已請求停止。當前頁面完成後將停止。",
        "finished_export": "已匯出 {n} 條唯一記錄至 {path}",
        "about": "BFSU WebLens\nBFSU LexiScope 工具箱組件。\n用於低頻、可審計、面向語料庫研究的 URL 發現與網路/新聞採集。",
        "help_query_title": "檢索詞填寫說明",
        "help_site_title": "站點/域名限定說明",
        "date_picker_title": "選擇日期",
        "today": "今天",
        "cancel": "取消",
        "apply": "套用",
        "year": "年份",
        "month": "月份",
        "weekday_names": "一 二 三 四 五 六 日",
        "query_help_text": """檢索詞模式說明：\n\n1. 單個檢索詞\n   輸入一個詞或短語，例如：\n   github\n\n2. 多個檢索詞：OR\n   多個檢索詞可逐行輸入，也可用英文分號分隔。系統會生成 term1 OR term2。\n\n3. 多個檢索詞：全部包含\n   多個詞用空格連接，Google 通常按近似 AND 的方式處理。\n\n4. 嚴格連續短語\n   系統會自動給第一個輸入項加英文雙引號。\n\n5. 多個嚴格短語：OR\n   每一行都會加雙引號，並用 OR 連接。\n\n6. 原始 Google 查詢式\n   適合高階使用者完全控制查詢式。示例：\n   site:cnn.com (\"water resources\" OR drought OR \"water shortage\")\n   intitle:github security\n   github -basketball\n\n注意：原始查詢式中的 OR 要使用英文大寫 OR。""",
        "site_help_text": """站點/域名限定會同時使用 Google 的 site: 操作符和本地 URL 過濾。\n\n示例：\n\n1. 限定單個網站\n   cnn.com\n\n2. 限定政府頂級域名\n   .gov\n\n3. 限定中國高校/科研機構域名\n   .edu.cn\n\n4. 多個限定\n   可逐行填寫，或用英文分號分隔：\n   .gov;.edu.cn\n   cnn.com\n\n5. 原始查詢式中已經寫了 site:\n   如果 raw query 已經包含 site:，請把這裡留空，避免重複限定。\n\n注意：site:.gov 和 cr=countryUS 不是一回事。site:.gov 按域名後綴限定；cr=countryUS 是 Google 的國家/地區集合限定。""",
    },
}


# v0.5 extended help and concise field hints.
TEXTS["en"].update({
    "menu_user_guide": "User guide",
    "menu_parameter_guide": "Parameter guide",
    "max_pages_hint": "Meaning: maximum Google result pages visited inside each date slice. Example: 30 pages × 10 results/page ≈ up to 300 visible results per slice.",
    "output_hint": "XLSX is recommended. Export fields include collection time, title, source, displayed time, link, snippet, query URL, date slice, page, and rank.",
    "about": "BFSU WebLens\n\nPart of the BFSU LexiScope toolkit.\n\nPurpose: a low-frequency, auditable, corpus-oriented search-result collection utility. It currently implements a Google engine tab and reserves Baidu and Bing tabs for later integration.\n\nDesign: Tkinter desktop GUI, BFSU LexiScope / AlignLens style, threaded crawling to avoid UI freeze, multi-language interface, explicit parameter validation, and export to XLSX/CSV/TXT/DOCX/XML.\n\nCompliance note: this tool is designed for modest research collection and reproducible URL discovery. Use conservative delays, respect access restrictions, and avoid high-frequency automated access.",
    "user_guide_title": "BFSU WebLens User Guide",
    "parameter_guide_title": "Parameter Guide",
    "user_guide_text": """BFSU WebLens — User Guide\n\n1. Select the search engine tab\n   The Google tab is implemented. Baidu and Bing tabs are reserved for future development.\n\n2. Fill in Google Query Settings\n   Choose the query mode, search vertical, and search terms.\n   - Google News tab: adds tbm=nws and collects from Google's News vertical.\n   - Google Web search: ordinary Google search result pages.\n\n3. Choose date range\n   Use the date pickers for Start date and End date. The date range is split into slices according to Day step. For high-frequency topics, day_step=1 is recommended.\n\n4. Select language and country/region restrictions\n   Language list maps to Google's lr parameter. Country/region list maps to Google's cr parameter. Multiple selections are joined by the OR operator |. Leave them empty if no restriction is needed.\n\n5. Optional: site/domain filters\n   Examples: cnn.com, .gov, .edu.cn, .gov.cn. Multiple filters can be separated by new lines or semicolons.\n\n6. Start collection\n   Use the Start button in the fixed toolbar at the top of the Google tab. Progress is shown by the top and bottom progress bars. Stop requests take effect after the current page finishes.\n\n7. Review and export\n   Results appear in the preview table. The program auto-exports after crawling if records exist. You can also click Export manually. XLSX is recommended for research logging.\n\n8. Network and access issues\n   If requests time out or Google is unreachable, the program will warn that proxy, DNS, firewall, or country/IP access restrictions may be involved. Increase timeout or verify network access before retrying.\n""",
    "parameter_guide_text": """Parameter Guide\n\nQuery mode\n- Single term: one word or phrase, sent as typed.\n- Any term, OR: terms are joined as term1 OR term2.\n- All terms: terms are joined with spaces; Google usually treats this as an AND-like query.\n- Exact phrase: the first line is wrapped in quotation marks.\n- Any exact phrase, OR: each line is quoted and joined with OR.\n- Raw Google query: use your own Google syntax, e.g. site:cnn.com (\"water resources\" OR drought).\n\nSearch vertical\n- Google News tab: adds tbm=nws.\n- Google Web search: no tbm=nws.\n\nLanguage restriction (lr)\n- Restricts result document language more precisely than interface language.\n- Multiple languages are joined with |, e.g. lang_en|lang_fr.\n\nCountry/region restriction (cr)\n- Restricts result origin by Google's country/region collection.\n- Multiple countries are joined with |, e.g. countryUS|countryUK.\n\nMax pages per slice\n- A slice is one date range unit, such as one day when day_step=1.\n- Max pages per slice means the maximum Google result pages requested for that one date slice.\n- Example: max_pages=30 and per_page=10 means approximately up to 300 visible results in each date slice.\n\nDay step\n- Number of days per date slice.\n- day_step=1 means each day is searched separately.\n- Larger values reduce requests but may increase truncation for popular topics.\n\nResults per page\n- num parameter. 10 is recommended because Google pagination commonly advances by start=0,10,20...\n\nDelays in milliseconds\n- Page delay: wait between pages inside the same date slice.\n- Slice delay: wait between date slices.\n- Error cooldown: wait after HTTP 429, timeout, or temporary request errors.\n\nDisable duplicate filtering\n- Adds filter=0. It may expose more similar results but can also increase duplicates.\n\nSafeSearch\n- off, medium, high, or blank.\n\nOutput format\n- XLSX is recommended; CSV, TXT, DOCX, and XML are also supported.\n""",
})

TEXTS["zh_sim"].update({
    "menu_user_guide": "使用说明",
    "menu_parameter_guide": "参数说明",
    "max_pages_hint": "含义：每一个日期切片内最多访问多少页 Google 结果。例如：30 页 × 每页 10 条 ≈ 每个切片最多约 300 条可见结果。",
    "output_hint": "建议使用 XLSX。导出字段包括采集时间、标题、来源、页面显示时间、链接、摘要、查询 URL、日期切片、页码和排名。",
    "about": "BFSU WebLens\n\nBFSU LexiScope 工具箱组件。\n\n用途：面向语料库研究的低频、可审计、可复现的搜索结果采集与 URL 发现工具。目前实现 Google 搜索引擎选项卡，并为百度和 Bing 预留扩展入口。\n\n设计：Tkinter 桌面 GUI；延续 BFSU LexiScope / AlignLens 的界面风格；后台线程采集，避免界面卡死；支持英语、简体中文和繁体中文；对输入参数进行显式校验；支持 XLSX/CSV/TXT/DOCX/XML 导出。\n\n合规提示：本工具定位为科研辅助和低频采集工具。建议使用保守等待时间，尊重访问限制，避免高频自动访问。",
    "user_guide_title": "BFSU WebLens 使用说明",
    "parameter_guide_title": "参数说明",
    "user_guide_text": """BFSU WebLens 使用说明\n\n1. 选择搜索引擎选项卡\n   当前 Google 选项卡已实现。百度和 Bing 选项卡为后续扩展预留。\n\n2. 填写 Google 检索设置\n   选择检索模式、检索范围并输入检索词。\n   - Google 新闻标签：加入 tbm=nws，从 Google 的新闻垂直搜索页采集。\n   - Google 网页检索：普通 Google 网页搜索结果。\n\n3. 选择日期范围\n   起始日期和结束日期均通过日期选择器填写。程序会按照“日期步长”把总日期范围切成若干切片。热门主题建议 day_step=1，即按天检索。\n\n4. 选择结果语种和国家/地区限定\n   语种列表对应 Google 的 lr 参数。国家/地区列表对应 Google 的 cr 参数。多选时程序会自动用 OR 运算符 | 连接。不需要限定时可以留空。\n\n5. 可选：站点/域名限定\n   例如 cnn.com、.gov、.edu.cn、.gov.cn。多个限定可以逐行填写，也可以用英文分号分隔。\n\n6. 开始采集\n   点击 Google 选项卡顶部固定工具栏中的“开始采集”按钮。顶部和底部均有进度条。点击停止后，程序会在当前页面请求完成后停止。\n\n7. 查看和导出\n   结果会显示在右侧预览表格中。采集结束后如果有记录，程序会自动导出；也可以手动点击“导出”。科研记录建议使用 XLSX。\n\n8. 网络与访问问题\n   如果请求超时或无法访问 Google，程序会提示可能与代理、DNS、防火墙或国家/IP 访问限制有关。可检查网络、代理或适当增加超时秒数。\n""",
    "parameter_guide_text": """参数说明\n\n检索模式\n- 单个检索词：按用户输入发送一个词或短语。\n- 多个检索词：OR：生成 term1 OR term2。\n- 多个检索词：全部包含：用空格连接，Google 通常按近似 AND 的方式处理。\n- 严格连续短语：自动给第一行加英文双引号。\n- 多个严格短语：OR：每一行加双引号后用 OR 连接。\n- 原始 Google 查询式：用户完全控制查询式，如 site:cnn.com (\"water resources\" OR drought)。\n\n检索范围\n- Google 新闻标签：加入 tbm=nws。\n- Google 网页检索：不加入 tbm=nws。\n\n结果语种限定 lr\n- 用于较精确地限定结果文档语言。\n- 多个语种自动用 | 连接，例如 lang_en|lang_fr。\n\n国家/地区限定 cr\n- 使用 Google 的国家/地区集合值限定结果来源。\n- 多个国家/地区自动用 | 连接，例如 countryUS|countryUK。\n\n每片最大页数\n- “切片”指一个日期范围单位。day_step=1 时，一个切片就是一天。\n- 每片最大页数指每个日期切片内最多请求多少页 Google 结果。\n- 例如 max_pages=30 且 per_page=10，表示每个日期切片最多约 300 条可见结果。\n\n日期步长\n- 每个日期切片包含多少天。\n- day_step=1 表示逐日检索。\n- 值越大，请求越少，但热门主题越容易被结果上限截断。\n\n每页结果数\n- 对应 Google 的 num 参数。建议使用 10，因为 Google 翻页通常按 start=0,10,20... 推进。\n\n等待时间，单位毫秒\n- 翻页等待：同一日期切片内，页与页之间等待。\n- 切片等待：不同日期切片之间等待。\n- 错误冷却：遇到 429、超时或临时请求错误后的等待。\n\n关闭重复过滤\n- 添加 filter=0，可能获得更多相似结果，但也会增加重复。\n\n安全搜索\n- 可为空，也可设为 off、medium、high。\n\n输出格式\n- 推荐 XLSX；也支持 CSV、TXT、DOCX 和 XML。\n""",
})

TEXTS["zh_tra"].update({
    "menu_user_guide": "使用說明",
    "menu_parameter_guide": "參數說明",
    "max_pages_hint": "含義：每一個日期切片內最多訪問多少頁 Google 結果。例如：30 頁 × 每頁 10 條 ≈ 每個切片最多約 300 條可見結果。",
    "output_hint": "建議使用 XLSX。匯出欄位包括採集時間、標題、來源、頁面顯示時間、連結、摘要、查詢 URL、日期切片、頁碼和排名。",
    "about": "BFSU WebLens\n\nBFSU LexiScope 工具箱組件。\n\n用途：面向語料庫研究的低頻、可審計、可複現的搜尋結果採集與 URL 發現工具。目前實現 Google 搜尋引擎選項卡，並為百度和 Bing 預留擴展入口。\n\n設計：Tkinter 桌面 GUI；延續 BFSU LexiScope / AlignLens 的介面風格；後台執行採集，避免介面卡死；支持英語、簡體中文和繁體中文；對輸入參數進行顯式校驗；支持 XLSX/CSV/TXT/DOCX/XML 匯出。\n\n合規提示：本工具定位為科研輔助和低頻採集工具。建議使用保守等待時間，尊重訪問限制，避免高頻自動訪問。",
    "user_guide_title": "BFSU WebLens 使用說明",
    "parameter_guide_title": "參數說明",
    "user_guide_text": """BFSU WebLens 使用說明\n\n1. 選擇搜尋引擎選項卡\n   目前 Google 選項卡已實現。百度和 Bing 選項卡為後續擴展預留。\n\n2. 填寫 Google 檢索設定\n   選擇檢索模式、檢索範圍並輸入檢索詞。\n   - Google 新聞標籤：加入 tbm=nws。\n   - Google 網頁檢索：普通 Google 網頁搜尋結果。\n\n3. 選擇日期範圍\n   起始日期和結束日期均通過日期選擇器填寫。程式會按照“日期步長”把總日期範圍切成若干切片。熱門主題建議 day_step=1，即按天檢索。\n\n4. 選擇結果語種和國家/地區限定\n   語種列表對應 Google 的 lr 參數。國家/地區列表對應 Google 的 cr 參數。多選時程式會自動用 OR 運算符 | 連接。不需要限定時可以留空。\n\n5. 可選：站點/域名限定\n   例如 cnn.com、.gov、.edu.cn、.gov.cn。多個限定可以逐行填寫，也可以用英文分號分隔。\n\n6. 開始採集\n   點擊 Google 選項卡頂部固定工具欄中的“開始採集”按鈕。頂部和底部均有進度條。點擊停止後，程式會在當前頁面請求完成後停止。\n\n7. 查看和匯出\n   結果會顯示在右側預覽表格中。採集結束後如果有記錄，程式會自動匯出；也可以手動點擊“匯出”。科研記錄建議使用 XLSX。\n\n8. 網路與訪問問題\n   如果請求逾時或無法訪問 Google，程式會提示可能與代理、DNS、防火牆或國家/IP 訪問限制有關。可檢查網路、代理或適當增加逾時秒數。\n""",
    "parameter_guide_text": """參數說明\n\n檢索模式\n- 單個檢索詞：按使用者輸入發送一個詞或短語。\n- 多個檢索詞：OR：生成 term1 OR term2。\n- 多個檢索詞：全部包含：用空格連接，Google 通常按近似 AND 的方式處理。\n- 嚴格連續短語：自動給第一行加英文雙引號。\n- 多個嚴格短語：OR：每一行加雙引號後用 OR 連接。\n- 原始 Google 查詢式：使用者完全控制查詢式，如 site:cnn.com (\"water resources\" OR drought)。\n\n檢索範圍\n- Google 新聞標籤：加入 tbm=nws。\n- Google 網頁檢索：不加入 tbm=nws。\n\n結果語種限定 lr\n- 用於較精確地限定結果文檔語言。\n- 多個語種自動用 | 連接，例如 lang_en|lang_fr。\n\n國家/地區限定 cr\n- 使用 Google 的國家/地區集合值限定結果來源。\n- 多個國家/地區自動用 | 連接，例如 countryUS|countryUK。\n\n每片最大頁數\n- “切片”指一個日期範圍單位。day_step=1 時，一個切片就是一天。\n- 每片最大頁數指每個日期切片內最多請求多少頁 Google 結果。\n- 例如 max_pages=30 且 per_page=10，表示每個日期切片最多約 300 條可見結果。\n\n日期步長\n- 每個日期切片包含多少天。\n- day_step=1 表示逐日檢索。\n- 值越大，請求越少，但熱門主題越容易被結果上限截斷。\n\n每頁結果數\n- 對應 Google 的 num 參數。建議使用 10，因為 Google 翻頁通常按 start=0,10,20... 推進。\n\n等待時間，單位毫秒\n- 翻頁等待：同一日期切片內，頁與頁之間等待。\n- 切片等待：不同日期切片之間等待。\n- 錯誤冷卻：遇到 429、逾時或臨時請求錯誤後的等待。\n\n關閉重複過濾\n- 添加 filter=0，可能獲得更多相似結果，但也會增加重複。\n\n安全搜尋\n- 可為空，也可設為 off、medium、high。\n\n輸出格式\n- 推薦 XLSX；也支持 CSV、TXT、DOCX 和 XML。\n""",
})

# v0.11 original-script compatibility labels and guide additions.
TEXTS["en"].update({
    "url_mode": "Google URL mode",
    "parameter_guide_text": TEXTS["en"]["parameter_guide_text"] + """

12. Google URL mode

Original-compatible URL mode (recommended)
- This follows the user's earlier working script more closely.
- It sends the URL as: hl=en, start=0/10/20..., num=..., tbm=nws, and puts language/country restrictions inside tbs, for example lr:lang_1en and ctr:countryUS.
- Practical effect: for some Google News pages, this receives a parseable HTML result page where the documented top-level lr/cr parameters may return a JavaScript shell to Python requests.
- Recommended when ordinary Requests mode reports a JavaScript/redirect shell.

Documented lr/cr parameter mode
- Sends language and country restrictions as top-level lr=lang_en and cr=countryUS.
- This is closer to the public Programmable Search Engine documentation, but in direct Google Search HTML scraping it may receive a different page variant.
""",
})

TEXTS["zh_sim"].update({
    "url_mode": "Google URL 模式",
    "parameter_guide_text": TEXTS["zh_sim"]["parameter_guide_text"] + """

12. Google URL 模式

兼容原脚本 URL 模式（推荐）
- 该模式尽量复用你原先可以运行的脚本逻辑。
- URL 会带有 hl=en、start=0/10/20...、num=...、tbm=nws，并把语种和国别限制放入 tbs，例如 lr:lang_1en 和 ctr:countryUS。
- 实际影响：在部分 Google News 页面上，这种写法更容易让 Python requests 拿到可解析的 HTML 结果页；而顶层 lr/cr 参数有时会让 Google 返回 JavaScript 壳页。
- 当日志提示 JavaScript/redirect shell 时，优先使用这个模式。

官方 lr/cr 参数模式
- 把语种和国家/地区限制作为顶层参数发送，即 lr=lang_en、cr=countryUS。
- 该模式更接近官方参数说明，但在直接抓取 Google Search HTML 时，Google 可能返回不同页面变体。
""",
})

TEXTS["zh_tra"].update({
    "url_mode": "Google URL 模式",
    "parameter_guide_text": TEXTS["zh_tra"]["parameter_guide_text"] + """

12. Google URL 模式

兼容原腳本 URL 模式（推薦）
- 該模式盡量復用你原先可以運行的腳本邏輯。
- URL 會帶有 hl=en、start=0/10/20...、num=...、tbm=nws，並把語種和國別限制放入 tbs，例如 lr:lang_1en 和 ctr:countryUS。
- 實際影響：在部分 Google News 頁面上，這種寫法更容易讓 Python requests 拿到可解析的 HTML 結果頁；而頂層 lr/cr 參數有時會讓 Google 返回 JavaScript 殼頁。
- 當日誌提示 JavaScript/redirect shell 時，優先使用這個模式。

官方 lr/cr 參數模式
- 把語種和國家/地區限制作為頂層參數發送，即 lr=lang_en、cr=countryUS。
- 該模式更接近官方參數說明，但在直接抓取 Google Search HTML 時，Google 可能返回不同頁面變體。
""",
})

def t(lang: str, key: str, **kwargs) -> str:
    text = TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text

# v0.8 expanded documentation: more explicit outcomes, effects, and attribution.
TEXTS["en"].update({
    "about": """BFSU WebLens

Author: Liu Dingjia, Beijing Foreign Studies University.
Toolkit: BFSU LexiScope.
Module role: WebLens is designed as the web-search and news-search collection lens in the LexiScope toolkit.

GPT role: ChatGPT assisted the author in software prototyping, interface drafting, code refactoring, documentation drafting, and debugging suggestions. The software concept, research workflow, corpus-design requirements, naming, parameter strategy, and final use decisions are authored and directed by Liu Dingjia.

Purpose: BFSU WebLens is a low-frequency, auditable, corpus-oriented search-result collection utility. It currently implements a Google engine tab and reserves Baidu and Bing tabs for later integration.

Design: Tkinter desktop GUI, BFSU LexiScope / AlignLens visual style, threaded crawling to avoid UI freeze, English / Simplified Chinese / Traditional Chinese interfaces, explicit input validation, and export to XLSX / CSV / TXT / DOCX / XML.

Compliance note: this tool is designed for modest research collection and reproducible URL discovery. Use conservative delays, respect access restrictions, and avoid high-frequency automated access.""",
    "parameter_guide_text": """BFSU WebLens — Detailed Parameter Guide

This guide explains not only what each setting means, but also what it changes in the generated Google URL, what effect it usually has on the result set, and what trade-offs it introduces.

1. Search vertical

Google News tab
- Generated URL effect: adds tbm=nws.
- Result effect: Google returns results from its News vertical. Items tend to be news articles, media reports, press releases, and news-like pages.
- When to use: recommended for news corpus collection.
- Trade-off: the HTML layout differs from ordinary web search and may change more often. The parser therefore uses multiple selectors and diagnostics.

Google Web search
- Generated URL effect: does not add tbm=nws.
- Result effect: Google returns ordinary web-search results, including news, official pages, blogs, documentation, PDFs, and other pages.
- When to use: broader web corpus discovery rather than strict news collection.
- Trade-off: precision for news is lower, but coverage is broader.

2. Search terms and query mode

Single term
- Input effect: the first line is sent as typed.
- Example: github
- Result effect: broad recall. Useful for simple topic exploration.
- Risk: common words may return many irrelevant pages.

Any term, OR
- URL/query effect: terms are joined with OR, for example drought OR "water shortage".
- Result effect: increases recall because any one term may match.
- Risk: result set becomes broader and noisier. Use more time slicing for popular topics.

All terms
- URL/query effect: terms are separated by spaces, for example water resources China.
- Result effect: Google generally treats this as an AND-like query, so pages are more likely to contain all key concepts.
- Risk: may miss relevant pages that use synonyms.

Exact phrase
- URL/query effect: wraps the first term in quotation marks.
- Example input: water resources → query: "water resources".
- Result effect: improves precision by requiring a continuous phrase.
- Risk: lower recall; pages using water-resource management or water supply may be missed.

Any exact phrase, OR
- URL/query effect: each line is quoted and joined by OR.
- Example: "water resources" OR "water shortage".
- Result effect: balances precision and recall for a controlled synonym set.
- Risk: if the phrase list is too long, the query may become hard to interpret and results may fluctuate.

Raw Google query
- URL/query effect: WebLens sends the query exactly as typed.
- Examples:
  site:cnn.com ("water resources" OR drought OR "water shortage")
  intitle:github security
  github -basketball
- Result effect: maximum control.
- Risk: if raw query already contains site:, leave the Site/domain field empty to avoid duplicate constraints.

3. Site/domain filters

- Generated query effect: adds site: constraints to the q parameter, and WebLens also applies local URL filtering after extraction.
- Examples:
  cnn.com → site:cnn.com
  .gov → site:.gov and local host-suffix matching for .gov
  .edu.cn → site:.edu.cn and local host-suffix matching for .edu.cn
  .gov;.edu.cn → site:.gov OR site:.edu.cn
- Result effect: sharply restricts domains and improves corpus source control.
- Risk: too strict site/domain filters may produce zero records even when the Google page contains results from other domains. If diagnostics show result anchors but zero parsed records, first check this field.

4. Result language restriction, lr

- Generated URL effect: selected languages are joined with | and sent as lr, for example lang_en|lang_fr.
- Result effect: restricts the language of result documents. This is more precise than interface language.
- Research effect: improves language purity for corpus construction.
- Risk: Google language detection is not perfect. For high-quality corpora, run local language identification after downloading full text.
- Empty selection: no language restriction is added.

5. Country/region restriction, cr

- Generated URL effect: selected countries/regions are joined with | and sent as cr, for example countryUS|countryUK.
- Result effect: restricts result origin according to Google's country/region collection.
- Research effect: useful for building country-specific or region-specific corpora.
- Risk: country origin is not the same as the language of the page, the physical server location, or the outlet's editorial location. Use it as a search constraint, not as a final metadata truth.
- Empty selection: no country/region restriction is added.

6. Date range and date slicing

Start date / End date
- Generated URL effect: adds tbs=cdr:1,cd_min:M/D/YYYY,cd_max:M/D/YYYY.
- Result effect: restricts results to Google's date-filtered range.
- Research effect: supports reproducible time-bounded collection.

Day step
- Meaning: number of days in one search slice.
- day_step=1: one query per day.
- day_step=7: one query per week.
- Effect: smaller slices reduce truncation bias for popular topics because each slice has its own visible-result cap.
- Trade-off: smaller slices create more requests and longer total runtime.

Max pages per slice
- Meaning: maximum Google result pages visited inside each date slice.
- Example: day_step=1, max_pages=30, per_page=10 means up to about 300 visible results per day.
- Effect: higher values increase coverage within each date slice.
- Trade-off: more pages mean more requests, longer runtime, and higher risk of rate limiting.

Results per page
- Generated URL effect: adds num.
- Recommended value: 10.
- Reason: Google pagination normally advances by start=0,10,20... Even if a larger num is sometimes accepted, it can cause overlap or unstable behavior.

7. Delays and access safety

Page delay ms
- Effect: random waiting time between result pages in the same date slice.
- Default recommendation: 3000–8000 ms.
- Lower value: faster but more likely to trigger blocking.
- Higher value: slower but safer.

Slice delay ms
- Effect: random waiting time between date slices.
- Use it to prevent continuous rapid requests over long collection tasks.

Error cooldown ms
- Effect: waiting time after HTTP 429, timeout, connection error, or temporary request failure.
- If Google returns Retry-After, WebLens respects it when possible.

Timeout seconds
- Effect: maximum time to wait for a page response.
- If your network or country/IP cannot reach Google reliably, increase this value and check proxy/DNS/firewall settings.

8. Duplicate filtering and SafeSearch

Disable duplicate filtering
- Generated URL effect: adds filter=0.
- Result effect: may expose more similar pages that Google would otherwise suppress.
- Research effect: can improve recall, but increases duplicates.

SafeSearch
- Generated URL effect: adds safe=off, safe=medium, or safe=high if set.
- Result effect: affects adult/explicit content filtering.
- Corpus effect: keep it consistent across runs to maintain comparability.

9. Export settings

Output file
- Determines where results are saved.
- XLSX is recommended because it preserves column structure and is convenient for later manual checking.

Output format
- XLSX: recommended default.
- CSV: useful for data pipelines.
- TXT: URL-focused output.
- DOCX: useful for browsing/reporting.
- XML: useful for structured archival and interchange.

10. Parser diagnostics

If the log says no records were parsed, WebLens now reports counts such as a.WlydOe, YKoRaf, UWckNb, h3, /url?, and http_links.
- Positive counts but zero records may indicate site/domain filters excluded all results, or Google changed the card layout.
- Zero counts may indicate a consent page, block page, login-related page, or an HTML layout not yet supported.
- If the generated URL opens normally in Chrome but WebLens finds no records, save the HTML and compare these diagnostic counts.
""",
})

TEXTS["zh_sim"].update({
    "about": """BFSU WebLens

作者：刘鼎甲，北京外国语大学。
所属工具箱：BFSU LexiScope。
模块定位：WebLens 是 LexiScope 工具箱中的网络检索与新闻检索采集组件。

GPT 的角色：ChatGPT 参与了软件原型设计、界面草拟、代码重构、文档撰写和调试建议。软件概念、研究流程、语料库建设需求、命名、参数策略和最终使用决策均由刘鼎甲提出、设计并主导。

用途：BFSU WebLens 面向语料库研究，提供低频、可审计、可复现的搜索结果采集与 URL 发现功能。目前已实现 Google 搜索引擎选项卡，并为百度和 Bing 预留扩展入口。

设计：Tkinter 桌面 GUI；延续 BFSU LexiScope / AlignLens 的界面风格；后台线程采集，避免界面卡死；支持英语、简体中文和繁体中文；对输入参数进行显式校验；支持 XLSX / CSV / TXT / DOCX / XML 导出。

合规提示：本工具定位为科研辅助和低频采集工具。建议使用保守等待时间，尊重访问限制，避免高频自动访问。""",
    "parameter_guide_text": """BFSU WebLens 详细参数说明

本说明不仅解释“该填什么”，也说明该参数会如何改变 Google 查询 URL、会怎样影响结果集，以及会带来哪些取舍。

1. 检索范围

Google 新闻标签
- URL 结果：添加 tbm=nws。
- 结果影响：Google 返回新闻垂直搜索结果，通常包括新闻报道、媒体文章、新闻稿和新闻类页面。
- 适用场景：新闻语料采集首选。
- 取舍：新闻标签页 HTML 结构与普通网页检索不同，且变化较频繁，因此程序使用多套选择器和诊断信息。

Google 网页检索
- URL 结果：不添加 tbm=nws。
- 结果影响：返回普通网页搜索结果，可能包括新闻、官方网站、博客、文档、PDF 等。
- 适用场景：更广义的网络语料发现。
- 取舍：新闻精确性较低，但覆盖范围更广。

2. 检索词与检索模式

单个检索词
- 查询效果：第一行按原样发送。
- 示例：github。
- 结果影响：召回率高，适合初步探索。
- 风险：常见词可能带来较多无关结果。

多个检索词：OR
- 查询效果：自动拼成 term1 OR term2。
- 示例：drought OR "water shortage"。
- 结果影响：只要命中任一检索词即可，召回率更高。
- 风险：结果更宽泛，噪音更多；热门主题建议使用更细日期切片。

多个检索词：全部包含
- 查询效果：用空格连接多个词，如 water resources China。
- 结果影响：Google 通常按近似 AND 处理，结果更可能同时包含多个概念。
- 风险：可能漏掉使用同义表达的相关网页。

严格连续短语
- 查询效果：自动给第一个输入项加英文双引号。
- 示例：water resources → "water resources"。
- 结果影响：要求连续短语命中，精确性更高。
- 风险：召回率下降，使用变体表达的页面可能被漏掉。

多个严格短语：OR
- 查询效果：每行加引号后用 OR 连接。
- 示例："water resources" OR "water shortage"。
- 结果影响：在同义短语组内兼顾精确性和召回率。
- 风险：短语过多时，查询会变复杂，结果稳定性可能下降。

原始 Google 查询式
- 查询效果：完全按用户输入发送。
- 示例：site:cnn.com ("water resources" OR drought OR "water shortage")；intitle:github security；github -basketball。
- 结果影响：控制力最高。
- 风险：如果原始查询式里已经写了 site:，站点/域名限定处应留空，避免重复限定。

3. 站点/域名限定

- 查询效果：在 q 参数中添加 site: 限定，同时在解析后进行本地 URL 过滤。
- 示例：cnn.com → site:cnn.com；.gov → site:.gov 并匹配 .gov 结尾主机；.edu.cn → site:.edu.cn 并匹配 .edu.cn 结尾主机；.gov;.edu.cn → site:.gov OR site:.edu.cn。
- 结果影响：显著收紧来源范围，提高语料来源可控性。
- 风险：限定过严会导致零记录。若日志诊断显示页面中有结果锚点但无记录，首先检查该字段是否排除了所有结果。

4. 结果语种限定 lr

- URL 结果：多个语种用 | 连接后作为 lr 参数，如 lang_en|lang_fr。
- 结果影响：限定结果文档语言，比界面语言更精确。
- 语料影响：提高语料语言纯度。
- 风险：Google 的语言识别并非百分之百准确。高质量语料建议正文下载后再用本地语言识别复核。
- 留空：不添加语种限定。

5. 国家/地区限定 cr

- URL 结果：多个国家/地区用 | 连接后作为 cr 参数，如 countryUS|countryUK。
- 结果影响：按 Google 的国家/地区集合限定结果来源。
- 语料影响：适合构建特定国家或区域来源的语料。
- 风险：国家/地区来源不等同于网页语言、服务器所在地或媒体编辑部所在地，应作为检索约束，而不是最终元数据真值。
- 留空：不添加国家/地区限定。

6. 日期范围与日期切片

起始日期 / 结束日期
- URL 结果：添加 tbs=cdr:1,cd_min:M/D/YYYY,cd_max:M/D/YYYY。
- 结果影响：限定 Google 的日期过滤范围。
- 研究影响：支持可复现的时段采集。

日期步长
- 含义：一个日期切片包含多少天。
- day_step=1：每天一个查询片。
- day_step=7：每周一个查询片。
- 影响：切片越小，热门主题越不容易被单次查询可见结果上限截断。
- 取舍：切片越小，请求次数越多，总运行时间越长。

每片最大页数
- 含义：每个日期切片内最多访问多少页 Google 结果。
- 示例：day_step=1、max_pages=30、per_page=10，表示每天最多约 300 条可见结果。
- 影响：数值越大，单个日期片内覆盖率越高。
- 取舍：页数越多，请求越多、运行越慢，也越容易触发限制。

每页结果数
- URL 结果：添加 num 参数。
- 建议值：10。
- 原因：Google 翻页通常按 start=0,10,20... 推进。较大 num 有时可用，但可能造成重叠或不稳定。

7. 等待时间与访问安全

翻页等待 ms
- 影响：同一日期切片内，页与页之间随机等待。
- 默认建议：3000–8000 ms。
- 数值较低：速度快，但更容易触发限制。
- 数值较高：速度慢，但更稳妥。

切片等待 ms
- 影响：不同日期切片之间的随机等待。
- 作用：防止长任务连续高频请求。

错误冷却 ms
- 影响：遇到 HTTP 429、超时、连接错误或临时请求失败后的等待。
- 如果 Google 返回 Retry-After，程序会尽量遵守。

超时秒数
- 影响：单页请求最多等待多久。
- 如果当前网络或国家/IP 访问 Google 不稳定，可增大该值，并检查代理、DNS、防火墙。

8. 重复过滤与安全搜索

关闭重复过滤
- URL 结果：添加 filter=0。
- 结果影响：可能显示更多 Google 原本会抑制的相似结果。
- 研究影响：可能提高召回率，但会增加重复，需要后续去重。

安全搜索
- URL 结果：可添加 safe=off、safe=medium 或 safe=high。
- 结果影响：影响成人或露骨内容过滤。
- 语料影响：跨批次采集应保持一致，否则会影响可比性。

9. 输出设置

输出文件
- 指定结果保存位置。
- 推荐使用 XLSX，便于保留列结构和人工核查。

输出格式
- XLSX：推荐默认。
- CSV：适合数据管线。
- TXT：适合只保存 URL。
- DOCX：适合浏览和报告。
- XML：适合结构化归档和交换。

10. 解析诊断

如果日志提示没有解析到记录，WebLens 现在会报告 a.WlydOe、YKoRaf、UWckNb、h3、/url?、http_links 等计数。
- 这些计数为正但记录为 0：可能是站点/域名限定排除了结果，或 Google 卡片结构发生变化。
- 这些计数为 0：可能是同意页、异常流量页、登录相关页面，或尚未支持的 HTML 布局。
- 如果生成的 URL 在 Chrome 中能打开但软件无记录，可保存 HTML，与诊断计数一起定位问题。
""",
})

TEXTS["zh_tra"].update({
    "no_new_pages_limit": "連續無新增頁數後停止",
    "about": """BFSU WebLens

作者：劉鼎甲，北京外國語大學。
所屬工具箱：BFSU LexiScope。
模組定位：WebLens 是 LexiScope 工具箱中的網路檢索與新聞檢索採集組件。

GPT 的角色：ChatGPT 參與了軟體原型設計、介面草擬、程式碼重構、文檔撰寫和除錯建議。軟體概念、研究流程、語料庫建設需求、命名、參數策略和最終使用決策均由劉鼎甲提出、設計並主導。

用途：BFSU WebLens 面向語料庫研究，提供低頻、可審計、可複現的搜尋結果採集與 URL 發現功能。目前已實現 Google 搜尋引擎選項卡，並為百度和 Bing 預留擴展入口。

設計：Tkinter 桌面 GUI；延續 BFSU LexiScope / AlignLens 的介面風格；後台執行採集，避免介面卡死；支援英語、簡體中文和繁體中文；對輸入參數進行顯式校驗；支援 XLSX / CSV / TXT / DOCX / XML 匯出。

合規提示：本工具定位為科研輔助和低頻採集工具。建議使用保守等待時間，尊重訪問限制，避免高頻自動訪問。""",
    "parameter_guide_text": TEXTS["zh_sim"]["parameter_guide_text"].replace("参数", "參數").replace("检索", "檢索").replace("语种", "語種").replace("国家", "國家").replace("地区", "地區").replace("结果", "結果").replace("查询", "查詢").replace("设置", "設定").replace("输出", "輸出").replace("采集", "採集").replace("网络", "網路"),
})

# v0.10 request/parse stability labels and guide additions.
TEXTS["en"].update({
    "post_fetch_wait_ms": "Post-fetch wait ms",
    "empty_page_retry_count": "Empty-page retries",
    "empty_page_retry_wait_ms": "Empty-page retry wait ms",
    "no_new_pages_limit": "Stop after no-new pages",
    "parameter_guide_text": TEXTS["en"]["parameter_guide_text"] + """

11. Google response and parsing stability

User-Agent
- Current default: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36
- Effect: makes the request header closer to a modern desktop Chrome browser. This can reduce cases where Google returns a minimal shell page to Python requests.
- Limitation: it does not execute JavaScript and does not bypass Google access restrictions.

Post-fetch wait ms
- Effect: after a successful HTTP 200 response, the program waits before parsing.
- Important: Python requests is synchronous; it finishes downloading the HTTP body before resp.text is parsed. This setting does not wait for JavaScript rendering. It only spaces parsing/retry steps and helps diagnose unstable Google responses.
- Suggested values: 500–1500 ms. Use 0 to disable.

Empty-page retries
- Effect: if the downloaded HTML contains no recognizable result cards, the program waits and requests the same page again.
- Why useful: Google may return different HTML to non-browser requests, including consent pages, JavaScript redirect shells, login-related shells, or A/B layouts.
- Suggested values: 1–3. Higher values slow the crawl and may increase access pressure.

Empty-page retry wait ms
- Effect: waiting time before retrying a page whose HTML has no parseable result records.
- Suggested values: 1000–3000 ms.

No-new pages stop
- Effect: after URL normalization and duplicate filtering, if this many consecutive result pages add no new valid external links, WebLens stops the current date slice.
- Suggested value: 2. This prevents Google navigation links such as Home, Maps, Images, and Preferences from keeping pagination alive.

Debug HTML
- When parsing fails, WebLens saves the actual HTML received by Python into weblens_debug_html/.
- If the debug HTML has no a.WlydOe, no YKoRaf, no h3, and very few http links, the problem is not the parser; it means Python received a different page from the one visible in Chrome.
""",
})

TEXTS["zh_sim"].update({
    "post_fetch_wait_ms": "获取后等待 ms",
    "empty_page_retry_count": "空结果页重试次数",
    "empty_page_retry_wait_ms": "空结果页重试等待 ms",
    "no_new_pages_limit": "连续无新增页数后停止",
    "parameter_guide_text": TEXTS["zh_sim"]["parameter_guide_text"] + """

11. Google 响应与解析稳定性

User-Agent
- 当前默认值：Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36
- 影响：让请求头更接近现代桌面版 Chrome，减少 Google 向 Python requests 返回极简壳页面的概率。
- 限制：它不能执行 JavaScript，也不能绕过 Google 的访问限制。

获取后等待 ms
- 影响：收到 HTTP 200 响应后，程序先等待一小段时间再解析。
- 重要说明：Python requests 是同步请求；程序调用 resp.text 前，HTTP 响应体已经下载完成。因此这个参数不是为了“等网页下载完”，而是为了在 Google 返回不稳定壳页面时提供缓冲和诊断空间。它不能等待 JavaScript 渲染结果。
- 建议值：500–1500 ms。填 0 表示关闭。

空结果页重试次数
- 影响：如果下载到的 HTML 中没有可识别的结果卡片，程序会等待后重新请求同一页。
- 适用场景：Google 可能给非浏览器请求返回同意页、JS 跳转壳、登录相关壳页面或 A/B 布局，而不是 Chrome 中看到的完整结果 DOM。
- 建议值：1–3。数值过大会拖慢采集，也会增加访问压力。

空结果页重试等待 ms
- 影响：每次空结果页重试前等待多久。
- 建议值：1000–3000 ms。

连续无新增页数后停止
- 影响：URL 标准化和去重后，如果连续达到该数量的结果页都没有新增有效外部链接，WebLens 会停止当前日期切片。
- 建议值：2。这样 Home、Maps、Images、Preferences 等 Google 导航链接不会让翻页无限继续。

调试 HTML
- 解析失败时，WebLens 会把 Python 实际收到的 HTML 保存到 weblens_debug_html/。
- 如果调试 HTML 里没有 a.WlydOe、YKoRaf、h3，且 http_links 很少，问题通常不在解析器，而是 Python 请求得到的页面与 Chrome 中看到的页面不同。
""",
})

TEXTS["zh_tra"].update({
    "post_fetch_wait_ms": "獲取後等待 ms",
    "empty_page_retry_count": "空結果頁重試次數",
    "empty_page_retry_wait_ms": "空結果頁重試等待 ms",
    "no_new_pages_limit": "連續無新增頁數後停止",
    "parameter_guide_text": TEXTS["zh_tra"]["parameter_guide_text"] + """

11. Google 回應與解析穩定性

User-Agent
- 目前預設值：Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36
- 影響：讓請求頭更接近現代桌面版 Chrome，降低 Google 向 Python requests 返回極簡殼頁面的概率。
- 限制：它不能執行 JavaScript，也不能繞過 Google 的訪問限制。

獲取後等待 ms
- 影響：收到 HTTP 200 回應後，程式先等待一小段時間再解析。
- 重要說明：Python requests 是同步請求；程式讀取 resp.text 前，HTTP 回應體已經下載完成。因此這個參數不是為了“等網頁下載完”，而是為了在 Google 返回不穩定殼頁面時提供緩衝和診斷空間。它不能等待 JavaScript 渲染結果。
- 建議值：500–1500 ms。填 0 表示關閉。

空結果頁重試次數
- 影響：如果下載到的 HTML 中沒有可識別的結果卡片，程式會等待後重新請求同一頁。
- 適用場景：Google 可能給非瀏覽器請求返回同意頁、JS 跳轉殼、登入相關殼頁面或 A/B 版面，而不是 Chrome 中看到的完整結果 DOM。
- 建議值：1–3。數值過大會拖慢採集，也會增加訪問壓力。

空結果頁重試等待 ms
- 影響：每次空結果頁重試前等待多久。
- 建議值：1000–3000 ms。

連續無新增頁數後停止
- 影響：URL 標準化和去重後，如果連續達到該數量的結果頁都沒有新增有效外部連結，WebLens 會停止當前日期切片。
- 建議值：2。這樣 Home、Maps、Images、Preferences 等 Google 導航連結不會讓翻頁無限繼續。

調試 HTML
- 解析失敗時，WebLens 會把 Python 實際收到的 HTML 保存到 weblens_debug_html/。
- 如果調試 HTML 裡沒有 a.WlydOe、YKoRaf、h3，且 http_links 很少，問題通常不在解析器，而是 Python 請求得到的頁面與 Chrome 中看到的頁面不同。
""",
})

# v0.12: browser backend and removal of URL-mode selector.
TEXTS["en"].update({
    "fetch_backend": "Fetch backend",
    "browser_wait_ms": "Browser wait ms",
    "browser_headless": "Headless browser mode",
    "parameter_guide_text": TEXTS["en"]["parameter_guide_text"] + """

12. Fetch backend and browser rendering

Selenium Chrome browser (recommended)
- Generated workflow effect: WebLens opens a real Chrome window, navigates to the generated Google URL, waits for the page to render, then parses the browser DOM.
- Result effect: this can read result cards such as a.WlydOe / YKoRaf when Google returns only a JavaScript or redirect shell to raw requests.
- When to use: use this by default when logs say: Google returned a JavaScript/redirect shell, html_len is large, but a.WlydOe=0 and http_links is very small.
- Requirement: install selenium; Selenium Manager will normally locate or download the matching browser driver automatically.

Selenium Edge browser
- Same logic as Chrome, but uses Microsoft Edge. It is useful if Edge is more stable on a particular Windows machine.

Requests HTTP mode
- Generated workflow effect: WebLens downloads the raw HTTP response with requests and parses it directly.
- Result effect: faster and lighter, but cannot execute JavaScript. If Google returns a JS shell, it will still parse zero records.
- When to use: only use it when you have verified that requests can receive result-card HTML on your network.

Browser wait ms
- Effect: after the browser reports document.readyState, WebLens waits this many milliseconds before reading page_source.
- Why it matters: Google News cards may appear shortly after the initial document load.
- Recommended value: 2500–5000 ms. Increase it if pages load slowly.

Headless browser mode
- Effect: runs Chrome/Edge without a visible window.
- Trade-off: faster and less intrusive, but Google may return different pages to headless browsers. For stability, visible browser mode is recommended.

URL mode selector
- Removed in v0.12. WebLens now uses explicit Google lr and cr parameters directly, while the fetch backend controls whether pages are obtained by requests or by a real browser.
""",
})

TEXTS["zh_sim"].update({
    "fetch_backend": "采集后端",
    "browser_wait_ms": "浏览器等待 ms",
    "browser_headless": "无头浏览器模式",
    "parameter_guide_text": TEXTS["zh_sim"]["parameter_guide_text"] + """

12. 采集后端与浏览器渲染

Selenium Chrome 浏览器模式（推荐）
- 工作流影响：WebLens 会打开真实 Chrome 窗口，访问生成的 Google URL，等待页面渲染完成，然后解析浏览器 DOM。
- 结果影响：当 Google 给 requests 返回 JavaScript/redirect shell，但真实浏览器能看到 a.WlydOe / YKoRaf 结果卡片时，该模式可以读取真实渲染后的结果。
- 适用场景：日志出现“Google returned a JavaScript/redirect shell”，且 html_len 很大，但 a.WlydOe=0、http_links 很少时，优先使用该模式。
- 依赖要求：需要安装 selenium；新版 Selenium 通常会通过 Selenium Manager 自动定位或下载匹配的浏览器驱动。

Selenium Edge 浏览器模式
- 与 Chrome 模式逻辑相同，但使用 Microsoft Edge。若用户机器上 Edge 更稳定，可选择该模式。

Requests HTTP 模式
- 工作流影响：使用 requests 直接下载原始 HTTP 响应并解析。
- 结果影响：速度快、资源占用低，但不能执行 JavaScript。如果 Google 返回 JS 壳页，仍然会解析为 0 条。
- 适用场景：只有在确认当前网络下 requests 能拿到 Google 结果卡片 HTML 时再使用。

浏览器等待 ms
- 影响：浏览器报告 document.readyState 后，WebLens 继续等待多少毫秒再读取 page_source。
- 原因：Google News 结果卡片有时会在初始文档加载后稍晚出现。
- 建议值：2500–5000 ms。如果页面加载慢，可以增大。

无头浏览器模式
- 影响：Chrome/Edge 不显示窗口，在后台运行。
- 取舍：更省界面空间，但 Google 可能给无头浏览器返回不同页面。为保证稳定，推荐先用可见浏览器模式。

URL 模式选择
- v0.12 已移除。WebLens 现在统一使用明确的 Google lr 与 cr 参数；由采集后端决定是用 requests 直接获取，还是用真实浏览器获取渲染后的页面。
""",
})

TEXTS["zh_tra"].update({
    "fetch_backend": "採集後端",
    "browser_wait_ms": "瀏覽器等待 ms",
    "browser_headless": "無頭瀏覽器模式",
    "parameter_guide_text": TEXTS["zh_tra"]["parameter_guide_text"] + """

12. 採集後端與瀏覽器渲染

Selenium Chrome 瀏覽器模式（推薦）
- 工作流影響：WebLens 會打開真實 Chrome 視窗，訪問生成的 Google URL，等待頁面渲染完成，然後解析瀏覽器 DOM。
- 結果影響：當 Google 給 requests 返回 JavaScript/redirect shell，但真實瀏覽器能看到 a.WlydOe / YKoRaf 結果卡片時，該模式可以讀取真實渲染後的結果。
- 適用場景：日誌出現 “Google returned a JavaScript/redirect shell”，且 html_len 很大，但 a.WlydOe=0、http_links 很少時，優先使用該模式。
- 依賴要求：需要安裝 selenium；新版 Selenium 通常會透過 Selenium Manager 自動定位或下載匹配的瀏覽器驅動。

Selenium Edge 瀏覽器模式
- 與 Chrome 模式邏輯相同，但使用 Microsoft Edge。若使用者機器上 Edge 更穩定，可選擇該模式。

Requests HTTP 模式
- 工作流影響：使用 requests 直接下載原始 HTTP 回應並解析。
- 結果影響：速度快、資源佔用低，但不能執行 JavaScript。如果 Google 返回 JS 殼頁，仍然會解析為 0 條。
- 適用場景：只有在確認當前網路下 requests 能拿到 Google 結果卡片 HTML 時再使用。

瀏覽器等待 ms
- 影響：瀏覽器報告 document.readyState 後，WebLens 繼續等待多少毫秒再讀取 page_source。
- 原因：Google News 結果卡片有時會在初始文檔載入後稍晚出現。
- 建議值：2500–5000 ms。如果頁面載入慢，可以增大。

無頭瀏覽器模式
- 影響：Chrome/Edge 不顯示視窗，在背景運行。
- 取捨：更省介面空間，但 Google 可能給無頭瀏覽器返回不同頁面。為保證穩定，推薦先用可見瀏覽器模式。

URL 模式選擇
- v0.12 已移除。WebLens 現在統一使用明確的 Google lr 與 cr 參數；由採集後端決定是用 requests 直接獲取，還是用真實瀏覽器獲取渲染後的頁面。
""",
})

# v0.13: local driver path support.
TEXTS["en"].update({
    "browser_driver_path": "Browser driver path",
    "browse_driver": "Browse",
    "select_driver": "Select ChromeDriver / EdgeDriver",
    "parameter_guide_text": TEXTS["en"]["parameter_guide_text"] + """

13. Browser driver path

What it controls
- This path tells Selenium exactly where chromedriver.exe or msedgedriver.exe is located.
- If it is blank or the file does not exist, WebLens tries tools/chromedriver.exe or tools/msedgedriver.exe, then PATH, then Selenium Manager.

Recommended project layout on Windows
BFSU_WebLens/
├─ main.py
├─ tools/
│  └─ chromedriver.exe

Common causes of driver errors
- The file is named chromedriver-win64.exe instead of chromedriver.exe. Rename it to chromedriver.exe.
- The file is inside tools/chromedriver-win64/chromedriver.exe rather than tools/chromedriver.exe. Either move it or choose the nested file with Browse.
- ChromeDriver major version does not match Chrome major version. For example, Chrome 152 usually needs ChromeDriver 152.
- Windows blocked the downloaded executable. Right-click chromedriver.exe → Properties → Unblock, if shown.
- You selected Chrome backend but provided msedgedriver.exe, or selected Edge backend but provided chromedriver.exe.
""",
})

TEXTS["zh_sim"].update({
    "browser_driver_path": "浏览器驱动路径",
    "browse_driver": "浏览",
    "select_driver": "选择 ChromeDriver / EdgeDriver",
    "parameter_guide_text": TEXTS["zh_sim"]["parameter_guide_text"] + """

13. 浏览器驱动路径

控制什么
- 这个路径用于明确告诉 Selenium：chromedriver.exe 或 msedgedriver.exe 在哪里。
- 如果路径为空或文件不存在，WebLens 会依次尝试 tools/chromedriver.exe 或 tools/msedgedriver.exe、系统 PATH，然后才使用 Selenium Manager 自动查找/下载。

Windows 下推荐目录结构
BFSU_WebLens/
├─ main.py
├─ tools/
│  └─ chromedriver.exe

常见错误原因
- 文件名是 chromedriver-win64.exe，而不是 chromedriver.exe。请改名为 chromedriver.exe。
- 文件放在 tools/chromedriver-win64/chromedriver.exe 里，而不是 tools/chromedriver.exe。可以移动出来，也可以点击“浏览”选择里面那个 exe。
- ChromeDriver 主版本与 Chrome 主版本不一致。例如 Chrome 152 通常需要 ChromeDriver 152。
- Windows 阻止了下载的 exe。右键 chromedriver.exe → 属性 → 如果看到“解除锁定”，请勾选。
- 选择了 Chrome 后端，却填写了 msedgedriver.exe；或者选择了 Edge 后端，却填写了 chromedriver.exe。
""",
})

TEXTS["zh_tra"].update({
    "browser_driver_path": "瀏覽器驅動路徑",
    "browse_driver": "瀏覽",
    "select_driver": "選擇 ChromeDriver / EdgeDriver",
    "parameter_guide_text": TEXTS["zh_tra"]["parameter_guide_text"] + """

13. 瀏覽器驅動路徑

控制什麼
- 這個路徑用於明確告訴 Selenium：chromedriver.exe 或 msedgedriver.exe 在哪裡。
- 如果路徑為空或檔案不存在，WebLens 會依次嘗試 tools/chromedriver.exe 或 tools/msedgedriver.exe、系統 PATH，然後才使用 Selenium Manager 自動查找/下載。

Windows 下推薦目錄結構
BFSU_WebLens/
├─ main.py
├─ tools/
│  └─ chromedriver.exe

常見錯誤原因
- 檔名是 chromedriver-win64.exe，而不是 chromedriver.exe。請改名為 chromedriver.exe。
- 檔案放在 tools/chromedriver-win64/chromedriver.exe 裡，而不是 tools/chromedriver.exe。可以移動出來，也可以點擊「瀏覽」選擇裡面的 exe。
- ChromeDriver 主版本與 Chrome 主版本不一致。例如 Chrome 152 通常需要 ChromeDriver 152。
- Windows 阻止了下載的 exe。右鍵 chromedriver.exe → 內容 → 如果看到「解除鎖定」，請勾選。
- 選擇了 Chrome 後端，卻填寫了 msedgedriver.exe；或者選擇了 Edge 後端，卻填寫了 chromedriver.exe。
""",
})

# v0.14: browser binary path support.  ChromeDriver controls the browser, but
# Selenium also needs to know where chrome.exe / msedge.exe is installed when the
# browser is not in a standard system location.
TEXTS["en"].update({
    "browser_binary_path": "Browser binary path",
    "browse_binary": "Browse",
    "select_browser_binary": "Select Chrome / Edge executable",
    "browser_startup_hint": "The Selenium browser could not be started. This is a local browser/driver configuration issue, not a Google network-access issue.",
    "parameter_guide_text": TEXTS["en"]["parameter_guide_text"] + """

14. Browser binary path

What it controls
- This path points to the actual browser program, such as chrome.exe or msedge.exe.
- It is different from the browser driver path. The driver path points to chromedriver.exe / msedgedriver.exe; the browser binary path points to Chrome or Edge itself.
- If ChromeDriver reports "cannot find Chrome binary", fill this field manually.

Common Chrome locations on Windows
- C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe
- C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe
- C:\\Users\\<your name>\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe
- C:\\Program Files\\Google\\Chrome Dev\\Application\\chrome.exe
- C:\\Users\\<your name>\\AppData\\Local\\Google\\Chrome SxS\\Application\\chrome.exe

Typical pairing
- Selenium Chrome backend + chromedriver.exe + chrome.exe.
- Selenium Edge backend + msedgedriver.exe + msedge.exe.
""",
})

TEXTS["zh_sim"].update({
    "browser_binary_path": "浏览器程序路径",
    "browse_binary": "浏览",
    "select_browser_binary": "选择 Chrome / Edge 浏览器程序",
    "browser_startup_hint": "Selenium 浏览器未能启动。这是本机浏览器/驱动配置问题，不是 Google 网络访问问题。",
    "parameter_guide_text": TEXTS["zh_sim"]["parameter_guide_text"] + """

14. 浏览器程序路径

控制什么
- 这个路径指向真正的浏览器程序，例如 chrome.exe 或 msedge.exe。
- 它不同于“浏览器驱动路径”。驱动路径指向 chromedriver.exe / msedgedriver.exe；浏览器程序路径指向 Chrome 或 Edge 本身。
- 如果 ChromeDriver 报错 "cannot find Chrome binary"，就需要手动填写这个路径。

Windows 下常见 Chrome 路径
- C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe
- C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe
- C:\\Users\\<你的用户名>\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe
- C:\\Program Files\\Google\\Chrome Dev\\Application\\chrome.exe
- C:\\Users\\<你的用户名>\\AppData\\Local\\Google\\Chrome SxS\\Application\\chrome.exe

典型配对
- Selenium Chrome 后端 + chromedriver.exe + chrome.exe。
- Selenium Edge 后端 + msedgedriver.exe + msedge.exe。
""",
})

TEXTS["zh_tra"].update({
    "browser_binary_path": "瀏覽器程式路徑",
    "browse_binary": "瀏覽",
    "select_browser_binary": "選擇 Chrome / Edge 瀏覽器程式",
    "browser_startup_hint": "Selenium 瀏覽器未能啟動。這是本機瀏覽器/驅動設定問題，不是 Google 網路訪問問題。",
    "parameter_guide_text": TEXTS["zh_tra"]["parameter_guide_text"] + """

14. 瀏覽器程式路徑

控制什麼
- 這個路徑指向真正的瀏覽器程式，例如 chrome.exe 或 msedge.exe。
- 它不同於「瀏覽器驅動路徑」。驅動路徑指向 chromedriver.exe / msedgedriver.exe；瀏覽器程式路徑指向 Chrome 或 Edge 本身。
- 如果 ChromeDriver 報錯 "cannot find Chrome binary"，就需要手動填寫這個路徑。

Windows 下常見 Chrome 路徑
- C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe
- C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe
- C:\\Users\\<你的使用者名稱>\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe
- C:\\Program Files\\Google\\Chrome Dev\\Application\\chrome.exe
- C:\\Users\\<你的使用者名稱>\\AppData\\Local\\Google\\Chrome SxS\\Application\\chrome.exe

典型配對
- Selenium Chrome 後端 + chromedriver.exe + chrome.exe。
- Selenium Edge 後端 + msedgedriver.exe + msedge.exe。
""",
})

# v0.17 UI interaction and settings strings
TEXTS["en"].update({
    "menu_tools": "Tools",
    "menu_settings": "Settings",
    "open_link": "Open link",
    "delete_selected": "Delete",
    "sort_by_time": "Sort by time",
    "sort_by_title": "Sort by title",
    "sort_by_source": "Sort by source",
    "deleted_selected": "Deleted {n} selected record(s).",
    "settings_title": "WebLens Settings",
    "user_agent_label": "Browser User-Agent",
    "user_agent_hint": "This User-Agent is used by both Requests HTTP mode and Selenium browser mode. Change it only when Google returns different pages to automated clients or when you need to match a specific browser profile.",
    "settings_saved": "Settings saved.",
    "reset_default": "Reset default",
    "apply": "Apply",
    "ok": "OK",
    "close": "Close",
    "about": """BFSU WebLens

Author
- Liu Dingjia, Beijing Foreign Studies University.

Series
- BFSU LexiScope: an intelligent toolkit for corpus-oriented data collection, processing and analysis.
- WebLens is the web-search and news-search collection component in this series, parallel in style and positioning to AlignLens and ProofLens.

Purpose
- Low-frequency, auditable and reproducible discovery of Google Search / Google News result records.
- Suitable for corpus construction, web-news sampling, source URL discovery and documented search-result collection.

Current status
- Google Search / Google News collection has been implemented.
- Baidu and Bing tabs are reserved for later integration.
- Selenium Chrome / Edge backends are provided for pages that cannot be collected reliably through plain HTTP requests.

GPT role
- GPT assisted with prototype drafting, GUI layout, code refactoring, documentation wording and debugging suggestions.
- The software concept, research workflow, corpus-building requirements, naming, parameter strategy and final design decisions are authored and directed by Liu Dingjia.

Design style
- Tkinter desktop interface.
- Blue-gray visual language aligned with the BFSU LexiScope family.
- UTF-8 output, explicit logs, visible parameters and user-controlled export.
""",
})

TEXTS["zh_sim"].update({
    "menu_tools": "工具",
    "menu_settings": "设置",
    "open_link": "打开链接",
    "delete_selected": "删除",
    "sort_by_time": "按时间排序",
    "sort_by_title": "按标题排序",
    "sort_by_source": "按来源排序",
    "deleted_selected": "已删除 {n} 条选中记录。",
    "settings_title": "WebLens 设置",
    "user_agent_label": "浏览器 User-Agent",
    "user_agent_hint": "该 User-Agent 会同时用于 Requests HTTP 模式和 Selenium 浏览器模式。只有在 Google 对自动客户端返回不同页面，或需要模拟特定浏览器配置时，才建议修改。",
    "settings_saved": "设置已保存。",
    "reset_default": "恢复默认",
    "apply": "应用",
    "ok": "确定",
    "close": "关闭",
    "about": """BFSU WebLens

作者
- 刘鼎甲，北京外国语大学。

所属系列
- BFSU LexiScope：面向语料库研究的数据采集、数据处理与数据分析智能工具箱。
- WebLens 是该系列中的网络检索与新闻检索采集组件，在界面风格和功能定位上与 AlignLens、ProofLens 保持一致。

软件用途
- 面向语料库建设、网络新闻抽样、来源 URL 发现与搜索结果留痕。
- 强调低频、可审计、可复现的搜索结果采集，而不是高并发爬取。

当前状态
- 已实现 Google Search / Google News 结果采集。
- 百度和 Bing 选项卡作为后续扩展入口保留。
- 对普通 HTTP 请求无法稳定获取的页面，提供 Selenium Chrome / Edge 浏览器后端。

GPT 的角色
- GPT 参与了软件原型草拟、界面布局、代码重构、文档表述和调试建议。
- 软件概念、研究流程、语料库建设需求、命名、参数策略和最终设计决策均由刘鼎甲提出、设计并主导。

设计风格
- Tkinter 桌面界面。
- 延续 BFSU LexiScope 系列蓝灰色视觉风格。
- UTF-8 输出，日志清晰，参数可见，导出可控。
""",
})

TEXTS["zh_tra"].update({
    "menu_tools": "工具",
    "menu_settings": "設定",
    "open_link": "開啟連結",
    "delete_selected": "刪除",
    "sort_by_time": "按時間排序",
    "sort_by_title": "按標題排序",
    "sort_by_source": "按來源排序",
    "deleted_selected": "已刪除 {n} 條選中記錄。",
    "settings_title": "WebLens 設定",
    "user_agent_label": "瀏覽器 User-Agent",
    "user_agent_hint": "該 User-Agent 會同時用於 Requests HTTP 模式和 Selenium 瀏覽器模式。只有在 Google 對自動客戶端返回不同頁面，或需要模擬特定瀏覽器配置時，才建議修改。",
    "settings_saved": "設定已儲存。",
    "reset_default": "恢復預設",
    "apply": "套用",
    "ok": "確定",
    "close": "關閉",
    "about": """BFSU WebLens

作者
- 劉鼎甲，北京外國語大學。

所屬系列
- BFSU LexiScope：面向語料庫研究的資料採集、資料處理與資料分析智能工具箱。
- WebLens 是該系列中的網路檢索與新聞檢索採集組件，在介面風格和功能定位上與 AlignLens、ProofLens 保持一致。

軟體用途
- 面向語料庫建設、網路新聞抽樣、來源 URL 發現與搜尋結果留痕。
- 強調低頻、可審計、可複現的搜尋結果採集，而不是高併發爬取。

當前狀態
- 已實現 Google Search / Google News 結果採集。
- 百度和 Bing 選項卡作為後續擴展入口保留。
- 對普通 HTTP 請求無法穩定獲取的頁面，提供 Selenium Chrome / Edge 瀏覽器後端。

GPT 的角色
- GPT 參與了軟體原型草擬、介面佈局、程式碼重構、文檔表述和除錯建議。
- 軟體概念、研究流程、語料庫建設需求、命名、參數策略和最終設計決策均由劉鼎甲提出、設計並主導。

設計風格
- Tkinter 桌面介面。
- 延續 BFSU LexiScope 系列藍灰色視覺風格。
- UTF-8 輸出，日誌清晰，參數可見，匯出可控。
""",
})

# v0.18 sampling and result-preview edit strings
TEXTS["en"].update({
    "sample_scheme": "Sampling",
    "sample_count": "N",
    "sample_button": "Sample",
    "sample_simple": "Simple random",
    "sample_systematic": "Systematic",
    "sample_by_source": "By source",
    "sample_current": "Sample current preview",
    "edit_preview": "Edit",
    "undo": "Undo",
    "redo": "Redo",
    "reset_preview": "Reset to crawled results",
    "invalid_sample_count": "Sampling count must be a positive integer.",
    "sampled_done": "Sampled {n} record(s) in the current preview.",
    "sampled_by_source_done": "Sampled {n} record(s) across {sources} source group(s).",
    "nothing_to_undo": "Nothing to undo.",
    "nothing_to_redo": "Nothing to redo.",
    "undo_done": "Undo completed.",
    "redo_done": "Redo completed.",
    "reset_done": "Restored {n} originally crawled record(s).",
    "no_original_records": "No original crawled results are available for reset.",
    "unknown_source": "Unknown source",
})

TEXTS["zh_sim"].update({
    "sample_scheme": "采样",
    "sample_count": "数量",
    "sample_button": "采样",
    "sample_simple": "简单随机",
    "sample_systematic": "系统抽样",
    "sample_by_source": "按来源分层",
    "sample_current": "对当前预览采样",
    "edit_preview": "编辑",
    "undo": "撤销",
    "redo": "重做",
    "reset_preview": "重置为爬取结果",
    "invalid_sample_count": "采样数量必须是正整数。",
    "sampled_done": "已在当前预览中采样 {n} 条记录。",
    "sampled_by_source_done": "已按 {sources} 个来源分层采样，共保留 {n} 条记录。",
    "nothing_to_undo": "没有可撤销的操作。",
    "nothing_to_redo": "没有可重做的操作。",
    "undo_done": "已撤销。",
    "redo_done": "已重做。",
    "reset_done": "已恢复 {n} 条原始爬取记录。",
    "no_original_records": "没有可用于重置的原始爬取结果。",
    "unknown_source": "未知来源",
})

TEXTS["zh_tra"].update({
    "sample_scheme": "採樣",
    "sample_count": "數量",
    "sample_button": "採樣",
    "sample_simple": "簡單隨機",
    "sample_systematic": "系統抽樣",
    "sample_by_source": "按來源分層",
    "sample_current": "對當前預覽採樣",
    "edit_preview": "編輯",
    "undo": "撤銷",
    "redo": "重做",
    "reset_preview": "重置為爬取結果",
    "invalid_sample_count": "採樣數量必須是正整數。",
    "sampled_done": "已在當前預覽中採樣 {n} 條記錄。",
    "sampled_by_source_done": "已按 {sources} 個來源分層採樣，共保留 {n} 條記錄。",
    "nothing_to_undo": "沒有可撤銷的操作。",
    "nothing_to_redo": "沒有可重做的操作。",
    "undo_done": "已撤銷。",
    "redo_done": "已重做。",
    "reset_done": "已恢復 {n} 條原始爬取記錄。",
    "no_original_records": "沒有可用於重置的原始爬取結果。",
    "unknown_source": "未知來源",
})

# v0.19 safer crawling defaults and persistent settings strings
TEXTS["en"].update({
    "settings_saved_hint": "WebLens now saves the main GUI settings locally, including query options, date slicing, delays, output format/path, browser backend paths, sampling settings, and User-Agent.",
    "settings_file_hint": "Settings file: {path}",
    "reset_default": "Reset User-Agent",
    "reset_all_defaults": "Reset all defaults",
    "defaults_restored": "All settings have been reset to default values.",
})

TEXTS["zh_sim"].update({
    "settings_saved_hint": "WebLens 现在会把主要界面设置保存到本地，包括检索选项、日期切片、等待时间、输出格式/路径、浏览器后端路径、采样设置和 User-Agent。",
    "settings_file_hint": "设置文件：{path}",
    "reset_default": "重置 User-Agent",
    "reset_all_defaults": "重置全部默认设置",
    "defaults_restored": "已恢复全部默认设置。",
})

TEXTS["zh_tra"].update({
    "settings_saved_hint": "WebLens 現在會把主要介面設定儲存到本機，包括檢索選項、日期切片、等待時間、輸出格式/路徑、瀏覽器後端路徑、採樣設定和 User-Agent。",
    "settings_file_hint": "設定檔：{path}",
    "reset_default": "重置 User-Agent",
    "reset_all_defaults": "重置全部預設設定",
    "defaults_restored": "已恢復全部預設設定。",
})


# v0.20 compact Result Preview toolbar labels
TEXTS["en"].update({
    "preview_open_short": "Open",
    "preview_delete_short": "Delete",
    "preview_sort_label": "Sort:",
    "preview_sort_time_short": "Time",
    "preview_sort_title_short": "Title",
    "preview_sort_source_short": "Source",
    "preview_sample_label": "Sample:",
    "preview_sample_short": "Run",
    "preview_edit_short": "Edit",
})

TEXTS["zh_sim"].update({
    "preview_open_short": "打开",
    "preview_delete_short": "删除",
    "preview_sort_label": "排序：",
    "preview_sort_time_short": "时间",
    "preview_sort_title_short": "标题",
    "preview_sort_source_short": "来源",
    "preview_sample_label": "采样：",
    "preview_sample_short": "执行",
    "preview_edit_short": "编辑",
})

TEXTS["zh_tra"].update({
    "preview_open_short": "開啟",
    "preview_delete_short": "刪除",
    "preview_sort_label": "排序：",
    "preview_sort_time_short": "時間",
    "preview_sort_title_short": "標題",
    "preview_sort_source_short": "來源",
    "preview_sample_label": "採樣：",
    "preview_sample_short": "執行",
    "preview_edit_short": "編輯",
})

# v0.21 content download/cache workflow strings
TEXTS["en"].update({
    "menu_import_links": "Import links/results",
    "menu_download_selected": "Download selected content",
    "content_folder": "Content folder",
    "content_threads": "Content threads",
    "content_cleaning_scheme": "Cleaning scheme",
    "content_selenium_fallback": "Use Selenium fallback when requests cannot download/extract content",
    "select_content_folder": "Select content download folder",
    "select_content_folder_first": "Please select a content download folder first.",
    "preview_download_short": "Download",
    "preview_download_selected_short": "Download selected",
    "preview_download_all_short": "Download all",
    "preview_import_short": "Import links",
    "preview_download_settings_short": "Download settings",
    "download_settings_title": "Content download settings",
    "cleaning_scheme_help": "Choose a content extraction/cleaning scheme before downloading.\n\nAuto by source/domain: chooses a scheme from the URL/source.\nNews: newspaper3k first: uses newspaper3k when available, then falls back to BeautifulSoup.\nNews article: article/main: extracts article/main/body text and applies news-oriented boilerplate removal.\nGeneral webpage: conservative extraction for normal web pages.\nLight archive / academic: keeps more page text and removes less boilerplate.\nStrict corpus clean: stronger boilerplate and short-line filtering; use after checking results.",
    "download_selected_content": "Download selected content",
    "download_all_content": "Download all content",
    "select_rows_to_download": "Please select one or more rows in Result Preview first.",
    "content_download_running": "A content download task is already running.",
    "content_download_started": "Downloading content for {n} row(s) with {workers} worker thread(s). Same-domain URLs are serialized.",
    "content_progress": "Content download: {done}/{total}",
    "content_download_finished": "Content download finished: {done}/{total} processed.",
    "content_folder_hint": "Content files saved under: {path}. Metadata workbook: content_metadata.xlsx",
    "content_status_queued": "Queued",
    "content_status_downloaded": "Downloaded",
    "content_status_failed": "Failed",
    "content_download_ok": "[CONTENT OK] {title} | words={words} | quality={score}",
    "content_download_failed": "[CONTENT FAILED] {url} | {error}",
    "select_import_file": "Import WebLens export or URL file",
    "no_imported_links": "No links were found in the selected file.",
    "import_done": "Imported {n} new link(s) into Result Preview.",
    "preview_count": "Total: {n} | Selected: {selected}",
    "checkpoint_saved": "Checkpoint saved {n} record(s) to {path}",
})

TEXTS["zh_sim"].update({
    "menu_import_links": "导入链接/结果",
    "menu_download_selected": "下载选中内容",
    "content_folder": "内容下载文件夹",
    "content_threads": "内容下载线程数",
    "content_cleaning_scheme": "文本清洁方案",
    "content_selenium_fallback": "requests 无法下载/抽取时使用 Selenium 兜底",
    "select_content_folder": "选择内容下载文件夹",
    "select_content_folder_first": "请先选择内容下载文件夹。",
    "preview_download_short": "下载内容",
    "preview_download_selected_short": "下载选中",
    "preview_download_all_short": "下载全部",
    "preview_import_short": "导入链接",
    "preview_download_settings_short": "下载设置",
    "download_settings_title": "内容下载设置",
    "cleaning_scheme_help": "下载前请选择正文抽取/文本清洁方案。\n\n自动按来源/域名选择：根据 URL 或来源自动选择策略。\n新闻：优先 newspaper3k：优先调用 newspaper3k，失败后回退到 BeautifulSoup。\n新闻正文：article/main：优先抽取 article/main/body 中的正文，并清理新闻模板噪音。\n通用网页：适合普通网页，清理较保守。\n轻度清洁：归档/学术页：尽量保留页面文本，只做轻度降噪。\n严格语料清洁：加强模板、短噪音行过滤；建议先抽样检查后使用。",
    "download_selected_content": "下载选中内容",
    "download_all_content": "下载全部内容",
    "select_rows_to_download": "请先在结果预览中选择一行或多行。",
    "content_download_running": "内容下载任务正在运行。",
    "content_download_started": "开始下载 {n} 条内容，线程数 {workers}；同一域名会自动串行执行。",
    "content_progress": "内容下载：{done}/{total}",
    "content_download_finished": "内容下载完成：已处理 {done}/{total}。",
    "content_folder_hint": "内容文件保存位置：{path}。元信息汇总表：content_metadata.xlsx",
    "content_status_queued": "等待下载",
    "content_status_downloaded": "已下载",
    "content_status_failed": "失败",
    "content_download_ok": "[内容成功] {title} | 词数={words} | 质量={score}",
    "content_download_failed": "[内容失败] {url} | {error}",
    "select_import_file": "导入 WebLens 导出文件或链接文件",
    "no_imported_links": "所选文件中未发现链接。",
    "import_done": "已向结果预览导入 {n} 条新链接。",
    "preview_count": "总数：{n} | 已选：{selected}",
    "checkpoint_saved": "已保存阶段状态：{n} 条记录 -> {path}",
})

TEXTS["zh_tra"].update({
    "menu_import_links": "匯入連結/結果",
    "menu_download_selected": "下載選中內容",
    "content_folder": "內容下載資料夾",
    "content_threads": "內容下載執行緒數",
    "content_cleaning_scheme": "文本清潔方案",
    "content_selenium_fallback": "requests 無法下載/抽取時使用 Selenium 備援",
    "select_content_folder": "選擇內容下載資料夾",
    "select_content_folder_first": "請先選擇內容下載資料夾。",
    "preview_download_short": "下載內容",
    "preview_download_selected_short": "下載選中",
    "preview_download_all_short": "下載全部",
    "preview_import_short": "匯入連結",
    "preview_download_settings_short": "下載設定",
    "download_settings_title": "內容下載設定",
    "cleaning_scheme_help": "下載前請選擇正文抽取/文本清潔方案。\n\n自動按來源/網域選擇：根據 URL 或來源自動選擇策略。\n新聞：優先 newspaper3k：優先調用 newspaper3k，失敗後回退到 BeautifulSoup。\n新聞正文：article/main：優先抽取 article/main/body 中的正文，並清理新聞模板噪音。\n通用網頁：適合普通網頁，清理較保守。\n輕度清潔：歸檔/學術頁：盡量保留頁面文本，只做輕度降噪。\n嚴格語料清潔：加強模板、短噪音行過濾；建議先抽樣檢查後使用。",
    "download_selected_content": "下載選中內容",
    "download_all_content": "下載全部內容",
    "select_rows_to_download": "請先在結果預覽中選擇一行或多行。",
    "content_download_running": "內容下載任務正在執行。",
    "content_download_started": "開始下載 {n} 條內容，執行緒數 {workers}；同一網域會自動串列執行。",
    "content_progress": "內容下載：{done}/{total}",
    "content_download_finished": "內容下載完成：已處理 {done}/{total}。",
    "content_folder_hint": "內容檔案儲存位置：{path}。元資訊彙總表：content_metadata.xlsx",
    "content_status_queued": "等待下載",
    "content_status_downloaded": "已下載",
    "content_status_failed": "失敗",
    "content_download_ok": "[內容成功] {title} | 詞數={words} | 品質={score}",
    "content_download_failed": "[內容失敗] {url} | {error}",
    "select_import_file": "匯入 WebLens 匯出檔或連結檔",
    "no_imported_links": "所選檔案中未發現連結。",
    "import_done": "已向結果預覽匯入 {n} 條新連結。",
    "preview_count": "總數：{n} | 已選：{selected}",
    "checkpoint_saved": "已儲存階段狀態：{n} 條記錄 -> {path}",
})

# v1.1 Baidu module labels and concise guide updates.
TEXTS["en"].update({
    "baidu_tab": "Baidu",
    "reserved_hint": "Baidu collection is implemented in the main Collector panel. Click below to switch to Baidu News - media sites, Requests mode.",
    "baidu_open_collector": "Use Baidu module",
    "baidu_active_hint": "Baidu News - media sites selected. Requests mode is active.",
    "query_settings": "Search Query Settings",
    "limit_settings": "Google Language / Region Restrictions",
    "baidu_sort": "Baidu news sort",
    "invalid_query": "Please enter search terms or a raw query.",
    "network_hint": "The search engine cannot be reached or the request timed out. This may be related to proxy, DNS, firewall, or country/IP access restrictions.",
})
TEXTS["zh_sim"].update({
    "baidu_tab": "百度",
    "reserved_hint": "百度采集已接入主采集面板。点击下方按钮可切换到“百度资讯：媒体网站 + Requests 模式”。",
    "baidu_open_collector": "使用百度模块",
    "baidu_active_hint": "已选择百度资讯：媒体网站，并启用 Requests 模式。",
    "query_settings": "检索设置",
    "limit_settings": "Google 语种与国家/地区限定",
    "baidu_sort": "百度资讯排序",
    "invalid_query": "请输入检索词或原始检索式。",
    "network_hint": "搜索引擎无法访问或请求超时，可能与代理、DNS、防火墙或国家/IP访问限制有关。",
})
TEXTS["zh_tra"].update({
    "baidu_tab": "百度",
    "reserved_hint": "百度採集已接入主採集面板。點擊下方按鈕可切換到「百度資訊：媒體網站 + Requests 模式」。",
    "baidu_open_collector": "使用百度模組",
    "baidu_active_hint": "已選擇百度資訊：媒體網站，並啟用 Requests 模式。",
    "query_settings": "檢索設定",
    "limit_settings": "Google 語種與國家/地區限定",
    "baidu_sort": "百度資訊排序",
    "invalid_query": "請輸入檢索詞或原始檢索式。",
    "network_hint": "搜尋引擎無法訪問或請求逾時，可能與代理、DNS、防火牆或國家/IP訪問限制有關。",
})


# v1.1.2 download and anti-captcha controls.
TEXTS["en"].update({
    "content_fetch_mode": "Content fetch mode",
    "content_delay": "Content page delay ms",
    "content_receive_wait": "Content receive/render wait ms",
    "download_mode_help": "Content fetch mode: Requests only is fastest; Selenium only opens a browser for every content page; mixed mode tries Requests first and falls back to Selenium when the static page cannot be downloaded or extracted. Content page delay is a random per-domain delay before downloading each page. Receive/render wait lets slow pages load more completely before extraction.",
    "selenium_restart_pages": "Browser restart every N pages",
})
TEXTS["zh_sim"].update({
    "content_fetch_mode": "内容下载模式",
    "content_delay": "内容页面下载等待 ms",
    "content_receive_wait": "页面接收/渲染等待 ms",
    "download_mode_help": "内容下载模式：仅 Requests 速度最快；仅 Selenium 会为每个内容页打开浏览器；混合模式先用 Requests，静态页面无法下载或抽取时再用 Selenium。内容页面下载等待是在下载每个页面前按域名串行加入的随机延时；页面接收/渲染等待用于让慢页面加载更完整后再抽取正文。",
    "selenium_restart_pages": "每 N 页重启浏览器",
})
TEXTS["zh_tra"].update({
    "content_fetch_mode": "內容下載模式",
    "content_delay": "內容頁面下載等待 ms",
    "content_receive_wait": "頁面接收/渲染等待 ms",
    "download_mode_help": "內容下載模式：僅 Requests 速度最快；僅 Selenium 會為每個內容頁開啟瀏覽器；混合模式先用 Requests，靜態頁面無法下載或抽取時再用 Selenium。內容頁面下載等待是在下載每個頁面前按網域串列加入的隨機延時；頁面接收/渲染等待用於讓慢頁面載入更完整後再抽取正文。",
    "selenium_restart_pages": "每 N 頁重啟瀏覽器",
})


# v1.2 interface and documentation refresh.
TEXTS["en"].update({
    "google_tab": "Google",
    "baidu_tab": "Baidu",
    "query_settings": "Search Settings",
    "limit_settings": "Google Language / Region Restrictions",
    "about": """BFSU WebLens v1.2

Part of the BFSU LexiScope toolkit.

Purpose: a low-frequency, auditable search-result and web-news collection utility for corpus research. It currently provides two separated panels: Google and Baidu. Bing has been removed because practical access restrictions make stable research crawling difficult.

Core functions: Google Web/News collection, Baidu Web/News/media-site collection, date slicing, site/domain restriction, result preview, sampling/editing, exports, and content downloading.

v1.2 improves multilingual content downloading: raw bytes are preserved, encodings are auto-detected, common mojibake is repaired, newspaper3k is treated as an optional first attempt, and built-in BeautifulSoup/template fallbacks extract clean TXT from Chinese and other non-English pages when newspaper3k fails.

Author: Liu Dingjia, Beijing Foreign Studies University.
AI assistance: ChatGPT helped with software design, code generation, testing suggestions, and documentation drafting. Final use and parameter choices remain under the user's control.

Compliance note: use conservative delays, respect site access restrictions and copyright, and avoid high-frequency automated access.""",
    "user_guide_text": """BFSU WebLens v1.2 — User Guide

1. Choose a panel
   Google and Baidu are separated. Google collection is performed inside the Google tab. Baidu collection is performed inside the Baidu tab. Bing is not included in v1.2.

2. Fill search settings
   Google supports Web and News search, query modes including OR helpers, language restrictions, country/region restrictions, and site/domain filters. Baidu supports Web, News/Information, and News - media sites; Baidu intentionally hides Google-style language/country restrictions and OR helper modes.

3. Configure crawl timing
   Page delay defaults to 30,000–90,000 ms. Stop after no-new pages defaults to 1. Selenium browser restart is configurable; Google defaults to 4 pages and Baidu defaults to 0.

4. Review results
   Results appear in each panel's own Result Preview. Google and Baidu previews, logs, downloads and exports are independent.

5. Download content
   Download selected or all results. Content fetch mode can be Requests only, Selenium only, or Requests-first with Selenium fallback. Content page delay and receive/render wait can be adjusted for slow or JavaScript-heavy pages.

6. Multilingual extraction
   newspaper3k is tried when appropriate, but WebLens does not rely on it. If newspaper3k fails or gives weak text, WebLens falls back to site templates, article/main/content candidates, visible-text extraction, encoding repair, and clean TXT output.

7. Export and audit
   XLSX is recommended. Content downloads save raw HTML, raw bytes when available, raw text, clean text, per-page JSON metadata, a JSONL manifest, and content_metadata.xlsx.""",
})
TEXTS["zh_sim"].update({
    "google_tab": "Google",
    "baidu_tab": "百度",
    "query_settings": "检索设置",
    "limit_settings": "Google 语种与国家/地区限定",
    "about": """BFSU WebLens v1.2

BFSU LexiScope 工具箱组件。

用途：面向语料库研究的低频、可审计搜索结果与网络新闻采集工具。当前提供两个相互分离的面板：Google 和百度。由于 Bing 实际访问限制较多，v1.2 已移除 Bing 预留界面。

核心功能：Google 网页/新闻采集，百度网页/资讯/媒体网站采集，日期切片，站点/域名限定，结果预览，抽样与编辑，导出，以及正文下载。

v1.2 重点增强多语种正文下载：保留原始字节，自动判断编码，修复常见乱码；newspaper3k 仅作为优先尝试，不再作为唯一方案；当 newspaper3k 失败或抽取效果较差时，自动降级为站点模板、article/main/content 候选正文、可见文本抽取和干净 TXT 输出。该逻辑尤其改善了百度返回的中文新闻站点，但也适用于其它语种网页。

作者：刘鼎甲，北京外国语大学。
AI 辅助说明：ChatGPT 参与了软件设计、代码生成、测试建议与文档草拟。具体使用、参数设置与结果判断由用户负责。

合规提示：建议使用保守延时，尊重网站访问限制与版权要求，避免高频自动访问。""",
    "user_guide_text": """BFSU WebLens v1.2 使用说明

1. 选择面板
   Google 与百度已经分离。Google 采集在 Google 面板中完成；百度采集在百度面板中完成。v1.2 不再保留 Bing 预留界面。

2. 填写检索设置
   Google 支持网页和新闻搜索，支持 OR 辅助检索模式、语种限定、国家/地区限定和站点/域名限定。百度支持网页、资讯、资讯-媒体网站；百度界面隐藏 Google 风格的语种/国家限定和 OR 辅助模式。

3. 设置采集节奏
   Page delay 默认 30,000–90,000 ms。连续无新增页数后停止默认 1。Selenium 浏览器重启间隔可调；Google 默认每 4 页，百度默认 0，即不按页自动重启。

4. 查看结果
   两个面板各自拥有独立的结果预览、日志、下载和导出。Google 结果不会混入百度面板，百度结果也不会混入 Google 面板。

5. 下载正文
   可下载选中结果或全部结果。正文下载模式包括仅 Requests、仅 Selenium 浏览器、Requests 优先并用 Selenium 兜底。内容页面下载等待和页面接收/渲染等待可按网络和网页加载情况调整。

6. 多语种抽取
   newspaper3k 可用于部分英文和其它语种新闻页，但不是唯一依赖。若 newspaper3k 不可用或抽取效果弱，WebLens 会自动使用站点模板、正文候选区、可见文本抽取、编码修复和清洁 TXT 输出。

7. 导出与审计
   推荐使用 XLSX。正文下载会保存 raw HTML、可用时保存 raw bytes、raw text、clean text、单页 JSON 元信息、JSONL manifest 和 content_metadata.xlsx。""",
})
TEXTS["zh_tra"].update({
    "google_tab": "Google",
    "baidu_tab": "百度",
    "query_settings": "檢索設定",
    "limit_settings": "Google 語種與國家/地區限定",
    "about": """BFSU WebLens v1.2

BFSU LexiScope 工具箱組件。

用途：面向語料庫研究的低頻、可審計搜尋結果與網路新聞採集工具。當前提供兩個相互分離的面板：Google 和百度。由於 Bing 實際訪問限制較多，v1.2 已移除 Bing 預留介面。

核心功能：Google 網頁/新聞採集，百度網頁/資訊/媒體網站採集，日期切片，站點/網域限定，結果預覽，抽樣與編輯，匯出，以及正文下載。

v1.2 重點增強多語種正文下載：保留原始位元組，自動判斷編碼，修復常見亂碼；newspaper3k 僅作為優先嘗試，不再作為唯一方案；當 newspaper3k 失敗或抽取效果較差時，自動降級為站點模板、article/main/content 候選正文、可見文本抽取和乾淨 TXT 輸出。該邏輯尤其改善了百度返回的中文新聞站點，但也適用於其它語種網頁。

作者：劉鼎甲，北京外國語大學。
AI 輔助說明：ChatGPT 參與了軟體設計、程式碼生成、測試建議與文檔草擬。具體使用、參數設定與結果判斷由使用者負責。

合規提示：建議使用保守延時，尊重網站訪問限制與版權要求，避免高頻自動訪問。""",
    "user_guide_text": """BFSU WebLens v1.2 使用說明

1. 選擇面板
   Google 與百度已經分離。Google 採集在 Google 面板中完成；百度採集在百度面板中完成。v1.2 不再保留 Bing 預留介面。

2. 填寫檢索設定
   Google 支援網頁和新聞搜尋，支援 OR 輔助檢索模式、語種限定、國家/地區限定和站點/網域限定。百度支援網頁、資訊、資訊-媒體網站；百度介面隱藏 Google 風格的語種/國家限定和 OR 輔助模式。

3. 設定採集節奏
   Page delay 預設 30,000–90,000 ms。連續無新增頁數後停止預設 1。Selenium 瀏覽器重啟間隔可調；Google 預設每 4 頁，百度預設 0，即不按頁自動重啟。

4. 查看結果
   兩個面板各自擁有獨立的結果預覽、日誌、下載和匯出。Google 結果不會混入百度面板，百度結果也不會混入 Google 面板。

5. 下載正文
   可下載選中結果或全部結果。正文下載模式包括僅 Requests、僅 Selenium 瀏覽器、Requests 優先並用 Selenium 備援。內容頁面下載等待和頁面接收/渲染等待可按網路和網頁載入情況調整。

6. 多語種抽取
   newspaper3k 可用於部分英文和其它語種新聞頁，但不是唯一依賴。若 newspaper3k 不可用或抽取效果弱，WebLens 會自動使用站點模板、正文候選區、可見文本抽取、編碼修復和清潔 TXT 輸出。

7. 匯出與審計
   推薦使用 XLSX。正文下載會保存 raw HTML、可用時保存 raw bytes、raw text、clean text、單頁 JSON 元資訊、JSONL manifest 和 content_metadata.xlsx。""",
})


# v1.2 concise help-text cleanup.
TEXTS["en"].update({
    "query_help_text": """Search-term modes are engine-specific.

Google panel:
- Single term
- Any term, OR
- All terms
- Exact phrase
- Any exact phrase, OR
- Raw Google query

Baidu panel:
- Single term
- All terms
- Exact phrase
- Raw search query

Baidu does not show the Google-style Any/OR helper modes. Use Raw search query when you need full manual control, for example: site:people.com.cn rare earth.
""",
    "site_help_text": """Site/domain filters restrict results by the search engine's site: operator and by WebLens local URL filtering.

Examples:
cnn.com
people.com.cn
.gov
.edu.cn

Google: WebLens adds site:{domain} to the Google query and can combine it with language/country restrictions.
Baidu: WebLens inserts site:{domain} directly into the Baidu wd query expression. Multiple site filters are searched separately and then merged/deduplicated.
""",
    "parameter_guide_text": """BFSU WebLens v1.2 — Parameter Guide

Panels: Google and Baidu are separated. Bing is not included.

Page delay: random wait between search result pages. Default 30,000–90,000 ms.
Stop after no-new pages: stop the current date slice after N consecutive pages add no new links. Default 1.
Browser restart every N pages: Selenium-only search-session reset interval. Google default 4; Baidu default 0.
Content fetch mode: Requests only, Selenium only, or Requests first + Selenium fallback.
Content receive/render wait: wait after receiving or rendering a content page before extraction.
Cleaning scheme: Auto uses newspaper3k first where appropriate, then falls back to multilingual/site-template/BeautifulSoup extraction and clean TXT output.
""",
})
TEXTS["zh_sim"].update({
    "query_help_text": """检索词模式按搜索引擎区分。

Google 面板：
- 单个检索词
- 多个检索词：OR
- 多个检索词：全部包含
- 严格连续短语
- 多个严格短语：OR
- 原始 Google 查询式

百度面板：
- 单个检索词
- 多个检索词：全部包含
- 严格连续短语
- 原始检索式

百度界面不显示 Google 风格的 Any/OR 辅助模式。如需复杂表达式，请使用原始检索式，例如：site:people.com.cn 稀土。
""",
    "site_help_text": """站点/域名限定会使用搜索引擎的 site: 操作符，并在 WebLens 本地进行 URL 过滤。

示例：
cnn.com
people.com.cn
.gov
.edu.cn

Google：WebLens 会把 site:{domain} 加入 Google 查询式，并可同时使用语种/国家地区限定。
百度：WebLens 会把 site:{domain} 直接写入百度 wd 检索式。多个站点会分别检索，再合并去重。
""",
    "parameter_guide_text": """BFSU WebLens v1.2 参数说明

面板：Google 与百度完全分离。v1.2 不包含 Bing。

Page delay：搜索结果页之间的随机等待，默认 30,000–90,000 ms。
连续无新增页数后停止：当前日期切片连续 N 页没有新增链接时停止，默认 1。
每 N 页重启浏览器：Selenium 搜索会话的重启间隔。Google 默认 4；百度默认 0。
内容下载模式：仅 Requests、仅 Selenium、Requests 优先 + Selenium 兜底。
页面接收/渲染等待：正文页下载或渲染后等待一段时间再抽取。
文本清洁方案：自动模式会优先尝试 newspaper3k，失败或效果弱时降级为多语种/站点模板/BeautifulSoup 抽取，并输出 clean TXT。
""",
})
TEXTS["zh_tra"].update({
    "query_help_text": """檢索詞模式按搜尋引擎區分。

Google 面板：
- 單個檢索詞
- 多個檢索詞：OR
- 多個檢索詞：全部包含
- 嚴格連續短語
- 多個嚴格短語：OR
- 原始 Google 查詢式

百度面板：
- 單個檢索詞
- 多個檢索詞：全部包含
- 嚴格連續短語
- 原始檢索式

百度介面不顯示 Google 風格的 Any/OR 輔助模式。如需複雜表達式，請使用原始檢索式，例如：site:people.com.cn 稀土。
""",
    "site_help_text": """站點/網域限定會使用搜尋引擎的 site: 操作符，並在 WebLens 本地進行 URL 過濾。

示例：
cnn.com
people.com.cn
.gov
.edu.cn

Google：WebLens 會把 site:{domain} 加入 Google 查詢式，並可同時使用語種/國家地區限定。
百度：WebLens 會把 site:{domain} 直接寫入百度 wd 檢索式。多個站點會分別檢索，再合併去重。
""",
    "parameter_guide_text": """BFSU WebLens v1.2 參數說明

面板：Google 與百度完全分離。v1.2 不包含 Bing。

Page delay：搜尋結果頁之間的隨機等待，預設 30,000–90,000 ms。
連續無新增頁數後停止：當前日期切片連續 N 頁沒有新增連結時停止，預設 1。
每 N 頁重啟瀏覽器：Selenium 搜尋會話的重啟間隔。Google 預設 4；百度預設 0。
內容下載模式：僅 Requests、僅 Selenium、Requests 優先 + Selenium 備援。
頁面接收/渲染等待：正文頁下載或渲染後等待一段時間再抽取。
文本清潔方案：自動模式會優先嘗試 newspaper3k，失敗或效果弱時降級為多語種/站點模板/BeautifulSoup 抽取，並輸出 clean TXT。
""",
})

# v1.2 detailed help/default refresh.
TEXTS["en"].update({
    "day_step": "Day step (0 = no slicing)",
    "max_pages_hint": "Maximum result pages visited inside each date slice. Baidu default is 100. Day step 0 means the whole selected date range is one slice.",
    "output_hint": "XLSX is recommended for corpus-research audit trails. Export fields include engine, vertical, query, slice, page, rank, title, source, displayed time, URL, snippet, and Baidu/Google parameters where applicable.",
    "about": """BFSU WebLens v1.2

BFSU WebLens is a BFSU LexiScope component for low-frequency, auditable web-search and web-news collection in corpus research. It is designed for researchers who need transparent query construction, visible result review, conservative delays, reproducible metadata, and downloadable source material for later corpus cleaning.

Implemented search panels
- Google: Web search and News vertical search. It supports Google-specific language restriction (lr), country/region restriction (cr), date slicing, site/domain restriction, query-helper modes, result preview, sampling, editing, export, and content download.
- Baidu: Web search, News/Information search, and News - media sites. The Baidu panel intentionally omits Google-style language/country restrictions and OR helper modes because Baidu is most suitable for Chinese web/news discovery and uses different URL/query mechanisms.
- Bing: removed in v1.2 because practical access restrictions make stable low-frequency research crawling difficult.

Content downloading and multilingual extraction
WebLens tries to preserve evidence before cleaning. For downloaded content it saves decoded HTML and, when available, raw response bytes. It detects encodings, repairs common mojibake, tries newspaper3k as an optional first extractor, and then falls back to built-in site templates, article/main/content candidate extraction, visible-text extraction, and clean TXT generation. This improves Chinese news pages returned by Baidu and also helps non-English pages where newspaper3k is unavailable, weak, or over-fitted to English news conventions.

Author and acknowledgements
Author: Liu Dingjia, Beijing Foreign Studies University.
AI assistance: ChatGPT assisted with requirements analysis, software design, code generation, testing strategy, and documentation drafting. Final usage, settings, review of collected material, and interpretation of results remain the user's responsibility.

Disclaimer
This software is a research utility, not an official client for Google, Baidu, or any third-party website. Search result pages and news pages may change without notice. Collection completeness, ranking stability, metadata accuracy, encoding repair, and body-text extraction are not guaranteed. Users should respect robots.txt where applicable, website terms of service, copyright and database rights, privacy rules, institutional ethics requirements, and local laws. Use conservative delays and avoid high-frequency or disruptive automated access. The author and AI assistant do not assume responsibility for misuse, data loss, access blocking, copyright infringement, or decisions made from collected data.""",
    "user_guide_text": """BFSU WebLens v1.2 — Detailed User Guide

1. Choose the correct panel
Google and Baidu are separate workflows. Use the Google panel only for Google search. Use the Baidu panel only for Baidu search. Each panel has its own query settings, crawl settings, preview table, log, export, sampling/editing actions, and content-download actions.

2. Build the query
Google query modes:
- Single term: sends the first term or phrase as typed.
- Any term, OR: joins terms with OR.
- All terms: joins terms with spaces; Google normally treats this as an AND-like query.
- Exact phrase: wraps one phrase in quotation marks.
- Any exact phrase, OR: quotes each phrase and joins them with OR.
- Raw Google query: sends your own syntax, such as site:cnn.com (\"rare earth\" OR minerals).

Baidu query modes:
- Single term.
- All terms.
- Exact phrase.
- Raw search query.
Baidu does not expose Any/OR helper modes. For manual control use Raw search query, e.g. site:people.com.cn 稀土.

3. Select the search vertical
Google: Web search or News tab.
Baidu: Web search, News/Information, or News - media sites. The media-sites option adds Baidu's media-source filter where available.

4. Set date coverage
Start date and End date define the total collection window. Day step controls whether the window is split into smaller search slices.
- Day step 0: no slicing; the whole selected date range is searched as one slice.
- Day step 1: daily slices.
- Day step 7: weekly slices. Google default remains 7.
- Baidu default is 0 because Baidu date filtering is less predictable and broad one-slice collection is often safer.

5. Control pagination
Max pages per slice is the maximum number of result pages requested for each date slice. Google default is 30. Baidu default is 100. Stop after no-new pages defaults to 1, meaning a slice stops as soon as one full result page adds no new valid links after filtering and deduplication.

6. Choose the fetch backend
Requests is fastest and least visually intrusive. Selenium/Chrome or Selenium/Edge opens real browser pages and is useful when static HTML is incomplete. Browser receive/render wait controls how long WebLens waits after opening a page before extracting HTML.

7. Use conservative delays
Page delay is the wait between search result pages. The default 30,000–90,000 ms is intentionally conservative. Slice delay is the wait between date slices. Error cooldown is used after temporary failures, timeouts, or possible blocking.

8. Review and edit results
Use the Result Preview table to inspect title, source, time, URL and snippet. You can open links, delete rows, reset to original crawl results, undo/redo edits, and run sampling from the preview toolbar.

9. Download full content
Use Download selected content or Download all content. Content fetch mode can be Requests only, Selenium only, or Requests first + Selenium fallback. Content page delay controls the delay before downloading each content URL. Content receive/render wait helps slow or JavaScript-heavy pages finish loading before extraction.

10. Audit the output
Search exports record query, engine, vertical, date slice, page, rank, URL, source and snippets. Content downloads save raw/decoded HTML, raw text, clean text, metadata JSON, JSONL manifest and content_metadata.xlsx when possible. Always review samples before using the corpus analytically.""",
    "parameter_guide_text": """BFSU WebLens v1.2 — Complete Parameter Guide

A. Panel-level parameters
Search engine panel: Google and Baidu are independent. Settings shown in one panel apply to that panel's workflow.
Search vertical: selects the target result type. Google supports Web and News. Baidu supports Web, News/Information, and News - media sites.
Baidu news sort: Focus/relevance sorting uses rtt=1 where applicable. Time sorting uses the observed Baidu time-sort parameter where applicable; because Baidu may change front-end behavior, exported metadata records the actual search URL.

B. Query parameters
Query mode: controls how the text box is converted into a search expression. Google includes OR helper modes; Baidu does not.
Search terms / raw query text: the user-visible input that becomes the query. In raw mode WebLens sends it with minimal modification.
Site/domain filters: one or more domains, suffixes or source restrictions. Google and Baidu both use site: syntax, but Baidu inserts site:{domain} directly into the wd query. Multiple site filters are searched separately and merged/deduplicated.
User-Agent: HTTP identity string sent in Requests mode. Change only when necessary for compatibility.

C. Google-only restrictions
Language restriction (lr): restricts result document language, e.g. lang_en or lang_fr. This is not the same as interface language.
Country/region restriction (cr): restricts Google's country/region result collection. It is hidden in the Baidu panel.
SafeSearch: blank/off/medium/high. It is passed to Google when set.
Disable duplicate filtering: adds filter=0. It may surface similar results but increases duplicates.

D. Date and slicing
Start date: inclusive start of the total collection window.
End date: inclusive end of the total collection window.
Day step (0 = no slicing): number of days per date slice. 0 searches the entire window as one slice. 1 means daily slices. 7 means weekly slices. Google default: 7. Baidu default: 0.
Date slice: a generated sub-range used to reduce search truncation and improve auditability.

E. Search pagination and stopping
Max pages per slice: maximum result pages requested per date slice. Google default: 30. Baidu default: 100.
Results per page: requested number of visible results per search page. Some engines may ignore or cap this value.
Stop after no-new pages: stop the current slice after N consecutive pages add no new valid links. Default: 1 for both Google and Baidu.
Browser restart every N pages: Selenium-only search-session reset interval. 0 disables page-count-based restart. Google default: 4. Baidu default: 0.

F. Search fetching and browser parameters
Fetch backend: Requests, Selenium Chrome, or Selenium Edge. Requests is preferred first; Selenium is useful for JavaScript-rendered pages or when Requests returns incomplete HTML.
Browser driver path: path to chromedriver/msedgedriver when Selenium is used.
Browser binary path: optional path to Chrome/Edge executable.
Browser wait ms: wait after Selenium opens a search result page before parsing.
Browser headless: if enabled, browser runs without a visible window; visible mode is easier for diagnosis.
Timeout seconds: HTTP timeout for Requests.
Post-fetch wait ms: extra wait after receiving a search result page before parsing.
Empty page retry count: number of retries when a result page appears empty.
Empty page retry wait ms: wait before retrying an empty result page.

G. Delay parameters
Page delay min/max ms: random delay between search result pages. Default: 30,000–90,000 ms.
Slice delay min/max ms: random delay between date slices.
Error delay min/max ms: random cooldown after timeout, HTTP errors, or suspected access throttling.

H. Output and preview
Output path: target file for manual or automatic search-result export.
Output format: XLSX, CSV, TXT, DOCX or XML. XLSX is recommended for metadata auditing.
Result Preview: panel-specific result table. Editing actions affect only the active panel.
Sampling scheme: simple random, systematic, or source-stratified sampling for the current preview.
Sample count: number of rows to sample, or number per source for source-stratified sampling.

I. Content downloading
Content download directory: root folder for downloaded pages and extracted text.
Content threads: concurrent content-download workers. Domain-level politeness is still applied where implemented; use low values for fragile sites.
Content fetch mode: Requests only, Selenium only, or Requests first + Selenium fallback.
Content page delay ms: random delay before downloading each content page.
Content receive/render wait ms: wait after receiving or rendering the content page before extraction.
Cleaning scheme: Auto is recommended. WebLens tries newspaper3k when appropriate, then falls back to multilingual/site-template/BeautifulSoup extraction and visible-text cleanup.
Raw bytes / decoded HTML / clean text: downloads preserve evidence where possible before cleaning, so failed extraction can be reprocessed later.

J. Stop behavior
Stop button: requests cancellation of the active search crawl and active content download. The current HTTP request or browser page may need to finish before the worker stops.""",
})

TEXTS["zh_sim"].update({
    "day_step": "日期步长（0=不切片）",
    "max_pages_hint": "每个日期切片内最多访问的搜索结果页数。百度默认 100。日期步长为 0 表示所选日期范围整体作为一个切片。",
    "output_hint": "科研记录建议使用 XLSX。导出字段包括引擎、检索范围、检索式、切片、页码、排名、标题、来源、页面时间、URL、摘要，以及适用的 Google/百度参数。",
    "about": """BFSU WebLens v1.2

BFSU WebLens 是 BFSU LexiScope 工具箱组件，用于语料库研究中的低频、可审计网页检索与网络新闻采集。它面向需要透明检索式、结果预览、保守延时、可复现元数据和可下载原始材料的研究者。

已实现的检索面板
- Google：支持网页检索和新闻垂直检索，支持 Google 专用语种限定 lr、国家/地区限定 cr、日期切片、站点/域名限定、检索辅助模式、结果预览、抽样、编辑、导出和正文下载。
- 百度：支持网页检索、资讯检索、资讯-媒体网站。百度面板故意不提供 Google 风格的语种/国家地区限定和 OR 辅助模式，因为百度更适合中文网页/新闻发现，且使用不同的 URL 与查询机制。
- Bing：v1.2 已移除。原因是 Bing 的实际访问限制较多，不适合作为本工具当前的低频科研采集模块。

正文下载与多语种抽取
WebLens 在清洗前尽量保留证据。正文下载会保存 decoded HTML，并在可用时保存原始响应字节。程序会自动判断编码，修复常见 mojibake 乱码；newspaper3k 只作为可选的优先抽取器；随后会降级到内置站点模板、article/main/content 候选区域、可见文本抽取和 clean TXT 输出。这一逻辑改善了百度返回的中文新闻页，也有助于 newspaper3k 对非英语网页支持不足时的降级处理。

作者与致谢
作者：刘鼎甲，北京外国语大学。
AI 辅助说明：ChatGPT 参与需求分析、软件设计、代码生成、测试策略和文档草拟。具体使用、参数选择、结果复核和学术解释由用户负责。

免责声明
本软件是科研辅助工具，不是 Google、百度或任何第三方网站的官方客户端。搜索结果页和新闻网页结构可能随时变化；采集完整性、排名稳定性、元数据准确性、编码修复和正文抽取质量均不作保证。用户应遵守适用的 robots.txt、网站服务条款、版权与数据库权利、隐私规范、机构伦理要求和所在地法律法规。请使用保守延时，避免高频或干扰性自动访问。作者和 AI 助手不对误用、数据丢失、访问受限、版权争议或基于采集数据作出的决策承担责任。""",
    "user_guide_text": """BFSU WebLens v1.2 详细使用说明

1. 选择正确面板
Google 与百度是两个独立流程。Google 检索在 Google 面板内完成；百度检索在百度面板内完成。两个面板各自拥有检索设置、采集设置、结果预览、日志、导出、抽样/编辑和正文下载操作。

2. 构造检索式
Google 检索模式：
- 单个检索词：按原样发送一个词或短语。
- 多个检索词：OR：用 OR 连接多行词项。
- 多个检索词：全部包含：用空格连接，Google 通常按近似 AND 处理。
- 严格连续短语：给一个短语加英文双引号。
- 多个严格短语：OR：每个短语加双引号后用 OR 连接。
- 原始 Google 查询式：用户完全控制，例如 site:cnn.com (\"rare earth\" OR minerals)。

百度检索模式：
- 单个检索词。
- 多个检索词：全部包含。
- 严格连续短语。
- 原始检索式。
百度不显示 Any/OR 辅助模式。如需复杂表达式，请使用原始检索式，例如 site:people.com.cn 稀土。

3. 选择检索范围
Google：网页检索或新闻标签。
百度：网页检索、资讯检索、资讯-媒体网站。媒体网站选项会在可用时加入百度的媒体来源过滤。

4. 设置日期范围
Start date 和 End date 是总采集窗口。Day step 决定是否把窗口切成多个小切片。
- Day step=0：不切片，整个日期范围作为一个切片。
- Day step=1：逐日切片。
- Day step=7：逐周切片，Google 默认仍为 7。
- 百度默认 Day step=0，因为百度日期参数稳定性不如 Google，较宽的单切片默认值更稳。

5. 控制翻页
Max pages per slice 是每个日期切片最多请求的结果页数。Google 默认 30，百度默认 100。Stop after no-new pages 默认 1，表示某个切片中只要连续 1 页没有新增有效链接，就停止该切片。

6. 选择抓取后端
Requests 速度快、界面干扰少。Selenium Chrome/Edge 会打开真实浏览器，适合静态 HTML 不完整或需要渲染的页面。Browser wait 控制浏览器打开搜索结果页后的等待时间。

7. 使用保守延时
Page delay 是搜索结果页之间的等待。默认 30,000–90,000 ms，故意设置得比较保守。Slice delay 是日期切片之间的等待。Error cooldown 用于请求失败、超时或疑似被限速后的冷却。

8. 查看和编辑结果
Result Preview 可检查标题、来源、时间、URL 和摘要。可以打开链接、删除行、恢复原始结果、撤销/重做编辑，并使用工具栏抽样。

9. 下载正文
可下载选中结果或全部结果。正文下载模式包括仅 Requests、仅 Selenium、Requests 优先并用 Selenium 兜底。Content page delay 控制每个正文 URL 下载前的等待，Content receive/render wait 帮助慢页面或 JS 页面加载后再抽取。

10. 审计输出
搜索结果导出记录检索式、引擎、检索范围、日期切片、页码、排名、URL、来源和摘要。正文下载尽量保存 raw/decoded HTML、raw text、clean text、metadata JSON、JSONL manifest 和 content_metadata.xlsx。正式分析前应抽样复核。""",
    "parameter_guide_text": """BFSU WebLens v1.2 完整参数说明

A. 面板级参数
搜索引擎面板：Google 和百度彼此独立。一个面板中显示的参数只服务于该面板流程。
检索范围：选择结果类型。Google 支持网页和新闻；百度支持网页、资讯、资讯-媒体网站。
百度资讯排序：按焦点/相关排序在可用时使用 rtt=1；按时间排序使用目前观察到的百度时间排序参数。由于百度前端可能变化，导出中会保留实际 search_url。

B. 检索式参数
检索模式：决定文本框内容如何转换成搜索表达式。Google 包含 OR 辅助模式；百度不包含。
检索词 / 原始检索式：用户输入的检索内容。原始模式下 WebLens 尽量少改写。
站点/域名限定：可填写一个或多个域名、后缀或来源限定。Google 和百度都使用 site: 语法；百度会把 site:{domain} 直接写入 wd 检索式。多个站点会分别检索后合并去重。
User-Agent：Requests 模式发送的 HTTP 身份字符串。非必要不建议修改。

C. Google 专用限定
结果语种限定 lr：限定结果文档语言，如 lang_en、lang_fr；不同于界面语言。
国家/地区限定 cr：限定 Google 国家/地区结果集合。百度面板隐藏该项。
安全搜索：可为空，也可设 off/medium/high。
关闭重复过滤：添加 filter=0，可能显示更多相似结果，但重复会增加。

D. 日期与切片
Start date：总采集窗口起始日期，包含当天。
End date：总采集窗口结束日期，包含当天。
Day step（0=不切片）：每个日期切片包含的天数。0 表示整个窗口作为一个切片；1 表示逐日；7 表示逐周。Google 默认 7，百度默认 0。
日期切片：程序生成的子日期范围，用于降低搜索截断并增强可追溯性。

E. 翻页与停止
Max pages per slice：每个日期切片最多请求多少结果页。Google 默认 30，百度默认 100。
Results per page：请求每页可见结果数。搜索引擎可能忽略或限制该值。
Stop after no-new pages：连续 N 页没有新增有效链接时停止当前切片。Google 和百度默认均为 1。
Browser restart every N pages：仅 Selenium 搜索会话使用。0 表示不按页数自动重启。Google 默认 4，百度默认 0。

F. 搜索抓取与浏览器参数
Fetch backend：Requests、Selenium Chrome 或 Selenium Edge。建议先用 Requests；遇到 JS 渲染或静态页面不完整时再用 Selenium。
Browser driver path：Selenium 使用的 chromedriver/msedgedriver 路径。
Browser binary path：Chrome/Edge 浏览器可执行文件路径，可为空。
Browser wait ms：Selenium 打开搜索结果页后等待多久再解析。
Browser headless：无头模式；可见模式更方便诊断验证码、空页和跳转。
Timeout seconds：Requests 请求超时秒数。
Post-fetch wait ms：收到搜索结果页后额外等待再解析。
Empty page retry count：结果页看起来为空时重试次数。
Empty page retry wait ms：空页重试前等待时间。

G. 延时参数
Page delay min/max ms：搜索结果页之间的随机等待，默认 30,000–90,000 ms。
Slice delay min/max ms：日期切片之间的随机等待。
Error delay min/max ms：超时、HTTP 错误或疑似访问受限后的随机冷却时间。

H. 输出与预览
Output path：搜索结果导出文件路径。
Output format：XLSX、CSV、TXT、DOCX 或 XML。科研元数据审计建议 XLSX。
Result Preview：当前面板的结果表。编辑只影响当前面板。
Sampling scheme：简单随机、系统抽样或按来源分层抽样。
Sample count：抽样数量；按来源分层时表示每个来源抽多少条。

I. 正文下载
Content download directory：正文下载根目录。
Content threads：并发下载线程数。脆弱网站建议较低值。
Content fetch mode：仅 Requests、仅 Selenium、Requests 优先 + Selenium 兜底。
Content page delay ms：下载每个正文页前的随机等待。
Content receive/render wait ms：正文页接收或渲染后，抽取前等待时间。
Cleaning scheme：推荐 Auto。程序会优先尝试 newspaper3k，再降级为多语种/站点模板/BeautifulSoup/可见文本清洗。
Raw bytes / decoded HTML / clean text：尽量先保留证据，再清洗输出，方便后续重处理。

J. 停止机制
Stop 按钮：请求停止当前搜索采集和正文下载。正在进行的 HTTP 请求或浏览器页面可能需要完成后才会停止。""",
})

TEXTS["zh_tra"].update({
    "day_step": "日期步長（0=不切片）",
    "max_pages_hint": "每個日期切片內最多訪問的搜尋結果頁數。百度預設 100。日期步長為 0 表示所選日期範圍整體作為一個切片。",
    "output_hint": "科研記錄建議使用 XLSX。匯出欄位包括引擎、檢索範圍、檢索式、切片、頁碼、排名、標題、來源、頁面時間、URL、摘要，以及適用的 Google/百度參數。",
    "about": """BFSU WebLens v1.2

BFSU WebLens 是 BFSU LexiScope 工具箱組件，用於語料庫研究中的低頻、可審計網頁檢索與網路新聞採集。它面向需要透明檢索式、結果預覽、保守延時、可復現元資料和可下載原始材料的研究者。

已實現的檢索面板
- Google：支援網頁檢索和新聞垂直檢索，支援 Google 專用語種限定 lr、國家/地區限定 cr、日期切片、站點/網域限定、檢索輔助模式、結果預覽、抽樣、編輯、匯出和正文下載。
- 百度：支援網頁檢索、資訊檢索、資訊-媒體網站。百度面板故意不提供 Google 風格的語種/國家地區限定和 OR 輔助模式，因為百度更適合中文網頁/新聞發現，且使用不同的 URL 與查詢機制。
- Bing：v1.2 已移除。原因是 Bing 的實際訪問限制較多，不適合作為本工具當前的低頻科研採集模組。

正文下載與多語種抽取
WebLens 在清洗前盡量保留證據。正文下載會保存 decoded HTML，並在可用時保存原始回應位元組。程式會自動判斷編碼，修復常見 mojibake 亂碼；newspaper3k 只作為可選的優先抽取器；隨後會降級到內置站點模板、article/main/content 候選區域、可見文本抽取和 clean TXT 輸出。這一邏輯改善了百度返回的中文新聞頁，也有助於 newspaper3k 對非英語網頁支持不足時的降級處理。

作者與致謝
作者：劉鼎甲，北京外國語大學。
AI 輔助說明：ChatGPT 參與需求分析、軟體設計、程式碼生成、測試策略和文檔草擬。具體使用、參數選擇、結果覆核和學術解釋由使用者負責。

免責聲明
本軟體是科研輔助工具，不是 Google、百度或任何第三方網站的官方客戶端。搜尋結果頁和新聞網頁結構可能隨時變化；採集完整性、排名穩定性、元資料準確性、編碼修復和正文抽取品質均不作保證。使用者應遵守適用的 robots.txt、網站服務條款、版權與資料庫權利、隱私規範、機構倫理要求和所在地法律法規。請使用保守延時，避免高頻或干擾性自動訪問。作者和 AI 助手不對誤用、資料遺失、訪問受限、版權爭議或基於採集資料作出的決策承擔責任。""",
    "user_guide_text": TEXTS["zh_sim"]["user_guide_text"].replace("BFSU WebLens v1.2 详细使用说明", "BFSU WebLens v1.2 詳細使用說明").replace("百度", "百度").replace("检索", "檢索").replace("结果", "結果").replace("网页", "網頁").replace("导出", "匯出"),
    "parameter_guide_text": TEXTS["zh_sim"]["parameter_guide_text"].replace("BFSU WebLens v1.2 完整参数说明", "BFSU WebLens v1.2 完整參數說明").replace("参数", "參數").replace("检索", "檢索").replace("网页", "網頁").replace("结果", "結果").replace("导出", "匯出").replace("默认", "預設"),
})

# v1.2.1 resilient content-download queue, retry, timeout and resume labels.
TEXTS["en"].update({
    "content_retry_count": "Retry failed content N times",
    "content_task_timeout": "Single content task timeout seconds",
    "content_resume_enabled": "Resume content downloads: skip URLs already completed in manifest",
    "content_status_skipped": "Skipped",
    "content_download_skipped": "[CONTENT SKIPPED] {title} | already downloaded in manifest",
})
TEXTS["zh_sim"].update({
    "content_retry_count": "失败内容重试次数",
    "content_task_timeout": "单条内容任务超时秒数",
    "content_resume_enabled": "正文下载断点续传：跳过 manifest 中已完成的 URL",
    "content_status_skipped": "已跳过",
    "content_download_skipped": "[内容跳过] {title} | manifest 中已成功下载",
})
TEXTS["zh_tra"].update({
    "content_retry_count": "失敗內容重試次數",
    "content_task_timeout": "單條內容任務逾時秒數",
    "content_resume_enabled": "正文下載斷點續傳：跳過 manifest 中已完成的 URL",
    "content_status_skipped": "已跳過",
    "content_download_skipped": "[內容跳過] {title} | manifest 中已成功下載",
})

# v1.2.1 documentation refresh: download reliability and checkpoint scope.
TEXTS["en"].update({
    "about": """BFSU WebLens v1.2.1

Part of the BFSU LexiScope toolkit.

Purpose: WebLens is a low-frequency, auditable URL discovery and corpus-oriented web/news collection utility. It provides separate Google and Baidu panels, configurable search-result crawling, result preview/editing, sampling, export, and downstream content downloading.

Download reliability in v1.2.1: content downloading now uses a recoverable task queue. Completed content downloads are written immediately to content_manifest.jsonl, per-page JSON files, clean text files, and content_metadata.xlsx. When content-download resume is enabled, restarting the software and downloading the same imported/crawled links skips URLs already recorded as successful in the manifest. This checkpoint mechanism is deliberately limited to content downloading only; search-result crawling is never auto-resumed, to avoid unintended repeated search-engine pagination.

AI assistance: ChatGPT assisted with software design, code generation, refactoring, documentation drafting, and debugging suggestions. The software concept, research workflow, parameter strategy, corpus-design requirements, naming, and final use decisions are directed by Liu Dingjia.

Disclaimer: This tool is intended for lawful, modest, research-oriented collection and corpus preparation. Users are responsible for respecting website terms, robots/access policies, copyright, privacy, rate limits, institutional rules, and applicable laws. WebLens does not guarantee complete retrieval, exact metadata, or rights clearance. Search engines and source sites may change layout or impose access controls at any time. Use conservative delays, review samples, and verify outputs before academic analysis or publication.""",
    "user_guide_text": TEXTS["en"].get("user_guide_text", "") + """

v1.2.1 content-download recovery workflow
1. Crawl or import links as usual.
2. Click Download selected or Download all.
3. In Download settings, keep Resume content downloads enabled if you want breakpoint continuation.
4. WebLens writes each successful page to the content folder immediately: raw_html, raw_text, clean_text, metadata JSON, content_manifest.jsonl, and content_metadata.xlsx.
5. If the software or computer is force-closed, restart WebLens, load/crawl/import the same links, choose the same content folder, and start content download again. URLs already completed in the manifest are skipped; failed or unfinished URLs are attempted again.
6. This resume feature applies only to content downloading. Google/Baidu search crawling does not resume automatically after a forced close.
""",
    "parameter_guide_text": TEXTS["en"].get("parameter_guide_text", "") + """

Content-download reliability parameters
- Content threads: number of concurrent content-download workers. Same-domain URLs are still serialized to avoid hitting one site too quickly.
- Content fetch mode: Requests only, Selenium only, or Requests first + Selenium fallback.
- Content page delay ms: random delay before fetching each content page. This is separate from search-result page delay.
- Content receive/render wait ms: additional waiting time after receiving a page or rendering it with Selenium.
- Retry failed content N times: how many times WebLens retries a failed content URL before marking it failed.
- Single content task timeout seconds: GUI-level timeout for one content URL. If a task exceeds this value, WebLens records a timeout failure and continues with other URLs.
- Resume content downloads: when enabled, WebLens reads content_manifest.jsonl and skips URLs already successfully downloaded. This implements forced-close breakpoint continuation for content downloads only.
- Domain lock timeout: internal safety timeout for same-domain serialization. It prevents one stuck URL from blocking every later URL from the same domain forever.
""",
})
TEXTS["zh_sim"].update({
    "about": """BFSU WebLens v1.2.1

BFSU LexiScope 工具箱组件。

用途：WebLens 是面向语料库研究的低频、可审计 URL 发现与网页/新闻采集工具。软件将 Google 和百度面板分开，支持搜索结果采集、结果预览与编辑、抽样、导出，以及对已采集/导入链接进行正文下载。

v1.2.1 下载可靠性：正文下载现在使用可恢复任务队列。每一条正文下载成功后，会立即写入 content_manifest.jsonl、单页 JSON、clean text、raw HTML/raw text 和 content_metadata.xlsx。启用“正文下载断点续传”后，即使软件被强制关闭，下一次用同一下载文件夹下载同一批链接时，manifest 中已经成功的 URL 会自动跳过，只继续下载失败或未完成的链接。该断点续传机制只限正文下载，不用于 Google/百度搜索结果爬取，避免搜索引擎把自动续爬识别为不当高频翻页。

AI 辅助说明：ChatGPT 参与了软件设计、代码生成、重构、文档起草和调试建议。软件构想、研究流程、参数策略、语料库建设需求、命名和最终使用决策由刘鼎甲主导。

免责声明：本工具仅用于合法、低频、研究导向的网页发现与语料准备。用户应自行遵守网站服务条款、robots/访问政策、版权、隐私、访问频率、单位管理规定和适用法律。WebLens 不保证检索完整性、元信息完全准确或内容权利可用性。搜索引擎和来源网站可能随时改变页面结构或访问控制。正式研究或发表前，请使用保守延时、抽样复核，并核查输出结果。""",
    "user_guide_text": TEXTS["zh_sim"].get("user_guide_text", "") + """

v1.2.1 正文下载断点续传流程
1. 正常爬取或导入链接。
2. 点击“下载选中”或“下载全部”。
3. 在“下载设置”中保持“正文下载断点续传”启用。
4. WebLens 会把每条成功下载的页面立即写入内容下载文件夹，包括 raw_html、raw_text、clean_text、metadata JSON、content_manifest.jsonl 和 content_metadata.xlsx。
5. 如果软件或电脑被强制关闭，重新打开 WebLens 后，载入/导入同一批链接，选择同一个内容下载文件夹，再次开始正文下载。manifest 中已成功的 URL 会跳过，失败或未完成的 URL 会继续尝试。
6. 该机制只用于正文下载；Google/百度搜索结果爬取不会自动断点续爬。
""",
    "parameter_guide_text": TEXTS["zh_sim"].get("parameter_guide_text", "") + """

正文下载可靠性参数
- 内容下载线程数：同时运行的正文下载 worker 数。同一域名仍会自动串行，避免对同一站点过快访问。
- 内容下载模式：仅 Requests、仅 Selenium、或 Requests 优先 + Selenium 兜底。
- 内容页面下载等待 ms：每个正文页面下载前的随机等待，独立于搜索结果页等待。
- 页面接收/渲染等待 ms：收到页面或 Selenium 渲染后额外等待，让慢页面加载更完整。
- 失败内容重试次数：单条正文链接失败后自动重试的次数。
- 单条内容任务超时秒数：单个正文 URL 的 GUI 层硬超时。超过该值后，WebLens 记录超时失败并继续处理其它链接。
- 正文下载断点续传：启用后读取 content_manifest.jsonl，跳过已经成功下载的 URL。该功能只用于正文下载。
- 同域名锁超时：内部安全参数，防止同一域名中某个卡住的 URL 永久阻塞后续 URL。
""",
})
TEXTS["zh_tra"].update({
    "about": TEXTS["zh_sim"]["about"].replace("组件", "組件").replace("语料库", "語料庫").replace("网页", "網頁").replace("采集", "採集").replace("下载", "下載").replace("强制关闭", "強制關閉").replace("继续", "繼續").replace("链接", "連結").replace("结果", "結果").replace("启用", "啟用").replace("说明", "說明").replace("参与", "參與").replace("软件", "軟體"),
    "user_guide_text": TEXTS["zh_sim"].get("user_guide_text", "").replace("使用说明", "使用說明").replace("正文下载", "正文下載").replace("断点续传", "斷點續傳").replace("爬取", "爬取").replace("导入", "匯入").replace("链接", "連結").replace("下载", "下載").replace("启用", "啟用").replace("文件夹", "資料夾").replace("结果", "結果").replace("继续", "繼續"),
    "parameter_guide_text": TEXTS["zh_sim"].get("parameter_guide_text", "").replace("参数", "參數").replace("正文下载", "正文下載").replace("线程", "執行緒").replace("下载", "下載").replace("网页", "網頁").replace("结果", "結果").replace("断点续传", "斷點續傳").replace("启用", "啟用").replace("链接", "連結").replace("超时", "逾時"),
})

# v1.2.4 release documentation and multi-line site/domain control refresh.
TEXTS["en"].update({
    "site_filters": "Site/domain filters (one per line)",
    "site_help_link": "Site/domain help...",
    "help_site_title": "Site/domain filter guide",
    "site_help_text": """Site/domain filters restrict search results to selected source domains. The field is now multi-line: enter one domain or suffix per line. Semicolons are also accepted for compatibility with older settings.\n\nExamples:\npeople.com.cn\nxinhuanet.com\n.gov.cn\n.edu.cn\nsite:thepaper.cn\n\nHow WebLens uses this field:\n1. Google: WebLens adds site: expressions to the Google query and then applies local URL filtering after parsing.\n2. Baidu: WebLens inserts site:{domain} into the Baidu wd query expression and also applies local URL filtering after parsing.\n3. Multiple domains: values are split by line/semicolon and joined as site constraints in the generated query. Search engines may treat complex site OR syntax differently, so for very strict source control you can run separate tasks for each important domain.\n4. Domain suffixes: entries beginning with a dot, such as .gov or .edu.cn, match hosts ending with that suffix.\n5. Raw query caution: if you already typed site: constraints inside a raw query, leave this field empty to avoid duplicate constraints.\n\nRecommended practice for corpus work: use the multi-line list for auditability, export XLSX, and keep the search_url, query_raw, and site_limit fields for later verification.""",
    "about": """BFSU WebLens v1.2.8\n\nBFSU WebLens is a desktop component of the BFSU LexiScope toolkit. It is designed for corpus researchers who need low-frequency, auditable discovery of search-result URLs and downstream downloading of source web pages.\n\nMain workflow\n- Google and Baidu are completely separated. Each panel has its own search settings, crawl settings, result preview, logs, sampling/editing tools, export buttons, and content-download actions.\n- Bing has been removed from the interface because its current access restrictions make it unsuitable for the intended low-frequency research crawler.\n- Search-result crawling is intentionally not resumed after forced closure. This avoids unintended repeated pagination against search engines.\n- Content downloading supports checkpoint/resume through content_manifest.jsonl. The resume mechanism applies only after URLs have already been collected or imported.\n\nGoogle panel\n- Supports Google Web and Google News.\n- Supports query helper modes, language restriction through lr, country/region restriction through cr, site/domain constraints, date slicing, conservative delays, and optional Selenium browser crawling.\n\nBaidu panel\n- Supports Baidu Web, Baidu News/Information, and Baidu News - media sites.\n- Supports Baidu date filtering through observed gpc/tfflag parameters, Baidu news source filtering through medium=1, Baidu sorting where available, and site/domain constraints through site:{domain} in wd.\n- Baidu does not show Google-specific language/country controls or Google OR-helper modes.\n\nContent downloading\n- Supports Requests only, Selenium browser only, and Requests first + Selenium fallback.\n- Supports retry, per-task timeout, same-domain serialization, Stop control, and manifest-based resume.\n- Multilingual extraction uses layered fallback: encoding detection, mojibake repair, newspaper3k as an optional first attempt, site templates, article/main/content candidate extraction, visible-text extraction, and clean TXT output.\n\nDesktop release\n- build_exe.bat builds the PyInstaller onedir package from a local .venv_build virtual environment. The intended layout is dist/BFSU_WebLens/BFSU_WebLens.exe at the outer level and dependencies/resources in dist/BFSU_WebLens/_internal/. The build script keeps essential components such as assets, tools, Selenium support, newspaper3k, openpyxl, python-docx, charset repair, and multilingual extraction dependencies. Selenium dynamic modules are explicitly collected to avoid missing-module errors such as selenium.webdriver.chrome.webdriver in packaged desktop builds.\n\nAuthorship and AI assistance\n- Author and project lead: Liu Dingjia, Beijing Foreign Studies University.\n- ChatGPT assisted with requirement analysis, prototyping, code generation, refactoring, test planning, documentation drafting, and debugging suggestions. Final software requirements, research workflow, naming, parameter strategy, and usage decisions are directed by Liu Dingjia.\n\nDisclaimer\nThis software is for lawful, modest, research-oriented web discovery and corpus preparation. Users are responsible for respecting website terms of service, robots/access policies, copyright, privacy, institutional rules, rate limits, and applicable laws. WebLens does not guarantee complete retrieval, stable search-engine behavior, accurate metadata, clean extraction from every source, or rights clearance for downloaded content. Search engines and news sites may change layouts or impose access controls at any time. Use conservative delays, review samples, cite sources appropriately, and verify outputs before academic analysis, redistribution, or publication.""",
    "user_guide_text": """BFSU WebLens v1.2.8 — Detailed User Guide\n\n1. Choose an engine panel\nGoogle and Baidu are independent panels. Work inside the panel for the engine you want to use. Results, logs, exports, sampling actions, and content downloads are panel-specific.\n\n2. Enter search terms\nUse Search terms / phrases for ordinary query construction. Google includes OR helper modes. Baidu intentionally removes Google-style Any/OR helper modes because Baidu query behavior is less stable for complex Boolean helper syntax. Raw query mode is available when you need full manual control.\n\n3. Enter site/domain filters\nThe Site/domain field is multi-line. Put one domain or suffix per line, for example:\npeople.com.cn\nxinhuanet.com\n.gov.cn\n.edu.cn\n\nWebLens converts these into site constraints and also filters parsed URLs locally. If the raw query already includes site:, leave this field empty.\n\n4. Configure search vertical\nGoogle: choose Web or News. Baidu: choose Web, News/Information, or News - media sites. Baidu News - media sites uses the observed medium=1 filter.\n\n5. Configure date range and slicing\nStart date and End date define the total collection window. Day step controls slicing. Google default is 7. Baidu default is 0. Day step 0 means no slicing: the full date range is searched as one slice. Smaller slices improve coverage for popular topics but create more requests.\n\n6. Configure pagination and stopping\nMax pages per slice limits pages within each date slice. Baidu default is 100; Google default is 30. Stop after no-new pages defaults to 1; it stops a slice when consecutive pages add no new valid URLs after filtering and deduplication.\n\n7. Configure access method\nRequests is faster and simpler. Selenium Chrome/Edge opens a real browser and is useful when pages require rendering or when requests returns incomplete HTML. Browser restart every N pages controls Selenium search-session recycling. Google defaults to 4; Baidu defaults to 0.\n\n8. Use conservative delays\nPage delay controls the pause between search-result pages. Slice delay controls the pause between date slices. Error cooldown is used after temporary network errors. Defaults are intentionally conservative to reduce blocking and improve reproducibility.\n\n9. Review and edit result preview\nThe right-side result table shows title, link, source, time, snippet, and metadata. You can delete irrelevant rows, use sampling tools, undo/redo preview edits, reset to the original crawl result, and export.\n\n10. Export search results\nXLSX is recommended because it preserves metadata columns. CSV, TXT, DOCX, and XML are available for alternate workflows. Exported fields include engine, vertical, source filter, sort mode, site_limit, date fields, query fields, search_url, title, link, source, domain, time, and snippet.\n\n11. Download content after links are available\nUse Download selected content or Download all content. Content download settings include fetch mode, content threads, content delays, render wait, cleaning scheme, retry count, per-task timeout, and resume.\n\n12. Resume content downloads after forced closure\nChoose the same content download folder and download the same collected/imported links. WebLens reads content_manifest.jsonl and skips URLs already marked successful. This applies only to content download, not search-result crawling.\n\n13. Build desktop release\nRun build_exe.bat in the project directory. The script creates or reuses a local .venv_build virtual environment, installs requirements.txt there, and then creates a PyInstaller onedir package with BFSU_WebLens.exe outside and dependencies/resources inside _internal. Use build_exe.bat --fresh to recreate the build environment after major dependency changes. Zip the whole dist/BFSU_WebLens folder for distribution.""",
    "parameter_guide_text": """BFSU WebLens v1.2.8 — Complete Parameter Guide\n\nPanel\n- Google: Google Web and Google News collection. Includes language and country/region controls.\n- Baidu: Baidu Web, Baidu News/Information, and Baidu News - media sites. Removes Google-only language/country controls and OR helper modes.\n\nQuery mode\n- Single term: sends the first input line as the query.\n- Any term, OR: Google only; joins lines with OR.\n- All terms: joins input terms with spaces; search engines normally treat this as AND-like.\n- Exact phrase: quotes the first input item.\n- Any exact phrase, OR: Google only; quotes each line and joins with OR.\n- Raw query: sends the user expression with minimal rewriting. Use this for advanced syntax.\n\nSearch terms / phrases\n- Main topic words or phrases. One term per line is recommended for clarity.\n- In raw query mode, this becomes the final query expression unless site/domain filters are also added.\n\nSite/domain filters (one per line)\n- Accepts domains, domain suffixes, or site: expressions.\n- Examples: people.com.cn, xinhuanet.com, .gov, .edu.cn, site:thepaper.cn.\n- Google: inserted as site: constraints and then enforced by local URL filtering.\n- Baidu: inserted into wd as site:{domain} and then enforced by local URL filtering.\n- Multiple entries are split by newline or semicolon. If a search engine behaves poorly with complex site combinations, run separate collection tasks per domain.\n\nSearch vertical\n- Google Web: ordinary Google web result pages.\n- Google News: adds tbm=nws.\n- Baidu Web: tn=baidu.\n- Baidu News/Information: tn=news&cl=2.\n- Baidu News - media sites: adds medium=1.\n\nBaidu sort\n- Focus/relevance: observed rtt=1 behavior.\n- Time: observed time-sort behavior where Baidu respects it. WebLens records search_url for audit because Baidu may change behavior.\n\nLanguage restriction lr\n- Google only. Restricts result document language, for example lang_en. It is not the same as interface language.\n\nCountry/region restriction cr\n- Google only. Restricts Google's country/region result collection, not necessarily the publisher's legal location.\n\nStart date / End date\n- Defines the collection window. Google uses date filter parameters. Baidu uses observed gpc/tfflag parameters when date filtering is applied.\n\nDay step\n- Number of days per date slice. 0 means no slicing.\n- Google default: 7. Baidu default: 0.\n- Smaller values reduce truncation for high-volume topics but increase request count.\n\nMax pages per slice\n- Maximum result pages requested within each date slice. Google default: 30. Baidu default: 100.\n\nResults per page\n- Requested result count per page. Engines may cap or ignore it. Google pagination is most stable with start offsets of 0, 10, 20...\n\nStop after no-new pages\n- Stops a slice after N consecutive parsed pages add no new URLs after filtering/deduplication. Default: 1.\n\nFetch backend\n- Requests: faster, no browser rendering.\n- Selenium Chrome / Edge: opens a real browser, useful for rendered pages, diagnostics, and pages where static requests fail.\n\nBrowser driver path\n- Path to chromedriver.exe or msedgedriver.exe. Keep it compatible with the installed browser major version.\n\nBrowser binary path\n- Optional path to chrome.exe or msedge.exe. Useful when the browser is installed in a non-standard location.\n\nBrowser wait ms\n- Wait after Selenium loads a search-result page before parsing.\n\nBrowser headless\n- Runs the browser without a visible window. Visible mode is better when diagnosing captchas, redirects, and rendering problems.\n\nBrowser restart every N pages\n- Selenium search crawling only. 0 disables page-count restart. Google default: 4. Baidu default: 0.\n\nPage delay min/max ms\n- Random delay between search-result pages. Default: 30000–90000 ms.\n\nSlice delay min/max ms\n- Random delay between date slices.\n\nError cooldown min/max ms\n- Random delay after 429, timeout, connection errors, or temporary failures.\n\nTimeout seconds\n- Requests HTTP timeout for search-result pages.\n\nPost-fetch wait ms\n- Extra wait after a page is received before parsing. Useful for unstable or slow result pages.\n\nEmpty page retry count / wait\n- Retries a page when the parser sees no result cards but diagnostics suggest a temporary empty/shell page.\n\nSafeSearch\n- Google parameter: blank/off/medium/high. Keep consistent across comparable runs.\n\nDisable duplicate filtering\n- Google filter=0. May reveal similar results but increases duplicates.\n\nOutput file / format\n- XLSX is recommended. CSV, TXT, DOCX, and XML are provided for different data workflows.\n\nContent folder\n- Destination folder for downloaded pages. Contains raw_html, raw_text, clean_text, metadata JSON, content_manifest.jsonl, and content_metadata.xlsx.\n\nContent threads\n- Concurrent content-download workers. Same-domain URLs are serialized internally to reduce pressure on one website.\n\nContent fetch mode\n- Requests only, Selenium only, or Requests first + Selenium fallback.\n\nContent page delay ms\n- Delay before each content page request. Separate from search page delay.\n\nContent receive/render wait ms\n- Extra wait after receiving or rendering a content page.\n\nCleaning scheme\n- auto: layered multilingual extraction.\n- newspaper/readability/templates/visible text options are used as fallbacks where available.\n\nRetry failed content N times\n- Number of retries before marking a content URL as failed.\n\nSingle content task timeout seconds\n- Hard GUI-level limit for one content URL. Prevents one stuck page from blocking the entire download batch.\n\nResume content downloads\n- Reads content_manifest.jsonl and skips URLs already successfully downloaded. Applies only to content downloads.\n\nDomain lock timeout\n- Safety timeout for same-domain serialization.""",
})

TEXTS["zh_sim"].update({
    "site_filters": "站点/域名限定（每行一个）",
    "site_help_link": "站点/域名填写说明...",
    "help_site_title": "站点/域名限定说明",
    "site_help_text": """站点/域名限定用于把搜索结果限制在指定来源网站或域名后缀内。该输入框现在是多行控件：建议每行填写一个域名或后缀；也兼容旧设置中的英文分号。\n\n示例：\npeople.com.cn\nxinhuanet.com\n.gov.cn\n.edu.cn\nsite:thepaper.cn\n\nWebLens 的处理方式：\n1. Google：把输入转换为 site: 查询约束，并在解析结果后再次进行本地 URL 过滤。\n2. 百度：把输入写入百度 wd 检索式，即 site:{domain}，并在解析结果后再次进行本地 URL 过滤。\n3. 多个域名：程序会按换行/分号拆分，再生成多个 site 约束。不同搜索引擎对复杂 site OR 组合的稳定性不同；如果需要非常严格的来源控制，建议对重要域名单独分批采集。\n4. 域名后缀：以点开头的条目，如 .gov 或 .edu.cn，会匹配主机名以后缀结尾的网址。\n5. 原始查询式提醒：如果 raw query 中已经写了 site:，这里请留空，避免重复限定。\n\n语料库建设建议：使用多行输入便于审计；导出 XLSX 时保留 search_url、query_raw 和 site_limit 字段，便于后续复核。""",
    "about": """BFSU WebLens v1.2.8\n\nBFSU WebLens 是 BFSU LexiScope 工具箱的桌面组件，面向语料库研究者，用于低频、可审计地发现搜索结果 URL，并对已获得的网页/新闻链接进行正文下载和多语种清洗。\n\n主要工作流\n- Google 与百度完全分离。两个面板分别拥有独立的检索设置、采集设置、结果预览、日志、抽样/编辑工具、导出按钮和正文下载操作。\n- Bing 已从界面移除，因为当前实际访问限制较多，不适合作为本工具的低频科研采集模块。\n- 搜索结果爬取不做强制关闭后的自动断点续爬，以避免软件在用户未明确控制的情况下继续翻页访问搜索引擎。\n- 正文下载支持通过 content_manifest.jsonl 进行断点续传。该机制仅适用于已经爬取或导入链接之后的正文下载。\n\nGoogle 面板\n- 支持 Google 网页检索和 Google 新闻检索。\n- 支持检索式辅助模式、lr 语种限定、cr 国家/地区限定、站点/域名限定、日期切片、保守延时和可选 Selenium 浏览器模式。\n\n百度面板\n- 支持百度网页、百度资讯、百度资讯媒体网站。\n- 支持通过 gpc/tfflag 进行百度日期范围过滤；通过 medium=1 过滤媒体资讯；支持可用的百度排序参数；通过 wd 中的 site:{domain} 实现站点限定。\n- 百度面板不显示 Google 专用的语种/国家地区控件，也不显示 Google 风格的 Any/OR 辅助模式。\n\n正文下载\n- 支持仅 Requests、仅 Selenium、Requests 优先 + Selenium 兜底。\n- 支持失败重试、单任务超时、同域名串行、停止控制和 manifest 断点续传。\n- 多语种正文抽取采用分层降级策略：编码检测、乱码修复、newspaper3k 优先尝试、站点模板、article/main/content 候选区抽取、可见文本抽取和 clean TXT 输出。\n\n桌面版发布\n- build_exe.bat 会先创建/使用本地 .venv_build 虚拟环境，再用 PyInstaller 生成 onedir 桌面版。目标结构为 dist/BFSU_WebLens/BFSU_WebLens.exe 位于最外层，依赖和资源放入 dist/BFSU_WebLens/_internal/。脚本会保留 assets、tools、Selenium、newspaper3k、openpyxl、python-docx、编码修复和多语种抽取等关键组件，并显式收集 Selenium 动态模块，避免桌面版运行时报 selenium.webdriver.chrome.webdriver 等模块缺失。\n\n作者与 AI 辅助\n- 作者与项目主导：刘鼎甲，北京外国语大学。\n- ChatGPT 参与了需求分析、原型设计、代码生成、重构、测试思路、文档起草和调试建议。软件需求、研究流程、命名、参数策略和最终使用决策由刘鼎甲主导。\n\n免责声明\n本软件仅用于合法、低频、研究导向的网页发现和语料准备。用户应自行遵守网站服务条款、robots/访问政策、版权、隐私、单位管理规定、访问频率限制和适用法律。WebLens 不保证检索结果完整、搜索引擎行为稳定、元信息完全准确、所有来源均能干净抽取，也不保证下载内容具有再发布或再分发权利。搜索引擎和新闻网站可能随时改变页面结构或访问控制。正式研究、发表或共享数据前，请使用保守延时、抽样核查、标注来源，并复核输出结果。""",
    "user_guide_text": """BFSU WebLens v1.2.8 详细使用说明\n\n1. 选择搜索引擎面板\nGoogle 和百度是相互独立的面板。请在目标搜索引擎的面板内完成检索、采集、结果预览、导出、抽样和正文下载。\n\n2. 填写检索词\n“检索词/短语”用于普通查询构造。Google 保留 OR 辅助模式；百度不显示 Google 风格的 Any/OR 辅助模式，因为百度对复杂布尔辅助语法的稳定性不如 Google。需要完全控制时可使用“原始查询式”。\n\n3. 填写站点/域名限定\n站点/域名限定现在是多行输入框。建议每行填写一个域名或后缀，例如：\npeople.com.cn\nxinhuanet.com\n.gov.cn\n.edu.cn\n\nWebLens 会把这些条目转换为 site 约束，并在解析后再次做本地 URL 过滤。如果原始查询式里已经包含 site:，请把该输入框留空。\n\n4. 选择检索范围\nGoogle 支持网页和新闻。百度支持网页、资讯、资讯媒体网站。百度资讯媒体网站使用观察到的 medium=1 参数。\n\n5. 设置日期与切片\n起始日期和结束日期构成总采集窗口。日期步长控制切片。Google 默认 7；百度默认 0。日期步长 0 表示不切片，把整个日期范围作为一个切片检索。热门主题可用较小步长提高覆盖率，但请求次数也会增加。\n\n6. 设置翻页与停止\n每片最大页数限制每个日期切片内最多请求多少结果页。百度默认 100，Google 默认 30。“连续无新增页停止”默认 1，表示某页经过过滤和去重后没有新增 URL 时，即停止当前切片。\n\n7. 选择访问方式\nRequests 更快、更简单；Selenium Chrome/Edge 会打开真实浏览器，适合需要渲染、requests 返回不完整 HTML 或需要诊断验证码/跳转的情况。“每 N 页重启浏览器”只影响 Selenium 搜索采集。Google 默认 4，百度默认 0。\n\n8. 使用保守延时\n翻页等待控制搜索结果页之间的间隔；切片等待控制日期切片之间的间隔；错误冷却用于超时、429 或临时网络错误后等待。默认值偏保守，目的是降低封禁风险并提高可复现性。\n\n9. 查看与编辑结果预览\n右侧结果表显示标题、链接、来源、时间、摘要和元信息。可以删除无关行、抽样、撤销/重做编辑、重置为原始爬取结果，并导出。\n\n10. 导出搜索结果\n建议使用 XLSX，因为它能完整保留字段。CSV、TXT、DOCX、XML 也可使用。导出字段包括 engine、vertical、source_filter、sort_mode、site_limit、日期字段、query 字段、search_url、标题、链接、来源、域名、时间和摘要等。\n\n11. 对已有链接下载正文\n使用“下载选中”或“下载全部”。正文下载设置包括下载模式、线程数、正文下载延时、页面接收/渲染等待、清洗方案、重试次数、单任务超时和断点续传。\n\n12. 强制关闭后的正文下载续传\n重新打开软件后，载入或导入同一批链接，选择同一个正文下载文件夹，再次开始下载。WebLens 会读取 content_manifest.jsonl，跳过已经成功的 URL。该机制只适用于正文下载，不适用于搜索结果爬取。\n\n13. 打包桌面版\n在项目目录运行 build_exe.bat。脚本会创建或复用本地 .venv_build 虚拟环境，在其中安装 requirements.txt，然后生成 PyInstaller onedir 包。BFSU_WebLens.exe 位于外层，依赖与资源位于 _internal。依赖变化较大时可运行 build_exe.bat --fresh 重建构建环境。发布时压缩整个 dist/BFSU_WebLens 文件夹。""",
    "parameter_guide_text": """BFSU WebLens v1.2.8 完整参数说明\n\n面板\n- Google：用于 Google 网页和 Google 新闻采集，包含语种和国家/地区控件。\n- 百度：用于百度网页、百度资讯、百度资讯媒体网站；不显示 Google 专用语种/国家地区控件和 OR 辅助模式。\n\n检索模式\n- 单个检索词：发送第一行输入。\n- 多个检索词 OR：仅 Google 显示，用 OR 连接多行输入。\n- 全部包含：用空格连接输入项，搜索引擎通常按近似 AND 处理。\n- 严格连续短语：给第一项加英文双引号。\n- 多个严格短语 OR：仅 Google 显示，给每行加引号后用 OR 连接。\n- 原始查询式：尽量按用户输入发送，适合高级语法。\n\n检索词/短语\n- 填写主题词、关键词或短语。建议一行一个输入项，便于审计。\n- 原始查询式模式下，该框内容就是主要查询表达式。\n\n站点/域名限定（每行一个）\n- 接受域名、域名后缀或 site: 表达式。\n- 示例：people.com.cn、xinhuanet.com、.gov、.edu.cn、site:thepaper.cn。\n- Google：写入 site: 查询约束，并在本地过滤 URL。\n- 百度：写入 wd 中的 site:{domain}，并在本地过滤 URL。\n- 多个条目按换行或英文分号拆分。如果搜索引擎对复杂组合不稳定，建议按域名单独分批采集。\n\n检索范围\n- Google 网页：普通 Google 搜索结果。\n- Google 新闻：加入 tbm=nws。\n- 百度网页：tn=baidu。\n- 百度资讯：tn=news&cl=2。\n- 百度资讯媒体网站：加入 medium=1。\n\n百度排序\n- 按焦点/相关：观察到的 rtt=1 行为。\n- 按时间：使用观察到的百度时间排序参数。百度可能改变行为，因此导出中保留 search_url。\n\n结果语种 lr\n- 仅 Google。限定结果文档语言，例如 lang_en。不是界面语言。\n\n国家/地区 cr\n- 仅 Google。限定 Google 的国家/地区结果集合，不等同于出版机构所在地。\n\n起始日期/结束日期\n- 定义采集时间窗口。Google 使用日期过滤参数；百度使用观察到的 gpc/tfflag 参数。\n\n日期步长\n- 每个日期切片包含多少天。0 表示不切片。Google 默认 7，百度默认 0。\n- 值越小，热门主题覆盖越充分，但请求更多。\n\n每片最大页数\n- 每个日期切片内最多请求多少结果页。Google 默认 30，百度默认 100。\n\n每页结果数\n- 请求每页显示多少结果。搜索引擎可能限制或忽略该值。Google 翻页通常按 start=0、10、20 推进。\n\n连续无新增页停止\n- 当前切片中连续 N 页没有新增有效 URL 后停止。默认 1。\n\n访问后端\n- Requests：速度快，不执行 JavaScript。\n- Selenium Chrome/Edge：打开真实浏览器，适合渲染页面和诊断异常。\n\n浏览器驱动路径\n- chromedriver.exe 或 msedgedriver.exe 路径，应与浏览器主版本兼容。\n\n浏览器程序路径\n- chrome.exe 或 msedge.exe 路径。浏览器不在标准位置时填写。\n\n浏览器等待 ms\n- Selenium 打开搜索结果页后，解析前等待的时间。\n\n无头浏览器\n- 不显示浏览器窗口。诊断验证码、跳转、空白页时建议关闭无头模式。\n\n每 N 页重启浏览器\n- 仅 Selenium 搜索采集有效。0 表示不按页数重启。Google 默认 4，百度默认 0。\n\n翻页等待 min/max ms\n- 搜索结果页之间的随机等待。默认 30000–90000 ms。\n\n切片等待 min/max ms\n- 日期切片之间的随机等待。\n\n错误冷却 min/max ms\n- 遇到 429、超时、连接错误等临时失败后的等待。\n\n超时秒数\n- Requests 获取搜索结果页的 HTTP 超时。\n\n接收后等待 ms\n- 收到搜索结果页后，解析前额外等待。\n\n空页重试次数/等待\n- 当解析器认为可能是临时空页或壳页时，重新请求。\n\n安全搜索\n- Google 参数，可为空、off、medium、high。比较研究中应保持一致。\n\n关闭重复过滤\n- Google filter=0，可能暴露更多相似结果，但会增加重复。\n\n输出文件/格式\n- 推荐 XLSX。CSV、TXT、DOCX、XML 用于不同流程。\n\n正文下载文件夹\n- 保存 raw_html、raw_text、clean_text、单页 metadata JSON、content_manifest.jsonl、content_metadata.xlsx。\n\n正文下载线程数\n- 并发正文下载 worker 数。同一域名内部仍会串行。\n\n正文下载模式\n- 仅 Requests、仅 Selenium、Requests 优先 + Selenium 兜底。\n\n正文页面等待 ms\n- 每个正文页面下载前的等待。独立于搜索结果翻页等待。\n\n正文接收/渲染等待 ms\n- 页面收到或渲染后额外等待，让慢加载页面更完整。\n\n清洗方案\n- auto 使用多语种分层抽取：编码检测、乱码修复、newspaper3k、站点模板、article/main/content 候选区和可见文本。\n\n失败内容重试次数\n- 正文链接失败后重试次数。\n\n单条内容任务超时秒数\n- 单个正文 URL 的硬超时，防止一条链接卡住整个批次。\n\n正文下载断点续传\n- 读取 content_manifest.jsonl，跳过已经成功下载的 URL。只适用于正文下载。\n\n同域名锁超时\n- 同域名串行下载的安全超时，防止一个卡住的 URL 永久阻塞该域名后续链接。""",
})

TEXTS["zh_tra"].update({
    "site_filters": "站點/域名限定（每行一個）",
    "site_help_link": "站點/域名填寫說明...",
    "help_site_title": "站點/域名限定說明",
    "site_help_text": TEXTS["zh_sim"]["site_help_text"].replace("站点", "站點").replace("语料库", "語料庫").replace("检索", "檢索").replace("结果", "結果").replace("查询", "查詢").replace("填写", "填寫").replace("启用", "啟用").replace("导出", "匯出"),
    "about": TEXTS["zh_sim"]["about"].replace("语料库", "語料庫").replace("网页", "網頁").replace("采集", "採集").replace("检索", "檢索").replace("结果", "結果").replace("下载", "下載").replace("强制关闭", "強制關閉").replace("链接", "連結").replace("启用", "啟用").replace("设置", "設定").replace("输出", "輸出").replace("说明", "說明").replace("参与", "參與").replace("软件", "軟體"),
    "user_guide_text": TEXTS["zh_sim"]["user_guide_text"].replace("检索", "檢索").replace("结果", "結果").replace("网页", "網頁").replace("采集", "採集").replace("导出", "匯出").replace("下载", "下載").replace("链接", "連結").replace("设置", "設定").replace("强制关闭", "強制關閉").replace("断点续传", "斷點續傳").replace("文件夹", "資料夾").replace("启用", "啟用"),
    "parameter_guide_text": TEXTS["zh_sim"]["parameter_guide_text"].replace("参数", "參數").replace("检索", "檢索").replace("结果", "結果").replace("网页", "網頁").replace("采集", "採集").replace("导出", "匯出").replace("下载", "下載").replace("链接", "連結").replace("设置", "設定").replace("默认", "預設").replace("超时", "逾時").replace("启用", "啟用"),
})

# Manual Google verification waiting (v1.2.4 focused patch).
TEXTS["en"].update({
    "verification_wait_title": "Manual Google verification required",
    "verification_wait_status": "Paused: complete verification in the browser window.",
    "verification_wait_message": "Google is asking for human verification. WebLens has paused on the current browser page and will not refresh, open a new page, paginate, or restart the browser while verification remains. Complete the verification manually in the Chrome/Edge window. WebLens checks the current page periodically; after verification is passed, it will refresh the current page once and resume crawling automatically. The Stop button remains available.",
})
TEXTS["zh_sim"].update({
    "verification_wait_title": "需要手动完成 Google 验证",
    "verification_wait_status": "已暂停：请在浏览器窗口中完成验证。",
    "verification_wait_message": "Google 正在要求进行真人验证。WebLens 已停留在当前浏览器页面；验证未通过期间，不会刷新、打开新页面、翻页或重启浏览器。请在 Chrome/Edge 窗口中手动完成验证。程序会定期检测当前页面；确认验证通过后，将自动刷新当前页面一次并继续采集。等待期间仍可使用“停止”按钮。",
})
TEXTS["zh_tra"].update({
    "verification_wait_title": "需要手動完成 Google 驗證",
    "verification_wait_status": "已暫停：請在瀏覽器視窗中完成驗證。",
    "verification_wait_message": "Google 正在要求進行真人驗證。WebLens 已停留在目前瀏覽器頁面；驗證未通過期間，不會重新整理、開啟新頁面、翻頁或重新啟動瀏覽器。請在 Chrome/Edge 視窗中手動完成驗證。程式會定期檢測目前頁面；確認驗證通過後，將自動重新整理目前頁面一次並繼續採集。等待期間仍可使用「停止」按鈕。",
})



# v1.2.8 CustomTkinter / ClearLens visual refresh and richer About attribution.
TEXTS["en"]["about"] = TEXTS["en"].get("about", "BFSU WebLens").replace(
    "BFSU WebLens v1.2.8", "BFSU WebLens v1.2.8"
).replace(
    "Author and project lead: Liu Dingjia, Beijing Foreign Studies University.",
    "Author and project lead: Dr. Liu Dingjia (刘鼎甲 博士), Beijing Foreign Studies University.\n- Email: djliu@bfsu.edu.cn."
) + """

Interface refresh in v1.2.8
- The traditional WebLens layout and native menu bar are retained, while frames, sections, buttons, entries, comboboxes, checkboxes, text areas, progress bars, tab controls, split panes, date controls, and application dialogs now preferentially use CustomTkinter.
- Native Tk/ttk remains only where CustomTkinter has no direct replacement, principally the traditional menu system, result Treeview, and multi-select Listbox controls; these controls receive ClearLens colors and DPI-aware metrics.
- Panel spacing, control height, typography, border radius, surfaces, and toolbar rhythm have been aligned with BFSU ClearLens without changing the collection workflow.
- The left settings pane scrolls smoothly whenever the pointer is anywhere inside it, including over multiline text boxes and multi-select lists.
- Main and child windows are clamped and centered against the usable screen area so that high-DPI Windows 11 displays do not open with portions outside the screen.
- The WebLens icon has been redrawn in the ClearLens/LexiScope navy-and-teal style, with a globe inside the lens; the ICO contains dedicated 16–256 px images for clear title-bar and taskbar rendering."""

TEXTS["zh_sim"]["about"] = TEXTS["zh_sim"].get("about", "BFSU WebLens").replace(
    "BFSU WebLens v1.2.8", "BFSU WebLens v1.2.8"
).replace(
    "作者与项目主导：刘鼎甲，北京外国语大学。",
    "作者与项目主导：Dr. Liu Dingjia、刘鼎甲 博士，北京外国语大学。\n- 邮件地址：djliu@bfsu.edu.cn。"
) + """

v1.2.8 界面更新
- 保留 WebLens 原有的传统布局和原生菜单栏；框架、分组面板、按钮、输入框、下拉框、复选框、多行文本框、进度条、标签页、可拖动分栏、日期控件及应用内对话框均优先改为 CustomTkinter。
- 仅在 CustomTkinter 没有直接替代组件时保留原生 Tk/ttk，主要包括传统菜单、结果 Treeview 和多选 Listbox，并为这些控件加入 ClearLens 配色与 DPI 适配。
- 面板间距、控件高度、字体节奏、圆角、边框和工具栏留白均与 BFSU ClearLens 对齐，同时不改变原有采集流程。
- 鼠标位于左侧设定栏任意位置时均可平滑滚动，包括多行文本框和多选列表区域。
- 主窗口和各子窗口会根据可用屏幕尺寸自动限制大小并居中，避免 Windows 11 高 DPI 缩放下窗口只显示局部。
- WebLens 图标按 ClearLens/LexiScope 的深蓝—青绿色风格重新绘制，以放大镜中的地球突出网页采集功能；ICO 内含 16–256 px 专用图像，以改善标题栏和任务栏清晰度。"""

TEXTS["zh_tra"]["about"] = TEXTS["zh_tra"].get("about", TEXTS["zh_sim"]["about"]).replace(
    "BFSU WebLens v1.2.8", "BFSU WebLens v1.2.8"
).replace(
    "作者與項目主導：劉鼎甲，北京外國語大學。",
    "作者與項目主導：Dr. Liu Dingjia、劉鼎甲 博士，北京外國語大學。\n- 電子郵件：djliu@bfsu.edu.cn。"
).replace(
    "作者与项目主导：刘鼎甲，北京外国语大学。",
    "作者與項目主導：Dr. Liu Dingjia、劉鼎甲 博士，北京外國語大學。\n- 電子郵件：djliu@bfsu.edu.cn。"
) + """

v1.2.8 介面更新
- 保留 WebLens 原有的傳統配置和原生選單列；框架、分組面板、按鈕、輸入框、下拉框、核取方塊、多行文字框、進度列、分頁、可拖動分欄、日期控制項及應用程式對話框均優先改為 CustomTkinter。
- 僅在 CustomTkinter 沒有直接替代元件時保留原生 Tk/ttk，主要包括傳統選單、結果 Treeview 和多選 Listbox，並為這些控制項加入 ClearLens 配色與 DPI 適配。
- 面板間距、控制項高度、字體節奏、圓角、邊框和工具列留白均與 BFSU ClearLens 對齊，同時不改變原有採集流程。
- 滑鼠位於左側設定欄任意位置時均可平滑捲動，包括多行文字框和多選清單區域。
- 主視窗和各子視窗會根據可用螢幕尺寸自動限制大小並置中，避免 Windows 11 高 DPI 縮放下視窗只顯示局部。
- WebLens 圖示按 ClearLens/LexiScope 的深藍—青綠色風格重新繪製，以放大鏡中的地球突出網頁採集功能；ICO 內含 16–256 px 專用圖像，以改善標題列和工作列清晰度。"""


# v1.2.8 main-window positioning fix.
TEXTS["en"]["about"] += """

Window positioning fix in v1.2.8
- The main window is fitted to the usable monitor work area once at startup and is no longer repeatedly re-centered by the event queue.
- CustomTkinter logical dimensions are converted correctly against physical monitor pixels, and the Windows taskbar area is excluded, so the window remains fully visible and can be freely moved."""
TEXTS["zh_sim"]["about"] += """

v1.2.8 窗口位置修复
- 主窗口只在启动时按照显示器可用工作区定位一次，后台事件队列不再反复强制居中，用户可自由拖动窗口。
- 正确换算 CustomTkinter 逻辑尺寸与显示器物理像素，并扣除 Windows 任务栏区域，避免高 DPI 下窗口右侧或底部超出桌面。"""
TEXTS["zh_tra"]["about"] += """

v1.2.8 視窗位置修復
- 主視窗只在啟動時按照顯示器可用工作區定位一次，背景事件佇列不再反覆強制置中，使用者可自由拖動視窗。
- 正確換算 CustomTkinter 邏輯尺寸與顯示器實體像素，並扣除 Windows 工作列區域，避免高 DPI 下視窗右側或底部超出桌面。"""

# v1.2.8 toolbar, grouping and download-folder navigation.
TEXTS["en"].update({
    "open_download_folder": "Open downloads",
    "preview_records_group": "Records",
    "preview_sort_group": "Sort",
    "preview_sample_group": "Sampling",
    "preview_download_group": "Content download",
})
TEXTS["zh_sim"].update({
    "open_download_folder": "打开下载文件夹",
    "preview_records_group": "记录操作",
    "preview_sort_group": "排序",
    "preview_sample_group": "采样",
    "preview_download_group": "正文下载",
})
TEXTS["zh_tra"].update({
    "open_download_folder": "開啟下載資料夾",
    "preview_records_group": "記錄操作",
    "preview_sort_group": "排序",
    "preview_sample_group": "採樣",
    "preview_download_group": "正文下載",
})
