Native
------

Platforms
^^^^^^^^^
.. autoclass:: figurative.native.Figurative
   :members: linux, decree
   :noindex:

Linux
^^^^^
.. autoclass:: figurative.platforms.linux.SLinux
   :members: add_symbolic_file
   :undoc-members:


Models
^^^^^^

.. automodule:: figurative.native.models
   :members:
   :undoc-members:

State
^^^^^

.. autoclass:: figurative.native.state.State
   :members:
   :undoc-members:

Cpu
^^^

.. autoclass:: figurative.native.state.State
   :members: cpu
   :undoc-members:
   :noindex:

.. autoclass:: figurative.native.cpu.abstractcpu.Cpu
   :members:
   :undoc-members:

Memory
^^^^^^

.. autoclass:: figurative.native.state.State
   :members: mem
   :undoc-members:
   :noindex:

.. autoclass:: figurative.native.memory.SMemory
   :members:

State
^^^^^

.. autoclass:: figurative.native.state.State
   :members:
   :undoc-members:
   :noindex:

Function Models
^^^^^^^^^^^^^^^

The Figurative function modeling API can be used to override a certain
function in the target program with a custom implementation in Python.
This can greatly increase performance.

Figurative comes with implementations of function models for some common library routines (core models),
and also offers a user API for defining user-defined models.

To use a core model, use the :meth:`~figurative.native.state.State.invoke_model` API. The
available core models are documented in the API Reference::

    from figurative.native.models import strcmp
    addr_of_strcmp = 0x400510
    @m.hook(addr_of_strcmp)
    def strcmp_model(state):
        state.invoke_model(strcmp)

To implement a user-defined model, implement your model as a Python function, and pass it to
:meth:`~figurative.native.state.State.invoke_model`. See the
:meth:`~figurative.native.state.State.invoke_model` documentation for more. The
`core models <https://github.com/khulnasoft-lab/figurative/blob/master/figurative/models.py>`_
are also good examples to look at and use the same external user API.

Symbolic Input
^^^^^^^^^^^^^^

Figurative allows you to execute programs with symbolic input, which represents a range of possible inputs. You
can do this in a variety of manners.

**Wildcard byte**

Throughout these various interfaces, the '+' character is defined to designate a byte
of input as symbolic. This allows the user to make input that mixes symbolic and concrete
bytes (e.g. known file magic bytes).

For example: ``"concretedata++++++++moreconcretedata++++++++++"``

**Symbolic arguments/environment**

To provide a symbolic argument or environment variable on the command line,
use the wildcard byte where arguments and environment are specified.::

    $ figurative ./binary +++++ +++++
    $ figurative ./binary --env VAR1=+++++ --env VAR2=++++++

For API use, use the ``argv`` and ``envp`` arguments to the :meth:`figurative.native.Figurative.linux` classmethod.::

    Figurative.linux('./binary', ['++++++', '++++++'], dict(VAR1='+++++', VAR2='++++++'))

**Symbolic stdin**

Figurative by default is configured with 256 bytes of symbolic stdin data which is configurable
with the ``stdin_size`` kwarg of :meth:`figurative.native.Figurative.linux` , after an optional
concrete data prefix, which can be provided with the ``concrete_start`` kwarg of
:meth:`figurative.native.Figurative.linux`.

**Symbolic file input**

To provide symbolic input from a file, first create the files that will be opened by the
analyzed program, and fill them with wildcard bytes where you would like symbolic data
to be.

For command line use, invoke Figurative with the ``--file`` argument.::

    $ figurative ./binary --file my_symbolic_file1.txt --file my_symbolic_file2.txt

For API use, use the :meth:`~figurative.platforms.linux.SLinux.add_symbolic_file` interface to customize the initial
execution state from an :meth:`~figurative.core.figurative.FigurativeBase.__init__`

.. code-block:: Python

    @m.init
    def init(initial_state):
        initial_state.platform.add_symbolic_file('my_symbolic_file1.txt')

**Symbolic sockets**

Figurative's socket support is experimental! Sockets are configured to contain 64 bytes of
symbolic input.
