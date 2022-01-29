
import os, platform
from turtle import screensize
from lackey import *
from numpy import char
import win32api, win32con, win32gui
from ctypes import windll
from keyboard import mouse
from loggr import *
import glob

# determine current environment and return appropriate environment class
def getEnv():
    envname = platform.system()
    if envname == "Windows":
        return winEnv()
    return None

# ImageMissingHandler
def imageMissing(event):
    ColLog().red("***** Missing image: %s"%event)
    return

def getImageSet(imgBaseName):
    imgPattern = "%s%s*"%(getImagePath()[1], imgBaseName)
    # self.log(imgPattern)
    glb = glob.glob(imgPattern)
    return list(map(os.path.basename, glb))
    
# Environment classes -- handle all communication between bot and runescape window
class RSenv:
    def __init__(self):
        self.banking = False

        #debug self.logging settings
        self.logger = ColLog()
        Debug.setLogger(self.logger)
        Debug.setLoggerInfo("printh")
        Debug.setLoggerAction("printh")

        ## get OS name
        self.warn("Running in "+platform.system())

        ## find the runescape window
        self.rswindow = PlatformManager.getWindowByTitle("RuneScape")
        if self.rswindow:
            PlatformManager.focusWindow(self.rswindow)
            sleep(1)
            self.window = Region(PlatformManager.getWindowRect(self.rswindow))
            self.warn("Found Runescape window: %s %s %s %s"%(self.window.getTuple()))
            self.warn("%s"%self.window.getAutoWaitTimeout())
            self.window.setFindFailedResponse(Region.SKIP)
            self.window.setImageMissingHandler(imageMissing)

            ## image paths (per resolution)
            imgdir = "images/"
            imgresdir = imgdir+"%s-%s/"%(self.window.w, self.window.h)
            print("making img dir: %s"%(imgresdir))
            
            if not os.path.isdir(imgresdir):
                os.makedirs(imgresdir)
            # addImagePath(imgdir)
            addImagePath(imgresdir)
            # for f in os.listdir(imgdir):
            #     if os.path.isdir(imgdir+f):
            #         addImagePath(imgdir+f+"/")
            self.warn("using imagepath: %s"%getImagePath())

            # Debug.on(1)
        else:
            self.error("did not find Runescape window")
            exit(0)

    def log(self, msg):
        self.logger.cyan(msg)

    def logh(self, msg):
        self.logger.blue(msg)

    def info(self, msg):
        self.logger.green(msg)

    def warn(self, msg):
        self.logger.yellow(msg)

    def error(self, msg):
        self.logger.red(msg)

    def click(self, region):
        region.click()

    def dclick(self, region):
        region.click()
    
    def clickLoc(self, x, y):
        self.window.click(Location(x, y))
    def dclickLoc(self, x, y):
        self.clickLoc(x, y)
    
    # wait for a range of possibilities for a given imagename
    def wait(self, img, time=None, reg=None, sim=None):
        if reg is None:
            reg = self.window
        if sim is None:
            sim = Settings.MinSimilarity
        defs = Settings.MinSimilarity
        Settings.MinSimilarity = sim
        imgs = getImageSet(img)
        self.log("waiting for one of %s"%imgs)
        if len(imgs) == 0:
            self.error("did not find any matching images for: "+img)
        for i in imgs:
            try:
                x = reg.wait(i, time)
            except:
                continue
            if x is not None:
                Settings.MinSimilarity = defs
                return x
        Settings.MinSimilarity = defs

        return None

    # for quickly testing for one image
    def exists(self, img, reg=None, sim=None):
        if reg is None:
            reg = self.window
        if sim is None:
            sim = Settings.MinSimilarity
        defs = Settings.MinSimilarity
        Settings.MinSimilarity = sim
        defAWT = reg.getAutoWaitTimeout()
        imgs = getImageSet(img)
        imgf = None
        if len(imgs) == 0:
            self.error("could not find matching images for: '%s'"%img)
            return None
        else:
            imgf = imgs[0]
        self.info("looking for %s"%img)
        reg.setAutoWaitTimeout(0)
        x = reg.exists(imgf)
        reg.setAutoWaitTimeout(defAWT)
        Settings.MinSimilarity = defs
        return x

    def existsAny(self, img, reg=None, sim=None):
        if reg is None:
            reg = self.window
        if sim is None:
            sim = Settings.MinSimilarity
        defs = Settings.MinSimilarity
        Settings.MinSimilarity = sim
        defAWT = reg.getAutoWaitTimeout()
        imgs = getImageSet(img)
        self.info("looking for one of %s"%imgs)
        if len(imgs) == 0:
            self.error("did not find any matching images for: "+img)
        reg.setAutoWaitTimeout(0)
        x = None
        for i in imgs:
            try:
                x = reg.exists(i)
            except:
                continue
            if x is not None:
                break
        reg.setAutoWaitTimeout(defAWT)
        Settings.MinSimilarity = defs
        return x

    def keyDown(self, k):
        self.window.keyDown(k)
    
    def keyUp(self, k):
        self.window.keyUp(k)

    def scroll(self, amt):
        cloc = self.window.getCenter()
        mousepos = mouse.get_position()
        mouse.move(cloc.getX(), cloc.getY())
        sleep(1)
        mouse.wheel(amt)
        mouse.move(mousepos[0], mousepos[1])

    def write(self, text):
        text.replace("\n", Key.ENTER)
        self.window.type(text)

class winEnv(RSenv):
    def __init__(self):
        super().__init__()
        self.hWnd1 = win32gui.FindWindow (None, "Old School RuneScape")
        self.hwnds = [self.hWnd1]
        win32gui.EnumChildWindows(self.hWnd1, self.callback, self.hwnds)
        self.rswnd = self.hwnds[-1]
        self.warn("%s -> %s -> %s(rswnd)"%(self.hWnd1, self.hwnds, self.rswnd))
        self.tested = False

    def callback(self, hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            self.warn("RSWindow: %s %s %s"%(hwnd, win32gui.GetClassName(hwnd), win32gui.GetWindowPlacement(hwnd)))
            hwnds.append(hwnd)
        return True

    def click(self, region):
        coords = region.getCenter()
        self.clickLoc(coords.x, coords.y) if not self.banking else self.dclickLoc(coords.x, coords.y)

    def lbdown(self, x, y):
        lParam = win32api.MAKELONG(x, y)
        win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDOWN, win32con.VK_LBUTTON, lParam)

    def dclick(self, region):
        coords = region.getCenter()
        self.dclickLoc(coords.x, coords.y)

    def clickLocMine(self, x, y):
        # self.log("clicking in background %s,%s"%(x,y))
        lParam = win32api.MAKELONG(x, y)
       
        win32gui.PostMessage(self.rswnd, win32con.WM_MOUSEMOVE, None, lParam)
        win32gui.PostMessage(self.rswnd, win32con.WM_MOUSEHOVER, None, lParam)
        win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDOWN, win32con.VK_LBUTTON, lParam)
        sleep(0.04)
        win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDOWN, win32con.VK_LBUTTON, lParam)
        sleep(0.4)
        win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONUP, win32con.VK_LBUTTON, lParam)
        sleep(0.04)
        win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONUP, win32con.VK_LBUTTON, lParam)
        # win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDBLCLK, None, lParam)
    
    def clickLoc(self, x, y):
        # self.log("clicking in background %s,%s"%(x,y))
        lParam = win32api.MAKELONG(x, y)
       
        win32gui.PostMessage(self.rswnd, win32con.WM_MOUSEMOVE, None, lParam)
        win32gui.PostMessage(self.rswnd, win32con.WM_MOUSEHOVER, None, lParam)
        # win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDOWN, win32con.VK_LBUTTON, lParam)
        sleep(0.04)
        win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDOWN, win32con.VK_LBUTTON, lParam)
        sleep(0.4)
        win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONUP, win32con.VK_LBUTTON, lParam)
        sleep(0.04)
        win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONUP, win32con.VK_LBUTTON, lParam)
        # win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDBLCLK, None, lParam)

    def dclickLoc(self, x, y):
         # self.log("clicking in background %s,%s"%(x,y))
        lParam = win32api.MAKELONG(x, y)
        # clickarea = self.window.offset(Location(y-self.window.getX()-10, y-self.window.getY()-10), dy=0)
        # clickarea.setW(10)
        # clickarea.setH(10)
        # clickarea.highlight(3)
        for i in range(3):
            # win32gui.PostMessage(self.rswnd, win32con.WM_MOUSEMOVE, None, lParam)
            win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDOWN, win32con.VK_LBUTTON, lParam)
            self.warn("mousedown (%s,%s)"%(x,y))
            sleep(0.01)
            # self.warn("sleeping")
            self.warn("releasing%s"%i)
            win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONUP, win32con.VK_LBUTTON, lParam)
        # sleep(4)
        # self.warn("releasing2")
        # win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONUP, None, lParam)
        # win32gui.PostMessage(self.rswnd, win32con.WM_LBUTTONDBLCLK, None, lParam)

    def keyUp(self, k):
        if k == Key.UP:
            k = win32con.VK_UP
        elif k == Key.DOWN:
            k = win32con.VK_DOWN
        elif k == Key.LEFT:
            k = win32con.VK_LEFT
        elif k == Key.RIGHT:
            k = win32con.VK_RIGHT
        else: 
            return
        win32gui.PostMessage(self.rswnd, win32con.WM_KEYDOWN, k, 0)

    def keyDown(self, k):
        if k == Key.UP:
            k = win32con.VK_UP
        elif k == Key.DOWN:
            k = win32con.VK_DOWN
        elif k == Key.LEFT:
            k = win32con.VK_LEFT
        elif k == Key.RIGHT:
            k = win32con.VK_RIGHT
        else: 
            return
        win32gui.PostMessage(self.rswnd, win32con.WM_KEYUP, k, 0)


    def char2key(self, c):
        result = windll.User32.VkKeyScanW(ord(c))
        shift_state = (result & 0xFF00) >> 8
        vk_key = result & 0xFF
        if vk_key == 186:
            vk_key = 58 # get correct ;: char
        return vk_key

    def write(self, text):
        for c in text:
            kc= self.char2key(c)
            win32gui.PostMessage(self.rswnd, win32con.WM_KEYDOWN, kc, 0)
            win32gui.PostMessage(self.rswnd, win32con.WM_KEYUP, None, 0)
            sleep(0.03)
    


    # def scroll(self, amt):
    #     amt *= 10
    #     win32gui.PostMessage(self.rswnd, win32con.SB_VERT, win32con.WM_VSCROLL, amt)
        

