# kutt_api.py

import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Replace 'YOUR_API_KEY' with your actual Kutt.it API key
API_KEY = 'm4U0k9MV~mh_GHrRr1XPArq~YrORvQaWv2P6RlDa'
API_URL = "https://mundobiblico-kutt.7rzexr.easypanel.host/api/v2/links"

def shorten_link(url, custom_slug=None):
    """
    Encurta um link usando a API do Kutt.it.

    Args:
        url (str): A URL original a ser encurtada.
        custom_slug (str, opcional): Slug personalizado para a URL encurtada.

    Returns:
        tuple: (link_id, shortened_url, address) se bem-sucedido, caso contrário (None, None, None).
    """
    headers = {
        'X-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        'target': url
    }
    if custom_slug:
        data['customurl'] = custom_slug  # Parâmetro correto para slug personalizado

    try:
        response = requests.post(API_URL, json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        link_id = response_data.get('id')
        shortened_url = response_data.get('link')
        address = response_data.get('address')
        return link_id, shortened_url, address
    except requests.exceptions.HTTPError as http_err:
        error_message = response.json().get('error', response.text)
        print(f"Erro HTTP: {error_message}")
        return None, None, None
    except Exception as err:
        print(f"Erro: {err}")
        return None, None, None

def get_link_stats(link_id):
    """
    Obtém estatísticas de cliques para um link encurtado.

    Args:
        link_id (str): O ID do link no Kutt.it.

    Returns:
        int ou str: Número de cliques ou 'N/A' se não disponível.
    """
    headers = {
        'X-API-KEY': API_KEY
    }
    stats_url = f"{API_URL}/{link_id}/stats"

    try:
        response = requests.get(stats_url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        visit_count = response_data.get('visit_count', 0)
        return visit_count
    except:
        return 'N/A'

def delete_link_api(link_id):
    """
    Exclui um link encurtado via API do Kutt.it.

    Args:
        link_id (str): O ID do link no Kutt.it.

    Returns:
        bool: True se a exclusão for bem-sucedida, False caso contrário.
    """
    headers = {
        'X-API-KEY': API_KEY
    }
    delete_url = f"{API_URL}/{link_id}"

    try:
        response = requests.delete(delete_url, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as http_err:
        error_message = response.json().get('error', response.text)
        print(f"Erro HTTP: {error_message}")
        return False
    except Exception as err:
        print(f"Erro: {err}")
        return False

def update_link_api(link_id, new_target, new_address):
    """
    Atualiza um link encurtado via API do Kutt.it.

    Args:
        link_id (str): O ID do link no Kutt.it.
        new_target (str): A nova URL de destino.
        new_address (str): O novo slug personalizado.

    Returns:
        bool: True se a atualização for bem-sucedida, False caso contrário.
    """
    headers = {
        'X-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    update_url = f"{API_URL}/{link_id}"
    data = {
        'target': new_target,
        'address': new_address  # Parâmetro necessário ao atualizar
    }

    try:
        response = requests.patch(update_url, json=data, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as http_err:
        error_message = response.json().get('error', response.text)
        print(f"Erro HTTP: {error_message}")
        return False
    except Exception as err:
        print(f"Erro: {err}")
        return False

def get_all_links_from_kutt():
    """
    Obtém todos os links encurtados da conta no Kutt.it.

    Returns:
        list: Uma lista de dicionários de links.
    """
    headers = {
        'X-API-KEY': API_KEY
    }
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.HTTPError as http_err:
        error_message = response.json().get('error', response.text)
        print(f"Erro HTTP: {error_message}")
        return []
    except Exception as err:
        print(f"Erro: {err}")
        return []
    
def get_clicks_over_time(link_id):
    """
    Obtém o número de cliques por dia nos últimos 7 dias para um link.

    Args:
        link_id (str): O ID do link no Kutt.it.

    Returns:
        dict: Um dicionário com datas como chaves e número de cliques como valores.
    """
    headers = {
        'X-API-KEY': API_KEY
    }
    stats_url = f"{API_URL}/{link_id}/stats"

    try:
        response = requests.get(stats_url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        # Extrair os dados de visualizações diárias
        last_week_stats = response_data.get('last_week', {})
        clicks_data = {}
        for day_data in last_week_stats:
            date_str = day_data.get('date')
            clicks = day_data.get('count', 0)
            clicks_data[date_str] = clicks
        return clicks_data
    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        return {}
