from splinter import Browser
import time
import platform
import os
from helpers import vehicles,randomint
from colorama import init,Fore,Style
from vehicle import Vehicle
from mission import Mission
from despatch import Despatch
init()
operatingsystem = platform.system()
path = os.path.dirname(os.path.realpath(__file__))
#Skip doing missions, just build data. (for testing)
JUST_BUILD_DATA = False


class AlreadyExistsException(Exception):
    pass
class NothingToDespatch(Exception):
    pass



# Get URL from file
with open(path + "/url.txt", 'r') as f:
    BASE_URL = f.readline().strip()

class MissonChiefBot:
  def __init__(self):
    self.hrefs= []
    self.missionList = []
    self.vehicleList = []
    self.despatches = []
    logged_in = login(username,password)
    if logged_in:
      self.buildVehicles()
      while True:
        self.doMissions()
    else: 
      print("Couldn't log in...")
     
  def buildMissions(self):
    print("Removing Completed")
    #Check and remove completed missions
    oldMissions = self.missionList
    for oldMission in oldMissions:
      browser.visit("https://www.missionchief.co.uk/missions/"+oldMission.getID())
      try:
        if browser.find_by_css('missionNotFound'):
          print(oldMission.getName() + " was completed.")
          self.missionList.remove(oldMission)
          for v in self.despatches[oldMission.getID()].getVehicles():
            self.vehicleList[v].setStatus(1)
          self.despatches.remove(oldMission)
      except ElementDoesNotExist:
        continue
      
    print("Building New Missions")
    url = BASE_URL
    hrefs = []
    browser.visit(url)
    links = browser.links.find_by_partial_href('/missions/')
    for link in links:
        hrefs.append(link['href'])
    print(f"{str(len(links))} mission/s found")
    for href in hrefs:
      print(href)
      missionId = href.split("/")[4]
      try:
        for mission in self.missionList:
          if mission.getID() == missionId:
            #since the mission is already in the list, we can continue it.
            raise AlreadyExistsException()
        browser.visit("https://www.missionchief.co.uk/missions/"+missionId)
        missionName = browser.find_by_id('missionH1').text          
        requirements = getRequirements(missionId)
        currMission = Mission(missionId,missionName,requirements)
        self.missionList.append(currMission)

      except AlreadyExistsException:
        print("mission except")
        continue
      #time.sleep(5)


  def buildVehicles(self):
    print("Building Vehicles")
    url = BASE_URL
    hrefs = []
    browser.visit(url)
    links = browser.links.find_by_partial_href('/vehicles/')
    for link in links:
        hrefs.append(link['href'])
    print(f"{str(len(links))} vehicles/s found")
    for href in hrefs:
      vehicleId = href.split("/")[4]
      try:
        for vehicle in self.vehicleList:
          if vehicle.getID == vehicleId:
            #since the vehicle is already in the list, we can continue it.
            raise AlreadyExistsException()
        browser.visit("https://www.missionchief.co.uk/vehicles/"+vehicleId)
        vehicleName = browser.find_by_tag('h1').text
        vehicleType = browser.links.find_by_partial_href('/fahrzeugfarbe/').text
        vehicleStatus = browser.find_by_xpath('//span[contains(@class, "building_list_fms")]').text    
        currVehicle = Vehicle(vehicleId,vehicleName,vehicleType,vehicleStatus)
        self.vehicleList.append(currVehicle)
      except AlreadyExistsException:
        continue
      #time.sleep(5)
      
  def doMissions(self):
    self.buildMissions()
    print(Fore.MAGENTA + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("printing data")
    for mission in self.missionList:
        print(mission.getID(),mission.getName(),mission.getStatus())
    for vehicle in self.vehicleList:
        print(vehicle.getID(),vehicle.getName(),vehicle.getStatus(),vehicle.getType()) 
    print(Fore.MAGENTA + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"+Style.RESET_ALL)
    if not JUST_BUILD_DATA:
      print("Doing missions")
      for mission in self.missionList:
        print("Checking if "+ mission.getName()+" has units responding")
        if(mission not in self.despatches):
          self.despatchVehicles(mission)
        else:
          #We need to make sure that there's no missions with half dispatches (if there weren't enough vehicles to begin with)
          for despatch in self.despatches:
            if despatch == mission:
              totalVehiclesRequired = 0
              for requirement in mission.getRequirements():
                totalVehiclesRequired += int(requirement['qty'])
              if totalVehiclesRequired > len(despatch.getVehicles()):
                #If the amount of despatched vehicles is less than required. We can retry the dispatch
                print(mission.getName() + " still needs vehicles. Despatching...")
                self.despatchVehicles(mission)
                
          print(f"Mission {mission.getID()} was already despatched, doing nothing..")
    else:
      print("Not doing missions. Debug build only. ")
          
    #  Sleep after mission set.
    sleep()

  def despatchVehicles(self,mission):
    print(f"Going to mission {mission.getID()}")
    browser.visit("https://www.missionchief.co.uk/missions/"+mission.getID())
    print("Checking requirements " + mission.getName())
    despatchedVehicles = []
    for requirement in mission.getRequirements():
      todes = int(requirement['qty'])
      des = 0
      checkedunits = False
      try: 
        for category in vehicles:
          #Only need to check for required types
          if requirement['requirement'] == category:
            print("Mission needs " + category)
            for vehicle in vehicles[category]:
              for ownedVehicle in self.vehicleList:
                if(ownedVehicle.getType() == vehicle and (ownedVehicle.getStatus() == '1' or ownedVehicle.getStatus() == '2')):
                  print("We have a " + category + " " + ownedVehicle.getType() + " available")
                  print("Despatching " + ownedVehicle.getName() + " to " + mission.getName())
                  checkid = ownedVehicle.getID()
                  checkbox=browser.find_by_id('vehicle_checkbox_'+ownedVehicle.getID())    
                  if(des<todes):
                    checkbox.check()
                    checkedunits = True            
                    des+=1
                    despatchedVehicles.append(ownedVehicle.getID())   
                    ownedVehicle.setStatus(3)
            #we can skip the next categories as this requirement has now been fulfilled
            break
      except NothingToDespatch:
        print("Nothing to despatch")  
        continue            
    print(f"{des} units despatched")
    if(checkedunits==True):
      browser.find_by_name('commit').click()
      if(mission not in self.despatches):
        currDespatch = Despatch(mission.getID(),despatchedVehicles,10)
        self.despatches.append(currDespatch)
    else:
      print("Nothing to despatch") 
      
def sleep():
    print(Fore.CYAN + f"Sleeping for {str(15)} seconds")
    Style.RESET_ALL
    time.sleep(15)
   
def login(username,password):
    print(Fore.CYAN + "Logging in")
    Style.RESET_ALL
    # Visit URL
    url = BASE_URL+"/users/sign_in"
    browser.visit(url)
    # Filling in login information
    browser.fill("user[email]",username)
    browser.fill("user[password]",password)
    # Submitting login
    browser.find_by_name('commit').click()
    try : 
     # check we are logged in- by grabbing a random tag only visible on log in.
     alliance = browser.find_by_id('alliance_li')
     print("Logged in")
     if alliance['class']=="dropdown":
      return True
     else:
      return False
    except Exception: 
     return False


def getRequirements(missionId):
  print("Getting requirements")
  requirementsurl = browser.links.find_by_partial_href('/einsaetze/')[0]['href']
  browser.visit(requirementsurl)
  requiredlist = []
  requirements = browser.find_by_tag('td')
  Style.RESET_ALL
  print(Fore.YELLOW + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
  Style.RESET_ALL
  for index, r in enumerate(requirements):
    if r.text:
     if "Required" in r.text:
      if "Station" not in r.text:
       requirement = r.text.replace('Required','').strip().lower()
       qty = requirements[index+1].text
       print(f"Requirement found :   {str(qty)} x {str(requirement)}")
       requiredlist.append({'requirement':requirement,'qty': qty })
  print(Fore.YELLOW + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
  Style.RESET_ALL
  if(len(requiredlist)==0):
   requiredlist.append({'requirement':'ambulance','qty': 1 })

  return requiredlist


# Taking account information from file
with open(path + '/account.txt', 'r') as f:
    username = f.readline().strip()
    password = f.readline().strip()
    

# Setting up browser
if operatingsystem == "Windows":
 executable_path = {'executable_path': path +'/chromedriver.exe'}
elif operatingsystem == "Linux":
  executable_path = {'executable_path': path +'/linux/chromedriver'}

elif operatingsystem == "Darwin":
  executable_path = {'executable_path': path+'/mac/chromedriver'}
 
browser = Browser('chrome', **executable_path)

def begin(): 
 MissonChiefBot()

if __name__ == '__main__':
 begin()