# Plan: 新列补算 + 种子防污染

## Context

两个问题一起解决：
1. col_map 有 110 列，klines.duckdb 只有 101 列，新 9 列没入库
2. indicator_cache.py 的 close_cache() 能写回 klines.duckdb = 污染入口

**目标**：
- build_klines_indicators.py 是 klines.duckdb 的**唯一写入口**
- 新列自动检测+补算
- indicator_cache.py 降级为纯函数库（只提供 REGISTRY）
- 其他所有代码只能 read_only 连 klines.duckdb

---

## 改动

### A. `data/build_klines_indicators.py` — 新列自动补算

#### A1：新增 `_backfill_new_cols()` 函数（行 220 前插入）

对新增指标列做全量补算。逻辑：遍历所有 coin/interval 组 → 只算新列 → UPDATE 新列。

#### A2：`build_indicators()` 开头加新列检测（行 227 后）

```python
existing_cols = set(row[0] for row in con.execute("DESCRIBE klines").fetchall())
new_cols = [c for c in indicator_cols if c not in existing_cols]
if new_cols:
    print(f"发现 {len(new_cols)} 个新指标列，创建并补算...")
    for col in new_cols:
        con.execute(f'ALTER TABLE klines ADD COLUMN "{col}" DOUBLE')
    con.commit()
    _backfill_new_cols(con, {c: col_map[c] for c in new_cols})
```

#### A3：更新 docstring

描述新列自动检测+补算能力。

---

### B. `src/core/indicator_cache.py` — 降级为纯函数库

#### B1：删除写回相关代码

- 删除 `_pending_writes` 队列
- 删除 `_make_col_name()` 
- 删除 `_flush_pending_writes()`
- `close_cache()`：只清内存，不碰 DB

#### B2：删除 init_cache / get_indicator / close_cache 的 DB 写逻辑

- `init_cache()`：仍可 preload from duckdb（read_only=True），但不存 duckdb_path 用于写回
- `get_indicator()`：内存命中 → 返回；未命中 → 现场算 → 存内存 → 返回（不入写回队列）
- `close_cache()`：清内存缓存，不写 DB

#### B3：preload 连接强制 read_only

```python
con = duckdb.connect(str(duckdb_path), read_only=True)
```

#### B4：更新 docstring

```
indicator_cache.py — 指标函数注册表 + 运行时内存缓存

REGISTRY：50 个 compute_xxx 函数的注册表，供 build_klines_indicators.py 批量计算。
运行时：preload 从 klines.duckdb 读取（read_only），未命中现场算存内存，不写回 DB。
写入 klines.duckdb 的唯一入口：data/build_klines_indicators.py
```

---

### C. 全链路 read_only 排查

扫描所有连接 klines.duckdb 的代码，确保除 build_klines_indicators.py 外全部用 `read_only=True`。

---

### D. 文档 + CHANGELOG

- CHANGELOG.md 记录
- README_KLINES_SEED.md 更新指标存储描述（写入唯一入口）

---

## 关键文件

| 文件 | 操作 |
|------|------|
| `data/build_klines_indicators.py` | 新增 _backfill_new_cols + 新列检测 |
| `src/core/indicator_cache.py` | 砍写回逻辑，降级为纯函数库 |
| `CHANGELOG.md` | 记录 |
| `data/README_KLINES_SEED.md` | 更新 |

---

## 执行顺序

1. 改 indicator_cache.py（砍写回）
2. 改 build_klines_indicators.py（加新列补算）
3. 排查其他文件的 klines.duckdb 连接
4. 跑 `python3 build_klines_indicators.py`（补算 9 新列 × 240 组）
5. 四件套验证
6. CHANGELOG + 自审

---

## 验证

1. indicator_cache.py 无 `_flush_pending_writes`、无 `_make_col_name`
2. `grep -r "klines.duckdb" --include="*.py"` 除 build_klines_indicators.py 外全部 read_only
3. 跑脚本后 DESCRIBE klines 有 118 列（8 基础 + 110 指标）
4. `SELECT ad, volume_ratio_p20 FROM klines WHERE coin='BTC' AND interval='1h' LIMIT 5` 有值
5. mirror 组也有值
