import React, { useMemo, useState } from 'react';
import { Button, Checkbox, Drawer, Input, Select, Space, Tag, Typography, message } from 'antd';
import {
  ApiOutlined,
  CheckCircleOutlined,
  LinkOutlined,
  PlusOutlined,
  SearchOutlined,
  SettingOutlined,
  TeamOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { CATEGORIES, PROVIDER_FIELDS } from './CollaborationPanel';
import './ProjectConnectorsPanel.css';

const { Text } = Typography;

type ConnectorScope = 'universal' | 'project';
type ConnectorStatus = 'ready' | 'needs-setup';

interface ProjectConnector {
  name: string;
  logo: string;
  category: string;
  scope: ConnectorScope;
  status: ConnectorStatus;
  connectionName: string;
  details: Record<string, string>;
  workerIds: string[];
}

interface ProjectConnectorsPanelProps {
  requirementConnectors?: string[];
  workers?: any[];
}

const UNIVERSAL_CONNECTORS = new Set(['Jira', 'Asana', 'Slack', 'Teams', 'Meet', 'AWS', 'GCP', 'Azure']);
const DEFAULT_FIELDS = [
  { label: 'Connection name', key: 'connection_name', type: 'text', placeholder: 'Name this project connection' },
  { label: 'Workspace or endpoint', key: 'endpoint', type: 'text', placeholder: 'https://example.com/workspace' },
];

const connectorCatalog = CATEGORIES.flatMap((category) =>
  category.tools.map((tool) => ({
    ...tool,
    category: category.title,
    scope: (UNIVERSAL_CONNECTORS.has(tool.name) ? 'universal' : 'project') as ConnectorScope,
  })),
);

function initialConnectors(requirementConnectors: string[]): ProjectConnector[] {
  const normalized = requirementConnectors.map((item) => item.toLowerCase());
  return connectorCatalog
    .filter((tool) => normalized.some((item) => item.includes(tool.name.toLowerCase())))
    .map((tool) => ({
      ...tool,
      status: tool.scope === 'universal' ? 'ready' : 'needs-setup',
      connectionName: tool.scope === 'universal' ? `Organization ${tool.name}` : '',
      details: {},
      workerIds: [],
    }));
}

export const ProjectConnectorsPanel: React.FC<ProjectConnectorsPanelProps> = ({
  requirementConnectors = [],
  workers = [],
}) => {
  const [connectors, setConnectors] = useState<ProjectConnector[]>(() => initialConnectors(requirementConnectors));
  const [search, setSearch] = useState('');
  const [scopeFilter, setScopeFilter] = useState<'all' | ConnectorScope>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | ConnectorStatus>('all');
  const [addDrawerOpen, setAddDrawerOpen] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState('');
  const [configuring, setConfiguring] = useState<(typeof connectorCatalog)[number] | null>(null);
  const [configDraft, setConfigDraft] = useState<Record<string, string>>({});
  const [accessConnector, setAccessConnector] = useState<string | null>(null);
  const [accessDraft, setAccessDraft] = useState<string[]>([]);
  const requirementKey = requirementConnectors.join('|');

  React.useEffect(() => {
    if (!requirementKey) return;
    setConnectors((current) => current.length > 0 ? current : initialConnectors(requirementConnectors));
  }, [requirementKey]);

  const visibleConnectors = useMemo(() => {
    const query = search.trim().toLowerCase();
    return connectors.filter((connector) => (
      (!query || connector.name.toLowerCase().includes(query) || connector.category.toLowerCase().includes(query))
      && (scopeFilter === 'all' || connector.scope === scopeFilter)
      && (statusFilter === 'all' || connector.status === statusFilter)
    ));
  }, [connectors, scopeFilter, search, statusFilter]);

  const availableCatalog = useMemo(() => {
    const existing = new Set(connectors.map((connector) => connector.name));
    const query = catalogSearch.trim().toLowerCase();
    return connectorCatalog.filter((connector) => (
      !existing.has(connector.name)
      && (!query || connector.name.toLowerCase().includes(query) || connector.category.toLowerCase().includes(query))
    ));
  }, [catalogSearch, connectors]);

  const addUniversalConnector = (tool: (typeof connectorCatalog)[number]) => {
    setConnectors((current) => [...current, {
      ...tool,
      status: 'ready',
      connectionName: `Organization ${tool.name}`,
      details: {},
      workerIds: [],
    }]);
    message.success(`${tool.name} enabled for this project`);
  };

  const openConfiguration = (tool: (typeof connectorCatalog)[number], existing?: ProjectConnector) => {
    setConfiguring(tool);
    setConfigDraft(existing?.details || {});
    setAddDrawerOpen(false);
  };

  const connectProjectConnector = () => {
    if (!configuring) return;
    setConnectors((current) => {
      const existing = current.find((connector) => connector.name === configuring.name);
      const next: ProjectConnector = {
        ...configuring,
        status: 'ready',
        connectionName: configDraft.connection_name || `${configuring.name} connection`,
        details: configDraft,
        workerIds: existing?.workerIds || [],
      };
      return existing
        ? current.map((connector) => connector.name === configuring.name ? next : connector)
        : [...current, next];
    });
    message.success(`${configuring.name} connected`);
    setConfiguring(null);
    setConfigDraft({});
  };

  const openWorkerAccess = (connector: ProjectConnector) => {
    setAccessConnector(connector.name);
    setAccessDraft(connector.workerIds);
  };

  const saveWorkerAccess = () => {
    if (!accessConnector) return;
    setConnectors((current) => current.map((connector) => (
      connector.name === accessConnector ? { ...connector, workerIds: accessDraft } : connector
    )));
    message.success('Worker access updated');
    setAccessConnector(null);
  };

  const removeConnector = (connectorName: string) => {
    setConnectors((current) => current.filter((connector) => connector.name !== connectorName));
    message.success(`${connectorName} removed from this project`);
  };

  const configurationFields = configuring ? (PROVIDER_FIELDS[configuring.name] || DEFAULT_FIELDS) : DEFAULT_FIELDS;

  return (
    <div className="project-connectors">
      <div className="project-connectors__heading">
        <div>
          <span className="project-connectors__eyebrow">Project integrations</span>
          <h2>Project connectors</h2>
          <p>Manage shared services, private project connections, and worker access for this workspace.</p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddDrawerOpen(true)}>
          Add connector
        </Button>
      </div>

      <div className="project-connectors__toolbar">
        <Input
          prefix={<SearchOutlined />}
          placeholder="Search project connectors"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          allowClear
        />
        <Select
          aria-label="Filter by connector scope"
          value={scopeFilter}
          onChange={setScopeFilter}
          options={[
            { value: 'all', label: 'All scopes' },
            { value: 'universal', label: 'Universal' },
            { value: 'project', label: 'Project' },
          ]}
        />
        <Select
          aria-label="Filter by connector status"
          value={statusFilter}
          onChange={setStatusFilter}
          options={[
            { value: 'all', label: 'All statuses' },
            { value: 'ready', label: 'Ready' },
            { value: 'needs-setup', label: 'Needs setup' },
          ]}
        />
      </div>

      {visibleConnectors.length > 0 ? (
        <div className="project-connectors__groups">
          {(['universal', 'project'] as ConnectorScope[]).map((scope) => {
            const group = visibleConnectors.filter((connector) => connector.scope === scope);
            if (group.length === 0) return null;
            return (
              <section className="project-connectors__group" key={scope}>
                <div className="project-connectors__group-heading">
                  <div>
                    <h3>{scope === 'universal' ? 'Universal connectors' : 'Project connectors'}</h3>
                    <p>
                      {scope === 'universal'
                        ? 'Managed in Administration and enabled for this project.'
                        : 'Configured specifically for this project and unavailable elsewhere.'}
                    </p>
                  </div>
                  <Tag>{group.length}</Tag>
                </div>

                <div className="project-connectors__list">
                  {group.map((connector) => (
                    <article className={`project-connector-row project-connector-row--${connector.status}`} key={connector.name}>
                      <div className="project-connector-row__logo">
                        <img src={connector.logo} alt="" loading="lazy" />
                      </div>
                      <div className="project-connector-row__main">
                        <div className="project-connector-row__title">
                          <div>
                            <strong>{connector.name}</strong>
                            <span>{connector.category}</span>
                          </div>
                          <Tag color={connector.scope === 'universal' ? 'cyan' : 'gold'}>
                            {connector.scope}
                          </Tag>
                          <span className={`project-connector-row__status project-connector-row__status--${connector.status}`}>
                            {connector.status === 'ready' ? <CheckCircleOutlined /> : <WarningOutlined />}
                            {connector.status === 'ready' ? 'Ready' : 'Configuration required'}
                          </span>
                        </div>

                        {connector.status === 'ready' ? (
                          <div className="project-connector-row__details">
                            <div><span>Connection</span><strong>{connector.connectionName}</strong></div>
                            <div>
                              <span>Worker access</span>
                              <strong>{connector.workerIds.length > 0 ? `${connector.workerIds.length} workers` : 'No workers assigned'}</strong>
                            </div>
                          </div>
                        ) : (
                          <p className="project-connector-row__warning">
                            Selected during project discovery, but the project connection still needs to be completed.
                          </p>
                        )}

                        <div className="project-connector-row__actions">
                          {connector.status === 'ready' ? (
                            <>
                              <Button icon={<TeamOutlined />} onClick={() => openWorkerAccess(connector)}>Manage access</Button>
                              {connector.scope === 'project' ? (
                                <Button
                                  icon={<SettingOutlined />}
                                  onClick={() => openConfiguration(
                                    connectorCatalog.find((tool) => tool.name === connector.name)!,
                                    connector,
                                  )}
                                >
                                  Edit connection
                                </Button>
                              ) : (
                                <Button icon={<LinkOutlined />}>View connection</Button>
                              )}
                              <Button type="text" danger onClick={() => removeConnector(connector.name)}>Remove</Button>
                            </>
                          ) : (
                            <Button
                              type="primary"
                              icon={<SettingOutlined />}
                              onClick={() => openConfiguration(
                                connectorCatalog.find((tool) => tool.name === connector.name)!,
                                connector,
                              )}
                            >
                              Complete configuration
                            </Button>
                          )}
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      ) : (
        <div className="project-connectors__empty">
          <ApiOutlined />
          <strong>{connectors.length === 0 ? 'No project connectors yet' : 'No connectors match these filters'}</strong>
          <span>{connectors.length === 0 ? 'Add a connector when this project needs access to an external system.' : 'Try changing the search, scope, or status.'}</span>
          {connectors.length === 0 ? <Button type="primary" onClick={() => setAddDrawerOpen(true)}>Add connector</Button> : null}
        </div>
      )}

      <Drawer
        title="Add a project connector"
        width={520}
        open={addDrawerOpen}
        onClose={() => setAddDrawerOpen(false)}
      >
        <Input
          prefix={<SearchOutlined />}
          placeholder="Search connector catalog"
          value={catalogSearch}
          onChange={(event) => setCatalogSearch(event.target.value)}
          allowClear
          style={{ marginBottom: 16 }}
        />
        <div className="project-connector-catalog">
          {availableCatalog.map((tool) => (
            <div className="project-connector-catalog__item" key={tool.name}>
              <div className="project-connector-row__logo"><img src={tool.logo} alt="" /></div>
              <div>
                <strong>{tool.name}</strong>
                <span>{tool.category}</span>
              </div>
              <Tag color={tool.scope === 'universal' ? 'cyan' : 'gold'}>{tool.scope}</Tag>
              <Button
                type={tool.scope === 'universal' ? 'default' : 'primary'}
                onClick={() => tool.scope === 'universal' ? addUniversalConnector(tool) : openConfiguration(tool)}
              >
                {tool.scope === 'universal' ? 'Enable' : 'Configure'}
              </Button>
            </div>
          ))}
          {availableCatalog.length === 0 ? <Text type="secondary">No additional connectors found.</Text> : null}
        </div>
      </Drawer>

      <Drawer
        title={configuring ? `Configure ${configuring.name}` : 'Configure connector'}
        width={460}
        open={!!configuring}
        onClose={() => setConfiguring(null)}
        extra={<Tag color="gold">Project connector</Tag>}
      >
        <div className="project-connector-form">
          <div className="project-connector-form__notice">
            <ApiOutlined />
            <span>This frontend-only configuration is kept in memory and is not persisted yet.</span>
          </div>
          {configurationFields.map((field) => (
            <label key={field.key}>
              <span>{field.label}</span>
              {field.type === 'password' ? (
                <Input.Password
                  placeholder={field.placeholder}
                  value={configDraft[field.key] || ''}
                  onChange={(event) => setConfigDraft((current) => ({ ...current, [field.key]: event.target.value }))}
                />
              ) : (
                <Input
                  placeholder={field.placeholder}
                  value={configDraft[field.key] || ''}
                  onChange={(event) => setConfigDraft((current) => ({ ...current, [field.key]: event.target.value }))}
                />
              )}
            </label>
          ))}
          <Space style={{ justifyContent: 'flex-end', width: '100%' }}>
            <Button onClick={() => setConfiguring(null)}>Cancel</Button>
            <Button type="primary" icon={<LinkOutlined />} onClick={connectProjectConnector}>Connect</Button>
          </Space>
        </div>
      </Drawer>

      <Drawer
        title={`${accessConnector || 'Connector'} worker access`}
        width={440}
        open={!!accessConnector}
        onClose={() => setAccessConnector(null)}
        extra={<Tag color="blue">{accessDraft.length} selected</Tag>}
      >
        <p className="project-connectors__access-copy">Choose which project workers may use this connector.</p>
        <Checkbox.Group
          className="project-connectors__worker-list"
          value={accessDraft}
          onChange={(values) => setAccessDraft(values as string[])}
        >
          {workers.map((worker) => (
            <Checkbox value={worker.id} key={worker.id}>
              <span>
                <strong>{worker.name}</strong>
                <small>{worker.role || worker.type || 'Project worker'} · {worker.status || 'Waiting'}</small>
              </span>
            </Checkbox>
          ))}
        </Checkbox.Group>
        {workers.length === 0 ? <Text type="secondary">No project workers are available yet.</Text> : null}
        <div className="project-connectors__access-actions">
          <Button onClick={() => setAccessConnector(null)}>Cancel</Button>
          <Button type="primary" onClick={saveWorkerAccess}>Save access</Button>
        </div>
      </Drawer>
    </div>
  );
};
