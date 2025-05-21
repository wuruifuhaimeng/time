import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

class PlaceholderText(tk.Text):
    def __init__(self, master=None, placeholder="", color="#cccccc", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg'] if 'fg' in kwargs else "#000000"
        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._show_placeholder)
        self._show_placeholder()

    def _show_placeholder(self, event=None):
        if not self.get(1.0, tk.END).strip():
            self.insert(1.0, self.placeholder)
            self['fg'] = self.placeholder_color

    def _clear_placeholder(self, event=None):
        if self['fg'] == self.placeholder_color:
            self.delete(1.0, tk.END)
            self['fg'] = self.default_fg_color

    def get_value(self):
        if self['fg'] == self.placeholder_color:
            return ""
        return self.get(1.0, tk.END).strip()

    def set_value(self, value):
        self.delete(1.0, tk.END)
        if value:
            self.insert(1.0, value)
            self['fg'] = self.default_fg_color
        else:
            self._show_placeholder()

class FluentButton(tk.Canvas):
    def __init__(self, master, text, command=None, width=90, height=36, radius=18, bg='#F5F5F5', fg='#222', font=("微软雅黑", 12), **kwargs):
        super().__init__(master, width=width, height=height, bg=master['bg'], highlightthickness=0, bd=0, **kwargs)
        self.command = command
        self.text = text
        self.radius = radius
        self.bg_color = bg
        self.fg_color = fg
        self.font = font
        self.is_pressed = False
        self.button = self.create_oval(2, 2, width-2, height-2, fill=bg, outline='#bbb', width=1)
        self.label = self.create_text(width//2, height//2, text=text, fill=fg, font=font)
        self.bind('<Button-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Enter>', self.on_hover)
        self.bind('<Leave>', self.on_leave)
        self.tag_bind(self.button, '<Button-1>', self.on_press)
        self.tag_bind(self.button, '<ButtonRelease-1>', self.on_release)
        self.tag_bind(self.button, '<Enter>', self.on_hover)
        self.tag_bind(self.button, '<Leave>', self.on_leave)
        self.tag_bind(self.label, '<Button-1>', self.on_press)
        self.tag_bind(self.label, '<ButtonRelease-1>', self.on_release)
        self.tag_bind(self.label, '<Enter>', self.on_hover)
        self.tag_bind(self.label, '<Leave>', self.on_leave)

    def on_press(self, event):
        self.is_pressed = True
        self.scale('all', self.winfo_width()//2, self.winfo_height()//2, 0.96, 0.96)

    def on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.scale('all', self.winfo_width()//2, self.winfo_height()//2, 1/0.96, 1/0.96)
            if self.command:
                self.command()

    def on_hover(self, event):
        self.itemconfig(self.button, fill='#EEEEEE', outline='#888')

    def on_leave(self, event):
        self.itemconfig(self.button, fill=self.bg_color, outline='#bbb')

class TaskItemFrame(tk.Frame):
    def __init__(self, master, task, on_toggle=None):
        super().__init__(master, bg=master['bg'])
        self.task = task
        self.var = tk.BooleanVar(value=task.done)
        self.cb = tk.Checkbutton(self, variable=self.var, command=self.toggle, bg=master['bg'])
        self.cb.pack(side=tk.LEFT)
        self.label = tk.Label(self, text=task.text, bg=master['bg'])
        self.label.pack(side=tk.LEFT, padx=5)
        self.on_toggle = on_toggle

    def toggle(self):
        self.task.done = self.var.get()
        if self.on_toggle:
            self.on_toggle()

    def get(self):
        return self.task

    def set(self, text, done):
        self.label['text'] = text
        self.var.set(done)
        self.task.text = text
        self.task.done = done 