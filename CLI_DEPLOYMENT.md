# CLI 环境部署指南（无浏览器/无显示器）

如果你需要在没有浏览器的服务器或 CLI 环境中运行此应用，这里提供几种解决方案。

---

## 🚀 快速部署（推荐）

**适用场景：Linux 服务器/开发板，需要开机自启动和自动健康检查**

### 一键部署脚本

我们提供了自动化部署脚本，支持：
- ✅ 自动安装所有依赖
- ✅ 配置 systemd 服务
- ✅ 开机自启动
- ✅ 服务失败自动重启
- ✅ 健康检查：连续半小时查询日历失败会通过小爱音箱发送警报（仅在 17:00-21:00 时段，避免打扰）
- ✅ 持久化提醒记录，重启脚本不会重复提醒

### 部署步骤

#### 1. 在本地机器上完成 Google 授权（必须）

```bash
# 在你的电脑上（有浏览器的环境）
cd /path/to/ha-cal
source venv/bin/activate
python main.py
```

完成浏览器授权后，会在目录中生成 `token.pickle` 文件。

#### 2. 将项目文件传输到 Linux 服务器/开发板

```bash
# 方式 1：使用 scp
scp -r /path/to/ha-cal user@your-server:/tmp/

# 方式 2：使用 git（推荐）
ssh user@your-server
cd /opt
git clone https://github.com/your-repo/ha-cal.git

# 然后从本地复制授权文件
scp credentials.json token.pickle user@your-server:/opt/ha-cal/
```

#### 3. 配置环境变量

```bash
# SSH 登录到服务器
ssh user@your-server
cd /opt/ha-cal  # 或你的项目路径

# 创建 .env 文件
cp .env.example .env
nano .env  # 或使用 vi/vim 编辑

# 填写你的配置：
# HA_BASE_URL=http://192.168.1.100:8123
# HA_ACCESS_TOKEN=your_token_here
# XIAOMI_SPEAKER_ENTITY_ID=media_player.xiaoai_speaker_xxxxx
```

#### 4. 运行部署脚本

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 运行部署脚本（需要 root 权限）
sudo ./deploy.sh
```

部署脚本会自动完成以下操作：
1. 检查 Python 环境
2. 安装 Python 依赖
3. 复制文件到 `/opt/calendar-reminder`
4. 创建 systemd 服务
5. 设置开机自启动
6. 启动服务

#### 5. 验证服务状态

```bash
# 查看服务状态
sudo systemctl status calendar-reminder

# 查看实时日志
sudo journalctl -u calendar-reminder -f

# 或查看日志文件
tail -f /var/log/calendar-reminder.log
```

### 服务管理命令

```bash
# 启动服务
sudo systemctl start calendar-reminder

# 停止服务
sudo systemctl stop calendar-reminder

# 重启服务
sudo systemctl restart calendar-reminder

# 查看服务状态
sudo systemctl status calendar-reminder

# 禁用开机自启动
sudo systemctl disable calendar-reminder

# 启用开机自启动
sudo systemctl enable calendar-reminder

# 查看日志（实时）
sudo journalctl -u calendar-reminder -f

# 查看最近 100 行日志
sudo journalctl -u calendar-reminder -n 100
```

### 卸载服务

```bash
cd /opt/ha-cal  # 或你的项目路径

# 给卸载脚本添加执行权限
chmod +x uninstall.sh

# 运行卸载脚本
sudo ./uninstall.sh
```

卸载脚本会：
- 停止并禁用服务
- 删除 systemd 服务文件
- 询问是否删除安装目录（会自动备份重要文件）
- 询问是否删除日志文件

### 健康检查功能

应用内置了健康检查机制：

- **自动故障检测**：如果连续半小时无法查询 Google Calendar
- **语音警报**：通过小爱音箱播报故障通知
- **智能免打扰**：默认只在 17:00-21:00 时间段内发送语音警报，其他时间仅记录日志，避免打扰休息
- **自动恢复**：故障恢复后会记录日志
- **systemd 自动重启**：如果进程崩溃，systemd 会自动重启服务

可以通过 `.env` 文件中的 `HEALTH_ALERT_START_HOUR` 和 `HEALTH_ALERT_END_HOUR` 自定义通知时间段。

### 持久化提醒记录

应用会将提醒记录保存到 `reminded_events.json` 文件中：

- **防止重复提醒**：重启服务后不会重复发送已发送的提醒
- **自动清理**：超过 100 个事件记录后自动清理
- **状态恢复**：服务启动时自动加载历史提醒记录

---

## 方案 1：在本地授权后复制文件（最简单，强烈推荐）

这是最简单、最可靠的方法。

### 步骤

#### 1. 在本地机器（有浏览器的电脑）上首次授权

```bash
# 在你的电脑上
cd /path/to/ha-cal
source venv/bin/activate
python main.py
```

完成浏览器授权后，会在目录中生成 `token.pickle` 文件。

#### 2. 将文件复制到服务器

```bash
# 复制凭证文件和令牌到服务器
scp credentials.json token.pickle user@server:/path/to/ha-cal/

# 或者打包后复制
tar -czf google-auth.tar.gz credentials.json token.pickle
scp google-auth.tar.gz user@server:/path/to/ha-cal/

# 在服务器上解压
ssh user@server
cd /path/to/ha-cal
tar -xzf google-auth.tar.gz
```

#### 3. 在服务器上直接运行

```bash
# 服务器上
cd /path/to/ha-cal
source venv/bin/activate
python main.py
```

不需要任何授权，直接运行即可！

### 优点
- ✅ 最简单可靠
- ✅ 不需要修改代码
- ✅ token 会自动刷新
- ✅ 跨平台兼容

---

## 方案 2：使用 CLI 授权模式（需要手动输入授权码）

**注意**：Google 已在 2022 年废弃 OOB 流程，此方法可能不再可用。仅作为备选。

### 步骤

#### 1. 使用 CLI 模式运行

```bash
python main_cli.py --cli
# 或
python main_cli.py --headless
```

#### 2. 按照提示操作

程序会显示一个授权 URL，例如：
```
授权 URL:
https://accounts.google.com/o/oauth2/auth?client_id=...
```

#### 3. 在任何设备上打开这个 URL

- 可以在你的手机、平板或其他电脑上打开
- 登录你的 Google 账号
- 授权后会显示授权码

#### 4. 复制授权码并粘贴到终端

```
请输入授权码: 4/0AfJ...（粘贴你的授权码）
```

---

## 方案 3：使用 SSH 端口转发（适合可以 SSH 的服务器）

这种方法通过 SSH 隧道将服务器的端口转发到本地，让授权流程正常工作。

### 步骤

#### 1. 使用端口转发连接到服务器

```bash
# 在本地电脑上
ssh -L 8080:localhost:8080 user@server
```

#### 2. 在服务器上运行程序

```bash
cd /path/to/ha-cal
source venv/bin/activate
python main.py
```

#### 3. 授权流程

程序会尝试在 `localhost:8080` 启动服务器，由于你设置了端口转发，授权页面会在你本地电脑的浏览器中打开。

---

## 方案 4：Docker 容器部署

如果使用 Docker，推荐方案 1（复制文件）。

### Dockerfile 示例

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# credentials.json 和 token.pickle 需要通过 volume 挂载或 COPY
# COPY credentials.json token.pickle ./

CMD ["python", "main.py"]
```

### docker-compose.yml 示例

```yaml
version: '3.8'

services:
  calendar-reminder:
    build: .
    volumes:
      - ./credentials.json:/app/credentials.json:ro
      - ./token.pickle:/app/token.pickle
      - ./.env:/app/.env:ro
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
```

---

## 方案 5：systemd 服务（Linux 服务器）

创建系统服务，开机自启动。

### 创建 service 文件

```bash
sudo nano /etc/systemd/system/calendar-reminder.service
```

### 内容

```ini
[Unit]
Description=Calendar Reminder Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/ha-cal
ExecStart=/path/to/ha-cal/venv/bin/python /path/to/ha-cal/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 启用服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable calendar-reminder

# 启动服务
sudo systemctl start calendar-reminder

# 查看状态
sudo systemctl status calendar-reminder

# 查看日志
sudo journalctl -u calendar-reminder -f
```

---

## 文件权限设置

为了安全，建议设置合适的文件权限：

```bash
# 进入项目目录
cd /path/to/ha-cal

# 设置敏感文件权限为只有所有者可读写
chmod 600 .env credentials.json token.pickle

# 设置目录权限
chmod 700 .

# 如果使用 systemd，确保服务用户有权限访问
sudo chown your_username:your_username .env credentials.json token.pickle
```

---

## 常见问题

### Q: token.pickle 会过期吗？

A: 访问令牌 1 小时过期，但刷新令牌会自动续期。只要代码持续运行（至少 6 个月运行一次），就不会过期。

### Q: 可以在多台服务器上使用同一个 token.pickle 吗？

A: 可以，但要注意 Google 对每个 OAuth 客户端的刷新令牌有数量限制（通常 50 个）。如果超过限制，旧的令牌会失效。

### Q: 如何检查 token 是否有效？

A: 运行程序时会自动检查并刷新。如果失败，删除 `token.pickle` 重新授权即可。

---

## 推荐方案总结

| 场景 | 推荐方案 | 难度 |
|------|---------|------|
| **Linux 服务器/开发板** | **🚀 快速部署脚本（推荐）** | ⭐ 简单 |
| 个人服务器（手动部署） | 方案 1：本地授权后复制 | ⭐ 简单 |
| Docker 容器 | 方案 1 + Volume 挂载 | ⭐⭐ 中等 |
| 可 SSH 服务器 | 方案 3：SSH 端口转发 | ⭐⭐ 中等 |
| 生产环境 | 🚀 快速部署脚本 | ⭐ 简单 |

**建议**：
- **Linux 服务器/开发板**：使用页面顶部的"🚀 快速部署"，一键完成所有配置！
- **其他环境**：方案 1（本地授权后复制文件）是最佳选择！
