using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;
using System.IO;

namespace FileSystemWatcher
{
    public class JsonReader
    {
        private readonly JToken JSON_OBJ;

        public JsonReader(String dir)
        {
            if (Directory.Exists(dir))
            {
                string[] fileNames = Directory.GetFiles(dir);

                String jsonPath;

                try
                {
                    // the "First" function will throw an InvalidOperatonException
                    // if no target is found
                    jsonPath = fileNames.First((String file) =>
                    {
                        return Path.GetExtension(file) == ".json";
                    });
                } catch (InvalidOperationException ex)
                {
                    // Rethrow the Exception to give a more meaningful error message
                    throw new FileNotFoundException("No JSON file was found in the directory!");
                }

                String jsonStr = System.IO.File.ReadAllText(jsonPath);
                JSON_OBJ = JsonConvert.DeserializeObject<JToken>(jsonStr);
            }
            else
            {
                throw new FileNotFoundException("The given directory: " + dir + " is invalid!");
            }            
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="jsonPath">the URL of the JSON file</param>
        /// <param name="hashValueLoc">an array of String representing the path to the hash value 
        /// in the JSON file</param>
        /// <returns></returns>
        public String GetValue(params String[] path)
        {
                return GetToken(path).ToString();
        }

        public JToken GetToken(params String[] path)
        {
            JToken jsonObj = JSON_OBJ;
            foreach (String key in path)
            {
                jsonObj = jsonObj[key];
            }
            return jsonObj;
        }
    }
}
