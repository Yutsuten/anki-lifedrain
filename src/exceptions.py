# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

class LifedrainError(Exception):
    """Life Drain's base exception."""
    def __init__(self, message: str):
        super().__init__(f'Lifedrain {message}')

class GetMainWindowError(LifedrainError):
    """Failure to load Anki's main window `aqt.qt.mw`."""
    def __init__(self):
        super().__init__("failed to get Anki's main window instance.")

class GetCollectionError(LifedrainError):
    """Failure to load Anki's collection `aqt.qt.mw.col`."""
    def __init__(self):
        super().__init__("failed to get Anki's collection.")

class LoadConfigurationError(LifedrainError):
    """Failure to load configuration."""
    def __init__(self):
        super().__init__('failed to load its configuration.')

class NoDeckSelectedError(LifedrainError):
    """Failure to get currently selected deck."""
    def __init__(self):
        super().__init__('failed to update life bar because there is no currently selected deck.')
