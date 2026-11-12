# Dreams Imp source

The Windows download contains the complete runtime. Extract it and open Dreams Imp.exe.
No development tools or Dreams installation are needed to run it.

## Build

Use an x64 Visual Studio developer environment with clang-cl and the Windows SDK.
Set VULKAN_SDK to the Vulkan SDK directory and NLOHMANN_INCLUDE to the directory
containing nlohmann/json.hpp. Run native/build.cmd for the launcher and cursor renderer,
and native/ui/build.cmd for the button renderer. Run tools/build_portable_shaders.py
with --sdk PATH when rebuilding cursor SPIR-V; assembling the reference source alone
is insufficient because the AMD extension must be lowered. The package builder rejects
vendor-only SPIR-V imports. Python 3.12 and the Python packages
are bundled in the release ZIP; the Git checkout excludes that interpreter distribution.
Copy runtime/python from the Windows ZIP when building the checkout.

## Runtime

- runtime/app.py and sdl_picker.py: launcher, carousel and explicit cursor selection.
- runtime/desktop-imp.py: desktop actions and native animation selection.
- runtime/native-imp-motion.py, native_sparks.py, native_idle.py: native simulation bindings.
- runtime/live-imp-render.py and native/dreams-native-cursor/: cursor shader rendering.
- runtime/native_buttons.py, native_ui_pack.py and native/ui/: original button material,
  geometry packing, ported UI shaders, bloom and postprocessing.
- runtime/native_surprise.py and character_store.py: native appearance generation.
- runtime/reference-state/, native-code/, characters/ and shader-inputs/: bundled native
  inputs and game-derived data. These are required by the standalone runtime.
- runtime/picker_window.py, win-imp-overlay.py and cursor_guard.py: window management
  and restoring the Windows cursor if the overlay exits.

The picker and cursor run separately. Closing the picker releases previews while
keeping the chosen cursor running. Settings are outside the installation folder.

## Verification and limits

The packaged runtime is tested from a separate extracted directory, using its bundled
interpreter and fresh local settings. Native cursor frames, UI transitions, catalogue
assets and relative asset paths are checked before publication. The UI material-cache
repair reproduces frozen transitions with the old zero global, then verifies the
captured 0.1 value restores the transition and return to the base material.

GPU tests on the author's AMD Radeon 8060S do not establish compatibility on all GPUs.
NVIDIA and Intel depend on their advertised Vulkan features and have not been physically
tested here. Native assets and shaders do not establish complete visual or event parity:
root pointer transforms still include an interpolation of captured pitch samples, and
Windows events adapt game reactions. The cloud backdrop is a captured animation loop.

This is unofficial fan software. See THIRD_PARTY_NOTICES.txt for ownership and licences.
