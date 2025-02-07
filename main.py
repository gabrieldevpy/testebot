import os
import json
import logging

import firebase_admin
from firebase_admin import credentials, db

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext
)

# Configuração do logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inicializar o Firebase Admin usando as credenciais fornecidas na variável de ambiente FIREBASE_CONFIG
firebase_config = os.getenv("FIREBASE_CONFIG")
if not firebase_config:
    raise Exception("Variável de ambiente FIREBASE_CONFIG não configurada!")
cred = credentials.Certificate(json.loads(firebase_config))
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-project-id.firebaseio.com/'  # Substitua pela URL do seu Realtime Database
})

# Funções para persistência usando o Firebase Realtime Database
def load_courses():
    ref = db.reference('courses')
    courses = ref.get()
    if courses is None:
        return {}
    return courses

def save_courses(courses):
    ref = db.reference('courses')
    ref.set(courses)

# Removemos o uso do arquivo local; os dados serão sempre lidos do Firebase.

# Estados para o ConversationHandler de adicionar curso
AD_NOME, AD_AREA, AD_LINK = range(3)
# Estados para editar curso
ED_NOME, ED_CAMPO, ED_VALOR = range(3, 6)
# Estado para apagar curso (apenas nome)
AP_NOME = 6

# /start: Mostra o menu principal
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
    courses = load_courses()  # Carrega os cursos atuais do Firebase
    courses[nome] = {"area": area, "link": link}
    save_courses(courses)
    await update.message.reply_text(
        f"✅ Curso '{nome}' da área '{area}' adicionado com sucesso!\n"
        "Use /listar_cursos para ver os cursos."
    )
    return ConversationHandler.END

# --- Listar Cursos e Consultar Link ---

# /listar_cursos: Lista todos os cursos (agrupados por área)
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

# /curso: Retorna o link do curso (argumento obrigatório)
async def get_course_link(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("❗ Uso: /curso <nome do curso>")
        return
    courses = load_courses()
    nome = " ".join(context.args).strip()
    if nome in courses:
        link = courses[nome]["link"]
        await update.message.reply_text(f"🔗 Link do curso '{nome}': {link}")
    else:
        await update.message.reply_text(f"❗ Curso '{nome}' não encontrado.")

# --- Editar Curso ---

async def edit_course_start(update: Update, context: CallbackContext):
    courses = load_courses()
    if not courses:
        await update.message.reply_text("❗ Nenhum curso cadastrado para editar.")
        return ConversationHandler.END
    await update.message.reply_text("🔹 Envie o nome do curso que deseja editar:")
    return ED_NOME

async def edit_course_nome(update: Update, context: CallbackContext):
    courses = load_courses()
    nome = update.message.text.strip()
    if nome not in courses:
        await update.message.reply_text("❗ Curso não encontrado.")
        return ConversationHandler.END
    context.user_data["edit_nome"] = nome
    await update.message.reply_text(
        "🔹 O que deseja editar? Responda 'nome' para alterar o nome ou 'link' para alterar o link."
    )
    return ED_CAMPO

async def edit_course_field(update: Update, context: CallbackContext):
    field = update.message.text.strip().lower()
    if field not in ["nome", "link"]:
        await update.message.reply_text("❗ Opção inválida. Digite 'nome' ou 'link'.")
        return ED_CAMPO
    context.user_data["edit_field"] = field
    await update.message.reply_text(f"🔹 Envie o novo {field} para o curso:")
    return ED_VALOR

async def edit_course_value(update: Update, context: CallbackContext):
    new_val = update.message.text.strip()
    courses = load_courses()
    nome = context.user_data["edit_nome"]
    field = context.user_data["edit_field"]
    if field == "nome":
        courses[new_val] = courses.pop(nome)
        nome = new_val
    else:
        courses[nome][field] = new_val
    save_courses(courses)
    await update.message.reply_text(f"✅ Curso '{nome}' atualizado com sucesso!")
    return ConversationHandler.END

# --- Apagar Curso ---

async def delete_course_start(update: Update, context: CallbackContext):
    courses = load_courses()
    if not courses:
        await update.message.reply_text("❗ Nenhum curso cadastrado para apagar.")
        return ConversationHandler.END
    await update.message.reply_text("🔹 Envie o nome do curso que deseja apagar:")
    return AP_NOME

async def delete_course_confirm(update: Update, context: CallbackContext):
    courses = load_courses()
    nome = update.message.text.strip()
    if nome in courses:
        del courses[nome]
        save_courses(courses)
        await update.message.reply_text(f"✅ Curso '{nome}' apagado com sucesso!")
    else:
        await update.message.reply_text(f"❗ Curso '{nome}' não encontrado.")
    # Retorna ao menu principal (/start)
    await start(update, context)
    return ConversationHandler.END

# --- Cancelar ---
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("🚫 Operação cancelada.")
    return ConversationHandler.END

def main():
    # Obtém o token do bot a partir da variável de ambiente BOT_TOKEN
    bot_token = os.getenv("7990357492:AAHLaFLgCg7FBxZh5VoJwqMaIadyS7bp8Tc")
    if not bot_token:
        raise Exception("Variável de ambiente BOT_TOKEN não configurada!")
    app = Application.builder().token(bot_token).build()

    # ConversationHandler para adicionar curso
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("adicionar_curso", add_course_start)],
        states={
            AD_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_nome)],
            AD_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_area)],
            AD_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_link)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)]
    )

    # ConversationHandler para editar curso
    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("editar_curso", edit_course_start)],
        states={
            ED_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_course_nome)],
            ED_CAMPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_course_field)],
            ED_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_course_value)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)]
    )

    # ConversationHandler para apagar curso
    del_conv = ConversationHandler(
        entry_points=[CommandHandler("apagar_curso", delete_course_start)],
        states={
            AP_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_course_confirm)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("listar_cursos", list_courses))
    app.add_handler(CommandHandler("curso", get_course_link))
    app.add_handler(add_conv)
    app.add_handler(edit_conv)
    app.add_handler(del_conv)

    app.run_polling()

if __name__ == "__main__":
    main()
