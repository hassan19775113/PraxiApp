<#
 PraxisSoftware – Einfacher On-Prem Installer (Windows)
 Voraussetzungen:
 - PraxisSoftware.zip liegt im gleichen Ordner wie dieses Script
 - PostgreSQL-Installer liegt im gleichen Ordner (z.B. postgresql-16.11-2-windows-x64.exe)
 - Python 3.x im PATH
 - PowerShell als Administrator ausführen
 Hinweis: Immer frische PostgreSQL-16-Installation, keine Re-Use/Upgrades.
#>

$ErrorActionPreference = "Stop"  # bricht bei Fehlern ab

# ------------------ Logging ------------------
$ScriptRoot  = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallRoot = "C:\PraxisSoftware"
$AppRoot     = Join-Path $InstallRoot "app"
$LogDir      = Join-Path $InstallRoot "logs"
$LogFile     = Join-Path $LogDir "installer.log"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    "$ts  $Message" | Tee-Object -FilePath $LogFile -Append
}
Write-Log "=== PraxisSoftware Installer gestartet ==="

# ------------------ Admin-Check ------------------
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Log "FEHLER: Bitte PowerShell als Administrator ausführen."
    Read-Host "ENTER zum Beenden"
    exit 1
}

# ------------------ Basis-Variablen ------------------
$ZipPath          = Join-Path $ScriptRoot "PraxisSoftware.zip"
$PgInstaller      = Join-Path $ScriptRoot "postgresql-16.11-2-windows-x64.exe"
$PgPrefix         = "C:\Program Files\PostgreSQL\16"
$PgDataDir        = Join-Path $InstallRoot "postgres\data"
$PgServiceName    = "PraxisPostgres"
$PgSuperPassword  = "PraxisPass123!"   # Passwort des Postgres-Superusers
$PgServicePass    = $PgSuperPassword    # gleiches Passwort fuer Dienst
$DbName           = "praxis_db"
$DbUser           = "praxis_user"
$DbPassword       = "PraxisPass123!"   # Passwort fuer die App-DB
$PgPort           = 5432
$NginxDir         = Join-Path $InstallRoot "nginx"
$BackupsDir       = Join-Path $InstallRoot "backups"
$PostgresDir      = Join-Path $InstallRoot "postgres"

# ------------------ PostgreSQL Vor-Check (kein Re-Use) ------------------
$existingPg = Get-Service -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "postgres" -or $_.DisplayName -match "postgres" }
if ($existingPg) {
    $names = ($existingPg | Select-Object -ExpandProperty Name) -join ", "
    Write-Log "FEHLER: Bereits vorhandener PostgreSQL-Dienst gefunden ($names). Bitte komplett entfernen und Script erneut starten."
    Read-Host "ENTER zum Beenden"
    exit 1
}
# falls altes Zielverzeichnis existiert, abbrechen statt mergen
if (Test-Path $PgPrefix -or Test-Path $PgDataDir) {
    Write-Log "FEHLER: PostgreSQL-Zielpfade existieren bereits ($PgPrefix oder $PgDataDir). Bitte alte Installation entfernen."
    Read-Host "ENTER zum Beenden"
    exit 1
}
# Port-Check auf 5432
$portInUse = $null
try {
    $portInUse = Get-NetTCPConnection -State Listen -LocalPort $PgPort -ErrorAction Stop
} catch {
    Write-Log "HINWEIS: Port-Check per Get-NetTCPConnection nicht moeglich, bitte Port $PgPort manuell pruefen."
}
if ($portInUse) {
    Write-Log "FEHLER: Port $PgPort ist bereits belegt. Bitte Port freigeben und Script erneut starten."
    Read-Host "ENTER zum Beenden"
    exit 1
}

# ------------------ 1) Ordnerstruktur ------------------
Write-Log "Erstelle Basis-Verzeichnisse..."
$dirs = @($InstallRoot, $AppRoot, $LogDir, $BackupsDir, $NginxDir, $PostgresDir)
foreach ($d in $dirs) { New-Item -ItemType Directory -Path $d -Force | Out-Null }

# ------------------ 2) ZIP entpacken ------------------
if (-not (Test-Path $ZipPath)) {
    Write-Log "FEHLER: PraxisSoftware.zip nicht gefunden im Ordner: $ScriptRoot"
    Read-Host "ENTER zum Beenden"
    exit 1
}
if (Test-Path $AppRoot) { Remove-Item $AppRoot -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $AppRoot -Force | Out-Null
Write-Log "Entpacke ZIP nach $AppRoot..."
try {
    Expand-Archive -Path $ZipPath -DestinationPath $AppRoot -Force
} catch {
    Write-Log "FEHLER: Entpacken fehlgeschlagen. ZIP defekt oder fehlende Rechte? Fehler: $_"
    Read-Host "ENTER zum Beenden"
    exit 1
}

# ------------------ 3) Python + venv ------------------
Write-Log "Erstelle Python-venv..."
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Log "FEHLER: Python nicht gefunden. Bitte Python 3 im PATH installieren und erneut starten."
    Read-Host "ENTER zum Beenden"
    exit 1
}
$VenvPath = Join-Path $AppRoot "venv"
try {
    python -m venv $VenvPath
} catch {
    Write-Log "FEHLER: venv-Erstellung fehlgeschlagen. Ursache: $_"
    Read-Host "ENTER zum Beenden"
    exit 1
}
$PyExe  = Join-Path $VenvPath "Scripts\python.exe"
$PipExe = Join-Path $VenvPath "Scripts\pip.exe"
if (-not (Test-Path $PyExe)) {
    Write-Log "FEHLER: venv konnte nicht erstellt werden. Ist Python im PATH?"
    Read-Host "ENTER zum Beenden"
    exit 1
}
$Req = Join-Path $AppRoot "requirements.txt"
if (-not (Test-Path $Req)) {
    Write-Log "FEHLER: requirements.txt nicht gefunden: $Req"
    Read-Host "ENTER zum Beenden"
    exit 1
}
Write-Log "Installiere Python-Abhängigkeiten..."
try {
    & $PipExe install -r $Req
} catch {
    Write-Log "FEHLER: pip-Installation fehlgeschlagen. Internet/Proxy prüfen. Fehler: $_"
    Read-Host "ENTER zum Beenden"
    exit 1
}

# ------------------ 4) PostgreSQL installieren ------------------
if (-not (Test-Path $PgInstaller)) {
    Write-Log "FEHLER: PostgreSQL-Installer fehlt: $PgInstaller"
    Read-Host "ENTER zum Beenden"
    exit 1
} else {
    Write-Log "Starte PostgreSQL Silent-Install..."
    # sicherstellen, dass Zielpfade leer sind
    if (Test-Path $PgDataDir) { Remove-Item $PgDataDir -Recurse -Force -ErrorAction SilentlyContinue }
    $pgArgs = @(
        "--mode", "unattended",
        "--unattendedmodeui", "none",
        "--superpassword", $PgSuperPassword,
        "--servicename", $PgServiceName,
        "--servicepassword", $PgServicePass,
        "--datadir", $PgDataDir,
        "--prefix", $PgPrefix,
        "--locale", "en_US",
        "--encoding", "UTF8"
    )
    try {
        Start-Process -FilePath $PgInstaller -ArgumentList $pgArgs -Wait -NoNewWindow -PassThru | Out-Null
    } catch {
        Write-Log "FEHLER: PostgreSQL-Installation fehlgeschlagen. Installer/Logs pruefen. Fehler: $_"
        Read-Host "ENTER zum Beenden"
        exit 1
    }
}

# ------------------ 5) DB anlegen ------------------
Write-Log "Lege Datenbank und Benutzer an (falls PostgreSQL läuft)..."
$psql = Join-Path $PgPrefix "bin\psql.exe"
if (Test-Path $psql) {
    $env:PGPASSWORD = $PgSuperPassword
    try {
        & $psql -h localhost -p $PgPort -U postgres -d postgres -c "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$DbUser') THEN CREATE ROLE $DbUser LOGIN PASSWORD '$DbPassword'; END IF; END $$;"
        & $psql -h localhost -p $PgPort -U postgres -d postgres -c "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$DbName') THEN CREATE DATABASE $DbName OWNER $DbUser; END IF; END $$;"
    } catch {
        Write-Log "FEHLER: DB/Role-Anlage fehlgeschlagen. psql-Logs/Port/Passwort pruefen. Fehler: $_"
        Read-Host "ENTER zum Beenden"
        exit 1
    } finally {
        $env:PGPASSWORD = $null
    }
} else {
    Write-Log "FEHLER: psql nicht gefunden unter $psql. Bitte Installation pruefen."
    Read-Host "ENTER zum Beenden"
    exit 1
}

# ------------------ 6) .env erzeugen ------------------
Write-Log "Erzeuge .env aus env_template..."
$ConfigDir   = Join-Path $AppRoot "config"
$EnvTemplate = Join-Path $ConfigDir "env_template.txt"
$EnvFile     = Join-Path $ConfigDir ".env"
if (-not (Test-Path $EnvTemplate)) {
    Write-Log "FEHLER: env_template.txt nicht gefunden."
    Read-Host "ENTER zum Beenden"
    exit 1
}
$secret = [Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N")
try {
    (Get-Content $EnvTemplate) `
        -replace "SECRET_KEY=", "SECRET_KEY=$secret" `
        -replace "DB_NAME=.*", "DB_NAME=$DbName" `
        -replace "DB_USER=.*", "DB_USER=$DbUser" `
        -replace "DB_PASSWORD=.*", "DB_PASSWORD=$DbPassword" `
        -replace "DB_HOST=.*", "DB_HOST=localhost" `
        -replace "DB_PORT=.*", "DB_PORT=$PgPort" `
        -replace "ALLOWED_HOSTS=.*", "ALLOWED_HOSTS=localhost,127.0.0.1,praxis-server" `
        -replace "LICENSE_KEY=.*", "LICENSE_KEY=PLEASE_SET" `
        -replace "CUSTOMER_ID=.*", "CUSTOMER_ID=PLEASE_SET" `
        | Set-Content $EnvFile
} catch {
    Write-Log "FEHLER: .env konnte nicht erstellt werden. Pfad/Rechte pruefen. Fehler: $_"
    Read-Host "ENTER zum Beenden"
    exit 1
}
Write-Log ".env erstellt: $EnvFile"

# ------------------ 7) Django: migrate + collectstatic ------------------
Write-Log "Führe Django-Migrationen aus..."
$ManagePy = Join-Path $AppRoot "manage.py"
if (-not (Test-Path $ManagePy)) {
    Write-Log "FEHLER: manage.py nicht gefunden unter $ManagePy"
    Read-Host "ENTER zum Beenden"
    exit 1
}
Push-Location $AppRoot
try {
    & $PyExe $ManagePy migrate
} catch {
    Write-Log "FEHLER: migrate fehlgeschlagen. DB-Verbindung/ENV pruefen. Fehler: $_"
    Pop-Location
    Read-Host "ENTER zum Beenden"
    exit 1
}
Write-Log "Sammle statische Dateien..."
try {
    & $PyExe $ManagePy collectstatic --noinput
} catch {
    Write-Log "FEHLER: collectstatic fehlgeschlagen. STATIC_ROOT/Rechte pruefen. Fehler: $_"
    Pop-Location
    Read-Host "ENTER zum Beenden"
    exit 1
}
Pop-Location

# ------------------ 8) Test-Start Gunicorn (optional) ------------------
Write-Log "Starte Test-Run von Gunicorn (manuell zu prüfen)..."
$GunicornExe = Join-Path $VenvPath "Scripts\gunicorn.exe"
if (Test-Path $GunicornExe) {
    Write-Log "Testaufruf: \"$GunicornExe project.wsgi:application --chdir $AppRoot --bind 127.0.0.1:8000\""
} else {
    Write-Log "HINWEIS: gunicorn nicht gefunden. Ist es in requirements.txt?"
}

Write-Log "=== Installation abgeschlossen ==="
Write-Host ""
Write-Host "PraxisSoftware wurde vorbereitet."
Write-Host "Pruefe nun:"
Write-Host "- PostgreSQL laeuft"
Write-Host "- Starte Gunicorn (siehe Log-Hinweis)"
Write-Host "- Rufe im Browser auf: http://localhost/"
Write-Host ""
Read-Host "ENTER zum Beenden"
