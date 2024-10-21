#######################################################################################################################
## TexToMtlX Version 1.1 by Ciro Cardoso                                                                             ##
## This tool converts the textures inside a folder(s) or a texture selection into                                    ##
## TX files                                                                                                          ##
##                                                                                                                   ##
## For feedback, suggestions or bugs, get in touch - cirocardoso@yahoo.co.uk                                         ##
##                                                                                                                   ##
## Thanks to @_Approximated_ and @yonatanbary for the help testing the code and the ideas                            ##
## Version 1.1 - Added support for cavity, translucency maps. Added support to mtlXTiledImage                        ##
## Version 1.2 - Fix for the Solaris Composition Arc missing from material, fix for images without underscore        ##
##                                                                                                                   ##
##                                                                                                                   ##
#######################################################################################################################

import hou
import os
import re 
import subprocess

from collections import defaultdict

from PySide2.QtWidgets import (QMainWindow, QPushButton, QFileDialog, QLabel, QCheckBox, QProgressBar, QListView)
from PySide2.QtGui import (QStandardItemModel, QStandardItem)
from PySide2.QtCore import (QRect, Qt)

## VARIABLES
jobVar = hou.text.expandString("$JOB")
udimPattern = re.compile(r'_(\d{4})')
sizePattern = re.compile(r'_(\d+[Kk])')
texturesTypes = ['diffuse', 'diff', 'albedo', 'alb', 'base', 'col', 'color', 'basecolor',
                 'metallic', 'metalness', 'metal', 'mtl', 'met',
                 'specularity', 'specular', 'spec', 'spc',
                 'roughness', 'rough', 'rgh',
                 'gloss', 'glossy', 'glossiness', 'translucency',
                 'transmission', 'transparency', 'trans', 
                 'emission', 'emissive', 'emit', 'emm','alpha', 'opacity', 'opac',
                 'ao', 'ambient_occlusion', 'occlusion', 'cavity',
                 'bump', 'bmp', 'height', 'displacement', 'displace', 'disp', 'dsp', 'heightmap', 'user', 'mask',
                 'normal', 'nor', 'nrm', 'nrml', 'norm'
                 ]
textureExt = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.exr', '.bmp']  

## for TX conversion
dir = os.environ
imakeTX = "/imaketx.exe"
imaketxPath = ""

for x, y in dir.items():
    if x == "HB":
        imaketxPath = y + imakeTX

max_workers=os.cpu_count ()
reduceUsage = int(max_workers * 0.2)

#######################################################################################################################
##                    USER INTERFACE                                                                                 ##
#######################################################################################################################

class mainWindowUI (QMainWindow):
    
    ## defines the widgets and layout
    def __init__(self):
        super().__init__()
        
        ## variables
        global mtlTX
        mtlTX = False
        
        ## set window size
        self.setWindowTitle("TexToMtlX Version 1.2")
        self.setFixedSize(340, 570)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        ## set variables to help with layout
        yHeight = 130

        #########################################################
        #####                   UI                          #####
        #########################################################
        ## HELP BUTTON
        self.helpButton = QPushButton("Instructions", self)
        self.helpButton.setGeometry(30, 35, 291, 80)
        self.helpButton.clicked.connect(self.helpMenu)
        ## SELECT LIB BUTTON
        self.btLib = QPushButton("Material Lib", self)
        self.btLib.setGeometry(30, yHeight, 140, 70)
        self.btLib.clicked.connect(self.getMtlLib)
        ## OPEN FOLDER BUTTON
        self.btOpenFolder = QPushButton("Open Folder", self)
        self.btOpenFolder.setGeometry(180, yHeight + 30, 125, 40)
        self.btOpenFolder.setEnabled(False)
        self.btOpenFolder.clicked.connect(self.openFolder)
        ## TOP LEVEL LABEL
        self.mtlLab = QLabel("List of Materials:", self)
        self.mtlLab.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.mtlLab.setGeometry(30,yHeight + 90, 101,21)
        self.mtlLab.setWordWrap(True)
        ## CHECKBOX BUTTON
        self.checkbox = QCheckBox("Convert to Tx?", self)
        self.checkbox.setGeometry(180,yHeight,140,20)
        self.checkbox.setEnabled(False)
        self.checkbox.stateChanged.connect(self.onCheckBox)
        ## SELECTED ALL BUTTON
        self.btSelAll = QPushButton("All", self)
        self.btSelAll.setGeometry(150, yHeight + 90, 75, 20)
        self.btSelAll.setEnabled(False)
        self.btSelAll.clicked.connect(self.selectAll)
        ## SELECTED None BUTTON
        self.btSelNon = QPushButton("Reset", self)
        self.btSelNon.setGeometry(240, yHeight + 90, 75, 20)
        self.btSelNon.setEnabled(False)
        self.btSelNon.clicked.connect(self.deselectAll)
        ## LIST VIEW
        self.materialList = QListView(self)
        self.materialList.setObjectName(u"materialList")
        self.materialList.setGeometry(QRect(30, yHeight + 120, 291, 192))
        self.model = QStandardItemModel()
        ## CREATE MATERIALS BUTTON
        self.btCreate = QPushButton("Create Materials", self)
        self.btCreate.setGeometry(30, yHeight+320, 290, 50)
        self.btCreate.setEnabled(False)
        self.btCreate.clicked.connect(self.createMaterials)
        ## PROGRESS BAR
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(30,yHeight + 380,300,30)
        self.progressBar.setValue(0)
    
    ################################################################
    #####                   FUNCTIONS                          #####
    ################################################################
    
    ## Get the Material Lib information
    def getMtlLib(self): 
        global node
        global path 
        path = hou.ui.selectNode(title="Select one material library")
               
        if path == None:
            pass
        else:
            node = hou.node(path)
            expectedTypeLops = hou.nodeType(hou.lopNodeTypeCategory(), "materiallibrary")
            expectedTypeSops = hou.nodeType(hou.objNodeTypeCategory(), "matnet")
                
            if node.type() == expectedTypeLops or node.type() == expectedTypeSops or str(node) == 'mat':
                self.btOpenFolder.setEnabled(True)
            else:
                hou.ui.displayMessage("This isn't a material lib in LOPs, please select again", buttons=("OK",))
                self.btOpenFolder.setEnabled(False)

    ## Check if folder has images
    def folderImages(self, folder):
        found = False
        
        for file in os.listdir(folder):
            textures = os.path.join(folder, file)
            
            if os.path.isfile(textures) and file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.exr', '.bmp')):
                if '_' in file:
                    found = True
        return found

    ## Get help
    def helpMenu(self):
        textToDisplay = """Instructions\n\n\n Supports textures with and without UDIMs. 
                        \nMATERIAL_TEXTURE_UDIM    or    MATERIAL_TEXTURE
                        \nFor example: tires_Alb_1001.tif    or    tires_Alb.tif
                        \nNaming Convention for the textures:
                        \nColor: diffuse, diff, albedo, alb, base, col, color, basecolor,
                        \nMetal: metallic, metalness, metal, mtl, met,
                        \nSpecular: specularity, specular, spec, spc, 
                        \nRoughness: roughness, rough, rgh,
                        \nGlossiness: gloss, glossy, glossiness, 
                        \nTransmisson: transmission, transparency, trans,
                        \nSSS: translucency, 
                        \nEmmission: emission, emissive, emit, emm, 
                        \nOpacity: opacity, opac, alpha,
                        \nAmbient Occlusion: ambient_occlusion, ao, occlusion, cavity,
                        \nBump: bump, bmp,
                        \nHeight:displacement, displace, disp, dsp, heightmap, 'height',
                        \nExtra: user, mask, 
                        \nNormal: normal, nor, nrm, nrml, norm. """
        hou.ui.displayMessage(text = textToDisplay, buttons=('OK',), severity=hou.severityType.ImportantMessage)
    
    ## Get the material and texture name
    def retriveMtlName(self, path):
            
        textures = []
        global textList
        textList = defaultdict(lambda: defaultdict(list))
        for file in os.listdir(path):
            texPath = os.path.join(path, file).replace("\\","/")
                        
            if os.path.isfile(texPath) and file.lower().endswith(tuple(textureExt)):
                textures.append(file)
        
        for texture in textures:
        
            #split based on underscore, skipping any files without underscores
            if '_' not in texture:
                continue

            #extract material name
            texParts = texture.split('_')
            mtlName = texParts[0]
            mtlRest = "_".join(texParts[1:]) ## new var to avoid materials that have keys in the name, like metalRims has metal in it and can cause issues
            mtlRestSplit = mtlRest.split('_')
            #check if texture type exists in name
            texType = None

            for tType in texturesTypes:
                if any(tType in part.lower() or tType.capitalize() in part for part in mtlRestSplit):
                    texType = tType
                    break
            
            # if texture type isn't valid just skip it
            if not texType:
                continue
            
            #check UDIMs
            udimMatch = udimPattern.search(texture)
            udimPresent = bool(udimMatch)
            #check Size
            sizeMatch = sizePattern.search(texture)
            size = sizeMatch.group(1) if sizeMatch else None

            ## add textures to dictionary
            textList[mtlName][texType].append(texture)
            textList[mtlName]['UDIM'] = udimPresent

            if size:
                textList[mtlName]['Size'] = size

        textList = {k: dict(v) for k, v in textList.items()}
        
        ## this adds the texture list to the QViewList
        for key, value in textList.items():
            item = QStandardItem(key)
            self.model.appendRow(item)
        
        ## this adds some functionalities to be able to select those materials.
        self.materialList.setModel(self.model)
        self.materialList.setSelectionMode(QListView.MultiSelection)
        self.materialList.selectAll()
        ## set UI
        
        self.btSelAll.setEnabled(True)
        self.btSelNon.setEnabled(True)
        self.btSelAll.clicked.connect(self.materialList.selectAll)
               
    ## FUNCTION for the Open Folder Button
    def openFolder(self):
        global folderPath
        ##reset list in case there is previous materials
        self.model.clear()
        self.progressBar.setValue(0)
        #check for textures inside the folder
        folderPath = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folderImages(folderPath):
            self.retriveMtlName(folderPath)
            self.btCreate.setEnabled(True)
            self.checkbox.setEnabled(True)
        else:
            hou.ui.displayMessage("There are no textures inside this folder or any valid textures. \n\nCheck top label to understand the correct naming convention.", buttons=("Ok",))
    ## FUNCTION to run the script
    def createMaterials(self):
        selectedRows = self.materialList.selectedIndexes()
        self.progressBar.setMaximum(len(selectedRows))        
        progressBar = 0
        if len(selectedRows)==0:
            hou.ui.displayMessage(text="Select at least one material", buttons=('OK',))
        else:
            for index in selectedRows:
                row = index.row()
                key = list(textList .keys())[row]
                createMaterial = material(key, mtlTX)
                createMaterial.myfunc()
                
                self.progressBar.setValue(progressBar+1)
                progressBar +=1
    ## FUNCTIONS TO WORK WITH THE LIST VIEW
    def selectAll(self):
        self.materialList.setSelectionMode(QListView.MultiSelection)
        for i in range(self.model.rowCount()):
            self.model.item(i).setEnabled(True)
    def deselectAll(self):
        self.materialList.clearSelection()
        self.materialList.setSelectionMode(QListView.MultiSelection)
    ## FUNCTION for the checkbox TX
    def onCheckBox(self,state):
        global mtlTX
        
        if state == Qt.Checked:
            mtlTX = True
        else:
            mtlTX = False

##############################################################################################
######                          CLASS MATERIAL                                         #######
##############################################################################################

class material: ## blueprint to create the materialX
    def __init__(self, mat, mtlTX):
        self.mat = mat
        self.mtlTX = mtlTX
            
    def myfunc(self):
        getMat = textList[self.mat] ## base on the material's name get all textures associate to it 
        
        ##Add Size to the name
        if 'Size' in getMat:
            newMaterialName = self.mat + "_" + getMat['Size']
        else:
            newMaterialName = self.mat
        
        ##check if the material already exists and deletes it
        obj = hou.node(path) ##get path to material lib
        getExistingMaterials = obj.children()
        
        for mat in getExistingMaterials:
            if mat.name() == newMaterialName:
                mat.destroy()
        
        ## create subnet for the USD MaterialX
        mtlxSubnet = node.createNode("subnet", newMaterialName)
        subnetContext = node.node(mtlxSubnet.name())
        delSubOutput = subnetContext.allItems()
        delSubOutput[0].destroy()
        
        ##########################################################################################################################################################
        ## start create subnet folder MaterialX for mtlX context - STARTS
        groupParm = hou.ParmTemplateGroup()

        ## FOLDER MATERIALX
        mainParm = hou.FolderParmTemplate("folder1", "MaterialX Builder", folder_type=hou.folderType.Collapsible, default_value=0, ends_tab_group=False)
        mainParm.setTags({"group_type": "collapsible", "sidefx::shader_isparm": "0"})

        ##INHERIT FROM CLASS
        parmTemplate = hou.IntParmTemplate("inherit_ctrl", "Inherit from Class", 1, default_value=([2]), min=0, max=10, min_is_strict=False, max_is_strict=False, look=hou.parmLook.Regular, naming_scheme=hou.parmNamingScheme.Base1, menu_items=(["0","1","2"]), menu_labels=(["Never","Always","Material Flag"]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal, menu_use_token=False)
        mainParm.addParmTemplate(parmTemplate)

        ## CLASS ARC
        parmTemplate = hou.StringParmTemplate("shader_referencetype", "Class Arc", 1, default_value=(["n = hou.pwd()\nn_hasFlag = n.isMaterialFlagSet()\ni = n.evalParm('inherit_ctrl')\nr = 'none'\nif i == 1 or (n_hasFlag and i == 2):\n    r = 'inherit'\nreturn r"]), default_expression=(["n = hou.pwd()\nn_hasFlag = n.isMaterialFlagSet()\ni = n.evalParm('inherit_ctrl')\nr = 'none'\nif i == 1 or (n_hasFlag and i == 2):\n    r = 'inherit'\nreturn r"]), default_expression_language=([hou.scriptLanguage.Python]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=(["none","reference","inherit","specialize","represent"]), menu_labels=(["None","Reference","Inherit","Specialize","Represent"]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal)
        parmTemplate.setTags({"sidefx::shader_isparm": "0", "spare_category": "Shader"})
        mainParm.addParmTemplate(parmTemplate)

        ## Class Prim Path
        parmTemplate = hou.StringParmTemplate("shader_baseprimpath", "Class Prim Path", 1, default_value=(["/__class_mtl__/`$OS`"]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal)
        parmTemplate.setTags({"script_action": "import lopshaderutils\nlopshaderutils.selectPrimFromInputOrFile(kwargs)", "script_action_help": "Select a primitive in the Scene Viewer or Scene Graph Tree pane.\nCtrl-click to select using the primitive picker dialog.", "script_action_icon": "BUTTONS_reselect", "sidefx::shader_isparm": "0", "sidefx::usdpathtype": "prim", "spare_category": "Shader"})
        mainParm.addParmTemplate(parmTemplate)

        ## SEPARADOR
        parmTemplate = hou.SeparatorParmTemplate("separator1")
        mainParm.addParmTemplate(parmTemplate)

        ## TAB MENU
        parmTemplate = hou.StringParmTemplate("tabmenumask", "Tab Menu Mask", 1, default_value=(["MaterialX parameter constant collect null genericshader subnet subnetconnector suboutput subinput"]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal)
        parmTemplate.setTags({"spare_category": "Tab Menu"})
        mainParm.addParmTemplate(parmTemplate)

        ## RENDER CONTEXT
        parmTemplate = hou.StringParmTemplate("shader_rendercontextname", "Render Context Name", 1, default_value=(["mtlx"]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal)
        parmTemplate.setTags({"sidefx::shader_isparm": "0", "spare_category": "Shader"})
        mainParm.addParmTemplate(parmTemplate)

        ## FORCE 
        parmTemplate = hou.ToggleParmTemplate("shader_forcechildren", "Force Translation of Children", default_value=True)
        parmTemplate.setTags({"sidefx::shader_isparm": "0", "spare_category": "Shader"})
        mainParm.addParmTemplate(parmTemplate)

        groupParm.append(mainParm)
        mtlxSubnet.setParmTemplateGroup(groupParm)
        mtlxSubnet.setMaterialFlag(True)
        
        ## end create subnet folder MaterialX for mtlX context - ENDS
        ##########################################################################################################################################################
               
        ## setting up the surface output
        mtlxSubSConnect = subnetContext.createNode('subnetconnector', 'surface_ouput')
        mtlxSubSConnect.parm('connectorkind').set("output")
        mtlxSubSConnect.parm('parmname').set("surface")
        mtlxSubSConnect.parm('parmlabel').set("Surface")
        mtlxSubSConnect.parm('parmtype').set("surface")
        mtlxSubSConnect.setColor(hou.Color(0.89, 0.69, 0.6))

        ## setting up the displacement output
        mtlxSubDConnect = subnetContext.createNode('subnetconnector', 'displacement_output')
        mtlxSubDConnect.parm('connectorkind').set("output")
        mtlxSubDConnect.parm('parmname').set("displacement")
        mtlxSubDConnect.parm('parmlabel').set("Displacement")
        mtlxSubDConnect.parm('parmtype').set("displacement")
        mtlxSubDConnect.setColor(hou.Color(0.6, 0.69, 0.89))
        
        ## creating the mtlxSurface
        mtlxStandS = subnetContext.createNode('mtlxstandard_surface', "mtlxSurface")
        mtlxDisp = subnetContext.createNode('mtlxdisplacement', "mtlxDisp")
        mtlxSubSConnect.setInput(0, mtlxStandS)
        mtlxSubDConnect.setInput(0, mtlxDisp)

        inputNames = mtlxStandS.inputNames()
        textureTypesSorted = { 
            'texturesColor' :['diffuse', 'diff', 'albedo', 'alb', 'base', 'col', 'color', 'basecolor'], 
            'texturesMetal' : ['metallic', 'metalness', 'metal', 'mtl', 'met'], 
            'texturesSpecular' : ['specularity', 'specular', 'spec', 'spc'], 
            'texturesRough': ['roughness', 'rough', 'rgh'], 
            'texturesGloss' : ['gloss', 'glossy', 'glossiness'], 
            'texturesTrans' : ['transmission', 'transparency', 'trans'],
            'texturesEmm' : ['emission', 'emissive', 'emit', 'emm'], 
            'texturesAlpha' : ['alpha', 'opacity', 'opac'], 
            'texturesAO': ['ao', 'ambient_occlusion', 'occlusion'], 
            'texturesBump' : ['bump', 'bmp', 'height'], 
            'texturesDisp': ['displacement', 'displace', 'disp', 'dsp', 'heightmap'],
            'texturesExtra' : ['user', 'mask'] , 
            'texturesNormal': ['normal', 'nor', 'nrm', 'nrml', 'norm'],
            'texturesSSS' : ['translucency']
        }
        ## setup for Height(bump) and Normal maps
        bumpFound = False
        normalFound = False
        bumpNormal = {'normal':'', 'bump':''}
        bumpNormalSplit = {}

        ## TX Conversion
        getMatTx = []

        if self.mtlTX == True:
            for key, value in getMat.items():
                if key not in ['UDIM','Size']:
                    if isinstance(value, list):
                        getMatTx.extend(value)
            for x in getMatTx:
                newPath = folderPath + "/" + x.split('.')[0] + ".tx"
                oldPath = folderPath + "/" + x
                command = f'"{imaketxPath}" "{oldPath}" "{newPath}" --newer'
                subprocess.run(command, shell=True, capture_output=True, text=True)

        ## adding the 2D place control for textures without an UDIM
        if 'UDIM'in getMat:
            if getMat['UDIM'] == True:                    
                mtlxImageType = "mtlximage"
            else:
                mtlxImageType = "mtlxtiledimage"
                textCoord = subnetContext.createNode('mtlxtexcoord', self.mat + "_texcoord")
                textScale = subnetContext.createNode('mtlxconstant', self.mat + "_scale")
                textRotate = subnetContext.createNode('mtlxconstant', self.mat + "_rotate")
                textOffset = subnetContext.createNode('mtlxconstant', self.mat + "_offset")
                textPlace2D = subnetContext.createNode('mtlxplace2d', self.mat + "_place2d")
                textScale.parm('value').set(1)

                textPlace2D.setInput(0, textCoord)
                textPlace2D.setInput(2, textScale)
                textPlace2D.setInput(3, textRotate)
                textPlace2D.setInput(4, textOffset)  
        
        for texture in getMat:
            for textureKey, textureValue in textureTypesSorted.items():
                if texture in textureValue:
                    tex = texture ## this get's the key name for the nested dictionary [tires: {Alb: stuff }] we get the Alb key
                    firstValue = getMat[tex][0] # we only need the first value in the nested dictionary
                    
                    if self.mtlTX == True:
                        textValue = firstValue.split(".")[0]
                        firstValue = (str(textValue) + ".tx")
                    else:
                        firstValue = getMat[tex][0]
                                        
                    firstValue = folderPath + "/" + firstValue
                
                    ## adding the option for variable paths
                    if jobVar in firstValue:
                        firstValue = firstValue.replace(jobVar, "$JOB")
                
                    ##create the image materialx node
                    texMain = subnetContext.createNode(mtlxImageType, tex) # this creates a image for each the texture sets from listText - Alb, Disp, etc
                    texMain.parm('signature').set('color3')
                
                    if textureKey == 'texturesColor':
                        rangeAlb = subnetContext.createNode("mtlxrange", tex + "_CC")
                        rangeAlb.setInput(0, texMain)
                        mtlxStandS.setInput(inputNames.index("base_color"), rangeAlb)
                        texMain.parm('filecolorspace').set('srgb_texture')
                        if 'UDIM'in getMat:
                            if getMat['UDIM'] == False:
                                 texMain.setInput(2, textPlace2D)

                    if textureKey == 'texturesSSS':
                        texMain.parm('signature').set('color3')
                        texMain.parm('filecolorspace').set('srgb_texture')
                        if 'UDIM'in getMat:
                            if getMat['UDIM'] == False:
                                 texMain.setInput(2, textPlace2D)


                    if textureKey == 'texturesMetal' or textureKey == 'texturesSpecular' or textureKey == 'texturesRough' or textureKey == 'texturesGloss' or textureKey == 'texturesTrans' or textureKey == 'texturesEmm' or textureKey == 'texturesAlpha' or textureKey == 'texturesAO' or textureKey == 'texturesBump' or textureKey == 'texturesDisp':
                        ## sets color space based on the texture type            
                        texMain.parm('signature').set("float")
                        texMain.parm('filecolorspace').set('Raw')
                        if 'UDIM'in getMat:
                            if getMat['UDIM'] == False:
                                 texMain.setInput(2, textPlace2D)

                    if textureKey == 'texturesExtra':
                        texMain.parm('signature').set('color3')
                        texMain.parm('filecolorspace').set('srgb_texture')
                        separateUser = subnetContext.createNode('mtlxseparate3c', 'separateUser')
                        separateUser.setInput(0, texMain)
                        if 'UDIM'in getMat:
                            if getMat['UDIM'] == False:
                                 texMain.setInput(2, textPlace2D)

                    if textureKey == 'texturesNormal':
                        ## sets color space based on the texture type
                        texMain.parm('signature').set('vector3')
                        texMain.parm('filecolorspace').set('Raw')
                        bumpNormal['normal'] = texMain.path()
                        bumpNormalSplit[textureKey] = textureValue
                        if 'UDIM'in getMat:
                            if getMat['UDIM'] == False:
                                 texMain.setInput(2, textPlace2D)
                                        
                    if textureKey == 'texturesBump':
                        texMain.parm('signature').set("float")
                        texMain.parm('filecolorspace').set('Raw')
                        bumpNormal['bump'] = texMain.path()
                        bumpNormalSplit[textureKey] = textureValue
                        if 'UDIM'in getMat:
                            if getMat['UDIM'] == False:
                                 texMain.setInput(2, textPlace2D)
                                        
                    ## assigns the texture according to the name
                    if textureKey == 'texturesMetal': 
                        mtlxStandS.setInput(inputNames.index("metalness"), texMain)
                    
                    if textureKey == 'texturesSpecular':
                        mtlxStandS.setInput(inputNames.index("specular"), texMain)
                    
                    if textureKey == 'texturesRough':
                        rangeRough = subnetContext.createNode("mtlxrange", tex + "_CC")
                        rangeRough.setInput(0, texMain)
                        mtlxStandS.setInput(inputNames.index("specular_roughness"), rangeRough)

                    if textureKey == 'texturesGloss':
                        rangeGloss = subnetContext.createNode("mtlxrange", tex + "_CC")
                        rangeGloss.setInput(0, texMain)
                        rangeGloss.parm('outlow').set(1)
                        rangeGloss.parm('outhigh').set(0)
                        mtlxStandS.setInput(inputNames.index("specular_roughness"), rangeGloss)
                    
                    if textureKey == 'texturesTrans':
                        mtlxStandS.setInput(inputNames.index("transmission"), texMain)
                    
                    if textureKey == 'texturesEmm':
                        mtlxStandS.setInput(inputNames.index("emission"), texMain)
                    
                    if textureKey == 'texturesAlpha':
                        mtlxStandS.setInput(inputNames.index("opacity"), texMain)
                    
                    if textureKey == 'texturesAO':
                        mixAO = subnetContext.createNode("mtlxmix", tex + "_AO")
                        mixAO.setInput(2, texMain)
                    
                    if textureKey == 'texturesDisp':
                        mtlxDisp.setInput(0, texMain)
                    
                    if textureKey == 'texturesSSS':
                        mtlxStandS.setInput(inputNames.index("subsurface_color"), texMain)
                        mtlxStandS.parm('subsurface').set(1)

                    ## setup UDIM
                    if 'UDIM'in getMat:
                        if getMat['UDIM'] == True:
                            replaceUdim = firstValue.replace("1001", "<UDIM>")
                            texMain.parm('file').set(replaceUdim)
                        else:
                            texMain.parm('file').set(firstValue)
                    else:
                        texMain.parm('file').set(firstValue)
        
        ## we need to first check if we have a bump texture, then we check if we have a normal texture
        bumpName = ""
        normalName = ""
        
        for texture in getMat:
            for textureKey, textureValue in textureTypesSorted.items():
                if texture in textureValue:
                    if textureKey == 'texturesBump':
                        bumpFound = True
                        bumpName = texture
                    if textureKey == 'texturesNormal':
                        normalFound = True
                        normalName = texture
        print(bumpName)######################
        print(normalName)###################
        
        if bumpFound or normalFound:

            if bumpName:
                firstValueBump = getMat[bumpName][0]
                
                if self.mtlTX == True:
                    textValueBump = firstValueBump.split(".")[0]
                    firstValueBump = (str(textValueBump) + ".tx")
                
                firstValueBump = folderPath + "/" + firstValueBump
            else:
                pass

            if normalName:
                firstValueNormal = getMat[normalName][0]

                if self.mtlTX == True:
                    textValueNormal = firstValueNormal.split(".")[0]
                    firstValueNormal = (str(textValueNormal) + ".tx")
                firstValueNormal = folderPath + "/" + firstValueNormal
            
            else:
                pass    

                
            if bumpFound and normalFound:
                
                bump = hou.node(bumpNormal['bump'])
                normal = hou.node(bumpNormal['normal'])
                mtlxBump = subnetContext.createNode('mtlxbump', 'mtlxBump')
                mtlxBump.setInput(0,bump)
                mtlxStandS.setInput(inputNames.index("normal"), mtlxBump)
                mtlxNormal = subnetContext.createNode('mtlxnormalmap', 'mtxlNormal')
                mtlxNormal.setInput(0, normal)
                mtlxBump.setInput(3, mtlxNormal)
            
                if 'UDIM'in getMat:
                
                    if getMat['UDIM'] == True:
                        replaceUdimBump = firstValueBump.replace("1001", "<UDIM>")
                        replaceUdimNormal = firstValueNormal.replace("1001", "<UDIM>")
                        bump.parm('file').set(replaceUdimBump)
                        normal.parm('file').set(replaceUdimNormal)
                    else:
                        bump.parm('file').set(firstValueBump)
                        normal.parm('file').set(firstValueNormal)
                else:
                     bump.parm('file').set(firstValueBump)
                     normal.parm('file').set(firstValueNormal)
        
            elif bumpFound and not normalFound:

                bump = hou.node(bumpNormal['bump'])
                mtlxBump = subnetContext.createNode('mtlxbump', 'mtlxBump')
                mtlxBump.setInput(0,bump)
                mtlxStandS.setInput(inputNames.index("normal"), mtlxBump)

                if 'UDIM'in getMat:
                    if getMat['UDIM'] == True:
                        replaceUdim = firstValueBump.replace("1001", "<UDIM>")
                        bump.parm('file').set(replaceUdim)
                    else:
                        bump.parm('file').set(firstValueBump)
                else:
                    bump.parm('file').set(firstValueBump)
                        
            elif normalFound and not bumpFound:
                
                normal = hou.node(bumpNormal['normal'])
                mtlxNormal = subnetContext.createNode('mtlxnormalmap', 'mtxlNormal')
                mtlxNormal.setInput(0, normal)
                mtlxStandS.setInput(inputNames.index("normal"), mtlxNormal)

                if 'UDIM'in getMat:
                    if getMat['UDIM'] == True:
                        replaceUdim = firstValueNormal.replace("1001", "<UDIM>")
                        normal.parm('file').set(replaceUdim)
                    else:
                        normal.parm('file').set(firstValueNormal)
                else:
                    normal.parm('file').set(firstValueNormal)
                            
        subnetContext.layoutChildren()
        obj.layoutChildren()

windowUI = mainWindowUI()
windowUI.show()