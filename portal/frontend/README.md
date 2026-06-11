# 智审门户前端

这是独立部署的门户页面工程，不依赖主系统 `frontend` 的路由与布局。

## 本地开发

```bash
npm install
npm run dev
```

默认开发地址为 `http://127.0.0.1:5174/`。

## 构建部署

```bash
npm run build
```

构建产物输出到 `dist/`，可由 Nginx、对象存储或任意静态站点服务单独部署。

## Docker 部署

```bash
docker build -t contract-review-portal .
docker run --rm -p 8080:80 contract-review-portal
```

容器启动后访问 `http://127.0.0.1:8080/`。
