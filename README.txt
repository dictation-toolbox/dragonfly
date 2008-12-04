
Dragonfly

Dragonfly is a speech recognition framework. It is a Python 
package which offers a high-level object model and allows its 
users to easily write scripts, macros, and programs which use 
speech recognition.

It currently supports the following speech recognition engines:

    * Dragon NaturallySpeaking (DNS), a product of Nuance.
    * Window Speech Recognition (WSR), as included in Microsoft 
      Windows Vista. 

A sister project is the Dragonfly command-modules repository. 
This is a steadily growing collection of command-modules for 
controlling common programs and automating frequent desktop 
activities. This is the place to look if you want to use speech 
recognition to increase your productivity and efficiency. It 
also contains many examples, from simple to complex, of how to 
use the Dragonfly library.


Documentation

The library's documentation is available for browsing online. 
Please refer to it for a more detailed overview of the Dragonfly 
library.  It is available here:

http://dragonfly.googlecode.com/svn/trunk/dragonfly/documentation/index.html


Features

Dragonfly was written to make it very easy for Python macros, 
scripts, and applications to interface with speech recognition 
engines. Its design allows speech commands and grammar objects 
to be treated as first-class Python objects. This allows easy 
and intuitive definition of complex command grammars and greatly 
simplifies processing recognition results.

    * Language object model; 

    The core of Dragonfly is based on a flexible object model 
    for handling speech elements and command grammars. This 
    makes it easy to define complex language constructs, but 
    also greatly simplifies retrieving the semantic values 
    associated with a speech recognition. 

    * Support for multiple speech recognition engines; 

    Dragonfly's modular nature lets it use different speech 
    recognition engines at the back end, while still providing a 
    single front end interface to its users. This means that a 
    program that uses Dragonfly can be run on any of the 
    supported back end engines without any modification. 
    Currently Dragonfly supports Dragon NaturallySpeaking and 
    Windows Speech Recognition (included with Windows Vista). 

    * Built-in action framework; 

    Dragonfly contains its own powerful framework for defining 
    and executing actions. It includes actions for text input 
    and key-stroke simulation. 


Installation and Use

For detailed instructions on how to install and use Dragonfly, 
please refer to the library's documentation.


Rationale behind Dragonfly

Dragonfly offers a powerful and unified interface to developers 
who want to use speech recognition in their software. It is used 
for both speech-enabling applications and for automating 
computer activities.

In the field of scripting and automation, there are other 
alternatives available that add speech-commands to increase 
efficiency. Dragonfly differs from them in that it is a powerful 
development platform. The open source alternatives currently 
available for use with DNS are compared to Dragonfly as follows:

    * Vocola uses its own easy-to-use scripting language, 
    whereas Dragonfly uses Python and gives the macro-writer all 
    the power available.

    * Unimacro offers a set of macros for common activities, 
    whereas Dragonfly is a platform on which macro-writers can 
    easily build new commands. 
