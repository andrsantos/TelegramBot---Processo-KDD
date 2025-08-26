import logging
import httpx
import asyncio
import unicodedata

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONSTANTES ---
HF_API_URL = "https://andreyrsantos.app.n8n.cloud/webhook/b083795b-3671-4ec5-92d3-0e4952638003"
TELEGRAM_TOKEN = "8405385966:AAHJzRc3B83pJ2ipLkYbv1eSTJhBRdx5LBw" # Seu Token

# --- DICIONÁRIOS DE MAPEAMENTO PARA PADRONIZAÇÃO ---
LINGUAGEM_MAP = {
    'M Language': 'M',
    'Não utilizo': 'Nenhuma',
    'Nao atuo com pro...': 'Nenhuma',
    'Nenhum': 'Nenhuma',
    'Não uso': 'Nenhuma',
    'Nenhum desses': 'Nenhuma',
    'Nao utilizo': 'Nenhuma',
    'Softwares estatísti...': 'Softwares estatísticos',
    'SQL Postegres': 'SQL'
}

BANCOS_MAP = {
    'SQL SERVER': 'SQL',
    'MSSQL': 'SQL',
    'SQL Dbx': 'SQL',
    'Azure Data Lake': 'Microsoft Azure',
    'Azure Data lake': 'Microsoft Azure',
    'Azure SQL': 'Microsoft Azure',
    'Azure ADLS': 'Microsoft Azure',
    'Azure Synapse': 'Microsoft Azure',
    'Azure Storage Account': 'Microsoft Azure',
    'Azure': 'Microsoft Azure',
    'MS Azure': 'Microsoft Azure',
    'Google BigQuery': 'Google Cloud',
    'Google Big Query': 'Google Cloud',
    'Google Firestore': 'Google Cloud',
    'Google Cloud Storage': 'Google Cloud',
    'Bigtable': 'Google Cloud',
    'Amazon Aurora ou RDS': 'Amazon',
    'Amazon Athena': 'Amazon',
    'Amazon Redshift': 'Amazon',
    'S3': 'Amazon',
    'NENHUM': 'Nenhum/Outro',
    'interno': 'Nenhum/Outro',
    'Não utilizo.': 'Nenhum/Outro',
    'Não atuo ainda nisso': 'Nenhum/Outro',
    'Nao utilizo': 'Nenhum/Outro',
    'Nenhuma': 'Nenhum/Outro',
    'Não temos BD': 'Nenhum/Outro',
    'API': 'Nenhum/Outro',
    'não uso nenhum': 'Nenhum/Outro',
    'Não utilizo nenhum': 'Nenhum/Outro',
    'Nenhuma das respostas': 'Nenhum/Outro',
    'Nenhum dos listados': 'Nenhum/Outro',
    'Receita': 'Nenhum/Outro',
    'NÃO RECONHEÇO NENHUM': 'Nenhum/Outro',
    'Não atuo na área ainda': 'Nenhum/Outro',
    'Nao uso': 'Nenhum/Outro',
    'Nenhum desses': 'Nenhum/Outro',
    'Não trabalho com banco diretamente': 'Nenhum/Outro',
    'Base interna': 'Nenhum/Outro',
    'Dados geoespaciais': 'Nenhum/Outro',
    'Não possuímos um banco de dados.': 'Nenhum/Outro',
    'não utilizamos banco de dados': 'Nenhum/Outro',
    'Nenhum acima': 'Nenhum/Outro',
    'Outro': 'Nenhum/Outro',
    'OOO': 'Nenhum/Outro',
    'Não trabalho com base de dados.': 'Nenhum/Outro',
    'dados alternativos e dados internos da empresa': 'Nenhum/Outro',
    'Não uso BD no trabalho': 'Nenhum/Outro',
    'Nenhum dos citados acima': 'Nenhum/Outro',
    'nosso banco é no excel': 'Nenhum/Outro',
    'Não usamos': 'Nenhum/Outro',
    'Dados públicos externos': 'Nenhum/Outro',
    'Não sei': 'Nenhum/Outro',
    'Nda': 'Nenhum/Outro',
    'Nao atuo na area de tech na empresa ainda': 'Nenhum/Outro',
    'Não se aplica': 'Não se aplica',
    'Nenhum destes': 'Nenhum/Outro',
    'Nd': 'Nenhum/Outro',
    'Não utilizo bancos de dados.': 'Nenhum/Outro',
    'Fontes da empresa em html ou csv': 'Fontes não estruturadas',
    'Dados não estruturados': 'Fontes não estruturadas',
    'Dados internos': 'Fontes não estruturadas',
    'midias sociais': 'Fontes não estruturadas',
    'Bases Excel e csv extraídas direto no site': 'Excel',
    'B.O SAP': 'SAP',
    'SAP Business': 'SAP',
    'SAP ECC': 'SAP',
    'SAP HANA': 'SAP',
    'HANA': 'SAP'
}

FORMACAO_MAP = {
    "Engenharia/TI": "Computação / Engenharia de Software / Sistemas de Informação/ TI",
    "Estatística/Matemática": "Estatística/ Matemática / Matemática Computacional/ Ciências Atuariais",
    "Ciências Biológicas": "Ciências Biológicas/ Farmácia/ Medicina/ Área da Saúde",
    "Economia/Administração": "Economia/ Administração / Contabilidade / Finanças/ Negócios",
    "Ciências Sociais": "Ciências Sociais",
    "Outras engenharias": "Outras Engenharias",
    "Química/Física": "Química / Física",
    "Marketing/Publicação": "Marketing / Publicidade / Comunicação / Jornalismo",
    "Outra": "Outra opção"
}

# --- LISTA DE ESTADOS BRASILEIROS PARA VALIDAÇÃO ---
ESTADOS_BRASIL = [
    "Acre", "Alagoas", "Amapá", "Amazonas", "Bahia", "Ceará", "Distrito Federal",
    "Espírito Santo", "Goiás", "Maranhão", "Mato Grosso", "Mato Grosso do Sul",
    "Minas Gerais", "Pará", "Paraíba", "Paraná", "Pernambuco", "Piauí", "Rio de Janeiro",
    "Rio Grande do Norte", "Rio Grande do Sul", "Rondônia", "Roraima", "Santa Catarina",
    "São Paulo", "Sergipe", "Tocantins"
]

# --- LISTAS DE OPÇÕES ATUALIZADAS ---
OPCOES_LINGUAGENS = [
    "Python", "SQL", "R", "Java", "C/C++/C#", "Scala", "Go", "Julia", "Clojure",
    "Aql", "PySpark", "Spark", "VBA", "Dax", "javascript", "M", "Rust", "Elixir", "Nenhuma"
]

# Nova lista unificada de bancos de dados
OPCOES_BANCOS = [
    'Microsoft Azure', 'Google Cloud', 'Amazon', 'SAP',
    'SQL', 'MySQL', 'PostgreSQL', 'Oracle', 'SQLite', 'MariaDB', 'DB2', 'Sybase',
    'MongoDB', 'DynamoDB', 'Neo4J', 'Cassandra', 'Firebase', 'HBase',
    'Nenhum/Outro', 'Excel', 'Fontes não estruturadas', 'Access', 'API', 'ClickHouse', 
    'Databricks', 'Hadoop', 'Hive', 'Metabase', 'Redis', 'Snowflake', 'Splunk', 'Teradata', 'Outro'
]

OPCOES = {
    "cloud": ["AWS", "Google Cloud", "Microsoft Azure", "Outras"],
    "vive_no_brasil": ["Sim", "Não"],
    "nivel_ensino": ["Pós-graduação", "Graduação/Bacharelado", "Doutorado ou Phd", "Estudante de Graduação", "Mestrado", "Não tenho graduação formal"],
    "formacao": ["Ciências Biológicas", "Engenharia/TI", "Estatística/Matemática", "Economia/Administração", "Ciências Sociais", "Outras engenharias", "Química/Física", "Marketing/Publicação", "Outra"],
    "tempo_experiencia_dados": ["Menos de 1 ano", "De 1 a 2 anos", "De 2 a 3 anos", "De 3 a 5 anos", "Mais de 5 anos"]
}

# --- FUNÇÃO DE PADRONIZAÇÃO ---
def padronizar_coluna(valor_str, mapeamento):
    """
    Padroniza uma string de valores separados por vírgula usando um dicionário de mapeamento.
    """
    if not isinstance(valor_str, str):
        return valor_str
    
    valores_list = [v.strip() for v in valor_str.split(',')]
    padronizada_list = [mapeamento.get(v, v) for v in valores_list]
    return ','.join(sorted(list(set(padronizada_list))))

def normalizar_texto(texto):
    """Normaliza o texto, removendo acentos e convertendo para minúsculas."""
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto.lower()


# --- ESTADOS ATUALIZADOS ---
class Form(StatesGroup):
    """Representa os estados da conversa do usuário."""
    ask_age = State()
    ask_vive_no_brasil = State()
    ask_estado_moradia = State()
    ask_nivel_ensino = State()
    ask_formacao = State()
    ask_tempo_experiencia_dados = State()
    select_languages = State()
    select_databases = State()
    select_cloud = State()

# --- FUNÇÕES AUXILIARES ATUALIZADAS ---
def create_keyboard(options: list, selected_items: list, prefix: str) -> InlineKeyboardMarkup:
    """Cria o teclado de botões para listas."""
    builder = InlineKeyboardBuilder()
    
    for item in options:
        text = f"✅ {item}" if item in selected_items else item
        builder.button(text=text, callback_data=f"{prefix}_{item}")

    builder.adjust(2) # Ajuste para 2 botões por linha, mais compacto
    builder.row(InlineKeyboardButton(text="➡️ Próximo ➡️", callback_data="next"))
    
    return builder.as_markup()

# --- HANDLERS ATUALIZADOS ---

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await message.answer("Olá! Qual é sua idade?")
    await state.set_state(Form.ask_age)

@router.message(Form.ask_age, F.text)
async def ask_vive_no_brasil_handler(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        await message.answer("Por favor, digite apenas um número para a sua idade.")
        return

    await state.update_data(idade=int(message.text))
    
    keyboard = create_keyboard(OPCOES["vive_no_brasil"], [], "vive")
    await message.answer("Você mora no Brasil?", reply_markup=keyboard)
    await state.set_state(Form.ask_vive_no_brasil)


@router.callback_query(Form.ask_vive_no_brasil, F.data.startswith("vive_"))
async def handle_vive_no_brasil(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Opção selecionada!")
    
    vive_no_brasil = callback.data.split("_", 1)[1]
    await state.update_data(vive_no_brasil=vive_no_brasil)
    
    # Deleta a mensagem com o teclado anterior
    await callback.message.delete()
    
    if vive_no_brasil == "Sim":
        await callback.message.answer("Qual o seu estado de moradia?")
        await state.set_state(Form.ask_estado_moradia)
    else:
        # Pula a pergunta do estado e já vai para a próxima
        await state.update_data(estado_moradia="Não se aplica")
        
        keyboard = create_keyboard(OPCOES["nivel_ensino"], [], "ensino")
        await callback.message.answer("Qual o seu nível de ensino?", reply_markup=keyboard)
        await state.set_state(Form.ask_nivel_ensino)

@router.message(Form.ask_estado_moradia, F.text)
async def ask_nivel_ensino_handler(message: Message, state: FSMContext) -> None:
    normalized_input = normalizar_texto(message.text)
    
    # Valida se o estado digitado existe na lista de estados normalizada
    if normalized_input not in [normalizar_texto(e) for e in ESTADOS_BRASIL]:
        await message.answer("Estado inexistente. Verifique a grafia do seu estado.")
        return

    # Salva o estado com a grafia original (com acento e capitalizado)
    await state.update_data(estado_moradia=message.text)

    keyboard = create_keyboard(OPCOES["nivel_ensino"], [], "ensino")
    await message.answer("Qual o seu nível de ensino?", reply_markup=keyboard)
    await state.set_state(Form.ask_nivel_ensino)
    
    
@router.callback_query(Form.ask_nivel_ensino, F.data.startswith("ensino_"))
async def handle_nivel_ensino(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Opção selecionada!")
    
    nivel = callback.data.split("_", 1)[1]
    await state.update_data(nivel_ensino=nivel)
    
    # Deleta a mensagem com o teclado anterior
    await callback.message.delete()
    
    keyboard = create_keyboard(OPCOES["formacao"], [], "formacao")
    await callback.message.answer("Qual sua principal área de formação?", reply_markup=keyboard)
    await state.set_state(Form.ask_formacao)


@router.callback_query(Form.ask_formacao, F.data.startswith("formacao_"))
async def handle_formacao(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Opção selecionada!")
    
    formacao = callback.data.split("_", 1)[1]
    await state.update_data(formacao=formacao)
    
    # Deleta a mensagem com o teclado anterior
    await callback.message.delete()
    
    keyboard = create_keyboard(OPCOES["tempo_experiencia_dados"], [], "tempo")
    await callback.message.answer("Qual seu tempo de experiência na área de dados?", reply_markup=keyboard)
    await state.set_state(Form.ask_tempo_experiencia_dados)


@router.callback_query(Form.ask_tempo_experiencia_dados, F.data.startswith("tempo_"))
async def handle_tempo(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Opção selecionada!")
    
    tempo = callback.data.split("_", 1)[1]
    await state.update_data(tempo_experiencia_dados=tempo)
    
    # Deleta a mensagem com o teclado anterior
    await callback.message.delete()
    
    # MUDA O TECLADO PARA LINGUAGENS (AGORA AJUSTADO)
    keyboard = create_keyboard(OPCOES_LINGUAGENS, [], "lang")
    await callback.message.answer(
        "Escolha suas linguagens favoritas (você pode selecionar mais de uma):", 
        reply_markup=keyboard
    )
    await state.update_data(selected_languages=[])
    await state.set_state(Form.select_languages)


@router.callback_query(Form.select_languages, F.data.startswith("lang_"))
async def handle_language_selection(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    data = await state.get_data()
    selected_languages = data.get("selected_languages", [])
    
    lang_name = callback.data.split("_", 1)[1]
    
    if lang_name in selected_languages:
        selected_languages.remove(lang_name)
    else:
        selected_languages.append(lang_name)
    
    await state.update_data(selected_languages=selected_languages)
    new_keyboard = create_keyboard(OPCOES_LINGUAGENS, selected_languages, "lang")
    
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    

@router.callback_query(Form.select_languages, F.data == "next")
async def handle_next_from_languages(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Opção selecionada!")
    
    data = await state.get_data()
    selected_languages = data.get("selected_languages", [])
    
    if not selected_languages:
        await callback.answer("Você precisa escolher pelo menos uma linguagem.", show_alert=True)
        return

    # Passa para o próximo passo, com todos os bancos de uma vez
    keyboard = create_keyboard(OPCOES_BANCOS, [], "banco")
    await callback.message.edit_text(
        "Agora, escolha os bancos de dados que você utiliza:", 
        reply_markup=keyboard
    )
    await state.update_data(selected_databases=[])
    await state.set_state(Form.select_databases)


@router.callback_query(Form.select_databases, F.data.startswith("banco_"))
async def handle_database_selection(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    data = await state.get_data()
    selected_databases = data.get("selected_databases", [])

    db_name = callback.data.split("_", 1)[1]
    if db_name in selected_databases:
        selected_databases.remove(db_name)
    else:
        selected_databases.append(db_name)
    
    await state.update_data(selected_databases=selected_databases)
    new_keyboard = create_keyboard(OPCOES_BANCOS, selected_databases, "banco")
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)


@router.callback_query(Form.select_databases, F.data == "next")
async def handle_next_from_databases(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Opção selecionada!")
    
    data = await state.get_data()
    selected_databases = data.get("selected_databases", [])

    if not selected_databases:
        await callback.answer("Você precisa escolher pelo menos um banco de dados.", show_alert=True)
        return
    
    # Deleta a mensagem com o teclado anterior
    await callback.message.delete()
    
    # Passa para o próximo passo
    keyboard = create_keyboard(OPCOES["cloud"], [], "cloud")
    await callback.message.answer(
        "Qual a sua plataforma de nuvem preferida?",
        reply_markup=keyboard
    )
    await state.update_data(selected_cloud=[])
    await state.set_state(Form.select_cloud)

@router.callback_query(Form.select_cloud, F.data.startswith("cloud_"))
async def handle_cloud_selection(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    data = await state.get_data()
    selected_cloud = data.get("selected_cloud", [])

    cloud_name = callback.data.split("_", 1)[1]
    # Lógica para garantir que a escolha seja única
    selected_cloud = [cloud_name]
    
    await state.update_data(selected_cloud=selected_cloud)
    new_keyboard = create_keyboard(OPCOES["cloud"], selected_cloud, "cloud")
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)

@router.callback_query(Form.select_cloud, F.data == "next")
async def handle_next_from_cloud(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Opção selecionada!")
    
    data = await state.get_data()
    selected_cloud = data.get("selected_cloud", [])

    if not selected_cloud:
        await callback.answer("Você precisa escolher uma plataforma de nuvem.", show_alert=True)
        return
    
    # FIM DA CONVERSA - PREPARAÇÃO PARA A API
    await callback.message.edit_text("Processando sua solicitação... Isso pode levar um minuto.")
    
    # Recupera todos os dados coletados
    dados = await state.get_data()
    
    # Formata os dados de lista para string e aplica os mapeamentos
    linguagens_str = ", ".join(dados["selected_languages"])
    bancos_str = ", ".join(dados["selected_databases"])
    cloud_str = ", ".join(dados["selected_cloud"])
    formacao_mapeada = FORMACAO_MAP.get(dados["formacao"], dados["formacao"])
    
    # Cria o payload no formato esperado pela API
    payload = {
        "inputs": {
            "idade": dados["idade"],
            "linguagens_preferidas": padronizar_coluna(linguagens_str, LINGUAGEM_MAP),
            "bancos_de_dados": padronizar_coluna(bancos_str, BANCOS_MAP),
            "cloud_preferida": cloud_str,
            "vive_no_brasil": dados["vive_no_brasil"],
            "estado_moradia": dados["estado_moradia"],
            "nivel_ensino": dados["nivel_ensino"],
            "formacao": formacao_mapeada,
            "tempo_experiencia_dados": dados["tempo_experiencia_dados"]
        },
        "chatId": callback.message.chat.id
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(HF_API_URL, json=payload, timeout=60.0)
        response.raise_for_status()
        result = response.json()
        predicted_cargo = result.get("predicted_cargo", "Cargo não encontrado")
        
        # Deleta a mensagem de "Processando"
        await callback.message.delete()
        
        await callback.message.answer(
            f"Análise Concluída:\n\n"
            f"Sua idade: {dados['idade']}\n"
            f"Mora no Brasil: {dados['vive_no_brasil']}\n"
            f"Estado: {dados['estado_moradia']}\n"
            f"Nível de Ensino: {dados['nivel_ensino']}\n"
            f"Área de Formação: {formacao_mapeada}\n"
            f"Tempo de Exp. em Dados: {dados['tempo_experiencia_dados']}\n"
            f"Linguagens: {linguagens_str}\n"
            f"Bancos de Dados: {bancos_str}\n"
            f"Nuvem: {cloud_str}\n\n"
        )
    except Exception as e:
        logger.error(f"ERRO NA CHAMADA DA API: {e}")
        await callback.message.answer("Desculpe, ocorreu um erro ao consultar o serviço de previsão. Tente novamente mais tarde.")
    
    await state.clear()


# --- FUNÇÃO PRINCIPAL ---
async def main() -> None:
    dp = Dispatcher()
    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        logger.info("Iniciando o bot (aiogram)...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot desligado manualmente.")