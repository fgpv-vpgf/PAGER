using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;

namespace FileSystemWatcher
{
    
    public class NewFileTracker
    {
        private HashSet<String> prevFiles = new HashSet<String>();
        private readonly String dir;

        public String Dir
        {
            get { return dir;  }
        }

        public NewFileTracker(String dir) {
            this.dir = dir;
        }


        /// <summary>
        /// Returns a list of new file and directory names in the directory. 
        /// </summary>
        /// <returns></returns>
        public List<String> getNewFiles() 
        {
            List<String> newFiles = new List<String>();

            if (Directory.Exists(dir))
            {
                // Get files and directories.
                //string[] fileNames = Directory.GetFiles(dir).Concat(Directory.GetDirectories(dir)).ToArray();
                
                string[] fileNames = Directory.GetFiles(dir);

                foreach(String url in fileNames) {
                    String file = Path.GetFileName(url);
                    //comment checking if file exists in the list, since we would run update service in the same run
                    //if (!prevFiles.Contains(file)) {
                        prevFiles.Add(file);
                        newFiles.Add(file);
                    //}
                }
            }            
            
            return newFiles;
        }
    }
}
