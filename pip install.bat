@echo off
echo Python Module ��װ

@set "PATH=C:\Windows\System32;.\Python\Scripts;.\Python"

:restart
set /p var="python -m pip install "
cls
echo ��ʼ��װ

python -m pip install %var% --target .\Python\Lib\site-packages

goto restart