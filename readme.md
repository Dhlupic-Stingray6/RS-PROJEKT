# Sustav za praćenje temperature i kvalitete zraka

Raspodijeljeni sustav za prikupljanje i obradu podataka sa senzora temperature i kvalitete zraka.

## Arhitektura

Sustav se sastoji od nekoliko mikroservisa:
- **Storage Service**: Upravljanje bazom podataka
- **Ingest Service**: Primanje podataka od senzora  
- **Processing Service**: Obrada podataka i statistika
- **Simulator**: Simulacija senzora
