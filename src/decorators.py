"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""


def must_be_enabled(func):
    """Runs the method only if the add-on is enabled."""
    def _wrapper(self, *args, **kwargs):
        try:
            config = self.config.get()
        except AttributeError:
            return None

        if not config['enable']:
            return None
        return func(self, *args, **kwargs)

    return _wrapper
