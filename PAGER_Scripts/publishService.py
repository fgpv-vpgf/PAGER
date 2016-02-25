# -*- coding: UTF-8 -*-
"""Functions to aid in publishing a service in the publication workflow.
"""

import glob
import json
import os
import random
import string
import urllib2
import xml.dom.minidom as DOM
from xml.sax.saxutils import escape

import arcpy
import checkError


def createMXD(inFolder, template,logs):
    """Create MXD from the layers in the folder.

    Args:
        inFolder: Path of folder to work from.
        template: Template MXD file.
        logs: log list holds all log items for current publication
    Returns:
        A new MXD file.
    """

    checkError.printLog(logs,"Creating MXD...")
    arcpy.env.workspace = inFolder

    #Open the template
    mxd = arcpy.mapping.MapDocument(template)
    #Save the template to a new MXD, specific for this data
    mxd.saveACopy(inFolder + "\\" + "publishMXD.mxd")

    #Reopen the new file
    mxd = None
    mxd = arcpy.mapping.MapDocument(inFolder + "\\" + "publishMXD.mxd")

    #Add layer
    #http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/AddLayer/00s300000025000000/
    #http://gis.stackexchange.com/questions/4882/how-do-i-add-a-shapefile-in-arcgis-via-python
    shps = arcpy.ListFeatureClasses("*.shp", "")
    dataFrame = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    if shps:
        for shp in shps:
            newLayer = arcpy.mapping.Layer(inFolder + "\\" + shp)
            arcpy.mapping.AddLayer(dataFrame, newLayer, "BOTTOM")

            applyRandomSymbology(mxd, dataFrame, 0,logs)
            del newLayer

        mxd.save()
        checkError.printLog(logs,"Publishing MXD created")
    else:   #If there's no shapefile
        checkError.printLog(logs,"No shapefile. Check payload folder")

    return mxd


def applyRandomSymbology(mxd, dataFrame, layerIndex,logs):
    """Change the specified layer's symbology to a random colour.

    Args:
        mxd: MXD file.
        dataFrame: DataFrame object of the MXD file.
        layerIndex: Index value of layer.
        logs: log list holds all log items for current publication
    """
    #Layer you want to update
    updateLayer = arcpy.mapping.ListLayers(mxd, "", dataFrame)[layerIndex]
    #Grab the properties of the layer
    desc = arcpy.Describe(updateLayer)

    groupLayerFile = None

    if desc.shapeType == 'Point' or desc.shapeType == 'Polygon' or desc.shapeType == 'Polyline':
        groupLayerFile = arcpy.mapping.Layer(r"%s\%sColours.lyr" % (os.path.dirname(__file__), desc.shapeType))
    else:
        return

    groupLayerList = arcpy.mapping.ListLayers(groupLayerFile)

    groupLayersCount = len(groupLayerList)
    #Start with 1 because the first layer of groupLayerList is a group layer
    randomNumber = random.randint(1, groupLayersCount - 1)

    #Select random layer you want to apply to updateLayer
    sourceLayer = groupLayerList[randomNumber]

    arcpy.mapping.UpdateLayer(dataFrame, updateLayer, sourceLayer, True)


#Use ArcGIS for Server REST API to get the list of map services that is already
#published
def getCatalog(server, port,logs):
    """Use ArcGIS for Server REST API to get the list of map service that are already published.

    Args:
        server: Domain of server to connect to.
        port: Port of server to connect to.
        logs: log list holds all log items for current publication
    Returns:
        List of map services.
    """

    serviceList = []
    baseUrl = "http://{}:{}/arcgis/rest/services".format(server, port)

    catalog = json.load(urllib2.urlopen(baseUrl + "/" + "?f=json"))
    if "error" in catalog:
        return

    services = catalog['services']
    for service in services:
        response = json.load(urllib2.urlopen(baseUrl + '/' + service['name'] + '/' + service['type'] + "?f=json"))
        serviceList.append(service['name'])

    folders = catalog['folders']
    for folderName in folders:
        catalog = json.load(urllib2.urlopen(baseUrl + "/" + folderName + "?f=json"))
        if "error" in catalog:
            return
        services = catalog['services']

        for service in services:
            response = json.load(urllib2.urlopen(baseUrl + '/' + service['name'] + '/' + service['type'] + "?f=json"))
            serviceList.append(service['name'])
    return serviceList


def serviceStatus(serviceFullName,smallKey, smallKeyFolder, server, port,geocatUrl, geocatUsername, geocatPassword,logs):
    """Check the status of a pubilshed service.

    Args:
        smallKey: Small key of current payload.
        SmallKeyFolder: folder of current payload
        serviceFullName: Name of the service.
        server: Domain of server to connect to.
        port: Port of server to connect to.
        geocatUrl: geocat Url
        geocatUsername: geocat user name
        geocatPassword: geocat password
        logs: log list holds all log items for current publication
    Returns:
        A string - 'ERROR' or 'SUCCESS'.
    """
    status = 'SUCCESS'
    baseUrl = "http://{}:{}/arcgis/rest/services".format(server, port)
    response = json.load(urllib2.urlopen(baseUrl + '/' + serviceFullName + '/' + 'MapServer' + "?f=json"))
    if "error" in response:
        status = 'ERROR'
    else:
        #check further if there is any records returned
        queryUrl = baseUrl + '/' + serviceFullName + '/' + 'MapServer'
        queryUrl= queryUrl + "/0/query?where=1%3D1&text=&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&relationParam=&outFields=&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&returnIdsOnly=false&returnCountOnly=true&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&gdbVersion=&returnDistinctValues=false&f=json"
        response= json.load(urllib2.urlopen(queryUrl))
        if "error" in response:
            status ="ERROR"
            checkError.printLog(logs,"Service " + smallKey + " returns error.")
            onlineResources.updateErrorStatus(smallKey, smallKeyFolder, RESTENDPOINTNOTFOUND['code'],  geocatUrl, geocatUsername, geocatPassword)
    return status


#July 8, 2014 - Not working
def makeDescriptor(smallkey, baseUrl,logs):
    """Use the makeDescriptor service to create a JSON descriptor file.

    Assumption: The JSON file exists in a folder.

    Args:
        smallKey: Small key of current payload.
        baseUrl: Base URL of makeDescriptor service.
        logs: log list holds all log items for current publication
    """

    makeDescriptorUrl = baseUrl + '/' + smallkey
    print "make descriptorUrl:"+ makeDescriptorUrl
    response = json.load(urllib2.urlopen(makeDescriptorUrl + "?f=json"))

    if 'Error' in response:
        checkError.printLog(logs,response['Error'])
    else:
        checkError.printLog(logs,response['msg'])


def getFrenchText(prop):
    """Gets the French text for the given property and returns a string.

    Must be parent node that contains "gmd:LocalisedCharacterString" as a direct child.

    Args:
        prop: Nodelist object to retrieve text from.

    Returns:
        String of French text (or empty if none exists).
    """
    try:
        localisedString = prop.item(0).getElementsByTagName("gmd:LocalisedCharacterString")
        if localisedString.length > 0 and localisedString.item(0).hasChildNodes():
            return localisedString.item(0).firstChild.data
        else:
            return ""
    except:

        return ""

def getEnglishText(prop):
    """Gets the English text for the given property and returns a string.

    Must be parent node that contains "gco:CharacterString" as a direct child.

    Args:
        prop: Nodelist object to retrieve text from.

    Returns:
        String of English text (or empty if none exists).
    """
    try:
        characterString = prop.item(0).getElementsByTagName("gco:CharacterString")
        if characterString.length > 0 and characterString.item(0).hasChildNodes():
            return characterString.item(0).firstChild.data
        else:
            return ""
    except:

        return ""

def joinStrings((strings), separator=" / "):
    """Joins strings divided by a separator string and returns the result.

    Filters out empty strings.

    Args:
        (strings): Tuple of strings (i.e. (englishText, frenchText)).
        separator (optional): Separator string (default = " / ").

    Returns:
        The joined string.
    """

    return separator.join(filter(None, strings))


def setServiceProperties(prop, doc, propList):
    """Sets WMS/WFS service properties using propList dictionary values.

    Args:
        prop: DOM element node/property to be altered.
        doc: DOM Document instance.
        propList: Dictionary of WMS/WFS properties.
    """

    if prop.firstChild.data in propList:
        propValue = propList.get(prop.firstChild.data)
        if prop.nextSibling.hasChildNodes():
            prop.nextSibling.firstChild.replaceWholeText(propValue)
        else:
            txt = doc.createTextNode(propValue)
            prop.nextSibling.appendChild(txt)


def escapeSpecialCharacters(propList):
    """Substitutes special characters in dictionary with an escape sequence and returns a dictionary.

    See: http://resources.arcgis.com/en/help/main/10.2/index.html#//00sq00000082000000

    Args:
        propList: Dictionary of WMS/WFS properties to be parsed.

    Returns:
        Dictionary with substituted escape sequences.
    """

    chars = {"\"": "&quot;",
             "'": "&apos;"}
    for k, v in propList.items():
        #Uses xml.sax.saxutils.escape with custom entities for single/double
        #quotes
        propList[k] = escape(v, chars)
    return propList


def getFirstElement(nodeList, tagName):
    """Gets the first child element of a node list specified by a tag name and returns a node list object.

    Args:
        nodeList: Node list object to be searched.
        tagName: Element name to search for.

    Returns:
        A NodeList object.
    """

    return nodeList.item(0).getElementsByTagName(tagName)


def getMetadata(workspace, smallKey):
    """Gets the metadata records (Eng/Fr) from supplied XML and returns a dictionary.

    Args:
        workspace: Absolute path of workspace folder.
        smallKey: Small key of current payload.

    Returns:
        A dictionary filled with metadata records.
    """

    #WMS/WFS combined property list with default values
    propList = {u"title": u"",
                u"abstract": u"",
                u"keyword": u"",
                u"contactPerson": u"Inquiry Centre / Informathèque",
                u"individualName": u"Inquiry Centre / Informathèque",
                u"contactPosition": u"",
                u"positionName": u"",
                u"contactOrganization": u"Environment Canada / Environnement Canada",
                u"providerName": u"Environment Canada / Environnement Canada",
                u"address": u"10 Wellington, 23rd Floor / 10, rue Wellington, 23e étage",
                u"deliveryPoint": u"10 Wellington, 23rd Floor / 10, rue Wellington, 23e étage",
                u"addressType": u"",
                u"city": u"Gatineau",
                u"stateOrProvince": u"QC",
                u"administrativeArea": u"QC",
                u"postCode": u"K1A0H3",
                u"postalCode": u"K1A0H3",
                u"country": u"Canada",
                u"contactVoiceTelephone": u"800-668-6767",
                u"phone": u"800-668-6767",
                u"contactFacsimileTelephone": u"819-994-1412",
                u"facsimile": u"819-994-1412",
                u"contactElectronicMailAddress": u"enviroinfo@ec.gc.ca",
                u"electronicMailAddress": u"enviroinfo@ec.gc.ca",
                u"fees": u"None / Aucun",
                u"accessConstraints": u""}

    metadataXML = os.path.abspath(os.path.join(workspace, "..", smallKey + ".xml"))

    doc = DOM.parse(metadataXML)

    identificationInfoNode = doc.getElementsByTagName("gmd:identificationInfo")

    #Drill down to title node
    citationNode = getFirstElement(identificationInfoNode, "gmd:citation")
    titleNode = getFirstElement(citationNode, "gmd:title")
    propList["title"] = joinStrings((getEnglishText(titleNode), getFrenchText(titleNode)))

    #Drill down to abstract node
    abstractNode = getFirstElement(identificationInfoNode, "gmd:abstract")
    propList["abstract"] = joinStrings((getEnglishText(abstractNode), getFrenchText(abstractNode)))

    #Drill down to position node
    pointOfContactNode = getFirstElement(identificationInfoNode, "gmd:pointOfContact")
    positionNameNode = getFirstElement(pointOfContactNode, "gmd:positionName")
    propList["contactPosition"] = joinStrings((getEnglishText(positionNameNode), getFrenchText(positionNameNode)))
    propList["positionName"] = propList["contactPosition"]

    #Drill down to first keyword node
    descriptiveKeywordsNode = getFirstElement(identificationInfoNode, "gmd:descriptiveKeywords")
    keywordNode = getFirstElement(descriptiveKeywordsNode, "gmd:keyword")
    propList["keyword"] = joinStrings((getEnglishText(keywordNode), getFrenchText(keywordNode)), ", ")

    #Drill down to constraints node
    resourceConstraintsNode = getFirstElement(identificationInfoNode, "gmd:resourceConstraints")
    otherConstraintsNode = getFirstElement(resourceConstraintsNode, "gmd:otherConstraints")
    propList["accessConstraints"] = joinStrings((getEnglishText(otherConstraintsNode), getFrenchText(otherConstraintsNode)))

    return propList


def enableCapabilities(soeType, sddraft, smallKey, workspace,logs):
    """Enable capabilities for the service and set maxRecordCount.

    Args:
        soeType: List of capabilities.
        sddraft: Path to Service Definition Draft file.
        smallKey: Small key of current payload.
        workspace: Absolute path of workspace folder.
        logs: log list holds all log items for current publication
    Returns:
        Path to output .sddraft file.
    """

    #Properties dictionary for WMS/WFS Service
    propList = getMetadata(workspace, smallKey)
    propList = escapeSpecialCharacters(propList)

    #New maxRecordCount to set for publishing services (default: 1000)
    maxRecordCount = 10000

    #New maxInstances to set for publishing services (default: 2)
    maxInstances = 1

    #Read the sddraft xml.
    doc = DOM.parse(sddraft)

    #Find all elements named TypeName.  This is where the server object
    #extension (SOE) names are defined.
    typeNames = doc.getElementsByTagName('TypeName')

    for typeName in typeNames:
        #Get the TypeName whose properties we want to modify.
        if typeName.firstChild.data in soeType:
            extension = typeName.parentNode
            for extElement in extension.childNodes:
                #Enabled SOE.
                if extElement.tagName == 'Enabled':
                    extElement.firstChild.data = 'true'

            #Set WMS/WFS service properties
            if typeName.firstChild.data == "WMSServer" or typeName.firstChild.data == "WFSServer":
                svcExtension = typeName.parentNode
                for extElement in svcExtension.childNodes:
                    if extElement.tagName == "Props":
                        for propArray in extElement.childNodes:
                            for propSetProperty in propArray.childNodes:
                                for prop in propSetProperty.childNodes:
                                    if prop.nodeType == 1 and prop.tagName == "Key":
                                        setServiceProperties(prop, doc, propList)

        #Set maxRecordCount for MapServer services
        elif typeName.firstChild.data == "MapServer":
            svcConfiguration = typeName.parentNode
            for svcConfigElement in svcConfiguration.childNodes:
                if svcConfigElement.tagName == "Definition":
                    for definitionElement in svcConfigElement.childNodes:
                        if definitionElement.tagName == "ConfigurationProperties":
                            for propArray in definitionElement.childNodes:
                                for propSet in propArray.childNodes:
                                    for prop in propSet.childNodes:
                                        if prop.tagName == "Key":
                                            if prop.firstChild.data == "maxRecordCount":
                                                prop.nextSibling.firstChild.data = maxRecordCount
                                                print "maxRecordCount set to: %s" % str(maxRecordCount)
                        if definitionElement.tagName == "Props":
                            for propArray in definitionElement.childNodes:
                                for propSet in propArray.childNodes:
                                    for prop in propSet.childNodes:
                                        if prop.tagName == "Key":
                                            if prop.firstChild.data == "MaxInstances":
                                                prop.nextSibling.firstChild.data = maxInstances
                                                print "maxInstances set to: %s" % str(maxInstances)

    print "WMS/WFS service properties set"

    #Output to a new sddraft
    outXML = os.path.join(workspace, "ogcEnabledSDDraft.sddraft")
    if os.path.exists(outXML):
        os.remove(outXML)
    f = open(outXML, 'w')
    f.write(doc.toxml(encoding="utf-8"))
    f.close()
    checkError.printLog(logs,"Service definition created with %s enabled" % ", ".join(map(str, soeType)))
    checkError.printLog(logs,"")

    del f, doc
    return outXML


def addFileSizeToJson(smallKey, smallKeyFolder, shpFolder):
    """Add the file size in bytes of the .shp file to the JSON descriptor.

    Args:
        smallKey: Small key of current payload.
        smallKeyFolder: Folder in which data is unzipped to.
        shpFolder: Folder containing the .shp file.
    """

    os.chdir(shpFolder)
    for file in glob.glob("*.shp"):
        shpFileName = file
    shpFilePath = os.path.join(shpFolder, shpFileName)
    sizeInBytes = os.path.getsize(shpFilePath)
    jsonPath = os.path.join(smallKeyFolder, smallKey) + '.json'
    with open(jsonPath) as f:
        data = json.load(f)
        data["config"]["File_Size"] = sizeInBytes
    with open(jsonPath, "w") as f:
        json.dump(data, f)


def publishMXD(inFolder, mxd, connPath, serviceName, folder, logs, summary=None, tags=None):
    """Publish the service.

    Args:
        inFolder: Absolute path of workspace folder.
        mxd: MXD file to publish.
        connPath: Path to connection file that is used to connect to a GIS Server.
        serviceName: Name of the service.
        folder: Name of the folder to publish in.
        logs: log list holds all log items for current publication
        summary (optional): A string that represents the Item Description Summary (default=None).
        tags (optional): A string that represents the Item Description Tags (default=None).
    """

    workspace = inFolder
    checkError.printLog(logs,"Publishing MXD in: " + workspace)

    # Provide other service details
    service = serviceName
    sddraft = workspace + "/" + service + '.sddraft'
    sd = workspace + "/" + service + '.sd'
    folderName = folder

    # make sure the folder is registered with the server, if not, add it to the
    # datastore
    #if workspace not in [i[2] for i in arcpy.ListDataStoreItems(connPath, 'FOLDER')]:
    #    # both the client and server paths are the same
    #    dsStatus = arcpy.AddDataStoreItem(connPath, "FOLDER", "Workspace for " + service, workspace, workspace)
    #    print "Data store: " + str(dsStatus)

    # Create service definition draft
    # Data will be copied to server
    # Syntax: CreateMapSDDraft(map_document, out_sddraft, service_name,
    # {server_type}, {connection_file_path}, {copy_data_to_server},
    # {folder_name}, {summary}, {tags})
    arcpy.mapping.CreateMapSDDraft(mxd, sddraft, service, 'ARCGIS_SERVER', connPath, True, folderName, summary, tags)

    #Modify the sd to enable wms, wfs, and then wcs capabilities on the service
    soeType = ['WMSServer', 'WFSServer', 'GeoJSONServer']
    ogcSDDraft = enableCapabilities(soeType, sddraft, service, workspace,logs)

    # Analyze the service definition draft
    analysis = arcpy.mapping.AnalyzeForSD(ogcSDDraft)

    # Print errors, warnings, and messages returned from the analysis
    checkError.printLog(logs,"The following information was returned during analysis of the MXD:")

    for key in ('messages', 'warnings', 'errors'):
        checkError.printLog(logs,'----' + key.upper() + '---')
        vars = analysis[key]
        errorList =""
        if not vars:
            checkError.printLog(logs,'     None')
        else:
            for ((message, code), layerlist) in vars.iteritems():
                errorList= '    '+ message+ ' CODE %i' % code
                errorList =  errorList+ '       applies to:'
                for layer in layerlist:
                     errorList= errorList+ layer.name,
                checkError.printLog(logs,errorList)


    # Stage and upload the service if the sddraft analysis did not contain
    # errors
    if analysis['errors'] == {}:
        # Execute StageService.  This creates the service definition.
        arcpy.StageService_server(ogcSDDraft, sd)

        # Execute UploadServiceDefinition.  This uploads the service definition
        # and publishes the service.
        arcpy.UploadServiceDefinition_server(sd, connPath)
        checkError.printLog(logs, "Service successfully published")

        del ogcSDDraft
    else:
       checkError.printLog(logs,analysis['errors'])
       checkError.printLog(logs,"Service could not be published because errors were found during analysis.")
