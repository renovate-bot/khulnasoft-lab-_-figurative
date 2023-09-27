#!/usr/bin/env python

import sys
from figurative.native import Figurative

# This example demonstrates loading a simple binary in Figurative,
# running it to completion without any callbacks or instrumentation
# and producing basic information about the paths explored


if __name__ == "__main__":
    path = sys.argv[1]
    # Create a new Figurative object
    m = Figurative(path)
    m.run()
