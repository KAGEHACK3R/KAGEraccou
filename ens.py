import tkinter as tk
from tkinter import ttk, messagebox, Canvas
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pyperclip
from datetime import datetime, timedelta
import json
import os
import threading
import locale
import logging
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from cryptography.fernet import Fernet
import importlib.metadata
import subprocess

# Configuration du logging
logging.basicConfig(filename="multitool.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Vérification et installation des dépendances
required = {"requests", "pyperclip", "pillow", "matplotlib", "cryptography"}
installed = {d.name.lower() for d in importlib.metadata.distributions()}
missing = required - installed
if missing:
    logging.info(f"Installation des dépendances manquantes : {missing}")
    subprocess.check_call(["pip", "install", *missing])

# Clé de chiffrement
KEY_FILE = "secret.key"
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
with open(KEY_FILE, "rb") as f:
    cipher = Fernet(f.read())

# Configuration et traductions
CONFIG_FILE = "config.json"
HISTORY_FILE = "history.enc"
DEFAULT_CONFIG = {
    "theme": "dark",
    "lang": locale.getlocale()[0][:2] if locale.getlocale()[0] else "en",
    "safe_browsing_api": ""
}

translations = {
    "en": {
        "title": "Pro Multi-Tool - Ethical Hacking",
        "tab1": "Currency",
        "tab2": "URL",
        "amount": "Amount:",
        "from": "From:",
        "to": "To:",
        "convert": "Convert",
        "trend": "Show Trend",
        "history": "History:",
        "search": "Search History",
        "enter_url": "Enter URL:",
        "shorten": "Shorten",
        "analyze": "Analyze Safety",
        "copy": "Copy",
        "export": "Export",
        "theme": "Theme",
        "signature": "Created by Guy Kouakou (KAGEHACKER) - {}",
        "error_amount": "Invalid amount.",
        "error_api": "API error: {}",
        "safe": "URL is safe.",
        "unsafe": "URL may be unsafe!"
    },
    "fr": {
        "title": "Outil Pro Multi-Fonctions - Hacking Éthique",
        "tab1": "Devises",
        "tab2": "URL",
        "amount": "Montant :",
        "from": "De :",
        "to": "Vers :",
        "convert": "Convertir",
        "trend": "Voir Tendance",
        "history": "Historique :",
        "search": "Rechercher Historique",
        "enter_url": "Entrez URL :",
        "shorten": "Raccourcir",
        "analyze": "Analyser Sécurité",
        "copy": "Copier",
        "export": "Exporter",
        "theme": "Thème",
        "signature": "Créé par Guy Kouakou (KAGEHACKER) - {}",
        "error_amount": "Montant invalide.",
        "error_api": "Erreur API : {}",
        "safe": "URL sécurisée.",
        "unsafe": "URL potentiellement dangereuse !"
    }
}

class MultiToolApp:
    def __init__(self, root):
        self.root = root
        self.config = self.load_config()
        self.lang = translations.get(self.config["lang"], translations["en"])
        self.theme = self.config["theme"]
        self.currencies = self.fetch_currencies()
        self.last_short_url = ""
        self.history_data = self.load_history()
        self.setup_ui()
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        logging.info("Application initialisée")

    def load_config(self):
        try:
            Path(CONFIG_FILE).parent.mkdir(parents=True, exist_ok=True)
            if not os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Échec du chargement de la config : {e}")
            return DEFAULT_CONFIG

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Échec de la sauvegarde de la config : {e}")

    def fetch_currencies(self):
        try:
            response = self.session().get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            return sorted(response.json()["rates"].keys())
        except Exception as e:
            logging.warning(f"Échec de la récupération des devises : {e}")
            return ["USD", "EUR", "JPY", "GBP", "CAD"]

    def session(self):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def setup_ui(self):
        self.root.title(self.lang["title"])
        self.root.geometry("600x700")
        self.initialize_ui_components()
        self.apply_theme()
        self.update_colors()

    def initialize_ui_components(self):
        self.canvas = Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.dock = tk.Frame(self.canvas)
        self.canvas.create_window((300, 20), window=self.dock, anchor="n")
        ttk.Button(self.dock, text=self.lang["theme"], command=self.toggle_theme).pack(side="left", padx=5)
        ttk.Button(self.dock, text=self.lang["export"], command=self.export_history).pack(side="left", padx=5)

        self.notebook = ttk.Notebook(self.canvas)
        self.canvas.create_window((300, 350), window=self.notebook, anchor="center")
        self.setup_currency_tab()
        self.setup_url_tab()

        self.signature = tk.Label(self.canvas, text=self.lang["signature"].format(datetime.now().strftime("%d %B %Y")),
                                  font=("Helvetica", 9, "italic"))
        self.signature_id = self.canvas.create_window((300, 680), window=self.signature, anchor="s")
        self.animate_signature()

    def apply_theme(self):
        """Applique le thème via ttk.Style pour les widgets ttk et configure le fond de la fenêtre principale."""
        bg = "#2C3E50" if self.theme == "dark" else "#FFFFFF"
        fg = "#ECF0F1" if self.theme == "dark" else "#2C3E50"
        self.root.configure(bg=bg)
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=bg)
        if hasattr(self, 'dock'):
            self.dock.configure(bg=bg)
        # Configuration des styles ttk
        style = ttk.Style()
        style.configure("TButton", background="#3498DB" if self.theme == "dark" else "#2980B9", foreground=fg)
        style.configure("TNotebook", background=bg)
        style.configure("TCombobox", fieldbackground=bg, foreground=fg)
        style.configure("TFrame", background=bg)  # Pour les onglets

    def update_colors(self):
        """Met à jour les couleurs des widgets tk uniquement."""
        bg = "#2C3E50" if self.theme == "dark" else "#FFFFFF"
        fg = "#ECF0F1" if self.theme == "dark" else "#2C3E50"
        self._update_widget_colors(self.root, bg, fg)

    def _update_widget_colors(self, widget, bg, fg):
        """Met à jour les couleurs de manière récursive pour les widgets tk uniquement."""
        try:
            if isinstance(widget, tk.Frame):
                widget.config(bg=bg)
            elif isinstance(widget, tk.Label):
                widget.config(bg=bg, fg=fg)
            elif isinstance(widget, tk.Entry):
                widget.config(bg=bg, fg="#000000")  # Noir pour lisibilité
            elif isinstance(widget, tk.Listbox):
                widget.config(bg=bg, fg="#000000")  # Noir pour lisibilité
            # Les widgets ttk sont gérés par apply_theme et ignorés ici
        except Exception as e:
            logging.warning(f"Erreur lors de la mise à jour du widget {widget} : {e}")

        # Parcours récursif des enfants
        for child in widget.winfo_children():
            self._update_widget_colors(child, bg, fg)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.config["theme"] = self.theme
        self.save_config()
        self.apply_theme()
        self.update_colors()

    def animate_signature(self):
        if hasattr(self, 'signature_id'):
            self.canvas.move(self.signature_id, 0, -5)
            self.root.after(1000, self.animate_signature_reverse)

    def animate_signature_reverse(self):
        if hasattr(self, 'signature_id'):
            self.canvas.move(self.signature_id, 0, 5)
            self.root.after(1000, self.animate_signature)

    def setup_currency_tab(self):
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text=self.lang["tab1"])

        tk.Label(self.tab1, text=self.lang["amount"], font=("Helvetica", 12)).pack(pady=5)
        self.entry_amount = tk.Entry(self.tab1, font=("Helvetica", 12), width=20)
        self.entry_amount.pack()

        tk.Label(self.tab1, text=self.lang["from"], font=("Helvetica", 12)).pack(pady=5)
        self.combo_from = ttk.Combobox(self.tab1, values=self.currencies, state="readonly", width=10)
        self.combo_from.set("USD")
        self.combo_from.pack()

        tk.Label(self.tab1, text=self.lang["to"], font=("Helvetica", 12)).pack(pady=5)
        self.combo_to = ttk.Combobox(self.tab1, values=self.currencies, state="readonly", width=10)
        self.combo_to.set("EUR")
        self.combo_to.pack()

        ttk.Button(self.tab1, text=self.lang["convert"], command=self.convert_thread).pack(pady=5)
        ttk.Button(self.tab1, text=self.lang["trend"], command=self.show_trend).pack(pady=5)

        self.result_label = tk.Label(self.tab1, text="", font=("Helvetica", 12, "bold"))
        self.result_label.pack(pady=10)

        tk.Label(self.tab1, text=self.lang["history"], font=("Helvetica", 12)).pack(pady=5)
        self.history_frame = tk.Frame(self.tab1)
        self.history_frame.pack(pady=5, fill="x", padx=10)
        self.history_search = tk.Entry(self.history_frame, font=("Helvetica", 10))
        self.history_search.pack(side="left", padx=5)
        ttk.Button(self.history_frame, text=self.lang["search"], command=self.search_history).pack(side="left")
        self.history_list = tk.Listbox(self.tab1, height=5, font=("Helvetica", 10))
        self.history_list.pack(fill="x", padx=10)
        self.load_history_to_list()

    def setup_url_tab(self):
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text=self.lang["tab2"])

        tk.Label(self.tab2, text=self.lang["enter_url"], font=("Helvetica", 12)).pack(pady=5)
        self.entry_url = tk.Entry(self.tab2, font=("Helvetica", 12), width=30)
        self.entry_url.pack()

        ttk.Button(self.tab2, text=self.lang["shorten"], command=self.shorten_thread).pack(pady=5)
        ttk.Button(self.tab2, text=self.lang["analyze"], command=self.analyze_url_safety).pack(pady=5)

        self.url_result_label = tk.Label(self.tab2, text="", font=("Helvetica", 12, "bold"))
        self.url_result_label.pack(pady=10)

        self.copy_button = ttk.Button(self.tab2, text=self.lang["copy"], command=self.copy_url, state="disabled")
        self.copy_button.pack(pady=5)

    def convert_thread(self):
        threading.Thread(target=self.convert_currency, daemon=True).start()

    def convert_currency(self):
        try:
            amount = float(self.entry_amount.get())
            from_currency = self.combo_from.get()
            to_currency = self.combo_to.get()
            response = self.session().get(f"https://api.exchangerate-api.com/v4/latest/{from_currency}", timeout=5)
            data = response.json()
            rate = data["rates"][to_currency]
            result = amount * rate
            self.result_label.config(text=f"{amount} {from_currency} = {result:.2f} {to_currency}")
            self.history_data.append(f"{amount} {from_currency} -> {result:.2f} {to_currency}")
            self.save_history()
            self.load_history_to_list()
            logging.info(f"Converti {amount} {from_currency} en {result:.2f} {to_currency}")
        except ValueError:
            messagebox.showerror("Erreur", self.lang["error_amount"])
        except Exception as e:
            messagebox.showerror("Erreur", self.lang["error_api"].format(e))
            logging.error(f"Erreur de conversion : {e}")

    def show_trend(self):
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot([1, 2, 3], [1, 2, 3], label="Tendance Placeholder")
        ax.set_title("Tendance des devises")
        ax.legend()
        canvas = FigureCanvasTkAgg(fig, master=self.tab1)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=5)

    def shorten_thread(self):
        threading.Thread(target=self.shorten_url, daemon=True).start()

    def shorten_url(self):
        url = self.entry_url.get().strip()
        if not url:
            messagebox.showerror("Erreur", self.lang["error_api"].format("URL vide"))
            return
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        try:
            response = self.session().get(f"http://tinyurl.com/api-create.php?url={url}", timeout=5)
            self.last_short_url = response.text
            self.url_result_label.config(text=f"Raccourci : {self.last_short_url}")
            self.copy_button.config(state="normal")
            logging.info(f"URL raccourcie : {self.last_short_url}")
        except Exception as e:
            messagebox.showerror("Erreur", self.lang["error_api"].format(e))
            logging.error(f"Erreur de raccourcissement : {e}")

    def analyze_url_safety(self):
        if not self.last_short_url:
            messagebox.showerror("Erreur", "Raccourcissez une URL d'abord !")
            return
        messagebox.showinfo("Sécurité", self.lang["safe"])
        logging.info(f"Analyse de sécurité de l'URL : {self.last_short_url}")

    def copy_url(self):
        pyperclip.copy(self.last_short_url)
        self.show_toast("URL copiée avec succès")

    def save_history(self):
        try:
            encrypted = cipher.encrypt(json.dumps(self.history_data).encode())
            with open(HISTORY_FILE, "wb") as f:
                f.write(encrypted)
        except Exception as e:
            logging.error(f"Échec de la sauvegarde de l'historique : {e}")

    def load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "rb") as f:
                    decrypted = cipher.decrypt(f.read())
                    return json.loads(decrypted.decode())
            return []
        except Exception as e:
            logging.error(f"Échec du chargement de l'historique : {e}")
            return []

    def load_history_to_list(self):
        self.history_list.delete(0, tk.END)
        for item in self.history_data:
            self.history_list.insert(tk.END, item)

    def search_history(self):
        query = self.history_search.get().lower()
        self.history_list.delete(0, tk.END)
        for item in self.history_data:
            if query in item.lower():
                self.history_list.insert(tk.END, item)

    def export_history(self):
        try:
            with open("history_export.csv", "w", encoding="utf-8") as f:
                f.write("Historique\n")
                for item in self.history_data:
                    f.write(f"{item}\n")
            self.show_toast("Exporté vers history_export.csv")
            logging.info("Historique exporté")
        except Exception as e:
            logging.error(f"Échec de l'exportation : {e}")

    def show_toast(self, message):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.geometry(f"+{self.root.winfo_x()+200}+{self.root.winfo_y()+600}")
        tk.Label(toast, text=message, bg="#27AE60", fg="white", font=("Helvetica", 10)).pack(padx=10, pady=5)
        self.root.after(2000, toast.destroy)

    def toggle_fullscreen(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiToolApp(root)
    root.mainloop()
