using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace FileSystemWatcher
{
    public class Program
    {
        public static void Main(string[] args)
        {
           
            /*args = new String[] { 
                "C:/ECDMP/ECDMP_drop", 
                "1000", 
                "C:/PAGER/PAGER_Scripts/workflow.py", 
                "C:/Python27/ArcGIS10.1/python.exe",
                "C:/inetpub/wwwroot/pub_log.txt"}; */

            if (args.Length < 1)
            {
                Console.WriteLine("Usage: FileSystemWatcher <dir> <interval> <scriptLoc> <pyLoc> <logLoc>");
                Console.WriteLine("<dir> The directory containing the zip files");
                Console.WriteLine("<interval> Optional: The number of milliseconds between each check");
                Console.WriteLine("<scriptLoc> The location of the script to call");
                Console.WriteLine("<pyLoc> The location of python");
                Console.WriteLine("<logLoc> The location of the log file");
                return;
            }


            int interval;
            if (args.Length >= 2)
            {
                if (!Int32.TryParse(args[1], out interval) || interval < 1)
                {
                    Console.WriteLine("Invalid interval: " + args[1]);
                    Console.WriteLine("Interval must be a natural number");
                    return;
                }
            }
            else
            {
                // If no interval is specified, the default is 30 seconds
                interval = 30000;

                Console.WriteLine("No interval specified, using default: " + interval);
            }

            String scriptLoc;
            if (args.Length >= 3)
            {
                scriptLoc = args[2];
            }
            else
            {
                scriptLoc = "";

                Console.WriteLine("No scriptLoc specified, using default: " + scriptLoc);
            }

            String pyLoc;
            if (args.Length >= 4)
            {
                pyLoc = args[3];
            }
            else
            {
                pyLoc = "";

                Console.WriteLine("No pyLoc, using default: " + pyLoc);
            }

            String logLoc;
            if (args.Length == 5)
            {
                logLoc = args[4];
            }
            else
            {
                logLoc = "";

                Console.WriteLine("No logLoc, using default: " + logLoc);
            }

            if (args.Length > 5)
            {
                Console.Write("Too many arguments, rest of the arguments are ignored: ");
                Console.WriteLine(String.Join(", ", SubArray(args, 4)));
            }

            FileSystemWatcher fileSystemWatcher = new FileSystemWatcher(args[0], interval, pyLoc, scriptLoc, logLoc);
            fileSystemWatcher.Start();
        }

        public static T[] SubArray<T>(T[] data, int index)
        {
            return SubArray(data, index, data.Length - index);
        }

        public static T[] SubArray<T>(T[] data, int index, int length)
        {
            T[] result = new T[length];
            Array.Copy(data, index, result, 0, length);
            return result;
        }
    }
}
