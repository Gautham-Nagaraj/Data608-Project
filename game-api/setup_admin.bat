@echo off
echo Creating default admin user for Stock Roulette Game...
echo.

REM Run database migrations first
echo Running database migrations...
uv run -- alembic upgrade head
if %ERRORLEVEL% neq 0 (
    echo Migration failed!
    exit /b 1
)
echo Migrations completed successfully.
echo.

REM Create admin user
echo Creating default admin user...
python create_default_admin.py
if %ERRORLEVEL% neq 0 (
    echo Admin creation failed!
    exit /b 1
)

echo.
echo ==================================================
echo Setup completed successfully!
echo.
echo Login credentials:
echo   Username: admin
echo   Password: data608
echo.
echo Admin endpoints:
echo   Login: POST /api/admin/login
echo   Dashboard: GET /api/admin/dashboard
echo ==================================================
echo.
echo WARNING: Change the default password in production!
echo.
pause
