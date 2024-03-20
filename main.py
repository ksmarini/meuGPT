"""Importa os módulos necessários para o funcionamento do chatbot.

Módulos importados:
- re: Módulo para operações com expressões regulares.
- pickle: Módulo para serialização e desserialização de objetos Python.
- pathlib.Path: Classe para manipulação de caminhos de arquivos e diretórios.
- unidecode: Função para remover acentos de caracteres Unicode.
- openai: Módulo para interação com a API da OpenAI.
- streamlit: Módulo para criação de aplicativos web interativos.

"""
import re
import pickle
from pathlib import Path
from unidecode import unidecode
import openai
import streamlit as st


PASTA_CONFIGURACOES = Path(__file__).parent / 'configuracoes'
PASTA_CONFIGURACOES.mkdir(exist_ok=True)
PASTA_MENSAGENS = Path(__file__).parent / 'mensagens'
PASTA_MENSAGENS.mkdir(exist_ok=True)
CACHE_DESCONVERTE = {}


def chat_openai(api_key, mensagens, modelo='gpt-3.5-turbo', temperatura=0.5, stream=False):
    """
    Esta função cria uma sessão de chat com a API OpenAI usando a chave da API fornecida.

    Args:
        - api_key (str): A chave da API para a OpenAI.
        - mensagens (list): Uma lista de mensagens para enviar para a API. Cada mensagem
        é um dicionário com uma chave 'role' que pode ser 'system', 'user' ou 'assistant',
        e uma chave 'content' com o conteúdo da mensagem.
        - modelo (str, optional): O modelo da OpenAI a ser usado. Por padrão é 'gpt-3.5-turbo'.
        - temperatura (float, optional): O valor da temperatura afeta a aleatoriedade
        das respostas da API. Um valor maior significa respostas mais aleatórias,
        um valor menor significa respostas mais determinísticas. Por padrão é 0.5.
        - stream (bool, optional): Se definido como True,
        a API retornará as respostas como um stream. Por padrão é False.

    Returns:
        openai.ChatCompletion: O objeto de resposta da API.
    """
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=modelo,
        messages=mensagens,
        temperature=temperatura,
        stream=stream,
    )
    return response


def salva_chave(chave):
    """
    Salva a chave fornecida em um arquivo na pasta de configurações.

    Args:
        chave: A chave a ser salva no arquivo.

    Raises:
        OSError: Se ocorrer um erro ao acessar ou escrever no arquivo.
        pickle.PicklingError: Se ocorrer um erro ao serializar a chave.

    Returns:
        None
    """
    try:
        with open(PASTA_CONFIGURACOES / 'chave', 'wb') as f:
            pickle.dump(chave, f)
            print("Chave salva com sucesso")
    except (OSError, pickle.PicklingError) as e:
        print(f"Erro ao salvar a chave: {e}")


def le_chave():
    """
    Função que lê uma chave de um arquivo na pasta de configurações, se existir.

    Returns:
        str: A chave lida do arquivo, ou uma string vazia se o arquivo não existir.
    """
    if (PASTA_CONFIGURACOES / 'chave').exists():
        with open(PASTA_CONFIGURACOES / 'chave', 'rb') as f:
            return pickle.load(f)
    else:
        return ''


def converte_nome_mensagem(nome_mensagem):
    """Converte o nome da mensagem para um formato adequado para o nome do arquivo.

    Args:
        nome_mensagem (str): O nome da mensagem a ser convertido.

    Returns:
        str: Uma string representando o nome convertido para ser usado como nome de arquivo.

    Descrição:
        - Remove acentos e caracteres especiais.
        - Converte para letras minúsculas.
        - Remove espaços e caracteres não alfanuméricos.
    """
    if not nome_mensagem:
        raise ValueError("O nome da mensagem não pode ser vazio.")

    # Remove acentos usando unidecode
    nome_arquivo = unidecode(nome_mensagem)

    # Remove todos os caracteres não alfanuméricos (incluindo espaços) e converte para minúsculas
    nome_arquivo = re.sub(r'\W+', '', nome_arquivo).lower()

    return nome_arquivo


def retorna_nome_da_mensagem(mensagens):
    """
    Retorna os primeiros 30 caracteres do conteúdo da primeira mensagem de um usuário.

    Args:
        mensagens (list of dict): Uma lista de dicionários,
        onde cada dicionário representa uma mensagem.

    Returns:
        str: Os primeiros 30 caracteres do conteúdo da primeira mensagem de um usuário,
        ou uma string vazia se não houver mensagens de usuário.
    """
    # Usando next com uma expressão geradora para encontrar a primeira mensagem de um usuário
    nome_mensagem = next(
        (mensagem.get('content', '')[:30] for mensagem in mensagens
         if mensagem.get('role') == 'user'), '')
    return nome_mensagem


def salvar_mensagens(mensagens):
    """Salva o histórico das mensagens.

    Args:
        mensagens (list): Lista de dicionários contendo as mensagens.

    Returns:
        bool: True se a mensagem foi salva com sucesso, False caso contrário.
    """
    if not mensagens:
        print("Nenhuma mensagem para salvar.")
        return False

    nome_mensagem = retorna_nome_da_mensagem(mensagens)
    if not nome_mensagem:
        print("Nenhuma mensagem de usuário encontrada.")
        return False

    nome_arquivo = converte_nome_mensagem(nome_mensagem)
    arquivo_salvar = {
        'nome_mensagem': nome_mensagem,
        'nome_arquivo': nome_arquivo,
        'mensagem': mensagens
    }

    # Certifica-se de que a pasta de mensagens existe
    PASTA_MENSAGENS.mkdir(parents=True, exist_ok=True)

    caminho_arquivo = PASTA_MENSAGENS / nome_arquivo
    try:
        with open(caminho_arquivo, 'wb') as f:
            pickle.dump(arquivo_salvar, f)
        # print(f"Mensagem salva com sucesso em {caminho_arquivo}")
        return True
    except (OSError, pickle.PicklingError) as e:
        print(f"Erro ao salvar a mensagem: {e}")
        return False


def ler_mensagem_por_nome_arquivo(nome_arquivo, key='mensagem'):
    """
    Função que lê um arquivo de mensagens em formato pickle e retorna
    o conteúdo associado à chave especificada.

    Args:
        - nome_arquivo (str): O nome do arquivo a ser lido.
        - key (str, optional): A chave associada ao conteúdo desejado no arquivo.
        Por padrão é 'mensagem'.

    Returns:
        object: O conteúdo associado à chave especificada no arquivo de mensagens.
    """
    with open(PASTA_MENSAGENS / nome_arquivo, 'rb') as f:
        conteudo_mensagens = pickle.load(f)
    return conteudo_mensagens[key]


def desconverte_nome_mensagem(nome_arquivo):
    """
    Função que desconverte o nome de um arquivo para o nome da mensagem associada,
    usando um cache para otimização.

    Args:
        nome_arquivo (str): O nome do arquivo a ser desconvertido para o nome da mensagem.

    Returns:
        str: O nome da mensagem associada ao arquivo.
    """
    if nome_arquivo not in CACHE_DESCONVERTE:
        nome_mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo, key='nome_mensagem')
        CACHE_DESCONVERTE[nome_arquivo] = nome_mensagem
    return CACHE_DESCONVERTE[nome_arquivo]


def ler_mensagens(mensagens, key='mensagem'):
    """
    Função que lê o conteúdo de mensagens de um arquivo pickle com base
    no nome da mensagem fornecido.

    Args:
        - mensagens (list): Lista de mensagens.
        - key (str, optional): A chave associada ao conteúdo desejado no arquivo.
        Por padrão é 'mensagem'.

    Returns:
        object: O conteúdo associado à chave especificada no arquivo de mensagens.

    Raises:
        FileNotFoundError: Se o arquivo especificado não for encontrado.
        pickle.UnpicklingError: Se ocorrer um erro ao processar o arquivo pickle.
        KeyError: Se a chave especificada não for encontrada no arquivo de mensagens.
    """
    if not mensagens:
        return []

    nome_mensagem = retorna_nome_da_mensagem(mensagens)
    if not nome_mensagem:
        return []

    nome_arquivo = converte_nome_mensagem(nome_mensagem)
    caminho_arquivo = PASTA_MENSAGENS / nome_arquivo

    try:
        with open(caminho_arquivo, 'rb') as f:
            conteudo_mensagens = pickle.load(f)
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        print(f"Erro ao abrir ou processar o arquivo: {e}")
        return []

    if key not in conteudo_mensagens:
        raise KeyError(f"Chave '{key}' não encontrada no arquivo de mensagens.")

    return conteudo_mensagens[key]


def listar_conversas():
    """
    Função que lista as conversas disponíveis na pasta de mensagens,
    ordenadas por data de modificação.

    Returns:
        list: Lista dos nomes das conversas ordenadas por data de modificação.
    """
    conversas = list(PASTA_MENSAGENS.glob('*'))
    conversas = sorted(conversas, key=lambda item: item.stat().st_mtime_ns, reverse=True)
    return [c.stem for c in conversas]


def seleciona_conversa(nome_arquivo):
    """
    Limpa a lista de mensagens no estado da sessão
    se nenhum nome de conversa é fornecido.

    Esta função verifica se um nome de conversa não é fornecido
    (ou seja, uma string vazia ou um valor que avalia como False).
    Se nenhum nome é fornecido, a função redefine a lista de mensagens
    no estado da sessão para uma lista vazia. Isso pode
    ser utilizado para limpar as mensagens da interface do usuário em situações
    onde uma conversa é desselecionada ou quando
    se deseja resetar a visualização de mensagens sem selecionar uma nova conversa.

    Parâmetros:
    - nome_conversa (str): O nome da conversa. Se nenhum nome é fornecido
    (string vazia ou valor False), as mensagens serão limpas.

    Retorna:
    - None: A função não retorna nenhum valor, mas modifica o estado da sessão
    ao limpar a lista de mensagens.

    Exemplo de uso:
    >>> seleciona_conversa('')
    # Isso limpará as mensagens no estado da sessão, útil para resetar a visualização
    de mensagens quando nenhuma conversa está selecionada.
    """
    if not nome_arquivo:
        st.session_state['mensagens'] = []
    else:
        mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo, key='mensagem')
        st.session_state['mensagens'] = mensagem
    st.session_state['conversa_atual'] = nome_arquivo


def tab_conversas(tab):
    """
    Função que gera uma aba com botões de conversas existentes
    e um botão para criar uma nova conversa.

    Args:
        tab: Objeto de aba do Streamlit.

    """
    tab.button(
        '➕ Nova Conversa', on_click=seleciona_conversa, args=('', ), use_container_width=True
    )
    tab.markdown('')

    conversas = listar_conversas()
    for nome_arquivo in conversas:
        nome_mensagem = desconverte_nome_mensagem(nome_arquivo).capitalize()
        if len(nome_mensagem) > 29:
            nome_mensagem += '...'
        tab.button(desconverte_nome_mensagem(nome_arquivo).capitalize(),
                   on_click=seleciona_conversa,
                   args=(nome_arquivo,),
                   disabled=nome_arquivo==st.session_state['conversa_atual'],
                   use_container_width=True
        )


def tab_configuracoes(tab):
    """
    Função que gera uma aba de configurações com opções para selecionar
    o modelo e adicionar a API key.

    Args:
        tab: Objeto de aba do Streamlit.
    """
    modelo_escolhido = tab.selectbox('Selecione o modelo',
                                     ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview'])
    st.session_state['modelo'] = modelo_escolhido

    temperatura_gpt = tab.slider('Temperatura do ChatGPT',
                                        min_value=0.1,
                                        max_value=1.0,
                                        value=0.5,
                                        step=0.1)
    st.session_state['temperatura_gpt'] = temperatura_gpt

    chave = tab.text_input('Adicione sua API key', value=st.session_state['api_key'])
    if chave != st.session_state['api_key']:
        st.session_state['api_key'] = chave
        salva_chave(chave)
        tab.success('Chave salva com sucesso')


def inicializacao():
    """
    Função que inicializa as variáveis de estado da sessão do Streamlit, se necessário.

    Não possui parâmetros de entrada nem retorna valores.
    """
    if 'temperatura_gpt' not in st.session_state:
        st.session_state.temperatura_gpt = 0.5
    if 'mensagens' not in st.session_state:
        st.session_state.mensagens = []
    if 'conversa_atual' not in st.session_state:
        st.session_state.conversa_atual = ''
    if 'modelo' not in st.session_state:
        st.session_state.modelo = 'gpt-3.5-turbo'
    if 'api_key' not in st.session_state:
        st.session_state.api_key = le_chave()


def pagina_principal():
    """
    Função que exibe a página principal do chatbot, permitindo interação com
    o usuário e respostas do assistente.

    """
    mensagens = ler_mensagens(st.session_state['mensagens'])

    st.header('🤖 - Marini - Chatbot', divider=True)

    for mensagem in mensagens:
        chat = st.chat_message(mensagem['role'])
        chat.markdown(mensagem['content'])

    prompt = st.chat_input('Fale com o chat')
    if prompt:
        nova_mensagem = {'role': 'user', 'content': prompt}
        chat = st.chat_message(nova_mensagem['role'])
        chat.markdown(nova_mensagem['content'])
        mensagens.append(nova_mensagem)

        chat = st.chat_message('assistant')
        placeholder = chat.empty()
        placeholder.markdown("▌")
        resposta_completa = ''
        respostas = chat_openai(st.session_state['api_key'],
                                mensagens,
                                modelo=st.session_state['modelo'],
                                temperatura=st.session_state['temperatura_gpt'],
                                stream=True)

        for resposta in respostas:
            if resposta.choices[0].delta.content:
                resposta_completa += resposta.choices[0].delta.content
            placeholder.markdown(resposta_completa + "▌")
        placeholder.markdown(resposta_completa)
        nova_mensagem = {'role': 'assistant', 'content': resposta_completa}
        mensagens.append(nova_mensagem)

        st.session_state['mensagens'] = mensagens
        salvar_mensagens(mensagens)


if __name__ == '__main__':
    inicializacao()
    pagina_principal()
    tab1, tab2 = st.sidebar.tabs(['Conversas', 'Configurações'])
    tab_conversas(tab1)
    tab_configuracoes(tab2)
