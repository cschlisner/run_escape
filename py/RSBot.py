import json
from textwrap import indent
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

# XP table for different resources/spells
XPTABLE = {
    "iron": 35,
    "alchemy": 65,
    'oresMissed': -35,
    "superheat": 53+12,
}

# tracker for amount of resource types processed
STATS = {
    "mine": {},
    "alchemy": {},
    "superheat": {},
    "cut": {},
    "firemake": {},
    "smith": {},
    "smith": {},
}

ORE_TIMEOUT = {
    'iron': 1,
}


class NoOreException(Exception):
    pass

class RSBot:
    def __init__(self):
        self.env = getEnv()
        self.env.log("RSBot __init__()")    
        self.scrollpos = -1
        self.mmap = None
        self.defSim = 0.8
        self.running=False
        self.inv_full = False
        conf_f = "config.json"
        if not os.path.exists(conf_f):
            self.env.error("config.jspon not found. Creating config template and exiting.")
            with open(conf_f, "w+") as conf:
                conf.write("{\n\t\"login\":{\n\t\t\"user\":\"\",\n\t\t\"pass\":\"\"\n\t}\n}")
            exit(0)
        else:
            with open(conf_f) as config:
                self.conf = json.load(config)
        stat_f = "stats.json"
        if not os.path.exists(stat_f):
            self.stats = STATS
        else:
            with open(stat_f) as stat:
                self.stats = json.load(stat)
        # self.stats = STATS
        statstr = json.dumps(self.stats, indent=2)
        self.env.logh("%s"%statstr)

    def login(self):
        # detect / handle self.env.login 
        ret = self.env.exists("login_disconnected")
        if ret:
            self.env.click(ret)
        logIn = self.env.existsAny("login_loginscr")
        if logIn:
            self.env.info("login detected")
            logIn.highlight(1)
            logIn.click()
            user = self.env.existsAny("login_user")
            if user:
                user.highlight(1)
                user.click()
                user.click()
                self.env.info("entering username")
                type(self.conf['login']['user'])
            passWd = self.env.existsAny("login_pass")
            if passWd:
                passWd.highlight(1)
                passWd.click()
                self.env.info("entering password")
                type(self.conf['login']['pass'])
                lginBtn = self.env.existsAny("login_loginbtn")
                if lginBtn:
                    self.env.info("logging in")
                    lginBtn.click()
                    lginBtnTwo = self.env.wait("login_nextloginbtn", 10)
                    if lginBtnTwo:
                        lginBtnTwo.click()
                        return
            self.env.error("Could not complete login.")
        else:
            self.env.info("No login present.")
        
        
    def worldSwitch(self):
        self.env.info("Switching Worlds...")
        self.env.logout = self.env.existsAny("inv_logoutbtn")
        if self.env.logout:
            self.env.click(self.env.logout)
            mouse.move(0, -200, absolute=False)
            worldSwitchBtn = self.env.exists("inv_worldswitch")
            if worldSwitchBtn:
                self.env.click(worldSwitchBtn)
            freeworld = None
            if self.scrollpos < 0:
                self.env.scroll(-100)
                self.scrollpos = 0
            while freeworld is None:
                self.env.scroll(-5)
                self.scrollpos += 5
                x = self.env.exists("inv_scrollbottom")
                if x and x.getScore() > 0.98:
                    self.env.log("scroll bottom")
                    self.env.scroll(30)
                    self.scrollpos = 0
                freeworld = self.env.exists("inv_freeworld")
            if freeworld.getScore() >= 0.95:
                inventory = self.env.exists("inv_inventorybtn")
                self.env.click(freeworld)
                freeworld.highlight(1)
                if inventory:
                    self.env.click(inventory)
        sleep(1.5)
        self.env.write("\n")  
        self.reorient()    

    def reorient(self):
        self.env.info("Reorienting camera")
        Settings.MinSimilarity = 0.5
        compass = self.env.existsAny("map_compass", sim=0.8)
        if compass:
            self.env.click(compass)
        Settings.MinSimilarity = self.defSim
        self.env.keyDown(Key.UP)
        sleep(2)
        self.env.keyUp(Key.UP)
        self.env.scroll(100)

    def getMiniMap(self):
        d = 200
        self.mmap = self.env.wait("map_compass", sim=0.8)
        if self.mmap:
            self.mmap.setW(d)
            self.mmap.setH(d)
        return self.mmap      

    def locate(self, location, resources):
        self.env.logger.incIndent("locate")
        mmap = self.getMiniMap()
        if mmap:
            self.env.info("determining location...")
            if self.env.existsAny("%s_bankicon"%location, reg=mmap, sim=0.5):
                self.env.info("found bank.")
                if self.gotoBank(location, resources):
                    self.env.info("moving to: %s %s"%(location, resources))
                    self.follow(location, resources, reverse=True)
        
        #tuple
        resource_map = self.env.whichOneOf("%s_%s-map"%(location, resources[0]))
        timeout = 10
        while resource_map is None and timeout > 0:
            maplocators = self.env.existsAny("%s_%s-locator"%(location, resources[0]), self.getMiniMap(), sim=0.65)
            if maplocators:
                self.env.warn("moving to locator: %s"%maplocators)
                self.env.click(maplocators)
                maplocators.highlight(True, 1, "green")
            resource_map = self.env.whichOneOf("%s_%s-map"%(location, resources[0]), wait=3 if self.running else 5, reg=self.getMiniMap(), sim=0.5)
            timeout -= 1
        if resource_map:
            self.env.info("Found location: %s"%resource_map[1])
            self.env.click(resource_map[0])
            resource_map[0].highlight(True, 1, "green")
            self.env.wait("%s_#%s_*ore"%(location, resource_map[1]), 7 if self.running else 10)
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
        if self.env.existsAny("run_toggled", sim=0.85) is None:
            runbtn = self.env.exists("run_full", sim=0.9)
            if runbtn:
                self.env.log("toggling run")
                runbtn.highlight(1)
                self.env.click(runbtn)
                self.running = True
            else:
                if self.env.exists("run_empty", sim=0.85):
                    self.env.log("run empty")
                    self.running = False
        else: self.running = True

    def recordPath(self, fname):
        self.env.error("RECORDING PATH (%s). RIGHTCLICK TO STOP."%fname)

        if (not os.path.exists("paths/")):
            os.mkdir("paths/")
        with open(fname, "w+") as recf:
            recf.write("{\n\t\"path\": [\n\t\t")
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

    def follow(self,  location, resources, reverse=False, abs=False):
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
        
        self.running = self.env.existsAny("run_toggled", sim=0.9)
        with open(pathf) as pathfile:
            path = json.load(pathfile)
            self.env.logp("FOLLOWING PATH: '%s'\n%s"%(pathf, json.dumps(path, indent=2)))
            for step in path['path']:
                x, y, t = list(map(int, step.split(",")))
                t = t if abs else t * 0.5 if self.running else t
                xx = x+self.env.window.getX()
                yy = y+self.env.window.getY()
                self.env.logh("%s (%sms)"%("running" if self.running else "walking", t))
                sleep(int(t / 1000) + 1)
                self.env.logh("clicking (%s, %s)"%(x, y))
                
                self.env.clickLoc(xx,yy) if not self.env.banking else self.env.dclickLoc(xx, yy)
                if location != "superheat":
                    self.toggleRun()

    def getFromBank(self, resources, noted=False):
        self.env.banking = True
        bankwindow = self.env.exists("bank_bankwindow")
        orign = bankwindow.getBottomLeft()
        bankwindow.highlight(1)
        bankwindow.setW(420)
        bankwindow.setH(500)
        bankwindow.setY(orign.y-500)
        bankwindow.highlight(True, 1, "green")
        bankBtn = self.env.exists("bank_withdrawall")
        if bankBtn:
            self.env.click(bankBtn)
            sleep(1)
        else:
            self.env.warn("Did not see withdrawall")
        if noted:
            bankBtn = self.env.exists("bank_withdrawasnote")
            if bankBtn:
                self.env.click(bankBtn)
                sleep(1)
            else:
                self.env.warn("Did not see withdrawasnote")
        for resource in resources:
            bankItem = self.env.wait("bank_%s"%resource, time=1, reg=bankwindow, sim=0.60)
            if bankItem:
                self.env.info("Found %s in bank"%resource)
                self.env.click(bankItem)
                sleep(1)
            else:
                self.env.warn("Did not see %s in bank."%resource)
                return False
        x = self.env.wait("bank_closebankbtn")
        if x:
            if self.env.lbdown:
                c = x.getCenter()
                self.env.lbdown(c.x, c.y)
            else: self.env.click(x)
        else:
            self.env.error("COULD NOT CLOSE BANK??")
        self.env.banking = False


    def bankItems(self, location, gotobooth=False):
        x = self.env.exists("bank_closebankbtn")
        booth = None
        if x is None:
            booth = self.env.wait("%s_boothbank"%location, time=5, sim=0.8)
        else: 
            self.env.logh("Bank window open.")
        if booth:
            self.env.logh("found bank booth")
            self.env.click(booth)
            self.env.dclick(booth)
        if x or booth:
            d = self.env.wait("bank_depositbtn", time=5)
            if d is None:
                self.env.error("deposit button not seen.")
                return False
            self.env.logh("depositing")
            self.env.click(d)
            self.inv_full = False
            return True
        else:
            self.env.error("could not bank")
        return False

    def gotoBank(self, location, resources):
        self.env.warn("Inventory status: %s"%self.inv_full)
        if not self.inv_full and self.stats["mine"][resources[0]] > 0 and self.env.wait("%s_boothbank"%location, sim=0.8):
            return True
        self.env.logger.incIndent("bank")
        map = self.getMiniMap()
        if map:
            map.highlight(1)
            bankicon = self.env.existsAny("%s_bankicon"%location, map, sim=0.6)
            if bankicon:
                self.env.info("Moving to bank")
                self.env.click(bankicon)
                bankicon.highlight(8)
                self.env.write(self.talk("bank")+"\n")
                if self.env.existsAny("inv_empty", sim=0.98) is None:
                    self.env.logh("Inventory not empty. Depositing....")
                    self.env.logger.decIndent()
                    return self.bankItems(location)
                            
                else: 
                    self.env.info("Inventory empty.")
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

    
    # mine matching oretype for this specific resource location (X_Y_map.PNG) and return inventory full status
    def mineLocation(self, location, resourceLocation, resource): 
        if self.env.exists("inv_full", sim=0.93):
            return True

        # try to load precalced image mapping for this location
        resourceMap = self.getMapping(location, resource)
        ores = []
        foundOres = []

        oreSet = self.env.getImageSet("%s_#%s-%s_*ore"%(location, resource, resourceLocation)) 
        overwrite = resourceLocation not in resourceMap or len(resourceMap[resourceLocation]) <= 1
        if overwrite:
            # look for any matching ore if none were cached for this resource map
            ores = oreSet
        else:
            ores = resourceMap[resourceLocation]

        self.env.info("searching for: %s"%(ores))
        self.oresMissed = 0
        for oi, oref in enumerate(ores):
            orefname = oref.split(".")[0]

            oreFull = self.env.exists("%s_#%s-%s_%s"%(location, resource, resourceLocation, orefname), sim=0.85)
            
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
                
                minedOre = self.env.wait("msg_managed2mine",1)
                if minedOre is None:
                    noore = self.env.existsAny("msg_noore", sim=0.9)
                    if noore is None:
                        pickswing = self.env.exists("msg_pickswing")
                        if pickswing is not None:
                            self.env.logh("Pick swung.")
                            timeout = 0
                            minedOre = None
                            while minedOre is None and timeout < 15:
                                self.env.logh("Mining (%s)..."%timeout)
                                minedOre = self.env.exists("msg_managed2mine")
                                timeout += 1
                                if minedOre:
                                    self.stats["mine"][resource] += 1
                                    self.env.logh("Managed to mine some %s. (%s)"%(resource, self.stats["mine"][resource]))
                                else: 
                                    inv_full = self.env.exists("inv_full", sim=0.98)
                    else: 
                        self.env.warn("There's no ore here!!!1!1! >:(")
                        self.stats['mine']['oresMissed'] += 1
                else:
                    self.stats["mine"][resource] += 1
                    self.env.info("Managed to mine some %s. (%s)"%(resource, self.stats["mine"][resource]))

               
        if self.stats['mine']['oresMissed'] > len(foundOres): 
            self.worldSwitch() # switch worlds if we missed a bunch of ores
        if len(ores) < 3 or overwrite:
            self.env.logh("waiting for ore respawn")
            sleep(ORE_TIMEOUT[resource])
        
        if overwrite or len(foundOres) >= len(resourceMap[resourceLocation]):
            resourceMap[resourceLocation] = foundOres
            self.env.logh("saving resource mapping: \n%s"%json.dumps(resourceMap[resourceLocation], indent=1))
            self.saveMapping(location, resource, resourceMap)
            if foundOres == []:
                self.env.error("no ore found. looking for location.")
                raise NoOreException("no ore lol")
        else:
            self.env.warn("NOT ALL ORES FOUND. REMOVING RESOURCE MAPPING FOR %s in '%s_%s.json'...."%(resourceLocation, location, resource))
            resourceMap[resourceLocation] = [ores[0]]
            self.saveMapping(location, resource, resourceMap)
        return self.env.exists("inv_full", sim=0.94)        
   
    # mine at specified location
    def mine(self, location, resources):
        # locate self and navigate to mining area
        if not self.locate(location, resources):
            self.env.error("could not locate")
            return
        # self.reorient()
        self.stats['mine']['oresMissed'] = 0
        #load resource identifier images
        inv_full = self.env.exists("inv_full", sim=0.98)
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

                # visit each location for resource
                mapfile = "%s_%s-map"%(location, resource)
                r_locs = self.env.getImageSet(mapfile)
                if len(r_locs) == 0:
                    self.env.error("Could not find any matching images for %s"%mapfile)
                if len(resources) > 1 and resource != resources[r_ind-1]: # don't go to the first location again after locating
                    maplocators = self.env.getImageSet("%s_%s-locator"%(location, resource))
                    for ml in maplocators:
                        locatorFound=self.env.exists(ml, self.getMiniMap(), sim=0.5)
                        if locatorFound:
                            self.env.warn("moving to locator: %s"%ml)
                            self.env.click(locatorFound)
                            self.toggleRun()
                            locatorFound.highlight(4)

                for l_ind, curLoc in enumerate(r_locs):
                    self.env.warn("finding %s"%curLoc)
                    resourceLocation = curLoc[curLoc.index("map"):-4]
                    if len(r_locs) > 1 or len(resources) > 1:
                        if not moveTo:
                            nl = self.env.wait("%s_%s"%(location,resourceLocation), time=8 if self.running else 15, reg=self.getMiniMap(), sim=0.6)
                            if nl:
                                lostLMAO = False
                                self.env.warn("Moving to location: %s"%curLoc)
                                self.env.click(nl)
                                self.env.write(self.talk("mining")+"\n")
                                nl.highlight(True, 6 if self.running else 10, "green")
                            else:
                                self.env.warn("Did not see location")
                    
                    # mine all ores in this location map
                    try:
                        self.env.logger.incIndent(resourceLocation)
                        inv_full = self.mineLocation(location, resourceLocation, resource) # only use the base filename
                        self.env.logger.decIndent()
                    except NoOreException:
                        locmisses += 1
                    if inv_full:
                        break
                    moveTo = False
                self.env.logger.decIndent()
                if inv_full:
                    break
                # if only mining one location check if it has depleted and switch worlds
                if len(r_locs) == 1 and len(resources) == 1:
                    oreDepleted = self.env.exists("%s_#%s-%s_depleted"%(location, resource, resourceLocation))
                    if oreDepleted:
                        self.env.logh("ORE DEPLETED.")
                        self.worldSwitch()
                        self.env.click(self.env.exists("inv_inventorybtn"))
            if lostLMAO:
                self.env.error("I'm lost! lmao")
        if inv_full:
            self.env.logh("Inventory is full. Making bank run.")
            self.inv_full = True
            self.env.write(self.talk("invfull"))
            # go to bank and back
            self.follow(location, resource)
            self.gotoBank(location, resource)
            return True
        self.env.logh("Trip complete! (%s)"%self.stats["mine"])
        return True
    
    def woodcut(self):
        pass

    def firemake(self):
        pass


    def superheat(self, location, resources):
        atbank = False
        if self.env.existsAny("%s_boothbank"%location, sim=0.8) is None:
            atBank = self.gotoBank(location, resources)
        else: 
            atBank = self.bankItems(location)
        if not atBank:
            self.env.error("Not at bank booth")
            return True
        bankitems = ["natrunes"]
        bankitems.extend(resources)
        self.getFromBank(bankitems, noted=False)

        resource = resources[0]
        invbtn = self.env.wait("inv_inventorybtn", sim=0.8)
        if invbtn:
            self.env.click(invbtn)

        inventory = self.env.wait("inv_invbar", sim=0.6)
        if inventory:
            inventory.setH(300)
            inventory.highlight(1)
            oreinv = self.env.exists("item_%s"%resource, reg=inventory, sim=0.8)
            while oreinv:
                spellbk = self.env.existsAny("inv_spellbook", sim=0.9)
                if spellbk:
                    self.env.click(spellbk)
                    superh = self.env.exists("inv_superheat", sim=0.9)
                    if superh:
                        self.env.click(superh)
                        oreinv = self.env.wait("item_%s"%resource, time=1, reg=inventory)
                        if oreinv:
                            self.env.click(oreinv)
                            self.stats["superheat"][resource] += 1
                        sleep(0.4)
                    else: 
                        self.env.warn("Did not find superheat. Out of Nats?")
                        return False
        return True
                

    def alchemy(self, location, resources):
        atbank = False
        if self.env.existsAny("%s_boothbank"%location, sim=0.8) is None:
            atBank = self.gotoBank(location, resources)
        else: 
            atBank = self.bankItems(location)
        if not atBank:
            self.env.error("Not at bank booth")
            return True
        bankitems = ["natrunes"]
        bankitems.extend(resources)
        self.getFromBank(bankitems, noted=True)

        resource = resources[0]
        invbtn = self.env.wait("inv_inventorybtn", sim=0.8)
        if invbtn:
            self.env.click(invbtn)

        inventory = self.env.wait("inv_invbar", sim=0.6)
        if inventory:
            inventory.setH(350)
            inventory.setW(inventory.getW()+20)
            inventory.setX(inventory.getX()-10)
            inventory.setY(inventory.getY()-20)
            inventory.highlight(1)
            emptyinv = self.env.wait("alc_empty", time=1, reg=inventory)
            while emptyinv is None:
                spellbk = self.env.existsAny("inv_spellbook", sim=0.9)
                if spellbk:
                    self.env.click(spellbk)
                    spell = self.env.exists("inv_highalchemy", sim=0.9)
                    if spell:
                        self.env.click(spell)
                        if emptyinv is None:
                            alc_item = self.env.exists("item_%s-noted"%resource, sim=0.5)
                            if alc_item:
                                self.env.click(alc_item)
                                self.stats["alchemy"][resource] += 1
                            else:
                                self.env.warn("did not see item")
                                return True
                        emptyinv = self.env.exists("alc_empty", reg=inventory)
                    else: 
                        self.env.warn("Did not find spell. Out of Nats?")
                        return False
        return True

    def smith(self, location, resources):
        oriented = False
        for i in range(5):
            self.bankItems(location)
            self.getFromBank(["hammer", "ironbars"])
            if not oriented:
                self.env.scroll(-100)
                oriented=True
            self.follow("smith", "ironplatelegs", abs=True)

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
            "smith": self.smith,
        }

        if operation not in operationMap:
            self.env.error("operation '%s' not found", operation)

        for resource in resources:
            if resource not in self.stats[operation]:
                self.stats[operation][resource] = 0

        self.env.write("\n") #clear input
        self.env.logger.incIndent("%s"%location)
        i = 0
        # make sure we are self.env.logged in, window visible etc
        PlatformManager.focusWindow(self.env.rswindow)

        if self.env.exists("map_minimapglobe") is None:
            self.login()
        self.reorient()
        while (iterations is None  or i < iterations):
            i += 1
            # do op
            start_t = datetime.now()
            self.env.warn("Starting: %s %s %s %s"%(operation, location, resources, start_t))

            self.env.logger.incIndent("%s"%operation)
            ret = operationMap[operation](location, resources)
            self.env.logger.decIndent(2)

            start_t = int((datetime.now() - start_t).total_seconds())
            
            self.env.logh(''.join(["="]*100))
            
            self.env.logp("Operation %s %s %s finished %s (%s) in %ss"%(operation, location, resources, "succesfully" if ret else "unsuccessfully", i, start_t))

            for stat in self.stats:
                xp = 0 if stat not in XPTABLE else XPTABLE[stat]
                for res in self.stats[stat]:
                    xp = xp if xp > 0 else XPTABLE[res]
                    if ret:
                        self.env.logh("%s: %s x %s -> %sxp"%(stat, self.stats[stat][res], res, xp*self.stats[stat][res]))
                    else:
                        self.env.error("%s: %s x %s -> %sxp"%(stat, self.stats[stat][res], res, xp*self.stats[stat][res]))
            statstr = json.dumps(self.stats, indent=2)
            self.env.logh("%s"%statstr)
            with open("stats.json","w+") as statf:
                statf.write(statstr)
            
            self.env.logh(''.join(["="]*100))
            
            if not ret:
                break

        self.env.logger.decIndent()

        self.env.error("exiting..")
