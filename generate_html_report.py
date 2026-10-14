import json
import html
from collections import defaultdict

def build_html_report():
    with open('all_signup_pages.json') as f:
        pages = json.load(f)

    all_slot_items = {}
    for p in pages:
        items = p.get('signUpSlotItems', {})
        if isinstance(items, dict):
            all_slot_items.update(items)

    categorized_data = []

    for sid, data in all_slot_items.items():
        s = data.get('slot', {})
        it = data.get('item', {})
        rem = data.get('remaining', 0)
        taken = data.get('qtyTaken', 0)
        role_name = it.get('item', '').strip()
        comment = it.get('comment', '').strip()
        date_str = s.get('startdate', '')
        weekday = s.get('weekdayDisplay', '')
        time_str = s.get('timeDisplay') or s.get('altTimeDisplay') or (s.get('starttime','') + ' - ' + s.get('endtime',''))
        location = s.get('location', '')
        
        # Categorize
        is_dressing_room = 'Dressing Room' in role_name or 'Dressing Room Manager' in role_name
        is_props = 'Prop' in role_name
        is_security = 'Security' in role_name or 'Bouncer' in role_name
        is_beverage = 'Beverage' in role_name
        is_boutique = 'Boutique' in role_name
        is_usher = 'Usher' in role_name
        is_ticket = 'Ticket Scanner' in role_name
        is_cleanup = 'Clean Up' in role_name
        is_dropoff = 'Drop-off' in role_name
        is_runner = 'Supervisor & Runner' in role_name
        is_braider = 'Hair Braider' in role_name
        is_wardrobe = 'Wardrobe' in role_name
        is_setup = 'Set up' in role_name
        is_backstage_coord = 'Backstage Coordinator' in role_name

        tags = []
        male_fit = "no" # 'top', 'good', 'neutral', 'no'
        female_fit = "no"
        category = ""
        conflict_rating = ""
        rationale = ""

        if is_ticket:
            tags.extend(['Male Optimal', 'Female Optimal', 'Watch Show', 'Front of House'])
            male_fit = 'top'
            female_fit = 'top'
            category = 'front_of_house'
            conflict_rating = 'None (Ends at Curtain)'
            rationale = 'Shift ends right as performance begins (1:15pm or 5:15pm). Scan tickets, then take your seat and watch the entire show without missing a single moment.'
        elif is_boutique:
            tags.extend(['Male Optimal', 'Female Optimal', 'Watch Show', 'Front of House'])
            male_fit = 'top'
            female_fit = 'top'
            category = 'front_of_house'
            conflict_rating = 'None (Official Note: May Watch Show)'
            rationale = 'Official SignUpGenius permission: You may attend the performance! You work sales before the show, during intermission, and briefly post-show.'
        elif is_cleanup:
            tags.extend(['Male Optimal', 'Female Optimal', 'Zero Conflict', 'Post-Show Strike'])
            male_fit = 'top'
            female_fit = 'top'
            category = 'zero_conflict'
            conflict_rating = 'Zero Conflict (After All Shows)'
            rationale = 'Sunday 7:00pm–8:30pm after all 4 shows wrap up! You enjoy the entire weekend with your dancer, then return for 90 mins of breakdown (counts as 2 hrs).'
        elif is_dropoff:
            tags.extend(['Male Friendly', 'Female Friendly', 'Rehearsal Pre-Show', 'Performer Support'])
            male_fit = 'good'
            female_fit = 'good'
            category = 'rehearsal_support'
            conflict_rating = 'None (Pre-Rehearsal Check-In)'
            rationale = 'Stationed at check-in during tech dress rehearsals. Greet your dancer, help them settle in, and finish before the evening run starts.'
        elif is_usher:
            tags.extend(['Male Friendly', 'Female Friendly', 'Watch Show (Standing)', 'Auditorium'])
            male_fit = 'good'
            female_fit = 'good'
            category = 'front_of_house'
            conflict_rating = 'Low (Option to Watch from Back of Theater)'
            rationale = 'Direct patrons to seats before curtain, then stand and watch the show from the back of the auditorium without buying a ticket.'
        elif is_wardrobe:
            tags.extend(['Male Friendly', 'Female Friendly', 'Zero Conflict', 'Studio Prep'])
            male_fit = 'good'
            female_fit = 'good'
            category = 'zero_conflict'
            conflict_rating = 'Zero Conflict (Outside Show Dates)'
            rationale = 'Simple sewing/tagging in October or packing up on Dec 8. Gets volunteer credit done without touching performance weekend.'
        elif is_runner:
            tags.extend(['Male Friendly', 'Female Optimal', 'Rehearsal Only', 'Performer Support'])
            male_fit = 'good'
            female_fit = 'top'
            category = 'rehearsal_support'
            conflict_rating = 'Rehearsal Only (Not a Dressing Room Role)'
            rationale = 'Supervise young dancers (Mice, Soldiers, Fairies) between lobby, stage, and cafeteria during dress rehearsals. Hands-on reassurance.'
        elif is_braider:
            tags.extend(['Female Optimal', 'Rehearsal Only', 'Hair Styling'])
            male_fit = 'neutral'
            female_fit = 'top'
            category = 'rehearsal_support'
            conflict_rating = 'Rehearsal Prep Only'
            rationale = 'Help braid dancers hair backstage before Thursday tech rehearsal. Hands-on prep for dancers.'
        elif is_dressing_room:
            tags.extend(['Female Only', 'Backstage Direct Support', 'Costume & Jitters'])
            male_fit = 'no' # OFF LIMITS FOR MALES
            female_fit = 'top'
            category = 'dressing_room'
            conflict_rating = 'Backstage with Dancer (Cannot Watch Auditorium)'
            rationale = 'Off-limits for male volunteers due to privacy. Top pick for female parents wanting to support their dancer with costume changes and pre-stage nerves.'
        elif is_props:
            tags.extend(['Excluded', 'Performance Conflict'])
            male_fit = 'no'
            female_fit = 'no'
            category = 'excluded_conflict'
            conflict_rating = 'High Conflict (Backstage Entire Show)'
            rationale = 'Excluded per your preference: Requires working props backstage through entire performance; cannot watch from the auditorium.'
        elif is_security:
            tags.extend(['Excluded', 'Performance Conflict'])
            male_fit = 'no'
            female_fit = 'no'
            category = 'excluded_conflict'
            conflict_rating = 'High Conflict (Stationed Away from Stage)'
            rationale = 'Excluded per your preference: Stationed at exterior doors, hallways, or cafeteria during showtime. Cannot watch dancer perform.'
        elif is_beverage:
            tags.extend(['Excluded', 'Concessions Conflict'])
            male_fit = 'no'
            female_fit = 'no'
            category = 'excluded_conflict'
            conflict_rating = 'Moderate Conflict (Intermission & Show Overlap)'
            rationale = 'Shift runs 1:15pm-2:30pm or 5:15pm-6:30pm, overlapping intermission and the middle of the performance.'
        elif is_backstage_coord:
            tags.extend(['Excluded', 'Backstage Coordination'])
            male_fit = 'no'
            female_fit = 'neutral'
            category = 'excluded_conflict'
            conflict_rating = 'High Conflict (Full Show Coordination)'
            rationale = 'High responsibility coordinating dressing rooms and stage flow; entirely backstage.'
        else:
            tags.extend(['Other'])
            category = 'other'
            conflict_rating = 'Varies'
            rationale = comment or 'General production support.'

        categorized_data.append({
            'sid': sid,
            'role_name': role_name,
            'comment': comment,
            'date': date_str,
            'weekday': weekday,
            'time': time_str,
            'location': location,
            'remaining': rem,
            'taken': taken,
            'male_fit': male_fit,
            'female_fit': female_fit,
            'category': category,
            'conflict_rating': conflict_rating,
            'rationale': rationale,
            'tags': tags
        })

    # Sort slots chronologically
    def sort_key(item):
        d_parts = item['date'].split('/') if item['date'] else ['99', '99', '9999']
        # mm/dd/yyyy
        month = int(d_parts[0]) if len(d_parts) > 0 and d_parts[0].isdigit() else 99
        day = int(d_parts[1]) if len(d_parts) > 1 and d_parts[1].isdigit() else 99
        year = int(d_parts[2]) if len(d_parts) > 2 and d_parts[2].isdigit() else 9999
        return (year, month, day, item['time'], item['role_name'])

    categorized_data.sort(key=sort_key)

    # Compute overall statistics
    total_slots = len(categorized_data)
    total_open_spots = sum(x['remaining'] for x in categorized_data)
    male_optimum_count = sum(1 for x in categorized_data if x['male_fit'] in ['top', 'good'] and x['remaining'] > 0)
    female_optimum_count = sum(1 for x in categorized_data if x['female_fit'] in ['top', 'good'] and x['remaining'] > 0)
    excluded_count = sum(1 for x in categorized_data if x['category'] == 'excluded_conflict')

    json_slots = json.dumps(categorized_data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Marin Ballet Nutcracker 2026 - Parent Volunteer Strategic Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap" rel="stylesheet">
<style>
:root {{
    --bg-primary: #0b0f19;
    --bg-secondary: #121826;
    --bg-card: #182234;
    --bg-hover: #1f2d45;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-gold: #f59e0b;
    --accent-gold-light: #fef3c7;
    --accent-blue: #38bdf8;
    --accent-rose: #f43f5e;
    --accent-emerald: #10b981;
    --accent-purple: #a855f7;
    --border-color: #243048;
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
}}

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    padding: 24px;
}}

.container {{
    max-width: 1380px;
    margin: 0 auto;
}}

/* Header Banner */
.header-banner {{
    background: linear-gradient(135deg, #1e1b4b 0%, #1e293b 50%, #0f172a 100%);
    border: 1px solid #312e81;
    border-radius: var(--radius-lg);
    padding: 40px 36px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
}}

.header-banner::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(245, 158, 11, 0.12) 0%, rgba(245, 158, 11, 0) 70%);
    pointer-events: none;
}}

.header-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(245, 158, 11, 0.15);
    color: var(--accent-gold);
    border: 1px solid rgba(245, 158, 11, 0.3);
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 16px;
}}

.header-title {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 38px;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 12px;
    color: #fff;
}}

.header-subtitle {{
    font-size: 17px;
    color: var(--text-secondary);
    max-width: 860px;
    margin-bottom: 24px;
}}

.meta-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 14px;
}}

.meta-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-secondary);
}}

.meta-item strong {{
    color: #fff;
}}

/* Quick Stats Grid */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
    margin-bottom: 32px;
}}

.stat-card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 22px;
    transition: transform 0.2s, border-color 0.2s;
}}

.stat-card:hover {{
    transform: translateY(-2px);
    border-color: rgba(245, 158, 11, 0.4);
}}

.stat-label {{
    font-size: 13px;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}}

.stat-value {{
    font-size: 32px;
    font-weight: 800;
    color: #fff;
    line-height: 1;
    margin-bottom: 6px;
}}

.stat-desc {{
    font-size: 13px;
    color: var(--text-secondary);
}}

/* Strategy Box */
.strategy-card {{
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid var(--border-color);
    border-left: 4px solid var(--accent-gold);
    border-radius: var(--radius-md);
    padding: 24px 28px;
    margin-bottom: 32px;
}}

.strategy-title {{
    font-size: 20px;
    font-weight: 700;
    color: var(--accent-gold);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
}}

.strategy-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-top: 16px;
}}

.strategy-col {{
    background: rgba(0, 0, 0, 0.25);
    border-radius: var(--radius-sm);
    padding: 18px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}}

.strategy-col h4 {{
    font-size: 16px;
    color: #fff;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

.strategy-col p {{
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.5;
}}

/* Filter Controls */
.controls-panel {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 20px;
    margin-bottom: 24px;
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: center;
    justify-content: space-between;
}}

.tab-group {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}}

.filter-btn {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 10px 18px;
    border-radius: var(--radius-sm);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}}

.filter-btn:hover {{
    background: var(--bg-hover);
    color: #fff;
}}

.filter-btn.active {{
    background: #2563eb;
    color: #fff;
    border-color: #3b82f6;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}}

.filter-btn.active.male {{
    background: #0284c7;
    border-color: #38bdf8;
}}

.filter-btn.active.female {{
    background: #db2777;
    border-color: #f472b6;
}}

.filter-btn.active.zero {{
    background: #059669;
    border-color: #34d399;
}}

.filter-btn.active.excluded {{
    background: #475569;
    border-color: #64748b;
}}

.search-box {{
    position: relative;
    min-width: 280px;
    flex: 1;
    max-width: 400px;
}}

.search-box input {{
    width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 10px 14px 10px 38px;
    color: #fff;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
}}

.search-box input:focus {{
    border-color: var(--accent-gold);
}}

.search-icon {{
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
}}

/* Slots Table / Cards */
.table-container {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    overflow: hidden;
    margin-bottom: 40px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    text-align: left;
}}

thead th {{
    background: #151e2e;
    color: var(--text-muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 700;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    white-space: nowrap;
}}

tbody tr {{
    border-bottom: 1px solid var(--border-color);
    transition: background 0.15s;
}}

tbody tr:last-child {{
    border-bottom: none;
}}

tbody tr:hover {{
    background: var(--bg-hover);
}}

td {{
    padding: 16px 20px;
    vertical-align: middle;
}}

/* Specific table columns */
.role-name {{
    font-weight: 700;
    color: #fff;
    font-size: 15px;
    margin-bottom: 4px;
}}

.role-comment {{
    font-size: 12.5px;
    color: var(--text-secondary);
    line-height: 1.4;
    max-width: 380px;
}}

.date-time {{
    font-weight: 600;
    color: #e2e8f0;
}}

.date-badge {{
    font-size: 12px;
    color: var(--text-muted);
}}

.location-badge {{
    display: inline-block;
    font-size: 12px;
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-secondary);
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}}

/* Badges */
.badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
}}

.badge-open {{
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}}

.badge-full {{
    background: rgba(148, 163, 184, 0.12);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.2);
}}

.badge-top {{
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
}}

.badge-female {{
    background: rgba(244, 63, 94, 0.15);
    color: #fb7185;
    border: 1px solid rgba(244, 63, 94, 0.3);
}}

.badge-conflict-none {{
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.25);
}}

.badge-conflict-high {{
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.25);
}}

.badge-conflict-mod {{
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.25);
}}

.rationale-text {{
    font-size: 13px;
    color: #cbd5e1;
    max-width: 320px;
    line-height: 1.45;
}}

.cta-button {{
    display: inline-block;
    background: var(--accent-gold);
    color: #0f172a;
    font-weight: 700;
    padding: 12px 24px;
    border-radius: var(--radius-sm);
    text-decoration: none;
    transition: background 0.2s, transform 0.1s;
    font-size: 14px;
}}

.cta-button:hover {{
    background: #f59e0b;
    transform: translateY(-1px);
}}

/* Section Headings */
.section-title {{
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    margin: 40px 0 16px 0;
    display: flex;
    align-items: center;
    gap: 12px;
}}

.section-title span {{
    font-size: 14px;
    font-weight: 500;
    color: var(--text-muted);
}}

.disclaimer-box {{
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: var(--radius-sm);
    padding: 16px 20px;
    margin-bottom: 24px;
    color: #fca5a5;
    font-size: 14px;
}}

.empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}}

@media (max-width: 900px) {{
    body {{
        padding: 16px;
    }}
    .header-banner {{
        padding: 24px;
    }}
    .header-title {{
        font-size: 28px;
    }}
    .table-container {{
        overflow-x: auto;
    }}
    table {{
        min-width: 800px;
    }}
}}
</style>
</head>
<body>

<div class="container">
    <!-- Header Banner -->
    <div class="header-banner">
        <div class="header-badge">⭐ Live SignUpGenius Intelligence</div>
        <h1 class="header-title">Nutcracker 2026: Parent Volunteer Strategic Guide</h1>
        <p class="header-subtitle">
            A comprehensive, data-backed analysis of all <strong>150 volunteer slots</strong> across all 6 paginated sections of the Marin Ballet SignUpGenius. Specifically engineered to balance volunteer obligations while ensuring parents <strong>never miss their dancer on stage</strong> and are <strong>available when their performer needs them most</strong>.
        </p>
        <div class="meta-bar">
            <div class="meta-item">📍 <strong>Production:</strong> Marin Ballet Nutcracker</div>
            <div class="meta-item">📅 <strong>Performances:</strong> Dec 5 & 6 (1:00 PM & 5:00 PM)</div>
            <div class="meta-item">🎟️ <strong>Analyzed Slots:</strong> 150 slot items (All 6 Pages Navigated)</div>
            <div class="meta-item">👤 <strong>Coordinator:</strong> Stephanie Taubert</div>
            <div class="meta-item" style="margin-left:auto;">
                <a class="cta-button" href="https://m.signupgenius.com/#!/showSignUp/10C0C4BA9A929A7FA7-66294307-nutcracker?useFullSite=false" target="_blank">Open Live SignUpGenius ↗</a>
            </div>
        </div>
    </div>

    <!-- Quick Stats -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Total Unique Slot Items</div>
            <div class="stat-value">{total_slots}</div>
            <div class="stat-desc">Extracted across 6 paginated API pages</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Currently Open Spots</div>
            <div class="stat-value" style="color: #34d399;">{total_open_spots}</div>
            <div class="stat-desc">Available for immediate sign up</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Male Parent Top Picks</div>
            <div class="stat-value" style="color: #38bdf8;">{male_optimum_count}</div>
            <div class="stat-desc">Zero dressing room & zero performance conflict</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Female Parent Top Picks</div>
            <div class="stat-value" style="color: #f472b6;">{female_optimum_count}</div>
            <div class="stat-desc">Dressing room & front-of-house opportunities</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Filtered Out / Conflicts</div>
            <div class="stat-value" style="color: #f87171;">{excluded_count}</div>
            <div class="stat-desc">Props, security & beverage conflicts removed</div>
        </div>
    </div>

    <!-- The 3 Parent Strategies -->
    <div class="strategy-card">
        <div class="strategy-title">
            🎯 Strategic Rules of Engagement for Ballet Parents
        </div>
        <p style="color: var(--text-secondary); font-size: 15px;">
            How to satisfy school volunteer quotas without sacrificing your family's experience:
        </p>
        <div class="strategy-grid">
            <div class="strategy-col">
                <h4>1. The "Opposite-Cast" Hack</h4>
                <p>
                    Dancers almost never perform in all 4 shows (Sat 1pm/5pm, Sun 1pm/5pm). If your performer dances in <strong>Cast A (e.g. Sat 1pm & Sun 5pm)</strong>, volunteer during <strong>Cast B (Sat 5pm or Sun 1pm)</strong>! You watch your child's shows 100% free as a spectator.
                </p>
            </div>
            <div class="strategy-col">
                <h4>2. The "Front-of-House Watch" Roles</h4>
                <p>
                    <strong>Boutique Sales</strong> explicitly permits volunteers to sit and watch the performance! <strong>Ticket Scanner</strong> shifts end right as the curtain rises (1:15pm or 5:15pm). <strong>Parent Ushers</strong> can stand and watch from the back of the auditorium.
                </p>
            </div>
            <div class="strategy-col">
                <h4>3. The "Zero Show-Day Conflict" Roles</h4>
                <p>
                    Want zero stress on performance weekend? Take <strong>Clean Up Crew</strong> (Sunday 7:00pm–8:30pm after all shows wrap) or <strong>Wardrobe Prep/Packup</strong>. You satisfy all hours outside of performance times completely.
                </p>
            </div>
        </div>
    </div>

    <!-- Filter Controls -->
    <div class="controls-panel">
        <div class="tab-group" id="filterTabs">
            <button class="filter-btn active" onclick="setFilter('all', this)">All Slots ({total_slots})</button>
            <button class="filter-btn male" onclick="setFilter('male_optimum', this)">👔 Male Parents (Dads)</button>
            <button class="filter-btn female" onclick="setFilter('female_optimum', this)">👗 Female Parents (Moms)</button>
            <button class="filter-btn zero" onclick="setFilter('zero_conflict', this)">✨ Zero-Conflict Shifts</button>
            <button class="filter-btn" onclick="setFilter('open_only', this)">🟢 Open Spots Only</button>
            <button class="filter-btn excluded" onclick="setFilter('excluded', this)">⛔ Excluded Conflicts ({excluded_count})</button>
        </div>
        <div class="search-box">
            <span class="search-icon">🔍</span>
            <input type="text" id="searchInput" placeholder="Search role, date, level, notes..." oninput="handleSearch()">
        </div>
    </div>

    <!-- Active Filter Notice -->
    <div id="filterBanner" style="margin-bottom: 16px; font-size: 14px; color: var(--text-secondary);">
        Showing: <strong id="activeFilterName" style="color: #fff;">All Volunteer Slots</strong> (<span id="visibleCount">{total_slots}</span> slots)
    </div>

    <!-- Slots Table -->
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th style="width: 25%;">Role & Responsibilities</th>
                    <th style="width: 18%;">Date, Time & Location</th>
                    <th style="width: 12%;">Availability</th>
                    <th style="width: 14%;">Suitability</th>
                    <th style="width: 16%;">Show Conflict Level</th>
                    <th style="width: 15%;">Strategic Rationale</th>
                </tr>
            </thead>
            <tbody id="slotsTableBody">
                <!-- Injected via JavaScript -->
            </tbody>
        </table>
        <div id="emptyState" class="empty-state" style="display: none;">
            <h3>No matching volunteer slots found</h3>
            <p>Try clearing your search term or switching to another filter tab.</p>
        </div>
    </div>

</div>

<script>
const slotsData = {json_slots};
let currentFilter = 'all';
let searchQuery = '';

function renderSlots() {{
    const tbody = document.getElementById('slotsTableBody');
    const emptyState = document.getElementById('emptyState');
    tbody.innerHTML = '';

    const filtered = slotsData.filter(item => {{
        // Filter tabs
        if (currentFilter === 'male_optimum') {{
            if (item.male_fit !== 'top' && item.male_fit !== 'good') return false;
        }} else if (currentFilter === 'female_optimum') {{
            if (item.female_fit !== 'top' && item.female_fit !== 'good') return false;
        }} else if (currentFilter === 'zero_conflict') {{
            if (item.category !== 'zero_conflict' && !item.conflict_rating.includes('Zero Conflict')) return false;
        }} else if (currentFilter === 'open_only') {{
            if (item.remaining <= 0) return false;
        }} else if (currentFilter === 'excluded') {{
            if (item.category !== 'excluded_conflict' && item.male_fit !== 'no' && item.female_fit !== 'no') return false;
        }}

        // Search text
        if (searchQuery) {{
            const q = searchQuery.toLowerCase();
            const text = (item.role_name + ' ' + item.comment + ' ' + item.date + ' ' + item.weekday + ' ' + item.time + ' ' + item.location + ' ' + item.rationale).toLowerCase();
            if (!text.includes(q)) return false;
        }}

        return true;
    }});

    document.getElementById('visibleCount').textContent = filtered.length;

    if (filtered.length === 0) {{
        emptyState.style.display = 'block';
        return;
    }} else {{
        emptyState.style.display = 'none';
    }}

    filtered.forEach(item => {{
        const tr = document.createElement('tr');

        // Availability badge
        const availBadge = item.remaining > 0 
            ? `<span class="badge badge-open">🟢 ${{item.remaining}} Open</span>`
            : `<span class="badge badge-full">🔒 Full (${{item.taken}} filled)</span>`;

        // Suitability Badges
        let fitBadges = '';
        if (item.male_fit === 'top') {{
            fitBadges += '<span class="badge badge-top" title="Top Pick for Dads">👔 Dad Top Pick</span> ';
        }} else if (item.male_fit === 'good') {{
            fitBadges += '<span class="badge" style="background:rgba(56,189,248,0.1); color:#38bdf8;">👔 Dad Friendly</span> ';
        }} else if (item.male_fit === 'no') {{
            fitBadges += '<span class="badge" style="background:rgba(239,68,68,0.1); color:#fca5a5;">❌ Dad Off-Limits</span> ';
        }}

        if (item.female_fit === 'top') {{
            fitBadges += '<span class="badge badge-female" title="Top Pick for Moms">👗 Mom Top Pick</span> ';
        }} else if (item.female_fit === 'good') {{
            fitBadges += '<span class="badge" style="background:rgba(244,63,94,0.1); color:#f472b6;">👗 Mom Friendly</span> ';
        }}

        // Conflict badge
        let conflictClass = 'badge-conflict-none';
        if (item.conflict_rating.includes('High')) {{
            conflictClass = 'badge-conflict-high';
        }} else if (item.conflict_rating.includes('Moderate') || item.conflict_rating.includes('Low')) {{
            conflictClass = 'badge-conflict-mod';
        }}
        const conflictBadge = `<span class="badge ${{conflictClass}}">${{item.conflict_rating}}</span>`;

        tr.innerHTML = `
            <td>
                <div class="role-name">${{item.role_name}}</div>
                <div class="role-comment">${{item.comment || 'General volunteer support.'}}</div>
            </td>
            <td>
                <div class="date-time">${{item.date}} (${{item.weekday}})</div>
                <div class="date-badge">⏰ ${{item.time}}</div>
                <div style="margin-top:4px;"><span class="location-badge">📍 ${{item.location}}</span></div>
            </td>
            <td>
                ${{availBadge}}
                <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">Total Needed: ${{item.remaining + item.taken}}</div>
            </td>
            <td>${{fitBadges}}</td>
            <td>${{conflictBadge}}</td>
            <td><div class="rationale-text">${{item.rationale}}</div></td>
        `;
        tbody.appendChild(tr);
    }});
}}

function setFilter(filterType, btn) {{
    currentFilter = filterType;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const names = {{
        'all': 'All Volunteer Slots',
        'male_optimum': 'Optimum for Male Parents (Dads - Zero Dressing Room & Zero Performance Conflict)',
        'female_optimum': 'Optimum for Female Parents (Moms - Backstage Care & Show-Friendly)',
        'zero_conflict': 'Zero-Conflict Slots (Pre-Production, Rehearsals, and Post-Show Strike)',
        'open_only': 'Currently Open Slots Ready for Sign Up',
        'excluded': 'Excluded Roles (Props, Security, Beverage Conflicts)'
    }};
    document.getElementById('activeFilterName').textContent = names[filterType] || filterType;
    renderSlots();
}}

function handleSearch() {{
    searchQuery = document.getElementById('searchInput').value;
    renderSlots();
}}

// Initial render
renderSlots();
</script>

</body>
</html>
"""
    with open('/Users/auxend/code/mb/nutcracker_volunteer_report.html', 'w') as f:
        f.write(html_content)
    print("Report generated successfully at /Users/auxend/code/mb/nutcracker_volunteer_report.html")

if __name__ == '__main__':
    build_html_report()
