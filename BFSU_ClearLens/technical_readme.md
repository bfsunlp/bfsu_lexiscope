# BFSU ClearLens Technical Notes

## Architecture

The application is a Python/CustomTkinter desktop program, with selected native Tk/ttk controls where Windows integration or large tabular data makes them appropriate. It has six independent processing paths:

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
| `clearlens/fileio.py` | Sample-bounded encoding detection, folder discovery, output paths and logs |
| `clearlens/ai_client.py` | OpenAI/DeepSeek task preflight, structured edits and safety validation |
| `clearlens/llm_chunks.py` | Lossless line-aware chunks, read-only overlap, source fingerprints, and exact fragment resolution |
| `clearlens/history.py` | Compressed 50-operation multi-file undo/redo history |
| `clearlens/llm_rule_library.py` | Local natural-language rule persistence |
| `clearlens/profile.py` | Secret-free cleaning-profile import/export |
| `clearlens/statistics.py` | Text and character statistics |
| `clearlens/ui_settings.py` | Settings window |
| `clearlens/ui_statistics.py` | Current/selected/all statistics window |
| `clearlens/ui_ai_review.py` | One-by-one LLM suggestion review |
| `clearlens/ui_text.py` | Line-number gutters, exact fragment-to-line mapping, line-difference rows |
| `clearlens/window.py` | CustomTkinter application root, theme bootstrap, and `tkinterdnd2` compatibility layer |
| `clearlens/ui_common.py` | Shared CTk controls, product icons, draggable splitters, and DPI-aware Treeview adapter |
| `clearlens/ui_llm_rules.py` | Natural-language LLM rule library and editor |
| `clearlens/ui_regex_generator.py` | Asynchronous LLM-assisted regex proposal dialog |
| `clearlens/workers.py` | Pickle-safe process-pool cleaning jobs |
| `clearlens/document_ops.py` | Deterministic merge operations |
| `clearlens/ui_dialogs.py` | Regex library, scaled encoding chooser, and manual find/replace |
| `clearlens/i18n.py` | English, Simplified Chinese and Traditional Chinese UI text |

## Deterministic Pipeline

`clean_text()` receives immutable options and returns the cleaned text plus a `CleanResult`. Operations run in a fixed order so the same text, options, thresholds, and rules produce the same result.

Potentially destructive features are off by default, including global line deduplication, paragraph deduplication, private-use character removal, Emoji removal, web code-block removal, OCR placeholder removal, web boilerplate regex rules, Unicode normalization, character-width conversion, script conversion, punctuation conversion, indentation conversion, and hyphenated-line repair. Every paragraph/glyph combo box has a separate enable checkbox; its displayed choice is ignored while the checkbox is clear.

Blank-line detection decodes HTML entities for classification and treats non-breaking spaces, line-break tags, comments, empty tags, and nested empty tags as blank placeholders. The source text is otherwise unchanged unless the selected blank-line operation removes that line.

Rule preview always preserves the exact `TextFile.active_text` snapshot as its left-side baseline, then runs the complete local/regex pipeline for the right side. It never substitutes a locally cleaned intermediate state merely because a regex rule is enabled. If natural-language LLM rules are selected, the preview command performs the normal preflight and send confirmation, applies those rules as ordered preview-only passes after the local pipeline, and displays the result without mutating `TextFile`. General LLM proofreading remains a suggestion workflow because it has no single result until the user accepts or rejects items.

## Output and Collision Handling

Each imported folder is retained as a source root. When directory preservation is enabled, output paths use the source-relative path. When overwrite is disabled, an existing output gets a numbered filename instead of being replaced.

Processing and persistence have an explicit boundary. Rule cleaning, LLM operations, accepted review suggestions, manual edits, resets, and transcode preparation update only the in-memory `TextFile` working state. Choosing an output directory never writes a result. Disk output is limited to Save, Save As, Save All, and the separately confirmed merge command.

Each processing command snapshots `TextFile.active_text`, so later operations build on the latest completed result instead of reopening `original_text`. `original_text` remains immutable except when the user explicitly reopens the source with a chosen encoding. Undo, redo, and reset are the only commands that intentionally restore an earlier or imported state.

Encoding conversion uses strict encoding. A character that cannot be represented by the selected target encoding raises an error and is logged; the program does not silently replace it. A successful transcode command records the target encoding in memory, and the selected save command performs the actual byte encoding.

## LLM Safety Invariants

LLM direct cleaning and review return a structured list of atomic exact edits rather than a rewritten document. Every independent issue is one item. The provider contract contains only the operation, 1-based line hints, exact source fragment, replacement, occurrence hint, reason, and confidence. Stable edit ids, request-chunk identity, the 16-character source fingerprint, authoritative lines, global occurrence, and absolute source offsets are application-owned fields. They are bound or recomputed only after the response is associated with the exact request that produced it.

Before an LLM request is created, `AIClient.assess_task()` rejects natural-language tasks that require translation, summarization, free rewriting, generation, external knowledge, OCR, crawling, metadata extraction, or more rules than the bounded edit format can safely carry. `preflight()` then validates enabled state, provider key, non-empty input, and a minimum safe chunk budget independently for every target file. A failed preflight is reported before any document is transmitted.

`build_document_chunks()` covers every source character exactly once with non-overlapping editable cores. Normal logical lines remain intact; an extreme minified HTML/JSON line is divided by character position without loss. Neighboring chunks may repeat a small amount of read-only context, capped by both line count and characters. Each prompt exposes visible lines plus the editable core's start/end line and column; this disambiguates several chunks that all belong to one extreme logical line. An item is owned only by the chunk whose editable core contains its starting character, preventing overlap duplicates. The model is instructed to return only changed fragments, preferably one line and one correction per item; multiple lines are allowed only for one indivisible paragraph or line-break issue. `locate_chunk_fragment_candidates()` then searches the exact provider fragment only within the request's visible text and retains only starts owned by its editable core.

Automatic acceptance rules:

- `whitespace` and `paragraph`: the complete non-whitespace character sequence must remain identical.
- `punctuation`: the complete alphanumeric sequence must remain identical and in order.
- `delete_duplicate`: the exact fragment must occur at least twice and the replacement must be empty.
- `delete_symbol_noise`: the deleted fragment may not contain alphanumeric characters.
- A custom-rule `case_conversion` must preserve the casefolded alphanumeric sequence and every non-letter character.
- Custom lexical replace/delete/anchored-insert/composite edits require an exact quoted transformation extracted from the active user rule.
- Unknown, overlapping, stale, unanchored, or semantically unverifiable lexical edits are rejected from automatic mode.

LLM review suggestions may contain lexical corrections, but they are never applied merely because the model proposed them. Every change requires an explicit individual or bulk acceptance action in the review window. The suggestion table maps exact fragments to one or more logical line numbers in the latest working text. Double-click and Return navigate to and highlight those lines in the main current-result editor; neither gesture accepts an edit.

The review decision model supports accept, reject, accept all, and reject all. Bulk acceptance still resolves every suggestion against the current evolving text; stale fragments are marked and skipped. The complete review session is committed as one history entry when the window closes, so several accepted suggestions are undone together. Rejected suggestions never change text.

Natural-language rules use the same two provider paths, but a multi-rule user action is executed as independent ordered passes. Automatic mode feeds each completed pass into the next rule and remains transactional at file scope: if any later rule fails, the original task input is returned and no partial multi-rule result reaches `TextFile`. Review mode runs every rule independently against the same current working text, then deduplicates suggestions by resolved source span and replacement. This prevents provider list-following failures and prevents a deterministic scope check for one rule from rejecting valid edits belonging to another rule.

Each active rule is the complete and exclusive task specification for its pass; the prompt does not add generic residual-noise review. If a rule does not authorize deletion, empty replacements and deletion/noise operations are rejected locally. The common “all-uppercase words to initial-capital words” request has an additional deterministic scope check requiring the replacement to equal the exact capitalization transform. The schema and adapter recognize case conversion, bounded replacement, anchored insertion, deletion, reordering, and indivisible composite edits in addition to the original lossless categories. Automatic mode applies case-only changes only when casefolded content and all non-letter characters are preserved. Lexical replace/delete/insert/composite operations are auto-applied only when the user rule contains an explicit quoted source/target or anchor transformation that matches the returned edit exactly; broader operations remain human-review suggestions.

LLM-generated regular expressions are proposals, not executable free-form model output. The response is parsed into a fixed name/pattern/replacement/flags/description schema, compiled with Python `re`, and test-substituted against the optional selected sample before the normal regex editor opens. The user must inspect and save the rule before it joins the local library.

## API Integration

The OpenAI path uses `OpenAI().responses.parse()` with the minimal `AIProviderEditBatch` Pydantic schema and `store=False`. The DeepSeek path uses the OpenAI-compatible endpoint at `https://api.deepseek.com` and first forces a `submit_atomic_edits` function tool whose equally minimal JSON Schema is marked `strict: true`. Neither provider is asked to generate chunk ids, hashes, or stable edit ids. If the DeepSeek endpoint explicitly rejects strict tools with a compatibility-class 400/404/422 response, ClearLens retries that chunk with DeepSeek's documented JSON Object mode and caches the unsupported capability for the life of the batch client; later chunks go directly to JSON mode. Batch commands snapshot each target's current working text, keep documents separate, and process files sequentially. Each file makes one sequential request per line-aware chunk; no request combines files. Task suitability, provider-specific API-key presence, enabled state, non-empty text, and chunk budget are checked before work begins and again in the request path.

DeepSeek JSON Object mode guarantees syntactically valid JSON but does not itself guarantee application-schema conformance. Its fallback adapter therefore strips an optional JSON code fence; accepts `edits`, `changes`, `suggestions`, `operations`, or `items` roots; maps snake-case, camel-case, `before/after/op`, and other common field aliases; converts safe numeric strings; and expands a single `line` into equal start/end hints. Provider verbs such as `replace`, `edit`, `spacing`, `line_break`, `capitalize`, `transform_case`, `insert`, and `remove` are canonicalized from both the label and exact before/after fragments. Multi-level line/item containers with nested edit dictionaries are recursively expanded into independent children; a string operation list becomes one composite category. In the live request path, each valid content item receives the current request's real chunk id and fingerprint plus a locally generated edit id before `AIEditModel` validation. A malformed item is discarded without suppressing valid siblings. Missing replacement text is inferred as empty only when the provider explicitly labels the operation as deletion; a malformed replacement is never converted into deletion implicitly.

The stable task protocol and schema are placed before the variable document chunk, which makes eligible repeated prefixes compatible with provider prompt caching. Only problematic items are returned, minimizing output traffic. ClearLens does not summarize or perform model-generated token deletion on text before proofreading: complete evidence coverage is preferred because a rare fragment removed by compression may be the error being sought.

Provider responses never bypass local validation. A response is first bound to the exact request chunk. If an exact original fragment has one editable-core occurrence, ClearLens accepts that source identity and recomputes authoritative lines and occurrence even when provider metadata is wrong. If several occurrences exist, valid global line hints or the common visible-block-local line convention must select exactly one; otherwise the item is rejected as ambiguous. Absent source fragments, read-only-overlap-only edits, duplicate edits, stale fragments, unsupported operations, and lexically unsafe edits remain rejected. One failed chunk causes fail-closed behavior for that file: automatic mode applies none of its partial chunk results. Valid direct edits are applied in reverse absolute-offset order. Review suggestions retain stable source offsets, and later offsets are adjusted after each accepted change. If the target working text changes while a review request is in flight, the response is not opened against the newer state.

## LLM Design Basis

- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) motivates schema-constrained responses; [Prompt Caching](https://developers.openai.com/api/docs/guides/prompt-caching) motivates the repeated static prefix followed by variable text. Caching eligibility is provider-controlled and does not remove the need to transmit or validate the request.
- DeepSeek's [JSON Output guide](https://api-docs.deepseek.com/guides/json_mode/) documents JSON Object mode, its prompt requirement, truncation risk, and occasional empty content. The current [Chat Completion reference](https://api-docs.deepseek.com/api/create-chat-completion) documents strict JSON-Schema function tools. ClearLens combines strict tools with a validated JSON fallback instead of assuming valid JSON equals a valid edit batch.
- Liu et al., [Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/), show that usable long-context performance depends on information position. ClearLens therefore does not equate context-window capacity with reliable whole-file proofreading.
- Jiang et al., [LongLLMLingua](https://aclanthology.org/2024.acl-long.91/), and Pan et al., [LLMLingua-2](https://aclanthology.org/2024.findings-acl.57/), motivate explicit context budgets and faithful compression. ClearLens deliberately applies only lossless structural chunking—not semantic document compression—to the evidence being proofread.
- Raheja et al., [CoEdIT](https://aclanthology.org/2023.findings-emnlp.350/) and [mEdIT](https://aclanthology.org/2024.naacl-long.56/), motivate explicit task-specific editing instructions. ClearLens adds atomic source-indexed edits and local validation for auditable corpus work.

The line-aware, complete-coverage, fail-closed protocol is an engineering inference from these sources; the papers do not prescribe this exact application architecture.

## Task Execution

File discovery, decoding, deterministic rule preview and cleaning, transcoding, saving, merging, and LLM requests run outside the Tk main thread. Local rule cleaning can use a process pool; import, encoding, preview, and file output use bounded background threads. Every task carries an identity token, so cancellation immediately restores the interface and discards late events from stopped workers. Only one background task may own the token at a time; task entry points reject concurrent starts. While a task owns the token, the main menu and every state-changing button, checkbox, entry, combo box, editor, tab selector, and data table are disabled; only the Stop Task button and its Escape shortcut remain active. The status bar reports the active task on the left and overall completed/total/percentage progress on the right; LLM tasks report both file and chunk position. Manual typing updates only the affected queue row instead of rebuilding the file tree, preserving the caret and allowing continuous entry, paste, and whole-text edits.

The log table uses incremental row insertion while a batch is running instead of rebuilding every previous row after each result. Deterministic transforms have fast no-op paths for common HTML and whitespace cases. File selection is debounced. Long-line detection checks both average and maximum sampled line length, so a document containing one 140,000-character HTML line cannot be misclassified merely because it also contains many short lines. Such content is forced to no-wrap rendering and a 12,000-character hard editor cap; undo buffers are reset after programmatic document switches. Line-number redraw requests are coalesced, and a number is drawn only for `N.0` when that logical first row is actually visible, never for a wrapped continuation.

Rule preview is semantically independent from editor virtualization. The worker applies the selected deterministic options and regex library to the complete `active_text`, finds the first visible line-level difference, and creates bounded line-aware excerpts around that location. Excerpts carry their full-document starting line numbers into both gutters and the difference table. When regex rules are enabled, a second deterministic local-only baseline isolates the regex stage, allowing the preview to report exact regex match totals and show the requested rule rather than an earlier default whitespace change. Only editor rendering is bounded—the full `active_text` remains authoritative for processing, history, statistics, and output. Non-UTF-8 encoding candidates are ranked from at most a 1 MiB sample, followed by strict full-file validation of the best candidate rather than repeated full-file decoding.

Rule cleaning, direct LLM cleaning, natural-language LLM cleaning, suggestion application, transcode preparation, resets, and manual edits share one operation history. A batch stores one before/after snapshot containing every affected file, including its working-text marker, dirty state, target encoding, output path, and filename-suffix mode, so one undo or redo restores the whole batch. Snapshots are compressed and the history is capped at the most recent 50 operations. Import-list mutations and explicit re-decoding clear history because they change file identity or the authoritative source text.

The cleaning log is a timestamped `Treeview` table. Processing rows are linked to the stable identifier of their history entry after a batch completes. “Undo Selected Operation” succeeds only when that row belongs to the newest undo entry; this preserves cumulative processing order. Every row linked to the reverted entry is then frozen as undone, and the undo itself is appended as a new informational row. Save and diagnostic rows are intentionally not undoable.

The numbered file queue and document notebook are separated by a vertical CTk splitter. The initial queue allocation is 36 percent of the right workspace and the separator remains user-adjustable. Every splitter stores the user's current ratio, not an absolute sash coordinate, so maximize, restore, and ordinary resize operations preserve the relative pane allocation. The horizontal CTk splitter opens with a 26-percent left function panel and logical minimum widths for both panes. Original/input and current/preview editors use synchronized logical-line gutters. The main difference view is a row table built from line-level sequence opcodes; double-clicking a row navigates to its original line.

## Interface Layout

Version 1.5.0 migrated the main window and auxiliary dialogs to CustomTkinter 5.2.2. Version 1.5.1 hardens geometry allocation for scaled Windows displays, v1.5.2 corrects native menu-font construction for Python/Tk on Windows, v1.5.3 adds the two-row task toolbar and explicit natural-language-rule scope, v1.5.4 adds full task-time interface locking, asynchronous preview, incremental logs, numbered queues, selected-file task scopes, ratio-preserving split panes, and unsaved-exit protection, v1.5.5 adds LLM task/size preflight, per-file sequential requests, Find/Find All counts, a clean-workspace command, direct output-folder access, and bounded long-line preview rendering, v1.5.6 makes preview operate on complete text, isolates regex preview results, virtualizes extreme lines, stabilizes logical-line gutters, preserves editors across rule-library rebuilds, and fixes the scaled custom-regex editor layout, v1.5.7 adds line-indexed atomic LLM edits, complete-coverage large-document chunking, source fingerprints, overlap ownership, chunk progress, and fail-closed per-file application, v1.5.8 adds strict DeepSeek tool schemas, JSON fallback, operation-alias normalization, and item-level response recovery, v1.5.9 fixes the preview baseline, supports opt-in LLM-rule previews, executes multi-rule tasks as transactional ordered passes, and expands complex/nested edit compatibility, v1.5.10 moves transport identity ownership from the model to the application, repairs uniquely locatable line metadata locally, and reports unresolved fragment failures precisely, and v1.5.11 stabilizes preview snapshots, reapplies the main icon after window mapping, adds visible LLM wait/timeout telemetry, and retries incomplete or incompatible responses with smaller complete-coverage chunks. CTk windows, frames, buttons, checkboxes, entries, combo boxes, tab views, text editors, scrollbars, progress bars, and custom splitters share the bundled `assets/clearlens_theme.json` palette. Native Windows file dialogs are retained. Native ttk Treeview remains for the file queue, line-difference view, cleaning log, statistics, regular-expression library, natural-language rule library, and LLM review table because it provides mature multi-column data behavior.

`CTkSplitPane` calculates its ratio and minimum sizes in CTk logical units, converts the final bounds to actual widget pixels, and passes explicit rectangles to Tk's underlying place manager. Geometry propagation is disabled on both pane containers. Dragging updates the ratio; subsequent Configure events derive a new pixel position from that ratio. This prevents packed or gridded children from shrinking a pane independently of its separator and prevents window maximize/restore from changing relative proportions. The behavior applies to the main left/right workspace, queue/document workspace, and original/result preview workspace.

There is no application-wide interface-scale menu, preference, profile field, or default `display` configuration. During settings/profile normalization, legacy v1.4.4 `display` values are removed. CustomTkinter owns the normal component and font scaling path. The current-result editor retains its independent `editor.font_size` setting and A−/A+ controls; those controls change document text only and do not alter application scaling.

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

## Windows DPI Compatibility

The application root is `customtkinter.CTk`, exposed through `clearlens/window.py`. CustomTkinter performs its supported Windows display-scaling detection and scales CTk geometry and fonts together. ClearLens does not add a second application-wide scale multiplier, does not call a project-owned Per-Monitor V2 bootstrap, and does not ship a custom DPI manifest.

Treeview is not a CTk widget, so `DpiAwareTreeview` polls the effective DPI of its own top-level window with `GetDpiForWindow`. When the window DPI changes, it reapplies pixel-based fonts, row height, heading padding, and logical column widths through a unique ttk style. The line-number canvas uses the same per-window DPI basis for gutter geometry. This keeps the retained native data controls aligned with adjacent CTk controls on high-scale Windows displays.

Tk menus are retained for native menu behavior, but every main, cascade, and context menu is a `DpiAwareMenu`. It reads the owning top-level window DPI before display and assigns a negative-pixel font derived from the same 13-pixel logical base used by the CTk theme. The named font is created with tkinter's `root=` argument; passing `master=` is invalid because `Font` forwards unknown keywords to Tcl as font options. The menu therefore starts correctly on Windows and does not depend on a stale global Tk point-size conversion after a native file dialog has been opened.

The compatibility root combines `CTk` with `TkinterDnD.DnDWrapper` on one Tcl interpreter, then loads the native tkdnd extension. This preserves file/folder drag and drop without creating a second Tk root. If `tkinterdnd2` is unavailable while running source code, the application falls back to the normal CTk root; the release build installs and bundles both declared packages.

## Windows Onedir Build

`build_clearlens.bat` creates and uses `virtual_env`, installs the declared requirements there, and invokes PyInstaller with explicit `--onedir --contents-directory _internal`. It collects CustomTkinter (including its themes and metadata) and `tkinterdnd2`; Python, extension modules, and third-party runtime packages remain in `_internal`.

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
