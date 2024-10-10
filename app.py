# app.py

import streamlit as st
from datetime import datetime, timedelta
from kutt_api import (
    shorten_link,
    get_link_stats,
    delete_link_api,
    update_link_api,
    get_clicks_over_time  # Certifique-se de adicionar esta função ao kutt_api.py
)
from database import (
    create_table,
    insert_link,
    get_all_links,
    delete_link_from_db,
    update_link_in_db,
    sync_links
)
import re
import pandas as pd
import plotly.express as px
from urllib.parse import urlparse, parse_qs

# Inicializar a tabela e sincronizar os links
create_table()
sync_links()

# Configuração da página
st.set_page_config(
    page_title="Encurtador de Links com UTM",
    page_icon="🔗",
    layout="wide"
)

# CSS personalizado
st.markdown("""
    <style>
        /* Estilos personalizados */
        body {
            background-color: #f0f2f6;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        /* Ajustes para o cabeçalho */
        header {
            text-align: center;
        }
        /* Logo */
        .logo {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 200px;
        }
        /* Botão de download */
        .download-button {
            background-color: #008CBA;
            color: white;
        }
        .download-button:hover {
            background-color: #007bb5;
        }
    </style>
""", unsafe_allow_html=True)

# Adicionar logotipo
st.markdown("""
    <div style='text-align: center;'>
        <img src='https://pages.greatpages.com.br/lp.mundobiblico.com/1728478212/imagens/mobile/424273_1_17045703666599ae02ed082902047719.png' alt='Logo' class='logo'>
    </div>
""", unsafe_allow_html=True)

# Função para validar o slug
def is_valid_slug(slug):
    return re.match(r'^[a-zA-Z0-9\-_]+$', slug) is not None

# Título da aplicação
st.title("🔗 Encurtador de Links com UTM")

# Seção de geração de links
st.header("Gerar Link com UTM e Slug Personalizado")

with st.form(key='link_form'):
    base_url = st.text_input("URL Base (Obrigatório)", placeholder="https://exemplo.com")
    utm_source = st.text_input("UTM Source (Obrigatório)", placeholder="Google")
    utm_medium = st.text_input("UTM Medium (Obrigatório)", placeholder="Email")
    utm_campaign = st.text_input("UTM Campaign (Obrigatório)", placeholder="Campanha-2024")
    utm_content = st.text_input("UTM Content (Opcional)", placeholder="Banner")
    custom_slug = st.text_input("Slug Personalizado (Opcional)", placeholder="meu-slug")

    submit_button = st.form_submit_button(label='Gerar Link')

if submit_button:
    if base_url and utm_source and utm_medium and utm_campaign:
        # Validar o slug personalizado
        if custom_slug and not is_valid_slug(custom_slug):
            st.error("❌ O slug personalizado contém caracteres inválidos.")
        else:
            # Gerar a URL com parâmetros UTM
            utm_params = f"?utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}"
            if utm_content:
                utm_params += f"&utm_content={utm_content}"
            final_url = base_url + utm_params

            # Chamar a função para encurtar o link via API do Kutt
            link_id, shortened_url, address = shorten_link(final_url, custom_slug=custom_slug)

            if link_id and shortened_url:
                st.success(f"✅ Link gerado e encurtado: {shortened_url}")
                # Inserir no banco de dados
                insert_link(
                    link_id, address, base_url, shortened_url,
                    final_url, datetime.now().strftime("%Y-%m-%d")
                )
                # Atualizar a lista de links
                st.session_state['links_data'] = get_all_links()
            else:
                st.error("❌ Erro ao encurtar o link. Verifique se o slug já está em uso.")
    else:
        st.warning("⚠️ Por favor, preencha todos os campos obrigatórios.")

# Seção de gerenciamento de links
st.header("Gerenciar Links")

# Adicionar campos de filtro e pesquisa
with st.expander("🔍 Pesquisar e Filtrar Links"):
    search_query = st.text_input("Pesquisar por URL, slug ou campanha UTM")
    min_clicks = st.number_input("Número mínimo de cliques", min_value=0, value=0)
    max_clicks = st.number_input("Número máximo de cliques", min_value=0, value=1000000)
    apply_filters = st.button("Aplicar Filtros")

# Botão para exportar dados
if st.button("📥 Exportar Dados para CSV"):
    # Criar DataFrame com os dados dos links
    df_links = pd.DataFrame(st.session_state['links_data'], columns=[
        'ID', 'Link ID', 'Slug', 'URL Original', 'URL Encurtada', 'URL com UTM', 'Data de Criação'
    ])
    # Adicionar coluna de cliques
    df_links['Cliques'] = df_links['Link ID'].apply(get_link_stats)
    # Gerar CSV
    csv = df_links.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar CSV",
        data=csv,
        file_name='links.csv',
        mime='text/csv'
    )

# Carregar os links do banco de dados
if 'links_data' not in st.session_state:
    st.session_state['links_data'] = get_all_links()

links_data = st.session_state['links_data']

# Aplicar filtros se necessário
if apply_filters:
    filtered_links = []
    for link in st.session_state['links_data']:
        link_id_db, link_id_kutt, address, original_url, shortened_url, utm_url, creation_date = link
        clicks = get_link_stats(link_id_kutt)
        # Aplicar filtros
        if (search_query.lower() in original_url.lower() or
            search_query.lower() in address.lower() or
            search_query.lower() in utm_url.lower()):
            if min_clicks <= clicks <= max_clicks:
                filtered_links.append(link)
    links_data = filtered_links
else:
    links_data = st.session_state['links_data']

if links_data:
    for link in links_data:
        link_id_db, link_id_kutt, address, original_url, shortened_url, utm_url, creation_date = link
        clicks = get_link_stats(link_id_kutt)

        with st.expander(f"Link ID {link_id_db} - Criado em {creation_date}"):
            st.markdown(f"**URL Encurtada:** [{shortened_url}]({shortened_url})")
            st.markdown(f"**URL Original:** {original_url}")
            st.markdown(f"**URL com UTM:** {utm_url}")
            st.markdown(f"**Slug Personalizado:** {address}")
            st.markdown(f"**Total de Cliques:** {clicks}")

            # Obter dados de cliques
            clicks_over_time = get_clicks_over_time(link_id_kutt)
            if clicks_over_time:
                st.markdown("**Estatísticas de Cliques nos Últimos 7 Dias:**")
                dates = list(clicks_over_time.keys())
                clicks_list = list(clicks_over_time.values())

                # Criar DataFrame para o gráfico
                df_clicks = pd.DataFrame({
                    'Data': dates,
                    'Cliques': clicks_list
                })

                # Criar gráfico interativo com Plotly
                fig = px.bar(df_clicks, x='Data', y='Cliques', title='Cliques por Dia')
                fig.update_layout(xaxis_title='Data', yaxis_title='Número de Cliques')
                st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Editar", key=f"edit_{link_id_db}"):
                    st.session_state['edit_link'] = link
            with col2:
                if st.button("🗑️ Excluir", key=f"delete_{link_id_db}"):
                    st.session_state['delete_link'] = link

# Ação de edição na barra lateral
if 'edit_link' in st.session_state:
    st.sidebar.title("Editar Link")
    link_to_edit = st.session_state['edit_link']
    link_id_db, link_id_kutt, address, original_url, shortened_url, utm_url, creation_date = link_to_edit

    # Extrair parâmetros UTM da utm_url
    parsed_url = urlparse(utm_url)
    query_params = parse_qs(parsed_url.query)
    utm_source = query_params.get('utm_source', [''])[0]
    utm_medium = query_params.get('utm_medium', [''])[0]
    utm_campaign = query_params.get('utm_campaign', [''])[0]
    utm_content = query_params.get('utm_content', [''])[0]

    with st.sidebar.form(key='edit_form'):
        new_base_url = st.text_input("URL Base (Obrigatório)", value=original_url)
        new_utm_source = st.text_input("UTM Source (Obrigatório)", value=utm_source)
        new_utm_medium = st.text_input("UTM Medium (Obrigatório)", value=utm_medium)
        new_utm_campaign = st.text_input("UTM Campaign (Obrigatório)", value=utm_campaign)
        new_utm_content = st.text_input("UTM Content (Opcional)", value=utm_content)
        new_custom_slug = st.text_input("Slug Personalizado (Opcional)", value=address)
        submit_edit = st.form_submit_button(label='Atualizar Link')

    if submit_edit:
        if new_base_url and new_utm_source and new_utm_medium and new_utm_campaign:
            if new_custom_slug and not is_valid_slug(new_custom_slug):
                st.sidebar.error("❌ O slug personalizado contém caracteres inválidos.")
            else:
                utm_params = f"?utm_source={new_utm_source}&utm_medium={new_utm_medium}&utm_campaign={new_utm_campaign}"
                if new_utm_content:
                    utm_params += f"&utm_content={new_utm_content}"
                final_url = new_base_url + utm_params

                success = update_link_api(
                    link_id_kutt,
                    final_url,
                    new_custom_slug
                )
                if success:
                    # Recalcular o shortened_url com o novo slug
                    parsed_shortened_url = urlparse(shortened_url)
                    base_url_short = f"{parsed_shortened_url.scheme}://{parsed_shortened_url.netloc}"
                    new_shortened_url = f"{base_url_short}/{new_custom_slug}"

                    # Atualizar no banco de dados local
                    update_link_in_db(
                        link_id_kutt,
                        new_base_url,
                        final_url,
                        new_custom_slug,
                        new_shortened_url  # Passamos o novo shortened_url aqui
                    )

                    # Atualizar os dados na sessão
                    for idx, lnk in enumerate(st.session_state['links_data']):
                        if lnk[1] == link_id_kutt:
                            st.session_state['links_data'][idx] = (
                                link_id_db, link_id_kutt, new_custom_slug, new_base_url,
                                new_shortened_url, final_url, creation_date
                            )
                            break
                    st.sidebar.success("✅ Link atualizado com sucesso!")
                    # Remover o estado de edição
                    del st.session_state['edit_link']
                else:
                    st.sidebar.error("❌ Erro ao atualizar o link. Verifique se o slug já está em uso.")
        else:
            st.sidebar.warning("⚠️ Por favor, preencha todos os campos obrigatórios.")

    if st.sidebar.button("Cancelar"):
        del st.session_state['edit_link']

# Ação de exclusão na barra lateral
if 'delete_link' in st.session_state:
    st.sidebar.title("Excluir Link")
    link_to_delete = st.session_state['delete_link']
    link_id_db, link_id_kutt, address, original_url, shortened_url, utm_url, creation_date = link_to_delete

    st.sidebar.warning("Tem certeza que deseja excluir este link?", icon="⚠️")
    st.sidebar.markdown(f"**URL Encurtada:** [{shortened_url}]({shortened_url})")

    confirm_delete = st.sidebar.button("Confirmar Exclusão")
    cancel_delete = st.sidebar.button("Cancelar")

    if confirm_delete:
        success = delete_link_api(link_id_kutt)
        if success:
            delete_link_from_db(link_id_kutt)
            # Remover o link da sessão
            st.session_state['links_data'] = [lnk for lnk in st.session_state['links_data'] if lnk[1] != link_id_kutt]
            st.sidebar.success("✅ Link excluído com sucesso!")
            # Remover o estado de exclusão
            del st.session_state['delete_link']
        else:
            st.sidebar.error("❌ Falha ao excluir o link.")

    if cancel_delete:
        del st.session_state['delete_link']

# Rodapé
st.markdown("""
    <div style='text-align: center; color: #888888; margin-top: 2rem;'>
        Desenvolvido com ❤️ por Mundo Bíblico
    </div>
""", unsafe_allow_html=True)
