
/**
 * 文件冲突处理策略模块
 */

const ConflictStrategy = {
  ASK: 'ask',
  RENAME: 'rename',
  SKIP: 'skip',
  OVERWRITE: 'overwrite'
};

class OverwritePolicy {
  constructor(strategy = ConflictStrategy.RENAME) {
    this.strategy = strategy;
  }

  async getOutputPath(inputPath, suffix) {
    console.log('OverwritePolicy.getOutputPath called');
    console.log('inputPath:', inputPath);
    console.log('suffix:', suffix);

    // 兼容 / 和 \ 路径分隔符
    const normalized = inputPath.replace(/\\/g, '/');
    const lastSlash = normalized.lastIndexOf('/');
    const lastDot = normalized.lastIndexOf('.');

    const dir = lastSlash >= 0 ? normalized.substring(0, lastSlash + 1) : '';
    const ext = (lastDot > lastSlash) ? normalized.substring(lastDot) : '';
    const baseName = lastSlash >= 0
      ? normalized.substring(lastSlash + 1, (lastDot > lastSlash) ? lastDot : undefined)
      : ((lastDot > lastSlash) ? normalized.substring(0, lastDot) : normalized);

    const outputPath = dir + baseName + suffix + ext;
    console.log('Returning outputPath:', outputPath);
    return { path: outputPath, status: 'ok' };
  }
}
