"""日历提醒主程序"""
import os
import re
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from google_calendar import GoogleCalendarClient
from home_assistant import HomeAssistantClient

# 加载环境变量
load_dotenv()


class CalendarReminderApp:
    """日历提醒应用"""

    def __init__(self):
        """初始化应用"""
        # 初始化 Google Calendar 客户端
        self.calendar_client = GoogleCalendarClient(
            credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        )

        # 初始化 Home Assistant 客户端
        self.ha_client = HomeAssistantClient(
            base_url=os.getenv('HA_BASE_URL'),
            access_token=os.getenv('HA_ACCESS_TOKEN')
        )

        # 小米音箱实体 ID
        self.speaker_entity_id = os.getenv('XIAOMI_SPEAKER_ENTITY_ID')

        # 消息模板：支持 {event_name} 和 {minutes} 占位符
        self.message_template = os.getenv(
            'REMINDER_MESSAGE_TEMPLATE',
            '提醒：{event_name} 将在 {minutes} 分钟后开始'
        )

        # 已提醒的事件：{event_id: {提醒时间点的集合}}
        # 例如：{'event123': {5, 1}} 表示已经在5分钟和1分钟前提醒过
        self.reminded_events = {}

        # 检查间隔（秒）
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '60'))

    def parse_extra_reminder_time(self, event_summary):
        """
        从事件标题中解析额外的提醒时间

        Args:
            event_summary: 事件标题

        Returns:
            额外的提醒分钟数，如果没有标记则返回 0

        Examples:
            "会议 [10]" -> 10
            "普通会议" -> 0
            "重要会议 [30]" -> 30
        """
        # 匹配 [数字] 格式，数字范围 1-60
        match = re.search(r'\[(\d+)\]', event_summary)
        if match:
            extra_minutes = int(match.group(1))
            # 限制在 1-60 分钟范围内
            if 1 <= extra_minutes <= 60:
                return extra_minutes
        return 0

    def get_reminder_times(self, event_summary):
        """
        获取该事件的所有提醒时间点

        Args:
            event_summary: 事件标题

        Returns:
            提醒时间点列表（分钟），按从大到小排序

        Examples:
            "普通会议" -> [5, 1]
            "远程会议 [10]" -> [15, 11]  (5+10, 1+10)
        """
        extra_time = self.parse_extra_reminder_time(event_summary)

        if extra_time > 0:
            # 有额外标记：两次提醒都加上额外时间
            # (5 + extra_time) 分钟前、(1 + extra_time) 分钟前
            return [5 + extra_time, 1 + extra_time]
        else:
            # 普通日程：5 分钟前、1 分钟前
            return [5, 1]

    def send_reminder(self, event_summary, minutes_until):
        """
        发送提醒

        Args:
            event_summary: 事件摘要
            minutes_until: 距离事件开始还有多少分钟
        """
        # 使用模板格式化消息
        # 移除标题中的 [数字] 标记，只保留纯净的事件名称
        clean_event_name = re.sub(r'\s*\[\d+\]\s*', ' ', event_summary).strip()

        message = self.message_template.format(
            event_name=clean_event_name,
            minutes=minutes_until
        )

        print(f'\n[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] 发送提醒')
        print(f'  事件: {event_summary}')
        print(f'  倒计时: {minutes_until} 分钟')
        print(f'  消息内容: {message}')

        # 调用 Home Assistant 让小爱音箱播报
        print(f'  调用 Home Assistant API...')
        print(f'  - 实体/服务: {self.speaker_entity_id}')

        result = self.ha_client.xiaomi_speaker_say(
            entity_id=self.speaker_entity_id,
            message=message
        )

        if result:
            print(f'  ✓ 提醒发送成功!')
            print(f'  响应内容: {result}')
        else:
            print(f'  ✗ 提醒发送失败!')
        print('-' * 60)

    def check_events(self):
        """检查即将到来的事件"""
        now = datetime.now(timezone.utc)
        check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 获取未来 1 小时内的事件（确保能覆盖所有提醒时间）
        time_max = now + timedelta(hours=1)

        print(f'\n[{check_time}] 查询 Google Calendar...')
        print(f'  查询时间范围: {now.strftime("%Y-%m-%d %H:%M")} ~ {time_max.strftime("%Y-%m-%d %H:%M")} (UTC)')

        events = self.calendar_client.get_upcoming_events(
            time_min=now,
            time_max=time_max,
            max_results=50
        )

        if not events:
            print(f'  未找到即将到来的日程')
            return

        print(f'  查询到 {len(events)} 个日程:')

        for idx, event in enumerate(events, 1):
            event_id = event['id']
            start_time = self.calendar_client.get_event_start_time(event)
            event_summary = self.calendar_client.get_event_summary(event)

            # 计算距离事件开始的时间
            time_until_event = start_time - datetime.now(start_time.tzinfo)
            minutes_until = time_until_event.total_seconds() / 60

            # 获取该事件的所有提醒时间点
            reminder_times = self.get_reminder_times(event_summary)
            extra_time = self.parse_extra_reminder_time(event_summary)

            # 初始化该事件的提醒记录
            if event_id not in self.reminded_events:
                self.reminded_events[event_id] = set()

            # 构建状态显示
            reminded_at = self.reminded_events[event_id]
            if reminded_at:
                status = f'已提醒: {sorted(reminded_at, reverse=True)}分钟前'
            else:
                status = f'{int(minutes_until)}分钟后'

            # 显示事件信息
            extra_info = f' [+{extra_time}分钟]' if extra_time > 0 else ''
            print(f'  [{idx}] {event_summary}{extra_info}')
            print(f'      开始时间: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')
            print(f'      提醒时间点: {reminder_times} 分钟前')
            print(f'      状态: {status}')

            # 检查是否需要在任何时间点提醒
            for reminder_time in reminder_times:
                # 如果还没在这个时间点提醒过
                if reminder_time not in reminded_at:
                    # 检查是否到达该提醒时间点
                    # 只在接近提醒时间点时触发（容差范围：提醒时间点前后0.5分钟）
                    # 这样可以避免因为检查间隔错过提醒，同时防止重复提醒
                    if reminder_time - 0.5 <= minutes_until <= reminder_time + 0.5:
                        # 发送提醒
                        self.send_reminder(event_summary, int(minutes_until))
                        # 标记已在该时间点提醒
                        self.reminded_events[event_id].add(reminder_time)
                        print(f'      ✓ 已标记 {reminder_time} 分钟提醒')

        # 清理过期的事件记录（超过 24 小时的）
        if len(self.reminded_events) > 100:
            print(f'  清理过期提醒记录...')
            self.reminded_events.clear()

    def run(self):
        """运行主循环"""
        print('日历提醒应用启动!')
        print(f'提醒策略：')
        print(f'  - 普通日程：5分钟前、1分钟前')
        print(f'  - 标记日程（如"会议[10]"）：15分钟前(5+10)、11分钟前(1+10)')
        print(f'消息模板：{self.message_template}')
        print(f'  可用占位符：{{event_name}} {{minutes}}')
        print(f'检查间隔：每 {self.check_interval} 秒')
        print(f'小米音箱实体 ID: {self.speaker_entity_id}')
        print('-' * 50)

        # 测试 Home Assistant 连接
        if not self.ha_client.test_connection():
            print('警告：无法连接到 Home Assistant，请检查配置!')
            return

        try:
            while True:
                try:
                    self.check_events()
                except Exception as e:
                    print(f'检查事件时出错: {e}')

                # 等待下次检查
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print('\n应用已停止')


def main():
    """主函数"""
    # 检查必要的环境变量
    required_vars = ['HA_BASE_URL', 'HA_ACCESS_TOKEN', 'XIAOMI_SPEAKER_ENTITY_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print('错误：缺少以下环境变量:')
        for var in missing_vars:
            print(f'  - {var}')
        print('\n请在 .env 文件中配置这些变量。')
        return

    # 创建并运行应用
    app = CalendarReminderApp()
    app.run()


if __name__ == '__main__':
    main()
