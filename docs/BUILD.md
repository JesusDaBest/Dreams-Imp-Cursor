# Dreams Imp

Portable Windows cursor app using the original Dreams Imp assets, motion
routines and ported Vulkan shaders. Tap or click an Imp to set it as your cursor.
Opening the app or filtering categories does not activate or change the cursor.

## Run

Extract the complete Windows package, open `Dreams Imp.exe`, and tap an Imp.
Drag with one finger to scroll. Close the picker to restore the Windows cursor.
The included runtime contains Python, Tk and Pillow. No development tools are
needed to run it, and Dreams does not need to be open.

## Build the native launcher and renderer

Use an x64 Visual Studio developer command prompt with clang-cl and rc available.
Set `VULKAN_SDK` to your installed Vulkan SDK and `NLOHMANN_INCLUDE` to the folder
containing `nlohmann/json.hpp`. Run `native/build.cmd`.

The tested toolchain was Visual Studio 2022 Build Tools (clang-cl), Vulkan SDK
1.4.350.0 and Python 3.12. The launcher and renderer use the static C++ runtime.
The Source ZIP on the release page includes the built shaders and all runtime dependencies. This Git repository excludes the bundled Python runtime and compiled executable/DLL. To build the repository, copy runtime/python from the Windows ZIP, or use Python 3.12 with Tk and Pillow for development. Run python runtime/app.py after building the native renderer; the graphical launcher expects the bundled runtime.

## Source map

- `runtime/app.py`: explicit cursor activation, appearance selection and settings.
- `runtime/picker_controls.py`: Source Sans Pro category and grid controls.
- `runtime/gallery_client.py`, `runtime/gallery_worker.py`: viewport-only live
  previews in a separate process, using original animation/particle routines
  and shaders. Every visible Imp has its own simulation and temporal history;
  the render context and shader resources are shared. Minimized pickers pause.
- `runtime/desktop-imp.py`: mouse reactions, timing and desktop render loop.
- `runtime/native-imp-motion.py`: bindings to Dreams' original CPU routines.
- `runtime/verify-native-imp-*.py`: native animation, body and face bindings.
- `runtime/win-imp-overlay.py`: click-through window, input and cursor recovery.
- `runtime/live-imp-render.py`: Vulkan renderer binding.
- `native/dreams-native-cursor/verify-native-imp-draw.cpp`: drawing and resolve.
- `native/shaders/`: shader disassembly/GLSL reference, including portable variants.
- `runtime/shader-inputs/`, `runtime/eye-desktop.spv`, `runtime/stick-desktop.spv`:
  the SPIR-V actually loaded by the renderer.
- `runtime/characters/`: 149 decoded game presets and native face bindings.
- `tools/render_catalog.py`: offscreen GPU rendering test for all presets.
- `tests/test_live_gallery.py`: all-preset live rendering, viewport changes,
  minimize and shutdown checks. `tests/test_gallery_history.py` compares
  interleaved previews byte-for-byte with independent cursor shader draws.
- `tools/decode_characters.py`, `tools/prepare_character_bindings.py`: extraction
  provenance; these require local game/research inputs and are not user setup.

The portable fragment variant lowers the AMD trinary instruction to equivalent
core operations. The resolve variant preserves the original two 32-lane groups.
The original vertex/eye/antenna paths are retained. Assemble portable variants:

```
spirv-as --target-env spv1.3 native/shaders/khr-fragment.spvasm -o runtime/shader-inputs/PrimImpOverBokehPS-desktop-draw.spv
spirv-as --target-env spv1.3 native/shaders/wave32-resolve.spvasm -o runtime/shader-inputs/PrimImpTAAUpdate-desktop-resolve.spv
```

## Verification and limitations

All 149 presets were decoded with the game loader and native face setup routines.
The complete catalog passed 3,576 offscreen GPU frames on AMD Radeon 8060S.
The desktop renderer reported its first displayed frame in the local live check.
Twelve startup, gesture, explicit-selection and process-handover tests passed. The packaged renderer also passed
96 offscreen frames covering eight motions/expressions for the Clown, launched
from an unrelated working directory with the bundled Python runtime.
Thirteen desktop-access and visibility tests reproduce Windows error 5, verify that unavailable
input hides/pauses the overlay, and confirm that input resumes through the same
Windows API. It does not elevate or switch to a protected desktop.
They also cover application-hidden, null and touch-suppressed cursors, normal
transparent cursor replacements, custom cursors and hidden-to-visible transitions.
The final manual picker interaction check was interrupted by Escape. NVIDIA and
Intel hardware have not been physically tested; compatibility depends on driver
features, not a vendor-name check. This is not a claim of exact behavior of every
game revision or every Windows application.

Preset colours come from the decoded character data. Version 1.0.3 restores the
original 1.0.1 lighting inputs and all 149 original card images byte-for-byte.
The 1.0.2 body-light changes altered the intended appearance and were removed.
Displayed colours have not been compared against Dreams for every preset.

Hover bloom now uses only a separate draw of the two native tip particles with the
original eye shader and bloom math. A 64-frame GPU test checks hover transitions,
unchanged output while hover is off, and no halo from bright body pixels.
The picker shows only Imps in purple space and a category dropdown. Its purple
background is separate UI artwork; the native thumbnails retain their aspect
ratio and colours. Version 1.0.5 changes the picker only, not the renderer.
Windows single-finger touch promotion drives drag scrolling; selection occurs
on a tap release, never during a scroll. Mouse-wheel scrolling is also available.

Runtime state is stored under `%LOCALAPPDATA%/Dreams Imp`; it is excluded from the
packages. `MANIFEST.sha256` identifies shipped files. Nothing is published by the
packaging script. Third-party/game-derived material is described separately in
`THIRD_PARTY_NOTICES.txt`; inclusion does not grant redistribution rights.
