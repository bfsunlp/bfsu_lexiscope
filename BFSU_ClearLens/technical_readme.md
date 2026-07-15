# BFSU ClearLens Technical Notes

## Architecture

The application is a Python/Tkinter desktop program with six independent processing paths:

1. Deterministic rule preview and cleaning
2. Encoding-only conversion
3. Guarded LLM direct cleaning
4. LLM review suggestions with human approval
5. Guarded or review-only natural-language LLM rules
6. LLM-assisted regular-expression proposals with local validation

The main modules are:

| Module | Responsibility |
| --- | --- |
| `clearlens/app.py` | Main window, file queue, commands, background tasks, logs |
| `clearlens/cleaner.py` | Deterministic text transforms and regex execution |
| `clearlens/fileio.py` | Encoding detection, folder discovery, output paths and logs |
| `clearlens/ai_client.py` | OpenAI/DeepSeek structured edits and safety validation |
| `clearlens/history.py` | Compressed 50-operation multi-file undo/redo history |
| `clearlens/llm_rule_library.py` | Local natural-language rule persistence |
| `clearlens/profile.py` | Secret-free cleaning-profile import/export |
| `clearlens/statistics.py` | Text and character statistics |
| `clearlens/ui_settings.py` | Settings window |
| `clearlens/ui_statistics.py` | Current/selected/all statistics window |
| `clearlens/ui_ai_review.py` | One-by-one LLM suggestion review |
| `clearlens/ui_common.py` | Shared product icon handling for all windows |
| `clearlens/ui_llm_rules.py` | Natural-language LLM rule library and editor |
| `clearlens/ui_regex_generator.py` | Asynchronous LLM-assisted regex proposal dialog |
| `clearlens/workers.py` | Pickle-safe process-pool cleaning jobs |
| `clearlens/document_ops.py` | Deterministic merge operations |
| `clearlens/ui_dialogs.py` | Regex library and manual find/replace |
| `clearlens/i18n.py` | English, Simplified Chinese and Traditional Chinese UI text |

## Deterministic Pipeline

`clean_text()` receives immutable options and returns the cleaned text plus a `CleanResult`. Operations run in a fixed order so the same text, options, thresholds, and rules produce the same result.

Potentially destructive features are off by default, including global line deduplication, paragraph deduplication, private-use character removal, Emoji removal, web code-block removal, OCR placeholder removal, web boilerplate regex rules, script conversion, and punctuation conversion.

Blank-line detection decodes HTML entities for classification and treats non-breaking spaces, line-break tags, comments, empty tags, and nested empty tags as blank placeholders. The source text is otherwise unchanged unless the selected blank-line operation removes that line.

## Output and Collision Handling

Each imported folder is retained as a source root. When directory preservation is enabled, output paths use the source-relative path. When overwrite is disabled, an existing output gets a numbered filename instead of being replaced.

Processing and persistence have an explicit boundary. Rule cleaning, LLM operations, accepted review suggestions, manual edits, resets, and transcode preparation update only the in-memory `TextFile` working state. Choosing an output directory never writes a result. Disk output is limited to Save, Save As, Save All, and the separately confirmed merge command.

Each processing command snapshots `TextFile.active_text`, so later operations build on the latest completed result instead of reopening `original_text`. `original_text` remains immutable except when the user explicitly reopens the source with a chosen encoding. Undo, redo, and reset are the only commands that intentionally restore an earlier or imported state.

Encoding conversion uses strict encoding. A character that cannot be represented by the selected target encoding raises an error and is logged; the program does not silently replace it. A successful transcode command records the target encoding in memory, and the selected save command performs the actual byte encoding.

## LLM Safety Invariants

LLM direct cleaning returns a structured list of exact edits rather than a rewritten document. Every edit must identify an exact source fragment and its 1-based occurrence.

Automatic acceptance rules:

- `whitespace` and `paragraph`: the complete non-whitespace character sequence must remain identical.
- `punctuation`: the complete alphanumeric sequence must remain identical and in order.
- `delete_duplicate`: the exact fragment must occur at least twice and the replacement must be empty.
- `delete_symbol_noise`: the deleted fragment may not contain alphanumeric characters.
- Unknown, overlapping, stale, or lexical edits are rejected.

LLM review suggestions may contain lexical corrections, but they are never applied merely because the model proposed them. Every change requires an explicit individual or bulk acceptance action in the review window.

The review decision model supports accept, reject, accept all, and reject all. Bulk acceptance still resolves every suggestion against the current evolving text; stale fragments are marked and skipped. Single decisions create individual history entries, while Accept All emits one combined update. Rejected suggestions never change text.

Natural-language rules use the same two paths. Multiple enabled rules are numbered and sent together. Safe cleaning still accepts only operations that satisfy the direct-cleaning invariants; review mode may return broader suggestions, but each suggestion requires an explicit user action.

LLM-generated regular expressions are proposals, not executable free-form model output. The response is parsed into a fixed name/pattern/replacement/flags/description schema, compiled with Python `re`, and test-substituted against the optional selected sample before the normal regex editor opens. The user must inspect and save the rule before it joins the local library.

## API Integration

The OpenAI path uses `OpenAI().responses.parse()` with a Pydantic schema and `store=False`. The DeepSeek path uses the OpenAI-compatible endpoint at `https://api.deepseek.com`, requests JSON Object output, and validates the response against the same Pydantic schema. LLM calls remain sequential to respect API rate limits. Text length, provider-specific API-key presence, and enabled state are checked before each request path.

Provider responses never bypass the deterministic edit guards. Empty, refused, invalid JSON, truncated, stale, overlapping, unsupported, or lexically unsafe edits are rejected.

## Task Execution

File discovery, decoding, rule cleaning, transcoding, saving, merging, and LLM requests run outside the Tk main thread. Local rule cleaning can use a process pool; import, encoding, and file output use bounded thread pools. Every task carries an identity token, so cancellation immediately restores the interface and discards late events from stopped workers. Preview updates never rebuild the file tree, preventing recursive selection events.

Rule cleaning, direct LLM cleaning, natural-language LLM cleaning, suggestion application, transcode preparation, resets, and manual edits share one operation history. A batch stores one before/after snapshot containing every affected file, including its working-text marker, dirty state, target encoding, output path, and filename-suffix mode, so one undo or redo restores the whole batch. Snapshots are compressed and the history is capped at the most recent 50 operations. Import-list mutations and explicit re-decoding clear history because they change file identity or the authoritative source text.

Processing completion reports that results remain unsaved. Save, Save As, and Save All report completion only after the background write has finished. Failed and cancelled items are excluded from the saved-file count.

## Configuration

Bundled defaults and regex rules are read from `config/`. User settings, custom regex rules, and natural-language LLM rules are stored in separate JSON files under:

```text
%APPDATA%\BFSU_ClearLens
```

On non-Windows systems, the fallback is the current user's home directory.

OpenAI and DeepSeek keys are stored only in the local settings file when `remember_api_key` is enabled; otherwise they remain in process memory for the current session. Cleaning profiles include deterministic settings, custom regex rules, and natural-language LLM rules, but are recursively sanitized to remove API-key fields before writing.

## Window Identity

The main window and every `Toplevel` dialog use `apply_window_icon()` through a shared `IconToplevel` base. PNG icon data covers Tk-compatible platforms and the ICO resource covers native Windows title bars. The main icon is also registered as Tk's default icon for native child windows.

In a frozen onedir build, external resources are resolved from the executable directory first. The internal PyInstaller directory is a fallback only, so user-visible `assets/` and `config/` folders remain next to the EXE as documented.

## Windows Onedir Build

`build_clearlens.bat` creates and uses `virtual_env`, installs the declared requirements there, and invokes PyInstaller with explicit `--onedir --contents-directory _internal`. Python, extension modules, and third-party runtime packages remain in `_internal`.

The script does not use `--add-data` for application resources. After the executable is built, it copies `assets/`, `config/`, `samples/`, README, technical notes, release notes, and requirements into `dist/BFSU_ClearLens/` next to the EXE. A final layout check fails the build if any required root file or directory is missing. Source modules, tests, build caches, and `virtual_env` are not copied to the release directory.

## Verification

Run the test suite from the project root:

```bash
python -m unittest discover -s tests -v
```

Compile-check all Python modules:

```bash
python -m compileall -q .
```
