# MIT License

# Copyright (c) 2017 GiveMeAllYourCats

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Code author: Hotox
# Edits by: Hotox

import os
import bpy
import json
import copy
import pathlib
import collections
from datetime import datetime, timezone
from collections import OrderedDict

from .. import globs
from ..tools.register import register_wrap
# from ..googletrans import Translator  # Todo Remove this
from ..extern_tools.google_trans_new.google_trans_new import google_translator
from . import translate as Translate
# Lazy t - defers import to avoid circular dependency
def t(text, context='*'):
    from .translations import t as _t
    return _t(text, context)

main_dir = pathlib.Path(os.path.dirname(__file__)).parent.resolve()
resources_dir = os.path.join(str(main_dir), "resources")
settings_file = os.path.join(resources_dir, "settings.json")

settings_data = None
settings_data_unchanged = None

# Settings name = [Default Value, Require Blender Restart]
settings_default = OrderedDict()
settings_default['show_mmd_tabs'] = [True, False]
settings_default['embed_textures'] = [False, False]
settings_default['ui_lang'] = ["auto", False]
# settings_default['use_custom_mmd_tools'] = [False, True]

lock_settings = False



def save_settings():
    # print('SAVING SETTINGS')
    global settings_data
    try:
        with open(settings_file, 'w', encoding='utf8') as file:
            json.dump(settings_data, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print('ERROR SAVING SETTINGS:', e)


def reset_settings(full_reset=False):
    global settings_data, settings_data_unchanged
    if full_reset:
        settings_data = copy.deepcopy(settings_default)
    else:
        settings_data = copy.deepcopy(settings_data_unchanged)

    for setting in settings_default.keys():
        setattr(bpy.context.scene, setting, settings_data.get(setting))
    
    try:
        with open(settings_file, 'w', encoding='utf8') as file:
            json.dump(settings_data, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print('ERROR RESETTING SETTINGS:', e)


@register_wrap
class RevertChangesButton(bpy.types.Operator):
    bl_idname = 'cats_settings.revert'
    bl_label = t('RevertChangesButton.label')
    bl_description = t('RevertChangesButton.desc')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        for setting in settings_default.keys():
            setattr(bpy.context.scene, setting, settings_data_unchanged.get(setting))
        save_settings()
        self.report({'INFO'}, t('RevertChangesButton.success'))
        return {'FINISHED'}


@register_wrap
class ResetGoogleDictButton(bpy.types.Operator):
    bl_idname = 'cats_settings.reset_google_dict'
    bl_label = t('ResetGoogleDictButton.label')
    bl_description = t('ResetGoogleDictButton.desc')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        Translate.reset_google_dict()
        Translate.load_translations()
        self.report({'INFO'}, t('ResetGoogleDictButton.resetInfo'))
        return {'FINISHED'}


@register_wrap
class DebugTranslations(bpy.types.Operator):
    bl_idname = 'cats_settings.debug_translations'
    bl_label = t('DebugTranslations.label')
    bl_description = t('DebugTranslations.desc')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        bpy.context.scene.debug_translations = True
        translator = google_translator()
        try:
            translator.translate('cat')
        except:
            self.report({'INFO'}, t('DebugTranslations.error'))

        bpy.context.scene.debug_translations = False
        self.report({'INFO'}, t('DebugTranslations.success'))
        return {'FINISHED'}


def load_settings():
    # print('READING SETTINGS FILE')
    global settings_data, settings_data_unchanged

    # Load settings file and reset it if errors are found
    try:
        with open(settings_file, encoding="utf8") as file:
            settings_data = json.load(file, object_pairs_hook=collections.OrderedDict)
            # print('SETTINGS LOADED!')
    except FileNotFoundError:
        print("SETTINGS FILE NOT FOUND!")
        reset_settings(full_reset=True)
        return
    except json.decoder.JSONDecodeError:
        print("ERROR FOUND IN SETTINGS FILE")
        reset_settings(full_reset=True)
        return

    if not settings_data:
        print("NO DATA IN SETTINGS FILE")
        reset_settings(full_reset=True)
        return

    to_reset_settings = []

    # Check for missing entries, reset if necessary
    for setting, value in settings_default.items():
        settings_data[setting] = value[0]

    for setting in to_reset_settings:
            if setting in settings_default.keys():
                settings_data[setting] = settings_default[setting][0]
            else:
                settings_data[setting] = None

    save_settings()

    settings_data_unchanged = copy.deepcopy(settings_data)
    print('SETTINGS RESET')


def start_apply_settings_timer():
    global lock_settings
    lock_settings = True
    if hasattr(bpy.app, 'timers'):
        if not bpy.app.timers.is_registered(apply_settings_timer):
            bpy.app.timers.register(apply_settings_timer, first_interval=0.1)
    else:
        apply_settings()


def apply_settings_timer():
    if not apply_settings():
        return 0.3
    update_settings_data()
    return None


def apply_settings():
    if settings_data is None or not hasattr(bpy.context, 'scene'):
        return False

    scene = bpy.context.scene
    settings_to_reset = []
    for setting, default in settings_default.items():
        value = settings_data.get(setting, default[0])
        try:
            setattr(scene, setting, value)
        except TypeError:
            settings_data[setting] = default[0]
            settings_to_reset.append(setting)
            try:
                setattr(scene, setting, default[0])
            except TypeError:
                pass

    if settings_to_reset:
        save_settings()
        print("RESET SETTINGS ON TIMER:", ', '.join(settings_to_reset))

    # Unlock settings
    global lock_settings
    lock_settings = False
    return True


def settings_changed():
    for setting, value in settings_default.items():
        if value[1] and settings_data.get(setting) != settings_data_unchanged.get(setting):
            return True
    return False


def update_settings_data():
    # Use False and None for this variable, because Blender would complain otherwise
    # None means that the settings did change
    settings_changed_tmp = False
    if lock_settings:
        return settings_changed_tmp

    for setting in settings_default.keys():
        old = settings_data[setting]
        new = getattr(bpy.context.scene, setting)
        if old != new:
            settings_data[setting] = getattr(bpy.context.scene, setting)
            settings_changed_tmp = True

    if settings_changed_tmp:
        save_settings()

    return settings_changed_tmp


def update_settings(self, context):
    update_settings_data()
    return None




def get_use_custom_mmd_tools():
    return settings_data.get('use_custom_mmd_tools')


def get_embed_textures():
    return settings_data.get('embed_textures')


def get_ui_lang():
    return settings_data.get('ui_lang')

