# compile-workspace (macOS)

This tool lets you:

1. Choose a spec `.json` file (via file picker)
2. Choose where to save the output (Save As-style dialog)
3. Automatically compile using Python
4. Save output in a folder named after the spec file

---

## Project Structure

Your project should look like this:

```
compiler/
├── scripts/
│   └── compile_workspace_spec.py
└── mac/
    └── compile-workspace.sh

workspace/
├── specs/
└── compiled/
```

---

## Key Features

- ✅ No hardcoded user paths
- ✅ Uses project-relative paths
- ✅ Works on any Mac machine/user
- ✅ Native macOS dialogs (AppleScript)

---

## Requirements

- macOS
- Python 3

---

## Install Python (if needed)

Check:

```bash
python3 --version
```

If not installed:

Using Homebrew:

```bash
brew install python
```

---

## Make Script Executable

Navigate to mac compiler folder:

```bash
cd compiler/mac
```

Then:

```bash
chmod +x compile-workspace.sh
```

---

## Run the Tool

```bash
./compile-workspace.sh
```

---

## What Happens

1. File picker opens → choose your `.json` file from:

```
workspace/specs/
```

2. Save dialog opens → choose output location and name

3. Script compiles the workspace

4. Output folder is created:

```
selected-folder/spec-name
```

---

## Example

Input:

```
workspace/specs/i18n-localization-workspace.json
```

Output:

```
workspace/compiled/i18n-localization-workspace/
```

---

## How It Works (Internals)

The script dynamically resolves:

- Compiler script:
```
compiler/scripts/compile_workspace_spec.py
```

- Specs folder:
```
workspace/specs
```

- Output folder:
```
workspace/compiled
```

No hardcoded `$HOME` paths are used.

---

## Troubleshooting

### ❌ Python not found

Error dialog appears.

Fix:

```bash
python3 --version
```

If missing:

```bash
brew install python
```

---

### ❌ Compile script not found

Check:

```
compiler/scripts/compile_workspace_spec.py
```

---

### ❌ Specs folder not found

Check:

```
workspace/specs/
```

---

### ❌ Permission denied

Fix:

```bash
chmod +x compile-workspace.sh
```

---

## Notes

- Output is a **folder**, not a file
- Save dialog is used to choose folder name + location
- Script is portable and user-independent

---

## Summary

This setup is:

- portable
- clean
- consistent with Windows and Ubuntu versions

If something breaks:

1. Check Python
2. Check project structure
3. Run again
