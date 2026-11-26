# ScoreGauge

The logo's idea as UI: one page per level of the exam's scale, the reading in `amber`, levels already passed in the `sea` to `mist` ramp, levels above it in `unreached`, always on an `ink` disc. The consumer provides `levels` (defaults to CEFR A1 to C2), the `reading` index, the `value` to print ("NCLC 7") and a `caption` that states the range and confidence.

- It is always an estimate: keep the label "Estimated level" (FR "Niveau estimé") and always give a caption with the range, for example "Range NCLC 6 to 7 · based on 3 simulations".
- Use one per screen, on results and the dashboard. Never animate it past the real reading.
- Up to 12 levels (NCLC); beyond that, show the exam's bands instead.
