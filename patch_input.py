from pathlib import Path

# 1) GKD350H L+R long-press menu
p = Path("fceux/src/drivers/dingux-sdl/input.cpp")
s = p.read_text()

old = """\t// Power flick (SDLK_HOME) to enter GUI
\tif (_keyonly(DINGOO_L2)
\t\t|| MenuRequested) {
"""

new = """\t// Power flick (SDLK_HOME) / L2 to enter GUI.
\t// GKD350H intercepts POWER and has no L2/R2.
\t// Hold L+R for 300 ms to open the menu and avoid accidental triggers.
\tstatic Uint32 gkd350h_lr_started = 0;
\tstatic bool gkd350h_lr_latched = false;
\tbool gkd350h_lr_menu = false;
\tconst bool gkd350h_lr_pressed =
\t\tispressed(DINGOO_L) && ispressed(DINGOO_R);

\tif (gkd350h_lr_pressed) {
\t\tif (!gkd350h_lr_started)
\t\t\tgkd350h_lr_started = SDL_GetTicks();
\t\telse if (!gkd350h_lr_latched &&
\t\t\t(SDL_GetTicks() - gkd350h_lr_started >= 300)) {
\t\t\tgkd350h_lr_menu = true;
\t\t\tgkd350h_lr_latched = true;
\t\t}
\t} else {
\t\tgkd350h_lr_started = 0;
\t\tgkd350h_lr_latched = false;
\t}

\tif (_keyonly(DINGOO_L2)
\t\t|| MenuRequested
\t\t|| gkd350h_lr_menu) {
\t\tif (gkd350h_lr_menu) {
\t\t\tresetkey(DINGOO_L);
\t\t\tresetkey(DINGOO_R);
\t\t}
"""

if old not in s:
    raise SystemExit("Expected FCEUX OpenDingux menu block not found")
p.write_text(s.replace(old, new, 1))

# 2) GKD350H display defaults: hardware scaling, 4:3, nearest filter.
p = Path("fceux/src/drivers/dingux-sdl/config.cpp")
s = p.read_text()
s = s.replace(
    'config->addOption(\'f\', "fullscreen", "SDL.Fullscreen", 0);',
    'config->addOption(\'f\', "fullscreen", "SDL.Fullscreen", 1); // GKD350H optimized: hardware scaling'
)
s = s.replace(
    'config->addOption("SDL.VideoFilter", 2);',
    'config->addOption("SDL.VideoFilter", 0); // GKD350H optimized: nearest/sharp'
)
p.write_text(s)

# 3) Graceful handling of launcher/system termination.
#    The signal handler only sets a sig_atomic_t flag. All cleanup remains
#    in the normal main loop and therefore stays async-signal-safe.
p = Path("fceux/src/drivers/dingux-sdl/dingoo.cpp")
s = p.read_text()

anchor = """static void DriverKill(void);
"""
insert = """static void DriverKill(void);

static volatile sig_atomic_t gkd350h_terminate_requested = 0;

static void GKD350H_TerminationHandler(int sig)
{
\t(void)sig;
\tgkd350h_terminate_requested = 1;
}
"""
if anchor not in s:
    raise SystemExit("Could not find DriverKill declaration")
s = s.replace(anchor, insert, 1)

main_anchor = """int main(int argc, char *argv[]) {

\tint error;
"""
main_new = """int main(int argc, char *argv[]) {

\tint error;

\t// GKD350H launcher/system may terminate apps without generating SDL_QUIT.
\t// Convert catchable termination signals into a normal FCEUX shutdown path.
\tsignal(SIGTERM, GKD350H_TerminationHandler);
\tsignal(SIGINT, GKD350H_TerminationHandler);
\tsignal(SIGHUP, GKD350H_TerminationHandler);
"""
if main_anchor not in s:
    raise SystemExit("Could not find main() anchor")
s = s.replace(main_anchor, main_new, 1)

loop_old = """\twhile(GameInfo)
\t{
\t\tDoFun(frameskip,periodic_saves);
\t}
"""
loop_new = """\twhile(GameInfo && !gkd350h_terminate_requested)
\t{
\t\tDoFun(frameskip,periodic_saves);
\t}
"""
if loop_old not in s:
    raise SystemExit("Could not find game loop")
s = s.replace(loop_old, loop_new, 1)

p.write_text(s)

print("Applied GKD350H optimized defaults, 300 ms L+R menu hold, and graceful system-exit handling")
