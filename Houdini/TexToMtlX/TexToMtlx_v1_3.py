#######################################################################################################################
## TexToMtlX Version 1.3 by Ciro Cardoso                                                                             ##
## This tool converts the textures inside a folder(s) or a texture selection into                                    ##
## TX files                                                                                                          ##
##                                                                                                                   ##
## For feedback, suggestions or bugs, get in touch - cirocardoso@yahoo.co.uk                                         ##
##                                                                                                                   ##
## Thanks to @_Approximated_ and @yonatanbary for the help testing the code and the ideas                            ##
## Version 1.1 - Added support for cavity, translucency maps. Added support to mtlXTiledImage                        ##
## Version 1.2 - Fix for the Solaris Composition Arc missing from material, fix for images without underscore        ##
## Version 1.3 - Clean up the code, implemented the option to select multiple folders, fix issue with the normal     ##
##                                                                                                                   ##
#######################################################################################################################
import hou
import os
import re
import subprocess
import time 
import logging
import threading

from PySide2 import QtWidgets, QtGui, QtCore
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

class TxToMtlx (QtWidgets.QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        # SETUP CENTRAL WIDGET FOR UI
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # WINDOW PROPERTIES
        self.setWindowTitle("TexToMtlX Tool")
        self.resize(340, 570)
        self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        ## DATA
        self.mtlTX = False # Checkbox Convert to TX

        self._setup_help_section()
        self._setup_material_section()
        self._setup_list_section()
        self._setup_create_section()
        self._setup_connections()
        self.init_constants()

    def init_constants(self):
        '''Initialize constant values used throughtout the class'''

        # For material library information
        self.node_path = None
        self.node_lib = None
        self.folder_path = None

        # Texture related contants
        self.TEXTURE_EXT = ['.jpg', '.jpge', '.png', '.bmp', '.tif', '.tiff', '.exr', '.targa']
        self.TEXTURE_TYPES = ['diffuse', 'diff', 'albedo', 'alb', 'base', 'col', 'color', 'basecolor',
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
        self.texture_list = None
        self.UDIM_PATTERN = re.compile(r'(?:_)?(\d{4}())')
        self.SIZE_PATTERN = re.compile(r'(?:_)?(\d+[Kk])')

    def _setup_help_section(self):
        '''Setup the help button section'''
        self.help_layout = QtWidgets.QVBoxLayout()

        self.bt_instructions = QtWidgets.QPushButton("Instructions")
        self.bt_instructions.setMinimumHeight(80)
        self.help_layout.addWidget(self.bt_instructions)
        self.main_layout.addLayout(self.help_layout)
    
    def _setup_material_section(self):
        '''Setup the material library section'''

        self.material_layout = QtWidgets.QGridLayout()
        # MATERIAL LIBRARY
        self.bt_lib = QtWidgets.QPushButton("Material Lib")
        self.bt_lib.setMinimumHeight(70)
        self.material_layout.addWidget(self.bt_lib, 0, 0, 2, 1)
        # TX CHECKBOX
        self.checkbox = QtWidgets.QCheckBox("Convert to TX?")
        self.checkbox.setEnabled(False)
        self.material_layout.addWidget(self.checkbox, 1, 1)
        # OPEN FOLDER
        self.bt_open_folder = QtWidgets.QPushButton("Open Folder")
        self.bt_open_folder.setMinimumHeight(40)
        self.bt_open_folder.setEnabled(False)
        self.material_layout.addWidget(self.bt_open_folder, 0, 1)
        
        self.main_layout.addLayout(self.material_layout)
        
    def _setup_list_section(self):
        '''Setup the material list section'''
        self.list_layout = QtWidgets.QVBoxLayout()

        # HEADER LAYOUT
        self.header_layout = QtWidgets.QHBoxLayout()

        self.lb_material_list = QtWidgets.QLabel("List of Materials:")
        self.bt_sel_all = QtWidgets.QPushButton("All")
        self.bt_sel_non = QtWidgets.QPushButton("Reset")
        
        self.bt_sel_all.setEnabled(False)
        self.bt_sel_non.setEnabled(False)

        self.header_layout.addWidget(self.lb_material_list)
        self.header_layout.addWidget(self.bt_sel_all)
        self.header_layout.addWidget(self.bt_sel_non)

        # MATERIAL LIST
        self.material_list = QtWidgets.QListView()
        self.material_list.setMinimumHeight(200)
        self.model = QtGui.QStandardItemModel()
        self.material_list.setModel(self.model)
        self.material_list.setSelectionMode(QtWidgets.QListView.MultiSelection)

        self.list_layout.addLayout(self.header_layout)
        self.list_layout.addWidget(self.material_list)
        self.main_layout.addLayout(self.list_layout)
    
    def _setup_create_section(self):
        """Setup the create button and progress bar section"""
        self.create_layout = QtWidgets.QVBoxLayout()
        
        # Create Button
        self.bt_create = QtWidgets.QPushButton("Create Materials")
        self.bt_create.setMinimumHeight(50)
        self.bt_create.setEnabled(False)
                
        # Progress Bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setValue(0)
        
        self.create_layout.addWidget(self.bt_create)
        self.create_layout.addWidget(self.progress_bar)
        
        self.main_layout.addLayout(self.create_layout)        
    
    def _setup_connections(self) :
        '''Setup Signal Connections'''
        self.bt_instructions.clicked.connect(self.help_menu)
        self.bt_lib.clicked.connect(self.get_mtl_lib)
        self.bt_open_folder.clicked.connect(self.open_folder)
        self.checkbox.stateChanged.connect(self.on_checkbox)
        self.bt_sel_all.clicked.connect(self.select_all_mtl)
        self.bt_sel_non.clicked.connect(self.deselect_all_mtl)
        self.bt_create.clicked.connect(self.create_materials)

    def help_menu(self):
        '''Simple method to show instrcutions on how to use the tool'''

        text_to_display = """
                        Instructions\n\n\nSupports textures with and without UDIMs.
                        \nMATERIAL_TEXTURE_UDIM or MATERIAL_TEXTURE
                        \nFor example: tires_Alb_1001.tif or tires_Alb.tif
                        \nNaming Convention for the textures:
                        \nColor: diffuse, diff, albedo, alb, base, col, color, basecolor,
                        \nMetal: metallic, metalness, metal, mlt, met,
                        \nSpecular: speculatiry, specular, spec, spc,
                        \nRouhness: roughness, rough, rgh,
                        \nGlossiness: gloss, glossy, glossiness,
                        \nTransmission: transmission, transparency, trans,
                        \nSSS: translucency, sss,
                        \nEmission: emission, emissive, emit, emm,
                        \nOpacity: opacity, opac, alpha,
                        \nAmbient Occlusion: ambient_occlusion, ao, occlusion, cavity,
                        \nBump: bump, bmp,
                        \nHeight: displacement, displace, disp, dsp, heightmap, height,
                        \nExtra: user, mask,
                        \nNormal: normal, nor, nrm, nrml, norm
                        """
        hou.ui.displayMessage(text_to_display, severity = hou.severityType.ImportantMessage)

    def get_mtl_lib(self):
        '''Get the base material library where the materials are going to be saved'''

        self.node_path = hou.ui.selectNode(
            title = "Please select on material library", 
            node_type_filter = hou.nodeTypeFilter.ShopMaterial)
        
        if self.node_path:
            # Grabbing the material library object
            self.node_lib = hou.node(self.node_path)
            # Check if the material library select is inside a locked HDA
            if self.node_lib.isInsideLockedHDA():
                hou.ui.displayMessage(
                    "This isn't a valid material lib to create the materials. Please select again", 
                    severity = hou.severityType.Error)
            else:
                self.bt_open_folder.setEnabled(True)
                
    def open_folder(self):
        '''
        Grab the folder that contains the textures
        And resets the UI
        '''
        self.model.clear()
        self.progress_bar.setValue(0)
        # Dictionary for textures
        self.texture_list = {}
        
        folders_to_check = hou.ui.selectFile(
            title = "Select folder(s)", file_type = hou.fileType.Directory, multiple_select=True)
        
        self.folder_path = [hou.text.expandString(folder.strip()) 
            for folder in folders_to_check.split(';') if folder.strip()]
        
        self.folder_path = [folder for folder in self.folder_path if self.folder_with_textures(folder)]
        
        if self.folder_path:
            for folder in self.folder_path:
                if self.folder_with_textures(folder):
                    self.bt_create.setEnabled(True)
                    self.checkbox.setEnabled(True)
                    self.get_texture_details(folder)
                else:
                    hou.ui.displayMessage(
                        "There are not textures inside this folder or any valid textures.\n\nCheck Instructions",
                        severity = hou.severityType.Error
                    )

    def get_texture_details(self, path):
        '''Get the details for the textures inside a folder'''
        try:
            texture_list = defaultdict(lambda: defaultdict(list))

            # Validate the path
            if not os.path.exists(path):
                raise ValueError(f"Path does not exist {path}")
            
            # Get all the valid textures inside the folder

            valid_files = []
            
            for file in os.listdir(path):
                file_path = os.path.join(path, file)


                # Condition
                is_file = os.path.isfile(file_path)
                valid_extension = file.lower().endswith(tuple(self.TEXTURE_EXT))
                check_underscore = "_" in file

                if is_file and valid_extension and check_underscore:
                    valid_files.append(file)
            
            # Process files - textures
            for file in valid_files:
                split_text = file.split("_")
                material_name = split_text[0]
                
                # Find the texture type
                texture_type = None

                for tx_type in self.TEXTURE_TYPES:
                    for tx in split_text[1:]:
                        if tx_type in tx.lower():
                            texture_type = tx_type
                            break
                if not texture_type:
                    continue
                
                # Get UDIM and SIZE
                udim_match = self.UDIM_PATTERN.search(file)
                size_match = self.SIZE_PATTERN.search(file)
                
                # Add Path
                texture_list[material_name]['path'] = path

                # Update texture list
                texture_list[material_name][texture_type].append(file)
                texture_list[material_name]['UDIM'] = bool(udim_match)
                if size_match:
                    texture_list[material_name]['Size'] = size_match.group(1)

            # Convert defaultdict to regular dictionary
            _new_dict = {}

            for mat, tex_data in texture_list.items():
                _new_dict[mat] = dict(tex_data)

            self.texture_list.update(_new_dict)
            
            # Update the UI
            self.model.clear()
            for mat in self.texture_list:
                self.model.appendRow(QtGui.QStandardItem(mat))

            self.bt_sel_all.setEnabled(True)
            self.bt_sel_non.setEnabled(True)
            
        except Exception as e:
            hou.ui.displayMessage(f"Error retrieving the textures details: {str(e)}",
                                  severity = hou.severityType.Error)

    def folder_with_textures(self, folder):
        '''Checks to see it the folder contains any valid textures'''

        if not os.path.exists(folder):
            return False
        
        try:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)

                if not os.path.isfile(file_path):
                    continue
                if not file.lower().endswith(tuple(self.TEXTURE_EXT)):
                    continue
                if "_" in file:
                    return True

        except (OSError, PermissionError) as e: 
            hou.ui.displayMessage(
                f"Error accessing folder  {folder} : {str(e)}",
                severity = hou.severityType.Error
            )
            return False

    def on_checkbox(self,state):
        '''Check checkbox is on or off'''

        if state == QtCore.Qt.Checked:
            self.mtlTX = True
        else:
            self.mtlTX = False 

    def select_all_mtl(self):
        '''Selects all the items in the list view'''
        selection_model = self.material_list.selectionModel()

        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0)
            selection_model.select(index, QtCore.QItemSelectionModel.Select)

    def deselect_all_mtl(self):
        '''Clear all selections in the list view'''
        self.material_list.clearSelection()

    def create_materials(self):
        '''Passes the info needed to the MtlxMaterialClass'''

        selected_rows = self.material_list.selectedIndexes()

        if len(selected_rows) == 0:
            hou.ui.displayMessage(
                "Please sekect at least one material",
                severity = hou.severityType.Error
            )
            return

        # Setup the progress bar        
        self.progress_bar.setMaximum(len(selected_rows))
        progress_bar_default = 0

        # Common data
        common_data = {
            'mtlTX': self.mtlTX,
            'path': self.node_path,
            'node': self.node_lib,
            'folder_path': self.folder_path
        }

        for index in selected_rows:

            row = index.row()
            key = list(self.texture_list.keys())[row]
            create_material = MtlxMaterial(key, **common_data, texture_list = self.texture_list)
            create_material.create_materialx()

            self.progress_bar.setValue(progress_bar_default+1)
            progress_bar_default += 1

        hou.ui.displayMessage("Material creation completed!!!", severity = hou.severityType.Message)

class MtlxMaterial:

    def __init__(self, mat, mtlTX, path, node, folder_path, texture_list):
        self.material_to_create = mat
        self.mtlTX = mtlTX
        self.node_path = path
        self.node_lib = node
        self.folder_path = folder_path
        self.texture_list = texture_list

        self.init_constants()
        self._setup_imaketx()

    def init_constants(self):
        self.TEXTURE_TYPE_SORTED = { 
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

        # Variables to setup the worker pool
        self.MAX_WORKERS = os.cpu_count()
        self.WORKER_LIMIT = max(1, int(self.MAX_WORKERS * 0.85))

    def _setup_imaketx(self):
        '''Initialize the imaketx tool '''
        imaketx_tool = "imaketx.exe"
        self.imaketx_path = None

        houdini_folder = hou.text.expandString("$HB")

        if houdini_folder:
            self.imaketx_path = os.path.join(houdini_folder, imaketx_tool).replace(os.sep, "/")

            if not os.path.exists(self.imaketx_path):
                raise RuntimeError (f"imaketx tool not found at: {self.imaketx_path}")

    def _convert_to_tx(self, texture_paths, folder_path):
        '''Convert textures to TX using parallel processing with monitoring'''
        
        if not self.mtlTX:
            return 
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("TX Conversion")
        logger.handlers.clear()

        def convert_single_texture(texture_path):
            thread_id = threading.current_thread().ident
            start_time = time.time()

            try:
                logger.info(f"Thread {thread_id}: Starting conversion of {os.path.basename(texture_path)}")

                # Setup the outfile for the imaketx tool
                output_path = os.path.splitext(texture_path)[0] + ".tx"
                command = f'"{self.imaketx_path}" "{texture_path}" "{output_path}" --newer'
                result = subprocess.run(command, shell=True, capture_output=True, text=True)

                end_time = time.time()
                duration = round(end_time - start_time, 2)

                if result.returncode == 0:
                    logger.info(f"Thread {thread_id}: Completed {os.path.basename(texture_path)} in {duration}")
                    return True
                else:
                    logger.error(f"Thread {thread_id}: Failed to convert  {os.path.basename(texture_path)} in {result.stderr}")
                    return False 
            
            except Exception as e:
                logger.error(f"Thread {thread_id}: Error converting {os.path.basename(texture_path)}: {str(e)}")
                return False
            
        texture_paths = [os.path.join(folder_path, tex) for tex in texture_paths]
        total_textures = len(texture_paths)

        start_time = time.time()

        completed = 0
        failed = 0 

        with ThreadPoolExecutor(max_workers=self.WORKER_LIMIT) as executor:
            # Submit all the tasks and get the futures
            future_to_texture = {}
            for path in texture_paths:
                future_to_texture[executor.submit(convert_single_texture, path)] = path 

            # Process completed futures as they finish
            for future in as_completed(future_to_texture):
                texture_path = future_to_texture[future]

                try:
                    if future.result():
                        completed += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Error processing {os.path.basename(texture_path)}: {str(e)}")
                    failed += 1

                # Log progress
                progress = ((completed + failed) / total_textures) * 100
                logger.info(f"Progress: {progress:.1f}% ({completed + failed} / {total_textures})")

        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        
        logger.info(f"Conversion Complete: Total time: {total_time}, Sucessfully converted: {completed}, Failed: {failed}")
        return completed > 0 and failed == 0
    
    def create_materialx(self):
        '''Creates a MaterialX setup'''
        try:
            # Get the material info and handle TX conversion
            material_lib_info = self._prepare_material_info()
            
            # Create and setup the material subnet for MaterialX
            subnet_context = self._create_material_subnet(material_lib_info)
            
            # Create and connect the main nodes
            mtlx_standard_surf, mtlx_displacement = self._create_main_nodes(subnet_context)

            # Setup the place2d nodes if needed
            place2d = self._setup_place2d(subnet_context, material_lib_info)
            
            # Process all textures
            self._process_textures(subnet_context, mtlx_standard_surf, mtlx_displacement, material_lib_info, place2d)

            # Handle the bump and normal maps
            self._setup_bump_normal(subnet_context, mtlx_standard_surf, material_lib_info, place2d)
            # Layout nodes
            self._layout_nodes(subnet_context)

        except Exception as e:
            hou.ui.displayMessage(f"Error creating MaterialX: {str(e)}", severity = hou.severityType.Error)
        
    def _prepare_material_info(self):
        '''Prepares the material information and handles the TX conversion'''
        # From the material dictionary gets the info for the material to be created
        material_lib_info = self.texture_list[self.material_to_create]

        # TX conversion

        if self.mtlTX:
            all_textures = []
            for texture_type, texture_path in material_lib_info.items():
                if texture_type not in ['UDIM', 'Size']:
                    if isinstance (texture_path, list):
                        all_textures.extend(texture_path)
            
            folder_path = material_lib_info['path']
            self._convert_to_tx(all_textures, folder_path)
        
        return material_lib_info
        # Returns the texture information for the material we want to create

    def _create_material_subnet(self, material_lib_info):
        '''
        Create and setup the material subnet
        Args:
            material_lib_info - this is the dictionary with the information regarding the material we want to create
        Return:
            subnet_context - subnet MtlxMaterial to use as context to create the material and other nodes
        '''

        # Add size to the name
        material_name = (self.material_to_create + "_" + material_lib_info['Size']
                         if 'Size' in material_lib_info
                         else self.material_to_create)
        
        # Remove existing material if it exists
        existing_material = self.node_lib.node(material_name)
        if existing_material:
            existing_material.destroy()
        
        # Create the new subnet
        mtlx_subnet = self.node_lib.createNode("subnet", material_name)
        subnet_context = self.node_lib.node(mtlx_subnet.name())

        delete_subnet_output = subnet_context.allItems()
        for index, _ in enumerate(delete_subnet_output):
            delete_subnet_output[index].destroy()

        self._setup_material_parameters(mtlx_subnet)
        mtlx_subnet.setMaterialFlag(True)

        return subnet_context

    def _setup_material_parameters(self, mtlx_subnet):
        '''
        Setting up the USD materialX Builder Subnet with parameters
        Args:
            mtlx_subnet - default subnet
        Return:
            mtlx_subnet - with the correct parameters
        '''
        
        hou_parm_template_group = hou.ParmTemplateGroup()
        
        # FOLDER MATERIALX
        hou_parm_template = hou.FolderParmTemplate("folder1", "MaterialX Builder", folder_type=hou.folderType.Collapsible, default_value=0, ends_tab_group=False)
        hou_parm_template.setTags({"group_type": "collapsible", "sidefx::shader_isparm": "0"})
        # Inherit from Class
        hou_parm_template2 = hou.IntParmTemplate("inherit_ctrl", "Inherit from Class", 1, default_value=([2]), min=0, max=10, min_is_strict=False, max_is_strict=False, look=hou.parmLook.Regular, naming_scheme=hou.parmNamingScheme.Base1, menu_items=(["0","1","2"]), menu_labels=(["Never","Always","Material Flag"]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal, menu_use_token=False)
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Class Arc
        hou_parm_template2 = hou.StringParmTemplate("shader_referencetype", "Class Arc", 1, default_value=(["n = hou.pwd()\nn_hasFlag = n.isMaterialFlagSet()\ni = n.evalParm('inherit_ctrl')\nr = 'none'\nif i == 1 or (n_hasFlag and i == 2):\n    r = 'inherit'\nreturn r"]), default_expression=(["n = hou.pwd()\nn_hasFlag = n.isMaterialFlagSet()\ni = n.evalParm('inherit_ctrl')\nr = 'none'\nif i == 1 or (n_hasFlag and i == 2):\n    r = 'inherit'\nreturn r"]), default_expression_language=([hou.scriptLanguage.Python]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=(["none","reference","inherit","specialize","represent"]), menu_labels=(["None","Reference","Inherit","Specialize","Represent"]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal)
        hou_parm_template2.setTags({"sidefx::shader_isparm": "0", "spare_category": "Shader"})
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Class Prim Path
        hou_parm_template2 = hou.StringParmTemplate("shader_baseprimpath", "Class Prim Path", 1, default_value=(["/__class_mtl__/`$OS`"]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal)
        hou_parm_template2.setTags({"script_action": "import lopshaderutils\nlopshaderutils.selectPrimFromInputOrFile(kwargs)", "script_action_help": "Select a primitive in the Scene Viewer or Scene Graph Tree pane.\nCtrl-click to select using the primitive picker dialog.", "script_action_icon": "BUTTONS_reselect", "sidefx::shader_isparm": "0", "sidefx::usdpathtype": "prim", "spare_category": "Shader"})
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Separator
        hou_parm_template2 = hou.SeparatorParmTemplate("separator1")
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Tab Menu Mask
        hou_parm_template2 = hou.StringParmTemplate("tabmenumask", "Tab Menu Mask", 1, default_value=(["MaterialX parameter constant collect null genericshader subnet subnetconnector suboutput subinput"]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal)
        hou_parm_template2.setTags({"spare_category": "Tab Menu"})
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Render Context Name
        hou_parm_template2 = hou.StringParmTemplate("shader_rendercontextname", "Render Context Name", 1, default_value=(["mtlx"]), naming_scheme=hou.parmNamingScheme.Base1, string_type=hou.stringParmType.Regular, menu_items=([]), menu_labels=([]), icon_names=([]), item_generator_script="", item_generator_script_language=hou.scriptLanguage.Python, menu_type=hou.menuType.Normal)
        hou_parm_template2.setTags({"sidefx::shader_isparm": "0", "spare_category": "Shader"})
        hou_parm_template.addParmTemplate(hou_parm_template2)
        # Force Translation of Children
        hou_parm_template2 = hou.ToggleParmTemplate("shader_forcechildren", "Force Translation of Children", default_value=True)
        hou_parm_template2.setTags({"sidefx::shader_isparm": "0", "spare_category": "Shader"})
        hou_parm_template.addParmTemplate(hou_parm_template2)
        hou_parm_template_group.append(hou_parm_template)
        
        mtlx_subnet.setParmTemplateGroup(hou_parm_template_group)

        return mtlx_subnet

    def _create_main_nodes(self, subnet_context):
        '''
        Create and connect the main material nodes
        Args:
            subnet_context - the subnet where we want to create these nodes
        Return:
            tuple - node for standard surface and node for the displacement
        '''

        # Create main nodes
        mtlx_standard_surf = subnet_context.createNode("mtlxstandard_surface", self.material_to_create + "_mtlxSurface")
        mtlx_displacement = subnet_context.createNode("mtlxdisplacement", self.material_to_create + "_mtlxDisp")

        # Create output nodes
        surface_out = self._create_output_nodes(subnet_context, "surface")
        displacement_out = self._create_output_nodes(subnet_context, "displacement")
         
        # Connect outputs

        surface_out.setInput(0, mtlx_standard_surf)
        displacement_out.setInput(0, mtlx_displacement)

        return mtlx_standard_surf, mtlx_displacement

    def _create_output_nodes(self, context, output_type):
        '''
        Create an output connecto node
        Args:
            context - where to create the node
            output_type - is the type of connector we want to create
        Return:
            node - output connector node
        '''

        node = context.createNode("subnetconnector", f'{output_type}_output')
        node.parm("connectorkind").set("output")
        node.parm("parmname").set(output_type)
        node.parm("parmlabel").set(output_type.capitalize())
        node.parm("parmtype").set(output_type)

        colour = hou.Color(0.89, 0.69, 0.6) if output_type == "surface" else hou.Color(0.6, 0.69, 0.89)
        node.setColor(colour)

        return node
    
    def _setup_place2d(self, subnet_context, material_lib_info):
        '''
        Setup the place2d nodes for non-UDIM textures
        Args:
            subnet_context - where to create the nodes
            material_lib_info - texture details
        Return
            nodes - place2d setup
        '''
        
        if not material_lib_info.get('UDIM', True):
            nodes = {
                'coord': subnet_context.createNode("mtlxtexcoord", f"{self.material_to_create}_textcoord"),
                'scale': subnet_context.createNode("mtlxconstant", f"{self.material_to_create}_scale"),
                'rotate': subnet_context.createNode("mtlxconstant", f"{self.material_to_create}_rotation"),
                'offset': subnet_context.createNode("mtlxconstant", f"{self.material_to_create}_offset"),
                'place2d': subnet_context.createNode("mtlxplace2d", f"{self.material_to_create}_place2d")
            }
            nodes['scale'].parm("value").set(1)

            # Connect nodes
            nodes['place2d'].setInput(0, nodes['coord'])
            nodes['place2d'].setInput(2, nodes['scale'])
            nodes['place2d'].setInput(3, nodes['rotate'])
            nodes['place2d'].setInput(4, nodes['offset'])

            return nodes['place2d']

        return None
    
    def _process_textures(self, subnet_context, mtlx_standard_surf, mtlx_displacement, material_lib_info, place2d):
        '''
        Process and setup all the textures
        Args:
            subnet_context - the USD subnet where we are going to create the textures
            mtlx_standard_surf - the material we are going to connect the textures to
            mtlx_displacement - connecting the disp texture
            material_lib_info - contains the information regarding the textures for the material
            place2d - if no UDIM we used this system to control the texture
        '''
        input_names = mtlx_standard_surf.inputNames()

        for texture_type, texture_info in self._iterate_textures(material_lib_info):
            # Create and setup the texture node
            texture_node = self._create_texture_node(subnet_context, texture_info, material_lib_info)

            if place2d and not material_lib_info.get("UDIM", True):
                texture_node.setInput(2, place2d)
            
            # Connect textures based on type
            self._connect_texture(texture_node, texture_type, mtlx_standard_surf, mtlx_displacement, input_names)

    def _iterate_textures(self, material_lib_info):
        '''Iterator for processing textures based on their types and ignore the skip_keys'''
        skip_keys = ['UDIM', 'Size', 'normal', 'nor', 'nrm', 'nrml', 'norm', 'bump', 'bmp']

        for texture in material_lib_info:
            if texture in skip_keys:
                continue
            
            for texture_type, variants in self.TEXTURE_TYPE_SORTED.items():
                if any(variant in texture.lower() for variant in variants):
                    texture_info = {
                        'name': texture,
                        'file': material_lib_info[texture][0],
                        'type': texture_type 
                    }
                    yield texture_type, texture_info

    def _create_texture_node(self,subnet_context, texture_info, material_lib_info):
        '''Creates and setup a texture node based on its type'''
        # Check the node type based on the UDIM
        node_type = "mtlximage" if material_lib_info.get("UDIM", False) else "mtlxtiledimage"

        # Create the node
        texture_node = subnet_context.createNode(node_type, texture_info['name'])

        # Setup base texture path
        texture_path = self._get_texture_path(texture_info['name'], material_lib_info)
        texture_node.parm('file').set(texture_path)

        # Configure node based on the texture type
        self._configure_texture_node(texture_node, texture_info['type'])

        return texture_node

    def _get_texture_path(self, texture_name, material_lib_info):
        '''
        Get the full path for a texture, handling TX conversion if needed
        Args:
            texture_name - texture's name
            material_lib_info - the dictionary with the textures for the material we want to create
        Return:
            path - self.folder_path + texture_value
          '''
        texture_value = material_lib_info[texture_name][0]
        env_var = hou.text.expandString('$JOB')
        folder_path = material_lib_info['path']
        
        if folder_path.startswith(env_var):
            folder_path = folder_path.replace(env_var, '$JOB')
        
        if self.mtlTX:
            base_name = texture_value.split(".")[0]
            texture_value = f"{base_name}.tx"
        
        texture_path = f"{folder_path}{texture_value}"

        if material_lib_info.get("UDIM", False):
            texture_path = re.sub(r'\d{4}', '<UDIM>', texture_path)
        
        return texture_path

    def _configure_texture_node(self, node, texture_type):
        '''
        Configure a texture node based on its type
        Args:
            node - the image node we want to change
            texture_type - value that defines if we are working with colour or raw data
        '''
        # Default config
        signature = "float"
        colorspace = "raw"
        
        if texture_type in ['texturesColor', 'texturesSSS']:
            signature = "color3"
            if self.mtlTX:
                colorspace = "srg_tx"
            else:
                colorspace = "srg_texture"
        
        node.parm("signature").set(signature)
        node.parm("filecolorspace").set(colorspace)

    def _connect_texture(self, texture_node, texture_type, mtlx_standard_surf, mtlx_displacement, input_names):
        '''Connect a texture node to the material based on its type'''
        connection_map = {
            'texturesColor': {
                'input': 'base_color',
                'setup': self._setup_colour_texture
            },
            'texturesMetal': {
                'input': 'metalness',
                'setup': self._setup_direct_texture
            },
            'texturesSpecular': {
                'input': 'specular',
                'setup': self._setup_direct_texture
            },
            'texturesRough': {
                'input': 'specular_roughness',
                'setup': self._setup_roughness_texture
            },
            'texturesGloss': {
                'input': 'specular_roughness',
                'setup': self._setup_roughness_texture
            },
            'texturesTrans': {
                'input': 'transmission',
                'setup': self._setup_direct_texture
            },
            'texturesEmm': {
                'input': 'emission',
                'setup': self._setup_direct_texture
            },
            'texturesAlpha' : {
                'input': 'opacity',
                'setup': self._setup_direct_texture
            },
            'texturesSSS' : {
                'input': 'subsurface_color',
                'setup': self._setup_sss_texture
            }
        }

        if texture_type in connection_map:
            config = connection_map[texture_type]
            config['setup'](texture_node, mtlx_standard_surf, input_names.index(config['input']))

        if texture_type == 'texturesDisp':
            self._setup_displacement_texture(texture_node, mtlx_displacement)
        
        if texture_type == 'texturesExtra':
            self._setup_mask_texture(texture_node)

    def _setup_colour_texture(self,texture_node,mtlx_standard_surf, input_index):
        '''Setup the colour texture with a range node'''
        range_node = texture_node.parent().createNode("mtlxrange", texture_node.name() + "_CC")
        range_node.setInput(0, texture_node)
        range_node.parm("signature").set("color3")
        mtlx_standard_surf.setInput(input_index, range_node)

    def _setup_displacement_texture(self, texture_node, mtlx_displacement):
        '''Setup the displacement map'''
        mtlx_displacement.setInput(0, texture_node)

    def _setup_roughness_texture(self,texture_node,mtlx_standard_surf, input_index):
        '''Setup the roughness texture with a range node'''
        range_node = texture_node.parent().createNode("mtlxrange", texture_node.name() + "_ADJ")
        range_node.setInput(0, texture_node)
        mtlx_standard_surf.setInput(input_index, range_node)

    def _setup_glossiness_texture(self,texture_node,mtlx_standard_surf, input_index):
        '''Setup the glossiness texture with a range node'''
        range_node = texture_node.parent().createNode("mtlxrange", texture_node.name() + "_ADJ")
        range_node.setInput(0, texture_node)
        range_node.parm("outlow").set(1)
        range_node.parm("outhigh").set(0)
        mtlx_standard_surf.setInput(input_index, range_node)

    def _setup_sss_texture(self,texture_node,mtlx_standard_surf, input_index):
        '''Setup the SSS texture with a range node'''
        range_node = texture_node.parent().createNode("mtlxrange", texture_node.name() + "_CC")
        range_node.setInput(0, texture_node)
        range_node.parm("signature").set("color3")
        mtlx_standard_surf.setInput(input_index, range_node)
        mtlx_standard_surf.parm("subsurface").set(1)

    def _setup_direct_texture(self,texture_node,mtlx_standard_surf, input_index):
        '''Setup direct connection for other textures'''
        mtlx_standard_surf.setInput(input_index, texture_node)

    def _setup_mask_texture(self,texture_node):
        '''Setup for user or mask texture'''
        separate_node = texture_node.parent().createNode("mtlxseparate3c", texture_node.name() + "_SPLIT")
        separate_node.setInput(0, texture_node)

    def _setup_bump_normal(self, subnet_context, mtlx_standard_surf, material_lib_info, place2d):
        '''Setup bump and normal texture nodes and connections'''
        # Create mtlX image based on UDIM on or off
        node_type = "mtlximage" if material_lib_info.get("UDIM", False) else "mtlxtiledimage"
        
        def _create_bump():
            '''Create and setup the bump node and returns the bump node'''
            bump_node = subnet_context.createNode("mtlxbump", "mtlxBump")
            bump_image = subnet_context.createNode(node_type, "bump")
            bump_image.parm("signature").set("float")
            bump_image.parm("filecolorspace").set("raw")
            bump_path = self._get_texture_path(bump_normal_data['bump'], material_lib_info)
            bump_image.parm("file").set(bump_path)

            if place2d and not material_lib_info.get("UDIM", True):
                bump_image.setInput(2, place2d)
            
            bump_node.setInput(0, bump_image)

            return bump_node

        def _create_normal():
            '''Create and setup the bump node and returns the bump node'''
            normal_node = subnet_context.createNode("mtlxnormalmap", "mtlxNormal")
            normal_image = subnet_context.createNode(node_type, "normal")
            normal_image.parm("signature").set("vector3")
            normal_image.parm("filecolorspace").set("raw")
            normal_path = self._get_texture_path(bump_normal_data['normal'], material_lib_info)
            normal_image.parm("file").set(normal_path)

            if place2d and not material_lib_info.get("UDIM", True):
                normal_image.setInput(2, place2d)
            
            normal_node.setInput(0, normal_image)

            return normal_node

        
        input_names = mtlx_standard_surf.inputNames()
        bump_normal_data = self._find_bump_normal_textures(material_lib_info)

        if not any(bump_normal_data.values()):
            return
        
        if bump_normal_data['bump'] and bump_normal_data['normal']:
            # Create the nodes
            bump_node = _create_bump()
            normal_node = _create_normal()

            bump_node.setInput(2, normal_node)
            mtlx_standard_surf.setInput(input_names.index("normal"), bump_node)

        elif bump_normal_data['bump']:
            # Create the nodes
            bump_node = _create_bump()
            mtlx_standard_surf.setInput(input_names.index("normal"), bump_node)

        elif bump_normal_data['normal']:
            # Create the nodes
            normal_node = _create_normal()
            mtlx_standard_surf.setInput(input_names.index("normal"), normal_node)

    def _find_bump_normal_textures(self, material_lib_info):
        '''
        Find the bump and normal textures
        Args:
            material_lib_info - dictionary that contains info regarding the material
        Return:
            dictionary with the values for bump and normal
        '''
        
        texture_type_sorted = {
            'texturesBump' : ['bump', 'bmp', 'height'], 
            'texturesNormal': ['normal', 'nor', 'nrm', 'nrml', 'norm']
        }

        result = {'bump': None, 'normal': None}

        for texture in material_lib_info:
            for texture_name, texture_value in texture_type_sorted.items():
                if texture in texture_value:
                    key = 'bump' if texture_name == 'texturesBump' else 'normal'
                    result[key] = texture
        
        return result 

    def _layout_nodes(self, subnet_context):
        '''Layout nodes in the network'''
        subnet_context.layoutChildren()
        self.node_lib.layoutChildren()