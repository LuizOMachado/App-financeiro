import sqlite3
import logging
import os 

pasta_segura = os.environ.get("HOME", ".")
DB_NAME = os.path.join(pasta_segura, 'financeiro.db')
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - Banco de Dados - %(levelname)s - %(message)s')

def _get_connection():
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            
           
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracoes (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    meta_guardar REAL NOT NULL DEFAULT 0.0
                )
            ''')
            
            
            cursor.execute('''
                INSERT OR IGNORE INTO configuracoes (id, meta_guardar)
                VALUES (1, 0.0)
            ''')

            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    categoria TEXT CHECK(categoria IN ('Entrada Efetivada', 'Entrada Futura', 'Gasto Fixo', 'Gasto Variável')) NOT NULL,
                    data TEXT NOT NULL,
                    efetivada INTEGER NOT NULL DEFAULT 0
                )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erro ao inicializar tabelas: {e}")

def get_meta_guardar():
   
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT meta_guardar FROM configuracoes WHERE id = 1')
            result = cursor.fetchone()
            return result['meta_guardar'] if result else 0.0
    except sqlite3.Error as e:
        logging.error(f"Erro ao buscar meta a guardar: {e}")
        return 0.0

def set_meta_guardar(valor):
  
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE configuracoes 
                SET meta_guardar = ? 
                WHERE id = 1
            ''', (float(valor),))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erro ao definir meta a guardar: {e}")

def add_transacao(descricao, valor, categoria, data, efetivada):
  
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transacoes (descricao, valor, categoria, data, efetivada)
                VALUES (?, ?, ?, ?, ?)
            ''', (descricao, float(valor), categoria, data, int(efetivada)))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erro ao adicionar transação: {e}")

def delete_transacao(id_transacao):
  
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM transacoes WHERE id = ?', (id_transacao,))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erro ao deletar transação {id_transacao}: {e}")

def efetivar_transacao(id_transacao):
   
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transacoes 
                SET efetivada = 1,
                    categoria = CASE 
                        WHEN categoria = 'Entrada Futura' THEN 'Entrada Efetivada'
                        ELSE categoria 
                    END
                WHERE id = ?
            ''', (id_transacao,))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erro ao efetivar a transação {id_transacao}: {e}")

def get_transacoes_por_mes_ano(mes, ano):
   
    try:
        
        mes_str = str(mes).zfill(2)
        padrao_busca = f"{ano}-{mes_str}-%"
        
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transacoes 
                WHERE data LIKE ?
                ORDER BY data ASC
            ''', (padrao_busca,))
            
            
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Erro ao buscar transações referentes a {mes}/{ano}: {e}")
        return []


if __name__ == '__main__':
    create_tables()
    print("Banco de dados 'financeiro.db' criado/verificado com sucesso e pronto para uso.")