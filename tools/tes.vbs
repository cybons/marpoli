Dim hostname, macAddress, objHTTP, url, response

' ユーザーからのインプットを取得
hostname = InputBox("端末名を入力してください:", "端末名入力")
macAddress = InputBox("MACアドレスを入力してください:", "MACアドレス入力")

' HTTPリクエストの作成
Set objHTTP = CreateObject("MSXML2.ServerXMLHTTP.6.0")
url = "http://localhost:8000/mac_address_checker/check_mac/"

objHTTP.Open "POST", url, False
objHTTP.setRequestHeader "Content-Type", "application/json"
objHTTP.Send "{""hostname"":""" & hostname & """, ""mac_address"":""" & macAddress & """}"

' レスポンスを表示
response = objHTTP.responseText
MsgBox "結果: " & response

Set objHTTP = Nothing