"""Google Calendar API 集成模块 - 支持 CLI 无浏览器环境"""
import os
import pickle
from datetime import datetime, timedelta, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 如果修改这些作用域，请删除 token.pickle 文件
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class GoogleCalendarClient:
    """Google Calendar 客户端"""

    def __init__(self, credentials_path='credentials.json', headless=False):
        """
        初始化 Google Calendar 客户端

        Args:
            credentials_path: Google API 凭证文件路径
            headless: 是否使用无头模式（CLI 环境，无浏览器）
        """
        self.credentials_path = credentials_path
        self.headless = headless
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """验证并初始化 Google Calendar 服务"""
        creds = None

        # token.pickle 存储用户的访问和刷新令牌
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # 检查凭证是否需要刷新（提前5分钟刷新）
        needs_refresh = False
        if creds:
            if creds.expired:
                needs_refresh = True
            elif creds.expiry:
                # 提前5分钟刷新
                # 确保 expiry 是 timezone-aware 的
                if creds.expiry.tzinfo is None:
                    # 如果 expiry 是 naive datetime，假设它是 UTC 时间
                    expiry_aware = creds.expiry.replace(tzinfo=timezone.utc)
                else:
                    expiry_aware = creds.expiry
                time_until_expiry = expiry_aware - datetime.now(timezone.utc)
                if time_until_expiry.total_seconds() < 300:  # 5分钟 = 300秒
                    needs_refresh = True

        # 如果没有有效的凭证，让用户登录
        if not creds or not creds.valid or needs_refresh:
            if creds and creds.refresh_token and (creds.expired or needs_refresh):
                try:
                    print('刷新访问令牌...')
                    creds.refresh(Request())
                    # 保存刷新后的凭证
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(creds, token)
                    print('访问令牌刷新成功')
                except Exception as e:
                    print(f'刷新令牌失败: {e}')
                    print('需要重新授权...')
                    # 删除无效的 token 文件
                    if os.path.exists('token.pickle'):
                        os.remove('token.pickle')
                    creds = None
            
            # 如果刷新失败或没有有效凭证，执行完整的授权流程
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)

                if self.headless:
                    # CLI 模式 - 使用 OOB（Out-of-Band）流程
                    print('\n' + '=' * 60)
                    print('CLI 授权模式（无浏览器环境）')
                    print('=' * 60)
                    print('请按照以下步骤操作：')
                    print('1. 在任何设备的浏览器中访问下面的 URL')
                    print('2. 使用你的 Google 账号登录并授权')
                    print('3. 复制授权码并粘贴到下面')
                    print('-' * 60)

                    # 使用 OOB 流程（授权后显示授权码）
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    auth_url, _ = flow.authorization_url(prompt='consent')

                    print(f'\n授权 URL:\n{auth_url}\n')
                    print('-' * 60)

                    # 等待用户输入授权码
                    code = input('请输入授权码: ').strip()

                    # 使用授权码获取凭证
                    flow.fetch_token(code=code)
                    creds = flow.credentials

                    print('-' * 60)
                    print('✓ 授权成功！')
                    print('=' * 60 + '\n')
                else:
                    # 正常模式 - 自动打开浏览器
                    creds = flow.run_local_server(port=0)

            # 保存凭证供下次使用
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                print('凭证已保存到 token.pickle')

        self.service = build('calendar', 'v3', credentials=creds)

    def get_upcoming_events(self, time_min=None, time_max=None, max_results=10):
        """
        获取即将到来的日历事件

        Args:
            time_min: 开始时间（datetime 对象），默认为当前时间
            time_max: 结束时间（datetime 对象），默认为 24 小时后
            max_results: 最大返回结果数

        Returns:
            事件列表
        """
        try:
            if time_min is None:
                time_min = datetime.now(timezone.utc)
            if time_max is None:
                time_max = time_min + timedelta(hours=24)

            # 将时间转换为 RFC3339 格式
            # 如果时间已经是 timezone-aware 的，直接使用 isoformat()
            # 如果是 naive 的，添加 'Z' 表示 UTC
            if time_min.tzinfo is not None:
                time_min_str = time_min.isoformat()
            else:
                time_min_str = time_min.isoformat() + 'Z'

            if time_max.tzinfo is not None:
                time_max_str = time_max.isoformat()
            else:
                time_max_str = time_max.isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            return events

        except HttpError as error:
            print(f'获取日历事件时发生错误: {error}')
            return []

    def get_event_start_time(self, event):
        """
        获取事件的开始时间

        Args:
            event: Google Calendar 事件对象

        Returns:
            datetime 对象，表示事件开始时间
        """
        start = event['start'].get('dateTime', event['start'].get('date'))

        # 解析时间字符串
        if 'T' in start:
            # 包含时间的事件
            return datetime.fromisoformat(start.replace('Z', '+00:00'))
        else:
            # 全天事件
            return datetime.fromisoformat(start)

    def get_event_summary(self, event):
        """
        获取事件摘要（标题）

        Args:
            event: Google Calendar 事件对象

        Returns:
            事件标题字符串
        """
        return event.get('summary', '无标题事件')
