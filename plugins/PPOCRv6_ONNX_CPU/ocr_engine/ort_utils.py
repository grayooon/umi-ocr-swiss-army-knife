# ===============================================
# =============== ONNXRuntime 封装 ===============
# ===============================================
# 全部使用 CPUExecutionProvider ，纯 CPU 计算，不需要显卡、不联网。

import os


def cpu_count(default=4):
    try:
        n = os.cpu_count()
        return n if n and n > 0 else default
    except Exception:
        return default


def make_session(model_path, num_threads=0, inter_threads=1, log_severity=3):
    """创建一个纯 CPU 的 InferenceSession 。

    num_threads : 单个算子内部的并行线程数(intra_op)。0 = 自动(物理核心数)。
    inter_threads: 算子之间的并行线程数(inter_op)。CPU 上一般 1 即可。
    """
    import onnxruntime as ort
    ort.disable_telemetry_events()

    ort.set_default_logger_severity(log_severity)
    so = ort.SessionOptions()
    if num_threads and num_threads > 0:
        so.intra_op_num_threads = int(num_threads)
    else:
        so.intra_op_num_threads = max(1, cpu_count())
    so.inter_op_num_threads = max(1, int(inter_threads or 1))
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    # 关闭内存竞技场可略微降低常驻内存（对小模型更友好）
    so.enable_cpu_mem_arena = True
    sess = ort.InferenceSession(
        model_path, sess_options=so, providers=["CPUExecutionProvider"])
    return sess


def session_io(sess):
    """返回 (输入名, 输出名列表, 输入shape)"""
    inp = sess.get_inputs()[0]
    outs = [o.name for o in sess.get_outputs()]
    return inp.name, outs, list(inp.shape)


def ort_version():
    try:
        import onnxruntime as ort
        return ort.__version__
    except Exception:
        return "?"
