# BFSU ClearLens

中文名称：**BFSU 文本整理器**  
版本：**1.4.2**

BFSU ClearLens 是 BFSU LexiScope 框架下的批量文本整理、确定性降噪、编码转换与大模型辅助校对软件。软件只导入文本并输出文本，适用于 OCR 后文本、网页抓取后正文、语料采集结果和人工转写材料。

本软件**不执行 OCR、不抓取网页、不提取元信息**。这些任务由 LexiScope 中的其它工具承担。

## 发布版下载

通过百度网盘分享的文件：`BFSU_ClearLens.zip`  
下载链接：[https://pan.baidu.com/s/1Z-H233twN7OT57nKOs_aDQ](https://pan.baidu.com/s/1Z-H233twN7OT57nKOs_aDQ)  
提取码：`7h2n`  
分享来源：百度网盘超级会员 v9

## 主要功能

### 文件与批处理

- 导入单个或多个文本文件
- 递归导入文件夹
- 将文件或文件夹拖放到文件队列
- 多选删除、清空列表、右键菜单和快捷键
- 只整理当前选中文件，或批量整理全部文件
- 异步导入、可取消任务、进度显示和多进程/多线程批处理
- 默认并行任务数为当前逻辑处理器数量的一半，可在设置中调整
- 保存、另存为、全部保存；输出目录与源文件目录隔离
- 合并选中文件、合并全部文件
- 保留导入文件夹结构，避免同名文件相互覆盖
- CSV / JSON 整理日志导出
- 工具栏实时显示当前文件与全部文件字符数；统计窗口提供字符、字母、数字、标点、符号、行、段落和 UTF-8 字节等指标
- 编辑器字号可通过工具栏、快捷键或设置窗口调整
- 每个可勾选功能面板均提供“全选”和“取消全选”
- 当前整理参数、自定义正则和大模型自然语言规则可保存为独立 JSON 整理方案，并可在同类任务中重新导入
- 所有规则、大模型、转码和人工编辑都以上一次处理后的当前文本为输入，依次叠加
- 处理结果先保留在内存中；仅“保存”“另存为”和“全部保存”写入结果文件
- 保存完成时给出明确提示，未保存状态会在文件队列中标示

### 操作历史

- 编辑菜单提供撤回、重做、当前文件恢复原文、选中文件恢复原文和全部文件恢复原文
- 规则整理、大模型整理、大模型校对建议、自然语言规则和人工编辑均进入统一历史
- 一次批处理作为一个历史项，可同时撤回或重做多个文件
- 最近保存 50 项操作，历史文本采用快速压缩，降低大文件的内存开销

### 确定性文本整理

- 换行符、BOM、Unicode 规范化
- 控制字符、零宽字符、双向控制字符、私用区字符处理
- Emoji 表情符号处理
- ftfy 乱码修复
- HTML 实体还原
- JavaScript、CSS、`noscript`、`template` 等网页代码块处理
- 行首空白、行尾空白、重复空格、制表符规范化
- 汉字间异常空格处理
- 全角转半角、半角转全角
- 繁体转简体、简体转繁体
- 中文标点与半角标点转换
- 空行删除、连续空行合并、文末换行补齐；能识别 `&nbsp;`、`<br>`、HTML 注释和嵌套空标签构成的占位空行
- 相邻重复行、全文重复行、重复段落处理
- 异常符号行、重复短页眉页脚、OCR 占位符处理
- 英文断行连字符修复、段内强制换行重排、段首缩进整理
- 多语言正则规则库、自定义规则、规则测试
- 人工查找替换和整理结果手动编辑

### 编码转换

转码命令与规则整理完全分离。转码不会触发文本降噪；命令先校验当前工作文本能否按目标编码严格写出并登记待保存编码，只有随后执行保存命令才生成文件。可选择：

- UTF-8 / UTF-8 with BOM
- GB18030 / GBK / Big5
- UTF-16 / UTF-16 LE / UTF-16 BE
- UTF-32 / UTF-32 LE / UTF-32 BE
- Shift-JIS / CP949 / CP1252 / Latin-1 / ASCII
- LF / CRLF / CR 换行格式

若自动检测对极短文本给出较低可信度，可在“工具”或文件队列右键菜单中选择“按指定编码重新读取当前文件”，再执行整理或转码。

### 大模型辅助

大模型功能默认关闭，可在“设置 > 大模型”中选择 OpenAI / ChatGPT 或 DeepSeek，并分别配置 API 密钥和模型。

| 命令 | 输入 | 处理方式 |
| --- | --- | --- |
| 大模型整理当前/全部文件 | 当前工作文本 | 大模型提出精确编辑操作，程序只自动执行通过安全校验的操作 |
| 大模型校对当前文件 | 当前工作文本 | 大模型提供建议，用户在独立窗口逐条或批量同意、拒绝 |
| 大模型自然语言规则安全整理 | 当前或选中文本 | 一次提交多条自定义需求，仅自动执行通过无损校验的编辑 |
| 大模型自然语言规则校对 | 当前文本 | 一次提交多条自定义需求，涉及词句的建议由用户逐条或批量决定 |
| 大模型生成正则规则 | 用户需求及可选的指定文件 | 返回 Python `re` 结构化规则，本机编译校验后由用户编辑确认 |

大模型校对窗口提供“同意”“拒绝”“全部同意”“全部拒绝”。每条建议均显示原文片段、建议片段、理由、状态和差异；无法在当前文本中精确定位的建议会标记为“无法定位”，不会强制应用。已同意的修改可通过编辑菜单的操作历史撤回。

大模型自动整理不是让模型自由重写全文。模型只能提出以下类型的操作：空白、段落、标点、完全重复片段删除和纯符号噪声删除。程序会再次检查原文片段、出现次数、字符序列和操作类型；任何可能改变词语、汉字、字母或数字的自动操作都会被拒绝。

涉及错字、词句或其它语义层面的修改只会进入“大模型校对建议”，不会自动写入，必须由用户逐条确认。这个设计把自动阶段的词汇性增删约束为零，同时保留人工审阅能力。模型输出本身仍不应被视为绝对正确，研究用途应保留原文和日志。

OpenAI 路径使用 Responses API 与 Structured Outputs；DeepSeek 路径使用兼容的 Chat Completions JSON 输出。两条路径都返回精确编辑列表，并经过相同的本地安全校验。默认模型分别为 `gpt-5.4-mini` 和 `deepseek-v4-flash`，均可在设置中修改。

API 密钥只在当前会话或本机用户设置文件中使用，可在大模型设置中单独清除。密钥不会写入整理方案，也不会随方案导出。

## 推荐流程

1. 导入文件或文件夹。
2. 在左侧选择确定性整理功能、正则规则和可选的大模型自然语言规则。
3. 需要复用参数时，在“设置”菜单保存或导入整理方案。
4. 点击“预览规则效果”，检查前后对照与差异视图。
5. 执行“规则整理当前文件”或“规则整理全部文件”。之后的每项规则、大模型或人工编辑都会继续作用于当前结果。
6. 对少量复杂文本执行大模型校对，或一次提交多条自然语言规则，再逐条或批量决定建议。
7. 需要纯编码转换时执行“准备转码”命令；转码状态同样可以继续叠加其它整理。
8. 确认结果后执行“保存”“另存为”或“全部保存”，再导出整理日志并保留原始文本。

## 安装与运行

推荐 Python 3.10 或更高版本。

```bash
python -m pip install -r requirements.txt
python main.py
```

Windows 也可以运行：

```text
run_clearlens.bat
```

OpenAI API 密钥可以在软件设置中输入，也可以使用环境变量：

```bat
set OPENAI_API_KEY=your_api_key
```

DeepSeek API 密钥也可以使用环境变量：

```bat
set DEEPSEEK_API_KEY=your_api_key
```

若不勾选“将 API 密钥保存在本机用户设置中”，密钥只在当前软件会话中使用。

## Windows 打包

```text
build_clearlens.bat
```

脚本只使用项目目录下的 `virtual_env`，并生成 PyInstaller `onedir` 发布目录：

```text
dist\BFSU_ClearLens\
  BFSU_ClearLens.exe
  _internal\                 Python 与第三方运行依赖
  assets\                    图标与图片
  config\                    默认设置与内置正则规则
  samples\                   示例文本
  README.md
  technical_readme.md
  RELEASE_NOTES.md
  requirements.txt
```

`assets`、`config`、`samples` 和文档均与 EXE 同级；不会作为应用资源写入 `_internal`。脚本完成后会检查上述目录和必要文件，缺失时构建失败。

## 快捷键

| 快捷键 | 功能 |
| --- | --- |
| `Ctrl+O` | 导入文件 |
| `Ctrl+Shift+O` | 导入文件夹 |
| `Delete` | 删除选中文件 |
| `Ctrl+P` | 预览规则效果 |
| `F5` | 规则整理当前文件 |
| `Ctrl+F5` | 规则整理全部文件 |
| `F6` | 大模型整理当前文件 |
| `Ctrl+F6` | 大模型整理全部文件 |
| `F7` | 大模型校对当前文件 |
| `Ctrl+S` | 保存 |
| `Ctrl+Shift+S` | 另存为 |
| `Ctrl+Alt+S` | 全部保存 |
| `Ctrl+Z` | 撤回最近一次文本操作 |
| `Ctrl+Y` / `Ctrl+Shift+Z` | 重做 |
| `Ctrl+-` / `Ctrl+=` | 减小 / 增大编辑器字号 |
| `Esc` | 中止当前任务 |
| `Ctrl+F` | 查找与替换 |

## 项目结构

```text
BFSU_ClearLens/
  main.py
  requirements.txt
  build_clearlens.bat
  run_clearlens.bat
  README.md
  technical_readme.md
  assets/
  config/
  clearlens/
  samples/
  tests/
```

## English Summary

**BFSU ClearLens** is the text organization and deterministic cleaning application in the BFSU LexiScope framework. Every rule, LLM, transcode, and manual edit uses the latest working text, while only explicit Save, Save As, or Save All commands write result files. It supports responsive batch import, parallel processing, encoding conversion, save/merge workflows, 50-step undo/redo history, Unicode and whitespace normalization, duplicate/noise handling, paragraph reflow, regex rules, LLM-generated regex proposals, reusable natural-language LLM rules, guarded LLM cleaning, and individual or bulk review decisions.

ClearLens imports text and exports text. It does not perform OCR, web crawling, or metadata extraction.

## 作者与免责声明

作者：**刘鼎甲 博士 / Dr. Liu Dingjia**  
邮箱：**djliu@bfsu.edu.cn**

本软件用于辅助语料整理，不能替代学术、编辑、法律、隐私或信息安全审查。用户须核对输出，确认有权处理及发送相关材料，妥善备份源文件并保护 API 密钥。第三方大模型服务的数据处理、费用和可用性以各服务商条款为准。
