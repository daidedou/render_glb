
import mathutils
import numpy as np
import bpy
import blendertoolbox as bt



def set_render(resolution_x, resolution_y, cycles=True, numSamples=100, exposure=1.5, use_GPU=True):
    if cycles:
        bt.blenderInit(resolution_x, resolution_x, numSamples, exposure, use_GPU)
        if use_GPU:
            cyclePref = bpy.context.preferences.addons['cycles'].preferences
            cyclePref.compute_device_type = 'CUDA'
            for d in cyclePref.devices:
                d["use"] = 1
                print("Device:", d["name"], "Enabled:", d["use"])

            bpy.context.scene.cycles.device = 'GPU'
            bpy.context.preferences.addons['cycles'].preferences.refresh_devices()
        # ---------------------------------------------
        # Invisible ground and lighting
        # ---------------------------------------------
        bt.invisibleGround(shadowBrightness=0.9)
    else:
        # clear all
        bpy.ops.wm.read_homefile()
        bpy.ops.object.select_all(action = 'SELECT')
        bpy.ops.object.delete() 
        # Using EEVEE
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        bpy.context.scene.render.resolution_x = resolution_x 
        bpy.context.scene.render.resolution_y = resolution_y 
        bpy.context.scene.render.film_transparent = True

def prepare_cam_animation(turntable, N=20, fps=24, linear=True):

    # ---------------------------------------------
    # Animation settings (360 turntable)
    # ---------------------------------------------

    scene = bpy.context.scene

    scene.render.fps = fps
    scene.frame_start = 0
    scene.frame_end = N

    print("Animation settings:")
    print("FPS:", fps)
    print("Total frames:", N)

    # ---------------------------------------------
    # Animate 360° rotation of the empty
    # ---------------------------------------------

    scene = bpy.context.scene

    # Ensure rotation mode is Euler
    turntable.rotation_mode = 'XYZ'

    # --- Frame 0 ---
    scene.frame_set(0)
    turntable.rotation_euler[2] = 0
    turntable.keyframe_insert(data_path="rotation_euler", index=2)

    # --- Frame N ---
    scene.frame_set(N)
    turntable.rotation_euler[2] = np.radians(360)
    turntable.keyframe_insert(data_path="rotation_euler", index=2)

    print("✅ Keyframes inserted (0° → 360°)")

    if linear:
        # ---------------------------------------------
        # Force linear interpolation
        # ---------------------------------------------

        action = turntable.animation_data.action

        for fcurve in action.fcurves:
            if fcurve.data_path == "rotation_euler" and fcurve.array_index == 2:
                for k in fcurve.keyframe_points:
                    k.interpolation = 'LINEAR'

def get_bbox_center_world(o):
    """World-space center of an object's bounding box."""
    corners = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    center = mathutils.Vector((0.0, 0.0, 0.0))
    for v in corners:
        center += v
    center /= 8.0
    return center

def add_turntable_empty(target_obj, name="Turntable_Empty", empty_type='PLAIN_AXES'):
    """
    Create an Empty at the target object's bbox center (world space).
    """
    # If it already exists, reuse it
    existing = bpy.data.objects.get(name)
    if existing is not None:
        return existing

    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = empty_type

    # Place it at the object's center
    empty.location = get_bbox_center_world(target_obj)

    # Link into scene (active collection is usually fine)
    bpy.context.collection.objects.link(empty)

    return empty

def parent_camera_to_empty(camera, empty, verbose=True):
    """
    Parent the camera to the empty while preserving world transform.
    """
    # Save current world transform
    camera.parent = empty
    camera.matrix_parent_inverse = empty.matrix_world.inverted()

    if verbose:
        print(f"✅ Camera '{camera.name}' parented to '{empty.name}'")


def compositing(alphaThreshold, interpolationMode = 'CARDINAL'):
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
        # --- Nodes ---
    REND = tree.nodes.new("CompositorNodeRLayers")
    OUT  = tree.nodes.new("CompositorNodeComposite")

    # ---------
    # SHADOW / ALPHA FILTER BRANCH
    # ---------

    RAMP = tree.nodes.new("CompositorNodeValToRGB")
    RAMP.color_ramp.elements[0].color[3] = 0
    RAMP.color_ramp.elements[0].position = alphaThreshold
    RAMP.color_ramp.interpolation = interpolationMode

    tree.links.new(REND.outputs["Alpha"], RAMP.inputs[0])

    # ---------
    # WHITE BACKGROUND BRANCH
    # ---------

    WHITE = tree.nodes.new("CompositorNodeRGB")
    WHITE.outputs[0].default_value = (1, 1, 1, 1)

    ALPHA_OVER = tree.nodes.new("CompositorNodeAlphaOver")
    ALPHA_OVER.premul = 1

    # Background
    tree.links.new(WHITE.outputs[0], ALPHA_OVER.inputs[1])

    # Foreground image
    tree.links.new(REND.outputs["Image"], ALPHA_OVER.inputs[2])

    # Use filtered alpha as factor
    tree.links.new(RAMP.outputs[0], ALPHA_OVER.inputs[0])

    # ---------
    # OUTPUT
    # ---------

    tree.links.new(ALPHA_OVER.outputs[0], OUT.inputs[0])