"""Rebuild the complete synthetic analytical project from one fixed seed."""
from __future__ import annotations
import contextlib, io, json, os, sys
from pathlib import Path
import numpy as np
import pandas as pd
from model import assess, aggregate, optimize, FUEL, FUELEU_LIMIT

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; OUT=ROOT/'outputs'; NB=ROOT/'notebooks'; WEB=ROOT/'site'
for folder in (DATA, OUT, NB, WEB): folder.mkdir(parents=True,exist_ok=True)
RNG=np.random.default_rng(20260923)
routes=[
 ('DNI-IBZ','Dénia – Ibiza',62,1,1,1, .91),
 ('DNI-FOR','Dénia – Formentera',56,1,1,0,.87),
 ('DNI-PMI','Dénia – Mallorca',119,1,1,1,.90),
 ('VLC-PMI','Valencia – Palma',135,1,1,1,.93),
 ('BCN-IBZ','Barcelona – Ibiza',156,1,1,1,.91),
 ('BCN-PMI','Barcelona – Palma',112,1,1,1,.95),
 ('ALG-TNG','Algeciras – Tánger',19,1,0,0,.89),
 ('VLC-ORN','Valencia – Orán',166,1,0,0,.93),
]
vessels=[
 ('LF-01','Levante Azul','DNI-IBZ','LNG',790,1200,23,5700),
 ('LF-02','Levante Mar','DNI-IBZ','MGO',680,1000,22,4900),
 ('LF-03','Levante Sol','DNI-FOR','MGO',570,520,24,4400),
 ('LF-04','Levante Tramuntana','DNI-PMI','LNG',810,1800,21,6300),
 ('LF-05','Levante Levante','VLC-PMI','LNG',1080,2200,19,7400),
 ('LF-06','Levante Mistral','VLC-PMI','MGO',960,2100,18,6800),
 ('LF-07','Levante Poniente','BCN-IBZ','MGO',970,1800,20,6900),
 ('LF-08','Levante Norte','BCN-PMI','LNG',1000,2300,20,7100),
 ('LF-09','Levante Estrecho','ALG-TNG','MGO',720,1800,19,5100),
 ('LF-10','Levante Sur','VLC-ORN','MGO',850,2100,19,6500),
]
def seed_data():
    rd=pd.DataFrame(routes,columns=['route_id','route','distance_nm','depart_eu','arrive_eu','ops_available','ops_reliability'])
    rd['ets_scope']=np.where((rd.depart_eu==1)&(rd.arrive_eu==1),1.,.5)
    rd['fueleu_scope']=rd['ets_scope']
    rd['ops_eur_mj']=.024
    rd.to_csv(DATA/'routes.csv',index=False)
    vd=pd.DataFrame(vessels,columns=['vessel_id','vessel','route_id','fuel','pax_capacity','cargo_capacity_lm','speed_kn','fixed_cost_eur'])
    vd['gross_tonnage']=np.where(vd.pax_capacity>=800,17000,10000)
    vd['compatible_fuels']=vd.fuel.map({'LNG':'MGO|BIO_MGO|LNG|BIO_LNG','MGO':'MGO|BIO_MGO'})
    vd.to_csv(DATA/'vessels.csv',index=False)
    pd.DataFrame([{'fuel':k,**v,'source_type':'Illustrative model assumption; not certified'} for k,v in FUEL.items()]).to_csv(DATA/'fuel_assumptions.csv',index=False)
    observations=[]; seq=0
    for v in vd.to_dict('records'):
        rt=rd.set_index('route_id').loc[v['route_id']]
        d=float(rt.distance_nm); fast=v['speed_kn']>=22
        per_nm=870 if fast else 1080
        if d<25: per_nm*=1.28
        for day in pd.date_range('2026-01-01','2026-08-31'):
            for leg in range(2):
                seq+=1
                season=1+.23*np.sin(2*np.pi*(day.dayofyear-78)/365)
                wk=1.14 if day.weekday()>=4 else 1.
                load=np.clip((.66 if d>80 else .73)*season*wk+RNG.normal(0,.08),.25,.97)
                pax=int(round(v['pax_capacity']*load))
                cargo_load=np.clip(.62+.10*np.cos(2*np.pi*day.dayofyear/365)+RNG.normal(0,.09),.28,.92)
                cargo=int(round(v['cargo_capacity_lm']*cargo_load))
                scale=float(np.clip(RNG.normal(1,.055),.88,1.12))
                sea_energy=d*per_nm*scale
                port_energy=3400+v['pax_capacity']*2.4+RNG.uniform(0,850)
                ops=bool(rt.ops_available) and RNG.random()<float(rt.ops_reliability)*.20
                bio_share=.03 if v['fuel']=='LNG' else .015
                observations.append({
                    'voyage_id':f'LF26-{seq:05d}','date':day.strftime('%Y-%m-%d'),'month':day.strftime('%Y-%m'),
                    'route_id':v['route_id'],'route':rt.route,'vessel_id':v['vessel_id'],'vessel':v['vessel'],
                    'leg':leg+1,'distance_nm':d,'speed_kn':v['speed_kn'],'max_sea_hours':d/v['speed_kn']*1.085,
                    'fuel':v['fuel'],'compatible_fuels':v['compatible_fuels'],'bio_share':bio_share,
                    'ops_share':.6 if ops else 0.,'ops_available':bool(rt.ops_available),
                    'ops_eur_mj':float(rt.ops_eur_mj),'ets_scope':float(rt.ets_scope),
                    'fueleu_scope':float(rt.fueleu_scope),'pax_capacity':v['pax_capacity'],
                    'cargo_capacity_lm':v['cargo_capacity_lm'],'passengers':pax,'cargo_lm':cargo,
                    'fare_eur':round(35+.41*d+(5 if day.weekday()>=4 else 0),2),
                    'cargo_rate_eur_lm':round(2.9+.016*d,3),
                    'fixed_cost_eur':v['fixed_cost_eur'],'sea_energy_mj':round(sea_energy,2),
                    'port_energy_mj':round(port_energy,2),
                    'source_type':'Synthetic voyage / hypothetical Levante Ferries'})
    df=pd.DataFrame(observations)
    assert df.voyage_id.is_unique and (df.passengers<=df.pax_capacity).all()
    assert (df.cargo_lm<=df.cargo_capacity_lm).all() and df.isna().sum().sum()==0
    df.to_csv(DATA/'voyages_2026_synthetic.csv',index=False)
    return df,rd,vd

df,rd,vd=seed_data()
fact=assess(df)
fact.to_csv(OUT/'voyage_carbon_finance.csv',index=False)
route=aggregate(fact,['route_id','route']); fleet=aggregate(fact,['vessel_id','vessel','fuel'])
monthly=aggregate(fact,['month']); rf=aggregate(fact,['route','vessel'])
for name,table in [('routes_kpis',route),('fleet_kpis',fleet),('monthly_kpis',monthly),('route_vessel_kpis',rf)]:table.to_csv(OUT/(name+'.csv'),index=False)
options,sol=optimize(df)
options.to_csv(OUT/'optimization_choices.csv',index=False)
(OUT/'optimization_summary.json').write_text(json.dumps(sol,indent=2,ensure_ascii=False),encoding='utf-8')

# Scenario is a full revaluation of identical voyages, so baseline differences are comparable.
scenarios=[('Base 2026',1,0,0,1),('Reducción de velocidad',.94,0,0,1),
           ('Biofuel 35 %',1,.35,0,1),('OPS 80 % donde disponible',1,0,.8,1),
           ('Cartera combinada',.94,.35,.8,1),('Demanda +10 %',1,0,0,1.1)]
scenario_rows=[]
for label,sf,bio,ops,dem in scenarios:
    calc=[]
    for row in df.to_dict('records'):
        c=__import__('model').calculate(row,speed_factor=sf,
           bio_share=(bio if label in ('Biofuel 35 %','Cartera combinada') else row['bio_share']),
           ops_share=((ops if row['ops_available'] else 0) if label in ('OPS 80 % donde disponible','Cartera combinada') else row['ops_share']),
           demand_factor=dem)
        calc.append(c)
    z=pd.DataFrame(calc)
    scenario_rows.append(dict(scenario=label,ttw_t=z.ttw_co2e_kg.sum()/1000,
        wtw_t=z.wtw_co2e_kg.sum()/1000,energy_eur=z.energy_cost_eur.sum(),
        ets_eur=z.ets_cost_eur.sum(),cost_eur=z.total_cost_eur.sum(),
        revenue_eur=z.revenue_eur.sum(),margin_eur=z.margin_eur.sum(),
        passengers=z.passengers.sum(),fueleu_intensity_g_mj=1000*z.fueleu_wtw_kg.sum()/z.fueleu_energy_mj.sum()))
sc=pd.DataFrame(scenario_rows);sc['delta_ttw_pct']=100*(sc.ttw_t/sc.ttw_t.iloc[0]-1)
sc['delta_margin_eur']=sc.margin_eur-sc.margin_eur.iloc[0]
sc.to_csv(OUT/'scenarios.csv',index=False)

def records(tab):
    return json.loads(tab.round(5).to_json(orient='records',force_ascii=False))
payload={'meta':{'reporting_period':'2026-01-01 / 2026-08-31','data_class':'100% fictitious Levante Ferries',
  'method':'TTW CO2e inventory, separate EU ETS accrual, WTW FuelEU intensity proxy',
  'fueleu_limit_g_mj':FUELEU_LIMIT,'eua_eur_t':75},
  'overview':{'voyages':len(df),'passengers':int(fact.passengers.sum()),'distance_nm':float(fact.distance_nm.sum()),
  'ttw_t':float(fact.ttw_co2e_kg.sum()/1000),'wtw_t':float(fact.wtw_co2e_kg.sum()/1000),
  'ets_eur':float(fact.ets_cost_eur.sum()),'energy_eur':float(fact.energy_cost_eur.sum()),
  'margin_eur':float(fact.margin_eur.sum()),'revenue_eur':float(fact.revenue_eur.sum()),
  'fuel_mj':float(fact.fuel_energy_mj.sum()),'ops_mj':float(fact.ops_energy_mj.sum()),
  'fueleu_g_mj':float(1000*fact.fueleu_wtw_kg.sum()/fact.fueleu_energy_mj.sum()),
  'bio_energy_share':float((fact.fuel_energy_mj*fact.bio_share).sum()/fact.fuel_energy_mj.sum())},
  'routes':records(route),'fleet':records(fleet),'monthly':records(monthly),'route_vessel':records(rf),
  'scenarios':records(sc),'optimization':sol,'choices':records(options),
  'simulator_samples':records(df.groupby('route_id',sort=True).first().reset_index())}
(WEB/'data.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
template=(WEB/'dashboard.template.html').read_text(encoding='utf-8')
assert template.count('__DATA_JSON__')==1
(WEB/'index.html').write_text(template.replace('__DATA_JSON__',
    json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),
    encoding='utf-8')

def md(s):return {'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)}
def code(s):return {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':s.splitlines(keepends=True)}
common="""from pathlib import Path
import sys
ROOT = Path.cwd().resolve()
if ROOT.name == 'notebooks': ROOT = ROOT.parent
sys.path.insert(0,str(ROOT/'src'))
import pandas as pd
import numpy as np
from model import assess,aggregate,calculate,optimize,FUELEU_LIMIT
DATA=ROOT/'data'; OUT=ROOT/'outputs'
voyages=pd.read_csv(DATA/'voyages_2026_synthetic.csv')
print('Raíz:',ROOT.name,'| viajes:',len(voyages),'| periodo:',voyages.date.min(),voyages.date.max())"""
notebooks=[
 ('01_Data_Foundation', '01 — Data Foundation',[
  md('## Propósito\nUn viaje programado es la unidad de decisión. Datos 100 % ficticios y reproducibles con semilla 20260923. Cruce explícito de ruta, buque, combustible, demanda, coste y alcance regulatorio; los IDs de otros proyectos no se cruzan.'),
  code("routes=pd.read_csv(DATA/'routes.csv'); vessels=pd.read_csv(DATA/'vessels.csv'); fuels=pd.read_csv(DATA/'fuel_assumptions.csv')\nprint('Viajes, rutas, buques y combustibles:',len(voyages),len(routes),len(vessels),len(fuels))\nprint(voyages.groupby('route').size().to_string())"),
  code("assert voyages.voyage_id.is_unique\nassert voyages.isna().sum().sum()==0\nassert (voyages.passengers<=voyages.pax_capacity).all() and (voyages.cargo_lm<=voyages.cargo_capacity_lm).all()\nassert (voyages.distance_nm>0).all() and set(voyages.route_id)==set(routes.route_id)\nassert (voyages.vessel_id.map(vessels.set_index('vessel_id').route_id)==voyages.route_id).all()\nprint('Validación: unicidad, completitud, capacidad y relaciones coherentes')"),
  md('**Límite:** la demanda, las tarifas y los costes son simulados. Forecasting, pricing y finanzas previos aportan contratos conceptuales, no datos enlazados fila a fila.')]),
 ('02_Carbon_Accounting','02 — Carbon Accounting',[
  md('## Propósito\nInventario de CO₂, CH₄ y N₂O tank to wake; CO₂e con GWP fijos del modelo. Ciclo de vida well to wake separado. ETS: el bio combustible solo obtiene CO₂ biogénico cero en este ejemplo condicionado a prueba de sostenibilidad y trazabilidad. No es un informe MRV verificable.'),
  code("f=assess(voyages)\nprint('TTW t CO₂e: %.1f | WTW t CO₂e: %.1f | combustible t: %.1f'%(f.ttw_co2e_kg.sum()/1000,f.wtw_co2e_kg.sum()/1000,f.fuel_kg.sum()/1000))\nprint('CO₂ t: %.1f | CH₄ t: %.2f | N₂O t: %.3f'%(f.co2_kg.sum()/1000,f.ch4_kg.sum()/1000,f.n2o_kg.sum()/1000))"),
  code("assert abs(f.ttw_co2e_kg.sum()-(f.co2_kg+28*f.ch4_kg+265*f.n2o_kg).sum())<1e-6\nprint('kg CO₂e/milla: %.2f; kg/pasajero: %.2f; kg/metro lineal: %.2f'%(f.ttw_co2e_kg.sum()/f.distance_nm.sum(),f.ttw_co2e_kg.sum()/f.passengers.sum(),f.ttw_co2e_kg.sum()/f.cargo_lm.sum()))"),
  md('**Denominadores:** al agregar se dividen sumas; el indicador por pasajero y por metro lineal son intensidades paralelas del viaje compartido, no una atribución de emisiones que pueda sumarse.')]),
 ('03_Eco_Efficiency_Analysis','03 — Eco-Efficiency Analysis',[
  md('## Propósito\nComparar rutas y buques con sus denominadores, ocupación, coste y margen. Velocidad y carga observadas en datos simulados no prueban efectos causales.'),
  code("f=assess(voyages); routes=aggregate(f,['route']); fleet=aggregate(f,['vessel'])\nprint(routes[['route','voyages','kg_co2e_per_nm','kg_co2e_per_pax','margin_pct']].round(2).to_string(index=False))"),
  code("print(fleet[['vessel','voyages','kg_co2e_per_nm','kg_co2e_per_pax','kg_co2e_per_cargo_lm']].round(2).to_string(index=False))\nprint('Ocupación ponderada pasajeros: %.1f%%'%(100*f.passengers.sum()/f.pax_capacity.sum()))"),
  md('**Lectura:** la ecoeficiencia combina kg CO₂e/milla, kg/pasajero y margen. La carga compite por capacidad y contribuye a ingresos; no se asigna arbitrariamente el 100 % de emisiones a ambas actividades.')]),
 ('04_EU_ETS_FuelEU','04 — EU ETS & FuelEU Maritime',[
  md('## Propósito\n2026: 100 % de emisiones geográficamente cubiertas sujetas a ETS y entrega de derechos en 2027; ámbito 100 % intra EEE y 50 % viajes con tercer país. FuelEU compara intensidad WTW de energía cubierta frente a 89,3368 g CO₂e/MJ (2025–2029). Evaluación agregada final por buque, no por viaje.'),
  code("f=assess(voyages); fleet=aggregate(f,['vessel','fuel']);print('Derechos EUA proxy (t): %.1f | coste devengado €: %.0f'%(f.ets_tonnes.sum(),f.ets_cost_eur.sum()))\nprint(fleet[['vessel','fuel','fueleu_intensity_g_mj','compliance_gap_g_mj','compliance_balance_proxy_kg']].round(2).to_string(index=False))"),
  code("assert abs(f.ets_cost_eur.sum()-75*f.ets_tonnes.sum())<.01\nassert (f.ets_scope.isin([.5,1])).all()\nprint('Intensidad límite:',round(FUELEU_LIMIT,4),'g CO₂e/MJ; buques con brecha positiva:',int((fleet.compliance_gap_g_mj>0).sum()))"),
  md('**Alcance:** indicadores FuelEU y balance en este cuaderno son proxies. No se calcula sanción legal, banking, borrowing, pooling, derogaciones ni factores certificados; OPS se incluye como energía con factor regulatorio cero en la proxy FuelEU y mantiene un factor de red supuesto en el inventario WTW.')]),
 ('05_Decarbonization_Scenarios','05 — Decarbonization Scenarios',[
  md('## Propósito\nComparación contrafactual sobre los mismos viajes. El consumo marítimo por milla se escala aproximadamente con velocidad². La reducción de velocidad está condicionada por horarios y slots portuarios.'),
  code("sc=pd.read_csv(OUT/'scenarios.csv')\nprint(sc[['scenario','ttw_t','energy_eur','ets_eur','margin_eur','fueleu_intensity_g_mj','delta_ttw_pct']].round(2).to_string(index=False))"),
  code("base=sc.iloc[0]; combo=sc.loc[sc.scenario=='Cartera combinada'].iloc[0]\nprint('Cartera combinada Δt CO₂e:',round(combo.ttw_t-base.ttw_t,1),'| Δmargen €:',round(combo.margin_eur-base.margin_eur))\nassert abs(base.delta_margin_eur)<.001 and abs(base.delta_ttw_pct)<.001"),
  md('**Interpretación:** efectos supuestos, sin inferencia causal ni inversiones de capital. El escenario OPS requiere disponibilidad en ambos puertos; el de biofuel requiere certificación y suministro real.')]),
 ('06_Optimization_Engine','06 — Optimization Engine',[
  md('## Propósito\nProblema binario por grupo ruta–buque: escoger exactamente una opción entre velocidades, mezcla bio y OPS. Se preserva el número de viajes, demanda y capacidades históricas, se respeta el tiempo máximo de mar, se impone un techo de CO₂e 12 % inferior a base y el objetivo de intensidad FuelEU proxy por buque. Minimizar coste fijo + energía + EUA, con ingreso fijo para comparar margen. No incluye CAPEX ni coste de sanción.'),
  code("sel,summary=optimize(voyages)\nprint(summary)\nprint(sel[['route_id','vessel_id','voyages','speed_factor','bio_share','ops_share']].to_string(index=False))"),
  code("assert sel.voyages.sum()==len(voyages)\nassert sel.ttw_kg.sum()<=summary['baseline_ttw_t']*1000*(1-summary['cap_reduction'])+1e-5\nfor _,g in sel.groupby('vessel_id'):\n assert g.fueleu_wtw_kg.sum()<=FUELEU_LIMIT*g.fueleu_energy_mj.sum()/1000+1e-5\nprint('Restricciones de frecuencia, emisiones e intensidad por buque verificadas')"),
  md('**Límite de solver:** solución MIP con tolerancia 0,5 % y límite 35 s; si reporta estado de tiempo, se utiliza la mejor solución factible y se explicita el estado.')]),
 ('07_Executive_Sustainability_Model','07 — Executive Sustainability Model',[
  md('## Propósito\nUnir margen, emisiones, capacidad y energía en un marco de decisión. Integración conceptual: P1 aporta fiabilidad/ocupación; P2 una demanda prevista; P3 precios sujetos a elasticidad; P5 costes/margen y caja. Este proyecto usa valores sintéticos propios y no importa outputs de esos repositorios.'),
  code("f=assess(voyages); r=aggregate(f,['route']); sol=__import__('json').loads((OUT/'optimization_summary.json').read_text())\nr['zone']=np.where((r.margin_eur>=r.margin_eur.median())&(r.kg_co2e_per_pax<=r.kg_co2e_per_pax.median()),'Alto margen / baja intensidad',np.where((r.margin_eur<r.margin_eur.median())&(r.kg_co2e_per_pax>r.kg_co2e_per_pax.median()),'Prioridad de intervención','Revisar contexto'))\nprint(r[['route','margin_eur','ttw_co2e_kg','kg_co2e_per_pax','zone']].round(1).to_string(index=False))"),
  code("print('Margen base €:',round(f.margin_eur.sum()),'| reducción optimizada %:',round(100*(1-sol['optimized_ttw_t']/sol['baseline_ttw_t']),2),'| Δcoste €:',round(sol['optimized_cost_eur']-sol['baseline_cost_eur']))\nprint('Decisión: validar horarios y combustible certificado antes de contratar o implantar; contrastar con forecast y pricing sin asumir enlace de registros.')"),
  md('**Alcance ejecutivo:** las recomendaciones son pruebas de escenarios sintéticos, no autorizaciones de inversión ni declaraciones certificadas de cumplimiento.')])]

for filename,title,cells in notebooks:
    # Capture executed outputs without changing the logic cells or requiring Jupyter packages.
    full=[md('# '+title+'\n**Levante Ferries · portfolio ficticio · 2026**\n\nEjecutar desde la raíz del proyecto o desde `notebooks`. Cada tabla se calcula sobre CSV regenerables.'),code(common)]+cells
    env={'__name__':'__main__','__file__':str(NB/(filename+'.ipynb'))}
    counter=0
    old=os.getcwd();os.chdir(ROOT)
    try:
        for cell in full:
            if cell['cell_type']!='code':continue
            counter+=1;buf=io.StringIO();source=''.join(cell['source'])
            with contextlib.redirect_stdout(buf):exec(compile(source,filename+'.ipynb','exec'),env)
            cell['execution_count']=counter
            cell['outputs']=[{'output_type':'stream','name':'stdout','text':buf.getvalue().splitlines(keepends=True)}]
    finally:os.chdir(old)
    nb={'cells':full,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                                  'language_info':{'name':'python','version':sys.version.split()[0]}},
        'nbformat':4,'nbformat_minor':5}
    (NB/(filename+'.ipynb')).write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
    print('Executed',filename,'cells',counter)
print('Complete:',len(df),'voyages,',len(notebooks),'notebooks,',len(options),'optimized groups')
