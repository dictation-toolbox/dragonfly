Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_ using the
`reStructuredText format`_ instead of Markdown. This project adheres to
`Semantic Versioning`_ as of version 0.7.0_.

Note: this project had no release versions between 0.6.6b1_ and
0.7.0_. Notable changes made between these versions are documented in the
commit history and will be placed under headings in this file over time.

0.10.1_ - 2019-01-05
--------------------

Fixed
~~~~~
* Disable **backwards-incompatible** Unicode keyboard functionality by
  default for the :class:`Text` action. Restoring the old behaviour
  requires deleting/modifying the `~/.dragonfly2-speech/settings.cfg`
  file.


0.10.0_ - 2018-12-28
--------------------

Added
~~~~~
* Add configurable Windows Unicode keyboard support to the :class:`Text`
  action (thanks `@Versatilus`_).
* Add Windows accessibility API support to Dragonfly (thanks
  `@wolfmanstout`_).
* Add a command-line interface for Dragonfly with a "test" command.
* Add multi-platform RunCommand action.
* Add text input engine backend.

Changed
~~~~~~~
* Change default paste key for the Paste action to Shift+insert.
* Change typeables.py to log errors for untypeable characters.
* Make **backwards-incompatible** change to the :class:`Text` class where
  it no longer respects modifier keys being held down by default.
* Move TestContext class from Pocket Sphinx engine tests into
  test/infrastructure.py.
* Move command module classes from loader scripts into
  dragonfly/loader.py.

Fixed
~~~~~
* Fix various Unicode and encoding issues (thanks `@Versatilus`_).

0.9.1_ - 2018-11-22
-------------------

Changed
~~~~~~~
* Various changes to documentation.
* Make Arabic, Indonesian and Malaysian languages automatically load if
  required.

Fixed
~~~~~
* Fix a bug with dragonfly's MagnitudeIntBuilder class specific to
  Python 3.x.
* Replace all imports using 'dragonfly.all' with just 'dragonfly'.
* Fix a bug where mouse wheel scrolling fails with high repeat values
  (thanks `@wolfmanstout`_).
* Fix a few minor problems with the Pocket Sphinx engine.
* Fix error handling and logging when initialising the WSR/SAPI5
  engine.

0.9.0_ - 2018-10-28
-------------------

Added
~~~~~
* Add default VAD decoder config options to Pocket Sphinx engine config
  module.
* Add documentation page on dragonfly's supported languages.
* Add repository core.autorclf settings for consistent file line
  endings.
* Add scrolling and extra button support for dragonfly's Mouse action
  (thanks `@Versatilus`_).

Changed
~~~~~~~
* Adjust pyperclip version requirements now that a bug is fixed.
* Change error types raised in a few Rule class methods.
* Change NatlinkEngine.speak() to turn on the mic after speech playback
  for consistency between Dragon versions.
* Normalise all file line endings to Unix-style line feeds.

Fixed
~~~~~
* Make Read the Docs generate documentation from Python modules again.

0.8.0_ - 2018-09-27
---------------------

Added
~~~~~

* Add EngineBase.grammars property for retrieving loaded grammars.
* Add MappingRule.specs property to allow retrieval of specs after
  initialisation.
* Add checks in Sphinx engine for using unknown words in grammars and
  keyphrases.
* Add configurable speech and hypothesis recording to Sphinx engine for
  model training.
* Add Sphinx engine documentation page.

Changed
~~~~~~~

* Change Sphinx engine module loader to use local engine config if it
  exists.
* Change README to reference the new documentation page on the Sphinx
  engine.
* Change documentation/conf.py to allow the docs to be built locally.
* Change package distribution name to *dragonfly2* in order to upload
  releases to PyPI.org.
* Update README and documentation/installation.txt with instructions to
  install via pip.
* Replace README.md with README.rst because PyPI doesn't easily support
  markdown any more.

Fixed
~~~~~
* Fix a bug with CompoundRule.spec.
* Fix translation of RuleRef without explicit name in dragonfly2jsgf
  (thanks `@daanzu`_).
* Update virtual keyboard extended key support (thanks `@Versatilus`_).
* Add missing methods for WSR and Sphinx engines in
  test/element\_tester.
* Fix a few minor problems with the Sphinx engine.
* Fix bug where newly-constructed rules were not inactivated (thanks
  `@wolfmanstout`_).

Removed
~~~~~~~
* Remove pyjsgf submodule as it can be installed via pip now.
* Remove Sphinx engine's README now that there is a documentation page.
* Remove ez\_setup.py and stop using it in setup.py.

0.7.0_ - 2018-07-10
-------------------

Added
~~~~~
* Add multi-platform Clipboard class that works on Windows, Linux, Mac
  OS X.
* Support Unicode grammar specs and window titles.
* Support alternate keyboard layouts.
* Add additional speech recognition backend using CMU Pocket Sphinx.
* Add optional Sphinx dependencies as pyjsgf and sphinxwrapper Git
  sub-modules.
* Add additional unit tests for enhancements.
* Add additional six and pyperclip dependencies in setup.py.

Changed
~~~~~~~

* Mock Windows-specific functionality for other platforms to allow
  importing.
* Make pywin32 only required on Windows.
* Made natlink optional in dragonfly/timer.py.
* Clean up code styling and semantic issues.
* Convert code base to support Python 3.x as well as Python 2.7.
* Update natlink links in documentation.

Fixed
~~~~~
* Make the Paste action work with the Unicode clipboard format
  (thanks `@comodoro`_).
* Fix issues with dragonfly's monitor list and class.

2016
----

TODO

2015
----

TODO

2014
----

TODO

0.6.6b1_ - 2009-04-13
---------------------

TODO

0.6.5_ - 2009-04-08
-------------------

TODO

0.6.4_ - 2009-02-01
-------------------

TODO

`0.6.4-rc3`_ - 2008-12-06
-------------------------

TODO

`0.6.4-rc2`_ - 2008-12-02
-------------------------

TODO

`0.6.4-rc1`_ - 2008-11-12
-------------------------

TODO

0.6.1_ - 2008-10-18
-------------------

This release is the first in the Git version control system.


.. Release links.
.. _Unreleased:  https://github.com/Danesprite/dragonfly/compare/0.10.1...HEAD
.. _0.10.1:      https://github.com/Danesprite/dragonfly/compare/0.10.0...0.10.1
.. _0.10.0:      https://github.com/Danesprite/dragonfly/compare/0.9.1...0.10.0
.. _0.9.1:       https://github.com/Danesprite/dragonfly/compare/0.9.0...0.9.1
.. _0.9.0:       https://github.com/Danesprite/dragonfly/compare/0.8.0...0.9.0
.. _0.8.0:       https://github.com/Danesprite/dragonfly/compare/0.7.0...0.8.0
.. _0.7.0:       https://github.com/Danesprite/dragonfly/compare/74981c1...0.7.0
.. _0.6.6b1:     https://github.com/Danesprite/dragonfly/compare/0.6.5...0.6.6b1
.. _0.6.5:       https://github.com/Danesprite/dragonfly/compare/0.6.4-rc3...0.6.5
.. _0.6.4:       https://github.com/Danesprite/dragonfly/compare/0.6.4-rc3...0.6.4
.. _0.6.4-rc3:   https://github.com/Danesprite/dragonfly/compare/0.6.4-rc2...0.6.4-rc3
.. _0.6.4-rc2:   https://github.com/Danesprite/dragonfly/compare/0.6.4-rc1...0.6.4-rc2
.. _0.6.4-rc1:   https://github.com/Danesprite/dragonfly/compare/0.6.1...0.6.4-rc1
.. _0.6.1:       https://github.com/Danesprite/dragonfly/compare/03d06af...0.6.1

.. Other links.
.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _reStructuredText format: http://docutils.sourceforge.net/rst.html
.. _Semantic Versioning: http://semver.org/spec/v2.0.0.html
.. _@comodoro: https://github.com/comodoro
.. _@daanzu: https://github.com/daanzu
.. _@Versatilus: https://github.com/Versatilus
.. _@wolfmanstout: https://github.com/wolfmanstout
