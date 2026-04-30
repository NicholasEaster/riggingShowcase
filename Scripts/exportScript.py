import maya.cmds as cmds
import os

#Create a global variable to store the previous folder selected for export.
exportPath_OPTIONVAR = "OBJExporter_LastExportPath"

###############################################################
####################### PIVOT PLANET ##########################
###############################################################


######## FUNCTION TO CHANGE A PIVOT ########
## This function will change the pivot of selected object(s) by calling the helper function.

## It takes a pivot result contained in a radio button.
## Uses the changePivotHelper helper function.
def changePivot(pivotRadio):
    pivotResults = cmds.radioButtonGrp(pivotRadio, query=True, select=True)
    sel = cmds.ls(selection=True, long=True)
    
    if not sel:
        cmds.warning('No objects were selected')
        return
        
    for selectedObjects in sel:
        objName = selectedObjects.split("|")[-1] #This is needed because the default is Parent name|child name. 
        changePivotHelper(pivotResults, objName)        
    
######## FUNCTION TO HELP MODIFY A PIVOT ########
## This function will set the pivot to be either the bottom left or the bottom center based on user preference.

## It takes a pivot result as well as an object to apply the transformations to.
def changePivotHelper(pivotResults, object):
    if pivotResults == 1:
        bbox = cmds.xform(object, query=True, boundingBox=True, worldSpace=True) #Get the object bounds
        x = bbox[0]
        y = bbox[1]
        z = bbox[5]
        cmds.move(x, y, z, object+".scalePivot", object+".rotatePivot", absolute=True) #Move the pivot the the bottom left   
    elif pivotResults == 3:         
        bbox = cmds.xform(object, query=True, boundingBox=True, worldSpace=True) #Get the object bounds
        x = (bbox[0] + bbox[3]) / 2.0
        y = (bbox[1] + bbox[4]) / 2.0
        z = (bbox[2] + bbox[5]) / 2.0
        cmds.move(x, y, z, object+".scalePivot", object+".rotatePivot", absolute=True) #Move the pivot the the bottom center   
    elif pivotResults == 4:         
        bbox = cmds.xform(object, query=True, boundingBox=True, worldSpace=True) #Get the object bounds
        x = (bbox[0] + bbox[3]) / 2.0
        y = bbox[1]
        z = (bbox[2] + bbox[5]) / 2.0
        cmds.move(x, y, z, object+".scalePivot", object+".rotatePivot", absolute=True) #Move the pivot the the bottom center                

###############################################################
######################## GEO CHECKER ##########################
###############################################################


######## FUNCTION TO CHECK GEO ########
## This function will check the geometry of an object by calling the geo helper function.

## It takes the checkBoxes result given by the user.
## Uses the checkGEOHelper helper function.
def checkGEO(checkBoxes):               
    sel = cmds.ls(selection=True, long=True)
    
    if not sel:
        cmds.warning('No objects were selected')
        return
        
    for selectedObjects in sel:
        objName = selectedObjects.split("|")[-1] #This is needed because the default is Parent name|child name. 
        checkGEOHelper(checkBoxes, objName)        

######## FUNCTION TO HELP CHECK GEO ########
## This function will perform different checks on the selected object based on what the user selects.
## If the function is called by the exporter as apposed to manually through the button, it is hard coded to check the necessary components.

## It takes the checkBoxes result given by the user.
## Returns any issues found.
def checkGEOHelper(checkBoxes, object, mode="manual"):
    cmds.select(object, r=True) #Select the object just in case
    
    problemComponents = [] #Make an array of problems (verts / edges/ faces)
    issues = [] #Make an array to display the problems (just used for a warning)
    
    originalSelection = cmds.ls(sl=True) #Store the original selection
    
    if mode == "manual":
        nonManifoldCheck = cmds.checkBoxGrp(checkBoxes, query=True, value1=True) #Get info from checkboxes
        NgonsCheck = cmds.checkBoxGrp(checkBoxes, query=True, value2=True)
        deleteHistoryCheck = cmds.checkBoxGrp(checkBoxes, query=True, value3=True)
        freezeTransformsCheck = cmds.checkBoxGrp(checkBoxes, query=True, value4=True)
    elif  mode == "validate":
        nonManifoldCheck = True
        NgonsCheck = True
        deleteHistoryCheck = False
        freezeTransformsCheck = False
        
    if nonManifoldCheck:
        cmds.polySelectConstraint(mode=3, type=1, nonmanifold=True) #Check for non manifold geo
        nonManifoldGeo = cmds.ls(sl=True, fl=True) #If anything is selected, return true
        problemComponents.extend(nonManifoldGeo) #Add the geo to the array
    
        if nonManifoldGeo:
            issues.append("non-manifold")
            
    if NgonsCheck:
        cmds.polySelectConstraint(mode=3, type=8, size=3) #Check for Ngons, type is set to face
        ngons = cmds.ls(sl=True, fl=True) #If anything is selected, return true
        problemComponents.extend(ngons) #Add the geo to the array
    
        if ngons:
            issues.append("ngons")
    
    if deleteHistoryCheck:
        cmds.delete(object, constructionHistory=True) #Delete History
        
    if freezeTransformsCheck:
        cmds.makeIdentity(object, apply=True, t=1, r=1, s=1) #Freeze translate, rotate, scale
      
    cmds.polySelectConstraint(mode=0) #Reset constraint

    if problemComponents: #If there are elements in the problem array
        cmds.select(list(set(problemComponents)), replace=True) #Select them
    else:
        cmds.select(originalSelection) #Get the original selection
        
    if issues:
            cmds.warning(f"{object} issues: {', '.join(issues)}") #Format the warning                               
    return issues


###############################################################
##################### EXPORT CENTRAL ##########################
###############################################################


######## FUNCTION TO EXPORT AN OBJECT ########
## This function will take a given object(s), modify the pivots based on the user's choice, and check the geometry for issues.
## It will then duplicate the object, remove any of its groups, and move the object to the world origin.
## The duplicated object is then exported and deleted afterwards

## It takes a filePath as well as all of the radio buttons provided by the user
## Uses the checkGEOHelper and changePivotHelper helper functions.     
def exportObjects(filePath, pivotRadio, checkBoxes, exportRadio):
    exportPath = cmds.textField(filePath, query=True, text=True)
    pivotResults = cmds.radioButtonGrp(pivotRadio, query=True, select=True)    
    exportType = cmds.radioButtonGrp(exportRadio, query=True, select=True)
        
    ########PRELIMINARY CHECKS#######
    if not exportPath:
        cmds.warning("Please select an export directory.")
        return
            
    sel = cmds.ls(selection=True, long=True)
    if not sel:
        cmds.warning('No objects were selected')
        return

    invalidObjects = {} #Check for invalid objects
    for selectedObjects in sel:
        objName = selectedObjects.split("|")[-1]
        issues = checkGEOHelper(checkBoxes, objName, "validate")

        if issues:
            invalidObjects[objName] = issues

    if invalidObjects:
        cmds.warning("Export aborted: geometry issues detected.")
        return
                
    for selectedObjects in sel:
        ##Create the duplicate and transfer the name
        objName = selectedObjects.split("|")[-1] #This is needed because the default is Parent name|child name.
        tempRename = cmds.rename(selectedObjects, objName + "_")
        duplicate = cmds.duplicate(tempRename, name=objName)[0]       
         
        hasParent=cmds.listRelatives(selectedObjects, parent=True)                  
        if hasParent:
            cmds.parent(duplicate, world=True)
            
        ##Modify Pivot
        changePivotHelper(pivotResults, duplicate)
        
        ##Move to Origin
        currentPositionXYZ = cmds.xform(duplicate, q=True, ws=True, rp=True)
        cmds.move(-currentPositionXYZ[0], -currentPositionXYZ[1], -currentPositionXYZ[2], duplicate, r=True, ws=True)
        cmds.makeIdentity(duplicate, apply=True, translate=True, rotate=True, scale=True, normal=False, preserveNormals=True)
        
        cmds.select(duplicate, replace=True)
        
        ########EXPORT#######
        if (exportType == 1):
            cmds.loadPlugin("fbxmaya") 
            suffix = ".fbx"
            fileType = "FBX export"           
        else:
            cmds.loadPlugin('objExport')
            suffix = ".obj"
            fileType = "OBJexport"
                                   
        exportFile = os.path.join(exportPath, objName + suffix)
        try:
            cmds.file(
                exportFile,
                force=True,
                options="v=0;",
                type=fileType,
                exportSelected=True
            )
            print(f"Successfully exported selected objects to: {exportPath}")
        except RuntimeError as e:
            print(f"Error during FBX export: {e}")
        
        #######CLEANUP#######
        cmds.delete(duplicate)
        cmds.rename(tempRename, objName)
    cmds.optionVar(stringValue=(exportPath_OPTIONVAR, exportPath))
    
###############################################################
####################### WINDOW CREATION #######################
###############################################################


######## FUNCTION TO BROWSE FOR A FOLDER ########
## This function will open up the file directory built into maya.
## If something is then selected, the textfield is updated with the new path.

## It takes a textField that will store the folder location.
def browseForFolder(textField):
    folder = cmds.fileDialog2(fileMode=3, dialogStyle=2)

    if folder:
        cmds.textField(textField, edit=True, text=folder[0])
        cmds.optionVar(stringValue=(exportPath_OPTIONVAR, folder[0]))

########FUNCTION TO CREATE THE WINDOW#######
## This function creates the window and the buttons needed to run the program.

## Uses changePivot, checkGEO, browseForFolder, and exportObjects
def createWindow():
    # Create Window  
    windowName = "OBJ_Exporter"
    print (windowName)
    
    #Removes Current Window (If There Is One Already Up)
    if cmds.window(windowName, exists=True):
        cmds.deleteUI(windowName)
    
    windowWidth = 425
    windowHeight = 325 
    cmds.window(windowName, title=windowName, widthHeight=(windowWidth, windowHeight), sizeable=False)  
        
    mainLayout = cmds.columnLayout( adjustableColumn=True )    
    cmds.separator(height=8, style="in", parent=mainLayout)       
    #######PIVOT PLANET#######
    pivotFrame = cmds.frameLayout(
        label="Pivot Location",
        collapsable=False,
        marginWidth=8,
        marginHeight=6,
        parent=mainLayout
    )
    pivotColumn = cmds.columnLayout(adjustableColumn=True, parent=pivotFrame)

    pivotRadio = cmds.radioButtonGrp(
        labelArray4=["Bottom Left", "Custom", "Centered", "Bottom Center"],
        annotation="Change the pivot of an object, or keep the current pivot by selecting custom.",
        columnWidth=([1,100], [2,90], [3,90]),
        numberOfRadioButtons=4,
        select=2
    )
    
    #Start Pivot
    cmds.button(
        label="Modify Pivot",parent= mainLayout, annotation="Object selected: modify the pivot of the selected object.", 
        command=lambda *args: changePivot(pivotRadio)
    )
    
    cmds.text(label="",parent= mainLayout)
    
    #######MESH CLEANUP#######
    cmds.separator(height=8, style="in", parent=mainLayout)
    
    cleanupFrame = cmds.frameLayout(
        label="Cleanup Object",
        collapsable=False,
        marginWidth=8,
        marginHeight=6,
        parent=mainLayout
    )
    
    cleanupCol = cmds.rowColumnLayout(
        numberOfColumns=3,
        columnAttach=([1, 'right', 5], [2, 'left', 5], [3, 'left', 5]),
        parent=mainLayout
    )
    
    checkBoxes = cmds.checkBoxGrp(
    labelArray4=["nonManifold", "Ngons", "Delete History", "Freeze Transforms"],
    annotation="Verifies the mesh does not contain invalid geometry and can delete history or freeze the transforms.",    
    numberOfCheckBoxes=4,
    columnWidth4=[100,65,100,100]
    )
    
    #Start Cleanup
    cmds.button(
        label="Check Objects",parent= mainLayout, annotation="Object selected: validate the object and optionally clean up the object.", 
        command=lambda *args: checkGEO(checkBoxes)
    )
    
    cmds.text(label="",parent= mainLayout)
   
    #######EXPORT PATH#######
    cmds.separator(height=8, style="in", parent=mainLayout)
    
    exportFrame = cmds.frameLayout(
        label="Export Path",
        collapsable=False,
        marginWidth=8,
        marginHeight=6,
        parent=mainLayout
    )         

    exportCol = cmds.rowColumnLayout(
        numberOfColumns=2,
        columnAttach=([1, 'right', 5], [2, 'left', 5]),
        parent=mainLayout
    )
    
    spacer="    "        
    cmds.text(label=spacer+'Export Type:', align='right')   
     
    exportRadio = cmds.radioButtonGrp(
        labelArray2=['FBX', 'OBJ'],
        numberOfRadioButtons=2,
        annotation="The type of exported file.",        
        select=0
    )
    
    exportCol = cmds.rowColumnLayout(
        numberOfColumns=3,
        columnAttach=([1, 'right', 5], [2, 'left', 5], [3, 'left', 5]),
        parent=mainLayout
    )
    
    cmds.text(label=spacer+'Export Path:', align='right')
    exportPathField = cmds.textField(width=210)
    if cmds.optionVar(exists=exportPath_OPTIONVAR):
        savedPath = cmds.optionVar(query=exportPath_OPTIONVAR)
        cmds.textField(exportPathField, edit=True, text=savedPath)
    
    cmds.button(
        label="Browse...",
        command=lambda *args: browseForFolder(exportPathField)
    )
    
    #Start Export  
    cmds.button(
        label="Export Objects", parent= mainLayout, annotation="Object and folder selected: export the object to the given folder.", 
        command=lambda *args: exportObjects(exportPathField, pivotRadio, checkBoxes, exportRadio)
    )          
    cmds.separator(height=8, style="in", parent=mainLayout)   
          
    cmds.showWindow(windowName)
    
#main
createWindow()