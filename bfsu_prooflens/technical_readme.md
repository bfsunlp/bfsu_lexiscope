# BFSU ProofLens 智能 OCR 校对工具

**BFSU ProofLens OCR Proofreading Tool** 是一个 Windows 单机桌面软件项目，面向语言学、语料库建设、翻译研究、文献整理和教学资料数字化场景。软件支持图像/PDF OCR、图文对照校对、OpenAI / ChatGPT 辅助校对、多语种与多语混排识别提示、项目化保存和多格式导出。

当前版本：**V1.0.14 MVP**

> 本文档为技术版 README。仅使用图形界面的用户请阅读 `README.md`。

---

## 1. 已实现功能


### 界面语言

- 默认界面语言为英文；
- 菜单栏提供 `Settings -> Language -> English / 中文`；
- 用户切换语言后会立即刷新 GUI；
- 语言偏好写入 `config/user_config.json`，下次启动自动沿用。

### 核心界面

- `tkinter + ttk` 桌面 GUI；
- 菜单栏、工具栏、主工作区和状态栏；
- 左侧文件/页面列表；
- 中间单页图像预览；
- 右侧 OCR 文本编辑区；
- 底部 LLM 修订建议区；
- 关于窗口，含中英文介绍、作者、单位、邮箱与 AI 协作声明；
- 图标资源统一放在 `assets/` 文件夹中。

### 文件导入

- 支持导入：PDF、JPG/JPEG、PNG、TIF/TIFF、BMP、WebP；
- 支持批量导入；
- PDF 使用 PyMuPDF 渲染为单页图片；
- 每页保留独立 OCR 文本、LLM 校对文本、最终确认文本、OCR 坐标、置信度和修订建议。

### 语种选择与多语混排

工具栏和设置窗口都支持预先选择 OCR 语种：

- `zh_en_mixed`：中文 + English 混排，默认；
- `zh`：中文；
- `en`：English；
- `ja`：日本語；
- `ko`：한국어；
- `fr`：Français；
- `de`：Deutsch；
- `es`：Español；
- `ru`：Русский；
- `latin_mixed`：拉丁文字混排；
- `multi_mixed`：多语混排。

设置窗口可多选语言。多选语言会作为“多语混排”提示写入项目和 LLM Prompt。需要注意的是，RapidOCR 本身并不是对任意语种组合都能一次性同时识别；MVP 中会根据预设映射到 RapidOCR 的 `lang` 参数，同时把用户选择的多个语种保留给 LLM OCR / LLM 校对和导出记录。



### 批量任务队列与并行加速（V1.0.2）

本版本在上一版后台线程防假死机制基础上增加了批量任务与可选并行加速：

- `OCR -> Run OCR on Current File`：对当前文件的全部页面执行 RapidOCR；
- `OCR -> Run OCR on Whole Project`：对整个项目全部页面执行所选本地 OCR；
- `OCR -> Fast OCR (EasyOCR)`：对当前页、当前文件或整个项目执行 EasyOCR 快速识别；
- `LLM -> LLM OCR on Current File`：对当前文件逐页调用 LLM OCR；
- `LLM -> LLM Proofread Current File`：对当前文件逐页调用 LLM 校对；
- 主界面底部进度条会显示批量任务总体进度、当前文件和当前页状态；
- 左侧文件树会在每页完成后即时更新 `⏳ / ✅ / ❌ / ⚠` 状态；
- `src/parallel_workers.py` 提供可被线程池或进程池调用的顶层 worker 函数；
- RapidOCR 支持 `thread` 与 `process` 两种并行后端，默认为 `thread`；
- LLM OCR / LLM 校对使用线程池并发请求，不使用进程池；
- `main.py` 已加入 `multiprocessing.freeze_support()`，便于 Windows 与 PyInstaller 场景下使用可选进程池。

配置项位于 `config/default_config.json`：

```json
"ocr": {
  "parallel_backend": "thread",
  "max_workers": 1
},
"llm": {
  "max_concurrent_requests": 1
}
```

建议默认保持 `thread + 1 worker` 以获得最高兼容性。CPU 批量 OCR 可尝试 2–4 个 worker；GPU OCR 不建议使用进程池，以免多个子进程争抢同一 GPU。LLM 并发数应根据 API 限额和网络稳定性调整。


### EasyOCR 快速识别模式（V1.0.4）

V1.0.4 新增 `src/easy_ocr_backend.py`，提供 EasyOCR 本地快速识别后端。设计定位是“演示优先 / 快速草稿 OCR”，与 RapidOCR 的高质量识别形成互补。

主要设计：

- OCR backend 新增 `easyocr`；
- 菜单新增 `OCR -> Fast OCR (EasyOCR)`，可直接对当前页、当前文件或整个项目运行快速 OCR；
- 工具栏新增 `Fast OCR` 按钮，用于演示时快速识别当前页；
- `src/parallel_workers.py` 新增 `easyocr_recognize_page()`；
- RapidOCR 与 EasyOCR worker 均使用线程本地缓存，避免同一线程中每页重复初始化 OCR 模型；
- EasyOCR 默认开启 `easyocr_light_mode`，强制使用 `thread + 1 worker`，以降低 RAM/CPU 负载，避免多个 PyTorch Reader 同时加载；
- 可配置 `easyocr_model_dir`、`easyocr_canvas_size`、`easyocr_mag_ratio` 和 `easyocr_paragraph`。

新增配置项：

```json
"ocr": {
  "backend": "rapidocr",
  "easyocr_model_dir": "models/easyocr",
  "easyocr_light_mode": true,
  "easyocr_canvas_size": 1280,
  "easyocr_mag_ratio": 1.0,
  "easyocr_paragraph": false
}
```

使用建议：

- 演示、课堂展示、快速预览：优先使用 EasyOCR；
- 正式语料建设、论文材料转写和复杂版面：优先使用 RapidOCR；
- EasyOCR 首次运行仍需下载模型，之后模型会缓存在 `models/easyocr`。

### OCR 引擎

已实现：

- 本地 RapidOCR 识别；
- EasyOCR 快速识别模式；
- 输出 OCR 文本行；
- 输出文本块、置信度、坐标和阅读顺序；
- 可配置 RapidOCR `lang`、GPU、方向分类、PDF DPI 和模型目录；
- RapidOCR 懒加载：即使尚未安装 RapidOCR，软件也可以启动；运行 OCR 时会提示缺失依赖。

预留/已接入：

- `rapidocr`；
- `easyocr`；
- `llm_ocr`；
- `hybrid`。

### LLM / ChatGPT

已实现：

- OpenAI API Key 设置；
- 可从环境变量 `OPENAI_API_KEY` 读取；
- 用户可设置默认模型，默认写为 `gpt-5.5`；
- LLM OCR 当前页；
- LLM 校对当前页；
- 严格 JSON 输出 Prompt；
- 修订建议展示、接受、拒绝、全部接受、清空；
- 隐私提醒：调用外部 API 前提示用户确认；
- “仅本地模式”会禁用 LLM 功能。

### 项目管理

项目文件后缀：

```text
.bfsu_prooflens
```

项目保存内容包括：

- 项目名称；
- 软件版本；
- 配置信息；
- 导入文件路径；
- 页面图像路径；
- 每页 OCR 原文；
- 每页 LLM 校对文本；
- 每页最终确认文本；
- OCR 文本块、坐标和置信度；
- LLM 修订建议；
- OCR / LLM 状态和耗时。

### 导出格式

已实现以下导出函数，均位于 `src/export_utils.py`，不依赖 GUI：

```python
export_to_txt(project_data, export_path, scope="project", options=None)
export_to_docx(project_data, export_path, scope="project", options=None)
export_to_xlsx(project_data, export_path, scope="project", options=None)
export_to_json(project_data, export_path, scope="project", options=None)
export_to_xml(project_data, export_path, scope="project", options=None)
export_to_markdown(project_data, export_path, scope="project", options=None)
```

支持导出范围：

- 当前页；
- 当前文件；
- 整个项目。

支持导出格式：

- TXT；
- DOCX；
- XLSX；
- JSON；
- XML；
- Markdown / MD。

Markdown 为必选功能，已实现 UTF-8 输出、标题分级、代码块、修订建议表和 OCR 文本块表。

---

## 2. 项目结构

```text
bfsu_prooflens/
  main.py
  requirements.txt
  README.md                  # 简明图形界面用户说明
  technical_readme.md        # 技术说明、依赖安装与打包说明
  build_exe.bat
  clean_build.bat
  config/
    default_config.json
  assets/
    app.ico
    app.png
    logo.png
  models/
    rapidocr/
    easyocr/
  src/
    __init__.py
    app.py
    ui_main.py
    ui_about.py
    ui_settings.py
    ui_proofreading.py
    ui_export.py
    ocr_backend.py
    rapid_ocr_backend.py
    easy_ocr_backend.py
    parallel_workers.py
    llm_backend.py
    llm_prompts.py
    project_manager.py
    file_loader.py
    pdf_utils.py
    image_utils.py
    export_utils.py
    config_manager.py
    i18n.py
    logger.py
    utils.py
  output/
  temp/
  logs/
```

---

## 3. 安装与运行

建议使用 Python 3.10 或 Python 3.11。

### 3.1 创建虚拟环境

```bat
python -m venv .venv
call .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 3.2 运行软件

```bat
python main.py
```

### 3.3 本地 OCR 注意事项

`requirements.txt` 中包含：

```text
rapidocr
onnxruntime
easyocr
```

首次安装 RapidOCR / EasyOCR 可能较慢。EasyOCR 会安装 PyTorch 相关依赖，并在首次运行时下载对应语言模型。若需 GPU 版本 ONNXRuntime，请根据自己的 CUDA 环境到 ONNXRuntime 官方安装页选择对应版本。MVP 默认 `use_gpu=false`，即 CPU 模式。

使用建议：

- RapidOCR：正式、高质量 OCR；
- EasyOCR：演示、快速预览、草稿识别；
- EasyOCR 轻量/演示模式默认开启，使用单缓存 worker 降低重复加载和机器负载。

### 3.4 OpenAI / ChatGPT 设置

有两种方式配置 API Key：

方式一：在软件中打开：

```text
工具 -> 设置 -> 大模型 / LLM -> OpenAI API Key
```

方式二：设置环境变量：

```bat
set OPENAI_API_KEY=你的Key
```

默认模型在 `config/default_config.json` 中为：

```json
"model": "gpt-5.5"
```

也可以在设置窗口中修改。

---

## 4. 使用流程

1. 启动软件；
2. 新建项目；
3. 在工具栏选择 OCR 语种预设，必要时勾选“多语混排”；
4. 导入 PDF 或图片；
5. 在左侧选择页面；
6. 点击 `OCR识别` 运行 RapidOCR；
7. 在右侧编辑 OCR 文本；
8. 如需大模型辅助，在设置中关闭“仅本地模式”、启用 ChatGPT，并填写 API Key；
9. 点击 `LLM校对` 生成修订建议；
10. 在底部逐条接受或拒绝建议；
11. 保存项目；
12. 导出为 TXT、DOCX、XLSX、JSON、XML 或 Markdown。

---

## 5. PyInstaller 打包

Windows 下运行：

```bat
build_exe.bat
```

打包模式：`onedir`。

生成结果位于：

```text
dist\BFSU_ProofLens\BFSU_ProofLens.exe
```

清理打包文件：

```bat
clean_build.bat
```

---

## 6. 配置文件说明

默认配置：

```text
config/default_config.json
```

用户配置运行后保存到：

```text
config/user_config.json
```

主要配置项：

```json
{
  "ocr": {
    "backend": "rapidocr",
    "language_preset": "zh_en_mixed",
    "selected_languages": ["zh", "en"],
    "mixed_language_mode": true,
    "rapid_lang": "ch",
    "use_gpu": false,
    "use_angle_cls": true,
    "pdf_dpi": 200
  },
  "llm": {
    "enabled": false,
    "api_key": "",
    "model": "gpt-5.5",
    "temperature": 0,
    "structured_json": true
  },
  "privacy": {
    "local_only": true,
    "remind_before_llm": true,
    "do_not_save_api_key": false
  }
}
```

---

## 7. 隐私建议

如处理涉密、敏感或未获授权材料，请保持：

```text
仅本地模式 = 开启
```

此时软件只使用本地 RapidOCR，不会调用外部 API。

调用 LLM 前，软件会提示：

```text
您即将把当前页面图像或 OCR 文本发送给外部 API。请确认该文件不包含涉密或敏感信息。
```

---

## 8. 当前 MVP 的边界

- 拖拽导入仅预留，未启用；
- 行号显示为简化实现；
- RapidOCR 多语混排依赖 RapidOCR 自身模型能力，任意语种组合并非都能一次识别；
- Hybrid 双引擎目前保留流程接口，当前主流程为 RapidOCR + LLM OCR / LLM 校对；
- LLM API 调用使用 OpenAI Python SDK 的 Chat Completions 接口，不同模型是否支持图像输入取决于 OpenAI 模型能力；
- PDF 项目再次打开后，如果临时页面图像被删除，需要重新导入 PDF 或重新渲染。

---

## 9. 作者信息

作者 / Author：**Dingjia LIU**  
单位 / Affiliation：**Beijing Foreign Studies University**  
邮箱 / Email：**djliu@bfsu.edu.cn**

© 2026 Dingjia LIU. All rights reserved.

## V1.0.1 更新：后台任务与进度条

本版本将本地 OCR、LLM OCR 和 LLM 校对三个耗时操作从 Tkinter 主线程中移出，改为后台线程执行。界面更新统一通过主线程队列和 `after()` 轮询处理，避免 OCR 或 API 调用期间出现窗口假死。

新增内容包括：

- 主界面底部进度条；
- 当前任务显示；
- 当前处理文件显示；
- 文件/页面树中的 `⏳`、`✅`、`❌`、`⚠` 状态标记；
- 同一时间仅运行一个 OCR/LLM 任务的保护机制；
- 语言切换与设置窗口在任务运行期间会暂时阻止打开，避免后台任务与界面重建冲突。

---

## V1.0.4 更新：后台 PDF 导入与模型下载控制

此前版本已经将 OCR / LLM 任务移出 Tkinter 主线程，但 `import_files()` 在主线程中直接调用 `load_file_to_pages()`，而 PDF 导入会调用 PyMuPDF 将整本 PDF 逐页渲染为 PNG。因此，打开页数较多或分辨率较高的 PDF 时，Tkinter 事件循环会被阻塞，表现为主窗口“假死”。

V1.0.4 的修正：

- `import_files()` 改为使用 `_start_background_task()` 执行后台导入；
- `file_loader.load_file_to_pages()` 增加 `progress_callback`；
- `pdf_utils.render_pdf_to_images()` 增加逐页进度回调；
- 主界面底部进度条显示当前导入文件与 PDF 当前渲染页；
- 图像预览增加 `preview_max_side` 限制，避免超大页面预览时消耗过多 UI 线程时间和内存。

V1.0.4 还增加了 OCR 模型下载控制：

- `ocr.model_download_policy`: `ask` / `auto` / `manual`；
- `ask` 为默认策略，会在会话中首次使用对应 OCR 引擎时询问；
- EasyOCR 通过 `download_enabled` 显式控制自动下载；
- RapidOCR 的下载控制参数在不同版本中存在差异，代码会使用 `inspect.signature()` 检查当前安装版本是否支持 `download_enable` 或 `download_enabled`，支持则传入，不支持则安全忽略。

---

## V1.0.5 更新：PDF 导入独立进程与预览图缓存

V1.0.4 虽然把 `import_files()` 移入后台线程，但部分 Windows 电脑在打开 PDF 后仍可能出现“未响应”。代码检查发现，风险点主要有三类：

1. PyMuPDF 属于 C 扩展重负载渲染，后台线程不一定足以避免 GUI 响应延迟；
2. 导入完成后，主线程会打开 PDF 渲染出的原始大 PNG 做预览，超大页面会造成 Tkinter 主线程长时间解码图像；
3. 程序自动选择第一页时，`Treeview.selection_set()` 可能触发 `<<TreeviewSelect>>` 回调，导致重复选择与重复预览刷新。

V1.0.5 的修正：

- 新增 `src/import_workers.py`，使用 `multiprocessing` 独立进程执行文件导入与 PDF 渲染；
- `MainWindow.import_files()` 中的后台线程只负责桥接子进程进度消息，不再直接执行 PyMuPDF 渲染；
- `file_loader.load_file_to_pages()` 新增 `preview_max_side` 参数；
- 导入时为每页生成 `preview_path`，OCR 继续使用 `image_path` 原图，GUI 预览优先使用 `preview_path`；
- `show_image()` 和 `fit_image()` 优先加载预览图，降低主线程图像解码压力；
- 新增 `_suppress_tree_select`，防止程序化选择页面时重复触发 Treeview 选择事件；
- 大 PDF 文件节点不再强制自动展开全部页面，减少页面树刷新负担；
- PyInstaller 打包脚本加入 `src.import_workers` 隐式导入。

模型下载控制仍沿用 V1.0.4 机制：

- EasyOCR 使用 `download_enabled` 控制是否自动下载；
- RapidOCR 使用运行时签名检查，兼容不同版本可能存在的 `download_enable` / `download_enabled` 参数；
- 若 RapidOCR 当前安装版本不暴露下载控制参数，建议通过本地模型目录 `det_model_dir`、`rec_model_dir`、`cls_model_dir` 管理模型，并在演示前完成预下载。

---

## V1.0.6 更新：异步预览加载与设置窗口滚动布局

用户反馈：打开 PDF 后底部状态栏已经显示 Complete，但界面随后仍可能在点击时被 Windows 标记为“未响应”。进一步排查后，风险点主要集中在导入完成后的主线程收尾阶段，而不再是 OCR 或 PDF 渲染本身。

V1.0.6 的修正：

- `_poll_task_queue()` 改为小批量处理进度队列，每次最多处理 25 条事件，避免一次性消费大量导入进度消息；
- `_set_status()` 与 `_set_progress()` 移除 `update_idletasks()`，避免在后台任务回调内触发 Tkinter 重入式刷新；
- 导入成功回调只调度 `_finish_import_result()`，不再在队列轮询回调内直接完成全部 UI 收尾操作；
- 导入完成后延迟选择第一页，避免 Treeview 重建、页面选择和图像预览加载集中在同一轮事件循环中；
- `show_image()` 改为异步预览加载，后台线程负责 `PIL.Image.open()`、旋转、缩放和复制，主线程只创建 `ImageTk.PhotoImage` 并更新 Canvas；
- 默认 `ocr.preview_max_side` 从 1800 调整为 1400，以降低弱性能电脑上的 Tk 图像显示压力；
- PDF 导入子进程取消 `daemon=True`，并在完成后关闭 multiprocessing queue，提升 Windows / PyInstaller 环境稳定性；
- `SettingsDialog` 的每个 Notebook 选项卡改为可滚动 Canvas + 内嵌 Frame，底部 Save / Cancel 按钮固定在外层布局中，避免低分辨率屏幕上按钮不可见。

验证：

- 全部 Python 文件通过 `compileall`；
- 使用用户提供的 `lali.00019.hsu.pdf` 进行导入 worker 测试，成功导入 24 页；
- 在 `xvfb` 环境下完成主窗口加载、项目添加、页面树刷新、第一页选择与异步预览加载烟测；
- 在 `xvfb` 环境下完成 SettingsDialog 创建烟测。

---

## V1.0.7 更新：OCR/LLM 失败诊断与 RapidOCR 2.x/3.x 兼容

用户反馈：PDF 导入和界面卡死问题解决后，点击 Run OCR、LLM OCR、LLM Proofreading 时可能只显示“Batch Finished with Errors”，但没有暴露具体失败原因。本版主要修复错误诊断和 OCR 后端兼容性。

### 主要修正

- `src/ui_main.py`
  - 新增 `_preflight_ocr_engine()`：在启动 OCR 前检查 `rapidocr` / `easyocr` 是否安装；
  - 新增 `_preflight_llm()`：在启动 LLM 前检查 API Key、模型名、`openai` 包、图像/文本发送权限；
  - 批量任务结果新增 `errors` 字段；
  - 失败弹窗会显示前若干条具体页级错误，不再只显示成功/失败计数；
  - LLM 可读取 `OPENAI_API_KEY` 环境变量。

- `src/rapid_ocr_backend.py`
  - 重写 RapidOCR 包装器；
  - 同时支持 RapidOCR 2.x 风格：`RapidOCR(...).ocr(image, cls=...)`；
  - 支持 RapidOCR 3.x 风格：`RapidOCR(...).predict(image)`；
  - 初始化参数按当前安装版本签名过滤；
  - 兼容 `use_angle_cls` 与 `use_textline_orientation`；
  - 兼容旧版 `use_gpu` 与新版 `device`；
  - 支持解析 2.x 返回结构和 3.x `rec_texts` / `rec_scores` / `rec_polys` / `rec_boxes` 结构。

- `src/easy_ocr_backend.py`
  - EasyOCR light/demo mode 下会收缩过大的多语列表，减少多模型加载导致的失败和内存占用；
  - 改进 EasyOCR 未安装时的提示。

- `src/llm_backend.py`
  - API Key 支持从 `OPENAI_API_KEY` 环境变量读取；
  - 支持可选 `OPENAI_BASE_URL`；
  - Chat Completions 参数增加兼容回退：`max_completion_tokens` / `max_tokens` / 移除 temperature；
  - 图像文件缺失时给出明确错误。

### 调试建议

OCR 报错优先检查：

```bat
python -c "import rapidocr; print('rapidocr ok')"
python -c "import easyocr; print('easyocr ok')"
```

LLM 报错优先检查：

```bat
python -c "import openai; print('openai ok')"
set OPENAI_API_KEY=你的key
```

RapidOCR 3.x 的官方 Python 示例使用 `RapidOCR(...).predict(...)`，而 2.x 版本常用 `ocr(..., cls=True)`，因此本版在后端中同时保留两套调用路径。

## V1.0.8 Technical Notes

### RapidOCR model hosting errors

RapidOCR 3.x uses PaddleX model-host checks before model initialization. Some networks cannot reach the default hosting platform and may raise `No available model hosting platforms detected`. V1.0.8 exposes:

- `ocr.paddle_model_source`: `auto`, `huggingface`, `modelscope`, `aistudio`, `bos`;
- `ocr.paddle_disable_model_source_check`: sets `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` before RapidOCR initialization;
- `ocr.model_download_policy`: `ask`, `auto`, `manual`.

The default is `paddle_model_source=bos` and `paddle_disable_model_source_check=true`, which is more suitable for many Chinese-network demonstration environments.

### Embedded text layer for PDFs

`pdf_utils.extract_pdf_page_texts()` now extracts text blocks with PyMuPDF before PDF rasterization. `file_loader.load_file_to_pages()` stores this as `embedded_text`, initializes `ocr_text/final_text`, and marks the page as `ocr_status=text_layer`. `run_ocr_scope()` uses embedded text by default when `ocr.prefer_pdf_text_layer=true`, bypassing RapidOCR/EasyOCR for text-based PDFs.

### OCR text layout reconstruction

`utils.reconstruct_text_from_blocks()` groups OCR blocks by bounding boxes and reconstructs paragraph-like text. OCR backends use `ocr.text_layout`:

- `paragraph`: default; merge wrapped OCR lines into paragraphs using script-aware spacing;
- `line`: legacy behavior; preserve OCR block/line breaks.

### LLM proofreading data source

`run_llm_proofread_scope()` now prioritizes the current Text editor content for the current page. If `ocr_text` is empty, it uses `embedded_text` or the editor text as the OCR comparison source. The suggestion panel receives an informational suggestion even when the model returns no concrete corrections or non-JSON output.

## V1.0.11 Technical Notes

### Stronger LLM proofreading

`src/llm_prompts.py` now uses a more explicit OCR proofreading prompt. It asks the model to focus on OCR/PDF extraction problems rather than stylistic rewriting. Covered categories include:

- `ocr_typo`, `missing_text`, `extra_text`, `punctuation`, `whitespace`;
- `garbled_text`, `encoding_noise`, `language_confusion`;
- `hard_line_break`, `hyphenation`, `paragraph_reflow`;
- `reading_order`, `duplicate_text`, `header_footer_noise`, `table_or_list_format`.

`src/llm_backend.py` adds a lenient JSON recovery layer:

- strips Markdown code fences;
- extracts the first balanced JSON object from mixed text;
- removes common trailing commas;
- falls back to `ast.literal_eval` for Python-like dictionaries;
- recovers plain-text bullet points or `Original:` / `Suggested:` fragments as reviewable suggestions.

It also adds local rule-based text checks for common OCR artifacts, including replacement characters, `￾`, BOM/zero-width characters, hyphenated line breaks, hard-wrapped paragraphs, and repeated whitespace.

### RapidOCR CPU runtime compatibility

`src/rapid_ocr_backend.py` now configures conservative RapidOCR runtime flags before RapidOCR initialization:

- `PADDLE_PDX_MODEL_SOURCE=BOS` by default when model source is not `auto`;
- `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` when enabled in settings;
- `FLAGS_use_mkldnn=0` and `FLAGS_use_onednn=0` when `ocr.paddle_disable_onednn=true`;
- `FLAGS_enable_pir_api=0` when `ocr.paddle_disable_pir=true`.

The backend also passes `enable_mkldnn=false` and `cpu_threads` when the installed RapidOCR API accepts those parameters. Recognition retries once with conservative runtime flags if a oneDNN/PIR compatibility error is detected.

### EasyOCR fallback

`src/parallel_workers.py` now supports `ocr.auto_fallback_to_easyocr`. When a page-level RapidOCR task fails and fallback is enabled, the worker runs EasyOCR light mode and returns the result with `engine=easyocr_fallback` and a `fallback_reason` field. This prevents a single RapidOCR runtime failure from blocking demonstration workflows.


## V1.0.11 Technical Notes

V1.0.11 strengthens the LLM proofreading fallback layer:

- `src/llm_backend.py` now extracts text from multiple OpenAI-compatible message content shapes rather than assuming `message.content` is always a plain string.
- Non-JSON proofreading responses trigger one optional JSON repair pass controlled by `llm.auto_repair_non_json`.
- Plain-text responses are parsed for whole-text correction sections, `Original/Suggested` pairs, arrow-style corrections, and Markdown bullets. If no actionable replacement can be inferred, the raw feedback is still displayed as manual-review information instead of being hidden in `layout_notes`.
- Empty model responses are surfaced as `llm_empty_response` diagnostic suggestions rather than appearing as successful but blank proofreading runs.
- `src/ui_proofreading.py` uses a scrollable detail window, which is safer for long LLM feedback than a standard message box.

## V1.0.11 GUI/File Tree Technical Notes

This version adds explicit Simplified/Traditional Chinese UI support and file/page tree management:

- `src/i18n.py` now normalizes legacy `zh` to `zh_cn`, while adding explicit `zh_cn` and `zh_tr` language codes.
- `SettingsDialog` stores UI language as `en`, `zh_cn`, or `zh_tr`; existing old projects using `zh` remain compatible.
- `MainWindow` builds the language menu dynamically from `LANGUAGE_LABELS`.
- The file/page `Treeview` now has a right-click context menu and bottom `+`/`−` buttons.
- Deleting a file removes all its project pages; deleting a page renumbers the remaining pages.
- Adding pages to a selected file reuses the existing background import process and appends imported pages to the target file without blocking the GUI.


## V1.0.13 更新：文件/页面树删除行为修正

- `select_page()` 新增 `sync_tree_selection` 参数。来自 Treeview 单击事件的页面显示不会反向重写 Treeview 选区。
- 单击文件节点时，程序只把第一页加载到预览与文本编辑区，不再把选中项自动改为 `page:<file_id>:0`，因此随后点击 `−`、右键删除或按 `Delete` 会按文件级删除处理。
- `on_tree_context_menu()` 改为在右键点击当前多选范围内项目时保留多选，只有右键点击选区外项目时才切换为单项操作。
- `Delete` 与 `KP_Delete` 现在统一走 `_on_tree_delete_key()`，执行删除后返回 `break`，避免事件继续传播。

## V1.0.12 更新：RapidOCR 替换与文件/页面管理

- `src/rapid_ocr_backend.py` 替代旧的 PaddleOCR 包装器，OCR 主流程使用 `RapidOCRBackend`。
- `src/parallel_workers.py` 中新增 `rapidocr_recognize_page()`，保持线程本地缓存，并在 RapidOCR 失败时可自动回退到 EasyOCR。
- `src/ui_main.py` 的 OCR 批处理在提交页面任务前调用 `prepare_rapidocr_models()`，用于提前检查/准备 RapidOCR 模型，并通过进度条反馈模型检查状态。
- `src/ui_settings.py` 中 OCR 后端选项改为 `rapidocr / easyocr / llm_ocr / hybrid`；语言勾选区新增 `zh_tr`，语言预设只新增单独的 `zh_tr`，不新增繁体中文与英语混合预设。
- 文件/页面树改为扩展选择模式，删除逻辑支持文件级和页面级混合选择；键盘 `Delete` 与小按钮 `−` 复用同一删除函数。


## V1.0.14 更新：滚轮兼容与按源文件分别导出

- 所有主要带滚动条的区域统一接入鼠标中键滚轮支持，包括文件/页面树、图像预览、文本编辑器、设置窗口、修订建议表、建议详情窗口和关于窗口。
- 导出设置中新增“按源文件分别导出为 源文件名_ocr”选项。启用后，导出路径选择改为文件夹选择，并按每个源文件分别生成 `原文件名_ocr` 文件，扩展名随所选格式自动变化。
