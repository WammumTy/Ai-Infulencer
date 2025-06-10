from flask import Flask, render_template_string, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerNotRunningError
from bot import run_bot

app = Flask(__name__)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=run_bot, trigger="interval", hours=1)
scheduler.start()

@app.route("/")
def home():
    # Read the last 50 lines of the log file
    try:
        with open("activity_log.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]  # show last 50 lines
    except FileNotFoundError:
        lines = ["No log data yet."]

    log_html = "<br>".join(line.strip() for line in lines)

    # Simple HTML template
    html = f"""
    <h1>🟢 Reddit Bot Dashboard</h1>
    <p><b>Scheduler is running every hour.</b></p>
    <h2>Activity Log:</h2>
    <div style='background-color:#f4f4f4; padding:10px; border:1px solid #ccc; max-height:300px; overflow:auto;'>{log_html}</div>
    <form action="/run-now" method="post">
        <button type="submit">Run Bot Now</button>
    </form>
    """
    return html

@app.route("/run-now", methods=["POST"])
def run_now():
    run_bot()
    return redirect(url_for("home"))

# Safe shutdown
@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    if scheduler.running:
        try:
            scheduler.shutdown()
        except SchedulerNotRunningError:
            print("Scheduler already stopped.")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
