import requests
import threading
import time
import signal
import sys

# Global stop flag
stop_flag = False

# Graceful stop on Ctrl+C
def signal_handler(sig, frame):
    global stop_flag
    print("\nStopping test...")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)

# User inputs
target = input("Enter the URL to test: ")
requests_per_second = int(input("Enter number of concurrent requests per second: "))
duration = int(input("Enter duration of test in seconds: "))

def send_request():
    global stop_flag
    while not stop_flag:
        try:
            r = requests.get(target, timeout=5, headers={"User-Agent": "test-script/1.0"})
            print(f"{time.strftime('%H:%M:%S')} - Status: {r.status_code}")
            
            if r.status_code >= 500:
                print("Server down or error detected! Stopping test.")
                stop_flag = True
                break

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            print("Server might be down! Stopping test.")
            stop_flag = True
            break

# Start threads
threads = []
start_time = time.time()
for _ in range(requests_per_second):
    t = threading.Thread(target=send_request)
    t.start()
    threads.append(t)

# Wait until duration ends or stop_flag is True
try:
    while not stop_flag and (time.time() - start_time < duration):
        time.sleep(0.1)
except KeyboardInterrupt:
    stop_flag = True

# Wait for all threads to finish
for t in threads:
    t.join()

print("Test finished.")
