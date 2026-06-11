import hashlib
data = open('block-953250-header.bin','rb').read()
print(hashlib.sha256(hashlib.sha256(data).digest()).digest()[::-1].hex())