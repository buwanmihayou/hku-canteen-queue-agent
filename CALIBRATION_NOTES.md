# Time of day assumptions

The eight canteen profiles are provisional planning assumptions. The historical
eight-person baseline is multiplied by a continuous curve in Hong Kong time.
Lunch demand rises from 11:00, peaks at 12:00 to 12:30, declines through 13:30,
and reaches its off-peak level at 14:30. Dinner rises from 17:00, peaks at 18:00,
and returns to the off-peak level at 19:30. Midnight values agree across days.
These curves do not describe opening hours and are not live observations.

Manual or observed queue counts replace the assumed count. Waiting time remains
people multiplied by the empirical minutes-per-person rate; an observed queue
is not multiplied by the temporal demand weight again.

The synthetic tests validate interpolation, finite nonnegative results, ranking,
all daily minutes, time-window boundaries and UTC conversion. They do not prove
field calibration, photo headcount accuracy or the less-than-ten-percent target.
