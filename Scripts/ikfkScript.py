import maya.cmds as cmds

###############################################################
##################### CONTROL CREATION ########################
###############################################################


######## FUNCTION TO CHANGE THE COLOUR OF A NURBS CONTROL ########
## This function is used it change a nurbs circle (control) to a new colour.

## It takes a circle as well a given specific colour to apply.
def changeColour(providedCircle, colourValues):
    shapeNode = cmds.listRelatives(providedCircle, shapes=True)[0]
    cmds.setAttr(shapeNode+ ".overrideRGBColors", 1)
    cmds.setAttr(shapeNode + ".overrideEnabled", 1)
    cmds.setAttr(shapeNode + ".overrideColorRGB", colourValues[0],colourValues[1],colourValues[2])
    
######## FUNCTION TO CREATE A CIRCULAR CONTROL ########
## This function is used to create a control with a given colour. It does NOT parent anything.

## It takes a joint in order to name the control, a radius, and a colour value specified by the user.
## Returns the created joint control and its group.
## Uses the changeColour helper function.
def createControl(originalJnt, colour, controlSize):
    print(colour)
    jntControl = cmds.circle(name=originalJnt+'Control', radius=controlSize, nr=(1, 0, 0))[0]    
    changeColour(jntControl, colour)
    jntControlGrp = cmds.group(jntControl, name=jntControl+'Grp') 
    return jntControl, jntControlGrp
    
######## FUNCTION TO CREATE A SINGLE CONTROL########
## This function is used to create a single control and parents it to the selected joint.
## It allows the user to quickly create a control without needing to create the entire ik fk chain.

## It takes a radius and a colour value specified by the user.
## Uses the createControl helper function.
def createSingleControl(radiusField, colourValues):
    controlSize = cmds.intField(radiusField, query=True, value=True)
    selected = cmds.ls(selection=1, type='joint')
    
    if not selected:
        cmds.warning("You need to select a joint.")
    else: 
        jnt = cmds.ls(selection=1, type='joint')[0]   
        jntControl, jntControlGrp = createControl(jnt, colourValues["control"], controlSize)
        cmds.matchTransform(jntControlGrp, jnt)
        cmds.parentConstraint(jntControl, jnt)

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


###############################################################
####################### IK FK CREATION ########################
###############################################################


######## FUNCTION TO CREATE THE IKFK ########
## This function creates the IKFK setup by calling individual functions to handle their own portions.
## In order for the function to work, you must select a joint with atleast two parents.
## In this case, it is recommended to select the wrist (which will then use the elbow and the shoulder).

## It takes a radius and a colour value specified by the user.
## Uses the createFK, createIK, createSwitch, applySkinning, setupVisibility, and setupLocking helper functions.      
def createIkFk(radiusField, colourValues):
    basicColour = colourValues["control"]
    switchColour = colourValues["switch"]
    poleColour = colourValues["pole"]
    controlSize = cmds.intField(radiusField, query=True, value=True)
    
    selected = cmds.ls(selection=1, type='joint')
    if not selected:
        cmds.warning("You need to select a joint.")
    else:           
        # Store joints based on selection.
        wristJnt = cmds.ls(selection=1, type='joint')[0]
        wristPos = cmds.getAttr(f'{wristJnt}.translateX')
           
        elbowJnt = cmds.listRelatives(wristJnt, parent=1)           
        shoulderJnt = cmds.listRelatives(elbowJnt, parent=1)
    
        if (shoulderJnt == None):
            cmds.warning("You must have 2 parent joints")
        else:          
            elbowJnt = elbowJnt[0]
            shoulderJnt = shoulderJnt[0]
            
            #Store the joints in a list for easy access.
            originalJnts = [wristJnt, elbowJnt, shoulderJnt]
            
            #Create the fk arm
            fkJnts, fkControls = createFK(originalJnts, wristPos, controlSize, basicColour)
            
            #Create the ik arm
            ikJnts, ikControls, offsetLctr, createdIkHandle = createIK(originalJnts, wristPos, fkControls, controlSize, colourValues)
            
            #Create the switch
            ikFkSwitchControl = createSwitch(originalJnts, wristPos, ikJnts, fkJnts, fkControls, ikControls, offsetLctr, controlSize, switchColour)                                  
            
            #Apply the ik/fk arms to the original arm                                      
            applySkinning(originalJnts, ikFkSwitchControl)  
            
            #Setup the visibility conditions enforced when switching arms.
            setupVisibility(ikControls, fkControls, ikFkSwitchControl)
            
            #Creates a list of all joints and the locator
            combinedList = [ikJnts, fkJnts]
            ikFkJnts = [item for innerList in combinedList for item in innerList]
            ikFkJnts.append(offsetLctr)
            
            #Lock and hide specific attributes
            #setupLocking(ikFkJnts, ikFkSwitchControl, createdIkHandle)           

######## FUNCTION TO CREATE THE FK ARM ########
## This function creates the fk arm, including the controls, constraints and joints.

## It takes a list corresponding to the original joints of the arm, the wrist position, the control sizez and the control colours provided by the user.
## Uses the createControl helper function.
## Returns the created fk controls and joints in a list   
def createFK(originalJnts, wristPos, controlSize, basicColour):    
    
    # The duplication station starts here    
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
   
        # Delete all extra joints that arent the elbow and wrist
        
    if shoulderFkRelatives:
        cmds.delete(shoulderFkRelatives)

    # Build fk controls
        
    # Creates circles and groups them
    shoulderFkControl, shoulderFkControlGrp = createControl(shoulderFkJnt, basicColour, controlSize)
    elbowFkControl, elbowFkControlGrp = createControl(elbowFkJnt, basicColour, controlSize)    
    wristFkControl, wristFkControlGrp = createControl(wristFkJnt, basicColour, controlSize)             
    
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
    fkControls = [wristFkControl, elbowFkControl, shoulderFkControl]
    return fkJnts, fkControls

######## FUNCTION TO CREATE THE IK ARM ########
## This function creates the ik arm, including the controls, constraints, joints, and pole vector.

## It takes a list corresponding to the original joints of the arm, the wrist position, the created fkControls, the control sizez and the control colours provided by the user.
## Uses the createControl helper function.
## Returns the created ik controls and joints in a list   
def createIK(originalJnts, wristPos, fkControls, controlSize, colourValues):    
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
    createdIkHandle = cmds.ikHandle(startJoint=shoulderIkJnt, endEffector=wristIkJnt, sol='ikRPsolver', name=originalJnts[0]+'IkHandle')[0]
    
    # Creates a circle and groups it    
    wristIkControl, wristIkControlGrp = createControl(wristIkJnt, colourValues["control"], controlSize)
       
    # Match the groups transforms to the joints
    cmds.matchTransform(wristIkControlGrp, wristIkJnt)  

    # Parents the ikHandle to the wrist control    
    cmds.parent (createdIkHandle, wristIkControl)
   
    # Orients the wrist control to the wristIkJnt
    cmds.orientConstraint(wristIkControl, wristIkJnt)
   
    # create an elbow ik control and create pole vector constraint
    elbowIkControl = createNurbsCube(elbowIkJnt+'Control', controlSize/3)   
    changeColour(elbowIkControl, colourValues["pole"])
    elbowIkControlGrp = cmds.group(elbowIkControl, name=elbowIkControl+'Grp')  
    
    # Match the groups transforms to the joints
    
    cmds.matchTransform(elbowIkControlGrp, elbowIkJnt) 

    # Find the new location of the elbow control
    elbowDistance = (-2/3)
    elbowDistanceZ = wristPos * (elbowDistance)
    
    cmds.move(0,0,elbowDistanceZ, elbowIkControlGrp, relative=1, objectSpace=1)       
    # Create the pole vector contstraint
    cmds.poleVectorConstraint(elbowIkControl, createdIkHandle)
   
    # Crates an ik offset locator
    offsetLctr = cmds.spaceLocator(name=('ikOffsetLocator'))[0]
    #offsetLctrCounterGrp = cmds.group(offsetLctr, name=offsetLctr+'counterGrp')
    #offsetLctrGrp = cmds.group(offsetLctrCounterGrp, name=offsetLctr+'Grp')
    
    # Match the transforms and parent the group
    #cmds.matchTransform(offsetLctrGrp, originalJnts[1])
    #cmds.parent(offsetLctrGrp, fkControls[1])

    # Have the counter group rotate 50% in the opposite direction of the elbow fk con
    #offsetLctrMd = cmds.shadingNode('multiplyDivide', name=offsetLctr+'CounterMultiplyDivide', asUtility=True)
    #cmds.setAttr(offsetLctrMd+'.input2', -0.5, -0.5, -0.5)
    #cmds.connectAttr(fkControls[1]+'.rotate', offsetLctrMd+'.input1')
    #cmds.connectAttr(offsetLctrMd+'.output', offsetLctrCounterGrp+'.rotate')
        
    # Move the locator to the elbow ik con
    
    cmds.matchTransform(offsetLctr, elbowIkControl)
    ikJnts = [wristIkJnt, elbowIkJnt, shoulderIkJnt]
    ikControls = [wristIkControl, elbowIkControl]        
    return ikJnts, ikControls, offsetLctr, createdIkHandle


def createSwitch(originalJnts, wristPos, ikJnts, fkJnts, fkControls, ikControls, offsetLctr, controlSize, switchColour):
    # Create the Ik/Fk Switch control and group it
    
    ikFkSwitchDistance = (-2/3)
    ikFkSwitchControlZ = wristPos * ikFkSwitchDistance
    ikFkSwitchControl = cmds.circle(degree=1, name=originalJnts[0]+'IkFkSwitchControl', radius = controlSize)[0]
    ikFkSwitchControlGrp = cmds.group(ikFkSwitchControl, name=ikFkSwitchControl+'Grp')
    changeColour(ikFkSwitchControl, switchColour)
    
    # Match the groups transforms to the joints
    
    cmds.matchTransform(ikFkSwitchControlGrp, ikJnts[0])

    cmds.move(0,0,ikFkSwitchControlZ, ikFkSwitchControl, relative=1, objectSpace=1)
    cmds.makeIdentity (ikFkSwitchControl, apply=1, translate=1, rotate=1, scale=1, normal=0, preserveNormals=1)
    
    # Add a custom attribute
    
    cmds.addAttr(ikFkSwitchControl, keyable=1, longName='ikFkSwitch', defaultValue=1.0, minValue=0.0, maxValue=1.0, attributeType='float')    

    #Create a series of attributes in the switch control to allow easy ik/fk matching.
    #The premise is to store the selected joints using attributes to allow the matcher to find the joints without needing to search for them by name.
                            
    #fk Shoulder control
    cmds.addAttr(ikFkSwitchControl, longName="fkShoulderControl", attributeType="message")
    cmds.connectAttr(fkControls[2] + ".message", ikFkSwitchControl + ".fkShoulderControl")
    
    #fk Elbow control
    cmds.addAttr(ikFkSwitchControl, longName="fkElbowControl", attributeType="message")
    cmds.connectAttr(fkControls[1] + ".message", ikFkSwitchControl + ".fkElbowControl")

    #fk Wrist control
    cmds.addAttr(ikFkSwitchControl, longName="fkWristControl", attributeType="message")
    cmds.connectAttr(fkControls[0] + ".message", ikFkSwitchControl + ".fkWristControl")

    #ik Elbow control
    cmds.addAttr(ikFkSwitchControl, longName="ikElbowControl", attributeType="message")
    cmds.connectAttr(ikControls[1] + ".message", ikFkSwitchControl + ".ikElbowControl")   

    #ik Wrist control
    cmds.addAttr(ikFkSwitchControl, longName="ikWristControl", attributeType="message")
    cmds.connectAttr(ikControls[0] + ".message", ikFkSwitchControl + ".ikWristControl")

    #JOINTS:                                                                
    #ik Shoulder joint
    cmds.addAttr(ikFkSwitchControl, longName="ikShoulderJnt", attributeType="message")
    cmds.connectAttr(ikJnts[2] + ".message", ikFkSwitchControl + ".ikShoulderJnt")            

    #ik Elbow joint
    cmds.addAttr(ikFkSwitchControl, longName="ikElbowJnt", attributeType="message")
    cmds.connectAttr(ikJnts[1] + ".message", ikFkSwitchControl + ".ikElbowJnt")           

    #ik Wrist joint
    cmds.addAttr(ikFkSwitchControl, longName="ikWristJnt", attributeType="message")
    cmds.connectAttr(ikJnts[0] + ".message", ikFkSwitchControl + ".ikWristJnt")                                    

    #offset Locator
    cmds.addAttr(ikFkSwitchControl, longName="ikOffsetLocator", attributeType="message")
    cmds.connectAttr(offsetLctr + ".message", ikFkSwitchControl + ".ikOffsetLocator")       
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

def setupLocking(ikFkJnts, ikFkSwitchControl, createdIkHandle):
    #sets the axis, attributes, and visibility
        
    axis = ('x', 'y', 'z')
    attributes = ('r', 's')
    visibility = ('v')    
    
    # Turns off the jnts visibility and locks/hides them
    
    for jnts in ikFkJnts:   
        for vis in visibility:   
            cmds.setAttr (jnts+'.'+vis, 0)
            cmds.setAttr (jnts+'.'+vis, lock=1, keyable=0)
        
    # Hide the ik handle
    
    cmds.setAttr(createdIkHandle+'.visibility', 0)
    
    # Locks/hides specific controls attributes
    
    for ax in axis:
        for at in attributes:
            for vis in visibility:
                    cmds.setAttr(ikFkSwitchControl+'.'+at+ax, lock=1, keyable=0)
                    cmds.setAttr(ikFkSwitchControl+'.'+vis, lock=1, keyable=0)       
                    
def newColourSwatch(canvas, key, colourDict):
    cmds.colorEditor()
    
    if cmds.colorEditor(query=True, result=True):
        values = cmds.colorEditor(query=True, rgb=True)
        
        cmds.canvas(canvas, edit=True, rgbValue=values)
        
        colourDict[key] = values

def get(node_attr):
    con = cmds.listConnections(node_attr)
    if not con:
        cmds.error(f"Missing connection: {node_attr}")
    return con[0]
        
def find_joints():
    switch = cmds.ls(selection=True)[0]
    
    fkWristCtrl = get(switch + ".fkWristControl")    
    fkElbowCtrl = get(switch + ".fkElbowControl")
    fkShoulderCtrl = get(switch + ".fkShoulderControl")

    ikWristCtrl = get(switch + ".ikWristControl")
    ikElbowCtrl = get(switch + ".ikElbowControl")
    
    ikWristJnt = get(switch + ".ikWristJnt")
    ikElbowJnt = get(switch + ".ikElbowJnt")
    ikShoulderJnt = get(switch + ".ikShoulderJnt")

    offsetLctr = get(switch + ".ikOffsetLocator")
    
    listOfJoints = [fkWristCtrl, fkElbowCtrl, fkShoulderCtrl, ikWristJnt, ikElbowJnt, ikShoulderJnt, ikWristCtrl, ikElbowCtrl, offsetLctr, switch]
    return listOfJoints
    
def error_checks():
    # Is something selected?
    selected = cmds.ls(selection=1)
    if selected:
        ik_fk_switch = selected[0]                
        
        # Is it the switch control?       
        ik_fk_switch_attr = list(set(cmds.listAttr(ik_fk_switch)))
        
        for attribute in ik_fk_switch_attr:
            if ('ikFkSwitch') in attribute:
                return True
        else:
            cmds.warning("You need to select the ik_fk_switch_control.")
            return False
    else:
        cmds.warning("You need to select an object.")
        return False           
     
def ikFkMatcher(matchingRadio):       
    if error_checks():        
        #listOfJoints = [fkWristCtrl, fkElbowCtrl, fkShoulderCtrl, ikWristJnt, ikElbowJnt, ikShoulderJnt, ikWristCtrl, ikElbowCtrl, offsetLctr, switch]   
        listOfJoints = find_joints()
        matchingResults = cmds.radioButtonGrp(matchingRadio, query=True, select=True)
        if(matchingResults==1):
            cmds.matchTransform(listOfJoints[2], listOfJoints[5]) #fkShoulderCtrl, ikShoulderJnt
            cmds.matchTransform(listOfJoints[1], listOfJoints[4]) #fkElbowCtrl, ikElbowJnt
            cmds.matchTransform(listOfJoints[0], listOfJoints[3]) #fkWristCtrl, ikWristJnt
            cmds.setAttr(listOfJoints[9]+'.ikFkSwitch', 0) 
        else:       
            listOfJoints = find_joints()          
            cmds.matchTransform(listOfJoints[6], listOfJoints[0]) #ikWristCtrl, fkWristCtrl
            shoulder = listOfJoints[2]
            elbow    = listOfJoints[1]
            wrist    = listOfJoints[0]
            offset   = listOfJoints[8]
            pv_ctrl  = listOfJoints[7]
            
            snap_offset_locator(offset, shoulder, elbow, wrist)
            cmds.matchTransform(pv_ctrl, offset)
            #cmds.matchTransform(listOfJoints[7], listOfJoints[8]) #ikElbowCtrl, offsetLctr
            cmds.setAttr(listOfJoints[9]+'.ikFkSwitch', 1)      

def snap_offset_locator(offsetLctr, shoulder, elbow, wrist):
    import maya.api.OpenMaya as om
    
    def get_pos(obj):
        return om.MVector(cmds.xform(obj, q=True, ws=True, t=True))
    
    s = get_pos(shoulder)
    e = get_pos(elbow)
    w = get_pos(wrist)
    
    # midpoint between shoulder and wrist
    mid = (s + w) * 0.5
    
    # direction from midpoint to elbow
    direction = (e - mid).normal()
    
    # distance based on arm length
    dist = (w - s).length() * 0.5
    
    final_pos = e + (direction * dist)
    
    cmds.xform(offsetLctr, ws=True, t=(final_pos.x, final_pos.y, final_pos.z))
                        
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
    
    controlSettingsFrame = cmds.frameLayout(
        label="Controls",
        collapsable=False,
        marginWidth=8,
        marginHeight=3,
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
    basicColourValues = (0.05, 0, 0.6)    
    colourCanvas01 = cmds.canvas(
        width=40,
        rgbValue=basicColourValues,
        pressCommand=lambda *args: newColourSwatch(colourCanvas01, "control", colourValues)
    )
            
    cmds.text(label='  Switch Colour:', align='right')
    switchColourValues = (0, 0.4, 0)
    colourCanvas02 = cmds.canvas(
        width=40,
        rgbValue=switchColourValues,
        pressCommand=lambda *args: newColourSwatch(colourCanvas02, "switch", colourValues)
    )
    
    cmds.text(label='  Polevector Colour:', align='right')
    poleColourValues = (0.75, 0.45, 0)      
    colourCanvas03 = cmds.canvas(
        width=40,
        rgbValue=poleColourValues,
        pressCommand=lambda *args: newColourSwatch(colourCanvas03, "pole", colourValues)
    )  

    # Create a dictionary to store the colour values provided by the user.
    colourValues = {
        "control": basicColourValues,
        "switch": switchColourValues,
        "pole": poleColourValues
    }  
                
    cmds.button(
        label="Create Single Control", parent= mainLayout,
        command=lambda *args: createSingleControl(radiusField, colourValues)
    )   

    ####################
    cmds.separator(height=8, style="in", parent=mainLayout)    
    IkFkMatcherFrame = cmds.frameLayout(
        label="IKFK_Matcher",
        collapsable=False,
        marginWidth=8,
        marginHeight=3,
        parent=mainLayout
    )
    ikFkMatcherCol = cmds.rowColumnLayout(
        numberOfColumns=2,
        columnAttach=([1, 'right', 5], [2, 'left', 5]),
        parent=mainLayout
    )
    cmds.text(label='  IKFK Matcher:', align='right')   
     
    matchingRadio = cmds.radioButtonGrp(
        labelArray2=['IK->FK', 'FK->IK'],
        numberOfRadioButtons=2,
        select=0
    )
    fk_to_ik_button = cmds.button(label='Match', parent=mainLayout,
                command=lambda *args: ikFkMatcher(matchingRadio))  
                    
    ###############
    cmds.separator(height=8, style="in", parent=mainLayout)
    createIkFkFrame = cmds.frameLayout(
        label="IKFK_Creator",
        collapsable=False,
        marginWidth=8,
        marginHeight=3,
        parent=mainLayout
    )         
    cmds.button(
        label="Create IK FK", parent= mainLayout,
        command=lambda *args: createIkFk(radiusField, colourValues)
    )          
    cmds.separator(height=8, style="in", parent=mainLayout)              
                  
    cmds.showWindow(windowName)

#main
createWindow()