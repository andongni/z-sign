# 后端 API 文档

后端已迁移为 FastAPI + SQLAlchemy，接口前缀仍为 `/api`，前端无需调整 baseURL。

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env  # 如存在
```

3. 初始化数据库表：
```bash
python manage.py init-db
```

4. 创建或更新管理员：
```bash
python manage.py create-admin --username admin --email admin@example.com --password your-password
```

5. 启动开发服务器：
```bash
python manage.py runserver 8000
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 文档

- Swagger: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- 健康检查: `http://localhost:8000/api/health/`

## 兼容说明

- 登录接口仍为 `POST /api/auth/login/`，返回 `access` 和 `refresh`。
- 列表接口仍返回 DRF 风格分页：`count / next / previous / results`。
- 原 MySQL 表名保持不变，例如 `users_user`、`contracts_contract`、`reviews_review_task`。
- 原 Django `pbkdf2_sha256` 密码哈希可继续登录，新建用户也使用兼容哈希。
- Celery 已移除，审核任务通过 FastAPI 接口同步执行。

