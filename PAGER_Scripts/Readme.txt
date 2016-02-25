
The publish workflow python script structure:
- Code Folder (workflow.py, publishService.py, deleteService.py)
- Data Folder (the payload folder)
- log_publishworkflow.txt
- run_publishworkflow.bat


The script does the following:
	- unzip the shapefile to a folder (folder name: smallkey)
	- Validate the shapefile (mandatory files: *.shp, *.shx, *.proj, *.dbf)
	- parse the smallkey.json file to check the publication status
	- publish the shapefile as map service, with Mapping, KML, WMS, WFS capabilities enabled
	- or delete the service (NEED MORE TESTING)
	- cleanup the folder

To test the script: 
- modify the file path to workflow.py in the bat file
- modify the parameters in the main function in code\workflow.py 
	- server, port
	- Path to inputzip
	- path to map template
	- path to connection file
	- Path to make descriptor service url

	server = "wbur01dttrain9.ontario.int.ec.gc.ca"
        port = "6080"
        inputZip = "G:/ECDMP_py/workflow_py/Data/dd12em.zip"
        pubTemplate = "G:/ECDMP_py/workflow_py/Code/PubTemplate10.mxd"
        connPath = "G:/ECDMP_py/workflow_py/Code/publisher.ags"
	makeDesUrl = "http://sncr01wbingsdv1.ncr.int.ec.gc.ca/ECDMP_Service/makeDescriptor"

- Move the zip file into the Data folder
- Delete the map service in the publisher folder (if exist already)
- run the bat file



The script will be launched after the FileSystemWatcher has detected new file in the payload folder


