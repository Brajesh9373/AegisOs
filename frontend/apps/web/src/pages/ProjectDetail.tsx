/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-empty */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Tabs, Typography, Button, Space, Tag, Descriptions, Empty, Result, Divider, List, Spin, message } from 'antd';
import { ArrowLeftOutlined, EditOutlined, SettingOutlined, ThunderboltOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { ApiClient } from '../api/client';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';

const { Title, Text } = Typography;

export const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [generatingRecs, setGeneratingRecs] = useState(false);

  const [recPayload, setRecPayload] = useState<any>({
    recommendedEmployees: [],
    recommendedSkills: [],
    recommendedKnowledge: [],
    recommendedMemory: [],
    recommendedConnectors: [],
    recommendedWorkflow: [],
    assumptions: [],
    questions: [],
    risks: [],
  });

  const handleApproveAndGenerate = async () => {
    try {
      await ApiClient.post(`/projects/${id}/employees/generate`, { recommendations: recPayload });
      message.success('Recommendations Approved & Digital Employees Generated!');
      navigate('/employees');
    } catch (e: any) {
      ApiClient.handleError(e);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const data = await ApiClient.post(`/projects/${id}/analyze`, {});
      setAnalysis(data.analysis);
    } catch (e: any) {
      ApiClient.handleError(e);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateRecs = async () => {
    setGeneratingRecs(true);
    try {
      const data = await ApiClient.post(`/projects/${id}/recommend`, {});
      setRecPayload(data.payload);
      message.success('AI Recommendations generated successfully');
    } catch (e: any) {
      if (e.message && e.message.includes('Configure an AI Provider')) {
        message.warning('Configure an AI Provider to generate recommendations.');
      }
      ApiClient.handleError(e);
    } finally {
      setGeneratingRecs(false);
    }
  };

  const logRecAction = async (action: string, detail: string) => {
    try {
      await ApiClient.post(`/projects/${id}/recommendations/audit`, { action, detail });
    } catch (e: any) {}
  };

  const removeItem = (category: string, index: number) => {
    const updated = { ...recPayload };
    updated[category].splice(index, 1);
    setRecPayload(updated);
    logRecAction('Recommendation Modified', `Removed item from ${category}`);
  };

  const renderList = (
    category: string,
    items: any[],
    renderItem: (item: any, i: number) => React.ReactNode,
  ) => (
    <List
      size="small"
      dataSource={items}
      renderItem={(item: any, i: number) => (
        <List.Item
          actions={[
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => removeItem(category, i)}
            />,
          ]}
        >
          {renderItem(item, i)}
        </List.Item>
      )}
      locale={{
        emptyText: (
          <Button type="dashed" block icon={<PlusOutlined />}>
            Manually Add to {category}
          </Button>
        ),
      }}
    />
  );

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const data = await ApiClient.get(`/projects/${id}`);
        setProject(data);
      } catch (e) {
        ApiClient.handleError(e);
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchProject();
  }, [id]);

  if (loading) return <div style={{ padding: 48, textAlign: 'center' }}>Loading...</div>;
  if (!project) return <Result status="404" title="404" subTitle="Project not found" />;

  return (
    <PageContainer maxWidth={1400}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid #E5E7EB' }}>
        <Space align="center" size="middle">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/home')} style={{ color: '#111827', padding: 0 }} />
          <Title level={4} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>
            {project.name}
          </Title>
          <Tag style={{ background: '#EEF2FF', color: '#2563EB', border: 'none', fontWeight: 600 }}>{project.status}</Tag>
          <Tag style={{ background: '#FEF3C7', color: '#D97706', border: 'none', fontWeight: 600 }}>{project.priority}</Tag>
        </Space>
        <Space>
          <Button icon={<SettingOutlined />} style={{ fontWeight: 500 }}>Settings</Button>
          <Button type="primary" icon={<EditOutlined />} style={{ background: '#2563EB', fontWeight: 500 }}>
            Edit Project
          </Button>
        </Space>
      </div>

      <Panel bodyStyle={{ padding: 24 }}>
        <Tabs
          defaultActiveKey="1"
          items={[
            {
              key: '1',
              label: 'Overview',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <Descriptions column={2} bordered size="small">
                    <Descriptions.Item label="Business Goal" span={2}>
                      {project?.businessGoal}
                    </Descriptions.Item>
                    <Descriptions.Item label="Department">
                      {project?.department || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Created At">
                      {new Date(project?.createdAt).toLocaleString()}
                    </Descriptions.Item>
                  </Descriptions>

                  <Divider style={{ borderColor: '#E5E7EB' }} />
                  
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 20,
                    }}
                  >
                    <Title level={5} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>
                      Business Goal Analysis
                    </Title>
                    <Button
                      type="primary"
                      icon={<ThunderboltOutlined />}
                      onClick={handleAnalyze}
                      loading={analyzing}
                      disabled={!!analysis}
                      style={{ background: '#2563EB', fontWeight: 500 }}
                    >
                      {analysis ? 'Analyzed' : 'Run AI Analysis'}
                    </Button>
                  </div>

                  {analyzing && (
                    <div style={{ textAlign: 'center', padding: 40 }}>
                      <Spin tip="AI Reasoning Engine analyzing goal..." size="large" />
                    </div>
                  )}

                  {analysis && (
                    <div style={{ animation: 'fadeIn 0.5s' }}>
                      <Descriptions column={3} bordered size="small" style={{ marginBottom: 24 }}>
                        <Descriptions.Item label="Domain">
                          <Tag style={{ background: '#F3E8FF', color: '#7E22CE', border: 'none', fontWeight: 600 }}>{analysis.businessDomain}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Complexity">
                          <Tag style={{ background: analysis.estimatedComplexity === 'High' ? '#FEE2E2' : '#FEF3C7', color: analysis.estimatedComplexity === 'High' ? '#DC2626' : '#D97706', border: 'none', fontWeight: 600 }}>
                            {analysis.estimatedComplexity}
                          </Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Type">
                          <Tag style={{ background: '#F3F4F6', color: '#4B5563', border: 'none', fontWeight: 600 }}>{analysis.businessType}</Tag>
                        </Descriptions.Item>
                      </Descriptions>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                        <Card title="Required Intelligence" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                          <List
                            size="small"
                            header={<b>Skills</b>}
                            dataSource={analysis.requiredSkills}
                            renderItem={(item: any) => (
                              <List.Item>
                                <Tag style={{ background: '#EEF2FF', color: '#2563EB', border: 'none' }}>{item}</Tag>
                              </List.Item>
                            )}
                          />
                          <List
                            size="small"
                            header={<b>Knowledge</b>}
                            dataSource={analysis.requiredKnowledge}
                            renderItem={(item: any) => (
                              <List.Item>
                                <Tag style={{ background: '#E0F2FE', color: '#0369A1', border: 'none' }}>{item}</Tag>
                              </List.Item>
                            )}
                          />
                          <List
                            size="small"
                            header={<b>Connectors</b>}
                            dataSource={analysis.requiredConnectors}
                            renderItem={(item: any) => (
                              <List.Item>
                                <Tag style={{ background: '#EEF2FF', color: '#2563EB', border: 'none' }}>{item}</Tag>
                              </List.Item>
                            )}
                          />
                        </Card>

                        <Card title="Risk & Gaps" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                          <List
                            size="small"
                            header={<b>Potential Risks</b>}
                            dataSource={analysis.potentialRisks}
                            renderItem={(item: any) => (
                              <List.Item>
                                <Text type="danger">{item}</Text>
                              </List.Item>
                            )}
                          />
                          <List
                            size="small"
                            header={<b>Missing Information</b>}
                            dataSource={analysis.missingInformation}
                            renderItem={(item: any) => (
                              <List.Item>
                                <Text style={{ color: '#D97706' }}>{item}</Text>
                              </List.Item>
                            )}
                          />
                          <List
                            size="small"
                            header={<b>Questions for You</b>}
                            dataSource={analysis.questionsForUser}
                            renderItem={(item: any) => (
                              <List.Item>
                                <i>{item}</i>
                              </List.Item>
                            )}
                          />
                        </Card>
                      </div>
                    </div>
                  )}
                </div>
              ),
            },
            {
              key: '2',
              label: 'AI Recommendations',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <div
                    style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}
                  >
                    <div>
                      <Title level={5} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>
                        Proposed Architecture & Resources
                      </Title>
                      <Text type="secondary">
                        Review and approve AI-generated recommendations for this project.
                      </Text>
                    </div>
                    <Space>
                      <Button
                        type="primary"
                        onClick={handleGenerateRecs}
                        loading={generatingRecs}
                        icon={<ThunderboltOutlined />}
                        style={{ background: '#2563EB', fontWeight: 500 }}
                      >
                        Generate via AI Provider
                      </Button>
                    </Space>
                  </div>

                  <Tabs
                    type="card"
                    items={[
                      {
                        label: 'Digital Employees',
                        key: 'emp',
                        children: (
                          <div style={{ paddingTop: 12 }}>
                            {renderList(
                              'recommendedEmployees',
                              recPayload.recommendedEmployees,
                              (item) => (
                                <div style={{ width: '100%' }}>
                                  <b>{item.name}</b> ({item.role}){' '}
                                  <Tag style={{ background: '#EEF2FF', color: '#2563EB', border: 'none', fontWeight: 600 }}>{item.confidence}% Confidence</Tag>
                                  <br />
                                  <Text type="secondary">{item.purpose}</Text>
                                </div>
                              ),
                            )}
                          </div>
                        )
                      },
                      {
                        label: 'Skills & Knowledge',
                        key: 'skills',
                        children: (
                          <div
                            style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, paddingTop: 12 }}
                          >
                            <Card title="Skills (From Registry)" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                              {renderList(
                                'recommendedSkills',
                                recPayload.recommendedSkills,
                                (item) => (
                                  <Text>
                                    <b>{item.name}</b>: {item.reason}
                                  </Text>
                                ),
                              )}
                            </Card>
                            <Card title="Knowledge" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                              {renderList(
                                'recommendedKnowledge',
                                recPayload.recommendedKnowledge,
                                (item) => (
                                  <Text>
                                    <b>{item.name}</b>: {item.reason}
                                  </Text>
                                ),
                              )}
                            </Card>
                          </div>
                        ),
                      },
                      {
                        label: 'Memory & Connectors',
                        key: 'mem',
                        children: (
                          <div
                            style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, paddingTop: 12 }}
                          >
                            <Card title="Memory Systems" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                              {renderList(
                                'recommendedMemory',
                                recPayload.recommendedMemory,
                                (item) => (
                                  <Text>
                                    <Tag style={{ background: '#F3E8FF', color: '#7E22CE', border: 'none', fontWeight: 600 }}>{item.type}</Tag> <b>{item.name}</b>
                                  </Text>
                                ),
                              )}
                            </Card>
                            <Card title="Connectors" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                              {renderList(
                                'recommendedConnectors',
                                recPayload.recommendedConnectors,
                                (item) => (
                                  <Text>
                                    <b>{item.name}</b>
                                  </Text>
                                ),
                              )}
                            </Card>
                          </div>
                        ),
                      },
                      {
                        label: 'Workflow',
                        key: 'workflow',
                        children: (
                          <div style={{ paddingTop: 12 }}>
                            {renderList(
                              'recommendedWorkflow',
                              recPayload.recommendedWorkflow,
                              (item) => (
                                <Text>
                                  <b>{item.stage}</b>: {item.description}
                                </Text>
                              ),
                            )}
                          </div>
                        )
                      },
                      {
                        label: 'Risk & Analysis',
                        key: 'risk',
                        children: (
                          <div
                            style={{
                              display: 'grid',
                              gridTemplateColumns: '1fr 1fr 1fr',
                              gap: 24,
                              paddingTop: 12
                            }}
                          >
                            <Card title="Risks" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                              {renderList('risks', recPayload.risks, (item) => (
                                <Text type="danger">{item}</Text>
                              ))}
                            </Card>
                            <Card title="Questions" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                              {renderList('questions', recPayload.questions, (item) => (
                                <Text italic>{item}</Text>
                              ))}
                            </Card>
                            <Card title="Assumptions" size="small" style={{ borderRadius: 8, border: '1px solid #E5E7EB' }}>
                              {renderList('assumptions', recPayload.assumptions, (item) => (
                                <Text>{item}</Text>
                              ))}
                            </Card>
                          </div>
                        ),
                      },
                    ]}
                  />
                </div>
              ),
            },
          ]}
        />
      </Panel>
    </PageContainer>
  );
};
