/**
 * Debug utilities for MIDINecromancer.
 *
 * Enable debug logging via localStorage flags:
 * - midinecromancer:debug:gen - Generation debugging
 * - midinecromancer:debug:playback - Playback debugging
 * - midinecromancer:debug:polyrhythm - Polyrhythm debugging
 * - midinecromancer:debug:muteSolo - Mute/solo debugging
 */

export const DEBUG_GEN =
  typeof window !== "undefined" &&
  (localStorage.getItem("midinecromancer:debug:gen") === "true" || import.meta.env.DEV);

export const DEBUG_PLAYBACK =
  typeof window !== "undefined" &&
  (localStorage.getItem("midinecromancer:debug:playback") === "true" || import.meta.env.DEV);

export const DEBUG_POLYRHYTHM =
  typeof window !== "undefined" &&
  (localStorage.getItem("midinecromancer:debug:polyrhythm") === "true" || import.meta.env.DEV);

export const DEBUG_MUTE_SOLO =
  typeof window !== "undefined" &&
  (localStorage.getItem("midinecromancer:debug:muteSolo") === "true" || import.meta.env.DEV);

export function debugLog(category: "gen" | "playback" | "polyrhythm" | "muteSolo", ...args: any[]) {
  const enabled =
    (category === "gen" && DEBUG_GEN) ||
    (category === "playback" && DEBUG_PLAYBACK) ||
    (category === "polyrhythm" && DEBUG_POLYRHYTHM) ||
    (category === "muteSolo" && DEBUG_MUTE_SOLO);

  if (enabled) {
    console.log(`[Debug:${category}]`, ...args);
  }
}
