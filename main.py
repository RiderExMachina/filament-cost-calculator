import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QLabel, QComboBox, QLineEdit, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFormLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

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
        self.filament_cost_entry.addItems({"17.99":[17.99], "13.99": [13.99]})
        self.ppkilo = 17.99
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

    def filament_cost(self, cost):
        self.ppkilo = float(cost)
        print(f"Set price: {cost} per kg ({ float(cost) / 1000 } per g)")

    def calculate_options(self):
        wtprint = float(self.print_weight_entry.text())
        ttprint = self.print_time_entry.text()
        if wtprint == "":
            print("Needs Weight!")
        if ttprint == "":
            print("Needs Time!")

        else:
            if self.on_time.isChecked():
                pphour = .5
            if not self.on_time.isChecked():
                pphour = 2
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
            print(f"Print weighs {wtprint} g, will take {ttprint} minutes, and will cost {(float(self.ppkilo)/1000) * wtprint} to print")
            self.banner.setText(f"Print will cost ${total_price}")
    def calc_price(self, hour, time, weight, kilo):
        print(f"{Qt.CheckState.Checked.value}")
        hour_price = hour * time/60
        print(f"Price per hour: {hour_price}")
        weight_price = (float(kilo)/1000) * weight
        print(f"Price for print: {weight_price}")
        total_price = hour_price + weight_price

        return round(total_price, 2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
