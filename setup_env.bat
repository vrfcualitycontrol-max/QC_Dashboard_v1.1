@echo off
chcp 65001 >nul
echo ====================================================
echo Настройка рабочего окружения для QC Dashboard v1.1
echo ====================================================
echo.

set PROJECT_DIR=C:\Проекты\QC Dashboard v1.1

if not "%cd%"=="%PROJECT_DIR%" (
    echo [ВНИМАНИЕ] Скрипт запущен не из %PROJECT_DIR%
    echo Убедитесь, что вы перенесли папку проекта именно по этому пути.
    echo Текущая папка: %cd%
    echo.
)

echo [1] Проверка наличия Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден. Пожалуйста, установите Python ^(обязательно поставьте галочку "Add Python to PATH"^).
    pause
    exit /b
)

echo [2] Проверка наличия файла конфигурации .env...
if not exist .env (
    echo Создаю .env из .env.example...
    copy .env.example .env >nul
    echo Файл .env успешно создан.
) else (
    echo Файл .env уже существует, пропускаю создание.
)

echo [3] Создание виртуального окружения Python...
if not exist venv (
    python -m venv venv
    echo Виртуальное окружение venv создано.
) else (
    echo Виртуальное окружение уже существует.
)

echo [4] Активация окружения и установка зависимостей...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ====================================================
echo Готово! Окружение успешно настроено.
echo.
echo Для запуска авто-обновления данных (auto_updater.py):
echo 1. Откройте консоль в этой папке
echo 2. Введите: venv\Scripts\activate
echo 3. Введите: python auto_updater.py
echo.
echo Подробные инструкции читайте в файле MIGRATION_GUIDE.md
echo ====================================================
pause
