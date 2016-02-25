"""hold constants defined for error codes in the PAGER workflow.
   two types error check: FatalError and WarningError
"""
import json
import os
import zipfile
import arcpy
import base64
from BaseHTTPServer import BaseHTTPRequestHandler
import urllib
import urllib2


INVALIDSHAPFILE ={'code': 3002, 'description': 'SHA-256 hash check failed on Shapefile'}
PERMISSIONDENIEDTOACCESSPAYLOAD ={'code': 3003, 'description': 'Permission denied to access payload file'}
CANNOTACCESSMETADATA={'code': 3004, 'description': 'Malformed metadata / Cannot access metadata'}
INVALIDDISPLAYFIELD={'code': 3005, 'description': 'Invalid display field specified'}
EMPTYDISPLAYFIELD={'code': 3006, 'description': 'Empty display field'}
MISSINGFIELDSINJSON={'code': 3007, 'description': 'JSON payload file does not have required fields'}
RESTENDPOINTNOTFOUND={'code': 3008, 'description': 'REST endpoint not found, service sanity check failed'}
PERMISSSIONDENIEDFORWRITINGTOSERVER={'code': 3009, 'description': 'Permission denied for writing to server'}
MAPRENDERNOTSUPPORTED={'code': 3011, 'description': 'Map renderer not supported'}
CANNOTUPDATEMETA={'code': 3012, 'description': 'Cannot update metadata record'}
UNKNOWNERROR={'code': 3999, 'description': 'Unanticipated error'}
METADATADOESNOTEXIST={'code': 4000, 'description': 'The metadata with uuid XXXX does not exists'}
METADATAISNOTDATASET={'code': 4001, 'description': 'The metadata with uuid XXXX is not a dataset'}
METADATACANNOTUPDATE={'code': 4002, 'description': 'The metadata with uuid XXXX is submitted to a workflow, can not update it'}
METADATAUSERNORIGHT={'code': 4003, 'description': 'The user has no rights to update the metadata with uuid XXXX it'}
OTHERGENERICERROR={'code': 4999, 'description': 'Other generic exception: Exception message'}


def validateJsonFile(smallKey,smallKeyFolder,geocatUrl, geocatUsername,geocatPassword,logs):

    """Validate the json realted error.
       validte display field, doesn't have required fields
    Args:
        smallKey: ID of shapefile.
        smallKeyFolder: Folder of smallKey
        geocatUrl: geocat Url
        geocatUsername: geocat user name
        geocatPassword: geocat password
        logs: log list holds all log items for current publication
    Returns:
        0: no error
        1: fatal error
        2: warning error
    """
    result =0

    jsonPath = os.path.join(smallKeyFolder, smallKey + '.json')

    try:
        jsonData = open(jsonPath)
        jsonObj = json.load(jsonData)
        jsonData.close()
    except:
            printLog(logs,"json file is not found")
            result=1

    try:
            uuid = jsonObj['config']['UUID']
    except:

            printLog(logs,"UUID is not found in json file")
            updateErrorStatus(smallKey,smallKeyFolder, MISSINGFIELDSINJSON['code'], geocatUrl, geocatUsername, geocatPassword,logs)
            result=1

    try:
            status = jsonObj['config']['Status']
            if not (status =="1" or status=="2" or status =="3"):
                printLog(logs,"invalid publish status value in json file, should be 1 or 2 or 3")
                result=1

    except:
            printLog(logs,"Status is not found in json file")
            updateErrorStatus(smallKey,smallKeyFolder, MISSINGFIELDSINJSON['code'], geocatUrl, geocatUsername, geocatPassword,logs)
            result=1

    try:
            target = jsonObj['config']['Target']
            if not (target =="0" or target=="1"):
                printLog(logs,"invalid target value in json file, should be 0 or 1")
                result=1

    except:

            printLog(logs,"Status is not found in json file")
            updateErrorStatus(smallKey,smallKeyFolder, MISSINGFIELDSINJSON['code'], geocatUrl, geocatUsername, geocatPassword,logs)
            result=1

    try:
            displayField = jsonObj['config']['Display_Field_En']
            if len(displayField)<=0:
                printLog(logs,"display_field_en value is empty in json file")
                result=2
    except:
            printLog(logs,"Display_Field_En is not found in json file")
            updateErrorStatus(smallKey,smallKeyFolder, MISSINGFIELDSINJSON['code'], geocatUrl, geocatUsername, geocatPassword,logs)
            result=1

    try:
            displayField = jsonObj['config']['Display_Field_Fr']
            if len(displayField)<=0:
                printLog(logs,"display_field_fr value is empty in json file")
                result=2
    except:
            printLog(logs,"Display_Field_Fr is not found in json file")
            updateErrorStatus(smallKey,smallKeyFolder, MISSINGFIELDSINJSON['code'],  geocatUrl, geocatUsername, geocatPassword,logs)
            result=1

    return result


def validateSHP(smallKey,smallKeyFolder,geocatUrl, geocatUsername,geocatPassword,logs):
    """Validate the shapefile path.

    Mandatory files for the shapefile: .shp, .shx, .dbf, .prj
    Args:
        smallKey: ID of shapefile.
        smallKeyFolder: Folder of smallKey
        geocatUrl: geocat Url
        geocatUsername: geocat user name
        geocatPassword: geocat password
        logs: log list holds all log items for current publication
    Returns:
        True if valid, False otherwise.
    """
    isValid =True

    jsonPath = os.path.join(smallKeyFolder, smallKey + '.json')
    jsonData = open(jsonPath)
    jsonObj = json.load(jsonData)
    jsonData.close()

    uuid = jsonObj['config']['UUID']

    displayFieldEn = jsonObj['config']['Display_Field_En']
    displayFieldFr = jsonObj['config']['Display_Field_Fr']

    #Unzip file to the dropfolder
    printLog(logs,"")
    printLog(logs,"Start unzipping to folder: " + smallKeyFolder)

    inputZip = os.path.join(smallKeyFolder, smallKey + ".zip")
    unzipFile(inputZip, smallKeyFolder, smallKey,logs)
    shpFolder = os.path.join(smallKeyFolder, smallKey)

    #Start validating the content of the shapefile
    printLog(logs,"")
    printLog(logs,"Validating shapefile... ")

    arcpy.env.workspace = shpFolder
    #Mandatory formats
    formatList = [".shp", ".shx", ".dbf", ".prj"]
    counter = 0

    #List the feature classes in the drop folder (support for multiple feature
    #classes)
    shps = arcpy.ListFeatureClasses("*.shp", "")
    shpNames = []
    for shp in shps:
        shpName = os.path.splitext(os.path.basename(shp))[0]
        shpNames.append(shpName)

        if len(displayFieldEn) >0 and len(displayFieldFr) >0:
            #check display field here
            desc = arcpy.Describe(shp)
            fields = desc.fields

            isFieldExist= False

            for field in fields:
                # Check the field name exist for display field
                #
                if field.name.lower() == displayFieldEn.lower() or field.name.lower() == displayFieldFr.lower():
                   isFieldExist=True
                   break

            if isFieldExist== False:
                  printLog(logs, displayFieldEn  + " or "+ displayFieldFr +" is not found in shape file")
                  isValid=False
                  updateErrorStatus(smallKey, smallKeyFolder, INVALIDDISPLAYFIELD['code'],  geocatUrl, geocatUsername, geocatPassword,logs)
                  return isValid

    #Check if all the mandatory files are there for the shapefile
    for format in formatList:
        for name in shpNames:
            if arcpy.Exists(name + format):
                printLog(logs,name + format + " exists")
            else:
                printLog(logs,name + format + " is missing")
                counter += 1

    if counter == 0:
        isValid = True
    else:
        isValid=False
        updateErrorStatus(smallKey, smallKeyFolder, INVALIDSHAPFILE['code'], geocatUrl, geocatUsername, geocatPassword,logs)

    # Reset geoprocessing environment settings
    arcpy.ResetEnvironments()

    return isValid

def unzipFile(filePath, workspace, smallKey,logs):
    """Unzip the shapefile to the smallkey folder.

    Args:
        filePath: Path to the shapefile.
        workspace: ArcPy workspace environment setting (folder path).
        smallKey: ID of shapefile.
        logs: log list holds all log items for current publication
    """

    zipTemp = open(filePath, 'rb')
    unzipPath = os.path.join(workspace, smallKey)
    if not os.path.exists(unzipPath):
        os.makedirs(unzipPath)
    z = zipfile.ZipFile(zipTemp)
    for name in z.namelist():
        z.extract(name, unzipPath)
    zipTemp.close()
    del zipTemp

def validateMetaDataService(smallKey, workspace, metaDataUrl, logs):
    """Validate meta data setvice in the Data Catalogue

    Args:
        smallKey: ID of shapefile.
        workspace: Folder in which data is unzipped to.
        metaDataUrl:Malformed metadata url
        logs: log list holds all log items for current publication
    returns:  True if valid, False otherwise
    """
    isValid =True

    #un-comment followings when geodata update status service ready to use
    #Get the UUID from the supplied JSON file
    jsonPath = os.path.join(workspace, smallKey + '.json')
    jsonData = open(jsonPath)
    jsonObj = json.load(jsonData)
    jsonData.close()
    uuid = jsonObj['config']['UUID']

    metaDataUrl = metaDataUrl+ uuid

    request = urllib2.Request(metaDataUrl)

    try:
        response = urllib2.urlopen(request)

    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            printLog(logs,'access metaData, We failed to reach a server.')
            printLog(logs,'Reason: %s' % e.reason)

        elif hasattr(e, 'code'):
            responses = BaseHTTPRequestHandler.responses
            printLog(logs,'access metaData: The server couldn\'t fulfill the request.')
            printLog(logs,'Error code: %s - %s: %s' % (e.code, responses[e.code][0], responses[e.code][1]))
            isValid=False
    return isValid


def updateErrorStatus(smallKey, workspace, errorCode, geocatUrl, geocatUsername, geocatPassword,logs):
    """Update error Status in the Data Catalogue with the error code and message

    Args:
        smallKey: ID of shapefile.
        workspace: Folder in which data is unzipped to.
        errorCode: error code
        geocatUrl: URL of GeoCat's metadata.addmapresources call.
        geocatUsername: GeoCat username with administrator privileges.
        geocatPassword: Password for matching GeoCat admin account.
        logs: log list holds all log items for current publication
    """
    #un-comment followings when geodata update status service ready to use
    #Get the UUID from the supplied JSON file

    jsonPath = os.path.join(workspace, smallKey + '.json')
    jsonData = open(jsonPath)
    jsonObj = json.load(jsonData)
    jsonData.close()
    uuid = jsonObj['config']['UUID']
    #SOAP request body
    soapBody = """<request>
    <uuid>%s</uuid>
    <smallKey>%s</smallKey>
    <statusCode>%s</statusCode>
    </request>""" % (uuid, smallKey, errorCode)


    base64string = base64.b64encode('%s:%s' % (geocatUsername, geocatPassword)).replace('\n', '')
    headers = {'Content-Type': 'application/soap+xml+x-www-form-urlencoded; charset=utf-8',
               'Authorization': 'Basic %s' % base64string}

    #Build our Request object (POST)

    try:
        request = urllib2.Request(geocatUrl, soapBody, headers)
    except:
        raise


    try:
        urllib2.urlopen(request)

    except IOError, e:
        if hasattr(e, 'reason'):
            printLog(logs,'update error status We failed to reach a server.')
            printLog(logs,'Reason: %s' % e.reason)
        elif hasattr(e, 'code'):
            #Contains HTTP error codes and responses
            #Error code list: http://www.voidspace.org.uk/python/articles/urllib2.shtml#error-codes
            responses = BaseHTTPRequestHandler.responses
            printLog(logs,'update error status: The server couldn\'t fulfill the request.')
            printLog(logs,'Error code: %s - %s: %s' % (e.code, responses[e.code][0], responses[e.code][1]))

            if e.code ==401:
                raise

##    #comment below line when geodata update status service ready to use
##    printLog(logs,'Error Status Oupdate successful')



def errorValidation(smallKey,smallKeyFolder,publishStatus,geocatUrl, geocatUsername,geocatPassword,metaDataUrl,logs):
    """valid all error which may cause stop publication request.

    Args:
        smallKey: ID of shapefile.
        smallKeyFolder: Folder of smallKey
        publishStatus: would be 1:NEW 2:update 3:delete service
        geocatUrl: URL of GeoCat's metadata.addmapresources call.
        geocatUsername: GeoCat username with administrator privileges.
        geocatPassword: Password for matching GeoCat admin account.
        logs: log list holds all log items for current publication
    returns:
        0: no error
        1: fatal error
        2: warning error
    """
    result = 0

    if not (publishStatus =="1" or publishStatus=="2" or publishStatus =="3"):
        printLog(logs,"invalid publish status value in json file, should be 1 or 2 or 3")
        return 1

    #check json status
    jsonErr= validateJsonFile(smallKey,smallKeyFolder,geocatUrl, geocatUsername,geocatPassword,logs)
    if jsonErr==1:
        return 1
    elif jsonErr ==2:
        result = 2

    if publishStatus in ("1", "2"):   #NEW or UPDATE
        #validate shape file
        if validateSHP(smallKey,smallKeyFolder,geocatUrl, geocatUsername,geocatPassword,logs) ==False:
            return 1


    if validateMetaDataService(smallKey, smallKeyFolder, metaDataUrl, logs) ==False:
        return 1

    return result

def printLog(logs, msg):
    print msg
    logs.append("")  #have to add an empty line, otherwise no line break in email content
    logs.append(msg)

