from pathlib import Path

p = Path("fceux/src/drivers/dingux-sdl/input.cpp")
s = p.read_text()

old = """\t// Power flick (SDLK_HOME) to enter GUI
\tif (_keyonly(DINGOO_L2)
\t\t|| MenuRequested) {
"""

new = """\t// Power flick (SDLK_HOME) / L2 to enter GUI.
\t// GKD350H intercepts POWER and has no L2/R2, so use L+R too.
\tconst bool gkd350h_lr_menu =
\t\tispressed(DINGOO_L) && ispressed(DINGOO_R);

\tif (_keyonly(DINGOO_L2)
\t\t|| MenuRequested
\t\t|| gkd350h_lr_menu) {
\t\tresetkey(DINGOO_L);
\t\tresetkey(DINGOO_R);
"""

if old not in s:
    raise SystemExit("Expected FCEUX OpenDingux menu block not found")

p.write_text(s.replace(old, new, 1))
print("GKD350H L+R menu patch applied")
