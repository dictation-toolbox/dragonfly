# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project will adhere to [Semantic Versioning](http://semver.org/spec/v2.0.0.html) as of version 0.7.0.

Note: this project had no release versions between [0.6.6b1] and [0.7.0]. Notable changes made between these versions are documented in the commit history and will be placed under headings in this file over time.

## [0.8.0] - 2018-09-27
### Added
- Add EngineBase.grammars property for retrieving loaded grammars.
- Add MappingRule.specs property to allow retrieval of specs after initialisation.
- Add checks in Sphinx engine for using unknown words in grammars and keyphrases.
- Add configurable speech and hypothesis recording to Sphinx engine for model training.
- Add Sphinx engine documentation page.

### Changed
- Change Sphinx engine module loader to use local engine config if it exists.
- Change README to reference the new documentation page on the Sphinx engine.
- Change documentation/conf.py to allow the docs to be built locally.
- Change package distribution name to *dragonfly2* in order to upload releases to PyPI.org.
- Update README and documentation/installation.txt with instructions to install via pip.
- Replace README.md with README.rst because PyPI doesn't easily support markdown any more.

### Fixed
- Fix a bug with CompoundRule.spec.
- Fix translation of RuleRef without explicit name in dragonfly2jsgf (thanks [@daanzu](https://github.com/daanzu)).
- Update virtual keyboard extended key support (thanks [@Versatilus](https://github.com/Versatilus)).
- Add missing methods for WSR and Sphinx engines in test/element_tester.
- Fix a few minor problems with the Sphinx engine.
- Fix bug where newly-constructed rules were not inactivated (thanks [@wolfmanstout](https://github.com/wolfmanstout)).

### Removed
- Remove pyjsgf submodule as it can be installed via pip now.
- Remove Sphinx engine's README now that there is a documentation page.
- Remove ez_setup.py and stop using it in setup.py.

## [0.7.0] - 2018-07-10
### Added
- Add multi-platform Clipboard class that works on Windows, Linux, Mac OS X.
- Support Unicode grammar specs and window titles.
- Support alternate keyboard layouts.
- Add additional speech recognition backend using CMU Pocket Sphinx.
- Add optional Sphinx dependencies as pyjsgf and sphinxwrapper Git sub-modules.
- Add additional unit tests for enhancements.
- Add additional six and pyperclip dependencies in setup.py.

### Changed
- Mock Windows-specific functionality for other platforms to allow importing.
- Make pywin32 only required on Windows.
- Made natlink optional in dragonfly/timer.py.
- Clean up code styling and semantic issues.
- Convert code base to support Python 3.x as well as Python 2.7.
- Update natlink links in documentation.

### Fixed
- Make the Paste action work with the Unicode clipboard format (thanks [@comodoro](https://github.com/comodoro)).
- Fix issues with dragonfly's monitor list and class.

## [2016]
TODO

## [2015]
TODO

## [2014]
TODO

## [0.6.6b1] - 2009-04-13
TODO

## [0.6.5] - 2009-04-08
TODO

## [0.6.4] - 2009-02-01
TODO

## [0.6.4-rc3] - 2008-12-06
TODO

## [0.6.4-rc2] - 2008-12-02
TODO

## [0.6.4-rc1] - 2008-11-12
TODO

## [0.6.1] - 2008-10-18
This release is the first in the Git version control system.

[Unreleased]: https://github.com/Danesprite/dragonfly/compare/0.8.0...HEAD
[0.8.0]:      https://github.com/Danesprite/dragonfly/compare/0.7.0...0.8.0
[0.7.0]:      https://github.com/Danesprite/dragonfly/compare/74981c1...0.7.0
[0.6.6b1]:    https://github.com/Danesprite/dragonfly/compare/0.6.5...0.6.6b1
[0.6.5]:      https://github.com/Danesprite/dragonfly/compare/0.6.4-rc3...0.6.5
[0.6.4]:      https://github.com/Danesprite/dragonfly/compare/0.6.4-rc3...0.6.4
[0.6.4-rc3]:  https://github.com/Danesprite/dragonfly/compare/0.6.4-rc2...0.6.4-rc3
[0.6.4-rc2]:  https://github.com/Danesprite/dragonfly/compare/0.6.4-rc1...0.6.4-rc2
[0.6.4-rc1]:  https://github.com/Danesprite/dragonfly/compare/0.6.1...0.6.4-rc1
[0.6.1]:      https://github.com/Danesprite/dragonfly/compare/03d06af...0.6.1
