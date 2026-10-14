# Marin Ballet Nutcracker 2026 — Volunteer Navigator 🩰

An intelligent, mobile-friendly Single-Page Application (SPA) designed to help parents find optimal volunteer shifts for the **Marin Ballet Nutcracker 2026** production without missing their dancer's performance or being unavailable when needed backstage.

## 🚀 Live Demo & Standalone App

- **GitHub Pages**: [https://auxend.github.io/mb/](https://auxend.github.io/mb/)
- **Hostless Standalone File**: [`volunteer_navigator.html`](volunteer_navigator.html) / [`index.html`](index.html)
  - Fully inlined single-file application (~193 KB).
  - Runs directly via `file:///` in any modern desktop or mobile browser with **zero local server or dependencies**.
  - Features direct in-browser live synchronization with the SignUpGenius API (`Access-Control-Allow-Origin: *`).

---

## 🎯 Key Capabilities & Filters

- **Dad Persona Optimization**: Automatically eliminates female dressing room shifts while preserving backstage/front-of-house roles.
- **Show Viewing Guarantee**: Filters specifically for roles that allow watching the performance (Ticket Scanner ending at curtain, Boutique with official show attendance permission, Ushers from back of house, or off-show Clean Up).
- **Skill & Requirement Safeguards**:
  - **Sewing Filter**: Excludes wardrobe alteration/prep shifts requiring sewing skills (buttons, hooks/eyes).
  - **Conflict Exclusions**: Filters out props and security duties that keep parents away during the show.
  - **Availability Filter**: Hides filled/unavailable slots with live remaining capacity indicators.
  - **Max Volunteer Hours Slider**: Quickly filters by maximum shift duration (≤ 1.5h quick shifts, ≤ 2.5h, ≤ 3.5h, etc.).
  - **Cast Schedule Matcher**: Select your dancer's cast (Cast A, Cast B, or specific matinee/evening show) to eliminate conflicting volunteer times.

---

## 🛠️ Repository Contents

- `index.html` / `volunteer_navigator.html` — The standalone production single-file SPA.
- `volunteer-app/` — Full Svelte 5 + Vite source code with responsive mobile-first UI components.
- `.agent/skills/signupgenius-parser/` — Reverse-engineered SignUpGenius API specification and automated sync workflow.
- `generate_html_report.py` — Python report generation utility.
- `nutcracker_data.json` — Pre-parsed structured dataset of all 150 production volunteer slots.
