"""Blender 无头渲染：3D 中文字 + 刚体方块砸落 + 子弹时间（物理时间 1× → 0.12× → 1×）+ Cycles 路径追踪。
用法（在项目目录）：
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup --python scene.py -- [--still 2.0] [--from 0 --to 6] [--samples 64] [--scale 100]
  --still T：只渲第 T 秒一帧 → out/blender_T.png；否则渲染序列帧 → frames/blender/f00000.png…（帧号与 30fps 时间一致，可直接给 ffmpeg 或叠进 sy-styles-20）
改 CFG 里的文字、字体、颜色、时长即可复用。渲染设备自动选 OptiX/CUDA（RTX 4070 实测：960×540、16 采样、带运动模糊，120 帧连同物理烘焙共 4 分 24 秒，约 2 秒/帧）。
"""
import bpy, math, os, random, sys

CFG = {
    'title': '炫技', 'font': 'C:/Windows/Fonts/simhei.ttf',
    'title_color': (0.85, 0.22, 0.14), 'cube_colors': [(0.92, 0.9, 0.86), (0.85, 0.22, 0.14), (0.08, 0.08, 0.09)],
    'cubes': 550, 'fps': 30, 'duration': 6.0,
    'slowmo': (0.5, 0.8, 2.4, 3.0),      # 物理时间：1× →(0.5–0.8 减速)→ 0.12× →(2.4–3.0 加速)→ 1×；要卡在方块下落途中（落地后再慢就看不出）
    'bg': (0.02, 0.015, 0.012),
}
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index('--' + k) + 1] if '--' + k in argv else d
OUT = os.getcwd()

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
fps, N = CFG['fps'], int(CFG['duration'] * CFG['fps'])
sc.render.fps, sc.frame_start, sc.frame_end = fps, 0, N - 1
random.seed(7)

# ---------- 渲染设置：Cycles + GPU ----------
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for t in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
    try:
        prefs.compute_device_type = t; prefs.get_devices()
        if any(d.type == t for d in prefs.devices): break
    except Exception: pass
for d in prefs.devices: d.use = d.type != 'CPU'
sc.cycles.device = 'GPU' if any(d.use for d in prefs.devices) else 'CPU'
sc.cycles.samples = int(arg('samples', 64)); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = int(arg('scale', 100))
sc.render.film_transparent = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5

def mat(name, col, rough=0.35, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if coat: b.inputs['Coat Weight'].default_value = coat
    return m

# ---------- 世界、地面 ----------
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (*CFG['bg'], 1)
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
bpy.ops.mesh.primitive_plane_add(size=80)
floor = bpy.context.object; floor.data.materials.append(mat('floor', (0.03, 0.025, 0.022), rough=0.18, coat=0.6))
bpy.ops.rigidbody.world_add(); rbw = sc.rigidbody_world
rbw.point_cache.frame_start, rbw.point_cache.frame_end = 0, N
rbw.substeps_per_frame, rbw.solver_iterations = 20, 20
bpy.ops.rigidbody.object_add(); floor.rigid_body.type = 'PASSIVE'; floor.rigid_body.friction = 0.8

# ---------- 3D 文字（Blender 文字对象支持中文字体） ----------
font = bpy.data.fonts.load(CFG['font'])
bpy.ops.object.text_add(location=(0, 0, 0)); tx = bpy.context.object
tx.data.body = CFG['title']; tx.data.font = font; tx.data.size = 4.2; tx.data.align_x = 'CENTER'
tx.data.extrude = 0.35; tx.data.bevel_depth = 0.03; tx.data.bevel_resolution = 3
tx.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.convert(target='MESH'); tx = bpy.context.object
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
tx.location = (0, 0, tx.dimensions.z / 2)
tx.data.materials.append(mat('title', CFG['title_color'], rough=0.3, coat=0.8))
bpy.ops.rigidbody.object_add(); tx.rigid_body.type = 'PASSIVE'; tx.rigid_body.collision_shape = 'MESH'

# ---------- 刚体方块：从上方倾泻 ----------
mats = [mat(f'c{i}', c, rough=0.25 + 0.2 * i, metal=0.0 if i < 2 else 0.6) for i, c in enumerate(CFG['cube_colors'])]
bpy.ops.mesh.primitive_cube_add(size=0.28); proto = bpy.context.object
bev = proto.modifiers.new('bev', 'BEVEL'); bev.width = 0.025; bev.segments = 2
for i in range(CFG['cubes']):
    o = proto.copy(); o.data = proto.data.copy(); sc.collection.objects.link(o)
    o.location = (random.uniform(-7, 7), random.uniform(0.3, 3.0) if random.random() < 0.8 else random.uniform(-2.5, 0.3), 5 + random.random() * 9)   # 八成落在字后面，前景留给字
    o.rotation_euler = (random.random() * 6, random.random() * 6, random.random() * 6)
    s = random.uniform(0.6, 1.4); o.scale = (s, s, s)
    o.data.materials.append(mats[0 if i % 5 else (1 if i % 2 else 2)])
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.rigidbody.object_add(); o.select_set(False)
    o.rigid_body.mass = 0.3; o.rigid_body.friction = 0.6; o.rigid_body.restitution = 0.25
bpy.data.objects.remove(proto)

# ---------- 子弹时间：给物理世界的 time_scale 打关键帧 ----------
a, b, c, d = (x * fps for x in CFG['slowmo'])
for f, v in ((0, 1.0), (a, 1.0), (b, 0.12), (c, 0.12), (d, 1.0)):
    rbw.time_scale = v; rbw.keyframe_insert('time_scale', frame=int(f))

# ---------- 灯光、相机（缓慢推近 + 下降） ----------
bpy.ops.object.light_add(type='AREA', location=(-4, -6, 8)); k = bpy.context.object; k.data.energy = 2600; k.data.size = 6; k.data.color = (1, 0.92, 0.82)
k.rotation_euler = (math.radians(50), 0, math.radians(-30))
bpy.ops.object.light_add(type='AREA', location=(5, 5, 3)); r = bpy.context.object; r.data.energy = 900; r.data.size = 3; r.data.color = (0.7, 0.8, 1)
r.rotation_euler = (math.radians(-60), 0, math.radians(140))
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
cam.data.lens = 40; cam.data.dof.use_dof = True; cam.data.dof.focus_object = tx; cam.data.dof.aperture_fstop = 2.8
for f, loc in ((0, (0, -17, 2.6)), (N - 1, (0.9, -13, 1.6))):
    cam.location = loc; cam.keyframe_insert('location', frame=f)
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt); tgt.location = (0, 0, tx.dimensions.z * 0.5)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'

# ---------- 烘焙物理 + 渲染 ----------
print('DEVICE', prefs.compute_device_type, sc.cycles.device)
bpy.ops.ptcache.bake_all(bake=True)
if arg('still') is not None:
    f = round(float(arg('still')) * fps); sc.frame_set(f)
    os.makedirs(os.path.join(OUT, 'out'), exist_ok=True)
    sc.render.filepath = os.path.join(OUT, 'out', f"blender_{arg('still')}.png"); bpy.ops.render.render(write_still=True)
else:
    f0, f1 = round(float(arg('from', 0)) * fps), round(float(arg('to', CFG['duration'])) * fps) - 1
    sc.frame_start, sc.frame_end = f0, f1
    sc.render.filepath = os.path.join(OUT, 'frames', 'blender', 'f#####')
    sc.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(animation=True)
