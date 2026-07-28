import React, { useEffect, useState } from 'react';
import { Button, Space, Tag, Tooltip, Typography } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';

const { Text } = Typography;
const SAMPLE_DURATION_MS = 5_000;

interface GraphReadyDetail {
  renderer: 'd3' | 'cosmos';
  nodes: number;
  edges: number;
  interactiveMs: number;
}

interface BenchmarkResult extends GraphReadyDetail {
  sampledAt: string;
  sampleDurationMs: number;
  averageFps: number;
  slowFramePercent: number;
  domElements: number;
  heapUsedBytes?: number;
  userAgent: string;
}

declare global {
  interface Window {
    __ECMS_GRAPH_BENCHMARK__?: BenchmarkResult;
  }
}

export const GraphBenchmarkBadge: React.FC = () => {
  const [result, setResult] = useState<BenchmarkResult | null>(null);
  const [sampling, setSampling] = useState(false);

  useEffect(() => {
    let frameId = 0;
    const handleReady = (event: Event) => {
      const detail = (event as CustomEvent<GraphReadyDetail>).detail;
      const startedAt = performance.now();
      let previousFrame = startedAt;
      let frames = 0;
      let slowFrames = 0;
      setSampling(true);

      const sampleFrame = (now: number) => {
        const delta = now - previousFrame;
        previousFrame = now;
        frames += 1;
        if (delta > 33.34) slowFrames += 1;

        if (now - startedAt < SAMPLE_DURATION_MS) {
          frameId = requestAnimationFrame(sampleFrame);
          return;
        }

        const duration = now - startedAt;
        const memory = (
          performance as Performance & {
            memory?: { usedJSHeapSize: number };
          }
        ).memory;
        const nextResult: BenchmarkResult = {
          ...detail,
          sampledAt: new Date().toISOString(),
          sampleDurationMs: Math.round(duration),
          averageFps: Number(((frames * 1_000) / duration).toFixed(1)),
          slowFramePercent: Number(((slowFrames / Math.max(frames, 1)) * 100).toFixed(1)),
          domElements: document.getElementsByTagName('*').length,
          heapUsedBytes: memory?.usedJSHeapSize,
          userAgent: navigator.userAgent,
        };
        window.__ECMS_GRAPH_BENCHMARK__ = nextResult;
        setResult(nextResult);
        setSampling(false);
      };

      frameId = requestAnimationFrame(sampleFrame);
    };

    window.addEventListener('ecms:knowledge-graph-ready', handleReady);
    return () => {
      window.removeEventListener('ecms:knowledge-graph-ready', handleReady);
      cancelAnimationFrame(frameId);
    };
  }, []);

  const download = () => {
    if (!result) return;
    const blob = new Blob([`${JSON.stringify(result, null, 2)}\n`], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `knowledge-graph-${result.renderer}-${result.nodes}-${Date.now()}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      data-testid="knowledge-graph-benchmark"
      style={{
        position: 'absolute',
        top: 58,
        left: 12,
        zIndex: 11,
        border: '1px solid #bfdbfe',
        borderRadius: 8,
        background: 'rgba(239, 246, 255, 0.94)',
        padding: '7px 10px',
        boxShadow: '0 4px 12px rgba(37, 99, 235, 0.08)',
      }}
    >
      {result ? (
        <Space size={7}>
          <Tag color="blue" style={{ margin: 0 }}>
            {result.renderer.toUpperCase()} PROOF
          </Tag>
          <Text style={{ fontSize: 11 }}>{result.interactiveMs} ms interactive</Text>
          <Text style={{ fontSize: 11 }}>{result.averageFps} FPS</Text>
          <Text style={{ fontSize: 11 }}>{result.slowFramePercent}% slow frames</Text>
          <Tooltip title="Download benchmark JSON">
            <Button
              aria-label="Download benchmark JSON"
              type="text"
              size="small"
              icon={<DownloadOutlined />}
              onClick={download}
            />
          </Tooltip>
        </Space>
      ) : (
        <Text style={{ fontSize: 11, color: '#1d4ed8' }}>
          {sampling ? 'Sampling interaction FPS for 5 seconds…' : 'Waiting for renderer…'}
        </Text>
      )}
    </div>
  );
};

