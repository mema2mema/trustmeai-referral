import schedule
import time
from main import main

def job():
    print("🔁 Running scheduled RedHawk simulation...")
    main()

# Run every 15 minutes (customize as needed)
schedule.every(15).minutes.do(job)

print("🕒 RedHawk Auto Scheduler started...")

while True:
    schedule.run_pending()
    time.sleep(1)
