import type { ArrangementPanel } from "../types";
import api from "./client";

export const arrangementApi = {
  async getPanel(projectId: string): Promise<ArrangementPanel> {
    const response = await api.get<ArrangementPanel>(`/projects/${projectId}/arrangement/panel`);
    return response.data;
  },
};
