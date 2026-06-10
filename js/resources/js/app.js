
/**
 * 视频极简裁剪工具 - Neutralino.js 版本
 * 主应用逻辑
 */

let appState = {
  files: [],
  durations: {},
  currentEditingFile: null
};

let cutterManager = null;

let elements = {};

function initElements() {
  console.log('initElements called');
  
  elements.dropZone = document.getElementById('dropZone');
  elements.fileInput = document.getElementById('fileInput');
  elements.addFilesBtn = document.getElementById('addFilesBtn');
  elements.clearFilesBtn = document.getElementById('clearFilesBtn');
  elements.fileListBody = document.getElementById('fileListBody');
  
  elements.presetSelect = document.getElementById('presetSelect');
  elements.savePresetBtn = document.getElementById('savePresetBtn');
  elements.deletePresetBtn = document.getElementById('deletePresetBtn');
  
  elements.timeModeRadios = document.querySelectorAll('input[name="timeMode"]');
  elements.trimModeInputs = document.getElementById('trimModeInputs');
  elements.absoluteModeInputs = document.getElementById('absoluteModeInputs');
  elements.trimA = document.getElementById('trimA');
  elements.trimB = document.getElementById('trimB');
  elements.absStart = document.getElementById('absStart');
  elements.absEnd = document.getElementById('absEnd');
  elements.trimAPreview = document.getElementById('trimAPreview');
  elements.trimBPreview = document.getElementById('trimBPreview');
  elements.absStartPreview = document.getElementById('absStartPreview');
  elements.absEndPreview = document.getElementById('absEndPreview');
  
  console.log('elements.trimA:', elements.trimA);
  console.log('elements.trimB:', elements.trimB);
  
  elements.precisionMode = document.getElementById('precisionMode');
  
  elements.startBtn = document.getElementById('startBtn');
  elements.cancelBtn = document.getElementById('cancelBtn');
  elements.progressBar = document.getElementById('progressBar');
  elements.progressText = document.getElementById('progressText');
  elements.logArea = document.getElementById('logArea');
  
  elements.settingsBtn = document.getElementById('settingsBtn');
  elements.settingsModal = document.getElementById('settingsModal');
  elements.closeSettingsBtn = document.getElementById('closeSettingsBtn');
  elements.saveSettingsBtn = document.getElementById('saveSettingsBtn');
  elements.cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
  elements.ffmpegPath = document.getElementById('ffmpegPath');
  elements.ffprobePath = document.getElementById('ffprobePath');
  elements.outputSuffix = document.getElementById('outputSuffix');
  elements.conflictStrategy = document.getElementById('conflictStrategy');
  
  elements.presetModal = document.getElementById('presetModal');
  elements.closePresetModalBtn = document.getElementById('closePresetModalBtn');
  elements.confirmSavePresetBtn = document.getElementById('confirmSavePresetBtn');
  elements.cancelPresetBtn = document.getElementById('cancelPresetBtn');
  elements.presetName = document.getElementById('presetName');
  
  elements.customTimeModal = document.getElementById('customTimeModal');
  elements.closeCustomTimeBtn = document.getElementById('closeCustomTimeBtn');
  elements.saveCustomTimeBtn = document.getElementById('saveCustomTimeBtn');
  elements.cancelCustomTimeBtn = document.getElementById('cancelCustomTimeBtn');
}

function logMessage(msg) {
  const p = document.createElement('p');
  p.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  elements.logArea.appendChild(p);
  elements.logArea.scrollTop = elements.logArea.scrollHeight;
}

function renderFileList() {
  elements.fileListBody.innerHTML = '';

  appState.files.forEach((file, index) => {
    const tr = document.createElement('tr');

    let durationText = '加载中...';
    if (file.duration !== null) {
      durationText = formatSeconds(file.duration);
    }

    let timeConfigText = '默认';
    if (!file.useDefault) {
      timeConfigText = '自定义';
    }

    const statusClass = `status-${file.status || 'pending'}`;

    tr.innerHTML = `
      <td>${escapeHtml(file.name)}</td>
      <td>${durationText}</td>
      <td>${timeConfigText}</td>
      <td class="${statusClass}">${file.status || '等待'}</td>
      <td>
        <button class="btn btn-sm btn-secondary" onclick="editFileTime(${index})">设置时间</button>
        <button class="btn btn-sm btn-danger" onclick="removeFile(${index})">删除</button>
      </td>
    `;

    elements.fileListBody.appendChild(tr);
  });
}

function updatePresetSelect() {
  elements.presetSelect.innerHTML = '<option value="">选择预设...</option>';
  const presetsList = getPresets();
  presetsList.forEach(preset => {
    const option = document.createElement('option');
    option.value = preset.id;
    option.textContent = preset.name;
    elements.presetSelect.appendChild(option);
  });
}

async function getFileDuration(fileItem) {
  console.log('getFileDuration called for:', fileItem.path);
  const config = getConfig();
  const ffprobeHelper = new FFprobeHelper(config.ffprobePath, config.ffmpegPath);
  const duration = await ffprobeHelper.getDuration(fileItem.path);

  if (duration !== null) {
    fileItem.duration = duration;
    appState.durations[fileItem.path] = duration;
    console.log('Duration found:', duration);
  } else {
    console.warn('Failed to get duration for:', fileItem.path);
    logMessage(`⚠️ 无法获取时长: ${fileItem.name}（请确认 ffprobe/ffmpeg 已安装）`);
  }

  renderFileList();
}

function isVideoFile(path) {
  const ext = path.toLowerCase().split('.').pop();
  return ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'ts', 'm4v', '3gp', 'mpg', 'mpeg'].includes(ext);
}

function addFilePaths(paths) {
  paths.forEach(path => {
    if (!isVideoFile(path)) {
      logMessage(`跳过非视频文件: ${path}`);
      return;
    }
    if (appState.files.find(f => f.path === path)) {
      return;
    }
    const name = path.replace(/\\/g, '/').split('/').pop();
    const fileItem = {
      path: path,
      name: name,
      duration: null,
      useDefault: true,
      customMode: null,
      customA: null,
      customB: null
    };
    appState.files.push(fileItem);
    getFileDuration(fileItem);
  });
  renderFileList();
}

/**
 * 打开 Neutralino 原生文件选择对话框
 */
async function openFilePicker() {
  console.log('openFilePicker called');
  try {
    const entries = await Neutralino.os.showOpenDialog('选择视频文件', {
      multiSelections: true
    });
    console.log('showOpenDialog result:', entries);
    if (entries && entries.length > 0) {
      addFilePaths(entries);
    }
  } catch (e) {
    console.error('showOpenDialog error:', e);
    logMessage('打开文件对话框失败: ' + e.message);
  }
}

function removeFile(index) {
  const file = appState.files[index];
  delete appState.durations[file.path];
  appState.files.splice(index, 1);
  renderFileList();
}

function clearFiles() {
  appState.files = [];
  appState.durations = {};
  renderFileList();
  logMessage('文件列表已清空');
}

function editFileTime(index) {
  appState.currentEditingFile = index;
  const file = appState.files[index];

  const modeRadios = document.querySelectorAll('input[name="customTimeMode"]');
  modeRadios.forEach(radio => {
    radio.checked = file.useDefault ? radio.value === 'default' : radio.value === 'custom';
  });

  document.getElementById('customTimeInputs').style.display = file.useDefault ? 'none' : 'block';
  elements.customTimeModal.style.display = 'flex';
}

function saveCustomTime() {
  const index = appState.currentEditingFile;
  const file = appState.files[index];

  const useDefault = document.querySelector('input[name="customTimeMode"]:checked').value === 'default';

  if (useDefault) {
    file.useDefault = true;
    file.customMode = null;
    file.customA = null;
    file.customB = null;
  } else {
    const trimMode = document.querySelector('input[name="customTrimMode"]:checked').value;
    const aInput = document.getElementById('customTrimA').value;
    const bInput = document.getElementById('customTrimB').value;

    file.useDefault = false;
    file.customMode = trimMode;
    file.customA = parseTimeInput(aInput);
    file.customB = parseTimeInput(bInput);
  }

  elements.customTimeModal.style.display = 'none';
  renderFileList();
}

function validateTimeInput(input, preview) {
  const value = input.value.trim();
  console.log('validateTimeInput value:', value);
  
  if (!value) {
    input.classList.remove('error');
    preview.textContent = '';
    console.log('validateTimeInput returning null (empty)');
    return null;
  }

  const parsed = parseTimeInput(value);
  console.log('validateTimeInput parsed:', parsed);
  
  if (parsed === null) {
    input.classList.add('error');
    preview.textContent = '⚠️ 无效格式';
    console.log('validateTimeInput returning null (invalid)');
    return null;
  } else {
    input.classList.remove('error');
    preview.textContent = `= ${formatSeconds(parsed)}`;
    console.log('validateTimeInput returning:', parsed);
    return parsed;
  }
}

function handleTimeModeChange() {
  const mode = document.querySelector('input[name="timeMode"]:checked').value;

  if (mode === TimeMode.TRIM_HEAD_TAIL) {
    elements.trimModeInputs.style.display = 'flex';
    elements.absoluteModeInputs.style.display = 'none';
  } else {
    elements.trimModeInputs.style.display = 'none';
    elements.absoluteModeInputs.style.display = 'flex';
  }
}

function applyPreset(preset) {
  document.querySelector(`input[name="timeMode"][value="${preset.mode}"]`).checked = true;
  handleTimeModeChange();

  if (preset.mode === TimeMode.TRIM_HEAD_TAIL) {
    elements.trimA.value = preset.valueA !== null ? preset.valueA.toString() : '';
    elements.trimB.value = preset.valueB !== null ? preset.valueB.toString() : '';
    validateTimeInput(elements.trimA, elements.trimAPreview);
    validateTimeInput(elements.trimB, elements.trimBPreview);
  } else {
    elements.absStart.value = preset.valueA !== null ? preset.valueA.toString() : '';
    elements.absEnd.value = preset.valueB !== null ? preset.valueB.toString() : '';
    validateTimeInput(elements.absStart, elements.absStartPreview);
    validateTimeInput(elements.absEnd, elements.absEndPreview);
  }
}

function handlePresetSelect() {
  const presetId = elements.presetSelect.value;
  if (presetId) {
    const preset = getPreset(presetId);
    if (preset) {
      applyPreset(preset);
    }
  }
}

async function saveCurrentPreset() {
  const name = elements.presetName.value.trim();
  if (!name) {
    alert('请输入预设名称');
    return;
  }

  const mode = document.querySelector('input[name="timeMode"]:checked').value;
  let valueA, valueB;

  if (mode === TimeMode.TRIM_HEAD_TAIL) {
    valueA = parseTimeInput(elements.trimA.value);
    valueB = parseTimeInput(elements.trimB.value);
  } else {
    valueA = parseTimeInput(elements.absStart.value);
    valueB = parseTimeInput(elements.absEnd.value);
  }

  addPreset(name, mode, valueA, valueB);
  await savePresets();
  updatePresetSelect();

  elements.presetName.value = '';
  elements.presetModal.style.display = 'none';
  logMessage(`✓ 预设已保存: ${name}`);
}

async function deleteCurrentPreset() {
  const presetId = elements.presetSelect.value;
  if (!presetId) {
    alert('请先选择一个预设');
    return;
  }

  if (confirm('确定要删除这个预设吗？')) {
    deletePreset(presetId);
    await savePresets();
    updatePresetSelect();
    elements.presetSelect.value = '';
    logMessage('✓ 预设已删除');
  }
}

async function saveSettingsHandler() {
  const config = {
    ffmpegPath: elements.ffmpegPath.value.trim() || 'ffmpeg',
    ffprobePath: elements.ffprobePath.value.trim() || 'ffprobe',
    suffix: elements.outputSuffix.value.trim() || '_1',
    conflictStrategy: elements.conflictStrategy.value
  };

  await saveConfig(config);
  elements.settingsModal.style.display = 'none';
  logMessage('✓ 设置已保存');
}

async function startCutting() {
  console.log('startCutting called');

  if (appState.files.length === 0) {
    alert('请先添加视频文件');
    return;
  }

  // 等待所有文件时长加载完成（最多等待 10 秒）
  const hasNullDuration = appState.files.some(f => f.duration === null);
  if (hasNullDuration) {
    logMessage('正在等待时长加载...');
    let waited = 0;
    while (appState.files.some(f => f.duration === null) && waited < 10000) {
      await new Promise(r => setTimeout(r, 500));
      waited += 500;
    }
    if (appState.files.some(f => f.duration === null)) {
      logMessage('⚠️ 时长加载超时，请确认 ffprobe/ffmpeg 已正确安装');
      alert('部分视频时长未能获取，请确认 ffprobe/ffmpeg 已安装并在系统 PATH 中，或在设置中指定正确路径。');
      return;
    }
  }

  const mode = document.querySelector('input[name="timeMode"]:checked').value;
  console.log('Selected mode:', mode);
  
  let defaultA, defaultB;

  if (mode === TimeMode.TRIM_HEAD_TAIL) {
    console.log('Trim A input value:', elements.trimA.value);
    console.log('Trim B input value:', elements.trimB.value);
    defaultA = validateTimeInput(elements.trimA, elements.trimAPreview);
    defaultB = validateTimeInput(elements.trimB, elements.trimBPreview);
  } else {
    console.log('Abs Start input value:', elements.absStart.value);
    console.log('Abs End input value:', elements.absEnd.value);
    defaultA = validateTimeInput(elements.absStart, elements.absStartPreview);
    defaultB = validateTimeInput(elements.absEnd, elements.absEndPreview);
  }
  
  console.log('defaultA:', defaultA);
  console.log('defaultB:', defaultB);

  if (elements.trimA.classList.contains('error') || 
      elements.trimB.classList.contains('error') ||
      elements.absStart.classList.contains('error') ||
      elements.absEnd.classList.contains('error')) {
    alert('请修正时间输入错误');
    return;
  }

  appState.files.forEach(f => f.status = FileStatus.PENDING);
  renderFileList();

  const config = getConfig();
  cutterManager = new VideoCutterManager(
    config.ffmpegPath,
    config.suffix,
    config.conflictStrategy,
    elements.precisionMode.checked,
    config.movflagsFaststart
  );

  cutterManager.on('progress', (current, total) => {
    const percent = (current / total) * 100;
    elements.progressBar.style.width = `${percent}%`;
    elements.progressText.textContent = cutterManager.isCancelled
      ? `取消中... ${current}/${total}`
      : `处理中... ${current}/${total}`;
  });

  cutterManager.on('fileStatus', (path, status, message) => {
    const file = appState.files.find(f => f.path === path);
    if (file) {
      file.status = status;
      renderFileList();
    }
  });

  cutterManager.on('log', (msg) => logMessage(msg));

  cutterManager.on('allFinished', (success, failed, skipped) => {
    elements.startBtn.style.display = 'block';
    elements.cancelBtn.style.display = 'none';
    elements.progressBar.style.width = '0%';
    if (cutterManager.isCancelled) {
      elements.progressText.textContent = `已取消！成功: ${success}, 失败: ${failed}, 跳过: ${skipped}`;
    } else {
      elements.progressText.textContent = `完成！成功: ${success}, 失败: ${failed}, 跳过: ${skipped}`;
    }
  });

  elements.startBtn.style.display = 'none';
  elements.cancelBtn.style.display = 'block';
  elements.logArea.innerHTML = '';

  try {
    await cutterManager.startBatch(appState.files, mode, defaultA, defaultB, appState.durations);
  } catch (e) {
    console.error('startCutting error:', e);
    logMessage(`启动失败: ${e.message}`);
    elements.startBtn.style.display = 'block';
    elements.cancelBtn.style.display = 'none';
  }
}

function cancelCutting() {
  if (cutterManager) {
    cutterManager.cancel();
  }
}

function bindEvents() {
  elements.addFilesBtn.addEventListener('click', openFilePicker);
  elements.clearFilesBtn.addEventListener('click', clearFiles);

  elements.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropZone.classList.add('drag-over');
  });
  elements.dropZone.addEventListener('dragleave', () => {
    elements.dropZone.classList.remove('drag-over');
  });
  elements.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropZone.classList.remove('drag-over');
    openFilePicker();
  });
  elements.dropZone.addEventListener('click', openFilePicker);

  elements.timeModeRadios.forEach(radio => {
    radio.addEventListener('change', handleTimeModeChange);
  });

  elements.trimA.addEventListener('input', () => validateTimeInput(elements.trimA, elements.trimAPreview));
  elements.trimB.addEventListener('input', () => validateTimeInput(elements.trimB, elements.trimBPreview));
  elements.absStart.addEventListener('input', () => validateTimeInput(elements.absStart, elements.absStartPreview));
  elements.absEnd.addEventListener('input', () => validateTimeInput(elements.absEnd, elements.absEndPreview));

  elements.presetSelect.addEventListener('change', handlePresetSelect);
  elements.savePresetBtn.addEventListener('click', () => elements.presetModal.style.display = 'flex');
  elements.deletePresetBtn.addEventListener('click', deleteCurrentPreset);

  elements.closePresetModalBtn.addEventListener('click', () => elements.presetModal.style.display = 'none');
  elements.cancelPresetBtn.addEventListener('click', () => elements.presetModal.style.display = 'none');
  elements.confirmSavePresetBtn.addEventListener('click', saveCurrentPreset);

  elements.settingsBtn.addEventListener('click', () => elements.settingsModal.style.display = 'flex');
  elements.closeSettingsBtn.addEventListener('click', () => elements.settingsModal.style.display = 'none');
  elements.cancelSettingsBtn.addEventListener('click', () => elements.settingsModal.style.display = 'none');
  elements.saveSettingsBtn.addEventListener('click', saveSettingsHandler);

  elements.startBtn.addEventListener('click', startCutting);
  elements.cancelBtn.addEventListener('click', cancelCutting);

  elements.closeCustomTimeBtn.addEventListener('click', () => elements.customTimeModal.style.display = 'none');
  elements.cancelCustomTimeBtn.addEventListener('click', () => elements.customTimeModal.style.display = 'none');
  elements.saveCustomTimeBtn.addEventListener('click', saveCustomTime);

  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
      }
    });
  });

  document.querySelectorAll('input[name="customTimeMode"]').forEach(radio => {
    radio.addEventListener('change', () => {
      const isCustom = radio.value === 'custom';
      document.getElementById('customTimeInputs').style.display = isCustom ? 'block' : 'none';
    });
  });
}

function initUI() {
  updatePresetSelect();

  const config = getConfig();
  elements.ffmpegPath.value = config.ffmpegPath;
  elements.ffprobePath.value = config.ffprobePath;
  elements.outputSuffix.value = config.suffix;
  elements.conflictStrategy.value = config.conflictStrategy;
  elements.precisionMode.checked = config.precisionMode;
}

async function initApp() {
  await Neutralino.init();
  
  initElements();
  await loadConfig();
  await loadPresets();
  
  initUI();
  bindEvents();
  
  logMessage('应用已启动');

  const config = getConfig();
  const ffprobeHelper = new FFprobeHelper(config.ffprobePath, config.ffmpegPath);
  const ffprobeOk = await ffprobeHelper.checkFFprobe();
  if (!ffprobeOk) {
    logMessage('⚠️ 警告：未检测到 ffprobe，请在设置中配置正确路径');
  }
}

window.editFileTime = editFileTime;
window.removeFile = removeFile;

initApp();
