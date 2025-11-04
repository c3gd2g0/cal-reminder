"""测试小米音箱播报功能"""
import os
from dotenv import load_dotenv
from home_assistant import HomeAssistantClient

# 加载环境变量
load_dotenv()

def main():
    """测试小米音箱"""
    print('=' * 60)
    print('小米音箱测试脚本')
    print('=' * 60)

    # 检查环境变量
    ha_url = os.getenv('HA_BASE_URL')
    ha_token = os.getenv('HA_ACCESS_TOKEN')
    speaker_id = os.getenv('XIAOMI_SPEAKER_ENTITY_ID')

    if not all([ha_url, ha_token, speaker_id]):
        print('错误：缺少环境变量配置')
        print('请检查 .env 文件是否正确配置')
        return

    print(f'\n配置信息:')
    print(f'  Home Assistant URL: {ha_url}')
    print(f'  音箱配置: {speaker_id}')

    # 检测配置类型
    if speaker_id.startswith('script.'):
        print(f'  配置类型: Home Assistant Script ✓✓ 最推荐')
        print(f'  优势: 灵活、可自定义、易维护')
    elif speaker_id.startswith('notify.'):
        print(f'  配置类型: notify 服务（小米官方集成） ✓ 推荐')
        print(f'  💡 提示: 可以封装成 Script 以获得更多灵活性')
    elif speaker_id.startswith('media_player.'):
        print(f'  配置类型: media_player 实体（传统方式）')
        print(f'  💡 提示: 推荐改用 Script 或 notify 服务')
    else:
        print(f'  ⚠️  警告: 配置格式不正确')
        print(f'     应该以 script., notify. 或 media_player. 开头')

    print('-' * 60)

    # 创建 Home Assistant 客户端
    ha_client = HomeAssistantClient(
        base_url=ha_url,
        access_token=ha_token
    )

    # 测试连接
    print('\n1. 测试 Home Assistant 连接...')
    if not ha_client.test_connection():
        print('连接失败，请检查 URL 和访问令牌')
        return

    # 测试音箱播报
    print('\n2. 测试音箱播报功能...')
    test_message = '你好，这是日历提醒应用的测试消息'
    print(f'   播报内容: {test_message}')
    print('-' * 60)

    result = ha_client.xiaomi_speaker_say(
        entity_id=speaker_id,
        message=test_message
    )

    print('-' * 60)
    if result:
        print('\n✓ 测试成功！你应该能听到音箱的播报。')
        print('\n如果音��没有播报，请检查：')
        print('  1. 音箱是否在线且未静音')
        print('  2. 音箱音量是否合适')
        print('  3. Home Assistant 日志中的详细信息')
    else:
        print('\n✗ 测试失败！请检查:')
        if speaker_id.startswith('script.'):
            print('  1. 在 HA 设置 -> 自动化和场景 -> 脚本 中确认该脚本存在')
            print('  2. 在 HA 开发者工具 -> 服务 中测试该脚本')
            print('  3. 脚本配置中的字段���是否为 "msg"')
            print('  4. 脚本中的 notify 服务是否正确配置')
        elif speaker_id.startswith('notify.'):
            print('  1. 在 HA 开发者工具 -> 服务 中确认该 notify 服务存在')
            print('  2. 小米官方集成是否正确配置')
            print('  3. 音箱设备是否在线')
        else:
            print('  1. 音箱实体 ID 是否正确')
            print('  2. 音箱是否在线')
            print('  3. xiaomi_miot 集成是否已安装')
        print('  5. 查看 Home Assistant 日志中的错误信息')

    print('=' * 60)


if __name__ == '__main__':
    main()
