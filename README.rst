Dragonfly
=========

|Build Status|
|Docs Status|
|Join Gitter chat|
|Join Matrix chat|

.. contents:: Contents

Introduction
----------------------------------------------------------------------------

Dragonfly is a speech recognition framework for Python that makes it
convenient to create custom commands to use with speech recognition
software. It was written to make it very easy for Python macros, scripts,
and applications to interface with speech recognition engines. Its design
allows speech commands and grammar objects to be treated as first-class
Python objects.

Dragonfly can be used for general programming by voice. It is flexible
enough to allow programming in any language, not just Python. It can also be
used for speech-enabling applications, automating computer activities
and dictating prose.

Dragonfly contains its own powerful framework for defining and executing
actions. It includes actions for text input and key-stroke simulation. This
framework is cross-platform, working on Windows, macOS and Linux (X11 only).
See the `actions sub-package documentation
<https://dragonfly2.readthedocs.io/en/latest/actions.html>`__
for more information, including code examples.

This project is a fork of the original
`t4ngo/dragonfly <https://github.com/t4ngo/dragonfly>`__ project.

Dragonfly currently supports the following speech recognition engines:

-  *Dragon*, a product of *Nuance*. All versions up to 15 (the latest)
   should be supported. *Home*, *Professional Individual* and previous
   similar editions of *Dragon* are supported. Other editions may work too
-  *Windows Speech Recognition* (WSR), included with Microsoft Windows
   Vista, Windows 7+, and freely available for Windows XP
-  *Kaldi* (under development)
-  *CMU Pocket Sphinx* (with caveats)

Documentation and FAQ
----------------------------------------------------------------------------

Dragonfly's documentation is available online at `Read the
Docs <http://dragonfly2.readthedocs.org/en/latest/>`__. The changes in
each release are listed in the project's `changelog
<https://github.com/dictation-toolbox/dragonfly/blob/master/CHANGELOG.rst>`__.
Dragonfly's FAQ is available in the documentation `here
<https://dragonfly2.readthedocs.io/en/latest/faq.html>`__.
There are also a number of Dragonfly-related questions on `Stackoverflow
<http://stackoverflow.com/questions/tagged/python-dragonfly>`_, although
many of them are related to issues resolved in the latest version of
Dragonfly.

CompoundRule Usage example
----------------------------------------------------------------------------

A very simple example of Dragonfly usage is to create a static voice
command with a callback that will be called when the command is spoken.
This is done as follows:

..  code-block:: python

    from dragonfly import Grammar, CompoundRule

    # Voice command rule combining spoken form and recognition processing.
    class ExampleRule(CompoundRule):
        spec = "do something computer"                  # Spoken form of command.
        def _process_recognition(self, node, extras):   # Callback when command is spoken.
            print("Voice command spoken.")

    # Create a grammar which contains and loads the command rule.
    grammar = Grammar("example grammar")                # Create a grammar to contain the command rule.
    grammar.add_rule(ExampleRule())                     # Add the command rule to the grammar.
    grammar.load()                                      # Load the grammar.

To use this example, save it in a command module in your module loader
directory or Natlink user directory, load it and then say *do something
computer*. If the speech recognition engine recognized the command, then
``Voice command spoken.`` will be printed in the Natlink messages window.
If you're not using Dragon, then it will be printed into the console window.

MappingRule usage example
----------------------------------------------------------------------------

A more common use of Dragonfly is the ``MappingRule`` class, which allows
defining multiple voice commands. The following example is a simple grammar
to be used when Notepad is the foreground window:

..  code-block:: python

    from dragonfly import (Grammar, AppContext, MappingRule, Dictation,
                           Key, Text)

    # Voice command rule combining spoken forms and action execution.
    class NotepadRule(MappingRule):
        # Define the commands and the actions they execute.
        mapping = {
            "save [file]":            Key("c-s"),
            "save [file] as":         Key("a-f, a/20"),
            "save [file] as <text>":  Key("a-f, a/20") + Text("%(text)s"),
            "find <text>":            Key("c-f/20") + Text("%(text)s\n"),
        }

        # Define the extras list of Dragonfly elements which are available
        # to be used in mapping specs and actions.
        extras = [
            Dictation("text")
        ]


    # Create the grammar and the context under which it'll be active.
    context = AppContext(executable="notepad")
    grammar = Grammar("Notepad example", context=context)

    # Add the command rule to the grammar and load it.
    grammar.add_rule(NotepadRule())
    grammar.load()

To use this example, save it in a command module in your module loader
directory or Natlink user directory, load it, open a Notepad window and then
say one of mapping commands. For example, saying *save* or *save file* will
cause the control and S keys to be pressed.

The example aboves don't show any of Dragonfly's exciting features, such as
dynamic speech elements. To learn more about these, please take a look at
`Dragonfly's online docs <http://dragonfly2.readthedocs.org/en/latest/>`__.

Installation
----------------------------------------------------------------------------

Dragonfly is a Python package. It can be installed as *dragonfly2* using
pip:

.. code:: shell

    pip install dragonfly2

The distribution name has been changed to *dragonfly2* in order to
upload releases to PyPI.org, but everything can still be imported using
*dragonfly*. If you use any grammar modules that include something like
:code:`pkg_resources.require("dragonfly >= 0.6.5")`, you will need to either
replace :code:`dragonfly` with :code:`dragonfly2` or remove lines like this
altogether.

If you are installing this on Linux, you will also need to install the
`xdotool <https://www.semicomplete.com/projects/xdotool/>`__ program for the
``Key`` and ``Text`` actions to work. Please note that Dragonfly is only
fully functional in an X11 session. Input action classes, application
contexts and the ``Window`` class will **not** be functional under Wayland.
It is recommended that Wayland users switch to X11.

If you have dragonfly installed under the original *dragonfly*
distribution name, you'll need to remove the old version using:

.. code:: shell

    pip uninstall dragonfly

Dragonfly can also be installed by cloning this repository or
downloading it from `the releases
page <https://github.com/dictation-toolbox/dragonfly/releases>`__ and
running the following (or similar) command in the project's root
directory:

.. code:: shell

    python setup.py install

To use the CMU Pocket Sphinx engine, see the `relevant documentation
page <http://dragonfly2.readthedocs.org/en/latest/sphinx_engine.html>`__
on it.

If pip fails to install *dragonfly2* or any of its required or extra
dependencies, then you may need to upgrade pip with the following command:

.. code:: shell

    pip install --upgrade pip

Existing command modules
----------------------------------------------------------------------------

The related resources page of Dragonfly's documentation has a section on
`command
modules <http://dragonfly2.readthedocs.org/en/latest/related_resources.html#command-modules>`__
which lists various sources.

.. |Build Status| image:: https://travis-ci.org/dictation-toolbox/dragonfly.svg?branch=master
   :target: https://travis-ci.org/dictation-toolbox/dragonfly
.. |Docs Status| image:: https://readthedocs.org/projects/dragonfly2/badge/?version=latest&style=flat
   :target: https://dragonfly2.readthedocs.io
.. |Join Gitter chat| image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/dictation-toolbox/dragonfly
.. |Join Matrix chat| image:: https://img.shields.io/matrix/dragonfly2:matrix.org.svg?label=%5Bmatrix%5D
   :target: https://riot.im/app/#/room/#dragonfly2:matrix.org
