
/**
 * FFmpeg 和 FFprobe 封装
 */

/** 临时文件计数器 */
let _tmpId = 0;

/** 获取临时文件路径 */
async function _tmpPath(name) {
  const tmpDir = await Neutralino.os.getPath('cache');
  return `${tmpDir}/vc_${Date.now()}_${_tmpId++}_${name}`;
}

/**
 * 通用命令执行（用 spawnProcess + 临时文件，带超时）
 * 原理：spawnProcess 通过 shell 执行命令，stdout 重定向到临时文件，
 * 通过轮询退出码文件判断命令是否完成
 */
async function execWithTimeout(cmd, timeoutMs = 15000) {
  const outPath = await _tmpPath('out');
  const exitPath = await _tmpPath('exit');

  // 通过 shell 执行命令，将 stdout/stderr 重定向到文件，并记录退出码
  const escapedCmd = cmd.replace(/'/g, "'\\''" );
  const shellCmd = `/bin/sh -c '${escapedCmd}' > "${outPath}" 2>&1; echo $? > "${exitPath}"`;

  // spawnProcess 本身也可能阻塞，加 5 秒超时
  await Promise.race([
    Neutralino.os.spawnProcess(shellCmd),
    new Promise((_, reject) => setTimeout(() => reject(new Error('spawnProcess 阻塞')), 5000))
  ]);

  // 轮询等待退出码文件出现
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    await new Promise(r => setTimeout(r, 200));
    try {
      const exitCode = parseInt(await Neutralino.filesystem.readFile(exitPath));
      const stdOut = await Neutralino.filesystem.readFile(outPath).catch(() => '');
      // 清理临时文件
      Neutralino.filesystem.remove(outPath).catch(() => {});
      Neutralino.filesystem.remove(exitPath).catch(() => {});
      return { exitCode: isNaN(exitCode) ? -1 : exitCode, stdOut, stdErr: '' };
    } catch (e) {
      // 文件尚未生成，继续等待
    }
  }

  // 超时：清理临时文件
  Neutralino.filesystem.remove(outPath).catch(() => {});
  Neutralino.filesystem.remove(exitPath).catch(() => {});
  throw new Error(`命令超时 (${timeoutMs}ms): ${cmd}`);
}

class FFprobeHelper {
  constructor(ffprobePath = 'ffprobe', ffmpegPath = 'ffmpeg') {
    this.ffprobePath = ffprobePath;
    this.ffmpegPath = ffmpegPath;
  }

  async getDuration(filePath) {
    const quotedPath = `"${filePath}"`;
    const args = [
      '-v', 'error',
      '-show_entries', 'format=duration',
      '-of', 'default=noprint_wrappers=1:nokey=1',
      quotedPath
    ];

    try {
      const cmd = `${this.ffprobePath} ${args.join(' ')}`;
      console.log('FFprobe command:', cmd);

      const result = await execWithTimeout(cmd, 10000);
      console.log('FFprobe result:', result);

      if (result.exitCode === 0) {
        const output = result.stdOut.trim();
        const duration = parseFloat(output);
        if (!isNaN(duration) && isFinite(duration) && duration >= 0) {
          return duration;
        }
      }
    } catch (e) {
      console.error('FFprobe error:', e);
    }

    // ffprobe 失败，尝试用 ffmpeg 获取时长
    console.log('FFprobe failed, trying ffmpeg fallback...');
    return await this._getDurationViaFFmpeg(filePath);
  }

  async _getDurationViaFFmpeg(filePath) {
    try {
      const quotedPath = `"${filePath}"`;
      const cmd = `${this.ffmpegPath} -i ${quotedPath} -hide_banner`;
      console.log('FFmpeg duration probe:', cmd);

      const result = await execWithTimeout(cmd, 10000);
      const output = (result.stdErr || '') + (result.stdOut || '');
      const match = output.match(/Duration:\s*(\d+):(\d+):(\d+)\.(\d+)/);
      if (match) {
        const hours = parseInt(match[1]);
        const minutes = parseInt(match[2]);
        const seconds = parseInt(match[3]);
        const ms = parseInt(match[4]);
        return hours * 3600 + minutes * 60 + seconds + ms / 100;
      }
    } catch (e) {
      console.error('FFmpeg duration probe error:', e);
    }
    return null;
  }

  async checkFFprobe() {
    try {
      const result = await execWithTimeout(`${this.ffprobePath} -version`, 5000);
      return result.exitCode === 0;
    } catch (e) {
      return false;
    }
  }
}

class FFmpegRunner {
  constructor(ffmpegPath = 'ffmpeg') {
    this.ffmpegPath = ffmpegPath;
    this._pid = null;
    this._cancelled = false;
  }

  async run(args) {
    const cmd = [this.ffmpegPath, ...args].join(' ');
    console.log('FFmpeg command:', cmd);

    this._cancelled = false;

    const outPath = await _tmpPath('ffmpeg_out');
    const errPath = await _tmpPath('ffmpeg_err');
    const exitPath = await _tmpPath('ffmpeg_exit');

    // 通过 shell 执行，将 stdout/stderr/exitcode 分别写入临时文件
    const escapedCmd = cmd.replace(/'/g, "'\\''" );
    const shellCmd = `/bin/sh -c '${escapedCmd} > "${outPath}" 2> "${errPath}"; echo $? > "${exitPath}"'`;

    // 启动进程并获取 PID（用于取消）
    try {
      const process = await Promise.race([
        Neutralino.os.spawnProcess(shellCmd),
        new Promise((_, reject) => setTimeout(() => reject(new Error('spawnProcess 阻塞')), 5000))
      ]);
      this._pid = process.pid;
      console.log('FFmpeg spawned, pid:', process.pid);
    } catch (e) {
      console.error('FFmpeg spawn error:', e);
      return { exitCode: -1, stdErr: e.message || '启动FFmpeg失败', stdOut: '' };
    }

    // 轮询等待退出码文件（最多等 30 分钟）
    const maxWait = 30 * 60 * 1000;
    const start = Date.now();
    while (Date.now() - start < maxWait) {
      if (this._cancelled) {
        this._cleanup(outPath, errPath, exitPath);
        return { exitCode: -1, stdErr: '已取消', stdOut: '' };
      }
      await new Promise(r => setTimeout(r, 500));
      try {
        const exitCode = parseInt(await Neutralino.filesystem.readFile(exitPath));
        const stdOut = await Neutralino.filesystem.readFile(outPath).catch(() => '');
        const stdErr = await Neutralino.filesystem.readFile(errPath).catch(() => '');
        console.log('FFmpeg exited, code:', exitCode);
        this._cleanup(outPath, errPath, exitPath);
        return { exitCode: isNaN(exitCode) ? -1 : exitCode, stdOut, stdErr };
      } catch (e) {
        // 退出码文件尚未生成，继续等待
      }
    }

    this._cleanup(outPath, errPath, exitPath);
    return { exitCode: -1, stdErr: 'FFmpeg 处理超时', stdOut: '' };
  }

  async cancel() {
    this._cancelled = true;
    const pid = this._pid;
    if (pid) {
      console.log('Killing FFmpeg processes, shell pid:', pid);
      try {
        // 先杀子进程（ffmpeg），再杀 shell
        await Neutralino.os.spawnProcess(`pkill -P ${pid}; kill -9 ${pid}`);
      } catch (e) {
        console.error('Kill error:', e);
      }
    }
  }

  _cleanup(...paths) {
    for (const p of paths) {
      Neutralino.filesystem.remove(p).catch(() => {});
    }
    this._pid = null;
  }
}
