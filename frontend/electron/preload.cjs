const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("overlay", {
  setClickThrough(ignore) {
    ipcRenderer.send("set-click-through", Boolean(ignore));
  },
  moveBy(dx, dy) {
    ipcRenderer.send("move-by", dx, dy);
  },
  releaseFocus() {
    ipcRenderer.send("release-focus");
  },
  quit() {
    ipcRenderer.send("quit");
  },
});
