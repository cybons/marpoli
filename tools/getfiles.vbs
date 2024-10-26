Option Explicit

Sub SearchExcelFilesRecursively()
    Dim srcFolder As String
    Dim tempFolder As String
    Dim fso As Object
    Dim resultSheet As Worksheet
    Dim fileList As Collection
    Dim fileItem As Variant
    Dim lastRow As Long
    Dim searchPrefix As String
    Dim excludePrefix As String
    Dim startTime As Double
    
    ' 処理開始時間を記録
    startTime = Timer
    
    ' 設定
    srcFolder = "E:\マイドライブ\送付用\" ' ルートフォルダのパスを設定
    tempFolder = Environ("TEMP") & "\ExcelTemp\"
    searchPrefix = "\\"
    excludePrefix = "\\server\"
    
    ' ファイルシステムオブジェクトの作成
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    ' 一時フォルダの作成（存在しない場合）
    If Not fso.FolderExists(tempFolder) Then
        fso.CreateFolder tempFolder
    End If
    
    ' 結果出力用シートの準備
    On Error Resume Next
    Set resultSheet = ThisWorkbook.Worksheets("Results")
    If resultSheet Is Nothing Then
        Set resultSheet = ThisWorkbook.Worksheets.Add
        resultSheet.Name = "Results"
    End If
    On Error GoTo 0
    resultSheet.Cells.Clear
    ' ヘッダーの設定
    resultSheet.Range("A1:D1").Value = Array("値", "ファイル名", "ファイルパス", "ファイルバージョン")
    lastRow = 2
    
    ' ファイルリストの初期化
    Set fileList = New Collection
    
    ' ルートフォルダからすべてのExcelファイルを取得
    GetExcelFilesRecursive srcFolder, fileList, fso
    
    ' 取得したファイル数を表示
    Debug.Print "Total Excel files found: " & fileList.Count
    
    ' 各ファイルを処理
    For Each fileItem In fileList
        Dim filePath As String
        Dim fileName As String
        Dim fileExt As String
        Dim isOldVersion As String
        Dim wb As Workbook
        Dim ws As Worksheet
        Dim cell As Range
        
        filePath = fileItem
        fileName = fso.GetFileName(filePath)
        fileExt = LCase(fso.GetExtensionName(filePath))
        If fileExt = "xls" Then
            isOldVersion = "Old Version"
        Else
            isOldVersion = ""
        End If
        
        ' ファイルを一時フォルダにコピー
        On Error Resume Next
        fso.CopyFile filePath, tempFolder & fileName, OverWriteFiles:=True
        If Err.Number <> 0 Then
            Debug.Print "Failed to copy: " & filePath & " Error: " & Err.Description
            Err.Clear
            On Error GoTo 0
            GoTo NextFile
        End If
        On Error GoTo 0
        
        ' ファイルを開く
        On Error Resume Next
        Set wb = Workbooks.Open(fileName:=tempFolder & fileName, ReadOnly:=True, UpdateLinks:=False)
        If Err.Number <> 0 Then
            Debug.Print "Failed to open: " & tempFolder & fileName & " Error: " & Err.Description
            Err.Clear
            On Error GoTo 0
            GoTo NextFile
        End If
        On Error GoTo 0
        
        ' 各シートをループ
        For Each ws In wb.Worksheets
            ' シート内の全セルをループ（UsedRangeで使用されている範囲を取得）
            For Each cell In ws.UsedRange
                If Not IsError(cell.Value) Then
                    If VarType(cell.Value) = vbString Then
                        If Left(cell.Value, Len(searchPrefix)) = searchPrefix Then
                            If Left(cell.Value, Len(excludePrefix)) <> excludePrefix Then
                                ' 結果を記録
                                resultSheet.Cells(lastRow, 1).Value = cell.Value
                                resultSheet.Cells(lastRow, 2).Value = fileName
                                resultSheet.Cells(lastRow, 3).Value = filePath
                                resultSheet.Cells(lastRow, 4).Value = isOldVersion
                                lastRow = lastRow + 1
                            End If
                        End If
                    End If
                End If
            Next cell
        Next ws
        
        ' ファイルを閉じる
        wb.Close SaveChanges:=False
        
NextFile:
    Next fileItem
    
    ' 一時フォルダのクリーンアップ（オプション）
    ' Uncomment the following lines if you want to delete the temp folder after processing
    ' On Error Resume Next
    ' fso.DeleteFolder tempFolder, True
    ' On Error GoTo 0
    
    ' 処理完了メッセージ
    MsgBox "検索が完了しました。結果は 'Results' シートをご覧ください。" & vbCrLf & _
           "総ファイル数: " & fileList.Count & vbCrLf & _
           "処理時間: " & Format(Timer - startTime, "0.00") & " 秒", vbInformation
End Sub

' 再帰的にExcelファイルを取得するサブルーチン
Sub GetExcelFilesRecursive(ByVal folderPath As String, ByRef fileList As Collection, ByVal fso As Object)
    Dim folder As Object
    Dim subFolder As Object
    Dim file As Object
    Dim validExtensions As Variant
    Dim ext As Variant
    
    ' 対象とする拡張子
    validExtensions = Array("xls", "xlsx", "xlsm")
    
    On Error Resume Next
    Set folder = fso.GetFolder(folderPath)
    If Err.Number <> 0 Then
        Debug.Print "Failed to access folder: " & folderPath & " Error: " & Err.Description
        Err.Clear
        Exit Sub
    End If
    On Error GoTo 0
    
    ' フォルダ内のファイルをチェック
    For Each file In folder.Files
        ext = LCase(fso.GetExtensionName(file.Name))
        If IsInArray(ext, validExtensions) Then
            fileList.Add file.Path
        End If
    Next file
    
    ' サブフォルダを再帰的に検索
    For Each subFolder In folder.SubFolders
        GetExcelFilesRecursive subFolder.Path, fileList, fso
    Next subFolder
End Sub

' 配列内に値が存在するかチェックする関数
Function IsInArray(ByVal stringToBeFound As String, ByVal arr As Variant) As Boolean
    Dim element As Variant
    For Each element In arr
        If element = stringToBeFound Then
            IsInArray = True
            Exit Function
        End If
    Next element
    IsInArray = False
End Function


