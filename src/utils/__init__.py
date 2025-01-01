from asyncio.subprocess import Process
from typing import Any, Callable, assert_type
from playwright.async_api import Page, Route
import string

def file_size_to_bytes(file_size: str) -> int:
    units = { "B": 1, "KB": 10**3, "MB": 10**6, "KiB": 2**10, "MiB": 2**20}
    size = file_size.rstrip(string.ascii_letters)
    unit = file_size[len(size):]
    return int(float(size) * units[unit])

def ceil_div(n: int, d: int) -> int:
    # funny hack
    return -(n // -d)

async def terminate_and_wait(process: Process):
    if process.returncode is None:
        process.terminate()
        await process.wait()

# Page is already navigated to where we want to fetch the link from. Currently only for k2s.
async def get_download_url(page: Page) -> str:
    await page.get_by_role("button", name="Slow speed download Download").click()
    await page.get_by_text("Download now").click()
    url = await page.get_by_role("link", name="this link").get_attribute("href")
    if type(url) != str:
        print("Fuck")
        exit(64)

    return url
