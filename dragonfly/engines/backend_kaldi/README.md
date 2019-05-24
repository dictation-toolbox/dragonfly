# Kaldi Backend

> **Free, open source** speech recognition engine backend for **Linux or Windows** with **active context support**.

For more info, see [kaldi-active-grammar](https://github.com/daanzu/kaldi-active-grammar). Kaldi backend-specific issues, suggestions, and feature requests can be submitted there.

Requirements:
* Python 2.7, 3.?+ (only 2.7 tested currently); *64-bit required*
    * Microphone support provided by [pyaudio](https://pypi.org/project/PyAudio/) package
* OS: *Linux or Windows*; macOS planned if there is interest
* Only supports Kaldi left-biphone models, specifically *nnet3 chain* models

## Getting started

Make sure to install dependencies for Kaldi backend. This can be accomplished by installing the `kaldi` extras. From a checkout of this repo/branch:

```
pip install .[kaldi]
```

Download a [compatible general English Kaldi nnet3 chain model](https://github.com/daanzu/kaldi-active-grammar/releases/tag/v0.2.2) from [kaldi-active-grammar](https://github.com/daanzu/kaldi-active-grammar). Unzip it into a directory within the directory with your grammar modules.

Copy the `dragonfly/examples/kaldi_module_loader.py` script into the directory with your grammar modules and run it using:

```
python kaldi_module_loader.py
```

Examine loader file for details, including optional parameters to engine.

A simpler, standalone example can be found in [this gist](https://gist.github.com/daanzu/8bf5f14ed03552f8ab93c853e85de277).

## Known Issues

* Dictation is not processed or formatted, just returning raw lowercase text of the recognition.
* `ListRef` support is not implemented.
* macOS not supported currently.

Please post if this is important to you.
