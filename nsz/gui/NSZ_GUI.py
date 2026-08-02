from nsz.gui.GuiPath import getGuiPath
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import platform
from nsz.gui.ShaderWidget import ShaderWidget
from nsz.gui.RootWidget import RootWidget
from nsz.gui.GameList import GameList
from kivy.uix.settings import SettingsWithTabbedPanel
from kivy.logger import Logger
from nsz.gui.SettingScrollOptions import SettingScrollOptions
from nsz.nut import Print
from pathlib import Path
import logging
import sys
import subprocess
import ctypes

def apply_dpi_scaling(config):
    enable = int(config.get("DPI", "dpi_enable"))
    auto = int(config.get("DPI", "dpi_auto"))
    scale = float(config.get("DPI", "dpi_scale"))

    if not enable:
        return

    if auto:
        if sys.platform.startswith("linux"):
            try:
                out = subprocess.check_output(["xdpyinfo"]).decode()
                for line in out.splitlines():
                    if "resolution:" in line:
                        dpi = int(line.split()[1].split("x")[0])
                        scale = dpi / 96.0
            except Exception:
                pass

        elif sys.platform == "win32":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
                dpi = ctypes.windll.user32.GetDpiForSystem()
                scale = dpi / 96.0
            except Exception:
                pass

    Config.set("graphics", "display_scale", str(scale))

try:
    from nsz.version import GUI_VERSION as GUI_TITLE_VERSION
except Exception:
    GUI_TITLE_VERSION = "unknown version"


def patchKivyOpenGlExtensionDecode():
    try:
        from kivy.graphics import opengl_utils
        from kivy.graphics.opengl import GL_EXTENSIONS, glGetString
    except Exception:
        return

    if getattr(opengl_utils, "_nsz_safe_gl_extensions_patch", False):
        return

    originalGlGetExtensions = opengl_utils.gl_get_extensions

    def safeGlGetExtensions(*args, **kwargs):
        try:
            return originalGlGetExtensions(*args, **kwargs)
        except UnicodeDecodeError as e:
            try:
                rawExtensions = glGetString(GL_EXTENSIONS)
            except Exception:
                rawExtensions = None

            if isinstance(rawExtensions, bytes):
                parsedExtensions = rawExtensions.decode(
                    "utf-8", errors="replace"
                ).split()
            elif rawExtensions:
                parsedExtensions = str(rawExtensions).split()
            else:
                parsedExtensions = []

            Logger.warning(
                "NSZ GUI: Non-UTF8 OpenGL extension list encountered; "
                "continuing with sanitized extension names. (%s)",
                e,
            )
            return parsedExtensions

    opengl_utils.gl_get_extensions = safeGlGetExtensions
    opengl_utils._nsz_safe_gl_extensions_patch = True


def launchGui():
    kivyConfigPathObj = Path.home().joinpath(".kivy").joinpath("config.ini")
    if kivyConfigPathObj.exists():
        kivyConfigPath = str(kivyConfigPathObj)
        with open(kivyConfigPath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        brokenKivyConfig = False
        for i, line in enumerate(lines):
            if line.startswith("default_font") and "MPLUS1p-Medium.ttf" in line:
                brokenKivyConfig = True
                lines[i] = (
                    "default_font = ['Roboto', 'data/fonts/Roboto-Regular.ttf', 'data/fonts/Roboto-Italic.ttf', 'data/fonts/Roboto-Bold.ttf', 'data/fonts/Roboto-BoldItalic.ttf']\n"
                )
        if brokenKivyConfig:
            Print.info(f"Fixing {kivyConfigPath}", "INFO")
            with open(kivyConfigPath, "w", encoding="utf-8") as f:
                f.writelines(lines)
    return GUI().run()


class GUI(App):
    rootWidget = None

    def run(self):
        patchKivyOpenGlExtensionDecode()
        LabelBase.register(DEFAULT_FONT, getGuiPath("fonts/MPLUS1p-Medium.ttf"))
        super(GUI, self).run()
        Window.close()
        if not self.rootWidget.hardExit:
            return arguments(self.config, self.rootWidget)
        else:
            return None

    def build(self):
        apply_dpi_scaling(self.config)
        realLevel = Logger.level
        # To hide the wrongly appearance of "[WARNING] Both Window.minimum_width
        # and Window.minimum_height must be bigger than 0 for the size restriction
        # to take effect." caused by checking if booth variables are set after setting
        # one of them without offering any way of setting booth at the same time
        Logger.setLevel(logging.ERROR)
        Window.minimum_width = 800
        Window.minimum_height = 600
        Logger.setLevel(realLevel)
        Builder.load_file(getGuiPath("layout/GUI.kv"))
        self.title = f"NSZ GUI {GUI_TITLE_VERSION}"
        self.icon = getGuiPath("nsZip.png")
        root = FloatLayout()
        with open(getGuiPath("shaders/plasma.shader")) as stream:
            plasma_shader = stream.read()
            root.add_widget(ShaderWidget(fs=plasma_shader))
        gameList = GameList()
        self.rootWidget = RootWidget(gameList)
        root.add_widget(self.rootWidget)
        self.settings_cls = MySettingsWithTabbedPanel
        return root

    def on_start(self, *args):
        if platform == "win" and int(self.config.get("Tools", "kivy_topmost")) == 1:
            import nsz.gui.KivyOnTop

            nsz.gui.KivyOnTop.register_topmost(Window, self.title)

    def build_config(self, config):
        config.setdefaults(
            "Settings",
            {
                "level": "[Lv. 18] Great (default)",
                "block": 0,
                "solid": 0,
                "bs": "1 MB (default)",
                "verify_options": "Quick (NCA hashes)",
                "keep": 0,
            },
        )
        config.setdefaults(
            "Advanced",
            {
                "threads": -1,
                "multi": 4,
                "fixPadding": 0,
                "ldm": 0,
                "parseCnmt": 0,
                "overwrite": 0,
                "rm_old_version": 0,
                "rm_source": 0,
            },
        )
        config.setdefaults(
            "Tools",
            {
                "depth": 1,
                "extractregex": "",
                "kivy_topmost": 1,
            },
        )
        config.setdefaults(
            "DPI",
            {
                "dpi_enable": 1,
                "dpi_scale": 1.0,
                "dpi_auto": 1,
            },
        )


    def build_settings(self, settings):
        settings.register_type("scrolloptions", SettingScrollOptions)
        settings.add_json_panel(
            "Settings", self.config, getGuiPath("json/settings_basic.json")
        )
        settings.add_json_panel(
            "Advanced", self.config, getGuiPath("json/settings_advanced.json")
        )
        settings.add_json_panel(
            "Tools", self.config, getGuiPath("json/settings_tools.json")
        )
        settings.add_json_panel(
            "DPI", self.config, getGuiPath("json/settings_dpi.json")
        )

    def on_config_change(self, config, section, key, value):
        Logger.info(
            "main.py: App.on_config_change: {0}, {1}, {2}, {3}".format(
                config, section, key, value
            )
        )

    def close_settings(self, settings=None):
        Logger.info("main.py: App.close_settings: {0}".format(settings))
        super(GUI, self).close_settings(settings)


class MySettingsWithTabbedPanel(SettingsWithTabbedPanel):
    def on_close(self):
        Logger.info("main.py: MySettingsWithTabbedPanel.on_close")

    def on_config_change(self, config, section, key, value):
        Logger.info(
            "main.py: MySettingsWithTabbedPanel.on_config_change: "
            "{0}, {1}, {2}, {3}".format(config, section, key, value)
        )


class arguments:
    def __init__(self, config, rootWidget):
        level_scrolloptions = {
            "[Lv. 01] Debugging": 0,
            "[Lv. 08] Faster": 8,
            "[Lv. 12] Fast": 12,
            "[Lv. 14] Normal": 14,
            "[Lv. 18] Great (default)": 18,
            "[Lv. 22] Ultra (recommended)": 22,
        }
        bs_scrolloptions = {
            "64 KB": 16,
            "128 KB": 17,
            "256 KB": 18,
            "512 KB": 19,
            "1 MB (default)": 20,
            "2 MB": 21,
            "4 MB": 22,
            "8 MB": 23,
            "16 MB": 24,
        }
        self.file = rootWidget.gameList.filelist
        self.C = True if rootWidget.C is True else None
        self.D = True if rootWidget.D is True else None
        self.output = rootWidget.output
        self.info = True if rootWidget.info is True else None
        self.titlekeys = True if rootWidget.titlekeys is True else None
        self.extract = True if rootWidget.extract is True else None
        self.create = True if rootWidget.create is True else None
        self.level = level_scrolloptions.get(config.get("Settings", "level"), 18)
        self.block = True if int(config.get("Settings", "block")) == 1 else None
        self.solid = True if int(config.get("Settings", "solid")) == 1 else None
        self.bs = bs_scrolloptions.get(config.get("Settings", "bs"), 20)
        if rootWidget.verify is True or (
            (rootWidget.C is True or rootWidget.D is True)
            and config.get("Settings", "verify_options") == "Full (NCA & PFS0 hashes)"
        ):
            self.verify = True
        else:
            self.verify = None
        if (rootWidget.C is True or rootWidget.D is True) and config.get(
            "Settings", "verify_options"
        ) == "Quick (NCA hashes)":
            self.quick_verify = True
        else:
            self.quick_verify = None
        self.keep = True if int(config.get("Settings", "keep")) == 1 else False
        self.threads = int(config.get("Advanced", "threads"))
        self.multi = int(config.get("Advanced", "multi"))
        self.fix_padding = (
            True if int(config.get("Advanced", "fixPadding")) == 1 else False
        )
        self.long = True if int(config.get("Advanced", "ldm")) == 1 else False
        self.parseCnmt = True if int(config.get("Advanced", "parseCnmt")) == 1 else None
        self.overwrite = True if int(config.get("Advanced", "overwrite")) == 1 else None
        self.rm_old_version = (
            True if int(config.get("Advanced", "rm_old_version")) == 1 else None
        )
        self.rm_source = True if int(config.get("Advanced", "rm_source")) == 1 else None
        self.depth = int(config.get("Tools", "depth"))
        self.extractregex = str(config.get("Tools", "extractregex"))
        self.alwaysParseCnmt = False
        self.undupe = None
        self.undupe_dryrun = None
        self.undupe_prioritylist = ""
        self.undupe_whitelist = ""
        self.undupe_old_versions = False
        self.keys = None


if __name__ == "__main__":
    GUI().run()
