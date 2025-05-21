import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Toplevel
import json
from datetime import datetime
import os
import threading
import sys
import re
from pathlib import Path
import asyncio
from PIL import Image, ImageDraw, ImageTk
from typing import List
from dataclasses import asdict
import logging

from ..core.models import TimeTrackerData, TaskItem
from ..core.analyzer import TimeBlockUtils, NaturalLanguageParser
from .widgets.custom_widgets import PlaceholderText, FluentButton, TaskItemFrame

logger = logging.getLogger(__name__)

class TimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bg_color = "#FFFFFF"
        self.text_color = "#000000"
        self.root.configure(bg=self.bg_color)
        self.save_status = tk.StringVar()
        self.save_status.set("未保存")
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.data_dir = Path.cwd() / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.data = TimeTrackerData(date=self.current_date)
        self.current_module = "today"
        self.sentiment_analyzer = None
        self.sentiment_thread = threading.Thread(target=self.load_sentiment_model, daemon=True)
        self.sentiment_thread.start()
        self.create_widgets()
        self.load_data(self.current_date)
        self.auto_save_interval = 300  # 5分钟
        self.auto_save_task = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.root.after(100, self.start_auto_save)
        self.encourage_label = None
        self.last_encourage_count = 0
        logger.info("TimeTracker 初始化完成")

    def create_widgets(self):
        self.root.title(self.get_title())
        self.title_label = tk.Label(
            self.root,
            text="唯有那份炫目，未曾忘却",
            font=("微软雅黑", 20, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.title_label.pack(pady=20)
        self.button_frame = tk.Frame(self.root, bg=self.bg_color)
        self.button_frame.pack(pady=10)
        self.new_button = FluentButton(
            self.button_frame,
            text="新建",
            command=self.new_day,
            width=90
        )
        self.new_button.pack(side=tk.LEFT, padx=5)
        self.switch_button = FluentButton(
            self.button_frame,
            text="切换模块",
            command=self.switch_module,
            width=90
        )
        self.switch_button.pack(side=tk.LEFT, padx=5)
        self.export_button = FluentButton(
            self.button_frame,
            text="导出MD",
            command=self.export_md,
            width=90
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
        self.date_button = FluentButton(
            self.button_frame,
            text="选择日期",
            command=self.choose_date,
            width=90
        )
        self.date_button.pack(side=tk.LEFT, padx=5)
        self.status_label = tk.Label(
            self.root,
            textvariable=self.save_status,
            font=("微软雅黑", 10),
            bg=self.bg_color,
            fg="#008800"
        )
        self.status_label.pack(pady=2)
        self.time_stat_label = tk.Label(
            self.root,
            text="今日已记录时长: 0分钟",
            font=("微软雅黑", 10),
            bg=self.bg_color,
            fg="#000000"
        )
        self.time_stat_label.pack(pady=2)
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.init_today_module()

    def get_title(self):
        return f"时间记录器 - {self.current_date} [{self.save_status.get()}]"

    def update_title(self):
        self.root.title(self.get_title())

    def start_auto_save(self):
        """启动自动保存"""
        try:
            if not self.auto_save_task:
                self.auto_save_task = self.loop.create_task(self.async_auto_save_loop())
            self.root.after(100, self.start_auto_save)
        except Exception as e:
            logger.error(f"自动保存启动失败: {e}", exc_info=True)

    async def async_auto_save_loop(self):
        """自动保存循环"""
        while True:
            try:
                await asyncio.sleep(self.auto_save_interval)
                self.save_data(auto=True)
            except Exception as e:
                logger.error(f"自动保存失败: {e}", exc_info=True)
                await asyncio.sleep(60)  # 出错后等待1分钟再试

    def choose_date(self):
        date = simpledialog.askstring("选择日期", "请输入日期 (YYYY-MM-DD)：", initialvalue=self.current_date)
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
                self.save_data()
                self.current_date = date
                self.load_data(self.current_date)
                self.save_status.set("未保存")
                self.update_title()
            except ValueError:
                messagebox.showerror("错误", "日期格式不正确！")

    def load_data(self, date):
        filename = self.data_dir / f"{date}.json"
        if filename.exists():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    d['tasks'] = [TaskItem(**t) for t in d.get('tasks',[])]
                    self.data = TimeTrackerData(**d)
            except Exception as e:
                messagebox.showerror("错误", f"加载数据失败: {str(e)}")
                self.data = TimeTrackerData(date=date)
        else:
            self.data = TimeTrackerData(date=date)
        self.refresh_ui_from_data()

    def refresh_ui_from_data(self):
        if hasattr(self, 'time_blocks_text') and self.time_blocks_text.winfo_exists():
            self.time_blocks_text.set_value(self.data.time_blocks)
        if hasattr(self, 'diary_text') and self.diary_text.winfo_exists():
            self.diary_text.set_value(self.data.diary)
        if hasattr(self, 'tasks_frame') and self.tasks_frame.winfo_exists():
            for widget in self.tasks_frame.winfo_children():
                widget.destroy()
            for task in self.data.tasks:
                self.add_task_item(task.text, task.done)
        if hasattr(self, 'mood_var'):
            self.mood_var.set(self.data.mood)
        self.update_time_stat()
        self.update_title()

    def update_data_from_ui(self):
        if hasattr(self, 'time_blocks_text') and self.time_blocks_text.winfo_exists():
            self.data.time_blocks = self.time_blocks_text.get_value()
        if hasattr(self, 'diary_text') and self.diary_text.winfo_exists():
            self.data.diary = self.diary_text.get_value()
        if hasattr(self, 'tasks_frame') and self.tasks_frame.winfo_exists():
            tasks = []
            for widget in self.tasks_frame.winfo_children():
                if isinstance(widget, TaskItemFrame):
                    tasks.append(widget.get())
            self.data.tasks = tasks
        if hasattr(self, 'mood_var'):
            self.data.mood = self.mood_var.get()

    def switch_module(self):
        self.update_data_from_ui()
        if not self.validate_time_blocks():
            return
        self.save_data()
        if self.current_module == "today":
            self.current_module = "tomorrow"
            self.init_tomorrow_module()
        else:
            self.current_module = "today"
            self.init_today_module()
        self.refresh_ui_from_data()

    def new_day(self):
        self.update_data_from_ui()
        if not self.validate_time_blocks():
            return
        self.save_data()
        date = simpledialog.askstring("新建日期", "请输入新日期 (YYYY-MM-DD)：", initialvalue=datetime.now().strftime("%Y-%m-%d"))
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
                self.current_date = date
            except ValueError:
                messagebox.showerror("错误", "日期格式不正确！")
                return
        else:
            return
        self.data = TimeTrackerData(date=self.current_date)
        self.init_today_module() if self.current_module == "today" else self.init_tomorrow_module()
        self.refresh_ui_from_data()
        self.save_status.set("未保存")
        self.update_title()

    def save_data(self, auto=False):
        self.update_data_from_ui()
        filename = self.data_dir / f"{self.current_date}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                d = asdict(self.data)
                d['tasks'] = [asdict(t) for t in self.data.tasks]
                json.dump(d, f, ensure_ascii=False, indent=4)
            if self.data.time_blocks.strip():
                rows = TimeBlockUtils.parse_time_blocks(self.data.time_blocks, self.current_date)
                TimeBlockUtils.save_timeblock_df(self.data_dir, rows)
            if not auto:
                self.save_status.set("已保存")
            else:
                self.save_status.set("自动保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存数据失败: {str(e)}")
            self.save_status.set("保存失败")
        self.update_title()
        self.update_time_stat()
        if not auto and self.sentiment_analyzer:
            diary = self.data.diary.strip()
            if diary:
                threading.Thread(target=self.analyze_diary_sentiment, args=(diary,), daemon=True).start()

    def analyze_diary_sentiment(self, text):
        try:
            result = self.sentiment_analyzer(text[:512])[0]
            if result['label'] == 'NEGATIVE' and result['score'] > 0.7:
                self.show_encourage_message("检测到你今天心情不佳，记得多关心自己，明天会更好！")
        except Exception:
            pass

    def show_encourage_message(self, msg_or_count):
        if isinstance(msg_or_count, int):
            msg = f"已写{msg_or_count}字，继续加油！"
        else:
            msg = msg_or_count
        if self.encourage_label and self.encourage_label.winfo_exists():
            self.encourage_label.destroy()
        self.encourage_label = tk.Label(self.root, text=msg, font=("微软雅黑", 14, "bold"), bg="#222", fg="#fff")
        self.encourage_label.place(relx=0.5, rely=0.1, anchor="center")
        self.root.after(2000, lambda: self.encourage_label.destroy() if self.encourage_label and self.encourage_label.winfo_exists() else None)

    def export_md(self):
        self.save_data()
        tasks_md = "\n".join([f"- [{'x' if t.done else ' '}] {t.text}" for t in self.data.tasks])
        md_content = f"""# {self.current_date} 时间记录\n\n## 时间块\n{self.data.time_blocks}\n\n## 今日总结\n{self.data.diary}\n\n## 今日待办\n{tasks_md}\n\n## 心情\n{self.data.mood}\n"""
        filename = self.data_dir / f"{self.current_date}.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
            if sys.platform.startswith('win'):
                os.startfile(str(self.data_dir))
            elif sys.platform.startswith('darwin'):
                os.system(f'open "{self.data_dir}"')
            else:
                os.system(f'xdg-open "{self.data_dir}"')
            messagebox.showinfo("成功", f"已导出到 {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出Markdown失败: {str(e)}")

    def on_close(self):
        """关闭窗口时的处理"""
        try:
            if self.auto_save_task:
                self.auto_save_task.cancel()
            if self.loop.is_running():
                self.loop.stop()
            self.save_data()
            self.root.destroy()
        except Exception as e:
            logger.error(f"关闭窗口时出错: {e}", exc_info=True)
            self.root.destroy()

    def create_emoji_image(self, mood, size=32):
        img = Image.new('RGBA', (size, size), (255,255,255,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((2,2,size-2,size-2), fill='#FFF', outline='#222', width=2)
        if mood in ['happy','smile','neutral','sad','angry','sleepy','think']:
            draw.ellipse((size*0.28, size*0.38, size*0.38, size*0.48), fill='#222')
            draw.ellipse((size*0.62, size*0.38, size*0.72, size*0.48), fill='#222')
        if mood=='happy':
            draw.arc((size*0.28, size*0.55, size*0.72, size*0.85), 0, 180, fill='#222', width=2)
        elif mood=='smile':
            draw.arc((size*0.32, size*0.60, size*0.68, size*0.80), 10, 170, fill='#222', width=2)
        elif mood=='neutral':
            draw.line((size*0.32, size*0.75, size*0.68, size*0.75), fill='#222', width=2)
        elif mood=='sad':
            draw.arc((size*0.32, size*0.75, size*0.68, size*0.95), 190, 350, fill='#222', width=2)
        elif mood=='angry':
            draw.arc((size*0.32, size*0.80, size*0.68, size*0.95), 200, 340, fill='#222', width=2)
            draw.line((size*0.25, size*0.25, size*0.40, size*0.40), fill='#222', width=2)
            draw.line((size*0.60, size*0.40, size*0.75, size*0.25), fill='#222', width=2)
        elif mood=='sleepy':
            draw.arc((size*0.32, size*0.80, size*0.68, size*0.95), 200, 340, fill='#222', width=2)
            draw.line((size*0.28, size*0.45, size*0.38, size*0.45), fill='#222', width=2)
            draw.line((size*0.62, size*0.45, size*0.72, size*0.45), fill='#222', width=2)
        elif mood=='think':
            draw.arc((size*0.32, size*0.80, size*0.68, size*0.95), 200, 340, fill='#222', width=2)
            draw.ellipse((size*0.45, size*0.85, size*0.55, size*0.95), fill='#222')
        return ImageTk.PhotoImage(img)

    def init_today_module(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.time_blocks_text = PlaceholderText(
            self.main_frame,
            placeholder="如 08:00 睡觉 8小时\n09:30 阅读 40min\n也支持自然语言如 '下午读了2小时书'",
            height=5,
            width=50
        )
        self.time_blocks_text.pack(padx=5, pady=5, fill=tk.X)
        self.mood_var = tk.StringVar()
        mood_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        mood_frame.pack(pady=2)
        tk.Label(mood_frame, text="今日心情：", bg=self.bg_color).pack(side=tk.LEFT)
        self.emoji_imgs = {}
        emoji_map = [
            ('happy', '开心'),
            ('smile', '微笑'),
            ('neutral', '平静'),
            ('sad', '难过'),
            ('angry', '生气'),
            ('sleepy', '困倦'),
            ('think', '思考')
        ]
        for mood, label in emoji_map:
            img = self.create_emoji_image(mood)
            self.emoji_imgs[mood] = img
            b = tk.Radiobutton(mood_frame, image=img, variable=self.mood_var, value=mood, indicatoron=0, width=36, height=36, bg=self.bg_color, selectcolor='#ddd')
            b.pack(side=tk.LEFT, padx=2)
            b_tip = tk.Label(mood_frame, text=label, bg=self.bg_color, font=("微软雅黑", 8))
            b_tip.pack(side=tk.LEFT, padx=(0,8))
        self.diary_text = PlaceholderText(
            self.main_frame,
            placeholder="写下你的今日总结或心情...",
            height=10,
            width=50
        )
        self.diary_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.diary_text.bind("<KeyRelease>", self.on_diary_typing)
        self.last_encourage_count = 0

    def on_diary_typing(self, event=None):
        text = self.diary_text.get_value()
        count = len(text)
        if count // 50 > self.last_encourage_count:
            self.last_encourage_count = count // 50
            self.show_encourage_message(self.last_encourage_count * 50)
        if count // 50 == 0:
            self.last_encourage_count = 0

    def init_tomorrow_module(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        tk.Label(self.main_frame, text="今日待办", bg=self.bg_color, font=("微软雅黑", 12, "bold")).pack(anchor="w")
        self.tasks_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.tasks_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        add_task_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        add_task_frame.pack(pady=2)
        self.new_task_var = tk.StringVar()
        entry = tk.Entry(add_task_frame, textvariable=self.new_task_var, width=40, fg="#888888")
        entry.insert(0, "输入今日任务，回车添加")
        def on_focus_in(e):
            if entry.get() == "输入今日任务，回车添加":
                entry.delete(0, tk.END)
                entry['fg'] = "#000000"
        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, "输入今日任务，回车添加")
                entry['fg'] = "#888888"
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", lambda e: self.add_task_item(entry.get(), False, clear=True))
        entry.pack(side=tk.LEFT, padx=5)
        add_btn = tk.Button(add_task_frame, text="添加", command=lambda: self.add_task_item(entry.get(), False, clear=True))
        add_btn.pack(side=tk.LEFT)

    def add_task_item(self, text, done, clear=False):
        if not text or text == "输入今日任务，回车添加":
            return
        item = TaskItem(text, done)
        frame_item = TaskItemFrame(self.tasks_frame, item, on_toggle=self.save_data)
        frame_item.pack(anchor="w", pady=2, fill=tk.X)
        if clear:
            self.new_task_var.set("")

    def validate_time_blocks(self):
        if self.current_module != "today":
            return True
        lines = self.time_blocks_text.get_value().splitlines()
        parsed = None
        for idx, line in enumerate(lines):
            if line.strip() == "":
                continue
            std_line = line.strip()
            parsed = NaturalLanguageParser.parse_natural_timeblock(std_line)
            if parsed:
                lines[idx] = parsed
                std_line = parsed
            parts = std_line.split()
            match parts:
                case [time, *activity, duration] if (
                    (len(time.replace(':', '').replace(' ', '')) == 4 and ':' in time)
                    or (len(time.replace(':', '').replace(' ', '')) == 4 and time.count(':') == 1)
                ) and (
                    duration.endswith('小时') or duration.endswith('min')
                ):
                    continue
                case _:
                    messagebox.showerror(
                        "格式错误",
                        f"第{idx+1}行时间块格式应为 'HH:MM 活动 时长' 或 'HH: MM 活动 时长'，如 08:00 睡觉 8小时 或 09:30 阅读 40min\n也支持自然语言如 '下午读了2小时书'"
                    )
                    return False
        if parsed:
            self.time_blocks_text.set_value('\n'.join(lines))
        return True

    def update_time_stat(self):
        total_min = 0
        lines = self.data.time_blocks.splitlines()
        time_blocks = []
        for line in lines:
            m = re.match(r"^(\d{2}): ?(\d{2}) .+ (\d+)小时$", line.strip())
            if m:
                mins = int(m.group(3)) * 60
                total_min += mins
                time_blocks.append((line.strip(), mins))
            else:
                m = re.match(r"^(\d{2}): ?(\d{2}) .+ (\d+)min$", line.strip())
                if m:
                    mins = int(m.group(3))
                    total_min += mins
                    time_blocks.append((line.strip(), mins))
        self.time_stat_label.config(text=f"今日已记录时长: {total_min}分钟")
        self.draw_time_bar(time_blocks, total_min)

    def draw_time_bar(self, time_blocks, total_min):
        if total_min == 0 or not time_blocks:
            return
        win = Toplevel(self.root)
        win.title("今日时间分布")
        text = tk.Text(win, height=20, width=60)
        text.pack(padx=10, pady=10)
        
        for desc, mins in time_blocks:
            percentage = (mins / total_min) * 100
            bar = "█" * int(percentage / 2)
            text.insert(tk.END, f"{desc}: {bar} {percentage:.1f}%\n")
        
        text.config(state=tk.DISABLED)

    def load_sentiment_model(self):
        try:
            from transformers import pipeline
            self.sentiment_analyzer = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
        except Exception as e:
            self.sentiment_analyzer = None 