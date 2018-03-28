import math
import random
from hashlib import md5


Symbols = '()*,-./0123456789:?@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqr'
Specials = {
    (1, 0):  's', (2, 0): 't', (1, -1): 'u', (1, 1): 'v', (0, 1): 'w',
    (0, -1): 'x', (3, 0): 'y', (2, -1): 'z', (2, 1): '~'
}

def delta(points):
    """
    Calculate motion delta and remove stall points. Internal function.

    >>> delta([(1, 1, 1), (2, 0, 3), (2, 0, 4), (2, 0, 5), (3, 1, 6), (3, 1, 7), (3, 1, 8)])
    [(1, -1, 2), (1, 1, 3), (0, 0, 2)]
    """

    dedup = [ n for p, n in zip([[None]*3] + points, points) if p[:2] != n[:2] ]
    if dedup[-1] != points[-1]:
        dedup.append(points[-1])
    diff = [tuple(round(n - p) for p, n in zip(*v)) for v in zip(dedup, dedup[1:])]
    return diff

def toSymbol(num):
    """
    Convert a number to its symbol representation. Internal function.

    Format: [sign][symbol of quotient][symbol of remainder]

    >>> toSymbol(0)
    '('
    >>> toSymbol(10)
    '3'
    >>> toSymbol(100)
    '$)P'
    >>> toSymbol(-100)
    '!$)P'
    >>> toSymbol(200)
    '$,.'
    """

    sign = '!' if num < 0 else ''
    num = abs(num)
    quotient, remainder = num // len(Symbols), num % len(Symbols)
    quotient = min(quotient, len(Symbols) - 1)
    quotient = ('$' + Symbols[quotient]) if quotient else ''
    return sign + quotient + Symbols[remainder]

def encodePoint(point):
    """
    Encode a point to its symbol tuple. Internal function.

    If the point is a pre-defined special point, put its symbol
    in Y array, otherwise put their symbols to corresponding array.

    >>> encodePoint((1, 1, 1))
    ('', 'v', ')')
    >>> encodePoint((10, 1, 1))
    ('3', ')', ')')
    >>> encodePoint((5, 6, 7))
    ('.', '/', '0')
    """

    if point[:2] in Specials:
        return ('', Specials[point[:2]], toSymbol(point[2]))
    return tuple(toSymbol(n) for n in point)

def toString(points):
    """
    Encode track. Calculate the field `aa` before perturb from raw position data. Internal function.

    >>> toString([[-22,-16,0],[0,0,0],[0,0,14],[0,-2,256],[0,-2,290],
    ... [2,-2,307],[3,-2,382],[6,-2,427],[9,-3,489],[9,-3,524]])
    'C(,(!!9!*tsy!)(!!($,oe$)3ZpP'
    """

    points = delta(points)
    res = map(''.join, zip(*map(encodePoint, points)))
    return '!!'.join(res)

def perturb(track, c, s):
    """
    Perturb encoded track with `c` and `s` from captcha data, output `aa`. Internal function.
    
    >>> perturb('C(,(!!9!*tsy!)(!!($,oe$)3ZpP', [12, 58, 98, 36, 43, 95, 62, 15, 12], '794c2a59')
    'C(,(!!9!*tsy!)(*!!($,Yoye$)3ZLpP'
    """

    result = track
    for i in range(0, len(s), 2):
        i = int(s[i:i+2], 16)
        l = (c[0] * i * i + c[2] * i + c[4]) % len(track)
        result = result[:l] + chr(i) + result[l:]
    return result

def userResponse(lastPos, challenge):
    """
    Calculate `userresponse` field.
    
    >>> userResponse(42, '4130c29e37423c27834e9a59115c40195m')
    'cccc000011'
    """

    tail = [ord(c) for c in challenge[32:34]]
    tail = [c - ord('0') if c <= ord('9') else c - ord('W') for c in tail]
    lastPos += 36 * tail[0] + tail[1]

    symbol = list(set(challenge))
    symbol.sort(key=lambda c: challenge.index(c))
    symbol = reversed(symbol[:5])

    multiplier = [50, 10, 5, 2, 1]
    result = ''
    for s, m in zip(symbol, multiplier):
        result += s * (lastPos // m)
        lastPos %= m
    return result

def encode(points, info):
    rp = info['gt'] + info['challenge'][:32] + str(points[-1][2])
    rp = md5(rp.encode('utf8')).hexdigest()
    return {
        'userresponse': userResponse(points[-1][0], info['challenge']),
        'passtime': points[-1][2],
        'imgload': random.randrange(140, 200),
        'aa': perturb(toString(points), info['c'], info['s']),
        'ep': {"v":"6.0.9"},
        'rp': rp,
    }

if __name__ == "__main__":
    import doctest
    doctest.testmod()
