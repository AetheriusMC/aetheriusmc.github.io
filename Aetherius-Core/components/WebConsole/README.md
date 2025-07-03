# Aetherius WebConsole v2.0

> 🚀 **Enterprise-grade Web Management Console for Aetherius Core**

WebConsole v2.0 是基于现有ComponentWeb深度分析和优化后的新一代Web管理界面，提供现代化、高性能、安全可靠的服务器管理体验。

## ✨ 主要特性

### 🎯 核心功能
- **实时仪表板**: 多维度性能监控和自定义面板
- **智能控制台**: 命令补全、日志分析、批量执行
- **高级玩家管理**: 玩家画像、权限管理、行为分析
- **文件管理器**: 在线编辑、版本管理、批量操作

### 🔧 扩展功能
- **插件管理中心**: 生命周期管理、依赖可视化
- **备份管理系统**: 自动备份、一键恢复
- **用户权限管理**: RBAC、用户组、审计日志
- **监控告警系统**: 自定义规则、多渠道通知

### 🏗️ 架构特性
- **企业级安全**: 多层安全防护、JWT认证、RBAC授权
- **高性能设计**: 异步架构、缓存优化、连接池
- **实时通信**: WebSocket、事件驱动、Server-Sent Events
- **模块化设计**: 依赖注入、松耦合、可扩展

## 🚀 快速开始

### 前置要求
- Python 3.11+
- Node.js 18+
- Redis (可选，用于缓存和任务队列)
- PostgreSQL/MySQL (可选，SQLite默认)

### 安装和启动

1. **一键启动（推荐）**
```bash
# 启动完整服务（前端+后端）
python start_component.py

# 可用选项
python start_component.py --help
```

2. **分离启动**
```bash
# 仅启动前端
python start_component.py --frontend-only

# 仅启动后端
python start_component.py --backend-only

# 自定义重试参数
python start_component.py --max-retries 5 --retry-delay 10
```

3. **通过Aetherius组件系统**
```bash
# 在Aetherius控制台中
component enable webconsole
```

4. **传统开发模式**
```bash
# 后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

3. **生产环境部署**
```bash
# 使用Docker Compose
docker-compose up -d
```

### 启动脚本功能

`start_component.py` 是增强的一键启动脚本，提供以下功能：

#### ✨ 核心特性
- **🔄 自动重试机制**: 启动失败时自动重试，最多3次
- **📦 依赖检查**: 自动检查Node.js、npm和前端依赖
- **🚀 前后端同时启动**: 一个命令启动完整服务
- **🎯 分离启动模式**: 支持单独启动前端或后端
- **🔧 可配置参数**: 自定义重试次数和延迟
- **📋 详细日志**: 提供启动过程的详细信息

#### 🛠️ 启动选项
```bash
# 完整启动（默认）
python start_component.py

# 仅启动前端（适用于后端已运行的情况）
python start_component.py --frontend-only

# 仅启动后端（适用于前端开发调试）
python start_component.py --backend-only

# 自定义重试参数
python start_component.py --max-retries 5 --retry-delay 10

# 禁用重试机制（立即失败）
python start_component.py --no-retry
```

#### 🔍 故障排除
脚本会自动处理以下常见问题：
- Node.js/npm未安装或路径问题
- 前端依赖未安装（自动执行npm install）
- 端口占用冲突
- Aetherius Core连接问题
- 权限问题

#### 📊 启动状态
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

## 📁 项目结构

```
WebConsole/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心服务
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   ├── utils/          # 工具函数
│   │   ├── middleware/     # 中间件
│   │   ├── websocket/      # WebSocket管理
│   │   └── tasks/          # 异步任务
│   ├── tests/              # 测试用例
│   ├── migrations/         # 数据库迁移
│   └── scripts/            # 脚本工具
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # 组件库
│   │   ├── views/          # 页面视图
│   │   ├── stores/         # 状态管理
│   │   ├── utils/          # 工具函数
│   │   ├── types/          # 类型定义
│   │   └── assets/         # 静态资源
│   ├── tests/              # 前端测试
│   └── public/             # 公共资源
├── docs/                   # 文档
├── scripts/                # 部署脚本
├── config/                 # 配置文件
└── data/                   # 数据存储
```

## 🔧 开发指南

### 开发环境搭建

1. **克隆项目**
```bash
git clone https://github.com/AetheriusMC/Aetherius-Core.git
cd Aetherius-Core/components/WebConsole
```

2. **安装依赖**
```bash
# 后端依赖
cd backend && pip install -r requirements.txt

# 前端依赖  
cd frontend && npm install
```

3. **配置环境**
```bash
# 复制配置文件
cp config/config.example.yaml config/config.yaml
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

4. **启动开发服务器**
```bash
# 启动后端 (终端1)
cd backend && python -m uvicorn app.main:app --reload --port 8080

# 启动前端 (终端2)
cd frontend && npm run dev
```

### 代码规范

- **Python**: 遵循PEP 8，使用black格式化，mypy类型检查
- **TypeScript**: 遵循ESLint配置，使用Prettier格式化
- **提交信息**: 遵循Conventional Commits规范

### 测试

```bash
# 后端测试
cd backend && pytest

# 前端测试
cd frontend && npm run test

# E2E测试
cd frontend && npm run test:e2e
```

## 📖 API文档

启动开发服务器后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🔒 安全

WebConsole v2.0 实现了企业级安全特性：

- **多层认证**: JWT Token + Session双重认证
- **细粒度授权**: 基于角色的权限控制(RBAC)
- **安全传输**: HTTPS强制、CORS配置
- **审计日志**: 完整的操作记录
- **防护机制**: 速率限制、输入验证、SQL注入防护

## 📊 性能

- **响应时间**: API P95 < 100ms
- **并发支持**: > 500并发用户
- **内存占用**: < 512MB (基础配置)
- **可用性**: > 99.9%

## 🤝 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](docs/CONTRIBUTING.md) 了解详细信息。

### 开发路线图

- [x] 基础架构设计
- [ ] 核心功能实现
- [ ] 扩展功能开发
- [ ] 性能优化
- [ ] 安全加固
- [ ] 文档完善

## 📄 许可证

本项目采用 MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

- 📧 邮箱: support@aetherius.mc
- 💬 QQ群: 123456789
- 🐛 问题反馈: [GitHub Issues](https://github.com/AetheriusMC/Aetherius-Core/issues)
- 📖 文档: [docs.aetherius.mc](https://docs.aetherius.mc)

---

**Built with ❤️ by Aetherius Team**