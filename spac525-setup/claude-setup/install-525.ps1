# Installs the spac-525-writing skill and the 525 rule memory on Windows.
# Run from this claude-setup folder:  powershell -ExecutionPolicy Bypass -File .\install-525.ps1 -MemoryDir "<your Claude Code project memory folder>"
param([string]$MemoryDir = "")
$skills = "C:\Users\one\.claude\skills"
New-Item -ItemType Directory -Force -Path $skills | Out-Null
Copy-Item -Recurse -Force "$PSScriptRoot\skills\spac-525-writing" $skills
Write-Host "Skill installed to $skills\spac-525-writing"
if ($MemoryDir) {
  New-Item -ItemType Directory -Force -Path $MemoryDir | Out-Null
  Copy-Item -Force "$PSScriptRoot\memory\the-525-rule.md" $MemoryDir
  $index = Join-Path $MemoryDir "MEMORY.md"
  $entry = Get-Content "$PSScriptRoot\memory\MEMORY-525-entry.md" -Raw
  if (-not (Test-Path $index) -or -not (Select-String -Path $index -Pattern "the-525-rule.md" -Quiet)) {
    Add-Content -Path $index -Value $entry.TrimEnd()
  }
  Write-Host "Memory added to $MemoryDir (MEMORY.md entry appended, existing entries kept)"
}
python "$skills\spac-525-writing\scripts\check_draft.py" --help | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "Checker runs." }
