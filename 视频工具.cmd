@echo off
chcp 65001 >nul
setlocal
rem Video hosting helper for Tencent COS.
rem Commands: check / ls / upload / sign / verify / publish
rem Example: video-tool.cmd check

set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%.tools\pylibs"
set "PY=C:\Users\dell\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

if exist "%PY%" goto run
set "PY=python"

:run
"%PY%" "%ROOT%scripts\cos-tool.py" %*
