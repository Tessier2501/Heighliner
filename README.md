# Heighliner

PDF 发票自动重命名与监听守护脚本。`watcher.py` 负责监听下载目录并调用 `rename_invoice.py` 解析金额与发票号，重命名后归档；`test.py` 可帮助检查 PDF 提取出的原始文本。

## 目录结构
- 0_incoming/：浏览器下载的原始 PDF，文件名需为纯数字订单号 (10~20 位)。
- 1_processing/：监听到后暂存处理中的文件。
- 2_processed/：重命名成功后的归档目录。
- 3_failed/：处理失败或被跳过的文件；包含调试工具 [3_failed/test.py](3_failed/test.py)。
- [watcher.py](watcher.py)：守护脚本，轮询 `0_incoming/`，调用 `rename_invoice.py`，并移动结果文件。
- [rename_invoice.py](rename_invoice.py)：解析 PDF，抽取金额与发票号，重命名文件。

## 依赖
- Python 3.10+ 建议。
- 第三方库：`pdfplumber`（依赖 `pdfminer.six` 等）。

安装：
```bash
pip install pdfplumber
```

## 工作流程
1) 将浏览器的下载目录指向仓库内的 `0_incoming/`，或手动把订单号命名的 PDF 放入该目录。
2) 运行监听：
```bash
cd <仓库根目录>
python watcher.py
```
3) `watcher.py` 每 2 秒扫描一次，过滤非 `.pdf`、临时下载后缀（`.crdownload/.part/.tmp/.download`），并对通过筛选的文件执行 0.5 秒稳定性检测（大小/mtime 连续两次不变才处理）。
4) 文件被移动到 `1_processing/`，订单号传给 `rename_invoice.py` 作为 `PLACEHOLDER_PREFIX`。成功后重命名文件移动到 `2_processed/`；若解析缺字段或异常则移动到 `3_failed/` 并在文件名标注原因。

## 解析规则（rename_invoice.py）
- 金额：匹配包含“价税合计…¥123.45”的行 (`AMOUNT_PATTERN`)。
- 发票号：匹配包含“发票号码：<数字>”的行 (`INVOICE_PATTERN`)。
- 校验：寻找“合 计”之后的两笔金额 (`LINE_AMOUNT_PATTERN`)，两者之和需等于“价税合计”。
- 重命名格式：`<订单号>_<金额>_<发票号>.pdf`（金额去掉逗号）。若重名则追加递增后缀。

## 常见问题与排查
- 解析缺失（日志显示 `Skipped (missing amount, invoice, sum_parts)`）：
	- PDF 可能为扫描件/图片，`pdfplumber` 无法提取文本；需先做 OCR。
	- 文案/符号与正则不一致：检查是否使用“￥”/缺少“¥”、标签不同（如“价税合计(小写)”），可调整正则以放宽匹配。
	- 行内有特殊空格或换行，导致模式跨行失败，调试见下。
- 校验失败（`sum mismatch`）：票面两笔金额之和与“价税合计”不等，需人工确认票据或放宽校验。
- 被抢占下载：已通过临时后缀过滤和稳定性检测缓解，如仍触发，可增大 `POLL_INTERVAL` 或 `wait_until_stable` 的 `checks/interval`。

### 调试 PDF 文本
使用 [3_failed/test.py](3_failed/test.py) 打印提取的逐行文本，观察实际字符与格式：
```bash
cd 3_failed
python test.py
```
根据输出调整正则（`AMOUNT_PATTERN`、`INVOICE_PATTERN`、`LINE_AMOUNT_PATTERN` 等）。

## 可调参数
- [watcher.py](watcher.py)
	- `POLL_INTERVAL`：轮询间隔（秒）。
	- `TEMP_SUFFIXES`：临时下载后缀白名单。
	- `wait_until_stable(... interval, checks ...)`：文件稳定性检测的间隔与次数。
	- `ORDER_ID_PATTERN`：订单号命名规则。
- [rename_invoice.py](rename_invoice.py)
	- `PLACEHOLDER_PREFIX`：监听模式下会被订单号覆盖；单独运行时需手动设置。
	- 正则模式：`AMOUNT_PATTERN`、`INVOICE_PATTERN`、`TOTAL_HEADER_PATTERN`、`LINE_AMOUNT_PATTERN` 可按票面调整。

## 独立批处理（不跑 watcher）
将待处理 PDF 放到与 [rename_invoice.py](rename_invoice.py) 同目录，设置 `PLACEHOLDER_PREFIX`，然后运行：
```bash
python rename_invoice.py
```
脚本会遍历当前目录下的所有 `.pdf` 并尝试重命名。

## 安全与日志
- 移动操作使用 `shutil.move`，同分区近似原子；跨分区为复制+删除。
- 失败文件名会附加 `__FAILED__<原因>`，避免覆盖。
- 控制台打印所有处理步骤，可重定向输出留存日志。
