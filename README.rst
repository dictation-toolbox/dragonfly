Dragonfly
=========

|Build Status|

Dragonfly is a speech recognition framework. It is a Python package
which offers a high-level object model and allows its users to easily
write scripts, macros, and programs which use speech recognition.

It currently supports the following speech recognition engines:

-  *Dragon NaturallySpeaking* (DNS), a product of *Nuance*
-  *Windows Speech Recognition* (WSR), included with Microsoft Windows
   Vista, Windows 7, and freely available for Windows XP
-  *CMU Pocket Sphinx* (with caveats)

Dragonfly's documentation is available online at `Read the
Docs <http://dragonfly2.readthedocs.org/en/latest/>`__. Dragonfly's FAQ
is available at
`Stackoverflow <http://stackoverflow.com/questions/tagged/python-dragonfly>`__.
Dragonfly's mailing list/discussion group is available at `Google
Groups <https://groups.google.com/forum/#!forum/dragonflyspeech>`__.

There is also a gitter channel:

|Join the chat at https://gitter.im/sphinx-dragonfly|

Installation
------------

Dragonfly is a Python package. It can be installed as *dragonfly2* using
pip:

.. code:: shell

    pip install dragonfly2

The distribution name has been changed to *dragonfly2* in order to
upload releases to PyPI.org, but everything can still be imported using
*dragonfly*.

If you have dragonfly installed under the original *dragonfly*
distribution name, you'll need to remove the old version using:

.. code:: shell

    pip uninstall dragonfly

Dragonfly can also be installed by cloning this repository or
downloading it from `the releases
page <https://github.com/Danesprite/dragonfly/releases>`__ and running
the following (or similar) command in the project's root directory:

.. code:: shell

    python setup.py install

To use the CMU Pocket Sphinx engine, see the `relevant documentation
page <http://dragonfly2.readthedocs.org/en/latest/sphinx_engine.html>`__
on it.

Features
--------

Dragonfly was written to make it very easy for Python macros, scripts,
and applications to interface with speech recognition engines. Its
design allows speech commands and grammar objects to be treated as
first-class Python objects. This allows easy and intuitive definition of
complex command grammars and greatly simplifies processing recognition
results.

| *Language object model*
| The core of Dragonfly is based on a flexible object model for handling
  speech elements and command grammars. This makes it easy to define
  complex language constructs, but also greatly simplifies retrieving
  the semantic values associated with a speech recognition.

|
| *Support for multiple speech recognition engines*
| Dragonfly's modular nature lets it use different speech recognition
  engines at the back end, while still providing a single front end
  interface to its users. This means that a program that uses Dragonfly
  can be run on any of the supported back end engines without any
  modification. Currently Dragonfly supports Dragon NaturallySpeaking
  and Windows Speech Recognition (included with Windows Vista).

|
| *Built-in action framework*
| Dragonfly contains its own powerful framework for defining and
  executing actions. It includes actions for text input and key-stroke
  simulation.

Existing command modules
------------------------

The related resources page of Dragonfly's documentation has a section on
`command
modules <http://dragonfly2.readthedocs.org/en/latest/related_resources.html#command-modules>`__
which lists various sources.

Usage example
-------------

A very simple example of Dragonfly usage is to create a static voice
command with a callback that will be called when the command is spoken.
This is done as follows:

.. code-block:: python

    from dragonfly.all import Grammar, CompoundRule

    # Voice command rule combining spoken form and recognition processing.
    class ExampleRule(CompoundRule):
        spec = "do something computer"                  # Spoken form of command.
        def _process_recognition(self, node, extras):   # Callback when command is spoken.
            print("Voice command spoken.")

    # Create a grammar which contains and loads the command rule.
    grammar = Grammar("example grammar")                # Create a grammar to contain the command rule.
    grammar.add_rule(ExampleRule())                     # Add the command rule to the grammar.
    grammar.load()                                      # Load the grammar.

The example above is very basic and doesn't show any of Dragonfly's
exciting features, such as dynamic speech elements. To learn more about
these, please take a look at `Dragonfly's online
docs <http://dragonfly2.readthedocs.org/en/latest/>`__.

Rationale behind Dragonfly
--------------------------

Dragonfly offers a powerful and unified interface to developers who want
to use speech recognition in their software. It is used for both
speech-enabling applications and for automating computer activities.

In the field of scripting and automation, there are other alternatives
available that add speech-commands to increase efficiency. Dragonfly
differs from them in that it is a powerful development platform. The
open source alternatives currently available for use with DNS are
compared to Dragonfly as follows:

-  Vocola uses its own easy-to-use scripting language, whereas Dragonfly
   uses Python and gives the macro-writer all the power available.

-  Unimacro offers a set of macros for common activities, whereas
   Dragonfly is a platform on which macro-writers can easily build new
   commands.

.. |Build Status| image:: https://travis-ci.org/Danesprite/dragonfly.svg?branch=master
   :target: https://travis-ci.org/Danesprite/dragonfly
.. |Join the chat at https://gitter.im/sphinx-dragonfly| image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/sphinx-dragonfly
