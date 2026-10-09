"""Illustrative maritime decision model. Not an MRV or FuelEU compliance engine."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint

BASELINE_WTW = 91.16  # gCO2e/MJ; FuelEU 2020 reference
FUELEU_LIMIT = BASELINE_WTW * .98  # 2025–2029
GWP_CH4, GWP_N2O = 28., 265.  # fixed illustrative GWP assumptions
FUEL = {
    # Model assumptions; never present these as certified regulatory factors.
    'MGO': {'mj_kg': 42.7, 'eur_mj': .0180, 'co2_g_mj': 74., 'ch4_g_mj': .010, 'n2o_g_mj': .004, 'wtw_g_mj': 91.16},
    'LNG': {'mj_kg': 49.0, 'eur_mj': .0150, 'co2_g_mj': 56., 'ch4_g_mj': .650, 'n2o_g_mj': .002, 'wtw_g_mj': 89.0},
    'BIO_MGO': {'mj_kg': 42.7, 'eur_mj': .0330, 'co2_g_mj': 0., 'ch4_g_mj': .010, 'n2o_g_mj': .004, 'wtw_g_mj': 32.0},
    'BIO_LNG': {'mj_kg': 49.0, 'eur_mj': .0280, 'co2_g_mj': 0., 'ch4_g_mj': .650, 'n2o_g_mj': .002, 'wtw_g_mj': 30.0},
}
GRID_WTW_G_MJ = 55.  # illustrative grid factor, not zero lifecycle emissions


def fuel_pair(primary):
    return (primary, 'BIO_LNG' if primary == 'LNG' else 'BIO_MGO')


def calculate(row, *, speed_factor=1., bio_share=None, ops_share=None, eua_price=75.,
              fuel_price_factor=1., demand_factor=1., fuel_override=None):
    """One voyage: TTW inventory, simplified WTW FuelEU proxy and commercial margin.

    The same measured sea/port energy cannot be counted twice. ETS covers TTW
    CO2+CH4+N2O for the synthetic 2026 reporting period. OPS replaces a share
    of auxiliary port fuel. Grid WTW is recorded in inventory; supplied
    electricity receives zero in the separate FuelEU policy proxy.
    """
    r = row if isinstance(row, dict) else row.to_dict()
    chosen = r['fuel'] if fuel_override is None else fuel_override
    if chosen not in r['compatible_fuels'].split('|') or chosen not in ('MGO','LNG'):
        raise ValueError('Fuel not compatible with vessel')
    primary, bio = fuel_pair(chosen)
    b = float(r.get('bio_share', 0.) if bio_share is None else bio_share)
    o = float(r.get('ops_share', 0.) if ops_share is None else ops_share)
    if not (0 <= b <= 1 and 0 <= o <= 1 and speed_factor > 0):
        raise ValueError('Shares must be 0–1; speed must be positive')
    if o > 0 and not bool(r['ops_available']):
        raise ValueError('OPS is unavailable at this route/port pairing')
    sf = float(speed_factor)
    sea_mj = float(r['sea_energy_mj']) * sf ** 2  # power~v³, transit time~1/v
    port_mj = float(r['port_energy_mj'])
    burning_mj = sea_mj + port_mj * (1-o)
    ops_mj = port_mj * o
    shares = {primary: 1-b, bio: b}
    co2_kg = burning_mj * sum(shares[f]*FUEL[f]['co2_g_mj'] for f in shares)/1000
    ch4_kg = burning_mj * sum(shares[f]*FUEL[f]['ch4_g_mj'] for f in shares)/1000
    n2o_kg = burning_mj * sum(shares[f]*FUEL[f]['n2o_g_mj'] for f in shares)/1000
    ttw_kg = co2_kg + GWP_CH4*ch4_kg + GWP_N2O*n2o_kg
    fuel_wtw_kg = burning_mj*sum(shares[f]*FUEL[f]['wtw_g_mj'] for f in shares)/1000
    grid_wtw_kg = ops_mj*GRID_WTW_G_MJ/1000
    fuel_cost = burning_mj*sum(shares[f]*FUEL[f]['eur_mj'] for f in shares)*fuel_price_factor
    ops_cost = ops_mj*float(r['ops_eur_mj'])
    # 2026: accrual 100%, surrendered in 2027. Bio zero rating conditional on certification.
    ets_tonnes = ttw_kg/1000*float(r['ets_scope'])
    ets_cost = ets_tonnes*eua_price
    pax = min(float(r['pax_capacity']), max(0., float(r['passengers'])*demand_factor))
    cargo = min(float(r['cargo_capacity_lm']), max(0., float(r['cargo_lm'])*demand_factor))
    revenue = pax*float(r['fare_eur']) + cargo*float(r['cargo_rate_eur_lm'])
    fixed_cost = float(r['fixed_cost_eur'])
    total_cost = fixed_cost+fuel_cost+ops_cost+ets_cost
    return {'sea_energy_mj':sea_mj, 'fuel_energy_mj':burning_mj,'ops_energy_mj':ops_mj,
            'co2_kg':co2_kg,'ch4_kg':ch4_kg,'n2o_kg':n2o_kg,
            'ttw_co2e_kg':ttw_kg,'wtw_co2e_kg':fuel_wtw_kg+grid_wtw_kg,
            'fuel_wtw_kg':fuel_wtw_kg,'ets_tonnes':ets_tonnes,'ets_cost_eur':ets_cost,
            'energy_cost_eur':fuel_cost+ops_cost,'fuel_cost_eur':fuel_cost,
            'ops_cost_eur':ops_cost,'fixed_cost_eur':fixed_cost,'total_cost_eur':total_cost,
            'revenue_eur':revenue,'margin_eur':revenue-total_cost,'passengers':pax,'cargo_lm':cargo,
            'fuel_kg':burning_mj*sum(shares[f]/FUEL[f]['mj_kg'] for f in shares),
            'fueleu_energy_mj':(burning_mj+ops_mj)*float(r['fueleu_scope']),
            'fueleu_wtw_kg':fuel_wtw_kg*float(r['fueleu_scope']),
            'speed_kn':float(r['speed_kn'])*sf,
            'sea_hours':float(r['distance_nm'])/(float(r['speed_kn'])*sf),
            'bio_share':b,'ops_share':o,'eua_price':eua_price}


def assess(voyages):
    rows = [calculate(r) for r in voyages.to_dict('records')]
    out = pd.concat([voyages.reset_index(drop=True), pd.DataFrame(rows).drop(columns=['passengers','cargo_lm','sea_energy_mj','bio_share','ops_share'])], axis=1)
    out['ttw_co2e_per_nm_kg'] = out.ttw_co2e_kg/out.distance_nm
    out['ttw_co2e_per_passenger_kg'] = out.ttw_co2e_kg/out.passengers.replace(0,np.nan)
    out['ttw_co2e_per_cargo_lm_kg'] = out.ttw_co2e_kg/out.cargo_lm.replace(0,np.nan)
    return out


def aggregate(df, by):
    cols=['distance_nm','passengers','cargo_lm','ttw_co2e_kg','wtw_co2e_kg',
          'fueleu_energy_mj','fueleu_wtw_kg','energy_cost_eur','ets_cost_eur',
          'total_cost_eur','revenue_eur','margin_eur','fuel_energy_mj','ops_energy_mj','fuel_kg']
    g=df.groupby(by,dropna=False).agg({**{c:'sum' for c in cols},'voyage_id':'count'}).rename(columns={'voyage_id':'voyages'}).reset_index()
    g['kg_co2e_per_nm']=g.ttw_co2e_kg/g.distance_nm
    g['kg_co2e_per_pax']=g.ttw_co2e_kg/g.passengers.replace(0,np.nan)
    g['kg_co2e_per_cargo_lm']=g.ttw_co2e_kg/g.cargo_lm.replace(0,np.nan)
    g['margin_pct']=100*g.margin_eur/g.revenue_eur.replace(0,np.nan)
    g['fueleu_intensity_g_mj']=1000*g.fueleu_wtw_kg/g.fueleu_energy_mj
    # Diagnostic only: legal compliance is annual ship-level after verified adjustments.
    g['compliance_gap_g_mj']=g.fueleu_intensity_g_mj-FUELEU_LIMIT
    g['compliance_balance_proxy_kg']=((FUELEU_LIMIT*g.fueleu_energy_mj/1000)-g.fueleu_wtw_kg)
    return g


def optimize(voyages, cap_reduction=.12, eua_price=75.):
    """Choose one option per route-vessel group; 2026 synthetic costs and proxies.

    Preserves scheduled departures, passenger/cargo capacity and max sea time.
    FuelEU intensity constraint is enforced per vessel across its groups.
    """
    baseline=assess(voyages)
    groups=list(voyages.groupby(['route_id','vessel_id'],sort=True))
    records=[]
    for key, group in groups:
        g=group.to_dict('records')
        fuels=[f for f in ('MGO','LNG') if f in g[0]['compatible_fuels'].split('|')]
        for primary in fuels:
            for sf in (.88,.94,1.,1.06):
                for b in (0.,.15,.35,.65,1.):
                    for ops in ((0.,.7,1.) if all(x['ops_available'] for x in g) else (0.,)):
                        if any(x['distance_nm']/(x['speed_kn']*sf)>x['max_sea_hours']+1e-8 for x in g):
                            continue
                        calc=[calculate(x,speed_factor=sf,bio_share=b,ops_share=ops,eua_price=eua_price,fuel_override=primary) for x in g]
                        records.append(dict(route_id=key[0],vessel_id=key[1],voyages=len(g),fuel=primary,
                            speed_factor=sf,bio_share=b,ops_share=ops,
                            cost_eur=sum(z['total_cost_eur'] for z in calc),
                            ttw_kg=sum(z['ttw_co2e_kg'] for z in calc),
                            fueleu_energy_mj=sum(z['fueleu_energy_mj'] for z in calc),
                            fueleu_wtw_kg=sum(z['fueleu_wtw_kg'] for z in calc),
                            revenue_eur=sum(z['revenue_eur'] for z in calc)))
    opt=pd.DataFrame(records)
    n=len(opt); constraints=[]
    for key,_ in groups:
        mask=((opt.route_id==key[0])&(opt.vessel_id==key[1])).astype(float).to_numpy()
        constraints.append(LinearConstraint(mask,1,1))
    for vessel in sorted(opt.vessel_id.unique()):
        mask=(opt.vessel_id==vessel).to_numpy()
        coeff=np.where(mask,opt.fueleu_wtw_kg-FUELEU_LIMIT*opt.fueleu_energy_mj/1000,0)
        constraints.append(LinearConstraint(coeff,-np.inf,0))
    baseline_kg=float(baseline.ttw_co2e_kg.sum())
    constraints.append(LinearConstraint(opt.ttw_kg.to_numpy(),-np.inf,baseline_kg*(1-cap_reduction)))
    res=milp(c=opt.cost_eur.to_numpy()/1e6,integrality=np.ones(n),
             bounds=Bounds(np.zeros(n),np.ones(n)),constraints=constraints,
             options={'time_limit':35,'mip_rel_gap':.005})
    if res.x is None: raise RuntimeError(f'Optimization infeasible or timed out: {res.message}')
    selected=opt.loc[res.x>.5].copy().reset_index(drop=True)
    assert len(selected)==len(groups)
    return selected, {'solver_status':int(res.status),'solver_message':str(res.message),
        'baseline_ttw_t':baseline_kg/1000,'optimized_ttw_t':selected.ttw_kg.sum()/1000,
        'baseline_cost_eur':baseline.total_cost_eur.sum(),
        'optimized_cost_eur':selected.cost_eur.sum(),
        'savings_eur':baseline.total_cost_eur.sum()-selected.cost_eur.sum(),
        'cap_reduction':cap_reduction,'groups':len(groups),'candidates':n}
