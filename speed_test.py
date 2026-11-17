#!/usr/bin/env python3
"""Последовательный замер скорости скачивания по URL."""

from __future__ import annotations

import argparse
import ssl
import sys
import time
import urllib.error
import urllib.request

DEFAULT_REQUESTS = 10
USER_AGENT = "internet-speed-cli/1.0"


def fetch(url: str, timeout: float) -> tuple[float, int]:
    """Скачивает ресурс целиком; возвращает (секунды, байты)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        data = response.read()
    elapsed = time.perf_counter() - start
    return elapsed, len(data)


def format_bytes(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.2f} MiB"
    if n >= 1024:
        return f"{n / 1024:.2f} KiB"
    return f"{n} B"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Делает несколько последовательных GET-запросов и считает скорость скачивания.",
    )
    parser.add_argument("url", help="Адрес ресурса (например, URL тяжёлой картинки)")
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=DEFAULT_REQUESTS,
        metavar="N",
        help=f"Число запросов (по умолчанию {DEFAULT_REQUESTS})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        metavar="SEC",
        help="Таймаут одного запроса в секундах (по умолчанию 120)",
    )
    args = parser.parse_args()

    if args.count < 1:
        print("Число запросов должно быть не меньше 1.", file=sys.stderr)
        return 1

    durations: list[float] = []
    total_bytes = 0

    print(f"URL: {args.url}")
    print(f"Запросов: {args.count}\n")

    for i in range(1, args.count + 1):
        try:
            elapsed, size = fetch(args.url, args.timeout)
        except urllib.error.URLError as exc:
            print(f"Запрос {i}/{args.count}: ошибка — {exc}", file=sys.stderr)
            return 1
        durations.append(elapsed)
        total_bytes += size
        print(
            f"Запрос {i}/{args.count}: {elapsed:.3f} с, "
            f"получено {format_bytes(size)}"
        )

    wall_total = sum(durations)
    avg_time = wall_total / len(durations)
    # Скорость: весь объём, делённый на суммарное время всех запросов (последовательно)
    mib_per_sec = (total_bytes / (1024 * 1024)) / wall_total if wall_total > 0 else 0.0
    mbit_per_sec = (total_bytes * 8 / 1_000_000) / wall_total if wall_total > 0 else 0.0

    print()
    print("--- Итог ---")
    print(f"Среднее время запроса: {avg_time:.3f} с")
    print(f"Суммарный объём данных: {format_bytes(total_bytes)} ({total_bytes} байт)")
    print(f"Суммарное время загрузки: {wall_total:.3f} с")
    print(f"Скорость скачивания: {mib_per_sec:.2f} MiB/s ({mbit_per_sec:.2f} Mbit/s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())