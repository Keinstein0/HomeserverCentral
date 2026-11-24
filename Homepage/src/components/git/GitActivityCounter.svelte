<script lang="ts">
  import { onMount } from "svelte";
  import scratchedMetalTile from "./../../assets/scratched-metal-tile.webp";

  export let username: string = "keinstein0";
  export let label: string = "GIT ACTIVITY";
  export let weeks: number = 32;
  export let showDeckHue: boolean = false;

  interface ContributionDay {
    date: string;
    count: number;
    level: 0 | 1 | 2 | 3 | 4;
  }

  let columns: ContributionDay[][] = [];
  let monthLabels: (string | null)[] = [];
  let hoveredDay: ContributionDay | null = null;
  let totalContributions: number | null = null;

  function formatDate(date: string): string {
    const [y, m, d] = date.split("-");
    return y && m && d ? `${d}-${m}-${y}` : date;
  }

  function dateKey(date: Date): string {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
      date.getDate()
    ).padStart(2, "0")}`;
  }

  interface GridResult {
    columns: ContributionDay[][];
    monthLabels: (string | null)[];
  }

  /**
   * Builds a GitHub-style calendar grid anchored to real dates:
   * columns run oldest -> newest (left -> right) and always start on
   * a Monday, with rows Monday -> Sunday top -> bottom. This is what
   * keeps the matrix from rendering mirrored/shifted regardless of
   * the order the data source returns days in.
   */
  function buildCalendarGrid(
    numWeeks: number,
    dayFor: (date: Date) => ContributionDay
  ): GridResult {
    const months = [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ];

    const today = new Date();
    // Weekday index with Monday = 0.
    const mondayOffset = (today.getDay() + 6) % 7;
    const currentMonday = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate() - mondayOffset
    );
    const start = new Date(currentMonday);
    start.setDate(currentMonday.getDate() - (numWeeks - 1) * 7);

    const columns: ContributionDay[][] = [];
    const monthLabels: (string | null)[] = [];
    let lastLabeledMonth = -1;

    for (let w = 0; w < numWeeks; w++) {
      const col: ContributionDay[] = [];
      let monthLabel: string | null = null;
      let labelMonth = -1;

      for (let d = 0; d < 7; d++) {
        const current = new Date(start);
        current.setDate(start.getDate() + w * 7 + d);
        // First day of a month gets a label, but not on the very first
        // column (it would clip) and not if it repeats the last one.
        if (current.getDate() === 1) {
          labelMonth = current.getMonth();
          if (w > 0 && labelMonth !== lastLabeledMonth) {
            monthLabel = months[labelMonth];
          }
        }
        col.push(dayFor(current));
      }

      if (monthLabel) lastLabeledMonth = labelMonth;
      columns.push(col);
      monthLabels.push(monthLabel);
    }

    return { columns, monthLabels };
  }

  function fallbackDayFor(seedRef: { seed: number }) {
    return (date: Date): ContributionDay => {
      const r = (seedRef.seed = (seedRef.seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
      let level: 0 | 1 | 2 | 3 | 4 = 0;
      let count = 0;
      if (r > 0.86) {
        level = 4;
        count = 8 + Math.floor(r * 1000) % 6;
      } else if (r > 0.7) {
        level = 3;
        count = 5 + Math.floor(r * 1000) % 3;
      } else if (r > 0.52) {
        level = 2;
        count = 3 + Math.floor(r * 1000) % 2;
      } else if (r > 0.36) {
        level = 1;
        count = 1 + Math.floor(r * 1000) % 2;
      }
      return { date: dateKey(date), count, level };
    };
  }

  // Offline fallback: deterministic pseudo-random pattern.
  const fallback = buildCalendarGrid(weeks, fallbackDayFor({ seed: 42 }));
  columns = fallback.columns;
  monthLabels = fallback.monthLabels;

  onMount(async () => {
    try {
      const res = await fetch(
        `https://github-contributions-api.jogruber.de/v4/${encodeURIComponent(username)}?y=last`
      );
      if (!res.ok) return;
      const data = await res.json();
      if (Array.isArray(data?.contributions) && data.contributions.length > 0) {
        // Index by date so grid order comes purely from the calendar,
        // never from the order the API happens to return rows in.
        const byDate = new Map<string, ContributionDay>();
        let total = 0;
        for (const c of data.contributions) {
          byDate.set(String(c.date ?? ""), {
            date: String(c.date ?? ""),
            count: Number(c.count ?? 0),
            level: Math.min(4, Math.max(0, Number(c.level ?? 0))) as 0 | 1 | 2 | 3 | 4,
          });
        }
        const today = new Date();
        const result = buildCalendarGrid(weeks, (date) => {
          if (date > today) {
            // Future days have no data yet — render as dark LEDs.
            return { date: dateKey(date), count: 0, level: 0 };
          }
          const day = byDate.get(dateKey(date));
          if (day) total += day.count;
          return day ?? { date: dateKey(date), count: 0, level: 0 };
        });
        columns = result.columns;
        monthLabels = result.monthLabels;
        totalContributions = total;
      }
    } catch {
      // Keep fallback grid silently when offline or blocked
    }
  });
</script>

<div class="physical-apparatus">
  <div class="metal-chassis-box">
    <div
      class="chassis-top-deck"
      style:background-image="linear-gradient(180deg, rgba(255, 255, 255, 0.22)
      0%, transparent 60%), url({scratchedMetalTile})"
    >
      {#if showDeckHue}
        <div class="led-deck-reflection"></div>
      {/if}
    </div>

    <div
      class="chassis-front-face"
      style:background-image="linear-gradient(180deg, rgba(255, 255, 255, 0.1)
      0%, rgba(0, 0, 0, 0.25) 100%), url({scratchedMetalTile})"
    >
      <div class="bolt-socket top-left">
        <span class="slotted-screw screw-rot-1"></span>
      </div>
      <div class="bolt-socket top-right">
        <span class="slotted-screw screw-rot-2"></span>
      </div>
      <div class="bolt-socket bottom-left">
        <span class="slotted-screw screw-rot-3"></span>
      </div>
      <div class="bolt-socket bottom-right">
        <span class="slotted-screw screw-rot-4"></span>
      </div>

      <div class="matrix-scroller">
        <div class="matrix-content">
          <div class="month-row">
            {#each columns as _, w}
              <span class="month-cell" class:has-label={monthLabels[w]}>{monthLabels[w] ?? ""}</span>
            {/each}
          </div>

          <div class="bezel-row">
            <div class="weekday-labels" aria-hidden="true">
              <span>Mon</span>
              <span></span>
              <span>Wed</span>
              <span></span>
              <span>Fri</span>
              <span></span>
              <span>Sun</span>
            </div>
            <div class="led-bezel">
              <div
                class="led-matrix"
                role="img"
                aria-label="Git activity LED matrix for {username}"
                on:mouseleave={() => (hoveredDay = null)}
              >
                {#each columns as week}
                  <div class="led-col">
                    {#each week as day}
                      <span
                        class="led level-{day.level}"
                        role="presentation"
                        title="{formatDate(day.date)}: {day.count} contribution{day.count === 1 ? '' : 's'}"
                        on:mouseenter={() => (hoveredDay = day)}
                      ></span>
                    {/each}
                  </div>
                {/each}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="face-footer">
        <div class="readout">
          {#if hoveredDay}
            <span>{formatDate(hoveredDay.date)} · {hoveredDay.count} commit{hoveredDay.count === 1 ? "" : "s"}</span>
          {:else if totalContributions !== null}
            <span>{totalContributions} commits / {weeks}w</span>
          {:else}
            <span>@{username}</span>
          {/if}
        </div>

        {#if label}
          <span class="engraved-label">{label}</span>
        {/if}
      </div>
    </div>

    <div class="chassis-ground-shadow"></div>
  </div>
</div>

<style>
  .physical-apparatus {
    width: 100%;
    max-width: 720px;
    margin: 2.2rem auto 3.8rem;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    padding: 0 16px;
  }

  .metal-chassis-box {
    position: relative;
    width: 100%;
    max-width: 680px;
    box-sizing: border-box;
    z-index: 2;
    box-shadow:
      0 10px 22px rgba(0, 0, 0, 0.28),
      0 3px 6px rgba(0, 0, 0, 0.18);
    border-radius: 8px;
  }

  .chassis-top-deck {
    height: 22px;
    width: 100%;
    background-repeat: repeat-x;
    background-size: 547px auto;
    background-position: top left;
    border-radius: 8px 8px 0 0;
    border-top: 1.5px solid rgba(255, 255, 255, 0.42);
    border-left: 1.5px solid rgba(255, 255, 255, 0.18);
    border-right: 1.5px solid rgba(0, 0, 0, 0.6);
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
  }

  .led-deck-reflection {
    position: absolute;
    inset: 0;
    background: radial-gradient(
      ellipse at 50% 100%,
      rgba(34, 255, 102, 0.22) 0%,
      rgba(16, 185, 72, 0.08) 55%,
      transparent 80%
    );
    pointer-events: none;
  }

  .chassis-front-face {
    position: relative;
    padding: 10px 2.2rem 2.1rem;
    background-repeat: repeat-x;
    background-size: 547px auto;
    background-position: left center;
    border-radius: 0 0 8px 8px;
    border-top: 2px solid #554437;
    border-left: 1.5px solid rgba(255, 255, 255, 0.14);
    border-right: 2px solid #080605;
    border-bottom: 2.5px solid #080605;
    box-shadow:
      inset 0 1px 2px rgba(255, 255, 255, 0.2),
      inset 0 -2px 5px rgba(0, 0, 0, 0.7);
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }

  .led-bezel {
    width: 100%;
    background: linear-gradient(180deg, #070a08 0%, #0d130f 100%);
    border-radius: 6px;
    padding: 12px 14px;
    box-sizing: border-box;
    border-top: 2px solid #030403;
    border-left: 1.5px solid #050706;
    border-right: 1.5px solid rgba(255, 255, 255, 0.08);
    border-bottom: 1.5px solid rgba(255, 255, 255, 0.14);
    box-shadow:
      inset 0 4px 12px rgba(0, 0, 0, 0.95),
      0 1px 0 rgba(255, 255, 255, 0.12);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .matrix-scroller {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  /* Keeps the LED graph compact; on narrow screens the whole block
     (labels + months + bezel) scrolls together, so nothing stretches
     the chassis and month labels stay over their columns. */
  .matrix-content {
    min-width: 410px;
    position: relative;
  }

  .month-row {
    display: flex;
    justify-content: space-between;
    /* First in-flow element of the face: with the face's top padding at
       10px, this row sits exactly level with the bolt screws (top: 10px)
       without clipping or eating extra height. Left/right offsets skip
       the weekday gutter + bezel padding so labels align over their
       LED columns. */
    margin-left: calc(30px + 6px + 14px);
    margin-right: 14px;
    margin-bottom: 8px;
    line-height: 1;
    box-sizing: border-box;
  }

  .month-cell {
    flex: none;
    width: 10px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.7rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: 0;
    color: #060503;
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.35);
    white-space: nowrap;
  }

  .bezel-row {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    width: 100%;
  }

  .weekday-labels {
    display: flex;
    flex-direction: column;
    width: 30px;
    flex: none;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.7rem;
    font-weight: 700;
    color: #060503;
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.35);
    text-align: right;
    user-select: none;
    /* One 14px-tall slot per LED row (10px LED + 4px gap). The bezel's
       12px top padding shifts the first LED down, so the slots start at
       10px to centre every label over its LED row. */
    padding-top: 10px;
    box-sizing: border-box;
  }

  .weekday-labels span {
    height: 14px;
    line-height: 14px;
    white-space: nowrap;
  }

  .led-matrix {
    display: flex;
    justify-content: space-between;
    gap: 4px;
  }

  .led-col {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .led {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: block;
    transition: transform 0.12s ease, filter 0.12s ease;
    cursor: default;
  }

  .led:hover {
    transform: scale(1.35);
    z-index: 3;
  }

  .led.level-0 {
    background: radial-gradient(circle at 35% 35%, #1d2e22 0%, #0d1710 70%, #070d09 100%);
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.85),
      0 0 1px rgba(0, 0, 0, 0.6);
  }

  .led.level-1 {
    background: radial-gradient(circle at 35% 35%, #4ade80 0%, #166534 65%, #0d3b1e 100%);
    box-shadow:
      0 0 4px rgba(34, 197, 94, 0.45),
      inset 0 1px 1px rgba(255, 255, 255, 0.25);
  }

  .led.level-2 {
    background: radial-gradient(circle at 35% 35%, #86efac 0%, #22c55e 60%, #15803d 100%);
    box-shadow:
      0 0 6px rgba(34, 197, 94, 0.7),
      0 0 10px rgba(34, 197, 94, 0.25),
      inset 0 1px 1px rgba(255, 255, 255, 0.35);
  }

  .led.level-3 {
    background: radial-gradient(circle at 35% 35%, #bbf7d0 0%, #4ade80 55%, #16a34a 100%);
    box-shadow:
      0 0 7px rgba(74, 222, 128, 0.85),
      0 0 14px rgba(34, 197, 94, 0.45),
      inset 0 1px 1.5px rgba(255, 255, 255, 0.5);
  }

  .led.level-4 {
    background: radial-gradient(circle at 35% 35%, #ecfdf5 0%, #6ee7b7 45%, #22c55e 100%);
    box-shadow:
      0 0 8px rgba(110, 231, 183, 0.95),
      0 0 16px rgba(34, 197, 94, 0.65),
      inset 0 1px 2px rgba(255, 255, 255, 0.75);
  }


  .face-footer {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0.5rem;
    box-sizing: border-box;
    min-height: 1.4rem;
  }

  .readout {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.75rem;
    letter-spacing: 0.06em;
    color: rgba(134, 239, 172, 0.78);
    text-shadow: 0 0 6px rgba(34, 197, 94, 0.45);
  }

  .engraved-label {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #060503;
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.4);
    user-select: none;
  }

  .bolt-socket {
    position: absolute;
    width: 17px;
    height: 17px;
    border-radius: 50%;
    background: #090706;
    box-shadow:
      inset 0 2px 4px rgba(0, 0, 0, 0.95),
      0 1px 1px rgba(255, 255, 255, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 12;
  }

  .top-left {
    top: 10px;
    left: 12px;
  }
  .top-right {
    top: 10px;
    right: 12px;
  }
  .bottom-left {
    bottom: 10px;
    left: 12px;
  }
  .bottom-right {
    bottom: 10px;
    right: 12px;
  }

  .slotted-screw {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: radial-gradient(
      circle at 35% 35%,
      #d0d0d0 0%,
      #777 55%,
      #2a2a2a 100%
    );
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
    position: relative;
  }

  .slotted-screw::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 1.5px;
    right: 1.5px;
    height: 1.8px;
    background: #111;
    transform: translateY(-50%);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.3);
  }

  .screw-rot-1 {
    transform: rotate(34deg);
  }
  .screw-rot-2 {
    transform: rotate(-52deg);
  }
  .screw-rot-3 {
    transform: rotate(78deg);
  }
  .screw-rot-4 {
    transform: rotate(-18deg);
  }

  .chassis-ground-shadow {
    position: absolute;
    bottom: -14px;
    left: 2%;
    right: 2%;
    height: 22px;
    background: radial-gradient(
      ellipse at center,
      rgba(0, 0, 0, 0.48) 0%,
      rgba(0, 0, 0, 0.16) 55%,
      transparent 80%
    );
    filter: blur(5px);
    z-index: -1;
    pointer-events: none;
  }

  @media (max-width: 600px) {
    .chassis-front-face {
      padding: 10px 1.2rem 1.8rem;
    }
  }
</style>
