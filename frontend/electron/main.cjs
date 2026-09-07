const { app, BrowserWindow, ipcMain, Menu, screen } = require("electron");
const path = require("path");

const RENDERER_URL = process.env.AMADEUS_RENDERER_URL || "http://127.0.0.1:5173/";
const WINDOW_WIDTH = 520;
const WINDOW_HEIGHT = 720;

app.setName("Maho Overlay");
app.commandLine.appendSwitch("enable-transparent-visuals");

function overlayBounds() {
  const { workArea } = screen.getPrimaryDisplay();
  return {
    width: WINDOW_WIDTH,
    height: WINDOW_HEIGHT,
    x: Math.round(workArea.x + workArea.width - WINDOW_WIDTH - 28),
    y: Math.round(workArea.y + workArea.height - WINDOW_HEIGHT - 16),
  };
}

function createOverlay() {
  const bounds = overlayBounds();
  const win = new BrowserWindow({
    ...bounds,
    frame: false,
    transparent: true,
    hasShadow: false,
    alwaysOnTop: true,
    skipTaskbar: false,
    resizable: false,
    fullscreenable: false,
    minimizable: false,
    maximizable: false,
    acceptFirstMouse: true,
    roundedCorners: false,
    backgroundColor: "#00000000",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      backgroundThrottling: false,
    },
  });

  win.setAlwaysOnTop(true, "floating");
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  win.setIgnoreMouseEvents(true, { forward: true });
  win.setMenuBarVisibility(false);
  win.setHasShadow(false);
  win.setBackgroundColor("#00000000");

  win.once("ready-to-show", () => win.showInactive());
  win.on("closed", () => app.quit());

  win.webContents.on("context-menu", () => {
    Menu.buildFromTemplate([
      { label: "Quit Maho Overlay", role: "quit" },
    ]).popup({ window: win });
  });

  void win.loadURL(RENDERER_URL);
  return win;
}

ipcMain.on("set-click-through", (event, ignore) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  if (!win) return;
  if (ignore) win.setIgnoreMouseEvents(true, { forward: true });
  else win.setIgnoreMouseEvents(false);
});

ipcMain.on("move-by", (event, dx, dy) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  if (!win) return;
  const [x, y] = win.getPosition();
  win.setPosition(
    Math.round(x + (Number(dx) || 0)),
    Math.round(y + (Number(dy) || 0)),
  );
});

ipcMain.on("quit", () => app.quit());

app.whenReady().then(() => {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {
      label: "Maho Overlay",
      submenu: [{ role: "quit", label: "Quit Maho Overlay" }],
    },
  ]));
  createOverlay();
});

app.on("window-all-closed", () => app.quit());
