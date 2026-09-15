"""Sode finish variant using the unchanged three Dō atlas images."""
import bpy


def build_material(original):
    material = original.copy()
    material.name = 'M_Sode01'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bs = nodes.get('Principled BSDF')
    color = next(n for n in nodes if n.type == 'TEX_IMAGE' and 'BaseColor' in n.image.name)
    orm = next(n for n in nodes if n.type == 'TEX_IMAGE' and 'ORM' in n.image.name)
    uv = nodes.new('ShaderNodeTexCoord')
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(uv.outputs['UV'], separate.inputs[0])

    def math_node(op, first=None, second=0):
        n = nodes.new('ShaderNodeMath'); n.operation = op
        if first is not None: links.new(first, n.inputs[0])
        n.inputs[1].default_value = second
        return n

    x = math_node('MULTIPLY', separate.outputs['X'], 4)
    y = math_node('MULTIPLY', separate.outputs['Y'], 4)
    x = math_node('FLOOR', x.outputs[0])
    y = math_node('FLOOR', y.outputs[0])
    y = math_node('MULTIPLY', y.outputs[0], 4)
    index = math_node('ADD', x.outputs[0]); links.new(y.outputs[0], index.inputs[1])
    index = math_node('DIVIDE', index.outputs[0], 15)
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.label = 'Lacquer / dark red silk / aged brass'
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for tile in range(16):
        el = ramp.color_ramp.elements[0] if tile == 0 else ramp.color_ramp.elements.new((tile-.1)/15)
        tint = (.28,.29,.30) if tile in (0,10) else (.38,.30,.28) if tile == 3 else (.85,.78,.67) if tile in (2,11) else (.85,.85,.85)
        el.color = (*tint,1)
    links.new(index.outputs[0], ramp.inputs[0])
    multiply = nodes.new('ShaderNodeMixRGB'); multiply.blend_type = 'MULTIPLY'; multiply.inputs[0].default_value = 1
    links.new(color.outputs['Color'], multiply.inputs[1]); links.new(ramp.outputs['Color'], multiply.inputs[2])
    links.new(multiply.outputs[0], bs.inputs['Base Color'])
    channels = nodes.new('ShaderNodeSeparateColor'); links.new(orm.outputs['Color'], channels.inputs[0])
    roughness = math_node('ADD', channels.outputs['Green'], .08); roughness.use_clamp = True
    links.new(roughness.outputs[0], bs.inputs['Roughness'])
    bs.inputs['Specular IOR Level'].default_value = .30
    for node in nodes:
        if node.type == 'NORMAL_MAP': node.inputs['Strength'].default_value = .65
        if node.type == 'TEX_IMAGE' and node.image: node.image.pack()
    return material
