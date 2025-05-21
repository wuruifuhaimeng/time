import unittest
from datetime import datetime
from ..core.models import TaskItem, TimeTrackerData, TimeBlock

class TestTaskItem(unittest.TestCase):
    def test_task_item_creation(self):
        task = TaskItem("测试任务")
        self.assertEqual(task.text, "测试任务")
        self.assertFalse(task.done)
        
        task = TaskItem("已完成任务", True)
        self.assertEqual(task.text, "已完成任务")
        self.assertTrue(task.done)

class TestTimeTrackerData(unittest.TestCase):
    def test_time_tracker_data_creation(self):
        data = TimeTrackerData("2024-03-20")
        self.assertEqual(data.date, "2024-03-20")
        self.assertEqual(data.time_blocks, "")
        self.assertEqual(data.diary, "")
        self.assertEqual(data.tasks, [])
        self.assertEqual(data.mood, "")

class TestTimeBlock(unittest.TestCase):
    def test_time_block_creation(self):
        block = TimeBlock("08:00", "睡觉", "8小时")
        self.assertEqual(block.time, "08:00")
        self.assertEqual(block.activity, "睡觉")
        self.assertEqual(block.duration, "8小时")
        self.assertEqual(block.date, datetime.now().strftime("%Y-%m-%d"))

if __name__ == '__main__':
    unittest.main() 