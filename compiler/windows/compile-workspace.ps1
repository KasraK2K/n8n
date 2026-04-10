Add-Type -AssemblyName System.Windows.Forms

$python = $null

$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -notlike "*\WindowsApps\python.exe") {
    $python = $cmd.Source
}

if (-not $python) {
    $pythonCandidates = @(
        "$env:USERPROFILE\anaconda3\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    )

    $python = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $python) {
    Write-Host "Python executable was not found."
    Write-Host "A Microsoft Store alias may be installed instead of real Python."
    Write-Host "Please install Python or update the `$python value manually."
    Read-Host 'Press Enter to close'
    exit 9009
}

$windowsDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$compilerDir = Split-Path -Parent $windowsDir
$rootDir     = Split-Path -Parent $compilerDir

$script = Join-Path $compilerDir "scripts\compile_workspace_spec.py"
$specDir = Join-Path $rootDir "workspace\specs"
$compiledDir = Join-Path $rootDir "workspace\compiled"

if (-not (Test-Path $script)) {
    Write-Host "Compile script was not found:"
    Write-Host $script
    Read-Host 'Press Enter to close'
    exit 9001
}

if (-not (Test-Path $specDir)) {
    Write-Host "Specs folder was not found:"
    Write-Host $specDir
    Read-Host 'Press Enter to close'
    exit 9002
}

if (-not (Test-Path $compiledDir)) {
    New-Item -ItemType Directory -Path $compiledDir | Out-Null
}

$open = New-Object System.Windows.Forms.OpenFileDialog
$open.Title = 'Choose spec JSON file'
$open.InitialDirectory = $specDir
$open.Filter = 'JSON files (*.json)|*.json|All files (*.*)|*.*'
$open.Multiselect = $false

if ($open.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    exit 1
}

$inputFile = $open.FileName
$defaultName = [System.IO.Path]::GetFileNameWithoutExtension($inputFile)

$save = New-Object System.Windows.Forms.SaveFileDialog
$save.Title = 'Choose output folder name'
$save.InitialDirectory = $compiledDir
$save.FileName = $defaultName
$save.Filter = 'Folder placeholder|*.folder'
$save.OverwritePrompt = $false

if ($save.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    exit 2
}

$outputDir = [System.IO.Path]::Combine(
    [System.IO.Path]::GetDirectoryName($save.FileName),
    [System.IO.Path]::GetFileNameWithoutExtension($save.FileName)
)

Write-Host ""
Write-Host "Python: $python"
Write-Host "Script: $script"
Write-Host "Input : $inputFile"
Write-Host "Output: $outputDir"
Write-Host ""

& $python $script $inputFile --out $outputDir
$code = $LASTEXITCODE

Write-Host ""
Write-Host "Exit code: $code"
Read-Host 'Press Enter to close'
exit $code