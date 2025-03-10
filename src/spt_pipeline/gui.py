#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import logging
import os
import queue
import tkinter as tk
from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox, scrolledtext

from spt_pipeline.main import main
from spt_pipeline.utils import ADDON_URL, BLENDER_PATH, RESOURCE_DIR


class GuiLogHandler(logging.Handler):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.queue = queue.Queue()

    def emit(self, record):
        msg = self.format(record)
        level = record.levelname
        self.queue.put((level, msg))
        self.root.event_generate("<<NewLog>>")


class PathSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("Import wizard")

        self.blender_exe = tk.StringVar(value=BLENDER_PATH)
        self.game_path = tk.StringVar()

        self.install_blender = tk.BooleanVar(value=False)

        self.logger = logging.getLogger(__name__)

        self.create_widgets()
        self.setup_logging()

    def create_widgets(self):
        input_group = tk.LabelFrame(self.root, text="Configuration", padx=10, pady=10)
        input_group.pack(fill="x", padx=20, pady=10)

        tk.Label(input_group, text="Blender Path:", anchor="w").grid(
            row=0, column=0, padx=10, sticky="w"
        )
        self.blender_entry = tk.Entry(input_group, textvariable=self.blender_exe, width=40)
        self.blender_entry.grid(row=0, column=1, padx=10)

        self.blender_browse_btn = tk.Button(
            input_group, text="Browse...", command=lambda: self.file_dialog("blender")
        )
        self.blender_browse_btn.grid(row=0, column=2)

        state = "disabled" if os.name != "nt" else "normal"

        tk.Checkbutton(
            input_group,
            text="Install Blender",
            variable=self.install_blender,
            command=self.toggle_blender_field,
            state=state,
        ).grid(row=0, column=3, padx=10, sticky="w")

        tk.Label(input_group, text="Game path:", width=15, anchor="w").grid(
            row=1, column=0, padx=10, sticky="e"
        )
        tk.Entry(input_group, textvariable=self.game_path, width=40).grid(row=1, column=1, padx=10)
        tk.Button(
            input_group, text="Browse...", command=lambda: self.directory_dialog(self.game_path)
        ).grid(row=1, column=2, padx=10)

        log_label = tk.Label(self.root, text="Logs", font=("Arial", 10, "bold"))
        log_label.pack(anchor="w", padx=20, pady=(10, 0))

        self.log_display = scrolledtext.ScrolledText(
            self.root, height=12, state="disabled", bg="#f8f8f8"
        )
        self.log_display.pack(fill="both", expand=True, padx=20, pady=5)

        self.log_display.tag_config("INFO", foreground="black")
        self.log_display.tag_config("WARNING", foreground="orange")  # Orange-ish
        self.log_display.tag_config("ERROR", foreground="red")  # Red
        self.log_display.tag_config("SUCCESS", foreground="green")  # Green

        self.next_button = tk.Button(self.root, text="Next", width=10, command=self.on_next)
        self.next_button.pack(side="right", padx=20, pady=10)

    def toggle_blender_field(self):
        state = "disabled" if self.install_blender.get() else "normal"
        self.blender_entry.config(state=state)
        self.blender_browse_btn.config(state=state)
        self.blender_exe.set(BLENDER_PATH)
        self.logger.debug(f"Install blender: {self.install_blender.get()}")

    def file_dialog(self, var):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def directory_dialog(self, var):
        path = filedialog.askdirectory(mustexist=True)
        if path:
            var.set(path)

    def on_next(self):
        if not all([self.blender_exe.get(), self.game_path.get()]):
            messagebox.showwarning(
                "Missing paths", "Please provide all three paths before continuing."
            )
            return

        pipeline_path = RESOURCE_DIR / "pipeline.yaml"
        file = open(pipeline_path, "r", encoding="utf-8")
        self.thread = Thread(
            target=main,
            kwargs={
                "source": Path(self.game_path.get()),
                "blender": Path(self.blender_exe.get()),
                "file": file,
                "blender_install": self.install_blender.get(),
            },
        )
        self.thread.start()

    def setup_logging(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        handler = GuiLogHandler(self.root)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.gui_handler = handler
        self.root.bind("<<NewLog>>", self.handle_new_log)

    def handle_new_log(self, event):
        try:
            while True:
                lvl, msg = self.gui_handler.queue.get(block=False)
                self.log_display.configure(state="normal")
                self.log_display.insert(tk.END, msg + "\n", lvl)
                self.log_display.configure(state="disabled")
                self.log_display.yview(tk.END)  # Auto-scroll to bottom
        except queue.Empty:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = PathSelector(root)
    root.mainloop()
