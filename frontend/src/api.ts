export type MessageReply = {
  response: string;
  speechUrl?: string;
};

const API_BASE = "http://127.0.0.1:5050";

async function parseResponse(response: Response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.message || `Request failed (${response.status})`);
  }
  return data;
}

export async function sendInteraction(
  interactionValue: number,
): Promise<MessageReply> {
  const response = await fetch(`${API_BASE}/doSpecialInteraction`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      interaction_value: interactionValue,
    }),
  });

  const data = await parseResponse(response);
  if (typeof data.response !== "string") {
    throw new Error("Invalid interaction response");
  }
  return {
    response: data.response,
    speechUrl:
      typeof data.audio_url === "string" &&
      data.audio_url.startsWith("/reaction_audio/")
        ? `${API_BASE}${data.audio_url}`
        : undefined,
  };
}
