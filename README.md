# Ving

Et Django‑basert prosjekt for scraping og håndtering av reiselinks fra Ving.  

## 🚀 Funksjoner
- Scraping med Playwright for å hente oppdaterte Ving‑data  
- Logging og visuell feedback for validering av koblinger  
- Container‑arkitektur med separate web‑ og cronjob‑miljøer  
- CI/CD pipelines via GitHub Actions og Helm‑chart for Kubernetes  

## 📂 Struktur
- `mysite/` – Django‑applikasjonen  
- `helm-chart/` – Kubernetes‑konfigurasjon  
- `Dockerfile` og `Dockerfile.cron` – web‑ og cronjob‑containere  
- `.github/workflows/` – automatisert bygg og deploy  

## 📊 Datamodell
- **VingURL** – lagrer unike URLer  
- **VingData** – kobles via ForeignKey til `VingURL`  

## 🌍 Deploy
Prosjektet er laget for å kjøre i containere og kan enkelt skaleres med Kubernetes.  
Helm‑chart er inkludert for produksjonsdeployments.
