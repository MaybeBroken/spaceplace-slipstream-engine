import os
import sys
import shutil
from time import sleep
from json import loads
import glob
import urllib.request

try:
    from colorama import init, Fore, Style
except ImportError as e:
    os.system("python3 -m pip install colorama")
    from colorama import init, Fore, Style

if sys.platform == "win32":
    userAppData = os.getenv("APPDATA")
elif sys.platform == "linux":
    userAppData = os.path.expanduser("~/.local/share")
elif sys.platform == "darwin":
    userAppData = os.path.expanduser("~/Library/Application Support")
appId = "MaybeBroken-Software-Updater"

if not os.path.exists(userAppData + os.sep + appId):
    os.makedirs(userAppData + os.sep + appId)

os.chdir(userAppData + os.sep + appId)

init()


class PACKAGE:
    def __init__(self, _dict: dict):
        self.name = _dict.get("name")
        self.version = _dict.get("currentVersion")
        self.url = _dict.get("currentPackageUrl")
        self.date = _dict.get("currentReleaseDate")


def download_report_hook(count, block_size, total_size):
    percent = min(int(count * block_size * 100 / total_size), 100)
    bar_length = 40
    filled_length = int(bar_length * percent / 100)
    bar = "▓" * filled_length + "░" * (bar_length - filled_length)
    print(
        f"\rDownloading: |{Fore.GREEN}{bar}{Style.RESET_ALL}| {Fore.CYAN}{percent}%{Style.RESET_ALL}",
        end="",
    )
    sys.stdout.flush()


def download_file(url: str, filename: str) -> None:
    try:
        urllib.request.urlretrieve(url, filename, reporthook=download_report_hook)
        print()
    except Exception as e:
        print(f"\n{Fore.RED}Error downloading file [{url}]: {e}{Style.RESET_ALL}")
        exit(1)


def get_packages() -> list[dict]:
    download_file(
        "https://maybebroken.github.io/api/v1/software/index.json", "app_index.json"
    )
    with open("app_index.json", "r") as f:
        packages = loads(f.read())
    return packages


def build_package_index(packages: list[dict]) -> list[PACKAGE]:
    package_index = []
    for package in packages:
        package_index.append(PACKAGE(package))
    return package_index


def cleanup():
    if os.path.exists("app_index.json"):
        os.remove("app_index.json")

    print(f"{Fore.LIGHTYELLOW_EX}Cleaning up temporary files...{Style.RESET_ALL}")


def exit(message: str = None):
    print(message) if message else None
    cleanup()
    print(f"{Fore.RED}Exiting...{Style.RESET_ALL}")
    sleep(3)
    sys.exit(1)


def print_args():
    print(
        f"{Fore.LIGHTYELLOW_EX}Usage: [--name <name> --version <version> --file-index-path <path> --root-path <path>]{Style.RESET_ALL}"
    )


class get_args:
    def __init__(self):
        if "--name" in sys.argv:
            self.name = sys.argv[sys.argv.index("--name") + 1]
        else:
            print_args()
            exit(f"{Fore.RED}No name provided.{Style.RESET_ALL}")
        if "--version" in sys.argv:
            self.version = sys.argv[sys.argv.index("--version") + 1]
        else:
            print_args()
            exit(f"{Fore.RED}No version provided.{Style.RESET_ALL}")
        if "--file-index-path" in sys.argv:
            self.file_index_path = sys.argv[sys.argv.index("--file-index-path") + 1]
        else:
            print_args()
            exit(f"{Fore.RED}No file index path provided.{Style.RESET_ALL}")
        if "--root-path" in sys.argv:
            self.root_path = sys.argv[sys.argv.index("--root-path") + 1]
        else:
            print_args()
            exit(f"{Fore.RED}No root path provided.{Style.RESET_ALL}")


if __name__ == "__main__":
    args = get_args()
    print(f"{Fore.LIGHTYELLOW_EX}Checking for updates...{Style.RESET_ALL}")
    print(f"{Fore.LIGHTYELLOW_EX}Fetching packages from server...{Style.RESET_ALL}")
    packages = get_packages()
    package_index = build_package_index(packages)
    print(
        f"{Fore.LIGHTGREEN_EX}Found {len(package_index)} packages on server.{Style.RESET_ALL}"
    )
    if args.name == "":
        exit(f"{Fore.RED}No name provided.{Style.RESET_ALL}")
    if args.version == "":
        exit(f"{Fore.RED}No version provided.{Style.RESET_ALL}")
    if args.file_index_path == "":
        exit(f"{Fore.RED}No file index path provided.{Style.RESET_ALL}")
    if args.root_path == "":
        exit(f"{Fore.RED}No root path provided.{Style.RESET_ALL}")
    downloadedFileName = None
    for package in package_index:
        if package.name == args.name:
            if package.version != args.version:
                print(f"{Fore.LIGHTYELLOW_EX}Update found!{Style.RESET_ALL}")
                print(
                    f"{Fore.LIGHTYELLOW_EX}Downloading [{package.name}]...{Style.RESET_ALL}"
                )
                downloadedFileName = package.name + ".zip"
                download_file(package.url, downloadedFileName)

                print(f"{Fore.LIGHTGREEN_EX}Download complete!{Style.RESET_ALL}")
                version = package.version
            else:
                print(f"{Fore.LIGHTGREEN_EX}No update found.{Style.RESET_ALL}")
                exit(0)
        else:
            print(f"{Fore.RED}Package name not found.{Style.RESET_ALL}")
            exit(1)
    if downloadedFileName is None:
        exit(f"{Fore.RED}No downloaded file name found.{Style.RESET_ALL}")
    if os.path.exists(downloadedFileName):
        print(f"{Fore.LIGHTYELLOW_EX}Installing [{args.name}]...{Style.RESET_ALL}")
        if os.path.exists(args.file_index_path):
            os.chdir(os.path.dirname(args.file_index_path))
            with open(args.file_index_path, "r") as f:
                file_index = loads(f.read())
            for pattern in file_index["removeList"]:
                for file in glob.glob(pattern, recursive=True):
                    if os.path.exists(file):
                        try:
                            if os.path.isdir(file):
                                shutil.rmtree(file)
                                print(
                                    f"{Fore.LIGHTGREEN_EX}Removed {file}.{Style.RESET_ALL}"
                                )
                            else:
                                os.remove(file)
                                print(
                                    f"{Fore.LIGHTGREEN_EX}Removed {file}.{Style.RESET_ALL}"
                                )
                        except Exception as e:
                            print(
                                f"{Fore.RED}Error removing {file}: {e}{Style.RESET_ALL}"
                            )
                    else:
                        print(f"{Fore.RED}File {file} does not exist.{Style.RESET_ALL}")
            os.chdir(userAppData + os.sep + appId)
            shutil.unpack_archive(
                downloadedFileName,
                os.path.abspath(os.path.dirname(args.file_index_path)),
            )
            print(f"{Fore.LIGHTGREEN_EX}Installation complete!{Style.RESET_ALL}")
            os.remove(downloadedFileName)
            # return to the original directory
            os.chdir(args.root_path)
            with open(
                os.path.abspath(os.path.dirname(args.file_index_path)) + os.sep + "ver",
                "w",
            ) as f:
                f.write(version)
        else:
            exit(f"{Fore.RED}File index path does not exist.{Style.RESET_ALL}")
    else:
        exit(f"{Fore.RED}Downloaded file no longer exists.{Style.RESET_ALL}")
else:
    print(f"{Fore.RED}This script is only meant to be run directly.{Style.RESET_ALL}")
    exit(1)
