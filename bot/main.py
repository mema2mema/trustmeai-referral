# Shim entry so 'python -m bot.main' or 'python bot/main.py' works
from bot_main import main

if __name__ == "__main__":
    main()
