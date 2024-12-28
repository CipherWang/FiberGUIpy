import sys

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QPushButton, QMessageBox
from datetime import datetime

from fiber_rpc import FiberRPC
from main_window import Ui_MainWindow
from threading import Timer


def show_error_message(data):
    """
    弹出错误提示框
    """
    # 创建错误提示框
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Icon.Critical)  # 设置为错误图标
    error_box.setWindowTitle("Error")  # 设置标题
    error_box.setText("RPC error has occurred!")  # 设置主要错误信息
    error_box.setInformativeText(data)  # 设置补充信息
    error_box.setStandardButtons(QMessageBox.StandardButton.Ok)  # 添加按钮
    error_box.setDefaultButton(QMessageBox.StandardButton.Ok)  # 设置默认按钮

    # 显示提示框
    error_box.exec()


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.btnConnect.clicked.connect(self.on_connect_click)
        self.ui.btnOpenChn.clicked.connect(self.on_open_channel)
        validator = QDoubleValidator(0.0, 1000000000.0, 8)  # 范围 [-100.0, 100.0]，精度 2 位小数
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)  # 标准表示法
        self.ui.txtChnAmount.setValidator(validator)
        self.ui.tableChn.itemClicked.connect(self.on_channel_item_clicked)
        self.ui.btnCloseChn.clicked.connect(self.on_close_channel_clicked)

    def on_connect_click(self):
        if self.update_node_info():
            # add url to combox
            comboxURL = self.ui.comboURL
            duplicated = False
            for i in range(comboxURL.count()):
                if comboxURL.currentText() == comboxURL.itemText(i):
                    duplicated = True
                    break
            if not duplicated:
                comboxURL.addItem(comboxURL.currentText())

        self.update_channels()

    def update_node_info(self):
        # clear
        tableChn = self.ui.tableChn
        self.ui.txtAlias.setText("Error!")
        self.ui.txtAddress.setText("")
        self.ui.txtPk.setText("")

        # Get node info
        rpc = FiberRPC(self.ui.comboURL.currentText())
        node_info = rpc.node_info()
        if node_info["code"] == "ok":
            self.ui.txtAlias.setText(node_info['data']['node_name'])
            self.ui.txtAddress.setText(node_info['data']['addresses'][0])
            self.ui.txtPk.setText(node_info['data']['public_key'])
            return True
        else:
            self.statusBar().showMessage("Failed to get node info")
            return False

    def update_channels(self):
        # clear
        self.ui.txtChID.setText("")
        tableChn = self.ui.tableChn
        while tableChn.rowCount() > 0:
            tableChn.removeRow(0)

        rpc = FiberRPC(self.ui.comboURL.currentText())
        # Get channel info
        channels = rpc.list_channels([{"include_closed": True}])
        if channels["code"] == "ok":
            for item in channels["data"]['channels']:
                row_count = tableChn.rowCount()
                tableChn.insertRow(row_count)
                tableChn.setItem(row_count, 0, QTableWidgetItem(item['channel_id']))
                tableChn.setItem(row_count, 1, QTableWidgetItem(item['peer_id']))
                coin = "CKB"
                if item['funding_udt_type_script'] is not None:
                    coin = item['funding_udt_type_script']
                tableChn.setItem(row_count, 2, QTableWidgetItem(coin))
                local_balance = str(int(item['local_balance'], 16) / 10 ** 8)
                remote_balance = str(int(item['remote_balance'], 16) / 10 ** 8)
                tableChn.setItem(row_count, 3, QTableWidgetItem(local_balance))
                tableChn.setItem(row_count, 4, QTableWidgetItem(remote_balance))
                local_time = datetime.fromtimestamp(int(item['created_at'], 16) / 1000.0)
                tableChn.setItem(row_count, 5, QTableWidgetItem(local_time.strftime("%Y-%m-%d %H:%M:%S")))
                tableChn.setItem(row_count, 6, QTableWidgetItem(item['state']['state_name']))
            self.statusBar().showMessage("Successfully list channels")
        else:
            self.statusBar().showMessage("Failed to list channels")
            return

    def async_update_channels(self):
        self.ui.txtChnAmount.setText("")
        self.ui.txtPeerID.setText("")
        self.update_channels()
        self.ui.btnOpenChn.setEnabled(True)

    def on_open_channel(self):
        if self.ui.txtPeerID.text() == "" or self.ui.txtChnAmount.text() == "":
            return
        self.ui.btnOpenChn.setEnabled(False)
        rpc = FiberRPC(self.ui.comboURL.currentText())
        peer_id = self.ui.txtPeerID.text()
        amount = float(self.ui.txtChnAmount.text())
        result = rpc.open_channel(peer_id, amount)
        if result["code"] == "ok":
            self.statusBar().showMessage("Successfully initialized the channel opening, refreshing...")
            Timer(5, self.async_update_channels).start()
        else:
            self.ui.btnOpenChn.setEnabled(True)
            show_error_message(result['data'])

    def on_channel_item_clicked(self, item):
        index = item.row()+1
        self.ui.txtChID.setText(str(index))

    def on_close_channel_clicked(self):
        if self.ui.txtChID.text() == "":
            return
        tableChn = self.ui.tableChn
        row = tableChn.currentRow()
        chn_id = tableChn.item(row, 0).text()
        rpc = FiberRPC(self.ui.comboURL.currentText())
        result = rpc.shutdown_channel(chn_id)
        if result["code"] == "error":
            show_error_message(result['data'])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
