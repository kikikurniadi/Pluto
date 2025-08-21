"""Simple scheduler demo that runs fetch_and_store_demo periodically.

Usage:
  PYTHONPATH=agents python agents/scheduler_demo.py --symbol bitcoin --interval 60 --runs 10

By default it runs in dry-run mode unless ICP env variables are set.
"""
import argparse
import asyncio
import datetime
import importlib


async def run_once(symbol: str):
    # call the existing demo main
    demo = importlib.import_module("fetch_and_store_demo")
    await demo.main(symbol)


async def run_scheduler(symbol: str, interval: float, runs: int):
    print(f"Scheduler starting: symbol={symbol}, interval={interval}s, runs={runs}")
    for i in range(runs):
        now = datetime.datetime.utcnow().isoformat()
        print(f"[{now}] Run {i+1}/{runs}")
        try:
            await run_once(symbol)
        except Exception as e:
            print(f"Error during run {i+1}: {e}")
        if i < runs - 1:
            await asyncio.sleep(interval)
    print("Scheduler finished")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="bitcoin")
    parser.add_argument("--interval", type=float, default=60.0)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()

    asyncio.run(run_scheduler(args.symbol, args.interval, args.runs))


if __name__ == "__main__":
    main()
