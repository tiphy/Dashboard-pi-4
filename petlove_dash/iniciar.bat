@echo off
title PetLove Dashboard
cd /d "%~dp0"

rem --- 1) procura o Python
set PY=
where py >nul 2>nul
if %errorlevel%==0 set PY=py
if "%PY%"=="" (
  where python >nul 2>nul
  if %errorlevel%==0 set PY=python
)
if "%PY%"=="" goto sem_python

rem --- 2) cria ambiente virtual na primeira vez
if not exist ".venv\Scripts\activate.bat" (
  echo Criando ambiente virtual ^(so na primeira vez^)...
  %PY% -m venv .venv
  if errorlevel 1 goto erro
)
call ".venv\Scripts\activate.bat"

rem --- 3) instala dependencias na primeira vez
if not exist ".venv\.instalado" (
  echo Instalando dependencias ^(so na primeira vez, pode levar alguns minutos^)...
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  if errorlevel 1 goto erro
  echo ok> ".venv\.instalado"
)

rem --- 4) evita o pedido de e-mail do Streamlit
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  mkdir "%USERPROFILE%\.streamlit" 2>nul
  (echo [general]& echo email = "") > "%USERPROFILE%\.streamlit\credentials.toml"
)

rem --- 5) gera dados de exemplo se a pasta dados estiver vazia
if not exist "dados\dados.json" python gerar_dados_exemplo.py

echo.
echo Abrindo o dashboard no navegador... ^(feche esta janela para encerrar^)
python -m streamlit run app.py
goto fim

:sem_python
echo.
echo Python nao encontrado. Instale em https://www.python.org/downloads/
echo e marque a opcao "Add Python to PATH" durante a instalacao.
goto fim

:erro
echo.
echo Ocorreu um erro. Copie a mensagem acima e me envie.

:fim
echo.
pause
