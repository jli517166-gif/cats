# Thanks to https://www.thegrove3d.com/learn/how-to-translate-a-blender-addon/ for the idea

import os
import csv
import ssl
import bpy
import json
import urllib
import pathlib
import addon_utils
from bpy.app.translations import locale

from .register import register_wrap
# from . import settings

main_dir = pathlib.Path(os.path.dirname(__file__)).parent.resolve()
resources_dir = os.path.join(str(main_dir), "resources")
translations_file = os.path.join(resources_dir, "translations.csv")
settings_file = os.path.join(resources_dir, "settings.json")

dictionary = {}
languages = []
verbose = True
translation_download_link = "https://docs.google.com/spreadsheets/d/1ZAqNxaduDJJ31t9z3BXyBSDmq4mEGySaFafydRoglf4/export?gid=346601779&format=csv"

language_aliases = {
    "zh": "cn_CN",
    "zh_cn": "cn_CN",
    "zh_hans": "cn_CN",
    "zh_hans_cn": "cn_CN",
    "chinese": "cn_CN",
    "chinese (simplified)": "cn_CN",
}

language_labels = {
    "auto": "Auto",
    "en_US": "English",
    "ja_JP": "日本語",
    "ko_KR": "한국어",
    "cn_CN": "简体中文",
}


maintained_translation_overrides = {
    "en_US": {
        "ModelSettings.section.protection": "Protection",
        "ModelSettings.section.custom": "Repair Items",
        "Scene.repair_model_scope.label": "Repair Scope",
        "Scene.repair_model_scope.desc": "Choose which repair preset Fix Model runs",
        "Scene.repair_model_scope.full.label": "Full Repair",
        "Scene.repair_model_scope.full.desc": "Run the full model repair pipeline",
        "Scene.repair_model_scope.safe.label": "Safe Rig Repair",
        "Scene.repair_model_scope.safe.desc": "Repair the rig while keeping IK FK constraints and physics safer",
        "Scene.repair_model_scope.armature.label": "Armature Only",
        "Scene.repair_model_scope.armature.desc": "Repair bone names hierarchy and binding without material edits",
        "Scene.repair_model_scope.weights.label": "Weights Only",
        "Scene.repair_model_scope.weights.desc": "Repair vertex groups and armature binding with minimal scene cleanup",
        "Scene.repair_model_scope.materials.label": "Materials Only",
        "Scene.repair_model_scope.materials.desc": "Repair materials shaders and faulty UV coordinates only",
        "Scene.repair_model_scope.cleanup.label": "Cleanup Only",
        "Scene.repair_model_scope.cleanup.desc": "Remove unused objects and optional physics helpers without changing the rig",
        "Scene.repair_model_scope.custom.label": "Custom",
        "Scene.repair_model_scope.custom.desc": "Use the individual repair switches below",
        "Scene.repair_model_type.label": "Model Type",
        "Scene.repair_model_type.desc": "Choose the model family used by model specific repair steps",
        "Scene.repair_model_type.auto.label": "Auto Detect",
        "Scene.repair_model_type.auto.desc": "Detect MMD VRM Source and FBX style repairs automatically",
        "Scene.repair_model_type.mmd.label": "MMD PMX PMD",
        "Scene.repair_model_type.mmd.desc": "Prefer MMD morph shader and bone handling",
        "Scene.repair_model_type.vrm.label": "VRM",
        "Scene.repair_model_type.vrm.desc": "Prefer VRM mesh and shapekey handling",
        "Scene.repair_model_type.source.label": "Source Engine",
        "Scene.repair_model_type.source.desc": "Prefer Source Engine cleanup and shapekey handling",
        "Scene.repair_model_type.fbx_xps.label": "FBX XPS Unreal",
        "Scene.repair_model_type.fbx_xps.desc": "Prefer transform and orientation repair for FBX XPS style rigs",
        "Scene.repair_model_type.generic.label": "Generic",
        "Scene.repair_model_type.generic.desc": "Use generic repair steps without source specific cleanup",
        "Scene.repair_preserve_ik.label": "Preserve IK",
        "Scene.repair_preserve_ik.desc": "Protect IK bones targets and IK constraints during repair",
        "Scene.repair_preserve_fk.label": "Preserve FK Controls",
        "Scene.repair_preserve_fk.desc": "Protect FK and control bones during repair",
        "Scene.repair_preserve_constraints.label": "Preserve Constraints",
        "Scene.repair_preserve_constraints.desc": "Protect bones used by existing constraints",
        "Scene.repair_rename_bones.label": "Rename Bones",
        "Scene.repair_rename_bones.desc": "Standardize bone names while preserving vertex group weights",
        "Scene.repair_weights.label": "Repair Weights",
        "Scene.repair_weights.desc": "Merge compatible vertex groups and repair armature binding",
        "Scene.repair_hierarchy.label": "Repair Hierarchy",
        "Scene.repair_hierarchy.desc": "Repair parent child relationships for common avatar rigs",
        "Scene.repair_shapekeys.label": "Repair Shape Keys",
        "Scene.repair_shapekeys.desc": "Clean and sort shape keys where supported",
        "Scene.repair_transforms.label": "Repair Transforms",
        "Scene.repair_transforms.desc": "Apply safe transform and zero length bone fixes",
        "Scene.repair_clean_objects.label": "Clean Objects",
        "Scene.repair_clean_objects.desc": "Remove unused objects and broken helper meshes",
        "Scene.repair_uvs.label": "Repair UVs",
        "Scene.repair_uvs.desc": "Replace invalid UV coordinates that can break textures",
        "Scene.repair_model_specific.label": "Model Specific Fixes",
        "Scene.repair_model_specific.desc": "Enable MMD VRM Source and FBX specific handling",
    },
    "cn_CN": {
        "ModelSettings.section.protection": "保护",
        "ModelSettings.section.custom": "修复项目",
        "Scene.repair_model_scope.label": "修复范围",
        "Scene.repair_model_scope.desc": "选择修复模型执行的修复预设",
        "Scene.repair_model_scope.full.label": "完整修复",
        "Scene.repair_model_scope.full.desc": "执行完整模型修复流程",
        "Scene.repair_model_scope.safe.label": "安全骨架修复",
        "Scene.repair_model_scope.safe.desc": "更安全地保留 IK FK 约束和物理",
        "Scene.repair_model_scope.armature.label": "仅骨架",
        "Scene.repair_model_scope.armature.desc": "只修复骨骼命名 层级和绑定",
        "Scene.repair_model_scope.weights.label": "仅权重",
        "Scene.repair_model_scope.weights.desc": "修复顶点组和骨架绑定",
        "Scene.repair_model_scope.materials.label": "仅材质",
        "Scene.repair_model_scope.materials.desc": "只修复材质 着色器和异常 UV",
        "Scene.repair_model_scope.cleanup.label": "仅清理",
        "Scene.repair_model_scope.cleanup.desc": "清理无用对象 不改动骨架",
        "Scene.repair_model_scope.custom.label": "自定义",
        "Scene.repair_model_scope.custom.desc": "使用下方单独修复开关",
        "Scene.repair_model_type.label": "模型类型",
        "Scene.repair_model_type.desc": "选择模型专用修复参考的模型类型",
        "Scene.repair_model_type.auto.label": "自动识别",
        "Scene.repair_model_type.auto.desc": "自动识别 MMD VRM Source 和 FBX 类修复",
        "Scene.repair_model_type.mmd.label": "MMD PMX PMD",
        "Scene.repair_model_type.mmd.desc": "优先使用 MMD 表情 材质和骨骼处理",
        "Scene.repair_model_type.vrm.label": "VRM",
        "Scene.repair_model_type.vrm.desc": "优先使用 VRM 网格和表情键处理",
        "Scene.repair_model_type.source.label": "Source 引擎",
        "Scene.repair_model_type.source.desc": "优先使用 Source 引擎清理和表情键处理",
        "Scene.repair_model_type.fbx_xps.label": "FBX XPS Unreal",
        "Scene.repair_model_type.fbx_xps.desc": "优先修复 FBX XPS 类骨架的变换和朝向",
        "Scene.repair_model_type.generic.label": "通用",
        "Scene.repair_model_type.generic.desc": "使用通用修复步骤",
        "Scene.repair_preserve_ik.label": "保留 IK",
        "Scene.repair_preserve_ik.desc": "修复时保护 IK 骨骼 目标和 IK 约束",
        "Scene.repair_preserve_fk.label": "保留 FK 控制",
        "Scene.repair_preserve_fk.desc": "修复时保护 FK 和控制骨",
        "Scene.repair_preserve_constraints.label": "保留约束",
        "Scene.repair_preserve_constraints.desc": "保护现有约束正在使用的骨骼",
        "Scene.repair_rename_bones.label": "重命名骨骼",
        "Scene.repair_rename_bones.desc": "标准化骨骼名称并保留顶点组权重",
        "Scene.repair_weights.label": "修复权重",
        "Scene.repair_weights.desc": "合并兼容顶点组并修复骨架绑定",
        "Scene.repair_hierarchy.label": "修复层级",
        "Scene.repair_hierarchy.desc": "修复常见模型骨架的父子层级",
        "Scene.repair_shapekeys.label": "修复表情键",
        "Scene.repair_shapekeys.desc": "清理并排序支持的表情键",
        "Scene.repair_transforms.label": "修复变换",
        "Scene.repair_transforms.desc": "应用安全变换和零长度骨修复",
        "Scene.repair_clean_objects.label": "清理对象",
        "Scene.repair_clean_objects.desc": "移除无用对象和异常辅助网格",
        "Scene.repair_uvs.label": "修复 UV",
        "Scene.repair_uvs.desc": "修复可能破坏贴图的异常 UV 坐标",
        "Scene.repair_model_specific.label": "模型专用修复",
        "Scene.repair_model_specific.desc": "启用 MMD VRM Source 和 FBX 专用处理",
    },
}


def apply_maintained_translation_overrides(language):
    for key, value in maintained_translation_overrides["en_US"].items():
        dictionary.setdefault(key, value)

    localized = maintained_translation_overrides.get(language)
    if localized:
        dictionary.update(localized)


def normalize_language(language, available_languages=None):
    if not language:
        return "en_US"

    if available_languages and language in available_languages:
        return language

    normalized = str(language).replace("-", "_")
    alias = language_aliases.get(normalized.lower())
    if alias:
        return alias

    if available_languages and normalized in available_languages:
        return normalized

    return normalized


def load_translations():
    global dictionary, languages
    dictionary = {}
    languages = ["auto"]

    # Check the settings which translation to load
    language = get_language_from_settings()

    with open(translations_file, 'r', encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        if not csv_reader:
            return

        fieldnames = csv_reader.fieldnames or []
        language = normalize_language(language, fieldnames)
        if language not in fieldnames:
            language = "en_US"

        for i, row in enumerate(csv_reader):
            # print(row)
            text = row.get(language)
            if not text:
                text = row.get('en_US')
            dictionary[row['name']] = text

            # get all current languages
            if i == 0:
                for key in row.keys():
                    if '_' in key:
                        languages.append(key)

    apply_maintained_translation_overrides(language)
    check_missing_translations()


def t(phrase: str, *args, **kwargs):
    # Translate the given phrase into Blender's current language.
    output = dictionary.get(phrase)
    if output is None:
        if verbose:
            print('Warning: Unknown phrase: ' + phrase)
        return phrase

    try:
        return output.format(*args, **kwargs)
    except (IndexError, KeyError, ValueError) as e:
        if verbose:
            print('Warning: Could not format phrase: ' + phrase + ' (' + str(e) + ')')
        return output


def check_missing_translations():
    for key, value in dictionary.items():
        if not value and verbose:
            print('Translations en_US: Value missing for key: ' + key)


def get_languages_list(self, context):
    choices = []

    for language in languages:
        # 1. Will be returned by context.scene
        # 2. Will be shown in lists
        # 3. will be shown in the hover description (below description)
        choices.append((language, language_labels.get(language, language), language))

    bpy.types.Object.Enum = choices
    return bpy.types.Object.Enum


def update_ui(self, context):
    from . import settings
    if settings.update_settings_data():
        reload_scripts()


def get_language_from_settings():
    # Load settings file
    try:
        with open(settings_file, encoding="utf8") as file:
            settings_data = json.load(file)
    except FileNotFoundError:
        print("SETTINGS FILE NOT FOUND!")
        return
    except json.decoder.JSONDecodeError:
        print("ERROR FOUND IN SETTINGS FILE")
        return

    if not settings_data:
        print("NO DATA IN SETTINGS FILE")
        return

    lang = settings_data.get("ui_lang")
    if not lang or "auto" in lang.lower():
        return normalize_language(locale)

    return normalize_language(lang)


def reload_scripts():
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == 'Cats Blender Plugin':
            # importlib.reload(mod)
            # bpy.ops.wm.addon_enable(module=mod.__name__)
            # bpy.ops.preferences.addon_disable(module=mod.__name__)
            # bpy.ops.preferences.addon_enable(module=mod.__name__)
            bpy.ops.script.reload()
            break


load_translations()


@register_wrap
class DownloadTranslations(bpy.types.Operator):
    bl_idname = 'cats_translations.download_latest'
    bl_label = t('DownloadTranslations.label')
    bl_description = t('DownloadTranslations.desc')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        self.report({'INFO'}, t('DownloadTranslations.disabled'))
        return {'CANCELLED'}

        # Download csv
        print('DOWNLOAD FILE')
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            urllib.request.urlretrieve(translation_download_link, translations_file)
        except urllib.error.URLError:
            print("TRANSLATIONS FILE COULD NOT BE DOWNLOADED")
            self.report({'ERROR'}, "TRANSLATIONS FILE COULD NOT BE DOWNLOADED, check your internet connection")
            return {'CANCELLED'}
        print('DOWNLOAD FINISHED')

        reload_scripts()

        self.report({'INFO'}, "Successfully downloaded the translations")
        return {'FINISHED'}
