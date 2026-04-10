# compile-workspace (Windows)

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
└── windows/
    ├── compile-workspace.bat
    └── compile-workspace.ps1

workspace/
├── specs/
└── compiled/
```

---

## Key Improvements

- ✅ No hardcoded username (like `KASRA`)
- ✅ No hardcoded absolute paths
- ✅ Works relative to project structure
- ✅ Automatically detects Python

---

## Requirements

- Windows
- Python installed (Anaconda or standard Python)
- PowerShell (default on Windows)

---

## How It Works

### Python Detection Logic

The script tries:

1. `python` from PATH
2. Common install locations:
   - `%USERPROFILE%\anaconda3\python.exe`
   - `%LOCALAPPDATA%\Programs\Python\Python313\python.exe`
   - `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`
   - `%LOCALAPPDATA%\Programs\Python\Python311\python.exe`

If none are found → it shows an error.

---

## Run the Tool

Navigate to:

```
compiler/windows/
```

Then:

- Double-click:
  ```
  compile-workspace.bat
  ```

or run:

```bat
compile-workspace.bat
```

---

## What Happens

1. File picker opens → choose your `.json` file from `workspace/specs`
2. Save dialog opens → choose output location and name
3. Script compiles the workspace
4. Output folder is created:
   ```
   selected-folder/spec-name
   ```

---

## Output Example

Input:
```
workspace/specs/i18n-localization-workspace.json
```

Output:
```
workspace/compiled/i18n-localization-workspace/
```

---

## Troubleshooting

### ❌ Python not found

Error:
```
Python executable was not found.
```

Fix:

Run:

```powershell
python -c "import sys; print(sys.executable)"
```

Then manually set in `compile-workspace.ps1`:

```powershell
$python = 'FULL_PATH_TO_python.exe'
```

---

### ❌ Exit code 9009

Same issue: Python not found.

---

### ❌ Compile script not found

Error:
```
Compile script was not found
```

Fix:

Ensure file exists:

```
compiler/scripts/compile_workspace_spec.py
```

---

### ❌ Specs folder not found

Ensure:

```
workspace/specs/
```

exists.

---

### ❌ Window closes immediately

Use this `.bat`:

```bat
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0compile-workspace.ps1"
pause
```

---

## Notes

- Output is a **folder**, not a file
- Save dialog is used only to choose folder name + location
- Script is portable across users and machines

---

## Summary

This version is:

- portable
- user-independent
- safe for distribution

If something breaks:

1. Check Python
2. Check folder structure
3. Run again
