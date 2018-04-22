from aiohttp import web
import socketio
import random

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)


def generator():
    n = 100
    ar = []
    i = 1
    # задаем случайные величины (в нашем случае - цена)
    while i < n + 1:
        ar.append(round(i, 3))
        i = i + 1
    print(ar)
    ps = []
    # зададим вероятности выпадания этих величин(биномиальный зр)
    ps = [1/n for k in range(0, n)]
    print(ps)
    intervals = [ps[0]]
    for i in range(1, n):
        intervals.append(round(intervals[i - 1] + ps[i], 3))
    print(intervals)
    while True:
        tmp = random.random()
        for j in range(0, n):
            if tmp < intervals[j]:
                yield ar[j]
                break


g = generator()
bd = {}
cur_price = 0


def init_func(argv):
    sio.start_background_task(background_task)
    return app


@sio.on('connect')
async def connect(sid, environ):
    print("connect ", sid)
    await sio.send(sid)

@sio.on('login')
async def message(sid, data):
    bd[sid] = [data, 100, 0, 0]


@sio.on('buy')
async def message(sid, data):
    print('buyed',bd[sid][0])
    if bd[sid][1] - cur_price >= 0:
        bd[sid][1] -= cur_price
        bd[sid][2] += 1
        bd[sid][3] = 0


@sio.on('sell')
async def message(sid, data):
    print('selled',bd[sid][0])
    if bd[sid][2] != 0:
        bd[sid][1] += cur_price
        bd[sid][2] -= 1
        bd[sid][3] = 0


@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)
    bd.pop(sid)

async def background_task():
    global cur_price
    while True:
        await sio.sleep(2)
        cur_price = next(g)
        # print(bd)
        print('background    {}'.format(cur_price))
        for user in bd.copy():
            if bd[user][3] <= 10:
                bd[user][3] += 2
            if bd[user][3] > 10:
                await sio.disconnect(user)
                bd.pop(user)
        await sio.emit('message', cur_price)
        mas_out = sorted(bd.values(), key=(lambda x: x[1]), reverse=True)
        bd_out = dict(zip([i for i in range(len(mas_out))], mas_out))
        print(bd_out)
        await sio.emit('top', bd_out)
