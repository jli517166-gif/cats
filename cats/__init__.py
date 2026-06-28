# MIT License

# Copyright (c) 2026 Codex

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

# Code author: Codex (forked from GiveMeAllYourCats' Cats Blender Plugin)

bl_info = {
    'name': 'Cats Blender Plugin',
    'category': '3D View',
    'author': 'Codex',
    'location': 'View 3D > Tool Shelf > CATS',
    'description': 'Forked from Cats Blender Plugin - Tool for importing and optimizing VRChat models',
    'version': (4, 0, 0),  # Has to be (x, x, x) not [x, x, x]!! Only change this version and the dev branch var right before publishing the new update!
    'blender': (4, 1, 0),
    'wiki_url': '',
    'tracker_url': '',
    'warning': '',
}
dev_branch = False
_mmd_tools_system = False
import os
import sys

# Append files to sys path
file_dir = os.path.join(os.path.dirname(__file__), 'extern_tools')
if file_dir not in sys.path:
    sys.path.append(file_dir)

import shutil
import pathlib
import requests

from . import globs

# Check if cats is reloading or started fresh
if "bpy" not in locals():
    import bpy
    is_reloading = False
else:
    is_reloading = True

# Load or reload all cats modules
if not is_reloading:
    # This order is important
    import mmd_tools_local
    from . import tools
    from . import ui
    from . import extentions
else:
    import importlib
    importlib.reload(mmd_tools_local)
    importlib.reload(tools)
    importlib.reload(ui)
    importlib.reload(extentions)

from .tools import translations
from .tools.translations import t


# How to update mmd_tools: (outdated, no longer used)
# Delete mmd_tools_local folder
# Paste mmd_tools folder into project
# Refactor folder name "mmd_tools" to "mmd_tools_local"
# Move mmd_tools_local folder into extern_tools folder
# Search for "show_backface_culling" and set it to False in view.py
# Done

# How to update google_trans_new:
# In google_trans.py comment out everything that has to do with urllib3
# This is done because 3.5 doesn't have urllib3 by default and it is only used
# to suppress debug logs in the console
# Done

# How to update googletrans:  (outdated since a new googletrans is used Todo remove this)
# in the gtoken.py on line 57 update this line to include "verify=False":
# r = self.session.get(self.host, verify=False)
# In client.py on line 42 remove the Hyper part, it's not faster at all!
# Just comment it out.
# Also see pull request for TKK change
# Also wm progress in client.py
# Done

# How to set up PyCharm with Blender:
# https://b3d.interplanety.org/en/using-external-ide-pycharm-for-writing-blender-scripts/


def remove_corrupted_files():
    to_remove = [
        'googletrans',
        'mmd_tools_local',
        'extern_tools',
        'resources',
        'tests',
        'tools',
        'ui',
        '.gitignore',
        '.travis.yml',
        'LICENSE',
        'README.md',
        '__init__.py',
        'extensions.py',
        'globs.py',
    ]

    no_perm = False
    os_error = False
    wrong_path = False
    faulty_installation = False
    main_dir = str(pathlib.Path(os.path.dirname(__file__)).resolve())

    if main_dir.endswith('addons'):
        print(os.path.dirname(__file__))
        print(main_dir)
        print('Wrong installation path')
        wrong_path = True
    else:
        main_dir = str(pathlib.Path(os.path.dirname(__file__)).parent.resolve())

    # print('Checking for CATS files in the addon directory:\n' + main_dir)
    files = [f for f in os.listdir(main_dir) if os.path.isfile(os.path.join(main_dir, f))]
    folders = [f for f in os.listdir(main_dir) if os.path.isdir(os.path.join(main_dir, f))]

    for file in files:
        if file in to_remove:
            file_path = os.path.join(main_dir, file)
            try:
                os.remove(file_path)
                faulty_installation = True
                print('REMOVED', file)
            except PermissionError:
                no_perm = True
                print("Permissions: Failed to remove file " + file)
            except OSError:
                os_error = True
                print("OS: Failed to remove file " + file)

    for folder in folders:
        if folder in to_remove:
            folder_path = os.path.join(main_dir, folder)
            try:
                shutil.rmtree(folder_path)
                faulty_installation = True
                print('REMOVED', folder)
            except PermissionError:
                no_perm = True
                print("Permissions: Failed to remove folder " + folder)
            except OSError:
                os_error = True
                print("Failed to remove folder " + folder)

    if no_perm:
        unregister()
        sys.tracebacklimit = 0
        raise ImportError(t('Main.error.restartAdmin'))

    if os_error:
        unregister()
        sys.tracebacklimit = 0
        message = t('Main.error.deleteFollowing')

        for folder in folders:
            if folder in to_remove:
                message += "\n- " + os.path.join(main_dir, folder)

        for file in files:
            if file in to_remove:
                message += "\n- " + os.path.join(main_dir, file)

        raise ImportError(message)

    if wrong_path:
        unregister()
        sys.tracebacklimit = 0
        raise ImportError(t('Main.error.installViaPreferences'))

    if faulty_installation:
        unregister()
        sys.tracebacklimit = 0
        raise ImportError(t('Main.error.restartAndEnable'))


def check_unsupported_blender_versions():
    # Don't allow Blender versions older than 2.79
    if bpy.app.version < (2, 79):
        unregister()
        sys.tracebacklimit = 0
        raise ImportError(t('Main.error.unsupportedVersion'))



def set_cats_version_string():
    version = bl_info.get('version')
    version_temp = []
    version_str = ''

    for n in version:
        version_temp.append(n)

    if len(version_temp) > 0:
        # if in dev version, increase version
        if dev_branch:
            version_temp[len(version_temp)-1] += 1

        # Convert version to string
        version_str += str(version_temp[0])
        for index, i in enumerate(version_temp):
            if index == 0:
                continue
            version_str += '.' + str(version_temp[index])

    # Add -dev if in dev version
    if dev_branch:
        version_str += '-dev'

    return version_str


def register():
    print("\n### Loading CATS...")

    # Check for unsupported Blender versions
    check_unsupported_blender_versions()

    # Check for faulty CATS installations
    remove_corrupted_files()

    # Set cats version string
    version_str = set_cats_version_string()


    # Set some global settings, first allowed use of globs
    globs.dev_branch = dev_branch
    globs.version_str = version_str

    # Load settings and show error if a faulty installation was deleted recently
    try:
        tools.settings.load_settings()
    except FileNotFoundError:
        sys.tracebacklimit = 0
        raise ImportError(t('Main.error.restartAndEnable_alt'))

    # if not tools.settings.use_custom_mmd_tools():
    #     bpy.utils.unregister_module("mmd_tools")

    # Load mmd_tools
    # Check if mmd_tools is already installed as a system extension to avoid conflicts
    global _mmd_tools_system
    _mmd_tools_system = False

    # Also check if the official mmd_tools module is already registered in Blender
    try:
        # Check if a usable mmd_tools importer is already registered.
        if 'import_model' in dir(bpy.ops.mmd_tools):
            print('System mmd_tools detected, skipping bundled mmd_tools_local')
            print('CATS will still work but uses system mmd_tools instead')
            _mmd_tools_system = True
    except Exception:
        pass


    if _mmd_tools_system:
        print('Skipping bundled mmd_tools_local registration')
    else:
        try:
            mmd_tools_local.register()
        except NameError:
            print('Could not register local mmd_tools')
        except AttributeError:
            print('Could not register local mmd_tools')
        except ValueError:
            print('mmd_tools is already registered')

    # Register all classes
    count = 0
    tools.register.order_classes()
    for cls in tools.register.__bl_classes:
        try:
            bpy.utils.register_class(cls)
            count += 1
        except ValueError:
            pass
    # print('Registered', count, 'CATS classes.')
    if count < len(tools.register.__bl_classes):
        print('Skipped', len(tools.register.__bl_classes) - count, 'CATS classes.')

    # Register Scene types
    extentions.register()


    # Load the dictionaries and check if they are found.
    globs.dict_found = tools.translate.load_translations()

    # use_international_fonts was removed in Blender 3.0+ - no longer needed
    tools.common.get_user_preferences().filepaths.use_file_compression = True


    # Disable request warning when using google translate
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


    # Apply the settings after a short time, because you can't change checkboxes during register process
    tools.settings.start_apply_settings_timer()

    print("### Loaded CATS successfully!\n")


def unregister():
    print("### Unloading CATS...")


    # Register unloaded mmd_tools tabs if they are hidden to avoid issues when unloading mmd_tools
    if not bpy.context.scene.show_mmd_tabs:
        tools.common.toggle_mmd_tabs(shutdown_plugin=True)

    # Unload mmd_tools
    if not _mmd_tools_system:
        pass
    try:
        mmd_tools_local.unregister()
    except NameError:
        print('mmd_tools was not registered')
        pass
    except AttributeError:
        print('Could not unregister local mmd_tools')
        pass
    except ValueError:
        print('mmd_tools was not registered')
        pass

    # Unload all classes in reverse order
    count = 0
    for cls in reversed(tools.register.__bl_ordered_classes):
        try:
            bpy.utils.unregister_class(cls)
            count += 1
        except ValueError:
            pass
        except RuntimeError:
            pass
    print('Unregistered', count, 'CATS classes.')


    # Remove folder from sys path
    if file_dir in sys.path:
        sys.path.remove(file_dir)

    print("### Unloaded CATS successfully!\n")


if __name__ == '__main__':
    register()



