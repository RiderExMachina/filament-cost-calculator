import json, os, shutil, sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QLabel, QComboBox, QTextEdit, QLineEdit, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFormLayout, QToolBar

class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()


        layout = QVBoxLayout()
        price_form = QFormLayout()
        hourly_cost_form = QFormLayout()
        btn_box = QHBoxLayout()

        price_label = QLabel("&Prices per Kilo:")
        self.price_list = QTextEdit()
        price_label.setBuddy(self.price_list)
        price_form.addRow(price_label, self.price_list)

        pcph_label = QLabel("&Premium Cost")
        self.pcph_entry = QLineEdit()
        pcph_label.setBuddy(self.pcph_entry)

        ocph_label = QLabel("&Offtime Cost")
        self.ocph_entry = QLineEdit()
        ocph_label.setBuddy(self.ocph_entry)

        hourly_cost_form.addRow(pcph_label, self.pcph_entry)
        hourly_cost_form.addRow(ocph_label, self.ocph_entry)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.gather_data)
        btn_box.addWidget(save_button)

        layout.addLayout(price_form)
        layout.addLayout(hourly_cost_form)
        layout.addLayout(btn_box)

        self.pull_existing()
        self.setLayout(layout)

    def gather_data(self):
        data = {}
        kilo_prices = self.price_list.toPlainText().split("\n")
        pcph = self.pcph_entry.text()
        ocph = self.ocph_entry.text()

        data["kilo-cost"] = kilo_prices
        data["prem-hrly"] = pcph
        data["std-hrly"]  = ocph

        save_info(data)

    def pull_existing(self):
        data = load_info()

        kilo_prices = ",".join(data["kilo-cost"])
        self.price_list.setText(kilo_prices.replace(",", "\n"))
        self.pcph_entry.setText(str(data["prem-hrly"]))
        self.ocph_entry.setText(str(data["std-hrly"]))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.data = load_info()

        self.setWindowTitle("Filament Cost Calculator")
        widget = QWidget()

        layout = QVBoxLayout()
        form = QFormLayout()

        self.banner = QLabel()
        banner_font = self.banner.font()
        banner_font.setPointSize(24)
        self.banner.setFont(banner_font)
        self.banner.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        filament_cost_label = QLabel("Filament Cost per kg:")
        self.filament_cost_entry = QComboBox()
        self.filament_cost_entry.addItems(self.data["kilo-cost"])
        self.ppkilo = float(self.data["kilo-cost"][0])
        self.filament_cost_entry.currentTextChanged.connect(self.filament_cost)
        form.addRow(filament_cost_label, self.filament_cost_entry)

        print_weight_label = QLabel("&Grams used in print:")
        self.print_weight_entry = QLineEdit()
        print_weight_label.setBuddy(self.print_weight_entry)
        form.addRow(print_weight_label, self.print_weight_entry)

        print_time_label = QLabel("&Time to print:")
        self.print_time_entry = QLineEdit()
        print_time_label.setBuddy(self.print_time_entry)
        self.print_time_entry.returnPressed.connect(self.calculate_options)
        form.addRow(print_time_label, self.print_time_entry)

        on_time_label = QLabel("Printed at work/sleep (&F)")
        self.on_time = QCheckBox()
        on_time_label.setBuddy(self.on_time)
        form.addRow(on_time_label, self.on_time)

        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculate_options)

        layout.addLayout(form)
        layout.addWidget(self.banner)

        layout.addWidget(calculate_button)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        menu_bar = self.menuBar()

        settings_button = QAction("Settings", self)
        settings_button.setStatusTip("Manage Settings")
        settings_button.triggered.connect(self.show_settings)
        menu_bar.addAction(settings_button)

    def show_settings(self):
        dlg = SettingsWindow().exec()

    def filament_cost(self, cost):
        self.ppkilo = float(cost)
        print(f"Set price: {cost} per kg ({ float(cost) / 1000 } per g)")

    def calculate_options(self):
        good = False
        wtprint = self.print_weight_entry.text()
        ttprint = self.print_time_entry.text()
        if wtprint == "":
            self.banner.setText("Needs Weight!")
            print("Needs Weight!")
        if ttprint == "":
            self.banner.setText("Needs Time!")
            print("Needs Time!")
            good = False
        elif ttprint != "" and wtprint != "":
            wtprint = float(wtprint)
            good = True

        if good:
            if self.on_time.isChecked():
                pphour = float(self.data["std-hrly"])
            if not self.on_time.isChecked():
                pphour = float(self.data["prem-hrly"])
            if "h" in ttprint:
                hours = int(ttprint.split("h")[0]) * 60
                minutes = ttprint.split("h")[1].replace("m", "")
                if minutes != "":
                    minutes = int(minutes)
                else:
                    minutes = 0
                ttprint = hours + minutes
            else:
                ttprint = int(ttprint.replace("m", ""))

            total_price = self.calc_price(pphour, ttprint, wtprint, self.ppkilo)
            print(f"Print weighs {wtprint} g, will take {ttprint} minutes, and will cost {(float(self.ppkilo)/1000) * wtprint} in filament to print")
            print(f"Print will cost {pphour * (ttprint / 60)} at {pphour}/hour")
            self.banner.setText(f"Print will cost ${total_price}")
    def calc_price(self, hour, time, weight, kilo):
        print(f"{Qt.CheckState.Checked.value}")
        hour_price = hour * time/60
        print(f"Price per hour: {hour_price}")
        weight_price = (float(kilo)/1000) * weight
        print(f"Price for print: {weight_price}")
        total_price = hour_price + weight_price

        return round(total_price, 2)

def config_info():
    system = sys.platform

    config_dir = os.path.expanduser("~")

    match system:
        case 'win32':
            print("Appears we are running on a Windows Machine")
            config_folder = os.path.join(config_dir, "AppData", "filcalc")
        case 'darwin':
            print("Appears we are running on a Mac")
            config_folder = os.path.join(config_dir, ".config", "filcalc")
        case 'linux':
            #print("Appears we are running on Linux")
            config_folder = os.path.join(config_dir, ".config", "filcalc")
            #print(f"Setting config_folder as {config_folder}")

    if not os.path.exists(config_folder):
        print(f"\t- '{config_folder}' does not appear to exist. Making one.")
        os.mkdir(config_folder)

    config_file = os.path.join(config_folder, "settings.json")
    return config_file

def load_info():
    settings_file = config_info()

    if os.path.isfile(settings_file):
        print("Loading existing data")
        with open(settings_file, 'r') as config:
            data = json.load(config)
    else:
        data = {
                "kilo-cost": [
                    "17.99",
                    "13.99"
                ],
                "prem-hrly": 2.5,
                "std-hrly": 0.5
            }
    return data

def save_info(data):
    settings_file = config_info()
   #print(f"Saving new data to {settings_file}")

    with open(settings_file+".new", 'w') as new_file:
        json.dump(data, new_file, indent=4)

    shutil.copy(settings_file+".new", settings_file)
    print("Save successful!")

if __name__ == "__main__":
    VERSION = "0.1"
    print(f"Starting FCC version {VERSION}")
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
