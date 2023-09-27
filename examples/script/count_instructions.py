#!/usr/bin/env python

import sys
from figurative.native import Figurative

"""
Count the number of emulated instructions.

This example uses the context property of the Figurative object to store data
that's updated by the hook function. Figurative.context is needed to properly
share data when running with multiple worker processes.
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write(f"Usage: {sys.argv[0]} [binary]\n")
        sys.exit(2)

    m = Figurative(sys.argv[1])
    with m.locked_context() as context:
        context["count"] = 0

    @m.hook(None)
    def explore(state):
        with m.locked_context() as context:
            context["count"] += 1

    m.run()

    print(f"Executed {m.context['count']} instructions.")
