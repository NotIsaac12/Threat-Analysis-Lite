import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# ----------------------- ФАЙЛОВЫЕ ОПЕРАЦИИ -----------------------
THREATS_FILE = "threats.json"
OFFENDERS_FILE = "offenders.json"
CONFIG_FILE = "config.json"

def load_data(file, default=[]):
    if not os.path.exists(file):
        return default
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_data(data, file):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_config():
    return load_data(CONFIG_FILE, {"risk_scale": "5x5"})

def save_config(config):
    save_data(config, CONFIG_FILE)

def get_risk_level_ru(prob, damage, scale):
    risk = prob * damage
    if scale == "5x5":
        if risk >= 13: return "Высокий"
        elif risk >= 5: return "Средний"
        else: return "Низкий"
    else:
        if risk >= 6: return "Высокий"
        elif risk >= 3: return "Средний"
        else: return "Низкий"

# ----------------------- ОСНОВНОЕ ПРИЛОЖЕНИЕ -----------------------
class ThreatAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализ Угроз - Информационная Безопасность")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        self.config = load_config()
        # Создаём словари для сортировки заранее
        self.threat_sort = {}
        self.offender_sort = {}
        self.root.configure(bg='#2b2b2b')
        self.setup_styles()
        self.create_toolbar()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Вкладка "Угрозы"
        self.threats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.threats_frame, text="🚨 Угрозы")
        self.setup_threats_tab()

        # Вкладка "Нарушители"
        self.offenders_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.offenders_frame, text="👤 Нарушители")
        self.setup_offenders_tab()

        # Вкладка "Риски и Отчеты"
        self.risks_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.risks_frame, text="📊 Риски и Отчеты")
        self.setup_risks_tab()

        # Вкладка "Помощь"
        self.help_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.help_frame, text="❓ Помощь")
        self.setup_help_tab()

        # Вкладка "Настройки"
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="⚙️ Настройки")
        self.setup_settings_tab()

        self.refresh_threats_table()
        self.refresh_offenders_table()

        self.current_model_path = None
        self.create_menu()
        self.new_model()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background='#2b2b2b', foreground='#e0e0e0', fieldbackground='#3c3c3c')
        style.configure("TNotebook", background='#2b2b2b', borderwidth=0)
        style.configure("TNotebook.Tab", background='#3c3c3c', foreground='#e0e0e0', padding=[12, 4])
        style.map("TNotebook.Tab", background=[("selected", '#4e4e4e')])
        style.configure("TFrame", background='#2b2b2b')
        style.configure("TLabelframe", background='#2b2b2b', foreground='#e0e0e0')
        style.configure("TLabelframe.Label", background='#2b2b2b', foreground='#e0e0e0')
        style.configure("TLabel", background='#2b2b2b', foreground='#e0e0e0')
        style.configure("TButton", background='#4e4e4e', foreground='#e0e0e0', borderwidth=1)
        style.map("TButton", background=[('active', '#5e5e5e')])
        style.configure("Treeview", background='#3c3c3c', fieldbackground='#3c3c3c', foreground='#e0e0e0', rowheight=25)
        style.configure("Treeview.Heading", background='#4e4e4e', foreground='#e0e0e0', relief='flat')
        style.map("Treeview.Heading", background=[('active', '#5e5e5e')])
        style.configure("TCombobox", fieldbackground='#4e4e4e', background='#4e4e4e', foreground='#e0e0e0', arrowcolor='#e0e0e0')

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg='#3c3c3c', height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        tk.Button(toolbar, text="📥 Импорт из БДУ", command=self.import_from_bdu,
                  bg='#5a5a5a', fg='white', padx=10, pady=5, font=('Segoe UI', 9, 'bold'),
                  relief=tk.RAISED, bd=1, cursor='hand2').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="➕ Добавить угрозу", command=self.add_threat,
                  bg='#2e7d32', fg='white', padx=10, pady=5, font=('Segoe UI', 9, 'bold'),
                  relief=tk.RAISED, bd=1, cursor='hand2').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="➕ Добавить нарушителя", command=self.add_offender,
                  bg='#1565c0', fg='white', padx=10, pady=5, font=('Segoe UI', 9, 'bold'),
                  relief=tk.RAISED, bd=1, cursor='hand2').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Label(toolbar, text="🔍 Поиск угроз:", bg='#3c3c3c', fg='#e0e0e0', font=('Segoe UI', 9)).pack(side=tk.RIGHT, padx=(0, 5))
        self.search_entry = tk.Entry(toolbar, width=30, bg='#4e4e4e', fg='#e0e0e0', insertbackground='white')
        self.search_entry.pack(side=tk.RIGHT, padx=(0, 10), pady=5)
        self.search_entry.bind('<KeyRelease>', self.search_threats)

    def search_threats(self, event=None):
        term = self.search_entry.get().strip().lower()
        if not term:
            self.refresh_threats_table()
            return
        threats = load_data(THREATS_FILE)
        filtered = [t for t in threats if term in t["id"].lower() or term in t["name"].lower()]
        self._fill_threats_table(filtered)

    def _fill_threats_table(self, threats):
        for row in self.tree_threats.get_children():
            self.tree_threats.delete(row)
        for i, t in enumerate(threats):
            risk = t["probability"] * t["damage"]
            level = get_risk_level_ru(t["probability"], t["damage"], self.config["risk_scale"])
            bg = "#3c3c3c" if i % 2 == 0 else "#2c2c2c"
            self.tree_threats.insert("", tk.END, values=(
                t["id"], t["name"], t.get("category", ""), t.get("source", ""),
                t["probability"], t["damage"], risk, level
            ), tags=(bg,))
        self.tree_threats.tag_configure("#3c3c3c", background="#3c3c3c")
        self.tree_threats.tag_configure("#2c2c2c", background="#2c2c2c")

    def setup_threats_tab(self):
        control_panel = tk.Frame(self.threats_frame, bg='#2b2b2b')
        control_panel.pack(fill=tk.X, padx=5, pady=5)
        for text, cmd in [("✏️ Редактировать", self.edit_threat),
                          ("❌ Удалить", self.delete_threat),
                          ("🔄 Обновить", self.refresh_threats_table)]:
            tk.Button(control_panel, text=text, command=cmd,
                      bg='#4e4e4e', fg='white', padx=5, pady=2, cursor='hand2').pack(side=tk.LEFT, padx=2)

        columns = ("id", "name", "category", "source", "prob", "damage", "risk", "level")
        self.tree_threats = ttk.Treeview(self.threats_frame, columns=columns, show="headings", selectmode="browse")
        headers = {"id": "ID", "name": "Наименование угрозы", "category": "Категория",
                   "source": "Источник", "prob": "Вер.", "damage": "Ущ.", "risk": "Риск", "level": "Уровень"}
        for col in columns:
            self.tree_threats.heading(col, text=headers[col], command=lambda c=col: self.sort_threats_by_column(c))
            self.tree_threats.column(col, width=100)
        self.tree_threats.column("name", width=250)

        vsb = ttk.Scrollbar(self.threats_frame, orient="vertical", command=self.tree_threats.yview)
        self.tree_threats.configure(yscrollcommand=vsb.set)
        self.tree_threats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def sort_threats_by_column(self, col):
        reverse = self.threat_sort.get(col, False)
        items = [(self.tree_threats.set(child, col), child) for child in self.tree_threats.get_children('')]
        try:
            items.sort(key=lambda x: float(x[0]) if x[0].replace('.', '', 1).isdigit() else x[0], reverse=reverse)
        except:
            items.sort(key=lambda x: str(x[0]).lower(), reverse=reverse)
        for index, (val, child) in enumerate(items):
            self.tree_threats.move(child, '', index)
        self.threat_sort[col] = not reverse

    def refresh_threats_table(self):
        threats = load_data(THREATS_FILE)
        self._fill_threats_table(threats)
        self.threat_sort.clear()

    def add_threat(self):
        ThreatDialog(self.root, self, mode="add")

    def edit_threat(self):
        selected = self.tree_threats.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите угрозу для редактирования.")
            return
        item = self.tree_threats.item(selected[0])
        threat_id = item["values"][0]
        threats = load_data(THREATS_FILE)
        threat = next((t for t in threats if t["id"] == threat_id), None)
        if threat:
            ThreatDialog(self.root, self, mode="edit", threat=threat)

    def delete_threat(self):
        selected = self.tree_threats.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите угрозу для удаления.")
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранную угрозу?"):
            item = self.tree_threats.item(selected[0])
            threat_id = item["values"][0]
            threats = load_data(THREATS_FILE)
            threats = [t for t in threats if t["id"] != threat_id]
            save_data(threats, THREATS_FILE)
            self.refresh_threats_table()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новая модель", command=self.new_model)
        file_menu.add_command(label="Открыть модель", command=self.open_model)
        file_menu.add_command(label="Сохранить", command=self.save_model)
        file_menu.add_command(label="Сохранить как...", command=self.save_as_model)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        self.root.config(menu=menubar)

    def new_model(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".threatmodel",
            filetypes=[("Модель угроз", "*.threatmodel")],
            title="Сохранить новую модель как"
        )
        if not path:
            return
        self.threats = []
        self.offenders = []
        self.current_model_path = path
        self.refresh_threats_table()
        self.refresh_offenders_table()
        self._save_to_file(path)
        self.root.title(f"Анализ Угроз - {os.path.basename(path)}")
        self.threat_sort.clear()
        self.offender_sort.clear()
        messagebox.showinfo("Новая модель", f"Модель создана и сохранена.\n{path}")

    def open_model(self):
        """Открывает модель из JSON-файла."""
        path = filedialog.askopenfilename(filetypes=[("Model files", "*.threatmodel"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Загружаем данные
            save_data(data.get('threats', []), THREATS_FILE)
            save_data(data.get('offenders', []), OFFENDERS_FILE)
            self.current_model_path = path
            self.refresh_threats_table()
            self.refresh_offenders_table()
            self.root.title(f"Анализ Угроз - {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть модель: {e}")

    def save_model(self):
        """Сохраняет текущую модель в текущий путь."""
        if self.current_model_path:
            self._save_to_file(self.current_model_path)
        else:
            self.save_as_model()

    def save_as_model(self):
        """Сохраняет модель в новый файл."""
        path = filedialog.asksaveasfilename(defaultextension=".threatmodel",
                                            filetypes=[("Model files", "*.threatmodel")])
        if path:
            self._save_to_file(path)
            self.current_model_path = path
            self.root.title(f"Анализ Угроз - {os.path.basename(path)}")

    def _save_to_file(self, path):
        """Вспомогательный метод сохранения данных в файл."""
        threats = load_data(THREATS_FILE)
        offenders = load_data(OFFENDERS_FILE)
        data = {
            "threats": threats,
            "offenders": offenders,
            "version": 1
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Сохранение", f"Модель сохранена в {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    # ----------------------- НАРУШИТЕЛИ -----------------------
    def setup_offenders_tab(self):
        control_panel = tk.Frame(self.offenders_frame, bg='#2b2b2b')
        control_panel.pack(fill=tk.X, padx=5, pady=5)
        for text, cmd in [("✏️ Редактировать", self.edit_offender),
                          ("❌ Удалить", self.delete_offender),
                          ("🔄 Обновить", self.refresh_offenders_table)]:
            tk.Button(control_panel, text=text, command=cmd,
                      bg='#4e4e4e', fg='white', padx=5, pady=2, cursor='hand2').pack(side=tk.LEFT, padx=2)

        columns = ("id", "type", "level", "motivation", "description")
        self.tree_offenders = ttk.Treeview(self.offenders_frame, columns=columns, show="headings")
        headers = {"id": "ID", "type": "Тип", "level": "Уровень", "motivation": "Мотив", "description": "Описание действий"}
        for col in columns:
            self.tree_offenders.heading(col, text=headers[col], command=lambda c=col: self.sort_offenders_by_column(c))
            self.tree_offenders.column(col, width=150)
        self.tree_offenders.column("description", width=300)
        vsb = ttk.Scrollbar(self.offenders_frame, orient="vertical", command=self.tree_offenders.yview)
        self.tree_offenders.configure(yscrollcommand=vsb.set)
        self.tree_offenders.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def sort_offenders_by_column(self, col):
        reverse = self.offender_sort.get(col, False)
        items = [(self.tree_offenders.set(child, col), child) for child in self.tree_offenders.get_children('')]
        try:
            items.sort(key=lambda x: float(x[0]) if x[0].replace('.', '', 1).isdigit() else x[0], reverse=reverse)
        except:
            items.sort(key=lambda x: str(x[0]).lower(), reverse=reverse)
        for index, (val, child) in enumerate(items):
            self.tree_offenders.move(child, '', index)
        self.offender_sort[col] = not reverse

    def refresh_offenders_table(self):
        for row in self.tree_offenders.get_children():
            self.tree_offenders.delete(row)
        offenders = load_data(OFFENDERS_FILE)
        for o in offenders:
            self.tree_offenders.insert("", tk.END, values=(
                o["id"], o["type"], o["level"], o.get("motivation", ""), o.get("description", "")
            ))
        self.offender_sort.clear()

    def get_next_offender_id(self):
        offenders = load_data(OFFENDERS_FILE)
        max_num = 0
        for o in offenders:
            if o["id"].startswith("OF-"):
                try:
                    num = int(o["id"][3:])
                    if num > max_num: max_num = num
                except: pass
        return f"OF-{max_num+1:03d}"

    def add_offender(self):
        OffenderDialog(self.root, self, mode="add")

    def edit_offender(self):
        selected = self.tree_offenders.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите нарушителя.")
            return
        item = self.tree_offenders.item(selected[0])
        oid = item["values"][0]
        offenders = load_data(OFFENDERS_FILE)
        offender = next((o for o in offenders if o["id"] == oid), None)
        if offender:
            OffenderDialog(self.root, self, mode="edit", offender=offender)

    def delete_offender(self):
        selected = self.tree_offenders.selection()
        if not selected:
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранного нарушителя?"):
            item = self.tree_offenders.item(selected[0])
            oid = item["values"][0]
            offenders = load_data(OFFENDERS_FILE)
            offenders = [o for o in offenders if o["id"] != oid]
            save_data(offenders, OFFENDERS_FILE)
            self.refresh_offenders_table()

    # ----------------------- РИСКИ И ОТЧЕТЫ -----------------------
    def setup_risks_tab(self):
        btn_frame = tk.Frame(self.risks_frame, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        for text, cmd in [("📈 Рассчитать риски", self.calc_risks),
                          ("📎 Экспорт в CSV", self.export_csv),
                          ("📄 Экспорт в TXT", self.export_txt)]:
            tk.Button(btn_frame, text=text, command=cmd,
                      bg='#4e4e4e', fg='white', padx=5, pady=2, cursor='hand2').pack(side=tk.LEFT, padx=2)

        self.risk_text = tk.Text(self.risks_frame, wrap=tk.WORD, font=('Consolas', 10),
                                 bg='#3c3c3c', fg='#e0e0e0', insertbackground='white')
        scrollbar = ttk.Scrollbar(self.risks_frame, orient=tk.VERTICAL, command=self.risk_text.yview)
        self.risk_text.configure(yscrollcommand=scrollbar.set)
        self.risk_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def calc_risks(self):
        threats = load_data(THREATS_FILE)
        if not threats:
            self.risk_text.delete(1.0, tk.END)
            self.risk_text.insert(tk.END, "Нет угроз для расчета.")
            return
        self.risk_text.delete(1.0, tk.END)
        self.risk_text.insert(tk.END, "="*70 + "\n")
        self.risk_text.insert(tk.END, "РЕЗУЛЬТАТЫ ОЦЕНКИ РИСКОВ\n")
        self.risk_text.insert(tk.END, "="*70 + "\n")
        total_risk = 0
        high = []
        for t in threats:
            risk = t["probability"] * t["damage"]
            total_risk += risk
            level = get_risk_level_ru(t["probability"], t["damage"], self.config["risk_scale"])
            if level == "Высокий":
                high.append(t["id"])
            self.risk_text.insert(tk.END, f"{t['id']:12} | {t['name'][:45]:45} | Риск: {risk:2d} | Ур.: {level}\n")
        self.risk_text.insert(tk.END, "\n" + "-"*70 + "\n")
        self.risk_text.insert(tk.END, f"📊 Интегральный риск: {total_risk}\n")
        self.risk_text.insert(tk.END, f"Средний риск на угрозу: {total_risk/len(threats):.2f}\n")
        if high:
            self.risk_text.insert(tk.END, f"⚠️ Угрозы с высоким риском: {', '.join(high)}\n")

    def export_csv(self):
        threats = load_data(THREATS_FILE)
        if not threats:
            messagebox.showwarning("Экспорт", "Нет данных для экспорта.")
            return
        filename = f"угрозы_экспорт_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            import csv
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                fieldnames = ["id", "name", "category", "source", "probability", "damage", "description"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for t in threats:
                    writer.writerow({k: t.get(k, "") for k in fieldnames})
            messagebox.showinfo("Экспорт", f"Данные сохранены в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def export_txt(self):
        threats = load_data(THREATS_FILE)
        offenders = load_data(OFFENDERS_FILE)
        filename = f"отчет_по_угрозам_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("ОТЧЕТ ПО МОДЕЛИ УГРОЗ И НАРУШИТЕЛЕЙ\n")
                f.write(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"Шкала: {self.config['risk_scale']}\n\n")
                f.write("=== УГРОЗЫ ===\n")
                for t in threats:
                    f.write(f"{t['id']} | {t['name']} | {t.get('category', '')} | {t.get('source', '')}\n")
                    f.write(f"   Вероятность: {t['probability']}, Ущерб: {t['damage']}, Риск: {t['probability']*t['damage']}\n")
                    if t.get('description'):
                        f.write(f"   Описание: {t['description']}\n")
                f.write("\n=== НАРУШИТЕЛИ ===\n")
                for o in offenders:
                    f.write(f"{o['id']} | {o['type']} | {o['level']} | Мотив: {o.get('motivation', '')}\n")
                    if o.get('description'):
                        f.write(f"   {o['description']}\n")
                f.write(f"\n=== ИТОГО ===\nИнтегральный риск: {sum(t['probability']*t['damage'] for t in threats)}\n")
                f.write(f"Всего угроз: {len(threats)}\nВсего нарушителей: {len(offenders)}\n")
            messagebox.showinfo("Экспорт", f"Отчёт сохранён в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def import_from_bdu(self):
        file_path = filedialog.askopenfilename(title="Выберите JSON-файл с угрозами", filetypes=[("JSON", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            threats = []
            if isinstance(data, list):
                for item in data:
                    tid = item.get("id", "")
                    if tid and tid.startswith("УБИ."):
                        threats.append({
                            "id": tid,
                            "name": item.get("title") or item.get("name") or "Без названия",
                            "category": item.get("category", ""),
                            "source": item.get("source", ""),
                            "probability": 3,
                            "damage": 3,
                            "description": item.get("description", "")
                        })
            if threats:
                existing = load_data(THREATS_FILE)
                existing_ids = {t["id"] for t in existing}
                new_count = 0
                for t in threats:
                    if t["id"] not in existing_ids:
                        existing.append(t)
                        new_count += 1
                if new_count:
                    save_data(existing, THREATS_FILE)
                    self.refresh_threats_table()
                    messagebox.showinfo("Успех", f"Добавлено {new_count} угроз")
                else:
                    messagebox.showinfo("Импорт", "Новых угроз не найдено")
            else:
                messagebox.showwarning("Импорт", "Не удалось извлечь угрозы из файла")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def setup_help_tab(self):
        text = tk.Text(self.help_frame, wrap=tk.WORD, font=('Segoe UI', 11),
                       bg='#3c3c3c', fg='#e0e0e0')
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scroll = ttk.Scrollbar(self.help_frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        help_str = """🔐 РАЗРАБОТКА МОДЕЛИ УГРОЗ И НАРУШИТЕЛЯ

1. Описание системы (активы, архитектура).
2. Импорт угроз из БДУ ФСТЭК или добавление вручную.
3. Классификация нарушителей (внешние/внутренние, уровни Н1-Н4).
4. Для каждой угрозы задайте вероятность и ущерб (1-5).
5. Рассчитайте риски – программа покажет интегральный риск.
6. Угрозы с высоким риском требуют первоочередных мер.
7. Экспортируйте результаты в CSV или TXT для отчёта."""
        text.insert(tk.END, help_str)
        text.config(state=tk.DISABLED)

    def setup_settings_tab(self):
        frame = ttk.LabelFrame(self.settings_frame, text="Настройки шкалы рисков")
        frame.pack(fill=tk.X, padx=20, pady=20)
        ttk.Label(frame, text="Выберите метод расчёта:").pack(anchor=tk.W, padx=10, pady=5)
        self.scale_var = tk.StringVar(value=self.config["risk_scale"])
        ttk.Radiobutton(frame, text="3×3 (Низкий / Средний / Высокий)", variable=self.scale_var, value="3x3").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(frame, text="5×5 (Детальная, рекомендуется)", variable=self.scale_var, value="5x5").pack(anchor=tk.W, padx=20)
        def save_scale():
            self.config["risk_scale"] = self.scale_var.get()
            save_config(self.config)
            self.refresh_threats_table()
            messagebox.showinfo("Настройки", "Шкала обновлена. Пересчитайте риски.")
        ttk.Button(frame, text="Сохранить", command=save_scale).pack(pady=10)

# ----------------------- ДИАЛОГ УГРОЗЫ -----------------------
class ThreatDialog:
    def __init__(self, parent, app, mode="add", threat=None):
        self.app = app
        self.mode = mode
        self.threat = threat
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавление угрозы" if mode == "add" else "Редактирование угрозы")
        self.dialog.geometry("700x750")
        self.dialog.minsize(650, 700)
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='#1e2a3a')

        main = tk.Frame(self.dialog, bg='#1e2a3a')
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        row = 0
        tk.Label(main, text="ID угрозы:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
        frame_id = tk.Frame(main, bg='#1e2a3a')
        frame_id.grid(row=row+1, column=0, sticky='ew', pady=(0,10))
        self.prefix_var = tk.BooleanVar(value=True)
        self.prefix_check = tk.Checkbutton(frame_id, text="УБИ.", variable=self.prefix_var,
                                           bg='#1e2a3a', fg='#e0e0e0', selectcolor='#1e2a3a', activebackground='#1e2a3a')
        self.prefix_check.pack(side=tk.LEFT)
        self.id_entry = tk.Entry(frame_id, width=40, bg='#2c3e4e', fg='white', insertbackground='white')
        self.id_entry.pack(side=tk.LEFT, padx=5)
        if mode == "edit" and threat:
            self.prefix_var.set(False)
            self.prefix_check.config(state='disabled')
            self.id_entry.insert(0, threat["id"])
            self.id_entry.config(state='readonly')
        else:
            self.id_entry.insert(0, "016")
        row += 2

        tk.Label(main, text="Наименование угрозы *:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
        self.name_entry = tk.Entry(main, width=50, bg='#2c3e4e', fg='white', insertbackground='white')
        self.name_entry.grid(row=row+1, column=0, sticky='ew', pady=(0,10))
        if mode == "edit" and threat:
            self.name_entry.insert(0, threat["name"])
        row += 2

        tk.Label(main, text="Категория:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
        self.category_combo = ttk.Combobox(main, values=["Конфиденциальность", "Целостность", "Доступность"],
                                           width=47, state="readonly", style="Dark.TCombobox")
        self.category_combo.grid(row=row + 1, column=0, sticky='ew', pady=(0, 10))
        if mode == "edit" and threat:
            self.category_combo.set(threat.get("category", ""))
        row += 2

        # Настройка стиля для тёмных комбобоксов
        style = ttk.Style()
        style.configure("Dark.TCombobox",
                        fieldbackground='#2c3e4e',
                        background='#2c3e4e',
                        foreground='#e0e0e0',
                        selectbackground='#4e6e8e',
                        selectforeground='white')
        style.map("Dark.TCombobox",
                  fieldbackground=[('readonly', '#2c3e4e')],
                  background=[('readonly', '#2c3e4e')],
                  foreground=[('readonly', '#e0e0e0')])

        tk.Label(main, text="Источник угрозы:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
        self.source_combo = ttk.Combobox(main, values=["Внешний", "Внутренний"],
                                         width=47, state="readonly", style="Dark.TCombobox")
        self.source_combo.grid(row=row + 1, column=0, sticky='ew', pady=(0, 10))
        if mode == "edit" and threat:
            self.source_combo.set(threat.get("source", ""))
        row += 2

        frame_vals = tk.Frame(main, bg='#1e2a3a')
        frame_vals.grid(row=row, column=0, sticky='ew', pady=5)
        frame_vals.columnconfigure(0, weight=1)
        frame_vals.columnconfigure(1, weight=1)
        tk.Label(frame_vals, text="Вероятность (1-5):", bg='#1e2a3a', fg='#e0e0e0').grid(row=0, column=0, sticky='w')
        tk.Label(frame_vals, text="Ущерб (1-5):", bg='#1e2a3a', fg='#e0e0e0').grid(row=0, column=1, sticky='w')
        self.prob_entry = tk.Entry(frame_vals, width=10, bg='#2c3e4e', fg='white', insertbackground='white')
        self.prob_entry.grid(row=1, column=0, sticky='w', padx=(0,10))
        self.damage_entry = tk.Entry(frame_vals, width=10, bg='#2c3e4e', fg='white', insertbackground='white')
        self.damage_entry.grid(row=1, column=1, sticky='w')
        if mode == "edit" and threat:
            self.prob_entry.insert(0, str(threat["probability"]))
            self.damage_entry.insert(0, str(threat["damage"]))
        else:
            self.prob_entry.insert(0, "3")
            self.damage_entry.insert(0, "3")
        row += 1

        tk.Label(main, text="Описание угрозы:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row+1, column=0, sticky='w', pady=(15,0))
        self.desc_text = tk.Text(main, height=6, width=60, bg='#2c3e4e', fg='white', insertbackground='white')
        self.desc_text.grid(row=row+2, column=0, sticky='ew', pady=(5,15))
        if mode == "edit" and threat:
            self.desc_text.insert(tk.END, threat.get("description", ""))
        row += 3

        btn_frame = tk.Frame(main, bg='#1e2a3a')
        btn_frame.grid(row=row, column=0, pady=20)
        tk.Button(btn_frame, text="Сохранить", command=self.save,
                  bg='#2e7d32', fg='white', padx=20, pady=5, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Отмена", command=self.dialog.destroy,
                  bg='#b71c1c', fg='white', padx=20, pady=5, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=10)

        main.columnconfigure(0, weight=1)

    def save(self):
        if self.mode == "add":
            number = self.id_entry.get().strip()
            if not number:
                messagebox.showerror("Ошибка", "Введите число для ID угрозы (например, 016)")
                return
            if self.prefix_var.get():
                tid = f"УБИ.{number}"
            else:
                tid = number
        else:
            tid = self.threat["id"]
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Наименование угрозы обязательно.")
            return
        try:
            prob = int(self.prob_entry.get())
            damage = int(self.damage_entry.get())
            if not (1 <= prob <= 5 and 1 <= damage <= 5):
                raise ValueError
        except:
            messagebox.showerror("Ошибка", "Вероятность и ущерб должны быть целыми числами от 1 до 5.")
            return

        threat_data = {
            "id": tid,
            "name": name,
            "category": self.category_combo.get(),
            "source": self.source_combo.get(),
            "probability": prob,
            "damage": damage,
            "description": self.desc_text.get("1.0", tk.END).strip()
        }
        threats = load_data(THREATS_FILE)
        if self.mode == "add":
            if any(t["id"] == tid for t in threats):
                messagebox.showerror("Ошибка", f"Угроза с ID {tid} уже существует.")
                return
            threats.append(threat_data)
        else:
            for i, t in enumerate(threats):
                if t["id"] == tid:
                    threats[i] = threat_data
                    break
        save_data(threats, THREATS_FILE)
        self.app.refresh_threats_table()
        self.dialog.destroy()

# ----------------------- ДИАЛОГ НАРУШИТЕЛЯ -----------------------
class OffenderDialog:
    def __init__(self, parent, app, mode="add", offender=None):
        self.app = app
        self.mode = mode
        self.offender = offender
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавление нарушителя" if mode == "add" else "Редактирование нарушителя")
        self.dialog.geometry("650x600")
        self.dialog.minsize(600, 550)
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='#1e2a3a')

        main = tk.Frame(self.dialog, bg='#1e2a3a')
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        row = 0
        if mode == "add":
            tk.Label(main, text="ID будет сгенерирован автоматически", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
            self.id_label = tk.Label(main, text=app.get_next_offender_id(), bg='#1e2a3a', fg='#59BFFF', font=('Segoe UI', 10, 'bold'))
            self.id_label.grid(row=row+1, column=0, sticky='w', pady=(0,10))
            row += 2
        else:
            tk.Label(main, text="ID:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
            self.id_label = tk.Label(main, text=offender["id"], bg='#1e2a3a', fg='#59BFFF', font=('Segoe UI', 10, 'bold'))
            self.id_label.grid(row=row+1, column=0, sticky='w', pady=(0,10))
            row += 2

        tk.Label(main, text="Тип нарушителя *:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
        self.type_combo = ttk.Combobox(main, values=["Внешний", "Внутренний"],
                                       width=47, state="readonly", style="Dark.TCombobox")
        self.type_combo.grid(row=row + 1, column=0, sticky='ew', pady=(0, 10))
        if mode == "edit" and offender:
            self.type_combo.set(offender.get("type", ""))
        row += 2

        tk.Label(main, text="Уровень (Н1-Н4) *:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
        self.level_combo = ttk.Combobox(main, values=["Н1", "Н2", "Н3", "Н4"],
                                        width=47, state="readonly", style="Dark.TCombobox")
        self.level_combo.grid(row=row + 1, column=0, sticky='ew', pady=(0, 10))
        if mode == "edit" and offender:
            self.level_combo.set(offender.get("level", ""))
        row += 2

        tk.Label(main, text="Мотив:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
        self.motive_entry = tk.Entry(main, width=50, bg='#2c3e4e', fg='white', insertbackground='white')
        self.motive_entry.grid(row=row+1, column=0, sticky='ew', pady=(0,10))
        if mode == "edit" and offender:
            self.motive_entry.insert(0, offender.get("motivation", ""))
        row += 2

        tk.Label(main, text="Описание действий:", bg='#1e2a3a', fg='#e0e0e0', anchor='w').grid(row=row, column=0, sticky='w', pady=5)
        self.desc_text = tk.Text(main, height=5, width=50, bg='#2c3e4e', fg='white', insertbackground='white')
        self.desc_text.grid(row=row+1, column=0, sticky='ew', pady=(0,15))
        if mode == "edit" and offender:
            self.desc_text.insert(tk.END, offender.get("description", ""))
        row += 2

        btn_frame = tk.Frame(main, bg='#1e2a3a')
        btn_frame.grid(row=row, column=0, pady=20)
        tk.Button(btn_frame, text="Сохранить", command=self.save,
                  bg='#2e7d32', fg='white', padx=20, pady=5, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Отмена", command=self.dialog.destroy,
                  bg='#b71c1c', fg='white', padx=20, pady=5, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=10)

        main.columnconfigure(0, weight=1)

    def save(self):
        otype = self.type_combo.get()
        level = self.level_combo.get()
        if not otype or not level:
            messagebox.showerror("Ошибка", "Тип и уровень нарушителя обязательны.")
            return
        if self.mode == "add":
            oid = self.app.get_next_offender_id()
        else:
            oid = self.offender["id"]
        offender_data = {
            "id": oid,
            "type": otype,
            "level": level,
            "motivation": self.motive_entry.get().strip(),
            "description": self.desc_text.get("1.0", tk.END).strip()
        }
        offenders = load_data(OFFENDERS_FILE)
        if self.mode == "add":
            offenders.append(offender_data)
        else:
            for i, o in enumerate(offenders):
                if o["id"] == oid:
                    offenders[i] = offender_data
                    break
        save_data(offenders, OFFENDERS_FILE)
        self.app.refresh_offenders_table()
        self.dialog.destroy()

# ----------------------- ЗАПУСК -----------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ThreatAnalyzerApp(root)
    root.mainloop()