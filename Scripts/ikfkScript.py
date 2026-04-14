# IK_FK_Matcher
# Matches The Fk Controls To The Ik Controls And Vice Versa
# By @Nicholas Easter

import maya.cmds as cmds

# Checks for various problems that may arise

def error_checks():
    # Is something selected?
    selected = cmds.ls(selection=1)
    switch_checked = False
    if selected:
        ik_fk_switch = selected[0]
                
        # Is it the switch control?
       
        ik_fk_switch_attr = list(set(cmds.listAttr(ik_fk_switch)))
        
        for attribute in ik_fk_switch_attr:
            if ('ikFkSwitch') in attribute:
                switch_checked = True
                return (switch_checked)
        else:
            switch_checked = False
            cmds.warning("You need to select the ik_fk_switch_control.")
            return (switch_checked)
    else:
        cmds.warning("You need to select an object.")
        return (switch_checked)

# finds the joints, controls and other required objects

def find_joints():
    
    ik_fk_switch = cmds.ls(selection=1)[0]

    # Find The Switch Group (If There Is One)
    
    ik_fk_switch_grp_check = cmds.listRelatives(ik_fk_switch, parent=1)
    
    if ik_fk_switch_grp_check:
        ik_fk_switch_grp = cmds.listRelatives(ik_fk_switch, parent=1)[0]
    else:
        ik_fk_switch_grp = ik_fk_switch
        
    # Finds the original joints
    
        
    ik_fk_switch_grp_connections = list(set(cmds.listConnections(ik_fk_switch_grp, type='constraint')))[0]
    wrist_jnt = list(set(cmds.listConnections(ik_fk_switch_grp_connections, type='joint')))[0]
    
    elbow_jnt = cmds.listRelatives(wrist_jnt, parent=1)[0]
    shoulder_jnt = cmds.listRelatives(elbow_jnt, parent=1)[0]
    
    # Creates suffixes
    
    ik_suffix = '_ik'
    fk_suffix = '_fk'
    control_suffix = '_control'
    offset_locator_suffix = '_offset_locator'
    
    # Finds the IK joints
    
    ik_shoulder = (shoulder_jnt+ik_suffix)
    ik_elbow = (elbow_jnt+ik_suffix)
    ik_wrist = (wrist_jnt+ik_suffix)
    
    # Finds the IK controls
    
    ik_elbow_con = (elbow_jnt+ik_suffix+control_suffix)
    ik_wrist_con = (wrist_jnt+ik_suffix+control_suffix)
    
    # Finds the FK controls
    
    fk_shoulder_con = (shoulder_jnt+fk_suffix+control_suffix)
    fk_elbow_con = (elbow_jnt+fk_suffix+control_suffix)
    fk_wrist_con = (wrist_jnt+fk_suffix+control_suffix)
    
    # Finds the offset locator
    
    ik_offset_locator = (elbow_jnt+ik_suffix+offset_locator_suffix)
    
    # Returns the variables to be used when needed.
    
    return fk_shoulder_con, fk_elbow_con, fk_wrist_con, ik_shoulder, ik_elbow, ik_wrist, ik_elbow_con, ik_wrist_con, ik_offset_locator, ik_fk_switch
                
     
def fk_to_ik_button_push(*args):
    
    # Checks for errors
    
    switch_checked = error_checks()
    
    if switch_checked == True:
        
        # Brings in the variables
        
        fk_shoulder_con, fk_elbow_con, fk_wrist_con, ik_shoulder, ik_elbow, ik_wrist, ik_elbow_con, ik_wrist_con, ik_offset_locator, ik_fk_switch = find_joints()
        
        # Matches the fk controls to the ik Joints and sets the switch control to fk Mode    
  
        cmds.matchTransform(fk_shoulder_con, ik_shoulder)
        cmds.matchTransform(fk_elbow_con, ik_elbow)
        cmds.matchTransform(fk_wrist_con, ik_wrist)
        cmds.setAttr(ik_fk_switch+'.ikFkSwitch', 0)
    
    
def ik_to_fk_button_push(*args):
    
    # Checks for errors

    switch_checked = error_checks()
    
    if switch_checked == True:
        
        # Brings in the variables
        
        fk_shoulder_con, fk_elbow_con, fk_wrist_con, ik_shoulder, ik_elbow, ik_wrist, ik_elbow_con, ik_wrist_con, ik_offset_locator, ik_fk_switch = find_joints()
        
        cmds.matchTransform(ik_wrist_con, fk_wrist_con)
        cmds.matchTransform(ik_elbow_con, ik_offset_locator)
        cmds.setAttr(ik_fk_switch+'.ikFkSwitch', 1)


    # Match the ik wrist to the fk wrist and match the the ik elbow to the offset locator and set the switch control to ik Mode
    
window_name = 'TwistJointGenerator'
        
#Removes Current Window (If There Is One Already Up)

if cmds.window(window_name, exists=1):
    cmds.deleteUI(window_name)


#Creates The Window

cmds.window(window_name)

window_height= 125 
window_width = 300

main_layout = cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, window_width)])

cmds.separator(visible=False, height=10, parent=main_layout)

cmds.text(label='Match The IK Controls to the FK Joints', parent=main_layout)

fk_to_ik_button = cmds.button(label='IK to FK', parent=main_layout,
            command=fk_to_ik_button_push)

cmds.separator(visible=False, height=20, parent=main_layout)

cmds.text(label='Match The FK Controls to the IK Joints', parent=main_layout, align='center')

ik_to_fk_button = cmds.button(label='FK to IK', parent=main_layout,
            command=ik_to_fk_button_push)
            

cmds.window(window_name, edit=1, 
            width=window_width, 
            height=window_height)
cmds.showWindow(window_name)


    
