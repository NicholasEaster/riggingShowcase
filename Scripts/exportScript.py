import maya.cmds as cmds
import os

EXPORT_PATH_OPTIONVAR = "OBJExporter_LastExportPath"

########FUNCTION TO CHANGE A PIVOT#######
## Calls changePivotHelper
def changePivot(pivotRadio):
    pivotResults = cmds.radioButtonGrp(pivotRadio, query=True, select=True)
    sel = cmds.ls(selection=True, long=True)
    
    print(pivotResults)
    if not sel:
        cmds.warning('No objects were selected')
        return
        
    for selectedObjects in sel:
        obj_name = selectedObjects.split("|")[-1] #This is needed because the default is Parent name|child name. 
        changePivotHelper(pivotResults, obj_name)
    
    return
    
########FUNCTION TO HELP CHANGE A PIVOT#######
## This function works on a specific object provided 
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
        y = bbox[1]
        z = (bbox[2] + bbox[5]) / 2.0
        cmds.move(x, y, z, object+".scalePivot", object+".rotatePivot", absolute=True) #Move the pivot the the bottom center
    
    return

########FUNCTION TO CHECK MODEL GEOMETRY#######
## Calls checkGEOHelper
def checkGEO(checkBoxes):               
    sel = cmds.ls(selection=True, long=True)
    
    #print(pivotResults)
    if not sel:
        cmds.warning('No objects were selected')
        return
        
    for selectedObjects in sel:
        obj_name = selectedObjects.split("|")[-1] #This is needed because the default is Parent name|child name. 
        checkGEOHelper(checkBoxes, obj_name)
    
    return

########FUNCTION TO HELP CHECK GEO#######
## This function works on a specific object provided 
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

            
########FUNCTION TO EXPORT #######
## This function requires a export path and pivot radio to query
def export_Objects(filePath, pivotRadio, checkBoxes):
    export_path = cmds.textField(filePath, query=True, text=True)
    pivotResults = cmds.radioButtonGrp(pivotRadio, query=True, select=True)    
        
    ########PRELIMINARY CHECKS#######
    if not export_path:
        cmds.warning("Please select an export directory.")
        return
            
    sel = cmds.ls(selection=True, long=True)
    if not sel:
        cmds.warning('No objects were selected')
        return

    invalidObjects = {} #Check for invalid objects
    for selectedObjects in sel:
        obj_name = selectedObjects.split("|")[-1]
        issues = checkGEOHelper(checkBoxes, obj_name, "validate")

        if issues:
            invalidObjects[obj_name] = issues

    if invalidObjects:
        cmds.warning("Export aborted: geometry issues detected.")
        return
                
    for selectedObjects in sel:
        ##Create the duplicate and transfer the name
        obj_name = selectedObjects.split("|")[-1] #This is needed because the default is Parent name|child name.
        tempRename = cmds.rename(selectedObjects, obj_name + "_")
        duplicate = cmds.duplicate(tempRename, name=obj_name)[0]       
         
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
        export_file = os.path.join(export_path, obj_name + ".fbx")
        
        try:
            cmds.file(
                export_file,
                force=True,
                options="v=0;",
                typ="FBX export",
                exportSelected=True
            )
            print(f"Successfully exported selected objects to: {export_path}")
        except RuntimeError as e:
            print(f"Error during FBX export: {e}")
        
        #######CLEANUP#######
        cmds.delete(duplicate)
        cmds.rename(tempRename, obj_name)
    cmds.optionVar(stringValue=(EXPORT_PATH_OPTIONVAR, export_path))
    
########FUNCTION TO FIND A FOLDER#######
## This function requires a text field and will open a folder browser
def browseForFolder(text_field):
    folder = cmds.fileDialog2(fileMode=3, dialogStyle=2)

    if folder:
        cmds.textField(text_field, edit=True, text=folder[0])
        cmds.optionVar(stringValue=(EXPORT_PATH_OPTIONVAR, folder[0]))

########FUNCTION TO CREATE THE WINDOW#######
## This function creates a window and calls the functions above
def createWindow():
    # Create Window  
    windowName = "OBJ_Exporter"
    print (windowName)
    
    #Removes Current Window (If There Is One Already Up)
    if cmds.window(windowName, exists=True):
        cmds.deleteUI(windowName)
    
    window_width = 400
    window_height = 300 
    cmds.window(windowName, title=windowName, widthHeight=(window_width, window_height), sizeable=False)  
    
    #Creates The Window
    mainLayout = cmds.columnLayout( adjustableColumn=True )    
    
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
        labelArray3=["Bottom Left", "Custom", "Bottom Center"],
        numberOfRadioButtons=3,
        select=2
    )
    
    #Start Pivot
    cmds.button(
        label="Modify Pivot",parent= mainLayout,
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
    numberOfCheckBoxes=4,
    columnWidth4=[100,65,100,100]
    )
    
    #Start Cleanup
    cmds.button(
        label="Check Objects",parent= mainLayout,
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
        numberOfColumns=3,
        columnAttach=([1, 'right', 5], [2, 'left', 5], [3, 'left', 5]),
        parent=mainLayout
    )
    
    cmds.text(label='  Export Path:', align='right')
    exportPathField = cmds.textField(width=210)
    if cmds.optionVar(exists=EXPORT_PATH_OPTIONVAR):
        savedPath = cmds.optionVar(query=EXPORT_PATH_OPTIONVAR)
        cmds.textField(exportPathField, edit=True, text=savedPath)
    
    cmds.button(
        label="Browse...",
        command=lambda *args: browseForFolder(exportPathField)
    )
  
    cmds.button(
        label="Export Objects", parent= mainLayout,
        command=lambda *args: export_Objects(exportPathField, pivotRadio, checkBoxes)
    )          
      
    cmds.showWindow(windowName)
    
#main
createWindow()