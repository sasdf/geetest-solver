import aiohttp
import asyncio
import time
import threading
import queue

from api import Challenge
import solver


class CaptchaGenerator(object):
    def __init__(self, qlimit, plimit, climit, interval, gt):
        """
        A generator that will produce valid captcha.
        
        qlimit: Maximum number of buffered solved captcha.
        plimit: Maximum number of pending unsolved captcha.
        climit: Maximum concurrent connection.
        interval: Minimum time interval between two concurrent connection.
        gt: geetest key.
        """

        self.gt = gt
        self.climit = climit
        self.plimit = plimit
        self.interval = interval
        self.output = queue.Queue(qlimit)
        self.lock = threading.Lock()
        self._successRate = 0
        self.closed = False
        self.thread = threading.Thread(target=self.worker)
        self.thread.start()
        self.history = {}

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

    async def gen(self):
        c = await Challenge(self).load()
        distance = await solver.distance(c)
        if distance in self.history:
            answer = self.history[distance]
        else:
            answer = solver.motion(distance)
        res = await c.validate(answer)
        self.pending.release()
        if res['message'] == 'success':
            self.history[distance] = answer
            with self.lock:
                self._successRate *= 0.99
                self._successRate += 0.01
            res['challenge'] = c.info['challenge']
            self.output.put(res)
        else:
            if distance in self.history:
                del self.history[distance]
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
        last = 0
        self.pending = asyncio.Semaphore(self.plimit)
        self.concurrent = asyncio.Semaphore(self.climit)
        async with aiohttp.ClientSession() as session:
            self.session = session
            #  for i in range(10):
            while not self.closed:
                await self.pending.acquire()
                now = time.time() * 1000
                if now - last < self.interval:
                    await asyncio.sleep((self.interval - now + last) / 1000)
                last = now
                asyncio.ensure_future(self.gen())

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
