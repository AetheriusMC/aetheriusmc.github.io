# Aetherius核心集成指南

## 概述

本文档说明了Component: Web如何与Aetherius核心系统集成，以及如何在核心环境中部署和使用。

## 组件架构适配

### 1. 组件信息定义

组件信息在`backend/component_info.py`中定义，符合Aetherius ComponentInfo规范：

```python
component_info = ComponentInfo(
    name="web",
    display_name="Web Console",
    description="Aetherius的官方图形化界面",
    version="0.1.0",
    # ...其他配置
)
```

### 2. 组件类实现

主组件类`WebComponent`继承自Aetherius的`Component`基类：

```python
class WebComponent(Component):
    async def on_load(self):    # 组件加载
    async def on_enable(self):  # 组件启用
    async def on_disable(self): # 组件禁用
    async def on_unload(self):  # 组件卸载
```

### 3. 事件处理

组件使用`@event_handler`装饰器监听核心事件：

- `server.start` - 服务器启动
- `server.stop` - 服务器停止
- `player.join` - 玩家加入
- `player.quit` - 玩家退出
- `console.log` - 控制台日志

## 部署方式

### 方式1: 作为Aetherius组件（推荐）

1. 将整个`Component-Web`目录放置到Aetherius的组件目录
2. 核心会自动发现并加载组件
3. 通过核心的组件管理命令控制组件

```bash
# 在Aetherius控制台中
component enable web
component disable web
component reload web
```

### 方式2: 独立运行（开发模式）

仍然支持独立运行用于开发和测试：

```bash
cd backend
python -m uvicorn app.main:app --reload
```

## 配置管理

### 核心集成配置

组件配置通过Aetherius的配置系统管理：

- 配置模式定义在`component_info.py`的`config_schema`中
- 默认配置在`default_config`中
- 运行时配置通过`self.config`访问

### 独立运行配置

独立运行时使用环境变量和配置文件：

- `.env`文件用于环境变量
- `config.yml`用于YAML配置

## API适配

### 核心接口适配器

`AetheriusCoreAdapter`类适配Aetherius核心接口：

```python
# 组件模式下
core_adapter = AetheriusCoreAdapter(component.core)
await core_adapter.send_console_command("say Hello")

# 独立模式下
core_client = CoreClient()
await core_client.send_command("say Hello")
```

### 统一API层

`CoreAPI`类提供统一的接口，自动检测运行模式：

```python
# 自动适配运行模式
api = CoreAPI(core_client_or_adapter)
result = await api.send_console_command("say Hello")
```

## 权限系统

组件需要以下权限：

- `aetherius.console.execute` - 执行控制台命令
- `aetherius.status.read` - 读取服务器状态
- `aetherius.players.read` - 读取玩家信息
- `aetherius.players.manage` - 管理玩家
- `aetherius.files.read` - 读取文件
- `aetherius.files.write` - 写入文件

## 事件流

### 启动流程

1. 核心加载组件 → `on_load()`
2. 核心启用组件 → `on_enable()`
3. 启动Web服务器
4. 注册事件监听器
5. 组件就绪

### 运行时事件

1. 核心事件 → 事件处理器
2. 处理器 → WebSocket广播
3. 前端接收实时更新

### 停止流程

1. 核心禁用组件 → `on_disable()`
2. 停止Web服务器
3. 清理连接
4. 组件卸载 → `on_unload()`

## 开发指南

### 本地开发

1. 独立运行后端和前端进行开发
2. 使用Mock数据测试功能
3. 完成后在核心环境中测试集成

### 组件测试

1. 在Aetherius环境中加载组件
2. 验证事件处理
3. 测试权限和配置
4. 确认Web界面功能

### 调试技巧

- 查看核心组件日志
- 使用浏览器开发者工具
- 监控WebSocket连接
- 检查权限错误

## 故障排除

### 常见问题

1. **组件加载失败**
   - 检查组件信息定义
   - 验证依赖项
   - 查看核心日志

2. **权限错误**
   - 确认权限配置
   - 检查用户权限
   - 验证组件权限声明

3. **Web服务器启动失败**
   - 检查端口占用
   - 验证配置参数
   - 查看错误日志

4. **事件不响应**
   - 确认事件处理器注册
   - 检查事件名称
   - 验证WebSocket连接

### 日志位置

- 核心日志：Aetherius日志目录
- 组件日志：`logs/web_component.log`
- Web访问日志：Web服务器日志

## 更新和维护

### 组件更新

1. 更新组件代码
2. 修改版本号
3. 重新加载组件

```bash
component reload web
```

### 配置更新

1. 修改配置文件
2. 重启组件

```bash
component restart web
```

### 前端更新

1. 构建新的前端代码
2. 替换静态文件
3. 清除浏览器缓存

## 性能优化

### 建议配置

- 调整WebSocket连接数限制
- 优化日志缓存大小
- 配置合适的超时时间
- 启用请求压缩

### 监控指标

- WebSocket连接数
- API响应时间
- 内存使用情况
- 错误率统计