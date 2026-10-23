"""用 Blender 无头把 3D 模型转成 glTF（.glb），给 Three.js（R3.gltf）用。
用法：
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup --python <技能目录>/tools/to_gltf.py -- 输入.fbx 输出.glb [--decimate 0.3] [--scale 0.001] [--center]
支持输入：.fbx .obj .stl .ply .glb/.gltf .usd/.usdz/.usdc .abc（Blender 自带的导入器）。
  --decimate R：面数降到 R 倍（大模型给网页用，0.1–0.5）；--scale S：整体缩放（毫米单位的模型用 0.001）；--center：移到原点、落在地面。
其他格式：
  IFC（BIM）：Blender 不自带 IFC 导入。用 IfcOpenShell 的 IfcConvert 直接转：IfcConvert model.ifc model.glb（或装 Bonsai 扩展后在 Blender 里导入）。
  RVT（Revit）：只能在 Revit 里导出 IFC / FBX 再转；DWG/DXF：先转成 FBX/OBJ 或用 Blender 的 DXF 扩展。
"""
import bpy, os, sys

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = os.path.abspath(argv[0]), os.path.abspath(argv[1])
arg = lambda k, d=None: argv[argv.index('--' + k) + 1] if '--' + k in argv else d

bpy.ops.wm.read_factory_settings(use_empty=True)
ext = os.path.splitext(src)[1].lower()
imp = {
    '.fbx': lambda: bpy.ops.import_scene.fbx(filepath=src),
    '.obj': lambda: bpy.ops.wm.obj_import(filepath=src),
    '.stl': lambda: bpy.ops.wm.stl_import(filepath=src),
    '.ply': lambda: bpy.ops.wm.ply_import(filepath=src),
    '.glb': lambda: bpy.ops.import_scene.gltf(filepath=src), '.gltf': lambda: bpy.ops.import_scene.gltf(filepath=src),
    '.usd': lambda: bpy.ops.wm.usd_import(filepath=src), '.usdz': lambda: bpy.ops.wm.usd_import(filepath=src), '.usdc': lambda: bpy.ops.wm.usd_import(filepath=src),
    '.abc': lambda: bpy.ops.wm.alembic_import(filepath=src),
}.get(ext)
if not imp:
    sys.exit(f'不支持 {ext}，见文件头说明（IFC 用 IfcConvert，RVT 先从 Revit 导出）')
imp()
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print(f'导入 {len(meshes)} 个网格，{sum(len(o.data.polygons) for o in meshes):,} 个面')

if arg('scale'):
    s = float(arg('scale'))
    for o in bpy.context.scene.objects:
        if o.parent is None: o.scale = [v * s for v in o.scale]
    bpy.context.view_layer.update()
if arg('decimate'):
    r = float(arg('decimate'))
    for o in meshes:
        m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = r
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=m.name)
    print(f'减面后 {sum(len(o.data.polygons) for o in meshes):,} 个面')
if '--center' in argv and meshes:
    import mathutils
    pts = [o.matrix_world @ mathutils.Vector(c) for o in meshes for c in o.bound_box]
    lo = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    off = mathutils.Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for o in bpy.context.scene.objects:
        if o.parent is None: o.location -= off

bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_apply=True, export_yup=True)
print(f'✔ {dst}  {os.path.getsize(dst) / 1e6:.1f} MB')
