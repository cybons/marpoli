Dim hostname, macAddress, objHTTP, url, response

' ���[�U�[����̃C���v�b�g���擾
hostname = InputBox("�[��������͂��Ă�������:", "�[��������")
macAddress = InputBox("MAC�A�h���X����͂��Ă�������:", "MAC�A�h���X����")

' HTTP���N�G�X�g�̍쐬
Set objHTTP = CreateObject("MSXML2.ServerXMLHTTP.6.0")
url = "http://localhost:8000/mac_address_checker/check_mac/"

objHTTP.Open "POST", url, False
objHTTP.setRequestHeader "Content-Type", "application/json"
objHTTP.Send "{""hostname"":""" & hostname & """, ""mac_address"":""" & macAddress & """}"

' ���X�|���X��\��
response = objHTTP.responseText
MsgBox "����: " & response

Set objHTTP = Nothing