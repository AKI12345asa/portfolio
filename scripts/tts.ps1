<#
.SYNOPSIS
  离线中文配音生成器 —— 把稿子变成音频文件（Windows SAPI5 / System.Speech）

.DESCRIPTION
  读取一份稿子（txt / md / 任意纯文本），按句子切分，逐句合成后拼成一条音频，
  同时产出一份时间轴，方便对齐字幕或做视频旁白。

  产物：
    <Prefix>.wav        合成好的整条音频
    <Prefix>.timing.json 每句的起止时间（秒）
    <Prefix>.srt        字幕文件（加 -Srt 时）
    <Prefix>.mp3        mp3（加 -Mp3 时，需要 ffmpeg）

.EXAMPLE
  # 最简：稿子进，wav 出
  pwsh scripts/tts.ps1 稿子.txt

.EXAMPLE
  # 指定音色、语速，并同时产出字幕
  pwsh scripts/tts.ps1 稿子.txt -Voice Kangkang -Rate -1 -Srt -Prefix 首页旁白

.EXAMPLE
  # 不写文件，直接念一段话
  pwsh scripts/tts.ps1 -Text "你好，世界。" -Voice Yaoyao
#>
[CmdletBinding(DefaultParameterSetName = 'File')]
param(
  # 稿子文件路径（txt / md）
  [Parameter(ParameterSetName = 'File', Position = 0)]
  [string]$ScriptFile,

  # 直接传一段文字，不读文件
  [Parameter(ParameterSetName = 'Inline', Mandatory = $true)]
  [string]$Text,

  # 输出目录（相对当前目录或绝对路径）
  [string]$OutDir = 'output\tts',

  # 输出文件名前缀
  [string]$Prefix = 'narration',

  # whole = 整篇一次合成（断句靠引擎）；sentence = 逐句合成后拼接（推荐，可控、能出时间轴）
  [ValidateSet('whole', 'sentence')]
  [string]$Mode = 'sentence',

  # 音色：Huihui / Kangkang / Yaoyao，或完整名称（如 "Microsoft Huihui Desktop"）
  [string]$Voice = 'Huihui',

  # 语速 -10（最慢）~ 10（最快），0 为正常
  [ValidateRange(-10, 10)]
  [int]$Rate = 0,

  # 音量 0~100
  [ValidateRange(0, 100)]
  [int]$Volume = 100,

  # 句间停顿（毫秒），让拼接听起来像真人换气
  [ValidateRange(0, 5000)]
  [int]$PauseMs = 250,

  # 单句最大字数，超过就在逗号处再切（影响时间轴粒度）
  [int]$MaxChars = 120,

  # 把 markdown 标题（# 开头）也念出来；默认跳过，因为标题通常是结构不是台词
  [switch]$ReadHeadings,

  # 额外产出 SRT 字幕
  [switch]$Srt,

  # 额外产出 mp3（需要 ffmpeg）
  [switch]$Mp3,

  # 保留逐句的独立 wav 片段
  [switch]$KeepParts
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech

$SampleRate = 22050
$Bits = 16
$Channels = 1

# ---------- 1. 取稿 ----------
if ($PSCmdlet.ParameterSetName -eq 'File') {
  if (-not $ScriptFile) { throw '请提供稿子文件路径，或用 -Text 直接传入文字。' }
  $path = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $ScriptFile))
  if (-not (Test-Path $path)) { throw "找不到稿子文件：$path" }
  $raw = Get-Content -LiteralPath $path -Raw -Encoding UTF8
} else {
  $raw = $Text
}
if (-not $raw -or -not $raw.Trim()) { throw '稿子是空的。' }

# 去掉 markdown 装饰：标题井号、加粗星号、链接语法，只留可念的文字
$clean = $raw
if ($ReadHeadings) {
  $clean = $clean -replace '(?m)^\s{0,3}#{1,6}\s*', ''
} else {
  $clean = $clean -replace '(?m)^\s{0,3}#{1,6}\s.*(\n|$)', ''
}
$clean = $clean -replace '\*\*(.+?)\*\*', '$1'
$clean = $clean -replace '(?m)^\s*[-*+]\s+', ''
$clean = $clean -replace '\[(.+?)\]\((.*?)\)', '$1'
$clean = $clean -replace '`([^`]*)`', '$1'
$clean = $clean -replace '(?m)^\s*>\s?', ''
$clean = $clean -replace '(?m)^\s*\|.*\|\s*$', ''   # markdown 表格行不念
$clean = $clean -replace '(?m)^\s*(-{3,}|_{3,}|={3,})\s*$', ''

# ---------- 2. 选音色 ----------
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$installed = $synth.GetInstalledVoices() | Where-Object { $_.Enabled } | ForEach-Object { $_.VoiceInfo }

$alias = @{
  'huihui'   = 'Microsoft Huihui Desktop'
  '慧慧'      = 'Microsoft Huihui Desktop'
  'kangkang' = 'Microsoft Kangkang'
  '康康'      = 'Microsoft Kangkang'
  'yaoyao'   = 'Microsoft Yaoyao'
  '瑶瑶'      = 'Microsoft Yaoyao'
}

$target = $alias[$Voice.Trim().ToLower()]
if (-not $target) { $target = $Voice.Trim() }

$chosen = $installed | Where-Object { $_.Name -eq $target } | Select-Object -First 1
if (-not $chosen) { $chosen = $installed | Where-Object { $_.Name -like "*$target*" } | Select-Object -First 1 }
if (-not $chosen) {
  $chosen = $installed | Where-Object { $_.Culture.Name -eq 'zh-CN' } | Select-Object -First 1
  if ($chosen) { Write-Warning "没找到音色「$Voice」，改用中文音色：$($chosen.Name)" }
}
if (-not $chosen) { throw "系统里没有可用音色。已安装：$($installed.Name -join ', ')" }

$synth.SelectVoice($chosen.Name)
$synth.Rate = $Rate
$synth.Volume = $Volume

$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
  $SampleRate,
  [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
  [System.Speech.AudioFormat.AudioChannel]::Mono
)

# ---------- 3. 切句 ----------
function Split-Sentences {
  param([string]$RawText, [int]$Max)
  $result = New-Object System.Collections.Generic.List[string]
  $normalized = $RawText -replace "`r`n", "`n" -replace "`r", "`n"

  # 先按句末标点和换行切，标点保留在句尾
  $sentences = [regex]::Matches($normalized, '[^。！？!?；;…\n]+[。！？!?；;…]*')
  foreach ($m in $sentences) {
    $s = $m.Value.Trim()
    if (-not $s) { continue }

    if ($s.Length -le $Max) { $result.Add($s); continue }

    # 太长就在逗号/顿号处再切，避免一口气念不完
    $pieces = [regex]::Matches($s, '[^，,、]+[，,、]*')
    $buffer = ''
    foreach ($p in $pieces) {
      $piece = $p.Value
      if ($buffer -and ($buffer + $piece).Length -gt $Max) {
        $result.Add($buffer.Trim()); $buffer = $piece
      } else {
        $buffer += $piece
      }
    }
    if ($buffer.Trim()) { $result.Add($buffer.Trim()) }
  }
  return $result
}

if ($Mode -eq 'whole') {
  $sentences = @(($clean -replace '\s*\n\s*', ' ').Trim())
} else {
  $sentences = @(Split-Sentences -RawText $clean -Max $MaxChars)
}
if ($sentences.Count -eq 0) { throw '切句后没有内容，检查稿子是不是只有符号。' }

# ---------- 4. 合成 ----------
$bytesPerSecond = $SampleRate * $Channels * ($Bits / 8)
$silenceBytes = [int]($bytesPerSecond * ($PauseMs / 1000.0))
$silence = [byte[]]::new($silenceBytes)

$outPath = Join-Path (Get-Location) $OutDir
New-Item -ItemType Directory -Force -Path $outPath | Out-Null
$basePath = Join-Path $outPath $Prefix

$timeline = New-Object System.Collections.Generic.List[object]
$all = New-Object System.IO.MemoryStream
$cursor = 0.0
$index = 0

foreach ($sentence in $sentences) {
  $index++
  $ms = New-Object System.IO.MemoryStream
  $synth.SetOutputToAudioStream($ms, $format)
  $synth.Speak($sentence)
  $synth.SetOutputToNull()

  $pcm = $ms.ToArray()
  $ms.Dispose()
  if ($pcm.Length -eq 0) { Write-Warning "第 $index 句没有产出音频，已跳过：$sentence"; continue }

  $duration = $pcm.Length / $bytesPerSecond

  if ($KeepParts) {
    $partPath = '{0}.part{1:D3}.wav' -f $basePath, $index
    $header = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($header)
    $bw.Write([System.Text.Encoding]::ASCII.GetBytes('RIFF')); $bw.Write([int](36 + $pcm.Length))
    $bw.Write([System.Text.Encoding]::ASCII.GetBytes('WAVE'))
    $bw.Write([System.Text.Encoding]::ASCII.GetBytes('fmt ')); $bw.Write([int]16)
    $bw.Write([int16]1); $bw.Write([int16]$Channels); $bw.Write([int]$SampleRate)
    $bw.Write([int]($SampleRate * $Channels * ($Bits / 8))); $bw.Write([int16]($Channels * ($Bits / 8))); $bw.Write([int16]$Bits)
    $bw.Write([System.Text.Encoding]::ASCII.GetBytes('data')); $bw.Write([int]$pcm.Length)
    $bw.Flush()
    $headerBytes = $header.ToArray()
    $fs = [System.IO.File]::Create($partPath)
    $fs.Write($headerBytes, 0, $headerBytes.Length)
    $fs.Write($pcm, 0, $pcm.Length)
    $fs.Close()
  }

  $all.Write($pcm, 0, $pcm.Length)
  $timeline.Add([pscustomobject]@{
    index    = $index
    text     = $sentence
    start    = [math]::Round($cursor, 3)
    end      = [math]::Round($cursor + $duration, 3)
    duration = [math]::Round($duration, 3)
  })
  $cursor += $duration

  if ($index -lt $sentences.Count -and $silenceBytes -gt 0) {
    $all.Write($silence, 0, $silence.Length)
    $cursor += $PauseMs / 1000.0
  }
}

$pcmAll = $all.ToArray()
$all.Dispose()
if ($pcmAll.Length -eq 0) { throw '合成失败：没有产出任何音频数据。' }

# ---------- 5. 写 WAV ----------
$wavPath = "$basePath.wav"
$fs = [System.IO.File]::Create($wavPath)
$bw = New-Object System.IO.BinaryWriter($fs)
$bw.Write([System.Text.Encoding]::ASCII.GetBytes('RIFF')); $bw.Write([int](36 + $pcmAll.Length))
$bw.Write([System.Text.Encoding]::ASCII.GetBytes('WAVE'))
$bw.Write([System.Text.Encoding]::ASCII.GetBytes('fmt ')); $bw.Write([int]16)
$bw.Write([int16]1); $bw.Write([int16]$Channels); $bw.Write([int]$SampleRate)
$bw.Write([int]($SampleRate * $Channels * ($Bits / 8)))
$bw.Write([int16]($Channels * ($Bits / 8))); $bw.Write([int16]$Bits)
$bw.Write([System.Text.Encoding]::ASCII.GetBytes('data')); $bw.Write([int]$pcmAll.Length)
$bw.Write($pcmAll, 0, $pcmAll.Length)
$bw.Flush(); $bw.Close(); $fs.Close()

# ---------- 6. 时间轴 / 字幕 ----------
$jsonPath = "$basePath.timing.json"
[pscustomobject]@{
  voice      = $chosen.Name
  rate       = $Rate
  duration   = [math]::Round($cursor, 3)
  sampleRate = $SampleRate
  sentences  = $timeline
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

function Format-SrtTime([double]$seconds) {
  $ts = [TimeSpan]::FromSeconds($seconds)
  '{0:00}:{1:00}:{2:00},{3:000}' -f [int]$ts.TotalHours, $ts.Minutes, $ts.Seconds, $ts.Milliseconds
}

if ($Srt) {
  $srtPath = "$basePath.srt"
  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($item in $timeline) {
    $lines.Add("$($item.index)")
    $lines.Add("$(Format-SrtTime $item.start) --> $(Format-SrtTime $item.end)")
    $lines.Add($item.text)
    $lines.Add('')
  }
  Set-Content -LiteralPath $srtPath -Value ($lines -join "`r`n") -Encoding UTF8
}

# ---------- 7. mp3（可选） ----------
$mp3Path = $null
if ($Mp3) {
  $ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
  if (-not $ffmpeg) { $ffmpeg = Join-Path (Get-Location) '.tools\ffmpeg\bin\ffmpeg.exe'; if (-not (Test-Path $ffmpeg)) { $ffmpeg = $null } }
  if ($ffmpeg) {
    $mp3Path = "$basePath.mp3"
    & $ffmpeg -hide_banner -loglevel error -y -i $wavPath -codec:a libmp3lame -qscale:a 4 $mp3Path
    if ($LASTEXITCODE -ne 0) { Write-Warning 'mp3 转码失败，wav 仍然可用。'; $mp3Path = $null }
  } else {
    Write-Warning '没找到 ffmpeg，跳过 mp3。可先安装 ffmpeg 或改用 wav。'
  }
}

# ---------- 8. 汇报 ----------
$total = [math]::Round($cursor, 2)
Write-Host ''
Write-Host "音色    : $($chosen.Name)  (语速 $Rate, 句间停顿 ${PauseMs}ms)" -ForegroundColor Cyan
Write-Host "句数    : $($timeline.Count)" -ForegroundColor Cyan
Write-Host "时长    : $([TimeSpan]::FromSeconds($total).ToString('mm\:ss'))  采样 ${SampleRate}Hz 16bit 单声道" -ForegroundColor Cyan
Write-Host "WAV     : $wavPath" -ForegroundColor Green
Write-Host "时间轴  : $jsonPath" -ForegroundColor Green
if ($Srt) { Write-Host "字幕    : $srtPath" -ForegroundColor Green }
if ($mp3Path) { Write-Host "MP3     : $mp3Path" -ForegroundColor Green }
$synth.Dispose()
