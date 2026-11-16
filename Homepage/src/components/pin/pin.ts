import defaultPinSrc from './assets/Pin-01.png';

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
  /** Unique SVG filter id — one per instance so colors never bleed across pins */
  readonly filterId = `pin-tint-${Math.random().toString(36).slice(2, 9)}`;

  constructor(color = '#d90000', size = 44, src: string = defaultPinSrc) {
    this.color = color;
    this.size = size;
    this.src = src;
  }
}
