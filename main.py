import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QPushButton, QMessageBox, QGraphicsPixmapItem
from datetime import datetime

from fiber_rpc import FiberRPC
from main_window import Ui_MainWindow
from threading import Timer

import qrcode

def generate_qr_code(data, size):
    img = qrcode.make(data)
    return QPixmap.fromImage(img.toqimage())


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.payment_hash = None
        self.qr_data = None
        self.nodes_info = []
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.btnConnect.clicked.connect(self.on_connect_click)
        self.ui.btnOpenChn.clicked.connect(self.on_open_channel)
        validator = QDoubleValidator(0.0, 1000000000.0, 8)  # 范围 [-100.0, 100.0]，精度 2 位小数
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)  # 标准表示法
        self.ui.txtChnAmount.setValidator(validator)
        self.ui.txtPayAmount.setValidator(validator)
        self.ui.tableChn.itemClicked.connect(self.on_channel_item_clicked)
        self.ui.btnCloseChn.clicked.connect(self.on_close_channel_clicked)
        self.ui.btnRefreshNode.clicked.connect(self.on_node_refresh_clicked)
        self.ui.checkIPOnly.checkStateChanged.connect(self.on_node_filter_changed)
        self.ui.btnRefreshChn.clicked.connect(self.update_channels)
        self.ui.btnGenInvoice.clicked.connect(self.on_gen_invoice_clicked)
        self.ui.btnUpdateReceive.clicked.connect(self.on_check_invoice_clicked)

    def show_invoice_qr(self, data):
        self.qr_data = data
        if not data:
            pixmap = QPixmap(256, 256)
            pixmap.fill(Qt.GlobalColor.white)
        else:
            img = qrcode.make(data)
            pixmap = QPixmap.fromImage(img.toqimage())
        # auto scale
        label_size = self.ui.labelImage.size()
        scaled_pixmap = pixmap.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        self.ui.labelImage.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.show_invoice_qr(self.qr_data)

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

    def __refresh_nodes_table(self):
        # clear display
        tableNodes = self.ui.tableNode
        while tableNodes.rowCount() > 0:
            tableNodes.removeRow(0)
        ip_only = self.ui.checkIPOnly.isChecked()

        for item in self.nodes_info:
            if ip_only: # display nodes with ip only
                if len(item['addresses']) == 0:
                    continue
                addr = item['addresses'][0]
                if addr.find('0.0.0.0') != -1 or addr.find('127.0.0.1') != -1:
                    continue
            row_count = tableNodes.rowCount()
            tableNodes.insertRow(row_count)
            tableNodes.setItem(row_count, 0, QTableWidgetItem(item['alias']))
            if len(item['addresses']) > 0:
                tableNodes.setItem(row_count, 1, QTableWidgetItem(item['addresses'][0]))
            else:
                tableNodes.setItem(row_count, 1, QTableWidgetItem(""))
            tableNodes.setItem(row_count, 2, QTableWidgetItem(item['node_id']))
            local_time = datetime.fromtimestamp(int(item['timestamp'], 16) / 1000.0)
            tableNodes.setItem(row_count, 3, QTableWidgetItem(local_time.strftime("%Y-%m-%d %H:%M:%S")))
            udt_list = []
            for udt in item['udt_cfg_infos']:
                udt_list.append(udt['name'])
            tableNodes.setItem(row_count, 4, QTableWidgetItem(str(udt_list)))
            tableNodes.setItem(row_count, 5,
                               QTableWidgetItem(str(int(item['auto_accept_min_ckb_funding_amount'], 16) / 10 ** 8)))

    def update_nodes(self):
        self.nodes_info = []
        rpc = FiberRPC(self.ui.comboURL.currentText())
        result = rpc.graph_nodes()

        if result["code"] == "ok":
            self.nodes_info = result['data']
            self.__refresh_nodes_table()
            return True
        else:
            self.__refresh_nodes_table()
            self.statusBar().showMessage("Failed to get node graph")
            return False


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
        else:
            self.statusBar().showMessage("Successfully sent close command to this channel, refreshing...")
            Timer(5, self.async_update_channels).start()

    def on_node_refresh_clicked(self):
        self.update_nodes()

    def on_node_filter_changed(self):
        self.__refresh_nodes_table()

    def on_gen_invoice_clicked(self):
        self.show_invoice_qr(None)
        rpc = FiberRPC(self.ui.comboURL.currentText())
        t_amount = self.ui.txtPayAmount.text()
        t_desc = self.ui.txtDescription.text()
        if len(t_amount) == 0:
            return
        result = rpc.new_invoice_ckb(float(t_amount), t_desc)
        if result["code"] == "error":
            self.qr_data = None
            self.payment_hash = None
            show_error_message(result['data'])
        else:
            self.payment_hash = result['data']['invoice']['data']['payment_hash']
            self.statusBar().showMessage("Successfully generated new invoice.")
            self.show_invoice_qr(result['data']['invoice_address'])

    def on_check_invoice_clicked(self):
        if not self.payment_hash:
            return
        rpc = FiberRPC(self.ui.comboURL.currentText())
        result = rpc.get_invoice(self.payment_hash)
        if result["code"] == "error":
            self.ui.txtInvoiceStatus.setText("Error!")
            show_error_message(result['data'])
        else:
            print(result['data'])
            self.ui.txtInvoiceStatus.setText(result['data']['status'])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())


def show_error_message(data):
    """
    弹出错误提示框
    """
    # 创建错误提示框
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Icon.Critical)
    error_box.setWindowTitle("Error")
    error_box.setText("RPC error has occurred!")
    error_box.setInformativeText(data)
    error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    error_box.setDefaultButton(QMessageBox.StandardButton.Ok)

    # 显示提示框
    error_box.exec()
