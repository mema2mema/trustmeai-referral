import schedule
import time
import importlib.util
import os
import sys

# Dynamically load main.py
main_path = os.path.join(os.path.dirname(__file__), "main.py")
spec = importlib.util.spec_from_file_location("main_module", main_path)
main_module = importlib.util.module_from_spec(spec)
sys.modules["main_module"] = main_module
spec.loader.exec_module(main_module)

def job():
    print("✅ Running scheduled RedHawk simulation...")
    main_module.main()

# Schedule every 15 minutes
schedule.every(15).minutes.do(job)

print("🔁 RedHawk Auto Scheduler started...")
job()  # Optional: run once immediately

while True:
    schedule.run_pending()
    time.sleep(1)
