
/**
 * 配置管理模块
 */

const CONFIG_STORAGE_KEY = 'video_cutter_config';

const defaultConfig = {
  ffmpegPath: '/opt/homebrew/bin/ffmpeg',
  ffprobePath: '/opt/homebrew/bin/ffprobe',
  suffix: '_1',
  conflictStrategy: 'rename',
  precisionMode: false,
  movflagsFaststart: true
};

let appConfig = { ...defaultConfig };

async function loadConfig() {
  try {
    const stored = await Neutralino.storage.getData(CONFIG_STORAGE_KEY);
    appConfig = { ...defaultConfig, ...JSON.parse(stored) };
  } catch (e) {
    appConfig = { ...defaultConfig };
  }
  return appConfig;
}

async function saveConfig(config) {
  appConfig = { ...appConfig, ...config };
  await Neutralino.storage.setData(CONFIG_STORAGE_KEY, JSON.stringify(appConfig));
  return appConfig;
}

function getConfig() {
  return { ...appConfig };
}
