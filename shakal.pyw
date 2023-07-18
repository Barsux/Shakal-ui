import os
import datetime
import tempfile
import fitz
import copy
import platform
import subprocess
from PIL import Image, ImageOps
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QThread
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from threading import Thread


H_PAD = 10
W_PAD = 20
DEFAULT_WIDTH = 9.4
NUM_COLS = 2
NUM_ROWS = 4
TITLE = "Shakal_UI"


barcode_width = 3.7
buttonActiveStyle = "border-radius : 5; border : 1px solid black; background-color: #c2ffe0"
buttonInactiveStyle = "border-radius : 5; border : 1px solid black"

dependance_sample = {
    "state":False,
    1:[],
    0:[]
}

def printf(*args):
        print(f"[{datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')}] :", *args)


def openInPreffered(path):
    if platform.system() == "Windows":
            os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class Grid:
    ui = None
    buttons = []
    currpage = 1
    visited_pages = []
    grid_filled = False
    barcode_selected = 0
    def __init__(self, ui, num, cols, rows):
        width = ui.PageBox.frameGeometry().width()
        height = ui.PageBox.frameGeometry().height()
        self.button_width = int((width - (cols + 1) * W_PAD) / cols)
        self.button_height = int((height - (rows + 1) * H_PAD) / rows)
        self.num = num
        self.ui = ui
        self.pages = num
        self.cols = cols
        self.rows = rows
        col = 0
        row = 0
        page = 1
        for _ in range((num + 1) * 8):
            if col == self.cols:
                row += 1
                col = 0
            if row == self.rows:
                row = 0
                col = 0
                page += 1
            button = QtWidgets.QPushButton()
            button.setMinimumSize(QtCore.QSize(self.button_width, self.button_height))
            button.setStyleSheet(buttonInactiveStyle)
            button.setObjectName(f"gridButton#{col}#{row}#{page}")
            self.buttons.append(button)
            col += 1
    
    def button_pressed(self, idx):
        button = self.buttons[idx]
        if ui.converted:
            ui.convertButton.setEnabled(True)
        if button.styleSheet() == buttonInactiveStyle:
            if self.barcode_selected == 0:
                ui.convertButton.setEnabled(True)
            if (self.barcode_selected + 1) <= self.pages:
                button.setStyleSheet(buttonActiveStyle)
                self.barcode_selected += 1
        else:
            button.setStyleSheet(buttonInactiveStyle)
            self.barcode_selected -= 1
            if(self.barcode_selected == 0):
                ui.convertButton.setEnabled(False)
        if ui.convertButton.styleSheet() == ui.convertButtonFinishedStylesheet:
            ui.convertButton.setStyleSheet(ui.convertButtonActiveStylesheet)
        ui.image_selected(self.barcode_selected, self.pages)
    
    def get_buttons_on_page(self, page):
        left_ptr = 0
        right_ptr = 1
        for idx, button in enumerate(self.buttons):
            iter_page = int(button.objectName().split("#")[-1])
            if page == iter_page and not left_ptr:
                left_ptr = idx
            if page < iter_page:
                right_ptr = idx
                return left_ptr, right_ptr       
        return 0, 0
    

    def fill_grid_pushed(self):
        if not self.grid_filled:
            for button in self.buttons:
                button.setStyleSheet(buttonInactiveStyle)
            self.barcode_selected = self.pages
            for i in range(self.pages):
                self.buttons[i].setStyleSheet(buttonActiveStyle)
            ui.convertButton.setEnabled(True)
        else:
            for i in range(self.pages):
                if self.buttons[i].styleSheet() == buttonActiveStyle:
                    self.buttons[i].setStyleSheet(buttonInactiveStyle)
                    self.barcode_selected -= 1
            if self.barcode_selected == 0:
                ui.convertButton.setEnabled(False)
        if ui.convertButton.styleSheet() == ui.convertButtonFinishedStylesheet:
            ui.convertButton.setStyleSheet(ui.convertButtonActiveStylesheet)
        self.grid_filled = not self.grid_filled
        ui.image_selected(self.barcode_selected, self.pages)
        

    
    def get_coordinates(self):
        coordinates = []
        ptr = 0
        while len(coordinates) != self.barcode_selected:
            if self.buttons[ptr].styleSheet() == buttonActiveStyle:
                objectName = self.buttons[ptr].objectName()
                objectName = objectName.split('#')
                coordinates.append((int(objectName[-3]), int(objectName[-2]), int(objectName[-1])))
            ptr += 1
        return tuple(coordinates)
    
    def clear(self):
        for button in self.buttons:
            button.setParent(None)
    
    def __del__(self):
        for button in self.buttons:
            button.setParent(None)


class ImageWorker(QThread):
    def __init__(self, filename, tempImagesDir):
        super(QThread, self).__init__()
        self.filename = filename
        self.tempImagesDir = tempImagesDir

    def run(self):
        zoom_x = 4.0  
        zoom_y = 4.0  
        mat = fitz.Matrix(zoom_x, zoom_y) 
        with fitz.open(self.filename) as pdf_file:
            for idx, page in enumerate(pdf_file):
                pix = page.get_pixmap(matrix=mat)
                name = f"barcode_{idx}_.png"
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples, "raw", "RGB", 0, -1)
                img = img.rotate(90, expand=1)
                img = ImageOps.mirror(img)
                img.save(os.path.join(self.tempImagesDir.name, name))
        self.imageRes = img.height / img.width
        self.pages = idx + 1


class PdfWorker(QThread):
    def __init__(self, outDir, numDocuments, dir, coordinates, pagesize=A4, barcode_width=9.4, num_col=2, num_row=4):
        super(QThread, self).__init__()
        self.numDocuments = numDocuments
        self.outDir = outDir
        self.dir = dir
        self.coordinates = coordinates
        self.pagesize = A4
        self.barcode_width = barcode_width
        self.num_col = num_col
        self.num_row = num_row
        self.filename = "output_barcodes"
        self.format = "pdf"


    def run(self):
        self.name = f"{self.filename}_{self.numDocuments}.pdf"
        self.name = os.path.join(self.outDir, self.name)
        c = canvas.Canvas(self.name ,pagesize=self.pagesize)
        images = os.listdir(self.dir)
        images = tuple(sorted(map(lambda x: os.path.join(self.dir, x), images), key=lambda file: int(file.split('_')[-2])))
        imageSample = Image.open(images[0])
        aspect_ratio = imageSample.height / imageSample.width


        table_width = self.pagesize[0]
        table_height = self.pagesize[1]     


        cell_width = self.barcode_width * cm
        cell_height = cell_width * aspect_ratio
        width_pad = (table_width - (cell_width * self.num_col)) / (self.num_col + 1)
        height_pad = (table_height - (cell_height * self.num_row)) / (self.num_row + 1)
        

        x = []
        y = []
        yc = table_height
        for _ in range(self.num_row):
            yc = yc - cell_height - height_pad
            xc = width_pad
            for _ in range(self.num_col):
                x.append(xc)
                y.append(yc)
                xc += (cell_width + width_pad)


        currpage = 1
        for idx, coordinate in enumerate(self.coordinates):
            xc, yc, page = coordinate
            if page != currpage:
                currpage += 1
                c.showPage()
            num = yc * self.num_col + xc
            c.drawImage(images[idx], x[num], y[num], width=cell_width, height=cell_height)

        c.save()


class Ui_MainWindow(object):
    filePath = ''
    tempImagesDir = tempfile.TemporaryDirectory()
    tempPdfDir = tempfile.TemporaryDirectory()
    numImages = 0
    numDocuments = 1
    allImagesDetected = False
    gridData = None
    gridButtons = None
    grid = None
    page = 1
    imageResolution = None
    converted = False
    latestSaved = None
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(569, 424)
        MainWindow.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, stop:0 rgba(121, 121, 121, 255), stop:1 rgba(0, 0, 0, 255));")
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setStyleSheet("")
        self.centralwidget.setObjectName("centralwidget")
        self.PageBox = QtWidgets.QGroupBox(parent=self.centralwidget)
        self.PageBox.setGeometry(QtCore.QRect(10, 10, 270, 370))
        self.PageBox.setStyleSheet("border: 2px solid;\n"
"background-color: rgb(110, 110, 110);\n"
"border-color: rgb(255, 170, 0);\n"
"border-top-left-radius: 5;\n"
"border-bottom-left-radius: 5;\n"
"border-bottom-right-radius: 5;")
        self.PageBox.setTitle("")
        self.PageBox.setObjectName("PageBox")
        self.fillPages = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.fillPages.setGeometry(QtCore.QRect(290, 328, 16, 16))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        self.fillPages.setFont(font)
        self.fillPages.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: none;")
        self.fillPages.setText("")
        self.fillPages.setObjectName("fillPages")
        self.pageSettingsBox = QtWidgets.QGroupBox(parent=self.centralwidget)
        self.pageSettingsBox.setGeometry(QtCore.QRect(290, 10, 270, 131))
        self.pageSettingsBox.setStyleSheet("border: 2px solid;\n"
"background-color: rgb(121, 121, 121);\n"
"border-color: rgb(255, 170, 0);\n"
"border-top-right-radius: 5;\n"
"border-bottom-right-radius: 5;")
        self.pageSettingsBox.setTitle("")
        self.pageSettingsBox.setObjectName("pageSettingsBox")
        self.numCols = QtWidgets.QTextEdit(parent=self.pageSettingsBox)
        self.numCols.setGeometry(QtCore.QRect(200, 50, 61, 31))
        self.numCols.setStyleSheet("color: rgb(255, 255, 255);")
        self.numCols.setObjectName("numCols")
        self.ImageWidth = QtWidgets.QTextEdit(parent=self.pageSettingsBox)
        self.ImageWidth.setGeometry(QtCore.QRect(200, 10, 61, 31))
        self.ImageWidth.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color:(121, 121, 121);\n"
"border: 2px solid;\n"
"border-color: rgb(255, 170, 0);\n"
"")
        self.ImageWidth.setObjectName("ImageWidth")
        self.label_3 = QtWidgets.QLabel(parent=self.pageSettingsBox)
        self.label_3.setGeometry(QtCore.QRect(10, 60, 175, 16))
        font = QtGui.QFont()
        font.setFamily("Myanmar Text")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setStyleSheet("border: none;\n"
"color: rgb(255, 255, 255);")
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(parent=self.pageSettingsBox)
        self.label_2.setGeometry(QtCore.QRect(10, 20, 175, 16))
        font = QtGui.QFont()
        font.setFamily("Myanmar Text")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setStyleSheet("border: none;\n"
"color: rgb(255, 255, 255);")
        self.label_2.setObjectName("label_2")
        font = QtGui.QFont()
        font.setFamily("Myanmar Text")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_4 = QtWidgets.QLabel(parent=self.pageSettingsBox)
        self.label_4.setGeometry(QtCore.QRect(10, 100, 175, 16))
        font = QtGui.QFont()
        font.setFamily("Myanmar Text")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setStyleSheet("border: none;\n"
"color: rgb(255, 255, 255);")
        self.label_4.setObjectName("label_4")
        self.numRows = QtWidgets.QTextEdit(parent=self.pageSettingsBox)
        self.numRows.setGeometry(QtCore.QRect(200, 90, 61, 31))
        self.numRows.setStyleSheet("color: rgb(255, 255, 255);")
        self.numRows.setObjectName("numRows")
        self.prevBageButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.prevBageButton.setGeometry(QtCore.QRect(10, 385, 30, 30))
        self.prevBageButton.setStyleSheet("QPushButton {\n"
"    background-color: rgb(145, 145, 145);\n"
"    border: 2px solid;\n"
"    border-radius: 5;\n"
"    border-color: rgb(255, 170, 0);\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: rgb(121, 121, 121);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"    border-color: rgb(255, 170, 0);\n"
"}\n"
"QPushButton:hover:!pressed {\n"
"    background-color: rgb(145, 145, 145);\n"
"    border: 2px solid;\n"
"    border-color: rgb(255, 255, 255);\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color: rgb(121, 121, 121);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"    border-color: rgb(255, 170, 0);\n"
"}\n"
"\n"
"")
        self.prevBageButton.setText("")
        self.prevBageButton.setObjectName("prevBageButton")
        self.nextPageButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.nextPageButton.setGeometry(QtCore.QRect(250, 385, 30, 30))
        self.nextPageButton.setStyleSheet("QPushButton {\n"
"    background-color: rgb(145, 145, 145);\n"
"    border: 2px solid;\n"
"    border-radius: 5;\n"
"    border-color: rgb(255, 170, 0);\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: rgb(121, 121, 121);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"    border-color: rgb(255, 170, 0);\n"
"}\n"
"QPushButton:hover:!pressed {\n"
"    background-color: rgb(145, 145, 145);\n"
"    border: 2px solid;\n"
"    border-color: rgb(255, 255, 255);\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color: rgb(121, 121, 121);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"    border-color: rgb(255, 170, 0);\n"
"}\n"
"\n"
"")
        self.nextPageButton.setText("")
        self.nextPageButton.setObjectName("nextPageButton")
        self.convertButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.convertButton.setGeometry(QtCore.QRect(290, 350, 270, 30))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.convertButton.setFont(font)
        self.convertButton.setStyleSheet("\n"
"QPushButton {\n"
"    background-color: rgb(255, 170, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: rgb(195, 130, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:hover:!pressed {\n"
"    background-color: rgb(255, 170, 0);\n"
"    border: 2px solid;\n"
"    border-color: rgb(255, 255, 255);\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color: rgb(145, 97, 0);\n"
"    color: rgb(145, 97, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"")     
        self.convertButtonActiveStylesheet = self.convertButton.styleSheet()
        self.convertButtonFinishedStylesheet = "background-color: #c2ffe0; border-radius: 5; color: #c2ffe0"
        self.convertButton.setObjectName("convertButton")
        self.printButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.printButton.setGeometry(QtCore.QRect(290, 385, 133, 30))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.printButton.setFont(font)
        self.printButton.setStyleSheet("\n"
"QPushButton {\n"
"    background-color: rgb(255, 170, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: rgb(195, 130, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:hover:!pressed {\n"
"    background-color: rgb(255, 170, 0);\n"
"    border: 2px solid;\n"
"    border-color: rgb(255, 255, 255);\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color: rgb(145, 97, 0);\n"
"    color: rgb(145, 97, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"")
        self.printButton.setObjectName("printButton")
        self.openExplorerButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.openExplorerButton.setGeometry(QtCore.QRect(427, 385, 133, 30))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.openExplorerButton.setFont(font)
        self.openExplorerButton.setStyleSheet("\n"
"QPushButton {\n"
"    background-color: rgb(255, 170, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: rgb(195, 130, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:hover:!pressed {\n"
"    background-color: rgb(255, 170, 0);\n"
"    border: 2px solid;\n"
"    border-color: rgb(255, 255, 255);\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color: rgb(145, 97, 0);\n"
"    color: rgb(145, 97, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"")
        self.openExplorerButton.setObjectName("openExplorerButton")
        self.fileSelect = QtWidgets.QPushButton(parent=self.centralwidget)
        self.fileSelect.setEnabled(True)
        self.fileSelect.setGeometry(QtCore.QRect(290, 150, 235, 31))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.fileSelect.setFont(font)
        self.fileSelect.setStyleSheet("\n"
"QPushButton {\n"
"    background-color: rgb(255, 170, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: rgb(195, 130, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:hover:!pressed {\n"
"    background-color: rgb(255, 170, 0);\n"
"    border: 2px solid;\n"
"    border-color: rgb(255, 255, 255);\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color: rgb(195, 130, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"\n"
"")
        self.fileSelect.setObjectName("fileSelect")
        self.clearButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.clearButton.setEnabled(True)
        self.clearButton.setGeometry(QtCore.QRect(530, 150, 30, 31))
        self.clearButton.setStyleSheet("QPushButton {\n"
"    background-color:  rgb(255, 100, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color:  rgb(148, 56, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:hover:!pressed {\n"
"    background-color: rgb(255, 100, 0);\n"
"    border: 2px solid;\n"
"    border-color: rgb(255, 255, 255);\n"
"    border-radius: 5;\n"
"}\n"
"QPushButton:disabled {\n"
"    background-color:  rgb(148, 56, 0);\n"
"    border: none;\n"
"    border-radius: 5;\n"
"}\n"
"\n"
"")
        self.clearButton.setText("")
        self.clearButton.setObjectName("clearButton")
        self.documentName = QtWidgets.QLabel(parent=self.centralwidget)
        self.documentName.setGeometry(QtCore.QRect(290, 230, 260, 30))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        self.documentName.setFont(font)
        self.documentName.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: none;")
        self.documentName.setText("")
        self.documentName.setObjectName("documentName")
        self.numImagesLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.numImagesLabel.setGeometry(QtCore.QRect(290, 260, 260, 30))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        self.numImagesLabel.setFont(font)
        self.numImagesLabel.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: none;")
        self.numImagesLabel.setText("")
        self.numImagesLabel.setObjectName("numImagesLabel")
        self.pageSelectorLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.pageSelectorLabel.setGeometry(QtCore.QRect(290, 290, 260, 30))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        self.pageSelectorLabel.setFont(font)
        self.pageSelectorLabel.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: none;")
        self.pageSelectorLabel.setText("")
        self.pageSelectorLabel.setObjectName("pageSelectorLabel")
        self.pageLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.pageLabel.setGeometry(QtCore.QRect(95, 395, 100, 30))
        self.pageLabel.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: none;")
        self.pageLabel.setText("")
        self.pageLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.pageLabel.setObjectName("pageLabel")
        self.label_9 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_9.setGeometry(QtCore.QRect(310, 320, 241, 30))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Symbol")
        self.label_9.setFont(font)
        self.label_9.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: none;")
        self.label_9.setObjectName("label_9")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.connectUi()
        self.miscInit()
    

    def miscInit(self):
        self.gridB = QtWidgets.QGridLayout(parent=self.PageBox)
        self.gridB.setObjectName("grid")


    def barcode_changed(self):
        if self.convertButton.styleSheet() == self.convertButtonFinishedStylesheet:
            self.convertButton.setStyleSheet(self.convertButtonActiveStylesheet)
            self.convertButton.setEnabled(True)

    def connectUi(self):
        self.prevBageButton.clicked.connect(self.prevPageClicked)
        self.fileSelect.clicked.connect(self.select_file_clicked)
        self.convertButton.clicked.connect(self.convert)
        self.nextPageButton.clicked.connect(self.nextPageClicked)
        self.clearButton.clicked.connect(self.clearClicked)
        self.openExplorerButton.clicked.connect(self.open_explorer_decorator)
        self.printButton.clicked.connect(self.open_pdf_decorator)
        self.fileDependance = copy.deepcopy(dependance_sample)
        self.fileDependance[1] += [self.prevBageButton, self.nextPageButton, self.fillPages, self.convertButton, self.clearButton]

        self.convertDependance = copy.deepcopy(dependance_sample)
        self.convertDependance[1] += [self.printButton, self.openExplorerButton]
        self.convertDependance[0] += [self.convertButton]

        self.numCols.textChanged.connect(self.cols_rows_changed)
        self.numRows.textChanged.connect(self.cols_rows_changed)
        self.ImageWidth.textChanged.connect(self.barcode_changed)

        self.changeDependanceState(self.convertDependance)
        self.changeDependanceState(self.fileDependance)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", TITLE))
        self.label_3.setText(_translate("MainWindow", "Количество столбцов:"))
        self.label_2.setText(_translate("MainWindow", "Ширина штрих-кода (см):"))
        self.label_4.setText(_translate("MainWindow", "Количество строк:"))
        self.convertButton.setText(_translate("MainWindow", "Начать преобразование"))
        self.printButton.setText(_translate("MainWindow", "Открыть"))
        self.openExplorerButton.setText(_translate("MainWindow", "Открыть путь"))
        self.fileSelect.setText(_translate("MainWindow", "Выбрать файл"))
        self.label_9.setText(_translate("MainWindow", "Заполнить всё"))

    
    def image_selected(self, num, pages):
        self.pageSelectorLabel.setText(f"Выделено {num} из {pages}.")


    def cols_rows_changed(self):
        if not self.numImages:
            return
        self.rows = self.numRows.toPlainText()
        self.cols = self.numCols.toPlainText()
        if not self.rows.isdigit() or not self.cols.isdigit():
            return
        self.rows = int(self.rows)
        self.cols = int(self.cols) 
        if self.grid is not None:
            self.grid.clear()
            del self.grid
        self.grid = Grid(self, self.numImages, self.cols, self.rows)
        self.fillPages.setChecked(False)
        self.drawGrid(1)


    def changeDependanceState(self, dependance):
        state = dependance["state"]
        if dependance[1]:
            for obj in dependance[1]:
                obj.setEnabled(state)
        if dependance[0]:
            for obj in dependance[0]:
                obj.setEnabled(not state)

    
    def convert(self):
        self.converted = True
        self.barcode_width = self.ImageWidth.toPlainText()
        if isinstance(self.barcode_width, str) and not self.barcode_width.replace('.', '', 1).isdigit():
            return
        self.barcode_width = float(self.barcode_width)
        self.pdfworker = PdfWorker(self.tempPdfDir.name, self.numDocuments, self.tempImagesDir.name, self.grid.get_coordinates(), barcode_width=self.barcode_width)
        self.pdfworker.start()
        self.pdfworker.finished.connect(self.PdfWorker_finished)
        

    def PdfWorker_finished(self):
        self.numDocuments += 1
        self.convertDependance["state"] = True
        self.changeDependanceState(self.convertDependance)
        self.convertButton.setStyleSheet(self.convertButtonFinishedStylesheet)
        self.latestSaved = self.pdfworker.name


    def select_file_clicked(self):
        self.filePath, _ = QFileDialog.getOpenFileName(None, 'Open File', './', "pdf (*.pdf)")
        if not self.filePath:
            return 
        self.fileSelect.setEnabled(False)
        self.fileDependance["state"] = True
        self.changeDependanceState(self.fileDependance)
        self.documentName.setText(f"Документ: {self.filePath.split('/')[-1]}")
        self.imageworker = ImageWorker(self.filePath, self.tempImagesDir)
        self.imageworker.start()
        self.imageworker.finished.connect(self.ImageWorker_finished)


    def open_explorer_decorator(self):
        Thread(target=openInPreffered, args=(self.tempPdfDir.name,)).start()


    def open_pdf_decorator(self):
        Thread(target=openInPreffered, args=(self.latestSaved,)).start()

    
    def ImageWorker_finished(self):
        self.ImageWidth.setPlainText(str(DEFAULT_WIDTH))
        self.numCols.setPlainText(str(NUM_COLS))
        self.numRows.setPlainText(str(NUM_ROWS))
        self.rows = self.numRows.toPlainText()
        self.cols = self.numCols.toPlainText()
        if not self.rows.isdigit() or not self.cols.isdigit():
            return
        self.rows = int(self.rows)
        self.cols = int(self.cols)
        self.numImages = self.imageworker.pages
        self.imageResolution = self.imageworker.imageRes
        self.numImagesLabel.setText(f"Найдено {self.numImages} изображени(я/ий).")
        self.grid = Grid(self, self.numImages, self.cols, self.rows)
        self.fillPages.clicked.connect(self.grid.fill_grid_pushed)
        self.pageLabel.setText(f"{self.grid.currpage}/{self.grid.pages}")
        self.drawGrid(1)
        self.convertButton.setEnabled(False)
        self.fileDependance["state"] = True
        self.changeDependanceState(self.fileDependance)
        self.nextPageButton.setEnabled(True)
        self.prevBageButton.setEnabled(False)

    def prevPageClicked(self):
        if self.grid.currpage == self.grid.pages:
            self.nextPageButton.setEnabled(True)
        self.grid.currpage -= 1
        if self.grid.currpage == 1:
            self.prevBageButton.setEnabled(False)
        self.pageLabel.setText(f"{self.grid.currpage}/{self.grid.pages}")
        self.drawGrid(self.grid.currpage)


    def nextPageClicked(self):
        if self.grid.currpage == 1:
            self.prevBageButton.setEnabled(True)
        self.grid.currpage += 1
        if self.grid.currpage == self.numImages:
            self.nextPageButton.setEnabled(False)
        self.pageLabel.setText(f"{self.grid.currpage}/{self.grid.pages}")
        self.drawGrid(self.grid.currpage)

    
    def clearClicked(self):
        if self.grid is not None:
            del self.grid
        if self.imageworker is not None:
            del self.imageworker
        self.fileDependance["state"] = False
        self.changeDependanceState(self.fileDependance)
        self.tempImagesDir = tempfile.TemporaryDirectory()
        if self.converted:
            self.converted = False
            del self.pdfworker
            self.convertDependance["state"] = False
            self.changeDependanceState(self.convertDependance)
            self.convertButton.setStyleSheet(self.convertButtonActiveStylesheet)
            self.convertButton.setEnabled(False)
        if self.fillPages.isChecked():
            self.fillPages.setChecked(False)

        self.documentName.setText("")
        self.numImagesLabel.setText("")
        self.pageSelectorLabel.setText("")
        self.prevBageButton.setEnabled(False)
        self.fileSelect.setEnabled(True)

    

    def drawGrid(self, page, init=False):
        for i in reversed(range(self.gridB.count())): 
            self.gridB.itemAt(i).widget().setParent(None)
        visited = page in self.grid.visited_pages
        lidx, ridx = self.grid.get_buttons_on_page(page) 
        if page == 1:
            lidx = 0
        for i in range(lidx, ridx):
            name = self.grid.buttons[i].objectName()
            row = int(name.split('#')[-2])
            col = int(name.split('#')[-3])
            if not visited:
                self.grid.buttons[i].clicked.connect(lambda _, i=i: self.grid.button_pressed(i))
            self.gridB.addWidget(self.grid.buttons[i], row, col)
        self.grid.visited_pages.append(page)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
