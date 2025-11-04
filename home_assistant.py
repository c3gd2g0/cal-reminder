"""Home Assistant API 集成模块"""
import requests
import json


class HomeAssistantClient:
    """Home Assistant 客户端"""

    def __init__(self, base_url, access_token):
        """
        初始化 Home Assistant 客户端

        Args:
            base_url: Home Assistant 实例的 URL（例如：http://192.168.1.100:8123）
            access_token: Home Assistant 长期访问令牌
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

    def call_service(self, domain, service, service_data=None):
        """
        调用 Home Assistant 服务

        Args:
            domain: 服务域（例如：'tts'）
            service: 服务名称（例如：'xiaomi_ai_speaker_say'）
            service_data: 服务数据（字典）

        Returns:
            响应对象
        """
        url = f'{self.base_url}/api/services/{domain}/{service}'

        print(f'      → 请求详情:')
        print(f'        方法: POST')
        print(f'        URL: {url}')
        print(f'        请求体: {json.dumps(service_data or {}, ensure_ascii=False, indent=8)}')

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=service_data or {},
                timeout=10
            )

            print(f'      ← 响应详情:')
            print(f'        状态码: {response.status_code}')
            print(f'        响应头: {dict(response.headers)}')

            response.raise_for_status()

            response_data = response.json()
            print(f'        响应体: {json.dumps(response_data, ensure_ascii=False, indent=8)}')

            return response_data
        except requests.exceptions.RequestException as e:
            print(f'        ✗ 错误: {e}')
            if hasattr(e, 'response') and e.response is not None:
                print(f'        错误响应: {e.response.text}')
            return None

    def xiaomi_speaker_say(self, entity_id, message):
        """
        让小米小爱音箱播报消息

        Args:
            entity_id: 小米音箱的配置标识，支持三种方式：
                      1. Home Assistant Script（推荐）：
                         例如：'script.xiaomi_speaker_say'
                      2. notify 服务（小米官方集成）：
                         例如：'notify.xiaomi_cn_83422613_s12_play_text_a_5_1'
                      3. media_player 实体（传统方式）：
                         例如：'media_player.xiaomi_speaker'
            message: 要播报的消息

        Returns:
            响应对象，成功返回响应数据，失败返回 None
        """
        # 方式 1: 使用 Home Assistant Script（最推荐）
        if entity_id.startswith('script.'):
            print(f'      使用 Home Assistant Script: {entity_id}')

            # 调用 script.turn_on 服务，传递 entity_id 和 msg 参数
            service_data = {
                'entity_id': entity_id,
                'variables': {
                    'msg': message
                }
            }

            # 调用 script 服务
            # 构造的 API 路径: /api/services/script/turn_on
            result = self.call_service('script', 'turn_on', service_data)

            if result is not None:
                print(f'      ✓ Script 调用成功')
            else:
                print(f'      ✗ Script 调用失败，请检查：')
                print(f'        1. Script 是否存在: {entity_id}')
                print(f'        2. 在 HA 开发者工具 -> 服务 中测试该 script')
                print(f'        3. Script 配置中的字段名是否为 "msg"')

            return result

        # 方式 2: 使用 notify 服务（小米官方集成）
        if entity_id.startswith('notify.'):
            # 保持完整的 entity_id（包括 'notify.' 前缀）
            service_name = entity_id
            print(f'      使用小米官方 notify 服务: {service_name}')

            service_data = {
                'message': message
            }

            # 调用 notify 服务
            # 构造的 API 路径: /api/services/notify/{service_name}
            result = self.call_service('notify', service_name, service_data)

            if result is not None:
                print(f'      ✓ notify 服务调用成功')
            else:
                print(f'      ✗ notify 服务调用失败，请检查：')
                print(f'        1. 服务名称是否正确: {entity_id}')
                print(f'        2. 小米官方集成是否已配置')
                print(f'        3. 在 HA 开发者工具 -> 服务 中测试该服务')

            return result

        # 方式 3: 使用 media_player 实体（传统方式）
        print(f'      使用传统 media_player 方式')

        # 方法 1: 使用 xiaomi_miot 集成的 intelligent_speaker 服务
        print(f'      尝试 xiaomi_miot.intelligent_speaker 服务...')
        service_data = {
            'entity_id': entity_id,
            'text': message
        }

        result = self.call_service('xiaomi_miot', 'intelligent_speaker', service_data)

        if result is None:
            # 方法 2: 如果上面的方法失败，尝试使用通用 TTS 服务
            print('      尝试备用 TTS 方法 (tts.baidu_say)...')
            service_data = {
                'entity_id': entity_id,
                'message': message
            }
            result = self.call_service('tts', 'baidu_say', service_data)

        return result

    def test_connection(self):
        """
        测试与 Home Assistant 的连接

        Returns:
            True 如果连接成功，否则 False
        """
        url = f'{self.base_url}/api/'

        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            print('成功连接到 Home Assistant!')
            return True
        except requests.exceptions.RequestException as e:
            print(f'连接 Home Assistant 失败: {e}')
            return False

    def get_entity_state(self, entity_id):
        """
        获取实体状态

        Args:
            entity_id: 实体 ID

        Returns:
            实体状态数据
        """
        url = f'{self.base_url}/api/states/{entity_id}'

        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f'获取实体状态失败: {e}')
            return None
