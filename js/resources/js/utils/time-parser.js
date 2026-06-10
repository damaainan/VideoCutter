
/**
 * 时间解析工具
 * 支持多种时间格式的解析和格式化
 */

function parseTimeInput(text) {
  if (!text || !text.trim()) {
    return null;
  }

  text = text.trim();

  const numValue = parseFloat(text);
  if (!isNaN(numValue) && isFinite(numValue) && numValue >= 0) {
    return numValue;
  }

  const patternHms = /^(\d+):(\d{1,2}):(\d{1,2})(?:\.(\d+))?$/;
  const matchHms = text.match(patternHms);
  if (matchHms) {
    const hours = parseInt(matchHms[1], 10);
    const minutes = parseInt(matchHms[2], 10);
    const seconds = parseInt(matchHms[3], 10);
    const msStr = matchHms[4];

    if (minutes >= 60 || seconds >= 60) {
      return null;
    }

    let milliseconds = 0.0;
    if (msStr) {
      milliseconds = parseInt(msStr, 10) / Math.pow(10, msStr.length);
    }

    return hours * 3600 + minutes * 60 + seconds + milliseconds;
  }

  const patternMs = /^(\d+):(\d{1,2})$/;
  const matchMs = text.match(patternMs);
  if (matchMs) {
    const minutes = parseInt(matchMs[1], 10);
    const seconds = parseInt(matchMs[2], 10);

    if (seconds >= 60) {
      return null;
    }

    return minutes * 60 + seconds;
  }

  return null;
}

function formatSeconds(secs) {
  if (secs < 0) {
    secs = 0;
  }

  const totalSeconds = Math.floor(secs);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function formatSecondsWithMs(secs) {
  if (secs < 0) {
    secs = 0;
  }

  const totalSeconds = Math.floor(secs);
  const milliseconds = Math.floor((secs - totalSeconds) * 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (milliseconds > 0) {
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`;
  }
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
