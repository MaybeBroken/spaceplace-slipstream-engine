import os
import sys
from time import sleep
import atexit

if sys.platform == "win32":
    userAppData = os.getenv("APPDATA")
elif sys.platform == "linux":
    userAppData = os.path.expanduser("~/.local/share")
elif sys.platform == "darwin":
    userAppData = os.path.expanduser("~/Library/Application Support")
appId = "SlipstreamEngine"
if not os.path.exists(os.path.join(userAppData, appId)):
    os.makedirs(os.path.join(userAppData, appId))
os.chdir(os.path.join(userAppData, appId))
print("Current working directory:", os.path.abspath(os.getcwd()))

atexit.register(
    lambda: [
        print(
            "Exiting... Please wait a moment for the application to close completely."
        ),
        sleep(3),
    ]
)

try:
    is_python_installed = os.system("python3 --version") == 0

    if is_python_installed:
        print("Python is installed, proceeding with runtime.")
    else:
        if sys.platform == "win32":
            print("Python is not installed, taking you to the Microsoft Store.")
            os.system("start ms-windows-store://pdp/?ProductId=9NCVDN91XZQP")
        elif sys.platform == "linux":
            print("Python is not installed, taking you to the Python website.")
            os.system("xdg-open https://www.python.org/downloads/")
        elif sys.platform == "darwin":
            print("Python is not installed, taking you to the Python website.")
            os.system("open https://www.python.org/downloads/")
        else:
            print("Python is not installed, please install it manually.")
            input("Press Enter to exit...")
            sys.exit(1)

    attempts = 0
    while not is_python_installed and attempts < 12:
        print("Waiting for Python to be installed...")
        is_python_installed = os.system("python3 --version") == 0
        sleep(5)
        attempts += 1

    if not is_python_installed:
        print("Python installation check exceeded maximum attempts. Exiting.")
        input("Press Enter to exit...")
        sys.exit(1)
    if not os.path.exists("ver"):
        print("Version file not found. Creating a new one.")
        with open("ver", "w") as f:
            f.write("0.0.0")
    version = os.system(
        f'python3 updater.py\
 --name "SlipstreamEngine"\
 --version {open("ver").read().strip()}\
 --file-index-path {os.path.abspath("remove_index.json")}\
 --root-path "."'
    )
    os.system("python3 Main.py")
except:
    sleep(3)
    sys.exit(1)
