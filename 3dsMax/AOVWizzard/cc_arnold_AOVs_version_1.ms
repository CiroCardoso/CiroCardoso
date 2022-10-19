/*
// A helper to improve the AOV manager, by automate the process of creating 
// aovs such as, Cryptomatte, UV, AO and Normal Object Space AOV

// A big thanks to Giuseppe Schiralli for helping me out with the Light Groups
// and refine some other bits. 

// AOVS Wizzard 1.0 by Ciro Cardoso
// Bugs, suggestions and feedback --> cirocardoso@yahoo.co.uk

// Modified: 2022-02-24
// Version: 1.0

##### CHANGELOG #####

*/

--#########################################################################################
--			V A R I A B L E S  D E F A U L T 
--#########################################################################################

amw = MaxtoAOps.AOVsManagerWindow() --opens the AOV manager, otherwise you can't add the AOVS
renderSceneDialog.close()
rend = renderers.current

if (classof rend == Arnold) then ( global aov_man = rend.AOVManager )
else ( messageBox "Arnold is not the current renderer" title:"Incorrect renderer" beep:false )
global aov_name = "_AOVS_"

--#########################################################################################
--			D E F I N E  A R R A Y  A O V S
--#########################################################################################

beauty_AOVS = #("diffuse", "specular", "coat", "transmission", "sheen", "sss", "volume", "emission", "background")
data_AOVS = #()
crypto_AOVS = #()
gpu_AOVS = #()
noice_AOVS = #()
aovs_lightgpr = #()

--#########################################################################################
--			I N T E R F A C E 
--#########################################################################################

try (DestroyDialog _AOVShelper) catch()
rollout _AOVShelper "AOVs Wizard 1.0"
(
	--####################################################################################
	--			C O M P O N E N T S 
	--####################################################################################
	GroupBox _baseAOVS "BASE AOVS" pos:[5, 10] height:130 width:575
	GroupBox _1Components "1. Components (Beauty)" pos:[10, 30] height:100 width:215
	checkbox _rgback "RGBA (all)" pos:[15, 50] checked:false
	checkbox _diffuseck "diffuse" pos:[15, 70] checked: true
	checkbox _specularck "specular" pos:[15, 90] checked:true
	checkbox _transmissionck "transmission" pos:[15, 110] checked:true
	checkbox _sheenck "sheen" pos:[150, 50] checked:true
	checkbox _sssck "sss" pos:[150, 70] checked:true
	checkbox _volumeck "volume" pos:[150, 90] checked:true
	checkbox _coatck "coat" pos:[150, 110] checked:true
	--####################################################################################
	--			D I R E C T / I N D I R E C T 
	--####################################################################################
	GroupBox _2Direct "2. Direct\Indirect" pos:[230, 30] height:100 width:100
	checkbox _combinedDI "Combined" pos:[235, 50] checked: true 
	GroupBox _separateGB "Separate" pos:[235, 70] height:55 width:90 enabled: false
	checkbox _directck "Direct" pos:[240, 87] checked: true enabled: false
	checkbox _indirectck "Indirect" pos:[240, 107] checked: true enabled: false
	--####################################################################################
	--			A D I T I O N A L 
	--####################################################################################
	GroupBox _3Additional "3. Additional" pos:[340, 30] height:100 width:110
	checkbox _albedock "albedo" pos:[345, 50] checked: false
	checkbox _opacityck "opacity (volume)" pos:[345, 70] checked: false
	checkbox _emission "emission" pos:[345, 90] checked: true
	checkbox _background "background" pos:[345, 110] checked: true
	--####################################################################################
	--			L I G H T G R O U P S
	--####################################################################################
	GroupBox _4Light "4. Light Groups" pos:[460, 30] height:100 width:110
	checkbox _lightgroups "use light groups " pos:[465, 50] checked: false
	--####################################################################################
	--			D A T A 
	--####################################################################################
	GroupBox _dataAOVS "DATA AOVS" pos:[5, 150] height:100 width:260
	checkbox _dataALL "SELECT ALL"  pos:[15, 170] checked:false
	checkbox _ack "A (alpha)" pos:[15, 190] checked:false
	checkbox _nck "N (normal)" pos:[15, 210] checked:false
	checkbox _pck "P (position)" pos:[100, 170] checked:false
	checkbox _motionck "motionvector" pos:[100, 190] checked:false
	checkbox _zck "Z (zdepth)" pos:[100, 210] checked:false
	checkbox _uvck "UV"  pos:[190, 170] checked: false
	checkbox _aock "AO" pos:[190, 190] checked:false
	checkbox _n2ck "N (object)" pos:[190, 210] checked:false
	--####################################################################################
	--			C R Y P T O
	--####################################################################################
	GroupBox _cryptoAOVs "CRYPTOMATTE" pos:[270, 150] height:100 width:100
	checkbox _cryptoALL "ALL" pos:[285, 165] checked: false 
	GroupBox _cryptoSP "Separate" pos:[285, 180] height:65 width:80 enabled: true checked:false
	checkbox _cr_assetck "asset" pos:[290, 195] checked: false
	checkbox _cr_objectck "object" pos:[290, 210] checked: false
	checkbox _cr_mtlck "material" pos:[290, 225] checked: false
	--####################################################################################
	--			E X T R A
	--####################################################################################
	GroupBox _extra "EXTRA" pos:[380, 150] height:100 width:200
	edittext _renametxt "Prefix:" pos:[390, 170] fieldWidth:145 text:"default is 3ds Max file name"
	radiobuttons _exrSingle labels: #("Multi-channel", "Single Channel") pos:[390, 195] default:1 columns: 1 offsets: #([0,0], [0, 10])
	--####################################################################################
	--			D E N O I S E R  G P U 
	--####################################################################################
	GroupBox _denoiserOIDN "AOVS for OIDN\\OPTIX" pos:[5, 260] height:100 width:190
	checkbox _gpuaovs "Create AOVs for OIDN\\OPTIX" pos:[10, 280] checked: false
	checkbox _diffuseAOV "diffuse_albedo" pos:[25, 300] checked: false
	checkbox _nAOV "N (normal)" pos:[25, 320] checked: false
	label _gpuExp "for external denoising" pos:[10, 340] enabled: false 
	--####################################################################################
	--			D E N O I S E R  C P U
	--####################################################################################
	GroupBox _denoiserNOISE "AOVS for Noice" pos:[200, 260] height:100 width:150
	checkbox _noiceaovs "Create AOVs for Noice" pos:[205, 280] checked: false
	checkbox _directAOV "Direct AOVS" pos:[220, 300] checked: false
	checkbox _indirectAOV "Indirect AOVS" pos:[220, 320] checked: false
	label _cpuExp "for external denoising" pos:[210, 340] enabled: false 
	--####################################################################################
	--			B U T T O N S
	--####################################################################################
	button _createAOVs "Create AOVS" pos:[360, 260] height:100 width:165
	button _deleteAOVs "Delete AOVS" pos:[530, 260] height:100 width:50
	
	--#########################################################################################
	--			F U N C T I O N S
	--#########################################################################################
	
	--#########################################################################################
	--						B A S E  A O V S
	--#########################################################################################
	
	fn baseAOVS =
	(
		if (maxFileName == "") then (aov_name = "") 
		
		if (_renametxt.text == "default is 3ds Max file name") then
		(
			aov_name = substring maxFileName  1 (maxFileName.count - 4) -- check filename 
		)
		else(aov_name = _renametxt.text)
						
		if 	aovs_lightgpr.count == 1 then --aovs_lightgpr -- checkbox for Light Groups
		(
			if rend.AOV_Manager.Drivers.count != 0 then 
			(
				aov_add = (renderers.current.AOV_Manager.Drivers.count + 1) as string
				aov_naming = "_AOVS_" + aov_add
			)
			else(aov_naming = "_AOVS_")
			
			if (_exrSingle.state == 1) then
			(
				-- define AOV EXR settings 
				aov_driver = ArnoldEXRDriver()
				aov_driver.filenameSuffix = aov_name + aov_naming 	
				aov_driver.tiled = false
				aov_driver.halfprecision = true
				aov_driver.compression = "zips"
				
				append aov_man.drivers aov_driver -- adds the AOV EXR to the AOV Manager
				sort beauty_AOVS
					
				for i = 1 to beauty_AOVS.count do 
					(
						aov = ArnoldAOV()
						aov.name = beauty_AOVS[i]
						aov.data = "rgba"
						aov.filter = "gaussian_filter"
						append aov_driver.aovList aov
					)
			)
			else
			(
				for i = 1 to beauty_AOVS.count do
				(
					aov_driver = ArnoldEXRDriver()
					aov_driver.filenameSuffix = aov_name + "_" + beauty_AOVS[i]
					aov_driver.tiled = false
					aov_driver.halfprecision = true
					aov_driver.compression = "zips"
					append aov_man.drivers aov_driver 
					aov = ArnoldAOV()
					aov.name = beauty_AOVS[i]
					aov.data = "rgba"
					aov.filter = "gaussian_filter"
					append aov_driver.aovList aov
				)
			)
		)
		else 
		(
			for i = 1 to aovs_lightgpr.count do
			(
				-- define AOV EXR settings 
				sort aovs_lightgpr
				aov_driver = ArnoldEXRDriver()
				aov_naming = "_AOVS_" + (aovs_lightgpr[i] as string)
				aov_driver.filenameSuffix = aov_name + aov_naming 	
				aov_driver.tiled = false
				aov_driver.halfprecision = true
				aov_driver.compression = "zips"
		 		aov_driver.lightGroup = aovs_lightgpr[i]
				
				append aov_man.drivers aov_driver -- adds the AOV EXR to the AOV Manager
				sort beauty_AOVS
					
				for i = 1 to beauty_AOVS.count do 
					(
						aov = ArnoldAOV()
						aov.name = beauty_AOVS[i]
						aov.data = "rgba"
						aov.filter = "gaussian_filter"
						append aov_driver.aovList aov
					)			
			)
		)
	)
	--#########################################################################################
	--						D A T A  A O V S
	--#########################################################################################
	fn dataAOVS =
	(
		if (maxFileName == "") then (aov_name = "") else (aov_name = substring maxFileName  1 (maxFileName.count - 4)) -- check filename 
			
		if (_renametxt.text == "default is 3ds Max file name") then ( aov_name = substring maxFileName  1 (maxFileName.count - 4) )
		else ( aov_name = _renametxt.text)
	
		if renderers.current.AOV_Manager.Drivers.count != 0 then 
		(
			aov_add = (renderers.current.AOV_Manager.Drivers.count + 1) as string
			aov_naming = "_data_AOVS_" + aov_add
		)
		else ( aov_naming = "_data_AOVS_" )
		-- define AOV EXR settings 
		aov_driver = ArnoldEXRDriver()
		aov_naming --for the aov naming
		aov_driver.filenameSuffix = aov_name + aov_naming 	
		aov_driver.tiled = false
		aov_driver.halfprecision = true
		aov_driver.compression = "zips"
		append aov_man.drivers aov_driver -- adds the AOV EXR to the AOV Manager
		sort data_AOVS
			
		for i = 1 to data_AOVS.count do 
		(
			aov = ArnoldAOV()
			aov.name = data_AOVS[i]
							
			if (aov.name == "A") or (aov.name == "Z") then 
			(
				aov.filter = "closest_filter"
				aov.data = "float"
				append aov_driver.aovList aov
			)
			else
			(
				if (aov.name == "AO") or (aov.name == "crypto_asset") or (aov.name == "crypto_object") or (aov.name == "crypto_material")then 
				(
					aov.filter = "gaussian_filter"
					aov.data = "rgb"
					append aov_driver.aovList aov
				)
				else
				(
					if (aov.name == "motionvector") then
					(
						aov.filter = "closest_filter"
						aov.data = "vector2"
						append aov_driver.aovList aov
					)
					else
					(
						aov.filter = "closest_filter"
						aov.data = "vector"
						append aov_driver.aovList aov
					)
				)
			)
		)
	)

	--#########################################################################################
	--						G P U  A O V S
	--#########################################################################################
	
	fn gpuAOVS =
	(
		if (maxFileName == "") then (aov_name = "") 
		 
		if (_renametxt.text == "default is 3ds Max file name") then ( aov_name = substring maxFileName  1 (maxFileName.count - 4) )
		else ( aov_name = _renametxt.text )
						
		if renderers.current.AOV_Manager.Drivers.count != 0 then 
		(
			aov_add = (renderers.current.AOV_Manager.Drivers.count + 1) as string
			aov_naming = "_AOVS_" + aov_add
		)
		else ( aov_naming = "_AOVS_" )
		
		for i = 1 to gpu_AOVS.count do
		(
			aov_driver = ArnoldEXRDriver()
			aov_driver.filenameSuffix = aov_name + "_gpu" + "_" + gpu_AOVS[i]
			aov_driver.tiled = false
			aov_driver.halfprecision = true
			aov_driver.compression = "zips"
			append aov_man.drivers aov_driver 
			aov = ArnoldAOV()
			aov.name = gpu_AOVS[i]
			aov.data = "rgba"
			aov.filter = "gaussian_filter"
			append aov_driver.aovList aov
		)
	)
	
	--#########################################################################################
	--			C P U  A O V S
	--#########################################################################################	
	
	fn addNOICEAOVS =
	(
		if (maxFileName == "") then (aov_name = "") else (aov_name = substring maxFileName  1 (maxFileName.count - 4)) -- check filename 
			
		if (_renametxt.text == "default is 3ds Max file name") then ( aov_name = substring maxFileName  1 (maxFileName.count - 4) )
		else ( aov_name = _renametxt.text )
	
		if renderers.current.AOV_Manager.Drivers.count != 0 then 
		(
			aov_add = (renderers.current.AOV_Manager.Drivers.count + 1) as string
			aov_naming = "_noice_AOVS_" + aov_add
		)
		else ( aov_naming = "_noice_AOVS_" )
		-- define AOV EXR settings 
		aov_driver = ArnoldEXRDriver()
		aov_naming --for the aov naming
		aov_driver.filenameSuffix = aov_name + aov_naming 	
		aov_driver.tiled = false
		aov_driver.halfprecision = true
		aov_driver.compression = "zips"
		append aov_man.drivers aov_driver -- adds the AOV EXR to the AOV Manager
		sort noice_AOVS
			
		for i = 1 to noice_AOVS.count do 
			(
				aov = ArnoldAOV()
				aov.name = noice_AOVS[i]
								
				if (aov.name == "N")then 
				(
					aov.filter = "gaussian_filter"
					aov.data = "vector"
					append aov_driver.aovList aov
				)
				else
				(
					if (aov.name == "Z") then 
					(
						aov.filter = "gaussian_filter"
						aov.data = "float"
						append aov_driver.aovList aov
					)
					else
					(
						if (aov.name == "denoise_albedo") then
						(
							aov.filter = "gaussian_filter"
							aov.data = "rgba"
							append aov_driver.aovList aov
						)
						else
						(
							aov.filter = "variance_filter"
							aov.data = "rgb"
							append aov_driver.aovList aov
						)
					)
				)
			)
	)
	
	--#########################################################################################
	--		A D D   A O V S  D I R E C T  A N D  I N D I R E C T
	--#########################################################################################
	
	fn addAOVS_List _aovName =
	(
		aovN = findItem beauty_AOVS _aovName
		
		if aovN == 0 then ( appendIfUnique beauty_AOVS _aovName)
		else (deleteItem beauty_AOVS aovN)
		
		aovN_D = _aovName + "_direct"
		aovN = findItem beauty_AOVS aovN_D

		if aovN != 0 then (deleteItem beauty_AOVS aovN)
		
		aovN_I = _aovName + "_indirect"
		aovN = findItem beauty_AOVS aovN_I

		if aovN != 0 then (deleteItem beauty_AOVS aovN)
	)
	
	--#########################################################################################
	--			A D D  D A T A  A O V S 
	--#########################################################################################
	
	fn addAOVSDATA _aovData =
	(
		aovN = findItem data_AOVS _aovData
		
		if aovN == 0 then ( appendIfUnique data_AOVS _aovData)
		else (deleteItem data_AOVS aovN)
	)
	
	--#########################################################################################
	--			D I R E C T  O N  O R  O F F 
	--#########################################################################################
	fn addAOVS_DI _state _aovOPT =
	(
		if _state == true then
		(
			for i = 1 to beauty_AOVS.count do
			(
				aov_check = beauty_AOVS[i]
				aovOPT = _aovOPT
				-- aovOPT == 1 is all
				-- aovOPT == 2 is direct
				-- aovOPT == 3 is indirect
				if (matchPattern aov_check pattern:"*_*") then ( )
				else
				(
					if (matchPattern aov_check pattern:"*background*") or (matchPattern aov_check pattern:"*emission*") then ( )
					else
					(
						if (aovOPT == 1 ) then
						(
							aov_di = aov_check + "_direct"
							aovN = findItem beauty_AOVS aov_di
							if aovN == 0 then (append beauty_AOVS aov_di)
						
							aov_in = aov_check + "_indirect"
							aovN = findItem beauty_AOVS aov_in
							if aovN == 0 then ( append beauty_AOVS aov_in )
						)
						
						if (aovOPT == 2 ) then
						(
							aov_di = aov_check + "_direct"
							aovN = findItem beauty_AOVS aov_di
							if aovN == 0 then (append beauty_AOVS aov_di)
						)
						
						if (aovOPT == 3 ) then
						(
							aov_di = aov_check + "_indirect"
							aovN = findItem beauty_AOVS aov_di
							if aovN == 0 then (append beauty_AOVS aov_di)
						)
						
					)
				)
			)
		)
		
		if _state == false then
		(
			for i = beauty_AOVS.count to 1 by -1 do
			(
				aovOPT = _aovOPT
				if (aovOPT == 1) then
				(
					findDI = findString beauty_AOVS[i] "direct"
					
					if (findDI != undefined) then
					(
						aovN = findItem beauty_AOVS beauty_AOVS[i]
						deleteItem beauty_AOVS aovN
					)
				)
				
				if (aovOPT == 2) then
				(	
					findDI = matchPattern beauty_AOVS[i] pattern:"direct"
										
					if (findDI != undefined) and (findDI == true) then
					(
						aovN = findItem beauty_AOVS beauty_AOVS[i]
						deleteItem beauty_AOVS aovN
					)
					
					findDI = matchPattern beauty_AOVS[i] pattern:"*_direct"
										
					if (findDI != undefined) and (findDI == true) then
					(
						aovN = findItem beauty_AOVS beauty_AOVS[i]
						deleteItem beauty_AOVS aovN
					)
				)
				
				if (aovOPT == 3) then
				(	
					findDI = matchPattern beauty_AOVS[i] pattern:"*indirect"
					
					if (findDI != undefined) and (findDI == true) then
					(
						aovN = findItem beauty_AOVS beauty_AOVS[i]
						deleteItem beauty_AOVS aovN
					) 
				)
			)
		)
	)
	
	--########################################################################################
	--			A D D  S P E C I A L  A O V S 
	--########################################################################################
	
	fn add_N_AOV =
		(
			aovN = findItem data_AOVS "N_object"
		
			if aovN == 0 then 
			( 
				renderers.current.aov_shaders_mat_0 = ai_aov_write_vector name: "N_object"
				renderers.current.aov_shaders_mat_0.aov_name = "N_object"
				n_objectAOV = renderers.current.aov_shaders_mat_0
				n_objectAOV.aov_input_shader = ai_utility name: "N_object_utl"
				n_objectAOV.aov_input_shader.color_mode = 3
				n_objectAOV.aov_input_shader.shade_mode = 2
				amw.AddCustomAOV "N_object"
				appendIfUnique data_AOVS "N_object"
			)
			else 
			(
				renderers.current.aov_shaders_mat_0 = undefined
				deleteItem data_AOVS aovN
			)
		)
	
	fn add_AO_AOV = 
		(
			aovN = findItem data_AOVS "AO"
			
			if aovN == 0 then
			(
				renderers.current.aov_shaders_mat_1 = ai_aov_write_rgba name: "AO"
				renderers.current.aov_shaders_mat_1.aov_name = "AO"
				ao_objectAOV = renderers.current.aov_shaders_mat_1
				ao_objectAOV.aov_input_shader = ai_ambient_occlusion name: "AO_utl"
				ao_objectAOV.aov_input_shader.samples = 10
				ao_objectAOV.aov_input_shader.spread = 0.25
				ao_objectAOV.aov_input_shader.far_clip = 5
				amw.AddCustomAOV "AO"
				appendIfUnique data_AOVS "AO"
			)
			else 
			(
				renderers.current.aov_shaders_mat_1 = undefined
				deleteItem data_AOVS aovN
			)
		)
	
	fn add_UV_AOV = 
		(
			aovN = findItem data_AOVS "UV"
			
			if aovN == 0 then
			(
				renderers.current.aov_shaders_mat_2 = ai_aov_write_rgba name: "UV"
				renderers.current.aov_shaders_mat_2.aov_name = "UV"
				uv_objectAOV = renderers.current.aov_shaders_mat_2
				uv_objectAOV.aov_input_shader = ai_utility name: "UV_utl"
				uv_objectAOV.aov_input_shader.color_mode = 5
				uv_objectAOV.aov_input_shader.shade_mode = 2
				amw.AddCustomAOV "UV"
				appendIfUnique data_AOVS "UV"
			)
			else 
			(
				renderers.current.aov_shaders_mat_2 = undefined
				deleteItem data_AOVS aovN
			)
		)
		
	--#########################################################################################
	--			D E F I N E  C H E C K B O X E S  B E H A V I O U R 
	--#########################################################################################
	
	on _rgback changed theState do
	(
		if (theState == true ) then
		(
			_diffuseck.checked = theState 
			_diffuseck.enabled = NOT theState
			_specularck.checked = theState 
			_specularck.enabled = NOT theState
			_transmissionck.checked = theState 
			_transmissionck.enabled = NOT theState
			_sheenck.checked = theState 
			_sheenck.enabled = NOT theState
			_sssck.checked = theState 
			_sssck.enabled = NOT theState
			_volumeck.checked = theState 
			_volumeck.enabled = NOT theState
			_coatck.checked = theState 
			_coatck.enabled = NOT theState
			_emission.checked = theState 
			_emission.enabled = NOT theState
			_background.checked = theState 
			_background.enabled = NOT theState
		)
			if (theState == true) then 
			(
				beauty_AOVS = #()
				appendIfUnique beauty_AOVS "RGBA"
			)
			
			else (beauty_AOVS = #())
		
		if (theState == false ) then 
		(
			_diffuseck.checked = on
			_diffuseck.enabled = on
				appendIfUnique beauty_AOVS "diffuse"
			_specularck.checked = on 
			_specularck.enabled = on 
				appendIfUnique beauty_AOVS "specular"
			_transmissionck.checked = on 
			_transmissionck.enabled = on 
				appendIfUnique beauty_AOVS "transmission"
			_sheenck.checked = on
			_sheenck.enabled = on
				appendIfUnique beauty_AOVS "sheen"
			_sssck.checked = on
			_sssck.enabled = on 
				appendIfUnique beauty_AOVS "sss"
			_volumeck.checked = on 
			_volumeck.enabled = on 
				appendIfUnique beauty_AOVS "volume"
			_coatck.checked = on 
			_coatck.enabled = on 
				appendIfUnique beauty_AOVS "coat"
			_emission.checked = on
			_emission.enabled = on
				appendIfUnique beauty_AOVS "emission"
			_background.checked = on
			_background.enabled = on
				appendIfUnique beauty_AOVS "background"
			_directAOV.checked = off 
			_indirectAOV.checked = off
			noice_AOVS = #()
		)	
	)
		
	--#########################################################################################
	--			B A S E  C O M P O N E N T S 
	--#########################################################################################
	
	fn checkNOICE _aovName =
	(
		aovN = findItem noice_AOVS _aovName
		if aovN == 0 then 
		( 
			if (_combinedDI.state == true) then  ( appendIfUnique noice_AOVS _aovName )
			else
			(
				if (_directck.state == true) then 
				(
					di_aov = _aovName + "_direct"
					appendIfUnique noice_AOVS di_aove
				)
				
				if (_indirectck.state == true) then
				(
					di_aov = _aovName + "_indirect"
					appendIfUnique noice_AOVS di_aov
				)
			)
		)
		else (deleteItem noice_AOVS aovN)
	)
	
		on _diffuseck changed theState do 
		(
			addAOVS_List "diffuse"
			
			if theState == true then
			(
				if (_directck.enabled == true) then ( addAOVS_DI true 2 )
				else (addAOVS_DI false 2 )
				if (_indirectck.enabled == true) then (addAOVS_DI true 3 )
				else (addAOVS_DI false 3 )
				
				if (_directAOV.checked == true) then ( checkNOICE "diffuse_direct" )
				if (_indirectAOV.checked == true) then ( checkNOICE "diffuse_indirect" )
			)
			
			if theState == false then 
			(
				if (_directAOV.checked == true) then ( checkNOICE "diffuse_direct" )
				if (_indirectAOV.checked == true) then ( checkNOICE "diffuse_indirect" )
			)
		)
	
		on _specularck changed theState do 
		(
			addAOVS_List "specular"
			
			if theState == true then
			(
				if (_directck.enabled == true) then ( addAOVS_DI true 2 )
				else (addAOVS_DI false 2 )
				if (_indirectck.enabled == true) then (addAOVS_DI true 3 )
				else (addAOVS_DI false 3 )
				
				if (_directAOV.checked == true) then ( checkNOICE "specular_direct" )
				if (_indirectAOV.checked == true) then ( checkNOICE "specular_indirect" )
			)
			
			if theState == false then 
			(
				if (_directAOV.checked == true) then ( checkNOICE "specular_direct" )
				if (_indirectAOV.checked == true) then ( checkNOICE "specular_indirect" )
			)
		)
	
		on _transmissionck changed theState do 
			(
				addAOVS_List "transmission"
				
				if theState == true then
				(
					if (_directck.enabled == true) then ( addAOVS_DI true 2 )
					else (addAOVS_DI false 2 )
					if (_indirectck.enabled == true) then (addAOVS_DI true 3 )
					else (addAOVS_DI false 3 )
					
					if (_directAOV.checked == true) then ( checkNOICE "transmission_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "transmission_indirect" )
				)
				
				if theState == false then 
				(
					if (_directAOV.checked == true) then ( checkNOICE "transmission_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "transmission_indirect" )
				)
			)
	
		on _sheenck changed theState do 
			(
				addAOVS_List "sheen"
				
				if theState == true then
				(
					if (_directck.enabled == true) then ( addAOVS_DI true 2 )
					else (addAOVS_DI false 2 )
					if (_indirectck.enabled == true) then (addAOVS_DI true 3 )
					else (addAOVS_DI false 3 )
					
					if (_directAOV.checked == true) then ( checkNOICE "sheen_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "sheen_indirect" )
					
				)
				
				if theState == false then 
				(
					if (_directAOV.checked == true) then ( checkNOICE "sheen_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "sheen_indirect" )
				)
			)
	
		on _sssck  changed theState do 
			(
				addAOVS_List "sss"
				
				if theState == true then
				(
					if (_directck.enabled == true) then ( addAOVS_DI true 2 )
					else (addAOVS_DI false 2 )
					if (_indirectck.enabled == true) then (addAOVS_DI true 3 )
					else (addAOVS_DI false 3 )
					
					if (_directAOV.checked == true) then ( checkNOICE "sss_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "sss_indirect" )
				)
				
				if theState == false then 
				(
					if (_directAOV.checked == true) then ( checkNOICE "sss_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "sss_indirect" )
				)
			)

		on _volumeck changed theState do 
			(
				addAOVS_List "volume"
				
				if theState == true then
				(
					if (_directck.enabled == true) then ( addAOVS_DI true 2 )
					else (addAOVS_DI false 2 )
					if (_indirectck.enabled == true) then (addAOVS_DI true 3 )
					else (addAOVS_DI false 3 )
					
					if (_directAOV.checked == true) then ( checkNOICE "volume_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "volume_indirect" )
				)
				
				if theState == false then 
				(
					if (_directAOV.checked == true) then ( checkNOICE "volume_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "volume_indirect" )
				)
			)

		on _coatck changed theState do 
			(
				addAOVS_List "coat"
				
				if theState == true then
				(
					if (_directck.enabled == true) then ( addAOVS_DI true 2 )
					else (addAOVS_DI false 2 )
					if (_indirectck.enabled == true) then (addAOVS_DI true 3 )
					else (addAOVS_DI false 3 )
					
					if (_directAOV.checked == true) then ( checkNOICE "coat_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "coat_indirect" )
				)
				
				if theState == false then 
				(
					if (_directAOV.checked == true) then ( checkNOICE "coat_direct" )
					if (_indirectAOV.checked == true) then ( checkNOICE "coat_indirect" )
				)
			)
		
		on _emission changed theState do ( addAOVS_List "emission" )
		
		on _background changed theState do ( addAOVS_List "background" )
	
	--#########################################################################################
	--			D I R E C T \ I N D I R E C T  A O V S
	--#########################################################################################
	
	on _combinedDI changed theState do
	(
		if (theState == true) then
		(
			_separateGB.enabled = NOT theState
			_directck.enabled =   NOT theState
			_indirectck.enabled =  NOT theState
			addAOVS_DI false 1
		)
		
		if (theState == false) then
		(
			_separateGB.enabled = on
			_directck.enabled = on 
			_directck.checked = on
			_indirectck.enabled = on
			_indirectck.checked = on
				
			if _rgback.checked == true then
			(
				rgba_D = "direct"
				aovN = findItem beauty_AOVS rgba_D
				if aovN == 0 then (append beauty_AOVS rgba_D)
				
				rgba_I = "indirect"
				aovN = findItem beauty_AOVS rgba_I
				if aovN == 0 then (append beauty_AOVS rgba_I)
			)
			else
			(
				addAOVS_DI true 1
				addAOVS_DI true 2
			)
			sort beauty_AOVS
		)
	)
	
	on _directck changed theState do
	(
		if (theState == true) then (addAOVS_DI true 2)
		if (theState == false) then (addAOVS_DI false 2)
	)
	
	on _indirectck changed theState do
	(
		if (theState == true) then (addAOVS_DI true 3)
		if (theState == false) then (addAOVS_DI false 3)
	)
	
	--#########################################################################################
	--			A D D  A L L  D A T A
	--#########################################################################################
	
	on _dataALL changed theState do
	(
		if (theState == true) then
		(
			_nck.checked = theState 
			_nck.enabled = NOT theState
			appendIfUnique data_AOVS "N"
			_pck.checked = theState
			_pck.enabled = NOT theState
			appendIfUnique data_AOVS "P"
			_zck.checked = theState
			_zck.enabled = NOT theState
			appendIfUnique data_AOVS "Z"
			_ack.checked = theState
			_ack.enabled = NOT theState
			appendIfUnique data_AOVS "A"
			_n2ck.checked = theState
			_n2ck.enabled = NOT theState
			add_N_AOV()
			_aock.checked = theState
			_aock.enabled = NOT theState
			add_AO_AOV()
			_motionck.checked = theState
			_motionck.enabled = NOT theState
			appendIfUnique data_AOVS "motionvector"
			_uvck.checked = theState
			_uvck.enabled = NOT theState
			add_UV_AOV()
		)
		
		if (theState == false) then
		(
			_nck.checked = theState 
			_nck.enabled = NOT theState
			aovN = findItem data_AOVS "N"
			deleteItem data_AOVS aovN
			_pck.checked = theState
			_pck.enabled = NOT theState
			aovN = findItem data_AOVS "P"
			deleteItem data_AOVS aovN
			_zck.checked = theState
			_zck.enabled = NOT theState
			aovN = findItem data_AOVS "Z"
			deleteItem data_AOVS aovN
			_ack.checked = theState
			_ack.enabled = NOT theState
			aovN = findItem data_AOVS "A"
			deleteItem data_AOVS aovN
			_n2ck.checked = theState
			_n2ck.enabled = NOT theState
			add_N_AOV()
			_aock.checked = theState
			_aock.enabled = NOT theState
			add_AO_AOV()
			_motionck.checked = theState
			_motionck.enabled = NOT theState
			aovN = findItem data_AOVS "motionvector"
			deleteItem data_AOVS aovN
			_uvck.checked = theState
			_uvck.enabled = NOT theState
			add_UV_AOV()
		)
	)
	
	--#########################################################################################
	--			E X T R A 
	--#########################################################################################
	on _exrSingle changed theState do 
		(
			if _exrSingle.state == 1 then
			(
				_lightgroups.enabled = on
				aovs_lightgpr = #("All Lights")
			)
			
			if _exrSingle.state == 2 then
			(
				_lightgroups.checked = off
				_lightgroups.enabled = off
			)
		)

	--#########################################################################################
	--			G P U  A O V S
	--#########################################################################################
	on _gpuaovs changed theState do
	(
		if _gpuaovs.checked == true then 
		(
			_diffuseAOV.checked = true
			_diffuseAOV.enabled = NOT theState
			_nAOV.checked = true
			_nAOV.enabled = NOT theState
			appendIfUnique gpu_AOVS "diffuse_albedo"
			appendIfUnique gpu_AOVS "N"
		)
		
		if _gpuaovs.checked == false then 
		(
			_diffuseAOV.checked = false
			_diffuseAOV.enabled = NOT theState			
			_nAOV.checked = false
			_nAOV.enabled = NOT theState
			aovN = findItem gpu_AOVS "diffuse_albedo"
			deleteItem gpu_AOVS aovN
			aovN = findItem gpu_AOVS "N"
			deleteItem gpu_AOVS aovN
		)
	)
	
	on _diffuseAOV changed theState do 
	(
		if (theState == true) then ( appendIfUnique gpu_AOVS "diffuse_albedo" )
		
		if (theState == false) then
		(
			aovN = findItem gpu_AOVS "diffuse_albedo"
			deleteItem gpu_AOVS aovN
		)
	)
	
	on _nAOV changed theState do
	(
		if (theState == true) then ( appendIfUnique gpu_AOVS "N" )
		
		if (theState == false) then
		(
			aovN = findItem gpu_AOVS "N"
			deleteItem gpu_AOVS aovN
		)
	)
			
	--#########################################################################################
	--			C P U  A O V S 
	--#########################################################################################
	
	on _noiceaovs changed theState do
	(
		if _noiceaovs.checked == true then 
		(
			_directAOV.checked = true 
			_directAOV.enabled = NOT theState
			_indirectAOV.checked = true
			_indirectAOV.enabled = NOT theState
			
			noice_AOVS =#() 
			
			for i = 1 to beauty_AOVS.count do
			(
				findDI = findString beauty_AOVS[i] "_"
			
				if (findDI == undefined) and (beauty_AOVS[i] != "background") and (beauty_AOVS[i] != "emission") then
					(
						aovN = findItem beauty_AOVS beauty_AOVS[i]
						appendIfUnique noice_AOVS beauty_AOVS[i]
					)
			)
		
			appendIfUnique noice_AOVS "N"
			appendIfUnique noice_AOVS "Z"
			appendIfUnique noice_AOVS "denoise_albedo"
		)
		
		if _noiceaovs.checked == false then 
		(
			_directAOV.checked = false
			_directAOV.enabled = NOT theState			
			_indirectAOV.checked = false
			_indirectAOV.enabled = NOT theState
			
			noice_AOVS = #()
		)
	)
	
	on _directAOV changed theState do
	(
		if (theState == true) then
		(
			for i = 1 to beauty_AOVS.count do
			(
				findDI = MatchPattern beauty_AOVS[i] pattern: "*_*"
			
				if (findDI == false) and (beauty_AOVS[i] != "background") and (beauty_AOVS[i] != "emission") then
					(
						di_aov = beauty_AOVS[i] + "_direct"
						appendIfUnique noice_AOVS di_aov 
					)
			)
		
			appendIfUnique noice_AOVS "N"
			appendIfUnique noice_AOVS "Z"
			appendIfUnique noice_AOVS "denoise_albedo"
		)
		
		if (theState == false) then ( noice_AOVS = #() )
	)
		
	on _indirectAOV changed theState do
	(
		if (theState == true) then
		(
			for i = 1 to beauty_AOVS.count do
			(
				findDI = MatchPattern beauty_AOVS[i] pattern: "*_*"
			
				if (findDI == false) and (beauty_AOVS[i] != "background") and (beauty_AOVS[i] != "emission") then
					(
						di_aov = beauty_AOVS[i] + "_indirect"
						appendIfUnique noice_AOVS di_aov 
					)
			)
		
			appendIfUnique noice_AOVS "N"
			appendIfUnique noice_AOVS "Z"
			appendIfUnique noice_AOVS "denoise_albedo"
		)
		
		if (theState == false) then ( noice_AOVS = #() )
	)
		
	--#########################################################################################
	--			A L B E D O 
	--#########################################################################################
	on _albedock changed theState do
	(
		if theState == true then
		(
			for i = 1 to beauty_AOVS.count  do
			(
				aov_check = beauty_AOVS[i]
				
				if (matchPattern aov_check pattern:"*_*") then ()
				else
				(
					if (matchPattern aov_check pattern:"*background*") or (matchPattern aov_check pattern:"*emission*") then ()
					else
					(
						aov_di = aov_check + "_albedo"
						aovN = findItem beauty_AOVS aov_di
						if aovN == 0 then (append beauty_AOVS aov_di)
					)
				)
			)
		)
		
		if theState == false then
		(
			for i = 1 to beauty_AOVS.count do
			(
				aov_check = beauty_AOVS[i]
				if aov_check != undefined then
				(
					if (matchPattern beauty_AOVS[i] pattern:"*_albedo") then
					(
						aovN = findItem beauty_AOVS beauty_AOVS[i]
						deleteItem beauty_AOVS aovN 
					) 
				)
			)
		)
		
	)
	
	--#########################################################################################
	--			O P A C I T Y 
	--#########################################################################################
	on _opacityck changed theState do
	(
		aov_di = "volume_opacity"
		aovN = findItem beauty_AOVS aov_di
						
		if aovN == 0 then (append beauty_AOVS aov_di)
		else (deleteItem beauty_AOVS aovN)
	)
	--#########################################################################################
	--			L I G H T  G R O U P S 
	--#########################################################################################
	on _lightgroups changed theState do
	(
		lgm = MaxtoAOps.LightGroupsManager()
		if theState == false then ( lgm.Close() )
	)
	
	--#########################################################################################
	--			D A T A  A O V S
	--#########################################################################################
	on _nck changed theState do ( addAOVSDATA "N")
	on _pck changed theState do ( addAOVSDATA "P")
	on _zck changed theState do ( addAOVSDATA "Z")
	on _ack changed theState do ( addAOVSDATA "A")
	on _motionck changed theState do (addAOVSDATA "motionvector")
	on _n2ck changed theState do (add_N_AOV())
	on _aock changed theState do (add_AO_AOV()) 
	on _uvck changed theState do (add_UV_AOV())
	
	--#########################################################################################
	--			C R Y P T O M A T T E
	--#########################################################################################
	fn add_CRY_AOV _craov =
	(
		aovN = findItem data_AOVS _craov
			
		if aovN == 0 then ( appendIfUnique data_AOVS _craov	)
		else (deleteItem data_AOVS aovN)
				
		renderers.current.aov_shaders_map_0 = ai_cryptomatte name: "CRYPTOMATTE"
	)
		
	on _cr_assetck changed theState do (add_CRY_AOV "crypto_asset")
	on _cr_objectck changed theState do (add_CRY_AOV "crypto_object")
	on _cr_mtlck changed theState do (add_CRY_AOV "crypto_material")
		
	on _cryptoALL changed theState do
	(
		if (theState == true) then
		(
			_cryptoSP.enabled = NOT theState
			_cryptoSP.enabled = NOT theState
			_cr_assetck.enabled = NOT theState
			_cr_assetck.checked = theState
			_cr_objectck.enabled = NOT theState
			_cr_objectck.checked = theState
			_cr_mtlck.enabled = NOT theState
			_cr_mtlck.checked = theState
					
			add_CRY_AOV "crypto_asset"
			add_CRY_AOV "crypto_object"
			add_CRY_AOV "crypto_material"
		)
		
		if (theState == false) then
		(
			renderers.current.aov_shaders_map_0 = undefined
			_cryptoSP.enabled = NOT theState
			_cryptoSP.enabled = NOT theState
			_cr_assetck.enabled = NOT theState
			_cr_assetck.checked = theState
			_cr_objectck.enabled = NOT theState
			_cr_objectck.checked = theState
			_cr_mtlck.enabled = NOT theState
			_cr_mtlck.checked = theState
			add_CRY_AOV "crypto_asset"
			add_CRY_AOV "crypto_object"
			add_CRY_AOV "crypto_material"
		)
	)
	
	--#########################################################################################
	--			B U T T O N S 
	--#########################################################################################
	
	on _deleteAOVs pressed do ( renderers.current.aov_Manager.drivers = #() )
	
	on _createAOVs pressed do 
	(
		--check light groups 
		lt = lights
		aovs_lightgpr = #()
		lgm = MaxtoAOps.LightGroupsManager()
		lgm.Close()
		-- thanks to Giuseppe Schiralli for the help with the light groups
		if _lightgroups.state == true then
		(
			if lt.count >= 1 then 
			(
				_exrSingle.state = 1
				for i = 1 to lt.count do
				(
					isValidLight = false
					case (classof lt[i]) of 
					(
						default: isValidLight = false
						Arnold_Light: isValidLight = true
						Free_Light: isValidLight = true
						Free_Linear: isValidLight = true
						Free_Area: isValidLight = true
						Free_Disc: isValidLight = true
						Free_Sphere: isValidLight = true
						Free_Cylinder: isValidLight = true
						Target_Light: isValidLight = true
						Target_Linear: isValidLight = true
						Target_Area: isValidLight = true
						Target_Disc: isValidLight = true
						Target_Sphere: isValidLight = true
						Target_Cylinder: isValidLight = true
					)
						
				if (isValidLight == true) and (lt[i].superclassID != 16) then
					(
						temp = lgm.getLightGroup lt[i]
						if temp == "" then 
						(
							lgm.setLightGroup lt[i] "default"
							temp = lgm.getLightGroup lt[i]
						)
						
						appendIfUnique aovs_lightgpr temp
					)
					else ( format "Light % is not valid\n" lt[i].name )
				) 
			)
			else
			(
				messageBox "No lights present in the scene"
				_lightgroups.checked = off
			)
		)
		
		if _lightgroups.state == false then
		(
			aovs_lightgpr = #("All Lights")
		)
		
		baseAOVS()
		
		if (gpu_AOVS.count > 0) then ( gpuAOVS() )
		
		if (data_AOVS.count > 0) then ( dataAOVS() )
		
		if (noice_AOVS.count > 0) then (addNOICEAOVS ())
		
		renderers.current.AOV_Manager.outputPath = "<RenderFolder>"
		MaxtoAOps.AOVsManagerWindow()
	)
)
CreateDialog _AOVShelper 590 370