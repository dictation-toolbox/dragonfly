# Kaldi Backend

> **Free, open source** speech recognition engine backend for **Linux or Windows** with **active context support**.

For more info and troubleshooting, see [kaldi-active-grammar](https://github.com/daanzu/kaldi-active-grammar). Kaldi-specific issues, suggestions, and feature requests can be submitted there.

Requirements:
* Python 2.7 (3.x support planned); *64-bit required!*
    * Microphone support provided by [pyaudio](https://pypi.org/project/PyAudio/) package
* OS: *Linux or Windows*; macOS planned if there is interest
* Only supports Kaldi left-biphone models, specifically *nnet3 chain* models

## Getting started

Make sure to install dependencies for Kaldi backend. This can be accomplished by installing the `kaldi` extras. From a checkout of this repo/branch:

```
pip install .[kaldi]
```

Download a [compatible general English Kaldi nnet3 chain model](https://github.com/daanzu/kaldi-active-grammar/releases/tag/v0.3.0) from [kaldi-active-grammar](https://github.com/daanzu/kaldi-active-grammar). Unzip it into a directory within the directory with your grammar modules.

Copy the `dragonfly/examples/kaldi_module_loader_plus.py` script into the directory with your grammar modules and run it using:

```
python kaldi_module_loader_plus.py
```

This loader includes a basic sleep/wake grammar to control recognition (simply say "start listening" or "halt listening"). A simpler loader is in `kaldi_module_loader.py`.

Examine loader file for details, including optional parameters to the engine.

A simple, single-file, standalone example can be found in [this gist](https://gist.github.com/daanzu/8bf5f14ed03552f8ab93c853e85de277).

## Known Issues

* Dictation is not processed or formatted, just returning raw lowercase text of the recognition.
* `ListRef` is not fully supported; will only recognize initial elements of List.
* All grammars & rules must be loaded before starting recognition (with a call to `do_recognition()`).
* Grammars & rules cannot be unloaded.
* macOS not supported currently.

Please post if any of these is important to you.
