export type AudioInput = { deviceId: string; label: string };

function isNotFound(err: unknown): boolean {
  const dom = err as DOMException;
  return (
    dom?.name === "NotFoundError" ||
    (dom?.message?.includes("Requested device not found") ?? false)
  );
}

export function microphoneUnavailableReason(): string | null {
  if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
    return "Microphone API is not available in this browser.";
  }
  if (typeof window !== "undefined" && !window.isSecureContext) {
    return "Microphone requires HTTPS. Open the app with https:// (not http://).";
  }
  return null;
}

export async function listAudioInputs(): Promise<AudioInput[]> {
  const devices = await navigator.mediaDevices.enumerateDevices();
  return devices
    .filter((d) => d.kind === "audioinput" && d.deviceId)
    .map((d, i) => ({
      deviceId: d.deviceId,
      label: d.label || `Microphone ${i + 1}`,
    }));
}

export function mapMicrophoneError(err: unknown): string {
  const dom = err as DOMException;
  const name = dom?.name ?? "";
  const msg = dom?.message ?? (err instanceof Error ? err.message : String(err));

  if (name === "NotAllowedError" || name === "PermissionDeniedError") {
    return "Microphone permission denied. Allow mic access in your browser site settings and try again.";
  }
  if (name === "NotReadableError" || name === "TrackStartError") {
    return "Microphone is in use by another app. Close other apps using the mic and try again.";
  }
  if (isNotFound(err)) {
    return "No microphone found. Connect or enable an input device in system sound settings, then refresh the page.";
  }
  return msg || "Could not access microphone.";
}

/** Request mic access; tries other inputs if the default device is missing. */
export async function getMicrophoneStream(deviceId?: string): Promise<MediaStream> {
  const blocked = microphoneUnavailableReason();
  if (blocked) throw new Error(blocked);

  const tryStream = (id?: string) =>
    navigator.mediaDevices.getUserMedia({
      audio: id ? { deviceId: { exact: id } } : true,
    });

  if (deviceId) {
    try {
      return await tryStream(deviceId);
    } catch (err) {
      throw new Error(mapMicrophoneError(err));
    }
  }

  try {
    return await tryStream();
  } catch (firstErr) {
    if (!isNotFound(firstErr)) {
      throw new Error(mapMicrophoneError(firstErr));
    }
  }

  // Default device missing (common with disconnected Bluetooth headsets) — try others
  const inputs = await listAudioInputs();
  for (const input of inputs) {
    try {
      return await tryStream(input.deviceId);
    } catch (err) {
      if (!isNotFound(err)) throw new Error(mapMicrophoneError(err));
    }
  }

  throw new Error(mapMicrophoneError(new DOMException("Requested device not found", "NotFoundError")));
}
