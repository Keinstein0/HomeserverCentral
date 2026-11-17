import defaultPinSrc from './../../assets/pins/Pin-01.png';

/**
 * A recolorable pushpin.
 *
 * Create instances in your script and pass them to components that
 * support pins (PaperNote, PhotoNote):
 *
 *   const pin = new Pin('#3b82f6');
 *   <PaperNote {pin}>...</PaperNote>
 */
export class Pin {
  readonly src: string;
  readonly color: string;
  readonly size: number;
  /** Center of the pin head as a fraction of the artwork — the needle
   *  and shadow sit far off the geometric middle, so anything that
   *  needs the visible head (PinView placement, thread anchoring)
   *  uses this instead of the image center. */
  readonly anchor = { x: 0.723, y: 0.361 };
  /** Natural artwork dimensions; PinView passes them to the <img> as
   *  width/height attributes so the layout box is final before the
   *  bitmap arrives (no reflow when the pin image loads). */
  readonly artwork = { width: 450, height: 352 };
  /** Unique SVG filter id — one per instance so colors never bleed across pins */
  readonly filterId = `pin-tint-${Math.random().toString(36).slice(2, 9)}`;

  constructor(color = '#d90000', size = 44, src: string = defaultPinSrc) {
    this.color = color;
    this.size = size;
    this.src = src;
  }
}
