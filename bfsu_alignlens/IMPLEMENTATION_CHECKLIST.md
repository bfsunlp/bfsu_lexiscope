# BFSU AlignLens V1.2.0 修正清单

本版本针对用户提出的 6 项问题完成如下修正：

1. **文件导入逻辑重做**
   - 菜单栏导入按钮改为打开独立导入窗口。
   - 先选择 1 对 1、一语多译、多语平行模式。
   - 确认模式后水平打开源语和译语/译本子窗口。
   - 每个子窗口独立导入文件、排序、拖拽、删除、上移、下移。
   - 确认后在主窗口 File Manager 中水平多栏显示。

2. **ProofLens 风格**
   - 新增 `app/theme.py`。
   - 应用红金色主题、深红表头、金色强调、浅色背景。

3. **View 语言设置**
   - 直接显示“简体中文 / 繁體中文 / English”等语言原名。
   - 不再在 View 菜单中显示简写。

4. **Alignment Editor 多栏编辑**
   - 替换原 Treeview 为 Canvas + Text 的多栏编辑器。
   - 行边界统一，按最长单元格自动拉高行高。
   - 每个单元格可单独编辑。
   - 支持单元格上移、下移、合并、拆分、清空，且不与其它栏目联动。

5. **Logo 风格**
   - 重新生成红金色 lens 风格图标。
   - 已输出 `assets/app.png` 和 `assets/app.ico`。

6. **Help 菜单**
   - 仅保留 About。
   - About 内容按 ProofLens 类似风格重写。

测试：

```text
python -m compileall -q .
PYTHONPATH=. pytest -q
4 passed
```
