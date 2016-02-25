using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Diagnostics;

namespace FileSystemWatcher
{
    public class ScriptCaller
    {
        private readonly String pyLoc;
        private readonly String scriptLoc;

        public ScriptCaller(String pyLoc, String scriptLoc)
        {
            this.pyLoc = pyLoc;
            this.scriptLoc = scriptLoc;
        }


        public String executeScript(String smallKey, String zipPath, String serverName, String port, String templatePath, String connFilePath, String pubStatus, String folder, String makeDescriptorUrl, String geocatUrl, String geocatUsername, String geocatPassword, String agsUsername, String agsPassword, String emailServer, String fromAddress, String toAddresses, String metaDataUrl, String webAdaptorName)
        {
            string args = String.Format("\"{0}\" {1} \"{2}\" {3} {4} \"{5}\" \"{6}\" {7} {8} {9} {10} {11} {12} {13} {14} {15} {16} {17} {18} {19}",
                    scriptLoc, smallKey, zipPath, serverName, port, templatePath, connFilePath, pubStatus, folder, makeDescriptorUrl, geocatUrl, geocatUsername, geocatPassword, agsUsername, agsPassword, emailServer, fromAddress, toAddresses, metaDataUrl, webAdaptorName);
            //Console.WriteLine(args);

            // create the ProcessStartInfo using "cmd" as the program to be run,
            // and "/c " as the parameters.
            // Incidentally, /c tells cmd that we want it to execute the command that follows,
            // and then exit.
            System.Diagnostics.ProcessStartInfo procStartInfo =
                new System.Diagnostics.ProcessStartInfo();
            procStartInfo.FileName = pyLoc;
            procStartInfo.Arguments = args;

            // The following commands are needed to redirect the standard output.
            // This means that it will be redirected to the Process.StandardOutput StreamReader.
            procStartInfo.RedirectStandardOutput = true;
            procStartInfo.RedirectStandardError = true;
            procStartInfo.UseShellExecute = false;
            // Do not create the black window.
            procStartInfo.CreateNoWindow = true;

            // Run the external process & wait for it to finish
            using (Process proc = Process.Start(procStartInfo))
            {
                //proc.BeginOutputReadLine();
                //proc.BeginErrorReadLine();

                proc.WaitForExit();
                
                // Get the output into a string
                var output = String.Format("Script exited with code: {0}\nOutput: {1}", proc.ExitCode, proc.StandardOutput.ReadToEnd());

                // Don't include error if there is none.
                var stdError = proc.StandardError.ReadToEnd();
                if (!String.IsNullOrEmpty(stdError))
                {
                    output += Environment.NewLine + "Error: " + stdError;
                }

                return output;
            }
            
        }
    }
}
