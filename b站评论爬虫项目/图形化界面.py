import io
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser

from bilibililogin import *  # 保留原来的搜索视频和爬评论函数

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class BilibiliApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bilibili 视频评论爬取工具")
        self.geometry("800x600")

        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame, text="关键词：").pack(side="left")
        self.comment_kw = tk.Entry(frame, width=50)
        self.comment_kw.pack(side="left")
        ttk.Button(frame, text="搜索视频", command=lambda: self.threaded(self.search_video)).pack(side="left")

        self.video_listbox = tk.Listbox(self, height=8)
        self.video_listbox.pack(fill="x", padx=10, pady=5)

        ttk.Button(self, text="爬取评论", command=lambda: self.threaded(self.fetch_comments)).pack(pady=5)
        ttk.Button(self, text="打开视频链接", command=self.open_selected_video).pack(pady=5)

        self.comment_output = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=20)
        self.comment_output.pack(fill="both", expand=True, padx=10, pady=5)

    def threaded(self, func):
        threading.Thread(target=func).start()

    def search_video(self):
        kw = self.comment_kw.get().strip()
        if not kw:
            messagebox.showwarning("提示", "请输入关键词")
            return
        self.comment_output.delete(1.0, tk.END)
        self.comment_output.insert(tk.END, "正在搜索视频...\n")
        try:
            videos = search_videos(kw)  # 保留原来的搜索函数
            self.video_listbox.delete(0, tk.END)
            self.video_results = videos
            if not videos:
                self.comment_output.insert(tk.END, "未找到相关视频。\n")
            else:
                for bvid, title, url in videos:
                    self.video_listbox.insert(tk.END, f"{title} ({bvid})")
                self.comment_output.insert(tk.END, f"找到 {len(videos)} 个视频。\n")
        except Exception as e:
            self.comment_output.insert(tk.END, f"搜索视频异常：{e}\n")

    def open_selected_video(self):
        sel = self.video_listbox.curselection()
        if not sel:
            messagebox.showwarning("提示", "请先选择视频")
            return
        url = self.video_results[sel[0]][2]
        webbrowser.open_new_tab(url)

    def fetch_comments(self):
        sel = self.video_listbox.curselection()
        if not sel:
            messagebox.showwarning("提示", "请先选择视频")
            return
        info = self.video_listbox.get(sel[0])
        bvid = info.split('(')[-1].strip(')')
        self.comment_output.insert(tk.END, f"开始爬取视频 {bvid} 的评论...\n")
        try:
            comments = crawl_bilibili_comments(bvid)  # 保留原来的爬评论函数
            self.comment_output.insert(tk.END, f"共爬取 {len(comments)} 条评论。\n")
            for u, mid, msg in comments:
                self.comment_output.insert(tk.END, f"{u}({mid}): {msg}\n")
        except Exception as e:
            self.comment_output.insert(tk.END, f"爬取评论异常：{e}\n")


if __name__ == "__main__":
    app = BilibiliApp()
    app.mainloop()
