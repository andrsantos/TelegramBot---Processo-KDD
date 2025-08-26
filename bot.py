import os
import asyncio
import logging
import unicodedata
import httpx

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.bot import DefaultBotProperties

# --- CONFIGURAÇÃO BÁSICA DE LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- VARIÁVEIS DE AMBIENTE E CONSTANTES ---
# AQUI ESTÁ A CORREÇÃO PRINCIPAL: Lendo a variável de ambiente do Railway
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# !!! ATENÇÃO: Preencha as variáveis abaixo com seus valores reais !!!
# A URL da sua API no Hugging Face (ou onde quer que esteja)
HF_API_URL = "SUA_URL_DA_API_AQUI" 

# O mapeamento de linguagens que você usa na função padronizar_coluna
LINGUAGEM_MAP = {
    # Exemplo: 'JavaScript': 'javascript',
    # Preencha com seus dados...
}

# O mapeamento de bancos que você usa na função padronizar_coluna
BANCOS_MAP = {
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
    if not isinstance(valor_str, str):
        return valor_str
    
    valores_list = [v.strip() for v in valor_str.split(',')]
    padronizada_list = [mapeamento.get(v, v) for v in valores_list]
    return ','.join(sorted(list(set(padronizada_list))))

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto.lower()

# --- ESTADOS ATUALIZADOS ---
class Form(StatesGroup):
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
    builder = InlineKeyboardBuilder()
    
    for item in options:
        text = f"✅ {item}" if item in selected_items else item
        builder.button(text=text, callback_data=f"{prefix}_{item}")

    builder.adjust(2)
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
    await callback