' access_data.vbs

Option Explicit

Dim objConnection, objRecordset, objField, objTable, objQuery
Dim strDatabasePath, objFSO, objFile

strDatabasePath = WScript.Arguments.Item(0)

' Create FileSystemObject
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Create database connection
Set objConnection = Wscript.CreateObject("ADODB.Connection")
objConnection.Open "Driver={Microsoft Access Driver (*.mdb, *.accdb)}; DBQ=" & strDatabasePath 

' Get tables
Set objFile = objFSO.CreateTextFile("tables.csv", True)
Set objRecordset = objConnection.OpenSchema(20)
Do Until objRecordset.EOF
    If objRecordset("TABLE_TYPE") = "TABLE" Then
        objFile.WriteLine objRecordset("TABLE_NAME")
    End If
    objRecordset.MoveNext
Loop
objFile.Close

' Get queries
Set objFile = objFSO.CreateTextFile("queries.csv", True)
Set objRecordset = objConnection.OpenSchema(20)
Do Until objRecordset.EOF
    If objRecordset("TABLE_TYPE") = "VIEW" Then
        objFile.WriteLine objRecordset("TABLE_NAME")
    End If
    objRecordset.MoveNext
Loop
objFile.Close

objConnection.Close
