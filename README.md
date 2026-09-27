# GKD350H FCEUX Build

Custom FCEUX 2.6.6 OpenDingux 2014 build for GKD350H.

Change:
- Press L + R together to open the FCEUX handheld menu.
- Keep the existing FCEUX hotkeys and menu behavior otherwise unchanged.

Base source:
- plrguez/fceux-for-retrogame, branch: opendingux

中文說明
- L + R 按住約 0.3 秒進入選單
- Hardware scaling
- 4:3 畫面比例
- Nearest 清晰濾鏡
- Frameskip 0
- 新增 SIGTERM / SIGINT / SIGHUP 安全退出處理
- 系統要求結束 FCEUX 時，盡量先正常關閉遊戲、視訊與音效，再退出

opk檔案位置：
SD卡
.├─ apps
.│  ├─ fceux_gcw0-2.6.6.opk
.│  └─ nestopia.opk
.│
.└─ roms
.   └─ nes
.      ├─ game1.nes
.      ├─ game2.nes
.      └─ ...
