import json
from Crypto.Cipher import AES
from Crypto.Util.number import bytes_to_long


def ephemeral():
    """
    Return random 16 hex character. Internal function.
    """

    return '0' * 16

def aes(key, msg):
    """
    Encrypt `msg` by AES-CBC with an ephemeral `key`. Internal function.
    """

    pad = -len(msg) % 16
    if pad == 0:
        pad = 16
    msg = msg + chr(pad) * pad
    enc = AES.new(key, AES.MODE_CBC, IV='0'*16).encrypt(msg)
    return enc

def rsa(key):
    """
    Encrypt our ephemeral `key` by RSA public key cryptosystem. Internal function.
    """

    # return self.RSA.encrypt(self.ephemeral)
    assert(key == '0' * 16)
    return (
        '50775b34a8fd583a9ffb801cfafd725d197b7cb180e14a4714cc07cf89619bd9' +
        'bdf4d83dafe4e3b740738e51f6670d92e7cfbdedb637c8ea238464424b7d68d2' +
        '07e7e7b1605fc3cb3db6470095986615c3891e2dd3bdd872ce235bdaa5ccd149' +
        '2730da4f9a9aff74f2682ef0e37e012a82ee9a92da82da6b710b26ec73dcc3e1'
        )

def base64(msg):
    """
    A strange base64 encoding. Internal function.
    """

    symbol = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()'
    masks = [0x6f0000, 0x90b400, 0x004b14, 0x0000eb]
    def mix (block, mask):
        res = 0
        for i in range(23, -1, -1):
            if (mask >> i & 1):
                res = (res << 1) + (block >> i & 1)
        return symbol[res]
    res = ''
    for i in range(0, len(msg), 3):
        block = msg[i: i+3]
        l = len(block)
        if isinstance(block, str):
            block = block.encode('utf8')
        block = bytes_to_long(block) << (8 * (3 - l))
        res += ''.join(mix(block, m) for m in masks[:l+1]) + '.' * (3 - l)
    return res

def encrypt(obj):
    """
    Encrypt our payload object to `w`
    """

    msg = json.dumps(obj)
    key = ephemeral()
    return base64(aes(key, msg)) + rsa(key)
