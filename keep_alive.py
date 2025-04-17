from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

# Run the Flask app in a separate thread to keep the bot alive
def run():
    app.run(host='0.0.0.0', port=8080)

# Start the Flask app in a thread
def keep_alive():
    t = threading.Thread(target=run)
    t.start()
