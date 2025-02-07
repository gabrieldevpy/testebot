import logging
import json
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext
)
import functions_framework

# Configuração do logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Arquivo para persistência
COURSES_FILE = "cursos.json"

def load_courses():
    try:
        with open(COURSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_courses(courses):
    with open(COURSES_FILE, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=4)

# Carrega cursos ao iniciar
courses = load_courses()

# Estados para o ConversationHandler de adicionar curso
AD_NOME, AD_AREA, AD_LINK = range(3)
# Estados para editar curso
ED_NOME, ED_CAMPO, ED_VALOR = range(3, 6)
# Estado para apagar curso (apenas nome)
AP_NOME = 6

# Função para iniciar o bot via HTTP (Firebase Function)
@functions_framework.http
def telegram_bot(request):
    app = Application.builder().token("SEU_TOKEN_DO_BOT_AQUI").build()

    # Funções de resposta (como o /start) e outros handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("listar_cursos", list_courses))
    app.add_handler(CommandHandler("curso", get_course_link))

    # ConversationHandlers para manipular adição, edição e exclusão de cursos
    app.add_handler(add_conv)
    app.add_handler(edit_conv)
    app.add_handler(del_conv)

    # Recebe e processa a requisição do Telegram
    app.run_polling()  # Não é o ideal, mas vamos rodar isso para o Firebase até o limite.

    return "OK", 200  # Retorna resposta para o Firebase Functions

# --- Funções do Bot (como /start, /listar_cursos, etc) ---
async def start(update: Update, context: CallbackContext):
    msg = (
        "👋 Olá! Eu sou o bot de cursos. Comandos disponíveis:\n"
        "/adicionar_curso - Adicionar um novo curso\n"
        "/listar_cursos - Listar todos os cursos\n"
        "/curso <nome> - Consultar o link de um curso\n"
        "/editar_curso - Editar um curso\n"
        "/apagar_curso - Apagar um curso\n"
        "/cancelar - Cancelar a operação"
    )
    await update.message.reply_text(msg)

# --- Adicionar Curso ---
async def add_course_start(update: Update, context: CallbackContext):
    await update.message.reply_text("🔹 Qual é o nome do curso que deseja adicionar?")
    return AD_NOME

async def add_course_nome(update: Update, context: CallbackContext):
    nome = update.message.text.strip()
    if not nome:
        await update.message.reply_text("❗ Nome inválido. Tente novamente.")
        return AD_NOME
    context.user_data["add_nome"] = nome
    await update.message.reply_text(
        "🔹 Qual é a área do curso? Digite uma das opções:\n"
        "humanas, matematica, ciencias da natureza, redacao, linguagens"
    )
    return AD_AREA

async def add_course_area(update: Update, context: CallbackContext):
    area = update.message.text.strip().lower()
    if area not in ["humanas", "matematica", "ciencias da natureza", "redacao", "linguagens"]:
        await update.message.reply_text("❗ Área inválida. Tente novamente.")
        return AD_AREA
    context.user_data["add_area"] = area
    await update.message.reply_text("🔹 Agora, envie o link do curso:")
    return AD_LINK

async def add_course_link(update: Update, context: CallbackContext):
    link = update.message.text.strip()
    nome = context.user_data["add_nome"]
    area = context.user_data["add_area"]
    courses[nome] = {"area": area, "link": link}
    save_courses(courses)
    await update.message.reply_text(
        f"✅ Curso '{nome}' da área '{area}' adicionado com sucesso!\n"
        "Use /listar_cursos para ver os cursos."
    )
    return ConversationHandler.END

# --- Listar Cursos ---
async def list_courses(update: Update, context: CallbackContext):
    if not courses:
        await update.message.reply_text("❗ Nenhum curso cadastrado.")
        return
    msg = "📚 Cursos disponíveis:\n"
    grouped = {}
    for nome, info in courses.items():
        area = info["area"]
        grouped.setdefault(area, []).append(nome)
    for area, nomes in grouped.items():
        msg += f"\n🔸 {area.capitalize()}:\n"
        for nome in nomes:
            msg += f"  - {nome}\n"
    msg += "\nPara consultar o link, use: /curso <nome do curso>"
    await update.message.reply_text(msg)

# --- Consultar Link do Curso ---
async def get_course_link(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("❗ Uso: /curso <nome do curso>")
        return
    nome = " ".join(context.args).strip()
    if nome in courses:
        link = courses[nome]["link"]
        await update.message.reply_text(f"🔗 Link do curso '{nome}': {link}")
    else:
        await update.message.reply_text(f"❗ Curso '{nome}' não encontrado.")
