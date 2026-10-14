import defaultSlots from './nutcracker_data.json';

export function getDefaultSlots() {
  return defaultSlots;
}

function parseDurationHours(timeStr) {
  if (!timeStr || !timeStr.includes('-')) return 2.0;
  const match = timeStr.toLowerCase().match(/(\d+:\d+[ap]m)\s*-\s*(\d+:\d+[ap]m)/);
  if (!match) return 2.0;
  
  const parseTime = (s) => {
    const isPm = s.includes('pm');
    const parts = s.replace(/[ap]m/, '').split(':');
    let h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    if (isPm && h !== 12) h += 12;
    if (!isPm && h === 12) h = 0;
    return h * 60 + m;
  };

  try {
    const m1 = parseTime(match[1]);
    const m2 = parseTime(match[2]);
    let diffMinutes = m2 - m1;
    if (diffMinutes < 0) diffMinutes += 24 * 60;
    return Math.round((diffMinutes / 60) * 100) / 100;
  } catch (e) {
    return 2.0;
  }
}

function formatDuration(hours) {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (m === 0) return `${h}h`;
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export async function fetchLiveSlots(onProgress = null) {
  const urlId = "10C0C4BA9A929A7FA7-66294307-nutcracker";
  const directEndpoint = 'https://sugapi.signupgenius.com/v1/signup/viewSignUpLite/';
  
  if (onProgress) onProgress("Connecting directly to SignUpGenius API...");

  try {
    // Attempt direct in-browser fetch first (CORS allowed by SignUpGenius API)
    return await fetchAndNormalizeDirect(directEndpoint, urlId, onProgress);
  } catch (directErr) {
    console.warn("Direct browser fetch failed, trying local endpoints...", directErr);
    
    // Fallback 1: Local dev server sync endpoint if running via Vite
    try {
      const resp = await fetch('/api/sync-live', { method: 'POST' });
      if (resp.ok) {
        const result = await resp.json();
        if (result.success && Array.isArray(result.data)) {
          return result.data;
        }
      }
    } catch (_) {}

    // Fallback 2: Local proxy
    try {
      return await fetchAndNormalizeDirect('/api/sug/v1/signup/viewSignUpLite/', urlId, onProgress);
    } catch (proxyErr) {
      throw new Error(`Live sync failed: ${directErr.message || directErr}`);
    }
  }
}

async function fetchAndNormalizeDirect(endpoint, urlId, onProgress) {
  let pages = [];
  let page = 1;

  while (true) {
    if (onProgress) onProgress(`Fetching live page ${page}...`);
    const payload = {
      memberID: 0,
      parentID: "0",
      urlID: urlId,
      startFrom: String(page),
      customDataSet: page > 1,
      limitTo: false,
      fallbackUri: `https://m.signupgenius.com#!/showSignUp/${urlId}`
    };

    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const json = await resp.json();
    const rd = json.returnData;
    if (!rd?.success) throw new Error(rd?.message || "API Error");

    pages.push(rd.data);
    if (!rd.data.moreData) break;
    page++;
  }

  // Normalize
  const allSlotItems = {};
  for (const p of pages) {
    if (p.signUpSlotItems) Object.assign(allSlotItems, p.signUpSlotItems);
  }

  const normalized = [];
  for (const [sid, data] of Object.entries(allSlotItems)) {
    const s = data.slot || {};
    const it = data.item || {};
    const roleName = (it.item || '').trim();
    const comment = (it.comment || '').trim();
    const dateStr = (s.startdate || '').trim();
    const weekday = (s.weekdayDisplay || '').trim();
    const timeStr = (s.timeDisplay || s.altTimeDisplay || `${s.starttime || ''} - ${s.endtime || ''}`).trim();
    const location = (s.location || '').trim();
    const rem = Number(data.remaining || 0);
    const taken = Number(data.qtyTaken || 0);

    const durationHours = parseDurationHours(timeStr);
    const durationDisplay = formatDuration(durationHours);

    const roleLower = roleName.toLowerCase();
    const commentLower = comment.toLowerCase();

    const isDressingRoom = roleLower.includes('dressing room');
    const isSewing = commentLower.includes('sewing') || commentLower.includes('alteration') || 
                     commentLower.includes('hooks/eyes') || commentLower.includes('buttons');
    const isProps = roleLower.includes('prop');
    const isSecurity = roleLower.includes('security') || roleLower.includes('bouncer');
    const isBeverage = roleLower.includes('beverage');
    const isBoutique = roleLower.includes('boutique');
    const isTicket = roleLower.includes('ticket scanner');
    const isUsher = roleLower.includes('usher');
    const isCleanUp = roleLower.includes('clean up');
    const isDropoff = roleLower.includes('drop-off');
    const isRunner = roleLower.includes('supervisor & runner');
    const isBraider = roleLower.includes('hair braider') || roleLower.includes('braid');
    const isWardrobe = roleLower.includes('wardrobe');

    let session = "other";
    if (dateStr === "12/05/2026") {
      if (timeStr.includes("12:") || timeStr.includes("1:") || timeStr.includes("11:") || timeStr.includes("2:")) {
        session = "sat_matinee";
      } else {
        session = "sat_evening";
      }
    } else if (dateStr === "12/06/2026") {
      if (timeStr.includes("7:00pm") || roleLower.includes("clean up")) {
        session = "post_show_strike";
      } else if (timeStr.includes("12:") || timeStr.includes("1:") || timeStr.includes("11:") || timeStr.includes("2:")) {
        session = "sun_matinee";
      } else {
        session = "sun_evening";
      }
    } else if (dateStr.includes("12/03") || dateStr.includes("12/04")) {
      session = "theater_dress";
    } else if (dateStr.includes("11/23") || dateStr.includes("11/24") || dateStr.includes("11/21")) {
      session = "studio_dress";
    } else if (dateStr.startsWith("10/")) {
      session = "pre_production";
    }

    let canWatchShow = false;
    let watchType = "None";
    if (isTicket) {
      canWatchShow = true;
      watchType = "Full Show (Shift ends as curtain rises)";
    } else if (isBoutique) {
      canWatchShow = true;
      watchType = "Full Show (Official Note: You may attend performance)";
    } else if (isUsher) {
      canWatchShow = true;
      watchType = "Full Show (Option to stand and watch from back of theater)";
    } else if (isCleanUp || isWardrobe || ["pre_production", "post_show_strike"].includes(session)) {
      canWatchShow = true;
      watchType = "Zero Show Conflict (Outside showtimes completely)";
    }

    const maleSuitable = !isDressingRoom && !isProps && !isSecurity && !isBeverage;
    const maleSuitableNoSew = maleSuitable && !isSewing;
    const femaleSuitable = !isProps && !isSecurity && !isBeverage;

    normalized.push({
      id: sid,
      role: roleName,
      comment: comment,
      date: dateStr,
      weekday: weekday,
      time: timeStr,
      location: location,
      session: session,
      remaining: rem,
      taken: taken,
      total: rem + taken,
      durationHours,
      durationDisplay,
      isOpen: rem > 0,
      isDressingRoom,
      requiresSewing: isSewing,
      isProps,
      isSecurity,
      isBeverage,
      isBoutique,
      isTicketScanner: isTicket,
      isUsher,
      isCleanUp,
      isDropoff,
      isRunner,
      isBraider,
      isWardrobe,
      canWatchShow,
      watchType,
      maleSuitable,
      maleSuitableNoSew,
      femaleSuitable
    });
  }

  return normalized;
}
