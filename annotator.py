
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
		pass

	def evSlider(self, sl):
		pass
		

	def eventFilter(self, obj, event):
		if event.type() == QEvent.KeyPress and obj == self.listPoint:
			if event.key() == Qt.Key_Delete:
				listItems=self.listPoint.selectedItems()
				if not listItems: return        
				for item in listItems:
					idx = self.listPoint.row(item)
					del self.lsPoint[idx]
					del self.lsName[idx]
					self.listPoint.takeItem(idx)
					
			return super(Window, self).eventFilter(obj, event)
		else:
			return super(Window, self).eventFilter(obj, event)


	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):


		# if len(event.mimeData().urls()) != 1:
		# 	return
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
			print self.listFile.count()
			self.plotFirstInList()
			x,y = self.clickRepeat()

			savefolder = str(self.tbSaveFolder.toPlainText())
			filename, ext = os.path.splitext(str(self.listFile.item(0).text()))
			savefile = os.path.join(savefolder, filename + '.txt')
			numPoint = int(self.tbNum.text())
			if os.path.isfile(savefile):
				points = np.loadtxt(savefile, dtype='int')
				if len(points.shape) == 1:
					points = points.reshape(1,-1)
				row = np.array([[numPoint,x,y]])
				points = np.append(points,row,axis=0)
				points = points[points[:, 0].argsort()]
				np.savetxt(savefile, points, fmt='%i')
			else:
				row = np.array([[numPoint,x,y]])
				np.savetxt(savefile, row, fmt='%i')

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
			if len(points.shape) == 1:
				points = points.reshape(1,-1)
			for pt in points:
				numPoint,x,y = pt
				cv2.circle(self.img, center = (x,y), radius = 3, color = rainbow_cm[numPoint % 50], thickness = 2)
				
		self.ax.clear()
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

	def initUI(self):
		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)

		self.edt = QtGui.QPlainTextEdit()
		self.edt.setDisabled(True)
		self.edt.setMaximumBlockCount(10)
		self.edt.setFixedWidth(120)
		
		# self.cbGray = QtGui.QCheckBox("Gray")
		# self.cbGray.stateChanged.connect(lambda:self.evCheckBox(self.cbGray))
		

		# self.slGray = QtGui.QSlider(Qt.Horizontal)
		# self.slGray.setMinimum(0)
		# self.slGray.setMaximum(10)
		# self.slGray.setValue(5)
		# self.slGray.setTickPosition(QtGui.QSlider.TicksBelow)
		# self.slGray.setTickInterval(1)
		# self.slGray.setFixedWidth(80)
		# self.slGray.valueChanged.connect(lambda:self.evSlider(self.slGray))


		# self.cbHough = QtGui.QCheckBox("Use Hough")

		# self.slHough = QtGui.QSlider(Qt.Horizontal)
		# self.slHough.setMinimum(0)
		# self.slHough.setMaximum(10)
		# self.slHough.setValue(5)
		# self.slHough.setTickPosition(QtGui.QSlider.TicksBelow)
		# self.slHough.setTickInterval(1)
		# self.slHough.setFixedWidth(80)
		# self.slHough.valueChanged.connect(lambda:self.evSlider(self.slHough))

		# self.cbNonMaxSup = QtGui.QCheckBox("Non-Max-Sup")
		# self.cbNonMaxSup.stateChanged.connect(lambda:self.evCheckBox(self.cbNonMaxSup))

		# self.btnClick = QtGui.QPushButton('Click')
		# self.btnClick.setFixedWidth(100)
		# self.btnClick.clicked.connect(self.click)


		
		# self.btnTest = QtGui.QPushButton('Test')
		# self.btnTest.setFixedWidth(100)
		# self.btnTest.clicked.connect(self.test)

		self.lbSaveFolder = QtGui.QLabel("Save Folder :")
		self.lbSaveFolder.setFixedWidth(100)
		self.btnSaveFolder = QtGui.QPushButton('Search')
		self.btnSaveFolder.setFixedWidth(100)
		self.btnSaveFolder.clicked.connect(self.setSaveFolder)
		self.tbSaveFolder = QtGui.QPlainTextEdit()
		self.tbSaveFolder.setFixedWidth(120)
		self.tbSaveFolder.setFixedHeight(40)
		self.tbSaveFolder.setDisabled(True)

		self.listFile = QtGui.QListWidget()
		self.listFile.installEventFilter(self)
		self.listFile.setFixedWidth(120)

		self.lbNum = QtGui.QLabel("Point Number :")
		self.lbNum.setFixedWidth(100)
		self.tbNum = QtGui.QLineEdit("")
		self.tbNum.setFixedWidth(100)
		

		layoutControl = QtGui.QGridLayout()
		lsControl = [self.lbSaveFolder, self.btnSaveFolder, self.tbSaveFolder, self.listFile, 
					self.lbNum, self.tbNum, self.edt]
		
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


if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)

	main = Window()
	main.show()

	sys.exit(app.exec_())















