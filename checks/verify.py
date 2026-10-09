"""Check cross-deliverable conservation and genuinely executed notebooks."""
import json,sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from model import assess,FUELEU_LIMIT

v=pd.read_csv(ROOT/'data/voyages_2026_synthetic.csv')
f=pd.read_csv(ROOT/'outputs/voyage_carbon_finance.csv')
r=pd.read_csv(ROOT/'outputs/routes_kpis.csv')
b=pd.read_csv(ROOT/'outputs/fleet_kpis.csv')
s=pd.read_csv(ROOT/'outputs/scenarios.csv')
o=pd.read_csv(ROOT/'outputs/optimization_choices.csv')
d=json.loads((ROOT/'site/data.json').read_text())
assert len(v)==len(f)==d['overview']['voyages']==4860
assert v.voyage_id.is_unique and f.voyage_id.is_unique
for field in ('ttw_co2e_kg','wtw_co2e_kg','revenue_eur','margin_eur','total_cost_eur'):
    assert abs(f[field].sum()-r[field].sum())<.01,field
    assert abs(f[field].sum()-b[field].sum())<.01,field
assert abs(f.ttw_co2e_kg.sum()/1000-d['overview']['ttw_t'])<.001
assert abs(75*f.ets_tonnes.sum()-f.ets_cost_eur.sum())<.01
assert abs(f.margin_eur.sum()+f.total_cost_eur.sum()-f.revenue_eur.sum())<.01
assert abs(s.iloc[0].margin_eur-f.margin_eur.sum())<.01
assert abs(s.iloc[-1].ttw_t-s.iloc[0].ttw_t)<.001  # demand alone does not change fuel at fixed supply
assert o.voyages.sum()==len(v)
assert o.ttw_kg.sum()<=f.ttw_co2e_kg.sum()*.88+.001
for _,g in o.groupby('vessel_id'):
    assert g.fueleu_wtw_kg.sum()<=FUELEU_LIMIT*g.fueleu_energy_mj.sum()/1000+.001
assert d['optimization']['solver_status']==0
html=(ROOT/'site/index.html').read_text()
assert '__DATA_JSON__' not in html and html.count('"simulator_samples"')==1
assert str(d['overview']['voyages']) in html
for nb in sorted((ROOT/'notebooks').glob('*.ipynb')):
    j=json.loads(nb.read_text()); codes=[c for c in j['cells'] if c['cell_type']=='code']
    assert len(codes)>=3 and all(c['execution_count'] and c['outputs'] for c in codes),nb
assert len(list((ROOT/'notebooks').glob('*.ipynb')))==7
print('OK: 7 notebooks executed, 4,860 voyages reconciled; dashboard and optimization agree.')
