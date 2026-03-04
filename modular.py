import argparse
import blendertoolbox as bt
import bpy
import os
import numpy as np
import glb
import normals as nr
import utils_blender as ut
import utils
# ---------------------------------------------
# Parse command-line arguments
# ---------------------------------------------
parser = argparse.ArgumentParser(description="Render a GLB model using BlenderToolbox.")
parser.add_argument("--glb", type=str, required=True, help="Path to the .glb file to load")
parser.add_argument("--normals", action="store_true", help="Use custom normal logic (placeholder)")
parser.add_argument("--frames", type=int, default=4, help="Number of frames")
parser.add_argument("--sub", type=int, default=0, choices=range(0, 5), help="Subdivision level (0–4)")
parser.add_argument("--nr", type=int, default=0, help="Unused numeric option (reserved for future use)")
parser.add_argument("--render", action="store_true", help="If passed, render the image to PNG")
parser.add_argument("--full", action="store_true", help="If passed, use full quality (1080x1080, 4000 samples)")
parser.add_argument("--gpu", action="store_true", help="If passed, enable GPU rendering (CUDA)")
parser.add_argument("--eevee", action="store_true", help="If passed, use EEVEE instead of CYCLES (much faster, less pretty)")
parser.add_argument("--post", action="store_true", help="If passed, make the postprocessing (video, remove background if necessary) - Recommended to have a high number of frames")
parser.add_argument("--light", type=str, default="world/forest.exr",
                    help="Subpath inside 'studiolights' folder for the environment light (default: world/forest.exr)")
args, unknown = parser.parse_known_args()

# ---------------------------------------------
# Log arguments
# ---------------------------------------------
print(f"→ Loading GLB file: {args.glb}")
print(f"→ Number of frames: {args.frames}")
print(f"→ Normals flag: {args.normals}")
print(f"→ Subdivision level (--sub): {args.sub}")
print(f"→ NR value (--nr): {args.nr} (currently unused)")
print(f"→ Render flag (--render): {args.render}")
print(f"→ Renderer: ", "EEVEE" if args.eevee else "CYCLES")
print(f"→ Full quality flag (--full): {args.full}")

# ---------------------------------------------
# Initialize Blender
# ---------------------------------------------
if args.full:
    imgRes_x, imgRes_y = 1080, 1080
    numSamples = 400
    print("Using FULL quality: 1080x1080, 400 samples")
else:
    imgRes_x, imgRes_y = 400, 400
    numSamples = 100
    print("Using PREVIEW quality: 400x400, 100 samples")

ut.set_render(imgRes_x, imgRes_y, cycles=not(args.eevee), numSamples=numSamples, use_GPU=args.gpu)

# ---------------------------------------------
# Read mesh
# ---------------------------------------------
location = (0, 0, 0.75)
rotation = (-50, -5, 24)
scale = (1.5, 1.5, 1.5)

mesh = glb.readGLB(args.glb, location, rotation, scale)
mesh.shade_smooth()

obj = bpy.data.objects[mesh.name]
bpy.context.view_layer.objects.active = obj

# ---------------------------------------------
# Apply optional subdivision (based on --sub)
# ---------------------------------------------
if args.sub > 0:
    bpy.ops.object.modifier_add(type='SUBSURF')
    obj.modifiers["Subdivision"].render_levels = args.sub
    obj.modifiers["Subdivision"].levels = args.sub
    print(f"Applied subdivision level: {args.sub}")

# ---------------------------------------------
# Placeholder for --normals
# ---------------------------------------------
if args.normals:
    nr.normal_texture(args.nr)


camLocation = (0, -2.6, 1)
rotation_euler = (67, 0, 0)
focalLength = 45
cam = bt.setCamera_from_UI(camLocation, rotation_euler, focalLength=focalLength)

# Add empty object, parenting it to camera to easily set up our animation
turntable = ut.add_turntable_empty(obj, name="Turntable_Empty")
print("✅ Added empty:", turntable.name, "at", tuple(turntable.location))

ut.parent_camera_to_empty(cam, turntable)
ut.prepare_cam_animation(turntable, N=args.frames)

# Environment lighting
# Environment map path (inside local studiolights folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "studiolights", args.light)
if not os.path.exists(env_path):
    raise FileNotFoundError(f"Environment light file not found: {env_path}")

bpy.data.scenes[0].world.use_nodes = True
enode = bpy.data.scenes[0].world.node_tree.nodes.new("ShaderNodeTexEnvironment")
enode.image = bpy.data.images.load(env_path)
node_tree = bpy.data.scenes[0].world.node_tree
node_tree.links.new(enode.outputs['Color'], node_tree.nodes['Background'].inputs['Color'])
bg_node = node_tree.nodes.get('Background')
bg_node.inputs['Strength'].default_value = 3.0

## set gray shadow to completely white with a threshold 
#ut.compositing(alphaThreshold = 0.60, interpolationMode = 'CARDINAL')

# ---------------------------------------------
# Save outputs
# ---------------------------------------------
base_name = os.path.splitext(args.glb)[0]
blend_path = f"{base_name}.blend"
bpy.ops.wm.save_mainfile(filepath=blend_path)
print(f"✅ Saved blend file: {blend_path}")

output_dir = f"{base_name}_frames"

if args.render:
    # ---------------------------------------------
    # Animation render output (PNG sequence)
    # ---------------------------------------------

    scene = bpy.context.scene
    bpy.context.scene.camera = cam
    # Folder where frames will be saved
    os.makedirs(output_dir, exist_ok=True)

    # Blender requires a filepath prefix
    scene.render.filepath = os.path.join(output_dir, "frame_")

    # Render settings
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    print("Animation output directory:", output_dir)
    bpy.ops.render.render(animation=True)
    print(f"✅ Rendered animation: {output_dir}")
    if args.post:
        if not args.eevee:
            utils.remove_background(output_dir, os.path.join(output_dir, "clean"))
            utils.compile_video_from_folder(os.path.join(output_dir, "clean"))
        else:
            utils.compile_video_from_folder(output_dir)
else:
    print("⚠️  Render skipped (use --render to enable)")


