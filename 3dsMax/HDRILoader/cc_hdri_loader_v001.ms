/*
// A helper to improve the experience using OSL HDRI ENV 

// HDRI Loader 1.1 by Ciro Cardoso
// Bugs, suggestions and feedback --> cirocardoso@yahoo.co.uk

// Modified: 2024-08-29
// Version: 1.1 - fix issue with docking system

// A big thanks to Giuseppe Schiralli for helping me out with debugging and suggestions

##### CHANGELOG #####

*/


--#########################################################################################
--			D E F I N E  A R R A Y  A O V S
--#########################################################################################
hdri_list = #()
hdri_list_short = #()
hdri_list_exr = #()
hdri_list_hdr = #()
		
hdri_folder
hdri_light
hdri_map
gui = #("_appearanceGB", "_alignmentGB")

--#########################################################################################
--			I N T E R F A C E 
--#########################################################################################
--cui.unRegisterDialogBar _hdriLoader

try(DestroyDialog _hdriLoader) catch ()

rollout _hdriLoader "HDRI Loader 1.0"
(
	--####################################################################################
	--			L O A D  H D R I  
	--####################################################################################
	GroupBox _libraryGB "Load HDRI" pos:[5, 10] height:50 width:440
	button _library "Load HDRI Library" pos: [10, 30] height:20
	edittext _libraryloc "" pos: [120, 30] fieldWidth:310 text:"open hdri folder..." readOnly: true
	--####################################################################################
	--			L O A D  L I G H T  
	--####################################################################################
	GroupBox _lightGB "Load into scene as" pos:[5, 65] height:45 width:440
	radiobuttons _light labels: #("Arnold Dome Light", "Environment Map slot (8)") pos:[75, 85] default:1 offsets: #([0,0], [60, 0])
	button _createLight "Create light" pos:[5,115] height:20 width:440
	--####################################################################################
	--			H D R I  L I S T 
	--####################################################################################
	GroupBox _hdriGB "HDRI" pos:[5, 140] height:180 width:440
	listbox _hdriItems "List" items: #() width: 145 pos: [10, 155]
	bitmap _image bitmap: (bitmap 270 135 color: gray)  pos: [160, 170] height: 135 width: 270
	--####################################################################################
	--			O S L  S E T T I N G S  
	--####################################################################################
	GroupBox _exposureGB "OSL HDRI settings" pos:[5, 325] height:150 width:440 
	GroupBox _appearanceGB "Appearance" pos:[10, 345] height:120 width:140
	spinner _exposure "Exposure: " range:[-100,100,0] type:#float fieldWidth:50 pos: [15,370]
	spinner _contrast "Contrast:  " range: [0.01,100,1] type:#float fieldWidth:50 pos: [15,395]
	checkbox _clamp "Clamp" pos:[15, 420] checked:false
	spinner _clampstops "Clamp Stops: " range:[-10, 30, 0] type:#float fieldWidth:50 pos: [15,445] enbabled: off 
	
	GroupBox _alignmentGB "Alignment" pos:[155, 345] height:120 width:285
	spinner _rotation "Rotation: " range:[-360,360,0] type:#float fieldWidth:50 pos:[170,370]
	spinner _height "Height:    " range:[-1,1,0] type:#float fieldWidth:50 pos:[170, 390]
	spinner _tiltx "Tilt X:  " range:[-360,360,0] type:#float fieldWidth:50 pos:[310, 370]
	spinner _tilty "Tilt Y:  " range:[-360,360,0] type:#float fieldWidth:50 pos:[310, 395]
	checkbox _mirror "Mirror environment horizontally" pos:[170, 420]
	button _resetall "Reset OSL settings" pos: [170, 440] height:20 width:260
	--####################################################################################
	--			A R  N O L D  L I G H T 
	--####################################################################################
	GroupBox _ailight "Arnold Skydome Light" pos:[5,480]  height:200 width:440
	GroupBox _shape "Shape" pos:[10,500] height:150 width:155
	spinner _resolution "Resolution: " range:[0,32768,1024] type:#integer fieldWidth:60 pos:[15, 520]
	dropdownlist _portal "Portal Mode:" items:#("Off", "Interior Only", "Interior/Exterior") selection:2 width:120 alignment:#center pos:[15, 545]
	checkbox _lightvisible "Light Shape Visible" pos:[15,595] checked: true
	checkbox _visibleView "Always Visible in Viewport" pos:[15, 615] checked:true
	
	GroupBox _colorInt "Intensity" pos:[170, 500] height:150 width:150
	spinner _intlt "Intensity:  " range:[0,999999995904,1] type:#float fieldWidth:60 pos:[185, 520]
	spinner _explt "Exposure: " range:[-5,16,0] type:#float fieldWidth:60 pos:[185, 540]
	checkbox _normlt "Normalize Energy" pos:[182, 565]
	GroupBox _renderGB "Rendering" pos:[325, 500] height: 150 width:115
	spinner _sampleslt "Samples:   " range:[0,100,1] type:#integer fieldWidth:30 pos:[330, 520]
	spinner _volumes "Volume S:  "  range:[0, 100, 2] type:#integer fieldWidth:30 pos:[330, 540]
	
	button _resetLight "Reset Arnold Skydome Settings" pos:[10, 655] height:20 width:430
	--####################################################################################
	--			H D R I  L O A D E R 
	--####################################################################################
	on _hdriLoader open do 
	(
		check_env = environmentMap as string 
				
		if $aiHDRI != undefined or check_env == "osl_HDRIenv:OSL: HDRI Environment" then
		(
			_lightGB.enabled = true
			_light.enabled = true
			
			--in case the script is closed and opened again it loads the previous list of HDRIs
			if hdri_global_list != undefined then 
			(
				if hdri_global_list.count != 0 then 
				(
					join hdri_list_short hdri_global_list
					join hdri_list hdri_global_path 
					_hdriItems.items = hdri_list_short
					
					prev_hdri = hdri_map.HDRI
					sel_hdri = findItem hdri_list prev_hdri
					_hdriItems.selection = sel_hdri
				)
			)
			--makes sure if there is previous Skydome Light and pick up the settings
			if $aiHDRI != undefined then 
			(
				hdri_light = $aiHDRI
				hdri_map = $aiHDRI.texmap
				_light.state = 1
				environmentMap = undefined
				
				_resolution.value = hdri_light.resolution
				_portal.selection = hdri_light.portal_mode + 1
				_lightvisible.checked = hdri_light.lightShapeVisible
				_visibleView.checked = hdri_light.alwaysVisibleInViewport
				_intlt.value = hdri_light.intensity
				_explt.value = hdri_light.exposure
				_normlt.checked = hdri_light.normalize
				_sampleslt.value = hdri_light.Samples
				_volumes.value = hdri_light.volume_samples
							
				_exposure.value = hdri_map.exposure 
				_contrast.value = hdri_map.contrast
				_clamp.checked = hdri_map.clamp
				_clampstops.value = hdri_map.ClampStops
				_rotation.value = hdri_map.Rotation
				_height.value = hdri_map.Height
				_tiltx.value = hdri_map.TiltX
				_tilty.value = hdri_map.TiltY
				_mirror.checked = hdri_map.flip
			)
			
			--same principle with the Env Slot
			if check_env == "osl_HDRIenv:OSL: HDRI Environment" then 
			(
				_light.state = 2
				
				hdri_map = environmentMap
				
				_exposure.value = hdri_map.exposure 
				_contrast.value = hdri_map.contrast
				_clamp.checked = hdri_map.clamp
				_clampstops.value = hdri_map.ClampStops
				_rotation.value = hdri_map.Rotation
				_height.value = hdri_map.Height
				_tiltx.value = hdri_map.TiltX
				_tilty.value = hdri_map.TiltY
				_mirror.checked = hdri_map.flip
				
				_ailight.enabled = false
				_shape.enabled = false
				_resolution.enabled = false
				_portal.enabled = false
				_lightvisible.enabled = false
				_visibleView.enabled = false
				_colorInt.enabled = false
				_intlt.enabled = false
				_explt.enabled = false
				_normlt.enabled = false
				_sampleslt.enabled = false
				_volumes.enabled = false
				_resetLight.enabled = false
				_createLight.enabled = true
			)
			
			--creates the preview for each HDRI
			hdri_preview = hdri_map.HDRI
			new = openBitMap hdri_preview
			target = bitmap 300 300
			copy new target
			_image.bitmap = target
		)
		else
		(
			_lightGB.enabled = false
			_light.enabled = false
			_exposureGB.enabled = false
			_appearanceGB.enabled = false
			_exposure.enabled = false
			_contrast.enabled = false
			_clamp.enabled = false
			_clampstops.enabled = false
			_alignmentGB.enabled = false
			_rotation.enabled = false
			_height.enabled = false
			_tiltx.enabled = false
			_tilty.enabled = false
			_mirror.enabled = false
			_resetall.enabled = false
			_ailight.enabled = false
			_shape.enabled = false
			_resolution.enabled = false
			_portal.enabled = false
			_lightvisible.enabled = false
			_visibleView.enabled = false
			_colorInt.enabled = false
			_intlt.enabled = false
			_explt.enabled = false
			_normlt.enabled = false
			_sampleslt.enabled = false
			_volumes.enabled = false
			_renderGB.enabled = false
			_resetLight.enabled = false
			_createLight.enabled = false
		)
				
		check_light = $aiHDRI 
		
		if check_light != undefined then 
		( 
			hdri_light = $aiHDRI 
			hdri_map = hdri_light.texmap
		)
	)
	
	--####################################################################################
	--			L O A D  H D R I
	--####################################################################################
	on _library pressed do 
	(
		--resets the arrays for a new library
		hdri_list = #()
		hdri_list_short = #()
		hdri_list_exr = #()
		hdri_list_hdr = #()
			
		hdri_folder = getSavePath "Select Folder"
		
		if hdri_folder != undefined then 
		(	
			-- makes sure you can work with both exr and hdr files\
			hdri_list_exr = getFiles (hdri_folder + "/*.exr")
			hdri_list_hdr = getFiles (hdri_folder  + "/*.hdr")
			
			join hdri_list hdri_list_exr
			join hdri_list hdri_list_hdr
			
			if hdri_list.count >= 1 then 
			(	
				for i = 1 to hdri_list.count do 
				(
					new_hdri = getFilenameFile hdri_list[i]
					append hdri_list_short new_hdri
				)
				
				--creates the first preview
				hdri_preview = hdri_list[1]
				new = openBitMap hdri_preview
				target = bitmap 300 300
				copy new target
				_image.bitmap = target
				
				_hdriItems.items = hdri_list_short
				_hdriItems.selection = 1
				
				--creates the initial light
				global hdri_map = osl_HDRIenv()
				initial_hdri = hdri_list[_hdriItems.selection]
				hdri_map.HDRI = initial_hdri 
				hdri_map.clamp = 0
				
				if $aiHDRI != undefined then
				(
					$aiHDRI.texmap = hdri_map 
				)
								
				_lightGB.enabled = true
				_light.enabled = true
			)
			else ( messageBox "There is no HDRI in the folder" )
			
			_lightGB.enabled = true
			_light.enabled = true
			_exposureGB.enabled = true
			_appearanceGB.enabled = true
			_exposure.enabled = true
			_contrast.enabled = true
			_clamp.enabled = true
			_clampstops.enabled = true
			_alignmentGB.enabled = true
			_rotation.enabled = true
			_height.enabled = true
			_tiltx.enabled = true
			_tilty.enabled = true
			_mirror.enabled = true
			_resetall.enabled = true
			_ailight.enabled = true
			_shape.enabled = true
			_resolution.enabled = true
			_portal.enabled = true
			_lightvisible.enabled = true
			_visibleView.enabled = true
			_colorInt.enabled = true
			_intlt.enabled = true
			_explt.enabled = true
			_normlt.enabled = true
			_sampleslt.enabled = true
			_volumes.enabled = true
			_renderGB.enabled = true
			_resetLight.enabled = true
			_createLight.enabled = true 
			
			-- need this to make sure the script can be loaded a second time and keep the previous info
			global hdri_global_list = #()
			global hdri_global_path = #()
			
			join hdri_global_list hdri_list_short
			join hdri_global_path hdri_list
			
			if $aiHDRI != undefined then 
			(
				hdri_light.on = true
				useEnvironmentMap = off
				environmentMap = undefined
			)
			
			if useEnvironmentMap == true and environmentMap != undefined then 
			(
				useEnvironmentMap = true
				environmentMap = hdri_map
				
				_ailight.enabled = false
				_shape.enabled = false
				_resolution.enabled = false
				_portal.enabled = false
				_lightvisible.enabled = false
				_visibleView.enabled = false
				_colorInt.enabled = false
				_intlt.enabled = false
				_explt.enabled = false
				_normlt.enabled = false
				_sampleslt.enabled = false
				_volumes.enabled = false
				_renderGB.enabled = false
				_resetLight.enabled = false
			)
		)
		else ( print "Nothing was selected" )
	)
	
	--####################################################################################
	--			H D R I  L I S T B O X 
	--####################################################################################
	
	on _hdriItems selected itm do 
	(
		hdri_preview = hdri_list[itm]
		new = openBitMap hdri_preview
		target = bitmap 300 300
		copy new target
		_image.bitmap = target
		
		hdri_map.HDRI = hdri_list[itm]
		print hdri_list[itm]
		print itm 
	)
	
	--####################################################################################
	--			B U T T O N  C R E A T E  L I G H T 
	--####################################################################################
	on _createLight pressed do 
	(
		if _light.state == 1 then 
		(
			-- checks if any skydome light is present in the scene
			check_light = #()
			
			for i = 1 to lights.count do
			(
				if lights[i].superclassID != 16 then 
				(
					light_scene = lights[i]
					append check_light  light_scene
				)
			)
			
			for i = 1 to check_light.count do
			(
				if check_light[i].shapeType == 6 then
				(
					messageBox "One or more Arnold Skydome lights were found in the scene. To avoid conflits all remaining Arnold Skydome lights were disabled."
					check_light[i].on = false
				)
				
			)
			
			--uses the OSL Env if available, otherwise creates a new scene
			if $aiHDRI != undefined then
			(
				hdri_light.on = true
				useEnvironmentMap = off
				environmentMap = undefined
			)
			else
			(
				hdri_light = Arnold_Light name: "aiHDRI"  on: on shapeType:6  useColor: off useTexmap: on  intensity:1 exposure:0 normalize:off shapeType:6 targeted:off lightShapeVisible: on resolution: 1024
				hdri_light.texmap = hdri_map 
				useEnvironmentMap = off 
				environmentMap = undefined
			)
			
			_ailight.enabled = true 
			_shape.enabled = true
			_resolution.enabled = true
			_portal.enabled = true
			_lightvisible.enabled = true
			_visibleView.enabled = true
			_colorInt.enabled = true
			_intlt.enabled = true
			_explt.enabled = true
			_normlt.enabled = true
			_sampleslt.enabled = true
			_volumes.enabled = true
			_renderGB.enabled = true
			_resetLight.enabled = true
			
			_resolution.value = 1024
			hdri_light.resolution = 1024
			_portal.selection = 2
			hdri_light.portal_mode = 1
			_lightvisible.checked = on
			hdri_light.lightShapeVisible = on
			_visibleView.checked = on 
			hdri_light.alwaysVisibleInViewport = on
			_intlt.value = 1 
			hdri_light.intensity = 1
			_explt.value = 0
			hdri_light.exposure = 0
			_normlt.checked = false 
			hdri_light.normalize = off
			_sampleslt.value = 1
			hdri_light.Samples = 1
			_volumes.value = 2 
			hdri_light.volume_samples = 2
		)
		
		if _light.state == 2 then
		(
			if $aiHDRI != undefined then ( delete $aiHDRI )
		
			useEnvironmentMap = true
			environmentMap = hdri_map
						
			_ailight.enabled = false
			_shape.enabled = false
			_resolution.enabled = false
			_portal.enabled = false
			_lightvisible.enabled = false
			_visibleView.enabled = false
			_colorInt.enabled = false
			_intlt.enabled = false
			_explt.enabled = false
			_normlt.enabled = false
			_sampleslt.enabled = false
			_volumes.enabled = false
			_renderGB.enabled = false
			_resetLight.enabled = false
		)
	)
	
	--####################################################################################
	--			O S L  E N V  H D R I 
	--####################################################################################
	
	on _exposure changed theVal do  	( hdri_map.exposure = theVal )
	on _contrast changed theVal do 		( hdri_map.contrast = theVal )
	on _clamp changed theState do 		( hdri_map.clamp = NOT theState)
	on _clampstops changed theVal do 	( hdri_map.ClampStops = theVal)
	on _rotation changed theVal do 		( hdri_map.Rotation = theVal)
	on _height changed theVal do 		( hdri_map.Height = theVal)
	on _tiltx changed theVal do 		( hdri_map.TiltX = theVal)
	on _tilty changed theVal do 		( hdri_map.TiltY = theVal)
	on _mirror changed theState do 		( hdri_map.flip = theState)
	
	--####################################################################################
	--			B U T T O N  R E S E T 
	--####################################################################################
	on _resetall pressed do
	(
		if ($aiHDRI != undefined) or (environmentMap != undefined) then 
		(
			hdri_map.exposure = 0
			hdri_map.contrast = 1
			hdri_map.clamp = false
			hdri_map.ClampStops = 0
			hdri_map.Rotation = 0
			hdri_map.Height = 0
			hdri_map.TiltX = 0
			hdri_map.TiltY = 0
			hdri_map.flip = 0
			
			_exposure.value = 0
			_contrast.value = 1
			_clamp.checked = false
			_clampstops.value = 0
			_rotation.value = 0
			_height.value = 0
			_tiltx.value = 0
			_tilty.value = 0
			_mirror.checked = false
		)
		else ( messageBox "No HDRI present in the scene" )
	)

	--####################################################################################
	--			L I G H T  S E T T I N G S 
	--####################################################################################
 	on _resolution changed theVal do  		( hdri_light.resolution = theVal) 
	on _portal selected Sel do 				( hdri_light.portal_mode = Sel - 1)
	on _lightvisible changed theState do 	( hdri_light.lightShapeVisible = theState)
	on _visibleView changed theState do 	( hdri_light.alwaysVisibleInViewport = theState)
	on _intlt changed theVal do 			( hdri_light.intensity = theVal)
	on _explt changed theVal do 			( hdri_light.exposure = theVal)
	on _normlt changed theState do 			( hdri_light.normalize = theState)
	on _sampleslt changed theVal do 		( hdri_light.Samples = theVal)
	on _volumes changed theVal do 			( hdri_light.volume_samples = theVal)
	
	--####################################################################################
	--			B U T T O N  R E S E T  L I G H T 
	--####################################################################################
	on _resetLight pressed do
	(
		if ($aiHDRI != undefined) then 
		(
			_resolution.value = 1024
			hdri_light.resolution = 1024
			_portal.selection = 2
			hdri_light.portal_mode = 1
			_lightvisible.checked = on
			hdri_light.lightShapeVisible = on
			_visibleView.checked = on 
			hdri_light.alwaysVisibleInViewport = on
			_intlt.value = 1 
			hdri_light.intensity = 1
			_explt.value = 0
			hdri_light.exposure = 0
			_normlt.checked = false 
			hdri_light.normalize = off
			_sampleslt.value = 1
			hdri_light.Samples = 1
			_volumes.value = 2 
			hdri_light.volume_samples = 2
		)
		else ( messageBox "No Arnold Skydome in the scene" )
	)
)

CreateDialog _hdriLoader 450 700

cui.registerDialogBar _hdriLoader style:#(#cui_floatable,#cui_dock_left,#cui_dock_right,#cui_handles)
-- cui.dockDialogBar _hdriLoader #cui_dock_left