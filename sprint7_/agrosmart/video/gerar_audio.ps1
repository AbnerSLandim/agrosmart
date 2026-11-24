param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech

$videoDir = Join-Path $ProjectRoot 'video'
$audioDir = Join-Path $videoDir 'audio'
New-Item -ItemType Directory -Force -Path $audioDir | Out-Null
$segments = Get-Content -Raw -LiteralPath (Join-Path $videoDir 'narracao.json') | ConvertFrom-Json

foreach ($segment in $segments) {
    $output = Join-Path $audioDir ($segment.id + '.wav')
    $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $speaker.SelectVoice('Microsoft Maria Desktop')
        $speaker.Rate = 3
        $speaker.Volume = 100
        $speaker.SetOutputToWaveFile($output)
        $speaker.Speak([string]$segment.texto)
    }
    finally {
        $speaker.Dispose()
    }
    Write-Output $output
}
