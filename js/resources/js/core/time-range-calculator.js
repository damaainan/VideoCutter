
/**
 * 时间范围计算模块
 */

const TimeMode = {
  TRIM_HEAD_TAIL: 'trim_head_tail',
  ABSOLUTE_START_END: 'absolute_start_end'
};

class TimeRangeCalculator {
  static calculate(duration, mode, valueA, valueB) {
    const result = {
      valid: false,
      ss: null,
      to: null,
      errorMessage: ''
    };

    if (mode === TimeMode.TRIM_HEAD_TAIL) {
      return this._calculateTrimHeadTail(duration, valueA, valueB, result);
    } else if (mode === TimeMode.ABSOLUTE_START_END) {
      return this._calculateAbsolute(duration, valueA, valueB, result);
    }

    result.errorMessage = '无效的时间模式';
    return result;
  }

  static _calculateTrimHeadTail(duration, trimHead, trimTail, result) {
    let start = 0;
    let end = duration;

    if (trimHead !== null && trimHead !== undefined) {
      if (trimHead < 0) {
        result.errorMessage = '开头裁剪时间不能为负数';
        return result;
      }
      if (duration > 0 && trimHead >= duration) {
        result.errorMessage = '开头裁剪时间不能大于等于视频总时长';
        return result;
      }
      start = trimHead;
    }

    if (trimTail !== null && trimTail !== undefined) {
      if (trimTail < 0) {
        result.errorMessage = '结尾裁剪时间不能为负数';
        return result;
      }
      if (duration > 0 && trimTail >= duration) {
        result.errorMessage = '结尾裁剪时间不能大于等于视频总时长';
        return result;
      }
      end = duration - trimTail;
    }

    if (start >= end) {
      result.errorMessage = '裁剪参数无效：开头加结尾裁剪时间超过总时长';
      return result;
    }

    result.valid = true;
    result.ss = start > 0 ? start : null;
    result.to = end < duration ? end : null;
    return result;
  }

  static _calculateAbsolute(duration, startTime, endTime, result) {
    let start = 0;
    let end = duration;

    if (startTime !== null && startTime !== undefined) {
      if (startTime < 0) {
        result.errorMessage = '开始时间不能为负数';
        return result;
      }
      if (duration > 0 && startTime >= duration) {
        result.errorMessage = '开始时间不能大于等于视频总时长';
        return result;
      }
      start = startTime;
    }

    if (endTime !== null && endTime !== undefined) {
      if (endTime < 0) {
        result.errorMessage = '结束时间不能为负数';
        return result;
      }
      if (duration > 0 && endTime > duration) {
        result.errorMessage = '结束时间不能大于视频总时长';
        return result;
      }
      end = endTime;
    }

    if (start >= end) {
      result.errorMessage = '开始时间必须小于结束时间';
      return result;
    }

    result.valid = true;
    result.ss = start > 0 ? start : null;
    result.to = end < duration ? end : null;
    return result;
  }
}
