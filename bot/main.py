try:
    # When run as a package: python -m bot.main
    from .bot_main import main
except Exception:
    # When run as a script: python bot/main.py
    from bot_main import main

if __name__ == "__main__":
    main()
