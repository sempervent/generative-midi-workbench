import type { Track } from "../types";
import api from "./client";

export const tracksApi = {
  async toggleMute(trackId: string, muted: boolean): Promise<Track> {
    const response = await api.patch<Track>(`/tracks/${trackId}/mute?muted=${muted}`);
    return response.data;
  },
  async toggleSolo(trackId: string, soloed: boolean): Promise<Track> {
    const response = await api.patch<Track>(`/tracks/${trackId}/solo?soloed=${soloed}`);
    return response.data;
  },
};
