import type { Clip } from "../types";
import api from "./client";

export const clipsApi = {
  async toggleMute(clipId: string, muted: boolean): Promise<Clip> {
    const response = await api.patch<Clip>(`/clips/${clipId}/mute?muted=${muted}`);
    return response.data;
  },

  async toggleSolo(clipId: string, soloed: boolean): Promise<Clip> {
    const response = await api.patch<Clip>(`/clips/${clipId}/solo?soloed=${soloed}`);
    return response.data;
  },
};
