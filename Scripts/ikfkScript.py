# ik_fk_generator_A01240437.py 
# ik fk creation script
# Generates FK and IK controls for the selected joint (preferably the wrist)
# By @Nicholas Easter

import maya.cmds as cmds
selected = cmds.ls(selection=1, type='joint')
if selected:
    # Select the wrist joint (in a list to avoid error if there arent enough parent objects)
    
    wrist_jnt = cmds.ls(selection=1, type='joint')[0]
    wrist_pos = cmds.getAttr(f'{wrist_jnt}.translateX')
    
    # Select the wrist joint (in a list to avoid error if there arent enough parent objects)
    
    elbow_jnt = cmds.listRelatives(wrist_jnt, parent=1)
    
    # Select the wrist joint (in a list to avoid error if there arent enough parent objects)
    
    shoulder_jnt = cmds.listRelatives(elbow_jnt, parent=1)

    # Select the wrist joint (in a list to avoid error if there arent enough parent objects)
    
    clavicle_jnt = cmds.listRelatives(shoulder_jnt, parent=1)

    # Duplicate arm for FK
    
    if clavicle_jnt == None:
        cmds.warning("You must have 3 parent joints")
    else:
        
        # Get the selected joints and remove them from their respected lists
        
        elbow_jnt = elbow_jnt[0]
        shoulder_jnt = shoulder_jnt[0]
        clavicle_jnt = clavicle_jnt[0]

        # The duplication station starts here
        
        shoulder_fk = cmds.duplicate(shoulder_jnt, name=shoulder_jnt+'_fk', renameChildren=1)    
        shoulder_fk_relatives = cmds.listRelatives(shoulder_fk, allDescendents=1)
        shoulder_fk_jnt = (shoulder_fk)[0]
        
        # Get the duplicated elbow/ wrist joints        
        elbow_fk_jnt = cmds.listRelatives(shoulder_fk, children=1)[0]
        wrist_fk_jnt = cmds.listRelatives(shoulder_fk, children=1)[1]
        
        # Renames the new joints

        if shoulder_fk_relatives:
            if elbow_fk_jnt:
                shoulder_fk_relatives.remove(elbow_fk_jnt)
                elbow_fk_jnt = cmds.rename (elbow_fk_jnt, elbow_jnt+'_fk')
            if wrist_fk_jnt:    
                shoulder_fk_relatives.remove(wrist_fk_jnt)
                wrist_fk_jnt = cmds.rename (wrist_fk_jnt, wrist_jnt+'_fk')
       
            # Delete all extra joints that arent  the elbow and wrist
            
            if shoulder_fk_relatives:
                cmds.delete(shoulder_fk_relatives)

        # Build fk controls
        
        # Creates circles and groups them
        
        shoulder_fk_control = cmds.circle(name=shoulder_fk_jnt+'_control')[0]
        elbow_fk_control = cmds.circle(name=elbow_fk_jnt+'_control')[0]
        wrist_fk_control = cmds.circle(name=wrist_fk_jnt+'_control')[0]
        
        shoulder_fk_control_grp = cmds.group(shoulder_fk_control, name=shoulder_fk_control+'_grp')
        elbow_fk_control_grp = cmds.group(elbow_fk_control, name=elbow_fk_control+'_grp')
        wrist_fk_control_grp = cmds.group(wrist_fk_control, name=wrist_fk_control+'_grp')  
        
        # Match the groups transforms to the joints
        
        cmds.matchTransform(shoulder_fk_control_grp, shoulder_fk_jnt)
        cmds.matchTransform(elbow_fk_control_grp, elbow_fk_jnt)
        cmds.matchTransform(wrist_fk_control_grp, wrist_fk_jnt)
        
        # Parents the controls to the jnts
                
        cmds.parentConstraint(shoulder_fk_control, shoulder_fk_jnt)
        cmds.parentConstraint(elbow_fk_control, elbow_fk_jnt)
        cmds.parentConstraint(wrist_fk_control, wrist_fk_jnt)
        
        # Parents the wrist_ctrl to the elbow and elbow to the shoulder
        
        cmds.parent (wrist_fk_control_grp, elbow_fk_control)
        cmds.parent (elbow_fk_control_grp, shoulder_fk_control)
        
        # Duplicate arm for IK.
        
        # The duplication station starts here
        
        shoulder_ik = cmds.duplicate(shoulder_jnt, name=shoulder_jnt+'_ik', renameChildren=1)    
        shoulder_ik_relatives = cmds.listRelatives(shoulder_ik, allDescendents=1)
        shoulder_ik_jnt = (shoulder_ik)[0]
            
        # Get the duplicated elbow/ wrist joints
        elbow_ik_jnt = cmds.listRelatives(shoulder_ik, children=1)[0]
        wrist_ik_jnt = cmds.listRelatives(shoulder_ik, children=1)[1]

      
        # Renames the new joints
        
        if shoulder_ik_relatives:
            if elbow_ik_jnt:    
                shoulder_ik_relatives.remove(elbow_ik_jnt)
                elbow_ik_jnt = cmds.rename (elbow_ik_jnt, elbow_jnt+'_ik')
            if wrist_ik_jnt:    
                shoulder_ik_relatives.remove(wrist_ik_jnt)
                wrist_ik_jnt = cmds.rename (wrist_ik_jnt, wrist_jnt+'_ik')
           
            # Delete all extra joints that arent  the elbow and wrist


            if shoulder_ik_relatives:
                cmds.delete(shoulder_ik_relatives)
            
        # Create an ikHandle and parent it to the wrist control
        
        ik_handle = cmds.ikHandle(startJoint=shoulder_ik_jnt, endEffector=wrist_ik_jnt, sol='ikRPsolver', name=wrist_jnt+'_ik_handle')[0]
        
        # Creates a circle and groups it  
        wrist_ik_control = cmds.circle(name=wrist_ik_jnt+'_control')[0]
        wrist_ik_control_grp = cmds.group(wrist_ik_control, name=wrist_ik_control+'_grp')
        
        # Match the groups transforms to the joints
        
        cmds.matchTransform(wrist_ik_control_grp, wrist_ik_jnt)  
        
        # Parents the ik_handle to the wrist control
        
        cmds.parent (ik_handle, wrist_ik_control)
       
        # Orients the wrist control to the ik_handle
        
        cmds.orientConstraint(wrist_ik_control, ik_handle)
       
        # create an elbow ik control and create pole vector constraint
        
        # Creates a circle and groups it
        
        elbow_ik_control = cmds.circle(name=elbow_ik_jnt+'_control')[0]
        elbow_ik_control_grp = cmds.group(elbow_ik_control, name=elbow_ik_control+'_grp')
        
        # Match the groups transforms to the joints
        
        cmds.matchTransform(elbow_ik_control_grp, elbow_ik_jnt) 

        # Find the new location of the elbow control
        
        elbow_distance = (-2/3)
        
        elbow_distance_z = wrist_pos * (elbow_distance)
        
        cmds.move(0,0,elbow_distance_z, elbow_ik_control_grp, relative=1, objectSpace=1)
                
        # Create the pole vector contstraint

        cmds.poleVectorConstraint(elbow_ik_control, ik_handle)
       
        # Create the Ik/Fk Switch control and group it
        
        ik_fk_switch_distance = (-2/3)
        ik_fk_switch_control_z = wrist_pos * ik_fk_switch_distance
        ik_fk_switch_control = cmds.circle(degree=1, name=wrist_jnt+'_ik_fk_switch_control')[0]
        ik_fk_switch_control_grp = cmds.group(ik_fk_switch_control, name=ik_fk_switch_control+'_grp')
        
        # Match the groups transforms to the joints
        
        cmds.matchTransform(ik_fk_switch_control_grp, wrist_ik_jnt)
    
        # Parents constrains the wrist jnt to the ik_fk_switch_control_grp to the wrist jnt and offsets it.
        
        cmds.parentConstraint(wrist_jnt, ik_fk_switch_control_grp)
        cmds.move(0,0,ik_fk_switch_control_z, ik_fk_switch_control, relative=1, objectSpace=1)
        cmds.makeIdentity (ik_fk_switch_control, apply=1, translate=1, rotate=1, scale=1, normal=0, preserveNormals=1)
        
        # Add a custom attribute
        cmds.addAttr(ik_fk_switch_control, keyable=1, longName='ikFkSwitch', defaultValue=1, minValue=0, maxValue=1)
        
        # Connect the rotations of the IK and FK joints to the skinning joint
   
        original_jnts = [wrist_jnt, elbow_jnt, shoulder_jnt]
        for jnts in (original_jnts):
        
            # Create a pairBlend node
            ik_fk_blend = cmds.shadingNode('pairBlend', name=(jnts+'_pairBlend'), asUtility=1)

            # Connect fk joints rotate and translate to pairBlends in rotate1/inTranslate1

            cmds.connectAttr(jnts+'_fk.rotate', ik_fk_blend+'.inRotate1', force=1)
            cmds.connectAttr(jnts+'_fk.translate', ik_fk_blend+'.inTranslate1', force=1)
                    
            # Connect ik joints rotate and translate to pairBlends in rotate2/inTranslate2
            
            cmds.connectAttr(jnts+'_ik.rotate', ik_fk_blend+'.inRotate2', force=1)
            cmds.connectAttr(jnts+'_ik.translate', ik_fk_blend+'.inTranslate2', force=1)        
        
            # connect ik/fk switch ctrls switch channel to the pairBlends weight attribute
            
            cmds.connectAttr(ik_fk_switch_control+'.ikFkSwitch', ik_fk_blend+'.weight', force=1)                   
            
            # Connect pairBlends outRotate/outTranslate to the skinning joints rotate and translate

            cmds.connectAttr(ik_fk_blend+'.outRotate', jnts+'.rotate', force=1)
            cmds.connectAttr(ik_fk_blend+'.outTranslate', jnts+'.translate', force=1)           

            # Connect scale using a blend channel node
            
            ik_fk_colours = cmds.shadingNode('blendColors', name=(jnts+'_blendColours'), asUtility=1)
            
            # Connect fk scale to blendColours color 1, ik scale to color 2
            
            cmds.connectAttr(jnts+'_fk.scale', ik_fk_colours+'.color1', force=1)
            cmds.connectAttr(jnts+'_ik.scale', ik_fk_colours+'.color2', force=1)

            # Connect the ikFkSwitch ctrl attribute to the blendColors blender
            cmds.connectAttr(ik_fk_switch_control+'.ikFkSwitch', ik_fk_colours+'.blender', force=1) 
            
            # Connect the blend Colors output to skinning joint scale
 
            cmds.connectAttr(ik_fk_colours+'.output', jnts+'.scale', force=1)                   
            
        # Drive the visibility of the fk and ik controls with the switch control

        # When in Fk mode (switch attr = 0), hide ik controls  
        
        # Create condition node

        fk_vis_condition = cmds.shadingNode('condition', name=('fk_vis_condition'), asUtility=1)

        # Connect the ikFk Switch attributes to IK vis conditions firstTerm
        
        cmds.connectAttr(ik_fk_switch_control+'.ikFkSwitch', fk_vis_condition+'.firstTerm', force=1) 
        
        # Connect fk Vis Condition's outColor to fk wrist/elbow visibility
        
        cmds.connectAttr(fk_vis_condition+'.outColor.outColorR', elbow_ik_control+'.visibility', force=1) 
        cmds.connectAttr(fk_vis_condition+'.outColor.outColorR', wrist_ik_control+'.visibility', force=1) 
        
        # When in Ik mode (switch attr = 1), hide fk controls  
        
        # Create condition node
        
        ik_vis_condition = cmds.shadingNode('condition', name=('ik_vis_condition'), asUtility=1)

        # Connect the IkFkSwitch attr to FK Vis condition's first Term
        
        cmds.connectAttr(ik_fk_switch_control+'.ikFkSwitch', ik_vis_condition+'.firstTerm', force=1) 
        
        # Sets the ik condition's second term to be 1
                
        cmds.setAttr (ik_vis_condition+'.secondTerm', 1)
        
        # Connect Ik Vis Condition's outColorR to shoulder vis
        
        cmds.connectAttr(ik_vis_condition+'.outColor.outColorR', shoulder_fk_control+'.visibility', force=1) 
       
        # Hide the ik/fk joints
        
        #sets the axis, attributes, and visibility
        
        axis = ('x', 'y', 'z')
        attributes = ('t', 'r', 's')
        visibility = ('v')
        
        # Creates a list of all joints / controls
        1
        ik_fk_jnts = [wrist_ik_jnt, elbow_ik_jnt, shoulder_ik_jnt, wrist_fk_jnt, elbow_fk_jnt, shoulder_fk_jnt]
        ik_fk_ctrls = [wrist_ik_control, elbow_ik_control, wrist_fk_control, elbow_fk_control, shoulder_fk_control]
        
        # Turns off the jnts visibility and locks/hides them
        
        for jnts in ik_fk_jnts:   
            for vis in visibility:   
                cmds.setAttr (jnts+'.'+vis, 0)
                cmds.setAttr (jnts+'.'+vis, lock=1, keyable=0)
            
        # Hide the ik handle
        
        cmds.setAttr (ik_handle+'.visibility', 0)
        
        # Locks/hides specific controls attributes
        
        for ax in axis:
            for at in attributes:
                for vis in visibility:
                        #Unlocks and unhides all channels
                        cmds.setAttr(ik_fk_switch_control+'.'+at+ax, lock=1, keyable=0)
                        cmds.setAttr(ik_fk_switch_control+'.'+vis, lock=1, keyable=0)
                        cmds.setAttr(elbow_ik_control+'.r'+ax, lock=1, keyable=0)
                        cmds.setAttr(wrist_ik_control+'.r'+ax, lock=1, keyable=0)
    
else:
    cmds.warning("You need to select an object.")
