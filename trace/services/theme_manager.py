from __future__ import annotations

from enum import Enum

import qtawesome as qta
from qtpy.QtGui import QIcon, QColor, QPalette
from qtpy.QtCore import Signal, QObject, QSettings
from qtpy.QtWidgets import QPushButton, QApplication, QStyleFactory

from config import dark_stylesheet, light_stylesheet

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
    """Theme manager for Qt applications with icon support. It manages
    both Qt palette themes and icon colors, providing a unified interface
    for light/dark mode switching with persistent settings.

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
    ) -> None:
        """
        Initialize the integrated theme manager.

        Parameters
        ----------
        app : QApplication
            The Qt application instance to manage themes for.
        parent : QObject | None, optional
            Parent QObject for memory management, by default None.

        Examples
        --------
        >>> app = QApplication(sys.argv)
        >>> theme_manager = IntegratedThemeManager(app)
        >>> theme_manager.set_theme(Theme.DARK)
        """
        super().__init__(parent)
        self.app = app
        self.current_theme = Theme.LIGHT
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
            stylesheet = dark_stylesheet.read_text()
        else:
            self.app.setPalette(self.light_palette)
            stylesheet = light_stylesheet.read_text()

        self.app.main_window.setStyleSheet(stylesheet)

        settings = QSettings()
        settings.setValue("isDarkTheme", theme == Theme.DARK)

        self.theme_changed.emit(theme)

    def toggle_theme(self) -> None:
        """
        Toggle between light and dark themes.

        Switches from light to dark or dark to light, whichever is opposite
        to the current theme.

        Examples
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

        Examples
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

        Examples
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

        Examples
        --------
        >>> colors = theme_manager.get_all_icon_colors()
        >>> primary_color = colors[IconColors.PRIMARY]
        """
        return self.dark_icon_colors.copy() if self.current_theme == Theme.DARK else self.light_icon_colors.copy()
