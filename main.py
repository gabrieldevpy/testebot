import logging
import json
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext
)
from firebase_functions import https

# Configuração do logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Iniciar o Firebase Admin SDK
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred)
db = firestore.client()

# Configuração do bot
COURSES_COLLECTION = "courses"

# Funções Firebase para persistir dados no Firestore
def load_courses():
    courses_ref = db.collection(COURSES_COLLECTION)
    docs = courses_ref.stream()
    courses = {}
    for doc in docs:
        courses[doc.id] = doc.to_dict()
    return courses

def save_courses(courses):
    courses_ref = db.collection(COURSES_COLLECTION)
    for name, info in courses.items():
        courses_ref.document(name).set(info)

# --- Conversa com o Bot ---
AD_NOME, AD_AREA, AD_LINK = range(3)
ED_NOME, ED_CAMPO, ED_VALOR = range(3, 6)
AP_NOME = 6

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
    courses = load_courses()
    courses[nome] = {"area": area, "link": link}
    save_courses(courses)
    await update.message.reply_text(
        f"✅ Curso '{nome}' da área '{area}' adicionado com sucesso!\n"
        "Use /listar_cursos para ver os cursos."
    )
    return ConversationHandler.END

# --- Listar Cursos ---
async def list_courses(update: Update, context: CallbackContext):
    courses = load_courses()
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

# Função principal para o bot
def main():
    bot_token = "7990357492:AAHLaFLgCg7FBxZh5VoJwqMaIadyS7bp8Tc"  # Substitua pelo token do seu bot

    application = Application.builder().token(bot_token).build()

    # Definindo handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("listar_cursos", list_courses))

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("adicionar_curso", add_course_start)],
        states={
            AD_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_nome)],
            AD_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_area)],
            AD_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_link)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)]
    ))

    application.run_polling()

# Função Firebase para iniciar o bot no Firebase Functions
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("🚫 Operação cancelada.")
    return ConversationHandler.END

@https.on_request
def bot(request):
    main()
    return "Bot rodando"

