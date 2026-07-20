"""Blender-side scene for the hero render. Not run directly:
scripts/render_hero.py invokes it inside headless Blender as
    blender -b --python hero_scene.py -- <mesh_dir> <out_png> <w> <h> <samples>

One PLY per material lands in mesh_dir (render_hero.py's MATERIALS maps
the cad/ color tags to the names); PBR() below owns what each material
looks like. Studio setup: dark backdrop, warm key, cool fill, strong
rim so the copper and brass read as metal.
"""

import math
import sys

import bpy
from mathutils import Vector

mesh_dir, out_png, width, height, samples = sys.argv[-5:]


def principled(name, **inputs):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    for key, val in inputs.items():
        bsdf.inputs[key.replace("_", " ").title()].default_value = val
    return mat


def PBR(name):
    if name == "oak":
        return principled(name, base_color=(0.27, 0.155, 0.065, 1),
                          roughness=0.4)
    if name == "aluminum":
        return principled(name, base_color=(0.75, 0.76, 0.78, 1),
                          metallic=1.0, roughness=0.32)
    if name == "copper":
        return principled(name, base_color=(0.83, 0.40, 0.26, 1),
                          metallic=1.0, roughness=0.16)
    if name == "brass":
        return principled(name, base_color=(0.78, 0.57, 0.22, 1),
                          metallic=1.0, roughness=0.26)
    if name == "steel":
        return principled(name, base_color=(0.16, 0.16, 0.17, 1),
                          metallic=1.0, roughness=0.5)
    if name == "printed":
        return principled(name, base_color=(0.05, 0.05, 0.05, 1),
                          roughness=0.55)
    if name == "loadcell":
        return principled(name, base_color=(0.55, 0.56, 0.58, 1),
                          metallic=0.9, roughness=0.5)
    if name == "tank":  # frosted glass
        mat = principled(name, base_color=(0.85, 0.90, 0.94, 1),
                         roughness=0.12)
        mat.node_tree.nodes["Principled BSDF"].inputs[
            "Transmission Weight"].default_value = 1.0
        return mat
    raise ValueError(f"no PBR definition for material {name!r}")


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = int(samples)
scene.cycles.use_denoising = True
scene.render.resolution_x = int(width)
scene.render.resolution_y = int(height)

# machine meshes
import pathlib  # noqa: E402

lo = Vector((1e9,) * 3)
hi = Vector((-1e9,) * 3)
for ply in sorted(pathlib.Path(mesh_dir).glob("*.ply")):
    bpy.ops.wm.ply_import(filepath=str(ply))
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj
    obj.scale = (0.001,) * 3  # mm -> m
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(28))
    obj.data.materials.append(PBR(ply.stem))
    for v in obj.data.vertices:
        co = obj.matrix_world @ v.co
        lo = Vector(map(min, lo, co))
        hi = Vector(map(max, hi, co))

center = (lo + hi) / 2
size = hi - lo

# counter the machine stands on: oak-adjacent dark surface
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, lo.z))
bpy.context.object.data.materials.append(
    principled("counter", base_color=(0.035, 0.033, 0.03, 1), roughness=0.3))

# backdrop wall well behind the machine
bpy.ops.mesh.primitive_plane_add(
    size=8, location=(0, hi.y + 1.2, lo.z), rotation=(math.pi / 2, 0, 0))
bpy.context.object.data.materials.append(
    principled("backdrop", base_color=(0.03, 0.032, 0.035, 1), roughness=0.7))


def area_light(loc, target, energy, size, color):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat(
        "-Z", "Y").to_euler()
    return light


# front of the machine is -y (tray side), tank at the back
area_light((-0.8, -1.0, lo.z + 1.1), center, 70, 0.9, (1.0, 0.97, 0.92))
area_light((1.1, -0.5, lo.z + 0.7), center, 22, 1.2, (0.85, 0.90, 1.0))
area_light((0.3, 1.2, lo.z + 1.3), center, 170, 0.6, (1.0, 0.98, 0.95))
scene.view_settings.exposure = -0.7
scene.view_settings.look = "AgX - Punchy"
world = bpy.data.worlds.new("world")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.02, 0.022, 0.025, 1)
bg.inputs["Strength"].default_value = 1.0

# three-quarter front view, slightly low, long lens
azim, elev = math.radians(-30), math.radians(14)
direction = Vector((math.sin(azim) * math.cos(elev),
                    -math.cos(azim) * math.cos(elev),
                    math.sin(elev)))
aim = center + Vector((0, 0, -0.02))
bpy.ops.object.camera_add(location=aim + direction * max(size) * 3.7)
cam = bpy.context.object
cam.data.lens = 85
cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("rendered:", out_png)
