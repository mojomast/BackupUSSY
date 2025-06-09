<#
.SYNOPSIS
    Initializes Git repository for BackupUSSY

.DESCRIPTION
    This script initializes the Git repository, adds all files, and creates the initial commit.

.EXAMPLE
    .\init_git.ps1
#>

Write-Host "BackupUSSY Git Initialization" -ForegroundColor Cyan
Write-Host "Setting up Git repository for GitHub..." -ForegroundColor Cyan
Write-Host ""

# Check if Git is installed
try {
    $gitVersion = git --version 2>$null
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Git not found. Please install Git from https://git-scm.com/" -ForegroundColor Red
    exit 1
}

# Initialize git repository
Write-Host "Initializing Git repository..." -ForegroundColor Cyan
if (-not (Test-Path ".git")) {
    git init
    Write-Host "Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "Git repository already exists" -ForegroundColor Yellow
}

# Check git configuration
$userName = git config user.name 2>$null
$userEmail = git config user.email 2>$null

if (-not $userName) {
    Write-Host "Git user name not configured. Please run:" -ForegroundColor Yellow
    Write-Host "   git config --global user.name 'Your Name'" -ForegroundColor Cyan
} else {
    Write-Host "Git user: $userName" -ForegroundColor Green
}

if (-not $userEmail) {
    Write-Host "Git user email not configured. Please run:" -ForegroundColor Yellow
    Write-Host "   git config --global user.email 'your.email@example.com'" -ForegroundColor Cyan
} else {
    Write-Host "Git email: $userEmail" -ForegroundColor Green
}

# Add files to repository
Write-Host "Adding files to repository..." -ForegroundColor Cyan
git add .

# Show files to be committed
Write-Host "Files to be committed:" -ForegroundColor Cyan
$stagedFiles = git status --porcelain
if ($stagedFiles) {
    $stagedFiles | ForEach-Object {
        if ($_ -match '^A\s+(.+)$') {
            Write-Host "  Added: $($matches[1])" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  No new files to commit" -ForegroundColor Yellow
}

Write-Host "Files added to staging" -ForegroundColor Green

# Create initial commit
Write-Host "Creating initial commit..." -ForegroundColor Cyan

git commit -m "feat: initial release of BackupUSSY v1.0.0 - Complete LTO tape archiving solution"
Write-Host "Initial commit created" -ForegroundColor Green

# Show next steps
Write-Host ""
Write-Host "Git repository initialized successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps to publish on GitHub:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create a new repository on GitHub named 'backupussy'" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Add the remote and push:" -ForegroundColor Cyan
Write-Host "   git remote add origin https://github.com/KyleDurepos/backupussy.git" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Create your first release:" -ForegroundColor Cyan
Write-Host "   .\create_release.ps1 -Version '1.0.0'" -ForegroundColor Yellow
Write-Host "   git tag v1.0.0" -ForegroundColor Yellow
Write-Host "   git push origin v1.0.0" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. GitHub will automatically create the release!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your project is ready to go live!" -ForegroundColor Green

