Paperdoll Creator [NSFW, 18+]


# --------------------------
# content disclaimer
# --------------------------

The content used in this software may be found sexual in nature or inappropriate by some people. If you are under 18 years old or offended by content of such nature please do not clone, download or run this software or interact with it in any way.


# --------------------------
# functionality disclaimer
# --------------------------

There will be problems! This is an alpha release. It is not feature complete and it WILL HAVE BUGS!


# --------------------------
# summary
# --------------------------

This tool allows you to create dynamic paperdolls with various body shapes and fitting clothing. You draw the keyframes, for example the smallest and the largest size of a T-shirt, as SVG art and Paperdoll Creator calculates the indermediate sizes based on instructions in XML. Don't know what I'm talking about? Take the tour :-)


# --------------------------
# current features
# --------------------------

* Paperdolls with morphable bodies (1 doll as example art included)
* Morphable outfits that exactly fit the doll body (1 outfit as example art included, 1 body morph included)
* Dynamic clothing or accessories that are created from a single SVG graphic and morph by approximating the geometry changes in their target
* Support for SVG files created in Inkscape (SVGs from other sources might work too)


# --------------------------
# description
# --------------------------

# the problem and the solution
When creating paperdoll art for multiple characters, you usually have to decide if you want lots of different outfits or unique bodies for each character. The visually most interesting option, lots of different outfits and unique bodies, leads to an explosion of character and outfit combinations that quickly is just too much work to bother.
This is the problem Paperdoll Creator solves. By implementing a doll body that can have various shapes and outfits that can adapt to that shapes, you can create as many combinations of unique dolls
and outfits as you want with comparatively little effort.

# how it works
Paperdoll Creator implements something similar to an animation system, but you don't have to change shapes over time. You can also change shape A according to user input, morph shape B based on the changes in shape A or combine several similar shapes into one.
This animation system does not make a lot of assumptions on what you want to do, so you have to control it. This currently happens in an XML file, for example linedoll.xml of the included example art. A bit complicated, I know. The upside is that you have quite some flexibility in how you use this system despite not having to write code yourself.


# --------------------------
# implementation details
# --------------------------
Paperdoll Creator is powered by Python 3.5.2 and Qt 5.7


# --------------------------
# running from source
# --------------------------
1. Install Python 3.5.2; You will probably need that exact version, though other minor version of 3.5 might work too.
2. Install Qt 5.7 and PyQt for your Python 3.5 installation
3. Download the windows distribution of Paperdoll Creator
4. Unzip wherever you want
5. Open the directory called 'cuteimp-amd64-3.5' and delete all files except for 'launcher.py'. You can also rename that directory if you want.
6. Open a command line/shell, type 'python' and press Enter. The version displayed in the info text above the python shell should be 3.5.[some number]. Type 'quit()' to close the python shell.
7. Change the current directory of your shell to where 'launcher.py' is.
8. Type 'python launcher.py' and press Enter to start Paperdoll Creator. *fingers crossed*