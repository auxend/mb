#!/usr/bin/env python3
"""
SignUpGenius Live Sync Utility
Fetches and structures all paginated slots from a SignUpGenius URL or ID.
"""

import sys
import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Any

API_ENDPOINT = "https://sugapi.signupgenius.com/v1/signup/viewSignUpLite/"

def extract_url_id(input_str: str) -> str:
    """Extracts urlID from full SignUpGenius URL or returns it directly."""
    m = re.search(r'(?:showSignUp|go)/([A-Za-z0-9\-]+)', input_str)
    if m:
        return m.group(1).split('?')[0]
    return input_str.strip().split('?')[0]

def parse_duration_hours(time_str: str) -> float:
    """Calculates shift duration in decimal hours (e.g., '12:00pm - 1:15pm' -> 1.25)."""
    if not time_str or '-' not in time_str:
        return 2.0  # default estimate for untimed studio/at-home shifts
    m = re.match(r'(\d+:\d+[ap]m)\s*-\s*(\d+:\d+[ap]m)', time_str.lower().strip())
    if not m:
        return 2.0
    t1_s, t2_s = m.group(1), m.group(2)
    try:
        t1 = datetime.strptime(t1_s, '%I:%M%p')
        t2 = datetime.strptime(t2_s, '%I:%M%p')
        diff = (t2 - t1).total_seconds() / 3600.0
        if diff < 0:
            diff += 24.0
        return round(diff, 2)
    except Exception:
        return 2.0

def format_duration(hours: float) -> str:
    h = int(hours)
    m = int(round((hours - h) * 60))
    if m == 0:
        return f"{h}h"
    if h == 0:
        return f"{m}m"
    return f"{h}h {m}m"

def fetch_all_pages(url_id: str, verbose: bool = True) -> List[Dict[str, Any]]:
    pages = []
    page = 1
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Origin': 'https://m.signupgenius.com',
        'Referer': 'https://m.signupgenius.com/'
    }

    while True:
        if verbose:
            print(f"[*] Fetching page {page} for {url_id}...", file=sys.stderr)
        
        payload = {
            'memberID': 0,
            'parentID': '0',
            'urlID': url_id,
            'startFrom': str(page),
            'customDataSet': page > 1,
            'limitTo': False,
            'fallbackUri': f"https://m.signupgenius.com#!/showSignUp/{url_id}"
        }

        req = urllib.request.Request(
            API_ENDPOINT,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )

        try:
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode('utf-8'))
        except urllib.error.URLError as e:
            print(f"[!] Error fetching page {page}: {e}", file=sys.stderr)
            break

        rd = data.get('returnData', {})
        if not rd.get('success'):
            print(f"[!] API returned unsuccessful message: {rd.get('message')}", file=sys.stderr)
            break

        page_data = rd.get('data', {})
        pages.append(page_data)

        more_data = page_data.get('moreData', False)
        if not more_data:
            break

        page += 1
        time.sleep(0.3)

    return pages

def normalize_slots(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    all_slot_items = {}
    for p in pages:
        items = p.get('signUpSlotItems', {})
        if isinstance(items, dict):
            all_slot_items.update(items)

    normalized = []

    for sid, data in all_slot_items.items():
        s = data.get('slot', {})
        it = data.get('item', {})
        role_name = it.get('item', '').strip()
        comment = it.get('comment', '').strip()
        date_str = s.get('startdate', '').strip()
        weekday = s.get('weekdayDisplay', '').strip()
        time_str = (s.get('timeDisplay') or s.get('altTimeDisplay') or 
                    f"{s.get('starttime', '')} - {s.get('endtime', '')}").strip()
        location = s.get('location', '').strip()
        rem = data.get('remaining', 0)
        taken = data.get('qtyTaken', 0)

        duration_hours = parse_duration_hours(time_str)
        duration_display = format_duration(duration_hours)

        role_lower = role_name.lower()
        comment_lower = comment.lower()

        is_dressing_room = 'dressing room' in role_lower
        is_sewing = 'sewing' in comment_lower or 'alteration' in comment_lower or 'hooks/eyes' in comment_lower or 'buttons' in comment_lower
        is_props = 'prop' in role_lower
        is_security = 'security' in role_lower or 'bouncer' in role_lower
        is_beverage = 'beverage' in role_lower
        is_boutique = 'boutique' in role_lower
        is_ticket = 'ticket scanner' in role_lower
        is_usher = 'usher' in role_lower
        is_cleanup = 'clean up' in role_lower
        is_dropoff = 'drop-off' in role_lower
        is_runner = 'supervisor & runner' in role_lower
        is_braider = 'hair braider' in role_lower or 'braid' in role_lower
        is_wardrobe = 'wardrobe' in role_lower

        # Session classification
        session = "other"
        if date_str == "12/05/2026":
            if "12:" in time_str or "1:" in time_str or "11:" in time_str or "2:" in time_str:
                session = "sat_matinee"
            else:
                session = "sat_evening"
        elif date_str == "12/06/2026":
            if "7:00pm" in time_str or "clean up" in role_lower:
                session = "post_show_strike"
            elif "12:" in time_str or "1:" in time_str or "11:" in time_str or "2:" in time_str:
                session = "sun_matinee"
            else:
                session = "sun_evening"
        elif "12/03" in date_str or "12/04" in date_str:
            session = "theater_dress"
        elif "11/23" in date_str or "11/24" in date_str or "11/21" in date_str:
            session = "studio_dress"
        elif "10/" in date_str:
            session = "pre_production"

        can_watch_show = False
        watch_type = "None"
        if is_ticket:
            can_watch_show = True
            watch_type = "Full Show (Shift ends as curtain rises)"
        elif is_boutique:
            can_watch_show = True
            watch_type = "Full Show (Official Note: You may attend the performance)"
        elif is_usher:
            can_watch_show = True
            watch_type = "Full Show (Option to stand and watch from back of theater)"
        elif is_cleanup or is_wardrobe or session in ["pre_production", "post_show_strike"]:
            can_watch_show = True
            watch_type = "Zero Show Conflict (Outside showtimes completely)"

        male_suitable = not is_dressing_room and not is_props and not is_security and not is_beverage
        male_suitable_no_sew = male_suitable and not is_sewing
        female_suitable = not is_props and not is_security and not is_beverage

        normalized.append({
            'id': sid,
            'role': role_name,
            'comment': comment,
            'date': date_str,
            'weekday': weekday,
            'time': time_str,
            'location': location,
            'session': session,
            'remaining': rem,
            'taken': taken,
            'total': rem + taken,
            'durationHours': duration_hours,
            'durationDisplay': duration_display,
            'isOpen': rem > 0,
            'isDressingRoom': is_dressing_room,
            'requiresSewing': is_sewing,
            'isProps': is_props,
            'isSecurity': is_security,
            'isBeverage': is_beverage,
            'isBoutique': is_boutique,
            'isTicketScanner': is_ticket,
            'isUsher': is_usher,
            'isCleanUp': is_cleanup,
            'isDropoff': is_dropoff,
            'isRunner': is_runner,
            'isBraider': is_braider,
            'isWardrobe': is_wardrobe,
            'canWatchShow': can_watch_show,
            'watchType': watch_type,
            'maleSuitable': male_suitable,
            'maleSuitableNoSew': male_suitable_no_sew,
            'femaleSuitable': female_suitable
        })

    def parse_date_key(item):
        d_parts = item['date'].split('/') if item['date'] else ['99', '99', '9999']
        month = int(d_parts[0]) if len(d_parts) > 0 and d_parts[0].isdigit() else 99
        day = int(d_parts[1]) if len(d_parts) > 1 and d_parts[1].isdigit() else 99
        year = int(d_parts[2]) if len(d_parts) > 2 and d_parts[2].isdigit() else 9999
        return (year, month, day, item['time'], item['role'])

    normalized.sort(key=parse_date_key)
    return normalized

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "10C0C4BA9A929A7FA7-66294307-nutcracker"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "nutcracker_data.json"
    url_id = extract_url_id(target)

    print(f"[*] Starting sync for SignUpGenius ID: {url_id}", file=sys.stderr)
    pages = fetch_all_pages(url_id, verbose=True)
    print(f"[*] Fetched {len(pages)} pages successfully.", file=sys.stderr)

    slots = normalize_slots(pages)
    print(f"[*] Processed {len(slots)} slot items ({sum(1 for s in slots if s['isOpen'])} open).", file=sys.stderr)

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(slots, f, indent=2)

    print(f"[✓] Saved structured data to {out_file}", file=sys.stderr)

if __name__ == '__main__':
    main()
