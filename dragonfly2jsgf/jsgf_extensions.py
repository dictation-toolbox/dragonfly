from jsgf.expansions import Expansion


class Dictation(Expansion):
    """
    Class representing dictation input matching any words spoken that are
    in the active CMU Sphinx dictionary and language model.
    This expansion uses the default compile() implementation because JSGF
    does not handle dictation.
    """
    def __init__(self):
        super(Dictation, self).__init__([])

    def matching_regex(self):
        # Match one or more words separated by whitespace as well as any
        # whitespace preceding the words.
        word = "[a-zA-Z0-9?,\.\-_!;:']+"
        words = "(\s+%s)+" % word
        return words
