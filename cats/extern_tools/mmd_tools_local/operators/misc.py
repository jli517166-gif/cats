# -*- coding: utf-8 -*-

import re

import bpy
from bpy.types import Operator

from mmd_tools_local import register_wrap
from mmd_tools_local import utils
from mmd_tools_local.bpyutils import ObjectOp
from mmd_tools_local.core import model as mmd_model
from mmd_tools_local.core.morph import FnMorph
from mmd_tools_local.core.material import FnMaterial
from mmd_tools_local.core.bone import FnBone


@register_wrap
class MoveObject(Operator, utils.ItemMoveOp):
    bl_idname = 'mmd_tools.object_move'
    bl_label = 'Move Object'
    bl_description = 'Move active object up/down in the list'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    __PREFIX_REGEXP = re.compile(r'(?P<prefix>[0-9A-Z]{3}_)(?P<name>.*)')

    @classmethod
    def set_index(cls, obj, index):
        m = cls.__PREFIX_REGEXP.match(obj.name)
        name = m.group('name') if m else obj.name
        obj.name = '%s_%s'%(utils.int2base(index, 36, 3), name)

    @classmethod
    def get_name(cls, obj, prefix=None):
        m = cls.__PREFIX_REGEXP.match(obj.name)
        name = m.group('name') if m else obj.name
        return name[len(prefix):] if prefix and name.startswith(prefix) else name

    @classmethod
    def normalize_indices(cls, objects):
        for i, x in enumerate(objects):
            cls.set_index(x, i)

    @classmethod
    def poll(cls, context):
        return context.active_object

    def execute(self, context):
        obj = context.active_object
        objects = self.__get_objects(obj)
        if obj not in objects:
            self.report({ 'ERROR' }, 'Can not move object "%s"'%obj.name)
            return { 'CANCELLED' }

        objects.sort(key=lambda x: x.name)
        self.move(objects, objects.index(obj), self.type)
        self.normalize_indices(objects)
        return { 'FINISHED' }

    def __get_objects(self, obj):
        class __MovableList(list):
            def move(self, index_old, index_new):
                item = self[index_old]
                self.remove(item)
                self.insert(index_new, item)

        objects = []
        root = mmd_model.Model.findRoot(obj)
        if root:
            rig = mmd_model.Model(root)
            if obj.mmd_type == 'NONE' and obj.type == 'MESH':
                objects = rig.meshes()
            elif obj.mmd_type == 'RIGID_BODY':
                objects = rig.rigidBodies()
            elif obj.mmd_type == 'JOINT':
                objects = rig.joints()
        return __MovableList(objects)

@register_wrap
class CleanShapeKeys(Operator):
    bl_idname = 'mmd_tools.clean_shape_keys'
    bl_label = 'Clean Shape Keys'
    bl_description = 'Remove unused shape keys of selected mesh objects'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    @staticmethod
    def __can_remove(key_block):
        if key_block.relative_key == key_block:
            return False # Basis
        for v0, v1 in zip(key_block.relative_key.data, key_block.data):
            if v0.co != v1.co:
                return False
        return True

    def __shape_key_clean(self, obj, key_blocks):
        for kb in key_blocks:
            if self.__can_remove(kb):
                obj.shape_key_remove(kb)
        if len(key_blocks) == 1:
            obj.shape_key_remove(key_blocks[0])

    def execute(self, context):
        for ob in context.selected_objects:
            if ob.type != 'MESH' or ob.data.shape_keys is None:
                continue
            if not ob.data.shape_keys.use_relative:
                continue # not be considered yet
            self.__shape_key_clean(ObjectOp(ob), ob.data.shape_keys.key_blocks)
        return {'FINISHED'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        if root is None:
            self.report({'ERROR'}, '请选择一个 MMD 模型根对象 (通常是空物体)')
            return {'CANCELLED'}

        # === 1. 安全地收集并严格过滤网格对象 ===
        self.report({'INFO'}, '正在扫描并验证模型中的网格对象...')
        
        raw_mesh_candidates = []
        try:
            # 方法1：使用插件API（可能包含杂质）
            rig = mmd_model.Model(root)
            raw_mesh_candidates = list(rig.meshes())
        except Exception as e:
            self.report({'WARNING'}, f'插件API获取网格列表失败: {e}')

        # 如果插件API没找到，尝试直接场景扫描
        if not raw_mesh_candidates:
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH' and mmd_model.Model.findRoot(obj) == root:
                    raw_mesh_candidates.append(obj)

        # === 关键步骤：严格过滤 ===
        valid_meshes = []
        skipped_objects = []
        
        for candidate in raw_mesh_candidates:
            # 条件1：必须是MESH类型
            if candidate.type != 'MESH':
                skipped_objects.append(f'{candidate.name} (类型: {candidate.type})')
                continue
                
            # 条件2：必须有有效的网格数据块
            if not candidate.data or not hasattr(candidate.data, 'vertices'):
                skipped_objects.append(f'{candidate.name} (无效的网格数据)')
                continue
                
            # 条件3：网格应至少包含一些顶点（排除空的占位符）
            if len(candidate.data.vertices) == 0:
                skipped_objects.append(f'{candidate.name} (顶点数为0)')
                continue
                
            # 条件4：额外检查 - 排除可能是骨骼辅助器的简单网格
            # （例如，顶点数极少且可能有特定命名模式的物体）
            vert_count = len(candidate.data.vertices)
            is_likely_bone_mesh = (
                vert_count < 10 and  # 非常少的顶点
                ('bone' in candidate.name.lower() or 
                 '骨骼' in candidate.name or
                 'helper' in candidate.name.lower())
            )
            
            if is_likely_bone_mesh:
                skipped_objects.append(f'{candidate.name} (疑似骨骼辅助网格，顶点数: {vert_count})')
                continue
                
            # 通过所有检查，加入有效列表
            valid_meshes.append(candidate)
            self.report({'INFO'}, f'  确认有效网格: {candidate.name} (顶点数: {vert_count})')

        # 报告过滤结果
        if skipped_objects:
            self.report({'INFO'}, f'跳过 {len(skipped_objects)} 个非标准对象:')
            for skipped in skipped_objects:
                self.report({'INFO'}, f'  - {skipped}')

        # 最终有效性检查
        if len(valid_meshes) < 1:
            error_msg = '未找到任何可合并的有效网格对象。'
            if raw_mesh_candidates:
                error_msg += ' 所有候选对象都已被过滤（详见上方信息）。'
                error_msg += ' 这可能是因为您的模型使用了非标准的骨骼网格或代理对象。'
            else:
                error_msg += ' 请确保模型包含网格对象。'
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}
        
        if len(valid_meshes) == 1:
            self.report({'WARNING'}, '模型只有一个有效网格，无需合并。')
            return {'FINISHED'}

        # === 2. 继续执行安全的合并流程（使用之前验证有效的网格列表）===
        self.report({'INFO'}, f'准备合并 {len(valid_meshes)} 个有效网格...')
        
        # 确保我们有一个明确的活动网格
        context.view_layer.objects.active = valid_meshes[0]
        for obj in valid_meshes:
            obj.select_set(True)

        # [这里插入你之前验证可用的bmesh手动合并代码]
        # 但请将 `meshes_list` 替换为 `valid_meshes`
        # 并确保只对通过过滤的网格执行合并操作

@register_wrap
class AttachMeshesToMMD(Operator):
    bl_idname = 'mmd_tools.attach_meshes'
    bl_label = 'Attach Meshes to Model'
    bl_description = 'Finds existing meshes and attaches them to the selected MMD model'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        root = mmd_model.Model.findRoot(context.active_object)
        if root is None:
            self.report({ 'ERROR' }, 'Select a MMD model')
            return { 'CANCELLED' }

        rig = mmd_model.Model(root)
        armObj = rig.armature()
        if armObj is None:
            self.report({ 'ERROR' }, 'Model Armature not found')
            return { 'CANCELLED' }

        def __get_root(mesh):
            if mesh.parent is None:
                return mesh
            return __get_root(mesh.parent)

        meshes_list = (o for o in context.visible_objects if o.type == 'MESH' and o.mmd_type == 'NONE')
        for mesh in meshes_list:
            if mmd_model.Model.findRoot(mesh) is not None:
                # Do not attach meshes from other models
                continue
            mesh = __get_root(mesh)
            m = mesh.matrix_world
            mesh.parent_type = 'OBJECT'
            mesh.parent = armObj
            mesh.matrix_world = m
        return { 'FINISHED' }

@register_wrap
class ChangeMMDIKLoopFactor(Operator):
    bl_idname = 'mmd_tools.change_mmd_ik_loop_factor'
    bl_label = 'Change MMD IK Loop Factor'
    bl_description = "Multiplier for all bones' IK iterations in Blender"
    bl_options = {'REGISTER', 'UNDO'}

    mmd_ik_loop_factor = bpy.props.IntProperty(
        name='MMD IK Loop Factor',
        description='Scaling factor of MMD IK loop',
        min=1,
        soft_max=10,
        max=100,
        options={'SKIP_SAVE'},
        )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'

    def invoke(self, context, event):
        arm = context.active_object
        self.mmd_ik_loop_factor = max(arm.get('mmd_ik_loop_factor', 1), 1)
        vm = context.window_manager
        return vm.invoke_props_dialog(self)

    def execute(self, context):
        arm = context.active_object

        if '_RNA_UI' not in arm:
            arm['_RNA_UI'] = {}
        prop = {}
        prop['min'] = 1
        prop['soft_min'] = 1
        prop['soft_max'] = 10
        prop['max'] = 100
        prop['description'] = 'Scaling factor of MMD IK loop'
        arm['_RNA_UI']['mmd_ik_loop_factor'] = prop

        old_factor = max(arm.get('mmd_ik_loop_factor', 1), 1)
        new_factor = arm['mmd_ik_loop_factor'] = self.mmd_ik_loop_factor
        if new_factor == old_factor:
            return { 'FINISHED' }
        for b in arm.pose.bones:
            for c in b.constraints:
                if c.type != 'IK':
                    continue
                iterations = int(c.iterations * new_factor / old_factor)
                self.report({ 'INFO' }, 'Update %s of %s: %d -> %d'%(c.name, b.name, c.iterations, iterations))
                c.iterations = iterations
        return { 'FINISHED' }

@register_wrap
class RecalculateBoneRoll(Operator):
    bl_idname = 'mmd_tools.recalculate_bone_roll'
    bl_label = 'Recalculate bone roll'
    bl_description = 'Recalculate bone roll for arm related bones'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'

    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        c = layout.column()
        c.label(text='This operation will break existing f-curve/action.', icon='QUESTION')
        c.label(text='Click [OK] to run the operation.')

    def execute(self, context):
        arm = context.active_object
        FnBone.apply_auto_bone_roll(arm)
        return { 'FINISHED' }
