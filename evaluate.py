from generator import CaptchaGenerator
from tqdm import tqdm
import sys


total = 1000
captcha = CaptchaGenerator(100, 256, 1, sys.argv[1])
bar = tqdm(zip(range(total), captcha), total=total, smoothing=0)
for i, res in bar:
    bar.desc = 'success rate: %3.0f%%' % (captcha.successRate * 100)
captcha.close()
bar.close()
