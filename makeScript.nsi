# Define the installer name and output
OutFile "SlipstreamEngineInstaller.exe"

# Request user-level privileges (no admin required)
RequestExecutionLevel user

# Define the installation directory in the user's local application data folder
InstallDir "$APPDATA\SlipstreamEngine"

# Define the section for installation
Section "Install"

    # Create the installation directory
    CreateDirectory "$INSTDIR"

    # Copy the Python script to the installation directory
    SetOutPath "$INSTDIR"
    File "main.py"
    File "updater.py"
    File "remove_index.json"
    File /r "server"
    File /r "client"

    # Create a shortcut in the Windows Start Menu
    CreateShortCut "$SMPROGRAMS\Slipstream Engine.lnk" "$INSTDIR\SlipstreamEngine.exe"

    # Write the uninstaller to the installation directory
    WriteUninstaller "$INSTDIR\Uninstall Slipstream Engine.exe"

    # Create a shortcut for the uninstaller in the Start Menu
    CreateShortCut "$SMPROGRAMS\Uninstall Slipstream Engine.lnk" "$INSTDIR\Uninstall Slipstream Engine.exe"

    # Wait for the executed program to finish before exiting
    Exec '"$INSTDIR\SlipstreamEngine.exe"'

    # Exit the installer
    Quit
SectionEnd

# Define the section for uninstallation
Section "Uninstall"

    # Remove the installation directory and all its contents
    RMDir /r "$INSTDIR"

    # Remove the shortcut from the Start Menu
    Delete "$SMPROGRAMS\Slipstream Engine.lnk"
    Delete "$SMPROGRAMS\Uninstall Slipstream Engine.lnk"

    # Exit the uninstaller
    Quit
SectionEnd