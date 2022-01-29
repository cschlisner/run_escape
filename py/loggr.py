from lackey import *

def fmt(text,colors=[]):
        colCode = "\u001B"
        endCode = "\u001B[0m"
        fmts = colCode+"["
        for i, col in enumerate(colors):
            if col == "red":
                fmts += "31"
            elif col ==  "green":
                fmts += "92"
            elif col ==  "yellow":
                fmts += "93"
            elif col ==  "blue":
                fmts += "94"
            elif col ==  "purple" or col ==  "magenta":
                fmts += "35"
            elif col ==  "cyan":
                fmts += "96"
            elif col ==  "white":
                fmts += "37"
            elif col ==  "grey":
                fmts += "90"
            elif col ==  "bgblack":
                fmts += "40"
            elif col ==  "bgred":
                fmts += "41"
            elif col ==  "bggreen":
                fmts += "42"
            elif col ==  "bgyellow":
                fmts += "43"
            elif col ==  "bgblue":
                fmts += "44"
            elif col ==  "bgpurple" or col ==  "bgmagenta":
                fmts += "45"
            elif col ==  "bgcyan":
                fmts += "46"
            elif col ==  "bgwhite":
                fmts += "47"
            elif col ==  "bold":
                fmts+="1"
            elif col ==  "italics" or  col ==  "italic":
                fmts += "3"
            elif col ==  "underline":
                fmts += "4"
            elif col ==  "strikethrough":
                fmts += "9"
            if (len(colors) > 1 and i < len(colors)-1):
                fmts+=""
        fmts+="m"
        fmts+=text+endCode
        return fmts

class ColLog:
    def __init__(self):
        self.prefix = ""
        self.indent = ""
        self.labels = []
        pass

    def incIndent(self, label):
        # self.indent += "\t"
        self.labels.append(label)
        self.prefix = ":".join(self.labels)+self.indent
    
    def decIndent(self, i=1):
        # self.indent = self.indent[:-2]
        self.labels = self.labels[:-1 * i]
        self.prefix = ":".join(self.labels)+self.indent

    def cyan(self, msg):
        Debug.info(fmt(msg, ["cyan"]))

    def blue(self, msg):
        Debug.info(fmt(msg, ["blue"]))

    def green(self, msg):
        Debug.info(fmt(msg, ["green"]))

    def yellow(self, msg):
        Debug.info(fmt(msg, ["yellow"]))

    def red(self, msg):
        Debug.info(fmt(msg, ["red"]))
    
    def printh(self, msg):
        if "\u001B" in msg:
            print(self.prefix+msg)
        elif "[action]" in msg:
            print(fmt(self.prefix+msg, ["green"]))
        elif "[info] Couldn't find" in msg:
            print(fmt(self.prefix+msg, ["grey"]))
        else:
            print(fmt(self.prefix+msg, ["purple"]))