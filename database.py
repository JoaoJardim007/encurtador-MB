import sqlite3
from kutt_api import get_all_links_from_kutt

DATABASE_NAME = 'links.db'

def create_table():
    """
    Cria a tabela de links no banco de dados, se não existir.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id TEXT UNIQUE,
            address TEXT,
            target TEXT,
            shortened_url TEXT,
            utm_url TEXT,
            creation_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_link(link_id, address, target, shortened_url, utm_url, creation_date):
    """
    Insere um novo link no banco de dados.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO links 
        (link_id, address, target, shortened_url, utm_url, creation_date) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (link_id, address, target, shortened_url, utm_url, creation_date))
    conn.commit()
    conn.close()

def update_link_in_db(link_id, target, utm_url, address, shortened_url):
    """
    Atualiza um link existente no banco de dados, incluindo a URL encurtada.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE links SET 
            target = ?,
            utm_url = ?,
            address = ?,
            shortened_url = ?
        WHERE link_id = ?
    ''', (target, utm_url, address, shortened_url, link_id))
    conn.commit()
    conn.close()

def delete_link_from_db(link_id):
    """
    Exclui um link do banco de dados.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM links WHERE link_id = ?", (link_id,))
    conn.commit()
    conn.close()

def get_all_links():
    """
    Obtém todos os links do banco de dados.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT 
            id, link_id, address, target, shortened_url, utm_url, creation_date 
        FROM links
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def sync_links():
    """
    Sincroniza o banco de dados local com os links do Kutt.it.
    """
    kutt_links = get_all_links_from_kutt()
    if not kutt_links:
        return

    # Mapear os links do Kutt por link_id
    kutt_links_dict = {link['id']: link for link in kutt_links}

    # Obter links locais
    local_links = get_all_links()
    local_link_ids = {link[1] for link in local_links}  # link_id

    # Inserir ou atualizar links do Kutt no banco de dados local
    for link_id, kutt_link in kutt_links_dict.items():
        address = kutt_link.get('address')
        target = kutt_link.get('target')
        shortened_url = kutt_link.get('link')
        creation_date = kutt_link.get('created_at').split('T')[0]
        utm_url = target  # Supondo que o target inclua os parâmetros UTM

        insert_link(link_id, address, target, shortened_url, utm_url, creation_date)

    # Remover links locais que não estão no Kutt
    for local_link in local_links:
        if local_link[1] not in kutt_links_dict:
            delete_link_from_db(local_link[1])