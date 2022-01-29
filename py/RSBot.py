import json
from operator import inv
import re
from lackey import *
from keyboard import mouse
from botenv import *
from datetime import datetime
import random as rand

def is_mouse_down():
   key_code = win32con.VK_LBUTTON
   state = win32api.GetAsyncKeyState(key_code)
   return state != 0
def is_rmouse_down():
   key_code = win32con.VK_RBUTTON
   state = win32api.GetAsyncKeyState(key_code)
   return state != 0
def is_q_down():
   key_code = 0x51
   state = win32api.GetAsyncKeyState(key_code)
   return state != 0

class RSBot:
    def __init__(self):
        self.env = getEnv()
        self.env.log("RSBot __init__()")    
        self.scrollpos = -1
        self.amtMined = 0
        self.mmap = None
        self.defSim = 0.8
        self.running=False
        self.inv_full = False

    def login(self):
        # detect / handle self.env.login 
        ret = self.env.exists("disconnected")
        if ret:
            self.env.click(ret)
        logIn = self.env.existsAny("loginscr")
        if logIn:
            self.env.info("login detected")
            logIn.highlight(1)
            logIn.click()
            user = self.env.existsAny("user")
            if user:
                user.highlight(1)
                user.click()
                user.click()
                self.env.info("entering username")
                type("")
            passWd = self.env.existsAny("pass")
            if passWd:
                passWd.highlight(1)
                passWd.click()
                self.env.info("entering password")
                type("")
                lginBtn = self.env.existsAny("loginbtn")
                if lginBtn:
                    self.env.info("logging in")
                    lginBtn.click()
                    lginBtnTwo = self.env.wait("nextloginbtn", 10)
                    if lginBtnTwo:
                        lginBtnTwo.click()
                        return
            self.env.error("Could not complete login.")
        else:
            self.env.info("No login present.")
        
        
    def worldSwitch(self):
        self.env.info("Switching Worlds...")
        self.env.logout = self.env.existsAny("logoutbtn")
        if self.env.logout:
            self.env.click(self.env.logout)
            mouse.move(0, -200, absolute=False)
            worldSwitchBtn = self.env.exists("worldswitch")
            if worldSwitchBtn:
                self.env.click(worldSwitchBtn)
            freeworld = None
            if self.scrollpos < 0:
                self.env.scroll(-100)
                self.scrollpos = 0
            while freeworld is None:
                self.env.scroll(-5)
                self.scrollpos += 5
                x = self.env.exists("scrollbottom")
                if x and x.getScore() > 0.98:
                    self.env.log("scroll bottom")
                    self.env.scroll(30)
                    self.scrollpos = 0
                freeworld = self.env.exists("freeworld")
            if freeworld.getScore() >= 0.95:
                inventory = self.env.exists("inventory")
                self.env.click(freeworld)
                freeworld.highlight(1)
                self.env.write("green:wave:ayylmao")
                if inventory:
                    self.env.click(inventory)
        sleep(1.5)
        self.env.write("\n")      

    def reorient(self):
        self.env.info("Reorienting camera")
        Settings.MinSimilarity = 0.5
        self.env.click(self.env.existsAny("compass"))
        Settings.MinSimilarity = self.defSim
        self.env.keyDown(Key.UP)
        sleep(2)
        self.env.keyUp(Key.UP)
        self.env.scroll(100)

    def getMiniMap(self):
        d = 200
        self.mmap = self.env.wait("compass")
        if self.mmap:
            self.mmap.setW(d)
            self.mmap.setH(d)
        return self.mmap      

    def locate(self, location, resources):
        self.env.logger.incIndent("locate")
        mmap = self.getMiniMap()
        if mmap:
            self.env.info("determining location...")
            if self.env.existsAny("bankicon", reg=mmap, sim=0.5):
                self.env.info("found bank.")
                if self.gotoBank(location, resources):
                    self.env.info("moving to: %s %s"%(location, resources))
                    self.follow(location, resources, reverse=True)
        
        nl = self.env.existsAny("%s_%s_map"%(location, resources[0]), self.getMiniMap(), sim=0.6)
    
        timeout = 10
        while nl is None and timeout > 0:
            maplocators = self.env.existsAny("%s_%s_locator"%(location, resources[0]), self.getMiniMap(), sim=0.5)
            if maplocators:
                self.env.warn("moving to locator: %s"%maplocators)
                self.env.click(maplocators)
                maplocators.highlight(8 if self.running else 15)
            nl = self.env.existsAny("%s_%s_map"%(location, resources[0]), self.getMiniMap(), sim=0.5)
            timeout -= 1
        if nl:
            self.env.info("Found location: %s"%nl)
            self.env.click(nl)
            nl.highlight(True, 10, "green")
            self.env.logger.decIndent()
            return True
        self.env.logger.decIndent()
        return False

    def talk(self, responseType):
        return ""
        text = "\n\n"+""
        if responseType == "invfull":
            text = rand.choice(["She's all full matey", "Im about to bust a load"])
        elif responseType == "bank":
            text = rand.choice(["big d coming through", "Im about to bust a load into my bank account", "time to make some money"])
        elif responseType == "mining":
            text = rand.choice(['aw yis muthaflippin ore', 'thats IRONic', 'ayy lmao', 'meme doot danks', 'beautiful day eh mate'])
        fmt = "%s:%s:"%(rand.choice(['glow1', 'glow2', 'glow3', 'flash1', 'flash2', 'flash3']), 
                        rand.choice(['wave', 'wave2', 'scroll', 'slide', 'shake']))
        return text+"\n"

    def toggleRun(self):
        # click run toggle if run energy is full
        if self.env.existsAny("runtoggled", sim=0.90) is None:
            runbtn = self.env.exists("runfull")
            if runbtn:
                self.env.log("toggling run")
                runbtn.highlight(1)
                self.env.click(runbtn)
                self.running = True
            else:
                if self.env.exists("runempty", sim=0.85):
                    self.env.log("run empty")
                    self.running = False
        else: self.running = True

    def recordPath(self, fname):
        self.env.error("RECORDING PATH (%s). RIGHTCLICK TO STOP."%fname)

        if (not os.path.exists("paths/")):
            os.mkdir("paths/")
        with open(fname, "w+") as recf:
            recf.write("{\n\t\"dir\":\"north\",\n\t\"path\": [\n\t\t")
            lastclickt = datetime.now()
            back_arr = False
            nclicks = 0
            while (True):
                if is_rmouse_down():
                    recf.write("\n\t]\n}")
                    return
                if win32api.GetAsyncKeyState(ord('B')):
                    if (not back_arr): 
                        back_arr = True
                        recf.write("\n\t],\n\t\"pathb\": [\n\t\t")
                if (is_mouse_down()):
                    nclicks += 1
                    timediff = int((datetime.now() - lastclickt).total_seconds() * 1000)
                    lastclickt = datetime.now()
                    cp = win32api.GetCursorPos()
                    pathstep = "%s,%s,%s"%(cp[0] - self.env.window.getX(), cp[1]- self.env.window.getY(), timediff)
                    if (nclicks > 1): # don't write the first one 
                        self.env.info("recording: %s"%pathstep)
                        if (nclicks > 2):
                            recf.write(",\n\t\t")
                        recf.write("\"%s\""%pathstep)
                    time.sleep(2)

    def follow(self,  location, resources, reverse=False):
        resource = resources
        if type_(resources) == list:
            resource = resources[0]
        # self.reorient()
        # self.env.scroll(-33)
        pathf = "paths/%s_%s%s.json"%(location, resource, "_frombank" if reverse else "")
        if not os.path.exists(pathf):
            if platform.system() == "Windows":
                recordpath = popAsk("Path '%s' not found. Record path? (make sure run is disabled)"%pathf, title="Record %s"%pathf)
                if recordpath:
                    self.recordPath(pathf)
                    return
            else: self.env.error("path '%s' not found. Please record path and restart.")
        
        self.running = self.env.existsAny("runtoggled", sim=0.9)
        with open(pathf) as pathfile:
            path = json.load(pathfile)
            self.env.warn("FOLLOWING PATH: '%s'\n%s"%(pathf, json.dumps(path, indent=2)))
            for step in path['path']:
                x, y, t = list(map(int, step.split(",")))
                t = t * 0.5 if self.running else t
                xx = x+self.env.window.getX()
                yy = y+self.env.window.getY()
                self.env.log("%s (%sms)"%("running" if self.running else "walking", t))
                sleep(int(t / 1000) + 1)
                self.env.log("clicking (%s, %s)"%(x, y))
                
                self.env.clickLoc(xx,yy) if not self.env.banking else self.env.dclickLoc(xx, yy)
                if location != "superheat":
                    self.toggleRun()

    def getFromBank(self, resources, noted=False):
        self.env.banking = True
        bankwindow = self.env.exists("bankwindow")
        orign = bankwindow.getBottomLeft()
        bankwindow.highlight(1)
        bankwindow.setW(420)
        bankwindow.setH(500)
        bankwindow.setY(orign.y-500)
        bankwindow.highlight(True, 1, "green")
        bankBtn = self.env.exists("withdrawall")
        if bankBtn:
            self.env.click(bankBtn)
            sleep(1)
        else:
            self.env.warn("Did not see withdrawall")
        if noted:
            bankBtn = self.env.exists("withdrawasnote")
            if bankBtn:
                self.env.click(bankBtn)
                sleep(1)
            else:
                self.env.warn("Did not see withdrawasnote")
        for resource in resources:
            bankItem = self.env.wait("%s_bank"%resource, time=1, reg=bankwindow, sim=0.65)
            if bankItem:
                self.env.info("Found %s in bank"%resource)
                self.env.click(bankItem)
                sleep(1)
            else:
                self.env.warn("Did not see %s in bank."%resource)
                return False
        x = self.env.wait("closebankbtn")
        if x:
            if self.env.lbdown:
                c = x.getCenter()
                self.env.lbdown(c.x, c.y)
            else: self.env.click(x)
        else:
            self.env.error("COULD NOT CLOSE BANK??")
        self.env.banking = False
    def bank(self, gotobooth=False):
        booth = self.env.wait("boothbank", sim=0.8)
        if booth:
            self.env.log("found bank booth")
            self.env.click(booth)
            self.env.dclick(booth)
            x = self.env.wait("depositbtn")
            if x:
                self.env.log("depositing")
                self.env.click(x)
                self.inv_full = False
                self.env.logger.decIndent()
                return True
        else:
            self.env.error("could not find bankbooth")
        return False

    def gotoBank(self, location, resources):
        self.env.warn("Inventory status: %s"%self.inv_full)
        if not self.inv_full and self.amtMined > 0 and self.env.wait("boothbank_%s"%location, sim=0.8):
            return True
        self.env.logger.incIndent("bank")
        map = self.getMiniMap()
        if map:
            map.highlight(1)
            bankicon = self.env.existsAny("bankicon", map, sim=0.6)
            if bankicon:
                self.env.info("Moving to bank")
                self.env.click(bankicon)
                bankicon.highlight(8)
                self.env.write(self.talk("bank")+"\n")
                if self.env.existsAny("emptyinventory", sim=0.98) is None:
                    self.env.log("Inventory not empty. Depositing....")
                    return self.bank()
                            
                else: 
                    self.env.log("Inventory empty.")
                    self.env.logger.decIndent()
                    return True
            else:
                self.env.error("could not locate bank")
        else: 
            self.env.error("could not locate map")
        self.env.logger.decIndent()
        return False

    def oreDepletedCB(self, ore):
        self.env.warn("ORE DEPLETED: %s"%ore)

    def getMapping(self, location, resource):
        mapping = {}
        if (not os.path.exists("maps/")):
            os.mkdir("maps/")
        pathf = "maps/%s_%s.json"%(location, resource)
        if not os.path.exists(pathf):
            self.env.warn("Mapping '%s' not found."%pathf)
        else: 
            with open(pathf) as pathfile:
                mapping = json.load(pathfile)
        return mapping

    def saveMapping(self, location, resource, mapping):
        pathf = "maps/%s_%s.json"%(location, resource)
        if not os.path.exists(pathf):
            self.env.warn("Creating mapping: '%s'."%pathf)
        else:
            self.env.warn("Overwriting mapping: '%s'."%pathf)
        with open(pathf, "w+") as mapfile:
            mapfile.write(json.dumps(mapping, indent=2))

    ore_timeout = {
        'iron': 1,
    }

    # mine matching oretype for this specific resource location (X_Y_map.PNG) and return inventory full status
    def mineLocation(self, location, resourceLocation, resource): 

        # try to load precalced image mapping for this location
        resourceMap = self.getMapping(location, resource)
        ores = []
        foundOres = []
        inv_full = self.env.exists("fullinventory", sim=0.85)
        if inv_full:
            self.env.logh("Inventory is full. Making bank run.")
            self.inv_full = True
            self.env.write(self.talk("invfull"))
            # go to bank and back
            self.follow(location, resource)
            self.gotoBank(location, resource)
            return True
        oreSet = getImageSet("%s_ore*"%(resource)) 
        overwrite = resourceLocation not in resourceMap or len(resourceMap[resourceLocation]) <= 1
        if overwrite:
            # look for any matching ore if none were cached for this resource map
            ores = oreSet
        else:
            ores = resourceMap[resourceLocation]

        self.env.info("searching for: %s"%(ores))
        self.oresMissed = 0
        for oi, oref in enumerate(ores):


            oreFull = self.env.exists(oref, sim=0.93)
            
            oreDepleted = None
            if oreFull is None: 
                self.env.logh("didn't see ore '%s'."%oref)
                if ores != oreSet and oi > 0: # dont replace first image
                    self.env.logh("looking for replacement....")
                    for ore_f in oreSet:
                        if ore_f not in ores:
                            oreFull = self.env.exists(ore_f, sim=0.93)
                            if oreFull: 
                                self.env.logh("Found replacement image: %s"%ore_f)
                                oref = ore_f
                                break
                    if oreFull is None: 
                        self.env.logh("Could not find replacement image.")

            if oreFull:
                foundOres.append(oref)
                self.env.logh("%s ore spotted: %s"%(resource, foundOres))
                self.env.click(oreFull)
                oreFull.highlight(1)
                oreFull.onChange(20, self.oreDepletedCB)
                
                minedOre = self.env.wait("managed2mine",1)
                if minedOre is None:
                    noore = self.env.existsAny("noore")
                    if noore is None:
                        pickswing = self.env.exists("pickswing")
                        if pickswing is not None:
                            self.env.logh("Pick swung.")
                            timeout = 0
                            minedOre = None
                            while minedOre is None and inv_full is None and timeout < 30:
                                self.env.log("Mining (%s)..."%timeout)
                                minedOre = self.env.exists("managed2mine")
                                timeout += 1
                                if minedOre:
                                    self.amtMined += 1
                                    self.env.info("Managed to mine some %s. (%s)"%(resource, self.amtMined))
                    else: 
                        self.env.warn("There's no ore here!!!1!1! >:(")
                        self.oresMissed += 1
                else:
                    self.amtMined += 1
                    self.env.info("Managed to mine some %s. (%s)"%(resource, self.amtMined))
               
        if self.oresMissed > foundOres: 
            self.worldSwitch() # switch worlds if we missed a bunch of ores
        if len(ores) < 3 or overwrite:
            self.env.log("waiting for ore respawn")
            sleep(self.ore_timeout[resource])
        
        if overwrite or len(foundOres) >= len(resourceMap[resourceLocation]):
            resourceMap[resourceLocation] = foundOres
            self.env.log("saving resource mapping: \n%s"%json.dumps(resourceMap[resourceLocation], indent=1))
            self.saveMapping(location, resource, resourceMap)
            if foundOres == []:
                self.env.error("no ore found. looking for location.")
                raise Exception("no ore lol")
        else:
            self.env.warn("NOT ALL ORES FOUND. REMOVING RESOURCE MAPPING FOR %s in '%s_%s.json'...."%(resourceLocation, location, resource))
            resourceMap[resourceLocation] = [ores[0]]
            self.saveMapping(location, resource, resourceMap)
        return inv_full        
   
    # mine at specified location
    def mine(self, location, resources):
        # locate self and navigate to mining area
        if not self.locate(location, resources):
            self.env.error("could not locate")
            return
        # self.reorient()

        #load resource identifier images
        inv_full = self.env.exists("fullinventory")
        moveTo = True
        lostLMAO = False
        self.env.warn("Mining resources: %s"%resources)
        self.env.write(self.talk("mining")+"\n")
        locmisses = 0
        while inv_full is None and not lostLMAO:
            if len(resources) > 1 or locmisses > 3:
                lostLMAO = True 
            for r_ind, resource in enumerate(resources):
                self.env.logger.incIndent("%s"%(resource))
                self.env.warn("mining %s"%resource)
                curResource = resource
                # visit each location for resource
                mapfile = "%s_%s_map"%(location, resource)
                r_locs = getImageSet(mapfile)
                if len(r_locs) == 0:
                    self.env.error("Could not find any matching images for %s"%mapfile)
                
                if len(resources) > 1 and resource != resources[r_ind-1]: # don't go to the first location again after locating
                    maplocators = getImageSet("%s_%s_locator"%(location, resource))
                    for ml in maplocators:
                        locatorFound=self.env.exists(ml, self.getMiniMap(), sim=0.5)
                        if locatorFound:
                            self.env.warn("moving to locator: %s"%ml)
                            self.env.click(locatorFound)
                            self.toggleRun()
                            locatorFound.highlight(4)

                for l_ind, curLoc in enumerate(r_locs):
                    if len(r_locs) > 1 or len(resources) > 1:
                        if not moveTo:
                            nl = self.env.wait(curLoc, time=8 if self.running else 15, reg=self.getMiniMap(), sim=0.6)
                            if nl:
                                lostLMAO = False
                                self.env.warn("Moving to location: %s"%curLoc)
                                self.env.click(nl)
                                self.env.write(self.talk("mining")+"\n")
                                nl.highlight(True, 6 if self.running else 10, "green")
                            else:
                                self.env.warn("Did not see location")
                    self.env.logger.incIndent(curLoc[curLoc.index("map"):-4])
                    # mine all ores in this location map
                    try:
                        inv_full = self.mineLocation(location, curLoc, resource)
                    except:
                        locmisses += 1
                    if inv_full:
                        break
                    moveTo = False
                    self.env.logger.decIndent()
                self.env.logger.decIndent()
                if inv_full:
                    break
                # if only mining one location check if it has depleted and switch worlds
                if len(r_locs) == 1 and len(resources) == 1:
                    oreDepleted = self.env.exists("%s_%s_depleted"%(location, resource))
                    if oreDepleted:
                        self.env.logh("ORE DEPLETED.")
                        self.worldSwitch()
                        self.env.click(self.env.exists("inventory"))
            if lostLMAO:
                self.env.error("I'm lost! lmao")
        self.env.log("Trip complete! (%s)"%self.amtMined)
        return True
    
    def woodcut(self):
        pass

    def firemake(self):
        pass


    def superheat(self, location, resources):
        atbank = False
        gotobooth=self.env.exists("closebankbtn") is None
        if gotobooth or self.env.existsAny("boothbank") is None:
            atBank = self.gotoBank(location, resources)
        elif gotobooth:
            atBank = self.bank(True)
        else: 
            atBank = self.bank()
        if not atBank:
            self.env.error("Not at bank booth / couldn't withdraw all items")
            return
        bankitems = ["natrunes"]
        bankitems.extend(resources)
        self.getFromBank(bankitems)

        resource = resources[0]
        invbtn = self.env.wait("inventory", sim=0.8)
        if invbtn:
            self.env.click(invbtn)

        inventory = self.env.wait("invbar", sim=0.6)
        if inventory:
            inventory.setH(300)
            inventory.highlight(1)
            oreinv = self.env.exists("invore_%s"%resource, inventory)
            while oreinv:
                spellbk = self.env.existsAny("spellbook", sim=0.9)
                if spellbk:
                    self.env.click(spellbk)
                    superh = self.env.exists("superheat", sim=0.9)
                    if superh:
                        self.env.click(superh)
                        oreinv = self.env.wait("invore_%s"%resource, time=1, reg=inventory)
                        if oreinv:
                            self.env.click(oreinv)
                        sleep(0.4)
                    else: 
                        self.env.warn("Did not find superheat. Out of Nats?")
                        return False
        return True
                

    def alchemy(self, location, resources):
        atbank = False
        if self.env.existsAny("boothbank") is None:
            atBank = self.gotoBank(location, resources)
        else: 
            atBank = self.bank()
        if not atBank:
            self.env.error("Not at bank booth")
            return True
        bankitems = ["natrunes"]
        bankitems.extend(resources)
        self.getFromBank(bankitems, noted=True)

        resource = resources[0]
        invbtn = self.env.wait("inventory", sim=0.8)
        if invbtn:
            self.env.click(invbtn)

        inventory = self.env.wait("invbar", sim=0.6)
        if inventory:
            inventory.setH(300)
            inventory.highlight(1)
            emptyinv = self.env.wait("alc_invempty", time=1, reg=inventory)
            while emptyinv is None:
                spellbk = self.env.existsAny("spellbook", sim=0.9)
                if spellbk:
                    self.env.click(spellbk)
                    spell = self.env.exists("highalchemy", sim=0.9)
                    if spell:
                        self.env.click(spell)
                        emptyinv = self.env.exists("alc_invempty", reg=inventory)
                        if emptyinv is None:
                            alc_item = self.env.exists("%s_noted"%resource)
                            if alc_item:
                                self.env.click(alc_item)
                            else:
                                self.env.warn("did not see item")
                                return True
                    else: 
                        self.env.warn("Did not find spell. Out of Nats?")
                        return False
        return True

    # do ($operation for $resource in $location) * $iterations 

    def run(self, operation, location, resources=None, iterations=None):
        xpmap = {
            'iron': 35
        }
        operationMap = {
            "mine" : self.mine,
            "woodcut": self.woodcut, 
            "firemake": self.firemake, 
            "follow": self.follow,
            "superheat": self.superheat,
            "alchemy": self.alchemy,
            "bank": self.gotoBank,
        }

        if operation not in operationMap:
            self.env.error("operation '%s' not found", operation)

        self.env.write("\n") #clear input
        self.env.logger.incIndent("%s"%location)

        i = 0
        while (iterations is None  or i < iterations):
            i += 1

            ###### see if user terminated app
            # if (platform.system() == "Windows"):
            #     if win32api.GetAsyncKeyState(ord('W')):
            #         sys.exit(0)

            # make sure we are self.env.logged in, window visible etc
            PlatformManager.focusWindow(self.env.rswindow)

            if self.env.exists("minimapglobe") is None:
                self.login()
                self.reorient()
            
            # do op
            start_t = datetime.now()
            self.env.warn("Starting: %s %s %s %s"%(operation, location, resources, start_t))

            self.env.logger.incIndent("%s"%operation)
            ret = operationMap[operation](location, resources)
            self.env.logger.decIndent(2)

            start_t = int((datetime.now() - start_t).total_seconds())
            self.env.warn("Operation %s %s %s finished %s (%s) in %ss"%(operation, location, resources, "succesfully" if ret else "unsuccessfully", i, start_t))
            self.env.warn("Mined: (%s) -> %s"%(self.amtMined, "?" if resources[0] not in xpmap else self.amtMined * xpmap[resources[0]]))
            if not ret:
                break

        self.env.logger.decIndent()

        self.env.error("exiting..")
