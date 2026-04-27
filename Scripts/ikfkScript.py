
import maya.cmds as cmds

def createSingleControl(radiusField, colour):
    controlSize = cmds.intField(radiusField, query=True, value=True)
    selected = cmds.ls(selection=1, type='joint')
    if not selected:
        cmds.warning("You need to select a joint.")
    else: 
        jnt = cmds.ls(selection=1, type='joint')[0]   
        jntControl, jntControlGrp = createControl(jnt, colour, controlSize)
        cmds.matchTransform(jntControlGrp, jnt)
        cmds.parentConstraint(jntControl, jnt)
           

def createControl(originalJnt, colour, controlSize):
    jntControl = cmds.circle(name=originalJnt+'Control', radius=controlSize, nr=(1, 0, 0))[0]    
    changeColour(jntControl, colour)
    jntControlGrp = cmds.group(jntControl, name=jntControl+'Grp') 
    return jntControl, jntControlGrp
        
def createIkFk(radiusField, basicColourValues, switchColourValues):
    controlSize = cmds.intField(radiusField, query=True, value=True)
    selected = cmds.ls(selection=1, type='joint')
    if not selected:
        cmds.warning("You need to select a joint.")
    else:           
        # Select the wrist joint (in a list to avoid error if there arent enough parent objects)
        
        wristJnt = cmds.ls(selection=1, type='joint')[0]
        wristPos = cmds.getAttr(f'{wristJnt}.translateX')
        
        # Select the wrist joint (in a list to avoid error if there arent enough parent objects)
        
        elbowJnt = cmds.listRelatives(wristJnt, parent=1)
        
        # Select the wrist joint (in a list to avoid error if there arent enough parent objects)
        
        shoulderJnt = cmds.listRelatives(elbowJnt, parent=1)
    
        # Select the wrist joint (in a list to avoid error if there arent enough parent objects)
        
        clavicleJnt = cmds.listRelatives(shoulderJnt, parent=1)
    
        # Duplicate arm for FK
        
        if clavicleJnt == None:
            cmds.warning("You must have 3 parent joints")
        else:          
            # Get the selected joints and remove them from their respected lists
            
            elbowJnt = elbowJnt[0]
            shoulderJnt = shoulderJnt[0]
            
            originalJnts = [wristJnt, elbowJnt, shoulderJnt]
            
            fkJnts, fkControls = createFK(originalJnts, wristPos, controlSize, basicColourValues)
            
            ikJnts, ikControls, offsetLctr, ikHandle = createIK(originalJnts, wristPos, fkControls, controlSize, basicColourValues)
            
            ikFkSwitchControl = createSwitch(originalJnts, wristPos, ikJnts, fkJnts, controlSize, switchColourValues)          
                      
            applySkinning(originalJnts, ikFkSwitchControl)  
            # Drive the visibility of the fk and ik controls with the switch control
    
            # When in Fk mode (switch attr = 0), hide ik controls  
            
            setupVisibility(ikControls, fkControls, ikFkSwitchControl)
            
# Hide the ik/fk joints
            
            #sets the axis, attributes, and visibility
            
            axis = ('x', 'y', 'z')
            attributes = ('t', 'r', 's')
            visibility = ('v')
            
            # Creates a list of all joints / controls
            combinedList = [ikJnts, fkJnts]
            ikFkJnts = [item for innerList in combinedList for item in innerList]
            ikFkJnts.append(offsetLctr)
            
            # Turns off the jnts visibility and locks/hides them
            
            for jnts in ikFkJnts:   
                for vis in visibility:   
                    cmds.setAttr (jnts+'.'+vis, 0)
                    cmds.setAttr (jnts+'.'+vis, lock=1, keyable=0)
                
            # Hide the ik handle
            
            cmds.setAttr (ikHandle+'.visibility', 0)
            
            # Locks/hides specific controls attributes
            
            for ax in axis:
                for at in attributes:
                    for vis in visibility:
                            cmds.setAttr(ikFkSwitchControl+'.'+at+ax, lock=1, keyable=0)
                            cmds.setAttr(ikFkSwitchControl+'.'+vis, lock=1, keyable=0)

def createFK(originalJnts, wristPos, controlSize, basicColourValues):    
    # The duplication station starts here
    #originalJnts[wrist, elbow, shoulder]
    shoulderFk = cmds.duplicate(originalJnts[2], name=originalJnts[2]+'Fk', renameChildren=1)    
    shoulderFkRelatives = cmds.listRelatives(shoulderFk, allDescendents=1)
    shoulderFkJnt = (shoulderFk)[0]
    
    # Get the duplicated elbow/ wrist joints        
    elbowFkJnt = cmds.listRelatives(shoulderFk, children=1)[0]
    wristFkJnt = cmds.listRelatives(shoulderFk, children=1)[1]
    
    # Renames the new joints

    if shoulderFkRelatives:
        if elbowFkJnt:
            shoulderFkRelatives.remove(elbowFkJnt)
            elbowFkJnt = cmds.rename (elbowFkJnt, originalJnts[1]+'Fk')
        if wristFkJnt:    
            shoulderFkRelatives.remove(wristFkJnt)
            wristFkJnt = cmds.rename (wristFkJnt, originalJnts[0]+'Fk')
   
        # Delete all extra joints that arent  the elbow and wrist
        
    if shoulderFkRelatives:
        cmds.delete(shoulderFkRelatives)

    # Build fk controls
        
    # Creates circles and groups them
    shoulderFkControl, shoulderFkControlGrp = createControl(shoulderFkJnt, basicColourValues, controlSize)
    elbowFkControl, elbowFkControlGrp = createControl(elbowFkJnt, basicColourValues, controlSize)    
    wristFkControl, wristFkControlGrp = createControl(wristFkJnt, basicColourValues, controlSize)             
    
    # Match the groups transforms to the joints
    
    cmds.matchTransform(shoulderFkControlGrp, shoulderFkJnt)
    cmds.matchTransform(elbowFkControlGrp, elbowFkJnt)
    cmds.matchTransform(wristFkControlGrp, wristFkJnt)
    
    # Parents the controls to the jnts
            
    cmds.parentConstraint(shoulderFkControl, shoulderFkJnt)
    cmds.parentConstraint(elbowFkControl, elbowFkJnt)
    cmds.parentConstraint(wristFkControl, wristFkJnt)
    
    # Parents the wristCtrl to the elbow and elbow to the shoulder
    
    cmds.parent (wristFkControlGrp, elbowFkControl)
    cmds.parent (elbowFkControlGrp, shoulderFkControl)
    
    fkJnts = [wristFkJnt, elbowFkJnt, shoulderFkJnt]
    fkControls = [elbowFkControl, shoulderFkControl, wristFkControl]
    return fkJnts, fkControls


def createIK(originalJnts, wristPos, fkControls, controlSize, basicColourValues):    
    # Duplicate arm for IK.
 
    # The duplication station starts here
    
    shoulderIk = cmds.duplicate(originalJnts[2], name=originalJnts[2]+'Ik', renameChildren=1)    
    shoulderIkRelatives = cmds.listRelatives(shoulderIk, allDescendents=1)
    shoulderIkJnt = (shoulderIk)[0]
        
    # Get the duplicated elbow/ wrist joints
    elbowIkJnt = cmds.listRelatives(shoulderIk, children=1)[0]
    wristIkJnt = cmds.listRelatives(shoulderIk, children=1)[1]

  
    # Renames the new joints
    
    if shoulderIkRelatives:
        if elbowIkJnt:    
            shoulderIkRelatives.remove(elbowIkJnt)
            elbowIkJnt = cmds.rename (elbowIkJnt, originalJnts[1]+'Ik')
        if wristIkJnt:    
            shoulderIkRelatives.remove(wristIkJnt)
            wristIkJnt = cmds.rename (wristIkJnt, originalJnts[0]+'Ik')
       
        # Delete all extra joints that arent  the elbow and wrist


    if shoulderIkRelatives:
        cmds.delete(shoulderIkRelatives)
        
    # Create an ikHandle and parent it to the wrist control
    
    ikHandle = cmds.ikHandle(startJoint=shoulderIkJnt, endEffector=wristIkJnt, sol='ikRPsolver', name=originalJnts[0]+'IkHandle')[0]
    
    # Creates a circle and groups it    
    wristIkControl, wristIkControlGrp = createControl(wristIkJnt, basicColourValues, controlSize)
       
    # Match the groups transforms to the joints
    
    cmds.matchTransform(wristIkControlGrp, wristIkJnt)  

    # Parents the ikHandle to the wrist control
        
    cmds.parent (ikHandle, wristIkControl)
   
    # Orients the wrist control to the wristIkJnt
    
    cmds.orientConstraint(wristIkControl, wristIkJnt)
   
    # create an elbow ik control and create pole vector constraint
    
    # Creates a circle and groups it
    elbowIkControl, elbowIkControlGrp = createControl(elbowIkJnt, basicColourValues, controlSize)          
    
    # Match the groups transforms to the joints
    
    cmds.matchTransform(elbowIkControlGrp, elbowIkJnt) 

    # Find the new location of the elbow control
    
    elbowDistance = (-2/3)
    
    elbowDistanceZ = wristPos * (elbowDistance)
    
    cmds.move(0,0,elbowDistanceZ, elbowIkControlGrp, relative=1, objectSpace=1)       
    # Create the pole vector contstraint

    cmds.poleVectorConstraint(elbowIkControl, ikHandle)
   
    # Crates a ik offset locator
    
    offsetLctr = cmds.spaceLocator(name=('ikOffsetLocator'))[0]
    offsetLctrCounterGrp = cmds.group(offsetLctr, name=offsetLctr+'counterGrp')
    offsetLctrGrp = cmds.group(offsetLctrCounterGrp, name=offsetLctr+'Grp')
    
    # Match the transforms and parent the group
    cmds.matchTransform(offsetLctrGrp, originalJnts[1])
    cmds.parent(offsetLctrGrp, fkControls[1])

    # Have the counter group rotate 50% in the opposite direction of the elbow fk con
    
    offsetLctrMd = cmds.shadingNode('multiplyDivide', name=offsetLctr+'CounterMultiplyDivide', asUtility=True)
    cmds.setAttr(offsetLctrMd+'.input2', -0.5, -0.5, -0.5)
    cmds.connectAttr(fkControls[1]+'.rotate', offsetLctrMd+'.input1')
    cmds.connectAttr(offsetLctrMd+'.output', offsetLctrCounterGrp+'.rotate')
        
    # Move the locator to the elbow ik con
    
    cmds.matchTransform(offsetLctr, elbowIkControl)
    ikJnts = [wristIkJnt, elbowIkJnt, shoulderIkJnt]
    ikControls = [elbowIkControl, wristIkControl]        
    return ikJnts, ikControls, offsetLctr, ikHandle


def createSwitch(originalJnts, wristPos, ikJnts, fkJnts, controlSize, switchColourValues):
    # Create the Ik/Fk Switch control and group it
    
    ikFkSwitchDistance = (-2/3)
    ikFkSwitchControlZ = wristPos * ikFkSwitchDistance
    ikFkSwitchControl = cmds.circle(degree=1, name=originalJnts[0]+'IkFkSwitchControl', radius = controlSize)[0]
    ikFkSwitchControlGrp = cmds.group(ikFkSwitchControl, name=ikFkSwitchControl+'Grp')
    changeColour(ikFkSwitchControl, switchColourValues)
    
    # Match the groups transforms to the joints
    
    cmds.matchTransform(ikFkSwitchControlGrp, ikJnts[0])

    cmds.move(0,0,ikFkSwitchControlZ, ikFkSwitchControl, relative=1, objectSpace=1)
    cmds.makeIdentity (ikFkSwitchControl, apply=1, translate=1, rotate=1, scale=1, normal=0, preserveNormals=1)
    
    # Add a custom attribute
    
    cmds.addAttr(ikFkSwitchControl, keyable=1, longName='ikFkSwitch', defaultValue=1.0, minValue=0.0, maxValue=1.0, attributeType='float')
    return ikFkSwitchControl

def setupVisibility(ikControls, fkControls, ikFkSwitchControl):

    # Create condition node

    fkVisCondition = cmds.shadingNode('condition', name=('fkVisCondition'), asUtility=1)
    
    # Connect the ikFk Switch attributes to IK vis conditions firstTerm
    
    cmds.connectAttr(ikFkSwitchControl+'.ikFkSwitch', fkVisCondition+'.firstTerm', force=1) 
    
    # Connect fk Vis Condition's outColor to fk wrist/elbow visibility
    
    cmds.connectAttr(fkVisCondition+'.outColor.outColorR', ikControls[1]+'.visibility', force=1) 
    cmds.connectAttr(fkVisCondition+'.outColor.outColorR', ikControls[0]+'.visibility', force=1) 
    
    # When in Ik mode (switch attr = 1), hide fk controls  
    
    # Create condition node
    
    ikVisCondition = cmds.shadingNode('condition', name=('ikVisCondition'), asUtility=1)
    
    # Connect the IkFkSwitch attr to FK Vis condition's first Term
    
    cmds.connectAttr(ikFkSwitchControl+'.ikFkSwitch', ikVisCondition+'.firstTerm', force=1) 
    
    # Sets the ik condition's second term to be 1
            
    cmds.setAttr (ikVisCondition+'.secondTerm', 1)
    
    # Connect Ik Vis Condition's outColorR to fk vis
    
    cmds.connectAttr(ikVisCondition+'.outColor.outColorR', fkControls[2]+'.visibility', force=1) 
    cmds.connectAttr(ikVisCondition+'.outColor.outColorR', fkControls[1]+'.visibility', force=1) 
    cmds.connectAttr(ikVisCondition+'.outColor.outColorR', fkControls[0]+'.visibility', force=1) 

def applySkinning(originalJnts, ikFkSwitchControl):
  # Connect the rotations of the IK and FK joints to the skinning joint
    for jnts in (originalJnts):
    
        # Create a pairBlend node
        ikFkBlend = cmds.shadingNode('pairBlend', name=(jnts+'PairBlend'), asUtility=1)

        # Connect fk joints rotate and translate to pairBlends in rotate1/inTranslate1

        cmds.connectAttr(jnts+'Fk.rotate', ikFkBlend+'.inRotate1', force=1)
        cmds.connectAttr(jnts+'Fk.translate', ikFkBlend+'.inTranslate1', force=1)
                
        # Connect ik joints rotate and translate to pairBlends in rotate2/inTranslate2
        
        cmds.connectAttr(jnts+'Ik.rotate', ikFkBlend+'.inRotate2', force=1)
        cmds.connectAttr(jnts+'Ik.translate', ikFkBlend+'.inTranslate2', force=1)        
    
        # connect ik/fk switch ctrls switch channel to the pairBlends weight attribute
        
        cmds.connectAttr(ikFkSwitchControl+'.ikFkSwitch', ikFkBlend+'.weight', force=1)                   
    
        # Connect pairBlends outRotate/outTranslate to the skinning joints rotate and translate

        cmds.connectAttr(ikFkBlend+'.outRotate', jnts+'.rotate', force=1)
        cmds.connectAttr(ikFkBlend+'.outTranslate', jnts+'.translate', force=1)           

        # Connect scale using a blend channel node
        
        ikFkColours = cmds.shadingNode('blendColors', name=(jnts+'BlendColours'), asUtility=1)
        
        # Connect fk scale to blendColours color 1, ik scale to color 2
        
        cmds.connectAttr(jnts+'Fk.scale', ikFkColours+'.color1', force=1)
        cmds.connectAttr(jnts+'Ik.scale', ikFkColours+'.color2', force=1)

        # Connect the ikFkSwitch ctrl attribute to the blendColors blender
        cmds.connectAttr(ikFkSwitchControl+'.ikFkSwitch', ikFkColours+'.blender', force=1) 
            
        # Connect the blend Colors output to skinning joint scale
 
        cmds.connectAttr(ikFkColours+'.output', jnts+'.scale', force=1)      
                                                     
def changeColour(circleName, colourValues):
    shapeNode = cmds.listRelatives(circleName, shapes=True)[0]
    cmds.setAttr(shapeNode+ ".overrideRGBColors", 1)
    cmds.setAttr(shapeNode + ".overrideEnabled", 1)
    cmds.setAttr(shapeNode + ".overrideColorRGB", colourValues[0],colourValues[1],colourValues[2])

def newColourSwatch(canvas):
    cmds.colorEditor()
    
    if cmds.colorEditor(query=True, result=True):
        values = cmds.colorEditor(query=True, rgb=True)
        
        # Update the canvas color
        cmds.canvas(canvas, edit=True, rgbValue=values)
        
        return values
        
########FUNCTION TO CREATE THE WINDOW#######
## This function creates a window and calls the functions above
def createWindow():
    # Create Window  
    windowName = "ikFk_Creator"
    print (windowName)
    
    #Removes Current Window (If There Is One Already Up)
    if cmds.window(windowName, exists=True):
        cmds.deleteUI(windowName)
    
    windowWidth = 275
    windowHeight = 300 
    cmds.window(windowName, title=windowName, widthHeight=(windowWidth, windowHeight), sizeable=False)  
    
    #Creates The Window
    mainLayout = cmds.columnLayout( adjustableColumn=True )    
    
    #######EXPORT PATH#######
    cmds.separator(height=8, style="in", parent=mainLayout)
    
    exportFrame = cmds.frameLayout(
        label="Controls",
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
    
    cmds.text(label='  Control Size:', align='right')
    radiusField = cmds.intField(width=40, value = 1)
       
    cmds.text(label='  Control Colour:', align='right')
    basicColourValues = (0, 0, 0.5)    
    colourCanvas01  = cmds.canvas(width=40, rgbValue=(basicColourValues), pressCommand=lambda *args: newColourSwatch(colourCanvas01))
    
    cmds.text(label='  Control SwitchColour:', align='right')
    switchColourValues = (0, 0.7, 0)
    colourCanvas02  = cmds.canvas(width=40, rgbValue=(switchColourValues), pressCommand=lambda *args: newColourSwatch(colourCanvas02))
    
    cmds.button(
        label="Create Single Control", parent= mainLayout,
        command=lambda *args: createSingleControl(radiusField, basicColourValues)
    )   
    
    cmds.separator(height=8, style="in", parent=mainLayout)        
    cmds.button(
        label="Create IK FK", parent= mainLayout,
        command=lambda *args: createIkFk(radiusField, basicColourValues, switchColourValues)
    )          
      
    cmds.showWindow(windowName)

#main
createWindow()