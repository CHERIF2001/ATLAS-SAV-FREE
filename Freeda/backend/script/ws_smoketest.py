import asyncio
import json
import httpx
import websockets

async def run():
    async with httpx.AsyncClient() as client:
        r = await client.post('http://127.0.0.1:8000/tickets', json={'initial_message':'Test WS initial'}, timeout=20.0)
        print('CREATE STATUS', r.status_code)
        print(r.text)
        data = r.json()
        ticket_id = data['ticket_id']

    uri = f'ws://127.0.0.1:8000/ws/{ticket_id}'
    async with websockets.connect(uri) as ws:
        # receive snapshot
        msg = await ws.recv()
        print('WS SNAPSHOT', msg)

        async def post_message():
            await asyncio.sleep(0.5)
            async with httpx.AsyncClient() as c2:
                r2 = await c2.post(f'http://127.0.0.1:8000/tickets/{ticket_id}/messages', json={'message':'Message depuis test WS'}, timeout=30.0)
                print('POST MSG STATUS', r2.status_code)
                print(r2.text)

        task = asyncio.create_task(post_message())

        # expect 2 events: new_message (user) and new_message (assistant)
        for i in range(2):
            m = await ws.recv()
            print('WS EVENT', i+1, m)

        await task

if __name__ == '__main__':
    asyncio.run(run())
