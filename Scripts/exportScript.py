import maya.cmds as cmds
import maya.mel as mel
import os

def export_frozen_objects_to_fbx(export_folder):
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    selected_objects = cmds.ls(selection=True, long=True)
    if not selected_objects:
        cmds.warning("No objects selected.")
        return

    for obj in selected_objects:
        obj_name = obj.split("|")[-1]
        export_path = os.path.join(export_folder, obj_name + ".fbx")

        # Duplicate the object
        duplicate = cmds.duplicate(obj, name=obj_name + "_export")[0]

        # Get the object's bounding box center
        bbox = cmds.xform(duplicate, query=True, boundingBox=True, worldSpace=True)
        center_x = (bbox[0] + bbox[3]) / 2.0
        center_y = (bbox[1] + bbox[4]) / 2.0
        center_z = (bbox[2] + bbox[5]) / 2.0

        # Move geometry to origin using a temporary transform node
        cmds.move(-center_x, -center_y, -center_z, duplicate + ".vtx[*]", relative=True)

        # Export the duplicate
        cmds.select(duplicate, replace=True)
        mel.eval('FBXExport -f "{}" -s'.format(export_path))
        print(f"Exported {obj_name} to {export_path}")

        # Clean up
        #cmds.delete(duplicate)

    cmds.select(clear=True)
    print("All frozen transforms exported cleanly.")


# --- Example Usage ---
export_folder = "C:/Users/sandr/Desktop/Unreal_Project/SunkenCity/Unreal_Imports/FBX"  # Change this path as needed
export_selected_objects_to_fbx(export_folder)
