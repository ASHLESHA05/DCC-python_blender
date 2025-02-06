import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QListWidget, QHBoxLayout, QListWidgetItem, QMessageBox, QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import time
from dotenv import load_dotenv
import os
import requests

load_dotenv()

class ServerWorker(QThread):
    data_fetched = pyqtSignal(dict)
    
    def run(self):
        time.sleep(2)

        self.flask_url = os.getenv('FLASK_URL')
        self.port = os.getenv('PORT')

        self.url = f"{self.flask_url}:{self.port}/get-all-items"  
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.get(self.url, headers=headers) 
            self.data_dict={}
            if response.status_code == 200:
                print("Response: ",response.json())
                data = response.json()['res']
                for i in data:
                    self.data_dict[i[1]]=i[2]
            else:
                print('Bad Request returned with status code ',response.status_code)
            
        except Exception as e:
            print("Failed Error!! ",str(e))

        self.data_fetched.emit(
            self.data_dict
        )

class InventoryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Management")
        self.resize(300, 300)
        self.setStyleSheet("background-color: #2E3440; color: white; font-size: 14px;")
        self.inventory = {}
        self.initUI()
        self.loadInventory()
        self.flask_url = os.getenv('FLASK_URL')
        self.port = os.getenv('PORT')

        self.url = f"{self.flask_url}:{self.port}/"  
    
    def initUI(self):
        self.layout = QVBoxLayout()
        
        # Add search layout
        self.search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3B4252;
                color: white;
                padding: 8px;
                border-radius: 5px;
                border: none;
            }
        """)
        self.search_input.setPlaceholderText("Enter item name")
        self.search_layout.addWidget(self.search_input)
        
        self.add_button = QPushButton("Add")
        self.add_button.setStyleSheet("background-color: #81A1C1; padding: 8px; border-radius: 5px; color: black")
        self.add_button.clicked.connect(self.addItem)
        self.search_layout.addWidget(self.add_button)
        
        self.layout.addLayout(self.search_layout)
        
        self.inventory_list = QListWidget()
        self.inventory_list.setSelectionMode(QListWidget.SingleSelection)
        self.inventory_list.setStyleSheet("""
            QListWidget {
                background-color: #3B4252;
                color: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                min-width: 250px;
            }
            QListWidget::item:selected {
                background-color: #5E81AC;
            }
        """)
        self.layout.addWidget(self.inventory_list)
        
        self.button_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("Buy Item")
        self.buy_button.setStyleSheet("background-color: #88C0D0; padding: 8px; border-radius: 5px; color: black")
        self.buy_button.clicked.connect(self.buyItem)
        self.button_layout.addWidget(self.buy_button)
        
        self.return_button = QPushButton("Return Item")
        self.return_button.setStyleSheet("background-color: #D08770; padding: 8px; border-radius: 5px; color: black")
        self.return_button.clicked.connect(self.returnItem)
        self.button_layout.addWidget(self.return_button)
        
        self.delete_button = QPushButton("Delete Item")
        self.delete_button.setStyleSheet("background-color: #BF616A; padding: 8px; border-radius: 5px; color: black")
        self.delete_button.clicked.connect(self.deleteItem)
        self.button_layout.addWidget(self.delete_button)
        
        self.status_button = QPushButton("Show Status")
        self.status_button.setStyleSheet("background-color: #A3BE8C; padding: 8px; border-radius: 5px; color: black")
        self.status_button.clicked.connect(self.showStatus)
        self.button_layout.addWidget(self.status_button)
        
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def addItem(self):
        item_name = self.search_input.text().strip()
        if item_name:
            if item_name not in self.inventory:
                self.inventory[item_name] = 1

                # Add the item to database
                try:
                    response = requests.post(self.url + 'add-item', json={'name': item_name, 'quantity': 1})
                    if response.status_code == 201:
                        print("Added to database successfully")
                        self.inventory_list.addItem(item_name)
                        self.search_input.clear()
                    else:
                        print("Error adding to db", response.json())
                        QMessageBox.warning(self, "Error", f"Failed to add item: {response.json().get('message')}")
                except Exception as e:
                    print("Error adding item to database:", str(e))
                    QMessageBox.warning(self, "Error", "Could not connect to the server!")
            else:
                QMessageBox.warning(self, "Error", "Item already exists!")
    
    def loadInventory(self):
        self.worker = ServerWorker()
        self.worker.data_fetched.connect(self.populateInventory)
        self.worker.start()
    
    def populateInventory(self, items):
        self.inventory = items
        self.inventory_list.clear()
        for item in items:
            self.inventory_list.addItem(item)
    
    def getSelectedItem(self):
        selected = self.inventory_list.selectedItems()
        return selected[0].text() if selected else None
    
    def buyItem(self):
        item = self.getSelectedItem()
        if item and self.inventory[item] > 0:
            self.inventory[item] += 1
            # Update Database
            try:
                self.res = requests.put(self.url+'update-quantity',json={'name':str(item), 'quantity':str(self.inventory[item])})
                if self.res.status_code == 200:
                    print("Updated successfully")
                else:
                    print("Error in Updating  db ",self.res.status_code)
            except Exception as e:
                    print("Error in Updating quantity of database: ",str(e))
            print(f"Buying: {item}")
        else:
            QMessageBox.warning(self, "Error", "No item selected or out of stock!")
    
    def returnItem(self):
        item = self.getSelectedItem()
        if item:
            self.inventory[item] -= 1
            if self.inventory[item] > 0:
                try:
                    self.res = requests.put(self.url+'update-quantity',json={'name':str(item), 'quantity':str(self.inventory[item])})
                    if self.res.status_code == 200:
                        print("Updated successfully")
                    else:
                        print("Error in Updating  db ",self.res.status_code)
                except Exception as e:
                        print("Error in Updating quantity of database: ",str(e))
            else:
                try:
                    self.res = requests.delete(self.url+'remove-item',json={'name':str(item), 'quantity':str(self.inventory[item])})
                    if self.res.status_code == 200:
                        print("Delete successfully")
                    else:
                        print("Error in Deleting item from db ",self.res.status_code)
                except Exception as e:
                        print("Error in Deleting item from database: ",str(e))
            print(f"Returning: {item}")
        else:
            QMessageBox.warning(self, "Error", "No item selected!")
    
    def deleteItem(self):
        item = self.getSelectedItem()
        if item:
            try:
                self.res = requests.delete(self.url+'remove-item',json={'name':str(item), 'quantity':str(self.inventory[item])})
                if self.res.status_code == 200:
                    print(f"Deleted item: {item}")
                    # Remove from dictionary and list widget
                    self.inventory.pop(item)
                    self.inventory_list.takeItem(self.inventory_list.currentRow())
                else:
                    print("Error in Deleting item from db ",self.res.status_code)
            except Exception as e:
                print("Error in Deleting item from database: ",str(e))
        else:
            QMessageBox.warning(self, "Error", "No item selected!")

    def showStatus(self):
        status = "\n".join([f"{item}: {qty} " for item, qty in self.inventory.items()])
        QMessageBox.information(self, "Inventory Status", status)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryApp()
    window.show()
    sys.exit(app.exec_())