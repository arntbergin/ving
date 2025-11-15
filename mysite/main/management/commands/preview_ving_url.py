import asyncio
import logging
from playwright.async_api import async_playwright
from main.management.commands.hent_ving_data import normalize_ving_url
logger = logging.getLogger(__name__)

def parse_url_params(url: str) -> dict:
    parts = url.split("?", 1)
    if len(parts) < 2:
        return {}
    query = parts[1]
    params = {}
    for pair in query.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[key] = value
    return params

async def preview_urls(urls):
    results = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        for raw_url in urls:
            url = normalize_ving_url(raw_url)
            page = await browser.new_page()
            await page.goto(url)

            try:
                await page.wait_for_selector("div[class*='Cardstyle__Card']", timeout=15000)
            except:
                results.append({"url": url, "count": 0, "hoteller": []})
                await page.close()
                continue

            cards = await page.query_selector_all("div[class*='Cardstyle__Card']")
            hoteller = []
            for card in cards:
                name_el = await card.query_selector("div[class*='Titlestyle__Title']")
                if name_el:
                    destinasjon = (await name_el.inner_text()).strip()
                    hoteller.append(destinasjon)

            results.append({"url": url, "count": len(hoteller), "hoteller": hoteller})
            await page.close()
        await browser.close()
    return results

def preview_single_url(url):
    return asyncio.run(preview_urls([url]))
