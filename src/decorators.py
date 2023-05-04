# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from collections.abc import Any, Callable


def must_be_enabled(func: Callable) -> Callable:
    """Runs the method only if the add-on is enabled."""
    def _wrapper(self, *args, **kwargs) -> Any:
        try:
            config = self.config.get()
            self.deck_config.get()
        except AttributeError:
            return None

        if not config['enable']:
            return None
        return func(self, config, *args, **kwargs)

    return _wrapper
