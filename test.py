import sys
import os
import requests
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QListWidget,
                             QHBoxLayout, QMessageBox, QLineEdit, QSpinBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

load_dotenv()

class BaseWorker(QThread):
    request_finished = pyqtSignal(str, bool)

    def __init__(self, action, payload=None):
        super().__init__()
        self.flask_url = os.getenv('FLASK_URL')
        self.port = os.getenv('PORT')
        self.url = f"{self.flask_url}:{self.port}/"
        self.action = action
        self.payload = payload

class ServerWorker(BaseWorker):
    data_fetched = pyqtSignal(dict)
    
    def run(self):
        try:
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            if self.action == "get_all":
                response = requests.get(self.url + "get-all-items", headers=headers)
                if response.status_code == 200:
                    data_dict = {item[1]: item[2] for item in response.json().get('res', [])}
                    self.data_fetched.emit(data_dict)
                else:
                    self.data_fetched.emit({})
            elif self.action == "add":
                response = requests.post(self.url + "add-item", json=self.payload, headers=headers)
            elif self.action == "update":
                response = requests.put(self.url + "update-quantity", json=self.payload, headers=headers)
            elif self.action == "delete":
                response = requests.delete(self.url + "remove-item", json=self.payload, headers=headers)
            
            success = response.status_code in [200, 201]
            self.request_finished.emit(self.action, success)
        except Exception as e:
            print("Error in API request:", str(e))
            self.request_finished.emit(self.action, False)

class InventoryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Management")
        self.resize(400, 350)
        self.setStyleSheet("background-color: #2E3440; color: white; font-size: 14px;")
        self.inventory = {}
        self.initUI()
        self.loadInventory()
    
    def initUI(self):
        self.layout = QVBoxLayout()
        self.search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter item name")
        self.search_layout.addWidget(self.search_input)
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 100)
        self.quantity_input.setValue(1)
        self.search_layout.addWidget(self.quantity_input)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.addItem)
        self.search_layout.addWidget(self.add_button)
        
        self.layout.addLayout(self.search_layout)
        
        self.inventory_list = QListWidget()
        self.layout.addWidget(self.inventory_list)
        
        self.button_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("Buy Item")
        self.buy_button.clicked.connect(self.buyItem)
        self.button_layout.addWidget(self.buy_button)
        
        self.return_button = QPushButton("Return Item")
        self.return_button.clicked.connect(self.returnItem)
        self.button_layout.addWidget(self.return_button)
        
        self.delete_button = QPushButton("Delete Item")
        self.delete_button.clicked.connect(self.deleteItem)
        self.button_layout.addWidget(self.delete_button)
        
        self.status_button = QPushButton("Show Status")
        self.status_button.clicked.connect(self.showStatus)
        self.button_layout.addWidget(self.status_button)
        
        self.layout.addLayout(self.button_layout)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.loadInventory)
        self.layout.addWidget(self.refresh_button)
        
        # Processing Spinner
        self.spinner = QProgressBar()
        self.spinner.setRange(0, 0)
        self.spinner.setVisible(False)
        self.layout.addWidget(self.spinner, alignment=Qt.AlignRight)
        
        self.setLayout(self.layout)
    
    def showSpinner(self, show):
        self.spinner.setVisible(show)
    
    def loadInventory(self):
        self.showSpinner(True)
        self.worker = ServerWorker("get_all")
        self.worker.data_fetched.connect(self.populateInventory)
        self.worker.request_finished.connect(lambda action, success: self.showSpinner(False))
        self.worker.start()
    
    def populateInventory(self, items):
        self.inventory = items
        self.inventory_list.clear()
        for item, qty in items.items():
            self.inventory_list.addItem(f"{item} ({qty})")
    
    def addItem(self):
        item_name = self.search_input.text().strip()
        quantity = self.quantity_input.value()
        if item_name and item_name not in self.inventory:
            self.showSpinner(True)
            self.worker = ServerWorker("add", {"name": item_name, "quantity": quantity})
            self.worker.request_finished.connect(lambda action, success: self.handleResponse(action, success, item_name, quantity))
            self.worker.start()
        self.search_input.clear()
        self.quantity_input.clear()
    
    def getSelectedItem(self):
        selected = self.inventory_list.selectedItems()
        return selected[0].text().split(" (")[0] if selected else None
    
    def buyItem(self):
        item = self.getSelectedItem()
        if item:
            self.showSpinner(True)
            self.worker = ServerWorker("update", {"name": item, "quantity": self.inventory[item] + 1})
            self.worker.request_finished.connect(lambda action, success: self.handleResponse(action, success, item, 1))
            self.worker.start()
    
    def returnItem(self):
        item = self.getSelectedItem()
        if item and self.inventory[item] > 1:
            self.showSpinner(True)
            self.worker = ServerWorker("update", {"name": item, "quantity": self.inventory[item] - 1})
            self.worker.request_finished.connect(lambda action, success: self.handleResponse(action + 'R', success, item, -1))
            self.worker.start()
        elif item:
            self.deleteItem()
    
    def deleteItem(self):
        item = self.getSelectedItem()
        if item:
            self.showSpinner(True)
            self.worker = ServerWorker("delete", {"name": item})
            self.worker.request_finished.connect(lambda action, success: self.handleResponse(action, success, item, 0))
            self.worker.start()
    
    def showStatus(self):
        status = "\n".join([f"{item}: {qty}" for item, qty in self.inventory.items()])
        QMessageBox.information(self, "Inventory Status", status)
    
    def handleResponse(self, action, success, item, quantity):
        if success:
            if action == "add":
                self.inventory[item] = quantity
                self.inventory_list.addItem(f"{item} ({quantity})")
            elif action == "update":
                self.inventory[item] += quantity
                self.loadInventory()  # Refresh list
            elif action == "delete":
                self.inventory.pop(item, None)
                self.loadInventory()
            elif action == "updateR":
                self.inventory[item] -= 1
                if self.inventory[item] == 0:
                    self.inventory.pop(item)
                self.loadInventory()
        else:
            QMessageBox.warning(self, "Error", f"Failed to {action} item: {item}")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryApp()
    window.show()
    sys.exit(app.exec_())