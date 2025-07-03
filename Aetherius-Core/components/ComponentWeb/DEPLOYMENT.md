# Aetherius Web Component 部署指南

## 环境配置

### 本地开发环境

1. 复制环境变量模板：
```bash
cd frontend
cp .env.example .env
```

2. 默认配置适用于本地开发：
- 后端API: http://localhost:8000
- 前端开发服务器: http://localhost:3000
- WebSocket: ws://localhost:8000

### 云开发环境 (GitHub Codespaces, GitPod等)

在 `frontend/.env` 文件中配置：

```bash
# 使用完整的WebSocket URL
VITE_WS_BASE_URL=wss://your-backend-domain/api/v1

# 如果API也需要外部访问
VITE_API_BASE_URL=https://your-backend-domain/api/v1
```

### 生产环境

```bash
# 生产环境配置示例
VITE_API_BASE_URL=https://your-production-domain.com/api/v1
VITE_WS_BASE_URL=wss://your-production-domain.com/api/v1
```

## 启动方式

### 通过Aetherius组件系统启动（推荐）

```bash
# 启动Aetherius服务器
python -m aetherius server start

# 启用Web组件（自动启动前后端）
python -m aetherius component enable ComponentWeb
```

### 手动启动

```bash
# 启动后端
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
npm install
npm run dev
```

## 端口说明

- **3000**: 前端开发服务器
- **8000**: 后端API服务器
- **WebSocket**: 通过8000端口的WebSocket端点

## 故障排除

### WebSocket连接失败

1. 检查后端服务器是否在8000端口运行
2. 确认防火墙/代理设置允许WebSocket连接
3. 在云环境中，确保WebSocket URL正确配置
4. 检查浏览器控制台的具体错误信息

### API请求失败

1. 确认CORS设置正确
2. 检查API基础URL配置
3. 验证后端服务器可访问性