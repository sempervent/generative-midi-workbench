import { defineStore } from "pinia";
import { ref } from "vue";
import { projectsApi } from "../api/projects";
import type { Arrangement, Project } from "../types";

export const useProjectStore = defineStore("project", () => {
  const currentProject = ref<Project | null>(null);
  const currentArrangement = ref<Arrangement | null>(null);
  const loading = ref(false);

  async function loadProject(id: string) {
    loading.value = true;
    try {
      currentProject.value = await projectsApi.get(id);
      await loadArrangement(id);
    } finally {
      loading.value = false;
    }
  }

  async function loadArrangement(id: string) {
    try {
      currentArrangement.value = await projectsApi.getArrangement(id);
    } catch (error) {
      console.error("Failed to load arrangement:", error);
    }
  }

  async function updateProject(id: string, data: Partial<Project>) {
    currentProject.value = await projectsApi.update(id, data);
  }

  async function generate(kind: string, seed?: number, params?: Record<string, any>) {
    if (!currentProject.value) return;
    await projectsApi.generate(currentProject.value.id, kind, seed, params);
    await loadArrangement(currentProject.value.id);
  }

  return {
    currentProject,
    currentArrangement,
    loading,
    loadProject,
    loadArrangement,
    updateProject,
    generate,
  };
});
