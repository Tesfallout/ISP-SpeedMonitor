# Speed Monitor for providing reports on ISP up/down rates
# Created 6/2/2023 by Tesfallout


import speedtest
import tkinter as tk
from datetime import datetime
import time
import os


##### Start of User Variables #####


# 0 = no debug, only schedule tests
# 1 = show logs in console, do first test immediatly
# 2 = do above, countdown to next test, show test start time
debug_mode = 1

threshold_speed = 500  # User-defined threshold for minimum speed in Mbps, speeds lower than this will count as a failure and will try to trigger the alert popup if applicable.
interval_minutes = 30  # User-defined testing interval in minutes

pop_enabled = False  # Enable or disable the pop-up feature
pop_life = 5  # Life of popup before it auto-closes in seconds, a value of 0 or less will keep popup window open.

log_file = "speed_test_log.csv"  # Path to the log file
max_log_size = 100 * 1024 * 1024  # Maximum size of the log file in bytes. Currently 100Mb


##### End of User Variables #####


popup = None  # Define the popup as a global variable
global remaining_time

def check_log_size():
    if os.path.exists(log_file):
        log_size = os.path.getsize(log_file)
        if log_size > max_log_size:
            # Read the log file contents
            with open(log_file, "r") as f:
                lines = f.readlines()

            # Calculate the number of lines to keep
            num_lines_to_keep = 0
            total_size = 0
            for line in reversed(lines):
                total_size += len(line.encode('utf-8'))
                num_lines_to_keep += 1
                if total_size > max_log_size:
                    break

            # Trim the log file to the specified size
            with open(log_file, "w") as f:
                f.writelines(lines[-num_lines_to_keep:])

def log_speed_result(timestamp, download_speed, upload_speed):
    check_log_size()  # Check and trim log file if it exceeds the maximum size
    with open(log_file, "a") as f:
        f.write(f"Timestamp: {timestamp},")
        f.write(f"Download Speed: {download_speed:.2f} Mbps,")
        f.write(f"Upload Speed: {upload_speed:.2f} Mbps,\n")

def handle_popup(timestamp, download_speed, upload_speed):
    global popup  # Reference the global popup variable
    if download_speed < threshold_speed or upload_speed < threshold_speed:
        if pop_enabled:
            root = tk.Tk()
            root.withdraw()
            popup = tk.Toplevel(root)
            popup.title("Speed Alert")
            popup.geometry("300x100")

            message = f"Your speed is below {threshold_speed} Mbps!\n\n"
            message += f"Timestamp: {timestamp}\n"
            message += f"Download Speed: {download_speed:.2f} Mbps\n"
            message += f"Upload Speed: {upload_speed:.2f} Mbps"

            popup_label = tk.Label(popup, text=message, justify="center")
            popup_label.pack(pady=10)
            if pop_life > 0:
                popup.after(pop_life * 1000, popup.destroy)  # Close the popup after the specified duration

def get_remaining_seconds():
    current_time = datetime.now().time()
    remaining_minutes = interval_minutes - (current_time.minute % interval_minutes)
    remaining_seconds = (remaining_minutes * 60) - current_time.second
    return remaining_seconds

def update_remaining_time():
    print(f"Next test in {get_remaining_seconds()} seconds")
    root.after(5000, update_remaining_time)

def run_speed_test():
    try:
        # Perform speed test
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if debug_mode >= 2:
            print("starting speed test at:")
            print(timestamp)
        st = speedtest.Speedtest(secure=True)
        download_speed = st.download() / 10 ** 6
        upload_speed = st.upload() / 10 ** 6

        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Print speeds to console while debug mode is enabled
        if debug_mode >= 1:
            print(timestamp)
            print(f"Download Speed: {download_speed:.2f} Mbps")
            print(f"Upload Speed: {upload_speed:.2f} Mbps\n")

        # Log the results to a file
        log_speed_result(timestamp, download_speed, upload_speed)

        # Handle the popup if speed is below the threshold
        handle_popup(timestamp, download_speed, upload_speed)

        # Schedule the next speed test based on the user-defined interval
        interval_seconds = interval_minutes * 60
        root.after(get_remaining_seconds() * 1000, run_speed_test) #####

    except speedtest.SpeedtestException as e:
        print(f"An error occurred: {str(e)}")

def start_speed_test():
    if debug_mode >= 1:
        run_speed_test()
    else:
        # Schedule the first speed test immediately
        root.after(0, run_speed_test)

# Create the Tkinter root window
root = tk.Tk()
root.withdraw()

# Start the speed test
start_speed_test()

# Update the remaining time every 5 seconds while debug mode is enabled
if debug_mode >= 2:
    root.after(5000, update_remaining_time)

# Start the Tkinter event processing loop
root.mainloop()
