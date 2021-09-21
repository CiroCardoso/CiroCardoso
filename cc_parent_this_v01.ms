/*
Coded by Ciro Cardoso
cirocardoso@yahoo.co.uk for feedback\suggestions or bugs 

**** DESCRIPTION ****
A basic script to parent objects to a Dummy

2021/09/21 - version 1.0


*/

--------------------------------
-- **** DEFINE VARIABLES **** --
--------------------------------

selAll = $* as Array -- selects everything in the scene
selBase = getCurrentSelection()

try(destroyDialog _parentingNodes ) catch()

rollout _parentingNodes "Parent This... v1.0" 
	
	(
		--provides some info
		label _infoLb "Select the geometry you want to parent or..." pos: [14,20] align:#center
		
		-- option to select everything in the scene
		
		checkbox _selectAll "Select all geometry" pos: [70, 45] align:#center checked: false tooltip:"Selects all geo"
		
		-- give a specific name to the dummy
		
		edittext _dumName "Name the dummy" labelOnTop: true text: "Dummy"
		
		spinner _PercentScale "Scale %" type:#Float range:[0, 10000000, 100]  pos: [50, 110] enabled: true
		
		on _PercentScale changed newValue do

			(

				global dummyScaleIn = newValue/100
				
				/*
				if myDummy != undefined newValue do
					(

						global dummyScaleIn = 2 as float --newValue/100
						
						
					)
				*/
			)

		--listbox _scaleOpt "Scale %" items: #("10", "20", "50", "75", "100", "125") height: 6 selection: 5
		
		
		
		button _parentSelect "Parent" 
		
		on _parentSelect pressed do
			
			(
				--creates a dummy with the name the user assigned
				myDummy = dummy name:_dumName.text
				
				scaleValue = (dummyScaleIn as float)
				
				--checks if all geometry is selected or not
				if _selectAll.checked == True do
					(
						selBase = selAll
					)

				if _selectAll.checked == False do
					(
						selBase = getCurrentSelection()
					)
				
				
				for i = 1 to selBase.count do
					(
					
						if selBase[i].parent == undefined then
							
							(
								selBase[i].parent = myDummy
							)
							
						else 
						
							( 
								selBase[i].wirecolor = red 
							)
				
					)
				
				myDummy.scale = [scaleValue, scaleValue, scaleValue]
			)
		
					
		button _deleteParent "Delete and Reset" 
			
			on _deleteParent pressed do
				
				(
					if myDummy != undefined then
					(
						myDummy.scale = [1,1,1]
						delete myDummy
						myDummy = undefined
					)
					else (messageBox "Nothing to delete or rescale")
				)
		
		
	)
		
CreateDialog _parentingNodes 250 200