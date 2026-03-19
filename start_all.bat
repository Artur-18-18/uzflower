@echo off
REM ============================================================
REM Скрипт запуска всех сервисов UzFlower
REM ============================================================

echo ============================================================
echo   UzFlower - Запуск всех сервисов
echo ============================================================
echo.

REM 1. Остановить все процессы Python
echo [1/4] Остановка всех процессов Python...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo.

REM 2. Проверка что процессы остановлены
echo [2/4] Проверка процессов...
tasklist | findstr python >nul 2>&1
if %errorlevel% equ 0 (
    echo [!] Внимание: Некоторые процессы Python всё ещё запущены
    echo     Вручную закройте их и перезапустите скрипт
) else (
    echo [+] Все процессы Python остановлены
)
echo.

REM 3. Запуск сервера
echo [3/4] Запуск API сервера (main.py)...
cd /d "%~dp0"
start /B python main.py
echo [+] Сервер запущен
timeout /t 5 /nobreak >nul
echo.

REM 4. Запуск Telegram бота
echo [4/4] Запуск Telegram бота (run_bot.py)...
start /B python run_bot.py
echo [+] Telegram бот запущен
echo.

REM 5. Запуск Admin бота (опционально)
echo [?] Запуск Admin бота...
set /p run_admin="Запустить Admin бота? (Y/N): "
if /i "%run_admin%"=="Y" (
    start /B python run_admin_bot.py
    echo [+] Admin бот запущен
)
echo.

echo ============================================================
echo   Все сервисы запущены!
echo ============================================================
echo.
echo Сервисы:
echo   - API Сервер:    http://localhost:8000
echo   - Telegram бот:  @uzflowershop_bot
echo   - Admin бот:     @uzfloweradmin_bot
echo.
echo Логи:
echo   - server_debug.log
echo   - bot_debug.log
echo   - admin_bot.log
echo.
echo Для остановки всех сервисов:
echo   taskkill /F /IM python.exe
echo ============================================================
