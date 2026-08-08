<#
.SYNOPSIS
  Publishes each project folder under -Root as its own private GitHub repository.

.DESCRIPTION
  For every folder: initialises git if needed, drops in a .gitignore and a README
  when they are missing, makes one commit, creates the remote repo through the
  GitHub API and pushes.

  Idempotent — rerunning skips repos that already exist and folders with nothing
  new to commit.

  Defaults to a DRY RUN. Nothing touches disk or GitHub until you pass -Execute.

.PARAMETER Token
  GitHub PAT. Classic token needs the `repo` scope; a fine-grained token needs
  "Administration: Read and write" plus "Contents: Read and write" on the account.
  Falls back to $env:GITHUB_TOKEN.

.EXAMPLE
  # see what would happen
  .\publish-demo-repos.ps1 -Owner deussbelli

.EXAMPLE
  # do it, in batches
  $env:GITHUB_TOKEN = 'github_pat_...'
  .\publish-demo-repos.ps1 -Owner deussbelli -Execute -Limit 25
#>

[CmdletBinding()]
param(
    [string]$Root = 'N:\Repos\SITES',
    [Parameter(Mandatory = $true)][string]$Owner,
    [string]$Token = $env:GITHUB_TOKEN,
    [string[]]$Only = @(),
    [int]$Limit = 0,
    [int]$DelaySeconds = 2,
    [switch]$Public,
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'

# Folders that are infrastructure, not projects.
$Skip = @('_hub', '.git', '.venv', '.history', '.obsidian', '.agents', '.codex', 'node_modules')

$GitIgnore = @'
node_modules/
.pnp/
dist/
build/
out/
.next/
.nuxt/
.astro/
.svelte-kit/
.cache/
.parcel-cache/
coverage/
.env
.env.local
.env.*.local
*.log
logs/
.vercel/
.DS_Store
Thumbs.db
*.tsbuildinfo
next-env.d.ts
'@

function ConvertTo-RepoSlug {
    param([string]$Name)
    # strip accents so "Noir Cafe" keeps its e, and drop apostrophes rather
    # than turning them into separators
    $decomposed = $Name.Normalize([System.Text.NormalizationForm]::FormD)
    $stripped = -join ($decomposed.ToCharArray() | Where-Object {
            [System.Globalization.CharUnicodeInfo]::GetUnicodeCategory($_) -ne 'NonSpacingMark'
        })
    $slug = $stripped.ToLowerInvariant()
    $slug = $slug -replace "['’]", ''
    $slug = $slug -replace '&', ' and '
    $slug = $slug -replace "[^a-z0-9]+", '-'
    $slug = $slug.Trim('-')
    if ([string]::IsNullOrWhiteSpace($slug)) { $slug = 'project' }
    return $slug
}

function Get-ProjectDescription {
    param([string]$Path, [string]$Name)

    $pkgPath = Join-Path $Path 'package.json'
    $stack = @()
    if (Test-Path $pkgPath) {
        try {
            $pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
            $deps = @()
            if ($pkg.dependencies) { $deps += $pkg.dependencies.PSObject.Properties.Name }
            if ($pkg.devDependencies) { $deps += $pkg.devDependencies.PSObject.Properties.Name }
            foreach ($pair in @(
                    @('next', 'Next.js'), @('astro', 'Astro'), @('nuxt', 'Nuxt'),
                    @('vue', 'Vue'), @('svelte', 'Svelte'), @('react', 'React'),
                    @('tailwindcss', 'Tailwind'), @('typescript', 'TypeScript'),
                    @('vite', 'Vite'), @('three', 'Three.js'), @('ethers', 'ethers.js')
                )) {
                if ($deps -contains $pair[0]) { $stack += $pair[1] }
            }
        }
        catch { }
    }
    if (Test-Path (Join-Path $Path 'requirements.txt')) { $stack += 'Python' }

    if ($stack.Count -gt 0) {
        return "$Name - demo build ($($stack -join ', '))"
    }
    return "$Name - demo build"
}

function Invoke-GitHub {
    param([string]$Method, [string]$Path, [hashtable]$Body)

    $headers = @{
        Authorization          = "Bearer $Token"
        Accept                 = 'application/vnd.github+json'
        'X-GitHub-Api-Version' = '2022-11-28'
        'User-Agent'           = 'publish-demo-repos'
    }
    $request = @{ Method = $Method; Uri = "https://api.github.com$Path"; Headers = $headers }
    if ($Body) {
        $request.Body = ($Body | ConvertTo-Json -Depth 5)
        $request.ContentType = 'application/json'
    }
    return Invoke-RestMethod @request
}

# --- preflight -------------------------------------------------------------

if ($Execute -and [string]::IsNullOrWhiteSpace($Token)) {
    throw 'No token. Set $env:GITHUB_TOKEN or pass -Token.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git is not on PATH.'
}
if (-not (Test-Path $Root)) { throw "Root not found: $Root" }

$folders = Get-ChildItem -Path $Root -Directory |
    Where-Object { $Skip -notcontains $_.Name -and -not $_.Name.StartsWith('.') }

if ($Only.Count -gt 0) {
    $folders = $folders | Where-Object { $Only -contains $_.Name }
}
if ($Limit -gt 0) {
    $folders = $folders | Select-Object -First $Limit
}

$visibility = if ($Public) { 'public' } else { 'private' }
Write-Host ""
Write-Host "Root:       $Root"
Write-Host "Owner:      $Owner"
Write-Host "Visibility: $visibility"
Write-Host "Folders:    $($folders.Count)"
Write-Host "Mode:       $(if ($Execute) { 'EXECUTE' } else { 'DRY RUN (pass -Execute to apply)' })"
Write-Host ""

$done = 0
$skipped = 0
$failed = @()

foreach ($folder in $folders) {
    $name = $folder.Name
    $slug = ConvertTo-RepoSlug $name
    $path = $folder.FullName

    if (-not $Execute) {
        Write-Host ("  {0,-28} -> {1}/{2}" -f $name, $Owner, $slug)
        continue
    }

    Write-Host "==> $name -> $Owner/$slug"

    try {
        Push-Location $path

        if (-not (Test-Path '.git')) {
            git init -b main --quiet
        }

        # merge our rules into any .gitignore the project already has, rather than
        # trusting a thin one that lets dev logs and build output through
        $wanted = $GitIgnore -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }
        if (Test-Path '.gitignore') {
            $existing = @(Get-Content '.gitignore' | ForEach-Object { $_.Trim() })
            $missing = @($wanted | Where-Object { $existing -notcontains $_ })
            if ($missing.Count -gt 0) {
                Add-Content -Path '.gitignore' -Value $missing -Encoding utf8
            }
        }
        else {
            Set-Content -Path '.gitignore' -Value $GitIgnore -Encoding utf8
        }

        # drop anything already in the index that the rules now exclude
        $stale = @(git ls-files -i -c --exclude-standard)
        if ($stale.Count -gt 0) {
            git rm -r --cached --quiet -- $stale
        }

        if (-not (Test-Path 'README.md')) {
            $desc = Get-ProjectDescription -Path $path -Name $name
            Set-Content -Path 'README.md' -Value "# $name`n`n$desc`n" -Encoding utf8
        }

        git add -A
        $staged = git diff --cached --name-only
        if ($staged) {
            git commit -q -m "Add $name"
        }
        else {
            Write-Host "    nothing new to commit"
        }

        # create the remote if it is not there yet
        $exists = $true
        try { Invoke-GitHub -Method GET -Path "/repos/$Owner/$slug" | Out-Null }
        catch { $exists = $false }

        if (-not $exists) {
            $body = @{
                name        = $slug
                private     = (-not $Public.IsPresent)
                description = (Get-ProjectDescription -Path $path -Name $name)
                has_issues  = $false
                has_wiki    = $false
            }
            Invoke-GitHub -Method POST -Path '/user/repos' -Body $body | Out-Null
            Write-Host "    created $visibility repo"
            Start-Sleep -Seconds $DelaySeconds
        }
        else {
            Write-Host "    repo already exists"
        }

        $remoteUrl = "https://github.com/$Owner/$slug.git"
        $currentRemote = (git remote get-url origin 2>$null)
        if ($LASTEXITCODE -ne 0 -or -not $currentRemote) {
            git remote add origin $remoteUrl
        }
        elseif ($currentRemote.Trim() -ne $remoteUrl) {
            git remote set-url origin $remoteUrl
        }

        git push -u origin main --quiet
        Write-Host "    pushed"
        $done++
    }
    catch {
        Write-Warning "    FAILED: $($_.Exception.Message)"
        $failed += $name
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
if ($Execute) {
    Write-Host "Pushed:  $done"
    Write-Host "Skipped: $skipped"
    if ($failed.Count -gt 0) {
        Write-Host "Failed:  $($failed -join ', ')"
    }
}
else {
    Write-Host "Dry run only. Rerun with -Execute to apply."
}
