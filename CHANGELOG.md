# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project will adhere to [Semantic Versioning](http://semver.org/spec/v2.0.0.html) as of version 0.7.0.

Note: this project had no release versions between [0.6.6b1] and [0.7.0]. Notable changes made between these versions are documented in the commit history and will be placed under headings in this file over time.

## [0.7.0] - 2017-07-10
### Added
- Add multi-platform Clipboard class that works on Windows, Linux, Mac OS X
- Support Unicode grammar specs and window titles
- Support alternate keyboard layouts
- Add additional speech recognition backend using CMU Pocket Sphinx
- Add additional unit tests for enhancements
- Add additional six and pyperclip dependencies in setup.py

### Changed
- Mock Windows-specific functionality for other platforms to allow importing
- Make pywin32 only required on Windows
- Made natlink optional in dragonfly/timer.py
- Clean up code styling and semantic issues
- Convert code base to support Python 3.x as well as Python 2.x
- Update natlink links in documentation

### Fixed
- Make the Paste action work with the Unicode clipboard format @comodoro
- Fix issues with dragonfly's monitor list and class

## [2016]
TODO

## [2015]
TODO

## [2014]
TODO


[0.7.0]: https://github.com/Danesprite/dragonfly/compare/74981c1...0.7.0
