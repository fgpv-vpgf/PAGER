using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Timers;

namespace FileSystemWatcher
{
    public class FileSystemWatcher
    {
        private readonly NewFileTracker FILE_TRACKER;
        private readonly HashChecker HASH_CHECKER = new HashChecker();
        private readonly ScriptCaller SCRIPT_CALLER;

        private readonly Timer timer = new Timer();

        /// <summary>
        /// An array of String denoting where the small key is in the config
        /// </summary>
        private readonly String[] SMALLKEY_LOC;

        /// <summary>
        /// An array of String denoting where the publication status is in the config
        /// </summary>
        private readonly String[] PUB_STATUS_LOC;

        /// <summary>
        /// An array of String denoting where the file hash is in the config.
        /// </summary>
        private readonly String[] HASH_LOC;

        private readonly String SERVER_NAME, PORT, TEMPLATE_PATH, CONN_FILE_PATH, LOG_FILE_PATH, FOLDER, MAKE_DESCRIPTOR_URL, GEOCAT_URL, GEOCAT_USERNAME, GEOCAT_PASSWORD, AGS_USERNAME, AGS_PASSWORD, EMAIL_SERVER, EMAIL_FROMADDRESS,EMAIL_TOADDRESSES,METADATA_URL, WEBADAPTOR_NAME;
        private readonly Boolean CHECK_HASH;

        private const string BAD_PAYLOADS_DIR = "Bad_Payloads";
        private const string PUBLISHED_DIR = "Published";

        public FileSystemWatcher(String dir, int interval, String pyLoc, String scriptLoc, String logLoc)
        {
            FILE_TRACKER = new NewFileTracker(dir);
            SCRIPT_CALLER = new ScriptCaller(pyLoc, scriptLoc);

            JsonReader configReader;
            try
            {
                configReader = new JsonReader(".");
            }
            catch (FileNotFoundException ex)
            {
                // Rethrow the exception to contain a more useful error message
                throw new FileNotFoundException("The FileSystemWatcher config could not be found! Make sure it is in the current directory: " + Directory.GetCurrentDirectory());
            }

            SMALLKEY_LOC = new String[] {
                    configReader.GetToken("smallkeyPath")[0].ToString(),
                    configReader.GetToken("smallkeyPath")[1].ToString()
                };

            PUB_STATUS_LOC = new String[] {
                configReader.GetToken("pubStatus")[0].ToString(),
                configReader.GetToken("pubStatus")[1].ToString()
            };

            HASH_LOC = new String[] {
                configReader.GetToken("hashPath")[0].ToString(),
                configReader.GetToken("hashPath")[1].ToString()
            };

            SERVER_NAME = configReader.GetValue("serverName");
            PORT = configReader.GetValue("port");
            TEMPLATE_PATH = configReader.GetValue("templatePath");
            CONN_FILE_PATH = configReader.GetValue("connFilePath");
            CHECK_HASH = Boolean.Parse(configReader.GetValue("checkHash"));
            LOG_FILE_PATH = logLoc;
            FOLDER = configReader.GetValue("folder");
            MAKE_DESCRIPTOR_URL = ""; //deprecated
            GEOCAT_URL = configReader.GetValue("geocatUrl");
            
            GEOCAT_USERNAME = configReader.GetValue("geocatUsername");
            GEOCAT_PASSWORD = configReader.GetValue("geocatPassword");

            AGS_USERNAME = configReader.GetValue("agsUsername");
            AGS_PASSWORD = configReader.GetValue("agsPassword");

            EMAIL_SERVER = configReader.GetValue("smtpservername");
            EMAIL_FROMADDRESS = configReader.GetValue("fromaddress");
            EMAIL_TOADDRESSES = configReader.GetValue("toaddresses");

            METADATA_URL = configReader.GetValue("metaDataUrl");

            WEBADAPTOR_NAME = configReader.GetValue("webAdaptorName");
            timer.Elapsed += new ElapsedEventHandler(timer_Elapsed);
            timer.Interval = interval;
        }

        public void Start()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(LOG_FILE_PATH));

            timer.Enabled = true;

            log("Press \'q\' to quit.");
            while (Console.Read() != 'q') ;
            log("Exited Successfully");
        }

        private void log(String msg)
        {
            if (msg.Equals("."))
            {
                Console.Write(msg);
            }
            else
            {
                Console.WriteLine(msg);
                File.AppendAllText(LOG_FILE_PATH, string.Format("{0}{1}", msg, Environment.NewLine));
            }
        }

        private void timer_Elapsed(object sender, ElapsedEventArgs e)
        {
            timer.Stop();

            String currentTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

            List<String> newFiles = FILE_TRACKER.getNewFiles();
            if (newFiles.Count > 0)
            {
                foreach (String fileName in newFiles)
                {
                    if (Path.GetExtension(fileName) == ".zip")
                    {
                        String unzippedPath;

                        log("");
                        log(new String('-', 76));
                        log(currentTime);
                        log("Payload Found, Unzipping: " + fileName);
                        var fullPath = Path.Combine(FILE_TRACKER.Dir, fileName);
                        try
                        {
                            unzippedPath = FileExtractor.extract(fullPath);
                        }
                        catch (IOException ex)
                        {
                            // Ignore files that are being used (for example, are in the process of getting copied over).
                            // TODO: Should these be cleaned up afterwards?
                            if (ex.Message.Contains("being used by another process"))
                            {
                                log("This file is being used.");
                                timer.Start();
                                return;
                            }
                            else
                            {
                                log("Error opening zip file.");
                                log(ex.StackTrace);
                                MoveToBadPayloads(fullPath);
                                timer.Start();
                                return;
                            }
                        }
                        catch (Exception ex)
                        {
                            log("Error extracting zip file.");
                            log(ex.StackTrace);
                            MoveToBadPayloads(fullPath);
                            timer.Start();
                            return;
                        }

                        JsonReader jsonReader;
                        try
                        {
                            jsonReader = new JsonReader(unzippedPath);
                        }
                        catch (Exception ex)
                        {
                            log("Error reading JSON file.");
                            log(ex.StackTrace);
                            return;
                        }

                        if (CHECK_HASH)
                        {
                            try
                            {
                                String expected;
                                try
                                {
                                    expected = jsonReader.GetValue(HASH_LOC);
                                }
                                catch (Exception ex)
                                {
                                    log("Hash validation aborted due to invalid hash path: " + String.Join(", ", HASH_LOC));
                                    return;
                                }

                                bool hashMatches = HASH_CHECKER.HashMatches(unzippedPath, expected);
                                if (hashMatches)
                                {
                                    log("Hash matches.");
                                }
                                else
                                {
                                    log("Hash does not match.");
                                    return;
                                }
                            }
                            catch (Exception ex)
                            {
                                log("Hash validation aborted due to unexpected error.");
                                log(ex.StackTrace);
                                return;
                            }
                        }
                        else
                        {
                            log("Hash check skipped.");
                        }

                        try
                        {
                            String smallkey, pubStatus;
                            try
                            {
                                smallkey = jsonReader.GetValue(SMALLKEY_LOC);
                            }
                            catch (Exception ex)
                            {
                                log("Script calling aborted due to invalid small key path: " + String.Join(", ", SMALLKEY_LOC));
                                return;
                            }

                            try
                            {
                                pubStatus = jsonReader.GetValue(PUB_STATUS_LOC);
                                //must be initial string, otherwise argument will be ignored and following arguments all messed up when call .py script
                                if (pubStatus.Length <= 0) pubStatus = "-1";
                                
                            }
                            catch (Exception ex)
                            {
                                log("Script calling aborted due to invalid publication status path: " + String.Join(", ", PUB_STATUS_LOC));
                                return;
                            }

                            log(String.Format("Executing script with the parameters:{7}Smallkey: {0}{7}Payload Path: {1}{7}Server Name: {2}{7}Port: {3}{7}Template Path: {4}{7}Connection File Path: {5}{7}Publish Status: {6}{7}Folder: {8}{7}MakeDescriptor URL (DEPRECATED): {9}{7}Catalogue URL: {10}{7}Catalogue User: {11}{7}ArcGIS User: {13}{7}Email Server: {15}{7}Email sender: {16}{7}Email receiver(s): {17}{7} Catalogue Metadata URL: {18}{7}Web Adaptor Name: {19}{7}",
                                smallkey, unzippedPath, SERVER_NAME, PORT, TEMPLATE_PATH, CONN_FILE_PATH, pubStatus, Environment.NewLine, FOLDER, MAKE_DESCRIPTOR_URL, GEOCAT_URL, GEOCAT_USERNAME, GEOCAT_PASSWORD, AGS_USERNAME, AGS_PASSWORD, EMAIL_SERVER, EMAIL_FROMADDRESS, EMAIL_TOADDRESSES, METADATA_URL, WEBADAPTOR_NAME));
                            log(SCRIPT_CALLER.executeScript(smallkey, unzippedPath, SERVER_NAME, PORT, TEMPLATE_PATH, CONN_FILE_PATH, pubStatus, FOLDER, MAKE_DESCRIPTOR_URL, GEOCAT_URL, GEOCAT_USERNAME, GEOCAT_PASSWORD, AGS_USERNAME, AGS_PASSWORD, EMAIL_SERVER, EMAIL_FROMADDRESS, EMAIL_TOADDRESSES, METADATA_URL, WEBADAPTOR_NAME));
                        }
                        catch (Exception ex)
                        {
                            log("Script calling aborted due to unexpected error");
                            log(ex.StackTrace);
                            return;
                        }
                    }
                    else
                    {
                        // Delete folders created 2+ hours ago.
                        var dirPath = Path.Combine(FILE_TRACKER.Dir, fileName);
                        if (Directory.Exists(dirPath))
                        {
                            var dirInfo = new DirectoryInfo(fileName);

                            // If created more than 2 hours ago, and 
                            // isn't the folder where published zips are being stored
                            if (Directory.GetLastWriteTimeUtc(dirPath).AddHours(2) < DateTime.UtcNow &&
                                dirInfo.Name != PUBLISHED_DIR &&
                                dirInfo.Name != BAD_PAYLOADS_DIR)
                            {
                                Directory.Delete(dirPath, true);
                            }
                        }
                        else
                        {
                            log("New File Found, But Not a Zip File: " + fileName);
                        }
                    }
                }
            }
            else
            {
                log(".");
            }

            timer.Start();
        }

        /// <summary>
        /// Moves the file to the Bad_Payloads directory.
        /// </summary>
        private void MoveToBadPayloads(string filePath)
        {
            if (File.Exists(filePath))
            {
                var fileName = Path.GetFileName(filePath);
                var badPayloadsPath = Path.Combine(FILE_TRACKER.Dir, BAD_PAYLOADS_DIR);
                File.Move(filePath, Path.Combine(badPayloadsPath, fileName));

                log("Moved bad payload to " + badPayloadsPath);
            }

        }
    }
}