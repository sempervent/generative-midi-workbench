# Troubleshooting

This document covers common issues and how to diagnose and fix them.

## Middle Panes Not Rendering

### Symptoms

- The middle track displays (Drums/Chords/Bass/Melody) appear blank
- Chord timeline shows chords but the middle Chords pane is empty
- Panes don't update when changing bars range, toggling loop, or generating content

### Diagnosis Steps

1. **Check Browser Console**
   - Open DevTools (F12) and check for errors
   - Look for `NaN`, `undefined`, or `TypeError` messages
   - Check for timing conversion errors

2. **Enable Diagnostics Overlay**
   - Press `Ctrl+Shift+D` (or `Cmd+Shift+D` on Mac) in the Composer view
   - This shows:
     - Number of events per track
     - Ticks per bar calculation
     - Total bars
     - Visible time window

3. **Check Network Tab**
   - Verify API responses for `/api/v1/projects/{id}/arrangement`
   - Ensure `tracks[].clips[].notes[]` and `chord_events[]` are populated
   - Check that all required fields are present

4. **Verify Data Shape**
   - In browser console, inspect `arrangement.value` in ComposerView
   - Ensure `chord_events` have all expressive fields:
     - `start_tick`, `duration_tick`, `duration_beats`
     - `intensity`, `voicing`, `is_enabled`, etc.

### Common Causes

#### Data Shape Mismatch

**Problem**: Backend returns new fields but frontend types/parsing don't match.

**Fix**: 
- Compare `backend/src/midinecromancer/schemas/arrangement.py` with `frontend/src/types.ts`
- Ensure all fields in `ChordEventInArrangement` are in `ChordEvent` interface
- Add runtime validation in dev mode

#### Timing Conversion Bug

**Problem**: Hardcoded ticks-per-bar (e.g., `1920`) doesn't match actual time signature.

**Fix**:
- Use `frontend/src/music/timing.ts` utilities
- Never hardcode `1920` or assume 4/4 time
- Always pass `timeSignatureNum` and `timeSignatureDen` to components

#### Container Sizing Issue

**Problem**: Canvas/container has `height: 0` or `width: 0` due to CSS.

**Fix**:
- Inspect computed styles in DevTools
- Ensure parent containers have explicit height
- Use `ResizeObserver` to handle dynamic sizing
- Check for `overflow: hidden` clipping content

#### Reactivity Bug

**Problem**: State changes don't trigger re-render.

**Fix**:
- Ensure computed properties depend on reactive sources
- Use immutable updates (replace arrays, don't mutate)
- Check Vue DevTools for reactive dependencies

### Verification

After fixes, verify:

1. ✅ All panes show content when data exists
2. ✅ Changing bars range updates all panes
3. ✅ No console errors or warnings
4. ✅ No `NaN` or `undefined` in tick calculations
5. ✅ Resizing window doesn't blank panes
6. ✅ Diagnostics overlay shows correct values

## Chord Events Not Showing

### Symptoms

- Chord timeline (right panel) shows chords
- Middle Chords pane is blank
- Chords exist in API response

### Diagnosis

1. Check `ChordLane.vue` computed `chords`:
   ```javascript
   // In browser console
   chords.value.length // Should be > 0
   chords.value[0] // Should have all fields
   ```

2. Verify timing calculation:
   ```javascript
   // Check absolute start tick calculation
   chord.start_tick // Should be valid number
   clip.start_bar // Should be valid
   ```

3. Check CSS positioning:
   - Inspect `.chord-block` elements
   - Verify `left` and `width` are valid pixel values
   - Check for `display: none` or `opacity: 0`

### Fix

- Ensure `chord.is_enabled !== false` filter is correct
- Verify `clipLocalToProjectTicks` includes offsets
- Check container width calculation in `laneStyle`

## Notes Not Rendering

### Symptoms

- PianoRoll components show empty grids
- Notes exist in API response

### Diagnosis

1. Check `PianoRoll.vue` computed `visualEvents`:
   ```javascript
   visualEvents.value.length // Should match note count
   ```

2. Verify timing:
   - Notes should use `notesToVisualEvents` adapter
   - Check `startTick` and `durationTick` are valid

3. Check pitch range:
   - If all notes have same pitch, range might be 0
   - This causes division by zero in positioning

### Fix

- Use centralized timing utilities
- Add validation for edge cases (empty arrays, single pitch)
- Ensure proper time signature propagation

## Performance Issues

### Symptoms

- UI freezes when rendering many events
- Slow updates when changing bars range

### Diagnosis

- Check number of events per track
- Profile with Chrome DevTools Performance tab
- Look for expensive computed properties

### Fix

- Implement virtual scrolling for large datasets
- Debounce bar range updates
- Cache computed values where appropriate
- Use `requestAnimationFrame` for canvas updates

