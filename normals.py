
import bpy
import numpy as np

def normal_texture(normal_setup=0):
    # Create a new material
    mat = bpy.data.materials.new(name="MyMaterial")
    mat.use_nodes = True
    obj = bpy.context.object
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    # Access the node tree
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # === Remove the default Principled BSDF ===
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            nodes.remove(node)

    # === Get existing Material Output ===
    output = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output = node
            break


    texcoord = nodes.new(type='ShaderNodeTexCoord')
    texcoord.location = (-800, 0)


    vec_transform = nodes.new('ShaderNodeVectorTransform')
    vec_transform.location = (-500, 0)

    # Configure transformation: Object → Camera
    vec_transform.vector_type = 'NORMAL'
    vec_transform.convert_from = 'OBJECT'
    vec_transform.convert_to = 'CAMERA'

    # Link Normal → Vector
    links.new(texcoord.outputs['Normal'], vec_transform.inputs['Vector'])

    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-400, 0)

    # Set mapping type to "TEXTURE"
    mapping.vector_type = 'TEXTURE'

    # === Set your parameters ===
    if normal_setup == 0:
        mapping.inputs['Location'].default_value = (-1., -1., 1.)  # Translation
        mapping.inputs['Rotation'].default_value = (0.0, 0.0, 0.)  # Rotation (radians)
        mapping.inputs['Scale'].default_value = (2., 2., -2.)  # Scale
    elif normal_setup == 1:
        mapping.inputs['Location'].default_value = (1., 1., -1.)  # Translation
        mapping.inputs['Rotation'].default_value = (0.0, 0.0, 0.)  # Rotation (radians)
        mapping.inputs['Scale'].default_value = (-2., -2., 2.)  # Scale    
    elif normal_setup == 2:
        mapping.inputs['Location'].default_value = (-1., 1., 1.)  # Translation
        mapping.inputs['Rotation'].default_value = (0.0, -np.pi/2, 0.)  # Rotation (radians)
        mapping.inputs['Scale'].default_value = (-2., -2., -2.)  # Scale    
    elif normal_setup == 3:
        mapping.inputs['Location'].default_value = (1., -1., 1.)  # Translation
        mapping.inputs['Rotation'].default_value = (-np.pi/2., 0.0, 0.)  # Rotation (radians)
        mapping.inputs['Scale'].default_value = (-2., 2., 2.)  # Scale    

    links.new(vec_transform.outputs['Vector'], mapping.inputs['Vector'])


    # Gamma correction node
    gamma_node = nodes.new('ShaderNodeGamma')
    gamma_node.location = (200, 0)

    # Set gamma value
    gamma_node.inputs['Gamma'].default_value = 2.2
    links.new(mapping.outputs['Vector'], gamma_node.inputs['Color'])

    # output = nodes.new('ShaderNodeOutputMaterial')
    # output.location = (1000, 0)

    links.new(gamma_node.outputs['Color'], output.inputs['Surface'])