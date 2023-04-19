using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

public static class ImportScript
{
    [MenuItem("Harbinger/Import Script Setup")]
	public static void ImportPythonSetup()
	{
		string srcPath = System.IO.Path.GetFullPath("Packages/com.demo.harbinger/Editor/python");
		string destPath = System.IO.Path.Combine(Application.dataPath, "Harbinger", "python");
		UnityEngine.Debug.Log(srcPath + " " + destPath);
		if(System.IO.Directory.Exists(destPath))
		{
			System.IO.Directory.Delete(destPath, true);
		}
		FileUtil.CopyFileOrDirectory(srcPath, destPath);
	}
}
