import unittest
from pathlib import Path
import tempfile
import os
from ..core.analyzer import TimeBlockUtils, NaturalLanguageParser

class TestTimeBlockUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_time_blocks(self):
        time_blocks = """08:00 睡觉 8小时
09:30 阅读 40min"""
        blocks = TimeBlockUtils.parse_time_blocks(time_blocks, "2024-03-20")
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].time, "08:00")
        self.assertEqual(blocks[0].activity, "睡觉")
        self.assertEqual(blocks[0].duration, "8小时")
        self.assertEqual(blocks[1].time, "09:30")
        self.assertEqual(blocks[1].activity, "阅读")
        self.assertEqual(blocks[1].duration, "40min")

    def test_save_and_load_timeblock_df(self):
        rows = [
            {"date": "2024-03-20", "time": "08:00", "activity": "睡觉", "duration": "8小时"},
            {"date": "2024-03-20", "time": "09:30", "activity": "阅读", "duration": "40min"}
        ]
        TimeBlockUtils.save_timeblock_df(self.data_dir, rows)
        loaded_rows = TimeBlockUtils.load_timeblock_df(self.data_dir)
        self.assertEqual(len(loaded_rows), 2)
        self.assertEqual(loaded_rows[0]["date"], "2024-03-20")
        self.assertEqual(loaded_rows[0]["time"], "08:00")
        self.assertEqual(loaded_rows[0]["activity"], "睡觉")
        self.assertEqual(loaded_rows[0]["duration"], "8小时")

class TestNaturalLanguageParser(unittest.TestCase):
    def test_parse_natural_timeblock(self):
        test_cases = [
            ("下午读了2小时书", "14:00 读了2小时书 2小时"),
            ("早上跑步30分钟", "07:00 跑步30分钟 30min"),
            ("晚上看电影2小时", "20:00 看电影2小时 2小时")
        ]
        for input_text, expected in test_cases:
            result = NaturalLanguageParser.parse_natural_timeblock(input_text)
            self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main() 