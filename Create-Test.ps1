param(
    [string]$phrase = $(Read-Host "Enter the phrase to repeat"),
    [int]$repeats = $(Read-Host "Enter number of repetitions"),
    [string]$outputFile = "testfile.txt"
)

# Create the content
$content = ($phrase + [Environment]::NewLine) * $repeats

# Write to file
[System.IO.File]::WriteAllText($outputFile, $content)

# Show results
$fileSize = (Get-Item $outputFile).Length
Write-Host "Created $outputFile with:"
Write-Host "- Phrase: '$phrase'"
Write-Host "- Repetitions: $repeats"
Write-Host "- Final size: $($fileSize/1KB) KB"