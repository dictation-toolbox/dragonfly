import os
import subprocess

build_binary = r"c:\python25\scripts\sphinx-build"
build_type = "html"
directory = os.path.dirname(__file__)
src_dir = os.path.abspath(os.path.join(directory, "documentation"))
dst_dir = os.path.abspath(os.path.join(directory, "dragonfly", "documentation"))

arguments = [build_binary, "-a", "-b", build_type, src_dir, dst_dir]
print "Executing:", arguments
subprocess.call(arguments)
