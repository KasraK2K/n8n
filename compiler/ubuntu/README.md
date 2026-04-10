# compile-workspace (Ubuntu)

This tool lets you:

1. Choose a spec `.json` file
2. Automatically compile it using Python
3. Save output inside the project workspace

---

## Project Structure

Your project should look like this:

```
compiler/
├── scripts/
│   └── compile_workspace_spec.py
└── ubuntu/
    └── compile-workspace.sh

workspace/
├── specs/
└── compiled/
```

---

## Key Features

- ✅ No hardcoded user paths
- ✅ Uses project-relative paths
- ✅ Works on any machine/user
- ✅ Simple GUI via Zenity

---

## Requirements

You need:

- Python 3
- Zenity

---

## Install Dependencies

```bash
sudo apt update
sudo apt install python3 zenity
```

Verify installation:

```bash
python3 --version
zenity --version
```

---

## Make Script Executable

Navigate to the Ubuntu compiler folder:

```bash
cd compiler/ubuntu
```

Then run:

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

1. A file picker opens  
   → select your `.json` file from:

```
workspace/specs/
```

2. The script compiles the workspace

3. Output is generated in:

```
workspace/compiled/<spec-name>
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

The script dynamically resolves paths:

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

No `$HOME` or user-specific paths are used.

---

## Troubleshooting

### ❌ Python not found

Check:

```bash
python3 --version
```

If missing:

```bash
sudo apt install python3
```

---

### ❌ Zenity not found

Check:

```bash
zenity --version
```

If missing:

```bash
sudo apt install zenity
```

---

### ❌ Compile script not found

Ensure this file exists:

```
compiler/scripts/compile_workspace_spec.py
```

---

### ❌ Specs folder not found

Ensure this folder exists:

```
workspace/specs/
```

---

### ❌ Permission denied

Make script executable:

```bash
chmod +x compile-workspace.sh
```

---

## Notes

- Output is always a **folder**, not a file
- Folder name is based on the spec filename
- Script is fully portable across systems

---

## Summary

This setup is:

- portable
- user-independent
- easy to use

If something breaks:

1. Check Python
2. Check Zenity
3. Verify project structure
4. Run again
