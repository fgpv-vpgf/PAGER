"""Edit properties of an existing service.

Can be extended to edit additional properties other than maxRecordCount.

Reference:
    http://resources.arcgis.com/en/help/main/10.2/index.html#/Example_Edit_service_properties/0154000005r4000000/

Hardcoded:
    - admin username
    - admin password
    - server name: "wbur01dttrain9.ontario.int.ec.gc.ca"
    - server port: 6080
    - folder: "ECDMP"
    - new max record count

How it works:
    1. Generates a token for access to the API.
    2. Connects to the ArcGIS REST API at "http://wbur01dttrain9.ontario.int.ec.gc.ca/arcgis/admin/services/".
    2. Retrieves all services in ECDMP folder (http://wbur01dttrain9.ontario.int.ec.gc.ca/arcgis/admin/services/ECDMP) of type "MapServer".
    3. Edits the maxRecordCount property of all services one at a time only if the new value is different from the old value.
"""

import httplib
import json
import sys
import urllib


def main():
    #Admin username/password
    username = "arcgis"
    password = "@RCGIS42"

    #EDN server
    serverName = "wbur01dttrain9.ontario.int.ec.gc.ca"
    serverPort = 6080

    #Do work in this folder only
    folder = "ECDMP"
    folderPath = "/arcgis/admin/services/" + folder

    #Set maxRecordCount value
    newMaxRecordCount = 10000

    print
    print "Changing the maxRecordCount of all MapServer services published in the ~/services/%s folder." % (folder)

    #Get a token to access ArcGIS REST API
    token = getToken(username, password, serverName, serverPort)
    if token == "":
        print "Could not generate a token with the username and password provided."
        return

    #This request only needs the token and the response formatting parameter
    params = urllib.urlencode({'token': token, 'f': 'json'})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    #Get the response from the service folder
    try:
        folderJson = getServiceResponse(serverName, serverPort, folderPath, params, headers)
        folderObj = json.loads(folderJson)
    except:
        print
        print "No such folder exists."
        sys.exit()

    #Check for MapServer services in the folder
    if folderObj["services"]:
        #Get individual services from folder
        for services in folderObj["services"]:
            if services["type"] == "MapServer":
                #Set full service path
                serviceUrl = folderPath + "/" + services["serviceName"] + "." + services["type"]

                serviceJson = getServiceResponse(serverName, serverPort, serviceUrl, params, headers)
                serviceObj = json.loads(serviceJson)

                oldMaxRecordCount = serviceObj["properties"]["maxRecordCount"]

                print "Changing %s from %s to %s" % (serviceObj["serviceName"], oldMaxRecordCount, str(newMaxRecordCount))

                if int(oldMaxRecordCount) != newMaxRecordCount:
                    #Update maxRecordCount
                    serviceObj["properties"]["maxRecordCount"] = newMaxRecordCount

                    #Serialize back into JSON
                    updatedServiceJson = json.dumps(serviceObj)

                    #Call the edit operation on the service.  Pass in modified
                    #JSON.
                    editServiceUrl = serviceUrl + "/edit"
                    params = urllib.urlencode({'token': token, 'f': 'json', 'service': updatedServiceJson})
                    getServiceResponse(serverName, serverPort, editServiceUrl, params, headers)
                else:
                    print "maxRecordCount is the same. No editing necessary."
    else:
        print "No services found in the specified location."

    return


def getToken(username, password, serverName, serverPort):
    """Generate an access token for ArcGIS Portal API.

    Reference:
        http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r3000000m5000000

    Args:
        username: Username of user who wants to get a token.
        password: Password of user who wants to get a token.
        serverName: Domain of server to connect to.
        serverPort: Port of server to connect to.

    Returns:
        The generated token.
    """

    #Token URL is typically http://server[:port]/arcgis/admin/generateToken
    tokenURL = "/arcgis/admin/generateToken"

    params = urllib.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'})

    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    #Connect to URL and post parameters
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", tokenURL, params, headers)

    #Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Error while fetching tokens from admin URL. Please check the URL and try again."
        return
    else:
        data = response.read()
        httpConn.close()

        #Check that data returned is not an error object
        if not assertJsonSuccess(data):
            return

        #Extract the token from it
        token = json.loads(data)
        return token['token']


def assertJsonSuccess(data):
    """Checks that the input JSON object is not an error object.

    Args:
        data: JSON string.

    Returns:
        True if successful, False otherwise.
    """

    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True


def getServiceResponse(serverName, serverPort, service, params, headers):
    """Connects to the service to get its current JSON definition.

    Args:
        serverName: Domain of server to connect to.
        serverPort: Port of server to connect to.
        service: URL of service.
        params: URL parameters.
        headers: URL headers.

    Returns:
        The service's current JSON definition.
    """

    #Connect to service
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", service, params, headers)

    serviceName = str(service).split("/arcgis/admin/services/")[1]

    #Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Could not read service information."
        return
    else:
        data = response.read()

        #Check that data returned is not an error object
        if not assertJsonSuccess(data):
            print "Error when reading service information. " + str(data)
        else:
            if "edit" in service:
                print "Service edited successfully."
            else:
                print
                print serviceName + " responded successfully."

            httpConn.close()
            return data


if __name__ == "__main__":
    main()
