"""
Configurador de Sincronização Remota
Permite configurar a conexão com o servidor VPS para sincronização
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sqlite3
from pathlib import Path
import sys

class ConfiguradorSyncRemoto:
    def __init__(self, parent=None):
        if parent:
            self.root = tk.Toplevel(parent)
            self.root.transient(parent)
            self.root.grab_set()
        else:
            self.root = tk.Tk()

        self.root.title("Configurar Sincronização Remota")
        self.root.geometry("600x500")

        # Determinar diretório base
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.desktop_db = os.path.join(self.base_dir, 'financas.db')
        self.env_file = os.path.join(self.base_dir, '.env')

        self.criar_widgets()
        self.carregar_configuracao()

    def criar_widgets(self):
        """Cria a interface gráfica"""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title = ttk.Label(
            main_frame,
            text="Configuração de Sincronização Remota",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=(0, 15))

        # Descrição
        desc = ttk.Label(
            main_frame,
            text="Configure a conexão com o servidor VPS para sincronizar\n"
                 "os dados entre o aplicativo desktop e a versão web.",
            justify=tk.CENTER
        )
        desc.pack(pady=(0, 20))

        # Frame de modo
        modo_frame = ttk.LabelFrame(main_frame, text="Modo de Sincronização", padding="10")
        modo_frame.pack(fill=tk.X, pady=10)

        self.modo_var = tk.StringVar(value="local")

        ttk.Radiobutton(
            modo_frame,
            text="🏠 Local (Desenvolvimento) - PostgreSQL na máquina local",
            variable=self.modo_var,
            value="local",
            command=self.on_modo_changed
        ).pack(anchor=tk.W, pady=5)

        ttk.Radiobutton(
            modo_frame,
            text="🌐 Remoto (Produção) - PostgreSQL no servidor VPS",
            variable=self.modo_var,
            value="remoto",
            command=self.on_modo_changed
        ).pack(anchor=tk.W, pady=5)

        # Frame de configuração remota
        self.remote_frame = ttk.LabelFrame(main_frame, text="Configuração do Servidor Remoto", padding="10")
        self.remote_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Host
        ttk.Label(self.remote_frame, text="Host/IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.host_var = tk.StringVar()
        ttk.Entry(self.remote_frame, textvariable=self.host_var, width=40).grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)

        # Porta
        ttk.Label(self.remote_frame, text="Porta:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.porta_var = tk.StringVar(value="5432")
        ttk.Entry(self.remote_frame, textvariable=self.porta_var, width=40).grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)

        # Banco de dados
        ttk.Label(self.remote_frame, text="Banco de Dados:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.database_var = tk.StringVar(value="financeiro")
        ttk.Entry(self.remote_frame, textvariable=self.database_var, width=40).grid(row=2, column=1, sticky=tk.EW, pady=5, padx=5)

        # Usuário
        ttk.Label(self.remote_frame, text="Usuário:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.user_var = tk.StringVar(value="financeiro_user")
        ttk.Entry(self.remote_frame, textvariable=self.user_var, width=40).grid(row=3, column=1, sticky=tk.EW, pady=5, padx=5)

        # Senha
        ttk.Label(self.remote_frame, text="Senha:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(self.remote_frame, textvariable=self.password_var, width=40, show="*").grid(row=4, column=1, sticky=tk.EW, pady=5, padx=5)

        # Checkbox mostrar senha
        self.show_password_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.remote_frame,
            text="Mostrar senha",
            variable=self.show_password_var,
            command=self.toggle_password
        ).grid(row=5, column=1, sticky=tk.W, padx=5)

        # Configurar grid
        self.remote_frame.columnconfigure(1, weight=1)

        # Frame de exemplos
        example_frame = ttk.LabelFrame(main_frame, text="Exemplos de Configuração", padding="10")
        example_frame.pack(fill=tk.X, pady=10)

        ttk.Label(
            example_frame,
            text="🌐 VPS Remoto:\n"
                 "Host: finan.receberbemevinhos.com.br ou IP do servidor\n"
                 "Porta: 5432\n"
                 "Database: financeiro\n"
                 "User: financeiro_user",
            justify=tk.LEFT,
            font=('Consolas', 8)
        ).pack(anchor=tk.W)

        # Frame de botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            btn_frame,
            text="✓ Salvar Configuração",
            command=self.salvar_configuracao
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="🔌 Testar Conexão",
            command=self.testar_conexao
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self.root.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Status
        self.status_label = ttk.Label(main_frame, text="", foreground="blue")
        self.status_label.pack(pady=5)

    def on_modo_changed(self):
        """Habilita/desabilita campos baseado no modo"""
        modo = self.modo_var.get()

        if modo == "local":
            # Desabilitar campos remotos
            for widget in self.remote_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.config(state='disabled')
        else:
            # Habilitar campos remotos
            for widget in self.remote_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.config(state='normal')

    def toggle_password(self):
        """Mostra/esconde a senha"""
        for widget in self.remote_frame.winfo_children():
            if isinstance(widget, ttk.Entry) and widget.cget('textvariable') == str(self.password_var):
                if self.show_password_var.get():
                    widget.config(show="")
                else:
                    widget.config(show="*")

    def carregar_configuracao(self):
        """Carrega configuração salva"""
        try:
            # Tentar carregar do banco de dados
            if os.path.exists(self.desktop_db):
                conn = sqlite3.connect(self.desktop_db)
                cursor = conn.cursor()

                # Buscar configurações
                configs = {
                    'sync_mode': 'local',
                    'remote_host': '',
                    'remote_port': '5432',
                    'remote_database': 'financeiro',
                    'remote_user': 'financeiro_user',
                    'remote_password': ''
                }

                for chave in configs.keys():
                    try:
                        cursor.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
                        res = cursor.fetchone()
                        if res:
                            configs[chave] = res[0]
                    except:
                        pass

                conn.close()

                # Aplicar configurações
                self.modo_var.set(configs['sync_mode'])
                self.host_var.set(configs['remote_host'])
                self.porta_var.set(configs['remote_port'])
                self.database_var.set(configs['remote_database'])
                self.user_var.set(configs['remote_user'])
                self.password_var.set(configs['remote_password'])

                self.on_modo_changed()

        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")

    def salvar_configuracao(self):
        """Salva a configuração"""
        try:
            modo = self.modo_var.get()

            # Validar campos se for remoto
            if modo == "remoto":
                if not self.host_var.get():
                    messagebox.showerror("Erro", "Informe o host do servidor!")
                    return
                if not self.user_var.get():
                    messagebox.showerror("Erro", "Informe o usuário do banco!")
                    return
                if not self.password_var.get():
                    messagebox.showerror("Erro", "Informe a senha do banco!")
                    return

            # Salvar no banco de dados
            conn = sqlite3.connect(self.desktop_db)
            cursor = conn.cursor()

            # Criar tabela se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT
                )
            """)

            # Salvar configurações
            configs = {
                'sync_mode': modo,
                'remote_host': self.host_var.get(),
                'remote_port': self.porta_var.get(),
                'remote_database': self.database_var.get(),
                'remote_user': self.user_var.get(),
                'remote_password': self.password_var.get()
            }

            for chave, valor in configs.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)",
                    (chave, valor)
                )

            conn.commit()
            conn.close()

            # Atualizar .env se existir
            self.atualizar_env(modo, configs)

            self.status_label.config(text="✓ Configuração salva com sucesso!", foreground="green")
            messagebox.showinfo(
                "Sucesso",
                "Configuração salva com sucesso!\n\n"
                "Agora você pode usar a função de sincronização\n"
                "no menu Arquivo → Sincronizar Bancos"
            )

        except Exception as e:
            self.status_label.config(text=f"✗ Erro: {e}", foreground="red")
            messagebox.showerror("Erro", f"Erro ao salvar configuração:\n{e}")

    def atualizar_env(self, modo, configs):
        """Atualiza o arquivo .env com a configuração"""
        try:
            if modo == "remoto":
                database_url = (
                    f"postgresql://{configs['remote_user']}:{configs['remote_password']}"
                    f"@{configs['remote_host']}:{configs['remote_port']}/{configs['remote_database']}"
                )

                # Ler .env atual
                env_content = ""
                if os.path.exists(self.env_file):
                    with open(self.env_file, 'r') as f:
                        env_content = f.read()

                # Atualizar ou adicionar DATABASE_URL
                lines = env_content.split('\n')
                found = False
                for i, line in enumerate(lines):
                    if line.startswith('DATABASE_URL='):
                        lines[i] = f'DATABASE_URL={database_url}'
                        found = True
                        break

                if not found:
                    lines.append(f'DATABASE_URL={database_url}')

                # Salvar
                with open(self.env_file, 'w') as f:
                    f.write('\n'.join(lines))

        except Exception as e:
            print(f"Aviso: Não foi possível atualizar .env: {e}")

    def testar_conexao(self):
        """Testa a conexão com o servidor"""
        modo = self.modo_var.get()

        if modo == "local":
            messagebox.showinfo("Teste de Conexão", "Modo local não requer teste de conexão remota.")
            return

        # Validar campos
        if not self.host_var.get():
            messagebox.showerror("Erro", "Informe o host do servidor!")
            return
        if not self.user_var.get() or not self.password_var.get():
            messagebox.showerror("Erro", "Informe usuário e senha!")
            return

        self.status_label.config(text="Testando conexão...", foreground="blue")
        self.root.update()

        try:
            import psycopg2

            database_url = (
                f"postgresql://{self.user_var.get()}:{self.password_var.get()}"
                f"@{self.host_var.get()}:{self.porta_var.get()}/{self.database_var.get()}"
            )

            # Tentar conectar com timeout
            conn = psycopg2.connect(database_url, connect_timeout=10)
            cursor = conn.cursor()

            # Testar query simples
            cursor.execute("SELECT COUNT(*) FROM despesas")
            count = cursor.fetchone()[0]

            conn.close()

            self.status_label.config(
                text=f"✓ Conexão bem-sucedida! ({count} despesas encontradas)",
                foreground="green"
            )
            messagebox.showinfo(
                "Sucesso",
                f"Conexão estabelecida com sucesso!\n\n"
                f"Banco de dados: {self.database_var.get()}\n"
                f"Total de despesas: {count}"
            )

        except ModuleNotFoundError:
            self.status_label.config(text="✗ Módulo psycopg2 não instalado", foreground="red")
            messagebox.showerror(
                "Erro",
                "O módulo 'psycopg2' não está instalado.\n\n"
                "Instale com: pip install psycopg2-binary"
            )
        except Exception as e:
            self.status_label.config(text=f"✗ Erro de conexão: {str(e)[:50]}...", foreground="red")
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor:\n\n{e}")


def abrir_configurador(parent=None):
    """Função para abrir o configurador"""
    ConfiguradorSyncRemoto(parent)


if __name__ == "__main__":
    app = ConfiguradorSyncRemoto()
    app.root.mainloop()
