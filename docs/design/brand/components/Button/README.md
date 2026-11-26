# Button

Use Button for actions; the consumer provides the label as children and an `onClick`. **Primary** (`accent` fill, `on-accent` label) appears at most once per view, for the thing the screen is for: "Start the simulation", "Commencer la simulation". **Secondary** (`surface`, `line-strong` border) for supporting actions. **Ghost** is a `link`-coloured text action for low-stakes moves like "See how we estimate".

- Labels start with a verb, sentence case, no full stop, no exclamation mark.
- `md` (44px, `tap-min`) everywhere touch is possible; `sm` (36px) only in dense desktop tables.
- Never white text on amber; never amber text on paper.
- Focus is a solid 2px `focus` ring with a 2px offset.
