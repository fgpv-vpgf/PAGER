"""Functions to aid in deleting a service in the publication workflow.

Reference:
http://resources.arcgis.com/en/help/main/10.1/index.html#/DeleteMapService/00s30000004t000000/
"""

import json
import urllib
import urllib2
import checkError

def genToken(url, username, password, expiration=60):
    """Generate an access token for ArcGIS Portal API.

    Reference:
        http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r3000000m5000000

    Args:
        url: URL of a federated server for which a server-token needs to be generated.
        username: Username of user who wants to get a token.
        password: Password of user who wants to get a token.
        expiration (optional): The token expiration time in minutes (default=60).

    Returns:
        The generated token.
    """

    query_dict = {'username':   username,
                  'password':   password,
                  'expiration': str(expiration),
                  'client':     'requestip'}
    query_string = urllib.urlencode(query_dict)
    return json.loads(urllib.urlopen(url + "?f=json", query_string).read())['token']


def deleteService(server, servicename, username, password, folder, port, token=None):
    """Delete the service using the ArcGIS REST API.

        server: Domain of server to connect to.
        servicename: Name of the service.
        username: User's username.
        password: User's password.
        folder: Name of the folder where service exists.
        port: Port of server to connect to.
        token (optional): Access token (default=None).
    """

    if token is None:
        token_url = "http://{}:{}/arcgis/admin/generateToken".format(server, port)
        token = genToken(token_url, username, password)
    delete_service_url = "http://{}:{}/arcgis/admin/services/{}/{}/delete?token={}".format(server, port, folder, servicename, token)
    urllib2.urlopen(delete_service_url, ' ').read()     #The ' ' forces POST

