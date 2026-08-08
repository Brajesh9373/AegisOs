import React, { useEffect, useState } from 'react';
import { Typography, Table, Tag, Button, Space, Tooltip, ConfigProvider, theme, Popconfirm, message, Tabs } from 'antd';
import { useNavigate } from 'react-router-dom';
import { CheckCircleOutlined, GlobalOutlined, FileTextOutlined, ControlOutlined, ExclamationCircleOutlined, DeleteOutlined, EditOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ApiClient } from '../api/client';

const { Title, Text } = Typography;

export function ProjectsList() {
  const navigate = useNavigate();
  
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingProjectId, setDeletingProjectId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('all');

  const parseDraft = (p: any): any | null => {
    try {
      const raw = p.description || '';
      const j = JSON.parse(raw);
      return j?.draft || null;
    } catch { return null; }
  };

  const loadProjects = () => {
    setLoading(true);
    ApiClient.get('/projects')
      .then((rows) => {
        setProjects((rows || []).map((project: any) => ({
          id: project.id,
          name: project.name,
          status: project.status || 'Planning',
          health: project.status === 'Draft' ? 'Draft' : project.status === 'Completed' ? 'Green' : project.status ? 'Yellow' : '',
          progress: project.progress != null ? `${project.progress}%` : '',
          owner: project.ownername || project.ownerName || project.owner || project.owneremail || project.ownerEmail || (project.ownerid ? 'Project Owner' : 'Current User'),
          lastActivity: project.updatedat || project.createdat || '',
          sustainability: null,
          rawStatus: project.status,
          draft: parseDraft(project),
          description: project.description,
        })));
      })
      .catch(ApiClient.handleError)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleDeleteProject = async (projectId: string) => {
    setDeletingProjectId(projectId);
    try {
      await ApiClient.delete(`/projects/${projectId}`);
      setProjects((prev) => prev.filter((project) => project.id !== projectId));
      message.success('Project deleted.');
    } catch (err) {
      ApiClient.handleError(err);
    } finally {
      setDeletingProjectId(null);
    }
  };

  const handleContinueDraft = (project: any) => {
    navigate(`/projects/new?draft=${project.id}`);
  };

  const handleEditDraft = (project: any) => {
    navigate(`/projects/new?draft=${project.id}&edit=1`);
  };

  const columns = [
    { 
      title: 'Project Name', 
      dataIndex: 'name', 
      key: 'name', 
      render: (t: string) => <Text style={{ fontWeight: 600, color: '#111827' }}>{t}</Text> 
    },
    { 
      title: 'Health', 
      dataIndex: 'health', 
      key: 'health', 
      render: (t: string) => (
        <Space>
          {t === 'Green' ? <CheckCircleOutlined style={{ color: '#16A34A' }} /> : <ExclamationCircleOutlined style={{ color: '#D97706' }} />}
          <Text style={{ color: t === 'Green' ? '#16A34A' : '#D97706', fontWeight: 500 }}>{t}</Text>
        </Space>
      )
    },
    { 
      title: 'Progress', 
      dataIndex: 'progress', 
      key: 'progress', 
      render: (t: string) => <Text style={{ color: '#2563EB', fontWeight: 600 }}>{t}</Text> 
    },
    { 
      title: 'Owner', 
      dataIndex: 'owner', 
      key: 'owner',
      render: (t: string) => <Text style={{ color: '#4B5563' }}>{t}</Text>
    },
    { 
      title: 'Last Activity', 
      dataIndex: 'lastActivity', 
      key: 'lastActivity',
      render: (t: string) => <Text style={{ color: '#6B7280' }}>{t}</Text>
    },
    { 
      title: 'Sustainability', 
      key: 'sustainability', 
      render: (_: any, r: any) => (
        <Tooltip 
          placement="bottom" 
          color="#FFFFFF"
          overlayInnerStyle={{ color: '#111827', border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' }}
          title={r.sustainability ? (
            <div style={{ padding: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, gap: 16 }}><Text style={{ color: '#4B5563' }}>Tokens Used:</Text> <Text strong>{r.sustainability.tokens}</Text></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}><Text style={{ color: '#4B5563' }}>Estimated AI Cost:</Text> <Text strong>{r.sustainability.cost}</Text></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}><Text style={{ color: '#4B5563' }}>CO₂:</Text> <Text strong>{r.sustainability.co2}</Text></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}><Text style={{ color: '#4B5563' }}>Water Usage:</Text> <Text strong>{r.sustainability.water}</Text></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}><Text style={{ color: '#4B5563' }}>Energy Usage:</Text> <Text strong>{r.sustainability.energy}</Text></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}><Text style={{ color: '#4B5563' }}>Trees Required:</Text> <Text strong>{r.sustainability.trees}</Text></div>
              
              <div style={{ borderTop: '1px solid #E5E7EB', paddingTop: 8, marginTop: 4 }}>
                <Text style={{ color: '#9CA3AF', fontSize: 11 }}>Last Updated: {r.sustainability.updated}</Text>
              </div>
            </div>
          ) : (
            <Text style={{ color: '#6B7280', fontSize: 12 }}>No usage telemetry recorded.</Text>
          )}
        >
          <GlobalOutlined style={{ color: '#16A34A', fontSize: 16, cursor: 'pointer' }} />
        </Tooltip>
      )
    },
    { 
      title: 'Actions', 
      key: 'actions', 
      render: (_: any, r: any) => r.rawStatus === 'Draft' ? (
        <Space size="small">
          <Button size="small" icon={<PlayCircleOutlined />} type="primary" onClick={() => handleContinueDraft(r)}>Continue</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEditDraft(r)}>Edit</Button>
          <Popconfirm title="Delete draft?" okText="Delete" okButtonProps={{ danger: true, loading: deletingProjectId === r.id }} onConfirm={() => handleDeleteProject(r.id)}>
            <Button danger size="small" icon={<DeleteOutlined />} loading={deletingProjectId === r.id}>Delete</Button>
          </Popconfirm>
        </Space>
      ) : (
        <Space size="small">
          <Button size="small" icon={<FileTextOutlined />} style={{ borderColor: '#E5E7EB', color: '#111827' }}>Report</Button>
          <Button type="primary" size="small" icon={<ControlOutlined />} onClick={() => navigate(`/projects/${r.id}/workspace`)} style={{ background: '#2563EB', fontWeight: 500 }}>Workspace</Button>
          <Popconfirm
            title="Delete project?"
            description="This will remove the project workspace, meetings, workers, documents, and board items."
            okText="Delete"
            okButtonProps={{ danger: true, loading: deletingProjectId === r.id }}
            cancelText="Cancel"
            onConfirm={() => handleDeleteProject(r.id)}
          >
            <Button danger size="small" icon={<DeleteOutlined />} loading={deletingProjectId === r.id}>Delete</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const drafts = projects.filter(p => p.rawStatus === 'Draft');
  const nonDrafts = projects.filter(p => p.rawStatus !== 'Draft');
  const filteredProjects = activeTab === 'drafts' ? drafts : activeTab === 'active' ? nonDrafts : projects;
  const draftCount = drafts.length;

  return (
    <PageContainer maxWidth={1400}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24, alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>Project Registry</Title>
        <Button type="primary" style={{ background: '#2563EB', fontWeight: 500 }} onClick={() => navigate('/projects/new')}>Create Project</Button>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab} style={{ marginBottom: 16 }} items={[
        { key: 'all', label: `All Projects (${projects.length})` },
        { key: 'drafts', label: `Drafts (${draftCount})` },
        { key: 'active', label: `Active (${nonDrafts.length})` },
      ]} />

      {activeTab === 'all' && drafts.length > 0 && (
        <Panel
          style={{ marginBottom: 16, borderColor: '#FDE68A', background: '#FFFBEB' }}
          bodyStyle={{ padding: 0 }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #FDE68A' }}>
            <Space><FileTextOutlined style={{ color: '#D97706' }} /><Text strong>Drafts</Text><Tag color="gold">{draftCount} unfinished</Tag></Space>
            <Button size="small" onClick={() => setActiveTab('drafts')}>View all drafts</Button>
          </div>
          <Table
            dataSource={drafts.slice(0, 3)}
            columns={columns}
            loading={loading}
            pagination={false}
            rowKey="id"
            size="small"
          />
          {draftCount > 3 && <div style={{ padding: '8px 16px', textAlign: 'center' }}><Button type="link" size="small" onClick={() => setActiveTab('drafts')}>Show all {draftCount} drafts →</Button></div>}
        </Panel>
      )}

      <Panel
        bodyStyle={{ padding: 0 }}
      >
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #E5E7EB', fontWeight: 600 }}>
          {activeTab === 'drafts' ? <Space><FileTextOutlined style={{ color: '#D97706' }} /><Text strong>Draft Projects</Text><Tag color="gold">{draftCount}</Tag></Space> : activeTab === 'active' ? <Text strong>Active Projects</Text> : <Text strong>All Projects</Text>}
        </div>
        <Table 
          dataSource={filteredProjects}
          columns={columns}
          loading={loading}
          pagination={false}
          rowKey="id" 
          style={{ width: '100%' }}
          rowClassName={(r: any) => r.rawStatus === 'Draft' ? 'row-draft' : ''}
        />
      </Panel>
    </PageContainer>
  );
}
