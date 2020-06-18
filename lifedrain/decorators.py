"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from .defaults import DEFAULTS


def must_be_enabled(func):
    """Runs the method only if the add-on is enabled."""
    def _wrapper(self, *args, **kwargs):
        col = self.main_window.col
        if col is None:
            return None

        global_conf = col.conf.get('lifedrain')
        if global_conf is None:
            if col.conf.get('disable', not DEFAULTS['enable']):
                return None
        elif not global_conf['enable']:
            return None

        return func(self, *args, **kwargs)

    return _wrapper
