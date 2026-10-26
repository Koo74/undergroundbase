"""
UndergroundBase v5.3.2
=======================
SEARCH FIX RELEASE (over v5.3.1):
  10. FIXED: Universal search now uses OpenStreetMap Nominatim API.
      - You can now type ANY address, mall, or place in Malaysia (e.g. "Ampang, Selangor").
      - It will automatically find the GPS coordinates and drop a pin.
      - Fallback to local dictionary is still preserved for speed.
ALL v5.3.1 features and every existing feature preserved byte-for-byte.
"""

import streamlit as st
import folium
from folium.plugins import Fullscreen, MiniMap, MousePosition, Draw, HeatMap
from folium import raster_layers
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from functools import wraps
import requests
from pathlib import Path
import sqlite3
import pickle
import math
import threading
import queue
import plotly.express as px
import plotly.graph_objects as go

CYBERPUNK_CSS = """
<style>
    :root {
        --neon-cyan: #00f0ff;
        --neon-pink: #ff2d95;
        --neon-purple: #b026ff;
        --neon-green: #39ff14;
        --neon-yellow: #ffe84d;
    }
    .stApp { background: linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #0a0a1f 100%); }
    .main-title {
        font-family: 'Courier New', monospace;
        font-size: 3.5rem; font-weight: 900;
        background: linear-gradient(90deg, #00f0ff, #b026ff, #ff2d95);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(0, 240, 255, 0.3);
        letter-spacing: 4px; animation: glowPulse 3s ease-in-out infinite;
    }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 40px rgba(0, 240, 255, 0.3); }
        50% { text-shadow: 0 0 60px rgba(0, 240, 255, 0.6), 0 0 80px rgba(176, 38, 255, 0.3); }
    }
    .subtitle {
        font-family: 'Courier New', monospace; color: #00f0ff;
        font-size: 1.2rem; letter-spacing: 8px;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
        border-bottom: 1px solid rgba(0, 240, 255, 0.2);
        padding-bottom: 10px; margin-bottom: 20px;
    }
    .phase-badge {
        display: inline-block; padding: 4px 15px; border-radius: 20px;
        font-family: 'Courier New', monospace; font-size: 0.7rem;
        letter-spacing: 2px; text-transform: uppercase; font-weight: bold;
        margin: 0 5px; border: 1px solid;
    }
    .phase-badge-2 { color: #00f0ff; border-color: #00f0ff; background: rgba(0,240,255,0.05); }
    .phase-badge-3 { color: #39ff14; border-color: #39ff14; background: rgba(57,255,20,0.05); }
    .phase-badge-4 { color: #ffe84d; border-color: #ffe84d; background: rgba(255,232,77,0.05); }
    .phase-badge-5 { color: #ff2d95; border-color: #ff2d95; background: rgba(255,45,149,0.05); }
    .recommendation-container {
        background: rgba(15, 15, 35, 0.85);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 12px; padding: 20px; margin: 15px 0;
    }
    .recommendation-title {
        color: #00f0ff; font-family: 'Courier New', monospace;
        font-size: 1.2rem; font-weight: bold; letter-spacing: 2px;
        margin-bottom: 10px;
    }
    .recommendation-item {
        color: #ffffff; font-family: 'Courier New', monospace;
        font-size: 0.9rem; padding: 6px 0;
        border-bottom: 1px solid rgba(0, 240, 255, 0.05);
    }
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(176, 38, 255, 0.15)) !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        color: #00f0ff !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important; text-transform: uppercase !important;
        letter-spacing: 2px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.3), rgba(176, 38, 255, 0.3)) !important;
        border-color: #00f0ff !important;
        color: #ffffff !important;
    }
    [data-testid="metric-container"] {
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 10px; padding: 15px;
    }
    [data-testid="metric-container"] label { color: #00f0ff !important; }
    [data-testid="metric-container"] div { color: #ffffff !important; }
    .cyber-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #00f0ff, #b026ff, #ff2d95, transparent);
        margin: 20px 0; opacity: 0.5;
    }
    .stMarkdown p, .stMarkdown li { color: #ffffff !important; }
    .stMarkdown h1 { color: #00f0ff !important; }
    .stMarkdown h2 { color: #b026ff !important; }
    .stMarkdown h3 { color: #ff2d95 !important; }
    .confidence-bar {
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 8px; padding: 12px; margin: 10px 0;
    }
    .warning-box {
        background: rgba(255, 45, 149, 0.08);
        border: 1px solid rgba(255, 45, 149, 0.4);
        border-radius: 8px; padding: 12px; margin: 10px 0;
        color: #ffffff;
    }
    .blocked-score {
        background: rgba(255, 45, 149, 0.15) !important;
        border: 2px solid #ff2d95 !important;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
    }
    .not-feasible-box {
        background: rgba(255, 45, 149, 0.25) !important;
        border: 3px solid #ff2d95 !important;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
    }
    .alt-site-card {
        background: rgba(57, 255, 20, 0.05);
        border: 1px solid rgba(57, 255, 20, 0.3);
        border-radius: 8px; padding: 12px; margin: 8px 0;
    }
</style>
"""

# ============================================================================
# SCORE CAP FOR BLOCKERS
# ============================================================================

def compute_display_score(rd: Dict) -> Dict:
    raw_score = rd.get('suitability_percentage', 0)
    raw_rating = rd.get('rating', 'Unknown')
    raw_emoji = rd.get('rating_emoji', '⚪')

    protected = rd.get('protected_area', {})
    cave = rd.get('cave_warning')
    fault = rd.get('nearest_fault', {})
    seismic_risk = rd.get('seismic_risk', 'Low')

    cap_reason = None
    display_score = raw_score

    if protected.get('inside'):
        display_score = min(raw_score, 60.0)
        cap_reason = f"Site inside {protected.get('name', 'protected area')} (UNESCO/legal restriction)"
    elif cave and fault.get('distance_km', 999) < 10:
        display_score = min(raw_score, 50.0)
        cap_reason = "Cave system + fault within 10km (extreme engineering risk)"
    elif seismic_risk == 'High' and rd.get('water_table_depth_m', 100) < 10:
        display_score = min(raw_score, 55.0)
        cap_reason = "High seismic + shallow water table (compounding risk)"
    elif protected.get('near'):
        display_score = min(raw_score, 75.0)
        cap_reason = f"Near {protected.get('name', 'protected area')} (10km buffer)"

    is_capped = display_score < raw_score
    not_feasible = bool(protected.get('inside'))

    if is_capped:
        if display_score < 40:
            display_rating = 'Blocked'
            display_emoji = '🚫'
        elif display_score < 60:
            display_rating = 'High Risk'
            display_emoji = '🔴'
        else:
            display_rating = 'Limited'
            display_emoji = '⚠️'
    else:
        display_rating = raw_rating
        display_emoji = raw_emoji

    return {
        'display_score': round(display_score, 1),
        'raw_score': raw_score,
        'display_rating': display_rating,
        'display_emoji': display_emoji,
        'is_capped': is_capped,
        'cap_reason': cap_reason,
        'not_feasible': not_feasible,
    }


def compute_score_margin(rd: Dict) -> Dict:
    confidence = rd.get('data_confidence', {})
    confidence_pct = confidence.get('confidence_pct', 50)
    margin = round((100 - confidence_pct) * 0.35, 1)
    raw_score = rd.get('suitability_percentage', 0)
    lower = max(0, round(raw_score - margin, 1))
    upper = min(100, round(raw_score + margin, 1))
    return {
        'margin': margin,
        'lower_bound': lower,
        'upper_bound': upper,
        'confidence_pct': confidence_pct,
        'band': confidence.get('band', 'Unknown'),
    }

# ============================================================================
# NEARBY ALTERNATIVES
# ============================================================================

def _parse_location_coords(rd: Dict) -> Optional[tuple]:
    """Robustly extract (lat, lon) from rd['location']."""
    loc = rd.get('location', '')
    if not loc or '(' not in loc or ')' not in loc:
        return None
    try:
        inside = loc.split('(')[1].split(')')[0]
        parts = [p.strip() for p in inside.split(',')]
        if len(parts) != 2:
            return None
        lat = float(parts[0])
        lon = float(parts[1])
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None
        if abs(lat) > 90:
            lat, lon = lon, lat
        return (lat, lon)
    except Exception:
        return None


def _quick_static_estimate(lat: float, lon: float, region: str) -> Dict:
    """Fast suitability estimate — NO API calls. Tie-breaker included."""
    if region == 'borneo':
        if 5.8 < lat < 6.2 and 116.4 < lon < 116.8:
            elev_score, elev = 5.0, 1500
        elif lat > 3.0 and 114.0 < lon < 115.5:
            elev_score, elev = 4.5, 800
        elif lat > 5.0 and 115.0 < lon < 117.0:
            elev_score, elev = 4.5, 600
        elif lat > 4.0 and lon > 117.5:
            elev_score, elev = 4.0, 400
        else:
            elev_score, elev = 3.5, 200
    else:
        if 3.3 < lat < 4.7 and 101.3 < lon < 101.9:
            elev_score, elev = 4.5, 1200
        elif lat > 4.5 and 101.5 < lon < 102.5:
            elev_score, elev = 3.5, 400
        elif lat > 5.5 and 100.3 < lon < 101.0:
            elev_score, elev = 4.0, 500
        else:
            elev_score, elev = 3.0, 150

    karst = get_known_karst_geology(lat, lon)
    geo_score = karst['underground_score'] if karst else 3.5

    composite = (elev_score * 0.25 + geo_score * 0.30 + 4.0 * 0.45) * 20
    composite += ((lat * 13.7 + lon * 7.3) % 3.0) * 0.1
    composite = min(95, max(60, composite))

    if composite >= 80:
        rating, emoji = 'Excellent', '🏙️'
    elif composite >= 65:
        rating, emoji = 'Good', '👍'
    else:
        rating, emoji = 'Moderate', '👌'

    return {
        'suitability': round(composite, 1),
        'rating': rating,
        'rating_emoji': emoji,
        'investment': 'Very High' if elev > 800 else 'High' if elev > 400 else 'Moderate',
    }


def find_nearby_alternatives(lat: float, lon: float, region: str,
                             max_km: float = 150, max_results: int = 3) -> List[Dict]:
    candidates = (BORNEO_UNDERGROUND_CITY_CANDIDATES if region == 'borneo'
                  else WEST_MALAYSIA_UNDERGROUND_CITY_CANDIDATES)

    def _collect(max_km_local: float, allow_protected: bool) -> List[Dict]:
        out = []
        for name, (cand_lat, cand_lon) in candidates.items():
            dist_km = _haversine(lat, lon, cand_lat, cand_lon)
            if dist_km > max_km_local or dist_km < 0.5:
                continue
            karst = get_known_karst_geology(cand_lat, cand_lon)
            if karst and karst.get('protected_area') and not allow_protected:
                continue
            est = _quick_static_estimate(cand_lat, cand_lon, region)
            out.append({
                'name': name,
                'lat': cand_lat,
                'lon': cand_lon,
                'distance_km': round(dist_km, 1),
                'suitability': est['suitability'],
                'rating': est['rating'],
                'rating_emoji': est['rating_emoji'],
                'investment': est['investment'],
                'protected': '🚫' if (karst and karst.get('protected_area')) else '✅',
            })
        out.sort(key=lambda x: (-x['suitability'], x['distance_km']))
        return out[:max_results]

    result = _collect(max_km, allow_protected=False)
    if not result:
        result = _collect(max_km * 2.0, allow_protected=False)
    if not result:
        result = _collect(max_km * 2.0, allow_protected=True)
    return result


def estimate_cost_range(rd: Dict) -> Dict:
    try:
        estimator = CostEstimator()
        cost = estimator.estimate(rd, size_sqm=1000000)
        mid = cost['total_cost_billions']
    except Exception:
        mid = 5.0

    extras = []
    extra_total = 0.0
    if rd.get('protected_area', {}).get('inside'):
        extras.append("UNESCO compliance (~RM 500M+)")
        extra_total += 0.5
    if rd.get('cave_warning'):
        extras.append("Cave survey (~RM 200M+)")
        extra_total += 0.2
    if rd.get('slope_deg', 0) > 25:
        extras.append("Steep slope terracing (~RM 800M+)")
        extra_total += 0.8

    blocked = bool(rd.get('protected_area', {}).get('inside'))

    if blocked:
        low = round(mid * 0.7 + extra_total, 1)
        headline_mid = round(mid + extra_total, 1)
        high = round(mid * 1.3 + extra_total, 1)
    else:
        low = round(mid * 0.7, 1)
        headline_mid = round(mid, 1)
        high = round(mid * 1.3, 1)

    return {
        'low_billion': low,
        'mid_billion': headline_mid,
        'high_billion': high,
        'base_mid_billion': round(mid, 1),
        'extras_total_billion': round(extra_total, 1),
        'blocked': blocked,
        'includes': ['Excavation', 'Construction', 'Infrastructure', 'Finishing']
                    + (['Mandatory compliance/survey/terracing'] if blocked else []),
        'excludes': (extras if not blocked else ['Land acquisition', 'Contingency (10-20%)']),
    }


def build_radar_chart(sites_data: List[Dict]) -> Optional[go.Figure]:
    if len(sites_data) < 2:
        return None
    criteria = [
        ('elevation', 'Elevation'), ('bedrock_depth', 'Bedrock'),
        ('water_table_depth', 'Water Table'), ('seismic_risk', 'Seismic'),
        ('geology', 'Geology'), ('population_density', 'Population'),
        ('coastal_proximity', 'Coastal'), ('infrastructure_access', 'Infra'),
        ('land_availability', 'Land'), ('flood_risk', 'Flood'),
        ('slope', 'Slope'), ('fault_proximity', 'Fault'),
    ]
    fig = go.Figure()
    colors = ['#00f0ff', '#ff2d95', '#39ff14', '#ffe84d', '#b026ff']
    for i, site in enumerate(sites_data[:5]):
        scores = site.get('scores', {})
        values = [scores.get(k, 0) for k, _ in criteria]
        labels = [label for _, label in criteria]
        values_closed = values + [values[0]]
        labels_closed = labels + [labels[0]]
        fig.add_trace(go.Scatterpolar(
            r=values_closed, theta=labels_closed, fill='toself',
            name=site.get('name', f'Site {i+1}'),
            line_color=colors[i % len(colors)],
            fillcolor=colors[i % len(colors)], opacity=0.3,
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], tickfont=dict(color='#00f0ff')),
            bgcolor='rgba(15, 15, 35, 0.8)',
        ),
        paper_bgcolor='rgba(10, 10, 20, 0)',
        font=dict(color='#ffffff'),
        height=500,
    )
    return fig

# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

def generate_recommendation_strategy(result_data: Dict) -> Dict:
    score = result_data.get('suitability_percentage', 0)
    details = result_data.get('details', {})
    elevation_m = result_data.get('elevation_m', 0)
    flood_risk = result_data.get('flood_risk', 'Unknown')
    population_density = result_data.get('population_density', 0)
    coastal_distance = result_data.get('coastal_distance_km', 0)
    bedrock_depth = result_data.get('bedrock_depth_m', 50)
    water_table = result_data.get('water_table_depth_m', 10)
    seismic_risk = result_data.get('seismic_risk', 'Low')
    protected_area = result_data.get('protected_area', {})
    cave_warning = result_data.get('cave_warning')
    slope_deg = result_data.get('slope_deg', 0)
    nearest_fault = result_data.get('nearest_fault', {})
    investment_band_hint = result_data.get('investment_band', None)

    recommendations = {
        'immediate_actions': [], 'short_term_actions': [], 'long_term_actions': [],
        'investment_required': 'Low', 'overall_feasibility': 'High',
        'risk_level': 'Low', 'timeline_summary': {}
    }

    def add_action(bucket, text, priority, cost):
        recommendations[bucket].append({'text': text, 'priority': priority, 'cost': cost})

    if elevation_m < 20:
        add_action('immediate_actions', '🚨 CRITICAL: Low elevation (<20m).', 'Critical', '💸💸💸💸💸')
        recommendations['investment_required'] = 'Very High'
    elif elevation_m < 50:
        add_action('short_term_actions', '🌊 Moderate elevation (20-50m).', 'High', '💸💸💸')
        recommendations['investment_required'] = 'Moderate'
    elif elevation_m < 200:
        add_action('immediate_actions', '✅ Good elevation (50-200m).', 'Low', '💸')
    elif elevation_m < 500:
        add_action('short_term_actions', '⛰️ High elevation (200-500m).', 'Medium', '💸💸')
    elif elevation_m <= 2000:
        add_action('short_term_actions', '🏔️ Very high elevation (500-2000m).', 'Low', '💸💸')
    else:
        add_action('short_term_actions', '🏔️ Alpine elevation (>2000m).', 'Medium', '💸💸💸')

    if bedrock_depth < 10:
        add_action('immediate_actions', f'🪨 VERY SHALLOW BEDROCK ({bedrock_depth:.0f}m) - limited excavation depth.', 'High', '💸💸')
    elif bedrock_depth < 20:
        add_action('immediate_actions', f'🪨 SHALLOW BEDROCK ({bedrock_depth:.0f}m) - restricted depth.', 'Medium', '💸💸')
    elif bedrock_depth < 50:
        add_action('immediate_actions', f'🪨 MODERATE BEDROCK ({bedrock_depth:.0f}m) - adequate for shallow city.', 'Low', '💸💸')
    elif bedrock_depth < 100:
        add_action('short_term_actions', f'🪨 DEEP BEDROCK ({bedrock_depth:.0f}m) - good for deep construction.', 'Medium', '💸💸💸')
    else:
        add_action('long_term_actions', f'🪨 VERY DEEP BEDROCK ({bedrock_depth:.0f}m) - excavation cost high.', 'High', '💸💸💸💸')

    if water_table < 10:
        add_action('immediate_actions', f'💧 SHALLOW WATER TABLE ({water_table:.0f}m) - dewatering required.', 'Critical', '💸💸💸💸')
        recommendations['investment_required'] = 'Very High'
    elif water_table < 30:
        add_action('short_term_actions', f'💧 MODERATE WATER TABLE ({water_table:.0f}m) - waterproofing needed.', 'High', '💸💸💸')
        if recommendations['investment_required'] == 'Low':
            recommendations['investment_required'] = 'Moderate'
    elif water_table < 60:
        add_action('immediate_actions', f'💧 GOOD WATER TABLE ({water_table:.0f}m) - manageable.', 'Low', '💸💸')
    else:
        add_action('immediate_actions', f'💧 DEEP WATER TABLE ({water_table:.0f}m) - excellent.', 'Low', '💸')

    if population_density > 5:
        add_action('immediate_actions', '🏙️ HIGH POPULATION DENSITY.', 'High', '💸💸💸💸')
    elif population_density > 2:
        add_action('short_term_actions', '🏘️ MODERATE POPULATION.', 'Medium', '💸💸💸')
    else:
        add_action('immediate_actions', '✅ VERY LOW POPULATION.', 'Low', '💸')

    if seismic_risk == 'High':
        add_action('immediate_actions', '🌋 HIGH SEISMIC RISK!', 'Critical', '💸💸💸💸💸')
        recommendations['investment_required'] = 'Very High'
    elif seismic_risk in ('Moderate', 'Low-Moderate'):
        add_action('short_term_actions', f'🌋 {seismic_risk.upper()} SEISMIC RISK.', 'High', '💸💸💸💸')
        if recommendations['investment_required'] not in ('Very High', 'High'):
            recommendations['investment_required'] = 'High'
    else:
        add_action('immediate_actions', '✅ LOW SEISMIC RISK.', 'Low', '💸')

    if coastal_distance < 5:
        add_action('immediate_actions', f'🌊 COASTAL PROXIMITY ({coastal_distance:.0f}km) - sea-level rise risk.', 'High', '💸💸💸')
    elif coastal_distance < 30:
        add_action('short_term_actions', f'🚢 NEAR COAST ({coastal_distance:.0f}km) - balanced access.', 'Medium', '💸💸')
    else:
        add_action('long_term_actions', f'🚛 INLAND ({coastal_distance:.0f}km) - safer from sea-level rise.', 'Low', '💸💸')

    land_details = details.get('land_availability', {}).get('value', {})
    if isinstance(land_details, dict):
        forest = land_details.get('forest_areas', 0)
        developed = land_details.get('developed_areas', 0)
        if forest > 20 and developed < 5:
            add_action('immediate_actions', '🌳 ABUNDANT LAND.', 'Low', '💸')
        elif forest > 10 and developed < 10:
            add_action('short_term_actions', '🌿 GOOD LAND AVAILABILITY.', 'Medium', '💸💸')
        else:
            add_action('immediate_actions', '🏗️ LIMITED LAND.', 'High', '💸💸💸💸')

    if flood_risk == 'High':
        add_action('immediate_actions', '🌊 HIGH FLOOD RISK!', 'Critical', '💸💸💸💸💸')
        recommendations['investment_required'] = 'Very High'
    elif flood_risk == 'Moderate':
        add_action('short_term_actions', '🌊 MODERATE FLOOD RISK.', 'High', '💸💸💸')
        if recommendations['investment_required'] != 'Very High':
            recommendations['investment_required'] = 'Moderate'

    infra_details = details.get('infrastructure_access', {}).get('value', {})
    if isinstance(infra_details, dict):
        if infra_details.get('airports', 0) == 0:
            add_action('short_term_actions', '✈️ No airport within range (access limited).', 'High', '💸💸💸')
        if infra_details.get('major_roads', 0) == 0:
            add_action('short_term_actions', '🛣️ No major roads (access limited).', 'High', '💸💸💸')
        if infra_details.get('ports', 0) == 0:
            add_action('long_term_actions', '🚢 No port (supply chain cost).', 'Medium', '💸💸💸💸')
        if infra_details.get('power_facilities', 0) == 0:
            add_action('long_term_actions', '⚡ No power infrastructure (off-grid required).', 'High', '💸💸💸💸')

    if protected_area.get('inside'):
        add_action('immediate_actions', f'🚫 PROTECTED AREA OVERLAP: {protected_area.get("name", "Unknown")}.', 'Critical', '💸💸💸💸💸')
        recommendations['investment_required'] = 'Very High'
    elif protected_area.get('near'):
        add_action('short_term_actions', f'⚠️ Near protected area: {protected_area.get("name", "Unknown")}.', 'High', '💸💸')

    if cave_warning:
        add_action('immediate_actions', f'🗿 CAVE SYSTEM WARNING: {cave_warning}', 'High', '💸💸')

    if slope_deg > 25:
        add_action('short_term_actions', f'⛰️ Steep slope ({slope_deg:.1f}°).', 'High', '💸💸💸💸')

    if nearest_fault.get('distance_km', 999) < 30:
        add_action('immediate_actions', f'🌐 FAULT PROXIMITY: {nearest_fault.get("name", "Unknown")}.', 'High', '💸💸💸')

    high_cost_longterm = sum(1 for a in recommendations['long_term_actions'] if '💸💸💸' in a.get('cost', ''))
    if high_cost_longterm >= 2 and recommendations['investment_required'] not in ('Very High',):
        recommendations['investment_required'] = 'Very High'
    if investment_band_hint == 'Very High':
        recommendations['investment_required'] = 'Very High'

    critical_count = sum(1 for a in recommendations['immediate_actions'] if a['priority'] == 'Critical')
    high_count = sum(1 for a in recommendations['short_term_actions'] if a['priority'] == 'High')

    if score >= 80: score_band, score_emoji = 'Excellent', '✅'
    elif score >= 65: score_band, score_emoji = 'Good', '👍'
    elif score >= 50: score_band, score_emoji = 'Moderate', '👌'
    elif score >= 35: score_band, score_emoji = 'Limited', '⚠️'
    else: score_band, score_emoji = 'Poor', '❌'

    if protected_area.get('inside'):
        feasibility = '🚫 BLOCKED — Protected area overlap'
        risk_level = 'Very High'
    elif critical_count >= 3:
        feasibility = '❌ Poor - Major critical issues'
        risk_level = 'Very High'
    elif critical_count == 2:
        feasibility = '⚠️ Limited - Multiple critical issues'
        risk_level = 'High'
    elif critical_count == 1:
        feasibility = '👌 Moderate - One critical issue'
        risk_level = 'High'
    elif high_count >= 2:
        feasibility = '👌 Moderate - Several high-priority'
        risk_level = 'Medium'
    else:
        feasibility = f'{score_emoji} {score_band}'
        risk_level = {'Excellent': 'Low', 'Good': 'Low', 'Moderate': 'Medium', 'Limited': 'High', 'Poor': 'Very High'}[score_band]

    recommendations['overall_feasibility'] = feasibility
    recommendations['risk_level'] = risk_level
    recommendations['critical_action_count'] = critical_count
    recommendations['high_action_count'] = high_count
    recommendations['timeline_summary'] = {
        'immediate': f"{len(recommendations['immediate_actions'])} actions (0-6 months)",
        'short_term': f"{len(recommendations['short_term_actions'])} actions (6-18 months)",
        'long_term': f"{len(recommendations['long_term_actions'])} actions (18-36 months)"
    }
    return recommendations

# ============================================================================
# CACHE
# ============================================================================

class APICache:
    def __init__(self, cache_dir: str = "malaysia_underground_cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    def _get_cache_key(self, url, params):
        return hashlib.md5((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    def get(self, url, params):
        cf = self.cache_dir / f"{self._get_cache_key(url, params)}.json"
        if cf.exists():
            mt = datetime.fromtimestamp(cf.stat().st_mtime)
            if datetime.now() - mt < self.ttl:
                try:
                    with open(cf, 'r') as f: return json.load(f)
                except: return None
        return None
    def set(self, url, params, data):
        cf = self.cache_dir / f"{self._get_cache_key(url, params)}.json"
        try:
            with open(cf, 'w') as f: json.dump(data, f)
        except: pass
    def clear(self):
        for f in self.cache_dir.glob("*.json"): f.unlink()
    def get_stats(self):
        return {'total_cached': len(list(self.cache_dir.glob("*.json"))), 'cache_dir': str(self.cache_dir)}

api_cache = APICache()

# ============================================================================
# LOCATION DATA - SABAH
# ============================================================================

SABAH_LOCATIONS = {
    'Kota Kinabalu City Center': (5.9804, 116.0735),
    'KK Waterfront': (5.9850, 116.0750),
    'Tanjung Aru Beach': (5.9400, 116.0500),
    'Likas Bay': (5.9500, 116.0200),
    'Signal Hill': (5.9750, 116.0700),
    'Atkinson Clock Tower': (5.9800, 116.0710),
    'Sabah State Mosque': (5.9600, 116.0800),
    'Tun Mustapha Tower': (5.9900, 116.0700),
    'Sabah Museum': (5.9600, 116.0650),
    'Jesselton Point': (5.9850, 116.0750),
    '1Borneo Mall': (6.0200, 116.1100),
    'Imago Mall': (5.9800, 116.0700),
    'Suria Sabah': (5.9800, 116.0700),
    'Sutera Harbour': (5.9600, 116.0600),
    'Queen Elizabeth Hospital': (5.9680, 116.0680),
    'KPJ Sabah Hospital': (5.9800, 116.0730),
    'Universiti Malaysia Sabah': (6.0300, 116.1200),
    'Penampang': (5.9000, 116.0800),
    'Putatan': (5.8800, 116.0600),
    'Tuaran': (6.1800, 116.2400),
    'Papar': (5.7300, 115.9300),
    'Kinarut': (5.8200, 116.0500),
    'Lok Kawi': (5.8500, 116.0300),
    'Kota Kinabalu Industrial Park': (5.9200, 116.0400),
    'Menggatal': (6.0200, 116.1400),
    'Sepanggar': (6.0400, 116.0900),
    'Inanam': (6.0000, 116.1200),
    'Telipok': (6.0800, 116.1900),
    'Likas': (5.9600, 116.0300),
    'Luyang': (5.9300, 116.0700),
    'Donggongon': (5.9000, 116.0900),
    'Keningau': (5.3300, 116.1600),
    'Tenom': (5.1300, 115.9500),
    'Beaufort': (5.3500, 115.7500),
    'Sipitang': (5.0800, 115.5500),
    'Nabawan': (5.0800, 116.4300),
    'Tambunan': (5.6700, 116.3600),
    'Kuala Penyu': (5.5700, 115.5800),
    'Membakut': (5.4700, 115.7800),
    'Weston': (5.2700, 115.4800),
    'Kemabong': (5.0800, 116.0800),
    'Sook': (5.1300, 116.2200),
    'Melalap': (5.0800, 115.9000),
    'Bongawan': (5.5300, 115.8300),
    'Klias': (5.4300, 115.6800),
    'Limbawang': (5.1700, 115.5800),
    'Gana': (5.0300, 115.4800),
    'Kudat': (6.8860, 116.8430),
    'Kota Marudu': (6.5000, 116.7400),
    'Pitas': (6.7200, 117.0700),
    'Banggi Island': (7.2300, 117.1700),
    'Malawali Island': (7.1500, 117.1300),
    'Tanjung Simpang Mengayau': (7.0900, 116.9100),
    'Bakapit': (6.8000, 116.8000),
    'Matunggong': (6.7700, 116.7900),
    'Tindakon': (6.8700, 116.8500),
    'Pinangsoo': (6.9200, 116.8800),
    'Perancangan': (6.9500, 116.9000),
    'Sandakan City Center': (5.8400, 118.1200),
    'Sandakan Waterfront': (5.8420, 118.1220),
    'Sandakan Hospital': (5.8480, 118.1250),
    'Sandakan Airport': (5.9010, 118.0580),
    'Sandakan Harbour': (5.8400, 118.1300),
    'Sepilok Orangutan Centre': (5.8650, 117.9420),
    'Sandakan Rainforest Discovery Centre': (5.8700, 117.9450),
    'Gomantong Caves': (5.5300, 118.0700),
    'Sukau': (5.5000, 118.2500),
    'Kinabatangan River': (5.4000, 117.8000),
    'Telupid': (5.6300, 117.1300),
    'Beluran': (5.8800, 117.5600),
    'Pamol': (5.4800, 118.0800),
    'Batu Putih': (5.3800, 117.9200),
    'Muanad': (5.4800, 118.1800),
    'Bilit': (5.4200, 117.8200),
    'Abai': (5.3500, 117.6800),
    'Batu Bulan': (5.2800, 117.5800),
    'Tawau City Center': (4.2435, 117.8853),
    'Tawau Waterfront': (4.2450, 117.8870),
    'Tawau Hospital': (4.2520, 117.8970),
    'Tawau Airport': (4.3133, 117.9183),
    'Tawau Hills Park': (4.3500, 117.9000),
    'Tawau Sports Complex': (4.2400, 117.8800),
    'Lahad Datu': (5.0300, 118.3300),
    'Semporna': (4.4800, 118.6100),
    'Kunak': (4.6800, 118.2500),
    'Silam': (4.8700, 118.2300),
    'Kalabakan': (4.2200, 117.4800),
    'Maliau Basin': (4.7200, 117.5200),
    'Danum Valley': (4.9500, 117.7800),
    'Tabin Wildlife Reserve': (5.2000, 118.6500),
    'Tungku': (4.7000, 118.2000),
    'Merotai': (4.3000, 117.8500),
    'Apas': (4.2800, 117.8800),
    'Balung': (4.1800, 117.6800),
    'Umas Umas': (4.1500, 117.5800),
    'Bombalai': (4.1200, 117.4800),
    'Tanjung Batu': (4.0500, 117.3800),
    'Mount Kinabalu': (6.0750, 116.5583),
    'Kinabalu National Park': (6.0100, 116.5400),
    'Kundasang': (5.9800, 116.5700),
    'Ranau': (5.9500, 116.6700),
    'Mesilau': (6.0400, 116.5900),
    'Poring Hot Springs': (6.0500, 116.7000),
    'Crocker Range': (5.8000, 116.3000),
    'Trus Madi': (5.5000, 116.4000),
    'Maliau Basin Conservation': (4.7200, 117.5200),
    'Long Pasia': (4.4000, 115.7500),
    'Kipungit': (6.0200, 116.6200),
    'Eastern Sabah Hills': (5.0000, 117.8500),
    'Pulau Gaya': (5.9800, 116.0200),
    'Pulau Manukan': (5.9700, 116.0000),
    'Pulau Mamutik': (5.9600, 115.9900),
    'Pulau Sapi': (5.9500, 115.9900),
    'Pulau Sulug': (5.9400, 115.9800),
    'Pulau Sipadan': (4.1140, 118.6250),
    'Pulau Mabul': (4.2400, 118.6200),
    'Pulau Kapalai': (4.2100, 118.6600),
    'Pulau Ligitan': (4.1500, 118.8800),
    'Pulau Bohey Dulang': (4.5800, 118.7800),
    'Pulau Bum Bum': (4.5000, 118.7100),
    'Pulau Sebatik': (4.1300, 117.7800),
    'Pulau Tiga': (5.7200, 115.6300),
    'Pulau Dinawan': (5.7000, 115.5800),
}

# ============================================================================
# LOCATION DATA - SARAWAK
# ============================================================================

SARAWAK_LOCATIONS = {
    'Kuching City Center': (1.5497, 110.3633),
    'Kuching Waterfront': (1.5597, 110.3433),
    'Kuching Hospital': (1.5697, 110.3533),
    'Kuching Airport': (1.4843, 110.3469),
    'Sarawak Museum': (1.5547, 110.3633),
    'Sarawak State Mosque': (1.5547, 110.3533),
    'Kuching Civic Centre': (1.5597, 110.3633),
    'Borneo Convention Centre': (1.5647, 110.3833),
    'Satok Bridge': (1.5497, 110.3433),
    'Stutong Park': (1.5347, 110.3833),
    'Damai Beach': (1.7000, 110.3800),
    'Santubong': (1.7000, 110.3800),
    'Bako National Park': (1.7400, 110.4800),
    'Semenggoh Wildlife Centre': (1.4000, 110.3300),
    'Bau': (1.4100, 110.1500),
    'Lundu': (1.6700, 109.8500),
    'Puncak Borneo': (1.2500, 110.1000),
    'Padawan': (1.3500, 110.2000),
    'Serian': (1.1700, 110.5700),
    'Siburan': (1.3000, 110.3500),
    'Tebedu': (1.1200, 110.5300),
    'Bengkoh': (1.4500, 110.2500),
    'Kota Sentosa': (1.4800, 110.3300),
    'Jalan Batu Kawa': (1.5000, 110.3000),
    'Matang': (1.6200, 110.1800),
    'Kuching Wetlands': (1.5800, 110.3200),
    'Kota Samarahan': (1.4500, 110.5000),
    'Asajaya': (1.6000, 110.6200),
    'Simunjan': (1.3800, 110.7500),
    'Sebuyau': (1.5200, 110.9300),
    'Sadong Jaya': (1.4700, 110.7300),
    'Muaras': (1.5300, 110.5800),
    'Semera': (1.4200, 110.4800),
    'Sri Aman': (1.2000, 111.5000),
    'Lubok Antu': (1.0500, 111.8300),
    'Engkilili': (1.1300, 111.6700),
    'Pantu': (1.0800, 111.4200),
    'Lingga': (1.3300, 111.1500),
    'Balai Ringin': (1.0300, 111.1500),
    'Rimbang': (1.1000, 111.3000),
    'Betong': (1.4100, 111.5300),
    'Debak': (1.5600, 111.4200),
    'Pusa': (1.4800, 111.3000),
    'Saratok': (1.7400, 111.3200),
    'Spaoh': (1.4500, 111.4500),
    'Maludam': (1.6500, 111.2500),
    'Roban': (1.6800, 111.3800),
    'Sarikei': (2.1000, 111.8000),
    'Bintangor': (2.1500, 111.9000),
    'Julau': (2.0200, 111.9100),
    'Pakan': (1.8800, 111.7800),
    'Matu': (2.1000, 111.5300),
    'Daro': (2.0500, 111.4800),
    'Jakar': (2.0800, 111.6500),
    'Sibu City Center': (2.2871, 111.8301),
    'Sibu Waterfront': (2.2971, 111.8201),
    'Sibu Hospital': (2.2971, 111.8401),
    'Sibu Airport': (2.2586, 111.9661),
    'Sibu Central Market': (2.2871, 111.8301),
    'Tua Pek Kong Temple': (2.2871, 111.8301),
    'Kanowit': (2.1000, 112.1500),
    'Selangau': (2.5200, 112.3200),
    'Tatau': (2.8800, 112.8500),
    'Nanga Dap': (2.3200, 112.1000),
    'Durin': (2.2000, 111.9000),
    'Sungei Bidut': (2.2500, 111.7500),
    'Mukah': (2.9064, 112.0800),
    'Dalat': (2.7500, 111.9700),
    'Oya': (2.8500, 111.8500),
    'Balingian': (2.9200, 112.5300),
    'Tanjung Manis': (2.7100, 111.6200),
    'Igan': (2.8200, 111.7500),
    'Ladang': (2.7800, 112.0500),
    'Kapit': (2.0000, 112.5000),
    'Song': (2.0100, 112.5400),
    'Belaga': (2.7000, 113.7800),
    'Bakun Dam': (2.7600, 113.9300),
    'Murum Dam': (2.9400, 114.1700),
    'Baleh': (2.3000, 113.2000),
    'Nanga Merit': (1.8000, 112.8000),
    'Rumah Siga': (2.2000, 113.0000),
    'Bintulu City Center': (3.1746, 113.0316),
    'Bintulu Waterfront': (3.1846, 113.0216),
    'Bintulu Hospital': (3.1846, 113.0416),
    'Bintulu Airport': (3.1232, 113.0195),
    'Tanjung Batu Beach': (3.1946, 113.0116),
    'Bintulu Port': (3.1746, 113.0316),
    'Sebauh': (3.1000, 112.9800),
    'Samalaju': (3.4500, 113.1200),
    'Tubau': (3.1800, 113.1300),
    'Jepak': (3.1500, 112.9800),
    'Kemena': (3.2000, 113.0000),
    'Miri City Center': (4.3995, 113.9918),
    'Miri Waterfront': (4.4095, 113.9818),
    'Miri Hospital': (4.4095, 113.9918),
    'Miri Airport': (4.3223, 113.9868),
    'Miri Marina': (4.4195, 113.9718),
    'Tanjung Lobang': (4.4295, 113.9618),
    'Grand Old Lady': (4.3995, 113.9918),
    'Marudi': (4.1800, 114.3200),
    'Lutong': (4.4700, 114.0200),
    'Bekenu': (4.0600, 113.7700),
    'Niah National Park': (3.8100, 113.7700),
    'Lambir Hills': (4.2200, 114.0300),
    'Sibuti': (3.8000, 113.6300),
    'Kuala Baram': (4.5800, 114.0000),
    'Sungai Tujoh': (4.5000, 113.9500),
    'Piasau': (4.4200, 113.9800),
    'Permyjaya': (4.4500, 114.0000),
    'Limbang': (4.7500, 115.0000),
    'Lawas': (4.8500, 115.4000),
    'Sundar': (4.7200, 115.5800),
    'Trusan': (4.8700, 115.2000),
    'Long Semadoh': (4.0500, 115.5000),
    'Ba Kelalan': (3.9700, 115.6200),
    'Bario': (3.7300, 115.4700),
    'Mulu National Park': (4.0450, 114.9380),
    'Gunung Mulu': (4.0500, 114.9300),
    'Deer Cave': (4.0300, 114.9100),
    'Clearwater Cave': (4.0200, 114.9200),
    'Wind Cave': (4.0400, 114.9000),
    'Tebangan': (4.8000, 115.1000),
    'Merapok': (4.8300, 115.3500),
    'Bario Highlands': (3.7300, 115.4700),
    'Ba Kelalan Highlands': (3.9700, 115.6200),
    'Kelabit Highlands': (3.8000, 115.5000),
    'Long Banga': (3.6000, 115.4000),
    'Long Lellang': (3.7000, 115.3500),
    'Pa Dalih': (3.8500, 115.5200),
    'Pa Ramapuh': (3.9000, 115.5500),
}

BORNEO_LOCATIONS = {**SABAH_LOCATIONS, **SARAWAK_LOCATIONS}

BORNEO_UNDERGROUND_CITY_CANDIDATES = {
    'Kundasang Highlands, Sabah': (5.9800, 116.5700),
    'Ranau Valley, Sabah': (5.9500, 116.6700),
    'Mount Kinabalu Foothills, Sabah': (6.0100, 116.5400),
    'Crocker Range, Sabah': (5.8000, 116.3000),
    'Tambunan, Sabah': (5.6700, 116.3600),
    'Keningau, Sabah': (5.3300, 116.1600),
    'Trus Madi, Sabah': (5.5000, 116.4000),
    'Tenom, Sabah': (5.1300, 115.9500),
    'Nabawan, Sabah': (5.0800, 116.4300),
    'Maliau Basin, Sabah': (4.7200, 117.5200),
    'Danum Valley, Sabah': (4.9500, 117.7800),
    'Kinabatangan Hills, Sabah': (5.4000, 117.8000),
    'Telupid, Sabah': (5.6300, 117.1300),
    'Beluran, Sabah': (5.8800, 117.5600),
    'Pitas, Sabah': (6.7200, 117.0700),
    'Kota Marudu, Sabah': (6.5000, 116.7400),
    'Kudat Peninsula, Sabah': (6.8860, 116.8430),
    'Sepilok, Sabah': (5.8650, 117.9420),
    'Sukau, Sabah': (5.5000, 118.2500),
    'Silam, Sabah': (4.8700, 118.2300),
    'Kalabakan, Sabah': (4.2200, 117.4800),
    'Eastern Sabah Hills, Sabah': (5.0000, 117.8500),
    'Bario Highlands, Sarawak': (3.7300, 115.4700),
    'Ba Kelalan, Sarawak': (3.9700, 115.6200),
    'Mulu Highlands, Sarawak': (4.0450, 114.9380),
    'Kelabit Highlands, Sarawak': (3.8000, 115.5000),
    'Lambir Hills, Sarawak': (4.2200, 114.0300),
    'Miri Coast, Sarawak': (4.3995, 113.9918),
    'Bintulu Coast, Sarawak': (3.1746, 113.0316),
    'Lawas Coast, Sarawak': (4.8500, 115.4000),
    'Limbang, Sarawak': (4.7500, 115.0000),
    'Marudi, Sarawak': (4.1800, 114.3200),
    'Baram River, Sarawak': (4.3000, 114.2000),
    'Samalaju, Sarawak': (3.4500, 113.1200),
    'Balingian, Sarawak': (2.9200, 112.5300),
    'Mukah, Sarawak': (2.9064, 112.0800),
    'Tanjung Manis, Sarawak': (2.7100, 111.6200),
    'Dalat, Sarawak': (2.7500, 111.9700),
    'Kuala Baram, Sarawak': (4.5800, 114.0000),
    'Tanjung Lobang, Sarawak': (4.4295, 113.9618),
}

# ============================================================================
# LOCATION DATA - WEST MALAYSIA
# ============================================================================

WEST_MALAYSIA_LOCATIONS = {
    'Kangar (Perlis)': (6.4414, 100.1986),
    'Arau (Perlis)': (6.4297, 100.2703),
    'Padang Besar (Perlis)': (6.6601, 100.3244),
    'Kuala Perlis (Perlis)': (6.4000, 100.1300),
    'Chuping (Perlis)': (6.5000, 100.2600),
    'Wang Kelian (Perlis)': (6.6800, 100.1700),
    'Beseri (Perlis)': (6.4700, 100.2200),
    'Simpang Empat (Perlis)': (6.4600, 100.2100),
    'Alor Setar (Kedah)': (6.1248, 100.3678),
    'Sungai Petani (Kedah)': (5.6470, 100.4877),
    'Kulim (Kedah)': (5.3649, 100.5600),
    'Langkawi (Kedah)': (6.3500, 99.8000),
    'Kuah (Langkawi)': (6.3265, 99.8430),
    'Pantai Cenang (Langkawi)': (6.2930, 99.7250),
    'Teluk Ewa (Langkawi)': (6.4000, 99.9000),
    'Datai Bay (Langkawi)': (6.4700, 99.6800),
    'Baling (Kedah)': (5.6800, 100.9200),
    'Sik (Kedah)': (5.8200, 100.7400),
    'Pendang (Kedah)': (6.0000, 100.4700),
    'Jitra (Kedah)': (6.2683, 100.4225),
    'Yan (Kedah)': (5.8000, 100.3700),
    'Gurun (Kedah)': (5.8200, 100.4700),
    'Bedong (Kedah)': (5.7300, 100.5200),
    'Kuala Nerang (Kedah)': (6.1500, 100.6000),
    'George Town (Penang)': (5.4141, 100.3288),
    'Bayan Lepas (Penang)': (5.2950, 100.2700),
    'Batu Ferringhi (Penang)': (5.4750, 100.2400),
    'Balik Pulau (Penang)': (5.3500, 100.2300),
    'Butterworth (Penang)': (5.3990, 100.3630),
    'Bukit Mertajam (Penang)': (5.3630, 100.4670),
    'Nibong Tebal (Penang)': (5.1700, 100.4800),
    'Teluk Bahang (Penang)': (5.4600, 100.2100),
    'Gertak Sanggul (Penang)': (5.2700, 100.2000),
    'Batu Maung (Penang)': (5.2800, 100.2900),
    'Teluk Kumbar (Penang)': (5.2900, 100.2400),
    'Pulau Betong (Penang)': (5.3300, 100.2000),
    'Ipoh (Perak)': (4.5975, 101.0901),
    'Taiping (Perak)': (4.8500, 100.7333),
    'Teluk Intan (Perak)': (4.0259, 101.0214),
    'Kuala Kangsar (Perak)': (4.7700, 100.9400),
    'Lumut (Perak)': (4.2300, 100.6300),
    'Pangkor Island (Perak)': (4.2200, 100.5600),
    'Sitiawan (Perak)': (4.2200, 100.7000),
    'Batu Gajah (Perak)': (4.4700, 101.0400),
    'Kampar (Perak)': (4.3100, 101.1500),
    'Tapah (Perak)': (4.2000, 101.2600),
    'Tanjung Malim (Perak)': (3.6800, 101.5200),
    'Gerik (Perak)': (5.4300, 101.1300),
    'Lenggong (Perak)': (5.1000, 100.9700),
    'Pengkalan Hulu (Perak)': (5.7000, 100.9900),
    'Segari (Perak)': (4.2800, 100.6000),
    'Pantai Remis (Perak)': (4.4500, 100.6300),
    'Gopeng (Perak)': (4.4300, 101.1600),
    'Shah Alam (Selangor)': (3.0733, 101.5185),
    'Petaling Jaya (Selangor)': (3.1073, 101.6067),
    'Subang Jaya (Selangor)': (3.0567, 101.5850),
    'Klang (Selangor)': (3.0333, 101.4500),
    'Port Klang (Selangor)': (3.0000, 101.4000),
    'Kuala Selangor (Selangor)': (3.3500, 101.2500),
    'Kuala Kubu Bharu (Selangor)': (3.5600, 101.6400),
    'Rawang (Selangor)': (3.3200, 101.5800),
    'Sepang (Selangor)': (2.7000, 101.7500),
    'Banting (Selangor)': (2.8100, 101.5000),
    'Morib (Selangor)': (2.7500, 101.4400),
    'Tanjung Sepat (Selangor)': (2.6600, 101.5600),
    'Sekinchan (Selangor)': (3.5100, 101.1000),
    'Sabak Bernam (Selangor)': (3.7700, 100.9800),
    'Kajang (Selangor)': (2.9900, 101.7900),
    'Bangi (Selangor)': (2.9500, 101.7800),
    'Putrajaya (FT)': (2.9264, 101.6964),
    'Cyberjaya (Selangor)': (2.9200, 101.6500),
    'Puchong (Selangor)': (3.0000, 101.6200),
    'Batang Kali (Selangor)': (3.4700, 101.6500),
    'Carey Island (Selangor)': (2.8700, 101.3800),
    'Pulau Ketam (Selangor)': (3.0200, 101.2500),
    'Pulau Carey (Selangor)': (2.8800, 101.3500),
    'Pulau Indah (Selangor)': (2.9800, 101.3200),
    'Kuala Langat (Selangor)': (2.8500, 101.4500),
    'Kuala Lumpur City Centre': (3.1390, 101.6869),
    'KLCC (KL)': (3.1578, 101.7120),
    'Bukit Bintang (KL)': (3.1450, 101.7100),
    'Cheras (KL)': (3.0800, 101.7300),
    'Kepong (KL)': (3.2100, 101.6400),
    'Sungai Besi (KL)': (3.0600, 101.7000),
    'Batu Caves (Selangor)': (3.2379, 101.6840),
    'Seremban (N. Sembilan)': (2.7297, 101.9381),
    'Port Dickson (N. Sembilan)': (2.5228, 101.7967),
    'Nilai (N. Sembilan)': (2.8200, 101.8000),
    'Bahau (N. Sembilan)': (2.8000, 102.4000),
    'Tampin (N. Sembilan)': (2.4700, 102.2300),
    'Kuala Pilah (N. Sembilan)': (2.7400, 102.2500),
    'Rembau (N. Sembilan)': (2.5900, 102.0900),
    'Gemas (N. Sembilan)': (2.5800, 102.6100),
    'Lukut (N. Sembilan)': (2.5800, 101.8300),
    'Tanjung Tuan (N. Sembilan)': (2.4000, 101.8500),
    'Blue Lagoon (N. Sembilan)': (2.4800, 101.8300),
    'Linggi (N. Sembilan)': (2.4800, 102.0000),
    'Kuala Klawang (N. Sembilan)': (2.8200, 102.0400),
    'Melaka City (Melaka)': (2.1896, 102.2501),
    'Ayer Keroh (Melaka)': (2.2700, 102.2900),
    'Alor Gajah (Melaka)': (2.3800, 102.2100),
    'Jasin (Melaka)': (2.3100, 102.4300),
    'Masjid Tanah (Melaka)': (2.3500, 102.1100),
    'Merlimau (Melaka)': (2.1400, 102.4300),
    'Tanjung Kling (Melaka)': (2.2200, 102.1600),
    'Tanjung Bidara (Melaka)': (2.2800, 102.0900),
    'Pengkalan Balak (Melaka)': (2.3200, 102.0800),
    'Kuala Sungai Baru (Melaka)': (2.3500, 102.0400),
    'Johor Bahru (Johor)': (1.4927, 103.7414),
    'Iskandar Puteri (Johor)': (1.4300, 103.6300),
    'Kulai (Johor)': (1.6600, 103.6000),
    'Skudai (Johor)': (1.5400, 103.6700),
    'Senai (Johor)': (1.6200, 103.6600),
    'Pasir Gudang (Johor)': (1.4700, 103.9000),
    'Pengerang (Johor)': (1.3600, 104.1700),
    'Kota Tinggi (Johor)': (1.7300, 103.9000),
    'Mersing (Johor)': (2.4300, 103.8300),
    'Batu Pahat (Johor)': (1.8500, 102.9300),
    'Muar (Johor)': (2.0500, 102.5700),
    'Segamat (Johor)': (2.5100, 102.8100),
    'Kluang (Johor)': (2.0300, 103.3200),
    'Pontian (Johor)': (1.4800, 103.3800),
    'Desaru (Johor)': (1.5500, 104.2600),
    'Endau (Johor)': (2.6500, 103.6200),
    'Pulau Aur (Johor)': (2.4500, 104.5200),
    'Pulau Pemanggil (Johor)': (2.5800, 104.3300),
    'Pulau Sibu (Johor)': (2.2000, 104.1000),
    'Pulau Tinggi (Johor)': (2.3000, 104.1200),
    'Pulau Rawa (Johor)': (2.5300, 103.9700),
    'Pulau Kukup (Johor)': (1.3100, 103.4200),
    'Tanjung Piai (Johor)': (1.2700, 103.5100),
    'Labis (Johor)': (2.3800, 103.0200),
    'Yong Peng (Johor)': (2.0100, 103.0600),
    'Ayer Hitam (Johor)': (1.9200, 103.1800),
    'Kota Bharu (Kelantan)': (6.1256, 102.2386),
    'Kubang Kerian (Kelantan)': (6.1000, 102.2800),
    'Pasir Puteh (Kelantan)': (5.8300, 102.4000),
    'Pasir Mas (Kelantan)': (6.0500, 102.1400),
    'Tumpat (Kelantan)': (6.2000, 102.1700),
    'Bachok (Kelantan)': (6.0700, 102.4000),
    'Tanah Merah (Kelantan)': (5.8000, 102.1500),
    'Machang (Kelantan)': (5.7700, 102.2100),
    'Kuala Krai (Kelantan)': (5.5300, 102.2000),
    'Gua Musang (Kelantan)': (4.8800, 101.9600),
    'Jeli (Kelantan)': (5.7000, 101.8400),
    'Tok Bali (Kelantan)': (5.8200, 102.4500),
    'Pantai Cahaya Bulan (Kelantan)': (6.1300, 102.2900),
    'Kuala Terengganu (Terengganu)': (5.3303, 103.1408),
    'Kuala Nerus (Terengganu)': (5.3800, 103.0800),
    'Kemaman (Terengganu)': (4.2300, 103.4200),
    'Chukai (Terengganu)': (4.2200, 103.4200),
    'Kerteh (Terengganu)': (4.5200, 103.4500),
    'Paka (Terengganu)': (4.6400, 103.4400),
    'Dungun (Terengganu)': (4.7700, 103.4200),
    'Marang (Terengganu)': (5.2000, 103.2100),
    'Kuala Berang (Terengganu)': (5.0700, 102.9500),
    'Jerteh (Terengganu)': (5.7400, 102.5100),
    'Besut (Terengganu)': (5.7300, 102.5600),
    'Setiu (Terengganu)': (5.5800, 102.8000),
    'Kuala Besut (Terengganu)': (5.8300, 102.5600),
    'Pulau Perhentian (Terengganu)': (5.9100, 102.7400),
    'Pulau Redang (Terengganu)': (5.7800, 103.0000),
    'Pulau Kapas (Terengganu)': (5.2200, 103.2600),
    'Pulau Tenggol (Terengganu)': (4.8000, 103.6800),
    'Pulau Lang Tengah (Terengganu)': (5.7800, 102.8900),
    'Kijal (Terengganu)': (4.3600, 103.5000),
    'Kuantan (Pahang)': (3.8077, 103.3260),
    'Pekan (Pahang)': (3.4900, 103.3900),
    'Temerloh (Pahang)': (3.4500, 102.4200),
    'Bentong (Pahang)': (3.5200, 101.9100),
    'Raub (Pahang)': (3.7900, 101.8600),
    'Kuala Lipis (Pahang)': (4.1800, 102.0500),
    'Jerantut (Pahang)': (3.9400, 102.3600),
    'Mentakab (Pahang)': (3.4900, 102.3500),
    'Cameron Highlands (Pahang)': (4.4700, 101.3800),
    'Genting Highlands (Pahang)': (3.4200, 101.7900),
    'Fraser\'s Hill (Pahang)': (3.7100, 101.7400),
    'Tioman Island (Pahang)': (2.7900, 104.1700),
    'Cherating (Pahang)': (4.1300, 103.3900),
    'Balok (Pahang)': (3.9500, 103.3700),
    'Beserah (Pahang)': (3.8800, 103.3600),
    'Sungai Lembing (Pahang)': (3.9200, 103.0300),
    'Gambang (Pahang)': (3.7100, 103.0900),
    'Maran (Pahang)': (3.5800, 102.7700),
    'Kuala Rompin (Pahang)': (2.8200, 103.4800),
    'Nenasi (Pahang)': (2.9900, 103.4900),
    'Gebeng (Pahang)': (3.9600, 103.3700),
    'Bukit Ibam (Pahang)': (3.3000, 102.8500),
    'Lanchang (Pahang)': (3.5000, 102.2000),
    'Janda Baik (Pahang)': (3.3200, 101.8800),
}

WEST_MALAYSIA_UNDERGROUND_CITY_CANDIDATES = {
    'Cameron Highlands (Pahang)': (4.4700, 101.3800),
    'Fraser\'s Hill (Pahang)': (3.7100, 101.7400),
    'Genting Highlands (Pahang)': (3.4200, 101.7900),
    'Bukit Tinggi (Pahang)': (3.4000, 101.8200),
    'Janda Baik (Pahang)': (3.3200, 101.8800),
    'Kuala Lipis (Pahang)': (4.1800, 102.0500),
    'Jerantut (Pahang)': (3.9400, 102.3600),
    'Sungai Lembing (Pahang)': (3.9200, 103.0300),
    'Bukit Ibam (Pahang)': (3.3000, 102.8500),
    'Lanchang (Pahang)': (3.5000, 102.2000),
    'Maran (Pahang)': (3.5800, 102.7700),
    'Gopeng (Perak)': (4.4300, 101.1600),
    'Gerik (Perak)': (5.4300, 101.1300),
    'Lenggong (Perak)': (5.1000, 100.9700),
    'Pengkalan Hulu (Perak)': (5.7000, 100.9900),
    'Kuala Kangsar (Perak)': (4.7700, 100.9400),
    'Tapah (Perak)': (4.2000, 101.2600),
    'Kampar (Perak)': (4.3100, 101.1500),
    'Gua Musang (Kelantan)': (4.8800, 101.9600),
    'Kuala Krai (Kelantan)': (5.5300, 102.2000),
    'Dabong (Kelantan)': (5.3800, 102.0100),
    'Jeli (Kelantan)': (5.7000, 101.8400),
    'Batang Kali (Selangor)': (3.4700, 101.6500),
    'Kuala Kubu Bharu (Selangor)': (3.5600, 101.6400),
    'Pulau Carey (Selangor)': (2.8800, 101.3500),
    'Pulau Ketam (Selangor)': (3.0200, 101.2500),
    'Kuala Klawang (N. Sembilan)': (2.8200, 102.0400),
    'Bahau (N. Sembilan)': (2.8000, 102.4000),
    'Gemas (N. Sembilan)': (2.5800, 102.6100),
    'Labis (Johor)': (2.3800, 103.0200),
    'Segamat (Johor)': (2.5100, 102.8100),
    'Yong Peng (Johor)': (2.0100, 103.0600),
    'Ayer Hitam (Johor)': (1.9200, 103.1800),
    'Kluang Rural (Johor)': (2.0300, 103.3200),
    'Pulau Aur (Johor)': (2.4500, 104.5200),
    'Pulau Pemanggil (Johor)': (2.5800, 104.3300),
    'Pulau Tioman (Pahang)': (2.7900, 104.1700),
    'Baling (Kedah)': (5.6800, 100.9200),
    'Sik (Kedah)': (5.8200, 100.7400),
    'Pendang (Kedah)': (6.0000, 100.4700),
    'Wang Kelian (Perlis)': (6.6800, 100.1700),
    'Padang Besar (Perlis)': (6.6601, 100.3244),
    'Kuala Berang (Terengganu)': (5.0700, 102.9500),
    'Setiu (Terengganu)': (5.5800, 102.8000),
    'Pulau Tenggol (Terengganu)': (4.8000, 103.6800),
    'Pulau Redang (Terengganu)': (5.7800, 103.0000),
    'Pulau Perhentian (Terengganu)': (5.9100, 102.7400),
    'Pulau Kapas (Terengganu)': (5.2200, 103.2600),
    'Pulau Lang Tengah (Terengganu)': (5.7800, 102.8900),
}

# ============================================================================
# STATIC REFERENCE DATA
# ============================================================================

_AIRPORT_MIN_QUERY_DIST_KM = 1.0

STATIC_AIRPORTS = {
    'Kota Kinabalu International': (5.9375, 116.0490),
    'Sandakan Airport': (5.9010, 118.0580),
    'Tawau Airport': (4.3133, 117.9183),
    'Kudat Airport': (6.9180, 116.8280),
    'Lahad Datu Airport': (5.0310, 118.3200),
    'Semporna Airport': (4.4800, 118.6100),
    'Keningau Airport': (5.3300, 116.1600),
    'Ranau Airport': (5.9500, 116.6700),
    'Kota Marudu Airport': (6.5000, 116.7400),
    'Pitas Airport': (6.7200, 117.0700),
    'Telupid Airport': (5.6300, 117.1300),
    'Beluran Airport': (5.8800, 117.5600),
    'Kunak Airport': (4.6800, 118.2500),
    'Sipitang Airport': (5.0800, 115.5500),
    'Beaufort Airport': (5.3500, 115.7500),
    'Tenom Airport': (5.1300, 115.9500),
    'Tambunan Airport': (5.6700, 116.3600),
    'Papar Airport': (5.7300, 115.9300),
    'Tuaran Airport': (6.1800, 116.2400),
    'Pulau Sipadan Airport': (4.1140, 118.6250),
    'Kuching International': (1.4843, 110.3469),
    'Miri Airport': (4.3223, 113.9868),
    'Sibu Airport': (2.2586, 111.9661),
    'Bintulu Airport': (3.1232, 113.0195),
    'Limbang Airport': (4.7560, 115.0100),
    'Lawas Airport': (4.8500, 115.4000),
    'Mukah Airport': (2.9064, 112.0800),
    'Sarikei Airport': (2.1160, 111.5360),
    'Kapit Airport': (2.0000, 112.5000),
    'Betong Airport': (1.4100, 111.5300),
    'Sri Aman Airport': (1.2000, 111.5000),
    'Marudi Airport': (4.1800, 114.3200),
    'Bario Airport': (3.7300, 115.4700),
    'Ba Kelalan Airport': (3.9700, 115.6200),
    'Mulu Airport': (4.0483, 114.8057),
    'Long Semadoh Airport': (4.0500, 115.5000),
    'Sundar Airport': (4.7200, 115.5800),
    'Lutong Airport': (4.4700, 114.0200),
    'Tatau Airport': (2.8800, 112.8500),
    'Selangau Airport': (2.5200, 112.3200),
    'Kanowit Airport': (2.1000, 112.1500),
    'Daro Airport': (2.0500, 111.4800),
    'Matu Airport': (2.1000, 111.5300),
    'Dalat Airport': (2.7500, 111.9700),
    'Oya Airport': (2.8500, 111.8500),
    'Lubok Antu Airport': (1.0500, 111.8300),
    'Engkilili Airport': (1.1300, 111.6700),
    'Pusa Airport': (1.4800, 111.3000),
    'Saratok Airport': (1.7400, 111.3200),
    'Sebauh Airport': (3.1000, 112.9800),
    'Balingian Airport': (2.9200, 112.5300),
    'Langkawi International': (6.3297, 99.7287),
    'Sultan Abdul Halim (Alor Setar)': (6.1897, 100.3982),
    'Kangar Airport': (6.4500, 100.2000),
    'Penang International': (5.2972, 100.2768),
    'Butterworth Air Base': (5.4000, 100.3700),
    'Sultan Azlan Shah (Ipoh)': (4.5679, 101.0920),
    'Taiping Airport': (4.8667, 100.7167),
    'Pulau Pangkor Airstrip': (4.2200, 100.5500),
    'Lumut RMAF Base': (4.2300, 100.6200),
    'Sultan Abdul Aziz Shah (Subang)': (3.1306, 101.5493),
    'KLIA (Sepang)': (2.7456, 101.7099),
    'KLIA2 (Sepang)': (2.7430, 101.6860),
    'Melaka International': (2.2633, 102.2517),
    'Senai International (JB)': (1.6411, 103.6696),
    'Batu Pahat Airport': (1.8500, 102.9300),
    'Mersing Airport': (2.4300, 103.8300),
    'Sultan Ahmad Shah (Kuantan)': (3.7753, 103.2090),
    'Tioman Airport': (2.8183, 104.1600),
    'Sultan Mahmud (K. Terengganu)': (5.3825, 103.1033),
    'Kerteh Airport': (4.5200, 103.4500),
    'Sultan Ismail Petra (Kota Bharu)': (6.1664, 102.2924),
    'Tok Bali Airstrip': (5.8200, 102.4500),
    'Gua Musang Airstrip': (4.8800, 101.9600),
}

STATIC_SETTLEMENTS = {
    'Kota Kinabalu': {'coords': (5.9804, 116.0735), 'population': 500000},
    'Sandakan': {'coords': (5.8400, 118.1200), 'population': 150000},
    'Tawau': {'coords': (4.2435, 117.8853), 'population': 120000},
    'Lahad Datu': {'coords': (5.0300, 118.3300), 'population': 30000},
    'Kudat': {'coords': (6.8860, 116.8430), 'population': 20000},
    'Semporna': {'coords': (4.4800, 118.6100), 'population': 25000},
    'Keningau': {'coords': (5.3300, 116.1600), 'population': 20000},
    'Ranau': {'coords': (5.9500, 116.6700), 'population': 15000},
    'Kota Marudu': {'coords': (6.5000, 116.7400), 'population': 12000},
    'Beaufort': {'coords': (5.3500, 115.7500), 'population': 10000},
    'Tenom': {'coords': (5.1300, 115.9500), 'population': 8000},
    'Tambunan': {'coords': (5.6700, 116.3600), 'population': 7000},
    'Pitas': {'coords': (6.7200, 117.0700), 'population': 6000},
    'Kunak': {'coords': (4.6800, 118.2500), 'population': 8000},
    'Sipitang': {'coords': (5.0800, 115.5500), 'population': 5000},
    'Papar': {'coords': (5.7300, 115.9300), 'population': 7000},
    'Tuaran': {'coords': (6.1800, 116.2400), 'population': 10000},
    'Penampang': {'coords': (5.9000, 116.0800), 'population': 45000},
    'Putatan': {'coords': (5.8800, 116.0600), 'population': 30000},
    'Telupid': {'coords': (5.6300, 117.1300), 'population': 4000},
    'Beluran': {'coords': (5.8800, 117.5600), 'population': 5000},
    'Kinabatangan': {'coords': (5.4000, 117.8000), 'population': 3000},
    'Kuching': {'coords': (1.5497, 110.3633), 'population': 600000},
    'Miri': {'coords': (4.3995, 113.9918), 'population': 300000},
    'Sibu': {'coords': (2.2871, 111.8301), 'population': 200000},
    'Bintulu': {'coords': (3.1746, 113.0316), 'population': 150000},
    'Limbang': {'coords': (4.7500, 115.0000), 'population': 20000},
    'Lawas': {'coords': (4.8500, 115.4000), 'population': 15000},
    'Mukah': {'coords': (2.9064, 112.0800), 'population': 18000},
    'Sarikei': {'coords': (2.1160, 111.5360), 'population': 25000},
    'Kapit': {'coords': (2.0000, 112.5000), 'population': 15000},
    'Betong': {'coords': (1.4100, 111.5300), 'population': 12000},
    'Sri Aman': {'coords': (1.2000, 111.5000), 'population': 15000},
    'Marudi': {'coords': (4.1800, 114.3200), 'population': 10000},
    'Bario': {'coords': (3.7300, 115.4700), 'population': 1000},
    'Ba Kelalan': {'coords': (3.9700, 115.6200), 'population': 2000},
    'Lutong': {'coords': (4.4700, 114.0200), 'population': 15000},
    'Samalaju': {'coords': (3.4500, 113.1200), 'population': 5000},
    'Sebauh': {'coords': (3.1000, 112.9800), 'population': 8000},
    'Balingian': {'coords': (2.9200, 112.5300), 'population': 5000},
    'Dalat': {'coords': (2.7500, 111.9700), 'population': 8000},
    'Oya': {'coords': (2.8500, 111.8500), 'population': 6000},
    'Tanjung Manis': {'coords': (2.7100, 111.6200), 'population': 7000},
    'Kanowit': {'coords': (2.1000, 112.1500), 'population': 5000},
    'Selangau': {'coords': (2.5200, 112.3200), 'population': 4000},
    'Tatau': {'coords': (2.8800, 112.8500), 'population': 3000},
    'Song': {'coords': (2.0100, 112.5400), 'population': 3000},
    'Belaga': {'coords': (2.7000, 113.7800), 'population': 2000},
    'Kangar': {'coords': (6.4414, 100.1986), 'population': 50000},
    'Arau': {'coords': (6.4297, 100.2703), 'population': 30000},
    'Alor Setar': {'coords': (6.1248, 100.3678), 'population': 400000},
    'Sungai Petani': {'coords': (5.6470, 100.4877), 'population': 300000},
    'Kulim': {'coords': (5.3649, 100.5600), 'population': 150000},
    'Langkawi': {'coords': (6.3500, 99.8000), 'population': 90000},
    'Baling': {'coords': (5.6800, 100.9200), 'population': 30000},
    'George Town': {'coords': (5.4141, 100.3288), 'population': 700000},
    'Butterworth': {'coords': (5.3990, 100.3630), 'population': 200000},
    'Bukit Mertajam': {'coords': (5.3630, 100.4670), 'population': 200000},
    'Bayan Lepas': {'coords': (5.2950, 100.2700), 'population': 150000},
    'Ipoh': {'coords': (4.5975, 101.0901), 'population': 750000},
    'Taiping': {'coords': (4.8500, 100.7333), 'population': 200000},
    'Teluk Intan': {'coords': (4.0259, 101.0214), 'population': 100000},
    'Kuala Kangsar': {'coords': (4.7700, 100.9400), 'population': 50000},
    'Lumut': {'coords': (4.2300, 100.6300), 'population': 40000},
    'Sitiawan': {'coords': (4.2200, 100.7000), 'population': 150000},
    'Shah Alam': {'coords': (3.0733, 101.5185), 'population': 700000},
    'Petaling Jaya': {'coords': (3.1073, 101.6067), 'population': 800000},
    'Subang Jaya': {'coords': (3.0567, 101.5850), 'population': 700000},
    'Klang': {'coords': (3.0333, 101.4500), 'population': 900000},
    'Kuala Lumpur': {'coords': (3.1390, 101.6869), 'population': 1800000},
    'Putrajaya': {'coords': (2.9264, 101.6964), 'population': 100000},
    'Cyberjaya': {'coords': (2.9200, 101.6500), 'population': 100000},
    'Sepang': {'coords': (2.7000, 101.7500), 'population': 90000},
    'Kajang': {'coords': (2.9900, 101.7900), 'population': 300000},
    'Bangi': {'coords': (2.9500, 101.7800), 'population': 200000},
    'Kuala Selangor': {'coords': (3.3500, 101.2500), 'population': 40000},
    'Kuala Kubu Bharu': {'coords': (3.5600, 101.6400), 'population': 30000},
    'Rawang': {'coords': (3.3200, 101.5800), 'population': 200000},
    'Banting': {'coords': (2.8100, 101.5000), 'population': 40000},
    'Sekinchan': {'coords': (3.5100, 101.1000), 'population': 15000},
    'Sabak Bernam': {'coords': (3.7700, 100.9800), 'population': 30000},
    'Seremban': {'coords': (2.7297, 101.9381), 'population': 500000},
    'Port Dickson': {'coords': (2.5228, 101.7967), 'population': 100000},
    'Nilai': {'coords': (2.8200, 101.8000), 'population': 100000},
    'Bahau': {'coords': (2.8000, 102.4000), 'population': 30000},
    'Tampin': {'coords': (2.4700, 102.2300), 'population': 30000},
    'Kuala Pilah': {'coords': (2.7400, 102.2500), 'population': 20000},
    'Melaka City': {'coords': (2.1896, 102.2501), 'population': 500000},
    'Ayer Keroh': {'coords': (2.2700, 102.2900), 'population': 60000},
    'Alor Gajah': {'coords': (2.3800, 102.2100), 'population': 40000},
    'Jasin': {'coords': (2.3100, 102.4300), 'population': 30000},
    'Johor Bahru': {'coords': (1.4927, 103.7414), 'population': 1500000},
    'Iskandar Puteri': {'coords': (1.4300, 103.6300), 'population': 500000},
    'Kulai': {'coords': (1.6600, 103.6000), 'population': 200000},
    'Pasir Gudang': {'coords': (1.4700, 103.9000), 'population': 200000},
    'Pengerang': {'coords': (1.3600, 104.1700), 'population': 30000},
    'Kota Tinggi': {'coords': (1.7300, 103.9000), 'population': 50000},
    'Mersing': {'coords': (2.4300, 103.8300), 'population': 30000},
    'Batu Pahat': {'coords': (1.8500, 102.9300), 'population': 300000},
    'Muar': {'coords': (2.0500, 102.5700), 'population': 200000},
    'Segamat': {'coords': (2.5100, 102.8100), 'population': 80000},
    'Kluang': {'coords': (2.0300, 103.3200), 'population': 150000},
    'Pontian': {'coords': (1.4800, 103.3800), 'population': 50000},
    'Desaru': {'coords': (1.5500, 104.2600), 'population': 15000},
    'Kota Bharu': {'coords': (6.1256, 102.2386), 'population': 500000},
    'Kubang Kerian': {'coords': (6.1000, 102.2800), 'population': 50000},
    'Pasir Puteh': {'coords': (5.8300, 102.4000), 'population': 30000},
    'Pasir Mas': {'coords': (6.0500, 102.1400), 'population': 40000},
    'Tumpat': {'coords': (6.2000, 102.1700), 'population': 30000},
    'Bachok': {'coords': (6.0700, 102.4000), 'population': 20000},
    'Kuala Krai': {'coords': (5.5300, 102.2000), 'population': 20000},
    'Gua Musang': {'coords': (4.8800, 101.9600), 'population': 15000},
    'Kuala Terengganu': {'coords': (5.3303, 103.1408), 'population': 400000},
    'Kemaman': {'coords': (4.2300, 103.4200), 'population': 60000},
    'Chukai': {'coords': (4.2200, 103.4200), 'population': 40000},
    'Kerteh': {'coords': (4.5200, 103.4500), 'population': 20000},
    'Paka': {'coords': (4.6400, 103.4400), 'population': 15000},
    'Dungun': {'coords': (4.7700, 103.4200), 'population': 40000},
    'Marang': {'coords': (5.2000, 103.2100), 'population': 20000},
    'Kuala Berang': {'coords': (5.0700, 102.9500), 'population': 15000},
    'Jerteh': {'coords': (5.7400, 102.5100), 'population': 30000},
    'Besut': {'coords': (5.7300, 102.5600), 'population': 25000},
    'Setiu': {'coords': (5.5800, 102.8000), 'population': 15000},
    'Kuantan': {'coords': (3.8077, 103.3260), 'population': 600000},
    'Pekan': {'coords': (3.4900, 103.3900), 'population': 50000},
    'Temerloh': {'coords': (3.4500, 102.4200), 'population': 100000},
    'Bentong': {'coords': (3.5200, 101.9100), 'population': 60000},
    'Raub': {'coords': (3.7900, 101.8600), 'population': 50000},
    'Kuala Lipis': {'coords': (4.1800, 102.0500), 'population': 20000},
    'Jerantut': {'coords': (3.9400, 102.3600), 'population': 30000},
    'Mentakab': {'coords': (3.4900, 102.3500), 'population': 40000},
    'Cameron Highlands': {'coords': (4.4700, 101.3800), 'population': 40000},
    'Genting Highlands': {'coords': (3.4200, 101.7900), 'population': 30000},
    'Kuala Rompin': {'coords': (2.8200, 103.4800), 'population': 20000},
    'Cherating': {'coords': (4.1300, 103.3900), 'population': 10000},
    'Balok': {'coords': (3.9500, 103.3700), 'population': 15000},
    'Gambang': {'coords': (3.7100, 103.0900), 'population': 20000},
    'Maran': {'coords': (3.5800, 102.7700), 'population': 15000},
}

UNDERGROUND_CITY_TAGS = {
    'hospital': [('amenity', 'hospital'), ('amenity', 'clinic')],
    'airport': [('aeroway', 'aerodrome'), ('aeroway', 'airport'), ('aeroway', 'heliport')],
    'port': [('harbour', 'yes'), ('amenity', 'ferry_terminal'), ('waterway', 'port')],
    'power_plant': [('power', 'plant'), ('power', 'substation'), ('power', 'generator')],
    'road': [('highway', 'motorway'), ('highway', 'trunk'), ('highway', 'primary')],
    'railway': [('railway', 'rail'), ('railway', 'station')],
    'telecom': [('telecom', 'tower'), ('telecom', 'exchange'), ('man_made', 'tower')],
    'population_center': [('place', 'city'), ('place', 'town'), ('place', 'village')],
}

KNOWN_KARST_REGIONS = {
    (4.0, 4.1, 114.8, 115.0): {
        'name': 'Mulu Karst Formation',
        'type': 'Limestone Karst',
        'age': 'Eocene-Miocene',
        'significance': 'World Heritage Site - 295km of caves, massive chambers',
        'underground_score': 5.0,
        'details': 'Extremely stable limestone, natural cave systems, excellent for tunneling',
        'cave_collapse_warning': '⚠️ Documented cave systems (Deer Cave, Clearwater). Pre-tunneling geophysical survey mandatory.',
        'protected_area': True,
        'protection_name': 'Gunung Mulu National Park (UNESCO World Heritage)',
    },
    (5.8, 6.2, 116.4, 116.8): {
        'name': 'Kinabalu Granite Batholith',
        'type': 'Granitic Intrusive',
        'age': 'Miocene (7-10 Ma)',
        'significance': 'Hard crystalline rock, very stable',
        'underground_score': 5.0,
        'details': 'Excellent for deep underground construction, minimal fracturing',
        'cave_collapse_warning': None,
        'protected_area': True,
        'protection_name': 'Kinabalu Park (UNESCO World Heritage)',
    },
    (1.3, 1.8, 110.1, 110.5): {
        'name': 'Bau Limestone (Sarawak)',
        'type': 'Limestone Karst',
        'age': 'Triassic-Jurassic',
        'significance': 'Historic gold mining area, cave systems',
        'underground_score': 4.5,
        'details': 'Good karst geology with existing cave networks',
        'cave_collapse_warning': '⚠️ Historic mining area — subsidence risk. Survey required.',
        'protected_area': False,
        'protection_name': None,
    },
    (3.7, 3.9, 113.6, 113.9): {
        'name': 'Niah Caves Formation',
        'type': 'Limestone Karst',
        'age': 'Miocene',
        'significance': 'Archaeological caves, 60,000 years human history',
        'underground_score': 4.5,
        'details': 'Stable limestone, excellent natural caves',
        'cave_collapse_warning': '⚠️ Protected archaeological site — no tunneling within boundary.',
        'protected_area': True,
        'protection_name': 'Niah National Park',
    },
    (3.3, 4.7, 101.3, 101.9): {
        'name': 'Titiwangsa Granite Range',
        'type': 'Granitic Intrusive',
        'age': 'Triassic (200-250 Ma)',
        'significance': 'Main mountain range, very hard rock',
        'underground_score': 5.0,
        'details': 'Excellent for deep tunneling, minimal water ingress',
        'cave_collapse_warning': None,
        'protected_area': False,
        'protection_name': None,
    },
    (4.4, 5.6, 100.9, 101.5): {
        'name': 'Perak Limestone Belt',
        'type': 'Limestone Karst',
        'age': 'Ordovician-Permian',
        'significance': 'Historic tin mining, extensive cave systems',
        'underground_score': 4.5,
        'details': 'Well-studied karst, good for controlled tunneling',
        'cave_collapse_warning': '⚠️ Historic tin mining — mine void collapse risk. Detailed survey required.',
        'protected_area': False,
        'protection_name': None,
    },
    (5.4, 6.2, 101.9, 102.5): {
        'name': 'Kelantan Limestone',
        'type': 'Limestone Karst',
        'age': 'Permian-Triassic',
        'significance': 'Cave temples, karst hills',
        'underground_score': 4.5,
        'details': 'Good karst geology, cave systems common',
        'cave_collapse_warning': '⚠️ Cave systems common. Pre-construction survey mandatory.',
        'protected_area': False,
        'protection_name': None,
    },
    (3.3, 3.5, 101.6, 101.9): {
        'name': 'Batu Caves Formation',
        'type': 'Limestone Karst',
        'age': 'Silurian-Devonian (400+ Ma)',
        'significance': 'Iconic cave temple, 400 million year old limestone',
        'underground_score': 4.5,
        'details': 'Ancient stable limestone, major cave system',
        'cave_collapse_warning': '⚠️ Religious site — cultural sensitivity + cave stability survey required.',
        'protected_area': True,
        'protection_name': 'Batu Caves (Hindu temple)',
    },
    (4.0, 5.5, 102.5, 103.5): {
        'name': 'Pahang Volcanic Belt',
        'type': 'Volcanic/Rhyolitic',
        'age': 'Permian-Triassic',
        'significance': 'Ancient volcanic rocks',
        'underground_score': 4.0,
        'details': 'Hard volcanic rock, good for tunnels',
        'cave_collapse_warning': None,
        'protected_area': False,
        'protection_name': None,
    },
    (5.5, 6.5, 100.3, 101.0): {
        'name': 'Kedah Sedimentary Basin',
        'type': 'Sedimentary (Sandstone/Shale)',
        'age': 'Ordovician-Carboniferous',
        'significance': 'Langkawi UNESCO Geopark',
        'underground_score': 4.0,
        'details': 'Well-bedded sedimentary rock, good for construction',
        'cave_collapse_warning': None,
        'protected_area': True,
        'protection_name': 'Langkawi UNESCO Global Geopark',
    }
}

def get_known_karst_geology(lat: float, lon: float) -> Optional[Dict]:
    for (lat_min, lat_max, lon_min, lon_max), data in KNOWN_KARST_REGIONS.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return data
    return None

KNOWN_FAULT_LINES = [
    {'name': 'Sumatra Fault (proximity)', 'coords': [(2.5, 100.0), (0.5, 101.0)], 'activity': 'High', 'type': 'Strike-slip'},
    {'name': 'Semangko Fault', 'coords': [(3.0, 100.5), (1.5, 101.5)], 'activity': 'High', 'type': 'Strike-slip'},
    {'name': 'Borneo Interior Faults', 'coords': [(3.0, 114.5), (2.0, 113.5), (1.0, 112.5)], 'activity': 'Low-Moderate', 'type': 'Normal'},
    {'name': 'Crocker Fault', 'coords': [(6.0, 116.0), (5.5, 116.3), (5.0, 116.5)], 'activity': 'Moderate', 'type': 'Thrust'},
    {'name': 'Tarakan Fault', 'coords': [(3.5, 117.5), (3.0, 118.0)], 'activity': 'Low', 'type': 'Normal'},
]

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(min(1, math.sqrt(a)))

def distance_to_polyline(lat, lon, points):
    min_d = float('inf')
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        dx = p2[1] - p1[1]
        dy = p2[0] - p1[0]
        if dx == 0 and dy == 0:
            d = _haversine(lat, lon, p1[0], p1[1])
        else:
            t = max(0, min(1, ((lon - p1[1]) * dx + (lat - p1[0]) * dy) / (dx * dx + dy * dy)))
            proj_lat = p1[0] + t * dy
            proj_lon = p1[1] + t * dx
            d = _haversine(lat, lon, proj_lat, proj_lon)
        min_d = min(min_d, d)
    return min_d

def nearest_fault(lat, lon):
    best = None
    for fault in KNOWN_FAULT_LINES:
        dist = distance_to_polyline(lat, lon, fault['coords'])
        if best is None or dist < best['distance_km']:
            best = {'name': fault['name'], 'distance_km': round(dist, 1),
                    'activity': fault['activity'], 'type': fault['type']}
    return best

# ============================================================================
# ELEVATION + SLOPE API — v5.3.1 MULTI-PROVIDER FALLBACK
# ============================================================================

_ELEV_UA = {
    "User-Agent": "Mozilla/5.0 (compatible; UndergroundBase/5.3.1; +https://streamlit.io)",
    "Accept": "application/json",
}

def _fetch_elevations_open_elevation(points: List[tuple]) -> Optional[List[float]]:
    """Provider 1: api.open-elevation.com (single POST, batch points)."""
    try:
        payload = {"locations": [{"latitude": p[0], "longitude": p[1]} for p in points]}
        r = requests.post(
            "https://api.open-elevation.com/api/v1/lookup",
            json=payload, headers=_ELEV_UA, timeout=8,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results")
        if not isinstance(results, list) or len(results) != len(points):
            return None
        elevs = []
        for item in results:
            if not isinstance(item, dict) or "elevation" not in item:
                return None
            elevs.append(float(item["elevation"]))
        return elevs
    except Exception:
        return None


def _fetch_elevations_open_meteo(points: List[tuple]) -> Optional[List[float]]:
    """Provider 2: api.open-meteo.com (batch lat/lon, very reliable, no key)."""
    try:
        lats = ",".join(f"{p[0]:.5f}" for p in points)
        lons = ",".join(f"{p[1]:.5f}" for p in points)
        r = requests.get(
            "https://api.open-meteo.com/v1/elevation",
            params={"latitude": lats, "longitude": lons},
            headers=_ELEV_UA, timeout=8,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        elevs = data.get("elevation")
        if not isinstance(elevs, list) or len(elevs) != len(points):
            return None
        return [float(e) for e in elevs]
    except Exception:
        return None


def _fetch_elevations_opentopodata(points: List[tuple]) -> Optional[List[float]]:
    """Provider 3: api.opentopodata.org (SRTM 30m, one call per point — last resort)."""
    try:
        elevs = []
        for lat, lon in points:
            r = requests.get(
                "https://api.opentopodata.org/v1/srtm30m",
                params={"locations": f"{lat},{lon}"},
                headers=_ELEV_UA, timeout=8,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            results = data.get("results")
            if not isinstance(results, list) or not results:
                return None
            elevs.append(float(results[0]["elevation"]))
        return elevs
    except Exception:
        return None


_ELEV_PROVIDERS = [
    ("Open-Elevation", _fetch_elevations_open_elevation),
    ("Open-Meteo", _fetch_elevations_open_meteo),
    ("OpenTopoData", _fetch_elevations_opentopodata),
]


def _score_elevation(elev_m: float) -> tuple:
    """Turn a raw elevation (m) into (score, label) — same thresholds as v5.1.9."""
    if 100 <= elev_m <= 500:
        return 5.0, 'Optimal underground elevation'
    elif 50 <= elev_m < 100:
        return 4.5, 'Good underground elevation'
    elif 500 < elev_m <= 1000:
        return 4.5, 'High elevation, stable'
    elif 1000 < elev_m <= 2000:
        return 4.5, 'Very high elevation, excellent stability'
    elif elev_m > 2000:
        return 4.0, 'Alpine elevation, access costs high'
    elif 20 <= elev_m < 50:
        return 3.5, 'Moderate elevation'
    elif 0 <= elev_m < 20:
        return 2.0, 'Low elevation, flood risk'
    else:
        return 3.0, 'Sub-surface point'


@st.cache_data(ttl=3600, show_spinner=False)
def _get_elevation_cached(lat: float, lon: float) -> Dict:
    """v5.2.1/v5.3.1: cached site elevation — multi-provider."""
    points = [(lat, lon)]
    for provider_name, fetcher in _ELEV_PROVIDERS:
        for attempt in range(2):
            elevs = fetcher(points)
            if elevs is not None and len(elevs) == 1:
                elev_m = float(elevs[0])
                score, label = _score_elevation(elev_m)
                return {
                    'elev': elev_m,
                    'score': score,
                    'label': f'{provider_name} (Live) - {label}',
                    'source': f'{provider_name} (Live)',
                    'live': True,
                }
            if attempt == 0:
                time.sleep(0.3)
    return {
        'elev': None, 'score': None, 'label': None,
        'source': 'all elevation providers failed', 'live': False,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def _slope_lookup_cached(lat: float, lon: float) -> Dict:
    """v5.1.9/v5.3.1: cached slope lookup — multi-provider."""
    d = 0.005
    points = []
    for dy in (-d, 0, d):
        for dx in (-d, 0, d):
            points.append((lat + dy, lon + dx))

    for provider_name, fetcher in _ELEV_PROVIDERS:
        for attempt in range(2):
            elevs = fetcher(points)
            if elevs is not None:
                grid = np.array(elevs).reshape(3, 3)
                gy = (grid[2, 1] - grid[0, 1]) / (2 * d * 111000)
                gx = (grid[1, 2] - grid[1, 0]) / (2 * d * 111000)
                slope_pct = math.sqrt(gx ** 2 + gy ** 2) * 100
                slope_deg = math.degrees(math.atan(slope_pct / 100))
                if slope_deg < 5:
                    risk = 'Flat (Excellent for construction)'
                    score = 5.0
                elif slope_deg < 15:
                    risk = 'Gentle (Good for construction)'
                    score = 4.5
                elif slope_deg < 25:
                    risk = 'Moderate (Manageable with terracing)'
                    score = 3.5
                elif slope_deg < 40:
                    risk = 'Steep (Requires engineering)'
                    score = 2.5
                else:
                    risk = 'Very Steep (Major engineering challenge)'
                    score = 1.5
                return {
                    'slope_deg': round(slope_deg, 1),
                    'slope_pct': round(slope_pct, 1),
                    'risk': risk,
                    'score': score,
                    'source': f'{provider_name} DEM (Live)',
                }
            if attempt == 0:
                time.sleep(0.4)

    return {
        'slope_deg': 0, 'slope_pct': 0,
        'risk': 'Unknown (all elevation providers failed)',
        'score': 3.0, 'source': 'Fallback: slope unavailable',
    }


def estimate_slope(lat: float, lon: float) -> Dict:
    """v5.3.1: thin wrapper — the real work is cached by st.cache_data."""
    try:
        return _slope_lookup_cached(lat, lon)
    except Exception:
        return _slope_fallback(lat, lon)


def _slope_fallback(lat, lon):
    return {'slope_deg': 0, 'slope_pct': 0, 'risk': 'Unknown (API unavailable)',
            'score': 3.0, 'source': 'Fallback: slope unavailable'}


def _geographic_elevation_fallback(lat: float, lon: float, region: str) -> tuple:
    """Original v5.1.8 heuristic — used ONLY if all 3 providers fail."""
    if region == "borneo":
        if 5.8 < lat < 6.2 and 116.4 < lon < 116.8:
            return (5.0, 1500, 'Fallback: Kinabalu region - excellent underground site')
        elif lat > 4.5 and lon > 117.5:
            return (4.0, 300, 'Fallback: E. Sabah hills - good underground site')
        elif 2.5 < lat and 114.0 < lon < 115.5:
            return (4.5, 200, 'Fallback: Sarawak interior - good underground site')
        elif lat > 5.0 and 115.0 < lon < 117.0:
            return (4.5, 800, 'Fallback: Crocker Range - excellent underground site')
        else:
            return (3.5, 50, 'Fallback: Lowland area')
    else:
        if 3.3 < lat < 4.7 and 101.3 < lon < 101.9:
            return (4.5, 1200, 'Fallback: Titiwangsa highlands - excellent underground site')
        elif lat > 4.5 and 101.5 < lon < 102.5:
            return (3.5, 250, 'Fallback: Kelantan interior - moderate site')
        elif 3.5 < lat < 4.6 and 101.9 < lon < 102.8:
            return (3.5, 300, 'Fallback: Pahang interior - moderate site')
        elif lat < 2.5 and 102.5 < lon < 103.8:
            return (3.0, 80, 'Fallback: Johor interior')
        else:
            return (3.0, 30, 'Fallback: Coastal lowland')

# ============================================================================
# v5.3.0 NEW LIVE PROVIDERS (additive, zero deletions)
# ============================================================================

@st.cache_data(ttl=1800, show_spinner=False)
def _get_seismic_usgs_with_retry(lat: float, lon: float, radius_km: int = 200,
                                  max_retries: int = 3) -> Optional[Dict]:
    """
    v5.3.0 FEATURE 1: USGS with exponential backoff.
    Returns the same dict shape as the original _get_seismic_usgs(),
    so callers don't need to know the difference.
    """
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson", "latitude": lat, "longitude": lon,
        "maxradiuskm": radius_km, "starttime": "1975-01-01",
        "minmagnitude": 3.0, "orderby": "magnitude",
    }
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=_ELEV_UA, timeout=10)
            if r.status_code == 200:
                data = r.json()
                features = data.get('features', [])
                magnitudes = [f['properties']['mag'] for f in features
                              if f['properties'].get('mag') is not None]
                count = len(magnitudes)
                max_mag = max(magnitudes) if magnitudes else 0.0
                return {
                    'count': count, 'max_magnitude': round(max_mag, 2),
                    'source': 'USGS Earthquake API (Live)',
                    'radius_km': radius_km, 'period': '1975-present',
                }
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep((2 ** attempt) * 0.5)
                continue
            return None
        except requests.exceptions.Timeout:
            time.sleep((2 ** attempt) * 0.5)
            continue
        except Exception:
            return None
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def _get_population_osm(lat: float, lon: float, radius_m: int = 5000) -> Optional[Dict]:
    """
    v5.3.0 FEATURE 2: Live OSM building footprint count → population proxy.
    Returns None if OSM has insufficient data (caller falls back to heuristic).
    """
    try:
        url = "https://overpass-api.de/api/interpreter"
        q = f"""
        [out:json][timeout:20];
        (
          way["building"](around:{radius_m},{lat},{lon});
        );
        out count;
        """
        r = requests.post(url, data={'data': q}, headers=_ELEV_UA, timeout=25)
        if r.status_code != 200:
            return None
        data = r.json()
        elements = data.get('elements', [])
        building_count = 0
        for el in elements:
            if el.get('type') == 'count' or 'tags' in el:
                tags = el.get('tags', {})
                if 'total' in tags:
                    try:
                        building_count = int(tags['total'])
                    except (ValueError, TypeError):
                        building_count = 0
                    break
            else:
                building_count += 1

        area_km2 = math.pi * (radius_m / 1000.0) ** 2
        people_per_building = 2.5
        estimated_pop = building_count * people_per_building
        density = estimated_pop / area_km2 if area_km2 > 0 else 0

        if building_count < 5:
            return None

        if density > 5:
            score, label = 2.0, f'Near city (OSM: {density:.1f} ppl/km²)'
        elif density > 2:
            score, label = 3.0, f'Moderate population (OSM: {density:.1f} ppl/km²)'
        elif density > 1:
            score, label = 4.0, f'Low population (OSM: {density:.1f} ppl/km²)'
        elif density > 0.2:
            score, label = 4.5, f'Rural (OSM: {density:.1f} ppl/km²)'
        else:
            score, label = 5.0, f'Remote (OSM: {density:.2f} ppl/km²)'

        return {
            'score': score,
            'density': round(density, 2),
            'label': label,
            'source': f'OSM Overpass (Live) - {building_count} buildings in {radius_m}m',
            'live': True,
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def _get_land_use_osm(lat: float, lon: float, radius_m: int = 5000) -> Optional[Dict]:
    """
    v5.3.0 FEATURE 3: Live OSM landuse counts → land availability proxy.
    Returns None if OSM data too sparse.
    """
    try:
        url = "https://overpass-api.de/api/interpreter"
        q = f"""
        [out:json][timeout:25];
        (
          way["landuse"="forest"](around:{radius_m},{lat},{lon});
          way["landuse"="residential"](around:{radius_m},{lat},{lon});
          way["landuse"="farmland"](around:{radius_m},{lat},{lon});
          way["landuse"="industrial"](around:{radius_m},{lat},{lon});
          way["natural"="wood"](around:{radius_m},{lat},{lon});
        );
        out tags;
        """
        r = requests.post(url, data={'data': q}, headers=_ELEV_UA, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
        elements = data.get('elements', [])

        forest = 0
        residential = 0
        farmland = 0
        industrial = 0

        for el in elements:
            tags = el.get('tags', {})
            lu = tags.get('landuse', '')
            nat = tags.get('natural', '')
            if lu == 'forest' or nat == 'wood':
                forest += 1
            elif lu == 'residential':
                residential += 1
            elif lu == 'farmland':
                farmland += 1
            elif lu == 'industrial':
                industrial += 1

        total_polygons = forest + residential + farmland + industrial
        if total_polygons < 3:
            return None

        if forest > 20 and residential < 5:
            score, label = 5.0, f'Abundant land (OSM: {forest} forest, {residential} residential)'
        elif forest > 10 and residential < 10:
            score, label = 4.5, f'Good land (OSM: {forest} forest, {residential} residential)'
        elif residential > 15:
            score, label = 2.5, f'Developed area (OSM: {residential} residential)'
        else:
            score, label = 3.5, f'Mixed land (OSM: {forest}F/{residential}R/{farmland}A/{industrial}I)'

        return {
            'score': score,
            'forest_areas': forest,
            'developed_areas': residential,
            'agriculture': farmland,
            'industrial': industrial,
            'label': label,
            'source': f'OSM Overpass (Live) - {total_polygons} landuse polygons',
            'live': True,
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def _get_onegeology_with_retry(lat: float, lon: float) -> Optional[Dict]:
    """
    v5.3.0 FEATURE 4: OneGeology with retry + fallback WMS layer.
    """
    wms_url = "https://portal.onegeology.org/OneGeologyGlobal/WMS/1.3.0"
    layers_to_try = ["World_CGMW", "World_CGMW_2023", "World_CGMW_2022"]

    for layer in layers_to_try:
        for attempt in range(2):
            try:
                params = {
                    "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
                    "LAYERS": layer, "QUERY_LAYERS": layer,
                    "INFO_FORMAT": "text/plain", "I": 50, "J": 50,
                    "WIDTH": 101, "HEIGHT": 101, "CRS": "EPSG:4326",
                    "BBOX": f"{lat-0.1},{lon-0.1},{lat+0.1},{lon+0.1}",
                }
                r = requests.get(wms_url, params=params, headers=_ELEV_UA, timeout=10)
                if r.status_code == 200:
                    text = r.text.strip()
                    if text and "Geology" not in text and len(text) < 5000 and len(text) > 5:
                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                        summary = lines[0][:120] if lines else 'Regional geology available'
                        return {
                            'source': f'OneGeology WMS (Live) - layer {layer}',
                            'summary': summary,
                            'raw_length': len(text),
                            'layer_used': layer,
                        }
                if attempt == 0:
                    time.sleep(0.3)
            except Exception:
                if attempt == 0:
                    time.sleep(0.3)
                continue
    return None


def _compute_custom_weights_from_sidebar() -> Dict:
    """v5.3.0 FEATURE 5: read custom weight sliders from sidebar."""
    if not st.session_state.get('custom_weights_enabled', False):
        return {
            'elevation': 0.13, 'bedrock_depth': 0.13, 'water_table_depth': 0.10,
            'seismic_risk': 0.10, 'geology': 0.12, 'population_density': 0.08,
            'coastal_proximity': 0.07, 'infrastructure_access': 0.10,
            'land_availability': 0.05, 'flood_risk': 0.05,
            'slope': 0.04, 'fault_proximity': 0.03,
        }
    return st.session_state.get('custom_weights', {
        'elevation': 0.13, 'bedrock_depth': 0.13, 'water_table_depth': 0.10,
        'seismic_risk': 0.10, 'geology': 0.12, 'population_density': 0.08,
        'coastal_proximity': 0.07, 'infrastructure_access': 0.10,
        'land_availability': 0.05, 'flood_risk': 0.05,
        'slope': 0.04, 'fault_proximity': 0.03,
    })


def _render_sensitivity_analysis(rd: Dict):
    """v5.3.0 FEATURE 6: Sensitivity Analysis expander."""
    with st.expander("🧪 Sensitivity Analysis — what if the guesses are wrong?", expanded=False):
        st.caption("Shows how the score changes if bedrock / water table / geology estimates are off by ±20%")
        base_score = rd.get('suitability_percentage', 0)
        weights = rd.get('_weights_used', {
            'bedrock_depth': 0.13, 'water_table_depth': 0.10, 'geology': 0.12,
        })
        scores = rd.get('scores', {})
        max_possible = sum(weights.values()) * 5.0 if weights else 1.0

        scenarios = []
        scenarios.append({'Scenario': 'Baseline (as computed)', 'Score': base_score, 'Delta': 0.0})

        for key, label in [
            ('bedrock_depth', 'Bedrock ±20%'),
            ('water_table_depth', 'Water Table ±20%'),
            ('geology', 'Geology ±20%'),
        ]:
            current = scores.get(key, 3.0)
            pessimistic = max(1.0, current * 0.8)
            delta_p = (pessimistic - current) * weights.get(key, 0)
            optimistic = min(5.0, current * 1.2)
            delta_o = (optimistic - current) * weights.get(key, 0)

            new_score_p = base_score + (delta_p / max_possible * 100)
            new_score_o = base_score + (delta_o / max_possible * 100)

            scenarios.append({
                'Scenario': f'{label} (worse)',
                'Score': round(max(0, new_score_p), 1),
                'Delta': round(new_score_p - base_score, 1),
            })
            scenarios.append({
                'Scenario': f'{label} (better)',
                'Score': round(min(100, new_score_o), 1),
                'Delta': round(new_score_o - base_score, 1),
            })

        df = pd.DataFrame(scenarios)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"📌 Base score = {base_score}%. The three heuristic inputs (bedrock, water table, geology) contribute "
                   f"{(weights.get('bedrock_depth',0)+weights.get('water_table_depth',0)+weights.get('geology',0))*100:.0f}% "
                   f"of the total weight. If all three are simultaneously wrong by ±20%, the score can shift by up to "
                   f"~{abs(df['Delta']).max():.1f} points.")


def _render_climate_context_tab(site_data: Dict):
    """v5.3.0 FEATURE 7 (bonus): Climate Context tab in enhanced results."""
    st.subheader("🌦️ Climate Context")
    st.caption("Live climate data from Open-Meteo — pure context, does not affect suitability score")

    lat = site_data.get('_lat', None)
    lon = site_data.get('_lon', None)
    if lat is None or lon is None:
        coords = _parse_location_coords(site_data)
        if coords:
            lat, lon = coords

    if lat is None or lon is None:
        st.warning("Could not determine site coordinates for climate lookup.")
        return

    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/climate",
            params={
                "latitude": lat, "longitude": lon,
                "start_date": "2020-01-01", "end_date": "2024-12-31",
                "daily": "temperature_2m_mean,precipitation_sum",
                "timezone": "auto",
            },
            headers=_ELEV_UA, timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            daily = data.get('daily', {})
            temps = [t for t in daily.get('temperature_2m_mean', []) if t is not None]
            precip = [p for p in daily.get('precipitation_sum', []) if p is not None]

            if temps and precip:
                avg_temp = round(sum(temps) / len(temps), 1)
                max_temp = round(max(temps), 1)
                min_temp = round(min(temps), 1)
                annual_precip = round(sum(precip) / 5.0, 0)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Temperature", f"{avg_temp}°C")
                    st.caption(f"Range: {min_temp}°C — {max_temp}°C")
                with col2:
                    st.metric("Annual Rainfall (avg)", f"{annual_precip:.0f} mm")
                    st.caption(f"5-year total: {sum(precip):.0f} mm")
                with col3:
                    rain_days = sum(1 for p in precip if p > 1.0) / 5.0
                    st.metric("Rainy Days / Year", f"{rain_days:.0f}")
                    st.caption("Days with >1mm rainfall")

                st.markdown("---")
                if annual_precip > 2500:
                    st.warning(f"🌧️ **Very high rainfall zone** ({annual_precip:.0f} mm/yr) — "
                               f"expect significant waterproofing and drainage costs for underground construction.")
                elif annual_precip > 1500:
                    st.info(f"🌧️ **Moderate-high rainfall** ({annual_precip:.0f} mm/yr) — "
                            f"standard waterproofing required.")
                else:
                    st.success(f"☀️ **Low rainfall** ({annual_precip:.0f} mm/yr) — "
                               f"waterproofing costs minimal.")

                if avg_temp > 28:
                    st.warning(f"🌡️ **Hot climate** ({avg_temp}°C avg) — "
                               f"underground ventilation will need extra cooling capacity.")
                elif avg_temp < 20:
                    st.info(f"❄️ **Cool climate** ({avg_temp}°C avg) — "
                            f"underground heating may be needed.")
                else:
                    st.success(f"🌡️ **Comfortable climate** ({avg_temp}°C avg) — "
                               f"standard HVAC sufficient.")
                return
        st.info("Open-Meteo climate API did not return data for this site. This is normal for some locations.")
    except Exception as e:
        st.info(f"Climate context unavailable: {e}")


def _render_custom_weights_sidebar():
    """v5.3.0 FEATURE 5: Custom Weights expander in sidebar."""
    with st.expander("⚙️ Custom Weights (Advanced)", expanded=False):
        st.caption("Default values match v5.2.1. Only change if you know what you're doing.")
        enabled = st.checkbox("Enable custom weights", value=False, key="custom_weights_enabled")

        defaults = {
            'elevation': 0.13, 'bedrock_depth': 0.13, 'water_table_depth': 0.10,
            'seismic_risk': 0.10, 'geology': 0.12, 'population_density': 0.08,
            'coastal_proximity': 0.07, 'infrastructure_access': 0.10,
            'land_availability': 0.05, 'flood_risk': 0.05,
            'slope': 0.04, 'fault_proximity': 0.03,
        }
        labels = {
            'elevation': 'Elevation', 'bedrock_depth': 'Bedrock',
            'water_table_depth': 'Water Table', 'seismic_risk': 'Seismic',
            'geology': 'Geology', 'population_density': 'Population',
            'coastal_proximity': 'Coastal', 'infrastructure_access': 'Infra',
            'land_availability': 'Land', 'flood_risk': 'Flood',
            'slope': 'Slope', 'fault_proximity': 'Fault',
        }

        new_weights = {}
        for key, default in defaults.items():
            new_weights[key] = st.slider(
                labels[key], 0.0, 0.30, default, 0.01,
                key=f"w_{key}",
                disabled=not enabled,
            )

        total = sum(new_weights.values())
        if total > 0:
            normalized = {k: v / total for k, v in new_weights.items()}
        else:
            normalized = defaults

        st.caption(f"Sum = {total:.2f} → normalized automatically")
        st.session_state['custom_weights'] = normalized


# ============================================================================
# 🆕 v5.3.1 UNIVERSAL SEARCH — location name OR coordinates (SIDEBAR)
# ============================================================================

def _parse_search_coordinates(text: str) -> Optional[tuple]:
    """
    Try to parse the search text as coordinates. Accepts:
      "4.22, 114.03"       "4.22 114.03"
      "4.22N, 114.03E"     "4.22 S 114.03 W"
      "4.22;114.03"        "(4.22, 114.03)"
      "4.22E, 114.03N"     (order-insensitive)
    Returns (lat, lon) or None if not coordinates.
    """
    if not text or not text.strip():
        return None
    s = text.strip().upper()
    for ch in "()[]{}\"',;":
        s = s.replace(ch, " ")
    s = " ".join(s.split())

    parts = s.split()
    if len(parts) == 2:
        try:
            a, b = float(parts[0]), float(parts[1])
            if -90 <= a <= 90 and -180 <= b <= 180:
                return (a, b)
            if -180 <= a <= 180 and -90 <= b <= 90:
                return (b, a)
        except ValueError:
            pass

    import re
    pattern = r"([-+]?\d+(?:\.\d+)?)\s*([NSEW])"
    matches = re.findall(pattern, s)
    if len(matches) == 2:
        try:
            val1, dir1 = matches[0]
            val2, dir2 = matches[1]
            v1 = float(val1)
            v2 = float(val2)
            if dir1 in ("N", "S"):
                lat = v1 if dir1 == "N" else -v1
                lon = v2 if dir2 == "E" else (-v2 if dir2 == "W" else None)
                if lon is not None:
                    return (lat, lon)
            else:
                lon = v1 if dir1 == "E" else (-v1 if dir1 == "W" else None)
                lat = v2 if dir2 == "N" else (-v2 if dir2 == "S" else None)
                if lat is not None and lon is not None:
                    return (lat, lon)
        except ValueError:
            pass

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def _geocode_location(address: str) -> Optional[Dict]:
    """Uses OpenStreetMap Nominatim API to find ANY location in Malaysia."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": "my", # Restrict to Malaysia
            "addressdetails": 1
        }
        headers = {"User-Agent": "UndergroundBaseApp/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                res = data[0]
                return {
                    "name": res.get("display_name", address),
                    "lat": float(res["lat"]),
                    "lon": float(res["lon"]),
                    "region": "west_malaysia" if float(res["lon"]) < 109.0 else "borneo"
                }
    except Exception:
        pass
    return None


def _search_locations(query: str, region: str, max_results: int = 8) -> List[Dict]:
    """
    Fuzzy-search all locations (Sabah + Sarawak + West Malaysia).
    Returns list of dicts with 'name', 'lat', 'lon', 'score', 'region'.
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    pool = []
    for name, coords in SABAH_LOCATIONS.items():
        pool.append({'name': name, 'lat': coords[0], 'lon': coords[1], 'region': 'borneo'})
    for name, coords in SARAWAK_LOCATIONS.items():
        pool.append({'name': name, 'lat': coords[0], 'lon': coords[1], 'region': 'borneo'})
    for name, coords in WEST_MALAYSIA_LOCATIONS.items():
        pool.append({'name': name, 'lat': coords[0], 'lon': coords[1], 'region': 'west_malaysia'})

    results = []
    for item in pool:
        name_lower = item['name'].lower()
        if name_lower.startswith(query_lower):
            score = 100 - len(name_lower) * 0.01
        elif query_lower in name_lower:
            score = 50 - len(name_lower) * 0.01
        else:
            q_tokens = set(query_lower.split())
            n_tokens = set(name_lower.replace(',', ' ').replace('(', ' ').replace(')', ' ').split())
            overlap = len(q_tokens & n_tokens)
            if overlap == 0:
                continue
            score = 10 * overlap - len(name_lower) * 0.01
        results.append({**item, 'score': score})

    results.sort(key=lambda x: -x['score'])
    return results[:max_results]


def render_universal_search_sidebar():
    """
    v5.3.1: Universal search bar in the sidebar.
    Sits at the very top, above LOCATION SELECTOR.
    Accepts place names OR coordinates.
    Writes to st.session_state.selected_location on submit.
    """
    st.markdown("""
    <div style="padding: 8px 0 4px 0;">
        <div style="color: #00f0ff; font-family: 'Courier New', monospace; 
             letter-spacing: 2px; font-size: 0.9rem; font-weight: bold;">
            🆕 UNIVERSAL SEARCH</div>
        <div style="color: #8080a0; font-family: 'Courier New', monospace; 
             font-size: 0.65rem; letter-spacing: 1px; margin-top: 2px;">
            Type a name OR paste coordinates</div>
    </div>
    """, unsafe_allow_html=True)

    query = st.text_input(
        "Search",
        placeholder="e.g. Miri  OR  4.22, 114.03",
        label_visibility="collapsed",
        key="universal_search_input",
    )

    if st.button("🔍 SEARCH", use_container_width=True, type="primary", key="universal_search_btn"):
        if not query or not query.strip():
            st.warning("Type a location name or coordinates.")
            return

        query = query.strip()

        # ── Try coordinates first ─────────────────────────────────
        coords = _parse_search_coordinates(query)
        if coords is not None:
            lat, lon = coords
            if 0.5 <= lat <= 7.5 and 109.0 <= lon <= 119.5:
                new_region = 'borneo'
            elif 0.5 <= lat <= 7.5 and 99.0 <= lon <= 105.0:
                new_region = 'west_malaysia'
            else:
                new_region = st.session_state.get('region', 'borneo')
            st.session_state.selected_location = Location(
                lat=lat, lon=lon,
                name=f"Custom coordinates ({lat:.4f}, {lon:.4f})"
            )
            st.session_state.region = new_region
            st.session_state.current_results = None
            st.session_state.nearby_alternatives_cache = None
            st.success(f"📍 {lat:.4f}, {lon:.4f}")
            time.sleep(0.2)
            st.rerun()

        # ── 1. Try Fuzzy search in local database first ───────────
        matches = _search_locations(query, st.session_state.get('region', 'borneo'), max_results=8)

        # ── 2. If no local match, use OpenStreetMap Geocoding ─────
        if not matches:
            with st.spinner("Searching map database..."):
                geo_result = _geocode_location(query)
                
            if geo_result:
                st.session_state.selected_location = Location(
                    lat=geo_result['lat'], lon=geo_result['lon'], name=geo_result['name']
                )
                st.session_state.region = geo_result['region']
                st.session_state.current_results = None
                st.session_state.nearby_alternatives_cache = None
                st.success(f"📍 Found: {geo_result['name'][:40]}...")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning(f"Could not find '{query}'. Try adding 'Malaysia' or a state name (e.g., 'Ampang, Selangor').")
                return

        if len(matches) == 1 or matches[0]['score'] > 90:
            best = matches[0]
            st.session_state.selected_location = Location(
                lat=best['lat'], lon=best['lon'], name=best['name']
            )
            st.session_state.region = best['region']
            st.session_state.current_results = None
            st.session_state.nearby_alternatives_cache = None
            st.success(f"📍 {best['name']}")
            time.sleep(0.2)
            st.rerun()

        # Multiple matches — show picker
        st.markdown(f"**{len(matches)} matches — pick one:**")
        options = [f"{m['name']}  ·  ({m['lat']:.3f}, {m['lon']:.3f})" for m in matches]
        chosen = st.selectbox(
            "Pick",
            options=options,
            key="universal_search_picker",
            label_visibility="collapsed",
        )
        if st.button("🎯 GO", use_container_width=True, key="universal_search_go"):
            idx = options.index(chosen)
            best = matches[idx]
            st.session_state.selected_location = Location(
                lat=best['lat'], lon=best['lon'], name=best['name']
            )
            st.session_state.region = best['region']
            st.session_state.current_results = None
            st.session_state.nearby_alternatives_cache = None
            st.success(f"📍 {best['name']}")
            time.sleep(0.2)
            st.rerun()

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)


# ============================================================================
# END v5.3.1
# ============================================================================

def estimate_groundwater_quality(lat, lon, region):
    if region == 'borneo':
        if lat > 5.5 and 116 < lon < 117:
            return {'type': 'Freshwater fractured aquifer', 'salinity': 'Low (<500 mg/L)',
                    'score': 4.5, 'note': 'Mountainous interior — excellent quality'}
        elif 3 < lat < 5 and 114 < lon < 115.5:
            return {'type': 'Freshwater karst aquifer', 'salinity': 'Low (<500 mg/L)',
                    'score': 4.5, 'note': 'Mulu/Bario highlands — good quality'}
        elif lat < 3 or lon > 117.5:
            return {'type': 'Coastal aquifer', 'salinity': 'Moderate (500-1500 mg/L)',
                    'score': 3.0, 'note': 'Near coast — check saline intrusion'}
        return {'type': 'Mixed sedimentary', 'salinity': 'Low-Moderate',
                'score': 4.0, 'note': 'Regional classification'}
    else:
        if 3.3 < lat < 4.7 and 101.3 < lon < 101.9:
            return {'type': 'Fractured granite aquifer', 'salinity': 'Low (<300 mg/L)',
                    'score': 5.0, 'note': 'Titiwangsa highlands — pristine'}
        elif 4.5 < lat < 5.5 and 100.9 < lon < 101.5:
            return {'type': 'Limestone karst aquifer', 'salinity': 'Low-Moderate',
                    'score': 4.0, 'note': 'Perak — good but variable flow'}
        elif lat < 2.5:
            return {'type': 'Coastal alluvial', 'salinity': 'Moderate-High (risk)',
                    'score': 2.5, 'note': 'Johor south — saline intrusion risk'}
        return {'type': 'Mixed aquifer', 'salinity': 'Low-Moderate',
                'score': 3.5, 'note': 'Regional classification'}

def check_protected_area(lat, lon):
    karst = get_known_karst_geology(lat, lon)
    if karst and karst.get('protected_area'):
        return {
            'inside': True,
            'name': karst['protection_name'],
            'severity': 'HIGH',
            'message': f"⚠️ Site is inside or overlaps: {karst['protection_name']}. "
                       f"Development likely requires environmental impact assessment and "
                       f"may be legally restricted."
        }
    for (la_min, la_max, lo_min, lo_max), data in KNOWN_KARST_REGIONS.items():
        if data.get('protected_area'):
            center_lat = (la_min + la_max) / 2
            center_lon = (lo_min + lo_max) / 2
            if _haversine(lat, lon, center_lat, center_lon) < 10:
                return {
                    'inside': False,
                    'near': True,
                    'name': data['protection_name'],
                    'severity': 'MEDIUM',
                    'message': f"⚠️ Within 10km of {data['protection_name']}. "
                               f"Consult environmental authority before planning."
                }
    return {'inside': False, 'near': False, 'severity': 'LOW',
            'message': '✅ No protected area overlap detected (within our dataset).'}

@dataclass
class Location:
    lat: float
    lon: float
    name: str = ""
    properties: Dict = field(default_factory=dict)

@dataclass
class AnalysisStep:
    step_number: int
    name: str
    description: str
    status: str = "pending"
    result: Any = None
    execution_time: float = 0.0
    reasoning: str = ""

@dataclass
class AnalysisResult:
    query: str
    steps: List[AnalysisStep] = field(default_factory=list)
    final_result: Any = None
    total_time: float = 0.0
    timestamp: str = ""
    success: bool = False

@dataclass
class MemoryEntry:
    query: str
    query_embedding: List[float] = field(default_factory=list)
    result_summary: str = ""
    success: bool = False
    execution_time: float = 0.0
    timestamp: str = ""
    parameters_used: Dict = field(default_factory=dict)

class MemoryRepository:
    def __init__(self, db_path: str = "malaysia_underground_city_memory.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL, query_hash TEXT NOT NULL,
                result_summary TEXT, success INTEGER, execution_time REAL,
                parameters TEXT, timestamp TEXT, embedding BLOB
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL, parameter_name TEXT NOT NULL,
                optimal_value TEXT, success_rate REAL,
                usage_count INTEGER DEFAULT 1, last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()

    def store_analysis(self, entry: MemoryEntry):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query_hash = hashlib.md5(entry.query.lower().encode()).hexdigest()
        cursor.execute("""
            INSERT INTO analysis_memory
            (query, query_hash, result_summary, success, execution_time, parameters, timestamp, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry.query, query_hash, entry.result_summary,
              1 if entry.success else 0, entry.execution_time,
              json.dumps(entry.parameters_used), entry.timestamp,
              pickle.dumps(entry.query_embedding)))
        conn.commit()
        conn.close()

    def get_all_analyses(self, limit: int = 20) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_memory ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        results = [{
            'query': row[1], 'result_summary': row[3],
            'success': bool(row[4]), 'execution_time': row[5],
            'parameters': json.loads(row[6]) if row[6] else {},
            'timestamp': row[7]
        } for row in rows]
        conn.close()
        return results

    def find_similar_analyses(self, query: str, limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_memory ORDER BY timestamp DESC LIMIT 100")
        rows = cursor.fetchall()
        if not query or not query.strip():
            conn.close(); return []
        keywords = query.lower().split()
        results = []
        for row in rows:
            stored_query = row[1].lower()
            match_score = sum(1 for kw in keywords if kw in stored_query)
            if match_score > 0:
                results.append({
                    'query': row[1], 'result_summary': row[3],
                    'success': bool(row[4]), 'execution_time': row[5],
                    'parameters': json.loads(row[6]) if row[6] else {},
                    'timestamp': row[7], 'match_score': match_score
                })
        conn.close()
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:limit]

    def get_learned_parameter(self, analysis_type: str, parameter_name: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT optimal_value FROM learned_parameters
            WHERE analysis_type = ? AND parameter_name = ?
            ORDER BY success_rate DESC LIMIT 1
        """, (analysis_type, parameter_name))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def update_learned_parameter(self, analysis_type: str, parameter_name: str,
                                  value: str, success: bool):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, success_rate, usage_count FROM learned_parameters
            WHERE analysis_type = ? AND parameter_name = ? AND optimal_value = ?
        """, (analysis_type, parameter_name, value))
        row = cursor.fetchone()
        if row:
            new_count = row[2] + 1
            new_rate = ((row[1] * row[2]) + (1 if success else 0)) / new_count
            cursor.execute("""
                UPDATE learned_parameters
                SET success_rate = ?, usage_count = ?, last_updated = ?
                WHERE id = ?
            """, (new_rate, new_count, datetime.now().isoformat(), row[0]))
        else:
            cursor.execute("""
                INSERT INTO learned_parameters
                (analysis_type, parameter_name, optimal_value, success_rate, usage_count, last_updated)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (analysis_type, parameter_name, value,
                  1.0 if success else 0.0, datetime.now().isoformat()))
        conn.commit(); conn.close()

    def get_analysis_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM analysis_memory")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM analysis_memory WHERE success = 1")
        successful = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(execution_time) FROM analysis_memory")
        avg_time = cursor.fetchone()[0] or 0
        conn.close()
        return {
            'total_analyses': total, 'successful_analyses': successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_execution_time': avg_time
        }

# ============================================================================
# ANALYSIS STRATEGY
# ============================================================================

class AnalysisStrategy(ABC):
    @abstractmethod
    def analyse(self, location: Location, params: Dict) -> Dict: pass
    @abstractmethod
    def get_name(self) -> str: pass


class UndergroundCitySuitabilityStrategy(AnalysisStrategy):
    def __init__(self, region: str = "borneo"):
        self.region = region

    def get_name(self) -> str:
        return f"Underground City Suitability Analysis ({self.region.upper()} + USGS + OneGeology)"

    def _get_elevation_quick(self, location: Location) -> tuple:
        cached = _get_elevation_cached(location.lat, location.lon)
        if cached.get('live') and cached.get('elev') is not None:
            return (cached['score'], cached['elev'], cached['label'])
        return _geographic_elevation_fallback(location.lat, location.lon, self.region)

    def _estimate_bedrock_depth(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        if self.region == "borneo":
            if 5.8 < lat < 6.2 and 116.4 < lon < 116.8:
                return 5.0, 5, 'Geographic: Kinabalu region - shallow bedrock'
            elif lat > 5.5 and 116.0 < lon < 117.5:
                return 4.5, 15, 'Geographic: Interior highlands - shallow bedrock'
            elif lat > 4.5 and lon > 117.5:
                return 4.0, 25, 'Geographic: E. Sabah hills - moderate bedrock'
            elif lat > 2.5 and 114.0 < lon < 115.5:
                return 4.5, 20, 'Geographic: Sarawak interior - good bedrock'
            elif lat > 5.0 and 115.0 < lon < 117.0:
                return 5.0, 10, 'Geographic: Crocker Range - shallow bedrock'
            else:
                return 3.0, 50, 'Geographic: Lowland area - deeper bedrock'
        else:
            if 3.3 < lat < 4.7 and 101.3 < lon < 101.9:
                return 5.0, 8, 'Geographic: Titiwangsa Range - shallow bedrock'
            elif 5.5 < lat < 6.5 and 100.3 < lon < 101.0:
                return 4.5, 15, 'Geographic: Kedah interior - shallow bedrock'
            elif 4.5 < lat < 5.5 and 100.9 < lon < 101.5:
                return 4.5, 12, 'Geographic: Perak interior - limestone geology'
            elif 4.5 < lat < 6.0 and 101.5 < lon < 102.5:
                return 4.5, 20, 'Geographic: Kelantan/Pahang highlands - good bedrock'
            elif 3.5 < lat < 4.5 and 101.9 < lon < 103.0:
                return 4.0, 25, 'Geographic: Pahang interior - moderate bedrock'
            elif lat < 2.5 and 102.5 < lon < 104.0:
                return 4.0, 30, 'Geographic: Johor interior - moderate bedrock'
            else:
                return 3.0, 50, 'Geographic: Coastal lowland - deeper bedrock'

    def _estimate_water_table(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        if self.region == "borneo":
            if 5.8 < lat < 6.2 and 116.4 < lon < 116.8:
                return 5.0, 50, 'Geographic: Kinabalu region - GOOD water table (50m)'
            elif lat > 5.5 and 116.0 < lon < 117.5:
                return 4.5, 40, 'Geographic: Interior highlands - GOOD water table (40m)'
            elif lat > 4.5 and lon > 117.5:
                return 4.0, 30, 'Geographic: E. Sabah hills - GOOD water table (30m)'
            elif lat > 2.5 and 114.0 < lon < 115.5:
                return 4.5, 35, 'Geographic: Sarawak interior - GOOD water table (35m)'
            elif lat > 5.0 and 115.0 < lon < 117.0:
                return 5.0, 45, 'Geographic: Crocker Range - GOOD water table (45m)'
            else:
                return 2.5, 10, 'Geographic: Lowland area - SHALLOW water table (10m)'
        else:
            if 3.3 < lat < 4.7 and 101.3 < lon < 101.9:
                return 5.0, 60, 'Geographic: Titiwangsa highlands - DEEP water table (60m)'
            elif 5.5 < lat < 6.5 and 100.3 < lon < 101.0:
                return 4.5, 45, 'Geographic: Kedah interior - GOOD water table (45m)'
            elif 4.5 < lat < 5.5 and 100.9 < lon < 101.5:
                return 4.5, 50, 'Geographic: Perak interior - GOOD water table (50m)'
            elif 4.5 < lat < 6.0 and 101.5 < lon < 102.5:
                return 4.5, 50, 'Geographic: Kelantan/Pahang highlands - GOOD water table (50m)'
            elif 3.5 < lat < 4.5 and 101.9 < lon < 103.0:
                return 4.0, 40, 'Geographic: Pahang interior - GOOD water table (40m)'
            elif lat < 2.5 and 102.5 < lon < 104.0:
                return 4.0, 40, 'Geographic: Johor interior - GOOD water table (40m)'
            else:
                return 2.5, 10, 'Geographic: Coastal lowland - SHALLOW water table (10m)'

    def _get_seismic_usgs(self, location: Location) -> Optional[Dict]:
        try:
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                "format": "geojson", "latitude": location.lat, "longitude": location.lon,
                "maxradiuskm": 200, "starttime": "1975-01-01",
                "minmagnitude": 3.0, "orderby": "magnitude",
            }
            r = requests.get(url, params=params, timeout=8)
            data = r.json()
            features = data.get('features', [])
            magnitudes = [f['properties']['mag'] for f in features if f['properties'].get('mag') is not None]
            count = len(magnitudes)
            max_mag = max(magnitudes) if magnitudes else 0.0
            return {
                'count': count, 'max_magnitude': round(max_mag, 2),
                'source': 'USGS Earthquake API (Live)',
                'radius_km': 200, 'period': '1975-present',
            }
        except Exception:
            return None

    def _estimate_seismic_risk(self, location: Location) -> tuple:
        if st.session_state.get('use_osm_live', True):
            usgs = _get_seismic_usgs_with_retry(location.lat, location.lon)
        else:
            usgs = self._get_seismic_usgs(location)
        fault = nearest_fault(location.lat, location.lon)
        fault_activity = fault.get('activity', 'Low')
        fault_dist = fault.get('distance_km', 999)

        if usgs is not None:
            count = usgs['count']
            max_mag = usgs['max_magnitude']
            if count == 0:
                score, risk = 5.0, 'Low'
                note = 'USGS: No M3.0+ earthquakes within 200km (1975-present) — score 5.0/5'
            elif count <= 5 and max_mag < 4.0:
                score, risk = 4.5, 'Low'
                note = f"USGS: {count} minor events, max M{max_mag} — score 4.5/5"
            elif count <= 20 and max_mag < 4.5:
                score, risk = 4.0, 'Low'
                note = f"USGS: {count} events, max M{max_mag} — score 4.0/5"
            elif count <= 50 and max_mag < 5.0:
                score, risk = 3.5, 'Low-Moderate'
                note = f"USGS: {count} events, max M{max_mag} — score 3.5/5"
            elif count <= 100:
                score, risk = 3.0, 'Moderate'
                note = f"USGS: {count} events, max M{max_mag} — score 3.0/5 (moderate zone)"
            elif count <= 300 and max_mag < 6.0:
                score, risk = 2.5, 'High'
                note = f"USGS: {count} events, max M{max_mag} — score 2.5/5 (active)"
            else:
                score, risk = 2.0, 'High'
                note = f"USGS: {count} events, max M{max_mag} — score 2.0/5 (very active zone)"

            if fault_dist > 100 and fault_activity == 'Low-Moderate' and max_mag < 5.0 and score < 3.5:
                score = 3.5
                risk = 'Low-Moderate'
                note += f" [adjusted for fault {fault_dist:.0f}km away, Low-Moderate]"
            elif fault_dist < 30 and fault_activity in ('Moderate', 'High') and score > 4.0:
                score = 4.0
                note += f" [capped for nearby fault {fault_dist:.0f}km, {fault_activity}]"

            risk_emoji = {'Low': '🟢', 'Low-Moderate': '🟡', 'Moderate': '🟡', 'High': '🔴'}.get(risk, '⚪')
            return score, risk, note, risk_emoji
        else:
            lat, lon = location.lat, location.lon
            if self.region == "borneo":
                if lat > 6.5 and 116.5 < lon < 118.0:
                    return 4.5, 'Low', 'Geographic fallback: Northern Sabah — score 4.5/5', '🟢'
                elif 4.0 < lat < 5.5 and 118.0 < lon < 119.0:
                    return 4.0, 'Low', 'Geographic fallback: Eastern Sabah — score 4.0/5', '🟢'
                elif lat > 3.0 and 113.0 < lon < 115.0:
                    return 4.5, 'Low', 'Geographic fallback: Sarawak — score 4.5/5', '🟢'
                elif lat > 5.0 and 116.0 < lon < 117.5:
                    return 4.0, 'Low', 'Geographic fallback: Crocker Range — score 4.0/5', '🟢'
                else:
                    return 4.5, 'Low', 'Geographic fallback: Borneo region — score 4.5/5', '🟢'
            else:
                if lat > 5.5 and lon < 100.5:
                    return 4.5, 'Low', 'Geographic fallback: Northern West Malaysia — score 4.5/5', '🟢'
                elif lat > 3.5 and lon > 103.0:
                    return 4.0, 'Low', 'Geographic fallback: East Coast — score 4.0/5', '🟢'
                elif lat < 2.5 and lon < 103.0:
                    return 4.0, 'Moderate', 'Geographic fallback: Southern (near Sumatra fault) — score 4.0/5', '🟡'
                else:
                    return 4.5, 'Low', 'Geographic fallback: Peninsular Malaysia — score 4.5/5', '🟢'

    def _get_onegeology_summary(self, location: Location) -> Optional[Dict]:
        if st.session_state.get('use_osm_live', True):
            return _get_onegeology_with_retry(location.lat, location.lon)
        try:
            wms_url = "https://portal.onegeology.org/OneGeologyGlobal/WMS/1.3.0"
            params = {
                "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
                "LAYERS": "World_CGMW", "QUERY_LAYERS": "World_CGMW",
                "INFO_FORMAT": "text/plain", "I": 50, "J": 50,
                "WIDTH": 101, "HEIGHT": 101, "CRS": "EPSG:4326",
                "BBOX": f"{location.lat-0.1},{location.lon-0.1},{location.lat+0.1},{location.lon+0.1}",
            }
            r = requests.get(wms_url, params=params, timeout=8)
            if r.status_code != 200:
                return None
            text = r.text.strip()
            if text and "Geology" not in text and len(text) < 5000:
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                summary = lines[0][:120] if lines else 'Regional geology available'
                return {'source': 'OneGeology WMS (Live)', 'summary': summary, 'raw_length': len(text)}
            return None
        except Exception:
            return None

    def _geographic_score_coastal(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        if self.region == "borneo":
            if lon > 117.5: return 3.5, 5, 'Geographic: East coast (~5km) - good for access'
            elif lon > 116.5: return 3.0, 15, 'Geographic: Near coast (~15km) - balanced'
            elif lon > 115.5: return 3.5, 25, 'Geographic: Coastal (~25km) - good for supply'
            elif lon > 114.5: return 4.0, 35, 'Geographic: Inland (~35km) - safer from sea-level rise'
            else: return 4.5, 50, 'Geographic: Interior (~50km) - maximum protection'
        else:
            if lon > 103.0: return 3.5, 5, 'Geographic: East coast (~5km) - good for access'
            elif lon > 102.5: return 3.0, 15, 'Geographic: Near east coast (~15km) - balanced'
            elif lon > 101.5: return 4.0, 40, 'Geographic: Central inland (~40km) - safer from sea-level rise'
            elif lon > 100.5: return 3.5, 25, 'Geographic: Near west coast (~25km) - balanced'
            else: return 3.0, 10, 'Geographic: West coast (~10km, Strait of Malacca)'

    def _geographic_score_population(self, location: Location) -> tuple:
        if st.session_state.get('use_osm_live', True):
            osm_pop = _get_population_osm(location.lat, location.lon)
            if osm_pop is not None:
                return osm_pop['score'], osm_pop['density'], osm_pop['source']
        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, data in STATIC_SETTLEMENTS.items():
            s_lat, s_lon = data['coords']
            dist = _haversine(lat, lon, s_lat, s_lon)
            min_dist = min(min_dist, dist)
        if self.region == "borneo":
            if min_dist > 80: return 5.0, 0, 'Geographic: Remote - ideal for underground city'
            elif min_dist > 50: return 4.5, 1, 'Geographic: Rural - good isolation'
            elif min_dist > 30: return 4.0, 2, 'Geographic: Semi-rural - balanced'
            elif min_dist > 15: return 3.0, 5, 'Geographic: Near town - accessible'
            else: return 2.0, 10, 'Geographic: Near city - land expensive'
        else:
            if min_dist > 50: return 5.0, 0, 'Geographic: Remote - ideal for underground city'
            elif min_dist > 30: return 4.5, 1, 'Geographic: Rural - good isolation'
            elif min_dist > 20: return 4.0, 2, 'Geographic: Semi-rural - balanced'
            elif min_dist > 10: return 3.0, 5, 'Geographic: Near town - accessible'
            else: return 2.0, 10, 'Geographic: Near city - land expensive'

    def _geographic_score_infrastructure(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        min_dist = None
        min_name = None
        for name, coords in STATIC_AIRPORTS.items():
            d = _haversine(lat, lon, coords[0], coords[1])
            if d < _AIRPORT_MIN_QUERY_DIST_KM:
                continue
            if min_dist is None or d < min_dist:
                min_dist = d
                min_name = name
        details = {
            'airports': 1 if (min_dist is not None and min_dist < 60) else 0,
            'major_roads': 2 if (min_dist is not None and min_dist < 30) else 0,
            'ports': 0, 'power_facilities': 0
        }
        if min_dist is None:
            base = 2.5
            dist_label = "unknown (no airports in dataset)"
        elif min_dist < 30:
            base = 4.5
            dist_label = f"{min_dist:.0f}km"
        elif min_dist < 60:
            base = 4.0
            dist_label = f"{min_dist:.0f}km"
        elif min_dist < 100:
            base = 3.0
            dist_label = f"{min_dist:.0f}km"
        else:
            base = 2.5
            dist_label = f"{min_dist:.0f}km"
        if details['ports'] == 0:
            base -= 1.0
        if details['power_facilities'] == 0:
            base -= 0.5
        base = max(0.5, base)
        if min_name:
            source = f"Geographic: Nearest airport {dist_label} ({min_name})"
        else:
            source = f"Geographic: Nearest airport {dist_label}"
        if details['ports'] == 0:
            source += " (no port)"
        if details['power_facilities'] == 0:
            source += " (no power)"
        return round(base, 2), details, source

    def _geographic_score_land(self, location: Location) -> tuple:
        if st.session_state.get('use_osm_live', True):
            osm_land = _get_land_use_osm(location.lat, location.lon)
            if osm_land is not None:
                details = {
                    'forest_areas': osm_land['forest_areas'],
                    'developed_areas': osm_land['developed_areas'],
                    'agriculture': osm_land['agriculture'],
                }
                return osm_land['score'], details, osm_land['source']
        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, data in STATIC_SETTLEMENTS.items():
            d = _haversine(lat, lon, data['coords'][0], data['coords'][1])
            min_dist = min(min_dist, d)
        details = {
            'forest_areas': 30 if min_dist > 50 else 10,
            'developed_areas': 2 if min_dist > 50 else 10,
            'agriculture': 5
        }
        if self.region == "borneo":
            if min_dist > 80: return 5.0, details, 'Geographic: Abundant land - perfect'
            elif min_dist > 50: return 4.5, details, 'Geographic: Good land - suitable'
            elif min_dist > 30: return 4.0, details, 'Geographic: Moderate land - enough space'
            elif min_dist > 15: return 3.0, details, 'Geographic: Limited land - constrained'
            else: return 2.0, details, 'Geographic: Scarce land - difficult'
        else:
            if min_dist > 50: return 5.0, details, 'Geographic: Abundant land - perfect'
            elif min_dist > 30: return 4.5, details, 'Geographic: Good land - suitable'
            elif min_dist > 20: return 4.0, details, 'Geographic: Moderate land - enough space'
            elif min_dist > 10: return 3.0, details, 'Geographic: Limited land - constrained'
            else: return 2.0, details, 'Geographic: Scarce land - difficult'

    def _geographic_score_flood(self, elevation_m: float) -> tuple:
        if elevation_m > 200: return 5.0, 'Low'
        elif elevation_m > 100: return 4.5, 'Low'
        elif elevation_m > 50: return 4.0, 'Low'
        elif elevation_m > 20: return 3.0, 'Moderate'
        else: return 1.5, 'High'

    def _geographic_score_geology(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        karst = get_known_karst_geology(lat, lon)
        if karst:
            return karst['underground_score'], f"🗿 {karst['name']} ({karst['type']}) - {karst['details']}", karst
        if self.region == "borneo":
            if 3.5 < lat < 4.5 and 114.5 < lon < 115.5:
                return 5.0, 'Geographic: Mulu region - excellent karst geology', None
            elif 5.5 < lat < 6.5 and 116.0 < lon < 117.0:
                return 4.5, 'Geographic: Kinabalu region - good granite geology', None
            elif 4.0 < lat < 5.5 and 117.0 < lon < 118.5:
                return 4.0, 'Geographic: Eastern Sabah - mixed geology', None
            elif 1.0 < lat < 3.0 and 110.0 < lon < 112.0:
                return 4.0, 'Geographic: Southern Sarawak - sedimentary rocks', None
            else:
                return 3.5, 'Geographic: Borneo - variable geology', None
        else:
            if 3.3 < lat < 4.7 and 101.3 < lon < 101.9:
                return 5.0, 'Geographic: Titiwangsa Range - excellent granite geology', None
            elif 4.5 < lat < 5.5 and 100.9 < lon < 101.5:
                return 4.5, 'Geographic: Perak limestone - karst geology', None
            elif 4.5 < lat < 6.0 and 101.5 < lon < 102.5:
                return 4.5, 'Geographic: Kelantan limestone - karst caves', None
            elif 3.5 < lat < 4.5 and 101.9 < lon < 103.0:
                return 4.0, 'Geographic: Pahang interior - mixed geology', None
            elif 5.5 < lat < 6.5 and 100.3 < lon < 101.0:
                return 4.0, 'Geographic: Kedah interior - sedimentary rocks', None
            else:
                return 3.5, 'Geographic: Peninsular Malaysia - variable geology', None

    def _try_osm_in_background(self, location: Location, radius: int) -> Optional[Dict]:
        try:
            url = "https://overpass-api.de/api/interpreter"
            results = {}
            q = f'[out:json][timeout:5];(node["aeroway"="aerodrome"](around:{radius},{location.lat},{location.lon});way["aeroway"="aerodrome"](around:{radius},{location.lat},{location.lon}););out count;'
            results['airport_count'] = len(requests.post(url, data={'data': q}, timeout=5).json().get('elements', []))
            return results
        except Exception:
            return None

    def _compute_data_confidence(self, live_sources: Dict[str, bool]) -> Dict:
        weights = {
            'elevation': 0.20, 'bedrock': 0.15, 'water_table': 0.10,
            'seismic': 0.20, 'geology': 0.15, 'onegeology': 0.10,
            'slope': 0.05, 'fault': 0.05,
        }
        live_count = 0
        total = 0.0
        for key, w in weights.items():
            total += w
            if live_sources.get(key):
                live_count += w
        confidence_pct = round((live_count / total) * 100, 1) if total > 0 else 0
        if confidence_pct >= 80:
            band = 'High'
        elif confidence_pct >= 55:
            band = 'Moderate'
        else:
            band = 'Low'
        return {'confidence_pct': confidence_pct, 'band': band,
                'live_sources': live_sources}

    def _compute_investment_band(self, details: Dict, elevation_m: float, pop_density: float) -> str:
        infra = details.get('infrastructure_access', {}).get('value', {})
        high_cost_items = 0
        if isinstance(infra, dict):
            if infra.get('ports', 0) == 0:
                high_cost_items += 1
            if infra.get('power_facilities', 0) == 0:
                high_cost_items += 1
        if elevation_m > 500 and high_cost_items >= 2:
            return 'Very High'
        if high_cost_items >= 2 or elevation_m > 800:
            return 'High'
        if high_cost_items == 1 or elevation_m > 200:
            return 'Moderate'
        return 'Low'

    def analyse(self, location: Location, params: Dict) -> Dict:
        radius = params.get('radius', 10000)
        default_weights = {
            'elevation': 0.13, 'bedrock_depth': 0.13, 'water_table_depth': 0.10,
            'seismic_risk': 0.10, 'geology': 0.12, 'population_density': 0.08,
            'coastal_proximity': 0.07, 'infrastructure_access': 0.10,
            'land_availability': 0.05, 'flood_risk': 0.05,
            'slope': 0.04, 'fault_proximity': 0.03,
        }
        custom = params.get('weights', None)
        if custom is None and st.session_state.get('custom_weights_enabled', False):
            custom = _compute_custom_weights_from_sidebar()
        weights = custom if custom else default_weights

        scores, details = {}, {}
        data_source_details = []
        live_sources = {}
        osm_available = False

        elevation_score, elevation_m, elev_source = self._get_elevation_quick(location)
        scores['elevation'] = elevation_score
        details['elevation'] = {'score': elevation_score, 'value': f"{elevation_m:.0f}m",
                                'weight': weights['elevation'], 'source': elev_source}
        data_source_details.append(f"Elevation: {elev_source}")
        live_sources['elevation'] = 'Live' in elev_source

        bedrock_score, bedrock_m, bedrock_source = self._estimate_bedrock_depth(location)
        scores['bedrock_depth'] = bedrock_score
        details['bedrock_depth'] = {'score': bedrock_score, 'value': f"{bedrock_m:.0f}m",
                                    'weight': weights['bedrock_depth'], 'source': bedrock_source}
        data_source_details.append(f"Bedrock: {bedrock_source}")
        live_sources['bedrock'] = False

        water_score, water_m, water_source = self._estimate_water_table(location)
        scores['water_table_depth'] = water_score
        details['water_table_depth'] = {'score': water_score, 'value': f"{water_m:.0f}m",
                                        'weight': weights['water_table_depth'], 'source': water_source}
        data_source_details.append(f"Water Table: {water_source}")
        live_sources['water_table'] = False

        seismic_result = self._estimate_seismic_risk(location)
        if len(seismic_result) == 4:
            seismic_score, seismic_risk, seismic_source, seismic_emoji = seismic_result
        else:
            seismic_score, seismic_risk, seismic_source = seismic_result
            seismic_emoji = {'Low': '🟢', 'Moderate': '🟡', 'High': '🔴'}.get(seismic_risk, '⚪')
        scores['seismic_risk'] = seismic_score
        details['seismic_risk'] = {'score': seismic_score, 'value': f"{seismic_emoji} {seismic_risk}",
                                   'weight': weights['seismic_risk'], 'source': seismic_source}
        data_source_details.append(f"Seismic: {seismic_source}")
        live_sources['seismic'] = seismic_source.startswith('USGS')

        geology_score, geology_source, karst_data = self._geographic_score_geology(location)
        scores['geology'] = geology_score
        details['geology'] = {'score': geology_score, 'value': 'Underground construction',
                              'weight': weights['geology'], 'source': geology_source}
        data_source_details.append(f"Geology: {geology_source}")
        live_sources['geology'] = False

        onegeo = self._get_onegeology_summary(location)
        if onegeo:
            data_source_details.append(f"🗺️ OneGeology: {onegeo['summary']}")
        live_sources['onegeology'] = onegeo is not None

        pop_score, pop_density, pop_source = self._geographic_score_population(location)
        scores['population_density'] = pop_score
        details['population_density'] = {'score': pop_score, 'value': f"{pop_density:.1f} people/km²",
                                         'weight': weights['population_density'], 'source': pop_source}
        data_source_details.append(f"Population: {pop_source}")

        coastal_score, dist_coast, coastal_source = self._geographic_score_coastal(location)
        scores['coastal_proximity'] = coastal_score
        details['coastal_proximity'] = {'score': coastal_score, 'value': f"{dist_coast:.1f}km",
                                        'weight': weights['coastal_proximity'], 'source': coastal_source}
        data_source_details.append(f"Coastal: {coastal_source}")

        infra_score, infra_details, infra_source = self._geographic_score_infrastructure(location)
        scores['infrastructure_access'] = infra_score
        details['infrastructure_access'] = {'score': infra_score, 'value': infra_details,
                                            'weight': weights['infrastructure_access'], 'source': infra_source}
        data_source_details.append(f"Infrastructure: {infra_source}")

        land_score, land_details, land_source = self._geographic_score_land(location)
        scores['land_availability'] = land_score
        details['land_availability'] = {'score': land_score, 'value': land_details,
                                        'weight': weights['land_availability'], 'source': land_source}
        data_source_details.append(f"Land: {land_source}")

        flood_score, flood_risk = self._geographic_score_flood(elevation_m)
        scores['flood_risk'] = flood_score
        details['flood_risk'] = {'score': flood_score, 'value': flood_risk,
                                 'weight': weights['flood_risk'], 'source': 'From elevation'}

        slope_data = estimate_slope(location.lat, location.lon)
        scores['slope'] = slope_data['score']
        details['slope'] = {'score': slope_data['score'], 'value': f"{slope_data['slope_deg']}° ({slope_data['risk']})",
                            'weight': weights['slope'], 'source': slope_data['source']}
        data_source_details.append(f"Slope: {slope_data['slope_deg']}° ({slope_data['risk']})")
        live_sources['slope'] = 'Live' in slope_data['source']

        fault = nearest_fault(location.lat, location.lon)
        if fault['distance_km'] < 10:
            fault_score = 1.5
        elif fault['distance_km'] < 30:
            fault_score = 3.0
        elif fault['distance_km'] < 60:
            fault_score = 4.0
        else:
            fault_score = 5.0
        scores['fault_proximity'] = fault_score
        details['fault_proximity'] = {'score': fault_score,
                                      'value': f"{fault['distance_km']}km to {fault['name']}",
                                      'weight': weights['fault_proximity'],
                                      'source': f"Nearest fault: {fault['name']} ({fault['activity']}, {fault['type']})"}
        data_source_details.append(f"Fault: {fault['name']} ({fault['distance_km']}km, {fault['activity']})")
        live_sources['fault'] = False

        total_score = sum(scores[k] * weights.get(k, 0) for k in scores if k in weights)
        max_possible = sum(weights.values()) * 5.0
        percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0

        penalty = 0.0
        penalty_reasons = []
        if elevation_m < 20:
            penalty += 12.0
            penalty_reasons.append(f"Very low elevation ({elevation_m:.0f}m): -12%")
        if flood_risk == 'High':
            penalty += 10.0
            penalty_reasons.append("High flood risk: -10%")
        if pop_density > 5:
            penalty += 8.0
            penalty_reasons.append("High population density: -8%")
        if water_m < 10:
            penalty += 15.0
            penalty_reasons.append(f"Shallow water table ({water_m:.0f}m): -15%")
        if seismic_risk == 'High':
            penalty += 12.0
            penalty_reasons.append("High seismic risk: -12%")
        if bedrock_m > 100:
            penalty += 8.0
            penalty_reasons.append("Very deep bedrock: -8%")

        percentage = max(0.0, min(100.0, percentage - penalty))

        if percentage >= 80:
            rating, emoji, rec = 'Excellent', '🏙️', 'Highly suitable for underground city development'
        elif percentage >= 65:
            rating, emoji, rec = 'Good', '👍', 'Suitable with minor site preparation'
        elif percentage >= 50:
            rating, emoji, rec = 'Moderate', '👌', 'Suitable with significant site preparation'
        elif percentage >= 35:
            rating, emoji, rec = 'Limited', '⚠️', 'Marginal - requires major investment'
        else:
            rating, emoji, rec = 'Poor', '❌', 'Not recommended for underground city development'

        try:
            osm_data = self._try_osm_in_background(location, radius)
            if osm_data and any(v > 0 for v in osm_data.values()):
                osm_available = True
                data_source_details.append(f"🌐 OSM Background: {osm_data.get('airport_count', 0)} airports")
        except Exception:
            pass

        gw = estimate_groundwater_quality(location.lat, location.lon, self.region)
        protected = check_protected_area(location.lat, location.lon)
        cave_warning = karst_data.get('cave_collapse_warning') if karst_data else None
        confidence = self._compute_data_confidence(live_sources)
        investment_band = self._compute_investment_band(details, elevation_m, pop_density)

        region_name = "Borneo" if self.region == "borneo" else "West Malaysia"
        return {
            'success': True, 'scores': scores, 'details': details,
            'weighted_score': total_score, 'max_possible_score': max_possible,
            'suitability_percentage': round(percentage, 1),
            'base_percentage': round((total_score / max_possible * 100) if max_possible > 0 else 0, 1),
            'penalty_applied': round(penalty, 1),
            'penalty_reasons': penalty_reasons,
            'rating': rating, 'rating_emoji': emoji, 'recommendation': rec,
            'radius_used': radius,
            'location': f"{location.name or region_name + ' location'} ({location.lat:.4f}, {location.lon:.4f})",
            'elevation_m': elevation_m, 'bedrock_depth_m': bedrock_m,
            'water_table_depth_m': water_m, 'seismic_risk': seismic_risk,
            'seismic_risk_emoji': seismic_emoji,
            'population_density': pop_density, 'coastal_distance_km': dist_coast,
            'flood_risk': flood_risk,
            'data_source_details': data_source_details,
            'used_osm': osm_available,
            'used_usgs': seismic_source.startswith('USGS'),
            'used_onegeology': onegeo is not None,
            'used_fallback': True, 'from_cache': False,
            'analysis_method': f'HYBRID: {region_name} + USGS + OneGeology + OSM',
            'region': self.region,
            'slope_deg': slope_data['slope_deg'],
            'slope_risk': slope_data['risk'],
            'slope_source': slope_data['source'],
            'nearest_fault': fault,
            'groundwater': gw,
            'protected_area': protected,
            'cave_warning': cave_warning,
            'karst_info': karst_data,
            'data_confidence': confidence,
            'investment_band': investment_band,
            '_weights_used': weights,
            '_lat': location.lat,
            '_lon': location.lon,
        }


class ProximityAnalysisStrategy(AnalysisStrategy):
    def get_name(self) -> str:
        return "Proximity Analysis"

    def analyse(self, location: Location, params: Dict) -> Dict:
        amenity_type = params.get('amenity_type', 'hospital')
        radius = params.get('radius', 5000)
        tags = UNDERGROUND_CITY_TAGS.get(amenity_type, [('amenity', amenity_type)])
        parts = []
        for k, v in tags:
            parts.append(f'node["{k}"="{v}"](around:{radius},{location.lat},{location.lon});')
            parts.append(f'way["{k}"="{v}"](around:{radius},{location.lat},{location.lon});')
        query = f"[out:json][timeout:45];({chr(10).join(parts)});out center;"
        try:
            r = requests.post("https://overpass-api.de/api/interpreter",
                              data={'data': query},
                              headers={'User-Agent': 'MalaysiaUndergroundCityGeoAI/1.0'}, timeout=45)
            r.raise_for_status()
            results, seen = [], set()
            for elem in r.json().get('elements', []):
                lat = elem.get('lat') or elem.get('center', {}).get('lat')
                lon = elem.get('lon') or elem.get('center', {}).get('lon')
                if lat and lon:
                    key = f"{round(lat,5)}_{round(lon,5)}"
                    if key not in seen:
                        seen.add(key)
                        tags_d = elem.get('tags', {})
                        results.append({
                            'name': tags_d.get('name', tags_d.get('brand', 'Unknown')),
                            'lat': lat, 'lon': lon, 'type': amenity_type, 'tags': tags_d
                        })
            return {'success': True, 'count': len(results), 'amenities': results,
                    'radius': radius, 'amenity_type': amenity_type,
                    'location': f"Malaysia ({location.lat:.4f}, {location.lon:.4f})"}
        except Exception as e:
            return {'success': False, 'error': str(e), 'amenities': [],
                    'count': 0, 'radius': radius, 'amenity_type': amenity_type}


class StrategySelector:
    _strategies = {'underground_city': UndergroundCitySuitabilityStrategy,
                   'proximity': ProximityAnalysisStrategy}

    @classmethod
    def get_strategy(cls, t: str, region: str = "borneo") -> AnalysisStrategy:
        if t == 'underground_city':
            return UndergroundCitySuitabilityStrategy(region)
        c = cls._strategies.get(t)
        if not c: raise ValueError(f"Unknown strategy: {t}")
        return c()

# ============================================================================
# PIPELINE + RATE LIMITER
# ============================================================================

class PipelineStep:
    def __init__(self, name, processor, description=""):
        self.name = name; self.processor = processor
        self.description = description; self.execution_time = 0.0; self.result = None


class Pipeline:
    def __init__(self, name):
        self.name = name; self.steps = []; self.results = {}
        self.execution_log = []
    def add_step(self, s): self.steps.append(s); return self
    def execute(self, initial_data, progress_callback=None):
        current = initial_data.copy()
        total = len(self.steps)
        for i, step in enumerate(self.steps):
            a = AnalysisStep(step_number=i+1, name=step.name,
                             description=step.description, status="running")
            if progress_callback: progress_callback(i/total, f"Running: {step.name}")
            t0 = time.time()
            try:
                step.result = step.processor(current)
                current.update(step.result)
                self.results[step.name] = step.result
                step.execution_time = time.time() - t0
                a.status = "completed"; a.result = step.result
                a.execution_time = step.execution_time
                a.reasoning = f"Successfully processed {step.name}"
            except Exception as e:
                step.execution_time = time.time() - t0
                a.status = "failed"; a.reasoning = f"Error: {e}"
                self.execution_log.append(a); raise
            self.execution_log.append(a)
        if progress_callback: progress_callback(1.0, "Complete")
        return current


class RateLimiter:
    def __init__(self, calls_per_second=0.5):
        self.calls_per_second = calls_per_second; self.last_call = 0
    def wait(self):
        now = time.time()
        delta = now - self.last_call
        min_i = 1.0 / self.calls_per_second
        if delta < min_i: time.sleep(min_i - delta)
        self.last_call = time.time()

# ============================================================================
# AGENT
# ============================================================================

class MalaysiaUndergroundCityGeoAIAgent:
    def __init__(self):
        self.memory_repo = MemoryRepository()
        self.rate_limiter = RateLimiter(0.5)
        self.short_term_memory = {}
        self.current_analysis = None

    def reason_about_query(self, query: str, region: str) -> tuple:
        region_name = "Borneo" if region == "borneo" else "West Malaysia"
        steps = [{'step': 'Understanding Query',
                  'reasoning': f"Analysing underground city request for {region_name}: '{query}'",
                  'action': 'parse_intent'}]
        similar = self.memory_repo.find_similar_analyses(query, 3)
        if similar:
            steps.append({'step': 'Memory Recall',
                          'reasoning': f"Found {len(similar)} similar past analyses.",
                          'action': 'apply_learned_parameters'})
        analysis_type = 'underground_city'
        steps.append({'step': 'Strategy Selection',
                      'reasoning': f'Using Underground City Suitability strategy for {region_name}.',
                      'action': 'use_underground_city_strategy'})
        lr = self.memory_repo.get_learned_parameter(analysis_type, 'radius')
        if lr:
            steps.append({'step': 'Parameter Optimisation',
                          'reasoning': f"Using learned radius {lr}m.",
                          'action': 'apply_learned_radius', 'value': lr})
        else:
            steps.append({'step': 'Parameter Selection',
                          'reasoning': 'Using default radius 10000m.',
                          'action': 'use_default_radius', 'value': '10000'})
        steps.append({'step': 'Execution Planning',
                      'reasoning': f'Will execute {analysis_type} analysis for {region_name}.',
                      'action': 'prepare_execution'})
        return steps, analysis_type

    def execute_analysis(self, location, query, params, region="borneo", progress_callback=None):
        t0 = time.time()
        result = AnalysisResult(query=query, timestamp=datetime.now().isoformat())
        reasoning, atype = self.reason_about_query(query, region)
        for i, si in enumerate(reasoning):
            result.steps.append(AnalysisStep(step_number=i+1, name=si['step'],
                                             description=si['reasoning'],
                                             status='completed', reasoning=si['reasoning']))
        if progress_callback: progress_callback(0.3, "Executing hybrid analysis...")
        try:
            strategy = StrategySelector.get_strategy(atype, region)
            self.rate_limiter.wait()
            ar = strategy.analyse(location, params)
            ar['from_cache'] = False
            if ar.get('success'):
                result.steps.append(AnalysisStep(
                    step_number=len(result.steps)+1, name="Data Source Validation",
                    description=f"Method: {ar.get('analysis_method','HYBRID')}",
                    status='completed',
                    reasoning=f"USGS={ar.get('used_usgs')}, OneGeology={ar.get('used_onegeology')}, OSM={ar.get('used_osm')}"))
            result.steps.append(AnalysisStep(
                step_number=len(result.steps)+1,
                name=f"Execute {strategy.get_name()}",
                description=f"Running {atype} on {location.name or 'location'}",
                status='completed' if ar.get('success') else 'failed',
                result=ar, reasoning=f"Returned {len(str(ar))} bytes"))
            result.final_result = ar
            result.success = ar.get('success', False)
        except Exception as e:
            result.steps.append(AnalysisStep(
                step_number=len(result.steps)+1, name="Analysis Execution",
                description="Executing spatial analysis", status='failed',
                reasoning=f"Error: {e}"))
            result.success = False
        if progress_callback: progress_callback(0.8, "Storing in memory...")
        result.total_time = time.time() - t0
        self.memory_repo.store_analysis(MemoryEntry(
            query=query,
            result_summary=str(result.final_result)[:500] if result.final_result else "",
            success=result.success, execution_time=result.total_time,
            timestamp=result.timestamp, parameters_used=params))
        if result.success:
            self.memory_repo.update_learned_parameter(
                atype, 'radius', str(params.get('radius', 10000)), True)
        self.short_term_memory['last_analysis'] = result
        self.short_term_memory['last_location'] = location
        if progress_callback: progress_callback(1.0, "Complete")
        return result

# ============================================================================
# PHASE 2-5 MODULES
# ============================================================================

@dataclass
class InfrastructurePlan:
    site_name: str
    cost_breakdown: Dict
    transport_network: Dict
    utility_systems: Dict
    timeline: Dict
    total_cost: float
    timeline_years: int


class CostEstimator:
    COST_FACTORS = {
        'excavation': {'hard_rock': 2000, 'soft_rock': 1200, 'soil': 500},
        'construction': {'basic': 3000, 'mid': 5000, 'luxury': 8000},
        'infrastructure': {'water': 500, 'power': 800, 'ventilation': 1200, 'transport': 1500, 'telecom': 400},
        'finishing': {'basic': 1500, 'mid': 3000, 'luxury': 5000}
    }
    def estimate(self, site_data: Dict, size_sqm: int = 1000000) -> Dict:
        elevation = site_data.get('elevation_m', 100)
        geology_score = site_data.get('scores', {}).get('geology', 3)
        if elevation > 500 and geology_score > 4:
            rock_type = 'hard_rock'
        elif elevation > 200:
            rock_type = 'soft_rock'
        else:
            rock_type = 'soil'
        excavation_cost = self.COST_FACTORS['excavation'][rock_type] * size_sqm
        construction_cost = self.COST_FACTORS['construction']['mid'] * size_sqm * 0.4
        infrastructure_cost = sum(self.COST_FACTORS['infrastructure'].values()) * size_sqm * 0.2
        finishing_cost = self.COST_FACTORS['finishing']['mid'] * size_sqm * 0.3
        bedrock_depth = site_data.get('bedrock_depth_m', 30)
        if bedrock_depth < 20: excavation_cost *= 0.7
        elif bedrock_depth > 80: excavation_cost *= 1.3
        water_table = site_data.get('water_table_depth_m', 30)
        if water_table < 15: infrastructure_cost *= 1.4
        total = excavation_cost + construction_cost + infrastructure_cost + finishing_cost
        return {
            'total_cost_rm': total, 'total_cost_billions': total / 1_000_000_000,
            'excavation': excavation_cost, 'construction': construction_cost,
            'infrastructure': infrastructure_cost, 'finishing': finishing_cost,
            'per_sqm_cost': total / size_sqm, 'size_sqm': size_sqm,
            'rock_type': rock_type,
            'breakdown': {
                'Excavation': excavation_cost / total * 100,
                'Construction': construction_cost / total * 100,
                'Infrastructure': infrastructure_cost / total * 100,
                'Finishing': finishing_cost / total * 100
            }
        }


class TransportPlanner:
    def plan_transport(self, site_data: Dict, population: int = 50000) -> Dict:
        if population > 100000:
            transport_type, network_length = 'metro', population * 0.002
        elif population > 50000:
            transport_type, network_length = 'light_rail', population * 0.0015
        else:
            transport_type, network_length = 'automated_pod', population * 0.001
        depth = site_data.get('elevation_m', 100)
        elevators = 8 if depth > 200 else 5 if depth > 100 else 3
        return {
            'primary_transport': transport_type,
            'network_length_km': network_length,
            'elevators': elevators,
            'stations': max(10, int(population / 5000)),
            'estimated_cost': network_length * 50_000_000,
            'environmental_impact': 'Low',
            'access_points': 4 + elevators,
            'emergency_exits': int(population / 10000)
        }


class UtilityDesigner:
    def design_utilities(self, site_data: Dict, population: int = 50000) -> Dict:
        water_needed = population * 150
        power_needed = population * 5
        air_needed = population * 10
        return {
            'water': {'daily_need_liters': water_needed, 'storage_capacity': water_needed * 3,
                      'recycling_rate': 95, 'source': 'Rainwater + Groundwater'},
            'power': {'peak_demand_mw': power_needed / 1000, 'storage_mwh': power_needed * 12 / 1000,
                      'sources': ['Geothermal 60%', 'Solar 30%', 'Grid 10%'], 'redundancy': 3},
            'ventilation': {'airflow_m3h': air_needed, 'heat_exchange_efficiency': 85,
                            'co2_scrubbers': True, 'oxygen_generation': True},
            'waste': {'recycling_rate': 90, 'composting': True, 'zero_discharge': True}
        }


class ConstructionSimulator:
    def simulate_construction(self, site_data: Dict, plan: Dict,
                              elevation_complexity_factor: float = 1.0) -> Dict:
        size_sqm = 1000000
        elevation_m = site_data.get('elevation_m', 100)

        base_excavation = 8 + (size_sqm / 150_000)
        base_excavation = min(24, max(12, base_excavation))

        base_structural = 12 + (size_sqm / 100_000)
        base_structural = min(30, max(18, base_structural))

        phases = {
            'site_preparation': {
                'duration_months': 6,
                'tasks': ['Surveying', 'Access roads', 'Surface facilities'],
                'cost_percentage': 5
            },
            'excavation': {
                'duration_months': round(base_excavation * elevation_complexity_factor, 1),
                'tasks': ['Tunnel boring', 'Rock removal', 'Shoring'],
                'cost_percentage': 25
            },
            'structural': {
                'duration_months': round(base_structural * elevation_complexity_factor, 1),
                'tasks': ['Concrete work', 'Steel structures', 'Waterproofing'],
                'cost_percentage': 30
            },
            'systems_installation': {
                'duration_months': 12,
                'tasks': ['Ventilation', 'Power', 'Water', 'Communication'],
                'cost_percentage': 20
            },
            'finishing': {
                'duration_months': 12,
                'tasks': ['Lighting', 'Interior', 'Furnishing'],
                'cost_percentage': 15
            },
            'testing': {
                'duration_months': 6,
                'tasks': ['Systems testing', 'Safety checks', 'Commissioning'],
                'cost_percentage': 5
            }
        }

        total_months = sum(p['duration_months'] for p in phases.values())

        return {
            'phases': phases,
            'total_months': round(total_months, 1),
            'total_years': round(total_months / 12, 1),
            'total_months_human': f"{total_months:.0f} months (~{total_months/12:.1f} years)",
            'elevation_complexity_factor': round(elevation_complexity_factor, 2),
            'daily_progress': round(100 / total_months / 30, 4),
            'critical_path': ['excavation', 'structural', 'systems_installation'],
            'completion_probability': min(95, 100 - (1 / max(elevation_m / 100, 1) * 10)),
            'risk_factors': [
                'Geological unexpected conditions',
                'Water ingress' if elevation_m < 50 else 'Minimal (high elevation)',
                'Equipment failures'
            ]
        }


class ResourceOptimizer:
    def optimize_resources(self, site_data: Dict, construction_plan: Dict) -> Dict:
        size_sqm = 1000000
        return {
            'materials': {
                'concrete': {'amount_m3': size_sqm * 0.3, 'unit': 'm³', 'cost_per_unit': 250, 'suppliers': ['Local', 'Regional']},
                'steel': {'amount_tonnes': size_sqm * 0.05, 'unit': 'tonnes', 'cost_per_unit': 3000, 'suppliers': ['Regional', 'Import']},
                'tunnel_segments': {'amount': int(size_sqm / 100), 'unit': 'segments', 'cost_per_unit': 15000, 'suppliers': ['Specialized']}
            },
            'labor': {'engineers': int(size_sqm / 10000), 'workers': int(size_sqm / 1000), 'specialists': int(size_sqm / 5000)},
            'equipment': {'tbm': 3, 'excavators': 10, 'cranes': 5, 'ventilation_systems': 20},
            'optimization_score': 85, 'waste_reduction': 15, 'cost_savings_percentage': 12
        }


class ProgressMonitor:
    def monitor_progress(self, site_data: Dict, timeline: Dict) -> Dict:
        total_months = 48
        return {
            'current_progress': 30,
            'monthly_progress': 100 / total_months,
            'status': 'On Track',
            'milestones': [
                {'name': 'Site Survey Complete', 'month': 2, 'status': 'Completed'},
                {'name': 'Excavation Start', 'month': 4, 'status': 'Completed'},
                {'name': 'First Chamber', 'month': 12, 'status': 'In Progress'},
                {'name': 'Structural Complete', 'month': 24, 'status': 'Pending'},
                {'name': 'Systems Installation', 'month': 36, 'status': 'Pending'},
                {'name': 'Commissioning', 'month': 48, 'status': 'Pending'}
            ]
        }


class VRWalkthroughGenerator:
    def generate_walkthrough(self, site_data: Dict, plan: Dict) -> Dict:
        return {
            'scenes': [
                {'name': 'Main Entrance', 'description': 'Welcome to the underground city', 'features': ['Elevators', 'Security', 'Information Center']},
                {'name': 'City Center', 'description': 'The heart of the underground city', 'features': ['Shopping', 'Parks', 'Restaurants']},
                {'name': 'Residential Zone', 'description': 'Modern underground apartments', 'features': ['Homes', 'Schools', 'Healthcare']},
                {'name': 'Transit Hub', 'description': 'Automated transport network', 'features': ['Trains', 'Pods', 'Accessible Design']},
                {'name': 'Agricultural Center', 'description': 'Hydroponic vertical farming', 'features': ['Fresh produce', 'Sustainable']}
            ],
            'vr_ready': True, 'estimated_size_mb': 200,
            'platforms': ['Oculus', 'HTC Vive', 'WebVR'],
            'interactive_elements': 25
        }


class PublicConsultation:
    def create_consultation(self, site_data: Dict) -> Dict:
        return {
            'survey_questions': [
                {'question': 'Do you support underground city development?', 'options': ['Yes', 'No', 'Need more information']},
                {'question': 'What features are most important?', 'options': ['Housing', 'Jobs', 'Parks', 'Transportation', 'Education']},
                {'question': 'Would you consider living underground?', 'options': ['Yes', 'Maybe', 'No', 'Need to see it']},
                {'question': 'Environmental concerns?', 'options': ['Forest preservation', 'Water usage', 'Energy', 'Wildlife']}
            ],
            'community_events': ['Town halls', 'Virtual tours', 'Information sessions', 'School programs', 'Open houses'],
            'feedback_channels': ['Web portal', 'Mobile app', 'Physical center', 'Social media', 'Email newsletter']
        }


class EducationSystem:
    def create_education_material(self, site_data: Dict) -> Dict:
        return {
            'modules': [
                {'title': 'Understanding Underground Living', 'topics': ['History', 'Benefits', 'Future'], 'target_audience': 'General Public', 'duration_hours': 2},
                {'title': 'Underground City Systems', 'topics': ['Life support', 'Energy', 'Water', 'Waste'], 'target_audience': 'Students', 'duration_hours': 4},
                {'title': 'Construction Technology', 'topics': ['Tunneling', 'Safety', 'Materials', 'Innovation'], 'target_audience': 'Engineers', 'duration_hours': 8},
                {'title': 'Sustainability Underground', 'topics': ['Green design', 'Climate resilience', 'Biodiversity'], 'target_audience': 'All ages', 'duration_hours': 3}
            ],
            'formats': ['Video', 'Interactive', 'Workshops', 'Online courses']
        }


class TourismPlanner:
    def plan_tourism(self, site_data: Dict) -> Dict:
        return {
            'attractions': [
                {'name': 'World\'s Largest Underground City', 'type': 'Landmark', 'visitors_per_year': 500000},
                {'name': 'Cave Cathedral', 'type': 'Natural Wonder', 'visitors_per_year': 300000},
                {'name': 'Underground Gardens', 'type': 'Eco-tourism', 'visitors_per_year': 200000},
                {'name': 'Transport Experience', 'type': 'Technology', 'visitors_per_year': 150000}
            ],
            'facilities': {'hotels': 3, 'restaurants': 15, 'museums': 2, 'visitor_centers': 2, 'shops': 20},
            'estimated_annual_revenue': 50_000_000,
            'jobs_created': 1000, 'sustainability_score': 95
        }


class MultiCountrySupport:
    COUNTRIES = {
        'Malaysia': {'currency': 'RM', 'regulations': 'MS1234:2024', 'labor_cost_factor': 1.0, 'material_cost_factor': 1.0},
        'Singapore': {'currency': 'SGD', 'regulations': 'SS EN 1997', 'labor_cost_factor': 2.5, 'material_cost_factor': 1.8},
        'China': {'currency': 'CNY', 'regulations': 'GB 50838', 'labor_cost_factor': 0.7, 'material_cost_factor': 0.8},
        'Japan': {'currency': 'JPY', 'regulations': 'JIS A 8319', 'labor_cost_factor': 2.2, 'material_cost_factor': 1.5}
    }
    def adapt_site_analysis(self, site_data: Dict, country: str) -> Dict:
        country_data = self.COUNTRIES.get(country, self.COUNTRIES['Malaysia'])
        adapted = site_data.copy()
        if 'cost_estimates' in adapted:
            adapted['cost_estimates']['total_cost'] *= country_data['labor_cost_factor']
            adapted['cost_estimates']['material_cost'] *= country_data['material_cost_factor']
        adapted['country'] = country
        adapted['regulations'] = country_data['regulations']
        adapted['currency'] = country_data['currency']
        return adapted


class MarsAdaptation:
    def adapt_for_mars(self, site_data: Dict) -> Dict:
        return {
            'mars_adaptation': {
                'pressure_vessels': True, 'radiation_shielding': '5m regolith cover',
                'atmosphere': 'Earth-like (O2 + N2)', 'temperature': '0°C stable',
                'gravity': '0.38g adjustment', 'day_night_cycle': '24h 37m simulation',
                'water_source': 'Subsurface ice mining', 'power_source': 'Nuclear + Solar',
                'food_production': 'Hydroponics + Algae', 'transport': 'Pressurized rovers',
                'construction_materials': 'Regolith-based concrete', 'life_support': '100% closed loop'
            },
            'similarities': {
                'underground_construction': '90% transferable', 'life_support': '95% transferable',
                'energy_systems': '85% transferable', 'water_recycling': '95% transferable',
                'food_production': '90% transferable'
            },
            'timeline': {
                'design': '2026-2030', 'prototype': '2030-2035',
                'mars_ready': '2035-2040', 'first_colony': '2040-2050'
            }
        }


class ClimateCrisisModule:
    def assess_climate_resilience(self, site_data: Dict) -> Dict:
        elevation = site_data.get('elevation_m', 100)
        sea_level_rise = {'2030': 0.2, '2050': 0.5, '2100': 1.5}
        return {
            'elevation_safety': elevation > 50,
            'flood_protection_needed': elevation < 50,
            'sea_level_rise_projection': sea_level_rise,
            'temperature_stability': 'Excellent (underground)',
            'extreme_weather_protection': 'Complete (underground)',
            'energy_resilience': 'Self-sufficient 95%',
            'water_resilience': 'Self-sufficient 100%',
            'food_resilience': 'Self-sufficient 90%',
            'overall_resilience_score': min(95, 80 + (elevation / 50)),
            'climate_refuge_capacity': 100000 if elevation > 50 else 0
        }


class AISwarm:
    def __init__(self):
        self.agents = []
    def create_swarm(self, num_agents: int = 5) -> Dict:
        agent_roles = ['Site Surveyor', 'Geological Analyst', 'Infrastructure Planner',
                       'Construction Manager', 'Public Relations']
        self.agents = []
        for i in range(min(num_agents, len(agent_roles))):
            self.agents.append({
                'id': f'Agent_{i+1}', 'role': agent_roles[i], 'status': 'Active',
                'specialty': f'Underground city {agent_roles[i].lower()}',
                'capabilities': ['AI vision', 'NLP', 'Predictive modeling']
            })
        return {'agents': self.agents, 'coordination_level': 'High',
                'redundancy': 3, 'self_healing': True, 'learning_rate': 0.95}


class EnhancedUndergroundCityDeveloper:
    def __init__(self):
        self.cost_estimator = CostEstimator()
        self.transport_planner = TransportPlanner()
        self.utility_designer = UtilityDesigner()
        self.construction_simulator = ConstructionSimulator()
        self.resource_optimizer = ResourceOptimizer()
        self.progress_monitor = ProgressMonitor()
        self.vr_generator = VRWalkthroughGenerator()
        self.public_consultation = PublicConsultation()
        self.education_system = EducationSystem()
        self.tourism_planner = TourismPlanner()
        self.multi_country = MultiCountrySupport()
        self.mars_adaptation = MarsAdaptation()
        self.climate_module = ClimateCrisisModule()
        self.ai_swarm = AISwarm()

    def develop_complete_city(self, site_data: Dict, population: int = 50000) -> Dict:
        disp = compute_display_score(site_data)
        cost_range = estimate_cost_range(site_data)

        elevation_m = site_data.get('elevation_m', 0)
        elevation_complexity = min(2.0, max(1.0, 1.0 + (elevation_m / 3000.0)))

        simulation = self.construction_simulator.simulate_construction(
            site_data, {}, elevation_complexity_factor=elevation_complexity
        )
        total_months = simulation['total_months']
        total_years = simulation['total_years']

        return {
            'phase_1_site_selection': {
                'site_data': site_data,
                'suitability_score': disp['display_score'],
                'raw_geological_score': disp['raw_score'],
                'display_rating': disp['display_rating'],
                'display_emoji': disp['display_emoji'],
                'not_feasible': disp['not_feasible'],
                'cap_reason': disp['cap_reason'],
                'headline_cost_mid_billion': cost_range['mid_billion'],
                'total_months': total_months,
                'total_years': total_years,
                'total_months_human': simulation['total_months_human'],
                'elevation_complexity_factor': elevation_complexity,
            },
            'phase_2_infrastructure': {
                'cost_estimate': self.cost_estimator.estimate(site_data),
                'transport_plan': self.transport_planner.plan_transport(site_data, population),
                'utility_plan': self.utility_designer.design_utilities(site_data, population)
            },
            'phase_3_construction': {
                'simulation': simulation,
                'resource_optimization': self.resource_optimizer.optimize_resources(site_data, {}),
                'progress_plan': self.progress_monitor.monitor_progress(site_data, {})
            },
            'phase_4_public': {
                'vr_walkthrough': self.vr_generator.generate_walkthrough(site_data, {}),
                'consultation': self.public_consultation.create_consultation(site_data),
                'education': self.education_system.create_education_material(site_data),
                'tourism': self.tourism_planner.plan_tourism(site_data)
            },
            'phase_5_global': {
                'mars_adaptation': self.mars_adaptation.adapt_for_mars(site_data),
                'climate_resilience': self.climate_module.assess_climate_resilience(site_data),
                'ai_swarm': self.ai_swarm.create_swarm()
            }
        }

# ============================================================================
# UI FUNCTIONS
# ============================================================================

def init_session_state():
    if 'agent' not in st.session_state:
        st.session_state.agent = MalaysiaUndergroundCityGeoAIAgent()
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'region' not in st.session_state:
        st.session_state.region = 'borneo'
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = Location(
            lat=5.9800, lon=116.5700, name="Kundasang Highlands, Sabah")
    if 'reasoning_log' not in st.session_state:
        st.session_state.reasoning_log = []
    if 'current_results' not in st.session_state:
        st.session_state.current_results = None
    if 'basemap_choice' not in st.session_state:
        st.session_state.basemap_choice = "OpenStreetMap"
    if 'show_radius_circle' not in st.session_state:
        st.session_state.show_radius_circle = True
    if 'show_heatmap' not in st.session_state:
        st.session_state.show_heatmap = False
    if 'show_onegeology' not in st.session_state:
        st.session_state.show_onegeology = False
    if 'comparison_mode' not in st.session_state:
        st.session_state.comparison_mode = False
    if 'candidate_scores' not in st.session_state:
        st.session_state.candidate_scores = {}
    if 'phase_view' not in st.session_state:
        st.session_state.phase_view = 'all'
    if 'elevation_cache' not in st.session_state:
        st.session_state.elevation_cache = {}
    if 'multi_ranking_mode' not in st.session_state:
        st.session_state.multi_ranking_mode = False
    if 'multi_ranking_selected' not in st.session_state:
        st.session_state.multi_ranking_selected = []
    if 'multi_ranking_results' not in st.session_state:
        st.session_state.multi_ranking_results = None
    if 'nearby_alternatives_cache' not in st.session_state:
        st.session_state.nearby_alternatives_cache = None
    if 'use_osm_live' not in st.session_state:
        st.session_state.use_osm_live = True
    if 'custom_weights_enabled' not in st.session_state:
        st.session_state.custom_weights_enabled = False
    if 'custom_weights' not in st.session_state:
        st.session_state.custom_weights = {
            'elevation': 0.13, 'bedrock_depth': 0.13, 'water_table_depth': 0.10,
            'seismic_risk': 0.10, 'geology': 0.12, 'population_density': 0.08,
            'coastal_proximity': 0.07, 'infrastructure_access': 0.10,
            'land_availability': 0.05, 'flood_risk': 0.05,
            'slope': 0.04, 'fault_proximity': 0.03,
        }


def get_tiles_for_basemap(basemap_choice: str) -> str:
    if basemap_choice == "Satellite":
        return "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    return "OpenStreetMap"


def render_region_switcher():
    st.markdown("""
    <div style="text-align: center; margin: 10px 0;">
        <div style="color: #00f0ff; font-family: 'Courier New', monospace; 
             letter-spacing: 3px; font-size: 0.9rem; margin-bottom: 10px;">
            🌏 SELECT REGION</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏝️ BORNEO\n(Sabah & Sarawak)",
                     use_container_width=True,
                     type="primary" if st.session_state.region == 'borneo' else "secondary"):
            st.session_state.region = 'borneo'
            st.session_state.selected_location = Location(
                lat=5.9800, lon=116.5700, name="Kundasang Highlands, Sabah")
            st.session_state.current_results = None
            st.session_state.nearby_alternatives_cache = None
            st.rerun()
    with col2:
        if st.button("🏙️ WEST MALAYSIA\n(Peninsular)",
                     use_container_width=True,
                     type="primary" if st.session_state.region == 'west_malaysia' else "secondary"):
            st.session_state.region = 'west_malaysia'
            st.session_state.selected_location = Location(
                lat=4.4700, lon=101.3800, name="Cameron Highlands (Pahang)")
            st.session_state.current_results = None
            st.session_state.nearby_alternatives_cache = None
            st.rerun()

    return st.session_state.region


def render_region_selector(region):
    if region == 'borneo':
        regions = {
            '🌏 All Borneo': 'all',
            '🏝️ Sabah Only': 'sabah',
            '🏝️ Sarawak Only': 'sarawak',
            '🏙️ Underground City Candidates': 'candidates'
        }
        selected_region = st.selectbox("Select Region", options=list(regions.keys()), index=0)
        region_key = regions[selected_region]
        if region_key == 'sabah':
            locations = SABAH_LOCATIONS
            st.info(f"🏝️ Showing {len(locations)} locations in Sabah")
        elif region_key == 'sarawak':
            locations = SARAWAK_LOCATIONS
            st.info(f"🏝️ Showing {len(locations)} locations in Sarawak")
        elif region_key == 'candidates':
            locations = BORNEO_UNDERGROUND_CITY_CANDIDATES
            st.info(f"🏙️ Showing {len(locations)} underground city candidate sites")
        else:
            locations = BORNEO_LOCATIONS
            st.info(f"🌏 Showing {len(locations)} locations across Borneo")
        return locations, region_key
    else:
        regions = {
            '🌏 All West Malaysia': 'all',
            '🏝️ Northern (Perlis, Kedah, Penang, Perak)': 'north',
            '🏙️ Central (Selangor, KL, Putrajaya, N. Sembilan)': 'central',
            '🌴 Southern (Melaka, Johor)': 'south',
            '🌊 East Coast (Kelantan, Terengganu, Pahang)': 'east',
            '🏙️ Underground City Candidates': 'candidates'
        }
        sel = st.selectbox("Select Region", options=list(regions.keys()), index=0)
        rk = regions[sel]
        north = ['Perlis', 'Kedah', 'Penang', 'Perak']
        central = ['Selangor', 'Kuala Lumpur', 'Putrajaya', 'Negeri Sembilan']
        south = ['Melaka', 'Johor']
        east = ['Kelantan', 'Terengganu', 'Pahang']
        if rk == 'all':
            locations = WEST_MALAYSIA_LOCATIONS
            st.info(f"🌏 Showing {len(locations)} locations across West Malaysia")
        elif rk == 'candidates':
            locations = WEST_MALAYSIA_UNDERGROUND_CITY_CANDIDATES
            st.info(f"🏙️ Showing {len(locations)} underground city candidate sites")
        else:
            sl = {'north': north, 'central': central, 'south': south, 'east': east}[rk]
            locations = {k: v for k, v in WEST_MALAYSIA_LOCATIONS.items()
                        if any(f"({s})" in k for s in sl)}
            st.info(f"📍 Showing {len(locations)} locations in {sel}")
        return locations, rk


def render_phase_selector():
    st.markdown("""
    <div style="display: flex; gap: 10px; margin: 10px 0; flex-wrap: wrap;">
        <span class="phase-badge phase-badge-2">🔧 PHASE 2: INFRASTRUCTURE</span>
        <span class="phase-badge phase-badge-3">🏗️ PHASE 3: CONSTRUCTION AI</span>
        <span class="phase-badge phase-badge-4">👥 PHASE 4: PUBLIC ENGAGEMENT</span>
        <span class="phase-badge phase-badge-5">🌍 PHASE 5: GLOBAL EXPANSION</span>
    </div>
    """, unsafe_allow_html=True)
    phases = {
        'Phase 2: Infrastructure Planning': 'phase2',
        'Phase 3: Construction AI': 'phase3',
        'Phase 4: Public Engagement': 'phase4',
        'Phase 5: Global Expansion': 'phase5',
        '🎯 All Phases (Complete Plan)': 'all'
    }
    selected_phase = st.selectbox("Select Development Phase", options=list(phases.keys()), index=4)
    return phases[selected_phase]


def render_sidebar(region):
    with st.sidebar:
        region_label = "BORNEO" if region == 'borneo' else "WEST MALAYSIA"
        region_icon = "🏝️" if region == 'borneo' else "🏙️"

        st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <div style="font-size: 2.2rem; font-family: 'Courier New', monospace; 
                 background: linear-gradient(90deg, #00f0ff, #b026ff, #ff2d95);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 font-weight: 900; letter-spacing: 3px;">UNDERGROUND</div>
            <div style="color: #00f0ff; font-size: 0.75rem; font-family: 'Courier New', monospace;
                 letter-spacing: 4px;">
                {region_icon} {region_label}</div>
            <div class="cyber-divider"></div>
        </div>
        """, unsafe_allow_html=True)

        cache_stats = api_cache.get_stats()
        st.markdown(f"""
        <div style="color: #a0a0c0; font-family: 'Courier New', monospace; font-size: 0.7rem; 
             letter-spacing: 1px; text-align: center; border: 1px solid rgba(0, 240, 255, 0.1);
             border-radius: 4px; padding: 4px 8px; margin-bottom: 10px;">
            ⚡ CACHE: {cache_stats['total_cached']} RESPONSES
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        # 🆕 v5.3.1: UNIVERSAL SEARCH — sits at top of sidebar
        render_universal_search_sidebar()

        st.markdown("""<div style="color: #00f0ff; font-family: 'Courier New', monospace; 
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            ⚡ LOCATION SELECTOR</div>""", unsafe_allow_html=True)

        locations, region_key = render_region_selector(region)
        quick_location = st.selectbox("Select Location", list(locations.keys()), index=0)
        if st.button("⚡ GO TO LOCATION", use_container_width=True):
            coords = locations[quick_location]
            st.session_state.selected_location = Location(lat=coords[0], lon=coords[1], name=quick_location)
            st.session_state.nearby_alternatives_cache = None
            st.rerun()
        st.caption("Or click on the map to select any location")
        st.divider()

        st.markdown("""<div style="color: #00f0ff; font-family: 'Courier New', monospace; 
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            🗺️ MAP SETTINGS</div>""", unsafe_allow_html=True)

        basemap_choice = st.radio(
            "Map Style",
            options=["🗺️ OpenStreetMap", "🛰️ Satellite"],
            index=0 if st.session_state.basemap_choice == "OpenStreetMap" else 1,
            horizontal=True,
            label_visibility="collapsed"
        )
        if "Satellite" in basemap_choice:
            st.session_state.basemap_choice = "Satellite"
        else:
            st.session_state.basemap_choice = "OpenStreetMap"

        st.session_state.show_radius_circle = st.checkbox("Show Search Radius", value=True)
        st.session_state.show_onegeology = st.checkbox("🗺️ Show OneGeology Layer", value=False,
                                                       help="Overlay the global geological map (World CGMW)")
        st.divider()

        st.markdown("""<div style="color: #00f0ff; font-family: 'Courier New', monospace; 
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            🆕 LIVE DATA (v5.3.0)</div>""", unsafe_allow_html=True)
        st.session_state.use_osm_live = st.checkbox(
            "Use OSM live data (population, land, seismic retry)",
            value=True,
            help="OFF restores exact v5.2.1 behavior (geographic heuristics only). "
                 "ON uses live OSM Overpass + USGS retry.",
        )
        if st.session_state.use_osm_live:
            st.caption("✅ Using OSM Overpass + USGS retry — confidence may rise")
        else:
            st.caption("⚠️ Using v5.2.1 heuristic mode — same as previous version")

        _render_custom_weights_sidebar()
        st.divider()

        st.markdown("""<div style="color: #00f0ff; font-family: 'Courier New', monospace; 
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            ⚙️ ANALYSIS PARAMETERS</div>""", unsafe_allow_html=True)
        radius = st.slider("Assessment Radius (m)", 2000, 20000, 10000, 1000)
        st.divider()
        if st.button("🔄 COMPARE ALL", use_container_width=True):
            st.session_state.comparison_mode = True
            st.session_state.multi_ranking_mode = False
            st.rerun()
        if st.button("📊 MULTI-SITE RANKING", use_container_width=True):
            st.session_state.multi_ranking_mode = True
            st.session_state.comparison_mode = False
            st.rerun()
        if st.button("🧹 CLEAR", use_container_width=True):
            st.session_state.current_results = None
            st.session_state.reasoning_log = []
            st.session_state.candidate_scores = {}
            st.session_state.multi_ranking_results = None
            st.session_state.nearby_alternatives_cache = None
            st.success("Results cleared!"); st.rerun()
        if st.button("🗑️ CLEAR CACHE", use_container_width=True):
            api_cache.clear()
            st.session_state.elevation_cache = {}
            _slope_lookup_cached.clear()
            _get_elevation_cached.clear()
            _get_seismic_usgs_with_retry.clear()
            _get_population_osm.clear()
            _get_land_use_osm.clear()
            _get_onegeology_with_retry.clear()
            st.success("Cache cleared!"); st.rerun()
        st.divider()
        st.markdown("""<div style="color: #00f0ff; font-family: 'Courier New', monospace; 
             letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 10px;">
            🧠 AGENT MEMORY</div>""", unsafe_allow_html=True)
        stats = st.session_state.agent.memory_repo.get_analysis_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""<div style="text-align: center; padding: 8px; border: 1px solid rgba(0, 240, 255, 0.1);
                 border-radius: 4px;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem; 
                     letter-spacing: 1px;">ANALYSES</div>
                <div style="color: #00f0ff; font-family: 'Courier New', monospace; font-size: 1.2rem; 
                     font-weight: bold;">{stats['total_analyses']}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div style="text-align: center; padding: 8px; border: 1px solid rgba(0, 240, 255, 0.1);
                 border-radius: 4px;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem; 
                     letter-spacing: 1px;">SUCCESS RATE</div>
                <div style="color: #39ff14; font-family: 'Courier New', monospace; font-size: 1.2rem; 
                     font-weight: bold;">{stats['success_rate']*100:.0f}%</div></div>""", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align: center; padding: 8px; border: 1px solid rgba(0, 240, 255, 0.1);
             border-radius: 4px; margin-top: 8px;">
            <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem; 
                 letter-spacing: 1px;">AVG EXECUTION</div>
            <div style="color: #b026ff; font-family: 'Courier New', monospace; font-size: 1.2rem; 
                 font-weight: bold;">{stats['avg_execution_time']:.2f}s</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️ CLEAR MEMORY", use_container_width=True):
            Path("malaysia_underground_city_memory.db").unlink(missing_ok=True)
            st.session_state.agent = MalaysiaUndergroundCityGeoAIAgent()
            st.session_state.analysis_history = []
            st.session_state.current_results = None
            st.session_state.reasoning_log = []
            st.session_state.candidate_scores = {}
            st.success("All memory cleared!"); st.rerun()
        return {'radius': radius}


def render_map(params, region):
    region_label = "Borneo" if region == 'borneo' else "West Malaysia"
    st.subheader(f"🗺️ {region_label} Underground City Site Map")

    if region == 'borneo':
        center = [5.0, 117.0]
        zoom = 7
    else:
        center = [4.2, 102.0]
        zoom = 7

    location_name = region_label
    if st.session_state.selected_location:
        center = [st.session_state.selected_location.lat, st.session_state.selected_location.lon]
        location_name = st.session_state.selected_location.name or f"{region_label} Location"

    basemap_choice = st.session_state.get('basemap_choice', 'OpenStreetMap')
    tiles_url = get_tiles_for_basemap(basemap_choice)

    try:
        if basemap_choice == "Satellite":
            m = folium.Map(location=center, zoom_start=zoom,
                           tiles=tiles_url, attr='Esri World Imagery')
        else:
            m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
    except Exception:
        m = folium.Map(location=center, zoom_start=zoom)

    if st.session_state.get('show_onegeology', False):
        try:
            onegeo_layer = folium.WmsTileLayer(
                url="https://portal.onegeology.org/OneGeologyGlobal/WMS/1.3.0",
                name="OneGeology Bedrock",
                layers="World_CGMW",
                fmt="image/png",
                transparent=True,
                opacity=0.55,
                version="1.3.0",
            )
            onegeo_layer.add_to(m)
            folium.LayerControl(position='topright').add_to(m)
        except Exception:
            pass

    if st.session_state.selected_location:
        marker_color = 'red'
        result_data = st.session_state.get('current_results', None)
        if result_data and 'suitability_percentage' in result_data:
            disp = compute_display_score(result_data)
            pct = disp['display_score']
            if pct >= 80: marker_color = 'green'
            elif pct >= 65: marker_color = 'lightgreen'
            elif pct >= 50: marker_color = 'orange'
            elif pct >= 35: marker_color = 'lightred'
            else: marker_color = 'red'
        folium.Marker(
            center,
            popup=f"<b>🏙️ {location_name}</b><br>Lat: {center[0]:.6f}<br>Lon: {center[1]:.6f}",
            tooltip="🏙️ Candidate Site - Click for details",
            icon=folium.Icon(color=marker_color, icon='home', prefix='fa')
        ).add_to(m)
        if st.session_state.get('show_radius_circle', True):
            radius = params.get('radius', 10000)
            folium.Circle(center, radius=radius, color='#2ecc71', fill=True,
                          fillColor='#2ecc71', fillOpacity=0.1, weight=2,
                          tooltip=f"Assessment radius: {radius}m").add_to(m)
    try:
        Fullscreen(position='topleft').add_to(m)
        MiniMap(toggle_display=True, position='bottomright').add_to(m)
        MousePosition(position='bottomleft', prefix='Coords: ').add_to(m)
    except Exception:
        pass
    map_data = st_folium(m, width=None, height=500, use_container_width=True)
    if map_data and map_data.get('last_clicked'):
        clicked_lat = map_data['last_clicked']['lat']
        clicked_lon = map_data['last_clicked']['lng']
        new_location = Location(lat=clicked_lat, lon=clicked_lon, name=f"{region_label} Location")
        if st.session_state.selected_location is None or \
           abs(st.session_state.selected_location.lat - clicked_lat) > 0.0001 or \
           abs(st.session_state.selected_location.lon - clicked_lon) > 0.0001:
            st.session_state.selected_location = new_location
            st.session_state.nearby_alternatives_cache = None
            st.rerun()


def render_query_interface(params, region):
    region_label = "Borneo" if region == 'borneo' else "West Malaysia"
    st.subheader("💬 Natural Language Query")
    with st.expander("💡 Example Underground City Queries", expanded=False):
        st.markdown(f"""
        **🏙️ Underground City Site Selection ({region_label}):**
        - "Find the best location for an underground city in {region_label}"
        - "Which site has the best geology for underground construction?"
        - "Evaluate this site for subterranean city development"
        - "Compare all candidate sites for underground city"
        """)
    query = st.text_area("Describe what you want to analyse:",
                         placeholder=f"e.g., Find the best location for an underground city in {region_label}",
                         height=100)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        analyse_btn = st.button("🏙️ ANALYSE SITE", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🧹 CLEAR", use_container_width=True)
    if clear_btn:
        st.session_state.current_results = None
        st.session_state.reasoning_log = []
        st.session_state.nearby_alternatives_cache = None
        st.rerun()
    if analyse_btn and st.session_state.selected_location:
        with st.spinner("🧠 HYBRID: INSTANT + USGS + OneGeology + OSM..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            def update_progress(progress, status):
                progress_bar.progress(progress)
                status_text.text(status)
            result = st.session_state.agent.execute_analysis(
                st.session_state.selected_location,
                query if query else f"Evaluate this site for underground city development in {region_label}",
                params, region=region, progress_callback=update_progress)
            st.session_state.analysis_history.append(result)
            st.session_state.reasoning_log = result.steps
            st.session_state.current_results = result.final_result
            st.session_state.nearby_alternatives_cache = None
            progress_bar.empty(); status_text.empty()
            if result.success:
                st.success(f"✅ Analysis complete in {result.total_time:.2f}s"); st.rerun()
            else:
                st.error("❌ Analysis failed. Check reasoning log.")
    elif analyse_btn and not st.session_state.selected_location:
        st.warning(f"Please select a location in {region_label} first!")


def render_reasoning_log():
    st.subheader("🧠 Agent Reasoning (Chain of Thought)")
    if not st.session_state.reasoning_log:
        st.info("Run an underground city site analysis to see the agent's reasoning.")
        return
    for step in st.session_state.reasoning_log:
        icon = "✅" if step.status == "completed" else "❌" if step.status == "failed" else "⏳"
        with st.expander(f"{icon} Step {step.step_number}: {step.name}", expanded=False):
            st.write(f"**Reasoning:** {step.reasoning}")
            if step.execution_time > 0:
                st.write(f"**Execution Time:** {step.execution_time:.3f}s")
            if step.result and step.name.startswith("Execute"):
                st.json(step.result)


def render_nearby_alternatives(rd: Dict, region: str):
    protected = rd.get('protected_area', {})
    is_blocked = protected.get('inside') or rd.get('cave_warning')

    if not is_blocked:
        return

    st.markdown("---")
    st.markdown("### 🔄 Recommended Nearby Alternatives")
    st.caption("Your current site has blockers. Here are the best nearby sites that are NOT blocked.")

    coords = _parse_location_coords(rd)
    if coords is None:
        st.warning("Could not parse location coordinates from result.")
        return
    lat, lon = coords

    cache_key = f"alts_{lat:.4f}_{lon:.4f}_{region}"
    if (st.session_state.nearby_alternatives_cache is not None
            and st.session_state.nearby_alternatives_cache.get('key') == cache_key):
        alternatives = st.session_state.nearby_alternatives_cache['value']
    else:
        alternatives = find_nearby_alternatives(lat, lon, region, max_km=150, max_results=3)
        st.session_state.nearby_alternatives_cache = {'key': cache_key, 'value': alternatives}

    st.markdown(f"""
    <div style="background: rgba(0, 240, 255, 0.05); border: 1px solid rgba(0, 240, 255, 0.2); 
         border-radius: 6px; padding: 8px 12px; margin: 10px 0; 
         font-family: 'Courier New', monospace; font-size: 0.75rem; color: #00f0ff;">
        🔍 Debug: lat={lat:.4f}, lon={lon:.4f}, region={region}, found={len(alternatives)}
    </div>
    """, unsafe_allow_html=True)

    if not alternatives:
        st.warning(
            f"⚠️ No alternatives found within 150km of ({lat:.4f}, {lon:.4f}) even after "
            f"relaxing distance filter. The candidate dataset may not cover this region."
        )
        return

    st.markdown(f"**{len(alternatives)} alternatives found:** (fast static estimate — click Analyse for verified score)")
    for i, alt in enumerate(alternatives, 1):
        st.markdown(f"""
        <div class="alt-site-card">
            <div style="color: #39ff14; font-weight: bold; font-size: 1.1rem; margin-bottom: 6px;">
                {i}. {alt['rating_emoji']} {alt['name']}
            </div>
            <div style="color: #ffffff; font-size: 0.9rem;">
                📍 {alt['distance_km']}km away · 
                🏙️ <b>~{alt['suitability']:.1f}%</b> est. suitability · 
                {alt['protected']} · 
                💰 {alt['investment']} investment
            </div>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    for i, alt in enumerate(alternatives):
        col = [col1, col2, col3][i]
        with col:
            if st.button(f"🎯 Analyse {alt['name'].split(',')[0][:20]}",
                         key=f"alt_btn_{i}",
                         use_container_width=True):
                st.session_state.selected_location = Location(
                    lat=alt['lat'], lon=alt['lon'], name=alt['name'])
                st.session_state.current_results = None
                st.session_state.nearby_alternatives_cache = None
                st.rerun()


def render_data_confidence(confidence):
    pct = confidence['confidence_pct']
    band = confidence['band']
    color = '#39ff14' if band == 'High' else '#ffe84d' if band == 'Moderate' else '#ff2d95'
    live_list = ', '.join(k for k, v in confidence['live_sources'].items() if v) or 'none'
    st.markdown(f"""
    <div class="confidence-bar">
        <div style="color: #00f0ff; font-family: 'Courier New', monospace; font-size: 0.9rem; 
             font-weight: bold; letter-spacing: 2px; margin-bottom: 8px;">
            📡 DATA CONFIDENCE: <span style="color: {color};">{pct}% — {band}</span>
        </div>
        <div style="background: rgba(0,0,0,0.4); height: 8px; border-radius: 4px; overflow: hidden;">
            <div style="background: {color}; height: 100%; width: {pct}%;"></div>
        </div>
        <div style="color: #a0a0c0; font-family: 'Courier New', monospace; 
             font-size: 0.7rem; margin-top: 6px;">
            Live sources: {live_list}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_suitability_metric(rd: Dict):
    disp = compute_display_score(rd)
    margin = compute_score_margin(rd)

    if disp.get('not_feasible'):
        st.markdown(f"""
        <div class="not-feasible-box">
            <div style="color: #ffffff; font-family: 'Courier New', monospace; 
                 font-size: 1.0rem; font-weight: bold; letter-spacing: 2px; margin-bottom: 6px;">
                🚫 NOT FEASIBLE — LEGAL / PROTECTED AREA BLOCKER
            </div>
            <div style="color: #ffe84d; font-family: 'Courier New', monospace; 
                 font-size: 0.85rem;">
                {disp['cap_reason']}
            </div>
            <div style="color: #ffffff; font-family: 'Courier New', monospace; 
                 font-size: 0.75rem; margin-top: 8px;">
                The score below shows geological merit only. Actual development is
                legally restricted unless the protected area status is lifted.
            </div>
        </div>
        """, unsafe_allow_html=True)

    if disp['is_capped']:
        color = '#ff2d95' if disp['display_score'] < 60 else '#ffe84d'
        st.markdown(f"""
        <div class="blocked-score">
            <div style="color: {color}; font-family: 'Courier New', monospace; 
                 font-size: 0.8rem; letter-spacing: 2px; margin-bottom: 8px;">
                🏙️ UNDERGROUND CITY SUITABILITY
            </div>
            <div style="color: {color}; font-family: 'Courier New', monospace; 
                 font-size: 2.5rem; font-weight: 900;">
                {disp['display_score']}% {disp['display_emoji']}
            </div>
            <div style="color: {color}; font-family: 'Courier New', monospace; 
                 font-size: 0.9rem; font-weight: bold; letter-spacing: 2px;">
                {disp['display_rating'].upper()}
            </div>
            <div style="color: #ffffff; font-family: 'Courier New', monospace; 
                 font-size: 0.8rem; margin-top: 8px;">
                Raw geological score: <b>{disp['raw_score']}%</b>
            </div>
            <div style="color: #ff2d95; font-family: 'Courier New', monospace; 
                 font-size: 0.75rem; margin-top: 4px;">
                ⚠️ Capped because: {disp['cap_reason']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.metric("🏙️ Underground City Suitability",
                  f"{rd['suitability_percentage']}%",
                  delta=f"{rd['rating']} {rd['rating_emoji']}")
        st.caption(f"📡 Confidence range: **{margin['lower_bound']}% – {margin['upper_bound']}%** "
                   f"(±{margin['margin']}% at {margin['confidence_pct']}% data confidence)")


def render_cost_summary(rd: Dict):
    cost = estimate_cost_range(rd)
    st.markdown("---")
    st.markdown("### 💰 Estimated Cost")
    if cost['blocked']:
        st.caption(f"🔧 Headline range **includes** mandatory extras (RM {cost['extras_total_billion']:.1f}B). "
                   f"Base construction only: RM {cost['base_mid_billion']:.1f}B.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Low Estimate", f"RM {cost['low_billion']:.1f}B")
    with col2:
        st.metric("Mid Estimate", f"RM {cost['mid_billion']:.1f}B")
    with col3:
        st.metric("High Estimate", f"RM {cost['high_billion']:.1f}B")
    st.caption(f"**Includes:** {', '.join(cost['includes'])}  |  **Excludes:** {', '.join(cost['excludes'])}")


def render_results():
    st.subheader("🏙️ Underground City Site Analysis Results")
    if not st.session_state.analysis_history:
        st.info("No analysis results yet.")
        return
    lr = st.session_state.analysis_history[-1]
    if not lr.final_result:
        st.warning("No results available."); return
    rd = lr.final_result
    if not rd.get('success', False):
        st.error(f"Analysis failed: {rd.get('error', 'Unknown error')}"); return

    if 'suitability_percentage' in rd:
        usgs_badge = "🛰️ USGS Live" if rd.get('used_usgs') else "🌐 OSM"
        onegeo_badge = "🗺️ OneGeology Live" if rd.get('used_onegeology') else "📍 Geographic"
        region_badge = "🏝️ Borneo" if rd.get('region') == 'borneo' else "🏙️ West Malaysia"
        st.success(f"🌐 **HYBRID** · {region_badge} · {usgs_badge} · {onegeo_badge}")

        protected = rd.get('protected_area', {})
        if protected.get('inside'):
            st.markdown(f"""
            <div class="warning-box">
                <div style="color: #ff2d95; font-weight: bold; font-size: 1.1rem; margin-bottom: 6px;">
                    🚫 PROTECTED AREA OVERLAP — HIGH SEVERITY</div>
                <div>{protected['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        elif protected.get('near'):
            st.markdown(f"""
            <div class="warning-box">
                <div style="color: #ffe84d; font-weight: bold; font-size: 1.0rem; margin-bottom: 6px;">
                    ⚠️ NEAR PROTECTED AREA</div>
                <div>{protected['message']}</div>
            </div>
            """, unsafe_allow_html=True)

        if rd.get('cave_warning'):
            st.warning(rd['cave_warning'])

        col_export1, col_export2 = st.columns([3, 1])
        with col_export2:
            with st.expander("📋 Export", expanded=False):
                json_str = json.dumps(rd, indent=2, default=str)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"underground_city_{rd.get('region','analysis')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
                try:
                    coords = _parse_location_coords(rd)
                    if coords:
                        geojson = {
                            "type": "FeatureCollection",
                            "features": [{
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [coords[1], coords[0]]
                                },
                                "properties": {k: v for k, v in rd.items()
                                               if k not in ('details', 'scores', 'data_source_details', 'karst_info')}
                            }]
                        }
                        st.download_button(
                            label="🗺️ Download GeoJSON",
                            data=json.dumps(geojson, indent=2, default=str),
                            file_name=f"underground_city_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
                            mime="application/geo+json",
                            use_container_width=True
                        )
                except Exception:
                    pass
                if st.button("📋 Copy to Clipboard", use_container_width=True, key="copy_json_btn"):
                    st.code(json_str, language="json")
                    st.caption("✅ Select all and copy the JSON above")

        if rd.get('penalty_applied', 0) > 0:
            with st.expander(f"⚠️ Score Penalty Applied: -{rd['penalty_applied']}%"):
                st.write(f"**Base score:** {rd.get('base_percentage', 0)}%")
                st.write(f"**Penalty:** -{rd['penalty_applied']}%")
                st.write("**Reasons:**")
                for r in rd.get('penalty_reasons', []):
                    st.warning(r)
                st.write(f"**Final score:** {rd['suitability_percentage']}%")

        if 'data_source_details' in rd:
            with st.expander("📊 Data Sources Used"):
                for d in rd['data_source_details']:
                    if '🌐' in d: st.success(f"🌐 {d}")
                    elif 'USGS' in d: st.success(f"🛰️ {d}")
                    elif 'OneGeology' in d: st.success(f"🗺️ {d}")
                    elif 'Geographic' in d: st.info(f"📍 {d}")
                    elif 'Fallback' in d: st.warning(f"⚠️ {d}")
                    elif 'OSM' in d: st.success(f"🟢 {d}")
                    else: st.success(f"✅ {d}")

        if 'data_confidence' in rd:
            render_data_confidence(rd['data_confidence'])

        render_suitability_metric(rd)

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Elevation", f"{rd.get('elevation_m', 0):.0f}m")
        with c2: st.metric("Bedrock Depth", f"{rd.get('bedrock_depth_m', 0):.0f}m")
        with c3: st.metric("Water Table", f"{rd.get('water_table_depth_m', 0):.0f}m")

        render_cost_summary(rd)

        st.write("---")
        st.write("**Detailed Scoring Breakdown:**")
        details = rd.get('details', {}); scores = rd.get('scores', {})
        score_data = []
        for k, d in details.items():
            w = d.get('weight', 0); sc = scores.get(k, 0)
            src = d.get('source', 'Unknown')
            if 'USGS' in src: emoji = '🛰️'
            elif 'Geographic' in src: emoji = '📍'
            elif 'OSM' in src: emoji = '🟢'
            elif 'Live' in src: emoji = '✅'
            elif 'Fallback' in src: emoji = '⚠️'
            elif '🗿' in src: emoji = '🗿'
            else: emoji = 'ℹ️'
            display_key = k.replace('_', ' ').title()
            if 'Bedrock' in display_key: display_key = '🪨 ' + display_key
            elif 'Water Table' in display_key: display_key = '💧 ' + display_key
            elif 'Seismic' in display_key: display_key = '🌋 ' + display_key
            elif 'Geology' in display_key: display_key = '🗿 ' + display_key
            elif 'Slope' in display_key: display_key = '⛰️ ' + display_key
            elif 'Fault' in display_key: display_key = '🌐 ' + display_key

            src_clean = src
            for lead in ('🗿', '⚠️', '🛰️', '📍', '✅', '🌐', '🗺️', 'ℹ️', '🟢'):
                if src_clean.startswith(lead):
                    src_clean = src_clean[len(lead):].lstrip()
                    break

            score_data.append({
                'Criteria': display_key, 'Score': f"{sc:.1f}/5",
                'Value': d.get('value', 'N/A'), 'Weight': f"{w*100:.0f}%",
                'Weighted': f"{sc*w:.2f}",
                'Source': f"{emoji} {src_clean[:60]}{'...' if len(src_clean) > 60 else ''}"
            })
        st.dataframe(pd.DataFrame(score_data), use_container_width=True, hide_index=True)
        chart = pd.DataFrame([{'Criteria': r['Criteria'], 'Score': float(r['Score'].split('/')[0])}
                              for r in score_data])
        st.bar_chart(chart.set_index('Criteria'))

        if 'slope_deg' in rd:
            st.write("---")
            st.write("**⛰️ Terrain & Fault Analysis**")
            colA, colB = st.columns(2)
            with colA:
                st.metric("Slope", f"{rd['slope_deg']}°", delta=rd['slope_risk'])
                st.caption(f"Source: {rd['slope_source']}")
            with colB:
                fault = rd.get('nearest_fault', {})
                st.metric("Nearest Fault", f"{fault.get('distance_km', 0)}km",
                          delta=fault.get('name', 'Unknown'))
                st.caption(f"Activity: {fault.get('activity', 'Unknown')} · Type: {fault.get('type', 'Unknown')}")

        if 'groundwater' in rd:
            gw = rd['groundwater']
            st.write("---")
            st.write("**💧 Groundwater Quality**")
            colA, colB, colC = st.columns(3)
            colA.metric("Aquifer Type", gw['type'][:30])
            colB.metric("Salinity", gw['salinity'])
            colC.metric("Score", f"{gw['score']}/5")
            st.caption(gw['note'])

        _render_sensitivity_analysis(rd)

        render_nearby_alternatives(rd, rd.get('region', 'borneo'))

        st.write("---")
        st.write("**📋 Detailed Recommendation Strategy**")
        recs = generate_recommendation_strategy(rd)
        risk = recs.get('risk_level', 'Unknown')
        risk_color = ('#ff2d95' if risk in ('High', 'Very High')
                      else '#39ff14' if risk == 'Low' else '#ffe84d')
        st.markdown(f"""
        <div class="recommendation-container">
            <div class="recommendation-title">🎯 Overall Feasibility</div>
            <div style="color: #ffffff; font-family: 'Courier New', monospace; font-size: 1.1rem; padding: 10px;">
                {recs.get('overall_feasibility', 'Assessment not available')}
            </div>
            <div style="display: flex; gap: 20px; margin-top: 10px; flex-wrap: wrap;">
                <div style="color: #8080a0; border: 1px solid rgba(0,240,255,0.1); padding: 8px 15px; border-radius: 8px;">
                    💰 Investment: <span style="color: #00f0ff; font-weight: bold;">{recs.get('investment_required', 'Unknown')}</span></div>
                <div style="color: #8080a0; border: 1px solid rgba(255,45,149,0.3); padding: 8px 15px; border-radius: 8px;">
                    ⚠️ Risk: <span style="color: {risk_color}; font-weight: bold;">{risk}</span></div>
                <div style="color: #8080a0; border: 1px solid rgba(255,45,149,0.3); padding: 8px 15px; border-radius: 8px;">
                    🚨 Critical: <span style="color: #ff2d95; font-weight: bold;">{recs.get('critical_action_count', 0)}</span></div>
            </div>
            <div style="display: flex; gap: 20px; margin-top: 10px; flex-wrap: wrap;">
                <div style="color: #8080a0; border: 1px solid rgba(0,240,255,0.1); padding: 8px 15px; border-radius: 8px;">
                    ⏱️ Immediate: <span style="color: #39ff14;">{recs['timeline_summary']['immediate']}</span></div>
                <div style="color: #8080a0; border: 1px solid rgba(0,240,255,0.1); padding: 8px 15px; border-radius: 8px;">
                    ⏱️ Short: <span style="color: #ffe84d;">{recs['timeline_summary']['short_term']}</span></div>
                <div style="color: #8080a0; border: 1px solid rgba(0,240,255,0.1); padding: 8px 15px; border-radius: 8px;">
                    ⏱️ Long: <span style="color: #b026ff;">{recs['timeline_summary']['long_term']}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        for bucket, title in [
            ('immediate_actions', '🔴 IMMEDIATE ACTIONS (0-6 Months)'),
            ('short_term_actions', '🟡 SHORT-TERM ACTIONS (6-18 Months)'),
            ('long_term_actions', '🟢 LONG-TERM ACTIONS (18-36 Months)')
        ]:
            if recs[bucket]:
                st.markdown(f"""<div class="recommendation-container">
                    <div class="recommendation-title">{title}</div>""", unsafe_allow_html=True)
                for a in recs[bucket]:
                    st.markdown(f"""
                    <div class="recommendation-item">
                        <span class="icon">{a.get('priority', '')}</span>
                        {a['text']}
                        <span style="float: right; color: #8080a0; font-size: 0.8rem;">{a.get('cost', '')}</span>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


def render_comparison_mode(region):
    region_label = "Borneo" if region == 'borneo' else "West Malaysia"
    candidates = BORNEO_UNDERGROUND_CITY_CANDIDATES if region == 'borneo' else WEST_MALAYSIA_UNDERGROUND_CITY_CANDIDATES

    st.subheader(f"🔄 {region_label} Site Comparison Dashboard")
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("⬅️ BACK TO SINGLE SITE", key="back_from_comparison", use_container_width=True):
            st.session_state.comparison_mode = False
            st.rerun()
    with st.spinner(f"Analysing all {region_label} candidate sites..."):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i, (name, coords) in enumerate(candidates.items()):
            status_text.text(f"Analysing: {name}")
            progress_bar.progress((i + 1) / len(candidates))
            location = Location(lat=coords[0], lon=coords[1], name=name)
            params = {'radius': 10000}
            try:
                strategy = StrategySelector.get_strategy('underground_city', region)
                result = strategy.analyse(location, params)
                if result.get('success'):
                    disp = compute_display_score(result)
                    results.append({
                        'Site': name,
                        'Suitability %': disp['display_score'],
                        'Raw %': result['suitability_percentage'],
                        'Rating': f"{disp['display_rating']} {disp['display_emoji']}",
                        'Elevation (m)': result.get('elevation_m', 0),
                        'Bedrock (m)': result.get('bedrock_depth_m', 0),
                        'Water Table (m)': result.get('water_table_depth_m', 0),
                        'Seismic Risk': result.get('seismic_risk', 'Unknown'),
                        'Flood Risk': result.get('flood_risk', 'Unknown'),
                        'Protected': '🚫' if result.get('protected_area', {}).get('inside') else '✅',
                        'Slope°': result.get('slope_deg', 0),
                        'Investment': result.get('investment_band', 'Unknown'),
                        'Confidence': f"{result.get('data_confidence', {}).get('confidence_pct', 0)}%",
                        'Capped': '⚠️' if disp['is_capped'] else '',
                        'Method': ('🛰️ USGS + 🗺️ OneGeo' if result.get('used_usgs') and result.get('used_onegeology')
                                   else '🛰️ USGS' if result.get('used_usgs')
                                   else '📍 Geographic'),
                        'Data': result
                    })
            except Exception as e:
                results.append({
                    'Site': name, 'Suitability %': 0, 'Raw %': 0, 'Rating': 'Error',
                    'Elevation (m)': 0, 'Bedrock (m)': 0, 'Water Table (m)': 0,
                    'Seismic Risk': 'Unknown', 'Flood Risk': 'Unknown',
                    'Protected': '?', 'Slope°': 0, 'Investment': '?', 'Confidence': '0%',
                    'Capped': '', 'Method': 'Error', 'Data': None
                })
        progress_bar.empty(); status_text.empty()
        if results:
            df = pd.DataFrame(results)
            df_sorted = df.sort_values('Suitability %', ascending=False)
            st.write(f"**📊 Comparison of {len(results)} Candidate Sites**")
            top_site = df_sorted.iloc[0]
            st.success(f"🏙️ **Top Recommended Site: {top_site['Site']}** ({top_site['Suitability %']:.1f}%)")

            display_cols = ['Site', 'Suitability %', 'Raw %', 'Rating', 'Elevation (m)', 'Bedrock (m)',
                          'Water Table (m)', 'Seismic Risk', 'Flood Risk', 'Protected',
                          'Slope°', 'Investment', 'Confidence', 'Capped', 'Method']
            st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)

            st.markdown("### 🎯 Multi-Metric Radar (Top 5 Sites)")
            top5 = df_sorted.head(5).to_dict('records')
            sites_with_data = [r for r in top5 if r.get('Data') is not None]
            if len(sites_with_data) >= 2:
                radar_data = [{'name': r['Site'], 'scores': r['Data'].get('scores', {})} for r in sites_with_data]
                fig = build_radar_chart(radar_data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Need at least 2 valid sites for radar chart.")

            chart_data = df_sorted[['Site', 'Suitability %']].set_index('Site')
            st.bar_chart(chart_data)

            st.session_state.candidate_scores = {row['Site']: row['Suitability %'] for _, row in df.iterrows()}

            st.write("---")
            st.write("**🗺️ Site Map with Suitability Scores**")
            basemap_choice = st.session_state.get('basemap_choice', 'OpenStreetMap')
            tiles_url = get_tiles_for_basemap(basemap_choice)
            if region == 'borneo':
                map_center = [5.0, 117.0]; map_zoom = 6
            else:
                map_center = [4.2, 102.0]; map_zoom = 6
            if basemap_choice == "Satellite":
                m = folium.Map(location=map_center, zoom_start=map_zoom, tiles=tiles_url, attr='Esri World Imagery')
            else:
                m = folium.Map(location=map_center, zoom_start=map_zoom, tiles="OpenStreetMap")
            for _, row in df.iterrows():
                name = row['Site']; score = row['Suitability %']
                if score >= 80: color = 'green'
                elif score >= 65: color = 'lightgreen'
                elif score >= 50: color = 'orange'
                elif score >= 35: color = 'lightred'
                else: color = 'red'
                coords = candidates.get(name, (0, 0))
                folium.Marker(coords, popup=f"<b>{name}</b><br>Suitability: {score:.1f}%",
                              tooltip=f"{name}: {score:.1f}%",
                              icon=folium.Icon(color=color, icon='home', prefix='fa')).add_to(m)
            try: Fullscreen(position='topleft').add_to(m)
            except Exception: pass
            st_folium(m, width=None, height=400, use_container_width=True)
            selected_site = st.selectbox("Select a site for detailed analysis:", df_sorted['Site'].tolist())
            if selected_site:
                coords = candidates[selected_site]
                st.session_state.selected_location = Location(lat=coords[0], lon=coords[1], name=selected_site)
                st.session_state.comparison_mode = False
                st.session_state.nearby_alternatives_cache = None
                st.rerun()


def render_multi_ranking_mode(region):
    region_label = "Borneo" if region == 'borneo' else "West Malaysia"
    candidates = BORNEO_UNDERGROUND_CITY_CANDIDATES if region == 'borneo' else WEST_MALAYSIA_UNDERGROUND_CITY_CANDIDATES

    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(f"📊 {region_label} Multi-Site Ranking Table")
        st.caption("Select 2-15 sites to analyze and rank side-by-side")
    with col2:
        if st.button("⬅️ BACK", key="back_from_multi_ranking", use_container_width=True):
            st.session_state.multi_ranking_mode = False
            st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Step 1: Select Sites to Rank")

    col_a, col_b, col_c = st.columns(3)
    all_sites = list(candidates.keys())
    with col_a:
        if st.button("✅ Select All", use_container_width=True, key="select_all_sites"):
            st.session_state.multi_ranking_selected = all_sites
            st.rerun()
    with col_b:
        if st.button("🔝 Top 5 Suggested", use_container_width=True, key="select_top5"):
            top_defaults = all_sites[:5] if len(all_sites) >= 5 else all_sites
            st.session_state.multi_ranking_selected = top_defaults
            st.rerun()
    with col_c:
        if st.button("🧹 Clear Selection", use_container_width=True, key="clear_selection"):
            st.session_state.multi_ranking_selected = []
            st.rerun()

    st.markdown(f"**Selected: {len(st.session_state.multi_ranking_selected)} / {len(all_sites)} sites**")
    with st.expander(f"📝 Choose Sites ({len(all_sites)} available)", expanded=True):
        cols = st.columns(3)
        new_selection = []
        for i, site in enumerate(all_sites):
            with cols[i % 3]:
                checked = st.checkbox(site, value=(site in st.session_state.multi_ranking_selected), key=f"rank_cb_{i}")
                if checked:
                    new_selection.append(site)
        st.session_state.multi_ranking_selected = new_selection

    st.markdown("---")

    selected_sites = st.session_state.multi_ranking_selected
    if len(selected_sites) < 2:
        st.warning(f"⚠️ Please select at least 2 sites to rank. Currently selected: {len(selected_sites)}")
        return

    st.markdown(f"### 📊 Step 2: Analyze {len(selected_sites)} Sites")

    if st.button(f"🚀 RANK {len(selected_sites)} SITES", type="primary", use_container_width=True, key="run_multi_ranking"):
        with st.spinner(f"Analysing {len(selected_sites)} sites..."):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            for i, site_name in enumerate(selected_sites):
                status_text.text(f"Analysing {i+1}/{len(selected_sites)}: {site_name}")
                progress_bar.progress((i + 1) / len(selected_sites))
                coords = candidates.get(site_name, (0, 0))
                location = Location(lat=coords[0], lon=coords[1], name=site_name)
                params = {'radius': 10000}
                try:
                    strategy = StrategySelector.get_strategy('underground_city', region)
                    result = strategy.analyse(location, params)
                    if result.get('success'):
                        disp = compute_display_score(result)
                        results.append({
                            'Site': site_name,
                            'Suitability %': disp['display_score'],
                            'Raw %': result['suitability_percentage'],
                            'Rating': f"{disp['display_rating']} {disp['display_emoji']}",
                            'Elevation (m)': result.get('elevation_m', 0),
                            'Bedrock (m)': result.get('bedrock_depth_m', 0),
                            'Water Table (m)': result.get('water_table_depth_m', 0),
                            'Seismic': result.get('seismic_risk_emoji', '⚪') + ' ' + result.get('seismic_risk', 'Unknown'),
                            'Flood Risk': result.get('flood_risk', 'Unknown'),
                            'Protected': '🚫' if result.get('protected_area', {}).get('inside') else '✅',
                            'Slope°': result.get('slope_deg', 0),
                            'Investment': result.get('investment_band', 'Unknown'),
                            'Confidence': f"{result.get('data_confidence', {}).get('confidence_pct', 0)}%",
                            'Capped': '⚠️' if disp['is_capped'] else '',
                            'Data': result
                        })
                except Exception as e:
                    st.error(f"Error analysing {site_name}: {e}")
            progress_bar.empty()
            status_text.empty()
            st.session_state.multi_ranking_results = results

    if 'multi_ranking_results' in st.session_state and st.session_state.multi_ranking_results:
        results = st.session_state.multi_ranking_results
        df = pd.DataFrame(results)
        df_display = df.drop(columns=['Data'], errors='ignore')
        df_sorted = df_display.sort_values('Suitability %', ascending=False).reset_index(drop=True)

        medals = ['🥇', '🥈', '🥉']
        rank_col = []
        for i in range(len(df_sorted)):
            rank_col.append(f"{medals[i]} #{i+1}" if i < 3 else f"#{i+1}")
        df_sorted.insert(0, 'Rank', rank_col)

        st.markdown("---")
        st.markdown("### 🏆 Ranking Results")

        winner = df_sorted.iloc[0]
        st.success(f"🥇 **WINNER: {winner['Site']}** — Suitability: **{winner['Suitability %']:.1f}%** ({winner['Rating']})")

        winner_data = None
        for r in results:
            if r['Site'] == winner['Site']:
                winner_data = r.get('Data')
                break
        if winner_data and winner_data.get('protected_area', {}).get('inside'):
            st.error(f"🚫 WARNING: Winner overlaps with protected area: {winner_data['protected_area'].get('name', 'Unknown')}")

        st.dataframe(df_sorted, use_container_width=True, hide_index=True)

        st.markdown("### 🎯 Multi-Metric Radar (Top 5)")
        top5_results = []
        for _, row in df_sorted.head(5).iterrows():
            for r in results:
                if r['Site'] == row['Site'] and r.get('Data'):
                    top5_results.append({'name': r['Site'], 'scores': r['Data'].get('scores', {})})
                    break
        if len(top5_results) >= 2:
            fig = build_radar_chart(top5_results)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📈 Suitability Comparison")
        chart_data = df_sorted[['Site', 'Suitability %']].set_index('Site')
        st.bar_chart(chart_data)

        st.markdown("### 📥 Export Ranking")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv = df_sorted.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{region}_multi_ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_dl2:
            md_lines = [f"# {region_label} Multi-Site Ranking\n"]
            md_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            md_lines.append("| Rank | Site | Suitability % | Rating | Elevation | Bedrock | Water Table | Seismic | Protected |\n")
            md_lines.append("|------|------|---------------|--------|-----------|---------|-------------|---------|-----------|\n")
            for _, row in df_sorted.iterrows():
                md_lines.append(f"| {row['Rank']} | {row['Site']} | {row['Suitability %']} | {row['Rating']} | {row['Elevation (m)']} | {row['Bedrock (m)']} | {row['Water Table (m)']} | {row['Seismic']} | {row['Protected']} |\n")
            st.download_button(
                label="📥 Download Markdown",
                data="".join(md_lines),
                file_name=f"{region}_multi_ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )

        st.markdown("### 🗺️ Ranked Sites Map")
        basemap_choice = st.session_state.get('basemap_choice', 'OpenStreetMap')
        tiles_url = get_tiles_for_basemap(basemap_choice)
        if region == 'borneo':
            map_center = [5.0, 117.0]; map_zoom = 6
        else:
            map_center = [4.2, 102.0]; map_zoom = 6
        if basemap_choice == "Satellite":
            m = folium.Map(location=map_center, zoom_start=map_zoom, tiles=tiles_url, attr='Esri World Imagery')
        else:
            m = folium.Map(location=map_center, zoom_start=map_zoom, tiles="OpenStreetMap")
        for _, row in df_sorted.iterrows():
            name = row['Site']; score = row['Suitability %']
            if score >= 80: color = 'green'
            elif score >= 65: color = 'lightgreen'
            elif score >= 50: color = 'orange'
            elif score >= 35: color = 'lightred'
            else: color = 'red'
            coords = candidates.get(name, (0, 0))
            folium.Marker(
                coords,
                popup=f"<b>{row['Rank']} {name}</b><br>Suitability: {score:.1f}%",
                tooltip=f"{row['Rank']} {name}: {score:.1f}%",
                icon=folium.Icon(color=color, icon='trophy' if row['Rank'].startswith('🥇') else 'home', prefix='fa')
            ).add_to(m)
        try: Fullscreen(position='topleft').add_to(m)
        except Exception: pass
        st_folium(m, width=None, height=450, use_container_width=True)

        st.markdown("---")
        if st.button(f"🎯 Analyze Winner: {winner['Site']}", type="primary", use_container_width=True, key="pick_winner_btn"):
            coords = candidates[winner['Site']]
            st.session_state.selected_location = Location(lat=coords[0], lon=coords[1], name=winner['Site'])
            st.session_state.multi_ranking_mode = False
            st.session_state.multi_ranking_results = None
            st.session_state.nearby_alternatives_cache = None
            st.rerun()


def render_enhanced_results(complete_plan: Dict):
    st.subheader("🏙️ Complete Underground City Development Plan")
    tabs = st.tabs([
        "📊 Overview", "💰 Phase 2: Infrastructure", "🏗️ Phase 3: Construction",
        "👥 Phase 4: Public", "🌍 Phase 5: Global",
        "🌦️ Climate Context",
    ])
    with tabs[0]:
        site = complete_plan['phase_1_site_selection']['site_data']
        phase1 = complete_plan['phase_1_site_selection']
        disp = compute_display_score(site)
        cost_range = estimate_cost_range(site)
        not_feasible = disp.get('not_feasible', False)

        if not_feasible:
            st.markdown(f"""
            <div style="background: rgba(255, 45, 149, 0.25); border: 2px solid #ff2d95;
                 border-radius: 10px; padding: 15px; margin: 10px 0;">
                <div style="color: #ff2d95; font-family: 'Courier New', monospace; 
                     font-size: 1.1rem; font-weight: bold; letter-spacing: 2px;">
                    🚫 NOT FEASIBLE — DEVELOPMENT BLOCKED
                </div>
                <div style="color: #ffe84d; font-family: 'Courier New', monospace; 
                     font-size: 0.85rem; margin-top: 6px;">
                    {disp.get('cap_reason', 'Protected area overlap')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Site Suitability", f"{disp['display_score']:.1f}% {disp['display_emoji']}")
            if disp['is_capped']:
                st.caption(f"Raw geological: {disp['raw_score']:.1f}%")
        with col2:
            st.metric("Population Capacity", "50,000+")
        with col3:
            st.metric("Total Cost", f"RM {cost_range['mid_billion']:.1f}B")
            if cost_range['blocked']:
                st.caption(f"Base: RM {cost_range['base_mid_billion']:.1f}B + extras RM {cost_range['extras_total_billion']:.1f}B")
        with col4:
            total_years = phase1.get('total_years', 0)
            total_months = phase1.get('total_months', 0)
            if total_years > 0:
                st.metric("Completion Time", f"~{total_years:.1f} years")
                st.caption(f"{total_months:.0f} months (complexity ×{phase1.get('elevation_complexity_factor', 1.0):.2f})")
            else:
                st.metric("Completion Time", "TBD")

        if not_feasible:
            st.error("⛔ Development is legally restricted — plan shown for reference only.")
        else:
            st.info("✅ All phases ready for development.")
    with tabs[1]:
        cost_data = complete_plan['phase_2_infrastructure']['cost_estimate']
        transport_data = complete_plan['phase_2_infrastructure']['transport_plan']
        utility_data = complete_plan['phase_2_infrastructure']['utility_plan']
        st.subheader("💰 Cost Estimation")
        col1, col2, col3 = st.columns(3)
        with col1:
            site = complete_plan['phase_1_site_selection']['site_data']
            cost_range = estimate_cost_range(site)
            st.metric("Total Cost (headline)", f"RM {cost_range['mid_billion']:.2f}B")
            st.caption(f"Base construction: RM {cost_data['total_cost_billions']:.2f}B")
        with col2: st.metric("Per SQM Cost", f"RM {cost_data['per_sqm_cost']:,.0f}")
        with col3: st.metric("Rock Type", cost_data['rock_type'].replace('_', ' ').title())
        st.subheader("🚆 Transport Network")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Primary Transport", transport_data['primary_transport'].replace('_', ' ').title())
        with col2: st.metric("Network Length", f"{transport_data['network_length_km']:.1f} km")
        with col3: st.metric("Stations", transport_data['stations'])
        st.subheader("⚡ Utility Systems")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Water", f"{utility_data['water']['daily_need_liters']:,} L/day")
        with col2: st.metric("Power", f"{utility_data['power']['peak_demand_mw']:.1f} MW")
        with col3: st.metric("Ventilation", f"{utility_data['ventilation']['airflow_m3h']:,} m³/h")
    with tabs[2]:
        sim_data = complete_plan['phase_3_construction']['simulation']
        resource_data = complete_plan['phase_3_construction']['resource_optimization']
        st.subheader("🏗️ Construction Timeline")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Duration", sim_data.get('total_months_human',
                                                       f"{sim_data['total_months']:.0f} months"))
            st.caption(f"Elevation complexity: ×{sim_data.get('elevation_complexity_factor', 1.0):.2f}")
        with col2: st.metric("Completion Probability", f"{sim_data['completion_probability']:.1f}%")
        with col3: st.metric("Critical Path", " → ".join([s.replace('_', ' ').title() for s in sim_data['critical_path'][:2]]))
        st.subheader("📦 Resource Optimization")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Optimization Score", f"{resource_data['optimization_score']}%")
        with col2: st.metric("Waste Reduction", f"{resource_data['waste_reduction']}%")
        with col3: st.metric("Cost Savings", f"{resource_data['cost_savings_percentage']}%")
    with tabs[3]:
        vr_data = complete_plan['phase_4_public']['vr_walkthrough']
        consult_data = complete_plan['phase_4_public']['consultation']
        tourism_data = complete_plan['phase_4_public']['tourism']
        st.subheader("🕶️ VR Walkthrough")
        for scene in vr_data['scenes']:
            st.write(f"**📍 {scene['name']}**: {scene['description']}")
        st.subheader("🗳️ Public Consultation")
        for i, q in enumerate(consult_data['survey_questions'][:2]):
            st.write(f"**Q{i+1}:** {q['question']}")
        st.subheader("🏨 Tourism")
        visitor_total = sum(a['visitors_per_year'] for a in tourism_data['attractions'])
        col1, col2 = st.columns(2)
        with col1: st.metric("Annual Visitors", f"{visitor_total:,}")
        with col2: st.metric("Jobs Created", tourism_data['jobs_created'])
    with tabs[4]:
        mars_data = complete_plan['phase_5_global']['mars_adaptation']
        climate_data = complete_plan['phase_5_global']['climate_resilience']
        swarm_data = complete_plan['phase_5_global']['ai_swarm']
        st.subheader("🚀 Mars Adaptation")
        for key, value in list(mars_data['mars_adaptation'].items())[:5]:
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        st.subheader("🌍 Climate Resilience")
        col1, col2 = st.columns(2)
        with col1: st.metric("Resilience Score", f"{climate_data['overall_resilience_score']:.0f}%")
        with col2: st.metric("Climate Refuge Capacity", f"{climate_data['climate_refuge_capacity']:,}")
        st.subheader("🧠 AI Swarm")
        for agent in swarm_data['agents']:
            st.write(f"**{agent['role']}**: {agent['specialty']}")
    with tabs[5]:
        _render_climate_context_tab(complete_plan['phase_1_site_selection']['site_data'])


def render_memory_explorer():
    st.subheader("💾 Memory Explorer")
    tab1, tab2 = st.tabs(["Past Analyses", "Learned Parameters"])
    with tab1:
        all_analyses = st.session_state.agent.memory_repo.get_all_analyses(limit=20)
        if all_analyses:
            st.write(f"**{len(all_analyses)} past analyses stored**")
            for entry in all_analyses:
                query_preview = entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query']
                with st.expander(f"{'✅' if entry['success'] else '❌'} {query_preview}"):
                    st.write(f"**Query:** {entry['query']}")
                    st.write(f"**Success:** {'✅ Yes' if entry['success'] else '❌ No'}")
                    st.write(f"**Execution Time:** {entry['execution_time']:.2f}s")
                    st.write(f"**Timestamp:** {entry['timestamp']}")
        else:
            st.info("No past analyses stored yet.")
    with tab2:
        try:
            conn = sqlite3.connect("malaysia_underground_city_memory.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learned_parameters ORDER BY success_rate DESC")
            rows = cursor.fetchall(); conn.close()
            if rows:
                st.write(f"**{len(rows)} learned parameters**")
                df = pd.DataFrame(rows, columns=['ID', 'Analysis Type', 'Parameter', 'Value',
                                                 'Success Rate', 'Usage Count', 'Last Updated'])
                st.dataframe(df[['Analysis Type', 'Parameter', 'Value', 'Success Rate', 'Usage Count']],
                             use_container_width=True)
            else:
                st.info("No learned parameters yet.")
        except Exception:
            st.info("No learned parameters yet.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title="UndergroundBase", page_icon="🏙️", layout="wide")
    st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)

    region = st.session_state.get('region', 'borneo')
    region_flag = "🇲🇾🏝️" if region == 'borneo' else "🇲🇾🏙️"

    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <div class="main-title">🏙️ UNDERGROUNDBASE</div>
        <div class="subtitle">{region_flag} MALAYSIA · SITE SELECTOR v5.3.1</div>
        <div style="display: flex; justify-content: center; gap: 10px; margin: 10px 0;">
            <span class="phase-badge phase-badge-2">🔧 PHASE 2</span>
            <span class="phase-badge phase-badge-3">🏗️ PHASE 3</span>
            <span class="phase-badge phase-badge-4">👥 PHASE 4</span>
            <span class="phase-badge phase-badge-5">🌍 PHASE 5</span>
        </div>
        <div class="cyber-divider"></div>
        <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem; 
             letter-spacing: 4px; margin-top: 5px;">
            ⚡ HYBRID · 🛰️ USGS LIVE · 🗺️ ONEGEOLOGY LIVE · 🟢 OSM LIVE · ⛰️ SLOPE · 🌐 FAULTS · 🚫 PROTECTED · 📡 CONFIDENCE · 🧪 SENSITIVITY · 🌦️ CLIMATE · 🔍 SEARCH ⚡
        </div>
    </div>
    """, unsafe_allow_html=True)

    init_session_state()

    region = render_region_switcher()

    if region == 'borneo':
        total_locations = len(SABAH_LOCATIONS) + len(SARAWAK_LOCATIONS)
        total_candidates = len(BORNEO_UNDERGROUND_CITY_CANDIDATES)
        region_desc = "SABAH · SARAWAK · PHASES 2-5"
    else:
        total_locations = len(WEST_MALAYSIA_LOCATIONS)
        total_candidates = len(WEST_MALAYSIA_UNDERGROUND_CITY_CANDIDATES)
        region_desc = "PENINSULAR MALAYSIA · PHASES 2-5"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; padding: 8px 15px; 
         border: 1px solid rgba(0, 240, 255, 0.1); border-radius: 8px; 
         background: rgba(0, 240, 255, 0.03); margin-bottom: 15px;">
        <span style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem; 
             letter-spacing: 1px;">📍 LOCATIONS LOADED</span>
        <span style="color: #00f0ff; font-family: 'Courier New', monospace; font-size: 0.8rem; 
             font-weight: bold; letter-spacing: 1px;">{total_locations} (+ {total_candidates} candidates)</span>
        <span style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem; 
             letter-spacing: 1px;">{region_desc}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('multi_ranking_mode', False):
        render_multi_ranking_mode(region)
        return

    if st.session_state.get('comparison_mode', False):
        render_comparison_mode(region)
        return

    params = render_sidebar(region)
    selected_phase = render_phase_selector()

    col1, col2 = st.columns([1.5, 1])
    with col1:
        render_map(params, region)
        render_query_interface(params, region)
    with col2:
        if st.session_state.selected_location:
            name = st.session_state.selected_location.name or "Location"
            st.markdown(f"""
            <div style="padding: 10px 15px; border: 1px solid rgba(0, 240, 255, 0.15);
                 border-radius: 8px; background: rgba(0, 240, 255, 0.03); margin-bottom: 15px;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem; 
                     letter-spacing: 1px;">SELECTED LOCATION</div>
                <div style="color: #00f0ff; font-family: 'Courier New', monospace; font-size: 0.9rem;">
                    {name}</div>
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem; 
                     letter-spacing: 1px;">{st.session_state.selected_location.lat:.4f}, {st.session_state.selected_location.lon:.4f}</div>
            </div>
            """, unsafe_allow_html=True)
        render_reasoning_log()

    st.divider()

    if st.session_state.current_results:
        result_data = st.session_state.current_results
        col1, col2 = st.columns(2)
        with col1:
            render_results()
        with col2:
            render_memory_explorer()
        if selected_phase == 'all' and 'suitability_percentage' in result_data:
            st.write("---")
            with st.spinner("🧠 Generating complete development plan..."):
                developer = EnhancedUndergroundCityDeveloper()
                complete_plan = developer.develop_complete_city(result_data)
                render_enhanced_results(complete_plan)
    else:
        render_memory_explorer()

    st.markdown("""
    <div class="cyber-divider"></div>
    <div style="text-align: center; padding: 15px 0; color: #333; font-family: 'Courier New', monospace; 
         font-size: 0.6rem; letter-spacing: 2px;">
        <span style="color: #00f0ff;">[</span> 
        UNDERGROUNDBASEX v5.3.1 · UNIVERSAL SEARCH · ZERO DOWNLOADS
        <span style="color: #00f0ff;">]</span>
    </div>
    <div style="text-align: center; padding: 15px 0;">
        <p style="color: #8080a0; font-size: 0.8rem; letter-spacing: 2px;">☕ SUPPORT THIS PROJECT</p>
        <a href="https://buymeacoffee.com/stargazex" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" 
                 alt="Buy Me A Coffee" style="height: 60px;width: 217px;">
        </a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
