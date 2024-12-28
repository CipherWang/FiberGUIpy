import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from datetime import datetime

from fiber_rpc import FiberRPC
from main_window import Ui_MainWindow

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 关联按钮点击信号与槽函数
        self.ui.btnConnect.clicked.connect(self.on_connect_click)

    def on_connect_click(self):
        rpc = FiberRPC(self.ui.urlEdit.text())
        node_info = rpc.node_info()
        if node_info["code"] == "ok":
            self.ui.txtAlias.setText(node_info['data']['node_name'])
            self.ui.txtAddress.setText(node_info['data']['addresses'][0])
            self.ui.txtPk.setText(node_info['data']['public_key'])
        else:
            self.ui.txtAlias.setText("Error!")
            self.ui.txtAddress.setText("")
            self.ui.txtPk.setText("")

        channels = rpc.list_channels([{"include_closed":False}])
        if channels["code"] == "ok":
            tableChn = self.ui.tableChn
            for item in channels["data"]['channels']:
                row_count = tableChn.rowCount()  # 获取当前行数
                tableChn.insertRow(row_count)  # 在末尾插入一行
                tableChn.setItem(row_count, 0, QTableWidgetItem(item['channel_id']))
                tableChn.setItem(row_count, 1, QTableWidgetItem(item['peer_id']))
                coin = "CKB"
                if item['funding_udt_type_script'] is not None:
                    coin = item['funding_udt_type_script']
                tableChn.setItem(row_count, 2, QTableWidgetItem(coin))
                local_balance = str(int(item['local_balance'], 16)/10**8)
                remote_balance = str(int(item['remote_balance'], 16) / 10 ** 8)
                tableChn.setItem(row_count, 3, QTableWidgetItem(local_balance))
                tableChn.setItem(row_count, 4, QTableWidgetItem(remote_balance))
                print(int(item['created_at'], 16))
                local_time = datetime.fromtimestamp(int(item['created_at'], 16)/1000.0)
                tableChn.setItem(row_count, 5, QTableWidgetItem(local_time.strftime("%Y-%m-%d %H:%M:%S")))
        else:
            self.ui.tableChn.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
