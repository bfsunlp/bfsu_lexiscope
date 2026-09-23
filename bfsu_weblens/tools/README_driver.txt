BFSU WebLens 3.1.2 - Browser and WebDriver management

Browser policy
--------------
Chrome:
- Default: WebLens-managed portable Chrome for Testing.
- WebLens first reuses a compatible portable Chrome already under its managed tools/browser tree.
- If portable Chrome is missing, WebLens can download the official Chrome for Testing ZIP, extract it automatically, detect the executable and configure the matching ChromeDriver.
- System-installed Chrome remains available as an explicit alternative, but is not the recommended default because its independent auto-update cycle can change browser/Driver compatibility.

Microsoft Edge:
- Default: system-installed Microsoft Edge.
- Microsoft does not publish an official portable Edge ZIP comparable to Chrome for Testing, so WebLens detects the installed Edge version and prepares a matching EdgeDriver.
- A manually supplied Edge executable is still supported and is version-checked before use.

One-click configuration
-----------------------
Settings > Browser & Selenium > One-click configure Chrome & Edge follows the recommended mixed policy:
- Chrome: WebLens portable Chrome for Testing + matching ChromeDriver.
- Edge: system-installed Microsoft Edge + matching EdgeDriver.

Independent Detect / Download-configure / Detect-update-driver / Browse controls remain available if one-click configuration is only partially successful.

Compatibility checks
--------------------
- Chrome 115+: ChromeDriver is resolved through official Chrome for Testing metadata. Browser and Driver major.minor.build must match.
- Microsoft Edge: EdgeDriver major.minor.build must match the selected Edge build.
- Browser and Driver versions are checked when paths are selected/saved and again before every automatic collection task.
- Windows x64, Intel macOS, Apple Silicon macOS and common Linux driver packages are selected according to the running platform.

Storage
-------
Source/portable Windows builds use the WebLens-managed tools tree when it is writable.
Frozen macOS builds keep writable managed browser/driver files under:
  ~/Library/Application Support/BFSU WebLens/tools
This avoids modifying the signed .app bundle.

WebLens does not ship a permanently fixed chromedriver.exe or msedgedriver.exe. Compatible Drivers are detected from configured paths/caches or downloaded for the selected browser version. Selenium Manager remains a final runtime fallback.

Manual collection
-----------------
WebLens 3.x Manual Collection does not require Selenium, a browser Driver, or the Browser & Selenium environment. Browser configuration applies to automatic collection and Selenium-based target-page downloading only.
