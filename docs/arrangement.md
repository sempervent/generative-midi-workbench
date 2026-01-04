# Arrangement Panel

The Arrangement Panel provides a DAW-like interface for organizing and editing clips across your project's tracks.

## Contextual Editing

The Arrangement Panel supports **contextual editing** - click directly on any clip or empty space to open a smart popover that allows you to edit, regenerate, transform, and audition changes without leaving the arrangement view.

### Click Behavior

**Click on existing card**
- Opens Track Popover anchored to the card
- Popover contains all editing controls for that clip

**Click on empty space**
- Opens "Create New" popover for that lane type
- Allows you to create a new clip at the clicked position

### Track Popover

The Track Popover is organized into four collapsible sections:

#### Section A: Overview
- Track kind icon + name
- Start bar / length display (editable)
- Intensity meter (editable via slider or vertical drag)
- Mute / Solo / Lock toggles
- Quick actions: Duplicate, Half-time, Double-time, Delete

#### Section B: Generate / Regenerate
- Seed display (lock/unlock)
- Regenerate button with preview
- Variation knob (0-1)
- Scope selector (Rhythm only, Notes only, Velocity only, Timing only, All)
- "Keep structure" checkbox
- **Preview mode**: Changes preview immediately without committing
- **Apply**: Commits changes to database
- **Cancel**: Reverts to original state

#### Section C: Transform
- Time scaling: Half time, Double time
- Offset: Bars (+ / -) and fine offset (beats)
- Swing: Amount and basis (8th / 16th)
- Density slider (for beats/melody/bass)

All transforms preview live and are reversible before applying.

#### Section D: Advanced (Kind-Specific)

**Beats**
- Style selector (trap / boom bap / minimal / etc.)
- Hat mode (straight / roll / skip)
- Ghost note toggle
- Pause probability
- Accent strength

**Chords**
- Projection / voicing selector
- Inversion policy
- Gate %
- Strum (ms)
- Humanize (ms)

**Bass**
- Follow chords toggle
- Octave range
- Movement (static → walking)
- Rhythm source (chords / drums / grid)

**Melody**
- Scale lock
- Register range
- Leapiness
- Motif repeat probability

## Overview

The Arrangement Panel displays all clips in your project organized by track lanes (Beats, Chords, Bass, Melody). Each clip appears as a card that can be dragged, resized, and edited directly.

## Interaction & Shortcuts

### Card Interactions

#### Drag to Move
- Click and drag a card horizontally to change its start position
- Cards snap to the current grid setting
- Hold **Shift** while dragging to snap to 1 beat (fine control)
- Hold **Alt/Option** while dragging for free movement (quantized on drop)
- A ghost outline shows the snapped position while dragging
- Tooltip displays: "Start: bar X"

#### Resize
- Drag the left edge to adjust both start position and length
- Drag the right edge to adjust length only
- Minimum length: 1 beat (or 1 bar if system enforces bars)
- Resize respects grid snap settings
- Tooltip displays: "Length: X bars"

#### Multi-Select
- **Shift+Click** to add/remove cards from selection
- Selected cards are highlighted with a blue border
- Multi-select works within the same lane only
- Selected cards can be dragged together, duplicated, or scaled

### Grid Control

The grid selector in the panel header controls snap resolution:
- **1 bar** (default): Snap to whole bars
- **1/2**: Snap to half bars
- **1/4**: Snap to quarter bars
- **1 beat**: Snap to individual beats
- **Off**: Free movement (quantized to nearest beat on drop)

Grid affects:
- Drag-to-move
- Resize operations
- Duplication offsets
- Visual grid lines

### Zoom & Navigation

- **Mouse wheel + Cmd/Ctrl**: Zoom in/out (centered on cursor)
- **Trackpad pinch**: Zoom (if supported)
- **Zoom controls**: Use +/- buttons or reset button in header
- Grid lines adapt to zoom level (fade out when zoomed far out)

### Duplication

Three ways to duplicate a clip:
1. **Context menu** → Duplicate
2. **Cmd/Ctrl + D**: Duplicate selected clip(s)
3. **Alt-drag**: Drag with Alt pressed to create a copy

Duplicated clips are placed immediately after the original (respecting grid) and inherit all parameters.

### Time Scaling

From context menu or editor:
- **Half Time**: Doubles clip length, adjusts rhythm density
- **Double Time**: Halves clip length, adjusts rhythm density inversely

Time scaling animates so you can see the change.

### Intensity & Expression

Intensity is visualized through:
- Card opacity (muted cards are dimmed)
- Saturation (higher intensity = more vibrant)
- Border thickness (proportional to intensity)

To adjust intensity:
- Click and drag vertically on the intensity badge
- Hold **Shift** for fine control (0.01 steps)
- Tooltip shows numeric value

### Quick Toggles

On card hover, quick action buttons appear:
- **🔇 Mute**: Toggle mute state
- **📋 Duplicate**: Quick duplicate

### Context Menu

Right-click a card to access:
- Duplicate
- Half Time
- Double Time
- Mute/Unmute

### Keyboard Shortcuts

**Global (Arrangement Panel)**
- **Cmd/Ctrl + D**: Duplicate selected clip(s)
- **Escape**: Close popover/context menu, deselect all
- **Delete**: Delete selected clips (if implemented)
- **Shift + Click**: Multi-select clips

**In Track Popover**
- **Escape**: Close popover (with unsaved changes warning)
- **Cmd/Ctrl + Enter**: Apply changes
- **[ / ]**: Nudge start position by grid (when focused on start bar input)
- **Arrow keys**: Navigate inputs (↑/↓ for intensity, ←/→ for start bar)

### Editor Modal Shortcuts

When the clip editor is open:
- **←/→**: Nudge start position by grid
- **↑/↓**: Adjust intensity
- **H**: Half time
- **D**: Double time
- **Cmd/Ctrl + D**: Duplicate
- **Escape**: Close editor

## Visual Feedback

### Animations
- All state changes animate smoothly (150-220ms ease-out)
- Cards slide into position after drag
- Cards stretch during resize
- Duplicated cards pop in
- Invalid moves trigger a subtle shake animation

### Error Handling
- Invalid moves (overlaps, out-of-range) show shake animation
- Tooltip explains why the move was rejected
- Cards snap back to valid position

### Locked Cards
- Locked cards show a lock icon
- Drag and resize are disabled for locked cards
- Tooltip explains on hover

## Performance

The arrangement panel is optimized for performance:
- No unnecessary re-renders during drag
- Grid lines computed once per zoom level
- Smooth 60fps interactions
- Efficient event handling

## Troubleshooting

### Clicks Not Opening Popover

If clicking on arrangement cards doesn't open the popover:

1. **Check browser console** for errors (F12 → Console)
2. **Verify API connection**: Ensure backend is running and accessible
3. **Check network tab**: Look for failed requests to `/api/v1/projects/{id}/arrangement/panel`
4. **Refresh the page**: Sometimes state can get out of sync

### AudioContext Warnings

If you see "AudioContext was prevented from starting automatically" warnings:

- This is **normal and expected** - browsers require user interaction before starting audio
- The warning appears when Tone.js is imported but not yet started
- Audio will work correctly once you click Play or Preview (which calls `Tone.start()`)
- These warnings do not affect functionality and can be safely ignored

### Empty Arrangement Panel

If the arrangement panel shows "No arrangement data":

1. **Generate content**: Use the generation controls to create beats, chords, bass, or melody
2. **Check project**: Ensure you're viewing a project that has tracks and clips
3. **Refresh**: Click the refresh button in the arrangement panel header

## Best Practices

1. **Use grid snap** for musical alignment
2. **Multi-select** for batch operations
3. **Zoom out** to see the full arrangement
4. **Use context menu** for quick actions
5. **Adjust intensity** to create dynamic arrangements
