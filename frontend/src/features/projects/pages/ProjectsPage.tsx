import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type ChangeEvent, type SyntheticEvent } from "react";
import { Link } from "react-router-dom";

import { useActiveOrganization } from "../../../core/organization/useActiveOrganization";
import { container } from "../../../core/di/container";

export function ProjectsPage() {
  const queryClient = useQueryClient();

  const [name, setName] = useState("Demo Project");
  const [description, setDescription] = useState(
    "Project created from the app shell.",
  );

  const organizationsQuery = useQuery({
    queryKey: ["organizations"],
    queryFn: () => container.projectService.listOrganizations(),
  });

  const organizations = organizationsQuery.data ?? [];
  const { activeOrganizationId, setActiveOrganization } =
    useActiveOrganization(organizations);

  const projectsQuery = useQuery({
    queryKey: ["projects", activeOrganizationId],
    queryFn: () =>
      container.projectService.listProjects(activeOrganizationId),
    enabled: Boolean(activeOrganizationId),
  });

  const projects = projectsQuery.data ?? [];

  const createProjectMutation = useMutation({
    mutationFn: () =>
      container.projectService.createProject({
        organization_id: activeOrganizationId,
        name,
        description: description.trim() ? description : null,
      }),
    onSuccess: async () => {
      setName("");
      setDescription("");

      await queryClient.invalidateQueries({
        queryKey: ["projects", activeOrganizationId],
      });
    },
  });

  const deleteProjectMutation = useMutation({
    mutationFn: (projectId: string) =>
      container.projectService.deleteProject(projectId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["projects", activeOrganizationId],
      });
    },
  });

  function handleOrganizationChange(event: ChangeEvent<HTMLSelectElement>) {
    setActiveOrganization(event.target.value);
  }

  async function handleCreateProject(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!activeOrganizationId) {
      return;
    }

    await createProjectMutation.mutateAsync();
  }

  async function handleDeleteProject(projectId: string) {
    const confirmed = window.confirm("Delete this project?");

    if (!confirmed) {
      return;
    }

    await deleteProjectMutation.mutateAsync(projectId);
  }

  const errorMessage =
    organizationsQuery.isError || projectsQuery.isError
      ? "Could not load workspace data."
      : createProjectMutation.isError
        ? "Could not create project."
        : deleteProjectMutation.isError
          ? "Could not delete project."
          : null;

  const isLoading =
    organizationsQuery.isLoading ||
    projectsQuery.isLoading ||
    createProjectMutation.isPending ||
    deleteProjectMutation.isPending;

  return (
    <div>
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="mt-1 text-sm text-slate-400">
            Manage organization projects and open their boards.
          </p>
        </div>

        <select
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
          value={activeOrganizationId}
          onChange={handleOrganizationChange}
          disabled={organizations.length === 0 || organizationsQuery.isLoading}
        >
          {organizations.length === 0 ? (
            <option value="">No organization found</option>
          ) : null}

          {organizations.map((organization) => (
            <option key={organization.id} value={organization.id}>
              {organization.name}
            </option>
          ))}
        </select>
      </div>

      {errorMessage ? (
        <div className="mt-4 rounded-lg border border-red-900 bg-red-950/40 p-3 text-sm text-red-300">
          {errorMessage}
        </div>
      ) : null}

      <form
        onSubmit={(event) => void handleCreateProject(event)}
        className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-5"
      >
        <h2 className="text-lg font-semibold">Create project</h2>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="projectName" className="text-sm text-slate-300">
              Name
            </label>

            <input
              id="projectName"
              data-testid="project-name-input"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              required
              minLength={2}
            />
          </div>

          <div>
            <label
              htmlFor="projectDescription"
              className="text-sm text-slate-300"
            >
              Description
            </label>

            <input
              id="projectDescription"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          data-testid="project-submit"
          disabled={
            createProjectMutation.isPending ||
            !activeOrganizationId ||
            !name.trim()
          }
          className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {createProjectMutation.isPending ? "Saving..." : "Create project"}
        </button>
      </form>

      <section className="mt-6">
        <h2 className="text-lg font-semibold">Project list</h2>

        {isLoading ? (
          <p className="mt-4 text-sm text-slate-400">Loading...</p>
        ) : null}

        {!isLoading && projects.length === 0 ? (
          <div className="mt-4 rounded-2xl border border-dashed border-slate-700 p-8 text-center">
            <p className="text-slate-300">No projects yet.</p>
            <p className="mt-1 text-sm text-slate-500">
              Create your first project to start adding boards.
            </p>
          </div>
        ) : null}

        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => (
            <article
              key={project.id}
              data-testid="project-item"
              data-project-id={project.id}
              className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
            >
              <h3 className="font-semibold">{project.name}</h3>

              <p className="mt-2 min-h-10 text-sm text-slate-400">
                {project.description || "No description"}
              </p>

              <div className="mt-4 flex items-center gap-2">
                <Link
                  data-testid="open-boards-link"
                  to={`/projects/${project.id}/boards`}
                  className="rounded-lg bg-blue-600 px-3 py-2 text-sm hover:bg-blue-500"
                >
                  Open boards
                </Link>

                <button
                  type="button"
                  onClick={() => void handleDeleteProject(project.id)}
                  disabled={deleteProjectMutation.isPending}
                  className="rounded-lg bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}