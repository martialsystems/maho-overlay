const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("overlay", {
  setClickThrough(ignore) {
    ipcRenderer.send("set-click-through", Boolean(ignore));
  },
  moveBy(dx, dy) {
    ipcRenderer.send("move-by", dx, dy);
  },
  quit() {
    ipcRenderer.send("quit");
  },
});
