Sub EseguiPythonScript()
    Dim objShell As Object
    Dim PythonExePath, PythonScriptPath As String

    Set objShell = VBA.CreateObject("Wscript.Shell")

    ' Percorso all'eseguibile Python
    PythonExePath = """<YOUR_PATH>"""
    
    ' Percorso allo script Python
    PythonScriptPath = "<YOUR_PATH>"
    
    objShell.Run PythonExePath & PythonScriptPath

End Sub
