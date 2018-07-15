# anki-life-drain [![CodeFactor](https://www.codefactor.io/repository/github/yutsuten/anki-life-drain/badge)](https://www.codefactor.io/repository/github/yutsuten/anki-life-drain)

This addon adds a life bar during your reviews.
Your life reduces within time, and you must answer the questions in order to recover it.

## Objective

The objective is to give a visual feedback of how fast the questions are being answered.
If the life is low, it means that you are distracted or taking too much time to answer.

## Install
### Recommended way
- [AnkiWeb](https://ankiweb.net/shared/info/715575551)

### Manual
- Anki 2.0: Copy the file `lifedrain.py` (inside folder `lifedrain`) into your addons folder.
- Anki 2.1: Copy the folder `lifedrain` into your addons folder.

## Screenshot

![Review](screenshots/review_screen.png)

## Features

### Bar styling

There are many configurations to style the bar.
Access `Tools > Preferences`, then select the tab `Life Drain`, and you'll see this screen:

![Preferences](screenshots/preferences.png)

- **Position**: Choose where to show the bar: `Top` or `Bottom`.
- **Height**: The height of the bar, to make it bigger or smaller.
- **Background color**: The background color of the bar.
- **Foreground color**: The foreground color of the bar.
- **Border radius**: Adds a rounded border to the bar.
- **Style**: Allow selecting some custom style to the bar.

### Bar configuration (per deck)

The bar has 2 configurations: the `Maximum life` and `Recover`.

Select a deck, then in `Options`, select the tab `Life Drain`:

![Deck options](screenshots/deck_options.png)

Filtered deck configurations (Added in 2018-07-01):

![Custom deck options](screenshots/custom_deck_options.png)

- **Maximum life**: Is the time in seconds for the life bar go from full to empty.
- **Recover**: Is the time in seconds that is recovered after answering a card.

### Pause drain during reviews

If for some reason you want to stop the drain, press `P` to toggle it!

## Inspiration

This addon was inspired on the addon [Progress Bar](https://ankiweb.net/shared/info/2091361802) and the game [osu!](https://osu.ppy.sh/).

The [Progress Bar](https://ankiweb.net/shared/info/2091361802) addon showed me that it was possible to add a bar to the review screen, and provide visual feedback through it.

[Osu!](https://osu.ppy.sh/) is a rhythm game I play, and one of its features is a life bar that reduces while playing, and to recover it you have to click the circles in the correct timing.

And then I just thought: why not to have a life bar with drain in Anki?

## CHANGELOG
- **2018-05-20**: Initial release.
- **2018-06-10**: Fixed bugs when suspending cards while reviewing.
- **2018-07-01**: Added life drain options to filtered decks.

## Contribute

If you find any bugs, feel free to open issues. I'll try to answer / fix those as soon as I can!

If you want to help even more, fell free to open a PR too!

Any feedback and help is very welcome!
