from __future__ import annotations

from enum import Enum

import qtawesome as qta
from qtpy.QtGui import QIcon, QColor, QPalette
from qtpy.QtCore import Signal, QObject, QSettings
from qtpy.QtWidgets import QPushButton, QApplication, QStyleFactory

type ColorHex = str
type IconColorDict = dict[str, ColorHex]
type ButtonIconInfo = tuple[str, QPushButton, str, str]


class Theme(Enum):
    """Theme enumeration for light and dark modes."""

    LIGHT = "light"
    DARK = "dark"


class IconColors:
    """Constants for icon color types."""

    PRIMARY: str = "primary"
    SECONDARY: str = "secondary"
    ACCENT: str = "accent"
    SUCCESS: str = "success"
    WARNING: str = "warning"
    ERROR: str = "error"
    DISABLED: str = "disabled"


class ThemeManager(QObject):
    """
    theme manager for Qt applications with icon support.

    Manages both Qt palette themes and icon colors, providing a unified
    interface for light/dark mode switching with persistent settings.

    Attributes
    ----------
    theme_changed : Signal
        Signal emitted when theme changes, passes Theme enum value.
    current_theme : Theme
        Currently active theme.
    app : QApplication
        Qt application instance.
    light_palette : QPalette
        Palette configuration for light theme.
    dark_palette : QPalette
        Palette configuration for dark theme.
    light_icon_colors : IconColorDict
        Icon color mapping for light theme.
    dark_icon_colors : IconColorDict
        Icon color mapping for dark theme.
    """

    theme_changed = Signal(Theme)

    def __init__(
        self,
        app: QApplication,
        parent: QObject | None = None,
        light_stylesheet_path: str | None = None,
        dark_stylesheet_path: str | None = None,
    ) -> None:
        """
        Initialize the integrated theme manager.

        Parameters
        ----------
        app : QApplication
            The Qt application instance to manage themes for.
        parent : QObject | None, optional
            Parent QObject for memory management, by default None.
        light_stylesheet_path : str | None, optional
            Path to the light theme QSS stylesheet file, by default None.
        dark_stylesheet_path : str | None, optional
            Path to the dark theme QSS stylesheet file, by default None.

        Example
        --------
        >>> app = QApplication(sys.argv)
        >>> theme_manager = IntegratedThemeManager(app)
        >>> theme_manager.set_theme(Theme.DARK)
        """
        super().__init__(parent)
        self.app = app
        self.current_theme = Theme.LIGHT

        self.light_stylesheet_path = light_stylesheet_path
        self.dark_stylesheet_path = dark_stylesheet_path

        self.app.setStyle(QStyleFactory.create("Fusion"))

        self._setup_palettes()
        self._setup_icon_colors()

        # Load saved theme preference
        settings = QSettings()
        is_dark = settings.value("isDarkTheme", False, bool)
        self.set_theme(Theme.DARK if is_dark else Theme.LIGHT)

    def _setup_palettes(self) -> None:
        """
        Setup Qt palettes for light and dark themes.

        Creates and configures QPalette objects with appropriate colors
        for both light and dark themes, including disabled state colors.
        """
        # Light palette
        self.light_palette = QPalette()
        self.light_palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        self.light_palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        self.light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        self.light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 233, 233))
        self.light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        self.light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        self.light_palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        self.light_palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        self.light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        self.light_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        self.light_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        self.light_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        self.light_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        # Dark palette
        self.dark_palette = QPalette()
        self.dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        self.dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
        self.dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        self.dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        self.dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        self.dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        self.dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

        # Disabled colors for both palettes
        disabled_light_color = QColor(120, 120, 120)
        self.light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_light_color)
        self.light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_light_color)
        self.light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_light_color)

        disabled_dark_color = QColor(120, 120, 120)
        self.dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_dark_color)
        self.dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_dark_color)
        self.dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_dark_color)

    def _setup_icon_colors(self) -> None:
        """
        Setup icon color schemes for light and dark themes.

        Defines color mappings for different icon types (primary, secondary, etc.)
        optimized for visibility and accessibility in both light and dark themes.
        """
        self.light_icon_colors: IconColorDict = {
            IconColors.PRIMARY: "#000000",  # Black for primary icons
            IconColors.SECONDARY: "#666666",  # Dark gray for secondary icons
            IconColors.ACCENT: "#0078d4",  # Blue for accent colors
            IconColors.SUCCESS: "#107c10",  # Green for success
            IconColors.WARNING: "#ff8c00",  # Orange for warnings
            IconColors.ERROR: "#d13438",  # Red for errors
            IconColors.DISABLED: "#999999",  # Light gray for disabled
        }

        self.dark_icon_colors: IconColorDict = {
            IconColors.PRIMARY: "#ffffff",  # White for primary icons
            IconColors.SECONDARY: "#cccccc",  # Light gray for secondary icons
            IconColors.ACCENT: "#0078d4",  # Blue for accent colors
            IconColors.SUCCESS: "#107c10",  # Green for success
            IconColors.WARNING: "#ff8c00",  # Orange for warnings
            IconColors.ERROR: "#d13438",  # Red for errors
            IconColors.DISABLED: "#666666",  # Dark gray for disabled
        }

    def _load_stylesheet(self, stylesheet_path: str | None) -> str:
        """
        Load a QSS stylesheet from file.

        Parameters
        ----------
        stylesheet_path : str | None
            Path to the QSS stylesheet file, or None to return empty string.

        Returns
        -------
        str
            The stylesheet content, or empty string if file cannot be loaded.

        Examples
        --------
        >>> stylesheet = theme_manager._load_stylesheet("styles/dark.qss")
        """
        if not stylesheet_path:
            return ""

        try:
            with open(stylesheet_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            print(f"Warning: Stylesheet file not found: {stylesheet_path}")
            return ""
        except UnicodeDecodeError:
            print(f"Warning: Could not decode stylesheet file: {stylesheet_path}")
            try:
                # Try with different encoding
                with open(stylesheet_path, "r", encoding="latin-1") as file:
                    return file.read()
            except Exception as e:
                print(f"Warning: Failed to load stylesheet {stylesheet_path}: {e}")
                return ""
        except Exception as e:
            print(f"Warning: Failed to load stylesheet {stylesheet_path}: {e}")
            return ""

    def set_theme(self, theme: Theme) -> None:
        """
        Set the application theme.

        Parameters
        ----------
        theme : Theme
            The theme to apply (Theme.LIGHT or Theme.DARK).

        Examples
        --------
        >>> theme_manager.set_theme(Theme.DARK)
        >>> theme_manager.set_theme(Theme.LIGHT)
        """
        self.current_theme = theme

        if theme == Theme.DARK:
            self.app.setPalette(self.dark_palette)
            stylesheet = self._load_stylesheet(self.dark_stylesheet_path)
        else:
            self.app.setPalette(self.light_palette)
            stylesheet = self._load_stylesheet(self.light_stylesheet_path)

        self.app.setStyleSheet(stylesheet)

        settings = QSettings()
        settings.setValue("isDarkTheme", theme == Theme.DARK)

        self.theme_changed.emit(theme)

    def toggle_theme(self) -> None:
        """
        Toggle between light and dark themes.

        Switches from light to dark or dark to light, whichever is opposite
        to the current theme.

        Example
        --------
        >>> theme_manager.toggle_theme()  # Switches to opposite theme
        """
        new_theme = Theme.DARK if self.current_theme == Theme.LIGHT else Theme.LIGHT
        self.set_theme(new_theme)

    def get_current_theme(self) -> Theme:
        """
        Get the current theme.

        Returns
        -------
        Theme
            The currently active theme.
        """
        return self.current_theme

    def get_icon_color(self, color_type: str = IconColors.PRIMARY) -> ColorHex:
        """
        Get icon color for the current theme.

        Parameters
        ----------
        color_type : str, optional
            The type of icon color to retrieve, by default IconColors.PRIMARY.
            Must be one of the IconColors constants.

        Returns
        -------
        ColorHex
            Hex color string (e.g., '#ffffff') appropriate for the current theme.

        Example
        --------
        >>> color = theme_manager.get_icon_color(IconColors.PRIMARY)
        >>> warning_color = theme_manager.get_icon_color(IconColors.WARNING)
        """
        colors = self.dark_icon_colors if self.current_theme == Theme.DARK else self.light_icon_colors
        return colors.get(color_type, colors[IconColors.PRIMARY])

    def create_icon(
        self,
        icon_name: str,
        color_type: str = IconColors.PRIMARY,
        scale_factor: float = 1.0,
        custom_color: ColorHex | None = None,
    ) -> QIcon | None:
        """
        Create a themed icon using qtawesome.

        Parameters
        ----------
        icon_name : str
            The qtawesome icon name (e.g., 'fa.home', 'mdi.gear').
        color_type : str, optional
            The type of icon color to use, by default IconColors.PRIMARY.
        scale_factor : float, optional
            Scale factor for icon size, by default 1.0.
        custom_color : ColorHex | None, optional
            Custom hex color to override theme color, by default None.

        Returns
        -------
        QIcon | None
            The created icon, or None if qtawesome is not available.

        Example
        --------
        >>> icon = theme_manager.create_icon('fa.home')
        >>> warning_icon = theme_manager.create_icon('fa.exclamation-triangle', IconColors.WARNING)
        >>> custom_icon = theme_manager.create_icon('fa.gear', custom_color='#ff0000')
        """
        color = custom_color or self.get_icon_color(color_type)
        return qta.icon(icon_name, color=color, scale_factor=scale_factor)

    def get_all_icon_colors(self) -> IconColorDict:
        """
        Get all available icon colors for the current theme.

        Returns
        -------
        IconColorDict
            Dictionary mapping color type names to hex color strings.

        Example
        --------
        >>> colors = theme_manager.get_all_icon_colors()
        >>> primary_color = colors[IconColors.PRIMARY]
        """
        return self.dark_icon_colors.copy() if self.current_theme == Theme.DARK else self.light_icon_colors.copy()

    def set_stylesheet_paths(self, light_path: str | None = None, dark_path: str | None = None) -> None:
        """
        Update the stylesheet paths and reapply current theme.

        Parameters
        ----------
        light_path : str | None, optional
            Path to the light theme QSS file, by default None.
        dark_path : str | None, optional
            Path to the dark theme QSS file, by default None.

        Examples
        --------
        >>> theme_manager.set_stylesheet_paths(
        ...     light_path="new_styles/light.qss",
        ...     dark_path="new_styles/dark.qss"
        ... )
        """
        if light_path is not None:
            self.light_stylesheet_path = light_path
        if dark_path is not None:
            self.dark_stylesheet_path = dark_path

        # Reapply current theme to load new stylesheets
        current = self.current_theme
        self.set_theme(current)

    def get_stylesheet_paths(self) -> tuple[str | None, str | None]:
        """
        Get the current stylesheet paths.

        Returns
        -------
        tuple[str | None, str | None]
            Tuple of (light_stylesheet_path, dark_stylesheet_path).

        Examples
        --------
        >>> light_path, dark_path = theme_manager.get_stylesheet_paths()
        """
        return (self.light_stylesheet_path, self.dark_stylesheet_path)
