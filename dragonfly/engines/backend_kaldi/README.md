# Kaldi Backend

For more info, see [kaldi-active-grammar](https://github.com/daanzu/kaldi-active-grammar). Kaldi backend-specific issues, suggestions, and feature requests can be submitted there.

## Getting started

Make sure to install dependencies for Kaldi backend:

* `kaldi-active-grammar == 0.1.0.dev3`
* `pyparsing ~= 2.2`
* `webrtcvad ~= 2.0`
* `pyaudio == 0.2.*`

Download a [compatible general English Kaldi nnet3 chain model](https://github.com/daanzu/kaldi-active-grammar/releases/download/v0.1.0-dev3/kaldi_model_zamia.zip) (\~172MB) from [kaldi-active-grammar](https://github.com/daanzu/kaldi-active-grammar). Unzip it into a directory within the directory with your grammar modules.

Copy the `dragonfly/examples/kaldi_module_loader.py` script into the directory with your grammar modules and run it using:

```
python kaldi_module_loader.py
```
