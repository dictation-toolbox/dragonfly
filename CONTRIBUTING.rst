.. _RefContributing:

Contributing
============

There are many ways to contribute to Dragonfly.  They are documented in this file.

Reporting bugs/other issues
---------------------------

If you come across bugs or other issues with Dragonfly, you can open a new
issue in the `issue tracker`_.

If the issue is a bug, make sure you describe what you expected to happen
as well as what actually happened. Include a full traceback if there was an
exception.

Submitting patches/pull requests
--------------------------------

If you have changes that can resolve an issue in the `issue tracker`_, you
can create a `pull request`_ to merge your changes with the master branch.


Documentation changes
---------------------

There are parts of Dragonfly that are undocumented as well as, undoubtedly,
documented functionality which is poorly explained, out of date or
incorrect. If you notice problems with the documentation, you can open a
new issue in the `issue tracker`_.

Dragonfly's documentation is written in the `reStructuredText format`_.
ReStructuredText is similar to the Markdown format. If you are unfamiliar
with the format, the `reStructuredText primer`_ might be a good starting
point.

The `Sphinx documentation engine`_ and `Read the Docs`_ are used to
generate documentation from the *.txt* files in the *documentation/* folder.
Docstrings in the source code are included in a semi-automatic way through
use of the `sphinx.ext.autodoc`_ extension.

To build the documentation locally, install Sphinx and any other documentation
requirements:

.. code:: shell

   $ cd documentation
   $ pip install -r requirements.txt

Then run the following command on Windows to build the documentation:

.. code:: shell

   $ make.bat html

Or use the Makefile on other systems:

.. code:: shell

   $ make html

Or, if you have the `uv <https://docs.astral.sh/uv/>`_ tool installed, you can
disregard the above commands, and simply run one of the following commands from
the *documentation/* folder:

.. code:: shell

   $ uv run --no-project --with-requirements requirements.txt -- make.bat html
   $ uv run --no-project --with-requirements requirements.txt -- make html

If there were no errors during the build process, open the
*build/html/index.html* file in a web browser. Make changes, rebuild the
documentation and reload the doc page(s) in your browser as you go.

Improving spoken language support
---------------------------------

Dragonfly supports using various languages with speech recognition engines.
Language-specific code is located in sub-packages under *dragonfly.language*
and loaded automatically when *dragonfly.language* is imported.

English is fully supported with mappings from English words to characters,
integers (e.g. for ``IntegerRef``) and time/date formats.

Other languages such as German and Dutch only have mappings for using
``IntegerRef`` (and similar) elements.


.. _RefContributingNewEngines:

Contributing New Speech Recognition Engines
-------------------------------------------

Introduction and Criteria
~~~~~~~~~~~~~~~~~~~~~~~~~

Contribution of new Dragonfly speech recognition engine implementations is
welcome, provided certain criteria are met.  New implementations must:

 * be as functional as the current engines
 * have some significant advantage over the current engines, perhaps in
   terms of accuracy, speed, CPU/memory requirements and/or platform support
 * have a willing maintainer or require little maintenance

Before setting out to implement a new Dragonfly engine, please know that
it is difficult to achieve the first criterion on functionality.
Dragonfly's feature set requires a very specific type of speech recognition
engine.  Namely, it must be one which supports each of the following
features:

 1. definition of voice commands in a grammar format
 2. efficient and dynamic activation and deactivation of (parts of) grammars
    at the beginning of an utterance
 3. in-speech transition between dictated prose (dictation mode), loaded
    voice commands (command mode) and vice versa

Each Dragonfly engine supports features one and two.  All engines support
feature three except the CMU Pocket Sphinx engine.  However, Sphinx is
only limited in that dictated prose must be spoken in separate utterances.

These three requirements have effectively ruled out Dragonfly support for
most speech recognition engines that users have asked about in the past.
This is not meant to discourage those wishing to contribute new
implementations, it is simply a fact.

As for the second and third criteria listed above, they are fairly
self-explanatory.  There is no sense in contributing a new engine that
brings nothing new to the table and this library's maintainer does not wish
to substantially increase the effort needed to keep things working.

.. _RefContributingNewEngineGuide:

New SR Engine Guide
~~~~~~~~~~~~~~~~~~~

This section is meant to help the reader get started with implementing a new
speech recognition engine backend for Dragonfly.

Implementing a custom Dragonfly engine is a complex task.  It is
recommended that you start with a copy of the text-input engine source code
and make alterations with reference to the code of other engines.  The
source code may be consulted on GitHub or via the ReadTheDocs source code
links.

The various ``EngineBase`` virtual methods should all be implemented by your
new engine sub-class.  It should also have a unique name.  You can give it
one by overriding the ``_name`` class member in your engine sub-class.

If you want to customise say, the Natlink engine, start with the code (or
classes) for that engine instead.

Once you have implemented the required engine methods and classes, you will
need to initialize and register an engine instance with the special
``register_engine_init()`` function:

.. code-block:: python

   from dragonfly.engines import register_engine_init
   my_engine = MyEngine()
   register_engine_init(my_engine)

Your engine instance will then be returned by Dragonfly's ``get_engine()``
function, when it is invoked:

.. code-block:: python

   >>> from dragonfly.engines import get_engine
   >>> get_engine()
   MyEngine()

Please note that, if you make your new engine available this way, it will
not be useable with Dragonfly's Command-line Interface (CLI).  If you would
like to use the CLI, or if you intend to submit your new engine for
inclusion in this library, you should instead modify the ``get_engine()``
function itself to retrieve and initialize your new engine.  Please see the
function's source code and documentation for how to do this.

Your engine implementation should now be useable.  If you would like to test
your implementation against Dragonfly's test suite in a clone of the Git
repo, you will need to add an entry to the special ``engine_tests_dict``
dictionary in *setup.py*, at around line 59:

.. code-block:: python

   from dragonfly.test.suites import engine_tests_dict

   # Reuse the text-input engine's test suite for your new engine.
   name = 'myengine'
   my_engine_tests = engine_tests_dict['text'][:]
   my_engine_tests.remove('test_engine_text')
   my_engine_tests.append('test_engine_' + name)  # myengine test file.
   engine_tests_dict[name] = my_engine_tests

Please be aware that engines submitted for inclusion must test successfully
against Dragonfly's test suite.  In addition, engine-specific requirements
must be *optional* extras, specified in *setup.py*.  The library must still
be functional without these requirements installed.

.. Links.
.. _Read the docs: https://readthedocs.org/
.. _Sphinx documentation engine: https://www.sphinx-doc.org/en/master/
.. _issue tracker: https://github.com/dictation-toolbox/dragonfly/issues
.. _pull request: https://github.com/dictation-toolbox/dragonfly/compare
.. _reStructuredText format: http://docutils.sourceforge.net/rst.html
.. _restructuredText primer: http://docutils.sourceforge.net/docs/user/rst/quickstart.html
.. _sphinx.ext.autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
