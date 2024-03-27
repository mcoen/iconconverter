import sys
import time
import random

from iconconverter import IconFontConverter

start = time.time() * 1000

with open('./icons/available.txt') as f:
    availableIcons = f.read().splitlines()

f.close()

if len(availableIcons) == 1:
    stop = 1
else:
    stop = len(availableIcons) - 1

index = random.randrange(start=0, stop=stop)
usedIcon = availableIcons[index]

iconFont = IconFontConverter('./fa/fontawesome.css', './fa/fa-regular-400.ttf')
iconFont.exportIcon(usedIcon, 200, color='#5DADE2')

availableIcons.remove(usedIcon)
with open(r'./icons/available.txt', 'w') as f:
    for availableIcon in availableIcons:
        f.write(f"{availableIcon}\n")

f.close()

f = open("./icons/reserved.txt", "a")
f.write(f"{usedIcon}\n")
f.close()

end = time.time() * 1000
print('Runtime = ' + str(end - start) + 'ms')
