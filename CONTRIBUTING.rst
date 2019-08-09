Contributing
============

There are many ways to contribute to dragonfly and the project would
certainly benefit from more contributions.

Reporting bugs/other issues
---------------------------

If you come across bugs or other issues with dragonfly, you can open a new
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

There are parts of dragonfly that are undocumented as well as, undoubtedly,
documented functionality which is poorly explained, out of date or
incorrect. If you notice problems with the documentation, you can open a
new issue in the `issue tracker`_.

Dragonfly's documentation is written in the `reStructuredText format`_.
ReStructuredText is similar to the Markdown format. If you are unfamiliar
with the format, the `reStructuredText primer`_ might be a good starting
point.

The `Sphinx documentation engine`_ and `Read the Docs`_ are used to
generate documentation from the *.txt* files in *documentation/* and from
docstrings in dragonfly's source code.

To build the documentation locally, install Sphinx and the documentation
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


Additional SR engine backends
-----------------------------

Dragonfly supports using various speech recognition engines: Dragon
NaturallySpeaking (DNS), Windows Speech Recognition (WSR) and CMU Pocket
Sphinx.

Adding an additional engine backend is a significant undertaking. Engine
implementations should be placed in a sub-package of *dragonfly.engines*,
e.g. *backend_natlink*. The engine's sub-package should define an engine
class implementing the ``EngineBase`` class and a ``get_engine`` function
to be used in the *dragonfly/engines/__init__.py* file.

Examining the source code under *dragonfly/engines/backend_text/* may be a
good place to start, as it is currently the simplest engine implementation.

Implementations should define and use sub-classes of the
``DictationContainer``, ``RecObsManagerBase`` and ``TimerManagerBase`` base
classes from *dragonfly.engines.base*. These are for dictation result
containers, managing recognition observers and managing multiplexing timers
respectively.

A compiler class to translate dragonfly grammars into a format that the SR
engine accepts will probably also be required. Engine backends other than
the "text" engine have compiler classes to look at as examples.

If there are additional engine dependencies, they should be placed into the
*setup.py* file in the ``extras_require`` dictionary. For example:

..  code:: python

    extras_require={
        ...,
        "EngineX": ["engine_dependency >= X.Y.Z"],
    },

This allows the engine's dependencies to be installed using something like:

.. code:: shell

   $ pip install dragonfly2[EngineX]

In addition to the engine implementation, each engine should define its own
test suite in the *dragonfly/test/suites.py* file. For example:

..  code:: python

    # Define test files to run for the new engine, including common ones.
    x_names = [
        # Assume that "test_engine_x.py" exists. Including the '.py' file
        # extension is not necessary.
        "test_engine_x",

        # Include the tests for English integer content.
        "test_language_en_number",
    ] + common_names

    # Exclude one or more common names if the new engine doesn't [yet]
    # support certain dragonfly functionality. Also display a warning.
    x_names.remove("test_timer")
    _log.warning("Excluding 'test_timer' for engine X because multiplexing "
                 "timers are not supported (yet).")

    # Build a test suite for the engine.
    x_suite = build_suite(EngineTestSuite("<engine_name>"), x_names)

The test suite should be runnable using the following (or similar) command:

.. code:: shell

   $ python setup.py test --test-suite=dragonfly.test.suites.x_suite

The *suites.py* file should be able to build each engine's test suite
**without** engine-specific dependencies being available, such as
*natlink*. You should be able to test this by running the default test
suite `in a virtual environment <https://virtualenv.pypa.io/en/latest/>`__:

.. code:: shell

   $ python setup.py test

The above command should run successfully for Python versions 2.7 and 3.x.

The new engine and its tests should be documented in the engines and test
suites documentation pages respectively. If the engine implementation
doesn't work with some of dragonfly's functionality, such as ``Dictation``
elements, it should be mentioned somewhere in the engine's documentation.

.. Links.
.. _Sphinx documentation engine: https://www.sphinx-doc.org/en/master/
.. _reStructuredText format: http://docutils.sourceforge.net/rst.html
.. _restructuredText primer: http://docutils.sourceforge.net/docs/user/rst/quickstart.html
.. _Read the docs: https://readthedocs.org/
.. _issue tracker: https://github.com/dictation-toolbox/dragonfly/issues
.. _pull request: https://github.com/dictation-toolbox/dragonfly/compare
