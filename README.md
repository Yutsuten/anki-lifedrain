# anki-life-drain

This addon adds a life bar during your reviews.
Your life reduces within time, and you must answer the questions in order to recover it.

## Objective

The objective is to give the user a visual feedback of how fast the questions are being answered.
If the life is low, it means that the user is distracted or taking too much time to answer.

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

As it is written in the screenshot:

- **Maximum life**: Is the time in seconds for the life bar go from full to empty.
- **Recover**: Is the time in seconds that is recovered after answering a card.

### Pause drain during reviews

If for some reason you want to stop the drain, press `P` to toggle it!

## Inspiration

This addon was inspired on the addon [Progress Bar](https://ankiweb.net/shared/info/2091361802) and the game [osu!](https://osu.ppy.sh/).

The [Progress Bar](https://ankiweb.net/shared/info/2091361802) addon showed me that it was possible to add a bar to the review screen, and provide visual feedback through it.

[Osu!](https://osu.ppy.sh/) is a rhythm game I play, and one of its features is a life bar that reduces while playing, and to recover it you have to click the circles in the correct timing.

And then I just thought: why not to have a life bar with drain in Anki?

## Contribute

If you find any bugs, feel free to open issues. I'll try to answer / fix those whenever I can!

If you want to help even more, fell free to open a PR too!

Any feedback and help is very welcome!
