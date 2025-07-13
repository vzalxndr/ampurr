#!/usr/bin/env python3
import sys
import subprocess
import os
import re
import time
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QPushButton, QGroupBox, QStackedWidget, QProgressBar,
                             QTextEdit, QFormLayout, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QObject, QThread, pyqtSignal, pyqtSlot, QMetaObject

# --- application styles (qss) ---
APP_STYLESHEET = """
    QWidget {
        background-color: #282a36;
        color: #f8f8f2;
        font-family: Cantarell, "Segoe UI", "Ubuntu", sans-serif;
        font-size: 10pt;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #44475a;
        border-radius: 5px;
        margin-top: 1ex;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
    }
    QPushButton {
        background-color: #44475a;
        border: 1px solid #6272a4;
        padding: 10px 10px;
        border-radius: 3px;
    }
    QPushButton:disabled {
        background-color: #21222c;
        color: #6272a4;
    }
    QPushButton:hover {
        background-color: #6272a4;
    }
    QPushButton[property="active-profile"] {
        font-weight: bold;
        background-color: #50fa7b;
        color: #282a36;
        border: 1px solid #50fa7b;
    }
    QSlider::groove:horizontal {
        border: 1px solid #44475a;
        height: 8px;
        background: #21222c;
        margin: 2px 0;
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        background: #bd93f9;
        border: 1px solid #bd93f9;
        width: 16px;
        margin: -4px 0;
        border-radius: 8px;
    }
    QProgressBar {
        border: 1px solid #44475a;
        border-radius: 5px;
        text-align: center;
        color: #f8f8f2;
    }
    QProgressBar::chunk {
        background-color: #bd93f9;
    }
    QTextEdit {
        background-color: #21222c;
        border: 1px solid #44475a;
        border-radius: 3px;
    }
    QScrollArea {
        border: none;
    }
    QWidget[class="TabButton"] {
        background-color: transparent;
        border: none;
        border-radius: 8px;
    }
    QWidget[class="TabButton"][active-tab="false"]:hover {
        background-color: #3d3f50;
    }
    QWidget[class="TabButton"][active-tab="true"] {
        background-color: #44475a;
    }
    QWidget[class="TabButton"][active-tab="true"] QLabel#tab_text {
        border-bottom: 3px solid #bd93f9;
    }
    QStackedWidget {
        border: none;
    }
"""

GUI_RESOURCES_PATH = "/usr/share/ampurr-gui"

class IconTextButton(QWidget):
    """a custom widget that looks like a button but gives full style control"""
    clicked = pyqtSignal()

    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        self.setProperty("class", "TabButton")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 5)
        layout.setSpacing(2)

        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        icon_label.setPixmap(pixmap.scaled(90, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel(text)
        # assign a unique name for QSS access
        text_label.setObjectName("tab_text")
        text_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        """emits 'clicked' signal on mouse press"""
        self.clicked.emit()
        super().mousePressEvent(event)


# =============================================================================
# worker class for heavy tasks
# =============================================================================
class DataFetcher(QObject):
    dataReady = pyqtSignal(dict)

    def run_command(self, command, timeout=2.5):
        try:
            return subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout).stdout.strip()
        except subprocess.TimeoutExpired:
            return f"Error: Command '{' '.join(command)}' timed out."
        except Exception as e:
            return f"Error: {e}"

    def get_sensor_data(self):
        sensors_data = {};
        output = self.run_command(["sensors"])
        if "Error" in output: return {"Error": output}
        current_device = None
        for line in output.splitlines():
            stripped_line = line.strip()
            if not stripped_line: continue
            if not line.startswith((' ', '\t')) and not stripped_line.startswith(
                    "Adapter:") and ':' not in stripped_line: current_device = stripped_line; continue
            if stripped_line.startswith("Adapter:"): continue
            if ':' in stripped_line and current_device:
                try:
                    label, value_part = stripped_line.split(':', 1);
                    sensors_data[
                        f"{current_device} - {label.strip()}"] = value_part.split('(')[0].strip()
                except ValueError:
                    continue
        if not sensors_data: return {"Error": "Failed to parse any data from 'sensors' output."}
        return sensors_data

    @pyqtSlot()
    def fetch_data(self):
        self.dataReady.emit({'ps': self.run_command(["ps", "-eo", "%cpu,%mem,comm", "--sort=-%cpu"]),
                             'sensors': self.get_sensor_data()})


# =============================================================================
# main gui class
# =============================================================================
class AmpurrGUI(QWidget):
    CATEGORY_MAP = {"coretemp": "CPU", "zenpower": "CPU", "nouveau": "GPU", "amdgpu": "GPU", "nvme": "Storage",
                    "iwlwifi": "Network", "asus": "Motherboard", "acpi": "Motherboard", "acpitz": "Motherboard",
                    "BAT": "Battery"}

    def __init__(self):
        super().__init__()
        self.last_cpu_times = (0, 0);
        self.sensor_groups, self.sensor_layouts, self.sensor_value_labels = {}, {}, {};
        self.sensor_error_label = None
        self.init_ui();
        self.init_worker_thread();
        self.load_initial_state()
        self.monitor_timer = QTimer(self);
        self.monitor_timer.timeout.connect(self.on_monitor_timeout);
        self.monitor_timer.start(2000)

    def init_ui(self):
        main_layout = QVBoxLayout(self);
        main_layout.setContentsMargins(15, 15, 15, 15)
        header_container = QWidget();
        header_container.setMinimumHeight(60)
        icon_label = QLabel(header_container);
        logo_pixmap = QPixmap(os.path.join(GUI_RESOURCES_PATH, 'img/logo.png'));
        icon_label.setPixmap(logo_pixmap.scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation));
        icon_label.move(0, 0)
        title_label = QLabel("ampurr", header_container);
        title_label.setStyleSheet("font-size: 19pt; font-weight: normal;");
        title_label.move(50, 22);
        title_label.adjustSize()
        main_layout.addWidget(header_container);
        main_layout.addSpacing(10)

        self.tab_bar_layout = QHBoxLayout()
        self.btn_power = IconTextButton(os.path.join(GUI_RESOURCES_PATH, 'img/icon_power.png'), "Power Control")
        self.btn_usage = IconTextButton(os.path.join(GUI_RESOURCES_PATH, 'img/icon_resources.png'), "System Usage")
        self.btn_sensors = IconTextButton(os.path.join(GUI_RESOURCES_PATH, 'img/icon_sensors.png'), "Sensors")
        self.tab_buttons = [self.btn_power, self.btn_usage, self.btn_sensors]
        self.tab_bar_layout.addWidget(self.btn_power);
        self.tab_bar_layout.addWidget(self.btn_usage);
        self.tab_bar_layout.addWidget(self.btn_sensors)
        main_layout.addLayout(self.tab_bar_layout)

        self.pages_widget = QStackedWidget()
        power_tab, usage_tab, sensors_tab = QWidget(), QWidget(), QWidget()
        self.setup_power_control_tab(power_tab);
        self.setup_usage_monitor_tab(usage_tab);
        self.setup_sensors_tab(sensors_tab)
        self.pages_widget.addWidget(power_tab);
        self.pages_widget.addWidget(usage_tab);
        self.pages_widget.addWidget(sensors_tab)
        main_layout.addWidget(self.pages_widget);
        main_layout.addStretch()

        self.btn_power.clicked.connect(lambda: self.change_page(0));
        self.btn_usage.clicked.connect(lambda: self.change_page(1));
        self.btn_sensors.clicked.connect(lambda: self.change_page(2))
        self.change_page(0)

        self.setWindowTitle("Ampurr Dashboard");
        self.setFixedSize(750, 580);
        self.show()

    def change_page(self, index):
        self.pages_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            is_active = (i == index)
            btn.setProperty("active-tab", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            text_label = btn.findChild(QLabel, "tab_text")
            if text_label:
                text_label.style().unpolish(text_label)
                text_label.style().polish(text_label)
        self.style().unpolish(self)
        self.style().polish(self)

    def init_worker_thread(self):
        self.worker_thread = QThread();
        self.data_fetcher = DataFetcher();
        self.data_fetcher.moveToThread(self.worker_thread);
        self.data_fetcher.dataReady.connect(self.update_monitors_from_worker);
        self.worker_thread.start()

    def setup_power_control_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(15)

        battery_group = QGroupBox("Battery Charge Limit")
        battery_group.setMinimumHeight(125)
        battery_layout = QVBoxLayout(battery_group)
        self.limit_label = QLabel("Set Limit to: 100%")
        self.limit_slider = QSlider(Qt.Horizontal)
        self.limit_slider.setRange(50, 100)
        self.limit_slider.setTickInterval(10)
        self.limit_slider.setTickPosition(QSlider.TicksBelow)
        self.limit_slider.valueChanged.connect(self.update_battery_label)
        apply_battery_button = QPushButton("Apply Battery Limit")
        apply_battery_button.clicked.connect(self.apply_battery_limit)
        battery_layout.addWidget(self.limit_label)
        battery_layout.addWidget(self.limit_slider)
        battery_layout.addWidget(apply_battery_button)

        # create groupbox for cpu controls
        cpu_group = QGroupBox("CPU Power Profile")
        cpu_group.setMinimumHeight(125)
        # create a main vertical layout for it
        cpu_group_layout = QVBoxLayout(cpu_group)
        # create a separate horizontal layout for the buttons
        button_layout = QHBoxLayout()
        self.btn_powersave, self.btn_balanced, self.btn_performance = QPushButton("Powersave"), QPushButton(
            "Balanced"), QPushButton("Performance")
        self.btn_powersave.clicked.connect(lambda: self.set_cpu_governor("powersave"))
        self.btn_performance.clicked.connect(lambda: self.set_cpu_governor("performance"))
        # add buttons to their horizontal layout
        button_layout.addWidget(self.btn_powersave)
        button_layout.addWidget(self.btn_balanced)
        button_layout.addWidget(self.btn_performance)
        # add some spacing and the button layout to the main group layout
        cpu_group_layout.addSpacing(15)
        cpu_group_layout.addLayout(button_layout)
        # create and add the status label to the main group layout
        self.cpu_status_label = QLabel("Current Profile: Unknown")
        cpu_group_layout.addWidget(self.cpu_status_label, alignment=Qt.AlignCenter)

        # github link container
        github_container = QWidget()
        github_layout = QVBoxLayout()
        github_layout.setContentsMargins(0, 40, 0, 10)
        github_layout.setAlignment(Qt.AlignBottom)
        github_link = QLabel(
            '<a href="https://github.com/vzalxndr" style="color:#ffffff; text-decoration:none; font-weight: lighter;">GitHub @vzalxndr</a>')
        github_link.setAlignment(Qt.AlignCenter)
        github_link.setOpenExternalLinks(True)
        github_layout.addWidget(github_link)
        github_container.setLayout(github_layout)

        # add the finished groups to the main tab layout
        layout.addWidget(battery_group)
        layout.addWidget(cpu_group)
        layout.addWidget(github_container)
        layout.addStretch()

    def setup_usage_monitor_tab(self, tab):
        layout = QVBoxLayout(tab);
        layout.setContentsMargins(15, 20, 15, 15);
        layout.setSpacing(15)
        cpu_group = QGroupBox("CPU Usage");
        cpu_layout = QVBoxLayout(cpu_group);
        self.cpu_progress_bar = QProgressBar();
        cpu_layout.addWidget(self.cpu_progress_bar)
        ram_group = QGroupBox("Memory (RAM) Usage");
        ram_layout = QVBoxLayout(ram_group);
        self.ram_label = QLabel("Used: ? GB / ? GB");
        self.ram_progress_bar = QProgressBar()
        ram_layout.addWidget(self.ram_label);
        ram_layout.addWidget(self.ram_progress_bar)
        proc_group = QGroupBox("Top Processes (by CPU)");
        proc_layout = QVBoxLayout(proc_group);
        self.proc_text_edit = QTextEdit();
        self.proc_text_edit.setReadOnly(True);
        self.proc_text_edit.setFont(QFont("Monospace"));
        proc_layout.addWidget(self.proc_text_edit)
        layout.addWidget(cpu_group);
        layout.addWidget(ram_group);
        layout.addWidget(proc_group)

    def setup_sensors_tab(self, tab):
        main_layout = QVBoxLayout(tab);
        main_layout.setContentsMargins(0, 10, 0, 0);
        scroll = QScrollArea();
        scroll.setWidgetResizable(True);
        main_layout.addWidget(scroll)
        self.sensors_widget = QWidget();
        self.sensors_layout = QVBoxLayout(self.sensors_widget);
        self.sensors_layout.setContentsMargins(15, 10, 15, 15);
        self.sensors_layout.setSpacing(10);
        self.sensors_layout.setAlignment(Qt.AlignTop);
        scroll.setWidget(self.sensors_widget)

    def on_monitor_timeout(self):
        self.update_cpu_and_ram_usage();
        # invoke data fetch method in worker thread
        QMetaObject.invokeMethod(self.data_fetcher, "fetch_data", Qt.QueuedConnection)

    def update_cpu_and_ram_usage(self):
        idle, total = self.get_cpu_times()
        if self.last_cpu_times[1] > 0:
            delta_total = total - self.last_cpu_times[1];
            delta_idle = idle - self.last_cpu_times[0]
            if delta_total > 0: cpu_usage = max(0.0, min(100.0, (
                    1.0 - delta_idle / delta_total) * 100)); self.cpu_progress_bar.setValue(
                int(cpu_usage)); self.cpu_progress_bar.setFormat(f"{cpu_usage:.1f}%")
        self.last_cpu_times = (idle, total)
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines();
                mem_total = int(lines[0].split()[1]) / 1024 ** 2;
                mem_available = int(
                    lines[2].split()[1]) / 1024 ** 2;
                mem_used = mem_total - mem_available;
                self.ram_label.setText(
                    f"Used: {mem_used:.1f} GB / {mem_total:.1f} GB");
                self.ram_progress_bar.setValue(
                    int((mem_used / mem_total) * 100))
        except Exception:
            self.ram_label.setText("Could not read memory info")

    def update_monitors_from_worker(self, data):
        ps_output = data.get('ps', "Error");
        self.proc_text_edit.setText(
            "\n".join(ps_output.splitlines()[:7]) if "Error" not in ps_output else "Could not get process list");
        sensor_data = data.get('sensors', {"Error": "No data from worker"});
        self.update_sensors_tab_ui(sensor_data)

    def update_sensors_tab_ui(self, sensor_data):
        if "Error" in sensor_data:
            if not self.sensor_error_label:
                for i in reversed(range(self.sensors_layout.count())): self.sensors_layout.itemAt(i).widget().setParent(
                    None)
                self.sensor_groups.clear();
                self.sensor_layouts.clear();
                self.sensor_value_labels.clear();
                self.sensor_error_label = QLabel(sensor_data["Error"]);
                self.sensor_error_label.setWordWrap(True);
                self.sensor_error_label.setAlignment(Qt.AlignCenter);
                self.sensors_layout.addWidget(self.sensor_error_label)
            else:
                self.sensor_error_label.setText(sensor_data["Error"])
            return
        if self.sensor_error_label: self.sensor_error_label.setParent(None); self.sensor_error_label = None
        for full_name, value in sorted(sensor_data.items()):
            device_name, label_name = full_name.split(' - ', 1);
            category = "System"
            for key, cat in self.CATEGORY_MAP.items():
                if key in device_name: category = cat; break
            if category not in self.sensor_groups:
                group_box = QGroupBox(category);
                form_layout = QFormLayout(group_box);
                form_layout.setContentsMargins(10, 10, 10, 10);
                form_layout.setSpacing(8);
                self.sensors_layout.addWidget(group_box);
                self.sensor_groups[category] = group_box;
                self.sensor_layouts[category] = form_layout
            if full_name in self.sensor_value_labels:
                self.sensor_value_labels[full_name].setText(value)
            else:
                display_label = QLabel(f"{label_name}:");
                value_label = QLabel(value);
                value_label.setStyleSheet(
                    "font-weight: bold;");
                self.sensor_layouts[category].addRow(display_label, value_label);
                self.sensor_value_labels[full_name] = value_label

    def get_cpu_times(self):
        try:
            with open('/proc/stat', 'r') as f:
                parts = f.readline().strip().split();
                return int(parts[4]), sum(map(int, parts[1:]))
        except Exception as e:
            print(f"Error reading CPU times: {e}");
            return 0, 0

    def run_command(self, command, check=False):
        try:
            return subprocess.run(command, capture_output=True, text=True, check=check, timeout=40).stdout.strip()
        except Exception:
            return f"Error: Command '{command[0]}' failed."

    def load_initial_state(self):
        limit_output = self.run_command(["ampurr", "battery", "get"])
        if ':' in limit_output:
            try:
                limit = int(limit_output.split(":")[1].strip().replace('%', ''));
                self.limit_slider.setValue(
                    limit);
                self.update_battery_label(limit)
            except (ValueError, IndexError):
                self.limit_label.setText("Could not parse battery limit")
        else:
            self.limit_label.setText("Could not get battery limit")
        self.configure_cpu_buttons();
        self.update_cpu_status();
        self.on_monitor_timeout()

    def configure_cpu_buttons(self):
        output = self.run_command(["ampurr", "cpu", "list"])
        if "available governors" in output:
            try:
                available_govs = output.splitlines()[-1].strip().split();
                self.btn_powersave.setEnabled("powersave" in available_govs);
                self.btn_performance.setEnabled("performance" in available_govs);
                balanced_gov = "schedutil" if "schedutil" in available_govs else "ondemand"
                if balanced_gov in available_govs:
                    self.btn_balanced.setEnabled(True);
                    self.btn_balanced.clicked.connect(
                        lambda: self.set_cpu_governor(balanced_gov));
                    self.btn_balanced.setText(
                        f"Balanced ({balanced_gov})")
                else:
                    self.btn_balanced.setEnabled(False)
            except Exception:
                self.disable_all_cpu_buttons()
        else:
            self.disable_all_cpu_buttons()

    def disable_all_cpu_buttons(self):
        self.btn_powersave.setEnabled(False);
        self.btn_balanced.setEnabled(False);
        self.btn_performance.setEnabled(False);
        self.cpu_status_label.setText("Could not detect CPU profiles")

    def update_cpu_status(self):
        governor_output = self.run_command(["ampurr", "cpu", "status"]);
        buttons = [self.btn_powersave, self.btn_balanced, self.btn_performance]
        for btn in buttons: btn.setProperty("active-profile", False)
        if 'governor' in governor_output and ':' in governor_output:
            current_gov = governor_output.split(':')[1].strip();
            self.cpu_status_label.setText(f"Current Profile: {current_gov}")
            if current_gov == "powersave":
                self.btn_powersave.setProperty("active-profile", True)
            elif current_gov == "performance":
                self.btn_performance.setProperty("active-profile", True)
            else:
                self.btn_balanced.setProperty("active-profile", True)
        else:
            self.cpu_status_label.setText("Status: Error reading CPU profile")
        for btn in buttons: btn.style().unpolish(btn); btn.style().polish(btn)

    def update_battery_label(self, value):
        self.limit_label.setText(f"Set Limit to: {value}%")

    def apply_battery_limit(self):
        self.run_command(["pkexec", "ampurr", "battery", "set", str(self.limit_slider.value())])

    def set_cpu_governor(self, governor):
        self.run_command(["pkexec", "ampurr", "cpu", "set", governor]);
        self.update_cpu_status()

    def closeEvent(self, event):
        self.monitor_timer.stop();
        self.worker_thread.quit()
        if not self.worker_thread.wait(3000): self.worker_thread.terminate(); self.worker_thread.wait()
        event.accept()


# --- main execution block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    ex = AmpurrGUI()
    sys.exit(app.exec_())