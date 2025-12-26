import os
from dataclasses import dataclass
from typing import Optional, Tuple, List

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageDraw, ImageFont, ImageEnhance


SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")


@dataclass
class WatermarkConfig:
    mode: str  # "text" or "logo"
    text: str
    font_size: int
    opacity: int  # 0-100
    position: str  # "Bottom Right", ...
    margin: int
    scale_pct: int  # logo scale percent relative to image width
    logo_path: Optional[str]


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def list_images(folder: str) -> List[str]:
    paths = []
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and name.lower().endswith(SUPPORTED_EXTS):
            paths.append(p)
    return sorted(paths)


def compute_position(canvas_size: Tuple[int, int], wm_size: Tuple[int, int], pos: str, margin: int) -> Tuple[int, int]:
    cw, ch = canvas_size
    ww, wh = wm_size

    if pos == "Top Left":
        return (margin, margin)
    if pos == "Top Right":
        return (cw - ww - margin, margin)
    if pos == "Bottom Left":
        return (margin, ch - wh - margin)
    if pos == "Center":
        return ((cw - ww) // 2, (ch - wh) // 2)
    # Bottom Right default
    return (cw - ww - margin, ch - wh - margin)


def load_default_font(size: int) -> ImageFont.FreeTypeFont:
    # Tries common fonts; falls back to PIL built-in
    for font_name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(font_name, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def make_text_watermark_layer(base_size: Tuple[int, int], text: str, font_size: int, opacity_pct: int) -> Image.Image:
    layer = Image.new("RGBA", base_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    font = load_default_font(font_size)

    # Compute text bbox
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Create tight watermark image then paste later with chosen position
    wm = Image.new("RGBA", (tw + 12, th + 8), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(wm)

    # White text with subtle black shadow for readability
    shadow = (0, 0, 0, int(255 * (opacity_pct / 100.0)))
    fg = (255, 255, 255, int(255 * (opacity_pct / 100.0)))

    d2.text((7, 5), text, font=font, fill=shadow)
    d2.text((6, 4), text, font=font, fill=fg)

    return wm


def make_logo_watermark(logo_path: str, base_w: int, scale_pct: int, opacity_pct: int) -> Image.Image:
    logo = Image.open(logo_path).convert("RGBA")

    # Scale logo based on base image width
    target_w = max(24, int(base_w * (scale_pct / 100.0)))
    ratio = target_w / max(1, logo.width)
    target_h = max(24, int(logo.height * ratio))
    logo = logo.resize((target_w, target_h), Image.LANCZOS)

    # Apply opacity
    if opacity_pct < 100:
        alpha = logo.split()[-1]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity_pct / 100.0)
        logo.putalpha(alpha)

    return logo


def apply_watermark_to_image(img_path: str, out_path: str, cfg: WatermarkConfig) -> None:
    base = Image.open(img_path).convert("RGBA")

    if cfg.mode == "text":
        wm = make_text_watermark_layer(base.size, cfg.text.strip() or "Watermark", cfg.font_size, cfg.opacity)
    else:
        if not cfg.logo_path or not os.path.exists(cfg.logo_path):
            raise ValueError("Logo file not found. Select a valid logo image.")
        wm = make_logo_watermark(cfg.logo_path, base.width, cfg.scale_pct, cfg.opacity)

    x, y = compute_position((base.width, base.height), (wm.width, wm.height), cfg.position, cfg.margin)

    # Composite watermark
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(wm, (x, y), wm)
    out = Image.alpha_composite(base, layer)

    # Save as original format when possible; default PNG if alpha
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ext = os.path.splitext(out_path)[1].lower()

    # If saving JPEG, must remove alpha
    if ext in (".jpg", ".jpeg"):
        out = out.convert("RGB")
        out.save(out_path, quality=95)
    else:
        out.save(out_path)


class WatermarkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Watermarking Desktop App (Python)")
        self.geometry("820x520")
        self.minsize(820, 520)

        self.single_image_path = tk.StringVar(value="")
        self.input_folder = tk.StringVar(value="")
        self.output_folder = tk.StringVar(value="")
        self.logo_path = tk.StringVar(value="")

        self.mode = tk.StringVar(value="text")
        self.text = tk.StringVar(value="© Your Brand")
        self.font_size = tk.IntVar(value=48)
        self.opacity = tk.IntVar(value=35)
        self.position = tk.StringVar(value="Bottom Right")
        self.margin = tk.IntVar(value=24)
        self.scale_pct = tk.IntVar(value=18)

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 8}

        header = ttk.Label(self, text="Watermark Images", font=("Segoe UI", 16, "bold"))
        header.pack(anchor="w", **pad)

        # Paths frame
        paths = ttk.LabelFrame(self, text="Files / Folders")
        paths.pack(fill="x", padx=10, pady=8)

        # Single image row
        ttk.Label(paths, text="Single image:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(paths, textvariable=self.single_image_path, width=80).grid(row=0, column=1, sticky="we", padx=8)
        ttk.Button(paths, text="Browse", command=self.pick_single_image).grid(row=0, column=2, padx=8)

        # Batch folder row
        ttk.Label(paths, text="Input folder:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(paths, textvariable=self.input_folder, width=80).grid(row=1, column=1, sticky="we", padx=8)
        ttk.Button(paths, text="Browse", command=self.pick_input_folder).grid(row=1, column=2, padx=8)

        # Output folder row
        ttk.Label(paths, text="Output folder:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(paths, textvariable=self.output_folder, width=80).grid(row=2, column=1, sticky="we", padx=8)
        ttk.Button(paths, text="Browse", command=self.pick_output_folder).grid(row=2, column=2, padx=8)

        paths.grid_columnconfigure(1, weight=1)

        # Watermark config
        cfg = ttk.LabelFrame(self, text="Watermark Settings")
        cfg.pack(fill="x", padx=10, pady=8)

        # Mode
        ttk.Label(cfg, text="Type:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Radiobutton(cfg, text="Text", variable=self.mode, value="text", command=self._toggle_mode).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(cfg, text="Logo", variable=self.mode, value="logo", command=self._toggle_mode).grid(row=0, column=2, sticky="w")

        # Text
        ttk.Label(cfg, text="Text:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.text_entry = ttk.Entry(cfg, textvariable=self.text, width=50)
        self.text_entry.grid(row=1, column=1, columnspan=2, sticky="we", padx=8)

        # Logo picker
        ttk.Label(cfg, text="Logo file:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.logo_entry = ttk.Entry(cfg, textvariable=self.logo_path, width=50, state="disabled")
        self.logo_entry.grid(row=2, column=1, sticky="we", padx=8)
        self.logo_btn = ttk.Button(cfg, text="Browse", command=self.pick_logo, state="disabled")
        self.logo_btn.grid(row=2, column=2, padx=8)

        # Font size / opacity
        ttk.Label(cfg, text="Font size:").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        ttk.Spinbox(cfg, from_=10, to=200, textvariable=self.font_size, width=8).grid(row=3, column=1, sticky="w", padx=8)

        ttk.Label(cfg, text="Opacity (%):").grid(row=3, column=2, sticky="w", padx=8)
        ttk.Scale(cfg, from_=0, to=100, orient="horizontal", variable=self.opacity).grid(row=3, column=3, sticky="we", padx=8)

        # Position / margin / scale
        ttk.Label(cfg, text="Position:").grid(row=4, column=0, sticky="w", padx=8, pady=6)
        pos = ttk.Combobox(cfg, textvariable=self.position, values=["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center"], state="readonly", width=18)
        pos.grid(row=4, column=1, sticky="w", padx=8)

        ttk.Label(cfg, text="Margin (px):").grid(row=4, column=2, sticky="w", padx=8)
        ttk.Spinbox(cfg, from_=0, to=200, textvariable=self.margin, width=8).grid(row=4, column=3, sticky="w", padx=8)

        ttk.Label(cfg, text="Logo scale (% width):").grid(row=5, column=0, sticky="w", padx=8, pady=6)
        ttk.Spinbox(cfg, from_=5, to=60, textvariable=self.scale_pct, width=8).grid(row=5, column=1, sticky="w", padx=8)

        cfg.grid_columnconfigure(3, weight=1)

        # Actions
        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=10, pady=10)

        ttk.Button(actions, text="Watermark Single Image", command=self.watermark_single).pack(side="left")
        ttk.Button(actions, text="Watermark Folder (Batch)", command=self.watermark_batch).pack(side="left", padx=8)
        ttk.Button(actions, text="Open Output Folder", command=self.open_output).pack(side="left", padx=8)

        # Log box
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=True, padx=10, pady=8)

        self.log = tk.Text(log_frame, height=10, wrap="word")
        self.log.pack(fill="both", expand=True, padx=8, pady=8)

        self._toggle_mode()

    def _toggle_mode(self):
        is_text = self.mode.get() == "text"
        self.text_entry.configure(state="normal" if is_text else "disabled")
        self.logo_entry.configure(state="normal" if not is_text else "disabled")
        self.logo_btn.configure(state="normal" if not is_text else "disabled")

    def _cfg(self) -> WatermarkConfig:
        return WatermarkConfig(
            mode=self.mode.get(),
            text=self.text.get(),
            font_size=clamp(int(self.font_size.get()), 8, 400),
            opacity=clamp(int(self.opacity.get()), 0, 100),
            position=self.position.get(),
            margin=clamp(int(self.margin.get()), 0, 400),
            scale_pct=clamp(int(self.scale_pct.get()), 5, 80),
            logo_path=self.logo_path.get() or None,
        )

    def log_line(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def pick_single_image(self):
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All files", "*.*")]
        )
        if path:
            self.single_image_path.set(path)

    def pick_input_folder(self):
        path = filedialog.askdirectory(title="Select input folder")
        if path:
            self.input_folder.set(path)

    def pick_output_folder(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_folder.set(path)

    def pick_logo(self):
        path = filedialog.askopenfilename(
            title="Select a logo image (PNG recommended)",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All files", "*.*")]
        )
        if path:
            self.logo_path.set(path)

    def _default_output_folder(self) -> str:
        base = self.output_folder.get().strip()
        if base:
            return base
        # Default: ./output
        return os.path.join(os.getcwd(), "output")

    def watermark_single(self):
        img = self.single_image_path.get().strip()
        if not img or not os.path.exists(img):
            messagebox.showerror("Missing file", "Choose a valid single image file.")
            return

        out_dir = self._default_output_folder()
        os.makedirs(out_dir, exist_ok=True)

        name = os.path.basename(img)
        out_path = os.path.join(out_dir, name)

        try:
            apply_watermark_to_image(img, out_path, self._cfg())
            self.log_line(f"✅ Saved: {out_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_line(f"❌ Error: {e}")

    def watermark_batch(self):
        in_dir = self.input_folder.get().strip()
        if not in_dir or not os.path.isdir(in_dir):
            messagebox.showerror("Missing folder", "Choose a valid input folder.")
            return

        out_dir = self._default_output_folder()
        os.makedirs(out_dir, exist_ok=True)

        images = list_images(in_dir)
        if not images:
            messagebox.showinfo("No images", "No supported images found in that folder.")
            return

        cfg = self._cfg()
        ok = 0
        fail = 0

        self.log_line(f"Batch start: {len(images)} images → {out_dir}")
        for p in images:
            out_path = os.path.join(out_dir, os.path.basename(p))
            try:
                apply_watermark_to_image(p, out_path, cfg)
                ok += 1
            except Exception as e:
                fail += 1
                self.log_line(f"❌ {os.path.basename(p)}: {e}")

        self.log_line(f"✅ Done. Success: {ok}, Failed: {fail}")

    def open_output(self):
        out_dir = self._default_output_folder()
        os.makedirs(out_dir, exist_ok=True)
        try:
            os.startfile(out_dir)  # Windows
        except Exception:
            messagebox.showinfo("Output folder", out_dir)


if __name__ == "__main__":
    app = WatermarkApp()
    app.mainloop()
