#######################################################################################################################
## TexToTX Version 1.0 by Ciro Cardoso                                                                               ##
## This tool converts the textures inside a folder(s) or a texture selection into                                    ##
## TX files                                                                                                          ##
##                                                                                                                   ##
## For feedback, suggestions or bugs, get in touch - cirocardoso@yahoo.co.uk                                         ##
##                                                                                                                   ##
## TODO: Adding the option for a sufix \ Adding the option to export exr                                             ##
##                                                                                                                   ##
#######################################################################################################################

import hou
import os
import subprocess

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PySide2.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QCheckBox, QProgressBar)
from PySide2.QtCore import (QRect, Qt, QTimer)


## defines some variables
dir = os.environ
imakeTX = "/imaketx.exe"
imaketxPath = ""

for x, y in dir.items():
    if x == "HB":
        imaketxPath = y + imakeTX

max_workers=os.cpu_count ()
reduceUsage = int(max_workers * 0.2)

## this is where the files are going to be saved
global filesPath

class mainWindowUI (QMainWindow):
    
    ## defines the widgets and layout
    def __init__(self):
        super().__init__()
        
        ## set window size
        self.setWindowTitle("TexToTx Version 1.0")
        self.setFixedSize(350, 350)
        
        ## set variables to help with layout
        yHeight = 75
        
               
        #########################################################
        ## TOP LEVEL LABEL
        self.topLabel = QLabel("This tool converts the textures inside a folder or a texture selection into TX files", self)
        self.topLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.topLabel.setGeometry(10,yHeight - 55,345,41)
        self.topLabel.setWordWrap(True)

        #########################################################
        ## OPEN FOLDER BUTTON
        self.btOpenFolder = QPushButton("Open Folder", self)
        self.btOpenFolder.setGeometry(30, yHeight, 125, 60)
        self.btOpenFolder.clicked.connect(self.onOpenFolder)
        
        ## variable to store the folder path
        self.selectedFolderPath = ""
        
        #########################################################
        ## CHECKBOX BUTTON
        self.checkbox = QCheckBox("Include subfolders?", self)
        self.checkbox.setGeometry(35,yHeight + 25,250,100)
        self.checkbox.setEnabled(False)
        self.checkbox.stateChanged.connect(self.onCheckBox)
                
        #########################################################
        ## SELECTED IMAGES BUTTON
        self.btSelTex = QPushButton("Select Textures", self)
        self.btSelTex.setGeometry(200, yHeight, 125, 60)
        self.btSelTex.clicked.connect(self.onSelectTex)
        
        ## variable to store the list of textures selected
        self.selectedTextures = []
        
        #########################################################
        ## MID LEVEL LABEL
        self.midLabel = QLabel("Use one of the options to select the textures", self)
        self.midLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.midLabel.setGeometry(10,yHeight + 100 ,341,41)
        self.midLabel.setWordWrap(True)
        
        #########################################################
        ## CONVERT TEXTURES BUTTON
        self.btConvert = QPushButton("Convert textures", self)
        self.btConvert.setGeometry(30, yHeight+150, 300, 50)
        self.btConvert.setEnabled(False)
        self.btConvert.clicked.connect(self.processImagesParallel)
        
        #########################################################
        ## PROGRESS BAR
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(30,yHeight + 220,300,30)
        self.progressBar.setValue(0)
    
    
    ## OPEN FOLDER BUTTON
    ## function for when you click on the Open Folder button
    def onOpenFolder(self):
        
        ## set some global variables
        
        global folderPath
        global files
        global filesPath
        imageExt = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".exr", ".tga", ".hdr")
        folderPath = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if folderPath:
            self.checkbox.setEnabled(True)
            self.btSelTex.setEnabled(False)
            self.btConvert.setEnabled(True)
            files = [str(f) for f in Path(folderPath).iterdir() if f.is_file()]
            files = [file for file in files if ".tx" not in file]
            #for texture in os.listdir(folderPath):
            #    if texture.lower().endswith(imageExt):
            #        filesPath.append(os.path.join(folderPath, texture))
            filesPath.append(files)
            self.midLabel.setText(str(len(filesPath)) + " textures will be converted")
                                
    def getAll(self, folderPath):
        ## this lists all the files in the selected folder and the subfolders
        return [str(f) for f in Path(folderPath).rglob("*") if f.is_file()]

    def getFilesFolder(self, folderPath):
        ## this lists all the files inside the selected folder ignoring the any subfolders
        return [str(f) for f in Path(folderPath).iterdir() if f.is_file()]

    def onCheckBox(self, state):
        global filesPath
        
        if state == Qt.Checked:
            files = self.getAll(folderPath)
            filesPath = files
            self.midLabel.setText(str(len(filesPath)) + " textures will be converted")
            
        else:
            files = self.getFilesFolder(folderPath)
            filesPath = files
            self.midLabel.setText(str(len(filesPath)) + " textures will be converted")
   
    ## SELECT TEXTURES BUTTON
    ## function for when you click on the Select Textures button
    def onSelectTex(self):
        
        global filesPath
        
        imagePaths, _ = QFileDialog.getOpenFileNames(self, "Select textures", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.exr *.tga *.hdr)")
        
        if imagePaths:
            self.selectedTextures = imagePaths
            self.btConvert.setEnabled(True)
            self.btOpenFolder.setEnabled(False)
            self.midLabel.setText(str(len(self.selectedTextures)) + " textures will be converted")
            filesPath = imagePaths
        
    
    ## remove all the TX textures
    def convertTX(self, image_path):
        
        output_img = os.path.splitext(image_path) [0] + ".tx"
        command = f'"{imaketxPath}" "{image_path}" "{output_img}" --newer '
        subprocess.run(command, shell=True, capture_output=True, text=True)

    ## function to process multiple images

    def processImagesParallel (self):
        
        global filesPath
        
        self.progressBar.setMaximum(len(filesPath))
               
        with ThreadPoolExecutor (reduceUsage) as executor:
            runs = [executor.submit(self.convertTX, path) for path in filesPath]
            
            for i, _ in enumerate(as_completed(runs)):
                self.progressBar.setValue(i+1)
        
        
windowUI = mainWindowUI()
windowUI.show()