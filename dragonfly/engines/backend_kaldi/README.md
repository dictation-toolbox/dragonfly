# Kaldi Backend

For more info, see [kaldi-active-grammar](https://github.com/daanzu/kaldi-active-grammar). Kaldi backend-specific issues, suggestions, and feature requests can be submitted there.

Requirements:
* Python 2.7, 3.?+ (only 2.7 tested currently); *64-bit required*
    * Microphone support provided by [pyaudio](https://pypi.org/project/PyAudio/) package
* OS: *Windows only currently*; Linux & macOS planned
* Only supports Kaldi left-biphone models, specifically *nnet3 chain* models

## Getting started

Make sure to install dependencies for Kaldi backend. This can be accomplished by installing the `kaldi` extras. From a checkout of this repo/branch:

```
pip install .[kaldi]
```

Download a [compatible general English Kaldi nnet3 chain model](https://github.com/daanzu/kaldi-active-grammar/releases/download/v0.1.0-dev3/kaldi_model_zamia.zip) (\~172MB) from [kaldi-active-grammar](https://github.com/daanzu/kaldi-active-grammar). Unzip it into a directory within the directory with your grammar modules.

Copy the `dragonfly/examples/kaldi_module_loader.py` script into the directory with your grammar modules and run it using:

```
python kaldi_module_loader.py
```

## Known Issues

* `ListRef` support is not implemented.

Please post if this is important to you.
