@echo off
echo Python Module ж��

@set "PATH=C:\Windows\System32;.\Python\Scripts;.\Python"

:restart
set /p var="python -m pip uninstall "
cls
echo ��ʼж��

python -m pip uninstall %var%

goto restart