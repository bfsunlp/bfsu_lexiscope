# BFSU MetadataLens v3.5.5 Release Notes

## 中文

v3.5.5 重点优化所有子窗口的首次打开尺寸。v3.5.4 改用原生 `tkinter.Toplevel` 后，窗口生命周期已经稳定，但高 DPI/高缩放时 CustomTkinter 控件会按系统字体和缩放扩大，而原生 Toplevel 的固定几何尺寸不会自动按同样比例扩大，因此可能出现按钮、文字、选项卡、表格和底部操作区挤在一起或显示不全。

本版本的处理方式：

1. 子窗口在后台完成全部控件构建后，读取 `winfo_reqwidth()` / `winfo_reqheight()`；
2. 首次打开尺寸取“功能窗口推荐尺寸”和“实际组件请求尺寸”中的较大值，并增加安全边距；
3. 原生窗口第一次映射后再测量一次，只在确有需要时扩展一次；
4. 最终尺寸自动限制在当前显示器工作区内，避免超出屏幕；
5. 各类窗口的推荐基准尺寸同步提高；
6. 不改变 v3.5.4 的窗口生命周期策略，不重新引入 grab、topmost、强制焦点、HWND 修改或映射循环。

重点调整的窗口包括：新建项目、字段映射、大模型设置、模板库、单条 AI 识别、Batch AI Meta Extraction、批量字段修改、AI-assisted Schema Design、使用说明和 About。

## English

v3.5.5 makes every child window size itself to its actual contents at first open. After the move to native `tkinter.Toplevel` shells in v3.5.4, dialog lifecycle stability was improved, but high-DPI CustomTkinter widgets could request substantially more space than the old fixed Toplevel geometry. This caused controls and footer buttons to crowd or clip.

Dialogs are now measured after their widget trees are fully constructed. MetadataLens opens them at the larger of the recommended functional size and the measured requested size, with additional padding. A second one-time measurement after mapping accommodates controls that finalize late. The result is capped to the active monitor work area. Recommended baseline sizes have also been increased for all major dialogs.

The stable v3.5.4 lifecycle remains intact: there are still no persistent grabs, forced focus loops, topmost pulses, native HWND rewrites, or Map/Unmap restore loops.

---

## Historical: v3.5.3

## 中文

v3.5.3 修复 v3.5.2 中出现的严重子窗口回归问题：点击“新建项目”“大模型设置”“模板库”“AI-assisted Schema Design”等入口后，子窗口可能快速反复显示、隐藏或重新映射。

本次修复将子窗口管理恢复为更保守、可预测的 Tk/CustomTkinter 生命周期：

- 删除 Windows 原生 HWND owner 动态修改；
- 删除 `SetWindowPos`、`ShowWindow`、`BringWindowToTop` 和 `SetForegroundWindow` 等主动 z-order 干预；
- 删除子窗口 `<Map>` / `<Unmap>` 中的重复提升或重新显示逻辑；
- 应用自建子窗口不再设置 `wm transient`；
- 继续禁止持久 `grab_set()`、`focus_force()` 和 `-topmost`；
- 每个子窗口只执行一次“居中 → 显示 → 应用图标 → `lift()` → `focus_set()`”；
- 映射后只允许延迟重新应用图标，不再修改几何位置、owner、可见状态或层级；
- Windows 的 Win+D、最小化、恢复和前后层级由操作系统正常管理，避免应用自身再次触发窗口循环。

About 和 README 同步补充了软件作者、ChatGPT 5.5 在开发中的角色，以及北外语料库团队、BFSUNLP 和 BFSU LexiScope 的相关信息。文档明确说明：BFSU MetadataLens 由刘鼎甲博士发起、总体设计并主导开发，软件作者直接参与并完成关键代码开发、功能集成、测试和版本发布；ChatGPT 5.5 作为 AI 辅助开发工具参与部分代码草拟、重构建议、问题排查和文档整理，其角色为辅助性。

项目 XML、Schema、记录、模板、用户设置和大模型数据格式均未改变。

## English

v3.5.3 fixes the serious child-window regression introduced by the previous Windows z-order workaround. Commands such as **New Project**, **Provider Settings**, **Template Library**, and **AI-assisted Schema Design** could cause a dialog to enter a rapid show/hide/remap loop.

The dialog manager is now intentionally conservative and follows a predictable Tk/CustomTkinter lifecycle:

- native Windows HWND owner rewriting has been removed;
- `SetWindowPos`, `ShowWindow`, `BringWindowToTop`, and `SetForegroundWindow` dialog z-order intervention has been removed;
- child `<Map>` / `<Unmap>` callbacks no longer re-show or re-raise dialogs;
- application-created dialogs no longer use `wm transient`;
- persistent `grab_set()`, `focus_force()`, and `-topmost` remain prohibited;
- each child is presented once using centre → show → icon → `lift()` → `focus_set()`;
- the only delayed post-map action is icon reapplication, which does not modify geometry, ownership, visibility, or z-order;
- Win+D, taskbar minimize/restore, and normal window stacking are left to Windows instead of being reimplemented by the application.

About and README now also document the software author, the assistive role of ChatGPT 5.5, and information for the BFSU Corpus Research Group, BFSUNLP, and BFSU LexiScope. They explicitly state that BFSU MetadataLens was initiated, architected and led by Dr. Dingjia LIU, who directly contributed to and implemented key code, feature integration, testing and release work; ChatGPT 5.5 served as an AI-assisted development tool for portions of code drafting, refactoring suggestions, debugging and documentation support.

Project XML, schema, record, template, user-setting and LLM data formats are unchanged.

---

# BFSU MetadataLens v3.5.2 Release Notes

## 中文

v3.5.2 专门修复 Windows 下子窗口“闪现后立即隐藏到主窗口后方”的问题。该现象不是窗口被真正关闭，而是 CustomTkinter/Tk 子窗口完成本地 HWND 映射后，其 Windows z-order/owner 关系发生变化，所以最小化并恢复整个应用后窗口又会重新出现。

本版本修改：

1. 继续禁止应用自建窗口使用持久 `grab_set()`，保留 v3.5.0 对主窗口假死问题的修复。
2. 删除 v3.5.1 的 `-topmost` 脉冲。Windows 在从 TOPMOST 切回普通窗口时可能异步重排 z-order，这会造成“先显示、随后掉到主窗口后方”。
3. 新增 Windows 原生 HWND 解析，使用 `GetAncestor(..., GA_ROOT)` 获取真正参与窗口层级管理的顶层句柄。
4. 子窗口映射后，通过 `GWLP_HWNDPARENT` 重新确认 Windows 原生 owner，使子窗口成为主窗口的 owned window。
5. 使用 `SetWindowPos(HWND_TOP, ... SWP_NOACTIVATE)` 与 `BringWindowToTop` 做非 TOPMOST 层级修正，不让子窗口成为系统级永久置顶窗口。
6. 仅在用户主动打开新窗口时执行一次前台激活；后续 45/140/320 ms 的复核均不抢占系统焦点。
7. 移除 `wm_group`，避免它与 `transient`/Windows owner 同时存在时形成重复窗口分组关系。
8. 子窗口仍统一使用 MetadataLens 图标、居中和高 DPI 尺寸限制。
9. Win+D、任务栏最小化与恢复逻辑继续保留，并且不依赖 Tk grab。
10. 项目、Schema、记录、模板、用户设置与 LLM 数据格式保持完全兼容。

## English

v3.5.2 specifically fixes the Windows behavior where a CustomTkinter dialog briefly appears and then drops behind the main MetadataLens window. The dialog was not actually destroyed; its native z-order/ownership changed after the final HWND was realized, which is why minimizing and restoring the application made it visible again.

Changes:

1. Application-owned dialogs still do not use persistent `grab_set()`, preserving the v3.5.0 deadlock fix.
2. The v3.5.1 `-topmost` pulse is removed. Transitioning from TOPMOST back to a normal window can asynchronously reorder z-order on Windows.
3. MetadataLens now resolves the real top-level HWND using `GetAncestor(..., GA_ROOT)`.
4. After mapping, the dialog's native owner is reinforced through `GWLP_HWNDPARENT`, making it a true owned window of the main application.
5. `SetWindowPos(HWND_TOP, ... SWP_NOACTIVATE)` and `BringWindowToTop` are used for normal, non-TOPMOST z-order correction.
6. Foreground activation occurs only when the user explicitly opens the dialog. Follow-up checks at 45/140/320 ms do not steal focus.
7. `wm_group` is removed from dialog creation to avoid a second grouping relationship competing with `transient`/native ownership.
8. Dialog icon, centering and high-DPI size constraints remain unchanged.
9. Win+D/taskbar minimize and restore remain supported without relying on Tk grabs.
10. Project, schema, record, template, user-setting and LLM data formats remain fully compatible.
