# Plan: build_klines_indicators.py 完整供应链整合

## Context

K 线数据供应链断了三截：
1. 下载脚本在 auto-trading 里，DATA_DIR 指向错误路径，wuji 侧没有
2. JSON → klines.duckdb 导入脚本从来不存在（44GB 是手动搬的）
3. daily_pipeline.py 没调 build_klines_indicators.py

**目标**：build_klines_indicators.py 变成完整四阶段，一条命令跑完全链路。

---

## 改动

### 文件：`data/build_klines_indicators.py`

#### 新增阶段 0：Binance 增量下载

从 download_latest_coins_2.0.py 搬核心逻辑：
- ccxt.binance 连接（现货 + delivery）
- USDT_PAIRS（10 个）+ COIN_MARGINED_PAIRS（3 个）
- DOWNLOAD_CONFIG（10 周期 × 目标行数）
- download_coin() 函数（断点续传：往前补历史 + 往后补最新）
- DATA_DIR 改为 `wuji-auto-trading/data/historical/`

```python
def download_all_coins() -> None:
    """阶段 0：从 Binance 增量下载 K 线到 data/historical/"""
    import ccxt
    # ... 搬 download_latest_coins_2.0.py 的核心代码
    # DATA_DIR = Path(DATA_DIR) / "historical"（用现有 path_config）
```

#### 新增阶段 0.5：JSON → klines.duckdb 导入

遍历 data/historical/{COIN}/{interval}.json，增量导入到 klines 表。

```python
def import_json_to_duckdb(con) -> None:
    """阶段 0.5：将 historical/*.json 增量导入 klines 表"""
    historical_dir = Path(DATA_DIR) / "historical"
    
    for coin_dir in sorted(historical_dir.iterdir()):
        if not coin_dir.is_dir():
            continue
        coin = coin_dir.name
        for json_file in sorted(coin_dir.glob("*.json")):
            interval = json_file.stem  # "1h" from "1h.json"
            
            # 读 JSON
            data = json.loads(json_file.read_text())
            if not data:
                continue
            
            # 查 DB 里该 coin/interval 的最大 time
            existing_max = con.execute(
                "SELECT MAX(time) FROM klines WHERE coin = ? AND interval = ?",
                [coin, interval]
            ).fetchone()[0]
            
            # 过滤：只 INSERT 新行
            if existing_max:
                new_rows = [d for d in data if d["time"] > existing_max]
            else:
                new_rows = data  # 全新 coin/interval
            
            if not new_rows:
                continue
            
            # INSERT via DataFrame
            df = pd.DataFrame(new_rows)
            df["coin"] = coin
            df["interval"] = interval
            con.register("tmp_import", df)
            con.execute("""
                INSERT INTO klines (coin, interval, time, open, high, low, close, volume)
                SELECT coin, interval, time, open, high, low, close, volume
                FROM tmp_import
            """)
            con.unregister("tmp_import")
            con.commit()
            print(f"  [导入] {coin}/{interval} +{len(new_rows)} 行")
```

#### 阶段 1：mirror 生成（不动）

现有逻辑已正确：检测没有 _mirror 的组 → 价格取负 → INSERT。
增量安全：新增 K 线对应的 mirror 会被自动补上。

但需要改进：不只检测"是否存在 mirror"，还要检测 mirror 行数是否与原生一致（新 K 线追加后 mirror 少了）。

```python
# 改进：检测 mirror 行数 < 原生行数的组（增量追加场景）
groups = con.execute("""
    SELECT n.coin, n.interval
    FROM (SELECT coin, interval, COUNT(*) as cnt FROM klines 
          WHERE coin NOT LIKE '%_mirror' GROUP BY coin, interval) n
    LEFT JOIN (SELECT REPLACE(coin, '_mirror', '') as coin, interval, COUNT(*) as cnt 
               FROM klines WHERE coin LIKE '%_mirror' GROUP BY coin, interval) m
    ON n.coin = m.coin AND n.interval = m.interval
    WHERE m.cnt IS NULL OR m.cnt < n.cnt
""").fetchall()
```

实际做法更简单：**删掉旧 mirror，重新全量生成**。mirror 生成很快（120 组几十秒）。

#### 阶段 2：指标计算（不动）

现有新列检测 + 断点续传逻辑已正确。

#### 入口改造

```python
if __name__ == "__main__":
    # 阶段 0：下载
    download_all_coins()
    
    con = _open_db()
    try:
        # 阶段 0.5：JSON → DuckDB
        import_json_to_duckdb(con)
        # 阶段 1：mirror
        build_mirror_klines(con)
        # 阶段 2：指标
        build_indicators(con)
    finally:
        con.close()
```

支持 `--skip-download` 参数（本地数据已有时跳过下载）。

---

## 阶段 1 增量 mirror 策略

新 K 线追加后，原生有新行但 mirror 没有。两种方案：

**方案 A：删除重建**（推荐）
```sql
DELETE FROM klines WHERE coin LIKE '%_mirror'
```
然后全量重建。mirror 生成极快（120 组 × 几十秒），逻辑简单无 bug。

**方案 B：增量追加**
只对 mirror 行数 < 原生行数的组，补算缺失的行。更复杂但省时间。

选方案 A（简单可靠，符合静制动）。

---

## 新增依赖

- `ccxt`（已安装，download 脚本用的）
- `argparse`（标准库）

---

## 关键文件

| 文件 | 操作 |
|------|------|
| `data/build_klines_indicators.py` | 新增阶段 0（下载）+ 阶段 0.5（导入）+ 改进阶段 1（mirror 增量）|
| `CHANGELOG.md` | 记录 |

---

## 执行顺序

1. 改 build_klines_indicators.py（加阶段 0 + 0.5 + 改阶段 1）
2. 四件套验证（语法+逻辑+链路）
3. 先跑 `--skip-download` 模式测试导入+mirror+指标
4. 再跑完整模式测试下载
5. CHANGELOG + 自审

---

## 验证

1. `python3 build_klines_indicators.py --skip-download`：阶段 0.5 检测到无新 JSON → 跳过；阶段 1 mirror 数量一致 → 跳过；阶段 2 指标满 → 跳过
2. 手动往某个 JSON 追加几行假数据 → 重跑 → 验证 INSERT + mirror + 指标都补上
3. `python3 build_klines_indicators.py`：完整下载（Binance API 可达性）
4. klines.duckdb 最新时间戳应接近当前时间
