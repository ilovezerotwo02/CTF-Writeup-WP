import asyncio, sys
HOST="103.163.47.230"
open_ports=[]
sem=asyncio.Semaphore(2000)
async def chk(p):
    async with sem:
        try:
            r,w=await asyncio.wait_for(asyncio.open_connection(HOST,p),timeout=3)
            open_ports.append(p)
            w.close()
        except Exception:
            pass
async def main():
    for i in range(1,65536,4000):
        await asyncio.gather(*(chk(p) for p in range(i,min(i+4000,65536))))
    print(sorted(open_ports))
asyncio.run(main())
