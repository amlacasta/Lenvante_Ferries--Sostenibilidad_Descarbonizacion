# Proyecto 7 · Sustainability & Decarbonization Analytics

**Levante Ferries** · Portfolio de Álvaro Martínez Lacasta · Septiembre de 2026

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Notebooks](https://img.shields.io/badge/Notebooks-7%20ejecutados-blueviolet)
![Dashboard](https://img.shields.io/badge/Dashboard-HTML%20interactivo-brightgreen)
![Optimización](https://img.shields.io/badge/Optimizaci%C3%B3n-HiGHS-orange)
![Estado](https://img.shields.io/badge/Estado-Proyecto%20de%20portfolio-success)

## Dashboard interactivo

[**Abrir Sustainability & Decarbonization Analytics en amlacasta.tech**](https://www.amlacasta.tech/proyectos/sostenibilidad/)

El dashboard dark ofrece Executive Overview, Fleet, Routes, Energy Transition,
EU ETS & FuelEU y Decarbonization Simulator. También puede descargarse
[`site/index.html`](site/index.html) y abrirse en un navegador sin instalar nada.
GitHub muestra el código HTML, pero no ejecuta el simulador en la vista del archivo.

> Levante Ferries es una naviera ficticia. Todos los viajes, buques, ingresos,
> consumos y resultados son datos sintéticos. Las reglas descritas en las fuentes
> oficiales son reales; los coeficientes y precios del modelo son hipótesis.

## Pregunta directiva

¿Cómo reducir las emisiones de una naviera mediterránea y avanzar en su
descarbonización manteniendo rentabilidad, capacidad y nivel de servicio?

La unidad primaria es el **viaje**: viaje → ruta → buque → combustible →
demanda → coste → emisiones → regulación → decisión. El proyecto conserva
separados el inventario físico tank to wake (TTW), el inventario de ciclo de
vida well to wake (WTW), los derechos EU ETS y el indicador FuelEU.

## Resultados del caso simulado

Periodo enero–agosto de 2026: **4.860 viajes**, **3.140.788 pasajeros**,
**40.356 t CO₂e TTW**, **48.834 t CO₂e WTW** y **2,73 M€** de coste EUA
devengado con un precio **supuesto** de 75 €/t. Margen agregado: **235,55 M€**
tras los costes incluidos en el modelo. No incluye CAPEX, deuda, overhead
corporativo ni impuestos.

El motor encuentra una opción factible con **34.954 t CO₂e TTW** (**−13,4 %**)
y **40,58 M€** de coste total frente a **41,81 M€** en la base. Los **1,23 M€**
de diferencia son un resultado del modelo, no un ahorro realizado. Conserva los
viajes y su demanda, satisface el tiempo máximo de travesía supuesto y verifica
el objetivo de intensidad FuelEU simplificado por buque. El límite de emisiones
fijado como restricción es **−12 %**; el motor supera ese mínimo porque encuentra
una opción más económica con menores emisiones.

## Entregables y estructura

| Ruta | Contenido |
| --- | --- |
| `data/` | `voyages_2026_synthetic.csv`, rutas, buques y factores energéticos asumidos |
| `notebooks/01…07*.ipynb` | Siete cuadernos documentados, ejecutados, con salidas guardadas |
| `src/model.py` | Contabilidad, agregación y optimizador MIP compartidos |
| `src/build_project.py` | Generador determinista de datos, KPIs, escenarios, optimización y notebooks |
| `outputs/` | Tabla viaje × carbono × finanzas, KPIs, escenarios y decisiones óptimas |
| `site/index.html` | Dashboard dark **autónomo**, con datos incrustados; abrir en navegador |
| `site/dashboard.template.html` | Plantilla del dashboard para regenerar desde `data.json` |
| `docs/` | Fuentes, fórmulas, contratos de integración y publicación posterior |

## Abrir y reproducir

1. Abrir `site/index.html` con un navegador actualizado. No necesita servidor,
   clave ni conexión de datos. Las pestañas contienen Executive Overview,
   Fleet, Routes, Energy Transition, EU ETS & FuelEU y Decarbonization Simulator.
2. Para recalcular todo, crear un entorno con Python 3.11 o posterior, instalar
   `pip install -r requirements.txt` y ejecutar desde la raíz
   `python src/build_project.py`. Los siete `.ipynb` se ejecutan y guardan de
   nuevo durante ese comando; también se pueden abrir individualmente en
   Jupyter o Google Colab **después de subir la carpeta completa**.
3. `python checks/verify.py` comprueba conciliación, restricciones y salidas.
   Los resultados no son números aleatorios nuevos: la semilla está fijada en
   `20260923`.

**Para Colab:** subir el proyecto completo o montar Drive, situarse en la raíz
del proyecto y ejecutar un notebook. Cada notebook detecta si está en la raíz
o dentro de `notebooks/`. Requiere también `src/`, `data/` y `outputs/`.

## Indicadores principales

| Indicador | Cálculo | Unidad y advertencia |
| --- | --- | --- |
| CO₂e TTW | CO₂ kg + 28 × CH₄ kg + 265 × N₂O kg | kg; GWP del caso supuesto |
| CO₂e WTW | Σ combustible MJ × factor WTW + OPS MJ × factor red | kg; factores ilustrativos |
| Intensidad por milla | Σ CO₂e TTW kg / Σ millas náuticas | kg/nm; sumar antes de dividir |
| Intensidad por pasajero | Σ CO₂e TTW kg / Σ pasajeros | kg/pasajero; no asignación de emisiones |
| Intensidad por carga | Σ CO₂e TTW kg / Σ metros lineales | kg/m lineal; no sumarla con la de pasajeros |
| Energía y consumo | MJ combustible; Σ MJ combustible ÷ PCI MJ/kg ponderado | MJ y kg |
| Cobertura EU ETS | Σ CO₂e TTW t × factor geográfico | t EUA, 2026 |
| Coste EUA | Σ t EUA × precio supuesto €/t | €, devengo 2026 y entrega 2027 |
| Intensidad FuelEU proxy | Σ WTW combustible kg × 1.000 / Σ (energía combustible + OPS) MJ cubiertos | g CO₂e/MJ por buque y periodo; OPS factor regulatorio cero |
| Gap FuelEU proxy | Intensidad calculada − 89,3368 | g CO₂e/MJ, 2025–2029 |
| Balance energético proxy | Σ MJ cubiertos × límite g/MJ / 1.000 − Σ kg WTW cubiertos | kg; **no** sanción ni balance legal certificado |
| Coste total modelizado | Coste fijo por viaje + energía combustible + OPS + EUA | € |
| Margen modelizado | Ingresos pasajeros y carga − coste total modelizado | €; excluye CAPEX y overhead |

La energía consumida al navegar varía con **velocidad²** a distancia constante
en la sensibilidad. Es una aproximación operativa, no una curva calibrada a
máquinas reales. La capacidad de pasajeros y carga limita la demanda vendida.

## Regulación y alcance de las simplificaciones

En este caso todos los buques superan 5.000 GT. EU ETS cubre el 100 % de viajes
entre puertos de la UE/EEE y el 50 % de viajes con puerto de un tercer país. En
2026 cubre CO₂, CH₄ y N₂O; la obligación de entregar derechos por emisiones de
2026 corresponde a 2027. FuelEU Maritime compara la intensidad WTW de energía
cubierta por buque y año con 91,16 × (1 − 0,02) = 89,3368 g CO₂e/MJ entre 2025
y 2029. OPS tiene obligaciones específicas desde 2030 en puertos aplicables.

Se asume CO₂ biogénico TTW igual a cero **solo en escenarios hipotéticos de
combustible bio sostenible certificado**. La cifra final requiere trazabilidad,
factores reglamentarios, verificadores y evaluación de derogaciones. El modelo
incluye la energía OPS con factor regulatorio cero en la proxy FuelEU y registra
sus emisiones WTW de red supuestas por separado en el inventario global. No calcula sanciones FuelEU ni aplica
pooling, banking, borrowing, excepciones portuarias o fórmulas MRV verificadas.
Consulte [Fuentes y supuestos](docs/Fuentes_y_supuestos.md).

## Optimización

Se resuelve una elección binaria por pareja ruta–buque, con candidatos de
velocidad, combustible compatible, mezcla bio y OPS disponible. Minimiza
**coste operativo fijo + energía + EUA**. Para cada pareja elige una opción;
mantiene número de viajes, pasajeros y carga observados; no supera capacidades;
respeta el máximo de horas de mar; limita las emisiones TTW a **88 %** del caso
base; impone la intensidad FuelEU proxy por buque. El solver HiGHS obtuvo estado
óptimo en esta generación. Un cambio de precio o demanda en el simulador es
sensibilidad aislada y **no** vuelve a resolver automáticamente toda la red.

## Integración responsable con el portfolio

Los proyectos 1, 2, 3 y 5 pueden aportar respectivamente fiabilidad/ocupación,
demanda prevista, tarifa y costes/margen. Aquí se documenta el contrato de
datos para integrarlos en el futuro. **No se afirma que sus identificadores ni
sus datasets actuales coincidan**. El agente corporativo del proyecto 6 podría
consultar las vistas agregadas y describir supuestos y evidencia, sin ejecutar
cambios operativos ni afirmar cumplimiento legal. Véase
[Contratos de integración](docs/Contratos_integracion.md).

## Fuentes

Normativa y comunicaciones: [Comisión Europea sobre EU ETS marítimo](https://climate.ec.europa.eu/areas-action/transport-decarbonisation/reducing-emissions-shipping-sector_en),
[EMSA sobre FuelEU Maritime](https://www.emsa.europa.eu/reducing-emissions/fuel-eu-maritime-regulation.html),
[Reglamento UE 2023/1805](https://eur-lex.europa.eu/eli/reg/2023/1805/oj/eng).
Contexto sectorial, no datos de Levante Ferries:
[Baleària sobre bioGNL](https://www.balearia.com/en/sala-prensa/notas-prensa/balearia-begins-exclusive-biolng-use-on-three-of-its-ships-which-now-sail-with-zero-emissions)
y [electrificación](https://www.balearia.com/es/sala-prensa/notas-prensa/balearia-presenta-la-construccion-de-dos-fast-ferries-100-electricos-de-cero-emisiones-para-operar-el-primer-corredor-verde-entre-espana-y-marruecos).

## Portfolio Levante Ferries

1. [Control Operativo y Eficiencia](https://github.com/amlacasta/Levante-Ferries--Control_operativo_eficiencia)
2. [Forecasting de Demanda](https://github.com/amlacasta/Levante-Ferries--Demand_forecasting)
3. [Optimización del Pricing](https://github.com/amlacasta/Levante-Ferries--Optimizacion-del-pricing)
4. [People Analytics](https://github.com/amlacasta/Levante-Ferries--People_analitycs)
5. Finanzas Operativas
6. Agente corporativo de IA
7. **Sustainability & Decarbonization Analytics**

**Autor:** Álvaro Martínez Lacasta · Dirección + Datos + IA aplicada.
