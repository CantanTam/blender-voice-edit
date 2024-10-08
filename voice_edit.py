bl_info = {
    "name": "Voice Edit",
    "blender": (2, 80, 0),
    "category": "Object",
    "version": (1, 0, 0),
    "author": "Canta Tam",
    "description": "结合Ardunio语音模块，用语音命令进行Blender相关操作",
}

from typing import Literal
import bpy
from bpy.types import Context
import serial
import serial.tools.list_ports
import threading
import pyautogui
import math
import blf
import time
import os


# =========== ↓↓↓ 定义类 ↓↓↓ ============

# 自定义“切换标注”菜单的操作项
class VoiceSwitchAnnotationOperator(bpy.types.Operator):
    bl_label = "切换标注操作"
    bl_idname = "object.annotate"

    name: bpy.props.StringProperty()
    
    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name=self.name)
        return {'FINISHED'}

# 自定义”切换标注”菜单
class VoiceSwitchAnnotationMenu(bpy.types.Menu):
    bl_label = "切换标注"
    bl_idname = "VIEW3D_MT_voice_switch_annotation_menu"

    def draw(self, context):
        layout = self.layout
        
        layout.operator("object.annotate", text="标注",icon="IPO_EASE_IN_OUT").name = 'builtin.annotate'
        layout.operator("object.annotate", text="标注直线",icon="IPO_LINEAR").name = 'builtin.annotate_line'
        layout.operator("object.annotate", text="标注多段线",icon="IPO_CONSTANT").name = 'builtin.annotate_polygon'
        layout.operator("object.annotate", text="标注橡皮擦",icon="BRUSH_DATA").name = 'builtin.annotate_eraser'

# 自定义“切换添加”菜单的操作项
class VoiceQuickAddOperator(bpy.types.Operator):
    bl_idname = "object.add_primitive"
    bl_label = "切换添加操作"
    # name: bpy.props.StringProperty() 不能删除
    name: bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name=self.name)
        return {'FINISHED'}
    
# 自定义“切换添加“菜单
class VoiceQuickAddMenu(bpy.types.Menu):
    bl_label = "切换添加"
    bl_idname = "VIEW3D_MT_voice_quick_add_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.add_primitive", text="立方体", icon='MESH_CUBE').name = 'builtin.primitive_cube_add'
        layout.operator("object.add_primitive", text="锥体", icon='CONE').name = 'builtin.primitive_cone_add'
        layout.operator("object.add_primitive", text="柱体", icon='MESH_CYLINDER').name = 'builtin.primitive_cylinder_add'
        layout.operator("object.add_primitive", text="经纬球", icon='MESH_UVSPHERE').name = 'builtin.primitive_uv_sphere_add'
        layout.operator("object.add_primitive", text="棱角球", icon='MESH_ICOSPHERE').name = 'builtin.primitive_ico_sphere_add'

# 自定义“切换坐标系”菜单
class VoiceSwitchOrientationMenu(bpy.types.Menu):
    bl_label = "切换坐标系"
    bl_idname = "VIEW3D_MT_voice_switch_orientation_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.set_orientation", text="全局",icon="ORIENTATION_GLOBAL").orientation = 'GLOBAL'
        layout.operator("transform.set_orientation", text="局部",icon="ORIENTATION_LOCAL").orientation = 'LOCAL'
        layout.operator("transform.set_orientation", text="法向",icon="ORIENTATION_NORMAL").orientation = 'NORMAL'
        layout.operator("transform.set_orientation", text="万向",icon="ORIENTATION_GIMBAL").orientation = 'GIMBAL'
        layout.operator("transform.set_orientation", text="视图",icon="ORIENTATION_VIEW").orientation = 'VIEW'
        layout.operator("transform.set_orientation", text="游标",icon="ORIENTATION_CURSOR").orientation = 'CURSOR'
        layout.operator("transform.set_orientation", text="父级",icon="ORIENTATION_PARENT").orientation = 'PARENT'

# 自定义“切换坐标系”菜单操作项
class VoiceSwitchOrientationOperator(bpy.types.Operator):
    bl_idname = "transform.set_orientation"
    bl_label = "变换坐标系操作"

    orientation: bpy.props.StringProperty()

    def execute(self, context):
        # 设置变换方向
        context.scene.transform_orientation_slots[0].type = self.orientation
        return {'FINISHED'}
    
# 自定义“切换轴心点”菜单操作项
class VoiceSwitchPivotPointOperator(bpy.types.Operator):
    bl_idname = "transform.set_pivot_point"
    bl_label = "设置变换中心点"
    
    pivot: bpy.props.StringProperty()

    def execute(self, context):
        # 设置变换中心点
        context.scene.tool_settings.transform_pivot_point = self.pivot
        return {'FINISHED'}

# 自定义“切换轴心点”菜单
class VoiceSwitchPivotPointMenu(bpy.types.Menu):
    bl_label = "切换轴心点"
    bl_idname = "VIEW3D_MT_voice_switch_pivot_point_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.set_pivot_point", text="边界框中心", icon="PIVOT_BOUNDBOX").pivot = 'BOUNDING_BOX_CENTER'
        layout.operator("transform.set_pivot_point", text="3D 游标", icon="PIVOT_CURSOR").pivot = 'CURSOR'
        layout.operator("transform.set_pivot_point", text="各自的原点", icon="PIVOT_INDIVIDUAL").pivot = 'INDIVIDUAL_ORIGINS'
        layout.operator("transform.set_pivot_point", text="质心点", icon="PIVOT_MEDIAN").pivot = 'MEDIAN_POINT'
        layout.operator("transform.set_pivot_point", text="活动元素", icon="PIVOT_ACTIVE").pivot = 'ACTIVE_ELEMENT'

# 自定义“切换衰减”菜单操作项
class VoiceSwitchFalloffOperator(bpy.types.Operator):
    bl_idname = "mesh.proportional_edit_falloff_set"
    bl_label = "切换衰减操作项"

    type: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.tool_settings.proportional_edit_falloff = self.type
        return {'FINISHED'}

# 自定义“切换衰减”菜单
class VoiceSwitchFalloffMenu(bpy.types.Menu):
    bl_label = "切换衰减"
    bl_idname = "OBJECT_MT_voice_switch_falloff_menu"

    def draw(self, context):
        layout = self.layout

        # 菜单项
        layout.operator("mesh.proportional_edit_falloff_set", text="平滑",icon="SMOOTHCURVE").type = 'SMOOTH'
        layout.operator("mesh.proportional_edit_falloff_set", text="球状",icon="SPHERECURVE").type = 'SPHERE'
        layout.operator("mesh.proportional_edit_falloff_set", text="根凸",icon="ROOTCURVE").type = 'ROOT'
        layout.operator("mesh.proportional_edit_falloff_set", text="平方反比",icon="INVERSESQUARECURVE").type = 'INVERSE_SQUARE'
        layout.operator("mesh.proportional_edit_falloff_set", text="锐利",icon="SHARPCURVE").type = 'SHARP'
        layout.operator("mesh.proportional_edit_falloff_set", text="线性",icon="LINCURVE").type = 'LINEAR'
        layout.operator("mesh.proportional_edit_falloff_set", text="常值",icon="NOCURVE").type = 'CONSTANT'
        layout.operator("mesh.proportional_edit_falloff_set", text="随机",icon="RNDCURVE").type = 'RANDOM'

# 自定义“切换菜单”操作项
class VoiceToCameraView(bpy.types.Operator):
    bl_idname = "view.camera"
    bl_label = "摄像机测试"
    bl_description = "快捷键数字键盘 0"
    def execute(self, context: Context):
        voice_to_camera_view()
        return {'FINISHED'}
    
class VoiceToTopView(bpy.types.Operator):
    bl_idname = "view.topview"
    bl_label = "顶视图"
    def execute(self, context: Context):
        voice_view_top()
        return {'FINISHED'}
    
class VoiceToBottomView(bpy.types.Operator):
    bl_idname = "view.bottomview"
    bl_label = "底视图"
    def execute(self, context: Context):
        voice_view_bottom()
        return {'FINISHED'}
    
class VoiceToFrontView(bpy.types.Operator):
    bl_idname = "view.frontview"
    bl_label = "前视图"
    def execute(self, context: Context):
        voice_view_front()
        return {'FINISHED'}
    
class VoiceToBackView(bpy.types.Operator):
    bl_idname = "view.back"
    bl_label = "后视图"
    def execute(self, context: Context):
        voice_view_back()
        return {'FINISHED'}
    
class VoiceToLeftView(bpy.types.Operator):
    bl_idname = "view.left"
    bl_label = "左视图"
    def execute(self, context: Context):
        voice_view_left()
        return {'FINISHED'}
    
class VoiceToRightView(bpy.types.Operator):
    bl_idname = "view.right"
    bl_label = "右视图"
    def execute(self, context: Context):
        voice_view_right()
        return {'FINISHED'}
    
class VoiceToLocalView(bpy.types.Operator):
    bl_idname = "view.local"
    bl_label = "局部视图"
    def execute(self, context: Context):
        voice_view_part()
        return {'FINISHED'}
    
class VoiceHide(bpy.types.Operator):
    bl_idname = "view.hide"
    bl_label = "隐藏"
    def execute(self, context: Context):
        bpy.app.timers.register(lambda: voice_hide())
        return {'FINISHED'}
    
class VoiceHideOthers(bpy.types.Operator):
    bl_idname = "view.hideothers"
    bl_label = "隐藏其它"
    def execute(self, context: Context):
        bpy.app.timers.register(lambda: voice_hide_others())
        return {'FINISHED'}
    
class VoiceShowHide(bpy.types.Operator):
    bl_idname = "view.showhide"
    bl_label = "显示隐藏"
    def execute(self, context: Context):
        bpy.app.timers.register(lambda: voice_show_hide())
        return {'FINISHED'}
    
class VoiceViewAll(bpy.types.Operator):
    bl_idname = "view.all"
    bl_label = "框显全部"
    def execute(self, context: Context):
        voice_view_all()
        return {'FINISHED'}

class VoiceViewSelected(bpy.types.Operator):
    bl_idname = "view.selected"
    bl_label = "框显所选"
    def execute(self, context: Context):
        voice_view_selected()
        return {'FINISHED'}

# 自定义“切换视图”菜单
class VoiceSwitchViewMenu(bpy.types.Menu):
    bl_idname = "VIEW_MT_switch_view_menu"
    bl_label = "切换视图"

    def draw(self, context):
        layout = self.layout
        layout.operator(VoiceToCameraView.bl_idname,text = "摄像机",icon="CAMERA_DATA")
        layout.separator()
        layout.operator(VoiceViewAll.bl_idname,text="框显全部",icon="SHADING_BBOX")
        layout.operator(VoiceViewSelected.bl_idname,text="框显所选",icon="PIVOT_BOUNDBOX")
        layout.separator()
        layout.operator(VoiceToTopView.bl_idname, text="顶视图")
        layout.operator(VoiceToBottomView.bl_idname, text="底视图")
        layout.operator(VoiceToFrontView.bl_idname, text="前视图")
        layout.operator(VoiceToBackView.bl_idname, text="后视图")
        layout.operator(VoiceToLeftView.bl_idname, text="左视图")
        layout.operator(VoiceToRightView.bl_idname, text="右视图")
        layout.separator()
        layout.operator(VoiceToLocalView.bl_idname, text="局部视图")
        layout.separator()
        layout.operator(VoiceHide.bl_idname, text="隐藏",icon="HIDE_ON")
        layout.operator(VoiceHideOthers.bl_idname, text="隐藏其它",icon="HIDE_ON")
        layout.operator(VoiceShowHide.bl_idname, text="显示隐藏",icon="HIDE_OFF")

# 自定义"细分“菜单操作项，物体模式
class SetObjectSubdivisionLevel(bpy.types.Operator):
    bl_idname = "object.set_subdivision_level"
    bl_label = "物体细分"
    bl_options = {'REGISTER', 'UNDO'}

    level: bpy.props.IntProperty(name="细分级别", default=1, min=0, max=6)
    relative: bpy.props.BoolProperty(name="相对", default=False)

    def execute(self, context):
        if context.active_object and context.active_object.type == 'MESH':
            bpy.ops.object.subdivision_set(level=self.level, relative=self.relative)
            return {'FINISHED'}
        return {'CANCELLED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“细分”菜单操作项，编辑模式
class SetFacedivideLevel(bpy.types.Operator):
    bl_idname = "mesh.subdivide_edges"
    bl_label = "面细分"
    bl_options = {'REGISTER', 'UNDO'}

    number_cuts: bpy.props.IntProperty(name="切割数量", default=1, min=1, max=100)
    smoothness: bpy.props.FloatProperty(name="平滑度", default=0.0, min=0.0, max=1000.0)
    ngon: bpy.props.BoolProperty(name="创建多边形", default=True)
    quadcorner: bpy.props.EnumProperty(
        name="四边形角类型",
        items=[
            ('INNERVERT', "内角", ""),
            ('PATH', "路径", ""),
            ('STRAIGHT_CUT', "直切", ""),
            ('FAN', "扇形", "")
        ],
        default='STRAIGHT_CUT'
    )
    fractal: bpy.props.FloatProperty(name="分形", default=0.0, min=0.0, max=1e+06)
    fractal_along_normal: bpy.props.FloatProperty(name="法线方向分形", default=0.0, min=0.0, max=1.0)
    seed: bpy.props.IntProperty(name="随机种子", default=0, min=0)

    def execute(self, context):
        bpy.ops.mesh.subdivide(
            number_cuts=self.number_cuts,
            smoothness=self.smoothness,
            ngon=self.ngon,
            quadcorner=self.quadcorner,
            fractal=self.fractal,
            fractal_along_normal=self.fractal_along_normal,
            seed=self.seed
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# 自定义“细分”菜单
class VoiceObjectSubdivisionMenu(bpy.types.Menu):
    bl_idname = "VIEW_MT_voice_subdivision"
    bl_label = "细分"

    def draw(self, context):
        layout = self.layout
        layout.operator(SetObjectSubdivisionLevel.bl_idname)
        if context.active_object and context.active_object.type == 'MESH':
            if context.active_object.mode == 'EDIT':
                # 如果选中的是面，隐藏操作
                if context.tool_settings.mesh_select_mode[2] == 1:  # 如果选中面
                    layout.operator(SetFacedivideLevel.bl_idname)  # 隐藏该操作
                else:
                    pass  # 显示操作
            else:
                pass  # 显示操作

# 自定义“添加平面”类
class VoiceAddPlane(bpy.types.Operator):
    bl_idname = "mesh.voice_add_plane"
    bl_label = "添加平面"
    bl_options = {'REGISTER', 'UNDO'}

    size: bpy.props.FloatProperty(name="大小", default=2.0, min=0.0)
    calc_uvs: bpy.props.BoolProperty(name="生成UV", default=True)
    align: bpy.props.EnumProperty(
        name="对齐方式",
        items=[
            ('WORLD', "世界环境", ""),
            ('VIEW', "视图", ""),
            ('CURSOR', "3D游标", "")
        ],
        default='WORLD'
    )
    location: bpy.props.FloatVectorProperty(name="位置", default=(0.0, 0.0, 0.0),subtype='TRANSLATION')
    rotation: bpy.props.FloatVectorProperty(name="旋转", default=(0.0, 0.0, 0.0),subtype='EULER')

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(
            size=self.size,
            calc_uvs=self.calc_uvs,
            align=self.align,
            location=self.location,
            rotation=self.rotation
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“添加立方体”类
class VoiceAddCube(bpy.types.Operator):
    bl_idname = "mesh.voice_add_cube"
    bl_label = "添加立方体"
    bl_options = {'REGISTER', 'UNDO'}

    size: bpy.props.FloatProperty(name="大小", default=2.0, min=0.0)
    calc_uvs: bpy.props.BoolProperty(name="生成UV", default=True)
    align: bpy.props.EnumProperty(
        name="对齐方式",
        items=[
            ('WORLD', "世界环境", ""),
            ('VIEW', "视图", ""),
            ('CURSOR', "3D游标", "")
        ],
        default='WORLD'
    )
    location: bpy.props.FloatVectorProperty(name="位置", default=(0.0, 0.0, 0.0),subtype='TRANSLATION')
    rotation: bpy.props.FloatVectorProperty(name="旋转", default=(0.0, 0.0, 0.0),subtype='EULER')

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(
            size=self.size,
            calc_uvs=self.calc_uvs,
            align=self.align,
            location=self.location,
            rotation=self.rotation
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# 自定义“添加圆环”类
class VoiceAddCircle(bpy.types.Operator):
    bl_idname = "mesh.voice_add_circle"
    bl_label = "添加圆环"
    bl_options = {'REGISTER', 'UNDO'}

    vertices: bpy.props.IntProperty(name="顶点", default=32, min=3)
    radius: bpy.props.FloatProperty(name="半径", default=1,min=0.001)
    fill_type:bpy.props.EnumProperty(
        name="对齐类型",
        items=[
            ('NOTHING',"无",""),
            ('NGON',"多边形",""),
            ('TRIFAN',"三角扇片","")
        ],
        default='NOTHING'
    )
    calc_uvs: bpy.props.BoolProperty(name="生成UV", default=True)
    align: bpy.props.EnumProperty(
        name="对齐方式",
        items=[
            ('WORLD', "世界环境", ""),
            ('VIEW', "视图", ""),
            ('CURSOR', "3D游标", "")
        ],
        default='WORLD'
    )
    location: bpy.props.FloatVectorProperty(name="位置", default=(0.0, 0.0, 0.0),subtype='TRANSLATION')
    rotation: bpy.props.FloatVectorProperty(name="旋转", default=(0.0, 0.0, 0.0),subtype='EULER')

    def execute(self, context):
        bpy.ops.mesh.primitive_circle_add(
            vertices=self.vertices,
            radius=self.radius,
            fill_type=self.fill_type,
            calc_uvs=self.calc_uvs,
            align=self.align,
            location=self.location,
            rotation=self.rotation
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# 自定义“添加经纬球”类
class VoiceAddUVSphere(bpy.types.Operator):
    bl_idname = "mesh.voice_add_uv_sphere"
    bl_label = "添加经纬球"
    bl_options = {'REGISTER', 'UNDO'}

    segments: bpy.props.IntProperty(name="段数", default=32, min=3)
    ring_count: bpy.props.IntProperty(name="环", default=16,min=3)
    radius: bpy.props.FloatProperty(name="半径",default=1,min=0.001)
    calc_uvs: bpy.props.BoolProperty(name="生成UV", default=True)
    align: bpy.props.EnumProperty(
        name="对齐方式",
        items=[
            ('WORLD', "世界环境", ""),
            ('VIEW', "视图", ""),
            ('CURSOR', "3D游标", "")
        ],
        default='WORLD'
    )
    location: bpy.props.FloatVectorProperty(name="位置", default=(0.0, 0.0, 0.0),subtype='TRANSLATION')
    rotation: bpy.props.FloatVectorProperty(name="旋转", default=(0.0, 0.0, 0.0),subtype='EULER')

    def execute(self, context):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=self.segments,
            ring_count=self.ring_count,
            radius=self.radius,
            calc_uvs=self.calc_uvs,
            align=self.align,
            location=self.location,
            rotation=self.rotation
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“添加棱角球”类
class VoiceAddIcoSphere(bpy.types.Operator):
    bl_idname = "mesh.voice_add_ico_sphere"
    bl_label = "添加棱角球"
    bl_options = {'REGISTER', 'UNDO'}

    subdivisions: bpy.props.IntProperty(name="细分", default=2, max=10,min=1)
    radius: bpy.props.FloatProperty(name="半径",default=1,min=0.001)
    calc_uvs: bpy.props.BoolProperty(name="生成UV", default=True)
    align: bpy.props.EnumProperty(
        name="对齐",
        items=[
            ('WORLD', "世界环境", ""),
            ('VIEW', "视图", ""),
            ('CURSOR', "3D游标", "")
        ],
        default='WORLD'
    )
    location: bpy.props.FloatVectorProperty(name="位置", default=(0.0, 0.0, 0.0),subtype='TRANSLATION')
    rotation: bpy.props.FloatVectorProperty(name="旋转", default=(0.0, 0.0, 0.0),subtype='EULER')

    def execute(self, context):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=self.subdivisions,
            radius=self.radius,
            calc_uvs=self.calc_uvs,
            align=self.align,
            location=self.location,
            rotation=self.rotation
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“添加柱体”类
class VoiceAddCylinder(bpy.types.Operator):
    bl_idname = "mesh.voice_add_cylinder"
    bl_label = "添加柱体"
    bl_options = {'REGISTER', 'UNDO'}

    vertices: bpy.props.IntProperty(name="顶点", default=32, max=500,min=3)
    radius: bpy.props.FloatProperty(name="半径",default=1,min=0.001)
    depth: bpy.props.FloatProperty(name="深度",default=2,min=0.001)
    end_fill_type: bpy.props.EnumProperty(
        name="封盖类型",
        items=[
            ('NOTHING',"无",""),
            ('NGON',"多边形",""),
            ('TRIFAN',"三角扇片","")
        ],
        default='NGON'
    )
    calc_uvs: bpy.props.BoolProperty(name="生成UV", default=True)
    align: bpy.props.EnumProperty(
        name="对齐",
        items=[
            ('WORLD', "世界环境", ""),
            ('VIEW', "视图", ""),
            ('CURSOR', "3D游标", "")
        ],
        default='WORLD'
    )
    location: bpy.props.FloatVectorProperty(name="位置", default=(0.0, 0.0, 0.0),subtype='TRANSLATION')
    rotation: bpy.props.FloatVectorProperty(name="旋转", default=(0.0, 0.0, 0.0),subtype='EULER')

    def execute(self, context):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=self.vertices,
            radius=self.radius,
            depth=self.depth,
            end_fill_type=self.end_fill_type,
            calc_uvs=self.calc_uvs,
            align=self.align,
            location=self.location,
            rotation=self.rotation
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# 自定义“添加锥体”类
class VoiceAddCone(bpy.types.Operator):
    bl_idname = "mesh.voice_add_cone"
    bl_label = "添加锥体"
    bl_options = {'REGISTER', 'UNDO'}

    vertices: bpy.props.IntProperty(name="顶点", default=32, max=500,min=3)
    radius1: bpy.props.FloatProperty(name="半径1",default=1,min=0.001)
    radius2: bpy.props.FloatProperty(name="半径2",default=0,min=0)
    depth: bpy.props.FloatProperty(name="深度",default=2,min=0.001)
    end_fill_type: bpy.props.EnumProperty(
        name="底盖类型",
        items=[
            ('NOTHING',"无",""),
            ('NGON',"多边形",""),
            ('TRIFAN',"三角扇片","")
        ],
        default='NGON'
    )
    calc_uvs: bpy.props.BoolProperty(name="生成UV", default=True)
    align: bpy.props.EnumProperty(
        name="对齐",
        items=[
            ('WORLD', "世界环境", ""),
            ('VIEW', "视图", ""),
            ('CURSOR', "3D游标", "")
        ],
        default='WORLD'
    )
    location: bpy.props.FloatVectorProperty(name="位置", default=(0.0, 0.0, 0.0),subtype='TRANSLATION')
    rotation: bpy.props.FloatVectorProperty(name="旋转", default=(0.0, 0.0, 0.0),subtype='EULER')

    def execute(self, context):
        bpy.ops.mesh.primitive_cone_add(
            vertices=self.vertices,
            radius1=self.radius1,
            radius2=self.radius2,
            depth=self.depth,
            end_fill_type=self.end_fill_type,
            calc_uvs=self.calc_uvs,
            align=self.align,
            location=self.location,
            rotation=self.rotation
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“添加环体”类
class VoiceAddTorus(bpy.types.Operator):
    bl_idname = "mesh.voice_add_torus"
    bl_label = "添加环体"
    bl_options = {'REGISTER', 'UNDO','PRESET'}

    major_segments: bpy.props.IntProperty(name="主环段数",default=48,max=256,min=3)
    minor_segments: bpy.props.IntProperty(name="小环段数",default=12,max=256,min=3)
    mode: bpy.props.EnumProperty(
        name="尺寸模式",
        items=[
            ('MAJOR_MINOR',"主环/小环",""),
            ('EXT_INT',"外径/内径","")
        ],
        default='MAJOR_MINOR'
    )
    major_radius: bpy.props.FloatProperty(name="主环半径",default=1,min=0)
    minor_radius: bpy.props.FloatProperty(name="小环半径",default=0.25,min=0)
    abso_major_rad: bpy.props.FloatProperty(name="外径",default=1.2,min=0)
    abso_minor_rad: bpy.props.FloatProperty(name="内径",default=0.75,min=0)
    generate_uvs: bpy.props.BoolProperty(name="生成UV", default=True)
    align: bpy.props.EnumProperty(
        name="对齐",
        items=[
            ('WORLD', "世界环境", ""),
            ('VIEW', "视图", ""),
            ('CURSOR', "3D游标", "")
        ],
        default='WORLD'
    )
    location: bpy.props.FloatVectorProperty(name="位置", default=(0.0, 0.0, 0.0),subtype='TRANSLATION')
    rotation: bpy.props.FloatVectorProperty(name="旋转", default=(0.0, 0.0, 0.0),subtype='EULER')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True # 分隔属性名称和数值，参考官方 api 说明
        layout.use_property_decorate = False

        layout.prop(self, "major_segments")
        layout.prop(self, "minor_segments")
        layout.prop(self, "mode")

        # 根据当前模式显示不同的属性
        if self.mode == 'MAJOR_MINOR':
            layout.prop(self, "major_radius")
            layout.prop(self, "minor_radius")
        else:
            layout.prop(self, "abso_major_rad")
            layout.prop(self, "abso_minor_rad")

        layout.prop(self, "generate_uvs")
        layout.prop(self, "location")
        layout.prop(self, "rotation")

    def execute(self, context):
        bpy.ops.mesh.primitive_torus_add(
            major_segments=self.major_segments,
            minor_segments=self.minor_segments,
            mode=self.mode,
            major_radius=self.major_radius,
            minor_radius=self.minor_radius,
            abso_major_rad=self.abso_major_rad,
            abso_minor_rad=self.abso_minor_rad,
            generate_uvs=self.generate_uvs,
            align=self.align,
            location=self.location,
            rotation=self.rotation

        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# 自定义“切换原点”菜单
class VoiceSwitchOriginMenu(bpy.types.Menu):
    bl_label = "切换原点"
    bl_idname = "OBJECT_MT_voice_switch_origin_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.voice_switch_origin_set", text="几何中心->原点").type = 'GEOMETRY_ORIGIN'
        layout.operator("object.voice_switch_origin_set", text="原点->几何中心").type = 'ORIGIN_GEOMETRY'
        layout.operator("object.voice_switch_origin_set", text="原点->3D游标").type = 'ORIGIN_CURSOR'
        layout.operator("object.voice_switch_origin_set", text="原点->质心(表面)").type = 'ORIGIN_CENTER_OF_MASS'
        layout.operator("object.voice_switch_origin_set", text="原点->质心(体积)").type = 'ORIGIN_CENTER_OF_VOLUME'

# 自定义“切换原点”操作项
class VoiceSwitchOriginOperator(bpy.types.Operator):
    bl_idname = "object.voice_switch_origin_set"
    bl_label = "设置对象原点"
    type: bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.object.origin_set(type=self.type, center='MEDIAN')
        return {'FINISHED'}
    
# 自定义”间隔式弃选“弹出菜单类
class VoiceSelectNTH(bpy.types.Operator):
    bl_idname = "mesh.voice_select_nth"
    bl_label = "间隔式弃选"
    bl_options = {'REGISTER', 'UNDO'}

    skip: bpy.props.IntProperty(name="弃选项", default=1)
    nth: bpy.props.IntProperty(name="选中项", default=1)
    offset: bpy.props.IntProperty(name="偏移量", default=0)

    def execute(self, context):
        bpy.ops.mesh.select_nth(
            skip=self.skip,
            nth=self.nth,
            offset=self.offset
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“扩展选区”参数设置弹出菜单
class VoiceSelectMoreSetting(bpy.types.Operator):
    bl_idname = "mesh.voice_select_more_setting"
    bl_label = "扩展选区/加选"
    bl_options = {'REGISTER', 'UNDO'}

    more_use_face_step: bpy.props.BoolProperty(name="面步长", default=True)

    def execute(self, context):
        # 更新场景属性
        context.scene.more_use_face_step = self.more_use_face_step
        return {'FINISHED'}

    def invoke(self, context, event):
        # 从场景中读取之前保存的状态
        self.more_use_face_step = context.scene.get("more_use_face_step", True)
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“缩减选区”参数设置弹出菜单
class VoiceSelectLessSetting(bpy.types.Operator):
    bl_idname = "mesh.voice_select_less_setting"
    bl_label = "缩减选区/减选"
    bl_options = {'REGISTER', 'UNDO'}

    less_use_face_step: bpy.props.BoolProperty(name="面步长", default=True)

    def execute(self, context):
        # 更新场景属性
        context.scene.less_use_face_step = self.less_use_face_step
        return {'FINISHED'}

    def invoke(self, context, event):
        # 从场景中读取之前保存的状态
        self.less_use_face_step = context.scene.get("less_use_face_step", True)
        return context.window_manager.invoke_props_dialog(self)

# 自定义“分离“菜单
class VoiceSwitchSeparateMenu(bpy.types.Menu):
    bl_label = "分离"
    bl_idname = "Edit_MT_voice_switch_separate_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.separate", text="选中项").type = 'SELECTED'
        layout.operator("mesh.separate", text="按材质").type = 'MATERIAL'
        layout.operator("mesh.separate", text="按松散块").type = 'LOOSE'

# 自定义“边线折痕” props 菜单
class VoiceEdgeCreaseOperator(bpy.types.Operator):
    bl_idname = "mesh.voice_edge_crease"
    bl_label = "边线折痕"
    bl_options = {'REGISTER','UNDO'}

    value: bpy.props.FloatProperty(name="系数",default=0)

    def execute(self, context):
        bpy.ops.transform.edge_crease(
            value=self.value
        )
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# 自定义“融并边” props 菜单
class VoiceDissolveEdgeOperator(bpy.types.Operator):
    bl_idname = "mesh.voice_dissolve_edge"
    bl_label = "融并边"
    bl_options = {'REGISTER','UNDO'}

    use_verts: bpy.props.BoolProperty(name="融并顶点", default=True)
    use_face_split: bpy.props.BoolProperty(name="分离面",default=False )

    def execute(self, context):
        bpy.ops.mesh.dissolve_edges(
            use_verts=self.use_verts,
            use_face_split=self.use_face_split
        )
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“切换填充”菜单
class VoiceSwitchFillFaceMenu(bpy.types.Menu):
    bl_idname = "VIEW_MT_switch_fill_face_menu"
    bl_label = "切换填充"

    def draw(self, context):
        layout = self.layout
        layout.operator(VoiceFillFaceOperator.bl_idname,text = "填充")
        layout.operator(VoiceGridFillFaceOperator.bl_idname,text="栅格填充")
        layout.operator(VoiceBeautifyFillFaceOperator.bl_idname,text="完美建面")

# 自定义“填充” props 操作项
class VoiceFillFaceOperator(bpy.types.Operator):
    bl_idname = "mesh.voice_fill_face"
    bl_label = "填充"
    bl_options = {'REGISTER','UNDO'}

    use_beauty: bpy.props.BoolProperty(name="布线优化", default=True)

    def execute(self, context):
        bpy.ops.mesh.fill(
            use_beauty=self.use_beauty
        )
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“栅格填充” props 操作项
class VoiceGridFillFaceOperator(bpy.types.Operator):
    bl_idname = "mesh.voice_grid_fill_face"
    bl_label = "栅格填充"
    bl_options = {'REGISTER','UNDO'}

    span: bpy.props.IntProperty(name="跨分",min=1,max=1000)
    offset: bpy.props.IntProperty(name="偏移量", min=-1000, max=1000, default=0)
    use_interp_simple: bpy.props.BoolProperty(name="简单混合", default=False)

    def execute(self, context):
        bpy.ops.mesh.fill_grid(
            span=self.span,
            offset=self.offset,
            use_interp_simple=self.use_interp_simple
        )
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# 自定义“完美建面” props 操作项
class VoiceBeautifyFillFaceOperator(bpy.types.Operator):
    bl_idname = "mesh.voice_beautify_fill_face"
    bl_label = "完美建面"
    bl_options = {'REGISTER', 'UNDO'}

    # 用户输入的角度是度数，限制为一位小数
    angle_limit_degrees: bpy.props.FloatProperty(
        name="最大角度 (°)", 
        min=0, 
        max=180, 
        default=180,  # 默认值以度为单位
        precision=1   # 限制为一位小数
    )

    def execute(self, context):
        # 将度数转换为弧度，并调用 beautify_fill 操作
        angle_limit_radians = math.radians(self.angle_limit_degrees)
        bpy.ops.mesh.beautify_fill(angle_limit=angle_limit_radians)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# 雕刻模式“切换遮罩”菜单
class VoiceSwitchSculptMaskBrushMenu(bpy.types.Menu):
    bl_idname = "SCULPT_MT_switch_mask_brush"
    bl_label = "切换遮罩"

    def draw(self, context):
        layout = self.layout
        layout.operator(VoiceSwitchSculptBoxMask.bl_idname)
        layout.operator(VoiceSwitchSculptLassoMask.bl_idname)
        layout.operator(VoiceSwitchSculptLineMask.bl_idname)
        layout.operator(VoiceSwitchSculptPolylineMask.bl_idname)

# 雕刻模式“框选遮罩”操作项
class VoiceSwitchSculptBoxMask(bpy.types.Operator):
    bl_idname = "sculpt.boxmask"
    bl_label = "框选遮罩"
    def execute(self, context: Context):
        voice_brush_boxmask()
        return {'FINISHED'}

# 雕刻模式“套索遮罩”操作项
class VoiceSwitchSculptLassoMask(bpy.types.Operator):
    bl_idname = "sculpt.lassomask"
    bl_label = "套索遮罩"
    def execute(self, context: Context):
        voice_brush_lassomask()
        return {'FINISHED'}
    
# 雕刻模式“划线遮罩”操作项
class VoiceSwitchSculptLineMask(bpy.types.Operator):
    bl_idname = "sculpt.linemask"
    bl_label = "线性遮罩"
    def execute(self, context: Context):
        voice_brush_linemask()
        return {'FINISHED'}
    
class VoiceSwitchSculptPolylineMask(bpy.types.Operator):
    bl_idname = "sculpt.polylinemask"
    bl_label = "折线遮罩"
    def execute(self, context: Context):
        voice_brush_polylinemask()
        return {'FINISHED'}
    
# -----------------------------------------------------

# 雕刻模式“切换隐藏”菜单
class VoiceSwitchSculptHideBrushMenu(bpy.types.Menu):
    bl_idname = "SCULPT_MT_switch_hide_brush"
    bl_label = "切换隐藏"

    def draw(self, context):
        layout = self.layout
        layout.operator(VoiceSculptBoxHide.bl_idname)
        layout.operator(VoiceSculptLassoHide.bl_idname)
        layout.operator(VoiceSculptLineHide.bl_idname)
        layout.operator(VoiceSculptPolylineHide.bl_idname)

# 雕刻模式“框选隐藏”操作项
class VoiceSculptBoxHide(bpy.types.Operator):
    bl_idname = "sculpt.boxhide"
    bl_label = "框选隐藏"
    def execute(self, context: Context):
        voice_brush_boxhide()
        return {'FINISHED'}
    
# 雕刻模式“套索隐藏”操作项
class VoiceSculptLassoHide(bpy.types.Operator):
    bl_idname = "sculpt.lassohide"
    bl_label = "套索隐藏"
    def execute(self, context: Context):
        voice_brush_lassohide()
        return {'FINISHED'}
    
# 雕刻模式“划线隐藏”操作项
class VoiceSculptLineHide(bpy.types.Operator):
    bl_idname = "sculpt.linehide"
    bl_label = "划线隐藏"
    def execute(self, context: Context):
        voice_brush_linehide()
        return {'FINISHED'}
    
# 雕刻模式“折线隐藏”操作项
class VoiceSculptPolylineHide(bpy.types.Operator):
    bl_idname = "sculpt.polylinehide"
    bl_label = "折线隐藏"
    def execute(self, context: Context):
        voice_brush_polylinehide()
        return {'FINISHED'}
    
# -----------------------------------------------------

class VoiceSwitchSculptFacesetBrushMenu(bpy.types.Menu):
    bl_idname = "SCULPT_MT_switch_faceset_brush"
    bl_label = "切换面组"

    def draw(self, context):
        layout = self.layout
        layout.operator(VoiceSculptBoxFaceset.bl_idname)
        layout.operator(VoiceSculptLassoFaceset.bl_idname)
        layout.operator(VoiceSculptLineFaceset.bl_idname)
        layout.operator(VoiceSculptPolylineFaceset.bl_idname)

# 雕刻模式“框选面组”操作项
class VoiceSculptBoxFaceset(bpy.types.Operator):
    bl_idname = "sculpt.boxfaceset"
    bl_label = "框选面组"
    def execute(self, context: Context):
        voice_brush_boxfaceset()
        return {'FINISHED'}
    
# 雕刻模式“套索面组”操作项
class VoiceSculptLassoFaceset(bpy.types.Operator):
    bl_idname = "sculpt.lassofaceset"
    bl_label = "套索面组"
    def execute(self, context: Context):
        voice_brush_lassofaceset()
        return {'FINISHED'}
    
# 雕刻模式“划线面组”操作项
class VoiceSculptLineFaceset(bpy.types.Operator):
    bl_idname = "sculpt.linefaceset"
    bl_label = "划线面组"
    def execute(self, context: Context):
        voice_brush_linefaceset()
        return {'FINISHED'}
    
# 雕刻模式“折线面组”操作项
class VoiceSculptPolylineFaceset(bpy.types.Operator):
    bl_idname = "sculpt.polylinefaceset"
    bl_label = "折线面组"
    def execute(self, context: Context):
        voice_brush_polylinefaceset()
        return {'FINISHED'}
    
# -----------------------------------------------------

class VoiceSwitchSculptTrimBrushMenu(bpy.types.Menu):
    bl_idname = "SCULPT_MT_switch_trim_brush"
    bl_label = "切换修剪"

    def draw(self, context):
        layout = self.layout
        layout.operator(VoiceSculptBoxTrim.bl_idname)
        layout.operator(VoiceSculptLassoTrim.bl_idname)
        layout.operator(VoiceSculptLineTrim.bl_idname)
        layout.operator(VoiceSculptPolylineTrim.bl_idname)

# 雕刻模式“框选修剪”操作项
class VoiceSculptBoxTrim(bpy.types.Operator):
    bl_idname = "sculpt.boxtrim"
    bl_label = "框选修剪"
    def execute(self, context: Context):
        voice_brush_boxtrim()
        return {'FINISHED'}
    
# 雕刻模式“套索修剪”操作项
class VoiceSculptLassoTrim(bpy.types.Operator):
    bl_idname = "sculpt.lassotrim"
    bl_label = "套索修剪"
    def execute(self, context: Context):
        voice_brush_lassotrim()
        return {'FINISHED'}
    
# 雕刻模式“划线修剪”操作项
class VoiceSculptLineTrim(bpy.types.Operator):
    bl_idname = "sculpt.linetrim"
    bl_label = "划线修剪"
    def execute(self, context: Context):
        voice_brush_linetrim()
        return {'FINISHED'}
    
# 雕刻模式“折线修剪”操作项
class VoiceSculptPolylineTrim(bpy.types.Operator):
    bl_idname = "sculpt.polylinetrim"
    bl_label = "折线修剪"
    def execute(self, context: Context):
        voice_brush_polylinetrim()
        return {'FINISHED'}

# =========== ↑↑↑ 定义类 ↑↑↑ ============

# ==========↓↓↓↓↓ 通用操作 ↓↓↓↓↓========== #
# 判定是否是”物体模式“？
def is_object_mode():
    return bpy.context.active_object.mode == 'OBJECT'

# 切换到”物体模式“
def to_object_mode():
    bpy.ops.object.mode_set(mode='OBJECT')

# 判定是否是”编辑模式“？
def is_edit_mode():
    return bpy.context.active_object.mode == 'EDIT'

# 切换”编辑模式“
def to_edit_mode():
    bpy.ops.object.mode_set(mode='EDIT')

# 判定是否是“雕刻模式”？
def is_sculpt_mode():
    return bpy.context.active_object.mode == 'SCULPT'

# 切换“雕刻模式”
def to_sculpt_mode():
    bpy.ops.object.mode_set(mode='SCULPT')

# 调出“添加”菜单，object模式和mesh模式有区别
def voice_add():
    if not bpy.context.active_object:
        # 检查是否有任何对象
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    pyautogui.keyDown('shift')
    pyautogui.press('a')
    pyautogui.keyUp('shift')

# 调出“删除”菜单
def voice_delete():
    if is_object_mode() or is_edit_mode():
        pyautogui.press('x')
        
# 调出工具选择菜单
def voice_select_mode_menu():
    for area in bpy.context.screen.areas: # 确保上下文在 VIEW_3D 区域
        if area.type == 'VIEW_3D':
            with bpy.context.temp_override(area=area):
                bpy.ops.wm.toolbar_fallback_pie('INVOKE_DEFAULT')
            return
        
# 模拟“G”键进行移动
def voice_move():
    if is_object_mode() or is_edit_mode():
        pyautogui.press('g')

# 模拟“R”键进行旋转
def voice_rotate():
    if is_object_mode() or is_edit_mode():
        pyautogui.press('r')

# 模拟“S”键进行缩放
def voice_scale():
    if is_object_mode() or is_edit_mode():
        pyautogui.press('s')
    elif is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE5:
            pyautogui.keyDown('ctrl')
            operator_tip_upper_ctrl("-  中键缩放  +", font_size=30.0, color=(1.0, 1.0, 1.0, 0.3), hoffset=45, voffset=70)
            operator_tip_lower_ctrl("[取消缩放]取消", font_size=30.0, color=(0.0, 1.0, 1.0, 0.3), hoffset=40, voffset=20)

# 调用自定义的“切换标注”菜单
def voice_switch_annotation_mode():
    if is_object_mode() or is_edit_mode() or is_sculpt_mode():
        bpy.ops.wm.call_menu(name='VIEW3D_MT_voice_switch_annotation_menu')

# 调用自定义的”切换添加“菜单
def voice_quick_add():
    if is_object_mode() or is_edit_mode():
        bpy.ops.wm.call_menu(name='VIEW3D_MT_voice_quick_add_menu')

# 调用自定义的“切换坐标系”菜单
def voice_switch_orientation_menu():
    if is_object_mode() or is_edit_mode():
        bpy.ops.wm.call_menu(name='VIEW3D_MT_voice_switch_orientation_menu')

# 调用自定义的“切换轴心点”菜单
def voice_switch_pivot_menu():
    if is_object_mode() or is_edit_mode():
        bpy.ops.wm.call_menu(name='VIEW3D_MT_voice_switch_pivot_point_menu')

# 自定义“开/关吸附”函数
def voice_on_off_snap():
    if is_object_mode() or is_edit_mode():
        bpy.data.scenes["Scene"].tool_settings.use_snap = not bpy.data.scenes["Scene"].tool_settings.use_snap
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            if bpy.data.scenes["Scene"].tool_settings.use_snap == True:
                draw_text("吸附开●", font_size=50.0, color=(0.0, 1.0, 0.0, 0.3), duration=2.0)
            elif bpy.data.scenes["Scene"].tool_settings.use_snap == False:
                draw_text("吸附关○", font_size=50.0, color=(1.0, 0.0, 0.0, 0.3), duration=2.0)

# 调用”切换吸附”菜单
def voice_snap_menu():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            with bpy.context.temp_override(area=area):
                if is_object_mode() or is_edit_mode():
                    bpy.ops.wm.call_menu(name="VIEW3D_MT_snap")
            return
    print("")
        
# 自定义“开/关衰减”函数
def voice_on_off_falloff():
    if is_object_mode():
        bpy.data.scenes["Scene"].tool_settings.use_proportional_edit_objects = not bpy.data.scenes["Scene"].tool_settings.use_proportional_edit_objects
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            if bpy.data.scenes["Scene"].tool_settings.use_proportional_edit_objects == True:
                draw_text("衰减开●", font_size=50.0, color=(0.0, 1.0, 0.0, 0.3), duration=2.0)
            elif bpy.data.scenes["Scene"].tool_settings.use_proportional_edit_objects == False:
                draw_text("衰减关○", font_size=50.0, color=(1.0, 0.0, 0.0, 0.3), duration=2.0)
    elif is_edit_mode():
        bpy.data.scenes["Scene"].tool_settings.use_proportional_edit = not bpy.data.scenes["Scene"].tool_settings.use_proportional_edit
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            if bpy.data.scenes["Scene"].tool_settings.use_proportional_edit == True:
                draw_text("衰减开●", font_size=50.0, color=(0.0, 1.0, 0.0, 0.3), duration=2.0)
            elif bpy.data.scenes["Scene"].tool_settings.use_proportional_edit == False:
                draw_text("衰减关○", font_size=50.0, color=(1.0, 0.0, 0.0, 0.3), duration=2.0)

# 调用“切换衰减”菜单
def voice_falloff_menu():
    if is_object_mode() or is_edit_mode():
        bpy.ops.wm.call_menu(name="OBJECT_MT_voice_switch_falloff_menu")

# 调用“切换着色”菜单
def voice_shading_menu():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            with bpy.context.temp_override(area=area):
                bpy.ops.wm.call_menu_pie(name="VIEW3D_MT_shading_ex_pie")

# “线框/实体”开头切换
def voice_on_off_wireframe():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            if space.shading.type == 'WIREFRAME':
                space.shading.type = 'SOLID'
            else:
                space.shading.type = 'WIREFRAME'
            break  # 找到一个 VIEW_3D 就退出循环

# 调用“切换视图”菜单
def voice_switch_view_menu():
    if is_object_mode() or is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW_MT_switch_view_menu")

# 切换到摄像机视图
def voice_to_camera_view():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 找到该区域中的有效区域
            for region in area.regions:
                if region.type == 'WINDOW':
                    override = bpy.context.copy()
                    override['area'] = area
                    override['region'] = region
                    override['space'] = area.spaces.active

                    with bpy.context.temp_override(**override):
                        if bpy.context.scene.camera:
                            bpy.ops.view3d.view_camera()
                        else:
                            print("No active camera in the scene.")
                    break  # 找到一个 VIEW_3D 就退出循环
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义”框选全部“函数
def voice_view_all():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.view_all(center=False)  # 调用操作
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义”框选所选“函数
def voice_view_selected():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.view_selected(use_all_regions=False)  # 调用操作
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义“顶视图”函数
def voice_view_top():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.view_axis(type='TOP')  # 调用操作
                if bpy.context.preferences.addons[__name__].preferences.operatorE1:
                    draw_text("▴ 顶视图", font_size=50.0, color=(0.0, 0.5, 1.0, 0.7), duration=3.0)
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义“底视图”函数
def voice_view_bottom():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.view_axis(type='BOTTOM')  # 调用操作
                if bpy.context.preferences.addons[__name__].preferences.operatorE1:
                    draw_text("▾ 底视图", font_size=50.0, color=(0.0, 0.5, 1.0, 0.7), duration=3.0)
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义“前视图”函数
def voice_view_front():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.view_axis(type='FRONT')  # 调用操作
                if bpy.context.preferences.addons[__name__].preferences.operatorE1:
                    draw_text("☉ 前视图", font_size=50.0, color=(0.0, 1.0, 0.0, 0.7), duration=3.0)
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义“后视图”函数
def voice_view_back():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.view_axis(type='BACK')  # 调用操作
                if bpy.context.preferences.addons[__name__].preferences.operatorE1:
                    draw_text("○ 后视图", font_size=50.0, color=(0.0, 1.0, 0.0, 0.7), duration=3.0)
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义“左视图”函数
def voice_view_left():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.view_axis(type='LEFT')  # 调用操作
                if bpy.context.preferences.addons[__name__].preferences.operatorE1:
                    draw_text("◂ 左视图", font_size=50.0, color=(1.0, 0.0, 0.0, 0.7), duration=3.0)
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义“右视图”函数
def voice_view_right():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.view_axis(type='RIGHT')  # 调用操作
                if bpy.context.preferences.addons[__name__].preferences.operatorE1:
                    draw_text("▸ 右视图", font_size=50.0, color=(1.0, 0.0, 0.0, 0.7), duration=3.0)
            break  # 找到一个 VIEW_3D 就退出循环

# 自定义“开关局部显示”函数
def voice_view_part():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            # 调用操作
            with bpy.context.temp_override(area=area, region=override['region']):
                bpy.ops.view3d.localview() # 调用操作
            break  # 找到一个 VIEW_3D 就退出循环


# 自定义“隐藏”函数
def voice_hide():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            if is_object_mode():  # 调用操作
                with bpy.context.temp_override(area=area, region=override['region']):
                    bpy.ops.object.hide_view_set(unselected=False)  # 调用操作
                break  # 找到一个 VIEW_3D 就退出循环
            elif is_edit_mode():
                with bpy.context.temp_override(area=area, region=override['region']):
                    bpy.ops.mesh.hide(unselected=False)
                break  # 找到一个 VIEW_3D 就退出循环

# 自定义“隐藏其它”函数
def voice_hide_others():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            if is_object_mode():  # 调用操作
                with bpy.context.temp_override(area=area, region=override['region']):
                    bpy.ops.object.hide_view_set(unselected=True)  # 调用操作
                break  # 找到一个 VIEW_3D 就退出循环
            elif is_edit_mode():
                with bpy.context.temp_override(area=area, region=override['region']):
                    bpy.ops.mesh.hide(unselected=True)
                break  # 找到一个 VIEW_3D 就退出循环

# 自定义“显示隐藏”函数
def voice_show_hide():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()  # 创建上下文副本
            for region in area.regions:
                if region.type == 'WINDOW':
                    override['region'] = region  # 设置窗口区域
                    break
            
            if is_object_mode():  # 调用操作
                with bpy.context.temp_override(area=area, region=override['region']):
                    bpy.ops.object.hide_view_clear()  # 调用操作
                break  # 找到一个 VIEW_3D 就退出循环
            elif is_edit_mode():
                with bpy.context.temp_override(area=area, region=override['region']):
                    bpy.ops.mesh.reveal()
                break  # 找到一个 VIEW_3D 就退出循环

# 自定义“全选”
def voice_select_all():
    if is_object_mode or is_edit_mode():
        if is_object_mode():
            bpy.ops.object.select_all(action='SELECT')
        else:
            bpy.ops.mesh.select_all(action='SELECT')

# 自定义“反选”
def voice_select_inverse():
    if is_object_mode or is_edit_mode():
        if is_object_mode():
            bpy.ops.object.select_all(action='INVERT')
        else:
            bpy.ops.mesh.select_all(action='INVERT')

# 自定义“添加平面”
def voice_add_plane():
    if not bpy.context.active_object:
        # 检查是否有任何对象
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_add_plane('INVOKE_DEFAULT')

# 自定义“添加立方体”
def voice_add_cube():
    if not bpy.context.active_object:
        # 检查是否有任何对象
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_add_cube('INVOKE_DEFAULT')

# 自定义“添加圆环”
def voice_add_circle():
    if not bpy.context.active_object:
        # 检查是否有任何对象
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_add_circle('INVOKE_DEFAULT')

# 自定义“添加经纬球”
def voice_add_uv_sphere():
    if not bpy.context.active_object:
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_add_uv_sphere('INVOKE_DEFAULT')

# 自定义”添加棱角球“
def voice_add_ico_sphere():
    if not bpy.context.active_object:
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_add_ico_sphere('INVOKE_DEFAULT')

# 自定义“添加柱体”
def voice_add_cylinder():
    if not bpy.context.active_object:
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_add_cylinder('INVOKE_DEFAULT')

# 自定义“添加锥体”
def voice_add_cone():
    if not bpy.context.active_object:
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_add_cone('INVOKE_DEFAULT')

# 自定义“添加环体”
def voice_add_torus():
    if not bpy.context.active_object:
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_add_torus('INVOKE_DEFAULT')

# 自定义自由复制
def voice_quick_duplicate():
    # 检查是否选中一个网格对象
    if is_object_mode() or is_edit_mode():
        pyautogui.keyDown('shift')
        pyautogui.press('d')
        pyautogui.keyUp('shift')

# 自定义“细分”菜单
def voice_subdivision():
    if is_object_mode() or is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW_MT_voice_subdivision")

# 自定义“面朝向”显示/隐藏选项
def voice_on_off_face_orientation():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 反转面朝向
            area.spaces.active.overlay.show_face_orientation = not area.spaces.active.overlay.show_face_orientation

# ==========↑↑↑↑↑ 通用操作 ↑↑↑↑↑========== #


# ==========↓↓↓↓↓ 物体模式 ↓↓↓↓↓========== #

# 自定义“切换原点”函数
def voice_switch_origin_menu():
    if is_object_mode():
        bpy.ops.wm.call_menu(name='OBJECT_MT_voice_switch_origin_menu')
    else:
        to_object_mode()
        bpy.ops.wm.call_menu(name='OBJECT_MT_voice_switch_origin_menu')

# 自定义”切换清空”菜单
def voice_clear():
    if is_object_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_object_clear")
    else:
        to_object_mode()
        bpy.ops.wm.call_menu(name="VIEW3D_MT_object_clear")
        
# 自定义“切换应用”菜单
def voice_apply():
    if is_object_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_object_apply")
    else:
        to_object_mode()
        bpy.ops.wm.call_menu(name="VIEW3D_MT_object_apply")

# 自定义“常规复制”函数
def voice_copy():
    if is_object_mode():
        bpy.ops.view3d.copybuffer()

# 自定义“关联复制”函数
def voice_link_duplicate():
    if is_object_mode():
        pyautogui.keyDown('alt')
        pyautogui.press('d')
        pyautogui.keyUp('alt')

# 自定义“粘贴物体”函数
def voice_paste():
    if is_object_mode():
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # 确保当前上下文为 3D 视图
                with bpy.context.temp_override(area=area):
                    bpy.ops.view3d.pastebuffer()
                break

# 自定义“合并”函数,“物体模式”和“编辑模式”共用命令
def voice_join_and_merge():
    if is_object_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorB7:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    bpy.ops.object.join()
    elif is_edit_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorC37:
            bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_merge")

# ==========↑↑↑↑↑ 物体模式 ↑↑↑↑↑========== #

# ==========↓↓↓↓↓ 编辑模式 ↓↓↓↓↓========== #

# 自定义“选择点”函数
def voice_select_vertex():
    if is_edit_mode():
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("⊡ 选择点", font_size=50.0, color=(1.0, 1.0, 0.0, 0.3), duration=3.0)
    else:
        to_edit_mode()
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("⊡ 选择点", font_size=50.0, color=(1.0, 1.0, 0.0, 0.3), duration=3.0)

# 自定义“选择边”函数
def voice_select_edge():
    if is_edit_mode():
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("⧄ 选择边", font_size=50.0, color=(1.0, 1.0, 0.0, 0.3), duration=3.0)
    else:
        to_edit_mode()
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("⧄ 选择边", font_size=50.0, color=(1.0, 1.0, 0.0, 0.3), duration=3.0)

# 自定义“选择面”函数
def voice_select_face():
    if is_edit_mode():
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("■ 选择面", font_size=50.0, color=(1.0, 1.0, 0.0, 0.3), duration=3.0)
    else:
        to_edit_mode()
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("■ 选择面", font_size=50.0, color=(1.0, 1.0, 0.0, 0.3), duration=3.0)

# 自定义“挤出”函数
def voice_extrude():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        pyautogui.press('e')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')

# 自定义“切换挤出”函数
def voice_switch_extrude_menu():
    if is_edit_mode():
        pyautogui.keyDown('alt')
        pyautogui.press('e')
        pyautogui.keyUp('alt')

# 自定义“内插面”操作
def voice_inset():
    if is_edit_mode():
        if bpy.context.tool_settings.mesh_select_mode[2]:
            pyautogui.press('i')
        else:
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')

# 自定义“顶点倒角”函数
def voice_vertex_bevel():
    if is_edit_mode():
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('shift')
        pyautogui.press('b')
        pyautogui.keyUp('shift')
        pyautogui.keyUp('ctrl')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')

# 自定义“边倒角”函数
def voice_edge_bevel():
    if is_edit_mode():
        pyautogui.keyDown('ctrl')
        pyautogui.press('b')
        pyautogui.keyUp('ctrl')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')

# 自定义“环切”操作
def voice_loop_cut():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        pyautogui.keyDown('ctrl')
        pyautogui.press('r')
        pyautogui.keyUp('ctrl')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
        pyautogui.keyDown('ctrl')
        pyautogui.press('r')
        pyautogui.keyUp('ctrl')

# 自定义“偏移环切”操作
def voice_offset_loop_cut():
    if is_edit_mode():
        if not bpy.context.tool_settings.mesh_select_mode[0]:
            bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('shift')
            pyautogui.press('r')
            pyautogui.keyUp('shift')
            pyautogui.keyUp('ctrl')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.select", space_type='VIEW_3D')

# 自定义“切割”操作
def voice_knife():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.knife", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.knife", space_type='VIEW_3D')

# 自定义“切分”操作
def voice_bisect():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.bisect", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.bisect", space_type='VIEW_3D')

# 自定义“多边形建形”操作
def voice_poly_build():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.poly_build", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.poly_build", space_type='VIEW_3D')

# 自定义“旋绕”操作
def voice_spin():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.spin", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.spin", space_type='VIEW_3D')

# 自定义“光滑”操作,"编辑模式"和“雕刻模式”共用命令
def voice_smooth_edit_and_sculpt():
    if is_edit_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorC15:
            bpy.ops.wm.tool_set_by_id(name="builtin.smooth", space_type='VIEW_3D')
    elif is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorD10:
            if bpy.context.preferences.addons[__name__].preferences.operatorE1:
                draw_text("< 光滑 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth", space_type='VIEW_3D')

# 自定义“随机”操作
def voice_randomize():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.randomize", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.randomize", space_type='VIEW_3D')

# 自定义“边线滑移”操作
def voice_edge_slide():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.edge_slide", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='EDGE')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.edge_slide", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='EDGE')

# 自定义“顶点滑移”操作
def voice_vertex_slide():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.vertex_slide", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='VERT')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.vertex_slide", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='VERT')

# 自定义“法向缩放”操作
def voice_shrink_fatten():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.shrink_fatten", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.shrink_fatten", space_type='VIEW_3D')

# 自定义“推拉”操作
def voice_push_pull():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.push_pull", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.push_pull", space_type='VIEW_3D')

# 自定义“切变”操作
def voice_shear():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.shear", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.shear", space_type='VIEW_3D')

# 自定义“球形化”操作
def voice_to_sphere():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.to_sphere", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.to_sphere", space_type='VIEW_3D')

# 自定义“断离区域”操作
def voice_rip_region():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.rip_region", space_type='VIEW_3D')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.rip_region", space_type='VIEW_3D')

# 自定义“断离顶点”操作，我自已添加的功能
def voice_rip_region_vertex():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.rip_region", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='VERT')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.rip_region", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='VERT')

# 自定义“断离边”操作，我自已添加的功能
def voice_rip_region_edge():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.rip_region", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='EDGE')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.rip_region", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='EDGE')

# 自定义“断离边线”操作，我自已添加的功能
def voice_rip_edge():
    if is_edit_mode():
        bpy.ops.wm.tool_set_by_id(name="builtin.rip_edge", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='EDGE')
    else:
        to_edit_mode()
        bpy.ops.wm.tool_set_by_id(name="builtin.rip_edge", space_type='VIEW_3D')
        bpy.ops.mesh.select_mode(type='EDGE')

# 自定义“切换选择”菜单
def voice_switch_select_menu():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_select_edit_mesh")

# 自定义”间隔性弃选“操作
def voice_select_nth():
    if not bpy.context.active_object:
        # 检查是否有任何对象
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_select_nth('INVOKE_DEFAULT')

# 自定义“扩展选区”参数设置
def voice_select_more_setting():
    if not bpy.context.active_object:
        # 检查是否有任何对象
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_select_more_setting('INVOKE_DEFAULT')

# 自定义“缩减选区”参数设置
def voice_select_less_setting():
    if not bpy.context.active_object:
        # 检查是否有任何对象
        if bpy.data.objects:
            # 选择第一个对象
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].select_set(True)
    bpy.ops.mesh.voice_select_less_setting('INVOKE_DEFAULT')

# 自定义“选择相连”操作
def voice_select_linked():
    if is_edit_mode():
        pyautogui.press('l')
    else:
        to_edit_mode()
        pyautogui.press('l')

# 自定义”切换网格“菜单选项
def voice_mesh_menu():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh")

# 自定义“合并”
#def voice_merge():
#    if is_edit_mode():
#        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_merge")

# 自定义“拆分”
def voice_split():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_split")

# 自定义”分离“
def voice_separate():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="Edit_MT_voice_switch_separate_menu")

# 自定义“切换法向”菜单
def voice_switch_normal_menu():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_normals")
    else:
        to_edit_mode()
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_normals")

# 自定义“切换顶点”菜单
def voice_switch_vertex_menu():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_vertices")

# 自定义“填充顶点”操作
def voice_fill_vertex():
    if is_edit_mode():
        bpy.ops.mesh.edge_face_add()

# 自定义“连接顶点”操作
def voice_link_vertex():
    if is_edit_mode():
        bpy.ops.mesh.vert_connect_path()

# 自定义“滑移顶点”操作
def voice_slide_vertex():
    if is_edit_mode():
        pyautogui.keyDown('shift')
        pyautogui.press('v')
        pyautogui.keyUp('shift')

# 自定义“融并顶点”操作
def voice_dissolve_vertex():
    if is_edit_mode():
        bpy.ops.mesh.dissolve_verts()

# 自定义“切换边”菜单
def voice_switch_edge_menu():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_edges")

# 自定义“桥接循环边”方法
def voice_bridge_edge():
    if is_edit_mode():
        bpy.ops.mesh.bridge_edge_loops()

# 自定义“边线折痕”方法
def voice_edge_crease():
    if is_edit_mode():
        bpy.ops.mesh.voice_edge_crease('INVOKE_DEFAULT')

# 自定义“融并边”方法
def voice_dissolve_edge():
    if is_edit_mode():
        bpy.ops.mesh.voice_dissolve_edge('INVOKE_DEFAULT')

# 自定义“切换面”菜单
def voice_switch_face_menu():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_faces")

# 自定义“切换填充”菜单
def voice_switch_fill_face_menu():
    if is_edit_mode():
        bpy.ops.wm.call_menu(name="VIEW_MT_switch_fill_face_menu")

# 自定义“填充”方法
def voice_fill_face():
    if is_edit_mode():
        bpy.ops.mesh.voice_fill_face('INVOKE_DEFAULT')

# 自定义“栅格填充”方法
def voice_grid_fill_face():
    if is_edit_mode():
        bpy.ops.mesh.voice_grid_fill_face('INVOKE_DEFAULT')

# 自定义“完美建面”方法
def voice_beautify_fill_face():
    if is_edit_mode():
        bpy.ops.mesh.voice_beautify_fill_face('INVOKE_DEFAULT')

# ==========↑↑↑↑↑ 编辑模式 ↑↑↑↑↑========== #

# ==========↓↓↓↓↓ 雕刻模式 ↓↓↓↓↓========== #

# 定义 draw_text 作为复用函数
font_info = {}

def draw_text(text, font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0):
    """主函数，用于显示指定的文本"""
    font_path = bpy.path.abspath('//Zeyada.ttf')
    if os.path.exists(font_path):
        font_info["font_id"] = blf.load(font_path)
    else:
        font_info["font_id"] = 0

    font_info["start_time"] = time.time()
    font_info["text"] = text
    font_info["font_size"] = font_size
    font_info["color"] = color
    font_info["duration"] = duration

    # 如果已有 handler 在运行，先移除它
    if font_info.get("handler"):
        bpy.types.SpaceView3D.draw_handler_remove(font_info["handler"], 'WINDOW')
        font_info["handler"] = None

    # 注册绘制回调
    font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(
        draw_callback, (None, None), 'WINDOW', 'POST_PIXEL')
    
    for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # 查找 3D 视图区域
                area.tag_redraw()

def draw_callback(self, context):
    """绘制文本的回调函数"""
    font_id = font_info["font_id"]
    text = font_info["text"]
    font_size = font_info["font_size"]
    color = font_info["color"]

    blf.size(font_id, font_size)

    # 获取文本的宽度以进行居中对齐
    text_width = blf.dimensions(font_id, text)[0]
    region_width = bpy.context.region.width
    position_x = 0.5 * region_width - 0.5 * text_width

    # 设置颜色、位置并绘制文本
    blf.color(font_id, *color)
    blf.position(font_id, position_x, 30, 0)
    blf.draw(font_id, text)

    # 检查显示时长，如果超时，则移除 handler
    elapsed_time = time.time() - font_info["start_time"]
    if elapsed_time > font_info["duration"]:
        bpy.types.SpaceView3D.draw_handler_remove(font_info["handler"], 'WINDOW')
        font_info["handler"] = None

def voice_brush_freeline():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 自由线 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw", space_type='VIEW_3D')

def voice_brush_sharp():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 锐边 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Sharp", space_type='VIEW_3D')

def voice_brush_clay():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 黏塑 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Clay", space_type='VIEW_3D')

def voice_brush_claystrip():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 黏条 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Clay Strips", space_type='VIEW_3D')

def voice_brush_claythumb():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 指推 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Clay Thumb", space_type='VIEW_3D')

def voice_brush_layer():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 层次 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Layer", space_type='VIEW_3D')

def voice_brush_inflate():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 膨胀 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Inflate", space_type='VIEW_3D')

def voice_brush_blob():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 球体 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Blob", space_type='VIEW_3D')

def voice_brush_crease():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 折痕 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Crease", space_type='VIEW_3D')

#def voice_brush_smooth():
#    if is_sculpt_mode():
#        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
#            draw_text("< 光滑 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
#        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth", space_type='VIEW_3D')

def voice_brush_flatten():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 平化 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Flatten", space_type='VIEW_3D')

def voice_brush_fill():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 填充 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Fill", space_type='VIEW_3D')

def voice_brush_scrape():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 刮削 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Scrape", space_type='VIEW_3D')

def voice_brush_multiscrape():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 多平面刮削 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Multi-plane Scrape", space_type='VIEW_3D')

def voice_brush_pinch():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 夹捏 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Pinch", space_type='VIEW_3D')

def voice_brush_grab():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 抓起 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Grab", space_type='VIEW_3D')

def voice_brush_elasticdeform():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 弹性变形 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Elastic Deform", space_type='VIEW_3D')

def voice_brush_snakehook():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 蛇形钩 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Snake Hook", space_type='VIEW_3D')

def voice_brush_thumb():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 拇指 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Thumb", space_type='VIEW_3D')

def voice_brush_pose():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 姿态 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Pose", space_type='VIEW_3D')

def voice_brush_nudge():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 推移 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Nudge", space_type='VIEW_3D')

def voice_brush_rotate():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 旋转 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Rotate", space_type='VIEW_3D')

def voice_brush_sliderelax():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 滑动松弛(拓扑) >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Slide Relax", space_type='VIEW_3D')

def voice_brush_boundry():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 边界范围 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Boundary", space_type='VIEW_3D')

def voice_brush_cloth():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 布料 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Cloth", space_type='VIEW_3D')

def voice_brush_simplify():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 简化 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Simplify", space_type='VIEW_3D')

def voice_brush_mask():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 遮罩 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Mask", space_type='VIEW_3D')

def voice_brush_drawfaceset():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 绘制面组 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets", space_type='VIEW_3D')

def voice_brush_multiresdisplacementeraser():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 多精度置换橡皮擦 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Multires Displacement Eraser", space_type='VIEW_3D')

def voice_brush_multiresdisplacementsmear():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 多精度置换涂抹 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Multires Displacement Smear", space_type='VIEW_3D')

def voice_brush_paint():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 绘制 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Paint", space_type='VIEW_3D')

def voice_brush_smear():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 涂抹 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smear", space_type='VIEW_3D')
# ------------------------------------------------------------------------------------

def voice_sculpt_switch_mask_menu():
    if is_sculpt_mode():
        bpy.ops.wm.call_menu(name="SCULPT_MT_switch_mask_brush")

def voice_brush_boxmask():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 框选遮罩 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.box_mask", space_type='VIEW_3D')

def voice_brush_lassomask():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 套索遮罩 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.lasso_mask", space_type='VIEW_3D')

def voice_brush_linemask():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 划线遮罩 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.line_mask", space_type='VIEW_3D')

def voice_brush_polylinemask():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 折线遮罩 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.polyline_mask", space_type='VIEW_3D')

# ------------------------------------------------------------------------------------

def voice_sculpt_switch_hide_menu():
    if is_sculpt_mode():
        bpy.ops.wm.call_menu(name="SCULPT_MT_switch_hide_brush")

def voice_brush_boxhide():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 框选隐藏 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.box_hide", space_type='VIEW_3D')

def voice_brush_lassohide():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 套索隐藏 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.lasso_hide", space_type='VIEW_3D')

def voice_brush_linehide():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 划线隐藏 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.line_hide", space_type='VIEW_3D')

def voice_brush_polylinehide():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 折线隐藏 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.polyline_hide", space_type='VIEW_3D')

# ------------------------------------------------------------------------------------

def voice_sculpt_switch_faceset_menu():
    if is_sculpt_mode():
        bpy.ops.wm.call_menu(name="SCULPT_MT_switch_faceset_brush")

def voice_brush_boxfaceset():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 框选面组 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.box_face_set", space_type='VIEW_3D')

def voice_brush_lassofaceset():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 套索面组 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.lasso_face_set", space_type='VIEW_3D')

def voice_brush_linefaceset():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 划线面组 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.line_face_set", space_type='VIEW_3D')

def voice_brush_polylinefaceset():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 折线面组 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.polyline_face_set", space_type='VIEW_3D')

# ------------------------------------------------------------------------------------

def voice_sculpt_switch_trim_menu():
    if is_sculpt_mode():
        bpy.ops.wm.call_menu(name="SCULPT_MT_switch_trim_brush")

def voice_brush_boxtrim():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 框选修剪 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.box_trim", space_type='VIEW_3D')

def voice_brush_lassotrim():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 套索修剪 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.lasso_trim", space_type='VIEW_3D')

def voice_brush_linetrim():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 划线修剪 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.line_trim", space_type='VIEW_3D')

def voice_brush_polylinetrim():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 折线修剪 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.polyline_trim", space_type='VIEW_3D')

# ------------------------------------------------------------------------------------

def voice_brush_lineproject():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 划线投影 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.line_project", space_type='VIEW_3D')

def voice_brush_meshfilter():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 网格滤镜 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.mesh_filter", space_type='VIEW_3D')

def voice_brush_clothfilter():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 布料滤镜 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.cloth_filter", space_type='VIEW_3D')

def voice_brush_colorfilter():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 色彩滤镜 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.color_filter", space_type='VIEW_3D')

def voice_brush_facesetedit():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 编辑面组 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.face_set_edit", space_type='VIEW_3D')

def voice_brush_maskbycolor():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("< 按颜色遮罩 >", font_size=50.0, color=(0.0, 1.0, 1.0, 0.3), duration=5.0)
        bpy.ops.wm.tool_set_by_id(name="builtin.mask_by_color", space_type='VIEW_3D')

# “调节半径”，模拟 F 键
def voice_sculpt_radius():
    if is_sculpt_mode():
        pyautogui.press('f')

# "强度/力度"，模拟 Shift + F 键
def voice_sculpt_strength():
    if is_sculpt_mode():
        pyautogui.keyDown('shift')
        pyautogui.press('f')
        pyautogui.keyUp('shift')

# “角度”，模拟 Ctrl + F 键
def voice_sculpt_angle():
    if is_sculpt_mode():
        pyautogui.keyDown('ctrl')
        pyautogui.press('f')
        pyautogui.keyUp('ctrl')

# “编辑体素大小”, 模拟 R 键
def voice_sculpt_voxel_size():
    if is_sculpt_mode():
        pyautogui.press('r')

# “体素重构”，模拟 Ctrl + R 键
def voice_sculpt_voxel_remesh():
    if is_sculpt_mode():
        pyautogui.keyDown('ctrl')
        pyautogui.press('r')
        pyautogui.keyUp('ctrl')
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("[ 体素已重构 ]", font_size=50.0, color=(0.0, 1.0, 0.0, 0.3), duration=2.0)

# 开/关动态拓扑
def voice_toggle_dynamictopology():
    if is_sculpt_mode():
        bpy.ops.sculpt.dynamic_topology_toggle()
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            if bpy.context.object.use_dynamic_topology_sculpting:
                draw_text("< 动态拓扑● >", font_size=50.0, color=(0.0, 1.0, 0.0, 0.3), duration=5.0)
            else:
                draw_text("< 动态拓扑○ >", font_size=50.0, color=(1.0, 0.0, 0.0, 0.3), duration=5.0)

# “正向雕刻“
def voice_sculpt_to_add_direction():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("⊕", font_size=50.0, color=(0.0, 1.0, 0.0, 0.3), duration=2.0)
        bpy.data.brushes["SculptDraw"].direction = 'ADD'
        bpy.data.brushes["Draw Sharp"].direction = 'ADD'
        bpy.data.brushes["Clay"].direction = 'ADD'
        bpy.data.brushes["Clay Strips"].direction = 'ADD'
        bpy.data.brushes["Layer"].direction = 'ADD'
        bpy.data.brushes["Inflate/Deflate"].direction = 'INFLATE'
        bpy.data.brushes["Blob"].direction = 'ADD'
        bpy.data.brushes["Crease"].direction = 'ADD'
        bpy.data.brushes["Smooth"].direction = 'SMOOTH'
        bpy.data.brushes["Flatten/Contrast"].direction = 'CONTRAST'
        bpy.data.brushes["Fill/Deepen"].direction = 'FILL'
        bpy.data.brushes["Scrape/Peaks"].direction = 'SCRAPE'
        bpy.data.brushes["Pinch/Magnify"].direction = 'MAGNIFY'
        bpy.data.brushes["Mask"].direction = 'ADD'
        
# ”负向雕刻“
def voice_sculpt_to_subtract_direction():
    if is_sculpt_mode():
        if bpy.context.preferences.addons[__name__].preferences.operatorE1:
            draw_text("⊖", font_size=50.0, color=(1.0, 0.0, 0.0, 0.3), duration=2.0)
            bpy.data.brushes["SculptDraw"].direction = 'SUBTRACT'
            bpy.data.brushes["Draw Sharp"].direction = 'SUBTRACT'
            bpy.data.brushes["Clay"].direction = 'SUBTRACT'
            bpy.data.brushes["Clay Strips"].direction = 'SUBTRACT'
            bpy.data.brushes["Layer"].direction = 'SUBTRACT'
            bpy.data.brushes["Inflate/Deflate"].direction = 'DEFLATE'
            bpy.data.brushes["Blob"].direction = 'SUBTRACT'
            bpy.data.brushes["Crease"].direction = 'SUBTRACT'
            bpy.data.brushes["Smooth"].direction = 'ENHANCE_DETAILS'
            bpy.data.brushes["Flatten/Contrast"].direction = 'FLATTEN'
            bpy.data.brushes["Fill/Deepen"].direction = 'DEEPEN'
            bpy.data.brushes["Scrape/Peaks"].direction = 'PEAKS'
            bpy.data.brushes["Pinch/Magnify"].direction = 'PINCH'
            bpy.data.brushes["Mask"].direction = 'SUBTRACT'

# ==========↑↑↑↑↑ 雕刻模式 ↑↑↑↑↑========== #

# ==========↓↓↓↓↓ 附加功能 ↓↓↓↓↓========== #

# 切换语言
def voice_switch_language():
    if bpy.context.preferences.view.language == 'en_US':
        try:
        # 最新版本的中文参数是 zh_HANS,
            bpy.context.preferences.view.language = 'zh_HANS'
            bpy.context.preferences.view.use_translate_new_dataname = False
        except Exception:
        # 如果设置失败，尝试旧版本语言 zh_CN
            bpy.context.preferences.view.language = 'zh_CN'
            bpy.context.preferences.view.use_translate_new_dataname = False
    else:
        bpy.context.preferences.view.language = 'en_US'

# 模拟按下 Shift 键，消息提示 上层
tip_style_upper = {}

def operator_tip_upper(text, font_size, color, hoffset, voffset):
    """主函数，用于显示指定的文本"""
    font_path = bpy.path.abspath('//Zeyada.ttf')
    if os.path.exists(font_path):
        tip_style_upper["font_id"] = blf.load(font_path)
    else:
        tip_style_upper["font_id"] = 0

    tip_style_upper["text"] = text
    tip_style_upper["font_size"] = font_size
    tip_style_upper["color"] = color
    tip_style_upper["hoffset"] = hoffset # 文本横向偏移
    tip_style_upper["voffset"] = voffset # 文本垂直偏移

    # 如果已有 handler 在运行，先移除它
    if tip_style_upper.get("handler"):
        bpy.types.SpaceView3D.draw_handler_remove(tip_style_upper["handler"], 'WINDOW')
        tip_style_upper["handler"] = None

    # 注册绘制回调
    tip_style_upper["handler"] = bpy.types.SpaceView3D.draw_handler_add(
        draw_operator_tip_upper, (None, None), 'WINDOW', 'POST_PIXEL')

    for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # 查找 3D 视图区域
                area.tag_redraw()


def draw_operator_tip_upper(self, context):
    """绘制文本的回调函数"""
    font_id = tip_style_upper["font_id"]
    text = tip_style_upper["text"]
    font_size = tip_style_upper["font_size"]
    color = tip_style_upper["color"]
    hoffset = tip_style_upper["hoffset"]
    voffset = tip_style_upper["voffset"]


    blf.size(font_id, font_size)

    # 获取文本的宽度以进行居中对齐
    text_width = blf.dimensions(font_id, text)[0]
    region_width = bpy.context.region.width
    position_x = region_width - text_width - hoffset

    # 设置颜色、位置并绘制文本
    blf.color(font_id, *color)
    blf.position(font_id, position_x, voffset, 0)
    blf.draw(font_id, text)

# 模拟按下 Shift 键，消息提示 下层
tip_style_lower = {}

def operator_tip_lower(text, font_size, color, hoffset, voffset):
    """主函数，用于显示指定的文本"""
    font_path = bpy.path.abspath('//Zeyada.ttf')
    if os.path.exists(font_path):
        tip_style_lower["font_id"] = blf.load(font_path)
    else:
        tip_style_lower["font_id"] = 0

    tip_style_lower["text"] = text
    tip_style_lower["font_size"] = font_size
    tip_style_lower["color"] = color
    tip_style_lower["hoffset"] = hoffset # 文本横向偏移
    tip_style_lower["voffset"] = voffset # 文本垂直偏移

    # 如果已有 handler 在运行，先移除它
    if tip_style_lower.get("handler"):
        bpy.types.SpaceView3D.draw_handler_remove(tip_style_lower["handler"], 'WINDOW')
        tip_style_lower["handler"] = None

    # 注册绘制回调
    tip_style_lower["handler"] = bpy.types.SpaceView3D.draw_handler_add(
        draw_operator_tip_lower, (None, None), 'WINDOW', 'POST_PIXEL')

    for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # 查找 3D 视图区域
                area.tag_redraw()


def draw_operator_tip_lower(self, context):
    """绘制文本的回调函数"""
    font_id = tip_style_lower["font_id"]
    text = tip_style_lower["text"]
    font_size = tip_style_lower["font_size"]
    color = tip_style_lower["color"]
    hoffset = tip_style_lower["hoffset"]
    voffset = tip_style_lower["voffset"]


    blf.size(font_id, font_size)

    # 获取文本的宽度以进行居中对齐
    text_width = blf.dimensions(font_id, text)[0]
    region_width = bpy.context.region.width
    position_x = region_width - text_width - hoffset

    # 设置颜色、位置并绘制文本
    blf.color(font_id, *color)
    blf.position(font_id, position_x, voffset, 0)
    blf.draw(font_id, text)

# “移除按下 shift 提示”
def voice_remove_simulate_shift():
    if is_object_mode() or is_edit_mode() or is_sculpt_mode():
        bpy.types.SpaceView3D.draw_handler_remove(tip_style_upper["handler"], 'WINDOW')
        tip_style_upper["handler"] = None
        bpy.types.SpaceView3D.draw_handler_remove(tip_style_lower["handler"], 'WINDOW')
        tip_style_lower["handler"] = None
        pyautogui.keyUp('shift')
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # 查找 3D 视图区域
                area.tag_redraw() 

# 模拟按下 Ctrl 键，消息提示 上层
tip_style_upper_ctrl = {}

def operator_tip_upper_ctrl(text, font_size, color, hoffset, voffset):
    """主函数，用于显示指定的文本"""
    font_path = bpy.path.abspath('//Zeyada.ttf')
    if os.path.exists(font_path):
        tip_style_upper_ctrl["font_id"] = blf.load(font_path)
    else:
        tip_style_upper_ctrl["font_id"] = 0

    tip_style_upper_ctrl["text"] = text
    tip_style_upper_ctrl["font_size"] = font_size
    tip_style_upper_ctrl["color"] = color
    tip_style_upper_ctrl["hoffset"] = hoffset # 文本横向偏移
    tip_style_upper_ctrl["voffset"] = voffset # 文本垂直偏移

    # 如果已有 handler 在运行，先移除它
    if tip_style_upper_ctrl.get("handler"):
        bpy.types.SpaceView3D.draw_handler_remove(tip_style_upper_ctrl["handler"], 'WINDOW')
        tip_style_upper_ctrl["handler"] = None

    # 注册绘制回调
    tip_style_upper_ctrl["handler"] = bpy.types.SpaceView3D.draw_handler_add(
        draw_operator_tip_upper_ctrl, (None, None), 'WINDOW', 'POST_PIXEL')

    for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # 查找 3D 视图区域
                area.tag_redraw()


def draw_operator_tip_upper_ctrl(self, context):
    """绘制文本的回调函数"""
    font_id = tip_style_upper_ctrl["font_id"]
    text = tip_style_upper_ctrl["text"]
    font_size = tip_style_upper_ctrl["font_size"]
    color = tip_style_upper_ctrl["color"]
    hoffset = tip_style_upper_ctrl["hoffset"]
    voffset = tip_style_upper_ctrl["voffset"]


    blf.size(font_id, font_size)

    # 获取文本的宽度以进行居中对齐
    text_width = blf.dimensions(font_id, text)[0]
    region_width = bpy.context.region.width
    position_x = region_width - text_width - hoffset

    # 设置颜色、位置并绘制文本
    blf.color(font_id, *color)
    blf.position(font_id, position_x, voffset, 0)
    blf.draw(font_id, text)

# 模拟按下 Ctrl 键，消息提示 下层
tip_style_lower_ctrl = {}

def operator_tip_lower_ctrl(text, font_size, color, hoffset, voffset):
    """主函数，用于显示指定的文本"""
    font_path = bpy.path.abspath('//Zeyada.ttf')
    if os.path.exists(font_path):
        tip_style_lower_ctrl["font_id"] = blf.load(font_path)
    else:
        tip_style_lower_ctrl["font_id"] = 0

    tip_style_lower_ctrl["text"] = text
    tip_style_lower_ctrl["font_size"] = font_size
    tip_style_lower_ctrl["color"] = color
    tip_style_lower_ctrl["hoffset"] = hoffset # 文本横向偏移
    tip_style_lower_ctrl["voffset"] = voffset # 文本垂直偏移

    # 如果已有 handler 在运行，先移除它
    if tip_style_lower_ctrl.get("handler"):
        bpy.types.SpaceView3D.draw_handler_remove(tip_style_lower_ctrl["handler"], 'WINDOW')
        tip_style_lower_ctrl["handler"] = None

    # 注册绘制回调
    tip_style_lower_ctrl["handler"] = bpy.types.SpaceView3D.draw_handler_add(
        draw_operator_tip_lower_ctrl, (None, None), 'WINDOW', 'POST_PIXEL')

    for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # 查找 3D 视图区域
                area.tag_redraw()


def draw_operator_tip_lower_ctrl(self, context):
    """绘制文本的回调函数"""
    font_id = tip_style_lower_ctrl["font_id"]
    text = tip_style_lower_ctrl["text"]
    font_size = tip_style_lower_ctrl["font_size"]
    color = tip_style_lower_ctrl["color"]
    hoffset = tip_style_lower_ctrl["hoffset"]
    voffset = tip_style_lower_ctrl["voffset"]


    blf.size(font_id, font_size)

    # 获取文本的宽度以进行居中对齐
    text_width = blf.dimensions(font_id, text)[0]
    region_width = bpy.context.region.width
    position_x = region_width - text_width - hoffset

    # 设置颜色、位置并绘制文本
    blf.color(font_id, *color)
    blf.position(font_id, position_x, voffset, 0)
    blf.draw(font_id, text)

# 移除模拟按下 Ctrl 键的提示语
def voice_remove_simulate_ctrl():
    if is_sculpt_mode() or is_object_mode() or is_edit_mode():
        bpy.types.SpaceView3D.draw_handler_remove(tip_style_upper_ctrl["handler"], 'WINDOW')
        tip_style_upper_ctrl["handler"] = None
        bpy.types.SpaceView3D.draw_handler_remove(tip_style_lower_ctrl["handler"], 'WINDOW')
        tip_style_lower_ctrl["handler"] = None
        pyautogui.keyUp('ctrl')
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':  # 查找 3D 视图区域
                area.tag_redraw() 

# 模拟平移方法
def voice_shift_move():
    if is_object_mode() or is_edit_mode() or is_sculpt_mode():
        pyautogui.keyDown('shift')
        operator_tip_upper("◀ 中键平移 ▶", font_size=30.0, color=(1.0, 1.0, 1.0, 0.3), hoffset=45, voffset=70)
        operator_tip_lower("[取消平移]取消", font_size=30.0, color=(0.0, 1.0, 1.0, 0.3), hoffset=40, voffset=20)

# 模拟多选方法
def voice_shift_select():
    if is_object_mode() or is_edit_mode():
        pyautogui.keyDown('shift')
        operator_tip_upper("■ 左键多选 □", font_size=30.0, color=(1.0, 1.0, 1.0, 0.3), hoffset=45, voffset=70)
        operator_tip_lower("[取消多选]取消", font_size=30.0, color=(0.0, 1.0, 1.0, 0.3), hoffset=40, voffset=20)

# 模拟X轴
def voice_x_axis():
    if is_object_mode() or is_edit_mode():
        pyautogui.press('x')

# 模拟Y轴
def voice_y_axis():
    if is_object_mode() or is_edit_mode():
        pyautogui.press('y')

# 模拟Z轴
def voice_z_axis():
    if is_object_mode() or is_edit_mode():
        pyautogui.press('z')
            
# ==========↑↑↑↑↑ 附加功能 ↑↑↑↑↑========== #

# ++++++++++++++++++++++程序主线部分+++++++++++++++++
# 全局变量用于 Arduino 连接和状态
arduino_thread = None
serial_connection = None
listening_active = False

# Arduino监听器线程
def arduino_listener():
    global serial_connection, listening_active
    while listening_active:
        if serial_connection and serial_connection.in_waiting > 0:
            data = serial_connection.readline().decode('utf-8').strip()
            print(f"Received from Arduino: {data}")

            if data == "COMMAND1a" and bpy.context.preferences.addons[__name__].preferences.operatorA1:
                bpy.app.timers.register(lambda: to_object_mode()) # COMMAND1 切换到“物体模式”
            elif data == "COMMAND2a" and bpy.context.preferences.addons[__name__].preferences.operatorA2:
                bpy.app.timers.register(lambda: to_edit_mode()) # COMMAND2 切换到“编辑模式”
            elif data == "COMMAND3a" and bpy.context.preferences.addons[__name__].preferences.operatorA3:
                bpy.app.timers.register(lambda: to_sculpt_mode()) # COMMAND3 切换到“雕刻模式”
            elif data == "COMMAND4a" and bpy.context.preferences.addons[__name__].preferences.operatorA4:
                bpy.app.timers.register(lambda: voice_add()) # COMMAND4 调出“添加”菜单
            elif data == "COMMAND5a" and bpy.context.preferences.addons[__name__].preferences.operatorA5:
                bpy.app.timers.register(lambda: voice_delete()) # COMMAND5 调出“删除”菜单
            elif data == "COMMAND6a" and bpy.context.preferences.addons[__name__].preferences.operatorA6:
                bpy.app.timers.register(lambda: bpy.ops.ed.undo()) # COMMAND6 “撤销”操作
            elif data == "COMMAND7a" and bpy.context.preferences.addons[__name__].preferences.operatorA7:
                bpy.app.timers.register(lambda: bpy.ops.ed.redo()) # COMMAND7 “重做”操作
            elif data == "COMMAND8a" and bpy.context.preferences.addons[__name__].preferences.operatorA8:
                bpy.app.timers.register(lambda: voice_select_mode_menu()) # COMMAND8 调出工具选择菜单
            elif data == "COMMAND9a" and bpy.context.preferences.addons[__name__].preferences.operatorA9:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.select', space_type='VIEW_3D')) # COMMAND9 “调整”工具
            elif data == "COMMAND10a" and bpy.context.preferences.addons[__name__].preferences.operatorA10:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.select_box', space_type='VIEW_3D')) # COMMAND10 “框选”工具
            elif data == "COMMAND11a" and bpy.context.preferences.addons[__name__].preferences.operatorA11:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.select_circle', space_type='VIEW_3D')) # COMMAND11 “刷选”工具
            elif data == "COMMAND12a" and bpy.context.preferences.addons[__name__].preferences.operatorA12:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.select_lasso', space_type='VIEW_3D')) # COMMAND12 “套索选择”工具
            elif data == "COMMAND13a" and bpy.context.preferences.addons[__name__].preferences.operatorA13:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.cursor',space_type='VIEW_3D')) # COMMAND13 设置“游标”
            elif data == "COMMAND14a" and bpy.context.preferences.addons[__name__].preferences.operatorA14:
                bpy.app.timers.register(lambda: voice_move()) # COMMAND14 模拟“G”按键
            elif data == "COMMAND15a" and bpy.context.preferences.addons[__name__].preferences.operatorA15:
                bpy.app.timers.register(lambda: voice_rotate()) # COMMAND15 模拟“R”按键
            elif data == "COMMAND16a" and bpy.context.preferences.addons[__name__].preferences.operatorA16:
                bpy.app.timers.register(lambda: voice_scale()) # COMMAND16 模拟”S“按键
            elif data == "COMMAND17a" and bpy.context.preferences.addons[__name__].preferences.operatorA17:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.scale_cage', space_type='VIEW_3D')) # COMMAND17 罩体缩放
            elif data == "COMMAND18a" and bpy.context.preferences.addons[__name__].preferences.operatorA18:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.transform', space_type='VIEW_3D')) # COMMAND18
            elif data == "COMMAND19a" and bpy.context.preferences.addons[__name__].preferences.operatorA19:
                bpy.app.timers.register(lambda: voice_switch_annotation_mode()) # COMMAND19 调用“切换标注模式”菜单
            elif data == "COMMAND20a" and bpy.context.preferences.addons[__name__].preferences.operatorA20:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.annotate', space_type='VIEW_3D')) # COMMAND20 切换到“标注”
            elif data == "COMMAND21a" and bpy.context.preferences.addons[__name__].preferences.operatorA21:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.annotate_line', space_type='VIEW_3D')) # COMMAND21 切换到”标注直线“
            elif data == "COMMAND22a" and bpy.context.preferences.addons[__name__].preferences.operatorA22:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.annotate_polygon', space_type='VIEW_3D')) # COMMAND22 切换到”标注多段线“
            elif data == "COMMAND23a" and bpy.context.preferences.addons[__name__].preferences.operatorA23:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.annotate_eraser', space_type='VIEW_3D')) # COMMAND23 切换到”标注橡皮擦“
            elif data == "COMMAND24a" and bpy.context.preferences.addons[__name__].preferences.operatorA24:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.measure', space_type='VIEW_3D')) #COMMAND24 切换到“测量”
            elif data == "COMMAND25a" and bpy.context.preferences.addons[__name__].preferences.operatorA25:
                bpy.app.timers.register(lambda: voice_quick_add()) # COMMAND25 调用”切换添加“菜单
            elif data == "COMMAND26a" and bpy.context.preferences.addons[__name__].preferences.operatorA26:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.primitive_cube_add', space_type='VIEW_3D')) # 快速添加立方体
            elif data == "COMMAND27a" and bpy.context.preferences.addons[__name__].preferences.operatorA27:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.primitive_cone_add', space_type='VIEW_3D')) # 快速添加锥体
            elif data == "COMMAND28a" and bpy.context.preferences.addons[__name__].preferences.operatorA28:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.primitive_cylinder_add', space_type='VIEW_3D')) # 快速添加柱体
            elif data == "COMMAND29a" and bpy.context.preferences.addons[__name__].preferences.operatorA29:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.primitive_uv_sphere_add', space_type='VIEW_3D')) # 快速添加经纬球
            elif data == "COMMAND30a" and bpy.context.preferences.addons[__name__].preferences.operatorA30:
                bpy.app.timers.register(lambda: bpy.ops.wm.tool_set_by_id(name='builtin.primitive_ico_sphere_add', space_type='VIEW_3D')) # 快速添加棱角球
            elif data == "COMMAND31a" and bpy.context.preferences.addons[__name__].preferences.operatorA31:
                bpy.app.timers.register(lambda: voice_switch_orientation_menu()) # COMMAND31 调用“切换坐标系”菜单
            elif data == "COMMAND32a" and bpy.context.preferences.addons[__name__].preferences.operatorA32:
                bpy.app.timers.register(lambda: voice_switch_pivot_menu()) # COMMAND32 调用“切换轴心点”菜单
            elif data == "COMMAND33a" and bpy.context.preferences.addons[__name__].preferences.operatorA33:
                bpy.app.timers.register(lambda: voice_on_off_snap()) # COMMAND33 调用“开/关吸附”函数
            elif data == "COMMAND34a" and bpy.context.preferences.addons[__name__].preferences.operatorA34:
                bpy.app.timers.register(lambda: voice_snap_menu()) # COMMAND34 调用“吸附菜单”
            elif data == "COMMAND35a" and bpy.context.preferences.addons[__name__].preferences.operatorA35:
                bpy.app.timers.register(lambda: voice_on_off_falloff()) # COMMAND35 调用“开/关衰减”函数
            elif data == "COMMAND36a" and bpy.context.preferences.addons[__name__].preferences.operatorA36:
                bpy.app.timers.register(lambda: voice_falloff_menu()) # COMMAND36 调用“切换衰减”菜单
            elif data == "COMMAND37a" and bpy.context.preferences.addons[__name__].preferences.operatorA37:
                bpy.app.timers.register(lambda: voice_shading_menu()) # COMMAND37 调用“切换着色”菜单
            elif data == "COMMAND38a" and bpy.context.preferences.addons[__name__].preferences.operatorA38:
                bpy.app.timers.register(lambda: voice_on_off_wireframe()) # COMMAND38 调用“线框/实体”开头切换
            elif data == "COMMAND39a" and bpy.context.preferences.addons[__name__].preferences.operatorA39:
                bpy.app.timers.register(lambda: voice_switch_view_menu()) # COMMAND39 调用“切换视图”菜单
            elif data == "COMMAND40a" and bpy.context.preferences.addons[__name__].preferences.operatorA40:
                bpy.app.timers.register(lambda: voice_to_camera_view()) # COMMAND40 调用“摄像机”函数
            elif data == "COMMAND41a" and bpy.context.preferences.addons[__name__].preferences.operatorA41:
                bpy.app.timers.register(lambda: voice_view_all()) # COMMAND41 调用”框选全部“
            elif data == "COMMAND42a" and bpy.context.preferences.addons[__name__].preferences.operatorA42:
                bpy.app.timers.register(lambda: voice_view_selected()) #COMMAND42 调用”框选所选“
            elif data == "COMMAND43a" and bpy.context.preferences.addons[__name__].preferences.operatorA43:
                bpy.app.timers.register(lambda: voice_view_top()) #COMMAND43 调用“顶视图”
            elif data == "COMMAND44a" and bpy.context.preferences.addons[__name__].preferences.operatorA44:
                bpy.app.timers.register(lambda: voice_view_bottom()) # COMMAND44 调用“底视图”
            elif data == "COMMAND45a" and bpy.context.preferences.addons[__name__].preferences.operatorA45:
                bpy.app.timers.register(lambda: voice_view_front()) # COMMAND45 调用“前视图”
            elif data == "COMMAND46a" and bpy.context.preferences.addons[__name__].preferences.operatorA46:
                bpy.app.timers.register(lambda: voice_view_back()) # COMMAND46 调用“后视图”
            elif data == "COMMAND47a" and bpy.context.preferences.addons[__name__].preferences.operatorA47:
                bpy.app.timers.register(lambda: voice_view_left()) # COMMAND47 调用“左视图”
            elif data == "COMMAND48a" and bpy.context.preferences.addons[__name__].preferences.operatorA48:
                bpy.app.timers.register(lambda: voice_view_right()) # COMMAND48 调用“右视图”
            elif data == "COMMAND49a" and bpy.context.preferences.addons[__name__].preferences.operatorA49:
                bpy.app.timers.register(lambda: voice_view_part()) # COMMAND49 调用“局部显示”
            elif data == "COMMAND50a" and bpy.context.preferences.addons[__name__].preferences.operatorA50:
                bpy.app.timers.register(lambda: voice_hide()) #COMMAND50 调用“隐藏”函数
            elif data == "COMMAND51a" and bpy.context.preferences.addons[__name__].preferences.operatorA51:
                bpy.app.timers.register(lambda: voice_hide_others()) # COMMAND51 调用“隐藏其它”函数
            elif data == "COMMAND52a" and bpy.context.preferences.addons[__name__].preferences.operatorA52:   
                bpy.app.timers.register(lambda: voice_show_hide()) # COMMAND52 调用“显示隐藏”函数
            elif data == "COMMAND53a" and bpy.context.preferences.addons[__name__].preferences.operatorA53:
                bpy.app.timers.register(lambda: voice_select_all()) # COMMAND53 调用“全选”函数
            elif data == "COMMAND54a" and bpy.context.preferences.addons[__name__].preferences.operatorA54:
                bpy.app.timers.register(lambda: voice_select_inverse()) # COMMAND54 调用“反选”函数
            elif data == "COMMAND55a" and bpy.context.preferences.addons[__name__].preferences.operatorA55:
                bpy.app.timers.register(lambda: voice_add_plane()) # COMMAND55 调用“添加平面”函数
            elif data == "COMMAND56a" and bpy.context.preferences.addons[__name__].preferences.operatorA56:
                bpy.app.timers.register(lambda: voice_add_cube()) # COMMAND56 调用“添加立方体”函数
            elif data == "COMMAND57a" and bpy.context.preferences.addons[__name__].preferences.operatorA57:
                bpy.app.timers.register(lambda: voice_add_circle()) # COMMAND57 调用“添加圆环”
            elif data == "COMMAND58a" and bpy.context.preferences.addons[__name__].preferences.operatorA58:
                bpy.app.timers.register(lambda: voice_add_uv_sphere()) # COMMAND58 调用“添加经纬球”
            elif data == "COMMAND59a" and bpy.context.preferences.addons[__name__].preferences.operatorA59:
                bpy.app.timers.register(lambda: voice_add_ico_sphere()) # COMMAND59 调用”添加棱角球“
            elif data == "COMMAND60a" and bpy.context.preferences.addons[__name__].preferences.operatorA60:
                bpy.app.timers.register(lambda: voice_add_cylinder()) # COMMAND60 调用”添加柱体“
            elif data == "COMMAND61a" and bpy.context.preferences.addons[__name__].preferences.operatorA61:
                bpy.app.timers.register(lambda: voice_add_cone()) # COMMAND61 调用“添加锥体”
            elif data == "COMMAND62a" and bpy.context.preferences.addons[__name__].preferences.operatorA62:
                bpy.app.timers.register(lambda: voice_add_torus()) # COMMAND62 调用“添加环体”
            elif data == "COMMAND63a" and bpy.context.preferences.addons[__name__].preferences.operatorA63:
                bpy.app.timers.register(lambda: voice_quick_duplicate()) # COMMAND63 调用自由复制
            elif data == "COMMAND64a" and bpy.context.preferences.addons[__name__].preferences.operatorA64:
                bpy.app.timers.register(lambda: voice_subdivision()) # COMMAND64a 调用“细分”菜单
            elif data == "COMMAND65a" and bpy.context.preferences.addons[__name__].preferences.operatorA65:
                bpy.app.timers.register(lambda: voice_on_off_face_orientation()) # COMMAND65a 调用“面朝向”并关选项
            elif data == "COMMAND1b" and bpy.context.preferences.addons[__name__].preferences.operatorB1:
                bpy.app.timers.register(lambda: voice_switch_origin_menu()) # COMMAND1b 调用“切换原点”菜单
            elif data == "COMMAND2b" and bpy.context.preferences.addons[__name__].preferences.operatorB2:
                bpy.app.timers.register(lambda: voice_clear()) # COMMAND2b 调用“切换清空”菜单
            elif data == "COMMAND3b" and bpy.context.preferences.addons[__name__].preferences.operatorB3:
                bpy.app.timers.register(lambda: voice_apply()) # COMMAND3b 调用“切换应用”菜单
            elif data == "COMMAND4b" and bpy.context.preferences.addons[__name__].preferences.operatorB4:
                bpy.app.timers.register(lambda: voice_copy()) # COMMAND4b 调用“常规复制”函数
            elif data == "COMMAND5b" and bpy.context.preferences.addons[__name__].preferences.operatorB5:
                bpy.app.timers.register(lambda: voice_link_duplicate()) # COMMAND5b 调用“关联复制”函数
            elif data == "COMMAND6b" and bpy.context.preferences.addons[__name__].preferences.operatorB6:
                bpy.app.timers.register(lambda: voice_paste()) # COMMAND6b 调用“粘贴物体”函数
            elif data == "COMMAND7b":
                bpy.app.timers.register(lambda: voice_join_and_merge()) # COMMAND7b 调用“合并”函数
            elif data == "COMMAND1c" and bpy.context.preferences.addons[__name__].preferences.operatorC1:
                bpy.app.timers.register(lambda: voice_select_vertex()) # COMMAND1c 调用“选择点”函数
            elif data == "COMMAND2c" and bpy.context.preferences.addons[__name__].preferences.operatorC2:
                bpy.app.timers.register(lambda: voice_select_edge()) # COMMAND2c 调用“选择边”函数
            elif data == "COMMAND3c" and bpy.context.preferences.addons[__name__].preferences.operatorC3:
                bpy.app.timers.register(lambda: voice_select_face()) # COMMAND3c 调用“选择面”函数
            elif data == "COMMAND4c" and bpy.context.preferences.addons[__name__].preferences.operatorC4:
                bpy.app.timers.register(lambda: voice_extrude()) # COMMAND4c 调用“挤出”函数
            elif data == "COMMAND5c" and bpy.context.preferences.addons[__name__].preferences.operatorC5:
                bpy.app.timers.register(lambda: voice_switch_extrude_menu()) # COMMAND5c 调用“切换挤出”菜单
            elif data == "COMMAND6c" and bpy.context.preferences.addons[__name__].preferences.operatorC6:
                bpy.app.timers.register(lambda: voice_inset()) # COMMAND6c  调用“内插面”函数
            elif data == "COMMAND7c" and bpy.context.preferences.addons[__name__].preferences.operatorC7:
                bpy.app.timers.register(lambda: voice_vertex_bevel()) # COMMAND7c 调用“顶点倒角”
            elif data == "COMMAND8c" and bpy.context.preferences.addons[__name__].preferences.operatorC8:
                bpy.app.timers.register(lambda: voice_edge_bevel()) # COMMAND8c 调用“边倒角”
            elif data == "COMMAND9c" and bpy.context.preferences.addons[__name__].preferences.operatorC9:
                bpy.app.timers.register(lambda: voice_loop_cut()) # COMMAND9c 调用“环切”
            elif data == "COMMAND10c" and bpy.context.preferences.addons[__name__].preferences.operatorC10:
                bpy.app.timers.register(lambda: voice_offset_loop_cut()) # COMMAND10c 调用“偏移环切”
            elif data == "COMMAND11c" and bpy.context.preferences.addons[__name__].preferences.operatorC11:
                bpy.app.timers.register(lambda: voice_knife()) # COMMAND11c 调用“切割”
            elif data == "COMMAND12c" and bpy.context.preferences.addons[__name__].preferences.operatorC12:
                bpy.app.timers.register(lambda: voice_bisect()) # COMMAND12c 调用“切分”
            elif data == "COMMAND13c" and bpy.context.preferences.addons[__name__].preferences.operatorC13:
                bpy.app.timers.register(lambda: voice_poly_build()) # COMMAND13c 调用“多边形建形”函数
            elif data == "COMMAND14c" and bpy.context.preferences.addons[__name__].preferences.operatorC14:
                bpy.app.timers.register(lambda: voice_spin()) # COMMAND14c 调用“旋绕”函数
            elif data == "COMMAND15c":
                bpy.app.timers.register(lambda: voice_smooth_edit_and_sculpt()) # COMMAND15c 调用“光滑”函数
            elif data == "COMMAND16c" and bpy.context.preferences.addons[__name__].preferences.operatorC16:
                bpy.app.timers.register(lambda: voice_randomize()) # COMMAND16c 调用“随机”函数
            elif data == "COMMAND17c" and bpy.context.preferences.addons[__name__].preferences.operatorC17:
                bpy.app.timers.register(lambda: voice_edge_slide()) # COMMAND17c 调用“边线滑移”
            elif data == "COMMAND18c" and bpy.context.preferences.addons[__name__].preferences.operatorC18:
                bpy.app.timers.register(lambda: voice_vertex_slide()) # COMMAND18c 调用“顶点滑移”
            elif data == "COMMAND19c" and bpy.context.preferences.addons[__name__].preferences.operatorC19:
                bpy.app.timers.register(lambda: voice_shrink_fatten()) # COMMAND19c 调用“法向缩放”
            elif data == "COMMAND20c" and bpy.context.preferences.addons[__name__].preferences.operatorC20:
                bpy.app.timers.register(lambda: voice_push_pull()) # COMMAND20c 调用“推拉”
            elif data == "COMMAND21c" and bpy.context.preferences.addons[__name__].preferences.operatorC21:
                bpy.app.timers.register(lambda: voice_shear()) # COMMAND21c 调用“切变”
            elif data == "COMMAND22c" and bpy.context.preferences.addons[__name__].preferences.operatorC22:
                bpy.app.timers.register(lambda: voice_to_sphere()) # COMMAND22c 调用“球形化”
            elif data == "COMMAND23c" and bpy.context.preferences.addons[__name__].preferences.operatorC23:
                bpy.app.timers.register(lambda: voice_rip_region()) # COMMAND23c 调用“断离区域“
            elif data == "COMMAND24c" and bpy.context.preferences.addons[__name__].preferences.operatorC24:
                bpy.app.timers.register(lambda: voice_rip_region_vertex()) # COMMAND24c 调用“断离顶点”
            elif data == "COMMAND25c" and bpy.context.preferences.addons[__name__].preferences.operatorC25:
                bpy.app.timers.register(lambda: voice_rip_region_edge()) # COMMAND25c 调用“断离边”
            elif data == "COMMAND26c" and bpy.context.preferences.addons[__name__].preferences.operatorC26:
                bpy.app.timers.register(lambda: voice_rip_edge()) # COMMAND26c  调用“断离边“
            elif data == "COMMAND27c" and bpy.context.preferences.addons[__name__].preferences.operatorC27:
                bpy.app.timers.register(lambda: voice_switch_select_menu()) # COMMAND27c 调用“切换选择”菜单
            elif data == "COMMAND28c" and bpy.context.preferences.addons[__name__].preferences.operatorC28:
                bpy.app.timers.register(lambda: voice_select_nth()) # COMMAND28c 调用”间隔性弃选“操作
            elif data == "COMMAND29c" and bpy.context.preferences.addons[__name__].preferences.operatorC29:
                bpy.app.timers.register(lambda: voice_select_more_setting()) # COMMAND29c 调用“扩展选区”参数菜单
            elif data == "COMMAND30c" and bpy.context.preferences.addons[__name__].preferences.operatorC30:
                bpy.app.timers.register(lambda: bpy.ops.mesh.select_more(use_face_step=bpy.context.scene.more_use_face_step)) # COMMAND30c 调用“扩展选区”api,参数调用我在 VoiceSelectMoreSetting 中设置的 more_use_face_step 值
            elif data == "COMMAND31c" and bpy.context.preferences.addons[__name__].preferences.operatorC31:
                bpy.app.timers.register(lambda: voice_select_less_setting()) # COMMAND31c 调用“缩减选区”参数菜单
            elif data == "COMMAND32c" and bpy.context.preferences.addons[__name__].preferences.operatorC32:
                bpy.app.timers.register(lambda: bpy.ops.mesh.select_less(use_face_step=bpy.context.scene.less_use_face_step)) # COMMAND32c 调用“缩减选区”api，参数调用我在 VoiceSelectLessSetting 中设置的 less_use_face_step 值
            elif data == "COMMAND33c" and bpy.context.preferences.addons[__name__].preferences.operatorC33:
                bpy.app.timers.register(lambda: voice_select_linked()) # COMMAND33c 调用“选择相连”操作
            elif data == "COMMAND34c" and bpy.context.preferences.addons[__name__].preferences.operatorC34:
                bpy.app.timers.register(lambda: bpy.ops.mesh.loop_multi_select(ring=False)) # COMMAND34c 调用“循环边” api
            elif data == "COMMAND35c" and bpy.context.preferences.addons[__name__].preferences.operatorC35:
                bpy.app.timers.register(lambda: bpy.ops.mesh.loop_multi_select(ring=True)) # COMMAND35c 调用“并排边” api
            elif data == "COMMAND36c" and bpy.context.preferences.addons[__name__].preferences.operatorC36:
                bpy.app.timers.register(lambda: voice_mesh_menu()) # COMMAND36c 调用”网格“菜单 api
            #elif data == "COMMAND37c" and bpy.context.preferences.addons[__name__].preferences.operatorC37:
                #bpy.app.timers.register(lambda: voice_merge()) # COMMAND37c 调用“合并”菜单
            elif data == "COMMAND38c" and bpy.context.preferences.addons[__name__].preferences.operatorC38:
                bpy.app.timers.register(lambda: voice_split()) # COMMAND38c 调用“拆分”菜单
            elif data == "COMMAND39c" and bpy.context.preferences.addons[__name__].preferences.operatorC39:
                bpy.app.timers.register(lambda: voice_separate()) # COMMAND39c 调用”分离“菜单
            elif data == "COMMAND40c" and bpy.context.preferences.addons[__name__].preferences.operatorC40:
                bpy.app.timers.register(lambda: voice_switch_normal_menu()) # COMMAND40c 调用“切换法向”方法
            elif data == "COMMAND41c" and bpy.context.preferences.addons[__name__].preferences.operatorC41:
                bpy.app.timers.register(lambda: voice_switch_vertex_menu()) # COMMAND41c 调用“切换顶点”方法
            elif data == "COMMAND42c" and bpy.context.preferences.addons[__name__].preferences.operatorC42:
                bpy.app.timers.register(lambda: voice_fill_vertex()) # COMMAND42c 调用“填充顶点”方法
            elif data == "COMMAND43c" and bpy.context.preferences.addons[__name__].preferences.operatorC43:
                bpy.app.timers.register(lambda: voice_link_vertex()) # COMMAND43c 调用“连接顶点”方法
            elif data == "COMMAND44c" and bpy.context.preferences.addons[__name__].preferences.operatorC44:
                bpy.app.timers.register(lambda: voice_slide_vertex()) # COMMAND44c 调用“滑移顶点“方法
            elif data == "COMMAND45c" and bpy.context.preferences.addons[__name__].preferences.operatorC45:
                bpy.app.timers.register(lambda: voice_dissolve_vertex()) # COMMAND45c 调用“融并顶点”方法
            elif data == "COMMAND46c" and bpy.context.preferences.addons[__name__].preferences.operatorC46:
                bpy.app.timers.register(lambda: voice_switch_edge_menu()) # COMMAND46c 调用“切换边”菜单
            elif data == "COMMAND47c" and bpy.context.preferences.addons[__name__].preferences.operatorC47:
                bpy.app.timers.register(lambda: voice_bridge_edge()) # COMMAND47c 调用“桥接循环边”方法
            elif data == "COMMAND48c" and bpy.context.preferences.addons[__name__].preferences.operatorC48:
                bpy.app.timers.register(lambda: voice_edge_crease()) # COMMAND48c 调用“边线折痕”方法
            elif data == "COMMAND49c" and bpy.context.preferences.addons[__name__].preferences.operatorC49:
                bpy.app.timers.register(lambda: voice_dissolve_edge()) # COMMAND49c 调用“融并边”方法
            elif data == "COMMAND50c" and bpy.context.preferences.addons[__name__].preferences.operatorC50:
                bpy.app.timers.register(lambda: voice_switch_face_menu()) # COMMAND50c 调用“切换面”菜单
            elif data == "COMMAND51c" and bpy.context.preferences.addons[__name__].preferences.operatorC51:
                bpy.app.timers.register(lambda: voice_switch_fill_face_menu()) #COMMAND51c 调用“切换填充”菜单
            elif data == "COMMAND52c" and bpy.context.preferences.addons[__name__].preferences.operatorC52:
                bpy.app.timers.register(lambda: voice_fill_face()) # COMMAND52c 调用“填充”函数
            elif data == "COMMAND53c" and bpy.context.preferences.addons[__name__].preferences.operatorC53:
                bpy.app.timers.register(lambda: voice_grid_fill_face()) # COMMAND53c 调用“栅格填充”函数
            elif data == "COMMAND54c" and bpy.context.preferences.addons[__name__].preferences.operatorC54:
                bpy.app.timers.register(lambda: voice_beautify_fill_face()) # COMMAND54c 调用“完美建面”函数
            elif data == "COMMAND1d" and bpy.context.preferences.addons[__name__].preferences.operatorD1:
                bpy.app.timers.register(lambda: voice_brush_freeline()) # COMMAND1d 调用“自由线”笔刷
            elif data == "COMMAND2d" and bpy.context.preferences.addons[__name__].preferences.operatorD2:
                bpy.app.timers.register(lambda: voice_brush_sharp()) # COMMAND2d 调用“锐边”笔刷
            elif data == "COMMAND3d" and bpy.context.preferences.addons[__name__].preferences.operatorD3:
                bpy.app.timers.register(lambda: voice_brush_clay()) # COMMAND3d 调用“黏塑”笔刷
            elif data == "COMMAND4d" and bpy.context.preferences.addons[__name__].preferences.operatorD4:
                bpy.app.timers.register(lambda: voice_brush_claystrip()) # COMMAND4d 调用“黏条”笔刷
            elif data == "COMMAND5d" and bpy.context.preferences.addons[__name__].preferences.operatorD5:
                bpy.app.timers.register(lambda: voice_brush_claythumb()) # COMMAND5d 调用“指推”笔刷
            elif data == "COMMAND6d" and bpy.context.preferences.addons[__name__].preferences.operatorD6:
                bpy.app.timers.register(lambda: voice_brush_layer()) # COMMAND6d 调用“层次”笔刷
            elif data == "COMMAND7d" and bpy.context.preferences.addons[__name__].preferences.operatorD7:
                bpy.app.timers.register(lambda: voice_brush_inflate()) # COMMAND7d 调用“膨胀”笔刷
            elif data == "COMMAND8d" and bpy.context.preferences.addons[__name__].preferences.operatorD8:
                bpy.app.timers.register(lambda: voice_brush_blob()) # COMMAND8d 调用“球体”笔刷
            elif data == "COMMAND9d" and bpy.context.preferences.addons[__name__].preferences.operatorD9:
                bpy.app.timers.register(lambda: voice_brush_crease()) # COMMAND9d 调用“折痕”笔刷
            #elif data == "COMMAND10d" and bpy.context.preferences.addons[__name__].preferences.operatorD10:
            #    bpy.app.timers.register(lambda: voice_brush_smooth()) # COMMAND10d 调用“光滑”笔刷
            elif data == "COMMAND11d" and bpy.context.preferences.addons[__name__].preferences.operatorD11:
                bpy.app.timers.register(lambda: voice_brush_flatten()) # COMMAND11d 调用“平化”笔刷
            elif data == "COMMAND12d" and bpy.context.preferences.addons[__name__].preferences.operatorD12:
                bpy.app.timers.register(lambda: voice_brush_fill()) # COMMAND12d 调用“填充”笔刷
            elif data == "COMMAND13d" and bpy.context.preferences.addons[__name__].preferences.operatorD13:
                bpy.app.timers.register(lambda: voice_brush_scrape()) # COMMAND13d 调用“刮削”笔刷
            elif data == "COMMAND14d" and bpy.context.preferences.addons[__name__].preferences.operatorD14:
                bpy.app.timers.register(lambda: voice_brush_multiscrape()) # COMMAND14d 调用“多平面刮削”笔刷
            elif data == "COMMAND15d" and bpy.context.preferences.addons[__name__].preferences.operatorD15:
                bpy.app.timers.register(lambda: voice_brush_pinch()) # COMMAND15d 调用“夹捏”笔刷
            elif data == "COMMAND16d" and bpy.context.preferences.addons[__name__].preferences.operatorD16:
                bpy.app.timers.register(lambda: voice_brush_grab()) # COMMAND16d 调用“抓起”笔刷
            elif data == "COMMAND17d" and bpy.context.preferences.addons[__name__].preferences.operatorD17:
                bpy.app.timers.register(lambda: voice_brush_elasticdeform()) # COMMAND17d 调用“弹性变形”笔刷
            elif data == "COMMAND18d" and bpy.context.preferences.addons[__name__].preferences.operatorD18:
                bpy.app.timers.register(lambda: voice_brush_snakehook()) # COMMAND18d 调用“蛇形钩”笔刷
            elif data == "COMMAND19d" and bpy.context.preferences.addons[__name__].preferences.operatorD19:
                bpy.app.timers.register(lambda: voice_brush_thumb()) # COMMAND19d 调用“拇指”笔刷
            elif data == "COMMAND20d" and bpy.context.preferences.addons[__name__].preferences.operatorD20:
                bpy.app.timers.register(lambda: voice_brush_pose()) # COMMAND20d 调用“姿态”笔刷
            elif data == "COMMAND21d" and bpy.context.preferences.addons[__name__].preferences.operatorD21:
                bpy.app.timers.register(lambda: voice_brush_nudge()) # COMMAND21d 调用“推移”笔刷
            elif data == "COMMAND22d" and bpy.context.preferences.addons[__name__].preferences.operatorD22:
                bpy.app.timers.register(lambda: voice_brush_rotate()) # COMMAND22d 调用“旋转”笔刷
            elif data == "COMMAND23d" and bpy.context.preferences.addons[__name__].preferences.operatorD23:
                bpy.app.timers.register(lambda: voice_brush_sliderelax()) # COMMAND23d 调用“滑动松弛”笔刷
            elif data == "COMMAND24d" and bpy.context.preferences.addons[__name__].preferences.operatorD24:
                bpy.app.timers.register(lambda: voice_brush_boundry()) # COMMAND24d 调用“边界范围”笔刷
            elif data == "COMMAND25d" and bpy.context.preferences.addons[__name__].preferences.operatorD25:
                bpy.app.timers.register(lambda: voice_brush_cloth()) # COMMAND25d 调用“布料”笔刷
            elif data == "COMMAND26d" and bpy.context.preferences.addons[__name__].preferences.operatorD26:
                bpy.app.timers.register(lambda: voice_brush_simplify()) # COMMAND26d 调用“简化”笔刷
            elif data == "COMMAND27d" and bpy.context.preferences.addons[__name__].preferences.operatorD27:
                bpy.app.timers.register(lambda: voice_brush_mask()) # COMMAND27d 调用“遮罩”笔刷
            elif data == "COMMAND28d" and bpy.context.preferences.addons[__name__].preferences.operatorD28:
                bpy.app.timers.register(lambda: voice_brush_drawfaceset()) # COMMAND28d 调用“绘制面组”笔刷
            elif data == "COMMAND29d" and bpy.context.preferences.addons[__name__].preferences.operatorD29:
                bpy.app.timers.register(lambda: voice_brush_multiresdisplacementeraser()) # COMMAND29d 调用“多精度置换橡皮擦”笔刷
            elif data == "COMMAND30d" and bpy.context.preferences.addons[__name__].preferences.operatorD30:
                bpy.app.timers.register(lambda: voice_brush_multiresdisplacementsmear()) # COMMAND30d 调用“多精度置换涂抹”笔刷
            elif data == "COMMAND31d" and bpy.context.preferences.addons[__name__].preferences.operatorD31:
                bpy.app.timers.register(lambda: voice_brush_paint()) # COMMAND31d 调用“绘制”笔刷
            elif data == "COMMAND32d" and bpy.context.preferences.addons[__name__].preferences.operatorD32:
                bpy.app.timers.register(lambda: voice_brush_smear()) # COMMAND32d 调用“涂抹”笔刷
            elif data == "COMMAND33d" and bpy.context.preferences.addons[__name__].preferences.operatorD33:
                bpy.app.timers.register(lambda: voice_sculpt_switch_mask_menu()) # COMMAND33d 调用“切换遮罩”菜单
            elif data == "COMMAND34d" and bpy.context.preferences.addons[__name__].preferences.operatorD34:
                bpy.app.timers.register(lambda: voice_brush_boxmask()) # COMMAND34d 调用“框选遮罩”笔刷
            elif data == "COMMAND35d" and bpy.context.preferences.addons[__name__].preferences.operatorD35:
                bpy.app.timers.register(lambda: voice_brush_lassomask()) # COMMAND35d 调用“套索遮罩”笔刷
            elif data == "COMMAND36d" and bpy.context.preferences.addons[__name__].preferences.operatorD36:
                bpy.app.timers.register(lambda: voice_brush_linemask()) # COMMAND36d 调用“划线遮罩”笔刷
            elif data == "COMMAND37d" and bpy.context.preferences.addons[__name__].preferences.operatorD37:
                bpy.app.timers.register(lambda: voice_brush_polylinemask()) # COMMAND37d 调用“折线遮罩”笔刷
            elif data == "COMMAND38d" and bpy.context.preferences.addons[__name__].preferences.operatorD38:
                bpy.app.timers.register(lambda: voice_sculpt_switch_hide_menu()) # COMMAND38d 调用“切换隐藏”菜单
            elif data == "COMMAND39d" and bpy.context.preferences.addons[__name__].preferences.operatorD39:
                bpy.app.timers.register(lambda: voice_brush_boxhide()) # COMMAND39d 调用“框选隐藏”笔刷
            elif data == "COMMAND40d" and bpy.context.preferences.addons[__name__].preferences.operatorD40:
                bpy.app.timers.register(lambda: voice_brush_lassohide()) # COMMAND40d 调用“套索隐藏”笔刷
            elif data == "COMMAND41d" and bpy.context.preferences.addons[__name__].preferences.operatorD41:
                bpy.app.timers.register(lambda: voice_brush_linehide()) # COMMAND41d 调用“划线隐藏”笔刷
            elif data == "COMMAND42d" and bpy.context.preferences.addons[__name__].preferences.operatorD42:
                bpy.app.timers.register(lambda: voice_brush_polylinehide()) # COMMAND42d 调用“折线隐藏”笔刷
            elif data == "COMMAND43d" and bpy.context.preferences.addons[__name__].preferences.operatorD43:
                bpy.app.timers.register(lambda: voice_sculpt_switch_faceset_menu()) # COMMAND43d 调用“切换面组”菜单
            elif data == "COMMAND44d" and bpy.context.preferences.addons[__name__].preferences.operatorD44:
                bpy.app.timers.register(lambda: voice_brush_boxfaceset()) # COMMAND44d 调用“框选面组”笔刷
            elif data == "COMMAND45d" and bpy.context.preferences.addons[__name__].preferences.operatorD45:
                bpy.app.timers.register(lambda: voice_brush_lassofaceset()) # COMMAND45d 调用“套索面组”笔刷
            elif data == "COMMAND46d" and bpy.context.preferences.addons[__name__].preferences.operatorD46:
                bpy.app.timers.register(lambda: voice_brush_linefaceset()) # COMMAND46d 调用“划线面组”笔刷
            elif data == "COMMAND47d" and bpy.context.preferences.addons[__name__].preferences.operatorD47:
                bpy.app.timers.register(lambda: voice_brush_polylinefaceset()) # COMMAND47d 调用“折线面组”笔刷
            elif data == "COMMAND48d" and bpy.context.preferences.addons[__name__].preferences.operatorD48:
                bpy.app.timers.register(lambda: voice_sculpt_switch_trim_menu()) # COMMAND48d 调用“切换修剪”菜单
            elif data == "COMMAND49d" and bpy.context.preferences.addons[__name__].preferences.operatorD49:
                bpy.app.timers.register(lambda: voice_brush_boxtrim()) # COMMAND49d 调用“框选修剪”笔刷
            elif data == "COMMAND50d" and bpy.context.preferences.addons[__name__].preferences.operatorD50:
                bpy.app.timers.register(lambda: voice_brush_lassotrim()) # COMMAND50d 调用“套索修剪”笔刷
            elif data == "COMMAND51d" and bpy.context.preferences.addons[__name__].preferences.operatorD51:
                bpy.app.timers.register(lambda: voice_brush_linetrim()) # COMMAND51d 调用“划线修剪”笔刷
            elif data == "COMMAND52d" and bpy.context.preferences.addons[__name__].preferences.operatorD52:
                bpy.app.timers.register(lambda: voice_brush_polylinetrim()) # COMMAND52d 调用“折线修剪”笔刷
            elif data == "COMMAND53d" and bpy.context.preferences.addons[__name__].preferences.operatorD53:
                bpy.app.timers.register(lambda: voice_brush_lineproject()) # COMMAND53d 调用“划线投影”笔刷
            elif data == "COMMAND54d" and bpy.context.preferences.addons[__name__].preferences.operatorD54:
                bpy.app.timers.register(lambda: voice_brush_meshfilter()) # COMMAND54d 调用“网格滤镜”笔刷
            elif data == "COMMAND55d" and bpy.context.preferences.addons[__name__].preferences.operatorD55:
                bpy.app.timers.register(lambda: voice_brush_clothfilter()) # COMMAND55d 调用“布料滤镜”笔刷
            elif data == "COMMAND56d" and bpy.context.preferences.addons[__name__].preferences.operatorD56:
                bpy.app.timers.register(lambda: voice_brush_colorfilter()) # COMMAND56d 调用“色彩滤镜”笔刷
            elif data == "COMMAND57d" and bpy.context.preferences.addons[__name__].preferences.operatorD57:
                bpy.app.timers.register(lambda: voice_brush_facesetedit()) # COMMAND57d 调用“编辑面组”笔刷
            elif data == "COMMAND58d" and bpy.context.preferences.addons[__name__].preferences.operatorD58:
                bpy.app.timers.register(lambda: voice_brush_maskbycolor()) # COMMAND58d 调用“按颜色遮罩”笔刷
            elif data == "COMMAND59d" and bpy.context.preferences.addons[__name__].preferences.operatorD59:
                bpy.app.timers.register(lambda: voice_sculpt_radius()) # COMMAND59d 调用“调节半径”
            elif data == "COMMAND60d" and bpy.context.preferences.addons[__name__].preferences.operatorD60:
                bpy.app.timers.register(lambda: voice_sculpt_strength()) # COMMAND60d 调用“强度/力度”
            elif data == "COMMAND61d" and bpy.context.preferences.addons[__name__].preferences.operatorD61:
                bpy.app.timers.register(lambda: voice_sculpt_angle()) # COMMAND61d 调用“角度”
            elif data == "COMMAND62d" and bpy.context.preferences.addons[__name__].preferences.operatorD62:
                bpy.app.timers.register(lambda: voice_sculpt_voxel_size()) # COMMAND62d 调用“编辑体素大小”
            elif data == "COMMAND63d" and bpy.context.preferences.addons[__name__].preferences.operatorD63:
                bpy.app.timers.register(lambda: voice_sculpt_voxel_remesh()) # COMMAND63d 调用“体素重构”
            elif data == "COMMAND64d" and bpy.context.preferences.addons[__name__].preferences.operatorD64:
                bpy.app.timers.register(lambda: voice_toggle_dynamictopology()) # COMMAND64d 调用“开/关动态拓扑”
            elif data == "COMMAND65d" and bpy.context.preferences.addons[__name__].preferences.operatorD65:
                bpy.app.timers.register(lambda: voice_sculpt_to_add_direction()) # COMMAND65d 调用“正向雕刻”
            elif data == "COMMAND66d" and bpy.context.preferences.addons[__name__].preferences.operatorD66:
                bpy.app.timers.register(lambda: voice_sculpt_to_subtract_direction()) # COMMAND66d 调用“负向雕刻”
            elif data == "COMMAND2e" and bpy.context.preferences.addons[__name__].preferences.operatorE2:
                bpy.app.timers.register(lambda: voice_switch_language()) # COMMAND2e 调用“切换语言”
            elif data == "COMMAND3e" and bpy.context.preferences.addons[__name__].preferences.operatorE3:
                bpy.app.timers.register(lambda: voice_shift_move()) # COMMAND3e 调用“模拟平移”
            elif data == "COMMAND4e" and bpy.context.preferences.addons[__name__].preferences.operatorE4:
                bpy.app.timers.register(lambda: voice_shift_select()) # COMMAND4e 调用“模拟多选”
            elif data == "COMMANDXSHIFT" and ( bpy.context.preferences.addons[__name__].preferences.operatorE3 or bpy.context.preferences.addons[__name__].preferences.operatorE4 ) :
                bpy.app.timers.register(lambda: voice_remove_simulate_shift()) # COMMAND5e 调用“移除按下 Shift 提示”,“取消平移”和“取消多选”共用一条 COMMAND
            elif data == "COMMANDXCTRL" and bpy.context.preferences.addons[__name__].preferences.operatorE5:
                bpy.app.timers.register(lambda: voice_remove_simulate_ctrl()) # COMMAND6e 调用“移除按下 Ctrl 提示”
            elif data == "AXISX" and bpy.context.preferences.addons[__name__].preferences.operatorE6:
                bpy.app.timers.register(lambda: voice_x_axis()) # 调用“模拟X轴”函数
            elif data == "AXISY" and bpy.context.preferences.addons[__name__].preferences.operatorE6:
                bpy.app.timers.register(lambda: voice_y_axis()) # 调用“模拟Y轴”函数
            elif data == "AXISZ" and bpy.context.preferences.addons[__name__].preferences.operatorE6:
                bpy.app.timers.register(lambda: voice_z_axis()) # 调用“模拟Z轴”函数


# 定义可扩展菜单类
class ExpandableMenu(bpy.types.PropertyGroup):
    expand: bpy.props.BoolProperty(default=False)

# 插件设置类，用于保存和恢复设置
class ArduinoControlPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    arduino_port: bpy.props.EnumProperty(
        name="Arduino Port",
        description="选择串口端口",
        items=lambda self, context: [(port.device, port.device, "") for port in serial.tools.list_ports.comports()]
    )

    operatorA1: bpy.props.BoolProperty(
        name="物体模式/物体(Tab)",
        default=True,
        description="切换到物体模式"
    )

    operatorA2: bpy.props.BoolProperty(
        name="编辑模式/编辑(Tab)",
        default=True,
        description="切换到编辑模式"
    )

    operatorA3: bpy.props.BoolProperty(
        name="雕刻模式/雕刻",
        default=True,
        description="切换到雕刻模式"
    )

    operatorA4: bpy.props.BoolProperty(
        name="添加(Shift+A)",
        default=True,
        description="添加"
    )

    operatorA5: bpy.props.BoolProperty(
        name="删除(X)",
        default=True,
        description="删除"
    )

    operatorA6: bpy.props.BoolProperty(
        name="撤销(Ctrl+Z)",
        default=True,
        description="撤销"
    )

    operatorA7: bpy.props.BoolProperty(
        name="重做(Ctrl+Shift+Z)",
        default=True,
        description="重做"
    )

    operatorA8: bpy.props.BoolProperty(
        name="切换调整(Alt+W)",
        default=True,
        description="切换调整"
    )

    operatorA9: bpy.props.BoolProperty(
        name="调整(W)",
        default=True,
        description="调整"
    )

    operatorA10: bpy.props.BoolProperty(
        name="框选(W)",
        default=True,
        description="框选"
    )

    operatorA11: bpy.props.BoolProperty(
        name="刷选(W)",
        default=True,
        description="刷选"
    )

    operatorA12: bpy.props.BoolProperty(
        name="套索选择/套选(W)",
        default=True,
        description="套索选择"
    )

    operatorA13: bpy.props.BoolProperty(
        name="游标(Shift+右击)",
        default=True,
        description="游标"
    )

    operatorA14: bpy.props.BoolProperty(
        name="移动(G)",
        default=True,
        description="移动"
    )

    operatorA15: bpy.props.BoolProperty(
        name="旋转(R)",
        default=True,
        description="旋转"
    )

    operatorA16: bpy.props.BoolProperty(
        name="缩放(S)",
        default=True,
        description="缩放"
    )

    operatorA17: bpy.props.BoolProperty(
        name="罩体缩放",
        default=True,
        description="罩体缩放"
    )

    operatorA18: bpy.props.BoolProperty(
        name="变换",
        default=True,
        description="变换"
    )

    operatorA19: bpy.props.BoolProperty(
        name="切换标注",
        default=True,
        description="标注/标注直线/标注多段线/标注橡皮擦"
    )

    operatorA20: bpy.props.BoolProperty(
        name="标注",
        default=True,
        description="标注"
    )

    operatorA21: bpy.props.BoolProperty(
        name="标注直线",
        default=True,
        description="标注直线"
    )

    operatorA22: bpy.props.BoolProperty(
        name="标注多线段",
        default=True,
        description="标注多线段"
    )

    operatorA23: bpy.props.BoolProperty(
        name="标注橡皮擦",
        default=True,
        description="标注橡皮擦"
    )

    operatorA24: bpy.props.BoolProperty(
        name="测量",
        default=True,
        description="测量(M)"
    )

    operatorA25: bpy.props.BoolProperty(
        name="切换添加",
        default=True,
        description="立方体/锥体/柱体/经纬球/棱角球"
    )

    operatorA26: bpy.props.BoolProperty(
        name="立方体",
        default=True,
        description="快速添加立方体"
    )

    operatorA27: bpy.props.BoolProperty(
        name="锥体",
        default=True,
        description="快速添加锥体"
    )

    operatorA28: bpy.props.BoolProperty(
        name="柱体",
        default=True,
        description="快速添加柱体"
    )

    operatorA29: bpy.props.BoolProperty(
        name="经纬球",
        default=True,
        description="快速添加经纬球"
    )

    operatorA30: bpy.props.BoolProperty(
        name="棱角球",
        default=True,
        description="快速添加棱角球"
    )

    operatorA31: bpy.props.BoolProperty(
        name="切换坐标系/坐标系(<)",
        default=True,
        description="设置坐标系"
    )

    operatorA32: bpy.props.BoolProperty(
        name="切换轴心点/轴心点(>)",
        default=True,
        description="设置轴心点"
    )

    operatorA33: bpy.props.BoolProperty(
        name="吸附(Shift+Tab)",
        default=True,
        description="切换吸附开关状态"
    )

    operatorA34: bpy.props.BoolProperty(
        name="切换吸附(Shift+S)",
        default=True,
        description="切换吸附"
    )

    operatorA35: bpy.props.BoolProperty(
        name="衰减(O)",
        default=True,
        description="切换衰减开关状态"
    )

    operatorA36: bpy.props.BoolProperty(
        name="切换衰减",
        default=True,
        description="切换衰减类型"
    )

    operatorA37: bpy.props.BoolProperty(
        name="切换着色(Z)",
        default=True,
        description="切换着色类型"
    )

    operatorA38: bpy.props.BoolProperty(
        name="线框(Shift+Z)",
        default=True,
        description="线框/实体切换"
    )

    operatorA39: bpy.props.BoolProperty(
        name="切换视图(~)",
        default=True,
        description="切换视图菜单"
    )

    operatorA40: bpy.props.BoolProperty(
        name="摄像机/相机(Num0)",
        default=True,
        description="切换到摄像机视图"
    )

    operatorA41: bpy.props.BoolProperty(
        name="框选全部(Home)",
        default=True,
        description="显示视图框内所有项"
    )

    operatorA42: bpy.props.BoolProperty(
        name="框选所选(.)",
        default=True,
        description="突出显示选中项"
    )

    operatorA43: bpy.props.BoolProperty(
        name="顶视图(Num7)",
        default=True,
        description="顶视图"
    )

    operatorA44: bpy.props.BoolProperty(
        name="底视图(Ctrl+Num7)",
        default=True,
        description="底视图"
    )

    operatorA45: bpy.props.BoolProperty(
        name="前视图(Num1)",
        default=True,
        description="前视图"
    )

    operatorA46: bpy.props.BoolProperty(
        name="后视图(Ctrl+Num1)",
        default=True,
        description="后视图"
    )

    operatorA47: bpy.props.BoolProperty(
        name="左视图(Ctrl+Num3)",
        default=True,
        description="左视图"
    )

    operatorA48: bpy.props.BoolProperty(
        name="右视图(Num3)",
        default=True,
        description="右视图"
    )

    operatorA49: bpy.props.BoolProperty(
        name="局部视图/局部(/)",
        default=True,
        description="局部视图"
    )

    operatorA50: bpy.props.BoolProperty(
        name="隐藏(H)",
        default=True,
        description="隐藏选中项"
    )

    operatorA51: bpy.props.BoolProperty(
        name="隐藏其它/隐藏未选项(Shift+H)",
        default=True,
        description="隐藏未选项"
    )

    operatorA52: bpy.props.BoolProperty(
        name="显示隐藏/取消隐藏(Alt+H)",
        default=True,
        description="显示隐藏物体"
    )

    operatorA53: bpy.props.BoolProperty(
        name="选择全部/全选(A)",
        default=True,
        description="建议使用\"选择全部\""
    )

    operatorA54: bpy.props.BoolProperty(
        name="反选(Ctrl+I)",
        default=True,
        description="反选"
    )

    operatorA55: bpy.props.BoolProperty(
        name="添加平面",
        default=True,
        description="添加平面"
    )

    operatorA56: bpy.props.BoolProperty(
        name="添加立方体",
        default=True,
        description="添加立方体"
    )

    operatorA57: bpy.props.BoolProperty(
        name="添加圆环",
        default=True,
        description="添加圆环"
    )

    operatorA58: bpy.props.BoolProperty(
        name="添加经纬球",
        default=True,
        description="添加经纬球"
    )

    operatorA59: bpy.props.BoolProperty(
        name="添加棱角球",
        default=True,
        description="添加棱角球"
    )

    operatorA60: bpy.props.BoolProperty(
        name="添加柱体",
        default=True,
        description="添加柱体"
    )

    operatorA61: bpy.props.BoolProperty(
        name="添加锥体",
        default=True,
        description="添加锥体"
    )

    operatorA62: bpy.props.BoolProperty(
        name="添加环体",
        default=True,
        description="添加环体"
    )

    operatorA63: bpy.props.BoolProperty(
        name="复制(Shift+D)",
        default=True,
        description="复制"
    )

    operatorA64: bpy.props.BoolProperty(
        name="细分",
        default=True,
        description="物体模式和编辑模式会显示不同的\"细分\"选项"
    )

    operatorA65: bpy.props.BoolProperty(
        name="面朝向",
        default=True,
        description="显示/隐藏面朝向"
    )

    operatorB1: bpy.props.BoolProperty(
        name="切换原点/设置原点/原点",
        default=True,
        description="设置原点"
    )

    operatorB2: bpy.props.BoolProperty(
        name="切换清空/清空",
        default=True,
        description="清空"
    )

    operatorB3: bpy.props.BoolProperty(
        name="切换应用/应用(Ctrl+A)",
        default=True,
        description="应用"
    )

    operatorB4: bpy.props.BoolProperty(
        name="常规复制(Ctrl+C)",
        default=True,
        description="复制"
    )

    operatorB5: bpy.props.BoolProperty(
        name="关联复制(Alt+D)",
        default=True,
        description="关联复制"
    )

    operatorB6: bpy.props.BoolProperty(
        name="粘贴物体/粘贴(Ctrl+V)",
        default=True,
        description="粘贴物体"
    )

    operatorB7: bpy.props.BoolProperty(
        name="合并(Ctrl+J)",
        default=True,
        description="合并"
    )

    operatorC1: bpy.props.BoolProperty(
        name="选择点/选择顶点(1)",
        default=True,
        description="顶点选择模式"
    )

    operatorC2: bpy.props.BoolProperty(
        name="选择边(2)",
        default=True,
        description="边选择模式"
    )

    operatorC3: bpy.props.BoolProperty(
        name="选择面(3)",
        default=True,
        description="面选择模式"
    )

    operatorC4: bpy.props.BoolProperty(
        name="挤出(E)",
        default=True,
        description="挤出"
    )

    operatorC5: bpy.props.BoolProperty(
        name="切换挤出(Alt+E)",
        default=True,
        description="切换挤出"
    )

    operatorC6: bpy.props.BoolProperty(
        name="内插面/内插(I)",
        default=True,
        description="内插面"
    )

    operatorC7: bpy.props.BoolProperty(
        name="顶点倒角/点倒角(Ctrl+Shift+B)",
        default=True,
        description="顶点倒角"
    )

    operatorC8: bpy.props.BoolProperty(
        name="边倒角(Ctrl+B)",
        default=True,
        description="边倒角"
    )

    operatorC9: bpy.props.BoolProperty(
        name="环切(Ctrl+R)",
        default=True,
        description="环切"
    )

    operatorC10: bpy.props.BoolProperty(
        name="偏移环切(Ctrl+Shift+R)",
        default=True,
        description="偏移环切"
    )

    operatorC11: bpy.props.BoolProperty(
        name="切割(K)",
        default=True,
        description="切割"
    )

    operatorC12: bpy.props.BoolProperty(
        name="切分",
        default=True,
        description="切分"
    )

    operatorC13: bpy.props.BoolProperty(
        name="多边形建形",
        default=True,
        description="多边形建形"
    )

    operatorC14: bpy.props.BoolProperty(
        name="旋绕",
        default=True,
        description="旋绕"
    )

    operatorC15: bpy.props.BoolProperty(
        name="光滑",
        default=True,
        description="光滑"
    )

    operatorC16: bpy.props.BoolProperty(
        name="随机",
        default=True,
        description="随机"
    )

    operatorC17: bpy.props.BoolProperty(
        name="边线滑移",
        default=True,
        description="边线滑移"
    )

    operatorC18: bpy.props.BoolProperty(
        name="顶点滑移(Shift+V)",
        default=True,
        description="顶点滑移"
    )

    operatorC19: bpy.props.BoolProperty(
        name="法向缩放(Alt+S)",
        default=True,
        description="法向缩放"
    )

    operatorC20: bpy.props.BoolProperty(
        name="推拉",
        default=True,
        description="推拉"
    )

    operatorC21: bpy.props.BoolProperty(
        name="切变(Ctrl+Shift+Alt+S)",
        default=True,
        description="切变"
    )

    operatorC22: bpy.props.BoolProperty(
        name="球形化(Shift+Alt+S)",
        default=True,
        description="球形化"
    )

    operatorC23: bpy.props.BoolProperty(
        name="断离区域(V)",
        default=True,
        description="断离区域"
    )

    operatorC24: bpy.props.BoolProperty(
        name="断离顶点/断离点",
        default=True,
        description="断离顶点"
    )

    operatorC25: bpy.props.BoolProperty(
        name="断离边",
        default=True,
        description="断离边"
    )

    operatorC26: bpy.props.BoolProperty(
        name="断离边线(Alt+D)",
        default=True,
        description="断离边线"
    )

    operatorC27: bpy.props.BoolProperty(
        name="切换选择",
        default=True,
        description="切换选择"
    )

    operatorC28: bpy.props.BoolProperty(
        name="间隔性弃选/间隔选择",
        default=True,
        description="间隔性弃选"
    )

    operatorC29: bpy.props.BoolProperty(
        name="加选设置",
        default=True,
        description="扩展选区参数设置，不执行操作"
    )

    operatorC30: bpy.props.BoolProperty(
        name="加选(Ctrl+Num+)",
        default=True,
        description="扩展选区"
    )

    operatorC31: bpy.props.BoolProperty(
        name="减选设置",
        default=True,
        description="缩减选区参数设置，不执行操作()"
    )

    operatorC32: bpy.props.BoolProperty(
        name="减选(Ctrl+Num-)",
        default=True,
        description="缩减选区"
    )

    operatorC33: bpy.props.BoolProperty(
        name="选择相连(L)",
        default=True,
        description="关联项"
    )

    operatorC34: bpy.props.BoolProperty(
        name="选择循环/循环边",
        default=True,
        description="循环边"
    )

    operatorC35: bpy.props.BoolProperty(
        name="选择并排/并排边",
        default=True,
        description="并排边"
    )

    operatorC36: bpy.props.BoolProperty(
        name="切换网格",
        default=True,
        description="调出\"网格\"菜单"
    )

    operatorC37: bpy.props.BoolProperty(
        name="合并(M)",
        default=True,
        description="合并"
    )

    operatorC38: bpy.props.BoolProperty(
        name="拆分(Alt+M)",
        default=True,
        description="拆分"
    )

    operatorC39: bpy.props.BoolProperty(
        name="分离(P)",
        default=True,
        description="分离"
    )

    operatorC40: bpy.props.BoolProperty(
        name="切换法向(Alt+N)",
        default=True,
        description="法向菜单"
    )

    operatorC41: bpy.props.BoolProperty(
        name="切换顶点(Ctrl+V)",
        default=True,
        description="\"顶点\"菜单"
    )

    operatorC42: bpy.props.BoolProperty(
        name="填充顶点(F)",
        default=True,
        description="从顶点创建边/面"
    )

    operatorC43: bpy.props.BoolProperty(
        name="连接顶点(J)",
        default=True,
        description="连接顶点路径"
    )

    operatorC44: bpy.props.BoolProperty(
        name="滑移顶点(Shift+V)",
        default=True,
        description="滑移顶点"
    )

    operatorC45: bpy.props.BoolProperty(
        name="融并顶点(Ctrl+X)",
        default=True,
        description="融并顶点"
    )

    operatorC46: bpy.props.BoolProperty(
        name="切换边(Ctrl+E)",
        default=True,
        description="\"边\"菜单"
    )

    operatorC47: bpy.props.BoolProperty(
        name="桥接循环边/桥接",
        default=True,
        description="桥接循环边"
    )

    operatorC48: bpy.props.BoolProperty(
        name="边线折痕(Shift+E)",
        default=True,
        description="边线折痕"
    )

    operatorC49: bpy.props.BoolProperty(
        name="融并边(Ctrl+X)",
        default=True,
        description="融并边"
    )

    operatorC50: bpy.props.BoolProperty(
        name="切换面(Ctrl+F)",
        default=True,
        description="\"面\"菜单"
    )

    operatorC51: bpy.props.BoolProperty(
        name="切换填充",
        default=True,
        description="切换填充"
    )

    operatorC52: bpy.props.BoolProperty(
        name="填充(Alt+F)",
        default=True,
        description="填充"
    )

    operatorC53: bpy.props.BoolProperty(
        name="栅格填充",
        default=True,
        description="栅格填充"
    )

    operatorC54: bpy.props.BoolProperty(
        name="完美建面",
        default=True,
        description="完美建面"
    )

    operatorD1: bpy.props.BoolProperty(
        name="自由线(V)",
        default=True,
        description="自由线"
    )

    operatorD2: bpy.props.BoolProperty(
        name="锐边",
        default=True,
        description="绘制锐边"
    )

    operatorD3: bpy.props.BoolProperty(
        name="黏塑",
        default=True,
        description="黏塑"
    )

    operatorD4: bpy.props.BoolProperty(
        name="黏条(C)",
        default=True,
        description="黏条"
    )

    operatorD5: bpy.props.BoolProperty(
        name="指推",
        default=True,
        description="指推"
    )

    operatorD6: bpy.props.BoolProperty(
        name="层次",
        default=True,
        description="层次"
    )

    operatorD7: bpy.props.BoolProperty(
        name="膨胀(I)",
        default=True,
        description="膨胀"
    )

    operatorD8: bpy.props.BoolProperty(
        name="球体",
        default=True,
        description="球体"
    )

    operatorD9: bpy.props.BoolProperty(
        name="折痕(Shift+C)",
        default=True,
        description="折痕"
    )

    operatorD10: bpy.props.BoolProperty(
        name="光滑(S)",
        default=True,
        description="光滑"
    )

    operatorD11: bpy.props.BoolProperty(
        name="平化",
        default=True,
        description="平化"
    )

    operatorD12: bpy.props.BoolProperty(
        name="填充",
        default=True,
        description="填充"
    )

    operatorD13: bpy.props.BoolProperty(
        name="刮削(Shift+T)",
        default=True,
        description="刮削"
    )

    operatorD14: bpy.props.BoolProperty(
        name="多平面刮削",
        default=True,
        description="多平面刮削"
    )

    operatorD15: bpy.props.BoolProperty(
        name="夹捏(P)",
        default=True,
        description="夹捏"
    )

    operatorD16: bpy.props.BoolProperty(
        name="抓起(G)",
        default=True,
        description="抓起"
    )

    operatorD17: bpy.props.BoolProperty(
        name="弹性变形",
        default=True,
        description="弹性变形"
    )

    operatorD18: bpy.props.BoolProperty(
        name="蛇形钩(K)",
        default=True,
        description="蛇形钩"
    )

    operatorD19: bpy.props.BoolProperty(
        name="拇指",
        default=True,
        description="拇指"
    )

    operatorD20: bpy.props.BoolProperty(
        name="姿态",
        default=True,
        description="姿态"
    )

    operatorD21: bpy.props.BoolProperty(
        name="推移",
        default=True,
        description="推移"
    )

    operatorD22: bpy.props.BoolProperty(
        name="旋转",
        default=True,
        description="旋转"
    )

    operatorD23: bpy.props.BoolProperty(
        name="滑动松弛/拓扑",
        default=True,
        description="滑动松弛(拓扑)"
    )

    operatorD24: bpy.props.BoolProperty(
        name="边界范围",
        default=True,
        description="边界范围"
    )

    operatorD25: bpy.props.BoolProperty(
        name="布料",
        default=True,
        description="布料"
    )

    operatorD26: bpy.props.BoolProperty(
        name="简化",
        default=True,
        description="简化"
    )

    operatorD27: bpy.props.BoolProperty(
        name="遮罩",
        default=True,
        description="遮罩"
    )

    operatorD28: bpy.props.BoolProperty(
        name="绘制面组",
        default=True,
        description="绘制面组"
    )

    operatorD29: bpy.props.BoolProperty(
        name="置换橡皮擦",
        default=True,
        description="多精度置换橡皮擦"
    )

    operatorD30: bpy.props.BoolProperty(
        name="置换涂抹",
        default=True,
        description="多精度置换涂抹"
    )

    operatorD31: bpy.props.BoolProperty(
        name="绘制",
        default=True,
        description="绘制"
    )

    operatorD32: bpy.props.BoolProperty(
        name="涂抹",
        default=True,
        description="涂抹"
    )

    operatorD33: bpy.props.BoolProperty(
        name="切换遮罩",
        default=True,
        description="切换遮罩菜单"
    )

    operatorD34: bpy.props.BoolProperty(
        name="框选遮罩",
        default=True,
        description="框选遮罩(B)"
    )

    operatorD35: bpy.props.BoolProperty(
        name="套索遮罩",
        default=True,
        description="套索遮罩"
    )

    operatorD36: bpy.props.BoolProperty(
        name="线性遮罩",
        default=True,
        description="线性遮罩"
    )

    operatorD37: bpy.props.BoolProperty(
        name="折线遮罩",
        default=True,
        description="折线遮罩"
    )

    operatorD38: bpy.props.BoolProperty(
        name="切换隐藏",
        default=True,
        description="切换隐藏菜单"
    )

    operatorD39: bpy.props.BoolProperty(
        name="框选隐藏",
        default=True,
        description="框选隐藏"
    )

    operatorD40: bpy.props.BoolProperty(
        name="套索隐藏",
        default=True,
        description="套索隐藏"
    )

    operatorD41: bpy.props.BoolProperty(
        name="划线隐藏",
        default=True,
        description="划线隐藏"
    )

    operatorD42: bpy.props.BoolProperty(
        name="折线隐藏",
        default=True,
        description="折线隐藏"
    )

    operatorD43: bpy.props.BoolProperty(
        name="切换面组",
        default=True,
        description="切换面组"
    )

    operatorD44: bpy.props.BoolProperty(
        name="框选面组",
        default=True,
        description="框选面组"
    )

    operatorD45: bpy.props.BoolProperty(
        name="套索面组",
        default=True,
        description="套索面组"
    )

    operatorD46: bpy.props.BoolProperty(
        name="划线面组",
        default=True,
        description="划线面组"
    )

    operatorD47: bpy.props.BoolProperty(
        name="折线面组",
        default=True,
        description="折线面组"
    )

    operatorD48: bpy.props.BoolProperty(
        name="切换修剪",
        default=True,
        description="切换修剪"
    )

    operatorD49: bpy.props.BoolProperty(
        name="框选修剪",
        default=True,
        description="框选修剪"
    )

    operatorD50: bpy.props.BoolProperty(
        name="套索修剪",
        default=True,
        description="套索修剪"
    )

    operatorD51: bpy.props.BoolProperty(
        name="划线修剪",
        default=True,
        description="划线修剪"
    )

    operatorD52: bpy.props.BoolProperty(
        name="折线修剪",
        default=True,
        description="折线修剪"
    )

    operatorD53: bpy.props.BoolProperty(
        name="划线投影",
        default=True,
        description="划线投影"
    )

    operatorD54: bpy.props.BoolProperty(
        name="网格滤镜",
        default=True,
        description="网格滤镜()"
    )

    operatorD55: bpy.props.BoolProperty(
        name="布料滤镜",
        default=True,
        description="布料滤镜"
    )

    operatorD56: bpy.props.BoolProperty(
        name="色彩滤镜",
        default=True,
        description="色彩滤镜"
    )

    operatorD57: bpy.props.BoolProperty(
        name="编辑面组",
        default=True,
        description="编辑面组"
    )

    operatorD58: bpy.props.BoolProperty(
        name="按颜色遮罩",
        default=True,
        description="按颜色遮罩"
    )

    operatorD59: bpy.props.BoolProperty(
        name="半径",
        default=True,
        description="调节半径(F)"
    )

    operatorD60: bpy.props.BoolProperty(
        name="强度/力度",
        default=True,
        description="强度/力度(Shift+F)"
    )

    operatorD61: bpy.props.BoolProperty(
        name="角度",
        default=True,
        description="径向控制(Ctrl+F)"
    )

    operatorD62: bpy.props.BoolProperty(
        name="体素大小",
        default=True,
        description="编辑体素大小(R)"
    )

    operatorD63: bpy.props.BoolProperty(
        name="体素重构",
        default=True,
        description="体素重构(Ctrl+R)"
    )

    operatorD64: bpy.props.BoolProperty(
        name="动态拓扑",
        default=True,
        description="开/关动态拓扑"
    )

    operatorD65: bpy.props.BoolProperty(
        name="正向雕刻",
        default=True,
        description="笔刷增益效果"
    )

    operatorD66: bpy.props.BoolProperty(
        name="负向雕刻",
        default=True,
        description="笔刷消减效果"
    )

    operatorE1: bpy.props.BoolProperty(
        name="操作提示",
        default=True,
        description="开启后，雕刻模式的操作会出现相关提示"
    )

    operatorE2: bpy.props.BoolProperty(
        name="切换语言",
        default=True,
        description="切换中文、英文界面"
    )

    operatorE3: bpy.props.BoolProperty(
        name="平移(不推荐开启)",
        default=False,
        description="模拟鼠标平移(Shift+中键)"
    )

    operatorE4: bpy.props.BoolProperty(
        name="多选(不推荐开启)",
        default=False,
        description="模拟鼠标多选(Shift+左键)进行多选，只针对物体模式和雕刻模式有效"
    )

    operatorE5: bpy.props.BoolProperty(
        name="缩放(不推荐开启)",
        default=False,
        description="模拟鼠标缩放，只针对雕刻模式有效(Ctrl+中键)"
    )

    operatorE6: bpy.props.BoolProperty(
        name="红色/蓝色/绿色(不推荐开启)",
        default=False,
        description="\"红色\"模拟X轴\n\"蓝色\"模拟Z轴\n\"绿色\"模拟Y轴"
    )

    menuA: bpy.props.PointerProperty(type=ExpandableMenu)
    menuB: bpy.props.PointerProperty(type=ExpandableMenu)
    menuC: bpy.props.PointerProperty(type=ExpandableMenu)
    menuD: bpy.props.PointerProperty(type=ExpandableMenu)
    menuE: bpy.props.PointerProperty(type=ExpandableMenu)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "arduino_port", text="Arduino Port")

        col1 = layout.column()
        box_a = col1.box()  # 包裹在 box 中
        box_a.prop(self.menuA, "expand", icon="DOWNARROW_HLT" if self.menuA.expand else "RIGHTARROW", text="通用操作", emboss=False)
        if self.menuA.expand:
            box_a_1 = box_a.box()  # 为选项再添加一个 box
            box_a_1.prop(self, "operatorA1")
            box_a_1.prop(self, "operatorA2")
            box_a_1.prop(self, "operatorA3")
            box_a_1.prop(self, "operatorA4")
            box_a_1.prop(self, "operatorA5")
            box_a_1.prop(self, "operatorA6")
            box_a_1.prop(self, "operatorA7")
            box_a_1.prop(self, "operatorA8")
            box_a_1.prop(self, "operatorA9")
            box_a_1.prop(self, "operatorA10")
            box_a_1.prop(self, "operatorA11")
            box_a_1.prop(self, "operatorA12")
            box_a_1.prop(self, "operatorA13")
            box_a_1.prop(self, "operatorA14")
            box_a_1.prop(self, "operatorA15")
            box_a_1.prop(self, "operatorA16")
            box_a_1.prop(self, "operatorA17")
            box_a_1.prop(self, "operatorA18")
            box_a_1.prop(self, "operatorA19")
            box_a_1.prop(self, "operatorA20")
            box_a_1.prop(self, "operatorA21")
            box_a_1.prop(self, "operatorA22")
            box_a_1.prop(self, "operatorA23")
            box_a_1.prop(self, "operatorA24")
            box_a_1.prop(self, "operatorA25")
            box_a_1.prop(self, "operatorA26")
            box_a_1.prop(self, "operatorA27")
            box_a_1.prop(self, "operatorA28")
            box_a_1.prop(self, "operatorA29")
            box_a_1.prop(self, "operatorA30")
            box_a_1.prop(self, "operatorA31")
            box_a_1.prop(self, "operatorA32")
            box_a_1.prop(self, "operatorA33")
            box_a_1.prop(self, "operatorA34")
            box_a_1.prop(self, "operatorA35")
            box_a_1.prop(self, "operatorA36")
            box_a_1.prop(self, "operatorA37")
            box_a_1.prop(self, "operatorA38")
            box_a_1.prop(self, "operatorA39")
            box_a_1.prop(self, "operatorA40")
            box_a_1.prop(self, "operatorA41")
            box_a_1.prop(self, "operatorA42")
            box_a_1.prop(self, "operatorA43")
            box_a_1.prop(self, "operatorA44")
            box_a_1.prop(self, "operatorA45")
            box_a_1.prop(self, "operatorA46")
            box_a_1.prop(self, "operatorA47")
            box_a_1.prop(self, "operatorA48")
            box_a_1.prop(self, "operatorA49")
            box_a_1.prop(self, "operatorA50")
            box_a_1.prop(self, "operatorA51")
            box_a_1.prop(self, "operatorA52")
            box_a_1.prop(self, "operatorA53")
            box_a_1.prop(self, "operatorA54")
            box_a_1.prop(self, "operatorA55")
            box_a_1.prop(self, "operatorA56")
            box_a_1.prop(self, "operatorA57")
            box_a_1.prop(self, "operatorA58")
            box_a_1.prop(self, "operatorA59")
            box_a_1.prop(self, "operatorA60")
            box_a_1.prop(self, "operatorA61")
            box_a_1.prop(self, "operatorA62")
            box_a_1.prop(self, "operatorA63")
            box_a_1.prop(self, "operatorA64")
            box_a_1.prop(self, "operatorA65")



        col2 = layout.column()
        box_b = col2.box()  # 包裹在 box 中
        box_b.prop(self.menuB, "expand", icon="DOWNARROW_HLT" if self.menuB.expand else "RIGHTARROW", text="物体模式", emboss=False)
        if self.menuB.expand:
            box_b_1 = box_b.box()  # 为选项再添加一个 box
            box_b_1.prop(self, "operatorB1")
            box_b_1.prop(self, "operatorB2")
            box_b_1.prop(self, "operatorB3")
            box_b_1.prop(self, "operatorB4")
            box_b_1.prop(self, "operatorB5")
            box_b_1.prop(self, "operatorB6")
            box_b_1.prop(self, "operatorB7")
            box_b_1.prop(self, "operatorB8")
            box_b_1.prop(self, "operatorB9")
            box_b_1.prop(self, "operatorB10")
            box_b_1.prop(self, "operatorB11")
            box_b_1.prop(self, "operatorB12")
            box_b_1.prop(self, "operatorB13")
            box_b_1.prop(self, "operatorB14")
            box_b_1.prop(self, "operatorB15")
            box_b_1.prop(self, "operatorB16")
            box_b_1.prop(self, "operatorB17")
            box_b_1.prop(self, "operatorB18")
            box_b_1.prop(self, "operatorB19")
            box_b_1.prop(self, "operatorB20")


        col3 = layout.column()
        box_c = col3.box()  # 包裹在 box 中
        box_c.prop(self.menuC, "expand", icon="DOWNARROW_HLT" if self.menuC.expand else "RIGHTARROW", text="编辑模式", emboss=False)
        if self.menuC.expand:
            box_c_1 = box_c.box()  # 为选项再添加一个 box
            box_c_1.prop(self, "operatorC1")
            box_c_1.prop(self, "operatorC2")
            box_c_1.prop(self, "operatorC3")
            box_c_1.prop(self, "operatorC4")
            box_c_1.prop(self, "operatorC5")
            box_c_1.prop(self, "operatorC6")
            box_c_1.prop(self, "operatorC7")
            box_c_1.prop(self, "operatorC8")
            box_c_1.prop(self, "operatorC9")
            box_c_1.prop(self, "operatorC10")
            box_c_1.prop(self, "operatorC11")
            box_c_1.prop(self, "operatorC12")
            box_c_1.prop(self, "operatorC13")
            box_c_1.prop(self, "operatorC14")
            box_c_1.prop(self, "operatorC15")
            box_c_1.prop(self, "operatorC16")
            box_c_1.prop(self, "operatorC17")
            box_c_1.prop(self, "operatorC18")
            box_c_1.prop(self, "operatorC19")
            box_c_1.prop(self, "operatorC20")
            box_c_1.prop(self, "operatorC21")
            box_c_1.prop(self, "operatorC22")
            box_c_1.prop(self, "operatorC23")
            box_c_1.prop(self, "operatorC24")
            box_c_1.prop(self, "operatorC25")
            box_c_1.prop(self, "operatorC26")
            box_c_1.prop(self, "operatorC27")
            box_c_1.prop(self, "operatorC28")
            box_c_1.prop(self, "operatorC29")
            box_c_1.prop(self, "operatorC30")
            box_c_1.prop(self, "operatorC31")
            box_c_1.prop(self, "operatorC32")
            box_c_1.prop(self, "operatorC33")
            box_c_1.prop(self, "operatorC34")
            box_c_1.prop(self, "operatorC35")
            box_c_1.prop(self, "operatorC36")
            box_c_1.prop(self, "operatorC37")
            box_c_1.prop(self, "operatorC38")
            box_c_1.prop(self, "operatorC39")
            box_c_1.prop(self, "operatorC40")
            box_c_1.prop(self, "operatorC41")
            box_c_1.prop(self, "operatorC42")
            box_c_1.prop(self, "operatorC43")
            box_c_1.prop(self, "operatorC44")
            box_c_1.prop(self, "operatorC45")
            box_c_1.prop(self, "operatorC46")
            box_c_1.prop(self, "operatorC47")
            box_c_1.prop(self, "operatorC48")
            box_c_1.prop(self, "operatorC49")
            box_c_1.prop(self, "operatorC50")
            box_c_1.prop(self, "operatorC51")
            box_c_1.prop(self, "operatorC52")
            box_c_1.prop(self, "operatorC53")
            box_c_1.prop(self, "operatorC54")
            box_c_1.prop(self, "operatorC55")
            box_c_1.prop(self, "operatorC56")
            box_c_1.prop(self, "operatorC57")
            box_c_1.prop(self, "operatorC58")
            box_c_1.prop(self, "operatorC59")
            box_c_1.prop(self, "operatorC60")
            box_c_1.prop(self, "operatorC61")
            box_c_1.prop(self, "operatorC62")
            box_c_1.prop(self, "operatorC63")
            box_c_1.prop(self, "operatorC64")
            box_c_1.prop(self, "operatorC65")
            box_c_1.prop(self, "operatorC66")
            box_c_1.prop(self, "operatorC67")
            box_c_1.prop(self, "operatorC68")



        col4 = layout.column()
        box_d = col4.box()  # 包裹在 box 中
        box_d.prop(self.menuD, "expand", icon="DOWNARROW_HLT" if self.menuD.expand else "RIGHTARROW", text="雕刻模式", emboss=False)
        if self.menuD.expand:
            box_d_1 = box_d.box()  # 为选项再添加一个 box
            box_d_1.prop(self, "operatorD1")
            box_d_1.prop(self, "operatorD2")
            box_d_1.prop(self, "operatorD3")
            box_d_1.prop(self, "operatorD4")
            box_d_1.prop(self, "operatorD5")
            box_d_1.prop(self, "operatorD6")
            box_d_1.prop(self, "operatorD7")
            box_d_1.prop(self, "operatorD8")
            box_d_1.prop(self, "operatorD9")
            box_d_1.prop(self, "operatorD10")
            box_d_1.prop(self, "operatorD11")
            box_d_1.prop(self, "operatorD12")
            box_d_1.prop(self, "operatorD13")
            box_d_1.prop(self, "operatorD14")
            box_d_1.prop(self, "operatorD15")
            box_d_1.prop(self, "operatorD16")
            box_d_1.prop(self, "operatorD17")
            box_d_1.prop(self, "operatorD18")
            box_d_1.prop(self, "operatorD19")
            box_d_1.prop(self, "operatorD20")
            box_d_1.prop(self, "operatorD21")
            box_d_1.prop(self, "operatorD22")
            box_d_1.prop(self, "operatorD23")
            box_d_1.prop(self, "operatorD24")
            box_d_1.prop(self, "operatorD25")
            box_d_1.prop(self, "operatorD26")
            box_d_1.prop(self, "operatorD27")
            box_d_1.prop(self, "operatorD28")
            box_d_1.prop(self, "operatorD29")
            box_d_1.prop(self, "operatorD30")
            box_d_1.prop(self, "operatorD31")
            box_d_1.prop(self, "operatorD32")
            box_d_1.prop(self, "operatorD33")
            box_d_1.prop(self, "operatorD34")
            box_d_1.prop(self, "operatorD35")
            box_d_1.prop(self, "operatorD36")
            box_d_1.prop(self, "operatorD37")
            box_d_1.prop(self, "operatorD38")
            box_d_1.prop(self, "operatorD39")
            box_d_1.prop(self, "operatorD40")
            box_d_1.prop(self, "operatorD41")
            box_d_1.prop(self, "operatorD42")
            box_d_1.prop(self, "operatorD43")
            box_d_1.prop(self, "operatorD44")
            box_d_1.prop(self, "operatorD45")
            box_d_1.prop(self, "operatorD46")
            box_d_1.prop(self, "operatorD47")
            box_d_1.prop(self, "operatorD48")
            box_d_1.prop(self, "operatorD49")
            box_d_1.prop(self, "operatorD50")
            box_d_1.prop(self, "operatorD51")
            box_d_1.prop(self, "operatorD52")
            box_d_1.prop(self, "operatorD53")
            box_d_1.prop(self, "operatorD54")
            box_d_1.prop(self, "operatorD55")
            box_d_1.prop(self, "operatorD56")
            box_d_1.prop(self, "operatorD57")
            box_d_1.prop(self, "operatorD58")
            box_d_1.prop(self, "operatorD59")
            box_d_1.prop(self, "operatorD60")
            box_d_1.prop(self, "operatorD61")
            box_d_1.prop(self, "operatorD62")
            box_d_1.prop(self, "operatorD63")
            box_d_1.prop(self, "operatorD64")
            box_d_1.prop(self, "operatorD65")
            box_d_1.prop(self, "operatorD66")
            box_d_1.prop(self, "operatorD67")
            box_d_1.prop(self, "operatorD68")
            box_d_1.prop(self, "operatorD69")
            box_d_1.prop(self, "operatorD70")



        col5 = layout.column()
        box_e = col5.box()  # 包裹在 box 中
        box_e.prop(self.menuE, "expand", icon="DOWNARROW_HLT" if self.menuE.expand else "RIGHTARROW", text="附加功能", emboss=False)
        if self.menuE.expand:
            box_e_1 = box_e.box()  # 为选项再添加一个 box
            box_e_1.prop(self, "operatorE1")
            box_e_1.prop(self, "operatorE2")
            box_e_1.prop(self, "operatorE3")
            box_e_1.prop(self, "operatorE4")
            box_e_1.prop(self, "operatorE5")
            box_e_1.prop(self, "operatorE6")

# 面板类
class ArduinoControlPanel(bpy.types.Panel):
    bl_label = "语音编辑"
    bl_idname = "OBJECT_PT_arduino_control"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VoiceEdit'

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons[__name__].preferences

        layout.prop(prefs, "arduino_port", text="端口")

        if listening_active:
            layout.operator("wm.arduino_stop_operator", text="■")
        else:
            layout.operator("wm.arduino_start_operator", text="▶")

        col1 = layout.column()
        box_a = col1.box()  # 包裹在 box 中
        box_a.prop(prefs.menuA, "expand", icon="DOWNARROW_HLT" if prefs.menuA.expand else "RIGHTARROW", text="通用操作", emboss=False)
        if prefs.menuA.expand:
            box_a_1 = box_a.box()  # 为选项再添加一个 box
            box_a_1.prop(prefs, "operatorA1")
            box_a_1.prop(prefs, "operatorA2")
            box_a_1.prop(prefs, "operatorA3")
            box_a_1.prop(prefs, "operatorA4")
            box_a_1.prop(prefs, "operatorA5")
            box_a_1.prop(prefs, "operatorA6")
            box_a_1.prop(prefs, "operatorA7")
            box_a_1.prop(prefs, "operatorA8")
            box_a_1.prop(prefs, "operatorA9")
            box_a_1.prop(prefs, "operatorA10")
            box_a_1.prop(prefs, "operatorA11")
            box_a_1.prop(prefs, "operatorA12")
            box_a_1.prop(prefs, "operatorA13")
            box_a_1.prop(prefs, "operatorA14")
            box_a_1.prop(prefs, "operatorA15")
            box_a_1.prop(prefs, "operatorA16")
            box_a_1.prop(prefs, "operatorA17")
            box_a_1.prop(prefs, "operatorA18")
            box_a_1.prop(prefs, "operatorA19")
            box_a_1.prop(prefs, "operatorA20")
            box_a_1.prop(prefs, "operatorA21")
            box_a_1.prop(prefs, "operatorA22")
            box_a_1.prop(prefs, "operatorA23")
            box_a_1.prop(prefs, "operatorA24")
            box_a_1.prop(prefs, "operatorA25")
            box_a_1.prop(prefs, "operatorA26")
            box_a_1.prop(prefs, "operatorA27")
            box_a_1.prop(prefs, "operatorA28")
            box_a_1.prop(prefs, "operatorA29")
            box_a_1.prop(prefs, "operatorA30")
            box_a_1.prop(prefs, "operatorA31")
            box_a_1.prop(prefs, "operatorA32")
            box_a_1.prop(prefs, "operatorA33")
            box_a_1.prop(prefs, "operatorA34")
            box_a_1.prop(prefs, "operatorA35")
            box_a_1.prop(prefs, "operatorA36")
            box_a_1.prop(prefs, "operatorA37")
            box_a_1.prop(prefs, "operatorA38")
            box_a_1.prop(prefs, "operatorA39")
            box_a_1.prop(prefs, "operatorA40")
            box_a_1.prop(prefs, "operatorA41")
            box_a_1.prop(prefs, "operatorA42")
            box_a_1.prop(prefs, "operatorA43")
            box_a_1.prop(prefs, "operatorA44")
            box_a_1.prop(prefs, "operatorA45")
            box_a_1.prop(prefs, "operatorA46")
            box_a_1.prop(prefs, "operatorA47")
            box_a_1.prop(prefs, "operatorA48")
            box_a_1.prop(prefs, "operatorA49")
            box_a_1.prop(prefs, "operatorA50")
            box_a_1.prop(prefs, "operatorA51")
            box_a_1.prop(prefs, "operatorA52")
            box_a_1.prop(prefs, "operatorA53")
            box_a_1.prop(prefs, "operatorA54")
            box_a_1.prop(prefs, "operatorA55")
            box_a_1.prop(prefs, "operatorA56")
            box_a_1.prop(prefs, "operatorA57")
            box_a_1.prop(prefs, "operatorA58")
            box_a_1.prop(prefs, "operatorA59")
            box_a_1.prop(prefs, "operatorA60")
            box_a_1.prop(prefs, "operatorA61")
            box_a_1.prop(prefs, "operatorA62")
            box_a_1.prop(prefs, "operatorA63")
            box_a_1.prop(prefs, "operatorA64")
            box_a_1.prop(prefs, "operatorA65")


        col2 = layout.column()
        box_b = col2.box()  # 包裹在 box 中
        box_b.prop(prefs.menuB, "expand", icon="DOWNARROW_HLT" if prefs.menuB.expand else "RIGHTARROW", text="物体模式", emboss=False)
        if prefs.menuB.expand:
            box_b_1 = box_b.box()  # 为选项再添加一个 box
            box_b_1.prop(prefs, "operatorB1")
            box_b_1.prop(prefs, "operatorB2")
            box_b_1.prop(prefs, "operatorB3")
            box_b_1.prop(prefs, "operatorB4")
            box_b_1.prop(prefs, "operatorB5")
            box_b_1.prop(prefs, "operatorB6")
            box_b_1.prop(prefs, "operatorB7")
            box_b_1.prop(prefs, "operatorB8")
            box_b_1.prop(prefs, "operatorB9")
            box_b_1.prop(prefs, "operatorB10")
            box_b_1.prop(prefs, "operatorB11")
            box_b_1.prop(prefs, "operatorB12")
            box_b_1.prop(prefs, "operatorB13")
            box_b_1.prop(prefs, "operatorB14")
            box_b_1.prop(prefs, "operatorB15")
            box_b_1.prop(prefs, "operatorB16")
            box_b_1.prop(prefs, "operatorB17")
            box_b_1.prop(prefs, "operatorB18")
            box_b_1.prop(prefs, "operatorB19")
            box_b_1.prop(prefs, "operatorB20")


        col3 = layout.column()
        box_c = col3.box()  # 包裹在 box 中
        box_c.prop(prefs.menuC, "expand", icon="DOWNARROW_HLT" if prefs.menuC.expand else "RIGHTARROW", text="编辑模式", emboss=False)
        if prefs.menuC.expand:
            box_c_1 = box_c.box()  # 为选项再添加一个 box
            box_c_1.prop(prefs, "operatorC1")
            box_c_1.prop(prefs, "operatorC2")
            box_c_1.prop(prefs, "operatorC3")
            box_c_1.prop(prefs, "operatorC4")
            box_c_1.prop(prefs, "operatorC5")
            box_c_1.prop(prefs, "operatorC6")
            box_c_1.prop(prefs, "operatorC7")
            box_c_1.prop(prefs, "operatorC8")
            box_c_1.prop(prefs, "operatorC9")
            box_c_1.prop(prefs, "operatorC10")
            box_c_1.prop(prefs, "operatorC11")
            box_c_1.prop(prefs, "operatorC12")
            box_c_1.prop(prefs, "operatorC13")
            box_c_1.prop(prefs, "operatorC14")
            box_c_1.prop(prefs, "operatorC15")
            box_c_1.prop(prefs, "operatorC16")
            box_c_1.prop(prefs, "operatorC17")
            box_c_1.prop(prefs, "operatorC18")
            box_c_1.prop(prefs, "operatorC19")
            box_c_1.prop(prefs, "operatorC20")
            box_c_1.prop(prefs, "operatorC21")
            box_c_1.prop(prefs, "operatorC22")
            box_c_1.prop(prefs, "operatorC23")
            box_c_1.prop(prefs, "operatorC24")
            box_c_1.prop(prefs, "operatorC25")
            box_c_1.prop(prefs, "operatorC26")
            box_c_1.prop(prefs, "operatorC27")
            box_c_1.prop(prefs, "operatorC28")
            box_c_1.prop(prefs, "operatorC29")
            box_c_1.prop(prefs, "operatorC30")
            box_c_1.prop(prefs, "operatorC31")
            box_c_1.prop(prefs, "operatorC32")
            box_c_1.prop(prefs, "operatorC33")
            box_c_1.prop(prefs, "operatorC34")
            box_c_1.prop(prefs, "operatorC35")
            box_c_1.prop(prefs, "operatorC36")
            box_c_1.prop(prefs, "operatorC37")
            box_c_1.prop(prefs, "operatorC38")
            box_c_1.prop(prefs, "operatorC39")
            box_c_1.prop(prefs, "operatorC40")
            box_c_1.prop(prefs, "operatorC41")
            box_c_1.prop(prefs, "operatorC42")
            box_c_1.prop(prefs, "operatorC43")
            box_c_1.prop(prefs, "operatorC44")
            box_c_1.prop(prefs, "operatorC45")
            box_c_1.prop(prefs, "operatorC46")
            box_c_1.prop(prefs, "operatorC47")
            box_c_1.prop(prefs, "operatorC48")
            box_c_1.prop(prefs, "operatorC49")
            box_c_1.prop(prefs, "operatorC50")
            box_c_1.prop(prefs, "operatorC51")
            box_c_1.prop(prefs, "operatorC52")
            box_c_1.prop(prefs, "operatorC53")
            box_c_1.prop(prefs, "operatorC54")
            box_c_1.prop(prefs, "operatorC55")
            box_c_1.prop(prefs, "operatorC56")
            box_c_1.prop(prefs, "operatorC57")
            box_c_1.prop(prefs, "operatorC58")
            box_c_1.prop(prefs, "operatorC59")
            box_c_1.prop(prefs, "operatorC60")
            box_c_1.prop(prefs, "operatorC61")
            box_c_1.prop(prefs, "operatorC62")
            box_c_1.prop(prefs, "operatorC63")
            box_c_1.prop(prefs, "operatorC64")
            box_c_1.prop(prefs, "operatorC65")
            box_c_1.prop(prefs, "operatorC66")
            box_c_1.prop(prefs, "operatorC67")
            box_c_1.prop(prefs, "operatorC68")

        col4 = layout.column()
        box_d = col4.box()  # 包裹在 box 中
        box_d.prop(prefs.menuD, "expand", icon="DOWNARROW_HLT" if prefs.menuD.expand else "RIGHTARROW", text="雕刻模式", emboss=False)
        if prefs.menuD.expand:
            box_d_1 = box_d.box()  # 为选项再添加一个 box
            box_d_1.prop(prefs, "operatorD1")
            box_d_1.prop(prefs, "operatorD2")
            box_d_1.prop(prefs, "operatorD3")
            box_d_1.prop(prefs, "operatorD4")
            box_d_1.prop(prefs, "operatorD5")
            box_d_1.prop(prefs, "operatorD6")
            box_d_1.prop(prefs, "operatorD7")
            box_d_1.prop(prefs, "operatorD8")
            box_d_1.prop(prefs, "operatorD9")
            box_d_1.prop(prefs, "operatorD10")
            box_d_1.prop(prefs, "operatorD11")
            box_d_1.prop(prefs, "operatorD12")
            box_d_1.prop(prefs, "operatorD13")
            box_d_1.prop(prefs, "operatorD14")
            box_d_1.prop(prefs, "operatorD15")
            box_d_1.prop(prefs, "operatorD16")
            box_d_1.prop(prefs, "operatorD17")
            box_d_1.prop(prefs, "operatorD18")
            box_d_1.prop(prefs, "operatorD19")
            box_d_1.prop(prefs, "operatorD20")
            box_d_1.prop(prefs, "operatorD21")
            box_d_1.prop(prefs, "operatorD22")
            box_d_1.prop(prefs, "operatorD23")
            box_d_1.prop(prefs, "operatorD24")
            box_d_1.prop(prefs, "operatorD25")
            box_d_1.prop(prefs, "operatorD26")
            box_d_1.prop(prefs, "operatorD27")
            box_d_1.prop(prefs, "operatorD28")
            box_d_1.prop(prefs, "operatorD29")
            box_d_1.prop(prefs, "operatorD30")
            box_d_1.prop(prefs, "operatorD31")
            box_d_1.prop(prefs, "operatorD32")
            box_d_1.prop(prefs, "operatorD33")
            box_d_1.prop(prefs, "operatorD34")
            box_d_1.prop(prefs, "operatorD35")
            box_d_1.prop(prefs, "operatorD36")
            box_d_1.prop(prefs, "operatorD37")
            box_d_1.prop(prefs, "operatorD38")
            box_d_1.prop(prefs, "operatorD39")
            box_d_1.prop(prefs, "operatorD40")
            box_d_1.prop(prefs, "operatorD41")
            box_d_1.prop(prefs, "operatorD42")
            box_d_1.prop(prefs, "operatorD43")
            box_d_1.prop(prefs, "operatorD44")
            box_d_1.prop(prefs, "operatorD45")
            box_d_1.prop(prefs, "operatorD46")
            box_d_1.prop(prefs, "operatorD47")
            box_d_1.prop(prefs, "operatorD48")
            box_d_1.prop(prefs, "operatorD49")
            box_d_1.prop(prefs, "operatorD50")
            box_d_1.prop(prefs, "operatorD51")
            box_d_1.prop(prefs, "operatorD52")
            box_d_1.prop(prefs, "operatorD53")
            box_d_1.prop(prefs, "operatorD54")
            box_d_1.prop(prefs, "operatorD55")
            box_d_1.prop(prefs, "operatorD56")
            box_d_1.prop(prefs, "operatorD57")
            box_d_1.prop(prefs, "operatorD58")
            box_d_1.prop(prefs, "operatorD59")
            box_d_1.prop(prefs, "operatorD60")
            box_d_1.prop(prefs, "operatorD61")
            box_d_1.prop(prefs, "operatorD62")
            box_d_1.prop(prefs, "operatorD63")
            box_d_1.prop(prefs, "operatorD64")
            box_d_1.prop(prefs, "operatorD65")
            box_d_1.prop(prefs, "operatorD66")
            box_d_1.prop(prefs, "operatorD67")
            box_d_1.prop(prefs, "operatorD68")
            box_d_1.prop(prefs, "operatorD69")
            box_d_1.prop(prefs, "operatorD70")



        col5 = layout.column()
        box_e = col5.box()  # 包裹在 box 中
        box_e.prop(prefs.menuE, "expand", icon="DOWNARROW_HLT" if prefs.menuE.expand else "RIGHTARROW", text="附加功能", emboss=False)
        if prefs.menuE.expand:
            box_e_1 = box_e.box()  # 为选项再添加一个 box
            box_e_1.prop(prefs, "operatorE1")
            box_e_1.prop(prefs, "operatorE2")
            box_e_1.prop(prefs, "operatorE3")
            box_e_1.prop(prefs, "operatorE4")
            box_e_1.prop(prefs, "operatorE5")
            box_e_1.prop(prefs, "operatorE6")
            


# 开始监听操作
class ArduinoStartOperator(bpy.types.Operator):
    bl_idname = "wm.arduino_start_operator"
    bl_label = "Start Arduino Listening"
    bl_description = "启动语音编辑"

    def execute(self, context):
        global serial_connection, listening_active, arduino_thread

        prefs = context.preferences.addons[__name__].preferences
        port = prefs.arduino_port

        if not port:
            self.report({'ERROR'}, "请先选择一个串口。")
            return {'CANCELLED'}

        try:
            serial_connection = serial.Serial(port, 9600, timeout=1)
            listening_active = True
            arduino_thread = threading.Thread(target=arduino_listener, daemon=True)
            arduino_thread.start()
        except Exception as e:
            self.report({'ERROR'}, f"无法连接到串口: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


# 停止监听操作
class ArduinoStopOperator(bpy.types.Operator):
    bl_idname = "wm.arduino_stop_operator"
    bl_label = "Stop Arduino Listening"
    bl_description = "停止语音编辑"

    def execute(self, context):
        global listening_active, serial_connection

        listening_active = False
        if serial_connection:
            serial_connection.close()
            serial_connection = None

        return {'FINISHED'}


# 注册和注销函数
def register():
    bpy.utils.register_class(ExpandableMenu)
    bpy.utils.register_class(ArduinoControlPreferences)
    bpy.utils.register_class(ArduinoControlPanel)
    bpy.utils.register_class(ArduinoStartOperator)
    bpy.utils.register_class(ArduinoStopOperator)
    bpy.utils.register_class(VoiceSwitchAnnotationMenu)
    bpy.utils.register_class(VoiceQuickAddMenu)
    bpy.utils.register_class(VoiceSwitchOrientationMenu)
    bpy.utils.register_class(VoiceSwitchOrientationOperator)
    bpy.utils.register_class(VoiceQuickAddOperator)
    bpy.utils.register_class(VoiceSwitchAnnotationOperator)
    bpy.utils.register_class(VoiceSwitchPivotPointOperator)
    bpy.utils.register_class(VoiceSwitchPivotPointMenu)
    bpy.utils.register_class(VoiceSwitchFalloffOperator)
    bpy.utils.register_class(VoiceSwitchFalloffMenu)
    bpy.utils.register_class(VoiceSwitchViewMenu) #测试
    bpy.utils.register_class(VoiceToCameraView) # test
    bpy.utils.register_class(VoiceToTopView)
    bpy.utils.register_class(VoiceToBottomView)
    bpy.utils.register_class(VoiceToFrontView)
    bpy.utils.register_class(VoiceToBackView)
    bpy.utils.register_class(VoiceToLeftView)
    bpy.utils.register_class(VoiceToRightView)
    bpy.utils.register_class(VoiceToLocalView)
    bpy.utils.register_class(VoiceHide)
    bpy.utils.register_class(VoiceHideOthers)
    bpy.utils.register_class(VoiceShowHide)
    bpy.utils.register_class(VoiceViewAll)
    bpy.utils.register_class(VoiceViewSelected)
    bpy.utils.register_class(SetObjectSubdivisionLevel)
    bpy.utils.register_class(VoiceObjectSubdivisionMenu)
    bpy.utils.register_class(SetFacedivideLevel)
    bpy.utils.register_class(VoiceAddPlane)
    bpy.utils.register_class(VoiceAddCube)
    bpy.utils.register_class(VoiceAddCircle)
    bpy.utils.register_class(VoiceAddUVSphere)
    bpy.utils.register_class(VoiceAddIcoSphere)
    bpy.utils.register_class(VoiceAddCylinder)
    bpy.utils.register_class(VoiceAddCone)
    bpy.utils.register_class(VoiceAddTorus)
    bpy.utils.register_class(VoiceSwitchOriginMenu)
    bpy.utils.register_class(VoiceSwitchOriginOperator)
    bpy.utils.register_class(VoiceSelectNTH)
    bpy.utils.register_class(VoiceSelectMoreSetting)
    bpy.types.Scene.more_use_face_step = bpy.props.BoolProperty(name="面步长", default=True)
    bpy.utils.register_class(VoiceSelectLessSetting)
    bpy.types.Scene.less_use_face_step = bpy.props.BoolProperty(name="面步长", default=True)
    bpy.utils.register_class(VoiceSwitchSeparateMenu)
    bpy.utils.register_class(VoiceEdgeCreaseOperator)
    bpy.utils.register_class(VoiceDissolveEdgeOperator)
    bpy.utils.register_class(VoiceFillFaceOperator)
    bpy.utils.register_class(VoiceGridFillFaceOperator)
    bpy.utils.register_class(VoiceBeautifyFillFaceOperator)
    bpy.utils.register_class(VoiceSwitchFillFaceMenu)
    bpy.utils.register_class(VoiceSwitchSculptMaskBrushMenu)
    bpy.utils.register_class(VoiceSwitchSculptBoxMask)
    bpy.utils.register_class(VoiceSwitchSculptLassoMask)
    bpy.utils.register_class(VoiceSwitchSculptLineMask)
    bpy.utils.register_class(VoiceSwitchSculptPolylineMask)
    bpy.utils.register_class(VoiceSwitchSculptHideBrushMenu)
    bpy.utils.register_class(VoiceSculptBoxHide)
    bpy.utils.register_class(VoiceSculptLassoHide)
    bpy.utils.register_class(VoiceSculptLineHide)
    bpy.utils.register_class(VoiceSculptPolylineHide)
    bpy.utils.register_class(VoiceSwitchSculptFacesetBrushMenu)
    bpy.utils.register_class(VoiceSculptBoxFaceset)
    bpy.utils.register_class(VoiceSculptLassoFaceset)
    bpy.utils.register_class(VoiceSculptLineFaceset)
    bpy.utils.register_class(VoiceSculptPolylineFaceset)
    bpy.utils.register_class(VoiceSwitchSculptTrimBrushMenu)
    bpy.utils.register_class(VoiceSculptBoxTrim)
    bpy.utils.register_class(VoiceSculptLassoTrim)
    bpy.utils.register_class(VoiceSculptLineTrim)
    bpy.utils.register_class(VoiceSculptPolylineTrim)


def unregister():
    bpy.utils.unregister_class(ExpandableMenu)
    bpy.utils.unregister_class(ArduinoControlPreferences)
    bpy.utils.unregister_class(ArduinoControlPanel)
    bpy.utils.unregister_class(ArduinoStartOperator)
    bpy.utils.unregister_class(ArduinoStopOperator)
    bpy.utils.unregister_class(VoiceSwitchAnnotationMenu)
    bpy.utils.unregister_class(VoiceQuickAddMenu)
    bpy.utils.unregister_class(VoiceSwitchOrientationMenu)
    bpy.utils.unregister_class(VoiceSwitchOrientationOperator)
    bpy.utils.unregister_class(VoiceQuickAddOperator)
    bpy.utils.unregister_class(VoiceSwitchAnnotationOperator)
    bpy.utils.unregister_class(VoiceSwitchPivotPointOperator)
    bpy.utils.unregister_class(VoiceSwitchPivotPointMenu)
    bpy.utils.unregister_class(VoiceSwitchFalloffOperator)
    bpy.utils.unregister_class(VoiceSwitchFalloffMenu)
    bpy.utils.unregister_class(VoiceSwitchViewMenu) 
    bpy.utils.unregister_class(VoiceToCameraView)
    bpy.utils.unregister_class(VoiceToTopView)
    bpy.utils.unregister_class(VoiceToBottomView)
    bpy.utils.unregister_class(VoiceToFrontView)
    bpy.utils.unregister_class(VoiceToBackView)
    bpy.utils.unregister_class(VoiceToLeftView)
    bpy.utils.unregister_class(VoiceToRightView)
    bpy.utils.unregister_class(VoiceToLocalView)
    bpy.utils.unregister_class(VoiceHide)
    bpy.utils.unregister_class(VoiceHideOthers)
    bpy.utils.unregister_class(VoiceShowHide)
    bpy.utils.unregister_class(VoiceViewAll)
    bpy.utils.unregister_class(VoiceViewSelected)
    bpy.utils.unregister_class(SetObjectSubdivisionLevel)
    bpy.utils.unregister_class(VoiceObjectSubdivisionMenu)
    bpy.utils.unregister_class(SetFacedivideLevel)
    bpy.utils.unregister_class(VoiceAddPlane)
    bpy.utils.unregister_class(VoiceAddCube)
    bpy.utils.unregister_class(VoiceAddCircle)
    bpy.utils.unregister_class(VoiceAddUVSphere)
    bpy.utils.unregister_class(VoiceAddIcoSphere)
    bpy.utils.unregister_class(VoiceAddCylinder)
    bpy.utils.unregister_class(VoiceAddCone)
    bpy.utils.unregister_class(VoiceAddTorus)
    bpy.utils.unregister_class(VoiceSwitchOriginMenu)
    bpy.utils.unregister_class(VoiceSwitchOriginOperator)
    bpy.utils.unregister_class(VoiceSelectNTH)
    bpy.utils.unregister_class(VoiceSelectMoreSetting)
    del bpy.types.Scene.more_use_face_step
    bpy.utils.unregister_class(VoiceSelectLessSetting)
    del bpy.types.Scene.less_use_face_step
    bpy.utils.unregister_class(VoiceSwitchSeparateMenu)
    bpy.utils.unregister_class(VoiceEdgeCreaseOperator)
    bpy.utils.unregister_class(VoiceDissolveEdgeOperator)
    bpy.utils.unregister_class(VoiceFillFaceOperator)
    bpy.utils.unregister_class(VoiceGridFillFaceOperator)
    bpy.utils.unregister_class(VoiceBeautifyFillFaceOperator)
    bpy.utils.unregister_class(VoiceSwitchFillFaceMenu)
    bpy.utils.unregister_class(VoiceSwitchSculptMaskBrushMenu)
    bpy.utils.unregister_class(VoiceSwitchSculptBoxMask)
    bpy.utils.unregister_class(VoiceSwitchSculptLassoMask)
    bpy.utils.unregister_class(VoiceSwitchSculptLineMask)
    bpy.utils.unregister_class(VoiceSwitchSculptPolylineMask)
    bpy.utils.unregister_class(VoiceSwitchSculptHideBrushMenu)
    bpy.utils.unregister_class(VoiceSculptBoxHide)
    bpy.utils.unregister_class(VoiceSculptLassoHide)
    bpy.utils.unregister_class(VoiceSculptLineHide)
    bpy.utils.unregister_class(VoiceSculptPolylineHide)
    bpy.utils.unregister_class(VoiceSwitchSculptFacesetBrushMenu)
    bpy.utils.unregister_class(VoiceSculptBoxFaceset)
    bpy.utils.unregister_class(VoiceSculptLassoFaceset)
    bpy.utils.unregister_class(VoiceSculptLineFaceset)
    bpy.utils.unregister_class(VoiceSculptPolylineFaceset)
    bpy.utils.unregister_class(VoiceSwitchSculptTrimBrushMenu)
    bpy.utils.unregister_class(VoiceSculptBoxTrim)
    bpy.utils.unregister_class(VoiceSculptLassoTrim)
    bpy.utils.unregister_class(VoiceSculptLineTrim)
    bpy.utils.unregister_class(VoiceSculptPolylineTrim)


if __name__ == "__main__":
    register()
