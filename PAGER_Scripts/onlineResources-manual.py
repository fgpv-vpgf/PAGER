import arcpy
import base64
from BaseHTTPServer import BaseHTTPRequestHandler
import json
import os
import urllib
import urllib2

def main():

    # URL for OnlineResources SOAP request to be sent
    geocatUrl = 'http://intranet.ecdmp-stage.cmc.ec.gc.ca/geonetwork/srv/eng/metadata.addmapresources'
    username = 'admin'
    password = 'badmd1'

    print geocatUrl

    #URLs of all services to add
    smallKey = '8acf9e32'
    wms = 'http://sncr01wbingsqa1.ncr.int.ec.gc.ca/arcgis/services/data-donnees/' + smallKey + '/MapServer/WMSServer?request=GetCapabilities&service=WMS'
    wfs = 'http://sncr01wbingsqa1.ncr.int.ec.gc.ca/arcgis/services/data-donnees/' + smallKey + '/MapServer/WFSServer?request=GetCapabilities&service=WFS'
    rest = 'http://sncr01wbingsqa1.ncr.int.ec.gc.ca/arcgis/rest/services/data-donnees/' + smallKey + '/MapServer'
    geoJson = 'http://sncr01wbingsqa1.ncr.int.ec.gc.ca/arcgis/rest/services/data-donnees/' + smallKey + '/MapServer/exts/GeoJSONServer/GeoJSON?query=true&layer=0&f=pjson'
    kml = 'http://sncr01wbingsqa1.ncr.int.ec.gc.ca/arcgis/rest/services/data-donnees/' + smallKey + '/MapServer/generateKml?docName=Output&l:0=on&layers=0&layerOptions=nonComposite'
    uuid = '8acf9e32-6135-433e-87e0-8a4d8dd84962'
    

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

    base64string = base64.b64encode('%s:%s' % (username, password)).replace('\n', '')
    headers = {'Content-Type': 'application/soap+xml+x-www-form-urlencoded; charset=utf-8',
               'Authorization': 'Basic %s' % base64string}

    #Build our Request object (POST)
    request = urllib2.Request(geocatUrl, soapBody, headers)

    try:
        response = urllib2.urlopen(request)
    except IOError, e:
        if hasattr(e, 'reason'):
            print 'OnlineResources: We failed to reach a server.'
            print 'Reason: %s' % e.reason
        elif hasattr(e, 'code'):
            responses = BaseHTTPRequestHandler.responses
            print 'OnlineResources: The server couldn\'t fulfill the request.'
            print 'Error code: %s - %s: %s' % (e.code, responses[e.code][0], responses[e.code][1])
    else:
        print 'OnlineResources update successful'
		
if __name__ == '__main__':
    main()
