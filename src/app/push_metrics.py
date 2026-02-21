import asyncio
import time

import grpc.aio
import psutil
from contracts.metrics import metrics_pb2
from contracts.metrics import metrics_pb2_grpc


class MetricsPusher:
    def __init__(self, node_id: str, host: str, port: str, grpc_target: str):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.grpc_target = grpc_target

        self.channel = grpc.aio.insecure_channel(
            grpc_target,
            options=[
                ("grpc.keepalive_time_ms", 10000),
                ("grpc.keepalive_timeout_ms", 5000),
                ("grpc.keepalive_permit_without_calls", 1),
            ],
        )
        self.stub = metrics_pb2_grpc.MetricsServiceStub(self.channel)

        self._stop = asyncio.Event()

    async def start(self, interval_s: float = 0.25):
        psutil.cpu_percent(interval=None)

        prev_net = psutil.net_io_counters()
        while not self._stop.is_set():
            ts = int(time.time() * 1000)

            cpu = psutil.cpu_percent(interval=None) / 100.0
            mem = psutil.virtual_memory().percent / 100.0

            net = psutil.net_io_counters()
            net_in = float(net.bytes_recv)
            net_out = float(net.bytes_sent)

            msg = metrics_pb2.NodeMetrics(
                node_id=self.node_id,
                host=self.host,
                port=int(self.port),
                timestamp_unix_ms=ts,
                cpu_util=float(cpu),
                mem_util=float(mem),
                net_in_bytes=net_in,
                net_out_bytes=net_out,
                latency_ms=0.0,
            )

            batch = metrics_pb2.NodeMetricsBatch(items=[msg])

            try:
                await self.stub.PushMetrics(batch, timeout=2)
            except Exception as e:
                print("metrics push failed:", repr(e))

            prev_net = net
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval_s)
            except asyncio.TimeoutError:
                pass

    async def stop(self):
        self._stop.set()
        await self.channel.close()
