print("INIT")
import atexit
from time import sleep
import zipfile
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.core import loadPrcFileData
import io
from datetime import datetime
import os
import sys
import subprocess
from pathlib import Path


userdata = Path(os.getenv("APPDATA", os.path.expanduser("~")))

# Create specific directory for our application
log_dir = userdata / "SlipstreamEngine" / "logs"

# Ensure log directory exists and tee stdout/stderr to log file
os.makedirs(log_dir, exist_ok=True)
errlog_path = log_dir / "ENGINE.log"

if not len(os.sys.argv) > 1:
    with open(errlog_path, "w", encoding="utf-8") as f:
        f.write(f"--- Log started {datetime.now().isoformat()} ---\n")

# Keep references to the original stdout/stderr
_orig_stdout = sys.stdout
_orig_stderr = sys.stderr


class Tee(io.TextIOBase):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            try:
                if len(s.strip()) > 0:
                    # Prepend timestamp to each line
                    s = datetime.now().isoformat() + " " + str(s)
                st.write(s)
            except Exception:
                pass
        # Flush after each write to keep file up-to-date
        self.flush()
        return len(s)

    def flush(self):
        for st in self.streams:
            try:
                st.flush()
            except Exception:
                pass

    def fileno(self):
        return self.streams[0].fileno()

    def isatty(self):
        return all(getattr(st, "isatty", lambda: False)() for st in self.streams)


# Open the log file in append mode (line-buffered) and tee output
_log_file = open(errlog_path, "a", encoding="utf-8", buffering=1)
sys.stdout = Tee(_orig_stdout, _log_file)
sys.stderr = Tee(_orig_stderr, _log_file)


if not (len(os.sys.argv) > 1):

    def warn(message):
        from tkinter import Tk, messagebox

        root = Tk()
        root.withdraw()  # Hide the main window
        result = messagebox.askyesno("Warning", message)
        root.destroy()
        return result

    if not "__file__" in globals():
        __file__ = os.path.abspath(sys.argv[0])

    root_dir = Path(os.path.expanduser("~"))
    WORKING_DIR = root_dir / "Slipstream Engine" / "launcher"
    if not os.path.exists(WORKING_DIR):
        os.makedirs(WORKING_DIR)

    def extract_data(target_dir: Path, bin_data_path: Path):

        print(f"Extracting data from {bin_data_path} to {target_dir}")
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(bin_data_path, "r") as zip_ref:
            corrupt_check = zip_ref.testzip()
            if corrupt_check:  # Test for corrupt files
                print("Corrupt files found in zip: ", corrupt_check)
                return

            zip_ref.extractall(target_dir)

    def on_exit():
        """Best-effort exit handler that offers to open the session log."""
        try:
            # Ensure everything is flushed
            try:
                sys.stdout.flush()
            except Exception:
                pass
            try:
                sys.stderr.flush()
            except Exception:
                pass

            # Close the file handle so Windows can open it
            try:
                if not _log_file.closed:
                    _log_file.flush()
                    _log_file.close()
            except Exception:
                pass

            if warn("Open log location?"):
                # Make sure the file exists
                if not errlog_path.exists():
                    try:
                        errlog_path.touch()
                    except Exception:
                        pass
                try:
                    os.system(f'start "" "{errlog_path.parent}"')
                except Exception:
                    pass
        except Exception:
            # Avoid raising during interpreter shutdown
            pass

    atexit.register(on_exit)

    print(f"--- Session start @__LOGGING_ACTIVE__ ---")

    exe_location = Path(sys.argv[0]).resolve()
    print(f"Executable location: {exe_location}")
    # Check if running from PyInstaller bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running as a PyInstaller bundle
        BIN_DATA_LOCATION = Path(sys._MEIPASS) / "bin_data.bin"
    else:
        # Running in a normal Python environment
        BIN_DATA_LOCATION = Path("./bin_data.bin").resolve()
    print(f"Looking for 'bin_data.bin' file at: {BIN_DATA_LOCATION}")
    if not BIN_DATA_LOCATION.exists():
        if not warn(
            "Application integrity check failed. 'bin_data.bin' file is missing. The application may not function correctly, and there is an INCREDIBLY HIGH risk of data loss. Do you want to continue?"
        ):
            print("Exiting due to failed integrity check.")
            sys.exit(1)
    else:
        print(f"'bin_data.bin' file found at: {BIN_DATA_LOCATION}")

    print(f"moving to working directory: {WORKING_DIR}")
    os.chdir(WORKING_DIR)

    SERVER_LOCATION = WORKING_DIR.parent / "server"
    CLIENT_LOCATION = WORKING_DIR.parent / "client"

    if (
        not (CLIENT_LOCATION / "models").exists()
        or not (CLIENT_LOCATION / "shaders").exists()
    ):
        print(f"Client data missing 'models' or 'shaders', extracting from binary data")
        extract_data(CLIENT_LOCATION, BIN_DATA_LOCATION)
        print(f"Extracted client data to {CLIENT_LOCATION}")
    else:
        print(f"Client data found at: {CLIENT_LOCATION}")
    if (
        not (CLIENT_LOCATION / "models").exists()
        or not (CLIENT_LOCATION / "shaders").exists()
    ):
        if not warn(
            "Application integrity check failed. 'models' or 'shaders' directory is missing in client data. The application may not function correctly, and there is an INCREDIBLY HIGH risk of data loss. Do you want to continue?"
        ):
            print("Exiting due to failed integrity check.")
            sys.exit(1)


print("beginning server imports")
import server.serverApp as serverApp

print("beginning client imports")
import client.clientApp as clientApp


loadPrcFileData("", "win-size 350 150")
loadPrcFileData("", "window-title Slipstream Launcher")
loadPrcFileData("", "win-fixed-size true")
loadPrcFileData("", "load-display pandagl")
loadPrcFileData("", "aux-display p3tinydisplay")
loadPrcFileData("", "aux-display pandadx9")
loadPrcFileData("", "aux-display pandadx8")


class mainWindow(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()
        self.accept("q", self.quit)
        self.launch_server_button = DirectButton(
            text="Launch Server",
            pos=(0, 0, 0.35),
            scale=0.6,
            geom=None,
            relief=DGG.FLAT,
            command=self.launch_server,
        )
        self.launch_client_button = DirectButton(
            text="Launch Client",
            pos=(0, 0, -0.35),
            scale=0.6,
            geom=None,
            relief=DGG.FLAT,
            command=self.launch_client,
        )

    def launch_server(self):
        print("Launching server program...")
        subprocess.Popen(
            [sys.executable, sys.argv[0], "--server"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    def launch_client(self):
        print("Launching client program...")
        subprocess.Popen(
            [sys.executable, sys.argv[0], "--client"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    def quit(self):
        print("Exiting main program...")
        self.userExit()


def main():
    print("Slipstream Engine starting...")  # Console output for debugging
    try:
        app = mainWindow()
        app.run()
    except Exception as e:
        print("An error occurred. See log file for details.")
        sleep(2)
        sys.exit(e.__traceback__)


def run_server():
    serverApp.run_server()


def run_client():
    clientApp.run_client()


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Slipstream Engine Launcher")
    parser.add_argument("--server", action="store_true", help="Launch server only")
    parser.add_argument("--client", action="store_true", help="Launch client only")
    # Use parse_known_args to ignore unknown arguments (e.g., from multiprocessing)
    args, unknown = parser.parse_known_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    if args.server:
        run_server()
    elif args.client:
        run_client()
    else:
        main()
