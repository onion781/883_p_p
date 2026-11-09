@echo off
setlocal
pushd "%~dp0" || exit /b 1

if not exist ".venv\Scripts\python.exe" (
    echo SmartCampus needs its Python environment. Follow the setup steps in README.md.
    pause
    popd
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
set "APP_EXIT=%ERRORLEVEL%"
if not "%APP_EXIT%"=="0" (
    echo SmartCampus stopped with exit code %APP_EXIT%.
    pause
)
popd
exit /b %APP_EXIT%
