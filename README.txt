Dragonfly
============================================================================

Dragonfly is a speech recognition framework. It is a Python 
package which offers a high-level object model and allows its 
users to easily write scripts, macros, and programs which use 
speech recognition.

It currently supports the following speech recognition engines:

 - *Dragon NaturallySpeaking* (DNS), a product of *Nuance*
 - *Windows Speech Recognition* (WSR), included with Microsoft 
   Windows Vista, Windows 7, and freely available for Windows XP


Features
----------------------------------------------------------------------------

Dragonfly was written to make it very easy for Python macros, 
scripts, and applications to interface with speech recognition 
engines.  Its design allows speech commands and grammar objects 
to be treated as first-class Python objects.  This allows easy 
and intuitive definition of complex command grammars and greatly 
simplifies processing recognition results.

*Language object model*
   The core of Dragonfly is based on a flexible object model for 
   handling speech elements and command grammars.  This makes it 
   easy to define complex language constructs, but also greatly 
   simplifies retrieving the semantic values associated with a 
   speech recognition.

*Support for multiple speech recognition engines*
   Dragonfly's modular nature lets it use different speech 
   recognition engines at the back end, while still providing a 
   single front end interface to its users.  This means that a 
   program that uses Dragonfly can be run on any of the 
   supported back end engines without any modification. 
   Currently Dragonfly supports Dragon NaturallySpeaking and 
   Windows Speech Recognition (included with Windows Vista).

*Built-in action framework*
   Dragonfly contains its own powerful framework for defining 
   and executing actions.  It includes actions for text input 
   and key-stroke simulation.


Existing command modules
----------------------------------------------------------------------------

A sister project is the Dragonfly
`command-modules repository
<http://dragonfly-modules.googlecode.com/svn/trunk/command-modules/documentation/index.html>`_.
This is a steadily growing collection of command-modules for 
controlling common programs and automating frequent desktop 
activities. This is the place to look if you want to use speech 
recognition to increase your productivity and efficiency. It 
also contains many examples, from simple to complex, of how to 
use the Dragonfly library.


Usage example
----------------------------------------------------------------------------

A very simple example of Dragonfly usage is to create a static 
voice command with a callback that will be called when the 
command is spoken.  This is done as follows: ::

   from dragonfly.all import Grammar, CompoundRule

   # Voice command rule combining spoken form and recognition processing.
   class ExampleRule(CompoundRule):
       spec = "do something computer"                  # Spoken form of command.
       def _process_recognition(self, node, extras):   # Callback when command is spoken.
           print "Voice command spoken."

   # Create a grammar which contains and loads the command rule.
   grammar = Grammar("example grammar")                # Create a grammar to contain the command rule.
   grammar.add_rule(ExampleRule())                     # Add the command rule to the grammar.
   grammar.load()                                      # Load the grammar.

The example above is very basic and doesn't show any of 
Dragonfly's exciting features, such as dynamic speech elements. 
To learn more about these, please take a look at the project's 
documentation `here
<http://dragonfly.googlecode.com/svn/trunk/dragonfly/documentation/index.html>`_.


Rationale behind Dragonfly
----------------------------------------------------------------------------

Dragonfly offers a powerful and unified interface to developers 
who want to use speech recognition in their software. It is used 
for both speech-enabling applications and for automating 
computer activities.

In the field of scripting and automation, there are other 
alternatives available that add speech-commands to increase 
efficiency. Dragonfly differs from them in that it is a powerful 
development platform. The open source alternatives currently 
available for use with DNS are compared to Dragonfly as follows:

 - Vocola uses its own easy-to-use scripting language, 
   whereas Dragonfly uses Python and gives the macro-writer all 
   the power available.

 - Unimacro offers a set of macros for common activities, 
   whereas Dragonfly is a platform on which macro-writers can 
   easily build new commands. 
