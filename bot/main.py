try:
    from .bot_main import main   # python -m bot.main
except Exception:
    from bot_main import main    # python bot/main.py

if __name__ == "__main__":
    main()
