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


.. Links.
.. _Read the docs: https://readthedocs.org/
.. _Sphinx documentation engine: https://www.sphinx-doc.org/en/master/
.. _issue tracker: https://github.com/dictation-toolbox/dragonfly/issues
.. _pull request: https://github.com/dictation-toolbox/dragonfly/compare
.. _reStructuredText format: http://docutils.sourceforge.net/rst.html
.. _restructuredText primer: http://docutils.sourceforge.net/docs/user/rst/quickstart.html
.. _sphinx.ext.autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
