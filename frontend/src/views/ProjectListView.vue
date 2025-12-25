<template>
  <div class="project-list-view">
    <div class="header">
      <h1>MIDINecromancer</h1>
      <button class="primary" @click="showDialog = true">New Project</button>
    </div>

    <!-- Create Project Dialog -->
    <div v-if="showDialog" class="dialog-overlay" @click.self="showDialog = false">
      <div class="dialog">
        <h2>Create New Project</h2>
        <form @submit.prevent="handleCreateProject">
          <div class="form-group">
            <label for="project-name">Project Name</label>
            <input
              id="project-name"
              v-model="newProjectName"
              type="text"
              placeholder="Enter project name"
              required
              autofocus
            />
          </div>
          <div class="dialog-actions">
            <button type="button" @click="showDialog = false">Cancel</button>
            <button type="submit" class="primary">Create</button>
          </div>
        </form>
      </div>
    </div>

    <div class="projects-grid">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="openProject(project.id)"
      >
        <h3>{{ project.name }}</h3>
        <p class="meta">
          {{ project.key_tonic }} {{ project.mode }} • {{ project.bpm }} BPM • {{ project.bars }} bars
        </p>
        <p class="date">{{ formatDate(project.created_at) }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { projectsApi } from "../api/projects";
import type { Project } from "../types";

const router = useRouter();
const projects = ref<Project[]>([]);
const loading = ref(false);
const showDialog = ref(false);
const newProjectName = ref("New Project");

onMounted(async () => {
  await loadProjects();
});

async function loadProjects() {
  loading.value = true;
  try {
    projects.value = await projectsApi.list();
  } finally {
    loading.value = false;
  }
}

function openProject(id: string) {
  router.push(`/projects/${id}`);
}

async function handleCreateProject() {
  const name = newProjectName.value.trim();
  if (!name) return;

  try {
    const project = await projectsApi.create({
      name,
      bpm: 120,
      time_signature_num: 4,
      time_signature_den: 4,
      bars: 8,
      key_tonic: "C",
      mode: "ionian",
      seed: Math.floor(Math.random() * 1000000),
    });
    showDialog.value = false;
    newProjectName.value = "New Project";
    await loadProjects(); // Refresh the list
    openProject(project.id);
  } catch (error) {
    console.error("Failed to create project:", error);
    alert("Failed to create project");
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString();
}
</script>

<style scoped>
.project-list-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.header h1 {
  font-size: 32px;
  color: #fff;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.project-card {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s;
}

.project-card:hover {
  transform: translateY(-2px);
  border-color: #0066cc;
}

.project-card h3 {
  margin-bottom: 8px;
  color: #fff;
}

.meta {
  color: #aaa;
  font-size: 14px;
  margin-bottom: 8px;
}

.date {
  color: #666;
  font-size: 12px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #aaa;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 24px;
  min-width: 400px;
  max-width: 90vw;
}

.dialog h2 {
  margin: 0 0 20px 0;
  color: #fff;
  font-size: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #aaa;
  font-size: 14px;
}

.form-group input {
  width: 100%;
  padding: 10px;
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #fff;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #0066cc;
}

.dialog-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.dialog-actions button {
  padding: 8px 16px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #2a2a2a;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

.dialog-actions button:hover {
  background: #333;
}

.dialog-actions button.primary {
  background: #0066cc;
  border-color: #0066cc;
}

.dialog-actions button.primary:hover {
  background: #0052a3;
}
</style>

