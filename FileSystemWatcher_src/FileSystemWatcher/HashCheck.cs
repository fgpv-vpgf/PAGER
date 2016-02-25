using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace FileSystemWatcher
{
    public class HashChecker
    {
        public HashChecker()
        {
        }

        /// <summary>
        /// Returns the SHA-256 hash of the given file.
        /// </summary>
        /// <param name="path"></param>
        /// <returns></returns>
        private String GetHash(String path)
        {
            SHA256 mySHA256 = SHA256Managed.Create();

            FileStream fileStream = File.Open(path, FileMode.Open);
            // Be sure it's positioned to the beginning of the stream.
            fileStream.Position = 0;
            byte[] hashValue = mySHA256.ComputeHash(fileStream);

            // Close the file.
            fileStream.Close();

            return ByteArrayToHexString(hashValue);
        }

        private static string ByteArrayToHexString(byte[] ba)
        {
            string hex = BitConverter.ToString(ba);
            return hex.Replace("-", "");
        }

        /// <summary>
        /// Returns true if the SHA-256 hash of the first .zip file in the given dir matches
        /// the SHA-256 hash stored in the first .json file in the given dir.
        /// </summary>
        /// <param name="dir"></param>
        /// <returns></returns>
        public Boolean HashMatches(String dir, String expected)
        {
            if (Directory.Exists(dir))
            {
                string[] fileNames = Directory.GetFiles(dir);

                // Find the first file in the directory that ends in .zip
                String zipPath = fileNames.First((String file) =>
                {
                    return Path.GetExtension(file) == ".zip";
                });

                if (zipPath == null)
                {
                    throw new FileNotFoundException("A zip file was not found in the directory!");
                }

                String actual = GetHash(zipPath);

                //Console.WriteLine(String.Format("Expected: {0}\nActual: {1}", expected, actual));

                return expected.Equals(actual);
            }
            else
            {
                throw new FileNotFoundException("The given directory: " + dir + " is invalid!");
            }
        }

        // Print the byte array in a readable format.
        private void PrintByteArray(byte[] array)
        {
            int i;
            for (i = 0; i < array.Length; i++)
            {
                Console.Write(String.Format("{0:X2}", array[i]));
                if ((i % 4) == 3) Console.Write(" ");
            }
            Console.WriteLine();
        }
    }
}