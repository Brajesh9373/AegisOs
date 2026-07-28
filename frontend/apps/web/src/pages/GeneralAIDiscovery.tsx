import React, { useState } from 'react';
import { Typography, Row, Col, Button, Space, Tag, Input, Tabs, List, Select, Card, message, Divider } from 'antd';
import { ArrowLeftOutlined, RobotOutlined, WarningOutlined, FileTextOutlined, QuestionCircleOutlined, ThunderboltOutlined, InfoCircleOutlined, PaperClipOutlined, BookOutlined, MessageOutlined, CheckCircleOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ActionToolbar } from '../components/ui/ActionToolbar';
import { LifecycleStepper } from '../components/ui/LifecycleStepper';
import { OpportunitySidebar } from '../components/ui/OpportunitySidebar';
import { ActivityCenter } from '../components/ui/ActivityCenter';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const Form = ({ children, layout, onFinish }: any) => {
  return <form onSubmit={(e) => { e.preventDefault(); onFinish(); }}>{children}</form>;
};
Form.Item = ({ children, label }: any) => (
  <div style={{ marginBottom: 12 }}>
    <label style={{ fontSize: 12, fontWeight: 500, color: '#374151', display: 'block', marginBottom: 6 }}>{label}</label>
    {children}
  </div>
);

interface DiscussionQuestion {
  id: string;
  category: string;
  question: string;
  priority: 'High' | 'Medium' | 'Low';
  reason: string;
  suggestedAnswer: string;
  status: 'Pending' | 'Discussed' | 'Confirmed' | 'Rejected';
  customerResponse: string;
}

export function GeneralAIDiscovery() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('summary');

  // Stateful assumptions
  const [assumptions, setAssumptions] = useState<string[]>([
    "Target environment will be deployed on AWS RDS Aurora PostgreSQL Engine version 15.x.",
    "The client will supply full schema-level access and representative anonymized data subsets for dev testing.",
    "Network connectivity between source and target will be established via AWS DirectConnect."
  ]);

  // Stateful alignment questions
  const [questions, setQuestions] = useState<DiscussionQuestion[]>([
    {
      id: 'q1',
      category: 'Technical',
      question: 'Are there any proprietary Oracle data types (e.g. Spatial, XMLType) in use in VNU schemas?',
      priority: 'High',
      reason: 'Requires special conversion schemas if native PG matches do not exist.',
      suggestedAnswer: 'Convert Spatial to PostGIS extensions; parse XML to native PG xml schema.',
      status: 'Pending',
      customerResponse: ''
    },
    {
      id: 'q2',
      category: 'Infrastructure',
      question: 'What is the average and peak transactions-per-second (TPS) on VNU source databases?',
      priority: 'High',
      reason: 'Crucial for sizing Kafka Connect cluster memory limits.',
      suggestedAnswer: 'Deploy staging cluster with 3 nodes (m5.xlarge) to sustain peak 3,500 TPS.',
      status: 'Pending',
      customerResponse: ''
    },
    {
      id: 'q3',
      category: 'Licensing',
      question: 'Will licensing costs of RDS Aurora be billed directly to the VNU AWS account?',
      priority: 'Medium',
      reason: 'Affects final overall billing calculations for migration deliverables.',
      suggestedAnswer: 'Setup AWS billing integration to report cluster costs directly to Client.',
      status: 'Pending',
      customerResponse: ''
    },
    {
      id: 'q4',
      category: 'Security & Compliance',
      question: 'Does the source database store HIPAA/PCI-DSS regulated data fields?',
      priority: 'High',
      reason: 'Determines whether Debezium CDC logs must enforce field-level encryption.',
      suggestedAnswer: 'Enable data masking on SSN and payment columns inside Kafka Connect config.',
      status: 'Pending',
      customerResponse: ''
    },
    {
      id: 'q5',
      category: 'Integration',
      question: 'Do downstream consumer analytics topics require schema synchronization back to Oracle?',
      priority: 'Medium',
      reason: 'If yes, must configure reverse CDC pipeline (active-active target/source sync).',
      suggestedAnswer: 'Implement unidirectional sync initially; evaluate active-active rollback in Phase 3.',
      status: 'Pending',
      customerResponse: ''
    }
  ]);

  const [newFollowUp, setNewFollowUp] = useState('');
  const [newCategory, setNewCategory] = useState('Technical');
  const [newPriority, setNewPriority] = useState<'High' | 'Medium' | 'Low'>('Medium');

  const handleUpdateStatus = (qid: string, val: any) => {
    setQuestions(prev => prev.map(q => q.id === qid ? { ...q, status: val } : q));
    message.success('AI Memory & RFQ generator context synced.');
  };

  const handleUpdateResponse = (qid: string, val: string) => {
    setQuestions(prev => prev.map(q => q.id === qid ? { ...q, customerResponse: val } : q));
  };

  const handleSaveResponse = (qid: string) => {
    const q = questions.find(item => item.id === qid);
    if (!q) return;
    message.success('Knowledge Base refined. Timeline event logged for response update.');
  };

  const handleAddFollowUp = () => {
    if (!newFollowUp.trim()) return;
    const newQ: DiscussionQuestion = {
      id: `q-${Date.now()}`,
      category: newCategory,
      question: newFollowUp,
      priority: newPriority,
      reason: 'Added as follow-up alignment point by user.',
      suggestedAnswer: 'To be determined during customer session.',
      status: 'Pending',
      customerResponse: ''
    };
    setQuestions(prev => [...prev, newQ]);
    setNewFollowUp('');
    message.success('Follow-up question registered and timeline sync updated.');
  };

  const TabContentWrapper = ({ children }: { children: React.ReactNode }) => (
    <div style={{ paddingTop: 16 }}>{children}</div>
  );

  const EditableSection = ({ title, defaultText, icon }: { title: string, defaultText: string, icon?: React.ReactNode }) => (
    <div style={{ marginBottom: 24 }}>
      <Space style={{ marginBottom: 8 }}>
        {icon || <InfoCircleOutlined style={{ color: '#2563EB' }} />}
        <Text style={{ fontSize: 14, fontWeight: 600, color: '#111827' }}>{title}</Text>
      </Space>
      <TextArea
        defaultValue={defaultText}
        autoSize={{ minRows: 4, maxRows: 12 }}
        style={{ background: '#FFFFFF', color: '#374151', border: '1px solid #E5E7EB', borderRadius: 6, fontSize: 13 }}
      />
    </div>
  );

  const tabItems = [
    {
      key: 'summary',
      label: <span style={{ fontWeight: 500 }}><FileTextOutlined /> Summary</span>,
      children: (
        <TabContentWrapper>
          <EditableSection
            title="Executive Summary"
            defaultText="The client seeks a complete database modernization from Oracle 19c to PostgreSQL to eliminate legacy licensing costs, improve horizontally scalable throughput, and establish a cloud-native CDC integration pipeline."
          />
          <EditableSection
            title="Scope Understanding"
            defaultText="- Schema Migration: Modernization of 4 transactional databases (totaling 12TB).\n- Stored Procedures: Rewrite of heavily nested Oracle PL/SQL business rules to PostgreSQL pgSQL.\n- CDC Pipeline: Provision of Debezium Kafka Connector for real-time analytics stream."
          />
        </TabContentWrapper>
      )
    },
    {
      key: 'discussion',
      label: <span style={{ fontWeight: 600, color: '#2563EB' }}><MessageOutlined /> Client Discussion & Alignment</span>,
      children: (
        <TabContentWrapper>
          <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 8, padding: 16, marginBottom: 24 }}>
            <Text strong style={{ color: '#1E3A8A', fontSize: 13, display: 'block', marginBottom: 4 }}>🧠 AI Refinement Mode Enabled</Text>
            <Text style={{ color: '#1E40AF', fontSize: 12 }}>
              Updating statuses, adding meeting notes, or resolving questions automatically rebuilds the Knowledge Base context and adjusts the generated RFQ draft metrics in real time.
            </Text>
          </div>

          <List
            dataSource={questions}
            renderItem={(q) => (
              <Card
                size="small"
                style={{ marginBottom: 16, border: '1px solid #E5E7EB', borderRadius: 8 }}
                bodyStyle={{ padding: 16 }}
              >
                <Row gutter={16} align="middle" style={{ marginBottom: 12 }}>
                  <Col span={16}>
                    <Space wrap>
                      <Tag color={q.priority === 'High' ? 'red' : 'orange'}>{q.priority} Priority</Tag>
                      <Tag color="blue">{q.category}</Tag>
                    </Space>
                    <div style={{ marginTop: 8 }}>
                      <Text strong style={{ fontSize: 14, color: '#111827' }}>{q.question}</Text>
                    </div>
                  </Col>
                  <Col span={8} style={{ textAlign: 'right' }}>
                    <Space>
                      <Text style={{ fontSize: 12, color: '#6B7280' }}>Status:</Text>
                      <Select
                        value={q.status}
                        onChange={(val) => handleUpdateStatus(q.id, val)}
                        style={{ width: 120 }}
                        options={[
                          { value: 'Pending', label: 'Pending' },
                          { value: 'Discussed', label: 'Discussed' },
                          { value: 'Confirmed', label: 'Confirmed' },
                          { value: 'Rejected', label: 'Rejected' }
                        ]}
                      />
                    </Space>
                  </Col>
                </Row>

                <div style={{ background: '#F8FAFC', padding: 12, borderRadius: 6, marginBottom: 12, fontSize: 12 }}>
                  <div style={{ marginBottom: 4 }}><Text type="secondary"><b>Reason:</b> {q.reason}</Text></div>
                  <div><Text type="secondary"><b>Suggested Answer:</b> {q.suggestedAnswer}</Text></div>
                </div>

                <div style={{ marginTop: 8 }}>
                  <Text strong style={{ fontSize: 12, color: '#111827', display: 'block', marginBottom: 6 }}>Customer Response & Meeting Notes:</Text>
                  <TextArea
                    placeholder="Enter notes from discovery session or specific customer inputs..."
                    value={q.customerResponse}
                    onChange={(e) => handleUpdateResponse(q.id, e.target.value)}
                    autoSize={{ minRows: 2, maxRows: 6 }}
                    style={{ marginBottom: 8, fontSize: 13, background: '#FFFFFF', color: '#111827' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Button
                      size="small"
                      type="primary"
                      onClick={() => handleSaveResponse(q.id)}
                      style={{ background: '#2563EB', fontSize: 11 }}
                    >
                      Save Notes & Sync AI
                    </Button>
                    {q.status !== 'Confirmed' && (
                      <Button
                        size="small"
                        onClick={() => handleUpdateStatus(q.id, 'Confirmed')}
                        style={{ fontSize: 11 }}
                      >
                        Mark Confirmed
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            )}
          />

          <Divider />

          <Card title="Add Follow-up / New Alignment Question" size="small" style={{ background: '#F9FAFB' }}>
            <Form layout="vertical" onFinish={handleAddFollowUp}>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="Category">
                    <Select value={newCategory} onChange={setNewCategory} options={[
                      { value: 'Technical', label: 'Technical' },
                      { value: 'Licensing', label: 'Licensing' },
                      { value: 'Security & Compliance', label: 'Security & Compliance' },
                      { value: 'Infrastructure', label: 'Infrastructure' },
                      { value: 'Integration', label: 'Integration' },
                      { value: 'Commercial', label: 'Commercial' }
                    ]} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Priority">
                    <Select value={newPriority} onChange={(val: any) => setNewPriority(val)} options={[
                      { value: 'High', label: 'High' },
                      { value: 'Medium', label: 'Medium' },
                      { value: 'Low', label: 'Low' }
                    ]} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item label="Alignment Question">
                <TextArea
                  rows={2}
                  value={newFollowUp}
                  onChange={(e) => setNewFollowUp(e.target.value)}
                  placeholder="Enter the specific item or clarification requested..."
                />
              </Form.Item>
              <Button type="primary" onClick={handleAddFollowUp} style={{ background: '#2563EB' }}>
                Register Alignment Question
              </Button>
            </Form>
          </Card>
        </TabContentWrapper>
      )
    },
    {
      key: 'assumptions',
      label: <span style={{ fontWeight: 500 }}><InfoCircleOutlined /> Assumptions</span>,
      children: (
        <TabContentWrapper>
          <Text style={{ display: 'block', marginBottom: 12, color: '#6B7280' }}>Edit AI-generated assumptions to refine technical boundaries:</Text>
          {assumptions.map((ass, index) => (
            <div key={index} style={{ marginBottom: 16 }}>
              <TextArea
                value={ass}
                onChange={(e) => {
                  const val = e.target.value;
                  setAssumptions(prev => prev.map((item, i) => i === index ? val : item));
                }}
                autoSize={{ minRows: 2 }}
                style={{ fontSize: 13, background: '#FFFFFF', color: '#111827' }}
              />
            </div>
          ))}
          <Button
            type="primary"
            onClick={() => message.success('Assumptions saved. RFQ scope generation values updated.')}
            style={{ background: '#2563EB' }}
          >
            Save Assumptions
          </Button>
        </TabContentWrapper>
      )
    },
    {
      key: 'clarifications',
      label: <span style={{ fontWeight: 500 }}><QuestionCircleOutlined /> Clarifications</span>,
      children: (
        <TabContentWrapper>
          <EditableSection
            title="Clarifications Required"
            defaultText="1. Specific Oracle features currently in use (e.g., RAC, Oracle GoldenGate, Partitioning).\n2. Real-time availability requirements and maximum allowed downtime window for cutover.\n3. Security and regulatory constraints on CDC logs (e.g. PCI-DSS, GDPR masking rules)."
          />
          <EditableSection
            title="Missing Information"
            defaultText="- Source database load profiles and Peak IOPS requirements.\n- Volume of legacy stored procedures (packages, triggers, functions).\n- Latency SLA boundaries for target analytics consumer systems."
          />
        </TabContentWrapper>
      )
    },
    {
      key: 'gapAnalysis',
      label: <span style={{ fontWeight: 500 }}><ThunderboltOutlined /> Gap Analysis</span>,
      children: (
        <TabContentWrapper>
          <EditableSection
            title="RFP Gap Analysis"
            defaultText="The RFP lacks definitions for post-migration validation checks. There is no mention of parallel run periods or detailed rollback strategies. Target database security configuration (IAM vs standard password auth) is unspecified."
          />
        </TabContentWrapper>
      )
    },
    {
      key: 'risks',
      label: <span style={{ fontWeight: 500 }}><WarningOutlined /> Risks</span>,
      children: (
        <TabContentWrapper>
          <EditableSection
            title="Identified Risks"
            icon={<WarningOutlined style={{ color: '#EF4444' }} />}
            defaultText="- Target latency spikes during bulk CDC mapping intervals.\n- Automated conversion tools failing on complex PL/SQL proprietary packages.\n- Extended migration times due to network bandwidth constraints."
          />
          <EditableSection
            title="Key Dependencies"
            defaultText="- Client Infrastructure Team providing VPN/DirectConnect ingress ports.\n- Client Application Team frozen deployment windows during discovery phases."
          />
        </TabContentWrapper>
      )
    },
    {
      key: 'questions',
      label: <span style={{ fontWeight: 500 }}><QuestionCircleOutlined /> Questions</span>,
      children: (
        <TabContentWrapper>
          <EditableSection
            title="Technical & Integration Questions"
            defaultText="1. Are there any proprietary Oracle data types (e.g., Spatial, XMLType) used?\n2. What is the average and peak transactions-per-second (TPS) on the source database?\n3. Do you have a preferred Kafka registry schema versioning model?"
          />
          <EditableSection
            title="Business & Commercial Questions"
            defaultText="1. What is the business impact if target replication falls behind by more than 5 minutes?\n2. Will licensing costs of AWS RDS Aurora PostgreSQL be billed under the main developer contract?"
          />
          <EditableSection
            title="Compliance & Security Questions"
            defaultText="1. Does the schema store Personally Identifiable Information (PII) subject to GDPR/HIPAA?\n2. Will the CDC logs require at-rest encryption keys managed by the client?"
          />
        </TabContentWrapper>
      )
    },
    {
      key: 'attachments',
      label: <span style={{ fontWeight: 500 }}><PaperClipOutlined /> Attachments</span>,
      children: (
        <TabContentWrapper>
          <div style={{ padding: 24, textAlign: 'center', background: '#F8FAFC', border: '1px dashed #E5E7EB', borderRadius: 8 }}>
            <PaperClipOutlined style={{ fontSize: 24, color: '#6B7280', marginBottom: 8 }} />
            <Paragraph style={{ color: '#111827', margin: 0, fontWeight: 500 }}>No attachments uploaded yet</Paragraph>
            <Text type="secondary" style={{ fontSize: 12 }}>Upload secondary source documents or schema sheets to include them in the discovery analysis.</Text>
          </div>
        </TabContentWrapper>
      )
    },
    {
      key: 'knowledge',
      label: <span style={{ fontWeight: 500 }}><BookOutlined /> Knowledge</span>,
      children: (
        <TabContentWrapper>
          <EditableSection
            title="Associated Knowledge Assets"
            defaultText="- standard_postgresql_migration_strategy_v2.1\n- oracle_to_pg_schema_mappings_cheat_sheet\n- corporate_compliance_guidelines_2026"
          />
        </TabContentWrapper>
      )
    }
  ];



  return (
    <PageContainer maxWidth={1800}>
      <LifecycleStepper currentStage="Discovery" />

      <ActionToolbar
        extra={
          <Space>
            <Button type="primary" onClick={() => navigate(`/opportunities/${id || 'demo'}/rfq`)} style={{ background: '#2563EB', fontWeight: 600 }}>
              Generate RFQ
            </Button>
          </Space>
        }
      >
        <Space direction="vertical" size="small">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(`/opportunities/${id || 'demo'}`)} style={{ color: '#6B7280', padding: 0 }}>Back to Opportunity Details</Button>
          <Space>
            <Title level={3} style={{ margin: 0, fontWeight: 600 }}>General AI Discovery</Title>
            <Tag color="blue" icon={<RobotOutlined />}>AI Analysis Complete</Tag>
          </Space>
        </Space>
      </ActionToolbar>

      <Row gutter={24}>
        <Col span={5}>
          <OpportunitySidebar />
        </Col>

        <Col span={13}>
          <div style={{ background: '#FFFBEB', border: '1px solid #FCD34D', borderRadius: 8, padding: 16, marginBottom: 20 }}>
            <Text strong style={{ color: '#D97706', fontSize: 13, display: 'block', marginBottom: 4 }}>
              ⚠️ Enterprise RFP Completeness Warning (Estimated 64% Complete)
            </Text>
            <Text style={{ color: '#6B7280', fontSize: 12 }}>
              aegisOS has parsed the uploaded RFP and identified substantial gaps regarding legacy PL/SQL dependencies, security protocols, and target performance SLA specifications. Use the generated questions below to align with the client prior to RFQ submission.
            </Text>
          </div>

          <Panel bodyStyle={{ padding: 24 }}>
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={tabItems}
              style={{ minHeight: 400 }}
            />
          </Panel>
        </Col>

        <Col span={6}>
          <ActivityCenter />
        </Col>
      </Row>
    </PageContainer>
  );
}
