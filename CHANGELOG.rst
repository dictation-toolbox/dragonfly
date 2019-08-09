Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_ using the
`reStructuredText format`_ instead of Markdown. This project adheres to
`Semantic Versioning`_ as of version 0.7.0_.

Note: this project had no release versions between 0.6.6b1_ and
0.7.0_. Notable changes made between these versions are documented in the
commit history and will be placed under headings in this file over time.

0.16.1_ - 2019-08-04
--------------------

Added
~~~~~

* Add Dictation string formatting examples into documentation.
* Add Kaldi informational messages during grammar loading pauses.

Changed
~~~~~~~

* Clean up code style in engines/base/dictation.py.
* Bump required kaldi-active-grammar version to 0.6.0.
* Update Kaldi engine documentation (thanks `@daanzu`_ and `@LexiconCode`_).

Fixed
~~~~~

* Fix Win32Window.set_foreground() failures by forcing the interpreter's
  main thread to "receive" the last input event (press & release control).
* Fix quite a few bugs with the Kaldi engine. (thanks `@daanzu`_).
* Make the Sphinx engine ignore unknown words in grammars instead of raising
  errors.


0.16.0_ - 2019-07-21
--------------------

Added
~~~~~
* Add FakeWindow class imported as 'Window' on unsupported platforms.
* Add RPC methods for getting speech state & recognition history.
* Add Window.get_matching_windows() and Window.get_window class methods.
* Add X11Window class for interacting with windows on X11 (adapted from
  `Aenea`_).
* Add alternative dragonfly module loader for natlink.
* Add documentation for X11 keyboard and window support.
* Add enhancements to Dictation and DictationContainer objects (thanks `@mrob95`_).
* Add missing Integer Repeat factor example into documentation.
* Add optional '--language' argument to dragonfly's 'test' command (CLI).
* Add xdotool & libxdo keyboard implementations to replace pynput on X11
  (adapted from `Aenea`_).

Changed
~~~~~~~
* Change the dragonfly.windows.window module to import the current
  platform's Window class.
* Improve Kaldi documentation and add an example demo script
  (thanks `@daanzu`_).
* Make test_actions.py and test_window.py files run with all test suites and
  on all platforms.
* Move some code from FocusWindow into Window classes.
* Rename dragonfly's Window class to Win32Window and move it into
  win32_window.py.
* Swap Repeat class's constructor arguments so that 'extra' is first
  (backwards-compatible) (thanks `@mrob95`_).
* Unmock the Window, WaitWindow, FocusWindow, BringApp and StartApp classes
  for all platforms.
* Update Kaldi engine backend with user lexicon support, microphone listing,
  other improvements and bug fixes (thanks `@daanzu`_).

Fixed
~~~~~
* Fix DragonflyError raised if importing ShortIntegerContent whilst using a
  speaker language that isn't English.
* Fix Thread.isAlive() deprecation warnings in Python 3.7.
* Fix import error in SAPI5 engine file (specific to Python 3).
* Fix incorrect file names in the 'plus' module loaders.
* Fix problem with building documentation when kaldi_active_grammar is
  installed.
* Fix spec string decoding in the Text action class.


0.15.0_ - 2019-06-24
--------------------

Added
~~~~~
* Add new `Kaldi engine`_ backend for Linux & Windows, including
  documentation and module loaders  (thanks `@daanzu`_).
* Add more featureful loader for WSR with sleep/wake functionality
  (thanks `@daanzu`_).
* Add FuncContext class that determines context activity by callable
  argument (thanks `@daanzu`_).
* Allow all timer manager callbacks to be manually disabled (used in tests).

Changed
~~~~~~~
* Change RunCommand action to use a member for the process_command argument.
* Change how Sapi5Compiler compiles Impossible elements (more impossible
  now).
* Change sphinx engine install instructions and required dependency
  versions.
* Change the dragonfly.timer._Timer class so that it works correctly for all
  supported engines and platforms via engine.create_timer().
* Make local development documentation use read_the_docs theme (thanks
  `@daanzu`_).
* Move timer-related engine code into DelegateTimerManagerInterface so it is
  re-used by multiple engines.

Deprecated
~~~~~~~~~~
* Deprecate the old dragonfly.timer._Timer class.

Fixed
~~~~~
* Fix SAPI5 engine setting grammars as not exclusive (thanks `@daanzu`_).
* Fix SAPI5 window change detection and allow manually processing (thanks
  `@daanzu`_).
* Fix slow RPC response times for WSR and natlink by adjusting engine timer
  intervals.
* Preserve Dragon mic state in the NatlinkEngine.speak() method (thanks
  `@lexxish`_).

Removed
~~~~~~~
* Remove sphinxwrapper Git sub-module from project.

0.14.1_ - 2019-05-31
--------------------

Changed
~~~~~~~
* Change English integers to include "too" and "to" as equivalents for
  "two" (thanks `@lexxish`_).

0.14.0_ - 2019-05-21
--------------------

Added
~~~~~
* Add documentation on dragonfly's logging infrastructure.
* Add dragonfly.rpc sub-package and usage example.
* Add enable() and disable() methods to ThreadedTimerManager class.
* Add optional "repeating" parameter to the multiplexing Timer class and
  engine.create_timer() method.
* Add recognize_forever() method to WSR engine class.

Changed
~~~~~~~
* Change AppContext class to allow lists of titles and executables
  (thanks `@mrob95`_).
* Change WSR engine to call timer functions on the main thread.
* Change dragonfly stdout logging formatter to include the level name.
* Make dragonfly's multiplexing timer classes more thread safe.
* Replace WSR module loader's PumpWaitingMessages loop with
  engine.recognize_forever().
* Simplify sphinx engine availability checks.

Fixed
~~~~~
* Fix WSR engine context bug with a hook for foreground window changes
  (thanks `@tylercal`_).
* Fix a bug with Monitor objects caused by incorrect coordinate calculations
  (thanks `@tylercal`_).
* Fix some example files that break if used with Python 3.
* Stop calling setup_log() in a few dragonfly modules to avoid side effects.
* Stop encoding to windows-1252 in a few places if using Python 3
  (thanks `@tylercal`_).
* Stop erasing dragonfly's logging file now that setup_log() isn't always
  used.

0.13.0_ - 2019-04-24
--------------------

Added
~~~~~
* Add and document optional "remap_data" parameter to Function action to
  allow using extras with different names than the function argument names.
* Add Key, Text and Paste action support for X11 and Mac OS using `pynput`_.
* Add modified ContextAction class from `Aenea`_
  (thanks `@calmofthestorm`_).
* Add more flexible ShortIntegerRef class (thanks `@mrob95`_).

Changed
~~~~~~~
* Allow saying "oh" as well as "zero" for IntegerRefs.
* Change the Sphinx engine to disallow multiple grammars with the same name.
* Change the Text action's default pause value to 0.005 seconds & make it
  configurable.
* Rename *Language Support* doc page to *Language Support & Sub-package*.
* Rename 3 example command modules to start with underscores.
* Stop mocking Windows-only sendinput classes & functions on other
  platforms.
* Update some documentation to mention that dragonfly's module loaders will
  load from files matching "_\*.py" rather than "\*.py".

Fixed
~~~~~
* Allow Text sub-classes to override the '_pause_default' attribute.
* Fix Sphinx engine bug where grammar searches could be overridden.
* Fix some issues with dragonfly's mocked actions.

0.12.0_ - 2019-04-04
--------------------

Added
~~~~~
* Add *CONTRIBUTING.rst* file.
* Add Repetition 'optimize' parameter that should reduce grammar complexity.
* Add SphinxEngine.default_search_result property.
* Add SphinxEngine.write_transcript_files method.
* Add WSR/SAPI5 retain audio support for saving recognition data
  (thanks `@daanzu`_).
* Add example *sphinx_wave_transcriber.py* script into *dragonfly/examples*.
* Allow passing keyword arguments to get_engine() functions
  (thanks `@daanzu`_).

Changed
~~~~~~~
* Change Sphinx and text engines to call notify_recognition() before rule processing.
* Change Sphinx engine to allow specifying default decoder search options
  other than "-lm".
* Change SphinxEngine.process_wave_file() method to yield recognised words.
* Change the format of the Sphinx engine's saved training data.
* Disable the Sphinx engine's built-in key phrases if the engine language
  isn't English.
* Disable writing Sphinx engine training data to files by default.
* Erase dragonfly's log file when creating the logging handler to avoid
  large files.
* Make all Sphinx engine configuration optional.
* Replace Sphinx engine's *PYAUDIO_STREAM_KEYWORD_ARGS* config option with 4
  new options.
* Simplify Sphinx engine backend code and improve its performance.
* Update Sphinx engine documentation to reflect the other changes.

Fixed
~~~~~
* Add rule processing error handling to the Sphinx and text engines.
* Fix lots of bugs with the Sphinx engine backend.
* Fix Sphinx engine's support for exclusive grammars and multiplexing
  timers.
* Minimise dropped audio frames when recording with the Sphinx engine.

Removed
~~~~~~~
* Remove Sphinx engine's *config.py* file.
* Remove the Sphinx engine's support for Dictation elements for now.
* Remove/hide some unnecessary public SphinxEngine methods and properties.

0.11.1_ - 2019-02-22
--------------------

Changed
~~~~~~~
* Change the RunCommand action to allow the *command* argument to be a list
  to pass directly to *subprocess.Popen* instead of through *shlex.split()*.

Fixed
~~~~~
* Fix the RunCommand action so it properly parses command strings using
  non-POSIX/Windows paths.
* Fix minor issues with RunCommand's string representation and error logging.

0.11.0_ - 2019-01-30
--------------------

Added
~~~~~
* Add additional tests to dragonfly's test suites.
* Add documentation for dragonfly's timer classes.
* Add new synchronous and process properties and error handling to
  the RunCommand action.
* Add timer manager class for the text input and SAPI 5 engines.

Changed
~~~~~~~
* Change default engine class for SAPI 5 engine backend to
  Sapi5InProcEngine.
* Change logging framework to use *~/.dragonfly.log* as the log
  file to make logging work on Windows and on other operating
  systems.
* Change the Natlink test suite to run different tests for
  different DNS versions.
* Change the default test suite to the "text" engine's test suite
  and add it to the CI build.
* Change typeables.py so that all symbols can be referred to by
  their printable representation (thanks `@wolfmanstout`_).
* Make several changes to the SAPI 5 engine backend so it passes
  the relevant dragonfly tests.
* Update how _generate_typeables.py generates code used in
  typeables.py.
* Update several documentation pages.
* Use a RecognitionObserver in dfly-loader-wsr.py for user feedback
  when using Sapi5InProcEngine.

Fixed
~~~~~
* Add default implementation for the RunCommand.process_command
  method so that most commands don't hang without an implementation.
* Fix bug where the Text action intermittently ignores the
  hardware_apps override (thanks `@wolfmanstout`_).
* Fix some encoding bugs with the text input engine.
* Fix various issues with dragonfly's tests and test framework.

Removed
~~~~~~~
* Remove old test files.

0.10.1_ - 2019-01-06
--------------------

Fixed
~~~~~
* Disable **backwards-incompatible** Unicode keyboard functionality by
  default for the Text action. Restoring the old behaviour
  requires deleting/modifying the `~/.dragonfly2-speech/settings.cfg`
  file.

0.10.0_ - 2018-12-28
--------------------

Added
~~~~~
* Add configurable Windows Unicode keyboard support to the Text
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
* Make **backwards-incompatible** change to the Text class where
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
-------------------

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
.. _Unreleased:  https://github.com/dictation-toolbox/dragonfly/compare/0.16.1...HEAD
.. _0.16.1:      https://github.com/dictation-toolbox/dragonfly/compare/0.16.0...0.16.1
.. _0.16.0:      https://github.com/dictation-toolbox/dragonfly/compare/0.15.0...0.16.0
.. _0.15.0:      https://github.com/dictation-toolbox/dragonfly/compare/0.14.1...0.15.0
.. _0.14.1:      https://github.com/dictation-toolbox/dragonfly/compare/0.14.0...0.14.1
.. _0.14.0:      https://github.com/dictation-toolbox/dragonfly/compare/0.13.0...0.14.0
.. _0.13.0:      https://github.com/dictation-toolbox/dragonfly/compare/0.12.0...0.13.0
.. _0.12.0:      https://github.com/dictation-toolbox/dragonfly/compare/0.11.1...0.12.0
.. _0.11.1:      https://github.com/dictation-toolbox/dragonfly/compare/0.11.0...0.11.1
.. _0.11.0:      https://github.com/dictation-toolbox/dragonfly/compare/0.10.1...0.11.0
.. _0.10.1:      https://github.com/dictation-toolbox/dragonfly/compare/0.10.0...0.10.1
.. _0.10.0:      https://github.com/dictation-toolbox/dragonfly/compare/0.9.1...0.10.0
.. _0.9.1:       https://github.com/dictation-toolbox/dragonfly/compare/0.9.0...0.9.1
.. _0.9.0:       https://github.com/dictation-toolbox/dragonfly/compare/0.8.0...0.9.0
.. _0.8.0:       https://github.com/dictation-toolbox/dragonfly/compare/0.7.0...0.8.0
.. _0.7.0:       https://github.com/dictation-toolbox/dragonfly/compare/74981c1...0.7.0
.. _0.6.6b1:     https://github.com/dictation-toolbox/dragonfly/compare/0.6.5...0.6.6b1
.. _0.6.5:       https://github.com/dictation-toolbox/dragonfly/compare/0.6.4-rc3...0.6.5
.. _0.6.4:       https://github.com/dictation-toolbox/dragonfly/compare/0.6.4-rc3...0.6.4
.. _0.6.4-rc3:   https://github.com/dictation-toolbox/dragonfly/compare/0.6.4-rc2...0.6.4-rc3
.. _0.6.4-rc2:   https://github.com/dictation-toolbox/dragonfly/compare/0.6.4-rc1...0.6.4-rc2
.. _0.6.4-rc1:   https://github.com/dictation-toolbox/dragonfly/compare/0.6.1...0.6.4-rc1
.. _0.6.1:       https://github.com/dictation-toolbox/dragonfly/compare/03d06af...0.6.1

.. Other links.
.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _reStructuredText format: http://docutils.sourceforge.net/rst.html
.. _Semantic Versioning: http://semver.org/spec/v2.0.0.html
.. _@comodoro: https://github.com/comodoro
.. _@daanzu: https://github.com/daanzu
.. _@Versatilus: https://github.com/Versatilus
.. _@wolfmanstout: https://github.com/wolfmanstout
.. _@calmofthestorm: https://github.com/calmofthestorm
.. _@mrob95: https://github.com/mrob95
.. _@tylercal: https://github.com/tylercal
.. _@lexxish: https://github.com/lexxish
.. _@LexiconCode: https://github.com/LexiconCode
.. _Aenea: https://github.com/dictation-toolbox/aenea
.. _pynput: https://github.com/moses-palmer/pynput
.. _Kaldi engine: https://dragonfly2.readthedocs.io/en/latest/kaldi_engine.html
