$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."

$NotebookRoot = Join-Path $ProjectRoot "notebooks"
$OutputRoot = Join-Path $ProjectRoot "docs\notebooks"

# Clean previous export
if (Test-Path $OutputRoot) {
    Remove-Item $OutputRoot -Recurse -Force
}

# Recreate root output directory
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

# Find every notebook recursively
Get-ChildItem $NotebookRoot -Recurse -File -Filter "*.ipynb" | ForEach-Object {

    $Notebook = $_

    # Relative directory from notebooks root
    $RelativeDir = $Notebook.Directory.FullName.Substring($NotebookRoot.Length).TrimStart('\')

    # Matching output directory
    $NotebookOutputDir = Join-Path $OutputRoot $RelativeDir

    New-Item -ItemType Directory -Force -Path $NotebookOutputDir | Out-Null

    Write-Host "Exporting $($Notebook.FullName)"

    & "$ProjectRoot\.venv\Scripts\python.exe" `
        -m nbconvert `
        --to html `
        --execute `
        --output-dir "$NotebookOutputDir" `
        "$($Notebook.FullName)"
}

Write-Host ""
Write-Host "Done. HTML files written to:"
Write-Host $OutputRoot