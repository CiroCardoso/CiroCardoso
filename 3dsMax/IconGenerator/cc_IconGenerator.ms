/*  
Icon Generator
Thanks to Allan for the initial idea 

Feedback, bugs and suggestions 

cirocardoso@yahoo.co.uk


*/


try (DestroyDialog _IconGen) catch()
rollout _IconGen "Icon Generator 1.0"
(
	
	GroupBox _Instructions "Instructions" pos:[10, 20] height:50 width: 380
	label _imageMagick "Image Magick needs to be installed for this script to work." pos: [15, 35]
	hyperlink _download "Download it here -> https://imagemagick.org/script/download.php#windows" address: "https://imagemagick.org/script/download.php#windows" pos: [15, 50]
	
	label _selectFirst "1. - Select the Icon and\or the alpha" pos: [15, 80]
	edittext _locationIcon "Icon" width: 285 pos:[100, 110]
	edittext _locationIconA "Icon Alpha" width: 285 pos:[100, 160]
	
	button _chooseIconI "Select Icon" height: 35 pos:[15, 100]
	button _chooseIconA "Select Alpha" height: 35 pos:[15, 150]
	
	label _selectSecond "2. - Select the sizes - 16x15 isn't a typo" pos: [15, 200]
	
	checkbox _size48 "48x48" pos: [15, 220]
	checkbox _size32 "32x32" pos: [70, 220]
	checkbox _size24 "24x24" pos: [125, 220]
	checkbox _size16 "16x15" pos: [180, 220]
	
	label _selectThird "3. - OPTIONAL - Add a suffix or prefix" pos: [15, 250]
	
	edittext _addSuffix "Suffix" width: 180 pos:[15, 275]
	edittext _addPrefix "Prefix" width: 180 pos:[200, 275]
	
	label _selectForth "4. - CONVERT - By default converts to .bmp" pos: [15, 310]
	
	radiobuttons _PNG labels: #("BMP", "PNG", "JPG") pos: [15, 330]
	
	--bitmap _bitm bitmap:(bitmap 100 100 color: gray) pos:[15, 400]
	
	label _iconPrev "Icon Preview" pos:[40, 380]
	button bt "" width: 110 height: 110 pos:[15, 400]
	
	button _convertIcon "Convert Icons" width:250 height: 75 pos:[130, 400]
	button _dirIcon "Open Directory" width:250 height: 30 pos:[130, 480]
			
		
	on _chooseIconI pressed do
	(
		imgPath = getOpenFileName caption:"Select the Icon" types: "BMP (*.bmp)| *.bmp| PNG (*.png)| *.png"
		if imgPath != undefined do (_locationIcon.text = imgPath)
		
		sourceFile = _locationIcon.text
		newBitmap = #(sourceFile, undefined, 1, 1, 1, 1, 1)
		
		bt.images = newBitmap
		bt.width = 110
		bt.height = 110
		
		
	)
	
	on _chooseIconA pressed do
	(
		imgPath = getOpenFileName caption:"Select the Icon" types: "BMP (*.bmp)| *.bmp| PNG (*.png)| *.png"
		if imgPath != undefined do (_locationIconA.text = imgPath)
		
	)
	
	on _PNG changed ext do 
	(
		if _PNG.state == 1 do
		(
			global ext = ".bmp"
		)
		
		if _PNG.state == 2 do
		(
			global ext = ".png"
		)
	
		if _PNG.state == 3 do
		(
			global ext = ".jpg"
		)
		
	)
	
	
	
	on _convertIcon pressed do
	(
		imageMagick = "\"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe\""
		sourceFile = _locationIcon.text
		sourceAlpha = _locationIconA.text
		
				
		global dest_FileName = getFilenameFile sourceFile
		global dest_Path = getFilenamePath sourceFile
		
		
		
		if _addSuffix.text != undefined do 
		(
			dest_FileName = _addSuffix.text + dest_FileName
		)
		
		
		if textPrefix != undefined do
		(
			dest_FileName = dest_FileName + _addPrefix.text
		)
		
		global dest_Output = dest_Path + dest_FileName
		
		
		if _size48.checked == true do 
		(
			outputString = imageMagick + " convert " + sourceFile + " -resize 48x48! " + dest_Output + "_48i" + ext
			DOSCommand outputString 
		)
		
		if _size32.checked == true do
		(
			outputString = imageMagick + " convert " + sourceFile + " -resize 32x32! " + dest_Output + "_32i" + ext
			DOSCommand outputString 
		)
		
		if _size24.checked == true do
		(
			outputString = imageMagick + " convert " + sourceFile + " -resize 24x24! " + dest_Output + "_24i" + ext
			DOSCommand outputString 
		)
		
		if _size16.checked == true do
		(
			outputString = imageMagick + " convert " + sourceFile + " -resize 16x15 " + dest_Output + "_16i.bmp"
			DOSCommand outputString 
		)
		
		if _size48.checked == false and _size32.checked == false and _size24.checked == false and _size16.checked == false do
		(
		
			messageBox "You need to select at least one option"
		)
		
		if sourceAlpha != undefined do
		(
			
			if _size48.checked == true do 
			(
				outputString = imageMagick + " convert " + sourceAlpha + " -resize 48x48! " + dest_Output + "_48a.bmp"
				DOSCommand outputString 
			)
		
			if _size32.checked == true do
			(
				outputString = imageMagick + " convert " + sourceAlpha + " -resize 24x24! " + dest_Output + "_32a.bmp"
				DOSCommand outputString 
			)
		
			if _size24.checked == true do
			(
				outputString = imageMagick + " convert " + sourceAlpha + " -resize 32x32! " + dest_Output + "_24a.bmp"
				DOSCommand outputString 
			)
		
			if _size16.checked == true do
			(
				outputString = imageMagick + " convert " + sourceAlpha + " -resize 16x15 " + dest_Output + "_16a.bmp"
				DOSCommand outputString 
			)
			
		)
		
	)
	
	on _dirIcon pressed do
	(
		ShellLaunch dest_Path ""
		)
	
)
	
CreateDialog _IconGen 400 550
