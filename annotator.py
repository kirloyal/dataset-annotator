# from __future__ import print_function

import sys
import os
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from PyQt4 import QtGui
from PyQt4.QtCore import QTimer, QEvent, Qt, QDir

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.cm as cm

import cv2

n = 50
x = np.arange(n)
ys = [i+x+(i*x)**2 for i in range(n)]
rainbow_cm = cm.rainbow(np.linspace(0, 1, len(ys))) * 255

class Window(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("Multi-mp4-Sync")
        w = 1280; h = 720
        self.resize(w, h)
        self.setAcceptDrops(True)

        self.initUI()
        
        self.imgHarris = False
        self.imgHough = False

        self.lsPoint = []
        self.lsName = []
        self.folder = {}

    def evCheckBox(self, cb):    
        if cb == self.cbHistEqual:
            self.plotFirstInList()
        
            
    

    def evSlider(self, sl):
        pass
        

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                self.skip()
            elif event.key() == Qt.Key_D:
                self.delete()
            elif event.key() == Qt.Key_H:
                self.cbHistEqual.toggle()
            return super(Window, self).eventFilter(obj, event)
        else:
            return super(Window, self).eventFilter(obj, event)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            url = unicode(url.toLocalFile()) 
            if os.path.isdir(url):
                folder = os.path.dirname(url)
                for filename in os.listdir(url):
                    if os.path.splitext(filename)[1] == '.jpg' or os.path.splitext(filename)[1] == '.png':
                        self.listFile.addItem(filename)
                        self.folder[filename] = folder
            else:
                filename = os.path.basename(url)
                if os.path.splitext(filename)[1] == '.jpg' or os.path.splitext(filename)[1] == '.png':
                    self.listFile.addItem(filename)
                    self.folder[filename] = os.path.dirname(url)
        
        while self.listFile.count() > 0:
            if self.bDrawStripe:
                self.bDrawStripe = False
            elif self.cbClicking.isChecked():
                self.plotFirstInList()

            # x,y = self.clickRepeat()
            x,y = self.getClickedPoint()  
            
            if self.bDrawStripe:
                p0 = (x,y)
                p1 = self.getClickedPoint()  
                self.ax.plot([p0[0],p1[0]],[p0[1],p1[1]],'g')
                self.ax.plot((p0[0]+p1[0])/2, (p0[1]+p1[1])/2, 'g*')
                
                h, w, _ = self.img.shape
            
                
                if p0[0] == p1[0]:
                    maxl = max(h, w)
                    res = int(maxl / 20)
                    
                    for off in range(-20,30):
                        self.ax.plot([res * off,res * off],[0, w],'r')
                else:
                    maxl = max(h, w)
                    r = np.abs(p0[0]-p1[0]) / np.sqrt( (p0[1]-p1[1])**2 + (p0[0]-p1[0])**2 )
                    res = int(maxl / (20*r))
                    offs = range(-maxl, 2 * maxl, res)

                    r = float(p0[1] - p1[1]) / float(p0[0] - p1[0])
                    for off in range(-20,30):
                        self.ax.plot([0,w],[off * res, r * w + off * res],'r')
                
                self.canvas.draw()
                    
            elif self.cbClicking.isChecked():
                savefolder = str(self.tbSaveFolder.toPlainText())
                filename, ext = os.path.splitext(str(self.listFile.item(0).text()))
                savefile_txt = os.path.join(savefolder, filename + '.txt')
                savefile_img = os.path.join(savefolder, filename + '.jpg')
                numPoint = int(self.tbNum.text())
                if os.path.isfile(savefile_txt):
                    points = np.loadtxt(savefile_txt, dtype='int')
                    if points.size != 0:
                        if len(points.shape) == 1:
                            points = points.reshape(1,-1)
                        row = np.array([[numPoint,x,y]])
                        points = np.append(points,row,axis=0)
                        points = points[points[:, 0].argsort()]
                        np.savetxt(savefile_txt, points, fmt='%i')
                    else:
                        row = np.array([[numPoint,x,y]])
                        np.savetxt(savefile_txt, row, fmt='%i')
                else:
                    row = np.array([[numPoint,x,y]])
                    np.savetxt(savefile_txt, row, fmt='%i')

                h, w, _ = self.img.shape
                fs = max(float(max(h, w))/1000, 0.1)
                cv2.circle(self.img, center = (x,y), radius = max(int(fs*6),1), color = rainbow_cm[numPoint % 50], thickness = int(round(fs*3)))
                cv2.putText(self.img, str(numPoint), (int(x-fs*30), int(y+fs*30)), 
                    cv2.FONT_HERSHEY_SIMPLEX, fs, color = rainbow_cm[numPoint % 50], 
                    thickness=int(round(fs*3)) )
                cv2.imwrite(savefile_img, cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB))

                if not self.cbKeepEditing.isChecked():
                    file = str(self.listFile.item(0).text())
                    del self.folder[file]
                    self.listFile.takeItem(0)
            
                


    def plotFirstInList(self):        
        filename = str(self.listFile.item(0).text())
        folder = self.folder[filename]
        file = os.path.join(folder,filename)
        self.img = cv2.cvtColor(cv2.imread(file), cv2.COLOR_BGR2RGB)
        h, w, _ = self.img.shape

        savefolder = str(self.tbSaveFolder.toPlainText())
        savefile = os.path.join(savefolder, os.path.splitext(filename)[0] + '.txt')
        if os.path.isfile(savefile):
            points = np.loadtxt(savefile, dtype='int')
            if points.size != 0:
                if len(points.shape) == 1:
                    points = points.reshape(1,-1)
                for pt in points:
                    numPoint,x,y = pt
                    fs = max(float(max(h, w))/1000, 0.1)
                    cv2.circle(self.img, center = (x,y), radius = max(int(fs*6),1), color = rainbow_cm[numPoint % 50], thickness = int(round(fs*3)))
                    cv2.putText(self.img, str(numPoint), (int(x-fs*30), int(y+fs*30)), 
                        cv2.FONT_HERSHEY_SIMPLEX, fs, color = rainbow_cm[numPoint % 50], 
                        thickness=int(round(fs*3)) )

        self.ax.clear()
        if self.cbHistEqual.isChecked():
            img_yuv = cv2.cvtColor(self.img, cv2.COLOR_BGR2YUV)
            img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
            img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
            self.ax.imshow(img_output)

        else:
            self.ax.imshow(self.img)
        self.ax.set_xlabel(file)
        self.canvas.draw()

    def clickRepeat(self):
        while True:
            x,y = self.getClickedPoint()            
            self.ax.plot(x,y,'g.')
            self.canvas.draw()
            
            if QtGui.QMessageBox.question(self,'', "Is it the point?", 
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                return x, y
    
    def delete(self):
        savefolder = str(self.tbSaveFolder.toPlainText())
        filename, ext = os.path.splitext(str(self.listFile.item(0).text()))
        savefile_txt = os.path.join(savefolder, filename + '.txt')
        numPoint = int(self.tbNum.text())
        if os.path.isfile(savefile_txt):
            points = np.loadtxt(savefile_txt, dtype='int')
            if len(points.shape) == 1:
                points = points.reshape(1,-1)
            points = points[points[:,0] != numPoint,:]
            np.savetxt(savefile_txt, points, fmt='%i')
        self.plotFirstInList()
        
    def skip(self):
        file = str(self.listFile.item(0).text())
        del self.folder[file]
        if self.listFile.count() > 0:
            self.listFile.takeItem(0)
            self.plotFirstInList()

    def getClickedPoint(self):
        self.ax.set_xlim(self.ax.get_xlim()) 
        self.ax.set_ylim(self.ax.get_ylim()) 

        self.edt.appendPlainText("Click point")

        Xs = self.figure.ginput(1)
        while len(Xs) == 0:
            Xs = self.figure.ginput(1)            
        X = Xs[0]
        x, y = X
        x = int(round(x))
        y = int(round(y))
        self.edt.appendPlainText(str((x,y)))
        return x,y


    def setSaveFolder(self):
        dlg = QtGui.QFileDialog()
        dlg.setFileMode(QtGui.QFileDialog.DirectoryOnly)
        
        if dlg.exec_():
            lsUrl = dlg.selectedFiles()
            self.tbSaveFolder.setPlainText(lsUrl[0])

    def setStripe(self):
        self.bDrawStripe = True


    def initUI(self):
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.lbSaveFolder = QtGui.QLabel("Save Folder :")
        self.lbSaveFolder.setFixedWidth(100)
        self.btnSaveFolder = QtGui.QPushButton('Search')
        self.btnSaveFolder.setFixedWidth(100)
        self.btnSaveFolder.clicked.connect(self.setSaveFolder)
        self.tbSaveFolder = QtGui.QPlainTextEdit()
        self.tbSaveFolder.setFixedWidth(120)
        self.tbSaveFolder.setFixedHeight(40)
        self.tbSaveFolder.setDisabled(True)

        self.cbClicking = QtGui.QCheckBox("Click Points")

        self.cbKeepEditing = QtGui.QCheckBox("Keep img")
        
        self.cbHistEqual = QtGui.QCheckBox("Hist Equalize")
        self.cbHistEqual.stateChanged.connect(lambda:self.evCheckBox(self.cbHistEqual))
        
        self.btnSkip = QtGui.QPushButton('Skip')
        self.btnSkip.setFixedWidth(100)
        self.btnSkip.clicked.connect(self.skip)

        self.listFile = QtGui.QListWidget()
        self.listFile.installEventFilter(self)
        self.listFile.setFixedWidth(120)

        self.lbNum = QtGui.QLabel("Point Number :")
        self.lbNum.setFixedWidth(100)
        self.tbNum = QtGui.QLineEdit("")
        self.tbNum.setFixedWidth(100)

        self.btnDelete = QtGui.QPushButton('Delete')
        self.btnDelete.setFixedWidth(100)
        self.btnDelete.clicked.connect(self.delete)

        self.btnStripe = QtGui.QPushButton('Draw Stripe')
        self.btnStripe.setFixedWidth(100)
        self.btnStripe.clicked.connect(self.setStripe)
        self.bDrawStripe = False

        self.btnClear = QtGui.QPushButton('Clear')
        self.btnClear.setFixedWidth(100)
        self.btnClear.clicked.connect(self.plotFirstInList)


        self.edt = QtGui.QPlainTextEdit()
        self.edt.setDisabled(True)
        self.edt.setMaximumBlockCount(10)
        self.edt.setFixedWidth(120)

        layoutControl = QtGui.QGridLayout()
        lsControl = [self.lbSaveFolder, self.btnSaveFolder, self.tbSaveFolder, 
                    self.cbClicking, self.cbKeepEditing, self.cbHistEqual, 
                    self.btnSkip, self.listFile, self.lbNum, self.tbNum, self.btnDelete, 
                    self.btnStripe, self.btnClear, self.edt]
        
        gridW = 1
        for i in range(len(lsControl)):
            if isinstance(lsControl[i], list):
                gridW = max(gridW, len(lsControl[i]))        
        for i in range(len(lsControl)):
            if isinstance(lsControl[i], list):
                for j in range(len(lsControl[i])):
                    layoutControl.addWidget(lsControl[i][j],i,j,1,1)
            else:
                layoutControl.addWidget(lsControl[i],i,0,1,gridW)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.toolbar,0,0,1,4)
        layout.addWidget(self.canvas,1,1,4,3)
        layout.addLayout(layoutControl,1,0,1,1)
        
        self.setLayout(layout)
        self.ax = self.figure.add_subplot(111)
        self.figure.tight_layout()

        self.cbClicking.setChecked(True)
        self.cbKeepEditing.setChecked(True)
        self.cbHistEqual.setChecked(True)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())















