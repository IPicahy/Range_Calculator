import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import customtkinter as ctk

try:
    import pywinstyles

    HAS_WINSTYLES = True
except ImportError:
    HAS_WINSTYLES = False

PROFILES_FILE = "ballistic_profiles.json"


class BallisticGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Баллистический калькулятор MOA")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self.styled_frames = []
        self.styled_buttons = []
        self.styled_entries = []

        self.profiles = self.load_profiles()
        self.current_profile = ctk.StringVar()
        self.current_theme = ctk.StringVar(value="Тёмная")
        self.add_menu_visible = False

        if not self.profiles:
            self.profiles[".338 LM (Default)"] = {
                "points": [
                    [100, 0.8], [200, 3.2], [300, 6.8], [400, 8.0],
                    [450, 9.5], [500, 11.0], [600, 15.5], [700, 20.0],
                    [800, 24.9], [900, 30.6], [1000, 37.1], [1500, 81.6]
                ],
                "desc": "Дефолтный профиль",
                "zero_offset": 0.0
            }
            self.save_profiles(show_msg=False)

        self.build_ui()
        self.apply_theme(self.current_theme.get())
        self.update_profile_menu()

        self.root.bind("<Button-1>", self.close_custom_menu, add="+")

    def load_profiles(self):
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_profiles(self, show_msg=True):
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, indent=4, ensure_ascii=False)
        if show_msg:
            self.show_toast("💾 Сохранено")

    def interpolate_moa(self, points, target_dist):
        if len(points) < 2: return None, "Недостаточно точек"
        pts = sorted(points, key=lambda p: p[0])
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        warn = "⚠️ Экстраполяция"

        if target_dist <= x[0]:
            dx, dy = x[1] - x[0], y[1] - y[0]
            return y[0] - (dy / dx) * (x[0] - target_dist), warn if target_dist < x[0] else ""
        if target_dist >= x[-1]:
            dx, dy = x[-1] - x[-2], y[-1] - y[-2]
            return y[-1] + (dy / dx) * (target_dist - x[-1]), warn if target_dist > x[-1] else ""
        for i in range(len(x) - 1):
            if x[i] <= target_dist <= x[i + 1]:
                dx, dy = x[i + 1] - x[i], y[i + 1] - y[i]
                return y[i] + (dy / dx) * (target_dist - x[i]), ""

    def apply_theme(self, choice):
        self.root.attributes("-alpha", 1.0)
        border_w = 0
        border_c = "gray"
        frame_fg = None
        tree_bg, tree_fg, tree_select, tree_alt = "#FFFFFF", "#000000", "#1f538d", "#E2E6EA"
        header_color = "#FFFFFF"

        if HAS_WINSTYLES:
            pywinstyles.apply_style(self.root, "normal")
            self.root.configure(bg="gray86" if choice != "Тёмная" else "gray17")

        if choice == "Белая":
            ctk.set_appearance_mode("Light")
            header_color = "#EAEAEA"
        elif choice == "Тёмная":
            ctk.set_appearance_mode("Dark")
            tree_bg, tree_fg, tree_alt = "#2b2b2b", "#FFFFFF", "#333333"
            header_color = "#202020"
        elif choice == "Серая":
            ctk.set_appearance_mode("Light")
            frame_fg = "#D4D8DD"
            tree_bg, tree_fg, tree_alt = "#EAEAEA", "#000000", "#D8D8D8"
            header_color = "#D4D8DD"
        elif choice == "Белая с чёрными границами":
            ctk.set_appearance_mode("Light")
            border_w = 2
            border_c = "black"
            header_color = "#FFFFFF"
        elif choice == "Едва прозрачная":
            ctk.set_appearance_mode("Dark")
            header_color = "#0f0f0f"

            if HAS_WINSTYLES:
                self.root.configure(bg="#000000")
                pywinstyles.apply_style(self.root, "acrylic")
                self.root.attributes("-alpha", 0.95)
            else:
                self.root.attributes("-alpha", 0.90)

            tree_bg, tree_fg, tree_alt = "#151515", "#FFFFFF", "#1f1f1f"

        if HAS_WINSTYLES:
            pywinstyles.change_header_color(self.root, color=header_color)

        for frame in self.styled_frames:
            frame.configure(border_width=border_w, border_color=border_c)
            if frame_fg:
                frame.configure(fg_color=frame_fg)
            else:
                frame.configure(fg_color=["gray86", "gray17"])

        for btn in self.styled_buttons:
            btn.configure(border_width=border_w, border_color=border_c)

        for entry in self.styled_entries:
            entry.configure(border_width=border_w if border_w > 0 else 1,
                            border_color=border_c if border_w > 0 else "gray")

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview", background=tree_bg, foreground=tree_fg, fieldbackground=tree_bg, rowheight=25,
                        borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background=tree_alt, foreground=tree_fg,
                        relief="flat")

        style.map("Treeview.Heading", background=[('active', tree_alt)])
        style.map('Treeview', background=[('selected', tree_select)])

        self.tree.tag_configure('evenrow', background=tree_alt)
        self.tree.tag_configure('oddrow', background=tree_bg)
        self.refresh_tree()

    def build_ui(self):
        top_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        top_frame.pack(fill=tk.X, padx=15, pady=10)

        ctk.CTkLabel(top_frame, text="Профиль:", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        self.combo_profile = ctk.CTkComboBox(top_frame, variable=self.current_profile, state="readonly", width=200,
                                             corner_radius=8)
        self.combo_profile.pack(side=tk.LEFT, padx=5)
        self.combo_profile.configure(command=self.on_profile_select)

        btn_new = ctk.CTkButton(top_frame, text="➕ Новый", width=100, corner_radius=8, command=self.add_profile)
        btn_new.pack(side=tk.LEFT, padx=5)

        btn_del = ctk.CTkButton(top_frame, text="🗑️ Удалить", width=100, corner_radius=8, fg_color="#C0392B",
                                hover_color="#922B21", command=self.delete_profile)
        btn_del.pack(side=tk.LEFT, padx=5)

        self.combo_theme = ctk.CTkComboBox(top_frame, variable=self.current_theme,
                                           values=["Тёмная", "Белая", "Серая", "Белая с чёрными границами",
                                                   "Едва прозрачная"], state="readonly", width=180, corner_radius=8,
                                           command=self.apply_theme)
        self.combo_theme.pack(side=tk.RIGHT, padx=5)
        ctk.CTkLabel(top_frame, text="🎨 Тема:").pack(side=tk.RIGHT)

        self.styled_buttons.extend([btn_new, btn_del])

        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        left_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.styled_frames.append(left_frame)

        tree_container = ctk.CTkFrame(left_frame, fg_color="transparent", corner_radius=0)
        tree_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("dist", "moa")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("dist", text="Дистанция (м)")
        self.tree.heading("moa", text="Клик прицела (MOA)")
        self.tree.column("dist", anchor=tk.CENTER, width=120)
        self.tree.column("moa", anchor=tk.CENTER, width=120)

        self.tree.bind('<Button-1>', self.prevent_header_click)

        scrollbar = ctk.CTkScrollbar(tree_container, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))

        ctk.CTkLabel(left_frame, text="💡 ПКМ по точке для (Изменить / Удалить)", text_color="gray").pack(side=tk.BOTTOM,
                                                                                                         pady=(0, 10))
        self.tree.bind("<Button-3>", self.show_custom_context_menu)
        if self.root.tk.call('tk', 'windowingsystem') == 'aqua':
            self.tree.bind("<Button-2>", self.show_custom_context_menu)
            self.tree.bind("<Control-1>", self.show_custom_context_menu)

        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 0))

        zero_group = ctk.CTkFrame(right_frame, corner_radius=10)
        zero_group.pack(fill=tk.X, pady=(0, 15))
        self.styled_frames.append(zero_group)

        ctk.CTkLabel(zero_group, text="Калибровка прицела", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))

        sign_frame = ctk.CTkFrame(zero_group, fg_color="transparent")
        sign_frame.pack(fill=tk.X, padx=10)
        self.zero_sign = ctk.StringVar(value="-")
        ctk.CTkRadioButton(sign_frame, text="Запас ( - )", variable=self.zero_sign, value="-",
                           command=self.apply_zero).pack(side=tk.LEFT, padx=5)
        ctk.CTkRadioButton(sign_frame, text="Вверх ( + )", variable=self.zero_sign, value="+",
                           command=self.apply_zero).pack(side=tk.RIGHT, padx=5)

        inp_frame1 = ctk.CTkFrame(zero_group, fg_color="transparent")
        inp_frame1.pack(fill=tk.X, padx=10, pady=(10, 15))
        ctk.CTkLabel(inp_frame1, text="MOA:").pack(side=tk.LEFT)
        self.ent_zero = ctk.CTkEntry(inp_frame1, width=70, corner_radius=6)
        self.ent_zero.pack(side=tk.LEFT, padx=5)
        btn_apply = ctk.CTkButton(inp_frame1, text="✔", width=40, corner_radius=6, command=self.apply_zero)
        btn_apply.pack(side=tk.RIGHT)

        self.styled_entries.append(self.ent_zero)
        self.styled_buttons.append(btn_apply)

        calc_group = ctk.CTkFrame(right_frame, corner_radius=10)
        calc_group.pack(fill=tk.X, pady=(0, 15))
        self.styled_frames.append(calc_group)

        ctk.CTkLabel(calc_group, text="Быстрый расчет", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        self.ent_calc_dist = ctk.CTkEntry(calc_group, placeholder_text="Дистанция (м)", corner_radius=6)
        self.ent_calc_dist.pack(fill=tk.X, padx=10, pady=5)

        btn_calc = ctk.CTkButton(calc_group, text="⚡ Рассчитать", corner_radius=6, command=self.calculate_moa)
        btn_calc.pack(fill=tk.X, padx=10, pady=5)

        self.lbl_result = ctk.CTkLabel(calc_group, text="Результат: ---", font=("Segoe UI", 16, "bold"),
                                       text_color="#2ECC71")
        self.lbl_result.pack(pady=(5, 10))

        self.styled_entries.append(self.ent_calc_dist)
        self.styled_buttons.append(btn_calc)

        self.btn_toggle_menu = ctk.CTkButton(right_frame, text="▶ Добавить точку", fg_color="transparent",
                                             border_width=1, text_color=("black", "white"),
                                             command=self.toggle_add_menu)
        self.btn_toggle_menu.pack(fill=tk.X, pady=(0, 5))

        self.add_group = ctk.CTkFrame(right_frame, corner_radius=10)
        self.styled_frames.append(self.add_group)

        ctk.CTkLabel(self.add_group, text="Базовое значение", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        self.ent_dist = ctk.CTkEntry(self.add_group, placeholder_text="Дистанция (м)", corner_radius=6)
        self.ent_dist.pack(fill=tk.X, padx=10, pady=5)

        self.ent_moa = ctk.CTkEntry(self.add_group, placeholder_text="MOA (Без смещения)", corner_radius=6)
        self.ent_moa.pack(fill=tk.X, padx=10, pady=5)

        btn_save_pt = ctk.CTkButton(self.add_group, text="💾 Сохранить", corner_radius=6, command=self.save_point)
        btn_save_pt.pack(fill=tk.X, padx=10, pady=(5, 10))

        self.styled_entries.extend([self.ent_dist, self.ent_moa])
        self.styled_buttons.extend([self.btn_toggle_menu, btn_save_pt])

        btn_gen = ctk.CTkButton(right_frame, text="📊 Полная таблица", corner_radius=6, command=self.generate_table)
        btn_gen.pack(fill=tk.X, side=tk.BOTTOM)
        self.styled_buttons.append(btn_gen)

    def show_toast(self, message):
        if hasattr(self, 'toast') and self.toast.winfo_exists():
            self.toast.destroy()

        self.toast = tk.Toplevel(self.root)
        self.toast.overrideredirect(True)
        self.toast.attributes('-alpha', 0.0)

        bg_color = "#2C3E50" if ctk.get_appearance_mode() == "Light" else "#1ABC9C"
        self.toast.configure(bg=bg_color)

        lbl = tk.Label(self.toast, text=message, bg=bg_color, fg="white", font=("Segoe UI", 11, "bold"), padx=20,
                       pady=10)
        lbl.pack()

        self.toast.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() - self.toast.winfo_width() - 30
        y = self.root.winfo_rooty() + self.root.winfo_height() - self.toast.winfo_height() - 30
        self.toast.geometry(f"+{x}+{y}")

        self.fade_in(self.toast, 0.0)

    def fade_in(self, window, alpha):
        if not window.winfo_exists(): return
        alpha += 0.1
        window.attributes('-alpha', alpha)
        if alpha < 0.9:
            self.root.after(30, lambda: self.fade_in(window, alpha))
        else:
            self.root.after(1500, lambda: self.fade_out(window, 0.9))

    def fade_out(self, window, alpha):
        if not window.winfo_exists(): return
        alpha -= 0.05
        window.attributes('-alpha', alpha)
        if alpha > 0:
            self.root.after(30, lambda: self.fade_out(window, alpha))
        else:
            window.destroy()

    def prevent_header_click(self, event):
        if self.tree.identify_region(event.x, event.y) == "heading":
            return "break"

    def close_custom_menu(self, event=None):
        if hasattr(self, 'custom_menu') and self.custom_menu.winfo_exists():
            if event:
                try:
                    x, y = self.root.winfo_pointerxy()
                    mx = self.custom_menu.winfo_rootx()
                    my = self.custom_menu.winfo_rooty()
                    mw = self.custom_menu.winfo_width()
                    mh = self.custom_menu.winfo_height()
                    if mx <= x <= mx + mw and my <= y <= my + mh:
                        return
                except Exception:
                    pass
            self.custom_menu.destroy()

    def show_custom_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid: return
        self.tree.selection_set(iid)

        self.close_custom_menu()

        self.custom_menu = tk.Toplevel(self.root)
        self.custom_menu.wm_overrideredirect(True)

        theme = self.current_theme.get()
        if theme in ["Тёмная", "Едва прозрачная"]:
            bg_color, hover_color, text_color, sep_color = "#2b2b2b", "#1f538d", "#FFFFFF", "#111111"
        elif theme == "Белая с чёрными границами":
            bg_color, hover_color, text_color, sep_color = "#FFFFFF", "#EAEAEA", "#000000", "#000000"
        else:
            bg_color, hover_color, text_color, sep_color = "#FFFFFF", "#EAEAEA", "#000000", "#CCCCCC"

        border_frame = tk.Frame(self.custom_menu, bg=sep_color, bd=1)
        border_frame.pack(fill=tk.BOTH, expand=True)

        def cmd_edit():
            self.custom_menu.destroy()
            self.edit_point_from_menu(iid)

        def cmd_delete():
            self.custom_menu.destroy()
            self.delete_point(iid)

        btn_edit = ctk.CTkButton(border_frame, text="Изменить", width=156, height=26,
                                 corner_radius=0, fg_color=bg_color, text_color=text_color,
                                 hover_color=hover_color, font=("Segoe UI", 12), anchor="center", command=cmd_edit)
        btn_edit.pack(fill=tk.X, pady=(0, 1))

        btn_delete = ctk.CTkButton(border_frame, text="Удалить", width=156, height=26,
                                   corner_radius=0, fg_color=bg_color, text_color=text_color,
                                   hover_color=hover_color, font=("Segoe UI", 12), anchor="center", command=cmd_delete)
        btn_delete.pack(fill=tk.X)

        self.custom_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.custom_menu.focus_set()

    def edit_point_from_menu(self, iid=None):
        if not iid:
            selected = self.tree.selection()
            if not selected: return
            iid = selected[0]

        prof = self.current_profile.get()
        dist = float(self.tree.item(iid)["values"][0])
        raw_moa = next((p[1] for p in self.profiles[prof]["points"] if p[0] == dist), 0.0)

        if not self.add_menu_visible: self.toggle_add_menu()
        self.ent_dist.delete(0, tk.END)
        self.ent_dist.insert(0, str(dist))
        self.ent_moa.delete(0, tk.END)
        self.ent_moa.insert(0, str(raw_moa))
        self.ent_moa.focus()

    def delete_point(self, iid=None):
        prof = self.current_profile.get()
        if not iid:
            selected = self.tree.selection()
            if not selected: return
            iid = selected[0]

        dist_to_delete = float(self.tree.item(iid)["values"][0])
        pts = self.profiles[prof]["points"]
        self.profiles[prof]["points"] = [p for p in pts if p[0] != dist_to_delete]

        self.save_profiles()
        self.refresh_tree()

    def apply_zero(self):
        prof = self.current_profile.get()
        if not prof: return
        try:
            val_str = self.ent_zero.get().strip()
            val = float(val_str.replace(',', '.')) if val_str else 0.0
            val = abs(val)
            if self.zero_sign.get() == "-": val = -val

            self.profiles[prof]["zero_offset"] = val
            self.save_profiles()
            self.refresh_tree()
            if self.ent_calc_dist.get(): self.calculate_moa()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число!")

    def toggle_add_menu(self):
        if self.add_menu_visible:
            self.add_group.pack_forget()
            self.btn_toggle_menu.configure(text="▶ Добавить точку")
            self.add_menu_visible = False
        else:
            self.add_group.pack(fill=tk.X, pady=(0, 10))
            self.btn_toggle_menu.configure(text="▼ Скрыть")
            self.add_menu_visible = True

    def update_profile_menu(self):
        names = list(self.profiles.keys())
        self.combo_profile.configure(values=names)
        if names:
            if not self.current_profile.get() in names:
                self.combo_profile.set(names[0])
            self.on_profile_select()
        else:
            self.current_profile.set("")
            self.refresh_tree()

    def on_profile_select(self, choice=None):
        prof = self.current_profile.get()
        if prof and prof in self.profiles:
            offset = self.profiles[prof].get("zero_offset", 0.0)
            self.zero_sign.set("-" if offset <= 0 else "+")
            self.ent_zero.delete(0, tk.END)
            self.ent_zero.insert(0, str(abs(offset)))

        self.refresh_tree()
        self.lbl_result.configure(text="Результат: ---", text_color="#2ECC71")

    def refresh_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        prof = self.current_profile.get()
        if prof and prof in self.profiles:
            pts = sorted(self.profiles[prof]["points"], key=lambda x: x[0])
            offset = self.profiles[prof].get("zero_offset", 0.0)
            for i, p in enumerate(pts):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert("", tk.END, values=(f"{p[0]:.1f}", f"{(p[1] + offset):.2f}"), tags=(tag,))

    def add_profile(self):
        name = simpledialog.askstring("Новый профиль", "Название:", parent=self.root)
        if name:
            if name in self.profiles:
                messagebox.showerror("Ошибка", "Профиль уже существует!")
                return
            self.profiles[name] = {"points": [], "desc": "", "zero_offset": 0.0}
            self.save_profiles()
            self.current_profile.set(name)
            self.update_profile_menu()

    def delete_profile(self):
        prof = self.current_profile.get()
        if prof and messagebox.askyesno("Удаление", f"Удалить '{prof}'?"):
            del self.profiles[prof]
            self.save_profiles()
            self.update_profile_menu()

    def save_point(self):
        prof = self.current_profile.get()
        if not prof: return
        try:
            dist = float(self.ent_dist.get().replace(',', '.'))
            moa = float(self.ent_moa.get().replace(',', '.'))
        except ValueError:
            messagebox.showerror("Ошибка", "Введите числа!")
            return

        pts = self.profiles[prof]["points"]
        for i, p in enumerate(pts):
            if p[0] == dist:
                pts[i][1] = moa
                break
        else:
            pts.append([dist, moa])

        self.profiles[prof]["points"] = pts
        self.save_profiles()
        self.refresh_tree()
        self.ent_dist.delete(0, tk.END)
        self.ent_moa.delete(0, tk.END)
        self.ent_dist.focus()

    def calculate_moa(self):
        prof = self.current_profile.get()
        if not prof: return
        dist_str = self.ent_calc_dist.get().replace(',', '.')
        if not dist_str: return

        try:
            dist = float(dist_str)
        except ValueError:
            self.lbl_result.configure(text="Ошибка ввода!", text_color="#E74C3C")
            return

        pts = self.profiles[prof]["points"]
        offset = self.profiles[prof].get("zero_offset", 0.0)
        moa, warn = self.interpolate_moa(pts, dist)

        if moa is not None:
            self.lbl_result.configure(text=f"Клик: {(moa + offset):.2f} MOA", text_color="#2ECC71")
            if warn: self.show_toast("⚠️ Экстраполяция")
        else:
            self.lbl_result.configure(text="Мало данных!", text_color="#E74C3C")

    def generate_table(self):
        prof = self.current_profile.get()
        if not prof: return
        pts = self.profiles[prof]["points"]
        offset = self.profiles[prof].get("zero_offset", 0.0)
        if len(pts) < 2: return messagebox.showwarning("Ошибка", "Нужно минимум 2 точки.")

        win = ctk.CTkToplevel(self.root)
        win.title(f"Таблица: {prof}")
        win.geometry("380x600")

        if HAS_WINSTYLES:
            color = "#111111" if self.current_theme.get() == "Едва прозрачная" else None
            if color: pywinstyles.change_header_color(win, color=color)

        frame = ctk.CTkFrame(win, corner_radius=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        columns = ("dist", "moa")
        ftree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        ftree.heading("dist", text="Дистанция (м)")
        ftree.heading("moa", text="Клик прицела (MOA)")
        ftree.column("dist", anchor=tk.CENTER, width=130)
        ftree.column("moa", anchor=tk.CENTER, width=130)

        ftree.bind('<Button-1>', self.prevent_header_click)

        sb = ctk.CTkScrollbar(frame, orientation="vertical", command=ftree.yview)
        ftree.configure(yscrollcommand=sb.set)

        ftree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))

        for i, d in enumerate(range(100, 1500 + 50, 50)):
            moa, _ = self.interpolate_moa(pts, d)
            if moa is not None:
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                mark = " *" if any(abs(p[0] - d) < 1 for p in pts) else ""
                ftree.insert("", tk.END, values=(f"{d}", f"{(moa + offset):.2f}{mark}"), tags=(tag,))

        def copy_treeview():
            lines = []
            lines.append(f"Профиль: {prof}")
            lines.append(f"Смещение нуля: {offset} MOA")
            lines.append("-" * 35)
            lines.append("Дистанция (м) | Клик (MOA)")
            lines.append("-" * 35)

            for child in ftree.get_children():
                val_dist, val_moa = ftree.item(child)["values"]
                lines.append(f"{str(val_dist):>13} | {str(val_moa):>10}")

            lines.append("-" * 35)
            lines.append("* - подтвержденная точка")

            full_text = "\n".join(lines)
            win.clipboard_clear()
            win.clipboard_append(full_text)
            self.show_toast("📋 Таблица скопирована в буфер")

        ctk.CTkButton(win, text="📋 Скопировать всю таблицу", corner_radius=8, height=35, command=copy_treeview).pack(
            fill=tk.X, padx=15, pady=(0, 15))


if __name__ == "__main__":
    root = ctk.CTk()
    app = BallisticGUI(root)
    root.mainloop()