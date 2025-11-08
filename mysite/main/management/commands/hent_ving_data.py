# main/management/commands/hent_ving_data.py

from django.core.management.base import BaseCommand
from main.models import VingData
from main.utils import hent_urls_for_scraping
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async
from datetime import datetime, date
import asyncio

AVREISESTED_MAP = {
    "12672": "Trondheim",
    "12345": "Oslo",
    "67890": "Bergen"
}

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

class Command(BaseCommand):
    help = "Henter data fra Ving og lagrer i databasen med daglig duplikatbeskyttelse"

    def handle(self, *args, **kwargs):
        asyncio.run(self.scrape_ving())

    async def scrape_ving(self):
        urls = await sync_to_async(hent_urls_for_scraping)()
        if not urls:
            self.stdout.write("⚠ Ingen aktive URL-er funnet i databasen.")
            return

        today = date.today()
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)

            for url in urls:
                self.stdout.write(f"\n▶ Starter skraping for: {url}")
                page = await browser.new_page()
                await page.goto(url)

                params = parse_url_params(url)

                avreise_dato = None
                if "QueryDepDate" in params:
                    try:
                        avreise_dato = datetime.strptime(params["QueryDepDate"], "%Y%m%d").date()
                    except ValueError:
                        self.stdout.write(
                            f"  ⚠ Ugyldig datoformat i URL: {params['QueryDepDate']}"
                        )

                reiselengde = (
                    int(params.get("QueryDur", 0))
                    if "QueryDur" in params else None
                )
                dep_id = params.get("QueryDepID")
                avreisested = (
                    AVREISESTED_MAP.get(dep_id, f"Ukjent ({dep_id})")
                    if dep_id else "Ukjent"
                )

                # Vent på hotellkort
                try:
                    await page.wait_for_selector(
                        "div[class*='PriceSummarystyle__Price-sc-1u0b5nv-3 cABoUJ']",
                        timeout=15000
                    )
                except:
                    self.stdout.write("  ⚠ Ingen hotellkort funnet")
                    await page.close()
                    continue

                names  = await page.query_selector_all(
                    "div[class*='Titlestyle__Title-sc-lor2nk-0 hDPKDj']"
                )
                prices = await page.query_selector_all(
                    "div[class*='PriceSummarystyle__Price-sc-1u0b5nv-3 cABoUJ']"
                )
                total = min(len(names), len(prices))
                self.stdout.write(
                    f"  → Fant {len(names)} navn og {len(prices)} priser (bruker {total})"
                )
                if total == 0:
                    await page.close()
                    continue

                for i in range(total):
                    destinasjon = (await names[i].inner_text()).strip()
                    raw_price   = (await prices[i].inner_text()).strip()

                    clean_price = (
                        raw_price
                        .replace("\u00a0", "")
                        .replace("—", "")
                        .replace("–", "")
                        .replace(",-", "")
                        .replace(".", "")
                        .replace(",", "")
                        .strip()
                    )
                    try:
                        pris = int(clean_price)
                    except ValueError:
                        self.stdout.write(f"  ⚠ Klarte ikke tolke pris: {raw_price}")
                        continue

                    # Sjekk om vi allerede har lagret denne kombinasjonen i dag
                    exists_today = await sync_to_async(
                        VingData.objects.filter(
                            avreisested=avreisested,
                            destinasjon=destinasjon,
                            pris=pris,
                            avreise_dato=avreise_dato,
                            reiselengde=reiselengde,
                            url=url,
                            dato_skrapt=today
                        ).exists
                    )()

                    if exists_today:
                        self.stdout.write("  ↩ Hopper over (allerede skrapet i dag)")
                        continue

                    # Lagre posten
                    self.stdout.write(
                        f"  Lagrer: {avreisested} | {destinasjon} "
                        f"| {pris} kr | {avreise_dato} | {reiselengde} dager"
                    )
                    await sync_to_async(VingData.objects.create)(
                        avreisested=avreisested,
                        destinasjon=destinasjon,
                        pris=pris,
                        url=url,
                        avreise_dato=avreise_dato,
                        reiselengde=reiselengde
                    )

                count = await sync_to_async(VingData.objects.count)()
                self.stdout.write(f"  Totalt antall rader i DB: {count}")

                await page.close()

            await browser.close()