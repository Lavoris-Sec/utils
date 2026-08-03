from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
import pyautogui
from pynput import keyboard
from PIL import Image
import tkinter as tk


APP_DIR = Path(__file__).resolve().parent
PROFILES_DIR = APP_DIR / "profiles"
DEFAULT_THRESHOLD = 0.86
QUICK_PROFILE = "_quick_runtime"
DEFAULT_SCROLL_AFTER_MISSES = 1
DEFAULT_SCROLL_AMOUNT = -350


@dataclass
class Rect:
    left: int
    top: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)


@dataclass
class Profile:
    name: str
    search_region: Rect
    click_templates: list[str]
    skip_templates: list[str]
    threshold: float = DEFAULT_THRESHOLD
    scan_delay: float = 0.35
    max_clicks: int = 50
    auto_scroll: bool = True
    scroll_after_misses: int = DEFAULT_SCROLL_AFTER_MISSES
    scroll_amount: int = DEFAULT_SCROLL_AMOUNT


class Hud:
    def __init__(self, title: str) -> None:
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("360x170+16+80")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#111317")
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.stopped = False

        self.title_label = tk.Label(
            self.root,
            text=title,
            bg="#111317",
            fg="#e8eaed",
            font=("Consolas", 13, "bold"),
            anchor="w",
        )
        self.title_label.pack(fill="x", padx=14, pady=(12, 4))

        self.status = tk.Label(
            self.root,
            text="Starting...",
            bg="#111317",
            fg="#b6bdc7",
            font=("Consolas", 10),
            justify="left",
            anchor="w",
        )
        self.status.pack(fill="both", expand=True, padx=14)

        self.stop_button = tk.Button(
            self.root,
            text="Stop",
            command=self.stop,
            bg="#2b313a",
            fg="#ffffff",
            activebackground="#3a4250",
            activeforeground="#ffffff",
            relief="flat",
        )
        self.stop_button.pack(fill="x", padx=14, pady=(4, 12))

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)
        self.root.update_idletasks()
        self.root.update()

    def stop(self) -> None:
        self.stopped = True

    def close(self) -> None:
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def select_rect(prompt: str) -> Rect:
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.28)
    root.configure(bg="black")
    root.title(prompt)

    canvas = tk.Canvas(root, cursor="cross", bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    label = tk.Label(
        root,
        text=prompt,
        bg="#111317",
        fg="#ffffff",
        font=("Consolas", 16, "bold"),
        padx=16,
        pady=10,
    )
    label.place(x=20, y=20)

    state: dict[str, int | None] = {"x0": None, "y0": None, "rect": None}
    result: dict[str, Rect | None] = {"rect": None}

    def on_down(event: tk.Event) -> None:
        state["x0"], state["y0"] = event.x, event.y
        if state["rect"]:
            canvas.delete(state["rect"])
        state["rect"] = canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="#37a2ff",
            width=3,
        )

    def on_move(event: tk.Event) -> None:
        if state["x0"] is None or state["y0"] is None or state["rect"] is None:
            return
        canvas.coords(state["rect"], state["x0"], state["y0"], event.x, event.y)

    def on_up(event: tk.Event) -> None:
        if state["x0"] is None or state["y0"] is None:
            return
        x0, y0 = int(state["x0"]), int(state["y0"])
        x1, y1 = event.x, event.y
        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        if right - left >= 8 and bottom - top >= 8:
            result["rect"] = Rect(left, top, right - left, bottom - top)
        root.quit()

    def cancel(_: tk.Event) -> None:
        root.quit()

    canvas.bind("<ButtonPress-1>", on_down)
    canvas.bind("<B1-Motion>", on_move)
    canvas.bind("<ButtonRelease-1>", on_up)
    root.bind("<Escape>", cancel)
    root.mainloop()
    root.destroy()

    if result["rect"] is None:
        raise SystemExit("Selection cancelled.")
    return result["rect"]


def screenshot(rect: Rect | None = None) -> Image.Image:
    if rect is None:
        return pyautogui.screenshot()
    return pyautogui.screenshot(region=(rect.left, rect.top, rect.width, rect.height))


def save_crop(source: Image.Image, rect: Rect, path: Path) -> None:
    crop = source.crop((rect.left, rect.top, rect.left + rect.width, rect.top + rect.height))
    crop.save(path)


def image_to_cv(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def locate_template(region_image: Image.Image, template_path: Path, threshold: float) -> tuple[float, Rect | None]:
    haystack = image_to_cv(region_image)
    needle = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if needle is None:
        return 0.0, None
    if needle.shape[0] > haystack.shape[0] or needle.shape[1] > haystack.shape[1]:
        return 0.0, None

    result = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < threshold:
        return float(max_val), None
    h, w = needle.shape[:2]
    return float(max_val), Rect(max_loc[0], max_loc[1], w, h)


def load_profile(name: str) -> Profile:
    path = PROFILES_DIR / name / "profile.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["search_region"] = Rect(**data["search_region"])
    return Profile(**data)


def save_profile(profile: Profile) -> None:
    profile_dir = PROFILES_DIR / profile.name
    profile_dir.mkdir(parents=True, exist_ok=True)
    data = asdict(profile)
    (profile_dir / "profile.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ask_yes_no(question: str) -> bool:
    answer = input(f"{question} [y/N]: ").strip().lower()
    return answer in {"y", "yes", "д", "да"}


def ask_int(question: str, default: int) -> int:
    answer = input(f"{question} [{default}]: ").strip()
    if not answer:
        return default
    try:
        return int(answer)
    except ValueError:
        print(f"Bad number, using {default}.")
        return default


def resolve_scroll_settings(args: argparse.Namespace) -> tuple[bool, int, int]:
    if args.no_scroll:
        return False, args.scroll_after_misses, args.scroll_amount
    if not args.ask_scroll:
        return True, args.scroll_after_misses, args.scroll_amount

    print("4) Scroll settings.")
    if not ask_yes_no("Enable auto-scroll?"):
        return False, args.scroll_after_misses, args.scroll_amount

    after_misses = ask_int(
        "Scroll after this many missed scans",
        args.scroll_after_misses,
    )
    amount = ask_int(
        "Scroll amount. More negative = faster down scroll, for example -10",
        args.scroll_amount,
    )
    return True, max(1, after_misses), amount


def capture_profile(args: argparse.Namespace, name: str) -> tuple[Profile, Path]:
    pyautogui.FAILSAFE = True
    profile_dir = PROFILES_DIR / name
    profile_dir.mkdir(parents=True, exist_ok=True)

    print("1) Drag the dialog/search area.")
    search_region = select_rect("Drag the area where the dialog appears")
    full = screenshot()

    click_templates: list[str] = []
    skip_templates: list[str] = []

    print("2) Capture click targets. Select the exact toggle/button, not the whole card.")
    while True:
        rect = select_rect("Drag a button/toggle to click")
        filename = f"click_{len(click_templates) + 1}.png"
        save_crop(full, rect, profile_dir / filename)
        click_templates.append(filename)
        if not ask_yes_no("Add another click target?"):
            break

    print("3) Optional skip markers. If a marker is visible, the bot will not click.")
    while ask_yes_no("Add a skip-if-visible template?"):
        rect = select_rect("Drag the thing that means 'skip'")
        filename = f"skip_{len(skip_templates) + 1}.png"
        save_crop(full, rect, profile_dir / filename)
        skip_templates.append(filename)

    auto_scroll, scroll_after_misses, scroll_amount = resolve_scroll_settings(args)

    profile = Profile(
        name=name,
        search_region=search_region,
        click_templates=click_templates,
        skip_templates=skip_templates,
        threshold=args.threshold,
        scan_delay=args.scan_delay,
        max_clicks=args.max_clicks,
        auto_scroll=auto_scroll,
        scroll_after_misses=scroll_after_misses,
        scroll_amount=scroll_amount,
    )
    return profile, profile_dir


def train(args: argparse.Namespace) -> None:
    profile, profile_dir = capture_profile(args, args.name)
    save_profile(profile)
    print(f"Saved profile: {profile_dir / 'profile.json'}")


def start_hotkey_listener(hud: Hud) -> keyboard.Listener:
    def on_press(key: keyboard.Key | keyboard.KeyCode) -> None:
        char = getattr(key, "char", None)
        if char and char.lower() in {"q", "й"}:
            hud.stop()

    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
    return listener


def scroll_region(region: Rect, amount: int) -> None:
    x = region.left + max(12, region.width - 20)
    y = region.top + region.height // 2
    pyautogui.moveTo(x, y, duration=0.05)
    pyautogui.scroll(amount)


def run_engine(profile: Profile, profile_dir: Path, title: str, start_delay: float) -> None:
    pyautogui.FAILSAFE = True
    hud = Hud(title)
    listener = start_hotkey_listener(hud)

    clicked = 0
    scans = 0
    misses = 0
    scrolls = 0
    last_score = 0.0
    time.sleep(start_delay)

    try:
        while not hud.stopped and clicked < profile.max_clicks:
            scans += 1
            region_image = screenshot(profile.search_region)

            skip_hit = False
            for filename in profile.skip_templates:
                score, rect = locate_template(region_image, profile_dir / filename, profile.threshold)
                last_score = max(last_score, score)
                if rect is not None:
                    skip_hit = True
                    break

            if skip_hit:
                hud.set_status(
                    f"Skip marker visible\n"
                    f"scans: {scans}\n"
                    f"clicks: {clicked}/{profile.max_clicks}\n"
                    f"scrolls: {scrolls}\n"
                    f"best score: {last_score:.3f}\n"
                    f"stop: q / й"
                )
                time.sleep(profile.scan_delay)
                continue

            did_click = False
            for filename in profile.click_templates:
                score, rect = locate_template(region_image, profile_dir / filename, profile.threshold)
                last_score = max(last_score, score)
                if rect is None:
                    continue

                x = profile.search_region.left + rect.center[0]
                y = profile.search_region.top + rect.center[1]
                pyautogui.click(x, y)
                clicked += 1
                did_click = True
                misses = 0
                time.sleep(0.18)
                break

            if did_click:
                misses = 0
            else:
                misses += 1
                if profile.auto_scroll and misses >= profile.scroll_after_misses:
                    scroll_region(profile.search_region, profile.scroll_amount)
                    scrolls += 1
                    misses = 0
                    time.sleep(0.15)

            hud.set_status(
                f"{'Clicked' if did_click else 'Searching'}\n"
                f"scans: {scans}\n"
                f"clicks: {clicked}/{profile.max_clicks}\n"
                f"scrolls: {scrolls}\n"
                f"best score: {last_score:.3f}\n"
                f"stop: q / й"
            )
            time.sleep(profile.scan_delay)
    except pyautogui.FailSafeException:
        hud.set_status("Failsafe triggered")
        time.sleep(1.0)
    finally:
        listener.stop()
        hud.close()


def run_bot(args: argparse.Namespace) -> None:
    profile = load_profile(args.name)
    if args.no_scroll:
        profile.auto_scroll = False
    if args.scroll_after_misses is not None:
        profile.scroll_after_misses = args.scroll_after_misses
    if args.scroll_amount is not None:
        profile.scroll_amount = args.scroll_amount
    run_engine(profile, PROFILES_DIR / profile.name, f"Consent Bot: {profile.name}", args.start_delay)


def quick(args: argparse.Namespace) -> None:
    profile_name = args.save_profile or QUICK_PROFILE
    profile, profile_dir = capture_profile(args, profile_name)
    save_profile(profile)
    run_engine(profile, profile_dir, "Consent Bot: quick", args.start_delay)


def list_profiles(_: argparse.Namespace) -> None:
    if not PROFILES_DIR.exists():
        print("No profiles yet.")
        return
    for profile in sorted(PROFILES_DIR.iterdir()):
        if (profile / "profile.json").exists():
            print(profile.name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trainable screen template clicker.")
    subparsers = parser.add_subparsers(required=True)

    train_parser = subparsers.add_parser("train", help="Create/update a profile.")
    train_parser.add_argument("name")
    train_parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    train_parser.add_argument("--scan-delay", type=float, default=0.35)
    train_parser.add_argument("--max-clicks", type=int, default=50)
    train_parser.add_argument("--no-scroll", action="store_true")
    train_parser.add_argument("--ask-scroll", action="store_true")
    train_parser.add_argument("--scroll-after-misses", type=int, default=DEFAULT_SCROLL_AFTER_MISSES)
    train_parser.add_argument("--scroll-amount", type=int, default=DEFAULT_SCROLL_AMOUNT)
    train_parser.set_defaults(func=train)

    run_parser = subparsers.add_parser("run", help="Run a profile.")
    run_parser.add_argument("name")
    run_parser.add_argument("--start-delay", type=float, default=2.0)
    run_parser.add_argument("--no-scroll", action="store_true")
    run_parser.add_argument("--scroll-after-misses", type=int)
    run_parser.add_argument("--scroll-amount", type=int)
    run_parser.set_defaults(func=run_bot)

    quick_parser = subparsers.add_parser("quick", help="Train and run immediately.")
    quick_parser.add_argument("--save-profile")
    quick_parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    quick_parser.add_argument("--scan-delay", type=float, default=0.35)
    quick_parser.add_argument("--max-clicks", type=int, default=50)
    quick_parser.add_argument("--start-delay", type=float, default=2.0)
    quick_parser.add_argument("--no-scroll", action="store_true")
    quick_parser.add_argument("--ask-scroll", action="store_true", default=True)
    quick_parser.add_argument("--scroll-after-misses", type=int, default=DEFAULT_SCROLL_AFTER_MISSES)
    quick_parser.add_argument("--scroll-amount", type=int, default=DEFAULT_SCROLL_AMOUNT)
    quick_parser.set_defaults(func=quick)

    list_parser = subparsers.add_parser("list", help="List saved profiles.")
    list_parser.set_defaults(func=list_profiles)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
