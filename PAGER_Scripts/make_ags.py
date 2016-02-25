import arcpy
outdir = 'C:\PAGER\PAGER_Scripts\'
out_folder_path = outdir
out_name = 'publisher.ags'
server_url = 'http://Your_ArcGIS_Server/arcgis/admin'
use_arcgis_desktop_staging_folder = False
staging_folder_path = outdir
username = 'arcgis_service_account'
password = 'password'

arcpy.mapping.CreateGISServerConnectionFile("PUBLISH_GIS_SERVICES",
                                            out_folder_path,
                                            out_name,
                                            server_url,
                                            "ARCGIS_SERVER",
                                            use_arcgis_desktop_staging_folder,
                                            staging_folder_path,
                                            username,
                                            password,
                                            "SAVE_USERNAME")
