import maya.cmds as cmds

###############################################################
##################### CONTROL CREATION ########################
###############################################################


######## FUNCTION TO CHANGE THE COLOUR OF A NURBS CONTROL ########
## This function is used it change a nurbs circle (control) to a new colour.

## It takes a circle as well a given specific colour to apply.
def changeColour(providedCircle, colourValues):
    shapeNode = cmds.listRelatives(providedCircle, shapes=True,  fullPath=True)[0]
    print(shapeNode)
    cmds.setAttr(shapeNode+ ".overrideRGBColors", 1)
    cmds.setAttr(shapeNode + ".overrideEnabled", 1)
    cmds.setAttr(shapeNode + ".overrideColorRGB", colourValues[0],colourValues[1],colourValues[2])
    
######## FUNCTION TO CREATE A CIRCULAR CONTROL ########
## This function is used to create a control with a given colour. It does NOT parent anything.

## It takes a joint in order to name the control, a radius, and a colour value specified by the user.
## Returns the created joint control and its group.
## Uses the changeColour helper function.
def createControl(originalJnt, colour, controlSize, controlType, linear):
   
    jntControl = createControlType(originalJnt+"Control", controlSize, controlType, linear)
    
    changeColour(jntControl, colour)
    jntControlGrp = cmds.group(jntControl, name=jntControl+'Grp') 
                 
    return jntControl, jntControlGrp

def createControlType(controlName, controlSize, controlType, linear):
    if controlType == 1:
        newCtrl = createNurbsCube(controlName, controlSize)
    elif controlType == 2:        
        newCtrl = createNurbsArrow(controlName, controlSize)
    elif controlType == 3:
        if (linear):
            newCtrl = cmds.circle(name=controlName, radius=controlSize, nr=(1, 0, 0),degree=1)[0]
        else:
            newCtrl = cmds.circle(name=controlName, radius=controlSize, nr=(1, 0, 0),degree=3)[0]
    return newCtrl
        
######## FUNCTION TO CREATE A SINGLE CONTROL########
## This function is used to create a single control and parents it to the selected joint.
## It allows the user to quickly create a control without needing to create the entire ik fk chain.

## It takes a radius and a colour value specified by the user.
## Uses the createControl helper function.
def createSingleControl(radiusField, controlColour, newControlRadio, linearCheck):
    #'Cube', 'Arrow', 'Circle'
    controlType = cmds.radioButtonGrp(newControlRadio, query=True, select=True)
    controlSize = cmds.intField(radiusField, query=True, value=True)
    linear = cmds.checkBox(linearCheck, query=True, value=True)
    
    selected = cmds.ls(selection=1, type='joint')
    
    if not selected:
        cmds.warning("You need to select a joint.")
    else: 
        jnt = cmds.ls(selection=1, type='joint')[0]   
        jntControl, jntControlGrp = createControl(jnt, controlColour, controlSize, controlType, linear)
        cmds.matchTransform(jntControlGrp, jnt)
        
        if (controlType == 2):
            offsetArrow(1.5, jntControl)    
        cmds.parentConstraint(jntControl, jnt)

def offsetArrow(offset, arrow):
    cmds.move(
        0, offset, 0,
        arrow + ".cv[*]",
        relative=True,
        objectSpace=True
    )
    cmds.rotate(
        0, 90, 0,
        arrow + ".cv[*]",
        relative=True,
        objectSpace=True
    )
######## FUNCTION TO CREATE A CUBE ########
## This function allows you to create a nurbs cube with a given size.
## This is used to create the pole vector.

## It takes a name and size for the cube.
## Returns the created cube.    
def createNurbsCube(name, size):
    s = size

    points = [
        (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s), (-s, -s, -s),
        (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s), (-s, -s, s),
        (-s, -s, -s), (s, -s, -s), (s, -s, s), (s, s, s),
        (s, s, -s), (-s, s, -s), (-s, s, s)
    ]
    createdCube = cmds.curve(name=name, d=1, p=points)
    return createdCube    

def createNurbsArrow(name, size):
    s = size
    offsetY = -0.5 * s
    basePoints = [
        (0, 0, 0), (-2,2,0), (-1,2,0), (-1,6,0), (1,6,0), (1,2,0), (2,2,0), (0,0,0)
    ]
    scaledPoints = []
    
    for x, y, z in basePoints:
        scaledPoint = (
            x * size / 6,
            y * size / 6 + offsetY,
            z * size / 6
        )
        scaledPoints.append(scaledPoint)
    
    createdArrow = cmds.curve(name=name, d=1, p=scaledPoints)
    return createdArrow  
    
def isControl(obj):
    shapes = cmds.listRelatives(obj, shapes=True) or []
    return any(cmds.nodeType(shape) == "nurbsCurve" for shape in shapes)
    
def swapControlShape(radiusField, controlColour, newControlRadio, linearCheck):
    #'Cube', 'Arrow', 'Circle'
    swapControlResults = cmds.radioButtonGrp(newControlRadio, query=True, select=True)
    controlSize = cmds.intField(radiusField, query=True, value=True)
    linear = cmds.checkBox(linearCheck, query=True, value=True)
           
    controls = []
    selected = cmds.ls(selection=True)
    for obj in selected:
        if isControl(obj):
            controls.append(obj)
    
    if not controls:
        cmds.warning("You need to select a control")
        return     
   
    for con in controls:
        newCtrl = createControlType("tempSwapCtrl", controlSize, swapControlResults, linear)     
        changeColour(newCtrl, controlColour)
    
        # Get shapes
        newShape = cmds.listRelatives(newCtrl, shapes=True, fullPath=True)[0]
        oldShapes = cmds.listRelatives(con, shapes=True, fullPath=True) or []
        
        # Parent new shape under ctrl
        cmds.parent(newShape, con, shape=True, relative=True)
    
        # Re-query the newly parented shape
        newShape = cmds.listRelatives(
            con,
            shapes=True,
            fullPath=True
        )[-1]
    
        if (swapControlResults == 2):
            offsetArrow(1.5, newShape)
            
                 
        # Delete old shapes
        for shape in oldShapes:
            cmds.delete(shape)
        
        # Delete temp transform
        cmds.delete(newCtrl)
  
## Uses newColourSwatch, createSingleControl, ikFkMatcher, and createIkFk
def createWindow():
    # Create Window  
    windowName = "ikFk_Creator"
    print (windowName)
    
    #Removes Current Window (If There Is One Already Up)
    if cmds.window(windowName, exists=True):
        cmds.deleteUI(windowName)
    
    windowWidth = 275
    windowHeight = 400 
    cmds.window(windowName, title=windowName, widthHeight=(windowWidth, windowHeight), sizeable=False)  
    
    mainLayout = cmds.columnLayout( adjustableColumn=True )    
    cmds.separator(height=8, style="in", parent=mainLayout)       
    ####### CONTROL SETTINGS #######    
    controlSettingsFrame = cmds.frameLayout(
        label="Control Settings",
        collapsable=False,
        marginWidth=8,
        marginHeight=3,
        parent=mainLayout
    )
    
    exportCol = cmds.rowColumnLayout(
        numberOfColumns=2,
        columnAttach=([1, 'right', 70], [2, 'left', 5]),
        parent=mainLayout
    )
          
    cmds.text(label='Control Size:', align='right', annotation="The size of the controls for the joints.")
    radiusField = cmds.intField(width=40, value = 1)
   
    cmds.text(label='Control Colour:', align='right')
    controlColour = (0.05, 0, 0.6)
    
    colourCanvas01 = cmds.canvas(
        width=40,
        rgbValue=controlColour,
        annotation="The colour for the normal controls.",
        pressCommand=lambda *args: newColourSwatch(colourCanvas01, savedCol)
    )
    
    ikFkMatcherCol = cmds.rowColumnLayout(
        numberOfColumns=2,
        columnAttach=([1, 'right', 83], [2, 'left', 5]),
        parent=mainLayout
    )
    cmds.text(label='     Linear Circle:', align='right')   
    linearCheck = cmds.checkBox(label = "")
    
    spacer="                        "            

    savedCol = [controlColour]
      
    ikFkMatcherCol = cmds.rowColumnLayout(
        numberOfColumns=3,
        columnAttach=([1, 'right', 5], [2, 'left', 5], [3, 'left', 5]),
        parent=mainLayout
    )
    cmds.text(label='    Control Type:', align='right')   
     
    newControlRadio = cmds.radioButtonGrp(
        labelArray3=['Cube', 'Arrow', 'Circle'],
        annotation="Matches the arm from the first argument to the second argument.",
        numberOfRadioButtons=3,
        select=0,
        columnWidth=([1,55], [2,60], [3,50]),
    )
                    
    cmds.button(
        label="Create Single Control", parent= mainLayout, annotation="Select a joint: create a control for it and parent it to the joint.",
        command=lambda *args: createSingleControl(radiusField, savedCol[0], newControlRadio, linearCheck)
    )   
    cmds.text(label="",parent= mainLayout)
    
    ####### MOVEMENT/ROTATION #######
    cmds.separator(height=8, style="in", parent=mainLayout)    
    IkFkMatcherFrame = cmds.frameLayout(
        label="Control Manipulation",
        collapsable=False,
        marginWidth=8,
        marginHeight=3,
        parent=mainLayout
    )

    exportCol = cmds.rowColumnLayout(
        numberOfColumns=7,
        columnAttach=([1, 'right', 20],[2, 'right', 3], [3, 'right', 20],[4, 'right', 3], [5, 'right', 20],[6, 'right', 3], [7, 'right', 20]),
        parent=mainLayout
    )
    
    cmds.text(label='Translate:', align='right', annotation="The size of the controls for the joints.")
    cmds.text(label='X:', align='right', annotation="The size of the controls for the joints.")
    translateXField = cmds.intField(width=40, value = 0)
    cmds.text(label='Y:', align='right', annotation="The size of the controls for the joints.")
    translateYField = cmds.intField(width=40, value = 0)
    cmds.text(label='Z:', align='right', annotation="The size of the controls for the joints.")
    translateZField = cmds.intField(width=40, value = 0)
    translateFields = {
        "x":translateXField,
        "y":translateYField,
        "z":translateZField
    }
        
    cmds.text(label='Rotation:', align='right', annotation="The size of the controls for the joints.")
    cmds.text(label='X:', align='right', annotation="The size of the controls for the joints.")
    rotateXField = cmds.intField(width=40, value = 0)
    cmds.text(label='Y:', align='right', annotation="The size of the controls for the joints.")
    rotateYField = cmds.intField(width=40, value = 0)
    cmds.text(label='Z:', align='right', annotation="The size of the controls for the joints.")
    rotateZField = cmds.intField(width=40, value = 0)
    rotationFields = {
        "x":rotateXField,
        "y":rotateYField,
        "z":rotateZField
    }

    cmds.text(label='Scale:', align='right', annotation="The size of the controls for the joints.")
    cmds.text(label='X:', align='right', annotation="The size of the controls for the joints.")
    scaleXField = cmds.intField(width=40, value = 1)
    cmds.text(label='Y:', align='right', annotation="The size of the controls for the joints.")
    scaleYField = cmds.intField(width=40, value = 1)
    cmds.text(label='Z:', align='right', annotation="The size of the controls for the joints.")
    scaleZField = cmds.intField(width=40, value = 1)
    scaleFields = {
        "x":scaleXField,
        "y":scaleYField,
        "z":scaleZField
    }
    
    exportCol = cmds.rowColumnLayout(
        numberOfColumns=7,
        columnAttach=([1, 'right', 20],[2, 'right', 16], [3, 'right', 35],[4, 'right', 16], [5, 'right', 35],[6, 'right', 16], [7, 'right', 35]),
        parent=mainLayout
    )      
    cmds.text(label="    Mirror:", align='right', annotation="The size of the controls for the joints.")
    cmds.text(label='X:', align='right')    
    mirrorXCheckBox = cmds.checkBox(label="",annotation="")
    
    cmds.text(label='Y:', align='right')    
    mirrorYCheckBox = cmds.checkBox(label="",annotation="")

    cmds.text(label='Z:', align='right')    
    mirrorZCheckBox = cmds.checkBox(label="",annotation="")
        
    mirrorFields = {
        "x":mirrorXCheckBox,
        "y":mirrorYCheckBox,
        "z":mirrorZCheckBox
    }
                    
    fk_to_ik_button = cmds.button(label='Transform Shape', parent=mainLayout, annotation="Select created the switch: Match the pose between IK and FK.",
                command=lambda *args: transformShape(translateFields, rotationFields, scaleFields, mirrorFields))
                
    cmds.text(label="",parent= mainLayout)       
    
    
    ####### IKFK MATCHER #######
    cmds.separator(height=8, style="in", parent=mainLayout)    
    IkFkMatcherFrame = cmds.frameLayout(
        label="IK/FK Matcher",
        collapsable=False,
        marginWidth=8,
        marginHeight=3,
        parent=mainLayout
    )

    fk_to_ik_button = cmds.button(label='Change Shape', parent=mainLayout, annotation="Select created the switch: Match the pose between IK and FK.",
                command=lambda *args: swapControlShape(radiusField, savedCol[0], newControlRadio, linearCheck))
                               
    cmds.text(label="",parent= mainLayout)
    
   
    cmds.showWindow(windowName)    
    
def transformShape(translateFields, rotationFields, scaleFields, mirrorFields):
    translateValues = {
        "x":cmds.intField(translateFields["x"], query=True, value=True),
        "y":cmds.intField(translateFields["y"], query=True, value=True),  
        "z":cmds.intField(translateFields["z"], query=True, value=True)  
    }
    
    rotationValues = {
        "x":cmds.intField(rotationFields["x"], query=True, value=True),
        "y":cmds.intField(rotationFields["y"], query=True, value=True),  
        "z":cmds.intField(rotationFields["z"], query=True, value=True)  
    }
    
    scaleValues = {
        "x":cmds.intField(scaleFields["x"], query=True, value=True),
        "y":cmds.intField(scaleFields["y"], query=True, value=True),  
        "z":cmds.intField(scaleFields["z"], query=True, value=True)  
    }

    mirrorXResult = 1
    mirrorYResult = 1
    mirrorZResult = 1
    if(cmds.checkBox(mirrorFields["x"], query=True, value=True)):
        mirrorXResult = -1
    if(cmds.checkBox(mirrorFields["y"], query=True, value=True)):
        mirrorYResult = -1
    if(cmds.checkBox(mirrorFields["z"], query=True, value=True)):
        mirrorZResult = -1                
    
    mirrorValues = {
        "x":mirrorXResult,
        "y":mirrorYResult,
        "z":mirrorZResult                
    }
        
    if scaleValues["x"] == 0 or scaleValues["y"] == 0 or scaleValues["z"] == 0:
        cmds.warning("The scale of a control cannot be 0.")
        return
             
    controls = []
    selected = cmds.ls(selection=True)
    for obj in selected:
        if isControl(obj):
            controls.append(obj)
    
    if not controls:
        cmds.warning("You need to select a control.")
        return

    for con in controls:
        oldShapes = cmds.listRelatives(con, shapes=True, fullPath=True) or []
        for shape in oldShapes:
            scaleShape(shape,scaleValues["x"],scaleValues["y"],scaleValues["z"], "center") 
            rotateShape(shape,rotationValues["x"],rotationValues["y"],rotationValues["z"])
            moveShape(shape,translateValues["x"],translateValues["y"],translateValues["z"])
            scaleShape(shape,mirrorValues["x"],mirrorValues["y"],mirrorValues["z"], "none") 
                          

def getShapeCenter(shape):
    cvs = cmds.ls(shape + ".cv[*]", flatten=True)

    positions = [cmds.pointPosition(cv, world=True) for cv in cvs]

    avgX = sum(p[0] for p in positions) / len(positions)
    avgY = sum(p[1] for p in positions) / len(positions)
    avgZ = sum(p[2] for p in positions) / len(positions)

    return (avgX, avgY, avgZ)
        

def scaleShape(shapeNode, x, y, z, type):
    if (type=="center"):
        center = getShapeCenter(shapeNode)
        cmds.scale(
            x, y, z,
            shapeNode + ".cv[*]",
            relative=True,
            objectSpace=True,
            pivot=center
        )
    else:
        cmds.scale(
            x, y, z,
            shapeNode + ".cv[*]",
            relative=True,
            objectSpace=True,
        )                
            
def rotateShape(shapeNode, x, y, z):
    center = getShapeCenter(shapeNode)
    cmds.rotate(
        x, y, z,
        shapeNode + ".cv[*]",
        relative=True,
        objectSpace=True,
        pivot=center  
    )
    
def moveShape(shapeNode, x, y, z):
    cmds.move(
        x, y, z,
        shapeNode + ".cv[*]",
        relative=True,
        objectSpace=True
    )           
######## FUNCTION TO APPLY A NEW COLOUR TO THE CANVAS ########
## This function opens the colour editor and stores the result in the colour dictionary.

## Takes a canvas to apply the colour to, as well as a dictionary and its key to apply the values to.                            
def newColourSwatch(inputCanvas, savedCol):
    cmds.colorEditor()
    
    if cmds.colorEditor(query=True, result=True):
        values = cmds.colorEditor(query=True, rgb=True)
        
        cmds.canvas(inputCanvas, edit=True, rgbValue=values)
        savedCol[0] = values
         
#main
createWindow()