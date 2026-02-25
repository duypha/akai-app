const { app, BrowserWindow, Tray, Menu, globalShortcut, nativeImage, screen, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

let mainWindow;
let tray;

const WINDOW_WIDTH = 400;
const WINDOW_MARGIN = 10;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    minWidth: 360,
    minHeight: 500,
    frame: true,
    backgroundColor: '#F5F1EB',
    alwaysOnTop: false,
    skipTaskbar: false,
    resizable: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'icon.png')
  });

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    // mainWindow.webContents.openDevTools(); // Disabled for cleaner look
  } else {
    mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
  }

  // Handle window close - minimize to tray instead
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createTray() {
  // Create tray icon (simple colored square as placeholder)
  const iconSize = 16;
  const icon = nativeImage.createEmpty();

  tray = new Tray(icon);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open Akai',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: 'Snap to Right',
      click: () => snapToRight()
    },
    { type: 'separator' },
    {
      label: 'Start with System',
      type: 'checkbox',
      checked: app.getLoginItemSettings().openAtLogin,
      click: (menuItem) => {
        app.setLoginItemSettings({
          openAtLogin: menuItem.checked
        });
      }
    },
    {
      label: 'Create Desktop Shortcut',
      click: () => createDesktopShortcut()
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip('Akai - AI Assistant');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    }
  });
}

function snapToRight() {
  if (!mainWindow) return;

  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;

  const windowHeight = screenHeight - (WINDOW_MARGIN * 2);
  const xPosition = screenWidth - WINDOW_WIDTH - WINDOW_MARGIN;
  const yPosition = WINDOW_MARGIN;

  mainWindow.setBounds({
    x: xPosition,
    y: yPosition,
    width: WINDOW_WIDTH,
    height: windowHeight
  });

  mainWindow.show();
  mainWindow.focus();
}

function createDesktopShortcut() {
  if (process.platform === 'win32') {
    const desktopPath = path.join(app.getPath('desktop'), 'Akai.lnk');
    const exePath = process.execPath;

    // Use Windows Script Host to create shortcut
    const wsShortcut = `
      Set WshShell = WScript.CreateObject("WScript.Shell")
      Set shortcut = WshShell.CreateShortcut("${desktopPath.replace(/\\/g, '\\\\')}")
      shortcut.TargetPath = "${exePath.replace(/\\/g, '\\\\')}"
      shortcut.WorkingDirectory = "${path.dirname(exePath).replace(/\\/g, '\\\\')}"
      shortcut.Description = "Akai - AI Assistant"
      shortcut.Save
    `;

    const vbsPath = path.join(app.getPath('temp'), 'create_shortcut.vbs');
    fs.writeFileSync(vbsPath, wsShortcut);

    const { exec } = require('child_process');
    exec(`cscript //nologo "${vbsPath}"`, (error) => {
      fs.unlinkSync(vbsPath);
      if (!error) {
        mainWindow.webContents.send('notification', {
          title: 'Shortcut Created',
          body: 'Desktop shortcut has been created'
        });
      }
    });
  } else {
    // For Mac/Linux, just show the app location
    shell.showItemInFolder(process.execPath);
  }
}

function registerShortcuts() {
  // Global shortcut to toggle window (Ctrl+Shift+A)
  globalShortcut.register('CommandOrControl+Shift+A', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        snapToRight();
      }
    }
  });

  // Shortcut to snap to right (Ctrl+Shift+R)
  globalShortcut.register('CommandOrControl+Shift+R', () => {
    snapToRight();
  });
}

// IPC Handlers
function setupIPC() {
  // Window controls
  ipcMain.on('window-minimize', () => mainWindow?.minimize());
  ipcMain.on('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  });
  ipcMain.on('window-close', () => mainWindow?.hide());

  // Snap to right
  ipcMain.on('snap-to-right', () => snapToRight());

  // Refresh session
  ipcMain.on('refresh-session', () => {
    mainWindow?.webContents.reload();
  });

  // Create desktop shortcut
  ipcMain.on('create-shortcut', () => createDesktopShortcut());

  // Get screen sources for screen sharing
  ipcMain.handle('get-sources', async () => {
    const { desktopCapturer } = require('electron');
    const sources = await desktopCapturer.getSources({
      types: ['window', 'screen'],
      thumbnailSize: { width: 150, height: 150 }
    });
    return sources.map(source => ({
      id: source.id,
      name: source.name,
      thumbnail: source.thumbnail.toDataURL()
    }));
  });
}

// App ready
app.whenReady().then(() => {
  createWindow();
  createTray();
  registerShortcuts();
  setupIPC();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else {
      mainWindow.show();
    }
  });
});

// Quit when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Clean up shortcuts on quit
app.on('will-quit', () => {
  if (app.isReady()) {
    globalShortcut.unregisterAll();
  }
});

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}
