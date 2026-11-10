Dreams Imp for Windows — 1.0.7

Extract the whole ZIP, then double-click Dreams Imp.exe.
Tap or click an Imp to set it as your cursor. The dropdown filters categories.
The original size-1 sideways Imp carousel is the only layout.
Drag with one finger, or use the mouse wheel.
Opening the app or filtering categories does not change your cursor.
Minimize the picker to keep using the cursor; close it to
quit and restore the Windows cursor. No commands, Python installation, emulator,
or running copy of Dreams are needed.

149 presets from the available Dreams game revision are included: 147 named
Imps/specials plus 2 labelled internal presets. Classic Imps includes Clown;
Halloween includes Halloween Clown. Other collections include Art's Dream,
Halloween, Dream Queen and the Impys. Later game revisions may contain more.

This uses extracted Dreams animation data, native motion/particle routines and
ported original shaders. Windows mouse events drive the reactions. It is a
live, click-through cursor overlay, not a GIF. The render area is padded for
movement; the Imp is approximately 5 times the original cursor size. Animation
and morph speed are 50%; drawing targets 120 Hz, subject to GPU/CPU load.
The picker contains live Imps in purple space and a rounded category selector,
using bundled Source Sans Pro. Each visible Imp is simulated
and drawn by the original game routines and shaders, with its own frame history.
Offscreen Imps stop rendering; minimizing the picker pauses its renderer.
Original Imp lighting and colours are retained. The picker adds no glow.
Cursor hover bloom remains confined to the antenna tip.
The picker uses high-resolution frame timing and prepares images outside its
scroll/input loop. Original native morph calculations and shader pixels are retained.

Requirements
  Windows 10/11 x64, an AVX2-capable CPU and a current Vulkan 1.3 graphics driver.
  The GPU must expose fragment shader barycentrics, robustness2, depth clip,
  explicit workgroup memory layout and the required 32-lane subgroup features.
  GPU selection is not AMD-only. Local GPU testing used AMD Radeon 8060S;
  NVIDIA and Intel hardware have not been physically tested with this package.
  If required GPU features are absent, the app reports the error without hiding
  the ordinary cursor. Update your graphics driver before trying again.

Windows keeps control of the cursor on secure desktops and some exclusive
fullscreen applications. The overlay does not bypass those restrictions.
Custom cursors used by individual applications may still be visible there.
The Imp hides when an application hides the mouse cursor and returns when the
application shows it again.

The app saves the selected Imp and diagnostic logs in:
  %LOCALAPPDATA%\Dreams Imp
It does not install a service, alter Dreams saves or contact a server.
A separate watchdog restores the Windows cursor if the renderer exits/crashes.

Unofficial fan software, not affiliated with Media Molecule or Sony.
Read THIRD_PARTY_NOTICES.txt before redistributing game-derived assets/code.
