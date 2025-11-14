import asyncio
import logging
import re
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async

from main.models import VingData
from main.utils import hent_urls_for_scraping

logger = logging.getLogger(__name__)

AVREISESTED_MAP = {
    "12672": "Trondheim",
    "12345": "Oslo",
    "67890": "Bergen"
}

def normalize_ving_url(url: str) -> str:
    base, _, _ = url.partition("?")
    params = parse_url_params(url)
    params.pop("SessionId", None)  # fjern sessionid hvis den finnes
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return base + ("?" + query if query else "")

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


async def scrape_urls(urls, stdout=None):
    today = date.today()
    saved_count = 0
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        for raw_url in urls:
            url = normalize_ving_url(raw_url)
            if stdout:
                stdout.write(f"\n▶ Starter skraping for: {url}")

            page = await browser.new_page()
            await page.goto(url)

            params = parse_url_params(url)

            # --- Avreise / hjemreise / reiselengde ---
            avreise_dato = None
            hjemreise_dato = None
            reiselengde = None

            if "QueryDepDate" in params:
                try:
                    avreise_dato = datetime.strptime(params["QueryDepDate"], "%Y%m%d").date()
                except ValueError:
                    if stdout:
                        stdout.write(f"⚠ Ugyldig datoformat i URL: {params['QueryDepDate']}")

            # QueryRetDate har høyest prioritet
            if "QueryRetDate" in params and params["QueryRetDate"]:
                try:
                    hjemreise_dato = datetime.strptime(params["QueryRetDate"], "%Y%m%d").date()
                    if avreise_dato:
                        reiselengde = (hjemreise_dato - avreise_dato).days
                except ValueError:
                    if stdout:
                        stdout.write(f"⚠ Ugyldig datoformat i URL: {params['QueryRetDate']}")
            # Ellers bruk QueryDur
            elif "QueryDur" in params and params["QueryDur"]:
                try:
                    dur = int(params["QueryDur"])
                    if avreise_dato and dur > 0:
                        # Ving "8 dager" = 7 netter → retur = avreise + (dur - 1)
                        hjemreise_dato = avreise_dato + timedelta(days=dur - 1)
                        reiselengde = dur - 1
                except ValueError:
                    if stdout:
                        stdout.write(f"⚠ Ugyldig reiselengde i URL: {params['QueryDur']}")

            dep_id = params.get("QueryDepID")
            avreisested = AVREISESTED_MAP.get(dep_id, f"Ukjent ({dep_id})") if dep_id else "Ukjent"

            # --- Vent på hotellkort ---
            try:
                await page.wait_for_selector("div[class*='Cardstyle__Card']", timeout=15000)
            except:
                if stdout:
                    stdout.write("⚠ Ingen hotellkort funnet")
                await page.close()
                continue

            cards = await page.query_selector_all("div[class*='Cardstyle__Card']")
            for card in cards:
                name_el = await card.query_selector("div[class*='Titlestyle__Title']")
                price_summary = await card.query_selector("div[class*='PriceSummarystyle__PriceSummary']")
                if not name_el or not price_summary:
                    continue

                destinasjon = (await name_el.inner_text()).strip()
                price_el = await price_summary.query_selector("div[class*='PriceSummarystyle__Price-sc']")
                if not price_el:
                    continue

                raw_price = (await price_el.inner_text()).strip()
                digits = re.sub(r"\D", "", raw_price)
                if not digits:
                    if stdout:
                        stdout.write(f"⚠ Ingen tall funnet i pris: {raw_price}")
                    continue
                pris = int(digits)

                # --- Duplikatsjekk ---
                exists_today = await sync_to_async(
                    VingData.objects.filter(
                        avreisested=avreisested,
                        destinasjon=destinasjon,
                        pris=pris,
                        avreise_dato=avreise_dato,
                        hjemreise_dato=hjemreise_dato,
                        reiselengde=reiselengde,
                        url=url,
                        dato_skrapt=today
                    ).exists
                )()
                if exists_today:
                    if stdout:
                        stdout.write("↩ Hopper over (allerede skrapet i dag)")
                    continue

                if stdout:
                    stdout.write(
                        f"Lagrer: {avreisested} | {destinasjon} | {pris} kr | "
                        f"{avreise_dato} → {hjemreise_dato} | {reiselengde} dager"
                    )

                await sync_to_async(VingData.objects.create)(
                    avreisested=avreisested,
                    destinasjon=destinasjon,
                    pris=pris,
                    url=url,
                    avreise_dato=avreise_dato,
                    hjemreise_dato=hjemreise_dato,
                    reiselengde=reiselengde
                )
                saved_count += 1
            
            count = await sync_to_async(VingData.objects.count)()
            if stdout:
                stdout.write(f"Totalt antall rader i DB: {count}")

            await page.close()

        await browser.close()
    return saved_count

def scrape_single_url(url):
    clean_url = normalize_ving_url(url)
    return asyncio.run(scrape_urls([clean_url]))


class Command(BaseCommand):
    help = "Henter data fra Ving og lagrer i databasen med daglig duplikatbeskyttelse"

    def handle(self, *args, **kwargs):
        urls = hent_urls_for_scraping()
        asyncio.run(scrape_urls(urls, stdout=self.stdout))
