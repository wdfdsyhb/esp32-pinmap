# esp32-pinmap

[![CI](https://github.com/wdfdsyhb/esp32-pinmap/actions/workflows/tests.yml/badge.svg)](https://github.com/wdfdsyhb/esp32-pinmap/actions/workflows/tests.yml)

**Which GPIO can you actually use?** Safe-pin lookup CLI for classic ESP32 / ESP32-S3 / ESP32-C3.

查一下这根脚到底能不能用：strapping 引脚、flash/PSRAM 占用、USB-JTAG、UART0 控制台、input-only——新手"LED 不亮"的一半问题都出在挑错了脚。

## Why

每块 ESP32 都有一批"看着是 IO、实际动不得"的引脚：接了 LED 导致启动失败（strapping）、一动就崩溃（flash）、插上就断 USB（USB-JTAG）。文章速查表很多，但没有一个能在终端里直接回答"GPIO46 能干嘛"。esp32-pinmap 把官方 datasheet 里的分类做成了本地查询。

## Usage

```bash
python esp32_pinmap.py s3 0        # 单脚查询：为什么 GPIO0 特殊
python esp32_pinmap.py s3 --safe   # 列出安全引脚
python esp32_pinmap.py s3 --safe --output-only   # 只要能点 LED 的
python esp32_pinmap.py esp32 --table             # 全表 markdown，粘进笔记
```

输出示例：

```
$ python esp32_pinmap.py s3 0
GPIO0 (esp32-s3): RESERVED (strapping)
  boot mode; must be HIGH at reset

$ python esp32_pinmap.py s3 --safe --output-only
esp32-s3 safe pins (output-capable):
  1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 21, 38, 39, 40, 41, 42, 47, 48
```

## Covered boards

| 板卡 | 关键保留脚 |
|---|---|
| classic ESP32 (WROOM/WROVER) | strapping 0/2/5/12/15, flash 6-11, UART0 1/3, input-only 34-39 |
| ESP32-S3 (含 N8R8 octal PSRAM) | strapping 0/3/45/46, flash 26-32, PSRAM 33-37, USB-JTAG 19/20, UART0 43/44 |
| ESP32-C3 | strapping 2/8/9, flash 11-17, USB-JTAG 18/19, UART0 20/21 |

## Honest notes

- 数据来自 Espressif datasheet 的常见配置，WROOM/WROVER、N8/NR8 等模组差异在 note 里标了；**量产前以你手上模组的官方 datasheet 为准**，发现错漏欢迎 PR
- 判定标准偏保守：strapping 一律不建议接外部负载（加缓冲可用的场景自己权衡）
- 零依赖，纯标准库，数据就在脚本里一个 dict，改起来不用读代码

## License

MIT
