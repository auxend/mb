<script>
  import { onMount } from 'svelte';
  import { getDefaultSlots, fetchLiveSlots } from './lib/api.js';

  // State variables
  let slots = $state([]);
  let isLoading = $state(false);
  let statusMessage = $state('');
  let syncSuccessMsg = $state('');
  let isStandaloneFileMode = $state(false);
  let fileInputRef;
  let lastUpdatedTime = $state(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
  let mobileFiltersOpen = $state(false); // Mobile collapsible filter tray

  // Filter States
  let hideUnavailable = $state(true); // User: "filter out things which are not available"
  let parentPersona = $state('dad');  // 'dad' | 'mom' | 'either'
  let canSew = $state(false);          // User: "i can't sew so a lot of the wardrop is off limits"
  let mustWatchShow = $state(true);   // Must be able to watch show in the theater
  let hideConflicts = $state(true);   // Props, security, concessions
  let maxHours = $state(7.0);         // User: "add a dimension of max volunteer hours" (7.0 = No Limit)
  let dancerCast = $state('none');    // 'none' | 'cast_a' | 'cast_b' | 'sat_mat' | 'sat_eve' | 'sun_mat' | 'sun_eve'
  let searchQuery = $state('');
  let roleTypeFilter = $state('all'); // 'all' | 'tickets' | 'boutique' | 'usher' | 'cleanup' | 'dressing'
  let currentPreset = $state('dad_optimal');
  let presetScrollContainer = $state(null);
  let isDragging = false;
  let startX = 0;
  let scrollLeft = 0;
  let hasDragged = false;

  onMount(() => {
    isStandaloneFileMode = window.location.protocol === 'file:';
    slots = getDefaultSlots();
  });

  async function handleLiveSync() {
    isLoading = true;
    statusMessage = 'Connecting to live SignUpGenius server...';
    syncSuccessMsg = '';
    try {
      const freshSlots = await fetchLiveSlots((msg) => {
        statusMessage = msg;
      });
      slots = freshSlots;
      lastUpdatedTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      syncSuccessMsg = `Live update complete! Freshly parsed ${freshSlots.length} slots (${freshSlots.filter(s => s.isOpen).length} currently open).`;
    } catch (err) {
      console.warn("Direct live sync unavailable:", err);
      statusMessage = `Direct API sync error: ${err.message}. Retaining current verified data.`;
    } finally {
      isLoading = false;
      setTimeout(() => {
        syncSuccessMsg = '';
        statusMessage = '';
      }, 7000);
    }
  }

  function triggerFileInput() {
    if (fileInputRef) {
      fileInputRef.click();
    }
  }

  function handleFileImport(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target.result);
        if (Array.isArray(parsed)) {
          slots = parsed;
          lastUpdatedTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          syncSuccessMsg = `Imported ${parsed.length} slots from ${file.name} (${parsed.filter(s => s.isOpen).length} open)!`;
        } else {
          statusMessage = 'Invalid JSON: Expected an array of volunteer slots.';
        }
      } catch (err) {
        statusMessage = `Failed to parse JSON file: ${err.message}`;
      }
    };
    reader.readAsText(file);
  }

  // Quick Presets
  function applyPreset(name) {
    currentPreset = name;
    if (name === 'dad_optimal') {
      parentPersona = 'dad';
      canSew = false;
      hideUnavailable = true;
      mustWatchShow = true;
      hideConflicts = true;
      maxHours = 3.5;
      roleTypeFilter = 'all';
    } else if (name === 'quick_shifts') {
      parentPersona = 'dad';
      canSew = false;
      hideUnavailable = true;
      mustWatchShow = true;
      hideConflicts = true;
      maxHours = 1.5;
      roleTypeFilter = 'all';
    } else if (name === 'zero_stress') {
      parentPersona = 'either';
      canSew = false;
      hideUnavailable = true;
      mustWatchShow = true;
      hideConflicts = true;
      maxHours = 2.0;
      roleTypeFilter = 'cleanup';
    } else if (name === 'mom_backstage') {
      parentPersona = 'mom';
      canSew = false;
      hideUnavailable = true;
      mustWatchShow = false;
      hideConflicts = true;
      maxHours = 7.0;
      roleTypeFilter = 'dressing';
    } else if (name === 'tickets_only') {
      parentPersona = 'either';
      hideUnavailable = true;
      mustWatchShow = true;
      maxHours = 1.5;
      roleTypeFilter = 'tickets';
    } else if (name === 'reset') {
      parentPersona = 'either';
      canSew = true;
      hideUnavailable = false;
      mustWatchShow = false;
      hideConflicts = false;
      maxHours = 7.0;
      dancerCast = 'none';
      searchQuery = '';
      roleTypeFilter = 'all';
    }
  }

  function handlePresetWheel(e) {
    if (!presetScrollContainer) return;
    if (Math.abs(e.deltaY) > 0) {
      e.preventDefault();
      presetScrollContainer.scrollLeft += e.deltaY * 1.2;
    }
  }

  function scrollPresets(direction) {
    if (!presetScrollContainer) return;
    const scrollAmount = 260;
    presetScrollContainer.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth'
    });
  }

  function handleDragStart(e) {
    if (!presetScrollContainer) return;
    isDragging = true;
    hasDragged = false;
    startX = e.pageX - presetScrollContainer.offsetLeft;
    scrollLeft = presetScrollContainer.scrollLeft;
  }

  function handleDragMove(e) {
    if (!isDragging || !presetScrollContainer) return;
    const x = e.pageX - presetScrollContainer.offsetLeft;
    const walk = (x - startX) * 1.5;
    if (Math.abs(walk) > 4) {
      hasDragged = true;
      e.preventDefault();
      presetScrollContainer.scrollLeft = scrollLeft - walk;
    }
  }

  function handleDragEnd() {
    isDragging = false;
  }

  function handleChipClick(name) {
    if (hasDragged) {
      hasDragged = false;
      return;
    }
    applyPreset(name);
  }

  // Check show conflict with dancer schedule
  function getDancerConflict(slotSession, castChoice) {
    if (castChoice === 'none') return { conflict: false, opposite: false };

    const isSatMat = slotSession === 'sat_matinee';
    const isSatEve = slotSession === 'sat_evening';
    const isSunMat = slotSession === 'sun_matinee';
    const isSunEve = slotSession === 'sun_evening';

    if (castChoice === 'cast_a') {
      if (isSatMat || isSunEve) return { conflict: true, label: "⚠️ Conflicts with Performer's Cast A Show" };
      if (isSatEve || isSunMat) return { conflict: false, opposite: true, label: "⭐ Ideal Opposite-Cast Slot (Sat Eve / Sun Mat)" };
    } else if (castChoice === 'cast_b') {
      if (isSatEve || isSunMat) return { conflict: true, label: "⚠️ Conflicts with Performer's Cast B Show" };
      if (isSatMat || isSunEve) return { conflict: false, opposite: true, label: "⭐ Ideal Opposite-Cast Slot (Sat Mat / Sun Eve)" };
    } else if (castChoice === 'sat_mat') {
      if (isSatMat) return { conflict: true, label: "⚠️ Conflicts with Saturday Matinee" };
      if (isSatEve || isSunMat || isSunEve) return { conflict: false, opposite: true, label: "⭐ Opposite Show" };
    } else if (castChoice === 'sat_eve') {
      if (isSatEve) return { conflict: true, label: "⚠️ Conflicts with Saturday Evening" };
      if (isSatMat || isSunMat || isSunEve) return { conflict: false, opposite: true, label: "⭐ Opposite Show" };
    } else if (castChoice === 'sun_mat') {
      if (isSunMat) return { conflict: true, label: "⚠️ Conflicts with Sunday Matinee" };
      if (isSatMat || isSatEve || isSunEve) return { conflict: false, opposite: true, label: "⭐ Opposite Show" };
    } else if (castChoice === 'sun_eve') {
      if (isSunEve) return { conflict: true, label: "⚠️ Conflicts with Sunday Evening" };
      if (isSatMat || isSatEve || isSunMat) return { conflict: false, opposite: true, label: "⭐ Opposite Show" };
    }

    return { conflict: false, opposite: false };
  }

  // Reactive filtered list using Svelte 5 $derived
  let filteredSlots = $derived(
    slots.filter(item => {
      // 1. Availability filter (User: "i'll need to filter out things which are not available")
      if (hideUnavailable && !item.isOpen) {
        return false;
      }

      // 2. Max Hours filter (User: "add a dimension of max volunteer hours")
      const slotDuration = item.durationHours || 2.0;
      if (maxHours < 7.0 && slotDuration > maxHours) {
        return false;
      }

      // 3. Gender / Persona filter (User: "dressing room is off limits for males")
      if (parentPersona === 'dad') {
        if (item.isDressingRoom) return false;
      }

      // 4. Sewing ability filter (User: "i can't sew so a lot of the wardrop is off limits")
      if (!canSew && item.requiresSewing) {
        return false;
      }

      // 5. Conflicts filter (User: "not keen on propps, security as they conflict with the performances")
      if (hideConflicts) {
        if (item.isProps || item.isSecurity || item.isBeverage) {
          return false;
        }
      }

      // 6. Must watch show filter
      if (mustWatchShow && !item.canWatchShow) {
        return false;
      }

      // 7. Role Type Filter
      if (roleTypeFilter === 'tickets' && !item.isTicketScanner) return false;
      if (roleTypeFilter === 'boutique' && !item.isBoutique) return false;
      if (roleTypeFilter === 'usher' && !item.isUsher) return false;
      if (roleTypeFilter === 'cleanup' && !item.isCleanUp) return false;
      if (roleTypeFilter === 'dressing' && !item.isDressingRoom) return false;

      // 8. Dancer Cast Schedule Conflict
      const castMatch = getDancerConflict(item.session, dancerCast);
      if (castMatch.conflict) {
        return false;
      }

      // 9. Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const haystack = `${item.role} ${item.comment} ${item.date} ${item.weekday} ${item.time} ${item.location}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }

      return true;
    })
  );

  let totalAvailableCount = $derived(slots.filter(s => s.isOpen).length);
</script>

<main class="app-layout">
  <!-- Hidden File Input for Standalone Import -->
  <input 
    type="file" 
    accept=".json" 
    bind:this={fileInputRef} 
    onchange={handleFileImport} 
    style="display: none;" 
  />

  <!-- Top Navigation & Header -->
  <header class="app-header">
    <div class="header-content">
      <div class="header-left">
        <div class="badge-row">
          <span class="pill-badge">🩰 Marin Ballet Nutcracker</span>
          {#if isStandaloneFileMode}
            <span class="pill-mode hostless">📁 Hostless SPA</span>
          {:else}
            <span class="pill-mode live">⚡ Live Connected</span>
          {/if}
        </div>
        <h1>Volunteer Navigator</h1>
        <p class="subtitle">Smart slot recommendations for parents who want to see their dancer shine.</p>
      </div>

      <!-- Live Sync Action Zone -->
      <div class="header-sync-zone">
        <div class="sync-status-indicator">
          <span class="live-dot"></span>
          <span class="live-label">LIVE DATA</span>
          <span class="live-time">{lastUpdatedTime}</span>
        </div>

        <div class="action-buttons-group">
          <button class="btn-sync-prominent" onclick={handleLiveSync} disabled={isLoading}>
            {#if isLoading}
              <span class="spinner"></span> Syncing...
            {:else}
              🔄 Update Data
            {/if}
          </button>

          <button class="btn-import" onclick={triggerFileInput} title="Load refreshed nutcracker_data.json">
            📥 Import JSON
          </button>

          <a 
            href="https://m.signupgenius.com/#!/showSignUp/10C0C4BA9A929A7FA7-66294307-nutcracker?useFullSite=false" 
            target="_blank" 
            class="btn-external"
          >
            SignUpGenius ↗
          </a>
        </div>
      </div>
    </div>
  </header>

  <!-- Live Sync Notifications -->
  {#if statusMessage}
    <div class="status-banner info">
      <span class="spinner" style="margin-right: 8px;"></span>
      <span>{statusMessage}</span>
    </div>
  {/if}

  {#if syncSuccessMsg}
    <div class="status-banner success">
      <span>🎉 {syncSuccessMsg}</span>
    </div>
  {/if}

  <!-- Quick Presets Bar (With Smooth Scroll, Arrows & Wheel Support) -->
  <section class="presets-section">
    <div class="preset-label">⚡ Fast Presets:</div>
    <div class="presets-carousel-wrap">
      <button 
        type="button" 
        class="carousel-arrow arrow-left" 
        onclick={() => scrollPresets('left')} 
        aria-label="Scroll presets left"
      >
        ‹
      </button>

      <!-- svelte-ignore a11y_no_noninteractive_element_interactions, a11y_no_noninteractive_tabindex -->
      <div 
        class="preset-buttons-scroll"
        role="region"
        aria-label="Preset filters list"
        tabindex="0"
        bind:this={presetScrollContainer}
        onwheel={handlePresetWheel}
        onmousedown={handleDragStart}
        onmousemove={handleDragMove}
        onmouseup={handleDragEnd}
        onmouseleave={handleDragEnd}
      >
        <button 
          class="preset-chip {currentPreset === 'dad_optimal' ? 'active' : ''}" 
          onclick={() => handleChipClick('dad_optimal')}
        >
          🎯 Non-Sewing Dad (≤3.5h)
        </button>
        <button 
          class="preset-chip {currentPreset === 'quick_shifts' ? 'active' : ''}" 
          onclick={() => handleChipClick('quick_shifts')}
        >
          ⚡ Quick Shifts (≤ 1.5h)
        </button>
        <button 
          class="preset-chip {currentPreset === 'zero_stress' ? 'active' : ''}" 
          onclick={() => handleChipClick('zero_stress')}
        >
          🧹 Clean Up Crew (1.5h)
        </button>
        <button 
          class="preset-chip {currentPreset === 'tickets_only' ? 'active' : ''}" 
          onclick={() => handleChipClick('tickets_only')}
        >
          🎟️ Ticket Scanner (1.25h)
        </button>
        <button 
          class="preset-chip {currentPreset === 'mom_backstage' ? 'active' : ''}" 
          onclick={() => handleChipClick('mom_backstage')}
        >
          👗 Mom Backstage Care
        </button>
        <button 
          class="preset-chip reset {currentPreset === 'reset' ? 'active' : ''}" 
          onclick={() => handleChipClick('reset')}
        >
          🔄 Show All ({slots.length})
        </button>
      </div>

      <button 
        type="button" 
        class="carousel-arrow arrow-right" 
        onclick={() => scrollPresets('right')} 
        aria-label="Scroll presets right"
      >
        ›
      </button>
    </div>
  </section>

  <!-- Mobile Collapsible Toggle -->
  <div class="mobile-filter-toggle-row">
    <button class="btn-mobile-filter" onclick={() => mobileFiltersOpen = !mobileFiltersOpen}>
      <span>⚙️ Refine Filters ({filteredSlots.length} matching)</span>
      <span class="toggle-arrow">{mobileFiltersOpen ? '▲ Hide' : '▼ Expand'}</span>
    </button>
  </div>

  <!-- Filter Control Matrix (Collapsible on Mobile, Grid on Desktop) -->
  <section class="filter-dashboard {mobileFiltersOpen ? 'mobile-expanded' : 'mobile-collapsed'}">
    <!-- Card 1: Persona & Duration -->
    <div class="filter-card">
      <div class="filter-header">
        <h3>1. Who is Volunteering?</h3>
      </div>
      <div class="radio-pill-group">
        <label class="radio-pill {parentPersona === 'dad' ? 'selected' : ''}">
          <input type="radio" name="persona" value="dad" bind:group={parentPersona}>
          👔 Dad (Male Parent)
          <span class="helper-text">✓ Dressing rooms automatically excluded</span>
        </label>
        <label class="radio-pill {parentPersona === 'mom' ? 'selected' : ''}">
          <input type="radio" name="persona" value="mom" bind:group={parentPersona}>
          👗 Mom (Female Parent)
          <span class="helper-text">✓ Dressing room direct care included</span>
        </label>
        <label class="radio-pill {parentPersona === 'either' ? 'selected' : ''}">
          <input type="radio" name="persona" value="either" bind:group={parentPersona}>
          👥 Either / Both Parents
        </label>
      </div>

      <!-- Max Hours Dimension -->
      <div class="hours-filter-box" style="margin-top: 16px;">
        <div class="hours-header">
          <span class="hours-title">⏱️ Max Shift Length:</span>
          <span class="hours-val-pill">
            {#if maxHours >= 7.0}
              No Limit (All Durations)
            {:else}
              ≤ {maxHours} hours
            {/if}
          </span>
        </div>
        <input 
          type="range" 
          min="1.0" 
          max="7.0" 
          step="0.5" 
          bind:value={maxHours} 
          class="hours-slider"
        >
        <div class="hours-chips">
          <button class="hours-chip {maxHours === 1.5 ? 'active' : ''}" onclick={() => maxHours = 1.5}>≤ 1.5h</button>
          <button class="hours-chip {maxHours === 2.5 ? 'active' : ''}" onclick={() => maxHours = 2.5}>≤ 2.5h</button>
          <button class="hours-chip {maxHours === 3.5 ? 'active' : ''}" onclick={() => maxHours = 3.5}>≤ 3.5h</button>
          <button class="hours-chip {maxHours === 5.0 ? 'active' : ''}" onclick={() => maxHours = 5.0}>≤ 5.0h</button>
          <button class="hours-chip {maxHours >= 7.0 ? 'active' : ''}" onclick={() => maxHours = 7.0}>Any</button>
        </div>
      </div>
    </div>

    <!-- Card 2: Safeguards & Availability -->
    <div class="filter-card">
      <div class="filter-header">
        <h3>2. Skill & Availability Safeguards</h3>
      </div>
      <div class="toggle-group">
        <label class="toggle-switch highlight-toggle">
          <input type="checkbox" bind:checked={hideUnavailable}>
          <span class="toggle-slider"></span>
          <div class="toggle-text">
            <strong>Hide Unavailable / Full Slots</strong>
            <span class="subtext">Shows only roles with openings right now ({totalAvailableCount} open)</span>
          </div>
        </label>

        <label class="toggle-switch">
          <input type="checkbox" bind:checked={canSew}>
          <span class="toggle-slider"></span>
          <div class="toggle-text">
            <strong>Can you sew? (Buttons, hooks/eyes, hems)</strong>
            <span class="subtext">{canSew ? 'Yes: Sewing wardrobe tasks included' : 'No: Filters out all sewing wardrobe tasks'}</span>
          </div>
        </label>

        <label class="toggle-switch">
          <input type="checkbox" bind:checked={mustWatchShow}>
          <span class="toggle-slider"></span>
          <div class="toggle-text">
            <strong>Must Be Able to Watch Performance</strong>
            <span class="subtext">Limits to Ticket Scanner, Boutique, Ushers & Clean Up</span>
          </div>
        </label>

        <label class="toggle-switch">
          <input type="checkbox" bind:checked={hideConflicts}>
          <span class="toggle-slider"></span>
          <div class="toggle-text">
            <strong>Hide Show Conflicts (Props, Security, Concessions)</strong>
            <span class="subtext">Excludes roles that keep you trapped away from the stage</span>
          </div>
        </label>
      </div>
    </div>

    <!-- Card 3: Performer Cast Schedule -->
    <div class="filter-card">
      <div class="filter-header">
        <h3>3. Performer Cast Schedule</h3>
      </div>
      <div class="form-group">
        <label for="dancerCastSelect">Which show is your dancer performing in?</label>
        <select id="dancerCastSelect" bind:value={dancerCast} class="custom-select">
          <option value="none">Show All (Schedule Not Set)</option>
          <option value="cast_a">Cast A: Saturday 1:00 PM & Sunday 5:00 PM</option>
          <option value="cast_b">Cast B: Saturday 5:00 PM & Sunday 1:00 PM</option>
          <option value="sat_mat">Saturday 1:00 PM Matinee Only</option>
          <option value="sat_eve">Saturday 5:00 PM Evening Only</option>
          <option value="sun_mat">Sunday 1:00 PM Matinee Only</option>
          <option value="sun_eve">Sunday 5:00 PM Evening Only</option>
        </select>
        <p class="select-hint">
          {#if dancerCast !== 'none'}
            💡 <em>Conflicting show slots are automatically eliminated!</em>
          {:else}
            Select a cast to automatically eliminate slots that conflict with your child's stage time.
          {/if}
        </p>
      </div>

      <div class="form-group" style="margin-top: 14px;">
        <label for="searchQueryInput">Search by Keyword / Role:</label>
        <input 
          id="searchQueryInput"
          type="text" 
          placeholder="e.g. Ticket, Boutique, Sunday, Clean Up..." 
          bind:value={searchQuery}
          class="custom-input"
        >
      </div>
    </div>
  </section>

  <!-- Results Summary Counter -->
  <div class="results-bar">
    <div class="results-stats">
      <span class="stat-badge highlight">
        <strong>{filteredSlots.length}</strong> Matching
      </span>
      <span class="stat-badge open-count">
        <strong>{filteredSlots.filter(s => s.isOpen).length}</strong> Open
      </span>
      {#if maxHours < 7.0}
        <span class="stat-badge duration-indicator">
          ⏱️ ≤ {maxHours}h
        </span>
      {/if}
    </div>
    <div class="results-meta-count">
      Total Open: {totalAvailableCount} / {slots.length}
    </div>
  </div>

  <!-- Cards Grid View -->
  <section class="slots-container">
    {#if filteredSlots.length === 0}
      <div class="empty-card">
        <div class="empty-icon">🔍</div>
        <h3>No volunteer slots match your current criteria</h3>
        <p>Try loosening the filters (e.g. increase "Max Shift Length" or uncheck "Must Watch Performance").</p>
        <button class="btn-reset" onclick={() => applyPreset('dad_optimal')}>Reset to Recommended Dad Preset</button>
      </div>
    {:else}
      <div class="cards-grid">
        {#each filteredSlots as slot (slot.id)}
          {@const castInfo = getDancerConflict(slot.session, dancerCast)}
          <div class="slot-card {slot.isOpen ? 'card-open' : 'card-full'} {castInfo.opposite ? 'card-opposite' : ''}">
            <div class="card-top">
              <div class="role-title-row">
                <h4 class="role-title">{slot.role}</h4>
                {#if slot.isOpen}
                  <span class="status-pill open">🟢 {slot.remaining} Open</span>
                {:else}
                  <span class="status-pill full">🔒 Full</span>
                {/if}
              </div>

              {#if castInfo.opposite}
                <div class="badge-opposite">{castInfo.label}</div>
              {/if}

              <div class="meta-row">
                <span class="meta-date">📅 {slot.date} ({slot.weekday})</span>
                <span class="meta-time">⏰ {slot.time}</span>
              </div>
              
              <!-- Shift Duration Badge -->
              <div class="duration-row">
                <span class="duration-pill {(slot.durationHours || 2.0) <= 1.5 ? 'short' : (slot.durationHours || 2.0) <= 3.0 ? 'medium' : 'long'}">
                  ⏱️ {slot.durationDisplay || `${slot.durationHours || 2.0}h`} shift
                  {#if (slot.durationHours || 2.0) <= 1.5}
                    <span class="quick-tag">⚡ Quick</span>
                  {/if}
                </span>
                <span class="meta-location">📍 {slot.location}</span>
              </div>
            </div>

            <div class="card-body">
              {#if slot.comment}
                <p class="role-instructions">{slot.comment}</p>
              {:else}
                <p class="role-instructions muted">General volunteer assistance for production support.</p>
              {/if}

              <!-- Strategic Badges -->
              <div class="perks-list">
                {#if slot.isTicketScanner}
                  <span class="perk-tag green">🎉 Ends as Show Starts (Free at Curtain)</span>
                {:else}
                  {#if slot.isBoutique}
                    <span class="perk-tag green">🎟️ Allowed to Attend & Watch Show</span>
                  {:else}
                    {#if slot.isCleanUp}
                      <span class="perk-tag blue">✨ Zero Show Conflict (1.5h shift = 2 hrs credit)</span>
                    {:else}
                      {#if slot.isUsher}
                        <span class="perk-tag green">👀 Stand & Watch from Back of Theater</span>
                      {:else}
                        {#if slot.isDressingRoom}
                          <span class="perk-tag purple">👗 Backstage Direct Care (Moms Only)</span>
                        {:else}
                          {#if slot.isDropoff}
                            <span class="perk-tag teal">🚗 Rehearsal Drop-off Support</span>
                          {/if}
                        {/if}
                      {/if}
                    {/if}
                  {/if}
                {/if}

                {#if slot.requiresSewing}
                  <span class="perk-tag amber">✂️ Requires Sewing Skills</span>
                {/if}

                {#if slot.session === 'pre_production' || slot.session === 'post_show_strike'}
                  <span class="perk-tag blue">🗓️ Outside Performance Weekend</span>
                {/if}
              </div>
            </div>

            <div class="card-footer">
              <div class="capacity-info">
                <span>Filled: {slot.taken} / {slot.total}</span>
              </div>
              <a 
                href="https://m.signupgenius.com/#!/showSignUp/10C0C4BA9A929A7FA7-66294307-nutcracker?useFullSite=false" 
                target="_blank" 
                class="btn-signup"
              >
                Sign Up ↗
              </a>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </section>
</main>

<style>
  :global(:root) {
    --bg-dark: #0b1120;
    --bg-card: #151f32;
    --bg-card-hover: #1c2a44;
    --border-color: #26354f;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --accent-gold: #f59e0b;
    --accent-blue: #38bdf8;
    --accent-emerald: #10b981;
    --accent-rose: #f43f5e;
    --accent-purple: #c084fc;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
  }

  :global(*) {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
  }

  :global(html, body) {
    margin: 0;
    padding: 0;
    width: 100%;
    max-width: 100%;
    background-color: var(--bg-dark);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
  }

  .app-layout {
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px;
    padding-bottom: env(safe-area-inset-bottom, 24px);
    box-sizing: border-box;
    overflow-x: hidden;
    text-align: left;
  }

  /* Header */
  .app-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
    border: 1px solid #312e81;
    border-radius: var(--radius-lg);
    padding: 26px 30px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    min-width: 0;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .badge-row {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }

  .pill-badge {
    display: inline-block;
    background: rgba(245, 158, 11, 0.15);
    color: var(--accent-gold);
    border: 1px solid rgba(245, 158, 11, 0.3);
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .pill-mode {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
  }

  .pill-mode.hostless {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }

  .pill-mode.live {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
  }

  h1 {
    font-size: 26px;
    margin: 0 0 6px 0;
    color: #fff;
    font-weight: 800;
    line-height: 1.25;
  }

  .subtitle {
    margin: 0;
    color: var(--text-muted);
    font-size: 14.5px;
    line-height: 1.4;
  }

  /* Live Sync Zone */
  .header-sync-zone {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    background: rgba(0, 0, 0, 0.25);
    padding: 10px 14px;
    border-radius: var(--radius-md);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .action-buttons-group {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }

  .sync-status-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .live-dot {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 8px #10b981;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0% { transform: scale(0.95); opacity: 0.7; }
    50% { transform: scale(1.15); opacity: 1; }
    100% { transform: scale(0.95); opacity: 0.7; }
  }

  .live-label {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #10b981;
  }

  .live-time {
    font-size: 12px;
    color: var(--text-muted);
  }

  .btn-sync-prominent {
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: var(--radius-sm);
    padding: 9px 16px;
    font-weight: 700;
    font-size: 13.5px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
    min-height: 40px;
    transition: all 0.2s;
  }

  .btn-sync-prominent:hover:not(:disabled) {
    background: #1d4ed8;
    transform: translateY(-1px);
  }

  .btn-sync-prominent:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-import {
    background: rgba(255, 255, 255, 0.08);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: var(--radius-sm);
    padding: 9px 14px;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    min-height: 40px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .btn-external {
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
    text-decoration: none;
    border-radius: var(--radius-sm);
    padding: 9px 14px;
    font-weight: 600;
    font-size: 13px;
    min-height: 40px;
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Status Banners */
  .status-banner {
    padding: 12px 16px;
    border-radius: var(--radius-sm);
    font-size: 13.5px;
    margin-bottom: 16px;
    font-weight: 500;
    display: flex;
    align-items: center;
  }

  .status-banner.info {
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: var(--accent-blue);
  }

  .status-banner.success {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: var(--accent-emerald);
  }

  /* Presets Bar */
  .presets-section {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 10px 14px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  .preset-label {
    font-weight: 800;
    font-size: 12px;
    text-transform: uppercase;
    color: var(--accent-gold);
    letter-spacing: 0.5px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .presets-carousel-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    min-width: 0;
    position: relative;
    width: 100%;
  }

  .preset-buttons-scroll {
    display: flex;
    gap: 8px;
    flex-wrap: nowrap;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scroll-behavior: smooth;
    padding: 4px 2px;
    width: 100%;
    min-width: 0;
    cursor: grab;
    user-select: none;
    touch-action: pan-x;
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.25) transparent;
  }

  .preset-buttons-scroll:active {
    cursor: grabbing;
  }

  .preset-buttons-scroll::-webkit-scrollbar {
    height: 4px;
  }

  .preset-buttons-scroll::-webkit-scrollbar-track {
    background: transparent;
  }

  .preset-buttons-scroll::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 4px;
  }

  .preset-buttons-scroll::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.35);
  }

  .carousel-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid var(--border-color);
    border-radius: 50%;
    color: var(--text-main);
    font-size: 18px;
    line-height: 1;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.2s;
  }

  .carousel-arrow:hover {
    background: rgba(56, 189, 248, 0.2);
    border-color: var(--accent-blue);
    color: #fff;
  }

  .preset-chip {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    color: var(--text-main);
    padding: 8px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
    flex-shrink: 0;
  }

  .preset-chip:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: #3b82f6;
  }

  .preset-chip.active {
    background: rgba(37, 99, 235, 0.3);
    border-color: #38bdf8;
    color: #93c5fd;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
  }

  .preset-chip.reset {
    color: var(--text-muted);
  }

  /* Mobile Filter Toggle */
  .mobile-filter-toggle-row {
    display: none;
    margin-bottom: 14px;
  }

  .btn-mobile-filter {
    width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 14px 16px;
    color: #fff;
    font-weight: 700;
    font-size: 14px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .toggle-arrow {
    font-size: 12px;
    color: var(--accent-gold);
  }

  /* Filter Dashboard */
  .filter-dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
    gap: 16px;
    margin-bottom: 22px;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  .filter-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 18px;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  .filter-header h3 {
    margin: 0 0 14px 0;
    font-size: 15.5px;
    color: #fff;
    font-weight: 700;
  }

  /* Radio Pills */
  .radio-pill-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .radio-pill {
    display: flex;
    flex-direction: column;
    padding: 11px 14px;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.2s;
  }

  .radio-pill.selected {
    background: rgba(56, 189, 248, 0.12);
    border-color: var(--accent-blue);
    color: var(--accent-blue);
  }

  .radio-pill input {
    display: none;
  }

  .radio-pill .helper-text {
    font-size: 12px;
    color: var(--text-muted);
    font-weight: 400;
    margin-top: 3px;
  }

  /* Hours Filter Box */
  .hours-filter-box {
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 12px 14px;
  }

  .hours-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }

  .hours-title {
    font-size: 13px;
    font-weight: 700;
    color: #fff;
  }

  .hours-val-pill {
    background: rgba(245, 158, 11, 0.15);
    color: var(--accent-gold);
    border: 1px solid rgba(245, 158, 11, 0.3);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11.5px;
    font-weight: 700;
  }

  .hours-slider {
    width: 100%;
    accent-color: var(--accent-gold);
    cursor: pointer;
    margin: 8px 0;
    height: 6px;
  }

  .hours-chips {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 6px;
  }

  .hours-chip {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
    min-height: 32px;
  }

  .hours-chip.active {
    background: rgba(245, 158, 11, 0.2);
    border-color: var(--accent-gold);
    color: var(--accent-gold);
  }

  /* Toggles */
  .toggle-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .toggle-switch {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    cursor: pointer;
    padding: 4px 0;
  }

  .toggle-switch.highlight-toggle {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    padding: 10px 12px;
    border-radius: var(--radius-sm);
  }

  .toggle-switch input {
    display: none;
  }

  .toggle-slider {
    width: 40px;
    height: 22px;
    background: #334155;
    border-radius: 20px;
    position: relative;
    flex-shrink: 0;
    transition: background 0.2s;
    margin-top: 2px;
  }

  .toggle-slider::after {
    content: '';
    position: absolute;
    width: 16px;
    height: 16px;
    background: white;
    border-radius: 50%;
    top: 3px;
    left: 3px;
    transition: transform 0.2s;
  }

  .toggle-switch input:checked + .toggle-slider {
    background: #10b981;
  }

  .toggle-switch input:checked + .toggle-slider::after {
    transform: translateX(18px);
  }

  .toggle-text {
    display: flex;
    flex-direction: column;
  }

  .toggle-text strong {
    font-size: 13.5px;
    color: #fff;
    line-height: 1.35;
  }

  .toggle-text .subtext {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
  }

  /* Select & Input */
  .form-group label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 6px;
    color: var(--text-muted);
  }

  .custom-select, .custom-input {
    width: 100%;
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 11px 12px;
    color: #fff;
    font-size: 14px;
    outline: none;
    min-height: 44px;
  }

  .custom-select:focus, .custom-input:focus {
    border-color: var(--accent-gold);
  }

  .select-hint {
    font-size: 12px;
    color: var(--accent-gold);
    margin-top: 6px;
    line-height: 1.4;
  }

  /* Results Bar */
  .results-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
    padding: 0 4px;
    flex-wrap: wrap;
    gap: 10px;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  .results-stats {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    min-width: 0;
  }

  .stat-badge {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    padding: 6px 12px;
    border-radius: var(--radius-sm);
    font-size: 12.5px;
    color: var(--text-muted);
  }

  .stat-badge strong {
    color: #fff;
  }

  .stat-badge.highlight {
    background: rgba(37, 99, 235, 0.15);
    border-color: rgba(37, 99, 235, 0.3);
    color: #93c5fd;
  }

  .stat-badge.highlight strong {
    color: #60a5fa;
  }

  .stat-badge.open-count {
    color: #34d399;
    border-color: rgba(16, 185, 129, 0.25);
  }

  .stat-badge.duration-indicator {
    color: var(--accent-gold);
    border-color: rgba(245, 158, 11, 0.3);
  }

  .results-meta-count {
    font-size: 12.5px;
    color: var(--text-muted);
  }

  /* Slots Grid */
  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr));
    gap: 16px;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  .slot-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 18px;
    transition: transform 0.2s, border-color 0.2s;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    box-sizing: border-box;
    overflow: hidden;
  }

  .slot-card:hover {
    transform: translateY(-2px);
    border-color: rgba(245, 158, 11, 0.3);
  }

  .card-opposite {
    border-color: rgba(56, 189, 248, 0.4);
    background: linear-gradient(180deg, rgba(56, 189, 248, 0.05) 0%, var(--bg-card) 40%);
  }

  .role-title-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 8px;
    width: 100%;
    min-width: 0;
  }

  .role-title {
    margin: 0;
    font-size: 16.5px;
    font-weight: 700;
    color: #fff;
    line-height: 1.35;
    word-break: break-word;
    overflow-wrap: anywhere;
    min-width: 0;
  }

  .status-pill {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .status-pill.open {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }

  .status-pill.full {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.2);
  }

  .badge-opposite {
    display: inline-block;
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 13px;
    color: #e2e8f0;
    font-weight: 600;
    margin-bottom: 6px;
  }

  .duration-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }

  .duration-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11.5px;
    font-weight: 700;
  }

  .duration-pill.short {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }

  .duration-pill.medium {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
  }

  .duration-pill.long {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
  }

  .quick-tag {
    font-size: 10px;
    text-transform: uppercase;
    background: rgba(16, 185, 129, 0.25);
    padding: 1px 4px;
    border-radius: 3px;
    margin-left: 2px;
  }

  .meta-location {
    font-size: 12px;
    color: var(--text-muted);
  }

  .role-instructions {
    font-size: 13px;
    color: #cbd5e1;
    line-height: 1.45;
    margin: 0 0 14px 0;
  }

  .role-instructions.muted {
    color: var(--text-muted);
    font-style: italic;
  }

  .perks-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 16px;
  }

  .perk-tag {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.35;
  }

  .perk-tag.green {
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.25);
  }

  .perk-tag.blue {
    background: rgba(56, 189, 248, 0.12);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.25);
  }

  .perk-tag.purple {
    background: rgba(192, 132, 252, 0.12);
    color: #c084fc;
    border: 1px solid rgba(192, 132, 252, 0.25);
  }

  .perk-tag.teal {
    background: rgba(45, 212, 191, 0.12);
    color: #2dd4bf;
    border: 1px solid rgba(45, 212, 191, 0.25);
  }

  .perk-tag.amber {
    background: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.25);
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 14px;
    border-top: 1px solid var(--border-color);
  }

  .capacity-info {
    font-size: 12px;
    color: var(--text-muted);
  }

  .btn-signup {
    background: var(--accent-gold);
    color: #0b1120;
    text-decoration: none;
    font-weight: 700;
    font-size: 13.5px;
    padding: 8px 16px;
    border-radius: var(--radius-sm);
    min-height: 38px;
    display: inline-flex;
    align-items: center;
    transition: background 0.15s;
  }

  .btn-signup:hover {
    background: #f59e0b;
  }

  .empty-card {
    text-align: center;
    background: var(--bg-card);
    border: 1px dashed var(--border-color);
    border-radius: var(--radius-lg);
    padding: 40px 18px;
  }

  .empty-icon {
    font-size: 36px;
    margin-bottom: 12px;
  }

  .btn-reset {
    margin-top: 14px;
    background: #2563eb;
    color: #fff;
    border: none;
    padding: 11px 22px;
    border-radius: var(--radius-sm);
    font-weight: 600;
    cursor: pointer;
    min-height: 42px;
  }

  /* Tablet Breakpoint (769px - 1024px) */
  @media (max-width: 1024px) {
    .header-content {
      flex-direction: column;
      align-items: stretch;
      gap: 14px;
    }

    .header-sync-zone {
      width: 100%;
      justify-content: space-between;
    }
  }

  /* Mobile Media Queries */
  @media (max-width: 768px) {
    .app-layout {
      padding: 14px 12px;
    }

    .app-header {
      padding: 18px 16px;
      margin-bottom: 14px;
    }

    h1 {
      font-size: 22px;
    }

    .subtitle {
      font-size: 13px;
    }

    .header-content {
      flex-direction: column;
      align-items: stretch;
      gap: 14px;
    }

    .header-sync-zone {
      width: 100%;
      flex-direction: column;
      align-items: stretch;
      gap: 10px;
    }

    .sync-status-indicator {
      justify-content: center;
    }

    .action-buttons-group {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }

    .action-buttons-group .btn-sync-prominent {
      grid-column: span 2;
      justify-content: center;
    }

    .btn-import, .btn-external {
      justify-content: center;
    }

    /* Mobile Presets */
    .presets-section {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
      padding: 10px 12px;
    }

    .presets-carousel-wrap {
      width: 100%;
    }

    .carousel-arrow {
      display: none;
    }

    /* Mobile Collapsible Filters */
    .mobile-filter-toggle-row {
      display: block;
    }

    .filter-dashboard.mobile-collapsed {
      display: none;
    }

    .filter-dashboard.mobile-expanded {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .cards-grid {
      grid-template-columns: 1fr;
      gap: 14px;
    }

    .slot-card {
      padding: 16px;
    }

    .role-title {
      font-size: 16px;
    }

    .btn-signup {
      padding: 9px 18px;
      font-size: 14px;
    }
  }
</style>
