"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import {
  getMicrophoneStream,
  listAudioInputs,
  microphoneUnavailableReason,
  type AudioInput,
} from "@/lib/microphone";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Spinner } from "./ui/spinner";

type Props = { projectId: string };

type Status = "idle" | "connecting" | "connected" | "error";

export function VoicePanel({ projectId }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [audioInputs, setAudioInputs] = useState<AudioInput[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const dcRef = useRef<RTCDataChannel | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    const blocked = microphoneUnavailableReason();
    if (blocked) {
      setError(blocked);
      return;
    }
    listAudioInputs()
      .then(setAudioInputs)
      .catch(() => {});
    return () => disconnect();
  }, []);

  function log(line: string) {
    setTranscript((t) => [...t.slice(-20), line]);
  }

  async function handleToolCall(name: string, argsJson: string, callId: string) {
    if (name !== "search_library") return;
    const args = JSON.parse(argsJson || "{}");
    const query = args.query || "";
    const result = await api.voiceTool(projectId, query);
    const output = JSON.stringify({ snippets: result.snippets });

    dcRef.current?.send(
      JSON.stringify({
        type: "conversation.item.create",
        item: {
          type: "function_call_output",
          call_id: callId,
          output,
        },
      })
    );
    dcRef.current?.send(JSON.stringify({ type: "response.create" }));
  }

  async function connect() {
    setError(null);
    setStatus("connecting");
    try {
      const session = await api.voiceSession(projectId);
      const token = session.client_secret;
      if (!token) throw new Error("No voice session token");

      const pc = new RTCPeerConnection();
      pcRef.current = pc;

      const audioEl = document.createElement("audio");
      audioEl.autoplay = true;
      audioRef.current = audioEl;
      pc.ontrack = (e) => {
        audioEl.srcObject = e.streams[0];
      };

      const ms = await getMicrophoneStream(selectedDeviceId || undefined);
      micStreamRef.current = ms;
      ms.getTracks().forEach((track) => pc.addTrack(track, ms));

      const inputs = await listAudioInputs();
      if (inputs.length) setAudioInputs(inputs);

      const dc = pc.createDataChannel("oai-events");
      dcRef.current = dc;

      dc.addEventListener("message", async (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === "response.function_call_arguments.done") {
            await handleToolCall(msg.name, msg.arguments, msg.call_id);
          }
          if (
            msg.type === "response.audio_transcript.done" ||
            msg.type === "response.output_audio_transcript.done"
          ) {
            log(`Noteslash: ${msg.transcript}`);
          }
          if (
            msg.type === "conversation.item.input_audio_transcription.completed" ||
            msg.type === "conversation.item.input_audio_transcription.done"
          ) {
            log(`You: ${msg.transcript}`);
          }
        } catch {
          /* ignore parse errors */
        }
      });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const sdpResponse = await fetch("https://api.openai.com/v1/realtime/calls", {
        method: "POST",
        body: offer.sdp,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/sdp",
        },
      });

      if (!sdpResponse.ok) {
        throw new Error(`Realtime connection failed: ${sdpResponse.status}`);
      }

      const answer = { type: "answer" as RTCSdpType, sdp: await sdpResponse.text() };
      await pc.setRemoteDescription(answer);
      setStatus("connected");
      log("Voice connected — start speaking.");
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Voice connection failed");
    }
  }

  function disconnect() {
    dcRef.current?.close();
    pcRef.current?.close();
    dcRef.current = null;
    pcRef.current = null;
    micStreamRef.current?.getTracks().forEach((t) => t.stop());
    micStreamRef.current = null;
    if (audioRef.current) {
      audioRef.current.srcObject = null;
      audioRef.current = null;
    }
    setStatus("idle");
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-600">
        Talk with Noteslash about your library. The assistant searches your indexed content before
        answering. Requires a working microphone and HTTPS in production.
      </p>
      {audioInputs.length > 1 && status !== "connected" && (
        <label className="block text-sm text-neutral-600">
          Microphone
          <select
            className="mt-1 w-full max-w-md rounded-md border border-neutral-300 bg-white px-3 py-2 text-neutral-900"
            value={selectedDeviceId}
            onChange={(e) => setSelectedDeviceId(e.target.value)}
            disabled={status === "connecting"}
          >
            <option value="">System default</option>
            {audioInputs.map((d) => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="flex items-center gap-3">
        {status === "connected" ? (
          <Badge className="bg-emerald-100 text-emerald-800">Live</Badge>
        ) : status === "connecting" ? (
          <Badge>Connecting…</Badge>
        ) : (
          <Badge>Offline</Badge>
        )}
        {status !== "connected" ? (
          <Button onClick={connect} disabled={status === "connecting"}>
            {status === "connecting" ? (
              <span className="flex items-center gap-2">
                <Spinner className="h-4 w-4" /> Connecting
              </span>
            ) : (
              "Start voice"
            )}
          </Button>
        ) : (
          <Button variant="secondary" onClick={disconnect}>
            End session
          </Button>
        )}
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {transcript.length > 0 && (
        <div className="max-h-64 overflow-auto rounded-lg border border-neutral-200 bg-white p-3 text-sm">
          {transcript.map((line, i) => (
            <p key={i} className="mb-1 text-neutral-700">
              {line}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
