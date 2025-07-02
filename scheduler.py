import schedule
import subprocess
import time


def schedule_job(cron_expression: str, command: str) -> None:
    """
    Schedules a job to run at specified intervals using a cron-like expression.
    FIX: Removed the infinite while True loop. This function now only registers the job.
    Running of pending jobs must be handled by a separate background process/thread.
    """
    schedule.every().day.at(cron_expression).do(subprocess.call, command, shell=True)
    print(f"Job scheduled: '{command}' to run daily at {cron_expression}")

# NEW: Function to run scheduled jobs in a background thread
def run_scheduler_in_background():
    """
    Runs the schedule pending jobs in a continuous loop.
    This function is intended to be run in a separate thread.
    """
    print("Scheduler background thread started. Looking for pending jobs...")
    while True:
        schedule.run_pending()
        time.sleep(1) # Check every second
