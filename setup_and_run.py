import subprocess
import sys
import os

# Passo 1: Instalar as dependências
def install_requirements():
    # Cria o arquivo requirements.txt se ele não existir
    requirements_content = "python-telegram-bot"
    if not os.path.exists('requirements.txt'):
        with open('requirements.txt', 'w') as f:
            f.write(requirements_content)
    
    # Instala as dependências usando o pip
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# Passo 2: Rodar o bot
def run_bot():
    subprocess.check_call([sys.executable, 'bot.py'])

# Função principal
def main():
    install_requirements()  # Instala as dependências
    run_bot()  # Executa o bot

if __name__ == "__main__":
    main()
