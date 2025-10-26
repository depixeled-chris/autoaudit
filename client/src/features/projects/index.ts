export { ProjectsPage } from './pages/ProjectsPage';
export { ProjectDetailPage } from './pages/ProjectDetailPage';
export { CreateProjectModal } from './components/CreateProjectModal';
export {
  projectsApi,
  useGetProjectsQuery,
  useGetProjectQuery,
  useCreateProjectMutation,
  useGetProjectSummaryQuery,
} from './projectsApi';
export type { Project, ProjectCreate, ProjectSummary } from './projectsApi';
