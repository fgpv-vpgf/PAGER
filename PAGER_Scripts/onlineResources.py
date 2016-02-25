"""Script to update the OnlineResources in the Data Catalogue.

Works by sending a SOAP request to the Data Catalogue's metadata.addmapresources endpoint.
The SOAP request contains URLs to the resources.

Resources to be added are: REST, WMS, WFS, KML, GeoJSON
"""


import base64
from BaseHTTPServer import BaseHTTPRequestHandler
import json
import os
import urllib
import urllib2
import checkError
import sendEmail

def updateOnlineResources(smallKey, workspace, server, serviceFolder, geocatUrl, geocatUsername, geocatPassword,logs):
    """Update OnlineResources in the Data Catalogue with the appropriate endpoint URLs.

    Args:
        smallKey: ID of shapefile.
        workspace: Folder in which data is unzipped to.
        server: Domain of server to connect to.
        serviceFolder: Folder containing map services.
        geocatUrl: URL of GeoCat's metadata.addmapresources call.
        geocatUsername: GeoCat username with administrator privileges.
        geocatPassword: Password for matching GeoCat admin account.
    returns:
        0: no error
        1: fatal error
    """

    result=0

    servicesPath = 'arcgis/services'
    restServicesPath = 'arcgis/rest/services'

    #URLs of all services to add
    wms = 'http://%s/%s/%s/%s/MapServer/WMSServer?request=GetCapabilities&service=WMS' % (server, servicesPath, serviceFolder, smallKey)
    wfs = 'http://%s/%s/%s/%s/MapServer/WFSServer?request=GetCapabilities&service=WFS' % (server, servicesPath, serviceFolder, smallKey)
    rest = 'http://%s/%s/%s/%s/MapServer/0' % (server, restServicesPath, serviceFolder, smallKey)
    geoJson = 'http://%s/%s/%s/%s/MapServer/exts/GeoJSONServer/GeoJSON?query=true&layer=0&f=pjson' % (server, restServicesPath, serviceFolder, smallKey)
    kml = 'http://%s/%s/%s/%s/MapServer/generateKml?docName=Output&l:0=on&layers=0&layerOptions=nonComposite' % (server, restServicesPath, serviceFolder, smallKey)

    #Get the UUID from the supplied JSON file
    jsonPath = os.path.join(workspace, smallKey + '.json')
    jsonData = open(jsonPath)
    jsonObj = json.load(jsonData)
    jsonData.close()
    uuid = jsonObj['config']['UUID']

    #SOAP request body
    #CDATA used to send raw URLs without escaping characters (required for GeoJSON query)
    soapBody = """<request>
    <uuid>%s</uuid>
    <smallKey>%s</smallKey>
    <statusCode>0</statusCode>
    <endPoints>
    <endPoint protocol="REST"><![CDATA[%s]]></endPoint>
    <endPoint protocol="WMS"><![CDATA[%s]]></endPoint>
    <endPoint protocol="WFS"><![CDATA[%s]]></endPoint>
    <endPoint protocol="KML"><![CDATA[%s]]></endPoint>
    <endPoint protocol="GeoJSON"><![CDATA[%s]]></endPoint>
    </endPoints>
    </request>""" % (uuid, smallKey, rest, wms, wfs, kml, geoJson)

    base64string = base64.b64encode('%s:%s' % (geocatUsername, geocatPassword)).replace('\n', '')
    headers = {'Content-Type': 'application/soap+xml+x-www-form-urlencoded; charset=utf-8',
               'Authorization': 'Basic %s' % base64string}

    #Build our Request object (POST)
    request = urllib2.Request(geocatUrl, soapBody, headers)

    try:
        response = urllib2.urlopen(request)
    except IOError, e:
        if hasattr(e, 'reason'):
            checkError.printLog(logs,'OnlineResources: We failed to reach a server.')
            checkError.printLog(logs,'Reason: %s' % e.reason)
            checkError.updateErrorStatus(smallKey, workspace, checkError.METADATADOESNOTEXIST['code'], geocatUrl, geocatUsername, geocatPassword,logs)
        elif hasattr(e, 'code'):
            #Contains HTTP error codes and responses
            #Error code list: http://www.voidspace.org.uk/python/articles/urllib2.shtml#error-codes
            responses = BaseHTTPRequestHandler.responses
            checkError.printLog(logs,'OnlineResources: The server couldn\'t fulfill the request.')
            checkError.printLog(logs,'Error code: %s - %s: %s' % (e.code, responses[e.code][0], responses[e.code][1]))
            if e.code ==404:
                checkError.updateErrorStatus(smallKey, workspace, checkError.METADATADOESNOTEXIST['code'],  geocatUrl, geocatUsername, geocatPassword,logs)
            elif e.code ==401:
                checkError.updateErrorStatus(smallKey, workspace, checkError.METADATAUSERNORIGHT['code'], geocatUrl, geocatUsername, geocatPassword,logs)
            elif e.code==500:
                checkError.updateErrorStatus(smallKey, workspace, checkError.OTHERGENERICERROR['code'],  geocatUrl, geocatUsername, geocatPassword,logs)
            result =1
        return result
    checkError.printLog(logs,'OnlineResources update successful')
    return result



