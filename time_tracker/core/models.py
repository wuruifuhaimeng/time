from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class TaskItem:
    text: str
    done: bool = False

@dataclass
class TimeTrackerData:
    date: str
    time_blocks: str = ""
    diary: str = ""
    tasks: List[TaskItem] = field(default_factory=list)
    mood: str = ""

@dataclass
class TimeBlock:
    time: str
    activity: str
    duration: str
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d")) 