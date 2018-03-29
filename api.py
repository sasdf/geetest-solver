import re
import json
from PIL import Image
import numpy as np
import time
import random
import asyncio
import aiohttp
import io

from encryption import encrypt
import track


URLs = {
    'get': 'http://api.geetest.com/get.php',
    'validate': 'http://api.geetest.com/ajax.php'
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'Referer': 'http://example.com/',
}
imageOffset = [[
    157, 145, 265, 277, 181, 169, 241, 253, 109, 97,
    289, 301, 85,  73,  25,  37,  13,  1,   121, 133,
    61,  49,  217, 229, 205, 193
], [
    145, 157, 277, 265, 169, 181, 253, 241, 97,  109,
    301, 289, 73,  85,  37,  25,  1,   13,  133, 121,
    49,  61,  229, 217, 193, 205
]]


class Challenge(object):
    def __init__(self, context):
        self.context = context

    async def load(self):
        async with self.context.concurrent:
            async with self.context.session.get(URLs['get'], params={'gt': self.context.gt}, headers=headers) as req:
                if req.status != 200:
                    raise ValueError('Response status code %d not acceptable' % req.status)
                res = await req.text()
        challenge = re.search(r'Geetest\((\{[^\}]*?\})', res)
        if challenge is None:
            raise ValueError('Unknown response from server')
        self.info = json.loads(challenge[1])
        self.server = 'http://' + self.info['static_servers'][0]
        self.timestamp = time.time()
        return self

    async def getImage(self, url):
        async with self.context.concurrent:
            async with self.context.session.get(url, headers=headers) as req:
                if req.status != 200:
                    raise ValueError('Response status code %d not acceptable' % req.status)
                raw = io.BytesIO(await req.read())
        raw = np.asarray(Image.open(raw))
        img = np.empty((116, 260, 3), dtype=np.uint8)
        for y, row in enumerate(imageOffset):
            oy = (1-y) * 58
            for x, off in enumerate(row):
                img[y*58:(y+1)*58, x*10:(x+1)*10] = raw[oy:oy+58, off:off+10]
        return img.astype(float)

    @property
    def bg(self):
        return self.getImage(self.server+self.info['bg'])

    @property
    def fullbg(self):
        return self.getImage(self.server+self.info['fullbg'])

    def params(self, motion):
        w = encrypt(track.encode(motion, self.info))
        return {
            'gt': self.info['gt'],
            'challenge': self.info['challenge'],
            'w': w,
            'callback': 'geetest_' + str(int(time.time()*1000))
            }

    async def validate(self, motion):
        params = self.params(motion)
        passtime = motion[-1][2] / 1000
        remaining = passtime + 0.5 - time.time() + self.timestamp
        if remaining > 0:
            await asyncio.sleep(remaining)
        async with self.context.concurrent:
            async with self.context.session.get(URLs['validate'], params=params, headers=headers) as req:
                if req.status != 200:
                    raise ValueError('Response status code %d not acceptable' % req.status)
                res = await req.text()
        res = json.loads(res[len(params['callback'])+1:-1])
        return res
