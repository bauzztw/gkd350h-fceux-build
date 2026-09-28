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


# 4) Disable GKD350H-unsafe runtime aspect toggle (L+X).
p = Path("fceux/src/drivers/dingux-sdl/input.cpp")
s = p.read_text()

old = """\t\tif(_keyonly(DINGOO_X)) { // R + X Pixel Astect Ratio
\t\t\tif (s_fullscreen == 1) {
\t\t\t\tint aspect_select;
\t\t\t\tchar as_message[4];
\t\t\t\tg_config->getOption("SDL.AspectSelect", &aspect_select);
\t\t\t\taspect_select = (aspect_select + 1) % 3;
\t\t\t\tg_config->setOption("SDL.AspectSelect", aspect_select);
\t\t\t\tswitch (aspect_select) {
\t\t\t\tcase 0: snprintf(as_message,4,"1:1"); break;
\t\t\t\tcase 1: snprintf(as_message,4,"8:7"); break;
\t\t\t\tcase 2: 
\t\t\t\tdefault: snprintf(as_message,4,"4:3"); break;
\t\t\t\t}
\t\t\t\tFCEU_DispMessage("Aspect %s",0,as_message);
\t\t\t\tFCEUD_DriverReset();
\t\t\t\tdingoo_clear_video();
\t\t\t}
\t\t\tresetkey(DINGOO_X);
\t\t}
"""

new = """\t\tif(_keyonly(DINGOO_X)) { // GKD350H: disable runtime aspect toggle
\t\t\tFCEU_DispMessage("Aspect locked: 4:3", 0);
\t\t\tresetkey(DINGOO_X);
\t\t}
"""

if old not in s:
    raise SystemExit("Could not find L+X aspect toggle block")
p.write_text(s.replace(old, new, 1))

print("Disabled unsafe L+X runtime video reset on GKD350H")


# 5) Disable GKD350H-unsafe runtime fullscreen toggle (R+X).
p = Path("fceux/src/drivers/dingux-sdl/input.cpp")
s = p.read_text()

old = """\t\tif(_keyonly(DINGOO_X)) { // R + X  toggle fullscreen
\t\t\textern int s_fullscreen; // from dingoo_video.cpp
\t\t\ts_fullscreen = (s_fullscreen + 1) % 5;
\t\t\tg_config->setOption("SDL.Fullscreen", s_fullscreen);
\t\t\tFCEUD_DriverReset();
\t\t\tdingoo_clear_video();
\t\t\tresetkey(DINGOO_X);
\t\t}
"""

new = """\t\tif(_keyonly(DINGOO_X)) { // GKD350H: disable runtime fullscreen toggle
\t\t\tFCEU_DispMessage("Video mode locked", 0);
\t\t\tresetkey(DINGOO_X);
\t\t}
"""

if old not in s:
    raise SystemExit("Could not find R+X fullscreen toggle block")
p.write_text(s.replace(old, new, 1))

print("Disabled unsafe R+X runtime fullscreen reset on GKD350H")


# 6) Prefer external SD card for all FCEUX config/save data.
p = Path("fceux/src/drivers/dingux-sdl/config.cpp")
s = p.read_text()

old = """#else
\tchar *home = getenv("HOME");
\tif (home) {
\t\tdir = std::string(home) + "/.fceux";
\t} else {
#ifdef WIN32
"""

new = """#else
\t// GKD350H: prefer external SD card so settings survive internal-storage issues.
\tif (access("/media/sdcard", W_OK) == 0) {
\t\tdir = "/media/sdcard/.fceux-gkd350h";
\t} else if (access("/media/SDCARD", W_OK) == 0) {
\t\tdir = "/media/SDCARD/.fceux-gkd350h";
\t} else {
\t\tchar *home = getenv("HOME");
\t\tif (home) {
\t\t\tdir = std::string(home) + "/.fceux";
\t\t} else {
#ifdef WIN32
"""

if old not in s:
    raise SystemExit("Could not find GetBaseDirectory external-storage anchor")
s = s.replace(old, new, 1)

old_tail = """#else
\t\tdir = "";
#endif
\t}
#endif
}
"""
new_tail = """#else
\t\t\tdir = "";
#endif
\t\t}
\t}
#endif
}
"""
if old_tail not in s:
    raise SystemExit("Could not find GetBaseDirectory closing block")
s = s.replace(old_tail, new_tail, 1)

# Default ROM browser path: external SD root when available.
s = s.replace(
    'config->addOption("_lastopenfile", "SDL.LastOpenFile", home_dir);',
    'config->addOption("_lastopenfile", "SDL.LastOpenFile", access("/media/sdcard", R_OK) == 0 ? "/media/sdcard" : (access("/media/SDCARD", R_OK) == 0 ? "/media/SDCARD" : home_dir));'
)

p.write_text(s)

# 7) Hard-code requested default gamepad mapping for GKD350H:
# NES A -> physical B (SDLK_LALT)
# NES B -> physical A (SDLK_LCTRL, retained)
# Turbo A -> physical X (SDLK_SPACE)
# Turbo B -> physical Y (SDLK_LSHIFT)
p = Path("fceux/src/drivers/dingux-sdl/input.cpp")
s = p.read_text()

old = """\t{  SDLK_LCTRL, SDLK_LALT, SDLK_ESCAPE, SDLK_RETURN, SDLK_UP, SDLK_DOWN, SDLK_LEFT, SDLK_RIGHT, SDLK_SPACE, SDLK_LSHIFT },
"""
new = """\t{  SDLK_LALT, SDLK_LCTRL, SDLK_ESCAPE, SDLK_RETURN, SDLK_UP, SDLK_DOWN, SDLK_LEFT, SDLK_RIGHT, SDLK_SPACE, SDLK_LSHIFT },
"""
if old not in s:
    raise SystemExit("Could not find default GamePad mapping")
s = s.replace(old, new, 1)
p.write_text(s)

print("External SD config enabled; defaults: A=B, B=A, TurboA=X, TurboB=Y")
