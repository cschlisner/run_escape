from lackey import *

def fmt(text,colors=[]):
        colCode = "\u001B"
        endCode = "\u001B[0m"
        fmts = colCode+"["
        for i, col in enumerate(colors):
            if col == "red":
                fmts += "31"
            elif col ==  "bred":
                fmts += "92"
            elif col ==  "green":
                fmts += "32"
            elif col ==  "bgreen":
                fmts += "92"
            elif col ==  "yellow":
                fmts += "33"
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
    
    def purple(self, msg):
        Debug.info(fmt(msg, ["purple"]))
    
    def green(self, msg):
        Debug.info(fmt(msg, ["bgreen"]))

    def yellow(self, msg):
        Debug.info(fmt(msg, ["yellow"]))

    def red(self, msg):
        Debug.info(fmt(msg, ["red"]))

    def grey(self, msg):
        Debug.info(fmt(msg, ["grey"]))

    def getScoreColor(self, score):
        if score < 0.3:
            return "bred"
        elif score < 0.5:
            return "yellow"
        elif score < 0.7:
            return "white"
        elif score < 0.9:
            return "cyan"
        else:
            return "bgreen"

    def printh(self, msg):
        if "\u001B" in msg:
            print(self.prefix+msg)
        elif "[action]" in msg:
            print(fmt(self.prefix+msg, ["green"]))
        elif "[info] Couldn't find" in msg:
            print(fmt(self.prefix+"[info] Couldn't find %s"%msg[msg.index("d \'")+3:msg.index("' w")], ['yellow']))
        elif "[info] Found match" in msg:
            # example: [info] Found match for pattern 'images/831-775/inv/highalchemy.PNG' at ( 2149,754) with confidence ( 0.9823780655860901). Target at ( 2166,769)
            score = "%s"%(msg[msg.index("e (")+3:msg.index(". T")-1])
            print(fmt(self.prefix+"[info] Found %s -> "%msg[msg.index("n \'")+3:msg.index("' a")], ["green"])+fmt(score, [self.getScoreColor(float(score))]))
        else:
            print(fmt(self.prefix+msg, ["grey"]))


            