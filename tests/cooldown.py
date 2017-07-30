# Crude testing file, intended to be run from CLI at repository root
from datetime import datetime
import dateutil.parser

from glados.cooldown import *

timepoints = list(map(dateutil.parser.parse, [
    "2017-01-01T00:00:00.0000",
    "2017-01-01T00:00:01.0000",
    "2017-01-01T00:00:02.0000",
    "2017-01-01T00:00:03.0000",
    "2017-01-01T00:00:04.0000",
    "2017-01-01T00:00:05.0000",
    "2017-01-01T00:00:06.0000",
    "2017-01-01T00:00:07.0000",

    "2017-01-01T01:00:00.0000",
    "2017-01-01T01:00:01.0000",
    "2017-01-01T01:00:02.0000",
    "2017-01-01T01:00:03.0000",
    "2017-01-01T01:00:04.0000",
    "2017-01-01T01:00:05.0000",
    "2017-01-01T01:00:06.0000",
    "2017-01-01T01:00:07.0000"
]))

tracker = Tracker()
tracker.stamp = tracker.last_stamp = timepoints[0]

for t in timepoints:
    result = tracker.update(now=t)
    print(result, tracker)
