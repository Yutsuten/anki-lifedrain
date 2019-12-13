"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from .defaults import DEFAULTS


def must_be_enabled(func):
    """Runs the method only if the add-on is enabled."""
    def _wrapper(self, *args, **kwargs):
        col = self.main_window.col
        if col is None or col.conf.get('disable', DEFAULTS['disable']) is True:
            return None
        return func(self, *args, **kwargs)

    return _wrapper
