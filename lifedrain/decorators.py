'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from .defaults import DEFAULTS


def must_be_enabled(func):
    '''
    Runs the method only if the add-on is enabled.
    '''
    def wrapper(self, *args, **kwargs):  # pylint: disable=missing-docstring
        if self.main_window.col is None or \
                self.main_window.col.conf.get('disable', DEFAULTS['disable']) is True:
            return None
        return func(self, *args, **kwargs)
    return wrapper
