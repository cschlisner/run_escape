from datetime import datetime
from doctest import FAIL_FAST
from importlib.metadata import files
from os import pathsep
import os
from shutil import move
import win32api, win32con, argparse
import time
import math
import sys

from botenv import *
from RSBot import *

# Parse command-line options.
operations = ["mine", "woodcut", "firemake", "follow"]
locations = ["lumbridge", "falador", "alkharid", "varrock"]
resources = ["iron", "tin", "gold", "mithryl"]

parser = argparse.ArgumentParser()
parser.add_argument(
	"operation",
	help="Operation to perform. One of: %s"%operations
)
parser.add_argument(
	"location",
	help="Starting Location. One of: %s"%locations
)
parser.add_argument(
	"-p","--path",
	help="Path file to follow.",
    required=False
)
parser.add_argument(
	"-r","--resource",
	help="Resource to gather. One of: %s"%resources,
    required=False
)
parser.add_argument(
	"-i","--iterations",
	help="Amount of operations to perform",
    required=False
)
parser.add_argument(
	"-o","--output",
	help="Output file for path recording.",
    required=False
)
args = parser.parse_args()


## program start

bot = RSBot()
bot.run(args.operation, args.location, resources=args.resource.split(","), iterations=args.iterations)

