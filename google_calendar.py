"""Google Calendar API 集成模块"""
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

    def __init__(self, credentials_path='credentials.json'):
        """
        初始化 Google Calendar 客户端

        Args:
            credentials_path: Google API 凭证文件路径
        """
        self.credentials_path = credentials_path
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """验证并初始化 Google Calendar 服务"""
        creds = None

        # token.pickle 存储用户的访问和刷新令牌
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # 如果没有有效的凭证，让用户登录
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # 保存凭证供下次使用
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

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
