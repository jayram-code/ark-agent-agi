# Fix all src. prefix imports in src directory
# This script changes "from src.X import Y" to "from X import Y"

$files = Get-ChildItem -Path "src" -Recurse -Filter "*.py"

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    $newContent = $content -replace 'from src\.', 'from '
    
    if ($content -ne $newContent) {
        Set-Content -Path $file.FullName -Value $newContent -NoNewline
        Write-Host "Fixed: $($file.FullName)"
    }
}

Write-Host "`nDone! Fixed all src. imports."
