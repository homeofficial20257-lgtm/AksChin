# -*- coding: utf-8 -*-
"""AksChin - Persian collage maker for Windows."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageOps, ImageTk

TITLE = "عکس‌چین | کلاژساز عکس"

TEMPLATES = {
    "آزاد (شبکه‌ای)": ("شبکه‌ای", 2),
    "۲ عکس کنار هم": ("افقی", 2),
    "۳ عکس کنار هم": ("افقی", 3),
    "۴ عکس مربعی": ("شبکه‌ای", 2),
    "۶ عکس (۲×۳)": ("شبکه‌ای", 3),
    "۹ عکس (۳×۳)": ("شبکه‌ای", 3),
    "۴ عکس عمودی": ("عمودی", 1),
}

class AksChin:
    def __init__(self, root):
        self.root = root
        self.root.title(TITLE)
        self.root.geometry("1120x760")
        self.root.minsize(900, 640)
        self.paths = []
        self.bg = "#FFFFFF"
        self.preview = None
        self.drag_available = False
        self._style()
        self._ui()
        self._enable_drag_drop()
        self.refresh()
        self.update_preview()

    def _style(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("TFrame", background="#F4F6FA")
        s.configure("TLabelframe", background="#F4F6FA")
        s.configure("TLabelframe.Label", background="#F4F6FA", font=("Segoe UI", 10, "bold"))
        s.configure("TLabel", background="#F4F6FA", font=("Segoe UI", 10))
        s.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), foreground="#18243A")
        s.configure("Sub.TLabel", foreground="#596579")
        s.configure("TButton", padding=8, font=("Segoe UI", 9))
        s.configure("Accent.TButton", padding=10, font=("Segoe UI", 10, "bold"))
        self.root.configure(bg="#F4F6FA")

    def _ui(self):
        shell = ttk.Frame(self.root, padding=14)
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="عکس‌چین", style="Header.TLabel").pack(anchor="e")
        ttk.Label(shell, text="عکس‌ها را اضافه یا داخل پنجره رها کنید؛ قالب را انتخاب کنید و خروجی باکیفیت بگیرید.",
                  style="Sub.TLabel").pack(anchor="e", pady=(2, 12))

        split = ttk.Panedwindow(shell, orient="horizontal")
        split.pack(fill="both", expand=True)
        panel = ttk.Frame(split, padding=10)
        view = ttk.Frame(split, padding=10)
        split.add(panel, weight=1)
        split.add(view, weight=2)

        # Files
        ttk.Label(panel, text="مدیریت عکس‌ها", font=("Segoe UI", 12, "bold")).pack(anchor="e")
        buttons = ttk.Frame(panel)
        buttons.pack(fill="x", pady=7)
        ttk.Button(buttons, text="＋ افزودن عکس", command=self.add_dialog).pack(side="right", padx=2)
        ttk.Button(buttons, text="حذف انتخابی", command=self.remove).pack(side="right", padx=2)
        ttk.Button(buttons, text="پاک‌کردن همه", command=self.clear).pack(side="right", padx=2)

        self.drop_hint = ttk.Label(panel, text="📥 عکس‌ها را اینجا رها کنید (Drag & Drop)",
                                   anchor="center", relief="ridge", padding=10)
        self.drop_hint.pack(fill="x", pady=(0, 7))

        lf = ttk.Frame(panel)
        lf.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(lf, selectmode=tk.EXTENDED, font=("Segoe UI", 10),
                                  bg="white", relief="flat", highlightthickness=1,
                                  highlightbackground="#D9DFE8", activestyle="dotbox")
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        move = ttk.Frame(panel)
        move.pack(fill="x", pady=6)
        ttk.Button(move, text="▲ بالاتر", command=lambda: self.move(-1)).pack(side="right", padx=2)
        ttk.Button(move, text="▼ پایین‌تر", command=lambda: self.move(1)).pack(side="right", padx=2)

        # Layout options
        opts = ttk.LabelFrame(panel, text="قالب و تنظیمات", padding=9)
        opts.pack(fill="x", pady=6)
        self.template = tk.StringVar(value="آزاد (شبکه‌ای)")
        self.layout = tk.StringVar(value="شبکه‌ای")
        self.fit = tk.StringVar(value="برش برای پر کردن")
        self.cols = tk.IntVar(value=2)
        self.gap = tk.IntVar(value=14)
        self.out_w = tk.IntVar(value=2400)
        self.out_h = tk.IntVar(value=1600)

        self._combo(opts, "قالب آماده", self.template, list(TEMPLATES), self.apply_template)
        self._combo(opts, "چیدمان", self.layout, ["شبکه‌ای", "افقی", "عمودی"], self.update_preview)
        self._combo(opts, "جای‌گذاری عکس", self.fit, ["برش برای پر کردن", "نمایش کامل عکس"], self.update_preview)
        self._spin(opts, "تعداد ستون‌ها", self.cols, 1, 10)
        self._spin(opts, "فاصله بین عکس‌ها", self.gap, 0, 200)
        self._spin(opts, "عرض خروجی (px)", self.out_w, 400, 12000)
        self._spin(opts, "ارتفاع خروجی (px)", self.out_h, 400, 12000)

        colorbar = ttk.Frame(opts)
        colorbar.pack(fill="x", pady=4)
        ttk.Button(colorbar, text="انتخاب رنگ پس‌زمینه", command=self.pick_color).pack(side="right")
        self.color_text = ttk.Label(colorbar, text=self.bg)
        self.color_text.pack(side="right", padx=8)

        ttk.Button(panel, text="ساخت و ذخیره تصویر نهایی", style="Accent.TButton",
                   command=self.export).pack(fill="x", pady=(8, 2))
        ttk.Label(panel, text="خروجی PNG یا JPG با کیفیت قابل تنظیم",
                  style="Sub.TLabel").pack(anchor="e")

        # Preview area
        ttk.Label(view, text="پیش‌نمایش کلاژ", font=("Segoe UI", 12, "bold")).pack(anchor="e")
        self.preview_label = ttk.Label(view, text="هنوز عکسی انتخاب نشده است",
                                       anchor="center", relief="ridge")
        self.preview_label.pack(fill="both", expand=True, pady=8)
        ttk.Label(view, text="پیش‌نمایش کوچک‌نمایی می‌شود؛ فایل خروجی با ابعاد دقیق انتخاب‌شده ذخیره خواهد شد.",
                  style="Sub.TLabel", wraplength=620).pack(anchor="e")
        self.status = tk.StringVar(value="آماده")
        ttk.Label(shell, textvariable=self.status, relief="sunken", anchor="e", padding=5).pack(fill="x", pady=(10, 0))

    def _combo(self, parent, title, var, values, callback):
        row = ttk.Frame(parent); row.pack(fill="x", pady=3)
        ttk.Label(row, text=title).pack(side="right")
        cb = ttk.Combobox(row, textvariable=var, values=values, state="readonly", width=19)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda _e: callback())

    def _spin(self, parent, title, var, lo, hi):
        row = ttk.Frame(parent); row.pack(fill="x", pady=3)
        ttk.Label(row, text=title).pack(side="right")
        sp = ttk.Spinbox(row, from_=lo, to=hi, textvariable=var, width=9,
                         command=self.update_preview)
        sp.pack(side="left")
        sp.bind("<KeyRelease>", lambda _e: self.update_preview())
        sp.bind("<FocusOut>", lambda _e: self.update_preview())

    def _enable_drag_drop(self):
        # Optional native file drag-and-drop through tkinterdnd2.
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._drop)
            self.drop_hint.configure(text="📥 عکس‌ها را داخل پنجره رها کنید (Drag & Drop فعال است)")
            self.drag_available = True
        except Exception:
            self.drop_hint.configure(text="📥 برای Drag & Drop، نصب tkinterdnd2 لازم است؛ یا از «افزودن عکس» استفاده کنید.")

    def _drop(self, event):
        try:
            items = self.root.tk.splitlist(event.data)
            self.add_paths(items)
        except Exception as exc:
            messagebox.showerror("خطا", f"خواندن فایل‌های رهاشده ممکن نشد:\n{exc}")

    def add_dialog(self):
        files = filedialog.askopenfilenames(
            title="انتخاب عکس‌ها",
            filetypes=[("فایل‌های تصویری", "*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff")]
        )
        if files:
            self.add_paths(files)

    def add_paths(self, files):
        count = 0
        for path in files:
            path = os.path.abspath(path.strip("{}"))
            if not os.path.isfile(path) or path in self.paths:
                continue
            try:
                with Image.open(path) as im:
                    im.verify()
                self.paths.append(path)
                count += 1
            except Exception:
                continue
        self.refresh()
        self.update_preview()
        self.status.set(f"{count} عکس اضافه شد | مجموع: {len(self.paths)}")

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for i, p in enumerate(self.paths, 1):
            self.listbox.insert(tk.END, f"{i:02d}  |  {os.path.basename(p)}")

    def remove(self):
        for i in reversed(self.listbox.curselection()):
            del self.paths[i]
        self.refresh(); self.update_preview()

    def clear(self):
        self.paths.clear(); self.refresh(); self.update_preview()
        self.status.set("فهرست عکس‌ها پاک شد.")

    def move(self, direction):
        selected = list(self.listbox.curselection())
        if not selected: return
        if direction < 0:
            for i in selected:
                if i > 0 and i-1 not in selected:
                    self.paths[i-1], self.paths[i] = self.paths[i], self.paths[i-1]
            new = [max(0, i-1) for i in selected]
        else:
            for i in reversed(selected):
                if i < len(self.paths)-1 and i+1 not in selected:
                    self.paths[i+1], self.paths[i] = self.paths[i], self.paths[i+1]
            new = [min(len(self.paths)-1, i+1) for i in selected]
        self.refresh()
        for i in new: self.listbox.selection_set(i)
        self.update_preview()

    def apply_template(self):
        layout, columns = TEMPLATES[self.template.get()]
        self.layout.set(layout)
        self.cols.set(columns)
        if self.template.get() == "۴ عکس مربعی":
            self.cols.set(2)
        self.update_preview()

    def pick_color(self):
        picked = colorchooser.askcolor(color=self.bg, title="رنگ پس‌زمینه")
        if picked and picked[1]:
            self.bg = picked[1]
            self.color_text.configure(text=self.bg)
            self.update_preview()

    @staticmethod
    def _ival(var, default, lo, hi):
        try: return max(lo, min(hi, int(var.get())))
        except Exception: return default

    def compose(self, size):
        if not self.paths:
            raise ValueError("ابتدا چند عکس اضافه کنید.")
        W, H = size
        n = len(self.paths)
        gap = self._ival(self.gap, 14, 0, 200)
        if self.layout.get() == "افقی":
            cols, rows = n, 1
        elif self.layout.get() == "عمودی":
            cols, rows = 1, n
        else:
            cols = min(n, self._ival(self.cols, 2, 1, 10))
            rows = (n + cols - 1) // cols
        cw = max(1, (W - gap * (cols + 1)) // cols)
        ch = max(1, (H - gap * (rows + 1)) // rows)
        canvas = Image.new("RGB", (W, H), self.bg)
        for index, path in enumerate(self.paths):
            r, c = divmod(index, cols)
            x, y = gap + c * (cw + gap), gap + r * (ch + gap)
            with Image.open(path) as original:
                im = ImageOps.exif_transpose(original).convert("RGB")
                if self.fit.get() == "نمایش کامل عکس":
                    tile = ImageOps.contain(im, (cw, ch), Image.Resampling.LANCZOS)
                    canvas.paste(tile, (x + (cw-tile.width)//2, y + (ch-tile.height)//2))
                else:
                    tile = ImageOps.fit(im, (cw, ch), method=Image.Resampling.LANCZOS)
                    canvas.paste(tile, (x, y))
        return canvas

    def update_preview(self):
        if not hasattr(self, "preview_label"): return
        if not self.paths:
            self.preview_label.configure(image="", text="عکس‌ها را با دکمه افزودن یا Drag & Drop وارد کنید.")
            self.preview = None
            return
        try:
            w = self._ival(self.out_w, 2400, 400, 12000)
            h = self._ival(self.out_h, 1600, 400, 12000)
            im = self.compose((w, h))
            im.thumbnail((760, 590), Image.Resampling.LANCZOS)
            self.preview = ImageTk.PhotoImage(im)
            self.preview_label.configure(image=self.preview, text="")
        except Exception as exc:
            self.preview_label.configure(image="", text=f"خطا در پیش‌نمایش: {exc}")
            self.preview = None

    def export(self):
        if not self.paths:
            messagebox.showinfo("عکس‌چین", "ابتدا عکس‌ها را اضافه کنید.")
            return
        target = filedialog.asksaveasfilename(
            title="ذخیره کلاژ",
            initialfile="aks-chin.jpg",
            defaultextension=".jpg",
            filetypes=[("JPEG باکیفیت", "*.jpg"), ("PNG", "*.png")]
        )
        if not target: return
        try:
            w = self._ival(self.out_w, 2400, 400, 12000)
            h = self._ival(self.out_h, 1600, 400, 12000)
            image = self.compose((w, h))
            if target.lower().endswith(".png"):
                image.save(target, "PNG", optimize=True)
            else:
                image.save(target, "JPEG", quality=96, subsampling=0, optimize=True)
            self.status.set(f"ذخیره شد: {target}")
            messagebox.showinfo("انجام شد", f"کلاژ با موفقیت ذخیره شد:\n{target}")
        except Exception as exc:
            messagebox.showerror("خطا در ذخیره", str(exc))


def main():
    # TkinterDnD provides file drop support; ordinary Tk is used if unavailable.
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except Exception:
        root = tk.Tk()
    AksChin(root)
    root.mainloop()

if __name__ == "__main__":
    main()
