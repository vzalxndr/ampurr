# ampurr ᓚ₍ ^. .^₎

> The purr-fect toolkit for managing your Linux hardware and extending your battery's health.

Ampurr is a simple utility for Linux laptops designed to give you control over your hardware. Its primary goal is to help you extend your battery's lifespan by setting a charge threshold, but it's built to grow into a full-fledged system management toolkit.

---

## ✨ Features

*   **Battery Charge Limiting**: Set a charge threshold (e.g., 80%) to prevent your battery from the stress of being constantly at 100%.
*   **Persistent Settings**: Your chosen limit is automatically applied on every system boot.
*   **Dynamic Battery Detection**: Automatically finds the correct battery (`BAT0`, `BAT1`, etc.) on your system.
*   **Clean CLI Interface**: All features are accessible through a simple and intuitive command-line interface.
*   **Easy Installation**: A simple installation script handles everything for you.
*   **Safe Uninstallation**: The uninstaller cleans up after itself and safely resets your battery settings to 100%.

---

## 🚀 Installation

You can choose one of two methods to install ampurr.

### Method 1: Using Zip Archive (Recommended for most users)

1.  **Download the latest version:**
    *   Go to the [main page of the Ampurr repository](https://github.com/vzalxndr/ampurr).
    *   Click the green `<> Code` button.
    *   Click `Download ZIP`.

2.  **Unzip the archive:**
    Navigate to your Downloads folder and unzip the file. You can do this with your file manager or via the terminal:
    ```bash
    # Navigate to your downloads folder
    cd ~/Downloads

    # Unzip the file
    unzip ampurr-main.zip
    ```

3.  **Navigate into the directory:**
    ```bash
    cd ampurr-main
    ```

4.  **Run the installer:**
    You will need to run the installer with superuser privileges, as it needs to copy files to system directories and set up a system service.
    ```bash
    sudo bash install.sh
    ```

### Method 2: Using Git

1.  **Clone the repository:**
    This method requires you to have `git` installed on your system.
    ```bash
    git clone https://github.com/vzalxndr/ampurr.git
    ```

2.  **Navigate into the directory:**
    ```bash
    cd ampurr
    ```

3.  **Run the installer:**
    ```bash
    sudo bash install.sh
    ```

---

## ⚙️ Usage

Ampurr is controlled via the `ampurr` command in your terminal.

#### Show Status
To see the currently set charge limit and the current battery capacity, use the `status` command:
```bash
ampurr status
```
*Example output:*
```
set charge limit: 80%
current capacity:   65%
```

#### Get Current Limit
To see only the configured charge limit:
```bash
ampurr get
```
*Example output:*
```
current charge limit: 80%
```

#### Set a New Limit
To set a new charge limit, use the `set` command with a value between 50 and 100. This requires superuser privileges.
```bash
sudo ampurr set 75
```
*Example output:*
```
✅ charge limit successfully set to 75% for the current session.
✅ limit of 75% saved and will be applied on next boot.
```
The new limit is applied instantly and will be automatically restored after you reboot your machine.

---

## 🗑️ Uninstalling

If you wish to remove Ampurr from your system, you can use the uninstaller script from the same directory you cloned.

1.  **Navigate into the directory (if you are not already there):**
    ```bash
    cd /path/to/ampurr
    ```

2.  **Run the uninstaller with superuser privileges:**
    ```bash
    sudo bash uninstall.sh
    ```
The script will stop the service, remove all installed files, and reset your battery charge limit back to 100%.

---
thx^^
