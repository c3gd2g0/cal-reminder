# 使用 Home Assistant Script 配置小米音箱播报

## 为什么使用 Script？

使用 Home Assistant Script 相比直接调用 notify 服务有以下优势：
- ✅ 更灵活：可以自定义消息格式
- ✅ 易维护：在 HA UI 中可视化编辑
- ✅ 可扩展：可以添加条件判断、多个动作等
- ✅ 统一管理：所有配置都在 HA 中

## 在 Home Assistant 中创建 Script

### 方法 1：通过 UI 创建（推荐）

1. **打开 Home Assistant**
   - 进入：设置 → 自动化和场景 → 脚本

2. **创建新脚本**
   - 点击右下角的 "+" 按钮
   - 点击 "创建新脚本"

3. **配置脚本信息**
   - **名称**：`小爱播放文本`
   - **图标**：选择 `mdi:speaker-message`
   - **描述**：`播放文本`

4. **添加动作**
   - 点击 "添加动作"
   - 搜索并选择：`notify.send_message` 或你的具体 notify 服务
   - 配置参数：
     ```yaml
     message: "[\"{{ msg }}\"]"
     target:
       entity_id: notify.xiaomi_cn_83422613_s12_play_text_a_5_1
     ```

5. **添加字段（重要！）**
   - 点击右上角的 "⋮" → "编辑字段"
   - 添加字段：
     - **名称**：`msg`
     - **选择器**：文本
     - **必填**：是
     - **标签**：`小爱将会播放：`

6. **保存脚本**
   - 点击右上角的保存按钮
   - 脚本会自动生成 entity_id，例如：`script.xiao_ai_bo_fang_wen_ben`

### 方法 2：通过 YAML 配置

在 Home Assistant 的 `scripts.yaml` 或 `configuration.yaml` 中添加：

```yaml
xiaomi_speaker_say:
  alias: 小爱播放文本
  description: 播放文本
  icon: mdi:speaker-message
  fields:
    msg:
      description: 要播放的消息
      required: true
      selector:
        text:
  sequence:
    - action: notify.send_message
      metadata: {}
      data:
        message: "[\"{{ msg }}\"]"
      target:
        entity_id: notify.xiaomi_cn_83422613_s12_play_text_a_5_1
```

保存后重启 Home Assistant 或重新加载脚本配置。

## 配置本应用

### 1. 找到你的 Script Entity ID

创建 Script 后，在 Home Assistant 中：
1. 进入：设置 → 自动化和场景 → 脚���
2. 找到你创建的脚本，记下它的 entity_id
   - 格式通常是：`script.{脚本名称的拼音或英文}`
   - 例如：`script.xiaomi_speaker_say` 或 `script.xiao_ai_bo_fang_wen_ben`

### 2. 更新 .env 配置

编辑项目根目录的 `.env` 文件：

```bash
# 使用你的 script entity_id
XIAOMI_SPEAKER_ENTITY_ID=script.xiaomi_speaker_say
```

### 3. 测试配置

运行测试脚本验证配置是否正确：

```bash
python test_speaker.py
```

如果配置正确，你应该能看到：
```
配置类型: Home Assistant Script ✓✓ 最推荐
优势: 灵活、可自定义、易维护
```

## 常见问题

### Q: Script 调用失败，返回 404 错误
**A**: 检查以下几点：
1. Script 是否已保存并生效
2. Entity ID 是否正确（在 HA 开发者工具 → 服务 中搜索确认）
3. 在开发者工具中手动测试该 Script

### Q: Script 调用成功但音箱没有播报
**A**: 检查以下几点：
1. 音箱是否在线
2. 音箱是否静音或音量过低
3. Script 中的 notify 服务配置是否正确
4. 查看 Home Assistant 日志中的错误信息

### Q: 消息格式为什么是 `[\"{{ msg }}\"]`？
**A**: 这是小米官方集成要求的消息格式，用于直接播报文本而不是通知声音。

### Q: 能不能自定义消息格式？
**A**: 当然可以！这正是使用 Script 的优势。你可以在 Script 中修改消息模板，例如：
```yaml
message: "[\"主人，{{ msg }}\"]"  # 添加前缀
message: "[\"{{ msg }}，请注意！\"]"  # 添加后缀
```

## 在 Home Assistant 中测试 Script

1. 打开：开发者工具 → 服务
2. 搜索你的 script（例如：`script.xiaomi_speaker_say`）
3. 在 "msg" 字段输入测试消息：`测试消息，你好`
4. 点击 "调用服务"
5. 音箱应该播报该消息

## 高级用法

### 添加条件判断

只在白天播报：
```yaml
sequence:
  - if:
      - condition: sun
        after: sunrise
        before: sunset
    then:
      - action: notify.send_message
        data:
          message: "[\"{{ msg }}\"]"
        target:
          entity_id: notify.xiaomi_cn_83422613_s12_play_text_a_5_1
```

### 多个音箱同时播报

```yaml
sequence:
  - action: notify.send_message
    data:
      message: "[\"{{ msg }}\"]"
    target:
      entity_id:
        - notify.xiaomi_speaker_1
        - notify.xiaomi_speaker_2
```

### 添加日志记录

```yaml
sequence:
  - action: system_log.write
    data:
      message: "日历提醒播报: {{ msg }}"
      level: info
  - action: notify.send_message
    data:
      message: "[\"{{ msg }}\"]"
    target:
      entity_id: notify.xiaomi_cn_83422613_s12_play_text_a_5_1
```
