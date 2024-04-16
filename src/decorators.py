# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from __future__ import annotations

from typing import Any, Callable

from .exceptions import NoDeckSelectedError


def must_be_enabled(func: Callable) -> Callable:
    """Runs the method only if the add-on is enabled."""
    def _wrapper(self: Any, *args, **kwargs) -> Any:
        config: dict[str, Any] = self.config.get()
        if not config['enable']:
            return None
        return func(self, config, *args, **kwargs)
    return _wrapper

def must_have_active_deck(func: Callable) -> Callable:
    """Runs the method only if there is a deck currently active."""
    def _wrapper(self: Any, *args, **kwargs) -> Any:
        if self._cur_deck_id is None:
            raise NoDeckSelectedError
        bar_info = self._bar_info[self._cur_deck_id]
        if not bar_info['enable']:
            return lambda: None
        return func(self, bar_info, *args, **kwargs)
    return _wrapper
