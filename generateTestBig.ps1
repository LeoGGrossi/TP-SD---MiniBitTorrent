# Get current directory
$currentDir = Get-Location
$outFile = Join-Path -Path $currentDir -ChildPath "testfile.bin"
$fileSize = 200MB  # Change size as needed (500MB, 2GB, etc.)
$chunkSize = 1MB

# Create file in current directory
try {
    $random = New-Object System.Random
    $stream = [System.IO.File]::Create($outFile)
    
    $remaining = $fileSize
    while ($remaining -gt 0) {
        $chunk = [byte[]]::new([Math]::Min($remaining, $chunkSize))
        $random.NextBytes($chunk)
        $stream.Write($chunk, 0, $chunk.Length)
        $remaining -= $chunk.Length
        Write-Progress -Activity "Creating file" -Status "$([Math]::Round(($fileSize-$remaining)/1MB)) MB written" -PercentComplete (($fileSize-$remaining)/$fileSize*100)
    }
}
finally {
    if ($null -ne $stream) {
        $stream.Close()
    }
}

Write-Host "Successfully created $outFile ($($fileSize/1GB) GB)"
Write-Host "File saved to: $currentDir"