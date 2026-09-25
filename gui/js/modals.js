/**
 * Shared modal component definitions for ThesisForge GUI.
 * Extracted from index.html to allow a strict Content-Security-Policy
 * that omits 'unsafe-inline' from script-src.
 */

/**
 * Alpine.js component: Create Project modal form.
 * Mounted via x-data="createProjectModal()" in index.html.
 */
function createProjectModal() {
  return {
    form: {
      title: "",
      academic_level: "pregrado",
      area_of_study: "",
      topic: "",
      language: "es",
    },
    isSubmitting: false,
    async submitCreate() {
      if (!this.form.title.trim()) return;
      this.isSubmitting = true;
      try {
        const project = await Alpine.store("app").api("/api/projects", {
          method: "POST",
          body: JSON.stringify(this.form),
        });
        Alpine.store("app").toast(
          "success",
          "Proyecto creado",
          `El proyecto "${project.title}" ha sido inicializado.`
        );
        await Alpine.store("app").fetchProjects();
        await Alpine.store("app").selectProject(project.id);
        Alpine.store("app").showCreateModal = false;
        Alpine.store("app").activeTab = "advisor";
        this.form = {
          title: "",
          academic_level: "pregrado",
          area_of_study: "",
          topic: "",
          language: "es",
        };
      } catch (_err) {
        // Toast already handled by api()
      } finally {
        this.isSubmitting = false;
      }
    },
  };
}
