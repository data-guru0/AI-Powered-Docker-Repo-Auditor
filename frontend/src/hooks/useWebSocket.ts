"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { ScanProgressEvent } from "@/types/scan";
import { getIdToken } from "@/lib/auth";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL;

export function useWebSocket(jobId: string | null) {
  const [event, setEvent] = useState<ScanProgressEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef(true);

  const connect = useCallback(async () => {
    if (!jobId || !WS_URL) return;
    const token = await getIdToken();
    const url = `${WS_URL}?token=${token}&jobId=${jobId}`;

    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      setConnected(true);
    };

    ws.current.onmessage = (e) => {
      try {
        const data: ScanProgressEvent = JSON.parse(e.data);
        setEvent(data);
      } catch {
        /* ignore malformed messages */
      }
    };

    ws.current.onclose = () => {
      setConnected(false);
      if (shouldReconnect.current && jobId) {
        reconnectTimer.current = setTimeout(() => connect(), 3000);
      }
    };

    ws.current.onerror = () => {
      ws.current?.close();
    };
  }, [jobId]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();
    return () => {
      shouldReconnect.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  return { event, connected };
}
