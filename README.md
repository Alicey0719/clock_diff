# clock_diff

NTPサーバーとのシステムクロックのずれを監視するツールです。

## 使い方

```bash
python3 clock_diff.py
```

### オプション

- `-s, --server` : NTPサーバー（デフォルト: ntp.nict.jp）
- `-i, --interval` : ポーリング間隔（秒、デフォルト: 1.0）

