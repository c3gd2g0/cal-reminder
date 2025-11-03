# Google Calendar + Home Assistant 日历提醒应用

这是一个 Python 应用程序，可以自动监控 Google 日历，并在日程开始前 5 分钟通过 Home Assistant 控制小米小爱音箱进行语音提醒。

## 功能特性

- 自动读取 Google Calendar 日程
- 可配置的提前提醒时间（默认 5 分钟）
- 通过 Home Assistant API 控制小米小爱音箱播报提醒
- 后台持续运行，自动检查即将到来的事件
- 避免重复提醒同一事件

## 系统要求

- Python 3.7+
- Home Assistant 实例（已配置小米小爱音箱集成）
- Google Calendar API 凭证

## 安装步骤

### 1. 克隆或下载项目

```bash
cd /path/to/ha-cal
```

### 2. 创建并激活虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 Google Calendar API

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Google Calendar API
4. 创建 OAuth 2.0 凭证：
   - 点击"创建凭证" -> "OAuth 客户端 ID"
   - 应用类型选择"桌面应用"
   - 下载凭证 JSON 文件
5. 将下载的文件重命名为 `credentials.json` 并放在项目根目录

### 5. 配置 Home Assistant

1. 在 Home Assistant 中创建长期访问令牌：
   - 点击左下角用户名
   - 滚动到"长期访问令牌"部分
   - 点击"创建令牌"
   - 复制生成的令牌

2. 确认小米小爱音箱已正确集成到 Home Assistant
   - 在"开发者工具" -> "状态"中查找音箱的实体 ID
   - 实体 ID 通常类似：`media_player.xiaoai_speaker_xxxxx`

### 6. 配置环境变量

1. 复制配置文件模板：

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的配置信息：

```env
# Google Calendar API 配置
GOOGLE_CREDENTIALS_PATH=credentials.json

# Home Assistant 配置
HA_BASE_URL=http://192.168.1.100:8123
HA_ACCESS_TOKEN=your_long_lived_access_token_here

# 小米小爱音箱实体 ID
XIAOMI_SPEAKER_ENTITY_ID=media_player.xiaoai_speaker_xxxxx

# 提醒设置
REMINDER_MINUTES=5
CHECK_INTERVAL=60
```

## 使用方法

### 首次运行

首次运行时，应用会打开浏览器要求你授权 Google Calendar 访问权限：

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 运行应用
python main.py
```

按照浏览器中的提示完成授权，授权成功后会生成 `token.pickle` 文件，以后运行就不需要再次授权了。

### 正常运行

```bash
python main.py
```

应用会持续运行并在后台监控日历事件。

### 作为后台服务运行（可选）

#### macOS/Linux - 使用 systemd

创建服务文件 `/etc/systemd/system/calendar-reminder.service`：

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

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl enable calendar-reminder
sudo systemctl start calendar-reminder
sudo systemctl status calendar-reminder
```

#### macOS - 使用 launchd

创建 `~/Library/LaunchAgents/com.calendar.reminder.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.calendar.reminder</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/ha-cal/venv/bin/python</string>
        <string>/path/to/ha-cal/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/ha-cal</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

加载服务：

```bash
launchctl load ~/Library/LaunchAgents/com.calendar.reminder.plist
```

## 项目结构

```
ha-cal/
├── venv/                   # Python 虚拟环境
├── main.py                 # 主程序入口
├── google_calendar.py      # Google Calendar API 集成
├── home_assistant.py       # Home Assistant API 集成
├── requirements.txt        # Python 依赖
├── .env.example           # 配置文件模板
├── .env                   # 实际配置文件（需要自己创建）
├── credentials.json       # Google API 凭证（需要自己下载）
├── token.pickle          # Google 授权令牌（首次运行后自动生成）
└── README.md             # 本文件
```

## 配置说明

### 环境变量

- `GOOGLE_CREDENTIALS_PATH`: Google API 凭证文件路径
- `HA_BASE_URL`: Home Assistant 实例的 URL
- `HA_ACCESS_TOKEN`: Home Assistant 长期访问令牌
- `XIAOMI_SPEAKER_ENTITY_ID`: 小米音箱在 HA 中的实体 ID
- `REMINDER_MINUTES`: 提前多少分钟提醒（默认 5）
- `CHECK_INTERVAL`: 检查日历的间隔时间（秒，默认 60）

## 常见问题

### 1. 小爱音箱不播报

检查以下几点：
- 确认音箱实体 ID 正确
- 确认 Home Assistant 可以正常控制音箱
- 检查 Home Assistant 日志查看是否有错误信息
- 尝试在 HA 的开发者工具中手动调用服务测试

### 2. Google Calendar 授权失败

- 确认 `credentials.json` 文件正确
- 删除 `token.pickle` 文件后重试
- 检查 Google Cloud Console 中 API 是否已启用

### 3. 提醒不及时

- 调整 `CHECK_INTERVAL` 为更短的时间（如 30 秒）
- 注意：间隔太短可能导致 API 请求过于频繁

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
