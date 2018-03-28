import numpy as np
import random


async def solve(challenge):
    """
    Generate challenge answer.
    """
    d = distance(await challenge.bg, await challenge.fullbg)
    return motion(d)

def distance(a, b):
    """
    Find x coordinate of answer.
    """

    diff = np.abs(a - b) > 50
    diff = np.max(np.max(diff, 2), 0)
    d = next(i for i, e in enumerate(diff)if e) - 6
    return d

def motion(d):
    """
    Simulate mouse motion.
    """
    d -= 4

    y2 = 6 if d > 100 else d
    seg2 = np.arange(0, (d-y2) * 10, 20)
    seg2 = np.tanh(seg2 / (d-y2) * 0.3) * (d-y2) / 0.995
    seg3 = np.arange(0, y2 * 10 + 200, 20)
    seg3 = np.tanh(seg3 / y2 * 0.3) * y2 / 0.995 + (d-y2)
    x = np.concatenate([seg2, seg3]).astype(int).tolist()
    x = [n - p for n, p in zip(x[1:], x)]
    for _ in range(len(x) // 2):
        i = random.randrange(len(x) - 13)
        j = random.randrange(len(x) - 13)
        if i == j or x[i] // 4 == 0: continue
        d = random.randrange(x[i] // 4)
        x[i] -= d
        x[j] += d
    x = [0, 1, 1, 2] + x
    x = np.cumsum(x).astype(int).tolist()

    t = np.random.rand(len(x)) * 5 + 18
    t[:2] = [0, random.randrange(300, 600)]
    t = np.cumsum(t).astype(int).tolist()

    y = np.zeros_like(x)
    for i in range(3):
        y[random.randrange(len(x))] = 1
    y = np.cumsum(y).astype(int).tolist()

    data = [[random.randrange(-25, -15), random.randrange(-25, -15), 0]] + list(zip(x, y, t))

    return data
