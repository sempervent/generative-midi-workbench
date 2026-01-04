/**
 * Audio context management utility.
 * Ensures Tone.js AudioContext is started only after user gesture.
 */

import * as Tone from "tone";

let audioStarted = false;
let audioStartPromise: Promise<void> | null = null;

/**
 * Ensure AudioContext is started (only on user gesture).
 * This should be called before any audio playback.
 * It will only start the AudioContext once per session.
 *
 * @returns Promise that resolves when AudioContext is ready
 */
export async function ensureAudioStarted(): Promise<void> {
  if (audioStarted) {
    return Promise.resolve();
  }

  if (audioStartPromise) {
    return audioStartPromise;
  }

  audioStartPromise = Tone.start().then(() => {
    audioStarted = true;
    audioStartPromise = null;
  });

  return audioStartPromise;
}

/**
 * Reset the audio started flag (for testing or manual control).
 */
export function resetAudioStarted(): void {
  audioStarted = false;
  audioStartPromise = null;
}
