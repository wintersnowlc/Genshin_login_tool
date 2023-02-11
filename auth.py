import hashlib

while True:
    mac = input('请输入机器码：').strip()
    true_str = 'salt=20230209' + mac
    true_md5 = hashlib.md5(true_str.encode('u8')).hexdigest()[8:16]
    print('激活码为：')
    print(true_md5)
