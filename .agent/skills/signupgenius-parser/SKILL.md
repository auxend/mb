---
name: signupgenius-parser
description: >-
  Reverse-engineered API specification and automated synchronization workflow for
  SignUpGenius forms. Use whenever you need to fetch, paginate, parse, or refresh
  volunteer opportunities, slot availability, and event signups from SignUpGenius.
---

# SignUpGenius Parser & Sync Skill

This skill captures the reverse-engineered internal API specifications and repeatable workflow for parsing and synchronizing data from SignUpGenius (both desktop and mobile URLs) without headless browser overhead.

---

## 1. Why Standard Scraping Fails

SignUpGenius renders its sign-up pages using client-side AngularJS:
* Standard HTTP requests to URLs like `https://www.signupgenius.com/go/<id>` or `https://m.signupgenius.com/#!/showSignUp/<id>` return an empty HTML shell containing:
  ```html
  <div data-ng-view class="signupPage l-signuppage"></div>
  ```
* The actual data (dates, roles, capacities, remaining spots, comments) is fetched dynamically via an internal JSON API called during Angular's route resolution (`signUpRoutingController`).
* Headless browser scraping is slow and prone to timeout errors due to heavy third-party ads and tracker scripts (Rokt, HubSpot, Convert, Google Ad Manager).
* By calling the internal backend API directly, requests return in milliseconds with complete data.

---

## 2. API Specification

### Endpoint
* **URL:** `https://sugapi.signupgenius.com/v1/signup/viewSignUpLite/`
* **Method:** `POST`
* **Content-Type:** `application/json`

### Required Request Headers
```http
User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1
Origin: https://m.signupgenius.com
Referer: https://m.signupgenius.com/
Content-Type: application/json
```
*(No authentication tokens or session cookies are required for public signups).*

### Request Payload Schema
```json
{
  "memberID": 0,
  "parentID": "0",
  "urlID": "10C0C4BA9A929A7FA7-66294307-nutcracker",
  "startFrom": "1",
  "customDataSet": false,
  "limitTo": false,
  "fallbackUri": "https://m.signupgenius.com#!/showSignUp/10C0C4BA9A929A7FA7-66294307-nutcracker"
}
```

### Parameters Guide
* `urlID` *(string, required)*: The unique slug or alphanumeric ID from the URL (e.g. `10C0C4BA9A929A7FA7-66294307-nutcracker`).
* `startFrom` *(string, required)*: The 1-based page index (`"1"`, `"2"`, `"3"`, etc.).
* `customDataSet` *(boolean, required)*: Must be `false` for page 1, and `true` for page 2 and beyond.
* `limitTo` *(boolean)*: Usually `false`.
* `fallbackUri` *(string)*: The mobile URL format string.

---

## 3. Pagination Mechanics

SignUpGenius paginates signups with many dates/slots into batches (typically 20–25 slot items per page).

1. **Check `moreData`**: Each page response contains:
   ```json
   {
     "returnData": {
       "success": true,
       "data": {
         "moreData": true,
         "signUpSlotItems": { ... }
       }
     }
   }
   ```
2. **Loop Condition**:
   * Start with `page = 1` and `customDataSet = false`.
   * Keep fetching while `moreData === true`.
   * Increment `page += 1` and set `customDataSet = true`.
   * Add a small pause (~200ms–300ms) between page requests to be respectful.

---

## 4. Response Data Structure

The primary data lives in `returnData.data.signUpSlotItems`, which is an object mapping each `slotItemID` (integer/string) to its details:

```json
{
  "1863004415": {
    "ID": 1863004415,
    "remaining": 1,
    "qtyTaken": 0,
    "item": {
      "itemID": 495989502,
      "item": "Dressing Room - Level 7",
      "comment": "For this role, it is required that you attend at least 1 rehearsal and 1 performance.",
      "qty": 1
    },
    "slot": {
      "ID": 843088896,
      "startdate": "11/24/2026",
      "weekdayDisplay": "Tue",
      "starttime": "11:30 AM",
      "endtime": "5:45 PM",
      "timeDisplay": "11:30am - 5:45pm",
      "location": "Studio Dress - Act II"
    }
  }
}
```

Key fields to extract:
* `item.item`: The name of the volunteer role (e.g., "Ticket Scanner", "Wardrobe", "Clean Up Crew").
* `item.comment`: Specific instructions, requirements, or prerequisites.
* `slot.startdate`: Date in `MM/DD/YYYY` format.
* `slot.timeDisplay`: Time range string.
* `slot.location`: Venue or studio location.
* `remaining`: Number of open volunteer slots.
* `qtyTaken`: Number of filled volunteer slots.

---

## 5. Domain-Specific Classification Heuristics

When helping parents choose volunteer roles, apply these business rules:

1. **Gender / Dressing Room Restrictions**:
   * Any role containing `"Dressing Room"` is female-only in youth ballet due to dancer privacy during costume changes. Off-limits for male parents.
2. **Sewing / Alterations Restrictions**:
   * Any role where `item.comment` mentions `"sewing"`, `"alterations"`, `"hooks/eyes"`, or `"buttons"` requires sewing skills (e.g. October Wardrobe prep). Dads or moms without sewing skills must avoid these.
   * Note: Post-show `"Wardrobe Packup"` (e.g., Dec 8) is packing boxes and does **not** require sewing.
3. **Show Watching Capabilities**:
   * **Ticket Scanner**: Shift ends right as the show begins (e.g. 1:15 PM or 5:15 PM). Volunteer can sit and watch the entire performance.
   * **Boutique Sales**: SignUpGenius notes explicitly permit attending the performance, working only pre-show, intermission, and post-show.
   * **Parent Ushers**: Can watch from the back of the auditorium without a ticket.
   * **Clean Up Crew / Wardrobe Packup**: Outside performance hours entirely (Zero Show Conflict).
4. **Performance Conflicts**:
   * **Props (Stage Left/Right)**: Backstage in wings during entire performance.
   * **Security (Cafeteria / Hallway / Bouncer)**: Locked at doors/cafeterias away from stage.
   * **Beverage Sales**: Overlaps intermission and second act.

---

## 6. Sync Script Reference

Use the provided CLI tool located at `.agent/skills/signupgenius-parser/scripts/sync_signup.py`:

```bash
# Fetch and generate structured JSON:
python3 .agent/skills/signupgenius-parser/scripts/sync_signup.py 10C0C4BA9A929A7FA7-66294307-nutcracker nutcracker_data.json
```

---

## 7. Hostless Standalone SPA Architecture

To distribute the volunteer navigator without requiring node, python, or web servers:
1. `vite-plugin-singlefile` inlines all HTML, Svelte reactivity runtime, CSS styles, icons, and baseline JSON data into a single 190KB file: `volunteer_navigator.html`.
2. Can be opened directly with `open volunteer_navigator.html` via `file:///` on any computer.
3. Supports 1-click JSON import via browser file picker if the user runs the sync script to refresh data.
4. To rebuild the hostless bundle after modifying the app:
   ```bash
   cd volunteer-app && npm run build
   cp dist/index.html ../volunteer_navigator.html
   ```

