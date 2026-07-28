import React, { useState } from 'react';
import { Project, Template, ValidationResult } from '../index';

export interface ImplementationStudioProps {
  initialProjects: Project[];
  templates: Template[];
  onCreateProject: (name: string, templateId: string) => Promise<Project>;
  onValidate: (projectId: string) => Promise<ValidationResult>;
  onDeploy: (projectId: string) => Promise<void>;
}

export function ImplementationStudio({
  initialProjects,
  templates,
  onCreateProject,
  onValidate,
  onDeploy,
}: ImplementationStudioProps) {
  const [projects, setProjects] = useState<Project[]>(initialProjects);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [newProjectName, setNewProjectName] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);

  const handleCreate = async () => {
    if (!newProjectName || !selectedTemplate) return;
    const project = await onCreateProject(newProjectName, selectedTemplate);
    setProjects([...projects, project]);
    setNewProjectName('');
    setSelectedTemplate('');
  };

  const handleValidate = async (projectId: string) => {
    const result = await onValidate(projectId);
    setValidationResult(result);
  };

  const handleDeploy = async (projectId: string) => {
    await onDeploy(projectId);
    setProjects(projects.map((p) => (p.id === projectId ? { ...p, status: 'Deploying' } : p)));
  };

  return (
    <div className="implementation-studio" style={{ padding: '2rem' }}>
      <h1>Implementation Studio</h1>

      <div
        className="create-project"
        style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid #ccc' }}
      >
        <h2>Create Project</h2>
        <input
          type="text"
          placeholder="Project Name"
          value={newProjectName}
          onChange={(e) => setNewProjectName(e.target.value)}
        />
        <select value={selectedTemplate} onChange={(e) => setSelectedTemplate(e.target.value)}>
          <option value="">Select Template</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
        <button onClick={handleCreate}>Create Project</button>
      </div>

      <div style={{ display: 'flex', gap: '2rem' }}>
        <div className="project-list" style={{ flex: 1 }}>
          <h2>Project List</h2>
          <ul>
            {projects.map((project) => (
              <li
                key={project.id}
                style={{ padding: '1rem', border: '1px solid #eee', marginBottom: '1rem' }}
              >
                <h3>{project.name}</h3>
                <p>Status: {project.status}</p>
                <button
                  onClick={() => {
                    setSelectedProject(project);
                    setValidationResult(null);
                  }}
                >
                  View Details
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="project-details" style={{ flex: 1 }}>
          <h2>Project Details</h2>
          {selectedProject ? (
            <div style={{ padding: '1rem', border: '1px solid #eee' }}>
              <h3>
                {selectedProject.name} (ID: {selectedProject.id})
              </h3>
              <p>Status: {selectedProject.status}</p>
              <p>Template ID: {selectedProject.templateId}</p>

              <div
                className="validation-panel"
                style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f9f9f9' }}
              >
                <h4>Validation Panel</h4>
                <button onClick={() => handleValidate(selectedProject.id)}>Validate Project</button>
                {validationResult && (
                  <div style={{ marginTop: '1rem' }}>
                    <p>Status: {validationResult.valid ? 'Valid' : 'Invalid'}</p>
                    {!validationResult.valid && (
                      <ul>
                        {validationResult.errors.map((err, idx) => (
                          <li key={idx} style={{ color: 'red' }}>
                            {err}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>

              <div className="deployment-panel" style={{ marginTop: '1rem' }}>
                <button
                  onClick={() => handleDeploy(selectedProject.id)}
                  disabled={selectedProject.status === 'Deploying'}
                >
                  Deploy Button
                </button>
              </div>
            </div>
          ) : (
            <p>Select a project to view details.</p>
          )}
        </div>
      </div>
    </div>
  );
}
