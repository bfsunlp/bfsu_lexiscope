# BFSU WebLens Maintenance / 维护工具

These maintenance tools are included in both the source package and release packages.
这些维护工具同时包含在源码包和发布包中。

- `reset_user_settings`: remove only the persisted WebLens settings file. Downloaded browsers/drivers and corpus outputs are kept. / 仅删除 WebLens 用户设置，保留浏览器、Driver 与语料输出。
- `clear_web_components`: remove only WebLens-managed portable browsers, WebDrivers and WebLens-specific browser/driver caches. System Chrome/Edge and the shared Selenium cache are not touched. / 仅删除 WebLens 管理的便携浏览器、WebDriver 及 WebLens 专用缓存，不删除系统 Chrome/Edge，也不删除其他程序可能共用的 Selenium 全局缓存。
- `uninstall_weblens`: in a packaged release, remove WebLens application files after clearing WebLens state; user `output` and `content_downloads` folders are preserved. In a source checkout the source tree is never deleted. / 发布版中清理 WebLens 状态并移除程序文件，同时保留用户 `output` 与 `content_downloads`；源码模式下绝不会删除源码目录。

Windows: run the corresponding `.bat` file.  macOS: run the corresponding `.command` file.
Windows 运行相应 `.bat`；macOS 运行相应 `.command`。
