import re
import csv
from pathlib import Path
from typing import List, Dict
from .models import TimeBlock

class TimeBlockUtils:
    @staticmethod
    def parse_time_blocks(time_blocks: str, date: str) -> List[TimeBlock]:
        blocks = []
        for line in time_blocks.splitlines():
            parts = line.strip().split()
            if len(parts) >= 3:
                time = parts[0]
                activity = ' '.join(parts[1:-1])
                duration = parts[-1]
                blocks.append(TimeBlock(time=time, activity=activity, duration=duration, date=date))
        return blocks

    @staticmethod
    def load_timeblock_df(data_dir: Path) -> List[Dict]:
        csvfile = data_dir / 'timeblocks.csv'
        if csvfile.exists():
            with open(csvfile, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        return []

    @staticmethod
    def save_timeblock_df(data_dir: Path, rows: List[Dict]) -> None:
        csvfile = data_dir / 'timeblocks.csv'
        fieldnames = ['date', 'time', 'activity', 'duration']
        
        # 读取现有数据
        existing_rows = []
        if csvfile.exists():
            with open(csvfile, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_rows = list(reader)
        
        # 合并数据并去重
        all_rows = existing_rows + rows
        unique_rows = []
        seen = set()
        for row in all_rows:
            key = (row['date'], row['time'], row['activity'])
            if key not in seen:
                seen.add(key)
                unique_rows.append(row)
        
        # 保存数据
        with open(csvfile, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_rows)

class NaturalLanguageParser:
    @staticmethod
    def parse_natural_timeblock(text: str) -> str:
        # 匹配时间
        time_patterns = {
            r'早上|早晨': '07:00',
            r'上午': '09:00',
            r'中午': '12:00',
            r'下午': '14:00',
            r'晚上': '20:00',
            r'凌晨': '00:00'
        }
        
        # 匹配时长
        duration_pattern = r'(\d+)(?:个)?(小时|分钟|min)'
        
        # 提取时间
        time = None
        for pattern, default_time in time_patterns.items():
            if re.search(pattern, text):
                time = default_time
                break
        
        # 提取时长
        duration_match = re.search(duration_pattern, text)
        if duration_match:
            num, unit = duration_match.groups()
            if unit in ['小时', '个']:
                duration = f"{num}小时"
            else:
                duration = f"{num}min"
        else:
            duration = "30min"
        
        # 提取活动（简单处理：去除时间和时长后的剩余文本）
        activity = text
        for pattern in time_patterns.keys():
            activity = re.sub(pattern, '', activity)
        activity = re.sub(duration_pattern, '', activity).strip()
        
        if time and activity and duration:
            return f"{time} {activity} {duration}"
        return None 