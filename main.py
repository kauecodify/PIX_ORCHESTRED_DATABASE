# -*- coding: utf-8 -*-
"""

Created on Sun Sep 14 20:49:30 2025
@author: K

Pix Orchestrator - Olinda + Sandbox Transações com Acumulação

                ---reforma tributária---

- Usa SQLite para armazenar chaves e transações
- Worker atualiza dados periodicamente com acumulação inteligente
- Interface Tkinter para logs e controle
- Sistema de backup e recuperação de períodos offline
- Alterar DB para processamento de dados reais
- Botões de controle (sync, backup, restore, análise por data)

"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Label
import threading
import time
import logging
import requests
import sqlite3
from datetime import datetime, timedelta
import json
import os
import shutil
from PIL import Image, ImageTk

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "pix_orchestrator.db")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backups")
BCB_LOGO_PATH = os.path.join(SCRIPT_DIR, "bcb.png")

OLINDA_KEYS_URL = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/ChavesPix?$format=json"
OLINDA_TRANSACTIONS_URL = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/TransacoesPix"

# ---------------- DB INIT ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pix_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE,
            tipo TEXT,
            owner TEXT,
            instituicao TEXT,
            data_criacao TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'ATIVA'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS pix_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            end_to_end_id TEXT UNIQUE,
            chave_origem TEXT,
            chave_destino TEXT,
            valor REAL,
            horario TIMESTAMP,
            situacao TEXT,
            info_origem TEXT,
            info_destino TEXT,
            modalidade_agente TEXT,
            raw_data TEXT,
            processed INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY,
            catchup_enabled INTEGER DEFAULT 1,
            max_catchup_days INTEGER DEFAULT 7,
            polling_interval INTEGER DEFAULT 30,
            last_successful_sync TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            module TEXT,
            level TEXT,
            message TEXT
        )
    ''')
    c.execute('''
        INSERT OR IGNORE INTO system_config (id, catchup_enabled, max_catchup_days, polling_interval)
        VALUES (1, 1, 7, 30)
    ''')
    conn.commit()
    conn.close()

# ---------------- API ----------------
def fetch_bcb_data(url, params=None):
    try:
        headers = {'User-Agent': 'PixOrchestrator/1.0', 'Accept': 'application/json'}
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro API {url}: {e}")
        return None

def get_pix_keys_from_bcb():
    data = fetch_bcb_data(OLINDA_KEYS_URL)
    return data.get("value", []) if data else []

def get_pix_transactions_from_bcb(start_date, end_date):
    params = {
        "$filter": f"horario ge {start_date} and horario le {end_date}",
        "$format": "json",
        "$orderby": "horario desc"
    }
    data = fetch_bcb_data(OLINDA_TRANSACTIONS_URL, params)
    return data.get("value", []) if data else []

# ---------------- SAVE ----------------
def save_transactions(transactions):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for tx in transactions:
        try:
            c.execute('''
                INSERT OR REPLACE INTO pix_transactions
                (end_to_end_id, chave_origem, chave_destino, valor, horario,
                 situacao, info_origem, info_destino, modalidade_agente, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx.get('endToEndId'),
                tx.get('chaveOrigem'),
                tx.get('chaveDestino'),
                tx.get('valor'),
                tx.get('horario'),
                tx.get('situacao'),
                json.dumps(tx.get('infoOrigem', {})),
                json.dumps(tx.get('infoDestino', {})),
                tx.get('modalidadeAgente'),
                json.dumps(tx)
            ))
        except sqlite3.Error as e:
            logger.error(f"Erro salvar tx: {e}")
    conn.commit()
    conn.close()

def save_pix_keys(keys):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for k in keys:
        try:
            c.execute('''
                INSERT OR REPLACE INTO pix_keys
                (chave, tipo, owner, instituicao, data_criacao, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                k.get('chave'),
                k.get('tipo'),
                k.get('titular'),
                k.get('instituicao'),
                k.get('dataCriacao'),
                'ATIVA'
            ))
        except sqlite3.Error as e:
            logger.error(f"Erro salvar chave: {e}")
    conn.commit()
    conn.close()

def update_last_sync():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE system_config SET last_successful_sync = CURRENT_TIMESTAMP WHERE id = 1")
    conn.commit()
    conn.close()

# ---------------- BACKUP ----------------
def backup_database():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"pix_backup_{timestamp}.db")
    shutil.copy(DB_PATH, backup_file)
    logger.info(f"Backup criado: {backup_file}")
    return backup_file

def restore_database(path):
    if os.path.exists(path):
        shutil.copy(path, DB_PATH)
        logger.info(f"Banco restaurado de {path}")
        return True
    return False

# ---------------- WORKER ----------------
def sync_data():
    logger.info("Sincronizando manualmente com o BCB...")
    keys = get_pix_keys_from_bcb()
    save_pix_keys(keys)

    start_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    transactions = get_pix_transactions_from_bcb(start_date, end_date)
    save_transactions(transactions)

    update_last_sync()
    backup_database()
    logger.info("Sincronização concluída!")

def sync_worker():
    while True:
        try:
            sync_data()
        except Exception as e:
            logger.error(f"Erro no worker: {e}")
        time.sleep(60)

# ---------------- INTERFACE ----------------
class MatrixPixInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Pix Orchestrator - BCB ")
        self.root.geometry("1200x750")
        self.root.configure(bg="#2c3e50")
        self.load_logo()
        self.setup_interface()
        self.update_stats()
        threading.Thread(target=sync_worker, daemon=True).start()

    def load_logo(self):
        if os.path.exists(BCB_LOGO_PATH):
            try:
                logo = Image.open(BCB_LOGO_PATH).resize((90, 90))
                self.logo_img = ImageTk.PhotoImage(logo)
                Label(self.root, image=self.logo_img, bg="#2c3e50").grid(row=0, column=0, sticky="nw")
            except Exception as e:
                logger.error(f"Erro ao carregar logo: {e}")
        else:
            logger.warning(f"Logo não encontrado em: {BCB_LOGO_PATH}")
            Label(self.root, text="BCB Pix", fg="white", bg="#2c3e50",
                  font=("Arial", 16, "bold")).grid(row=0, column=0, sticky="nw")

    def setup_interface(self):
        # Estatísticas
        stats_frame = ttk.LabelFrame(self.root, text="Estatísticas")
        stats_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.stats_labels = {}
        for i, stat in enumerate(["total_keys","active_keys","total_transactions","last_sync"]):
            ttk.Label(stats_frame, text=stat).grid(row=0, column=i*2)
            self.stats_labels[stat] = ttk.Label(stats_frame, text="0")
            self.stats_labels[stat].grid(row=0, column=i*2+1)

        # Botões de controle
        control_frame = ttk.LabelFrame(self.root, text="Controles")
        control_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        ttk.Button(control_frame, text="🔄 Sync Manual", command=self.manual_sync).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="💾 Backup", command=self.manual_backup).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="♻️ Restaurar", command=self.restore_backup).grid(row=0, column=2, padx=5)

        # Filtros de data
        ttk.Label(control_frame, text="Data Início (YYYY-MM-DD):").grid(row=1, column=0)
        self.start_entry = ttk.Entry(control_frame)
        self.start_entry.grid(row=1, column=1)
        ttk.Label(control_frame, text="Data Fim (YYYY-MM-DD):").grid(row=1, column=2)
        self.end_entry = ttk.Entry(control_frame)
        self.end_entry.grid(row=1, column=3)
        ttk.Button(control_frame, text="📅 Analisar Período", command=self.analyze_period).grid(row=1, column=4, padx=5)

        # Área de dados
        data_frame = ttk.LabelFrame(self.root, text="Dados")
        data_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.notebook = ttk.Notebook(data_frame)
        self.notebook.pack(fill="both", expand=True)

        self.transactions_tree = ttk.Treeview(self.notebook, columns=("id","horario","chave_origem","chave_destino","valor","situacao"), show="headings")
        for col in ("id","horario","chave_origem","chave_destino","valor","situacao"):
            self.transactions_tree.heading(col, text=col)
        self.notebook.add(self.transactions_tree, text="Transações")

        self.keys_tree = ttk.Treeview(self.notebook, columns=("chave","tipo","owner","instituicao","status"), show="headings")
        for col in ("chave","tipo","owner","instituicao","status"):
            self.keys_tree.heading(col, text=col)
        self.notebook.add(self.keys_tree, text="Chaves Pix")

    def manual_sync(self):
        threading.Thread(target=sync_data, daemon=True).start()
        messagebox.showinfo("Sync", "Sincronização manual iniciada")

    def manual_backup(self):
        path = backup_database()
        messagebox.showinfo("Backup", f"Backup salvo em {path}")

    def restore_backup(self):
        path = filedialog.askopenfilename(initialdir=BACKUP_DIR, title="Escolha o backup",
                                          filetypes=[("DB Files","*.db")])
        if path and restore_database(path):
            messagebox.showinfo("Restaurar", f"Banco restaurado de {path}")
        else:
            messagebox.showerror("Erro", "Falha ao restaurar backup")

    def analyze_period(self):
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").strftime("%Y-%m-%dT%H:%M:%SZ")
            end_date = datetime.strptime(end, "%Y-%m-%d").strftime("%Y-%m-%dT%H:%M:%SZ")
            transactions = get_pix_transactions_from_bcb(start_date, end_date)
            save_transactions(transactions)
            messagebox.showinfo("Análise", f"{len(transactions)} transações carregadas no período")
        except Exception as e:
            messagebox.showerror("Erro", f"Data inválida ou falha: {e}")

    def update_stats(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM pix_keys")
        self.stats_labels["total_keys"].config(text=str(c.fetchone()[0]))
        c.execute("SELECT COUNT(*) FROM pix_keys WHERE status='ATIVA'")
        self.stats_labels["active_keys"].config(text=str(c.fetchone()[0]))
        c.execute("SELECT COUNT(*) FROM pix_transactions")
        self.stats_labels["total_transactions"].config(text=str(c.fetchone()[0]))
        c.execute("SELECT last_successful_sync FROM system_config WHERE id=1")
        last = c.fetchone()[0] or "Nunca"
        self.stats_labels["last_sync"].config(text=last)
        conn.close()
        self.root.after(10000, self.update_stats)

# ---------------- MAIN ----------------
def main():
    init_db()
    root = tk.Tk()
    app = MatrixPixInterface(root)
    root.mainloop()

if __name__ == "__main__":
    main()
