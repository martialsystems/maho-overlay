const { app, BrowserWindow, ipcMain, Menu, screen } = require("electron");
const fs = require("fs");
const path = require("path");

const RENDERER_URL = process.env.AMADEUS_RENDERER_URL || "http://127.0.0.1:5173/";

const SIZES = {
  small: { width: 336, height: 468 },
  medium: { width: 448, height: 624 },
  large: { width: 560, height: 780 },
  xl: { width: 728, height: 1014 },
};
const SIZE_ORDER = ["small", "medium", "large", "xl"];
const SIZE_LABELS = {
  small: "Small",
  medium: "Medium",
  large: "Large",
  xl: "XL",
};
const DEFAULT_SIZE = "large";

app.setName("Maho Overlay");
app.commandLine.appendSwitch("enable-transparent-visuals");

let currentSizeId = DEFAULT_SIZE;

function sizeFile() {
  return path.join(app.getPath("userData"), "overlay-size.json");
}

function loadSizeId() {
  try {
    const raw = JSON.parse(fs.readFileSync(sizeFile(), "utf8"));
    if (raw && SIZES[raw.id]) return raw.id;
  } catch {
    // first run, or a bad file: Large
  }
  return DEFAULT_SIZE;
}

function saveSizeId(id) {
  try {
    fs.writeFileSync(sizeFile(), `${JSON.stringify({ id })}\n`);
  } catch {
    // size still applies for this session
  }
}

function fitSize(id, workArea) {
  const size = SIZES[id];
  let width = size.width;
  let height = size.height;
  const maxW = Math.max(160, workArea.width - 16);
  const maxH = Math.max(160, workArea.height - 16);
  if (width > maxW || height > maxH) {
    const scale = Math.min(maxW / width, maxH / height);
    width = Math.round(width * scale);
    height = Math.round(height * scale);
  }
  return { width, height };
}

function overlayBounds(id) {
  const { workArea } = screen.getPrimaryDisplay();
  const { width, height } = fitSize(id, workArea);
  return {
    width,
    height,
    x: Math.round(workArea.x + workArea.width - width - 28),
    y: Math.round(workArea.y + workArea.height - height - 16),
  };
}

function applySize(win, id) {
  if (!SIZES[id]) return;
  const { workArea } = screen.getDisplayNearestPoint({
    x: win.getBounds().x,
    y: win.getBounds().y,
  });
  const { width, height } = fitSize(id, workArea);
  const before = win.getBounds();
  const cx = before.x + before.width / 2;
  const cy = before.y + before.height / 2;
  let x = Math.round(cx - width / 2);
  let y = Math.round(cy - height / 2);
  x = Math.min(Math.max(workArea.x, x), workArea.x + workArea.width - width);
  y = Math.min(Math.max(workArea.y, y), workArea.y + workArea.height - height);
  win.setResizable(true);
  win.setBounds({ x, y, width, height });
  win.setResizable(false);
  currentSizeId = id;
  saveSizeId(id);
  installMenus(win);
}

function sizeMenuItems(win) {
  return SIZE_ORDER.map((id) => ({
    label: SIZE_LABELS[id],
    type: "radio",
    checked: currentSizeId === id,
    click: () => applySize(win, id),
  }));
}

function installMenus(win) {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {
      label: "Maho Overlay",
      submenu: [
        { label: "Size", submenu: sizeMenuItems(win) },
        { type: "separator" },
        { role: "quit", label: "Quit Maho Overlay" },
      ],
    },
  ]));
}

function createOverlay() {
  const bounds = overlayBounds(currentSizeId);
  const win = new BrowserWindow({
    ...bounds,
    frame: false,
    transparent: true,
    hasShadow: false,
    alwaysOnTop: true,
    focusable: false,
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
  win.setFocusable(false);
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  win.setIgnoreMouseEvents(true, { forward: true });
  win.setMenuBarVisibility(false);
  win.setHasShadow(false);
  win.setBackgroundColor("#00000000");

  win.once("ready-to-show", () => win.showInactive());
  win.on("closed", () => app.quit());

  win.webContents.on("context-menu", () => {
    Menu.buildFromTemplate([
      { label: "Size", submenu: sizeMenuItems(win) },
      { type: "separator" },
      { label: "Quit Maho Overlay", role: "quit" },
    ]).popup({ window: win });
  });

  installMenus(win);
  void win.loadURL(RENDERER_URL);
  return win;
}

ipcMain.on("release-focus", (event) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  if (!win) return;
  win.blur();
});

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
  currentSizeId = loadSizeId();
  createOverlay();
});

app.on("window-all-closed", () => app.quit());
