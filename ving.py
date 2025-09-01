from playwright.async_api import async_playwright
import asyncio





# Definer alle URL-ene du vil skrape
one_week_2026_04_18 = (
    "https://www.ving.no/bestill-reise?"
    "QueryDepID=12672&QueryCtryID=4328&QueryAreaID=0&QueryResID=4345"
    "&QueryDepDate=20260428&QueryDur=8"
    "&CategoryId=2&QueryRoomAges=%7C42&QueryUnits=1"
    "&nrOfHotels=10&orderBy=LP"
)
one_week_2026_05_05 = (
    "https://www.ving.no/bestill-reise?"
    "QueryDepID=12672&QueryCtryID=4328&QueryAreaID=0&QueryResID=4345"
    "&QueryDepDate=20260505&QueryDur=8"
    "&CategoryId=2&QueryRoomAges=%7C42&QueryUnits=1"
    "&nrOfHotels=10&orderBy=LP"
    "&selectedTransport=flight%7CCgJWThIkNzQ4NTUxMTEtOGE4MS00MjUxLTk1MDYtOWY5ZDAyMWViMzg1"
)
two_weeks_2026_04_18 = (
    "https://www.ving.no/bestill-reise?"
    "QueryDepID=12672&QueryCtryID=4328&QueryAreaID=0&QueryResID=4345"
    "&QueryDepDate=20260428&QueryDur=15"
    "&CategoryId=2&QueryRoomAges=%7C42&QueryUnits=1"
    "&nrOfHotels=10&orderBy=LP"
)
two_weeks_2026_05_05 = (
    "https://www.ving.no/bestill-reise?"
    "QueryDepID=12672&QueryCtryID=4328&QueryAreaID=0&QueryResID=4345"
    "&QueryDepDate=20260505&QueryDur=15"
    "&CategoryId=2&QueryRoomAges=%7C42&QueryUnits=1"
    "&nrOfHotels=10&orderBy=LP"
    "&selectedTransport=flight%7CCgJWThIkNWQ2NTM1NmMtOWQyNS00YmZhLWI0ZDEtNWYyNjNhMmI1ZGVh"
)

URLS = [
    one_week_2026_04_18,
    one_week_2026_05_05,
    two_weeks_2026_04_18,
    two_weeks_2026_05_05,
]

async def scrape_ving():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in URLS:
            print(f"\n▶ Starter skraping for: {url}")
            await page.goto(url)

            # Aksepter cookies hvis popup dukker opp
            try:
                await page.wait_for_selector("button:has-text('GODTA ALLE')", timeout=5000)
                await page.click("button:has-text('GODTA ALLE')")
                print("✅ Cookies akseptert")
            except:
                print("ℹ Ingen cookie-popup funnet")

            # Vent til hotellnavnene er lastet
            await page.wait_for_selector(
                "h3[class*='hotelHitContentHeader__HotelHitContentTitle']",
                timeout=20000
            )
            await page.wait_for_timeout(1000)

            # Hent hotels og priser
            names = await page.query_selector_all(
                "h3[class*='hotelHitContentHeader__HotelHitContentTitle']"
            )
            prices = await page.query_selector_all(
                "div[class*='hotelHitContentPrice__CurrentPrice']"
            )
            total = min(len(names), len(prices))
            print(f"Fant {total} hoteller:")

            for i in range(total):
                name_text = (await names[i].inner_text()).strip()
                raw_price = await prices[i].inner_text()
                clean_price = (
                    raw_price
                    .replace("\u00a0", "")  # NBSP
                    .replace("—", "")       # em dash
                    .replace("–", "")       # en dash
                    .replace(",-", "")      # ,- på slutten
                    .replace(".", "")       # fjern punktum
                    .replace(",", "")       # fjern komma
                    .strip()
                )
                price = int(clean_price)
                print(f" - {name_text}: {price} NOK")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_ving())