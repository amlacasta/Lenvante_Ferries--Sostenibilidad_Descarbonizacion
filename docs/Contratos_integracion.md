# Contratos para integración futura con el portfolio

Los cinco proyectos anteriores trabajan con granos, periodos y definiciones propios. No se cruzan las filas sin una tabla de correspondencias auditada.

| Proyecto | Campo esperado | Grano de incorporación | Uso condicional |
| --- | --- | --- | --- |
| 1 Control operativo | `departure_id`, `cancelled`, `delay_minutes`, `actual_vessel_id` | Salida programada | Sustituir las salidas sintéticas por operaciones verificadas, conservando cancelaciones en el denominador de frecuencia |
| 2 Forecasting demanda | `departure_id`, `forecast_pax`, `forecast_interval`, `issue_timestamp` | Salida × emisión del pronóstico | Alimentar demanda y sensibilidad con previsiones hechas antes de la salida |
| 3 Optimización pricing | `departure_id`, `recommended_fare`, `expected_pax`, `price_model_version` | Salida × propuesta | Maximizar margen sujeto a capacidad y emisiones, sin confundir asociación de elasticidad con efecto causal |
| 5 Finanzas operativas | `departure_id`, `fuel_actual_eur`, `fixed_allocated_eur`, `revenue_actual_eur`, `accounting_period` | Salida × periodo de devengo | Conciliar coste operativo, energía, EUA y margen; documentar si el coste incluye derechos de carbono |
| 6 Agente corporativo IA | `question`, `metric_id`, `period`, `source_version`, `assumption_set` | Consulta agregada | Explicar KPIs y escenarios enlazando fuentes; revisión humana antes de implantar cambios |

**Clave maestra propuesta:** fecha y hora UTC de salida, puerto origen, destino, buque e identificador de servicio; mantener tabla de equivalencias con claves anteriores. Antes de integrar: verificar duplicados, cancelaciones, cambio de buque, alcance territorial, combustible observado, facturas, unidades, periodo y trazabilidad del pronóstico. Este repositorio no afirma disponer de esas correspondencias.

**Linaje:** cada métrica necesita `source_type` (real, regulatoria, supuesto, sintética), versión de factores, denominador y fecha de extracción. Los datos del agente 6 deben utilizar vistas agregadas con control de acceso en un entorno productivo.
