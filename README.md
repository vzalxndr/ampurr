# ampurr ᓚ₍ ^. .^₎

> The purr-fect toolkit for managing your Linux hardware and extending your battery's health.

Ampurr is a utility for Linux laptops designed to give you control over your hardware. It features both a powerful **GUI Dashboard** for system monitoring and a simple **CLI** for quick adjustments.

Its primary goal is to help you extend your battery's lifespan by setting a charge threshold, but ampurr also allows you to manage CPU power profiles and monitor system resources in real-time.



---

## ✨ Features

*   **Comprehensive GUI Dashboard**: A user-friendly panel to manage all features, monitor system resources, and view sensor data.
*   **Battery Charge Limiting**: Set a charge threshold (e.g., 80%) to reduce the stress on your battery from being constantly at 100%.
*   **CPU Profile Management**: Switch between `powersave` and `performance` modes directly from the app to balance performance and power consumption.
*   **System Monitoring**: Track CPU usage, RAM consumption, and a list of the top resource-hungry processes.
*   **Sensor Monitoring**: View temperatures, voltages, and fan speeds with seamless `lm-sensors` integration.
*   **Persistent Settings**: Your chosen charge limit is saved and automatically applied on every system boot.
*   **Easy Installation**: A smart installer handles file copying and dependency checks for you.
*   **Safe Uninstallation**: The uninstaller completely removes all components and safely resets your battery charge limit to 100%.

---

## 🚀 Installation

You can install ampurr by downloading the latest version or by using Git.

### Requirements

*   A Linux-based system with **systemd**.
*   **Python 3**.
*   The GUI also requires `python3-pyqt5`, `lm-sensors`, and `polkit`. **The installer can set these up for you.**

### Installation Steps

1.  **Get the project**
    *   **Option A: Download a Release**
        Go to the [**Releases page**](https://github.com/vzalxndr/ampurr/releases), then download and unzip the `ampurr-vX.X.X.zip` archive.
    *   **Option B: Use Git**
        ```bash
        git clone https://github.com/vzalxndr/ampurr.git
        cd ampurr
        ```

2.  **Run the installer**
    Navigate to the project folder and run the `install.sh` script with superuser privileges.

    *   **To install both CLI and GUI (Recommended):**
        The installer will check for dependencies and ask for permission to install them if needed.
        ```bash
        sudo bash install.sh --gui
        ```

    *   **To install the CLI only:**
        ```bash
        sudo bash install.sh
        ```

After installation, you can find `Ampurr` in your application menu (if you installed the GUI) or use the `ampurr` command in your terminal.

---

## ⚙️ Usage

### Graphical User Interface (GUI)

If you installed the GUI version, simply find and launch **"Ampurr"** from your system's application menu.

The interface is divided into three tabs:
*   **Power Control**: Set the battery charge limit and select the CPU power profile.
*   **System Usage**: Monitor CPU load, RAM usage, and running processes.
*   **Sensors**: View data from all available system sensors.

### Command-Line Interface (CLI)

All features are also accessible via the `ampurr` command.

#### Battery Management (`battery`)

*   **Show status:**
    ```bash
    ampurr battery status
    ```
    *Example output:*
    ```
    set charge limit: 80%
    current capacity:   65%
    ```

*   **Set a new limit (value from 50 to 100):**
    ```bash
    sudo ampurr battery set 75
    ```

#### CPU Management (`cpu`)

*   **Show the current profile:**
    ```bash
    ampurr cpu status
    ```
    *Example output:*
    ```
    current CPU governor: powersave
    ```
*   **List available profiles:**
    ```bash
    ampurr cpu list
    ```
*   **Set a new profile:**
    ```bash
    sudo ampurr cpu set performance
    ```

---

## 🗑️ Uninstalling

To completely remove Ampurr from your system:

1.  **Navigate to the project directory** where the `uninstall.sh` script is located.

2.  **Run the uninstaller with superuser privileges:**
    ```bash
    sudo bash uninstall.sh
    ```
The script will stop the service, remove all files (CLI, GUI, icons, menu entry), and reset your battery charge limit back to 100%.
