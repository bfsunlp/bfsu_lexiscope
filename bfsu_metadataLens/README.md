# BFSU MetadataLens v3.5.5

**BFSU MetadataLens** 是面向语言学研究、语料库建设、语言资源数据库建设和语料库翻译学研究的元信息规范设计、录入、批量整理与管理工具。

**BFSU MetadataLens** is a metadata schema design, entry, batch-processing and management tool for linguistic research, corpus construction, language-resource databases, and corpus-based translation studies.

---

## Download / 下载

**Current Release / 当前版本：** `BFSU MetadataLens v3.5.5`

**File / 文件名：** `BFSU_MetadataLens v3.5.5.zip`

### Direct Download / 直接下载

https://icloud.bfsu.edu.cn/seafhttp/f/0a5706e5f2b74eb1af69/?op=view

### Baidu Netdisk / 百度网盘

https://pan.baidu.com/s/1GeVCqrM6Hi1UgILYgkdNhQ?pwd=5pty

**Extraction Code / 提取码：** `5pty`

> Please download the complete ZIP package, extract it fully, and run BFSU MetadataLens from the extracted folder. Do not move only the executable file.  
> 请下载完整 ZIP 压缩包并完整解压后运行 BFSU MetadataLens，不要只单独移动可执行文件。

---

## v3.5.5 子窗口自适应尺寸优化

v3.5.5 在 v3.5.4 已稳定的原生 `tkinter.Toplevel` 子窗口机制上，重点解决高 DPI/高缩放环境中“窗口打开后面板太小、按钮和文字互相挤压、底部操作区显示不全”的问题。

本版本不再只依赖每个窗口写死的宽高。所有子窗口会在控件完整构建后，先读取当前字体、CustomTkinter 控件和表格实际请求的尺寸，再决定首次打开大小：

- 以各功能窗口的推荐尺寸作为基础下限；
- 根据已经构建完成的组件 `winfo_reqwidth()` / `winfo_reqheight()` 自动扩大窗口；
- 在窗口第一次映射后再测量一次，只有组件实际需要更大空间时才进行一次扩展；
- 自动限制在当前显示器可用工作区内，避免窗口超出屏幕；
- 保留 v3.5.4 的稳定窗口生命周期，不增加 `grab_set()`、`focus_force()`、`-topmost`、Windows HWND 修改或 Map/Unmap 循环。

同时提高了各类窗口的推荐打开尺寸，包括新建项目、字段映射、大模型设置、模板库、单条 AI 元信息识别、Batch AI Meta Extraction、批量字段修改、AI-assisted Schema Design、使用说明和 About。这样在常见的 125%–225% Windows 显示缩放下，首次打开时能够给按钮、说明文字、选项卡、表格和底部操作区留出更充分的空间。

## v3.5.4 Windows 子窗口生命周期修复

v3.5.4 针对“子窗口第一次打开后闪现并自动隐藏，之后再次打开又立即消失”的问题更换了子窗口的底层窗口壳。软件内部仍然使用与 BFSU CiteLens 一致的 CustomTkinter 控件、配色、卡片、选项卡和表单样式，但 **Windows 子窗口本身改为标准 `tkinter.Toplevel`**。这样可以绕开 CustomTkinter 5.x 在 Windows 上对 `CTkToplevel` 标题栏进行刷新时内部执行 `withdraw/deiconify` 所造成的窗口生命周期干扰。

本版本的子窗口策略为：

- 子窗口先以原生 Tk Toplevel 在后台完整构建，再一次性居中显示；
- 使用标准 `transient(owner)` 关系，使子窗口保持在所属主窗口之上；
- 子窗口内部所有按钮、输入框、卡片、选项卡、滚动区等仍使用 CustomTkinter，视觉风格不变；
- 不再使用 `CTkToplevel`；
- 不使用持久 `grab_set()`、`focus_force()`、`-topmost`、Windows HWND owner 重写或 Map/Unmap 重复提升；
- 子窗口仍统一使用 BFSU MetadataLens 图标，并按照当前显示器工作区居中。

## v3.5.3 子窗口稳定性修复

v3.5.3 针对 v3.5.2 中出现的“点击新建、设置等入口后，子窗口快速反复出现/隐藏”的严重回归问题重新简化窗口管理。

本版本不再使用 Windows 原生 HWND owner 修改、`SetWindowPos` / `ShowWindow` 层级干预、子窗口 `<Map>` 事件重复提升，也不再给子窗口设置 `wm transient`。子窗口现在只执行一次标准 Tk/CustomTkinter 显示流程：居中 → 显示 → 图标应用 → 普通 `lift()` → `focus_set()`。之后窗口层级交由 Windows 正常管理。

同时继续保持：

- 不使用持久 `grab_set()`，避免隐藏子窗口锁死主窗口；
- 不使用 `focus_force()`；
- 不使用 `-topmost`；
- 不在 `<Map>` / `<Unmap>` 事件中反复 `deiconify()` 或提升窗口；
- 不对 Windows 原生窗口 owner 做动态重写；
- 子窗口图标仍统一使用 BFSU MetadataLens 当前图标；
- 主窗口和子窗口仍按当前显示器工作区居中并限制在可见范围内。

该修复只涉及窗口生命周期与显示逻辑，不改变项目 XML、Schema、记录、模板、用户设置或大模型数据格式。

---

## v3.5.2 子窗口显示与 Windows 层级修复

v3.5.2 针对“新建、设置等子窗口闪现后立即落到主窗口后方，只有最小化再恢复后才能看到”的问题重新处理了 Windows 原生窗口所有权和 z-order。

本版本的窗口行为：

- 应用自建子窗口仍然**不使用持久 `grab_set()`**，因此隐藏窗口不会锁死主窗口；
- 不再通过 `-topmost` 开/关制造短暂置顶，因为 Windows 在解除 TOPMOST 时可能把窗口异步插入到主窗口后方；
- 子窗口映射后重新建立 Windows 原生 owner 关系，使其作为主窗口的 owned window 保持在主窗口之上；
- 用户点击“新建”“设置”“AI-assisted Schema Design”等入口时，子窗口会获得一次正常的前台激活；之后仅做不抢焦点的 z-order 校正；
- 新窗口映射后的 45 ms、140 ms 和 320 ms 会短暂复核原生所有权与层级，以覆盖 CustomTkinter 在高 DPI 环境下延迟创建最终 HWND 的情况；
- Win+D、任务栏最小化和恢复仍然不会留下 Tk grab，已打开的子窗口可以随主窗口正常恢复。

项目、Schema、记录、模板、用户设置和大模型数据格式均未改变。

---

# 中文说明

## 1. 软件简介

BFSU MetadataLens 用于解决语料库项目中常见的元信息工作问题：

- 先建立统一、可校验的元信息规范；
- 再根据规范录入具体记录；
- 批量导入已有 Excel/XML 元信息；
- 批量修改记录中的某个字段；
- 使用大模型辅助从文档、PDF、图片、网页或文本中识别元信息；
- 对大模型结果进行人工复核后再写入；
- 将项目统一保存为 UTF-8 XML；
- 导出 XML、Excel、CSV 或独立 Schema XML。

软件第一次启动时默认使用 **English**。可在菜单 **Language** 中切换为中文。之后软件会记住当前系统用户选择的界面语言。

---

## 2. 主要功能

### 2.1 元信息规范设计

每个字段可设置：

- Field ID；
- 中文名称；
- 英文名称；
- XML 标签；
- 数据类型；
- 元信息层级；
- 父级；
- 顺序；
- 必填；
- 可重复；
- 显示；
- 可编辑；
- 敏感字段；
- 默认值；
- 受控词表；
- 正则校验规则；
- 示例；
- 中文说明；
- 英文说明。

字段编辑区域会根据数据类型、示例、校验规则和可重复属性显示格式提示。

### 2.2 系统模板与用户模板

内置系统模板：

- Monolingual；
- Bilingual Parallel；
- Multilingual Parallel；
- Multiple Translations；
- Comparable；
- Learner；
- Spoken。

系统模板保存在：

```text
templates/system/
```

系统模板为只读模板。使用系统模板创建项目时，软件把模板复制到项目内部，因此项目中的修改不会改变系统模板。

在“元信息规范设计 → 模板库”中，选中任意系统模板或用户模板后，可点击 **“导入所选模板规范”**，把该模板的 Schema 复制到当前项目并替换当前规范。已有记录不会被删除，但新规范中不存在的旧字段值可能成为未定义字段，因此有已有数据时建议先保存项目。

当前 Schema 的 **规范名称和规范版本可以直接修改**。即使项目最初来自系统模板，或者后来删除并重新设计了字段，也可以在“元信息规范设计”顶部重新命名规范。

用户模板保存在当前操作系统用户的配置目录中，与软件目录分离。

Windows 默认位置：

```text
%APPDATA%\BFSU_MetadataLens\templates\user\
```

### 2.3 元信息条目录入

“条目录入”根据当前 Schema 自动生成表单。

支持：

- 新建记录；
- 编辑记录；
- 保存当前记录；
- 上一条 / 下一条；
- 当前记录校验；
- 大模型识别当前记录。

点击“保存当前记录”后按钮会显示“已保存”。如果再次修改任意字段，按钮恢复为“保存当前记录”。

### 2.4 记录总表

支持：

- 全字段搜索；
- 排序；
- 多选；
- 编辑；
- 复制；
- 删除；
- 校验；
- 双击进入条目录入；
- 批量修改字段。

### 2.5 批量修改字段

可以对：

- 当前选中的记录；
- 全部记录；

执行：

- 设置 / 替换；
- 追加；
- 清空。

应用前可预览结果。

### 2.6 Excel 导入

Excel 第一行作为列名。

软件会尝试根据以下信息匹配当前 Schema：

- field_id；
- XML 标签；
- 中文名称；
- 英文名称。

导入前可检查字段映射，并决定是否把未知列加入当前 Schema。

### 2.7 XML 导入

支持：

- MetadataLens 完整项目 XML；
- records XML；
- 一般 XML 文档。

软件会扫描 XML 标签并显示字段映射。

### 2.8 导出

可导出：

- Records XML；
- Excel；
- CSV；
- Schema XML。

---

## 3. 推荐工作流程

### 第一步：新建项目

选择：

```text
文件 → 新建项目
```

或点击顶部“新建”。

填写项目名称，然后选择：

- 系统默认模板；
- 用户模板；
- 空白规范。

### 第二步：检查元信息规范

进入：

```text
元信息规范设计
```

逐项检查字段。

建议先确认：

- Field ID 是否稳定；
- XML 标签是否正确；
- 数据类型是否正确；
- 必填字段是否合理；
- 可重复字段是否合理；
- 受控词表是否完整；
- 日期、年份、语言代码是否需要格式限制；
- 字段说明和示例是否足够清楚。

完成后执行：

```text
校验当前规范
```

### 第三步：录入或导入元信息

如果数据量少，可在“条目录入”逐条填写。

如果已有 Excel/XML 元信息，建议批量导入。

### 第四步：检查记录

进入“记录总表”：

- 抽查记录；
- 搜索缺失或异常内容；
- 按字段排序；
- 批量修改统一字段。

### 第五步：可选使用大模型

可以：

- 对当前记录识别元信息；
- 批量识别新的元信息记录；
- 辅助生成或扩展 Schema。

所有识别结果均应人工复核后应用。

### 第六步：校验、保存和导出

完成后：

- 校验 Schema；
- 校验记录；
- 保存项目 XML；
- 按需要导出 XML、Excel、CSV 或 Schema XML。

---

## 4. 元信息规范设计详细说明

### 4.1 Field ID

Field ID 是字段在项目内部的稳定标识。

建议：

```text
text_id
title
author
publication_year
language
translator
source_file
```

不建议频繁修改已经投入使用的 Field ID。

### 4.2 XML Tag

XML Tag 用于 XML 输出。

通常可以与 Field ID 相同。

### 4.3 数据类型

支持：

| 数据类型 | 用途 |
|---|---|
| string | 普通文本 |
| integer | 整数 |
| float | 小数 |
| date | 日期 |
| year | 四位年份 |
| boolean | 是/否 |
| enum | 受控词表 |
| long_text | 长文本 |
| language_code | 语言代码 |
| file_path | 文件路径 |

### 4.4 元信息层级

支持：

```text
corpus
subcorpus
text
version
file
speaker
segment
alignment
relation
project
```

### 4.5 必填字段

必填字段在录入界面显示 `*`。

项目导出前建议对必填字段进行校验。

### 4.6 可重复字段

例如作者、译者、多语种标签等可以设为可重复。

手工录入时多个值可用分号分隔：

```text
Author A; Author B
```

### 4.7 受控词表

对于固定分类建议使用 enum，例如：

```text
fiction; news; academic; legal; educational; other
```

### 4.8 校验规则

支持正则表达式。

例如四位年份：

```text
\d{4}
```

---

## 5. 条目录入详细说明

### 5.1 新建记录

点击：

```text
新建记录
```

软件根据当前 Schema 生成字段表单。

### 5.2 保存状态

未保存时：

```text
保存当前记录
```

保存后：

```text
已保存
```

只要再次修改字段，按钮恢复为“保存当前记录”。

### 5.3 校验当前记录

点击“校验当前记录”检查：

- 必填字段；
- 数据类型；
- 受控词表；
- 日期和年份；
- 正则规则。

---

## 6. 大模型接口

支持：

- OpenAI；
- DeepSeek；
- 千问 / Qwen；
- Claude；
- Gemini。

默认模型以低成本、高效率的结构化元信息任务为目标预设，用户可以自行修改模型名称。

---

## 7. API Key 本地保存规则

API Key 不保存在软件目录，也不保存在项目 XML。

普通设置：

```text
%APPDATA%\BFSU_MetadataLens\settings.json
```

API Key 单独保存：

```text
%APPDATA%\BFSU_MetadataLens\credentials.json
```

因此：

- 复制软件安装目录不会复制 Key；
- 压缩软件目录不会包含 Key；
- 项目 XML 不包含 Key；
- 用户模板不包含 Key；
- 把项目发给他人不会泄露 Key。

“大模型设置”提供：

```text
删除所有 Key
```

用于一次删除本机当前用户保存的全部服务商 API Key。

v3.2 及更早版本如果曾把 Key 写入本地 `settings.json`，v3.3 第一次读取时会自动迁移到 `credentials.json`，并重写 `settings.json`，移除其中的 Key。

---

## 8. 单条大模型识别元信息

识别请求会参考：

- 当前项目 ID；
- 当前项目名称；
- 语料库类型；
- 当前 Schema ID；
- Schema 名称；
- Schema 版本；
- Schema 完整字段；
- 当前记录已有字段；
- 用户选择的参考来源。

模型只允许返回当前 Schema 已存在的字段。

支持参考来源：

- `.txt`；
- `.md`；
- `.csv`；
- `.tsv`；
- `.json`；
- `.xml`；
- `.html` / `.htm`；
- `.pdf`；
- `.jpg` / `.jpeg`；
- `.png`；
- `.webp`；
- `.bmp`；
- `.gif`；
- `.tif` / `.tiff`；
- 网页 URL；
- 粘贴文本。

识别后显示：

- 当前值；
- 建议值；
- 置信度；
- 依据。

用户可以应用选中字段或全部建议。

处理期间：

- Start 按钮冻结；
- 显示处理状态；
- 可以点击 Stop；
- API、网络、额度、模型或返回格式错误会显示提示。

---

## 9. 批量大模型识别新增元信息

v3.3 起，批量识别的默认用途是 **创建新的元信息记录**；v3.4 在此基础上增加了 URL 列表批量导入。

不需要提前建立空记录，也不会把参考来源与当前项目中已有记录进行自动匹配。

### 操作方法

**方式 A：批量添加本地文件**

1. 打开“AI 批量识别”；
2. 点击“批量添加参考文件”；
3. 每个文件默认对应一条待新增记录。

**方式 B：从文本导入 URL 列表**

1. 准备 TXT、MD、CSV 或 TSV 文件；
2. 文本可以每行一个 URL，也可以在普通文本中包含多个 URL；
3. 点击“从文本导入 URL 列表”；
4. 软件会提取唯一的 `http://` / `https://` 地址；
5. 每个 URL 默认对应一条待新增记录。

然后：

1. 点击“开始批量识别”；
2. 左侧查看每个文件或 URL 的状态；
3. 右侧逐字段人工复核；
4. 可以只应用当前记录的选中字段；
5. 可以应用当前记录全部建议；
6. 可以确认后“一键应用全部新增记录”。

在用户点击应用之前，结果不会写入当前项目。单个来源失败不会阻止其它成功结果继续复核和应用。

---

## 10. 大模型辅助 Schema 设计

支持：

- Generate New Schema；
- Extend Current Schema。

用户应填写：

- 语料库类型；
- 研究目的；
- 元信息层级；
- 希望记录的信息；
- 是否有翻译版本；
- 是否涉及说话人；
- 是否涉及学习者；
- 是否涉及对齐关系；
- 受控词表要求；
- 可选参考材料。

AI 结果不会直接修改 Schema，而是先显示候选字段供人工检查。

---

## 11. 错误提示

大模型接口会针对常见问题给出提示，包括：

- API Key 无效；
- 权限不足；
- 模型名称错误；
- Base URL 错误；
- 额度不足；
- 请求频率过高；
- 网络连接失败；
- 请求超时；
- 服务商 5xx 错误；
- 返回内容不是有效 JSON。

---

## 12. 项目文件

项目统一保存为 UTF-8 XML。

基本结构：

```xml
<metadata_project>
    <project_info>...</project_info>
    <schema>...</schema>
    <records>...</records>
    <relations>...</relations>
</metadata_project>
```

覆盖已有项目文件前会自动创建备份。

---

## 13. 安装

建议 Python 3.10+。

```bash
python -m pip install -r requirements.txt
```

---

## 14. 运行

```bash
python main.py
```

依赖和模板检查：

```bash
python main.py --check
```

---

## 15. Windows 打包

可运行：

```cmd
build_windows.bat
```

或使用项目中的：

```text
BFSU_MetadataLens.spec
```

打包后的应用目录不会包含 `%APPDATA%\BFSU_MetadataLens\credentials.json`，因此不会携带当前用户 API Key。

---

## 16. 项目目录

```text
BFSU_MetadataLens/
├─ main.py
├─ requirements.txt
├─ README.md
├─ RELEASE_NOTES.md
├─ BFSU_MetadataLens.spec
├─ build_windows.bat
├─ assets/
│  ├─ app.png
│  ├─ app_2048.png
│  └─ app.ico
├─ templates/
│  └─ system/
├─ metadatalens/
│  ├─ app.py
│  ├─ config.py
│  ├─ i18n.py
│  ├─ llm.py
│  ├─ models.py
│  ├─ repository.py
│  ├─ schema_manager.py
│  ├─ excel_io.py
│  ├─ xml_io.py
│  ├─ templates.py
│  ├─ validators.py
│  ├─ utils.py
│  └─ ui/
└─ tests/
```

---

## 17. 软件作者、开发贡献与相关信息

### 17.1 软件作者

**刘鼎甲 博士 / Dr. Dingjia LIU**  
北京外国语大学 / Beijing Foreign Studies University  
Email: djliu@bfsu.edu.cn

BFSU MetadataLens 由软件作者发起、总体设计并主导开发。软件作者负责确定软件定位、核心功能、总体架构、元信息 Schema 工作流、项目 XML 数据组织、模板体系、大模型辅助流程和主要交互逻辑，并直接参与和完成关键代码的开发、功能集成、测试、修订与版本发布。软件的功能取舍、技术判断、质量控制和最终责任均由软件作者承担。

### 17.2 ChatGPT 5.5 在开发中的角色

ChatGPT 5.5 在软件开发过程中作为 **AI 辅助开发工具**参与，主要用于部分代码草拟、重构建议、问题排查、界面与文档文字整理以及迭代辅助。ChatGPT 5.5 的角色是辅助性的，不替代软件作者对软件的总体设计、关键代码开发、技术决策、测试确认和最终审核。

### 17.3 北外语料库团队与 BFSUNLP

- 北外语料库团队主页：https://corpus.bfsu.edu.cn/index.htm
- BFSUNLP GitHub：https://github.com/bfsunlp
- BFSU LexiScope GitHub：https://github.com/bfsunlp/bfsu_lexiscope
- BFSU LexiScope 主页：https://corpus.bfsu.edu.cn/index.htm

Copyright © 2026 Dingjia LIU. All rights reserved.

---


## v3.5.5 adaptive child-window sizing

v3.5.5 keeps the stable native `tkinter.Toplevel` shell introduced in v3.5.4 and addresses a different issue: at high Windows display scaling, child windows could open too small for the scaled CustomTkinter controls, causing labels, buttons, tabs, tables, and footer actions to crowd or clip.

Dialog sizing is now content-aware. After a dialog has been fully built, MetadataLens measures the requested size of the actual widget tree and enlarges the first-open geometry when needed. It measures once more after the native shell is mapped, expanding only if late CTk layout finalization requires additional space. The result is then constrained to the current monitor work area so the window remains visible.

Recommended baseline sizes were also increased for New Project, Mapping, Provider Settings, Template Library, single-record AI extraction, Batch AI Meta Extraction, Batch Field Edit, AI-assisted Schema Design, User Guide, and About. The v3.5.4 lifecycle safeguards remain unchanged: no persistent grab, forced focus, topmost pulse, native HWND rewriting, or Map/Unmap restore loop is introduced.

## v3.5.4 Windows child-window lifecycle fix

v3.5.4 changed the operating-system shell used for every MetadataLens child window. Application dialogs use standard `tkinter.Toplevel` shells while retaining CustomTkinter for all visible controls. Dialogs are built while hidden, centred, shown once, and attached to their owner with the standard Tk `transient` relationship. Persistent grabs, forced focus, topmost pulses, native HWND rewriting, and Map/Unmap re-raising remain disabled.

## v3.5.3 child-window stability fix

v3.5.3 fixes the serious regression in v3.5.2 where clicking **New Project**, **Provider Settings**, or other child-window commands could make a dialog repeatedly appear and disappear in a rapid loop.

The window manager has been deliberately simplified. MetadataLens no longer rewrites native Windows HWND ownership, calls `SetWindowPos` / `ShowWindow` for dialog z-order, raises a dialog from its `<Map>` event, or assigns `wm transient` to application-created child windows. A child now follows one standard Tk/CustomTkinter presentation sequence: centre → show → apply icon → ordinary `lift()` → `focus_set()`. Windows manages the window normally after that point.

The application still:

- uses no persistent `grab_set()`;
- uses no `focus_force()`;
- uses no `-topmost`;
- performs no repeated `deiconify()` or raise operation from `<Map>` / `<Unmap>` callbacks;
- does not dynamically rewrite native Windows owners;
- applies the current BFSU MetadataLens icon to child windows;
- keeps main and child windows centred and within the visible monitor work area.

This change affects only window presentation/lifecycle behavior. Project XML, schemas, records, templates, user settings and LLM data formats are unchanged.

---

## v3.5.2 child-window z-order fix

v3.5.2 addresses the Windows issue where dialogs such as **New Project** or **Provider Settings** could flash briefly and then fall behind the main window until the whole application was minimized and restored.

The revised window behavior is:

- application-owned dialogs still **do not use persistent `grab_set()`**, so an unreachable child cannot freeze the owner;
- MetadataLens no longer toggles `-topmost`, because removing TOPMOST can asynchronously place a Tk/CustomTkinter window underneath its owner on some Windows systems;
- after a dialog is mapped, MetadataLens reinforces the native Windows owner relationship so the dialog behaves as an owned window above the main window;
- a newly opened dialog receives one normal foreground activation, followed only by non-activating z-order corrections;
- ownership/z-order is rechecked at 45 ms, 140 ms and 320 ms to cover delayed native HWND realization under high-DPI CustomTkinter;
- Win+D and taskbar minimize/restore continue to work without leaving a Tk grab behind.

Project, schema, record, template, user-setting and LLM data formats are unchanged.

---

# English Documentation

## 1. Overview

BFSU MetadataLens is designed for corpus projects that need a consistent metadata specification and a practical workflow for entering, importing, reviewing, validating and exporting metadata.

It supports:

- metadata schema design;
- manual record entry;
- Excel/XML import;
- batch field editing;
- optional LLM-assisted metadata extraction;
- human review before LLM results are applied;
- unified UTF-8 XML project storage;
- XML, Excel, CSV and Schema XML export.

The first launch uses **English** by default. Use the **Language** menu to switch to Chinese. The selected language is remembered for the current operating-system user.

---

## 2. Main capabilities

### 2.1 Metadata schema design

Each field can define:

- Field ID;
- Chinese label;
- English label;
- XML tag;
- data type;
- metadata level;
- parent;
- order;
- required flag;
- repeatable flag;
- visibility;
- editability;
- sensitive flag;
- default value;
- controlled vocabulary;
- regular-expression validation;
- example;
- Chinese description;
- English description.

Format hints are generated from field type, example, validation rule and repeatability.

### 2.2 System and user templates

Bundled system templates:

- Monolingual;
- Bilingual Parallel;
- Multilingual Parallel;
- Multiple Translations;
- Comparable;
- Learner;
- Spoken.

System templates are stored under:

```text
templates/system/
```

They are read-only. Creating a project from a system template copies the schema into the project, so project edits never modify the bundled template.

In **Metadata Schema Design → Template Library**, select any system or user template and click **Import Selected Template Schema** to copy that schema into the active project and replace the current schema. Existing records are not deleted, although values for fields absent from the new schema may become undefined; save the project first when it already contains data.

The active **Schema Name and Schema Version are editable** at the top of Metadata Schema Design. A schema can be renamed even when the project originally came from a system template or its fields were later deleted and rebuilt.

User templates are kept in the current user's configuration directory, separate from the application folder.

Windows default:

```text
%APPDATA%\BFSU_MetadataLens\templates\user\
```

### 2.3 Metadata Entry

Metadata Entry builds a form from the active schema and supports:

- New Record;
- editing;
- Save Current Record;
- Previous / Next;
- record validation;
- AI Metadata Extraction.

After a successful save, the button changes to **Saved**. Editing any value changes it back to **Save Current Record**.

### 2.4 Records Table

Supports:

- full-field search;
- sorting;
- multiple selection;
- editing;
- copying;
- deletion;
- validation;
- double-click to open Metadata Entry;
- batch field editing.

### 2.5 Batch field editing

Apply an operation to selected records or all records:

- Set / Replace;
- Append;
- Clear.

A preview is shown before the change is applied.

### 2.6 Excel import

The first row is used as headers. MetadataLens attempts to map headers to the active schema using:

- field_id;
- XML tag;
- Chinese label;
- English label.

Review the mapping before import and decide whether unknown columns should be added to the schema.

### 2.7 XML import

Supports:

- complete MetadataLens project XML;
- records XML;
- general XML documents.

XML tags are scanned and presented for field mapping.

### 2.8 Export

Available exports:

- Records XML;
- Excel;
- CSV;
- Schema XML.

---

## 3. Recommended workflow

1. Create a project.
2. Choose a system template, user template or blank schema.
3. Review Metadata Schema Design.
4. Enter records manually or import Excel/XML metadata.
5. Optionally use single-record or batch LLM extraction.
6. Review and batch-edit data in Records Table.
7. Validate the schema and records.
8. Save the project and export required formats.

---

## 4. Schema design details

### 4.1 Field ID

Use stable identifiers such as:

```text
text_id
title
author
publication_year
language
translator
source_file
```

Avoid changing Field IDs after a project has accumulated substantial data.

### 4.2 XML Tag

The XML tag is used for XML export and may normally match the Field ID.

### 4.3 Data types

| Type | Use |
|---|---|
| string | plain text |
| integer | integer values |
| float | numeric values with decimals |
| date | date |
| year | four-digit year |
| boolean | yes/no |
| enum | controlled vocabulary |
| long_text | longer text |
| language_code | language code |
| file_path | file path |

### 4.4 Metadata levels

```text
corpus
subcorpus
text
version
file
speaker
segment
alignment
relation
project
```

### 4.5 Required fields

Required fields are marked with `*` in Metadata Entry.

### 4.6 Repeatable fields

Multiple values may be separated with semicolons:

```text
Author A; Author B
```

### 4.7 Controlled vocabularies

Example:

```text
fiction; news; academic; legal; educational; other
```

### 4.8 Validation rules

Regular expressions are supported.

Four-digit year example:

```text
\d{4}
```

---

## 5. Manual metadata entry

Click **New Record** in Metadata Entry. The form is generated from the active schema.

Use **Validate Current Record** to check:

- required fields;
- data types;
- controlled vocabularies;
- date/year formats;
- regular-expression rules.

---

## 6. LLM providers

Supported providers:

- OpenAI;
- DeepSeek;
- Qwen;
- Claude;
- Gemini.

Default model names are selected for efficient structured metadata work and can be edited by the user.

---

## 7. API-key storage

API keys are not stored in the application folder and are not stored in project XML.

Ordinary settings:

```text
%APPDATA%\BFSU_MetadataLens\settings.json
```

API keys:

```text
%APPDATA%\BFSU_MetadataLens\credentials.json
```

Therefore:

- copying the installed application folder does not copy keys;
- zipping the application folder does not include keys;
- project XML does not contain keys;
- user templates do not contain keys;
- sending a project to another user does not disclose keys.

Provider Settings includes **Delete All Keys** to remove every locally stored provider key for the current user.

If v3.2 or earlier stored keys in local `settings.json`, v3.3 migrates them to `credentials.json` on first load and rewrites `settings.json` without keys.

---

## 8. Single-record AI metadata extraction

The extraction request is constrained by:

- current project ID;
- project name;
- corpus type;
- current Schema ID;
- Schema name;
- Schema version;
- complete active Schema fields;
- existing values in the current record;
- user-selected reference source.

The model may only propose fields that already exist in the active schema.

Supported sources include text files, XML/JSON/CSV, HTML, PDFs, images, webpages and pasted text.

Results show:

- current value;
- suggested value;
- confidence;
- evidence.

Start is disabled during processing, status is shown, Stop is available, and provider/network errors are reported.

---

## 9. Batch AI extraction for new metadata

Starting with v3.3, batch extraction creates **new metadata records by default**. v3.4 adds bulk import of webpage URLs from text files.

There is no requirement to create empty records first, and sources are not automatically matched against existing project records.

**Method A — local files**

1. Open Batch AI Extraction.
2. Click Add Reference Files.
3. Each file becomes one pending new record by default.

**Method B — URL list from text**

1. Prepare a TXT, MD, CSV or TSV file.
2. It may contain one URL per line or URLs embedded in ordinary text.
3. Click Import URL List from Text.
4. MetadataLens extracts unique `http://` / `https://` addresses.
5. Each URL becomes one pending new record by default.

Then:

1. Click Start Batch Extraction.
2. Review source status on the left.
3. Review field suggestions, confidence and evidence on the right.
4. Apply selected fields for the current record, or
5. Apply the complete current record, or
6. Confirm Apply All New Records.

Nothing is written to the project until an Apply action is used. A failed source does not prevent successful sources from being reviewed and applied.

---

## 10. AI-assisted schema design

Supports:

- Generate New Schema;
- Extend Current Schema.

Describe the corpus type, research goal, metadata levels, fields, vocabularies and any translation/speaker/learner/alignment requirements. Optional sample material may be supplied.

AI-generated fields are reviewed before application.

---

## 11. Error handling

Common LLM failures are reported, including:

- invalid API key;
- insufficient permission;
- invalid model name;
- incorrect Base URL;
- insufficient quota;
- rate limit;
- network failure;
- timeout;
- remote 5xx failure;
- invalid JSON response.

---

## 12. Project format

Projects are saved as UTF-8 XML:

```xml
<metadata_project>
    <project_info>...</project_info>
    <schema>...</schema>
    <records>...</records>
    <relations>...</relations>
</metadata_project>
```

Existing project files are automatically backed up before overwrite.

---

## 13. Installation

Python 3.10+ is recommended.

```bash
python -m pip install -r requirements.txt
```

---

## 14. Run

```bash
python main.py
```

Dependency/template check:

```bash
python main.py --check
```

---

## 15. Windows build

Run:

```cmd
build_windows.bat
```

or use:

```text
BFSU_MetadataLens.spec
```

The packaged application directory does not include `%APPDATA%\BFSU_MetadataLens\credentials.json`, so local API keys are not copied into the distribution.

---

## 16. Software author, development contribution and related resources

### 16.1 Software author

**Dr. Dingjia LIU / 刘鼎甲 博士**  
Beijing Foreign Studies University  
Email: djliu@bfsu.edu.cn

BFSU MetadataLens was initiated, architected and led by the software author. The author determined the product scope, core functions, overall architecture, metadata-schema workflow, project XML organization, template system, LLM-assisted workflow and principal interaction logic, and directly contributed to and implemented key code, feature integration, testing, revision and release work. Functional decisions, technical judgment, quality control and final responsibility remain with the software author.

### 16.2 Role of ChatGPT 5.5

ChatGPT 5.5 participated as an **AI-assisted development tool**. Its contribution mainly involved portions of code drafting, refactoring suggestions, debugging assistance, interface/document wording and iterative development support. Its role was assistive and did not replace the software author's overall design, key-code development, technical decisions, testing confirmation or final review.

### 16.3 BFSU Corpus Research Group and BFSUNLP

- BFSU Corpus Research Group: https://corpus.bfsu.edu.cn/index.htm
- BFSUNLP GitHub: https://github.com/bfsunlp
- BFSU LexiScope GitHub: https://github.com/bfsunlp/bfsu_lexiscope
- BFSU LexiScope homepage: https://corpus.bfsu.edu.cn/index.htm

Copyright © 2026 Dingjia LIU. All rights reserved.
