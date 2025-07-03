# Aetherius Component: Web

> Aetherius 的官方图形化界面，将复杂的服务端管理任务转化为直观、流畅的点击操作。

## 🎯 项目概述

Component: Web 是 Aetherius 的可选图形化界面组件，提供：

- 🖥️ **实时控制台** - 完美复刻服务器控制台体验
- 📊 **状态仪表盘** - 服务器性能监控和可视化
- 👥 **玩家管理** - 可视化的玩家数据管理
- 📁 **文件管理器** - 安全的网页文件管理
- 🔌 **WebSocket 实时通信** - 实时数据更新和交互

## 🏗️ 技术架构

### 后端 (Backend)
- **框架**: FastAPI + Uvicorn
- **通信**: REST API + WebSocket
- **集成**: 与 Aetherius Core 完全解耦

### 前端 (Frontend)
- **框架**: Vue 3 + Vite + TypeScript
- **UI库**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts

## 🚀 快速开始

### 系统要求

- Python 3.8+
- Node.js 18+
- npm 或 yarn

### 安装和设置

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd Component-Web
   ```

2. **运行设置脚本**
   ```bash
   ./scripts/setup.sh
   ```

3. **启动开发环境**
   ```bash
   ./scripts/start-dev.sh
   ```

4. **访问应用**
   - 前端界面: http://localhost:3000
   - 后端API: http://localhost:8000
   - API文档: http://localhost:8000/docs

### 手动设置

如果自动脚本无法使用，可以手动设置：

**后端设置:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端设置:**
```bash
cd frontend
npm install
npm run dev
```

## 📁 项目结构

```
Component-Web/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # REST API 路由
│   │   ├── websocket/      # WebSocket 处理
│   │   ├── core/           # 核心引擎集成
│   │   ├── models/         # 数据模型
│   │   └── utils/          # 工具函数
│   ├── tests/              # 后端测试
│   └── requirements.txt    # Python 依赖
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── components/     # Vue 组件
│   │   ├── views/          # 页面组件
│   │   ├── stores/         # 状态管理
│   │   ├── utils/          # 工具函数
│   │   └── types/          # TypeScript 类型
│   └── package.json        # Node.js 依赖
├── scripts/                # 构建和部署脚本
├── docs/                   # 项目文档
└── README.md
```

## 🔧 开发指南

### 后端开发

**启动开发服务器:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**运行测试:**
```bash
cd backend
pytest
```

**代码格式化:**
```bash
cd backend
black .
isort .
```

### 前端开发

**启动开发服务器:**
```bash
cd frontend
npm run dev
```

**构建生产版本:**
```bash
cd frontend
npm run build
```

**代码检查:**
```bash
cd frontend
npm run lint
```

**类型检查:**
```bash
cd frontend
npm run type-check
```

## 🌐 API 文档

后端启动后，访问 http://localhost:8000/docs 查看完整的 API 文档。

### 主要端点

- `GET /health` - 健康检查
- `GET /api/v1/server/status` - 服务器状态
- `POST /api/v1/console/command` - 执行控制台命令
- `WS /api/v1/console/ws` - 控制台 WebSocket

## 🔌 WebSocket 通信

### 控制台 WebSocket

**连接:** `ws://localhost:8000/api/v1/console/ws`

**发送命令:**
```json
{
  "type": "command",
  "command": "say Hello World",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

**接收日志:**
```json
{
  "type": "console_log",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "level": "INFO",
    "source": "Server",
    "message": "Hello World"
  }
}
```

## 🧪 测试

### 单元测试

**后端测试:**
```bash
cd backend
pytest tests/ -v
```

**前端测试:**
```bash
cd frontend
npm run test
```

### 集成测试

```bash
# 启动后端和前端后
npm run test:e2e
```

## 📊 当前开发状态

### ✅ Sprint 1 (已完成)
- [x] FastAPI 项目结构
- [x] Vue 3 前端项目
- [x] WebSocket 双向通信
- [x] 实时控制台功能
- [x] 核心引擎集成接口

### 🚧 即将开发
- [ ] Sprint 2: 仪表盘模块
- [ ] Sprint 3: 玩家管理
- [ ] Sprint 4: 文件管理器

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送到分支: `git push origin feature/new-feature`
5. 提交 Pull Request

### 代码规范

- 后端遵循 PEP 8 规范
- 前端使用 ESLint + Prettier
- 提交信息遵循 Conventional Commits

## 📝 许可证

本项目基于 MIT 许可证开源。

## 🆘 故障排除

### 常见问题

**1. 端口占用**
```bash
# 查找占用端口的进程
lsof -i :8000
lsof -i :3000

# 终止进程
kill -9 <PID>
```

**2. 依赖安装失败**
```bash
# 清理缓存
npm cache clean --force
pip cache purge

# 重新安装
rm -rf node_modules package-lock.json
npm install
```

**3. WebSocket 连接失败**
- 确保后端服务器正在运行
- 检查防火墙设置
- 验证 CORS 配置

### 获取帮助

- 查看 [技术文档](./docs/)
- 提交 [Issue](./issues)
- 查看 [Wiki](./wiki)

## 📞 联系方式

- 项目维护者: Aetherius Team
- 问题反馈: GitHub Issues
- 文档: 项目 Wiki

---

**注意**: 这是一个开发中的项目，API 和功能可能会发生变化。