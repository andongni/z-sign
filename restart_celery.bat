@echo off
chcp 65001 >nul
echo ========================================
echo Celery 已移除
echo ========================================
echo.
echo 后端已迁移到 FastAPI，审核任务通过接口同步执行，不再需要 Celery Worker。
echo 请使用 start_backend.bat 启动后端。
pause >nul
