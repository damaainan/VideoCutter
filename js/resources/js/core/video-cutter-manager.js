
/**
 * 视频裁剪管理器
 */

const FileStatus = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  SUCCESS: 'success',
  FAILED: 'failed',
  SKIPPED: 'skipped',
  CANCELLED: 'cancelled'
};

class VideoCutterManager {
  constructor(ffmpegPath = 'ffmpeg', suffix = '_1', conflictStrategy = 'rename', precisionMode = false, movflagsFaststart = true) {
    this.ffmpegPath = ffmpegPath;
    this.suffix = suffix;
    this.conflictStrategy = conflictStrategy;
    this.precisionMode = precisionMode;
    this.movflagsFaststart = movflagsFaststart;
    this.files = [];
    this.isRunning = false;
    this.isCancelled = false;
    this.currentFFmpeg = null;
    this.listeners = {};
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  emit(event, ...args) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(...args));
    }
  }

  async startBatch(fileItems, defaultMode, defaultA, defaultB, durations = {}) {
    console.log('VideoCutterManager.startBatch called');
    console.log('fileItems:', fileItems);
    console.log('defaultMode:', defaultMode);
    console.log('defaultA:', defaultA);
    console.log('defaultB:', defaultB);
    
    if (this.isRunning) return;

    this.files = fileItems.map(item => ({
      ...item,
      duration: durations[item.path] || item.duration,
      status: FileStatus.PENDING,
      outputPath: null,
      errorMessage: ''
    }));

    this.isRunning = true;
    this.isCancelled = false;

    this.emit('log', `开始批量裁剪，共 ${this.files.length} 个文件`);
    this.emit('log', `默认模式: ${defaultMode}, A=${defaultA}, B=${defaultB}`);

    try {
      for (let i = 0; i < this.files.length; i++) {
        console.log(`Processing file ${i + 1}/${this.files.length}`);
        if (this.isCancelled) break;
        await this._processFile(i, defaultMode, defaultA, defaultB);
      }
    } catch (e) {
      console.error('startBatch error:', e);
      this.emit('log', `批量处理出错: ${e.message}`);
    } finally {
      this._finishBatch();
    }
  }

  cancel() {
    this.isCancelled = true;
    this.emit('log', '正在取消...');
    if (this.currentFFmpeg) {
      this.currentFFmpeg.cancel();
    }
  }

  async _processFile(index, defaultMode, defaultA, defaultB) {
    console.log('_processFile starting');
    const file = this.files[index];
    file.status = FileStatus.PROCESSING;

    try {
      this.emit('progress', index + 1, this.files.length);
      this.emit('fileStatus', file.path, FileStatus.PROCESSING, '处理中...');
      this.emit('fileStarted', file.path);

      this.emit('log', `\n处理 (${index + 1}/${this.files.length}): ${this._getFileName(file.path)}`);

      const mode = file.useDefault ? defaultMode : (file.customMode || defaultMode);
      const valueA = file.useDefault ? defaultA : file.customA;
      const valueB = file.useDefault ? defaultB : file.customB;

      console.log('Time mode:', mode);
      console.log('Value A:', valueA);
      console.log('Value B:', valueB);
      console.log('Duration:', file.duration);

      console.log('Calculating time range...');
      const result = TimeRangeCalculator.calculate(file.duration || 0, mode, valueA, valueB);
      console.log('Time range result:', result);

      if (!result.valid) {
        file.status = FileStatus.FAILED;
        file.errorMessage = result.errorMessage;
        this.emit('fileStatus', file.path, FileStatus.FAILED, result.errorMessage);
        this.emit('fileFinished', file.path, false, result.errorMessage);
        this.emit('log', `  错误: ${result.errorMessage}`);
        return;
      }

      console.log('Getting output path...');
      const overwritePolicy = new OverwritePolicy(this.conflictStrategy);
      const outputResult = await overwritePolicy.getOutputPath(file.path, this.suffix);
      console.log('Output result:', outputResult);

      if (outputResult.status === 'skipped') {
        file.status = FileStatus.SKIPPED;
        this.emit('fileStatus', file.path, FileStatus.SKIPPED, '已跳过');
        this.emit('fileFinished', file.path, true, '已跳过（文件已存在）');
        this.emit('log', `  已跳过（文件已存在）`);
        return;
      }

      file.outputPath = outputResult.path;
      console.log('Building FFmpeg args...');
      const args = this._buildFFmpegArgs(file.path, outputResult.path, result);
      console.log('FFmpeg args:', args);

      this.emit('log', `  输出: ${this._getFileName(outputResult.path)}`);

      if (this.isCancelled) {
        file.status = FileStatus.CANCELLED;
        this.emit('fileStatus', file.path, FileStatus.CANCELLED, '已取消');
        this.emit('log', `  已取消`);
        return;
      }

      console.log('Creating FFmpeg runner...');
      const ffmpegRunner = new FFmpegRunner(this.ffmpegPath);
      this.currentFFmpeg = ffmpegRunner;
      console.log('Running FFmpeg...');
      const ffmpegResult = await ffmpegRunner.run(args);
      this.currentFFmpeg = null;
      console.log('FFmpeg result:', ffmpegResult);

      if (this.isCancelled) {
        file.status = FileStatus.CANCELLED;
        this.emit('fileStatus', file.path, FileStatus.CANCELLED, '已取消');
        this.emit('log', `  已取消`);
      } else if (ffmpegResult.exitCode === 0) {
        file.status = FileStatus.SUCCESS;
        this.emit('fileStatus', file.path, FileStatus.SUCCESS, `输出: ${this._getFileName(outputResult.path)}`);
        this.emit('fileFinished', file.path, true, `输出: ${this._getFileName(outputResult.path)}`);
        this.emit('log', `  完成 ✓`);
      } else {
        file.status = FileStatus.FAILED;
        file.errorMessage = ffmpegResult.stdErr || '未知错误';
        this.emit('fileStatus', file.path, FileStatus.FAILED, file.errorMessage.substring(0, 200));
        this.emit('fileFinished', file.path, false, file.errorMessage);
        this.emit('log', `  失败: ${file.errorMessage.substring(0, 100)}`);
      }
    } catch (e) {
      console.error('Error processing file:', e);
      this.currentFFmpeg = null;
      file.status = FileStatus.FAILED;
      file.errorMessage = e.message || '处理出错';
      this.emit('fileStatus', file.path, FileStatus.FAILED, file.errorMessage.substring(0, 200));
      this.emit('fileFinished', file.path, false, file.errorMessage);
      this.emit('log', `  错误: ${file.errorMessage}`);
    }
  }

  _buildFFmpegArgs(inputPath, outputPath, timeResult) {
    const args = [];
    const quotedInput = `"${inputPath}"`;
    const quotedOutput = `"${outputPath}"`;

    if (this.precisionMode) {
      args.push('-i', quotedInput);
      if (timeResult.ss !== null) {
        args.push('-ss', timeResult.ss.toString());
      }
      if (timeResult.to !== null) {
        args.push('-to', timeResult.to.toString());
      }
      args.push('-c:v', 'libx264', '-c:a', 'aac');
    } else {
      if (timeResult.ss !== null) {
        args.push('-ss', timeResult.ss.toString());
      }
      args.push('-i', quotedInput);
      if (timeResult.to !== null) {
        args.push('-to', timeResult.to.toString());
      }
      args.push('-c', 'copy', '-map', '0', '-avoid_negative_ts', 'make_zero');
    }

    if (this.movflagsFaststart && outputPath.toLowerCase().endsWith('.mp4')) {
      args.push('-movflags', '+faststart');
    }

    args.push('-y', quotedOutput);

    return args;
  }

  _finishBatch() {
    this.isRunning = false;

    if (this.isCancelled) {
      for (let i = 0; i < this.files.length; i++) {
        if (this.files[i].status === FileStatus.PENDING) {
          this.files[i].status = FileStatus.CANCELLED;
          this.emit('fileStatus', this.files[i].path, FileStatus.CANCELLED, '已取消');
        }
      }
      this.emit('log', '\n任务已取消');
    }

    const success = this.files.filter(f => f.status === FileStatus.SUCCESS).length;
    const failed = this.files.filter(f => f.status === FileStatus.FAILED).length;
    const skipped = this.files.filter(f => f.status === FileStatus.SKIPPED).length;

    this.emit('log', `\n========== 完成 ==========`);
    this.emit('log', `成功: ${success}`);
    this.emit('log', `失败: ${failed}`);
    this.emit('log', `跳过: ${skipped}`);

    this.emit('allFinished', success, failed, skipped);
  }

  _getFileName(path) {
    const lastSlash = path.lastIndexOf('/');
    return lastSlash >= 0 ? path.substring(lastSlash + 1) : path;
  }
}
