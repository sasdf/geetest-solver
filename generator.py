import aiohttp
import asyncio
import time
import threading
import queue

from api import Challenge
from solver import solve


class CaptchaGenerator(object):
    def __init__(self, qlimit, climit, interval, gt):
        """
        A generator that will produce valid captcha.
        
        qlimit: Maximum number of buffered captcha.
        climit: Maximum concurrent connection.
        interval: Minimum time interval between two concurrent connection.
        gt: geetest key.
        """

        self.gt = gt
        self.climit = climit
        self.interval = interval
        self.output = queue.Queue(qlimit)
        self.lock = threading.Lock()
        self._successRate = 0
        self.closed = False
        self.thread = threading.Thread(target=self.worker)
        self.thread.start()

    def __iter__(self):
        return self

    def __next__(self):
        res = self.output.get()
        if res is None:
            raise StopIteration()
        return res

    def worker(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.executor())
        self.loop.stop()
        self.loop.close()

    async def get(self):
        c = await Challenge(self.gt, self.session).load()
        res = await c.validate(await solve(c))
        self.concurrent.release()
        if res['message'] == 'success':
            with self.lock:
                self._successRate *= 0.99
                self._successRate += 0.01
            self.output.put(res)
        else:
            with self.lock:
                self._successRate *= 0.99

    async def executor(self):
        """
        A generator that will produce valid captcha.
        
        gt: geetest key.
        qlimit: Maximum size of buffered captcha.
        climit: Maximum concurrent connection.
        interval: Minimum time interval between two concurrent connection.
        """
        self.concurrent = asyncio.Semaphore(self.climit)
        last = 0
        async with aiohttp.ClientSession() as session:
            self.session = session
            #  for i in range(10):
            while not self.closed:
                await self.concurrent.acquire()
                now = time.time() * 1000
                if now - last < self.interval:
                    await asyncio.sleep((self.interval - now + last) / 1000)
                last = now
                asyncio.ensure_future(self.get())

            for i in range(self.climit):
                await self.concurrent.acquire()
        self.output.put(None)

    @property
    def successRate(self):
        with self.lock:
            return self._successRate

    def close(self):
        self.closed = True
        if (self.output.qsize() > 0):
            self.output.get()
