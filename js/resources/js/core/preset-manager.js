
/**
 * 预设管理模块
 */

const PRESETS_STORAGE_KEY = 'video_cutter_presets';

let presets = [];

async function loadPresets() {
  try {
    const stored = await Neutralino.storage.getData(PRESETS_STORAGE_KEY);
    presets = JSON.parse(stored);
  } catch (e) {
    presets = [];
  }
  return presets;
}

async function savePresets() {
  await Neutralino.storage.setData(PRESETS_STORAGE_KEY, JSON.stringify(presets));
}

function getPresets() {
  return [...presets];
}

function addPreset(name, mode, valueA, valueB) {
  const preset = {
    id: Date.now().toString(),
    name,
    mode,
    valueA,
    valueB,
    createdAt: new Date().toISOString()
  };
  presets.push(preset);
  return preset;
}

function deletePreset(id) {
  const index = presets.findIndex(p => p.id === id);
  if (index !== -1) {
    presets.splice(index, 1);
    return true;
  }
  return false;
}

function getPreset(id) {
  return presets.find(p => p.id === id) || null;
}
