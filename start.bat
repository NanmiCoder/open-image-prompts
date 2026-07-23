@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 (
  echo.
  echo Error: Could not open the project directory "%~dp0".
  exit /b 1
)

echo.
echo [1/4] Preparing Git LFS data...
where git >nul 2>nul
if errorlevel 1 (
  echo.
  echo Error: Git is required: https://git-scm.com/downloads
  goto :fail
)
git lfs version >nul 2>nul
if errorlevel 1 (
  echo.
  echo Error: Git LFS is required: https://git-lfs.com/
  goto :fail
)
git lfs install --local
if errorlevel 1 goto :fail
git lfs pull
if errorlevel 1 goto :fail
if not exist "%CD%\db\prompts.db.gz" (
  echo.
  echo Error: The public database is missing. Clone this repository with Git LFS enabled.
  goto :fail
)
for %%F in ("%CD%\db\prompts.db.gz") do if %%~zF LSS 1024 (
  echo.
  echo Error: The public database is still a Git LFS pointer. Run git lfs pull and try again.
  goto :fail
)

echo.
echo [2/4] Preparing Python with uv...
set "UV_EXE="
set "UV_INSTALL_DIR=%CD%\.oip\tools\uv"
for /f "delims=" %%I in ('where uv 2^>nul') do if not defined UV_EXE set "UV_EXE=%%I"
if not defined UV_EXE if exist "%UV_INSTALL_DIR%\uv.exe" set "UV_EXE=%UV_INSTALL_DIR%\uv.exe"
if not defined UV_EXE (
  where powershell >nul 2>nul
  if errorlevel 1 (
    echo.
    echo Error: PowerShell is required to install uv: https://docs.astral.sh/uv/getting-started/installation/
    goto :fail
  )
  set "UV_NO_MODIFY_PATH=1"
  powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; irm https://astral.sh/uv/install.ps1 | iex"
  if errorlevel 1 goto :fail
)
if not defined UV_EXE if defined UV_INSTALL_DIR if exist "%UV_INSTALL_DIR%\uv.exe" set "UV_EXE=%UV_INSTALL_DIR%\uv.exe"
if not defined UV_EXE (
  echo.
  echo Error: uv was installed but its executable could not be found.
  goto :fail
)
"%UV_EXE%" sync --locked
if errorlevel 1 goto :fail

echo.
echo [3/4] Installing frontend dependencies...
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo Error: Node.js 20.19+ or 22.12+ is required: https://nodejs.org/
  goto :fail
)
where npm >nul 2>nul
if errorlevel 1 (
  echo.
  echo Error: npm is required and normally ships with Node.js: https://nodejs.org/
  goto :fail
)
node -e "const [major, minor] = process.versions.node.split('.').map(Number); if (!((major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major > 22)) { console.error('Node.js ' + process.versions.node + ' is unsupported. Install Node.js 20.19+ or 22.12+.'); process.exit(1) }"
if errorlevel 1 goto :fail
call npm.cmd --prefix web ci
if errorlevel 1 goto :fail

echo.
echo [4/4] Starting Open Image Prompts...
set "OIP_PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%OIP_PYTHON%" (
  echo.
  echo Error: uv did not create the expected Python environment at "%OIP_PYTHON%"
  goto :fail
)
node web\scripts\with_api.mjs dev
set "OIP_EXIT_CODE=%ERRORLEVEL%"
goto :done

:fail
set "OIP_EXIT_CODE=1"

:done
popd
endlocal & exit /b %OIP_EXIT_CODE%
