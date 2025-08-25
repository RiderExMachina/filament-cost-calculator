import json, os, shutil, sys, time
from PyQt6.QtCore import Qt, QTimer, QRegularExpression
from PyQt6.QtGui import QAction, QKeySequence, QIntValidator, QDoubleValidator, QRegularExpressionValidator
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QLabel, QScrollArea, QComboBox, QTextEdit, QLineEdit, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFormLayout, QToolBar

class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(2500)
        self.timer.timeout.connect(self.clear_message)

        layout = QVBoxLayout()
        price_form = QFormLayout()
        hourly_cost_form = QFormLayout()
        printer_options_form = QFormLayout()
        btn_box = QHBoxLayout()

        self.feedback = QLabel()

        price_label = QLabel("Prices per &Kilo:")
        self.price_list = QTextEdit()
        price_label.setBuddy(self.price_list)
        price_form.addRow(price_label, self.price_list)

        pcph_label = QLabel("&Premium Cost")
        self.pcph_entry = QLineEdit()
        self.pcph_entry.setValidator(QDoubleValidator())
        pcph_label.setBuddy(self.pcph_entry)

        ocph_label = QLabel("&Offtime Cost")
        self.ocph_entry = QLineEdit()
        self.ocph_entry.setValidator(QDoubleValidator())
        ocph_label.setBuddy(self.ocph_entry)

        hourly_cost_form.addRow(pcph_label, self.pcph_entry)
        hourly_cost_form.addRow(ocph_label, self.ocph_entry)

        num_printers_label = QLabel("&Number of Printers:")
        self.num_printers = QLineEdit()
        self.num_printers.setValidator(QIntValidator())
        num_printers_label.setBuddy(self.num_printers)

        printer_options_form.addRow(num_printers_label, self.num_printers)


        save_button = QPushButton("Save")
        save_button.clicked.connect(self.gather_data)
        save_and_quit = QPushButton("Save and Close")
        save_and_quit.clicked.connect(self.saq)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        btn_box.addWidget(save_button)
        btn_box.addWidget(save_and_quit)
        btn_box.addWidget(cancel_button)

        layout.addLayout(price_form)
        layout.addLayout(hourly_cost_form)
        layout.addLayout(printer_options_form)
        layout.addWidget(self.feedback)
        layout.addLayout(btn_box)

        self.pull_existing()
        self.setLayout(layout)

    def gather_data(self):
        data = {}
        kilo_prices = self.price_list.toPlainText().split("\n")
        pcph = self.pcph_entry.text()
        ocph = self.ocph_entry.text()
        printers = self.num_printers.text()

        data["kilo-cost"] = kilo_prices
        data["prem-hrly"] = pcph
        data["std-hrly"]  = ocph
        data["printers"] = printers

        result = save_info(data)
        if result:
            if not self.timer.isActive():
                self.feedback.setText("Saved!")
                self.timer.start()

    def saq(self):
        self.gather_data()
        self.close()

    def pull_existing(self):
        data = load_info()

        kilo_prices = ",".join(data["kilo-cost"])
        self.price_list.setText(kilo_prices.replace(",", "\n"))
        self.pcph_entry.setText(str(data["prem-hrly"]))
        self.ocph_entry.setText(str(data["std-hrly"]))

        try:
            ## Added in a later revision of the program. May be able to remove in the future.
            self.num_printers.setText(str(data["printers"]))
        except KeyError:
            self.num_printers.setText("1")

    def clear_message(self):
        self.feedback.clear()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        menu_bar = self.menuBar()

        settings_button = QAction("Settings", self)
        settings_button.setStatusTip("Manage Settings")
        settings_button.triggered.connect(self.show_settings)
        menu_bar.addAction(settings_button)

        refresh_button = QAction("Refresh", self)
        refresh_button.setStatusTip("Refresh information")
        refresh_button.triggered.connect(self.refresh)
        menu_bar.addAction(refresh_button)

        self.__create_ui__()


    def __create_ui__(self):
        self.data = load_info()
        self.printers = int(self.data["printers"])
        self.kilo_cost = self.data["kilo-cost"]


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
        self.filament_cost_entry.addItems(self.kilo_cost)
        self.ppkilo = float(self.kilo_cost[0])
        self.filament_cost_entry.currentIndexChanged.connect(self.filament_cost)
        form.addRow(filament_cost_label, self.filament_cost_entry)

        print_weight_label = QLabel("&Grams used in print:")
        self.print_weight_entry = QLineEdit()
        self.print_weight_entry.setValidator(QDoubleValidator())
        print_weight_label.setBuddy(self.print_weight_entry)
        form.addRow(print_weight_label, self.print_weight_entry)

        print_time_label = QLabel("&Time to print:")
        self.print_time_entry = QLineEdit()
        print_time_validator = QRegularExpressionValidator(
                QRegularExpression(r"\d+[HhMm]\d+[Mm]"), self.print_time_entry
            )
        self.print_time_entry.setValidator(print_time_validator)
        print_time_label.setBuddy(self.print_time_entry)
        self.print_time_entry.returnPressed.connect(self.calculate_options)
        form.addRow(print_time_label, self.print_time_entry)

        extra_label = QLabel("Extras:")
        extra_label_font = extra_label.font()
        extra_label_font.setPointSize(14)
        extra_label.setFont(extra_label_font)
        form.addRow(extra_label)

        on_time_label = QLabel("Printed at work/sleep (&F)")
        self.on_time = QCheckBox()
        on_time_label.setBuddy(self.on_time)
        account_printer_label = QLabel("A&ccount for printers in calculation")
        self.account_printers = QCheckBox()
        self.account_printers.setChecked(True)
        account_printer_label.setBuddy(self.account_printers)

        form.addRow(on_time_label, self.on_time)
        form.addRow(account_printer_label, self.account_printers)


        devel_time_label = QLabel("&Development Time:")
        self.devel_time_entry = QLineEdit()
        devel_time_validator = QRegularExpressionValidator(
                QRegularExpression(r"\d+[HhMm]\d+[Mm]"), self.devel_time_entry
            )
        self.devel_time_entry.setValidator(devel_time_validator)
        devel_time_label.setBuddy(self.devel_time_entry)
        self.devel_time_entry.returnPressed.connect(self.calculate_options)
        form.addRow(devel_time_label, self.devel_time_entry)

        assembly_time_label = QLabel("&Assembly Time (if applicable):")
        self.assembly_time_entry = QLineEdit()
        assembly_time_validator = QRegularExpressionValidator(
                QRegularExpression(r"\d+[HhMm]\d+[Mm]"), self.assembly_time_entry
            )
        self.assembly_time_entry.setValidator(assembly_time_validator)
        devel_time_label.setBuddy(self.devel_time_entry)
        assembly_time_label.setBuddy(self.assembly_time_entry)
        self.assembly_time_entry.returnPressed.connect(self.calculate_options)
        form.addRow(assembly_time_label, self.assembly_time_entry)

        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculate_options)

        extras_layout = QHBoxLayout()
        self.dev_banner = QLabel()
        self.assm_banner = QLabel()
        extras_layout.addWidget(self.dev_banner)
        extras_layout.addWidget(self.assm_banner)

        self.breakdown = QLabel()


        layout.addLayout(form)
        layout.addWidget(self.banner)
        layout.addLayout(extras_layout)
        layout.addWidget(self.breakdown)
        layout.addWidget(calculate_button)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def refresh(self):
        print("Refreshing window")
        temp_weight = self.print_weight_entry.text()
        temp_time = self.print_time_entry.text()
        self.__create_ui__()

        if temp_weight != "":
            self.print_weight_entry.setText(temp_weight)
        if temp_time != "":
            self.print_time_entry.setText(temp_time)

    def show_settings(self):
        dlg = SettingsWindow().exec()

    def filament_cost(self, cost):
        self.ppkilo = float(self.data["kilo-cost"][cost])
        print(f"Set price: {self.ppkilo} per kg ({ self.ppkilo / 1000 } per g)")

    def calculate_options(self):
        good = False
        wtprint = self.print_weight_entry.text().lower()
        ttprint = self.print_time_entry.text().lower()
        dev_time = self.devel_time_entry.text().lower()
        assemble = self.assembly_time_entry.text().lower()

        if wtprint == "":
            self.banner.setText("Needs Weight!")
            print("Needs Weight!")
        elif ttprint == "":
            self.banner.setText("Needs Time!")
            print("Needs Time!")
            good = False
        elif ttprint != "" and wtprint != "":
            wtprint = float(wtprint)
            good = True

        if dev_time != "":
            dev_time = split_time(dev_time)
            dev_cost = (dev_time / 60) * float(self.data["prem-hrly"])
            print(f"\t- Development costs: ${round(dev_cost, 2)}")
            self.dev_banner.setText(f"Development cost: \n${round(dev_cost, 2)}")
        if assemble != "":
            assemble = split_time(assemble)
            assm_cost = (assemble / 60) * float(self.data["prem-hrly"])
            print(f"\t- Estimated assembly cost: ${round(assm_cost, 2)}")
            self.assm_banner.setText(f"Assembly Cost: \n${round(assm_cost, 2)}")
        if dev_time == "":
            dev_cost = 0
        if assemble == "":
            assm_cost = 0

        if good:
            total_extra_cost = dev_cost + assm_cost
            if self.on_time.isChecked():
                pphour = float(self.data["std-hrly"])
            if not self.on_time.isChecked():
                pphour = float(self.data["prem-hrly"])

            ttprint = split_time(ttprint)

            total_price = self.calc_price(pphour, ttprint, wtprint, self.ppkilo)
            print(f"Print weighs {wtprint} g, will take {ttprint} minutes, and will cost {(float(self.ppkilo)/1000) * wtprint} in filament to print")
            print(f"Print will cost {pphour * (ttprint / 60)} at {pphour}/hour")
            self.banner.setText(f"Print will cost ${total_price}")

            sale_price = nearest_five(total_price)
            breakeven = (total_price + total_extra_cost) / (sale_price - total_price)
            if breakeven < 1:
                breakeven = 1
            print(f"\t- You would need to sell {breakeven} at ${sale_price} to break even.")
            self.breakdown.setText(f"You would need to sell {round(breakeven)} at ${sale_price} to break even.")
    def calc_price(self, hour, time, weight, kilo):
        ## Building out
        account_for_printers = self.account_printers.isChecked()
        hour_price = hour * time/60
        if account_for_printers:
            printers = self.printers
            hour_price = hour_price / printers
        print(f"Price per hour: {hour_price}")
        weight_price = (float(kilo)/1000) * weight
        print(f"Price for print: {weight_price}")
        total_price = hour_price + weight_price

        return round(total_price, 2)

def split_time(time_data):
    if "h" in time_data:
        hours = int(time_data.split("h")[0]) * 60
        minutes = time_data.split("h")[1].replace("m", "")
        if minutes != "":
            minutes = int(minutes)
        else:
            minutes = 0
        total_time = hours + minutes
    else:
        total_time = int(time_data.replace("m", ""))

    return total_time

def nearest_five(num1):
    num2 = 5
    while num2 < num1:
        num2 += 5
    return num2

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
                "std-hrly": 0.5,
                "printers": 1,
            }
    return data

def save_info(data):
    settings_file = config_info()
   #print(f"Saving new data to {settings_file}")

    with open(settings_file+".new", 'w') as new_file:
        json.dump(data, new_file, indent=4)

    shutil.copy(settings_file+".new", settings_file)
    print("Save successful!")
    return True

if __name__ == "__main__":
    VERSION = "0.5"
    print(f"Starting FCC version {VERSION}")
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
