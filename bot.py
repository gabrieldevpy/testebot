from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Dicionário para armazenar cursos (nome: link)
cursos = {}

# Função para adicionar um curso
def adicionar_curso(update: Update, context: CallbackContext) -> None:
    if len(context.args) >= 2:
        nome_curso = context.args[0]
        link_curso = " ".join(context.args[1:])
        cursos[nome_curso] = link_curso
        update.message.reply_text(f"Curso {nome_curso} adicionado com sucesso!")
    else:
        update.message.reply_text("Uso correto: /adicionar_curso <nome_do_curso> <link_do_curso>")

# Função para listar os cursos
def listar_cursos(update: Update, context: CallbackContext) -> None:
    if cursos:
        lista_cursos = "\n".join([f"{nome}: {link}" for nome, link in cursos.items()])
        update.message.reply_text(f"Cursos disponíveis:\n{lista_cursos}")
    else:
        update.message.reply_text("Nenhum curso disponível no momento.")

# Função para o comando /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Olá! Envie o comando /adicionar_curso <nome_do_curso> <link_do_curso> para adicionar cursos ou /listar_cursos para ver os cursos disponíveis.")

def main() -> None:
    # Token do bot (substitua com o seu)
    bot_token = "SEU_TOKEN_AQUI"

    # Criação do Updater e do Dispatcher
    updater = Updater(bot_token)

    # Adiciona os comandos
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("adicionar_curso", adicionar_curso))
    dispatcher.add_handler(CommandHandler("listar_cursos", listar_cursos))

    # Inicia o bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
