import { createRouter, createWebHistory } from "vue-router";
import ComposerView from "./views/ComposerView.vue";
import ProjectListView from "./views/ProjectListView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/projects",
      name: "projects",
      component: ProjectListView,
    },
    {
      path: "/projects/:id",
      name: "composer",
      component: ComposerView,
    },
  ],
});

export default router;
