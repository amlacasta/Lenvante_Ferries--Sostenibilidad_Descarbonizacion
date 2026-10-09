# Fuentes y supuestos

Consulta: 23 de septiembre de 2026. **Baleària figura solo como referencia de sector**; ningún dato de su negocio se atribuye a Levante Ferries.

| Afirmación | Naturaleza | Fuente o procedencia | Aplicación en el proyecto |
| --- | --- | --- | --- |
| EU ETS marítimo: umbral general 5.000 GT, 100 % intra UE/EEE, 50 % con tercer país; desde 2026 CH₄ y N₂O | Normativa real | [Comisión Europea](https://climate.ec.europa.eu/areas-action/transport-decarbonisation/reducing-emissions-shipping-sector_en) | Ámbito simplificado en `ets_scope` |
| Emisiones de 2026: 100 % de cobertura y entrega de EUA en 2027 | Normativa real | [Comisión Europea](https://climate.ec.europa.eu/areas-action/transport-decarbonisation/reducing-emissions-shipping-sector_en) | Devengo económico asignado al viaje 2026 |
| FuelEU: intensidad WTW, ámbito de energía 100 % intra UE/EEE y 50 % extra; evaluación por buque; pooling permitido | Normativa real | [EMSA](https://www.emsa.europa.eu/reducing-emissions/fuel-eu-maritime-regulation.html), [Reglamento UE 2023/1805](https://eur-lex.europa.eu/eli/reg/2023/1805/oj/eng) | Se calcula una proxy por buque y periodo |
| Referencia FuelEU 91,16 g CO₂e/MJ; 2 % 2025–2029, 6 % en 2030 | Normativa real | [Reglamento UE 2023/1805](https://eur-lex.europa.eu/eli/reg/2023/1805/oj/eng), [Consejo de la UE](https://www.consilium.europa.eu/es/press/press-releases/2023/07/25/fueleu-maritime-initiative-council-adopts-new-law-to-decarbonise-the-maritime-sector/) | Umbral modelizado 89,3368 g/MJ |
| OPS obligatorio a partir de 2030 para determinados pasajeros/portacontenedores en puertos aplicables, con condiciones | Normativa real | [Consejo de la UE](https://www.consilium.europa.eu/es/press/press-releases/2023/07/25/fueleu-maritime-initiative-council-adopts-new-law-to-decarbonise-the-maritime-sector/), [EMSA](https://www.emsa.europa.eu/reducing-emissions/fuel-eu-maritime-regulation.html) | Intervención opcional en el escenario 2026 |
| Factor well-to-tank regulatorio cero para electricidad OPS | Normativa real | [Preguntas y respuestas de la Comisión Europea](https://transport.ec.europa.eu/transport-modes/maritime/decarbonising-maritime-transport-fueleu-maritime/questions-and-answers-regulation-eu-20231805-use-renewable-and-low-carbon-fuels-maritime-transport_en) | En la proxy FuelEU se suma la energía OPS al denominador con factor cero en numerador |
| Uso de bioGNL en buques, proyectos de ferris eléctricos | Referencia pública real | [Baleària bioGNL](https://www.balearia.com/en/sala-prensa/notas-prensa/balearia-begins-exclusive-biolng-use-on-three-of-its-ships-which-now-sail-with-zero-emissions), [Baleària eléctricos](https://www.balearia.com/es/sala-prensa/notas-prensa/balearia-presenta-la-construccion-de-dos-fast-ferries-100-electricos-de-cero-emisiones-para-operar-el-primer-corredor-verde-entre-espana-y-marruecos) | Ideas de medidas; ni consumos ni resultados reales se importan |
| Rutas, buques, viajes, horarios, demanda, tarifas, consumos, costes, precio EUA 75 €/t, disponibilidad OPS | Ficción y supuestos | `src/build_project.py`, semilla 20260923 | Datasets de Levante Ferries, 1 enero–31 agosto 2026 |
| Factores MGO, LNG, BIO_MGO, BIO_LNG, red y GWP CH₄=28, N₂O=265 | Supuestos de cálculo | `data/fuel_assumptions.csv`, `src/model.py` | Escenarios ilustrativos, no factores certificados |

## Límites relevantes

- TTW CO₂e del viaje suma gases expresados en CO₂e. WTW agrega ciclo de vida del combustible y electricidad OPS; **no** se suman ambas medidas entre sí.
- El biofuel permite CO₂ biogénico cero en el modelo solo bajo supuesto de certificación válida. No se presume que el bioGNL dé emisiones físicas cero ni que el GNL fósil sea neutral; incluye methane slip supuesto.
- El factor WTW de red de electricidad es 55 g/MJ hipotéticos para inventario. La proxy FuelEU incorpora energía OPS al denominador con factor reglamentario cero en el numerador. Un cálculo regulatorio exige documentación energética, condiciones del puerto y método oficial íntegro.
- La intensidad FuelEU se agrega a nivel buque y periodo de ocho meses. La obligación legal se verifica para el año completo y puede admitir mecanismos no modelizados.
- El margen es de contribución modelizada por viaje; el coste fijo de 5.100–7.400 € por viaje se supone y no incluye toda la estructura corporativa.
- `simulator_samples` escoge una observación por ruta; representa un viaje, nunca el promedio anual de la ruta. No extrapolar directamente sus importes a la flota.
- Rutas extra UE/EEE representadas: Algeciras–Tánger y Valencia–Orán. El modelo no evalúa excepciones, disposiciones especiales insulares ni tratamientos territoriales particulares.
