
import json

class Api: 
    def getVehicles(BASE_URL,browser):
     browser.visit(BASE_URL+'/api/vehicles')
     vehiclesjson = browser.find_by_tag('pre').text
     return json.loads(vehiclesjson)
     