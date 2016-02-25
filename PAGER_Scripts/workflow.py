"""Publication workflow script.

The script does the following:
- unzip the shapefile to a folder (folder name: smallkey)
- validate the shapefile (mandatory files: *.shp, *.shx, *.proj, *.dbf)
- parse the smallkey.json file to check the publication status
- publish shapefile as map service with Mapping/KML/WMS/WFS/GeoJSON enabled
- or update the service
- or delete the service
- cleanup the folder
"""


import errno
import hashlib
import json
import os
import shutil
import sys
import traceback
import arcpy

import deleteService
import publishService
import onlineResources
import checkError
import sendEmail

arcpy.env.overwriteOutput = True


def main():

    #Parameters retrieved by FileSystemWatcher from
    #filesystemwatcher_config.json

    #logs to hold all log information for current smallkey publication
    logs =[]

    #Parameters retrieved by FileSystemWatcher from
    #filesystemwatcher_config.json

    smallKey = arcpy.GetParameterAsText(0)
    smallKeyFolder = arcpy.GetParameterAsText(1)
    server = arcpy.GetParameterAsText(2)
    port = arcpy.GetParameterAsText(3)
    pubTemplate = arcpy.GetParameterAsText(4)
    connPath = arcpy.GetParameterAsText(5)
    publishStatus = arcpy.GetParameterAsText(6)
    folder = arcpy.GetParameterAsText(7)
    geocatUrl = arcpy.GetParameterAsText(8)
    geocatUsername = arcpy.GetParameterAsText(9)
    geocatPassword = arcpy.GetParameterAsText(10)
    agsUser = arcpy.GetParameterAsText(11)
    agsPassword = arcpy.GetParameterAsText(12)
    smtpserver = arcpy.GetParameterAsText(13)
    fromaddr = arcpy.GetParameterAsText(14)
    toaddrs = arcpy.GetParameterAsText(15)
    metaDataUrl = arcpy.GetParameterAsText(16)
    webAdaptorName = arcpy.GetParameterAsText(17)

##    print("smallKey ="+ smallKey)
##    print("smallKeyFolder="+ smallKeyFolder)
##    print("server ="+ server)
##    print("port ="+ port)
##    print("pubTemplate ="+ pubTemplate)
##    print("connPath ="+ connPath)
##    print("publishStatus="+ publishStatus)
##    print("folder ="+folder)
##    print("geocatUrl ="+ geocatUrl)
##    print("geocatUsername ="+ geocatUsername )
##    print("geocatPassword ="+ geocatPassword)
##    print("agsUser ="+ agsUser)
##    print("agsPassword ="+ agsPassword)
##    print("smtpserver ="+smtpserver)
##    print("fromaddr="+ fromaddr)
##    print("toaddrs ="+ toaddrs)
##    print("metaDataUrl ="+metaDataUrl)


    try:

        serviceName = smallKey
        mapServiceFullName = folder + "/" + serviceName
        serviceNameDelete = serviceName + ".MapServer"

        #Folder to move payload zip files to after they are published
        (payloadFolder, sk) = os.path.split(smallKeyFolder)
        payloadZip = os.path.join(payloadFolder, smallKey + ".zip")

        publishedFolderName = "Published"
        publishedFolderPath = os.path.join(payloadFolder, publishedFolderName)

        badLoadsFolderName = "Bad_Payloads"
        badLoadsFolderPath = os.path.join(payloadFolder, badLoadsFolderName)

        #check error

        errReturns= checkError.errorValidation(smallKey,smallKeyFolder,publishStatus,geocatUrl, geocatUsername,geocatPassword,metaDataUrl,logs)
        if errReturns == 1:  #fatal error
            sys.exit(1)



        serviceExists = False

        #Get the list of existing map service
        agsServiceList = publishService.getCatalog(server, port,logs)

        #Check if the map service already exists
        if mapServiceFullName in agsServiceList:
            serviceExists = True


        if publishStatus in ("1", "2"):   #NEW or UPDATE

            if publishStatus == "1":    #NEW
                if serviceExists:
                    checkError.printLog(logs,"")
                    checkError.printLog(logs,mapServiceFullName + " already exists. System exit.")
                    moveFileToFolder(payloadZip, badLoadsFolderPath,logs)
                    sys.exit(0)
            else:   #UPDATE
                checkError.printLog(logs,"")
                checkError.printLog(logs,"Attempting to update the service: " + mapServiceFullName)

                if not serviceExists:
                    checkError.printLog(logs,"Service does not exist. Publishing as new service.")
                    checkError.printLog(logs,"")
                else:
                    deleteService.deleteService(server, serviceNameDelete, agsUser, agsPassword, folder, port)


            #Publish the new service
            shpFolder = os.path.join(smallKeyFolder, smallKey)
            pMXD = publishService.createMXD(shpFolder, pubTemplate,logs)

            try:
                publishService.publishMXD(shpFolder, pMXD, connPath, serviceName, folder,logs)
            finally:
                del pMXD

            #Check publishing status
            status = publishService.serviceStatus(mapServiceFullName, smallKey, smallKeyFolder,server, port,geocatUrl, geocatUsername, geocatPassword,logs)

            #If the service is published successfully, make the
            #descriptor file, otherwise exit
            if status == 'SUCCESS':

                publishService.addFileSizeToJson(smallKey, smallKeyFolder, shpFolder)
                moveFileToFolder(payloadZip, publishedFolderPath,logs)

                if onlineResources.updateOnlineResources(smallKey, smallKeyFolder, webAdaptorName, folder, geocatUrl, geocatUsername, geocatPassword,logs)==1:
                    sys.exit(1)
            elif status == 'ERROR':
                sys.exit(1)

            ##cleanUp(smallKeyFolder, smallKey,logs)

        elif publishStatus == "0":  #NOTHING

            checkError.printLog(logs,"")
            checkError.printLog(logs,"Status code 0 ignored.")

        elif publishStatus == "3":  #DELETE

            checkError.printLog(logs,"")
            checkError.printLog(logs,"Attempting to delete the service: " + mapServiceFullName)

            if serviceExists:
                deleteService.deleteService(server, serviceNameDelete, agsUser, agsPassword, folder, port)

                checkError.printLog(logs,mapServiceFullName + " map service has been deleted")

                publishedZipPath = os.path.join(payloadFolder, publishedFolderName, smallKey + ".zip")
                checkError.printLog(logs,"Deleted: " + publishedZipPath)

                if os.path.isfile(publishedZipPath):
                    os.remove(publishedZipPath)
                    checkError.printLog(logs,"Deleted: " + payloadZip)
                if os.path.isfile(payloadZip):
                    os.remove(payloadZip)
            else:
                checkError.printLog(logs,"Service does not exist. Exiting.")
                sys.exit(0)
        else:
            checkError.printLog(logs,"Unknown publish status: " + publishStatus)

        if errReturns == 2:  #warning error   #add at last to avoid duplicated emails
            sendEmail.sendEmail(smtpserver, fromaddr, toaddrs, smallKey, smallKeyFolder, logs)

    except:

        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "\n\nERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + \
                str(sys.exc_type) + ": " + str(sys.exc_value) + "\n"

        if hasattr(sys.exc_value, 'code'):
           if sys.exc_value.code !=0:  #only for un-normal exit
                moveFileToFolder(payloadZip, badLoadsFolderPath,logs)
                checkError.printLog(logs,pymsg)
                sendEmail.sendEmail(smtpserver, fromaddr, toaddrs, smallKey, smallKeyFolder, logs)
        else:
            moveFileToFolder(payloadZip, badLoadsFolderPath,logs)
            checkError.printLog(logs,pymsg)
            sendEmail.sendEmail(smtpserver, fromaddr, toaddrs, smallKey, smallKeyFolder, logs)

#July 8, 2014 - Does not work with WFS enabled
def cleanUp(workspace, smallKey,logs):
    """Clean up the workspace by removing smallkey folder and zip file.

    Args:
        workspace: ArcPy workspace environment setting (folder path).
        smallKey: ID of shapefile.
        logs: log list holds all log items for current publication
    """

    try:
        for root, dirs, files in os.walk(workspace, topdown=False):
            for f in files:
                print f
                os.unlink(os.path.join(root, f))
            for d in dirs:
                print d
                shutil.rmtree(os.path.join(root, d),ignore_errors=True)

        checkError.printLog(logs,workspace + " workspace cleaned up")

    except OSError as e:
        checkError.printLog(logs,"Folder clean up Failed with: "+ e.strerror)


def moveFileToFolder(sourcePath, destinationPath,logs):
    """Moves a file from one directory to another. If the file exists in the destination directory, it will be overwritten.
        if destination folder is not existed, create it first
    Args:
        sourcePath: Path of the source file.
        destinationPath: Path of the destination directory.
        logs: log list holds all log items for current publication
    """

    if not os.path.exists(destinationPath):
        os.makedirs(destinationPath)

    if os.path.exists(sourcePath):
        shutil.copy(sourcePath, destinationPath)
        os.remove(sourcePath)

if __name__ == '__main__':
    main()
