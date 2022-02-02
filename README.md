# run_escape
## We can't all be zezima.

![screen](https://github.com/cschlisner/run_escape/blob/main/screen.PNG)

an old school runescape bot using [lackey](https://github.com/glitchassassin/lackey) 

This is a tool to play oldschool runescape in a passive manner, I'm sure there are better bots out there if you're looking to make serious money. 

This program will use the default Old School RuneScape window (must be in default 831x775 resolution)* and control it in the background on windows (although the window must be visible). 

On Linux/MacOs** it will control it using the users mouse in the foreground until I figure out a way to do window communication for those platforms.***

*the images should technically work for other resolutions but has not been tested

**completely untested currently but it should work -- there is a seperate environment for each OS

*** If you can implement this then you'd just need to extend the RSEnv class in botenv.py.

## usage:
>$ python3 bot.py [-h] [-p PATH] [-r RESOURCES] [-i ITERATIONS] operation location

## examples:
>$ python bot.py mine alkharid -r gold,mithril,iron
>
>$ python bot.py alchemy varrock -r runepick
>
>$ python bot.py superheat alkharid -r iron

## supported locations (req. images captured for bank, bankbooths, etc):
> alkharid

> mineguild

> west lumbridge (wlumbridge)

> varrock

> GE

## supported resources:

> iron

> coal

> steel

> mithril

> gold

> iron>plate

> iron>platelegs

> steel>platelegs

> steel>platebody



## supported operations:

### mine
> will visit each location map found in /images/$location/$resource-\*map\*.\* (a screenshot of the specific mining area for a group of rocks)

>for each location it will look at the images in /images/$location/#$resource-$resourcemapname/ (will autocreate the directory on the fly for new locations/maps) for any images matching \*ore\*.\*

>until the users inventory is full it will mine each location for each ore set and then **follow()** a path defined by /paths/$location_$resource.json back to the nearest bank. If iterations is None or > 0 then it will travel back to the first mining map location on beginning the operation again. 

>it will repeat the mining process for each supplied resource type while the inventory is not full

>if only one resource and resource location is supplied, it will switch worlds if a matching /images/$location/$resource-depleted\*.\* image is seen

>the program will automatically save the order of ores found in a map so it doesn't need to re-search all ore images at each resource location. (it will automatically update the map if it misses an ore image previously found there)

### alchemy
> will open the users bank, retireve nature runes, the supplied **$resource(s)**, perform High Alchemy, reopen the bank deposit all items

> this process will repeat until $iterations is met or the user runs out of nature runes ore resources

### superheat
> will open the users bank, retireve nature runes, the required resource(s) for the supplied bar type, perform Super Heat on all the ores, reopen the bank deposit all items

> this process will repeat until **$iterations** is met or the user runs out of nature runes or resources

### smith
> resources must be in the form $resourceType>$product (e.g. *bot.py smith varrock -r adamant>plates*)

> will open the users bank, retireve a hammer and the supplied resource bar type, run to the nearest anvil, smith the supplied **$product** type, run back to the bank, reopen the bank deposit all items

> this process will repeat until **$iterations** is met or the user runs out of **$resource** bars


# notes on image format

>Upon searching for an image for a new location/resource/etc the program will autocreate the directory structure it expects to find the image in. use the filename format printed to the console to name the image. the filename can end in anything as long as it contains the text expected by the program. DO NOT USE "_" in filenames as they are treated as directory chars internally for finding images. 

>Images must be taken when the camera is oriented north (by clicking the compass) and positioned as far up as possible (hold the up arrow key). 

>If an image contains "$resource-map" then the program will create a directory called "#$resource-map/" is the appropriate location directory. The resource gathering commands (mine, cut, etc.) will then search for all resource images found in this directory upon locating and moving to the "$resource-map" image.

>The trailing name of an order matters, and performance can be changed depending on the image order. For instance: images named coalore0.png, coalore1.png,, coalore2.png, will be searched for in that order -- but simply renaming the images will change the order in which they are searched for, and newly added images will automatically be included in the search. This means copying the image named 'coalore1.png' and renaming the copy 'coalore4.png' will effectively create a loop in the search algorithm between the resources. 
