
import bpy

from .. import globs
from .main import ToolPanel, layout_split
from ..tools import settings as Settings
from ..tools.register import register_wrap
from ..tools.translations import t


@register_wrap
class SettingsPanel(ToolPanel, bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_settings_v3'
    bl_label = t('SettingsPanel.name').rstrip(':')
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        # Reset settings
        split = layout_split(layout, factor=0.3)
        row = split.row(align=True)
        row.scale_y = 0.8
        row.label(text=t('SettingsPanel.reset'))
        row = split.row(align=True)
        row.scale_y = 0.8
        row.operator(Settings.RevertChangesButton.bl_idname, icon='LOOP_BACK')

        col.separator()

        # MMD Tabs
        row = col.row(align=True)
        row.prop(context.scene, 'show_mmd_tabs')

        # Embed textures
        row = col.row(align=True)
        row.prop(context.scene, 'embed_textures')

        # UI Language
        row = col.row(align=True)
        row.prop(context.scene, 'ui_lang')

        # Debug Translations
        split = layout_split(layout, factor=0.4)
        row = split.row(align=True)
        row.scale_y = 0.8
        row.label(text=t('SettingsPanel.transDebug'))
        row = col.row(align=True)
        row.prop(context.scene, 'debug_translations')
        if context.scene.debug_translations:
            row = col.row(align=True)
            row.operator('cats_settings.test_translations', icon='PLAY')
