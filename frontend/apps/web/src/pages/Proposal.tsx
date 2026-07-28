import React from 'react';
import { Typography, Row, Col, Button, Space, Tag, Input } from 'antd';
import { EyeOutlined, FilePdfOutlined, MailOutlined, SaveOutlined, SendOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ActionToolbar } from '../components/ui/ActionToolbar';
import { LifecycleStepper } from '../components/ui/LifecycleStepper';
import { OpportunitySidebar } from '../components/ui/OpportunitySidebar';
import { ActivityCenter } from '../components/ui/ActivityCenter';

const { Title, Text } = Typography;
const { TextArea } = Input;

export function Proposal() {
  const navigate = useNavigate();
  const { id } = useParams();

  const ProposalSection = ({ title, text }: { title: string, text: string }) => (
    <div style={{ marginBottom: 32 }}>
      <Text strong style={{ display: 'block', fontSize: 15, borderBottom: '1px solid #E5E7EB', paddingBottom: 6, marginBottom: 12, color: '#111827', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</Text>
      <TextArea bordered={false} autoSize defaultValue={text} style={{ padding: 0, color: '#374151', fontSize: 13, lineHeight: 1.6 }} />
    </div>
  );

  return (
    <PageContainer maxWidth={1800}>
      <LifecycleStepper currentStage="Proposal" />

      <ActionToolbar
        extra={
          <Space>
            <Button icon={<EyeOutlined />} style={{ background: 'transparent' }}>Preview</Button>
            <Button icon={<FilePdfOutlined />} style={{ background: 'transparent', color: '#EF4444' }}>Export PDF</Button>
            <Button icon={<MailOutlined />} style={{ background: 'transparent' }}>Email Client</Button>
            <Button icon={<SaveOutlined />} style={{ background: 'transparent', color: '#2563EB' }}>Save Draft</Button>
            <Button type="primary" icon={<SendOutlined />} onClick={() => navigate(`/opportunities/${id || 'demo'}/approve`)} style={{ background: '#2563EB', fontWeight: 600 }}>Submit For Approval</Button>
          </Space>
        }
      >
        <Space direction="vertical" size="small">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(`/opportunities/${id || 'demo'}/rfq`)} style={{ color: '#6B7280', padding: 0 }}>Back to RFQ</Button>
          <Space>
            <Title level={3} style={{ margin: 0, fontWeight: 600 }}>Commercial Proposal</Title>
            <Tag color="blue">Review Mode</Tag>
          </Space>
        </Space>
      </ActionToolbar>

      <div style={{ background: '#FFFFFF', border: '1px solid #E5E7EB', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, borderRadius: 8 }}>
        <Space direction="vertical" size={2}>
          <Text strong style={{ fontSize: 15, color: '#111827' }}>VNU Database Modernization</Text>
          <Space size="large" style={{ fontSize: 11, color: '#6B7280' }}>
            <span>Customer: <b>VNU</b></span>
            <span>|</span>
            <span>Current Stage: <Tag color="blue" style={{ margin: 0, fontSize: 10 }}>Proposal</Tag></span>
            <span>|</span>
            <span>Status: <Tag color="success" style={{ margin: 0, fontSize: 10 }}>Active</Tag></span>
            <span>|</span>
            <span>Last Updated: <b>Today 10:30 AM</b></span>
          </Space>
        </Space>
      </div>

      <Row gutter={24}>
        <Col span={18}>
          <Panel bodyStyle={{ padding: 48, background: '#FFFFFF', color: '#111827', borderRadius: 12, border: '1px solid #E5E7EB' }}>

            {/* Cover Page */}
            <div style={{ borderBottom: '2px solid #111827', paddingBottom: 48, marginBottom: 48, textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '2px', display: 'block', marginBottom: 16 }}>COMMERCIAL PROJECT PROPOSAL</Text>
              <Title level={1} style={{ margin: '0 0 16px 0', color: '#111827', fontWeight: 800 }}>DATABASE MODERNIZATION & SYNC PIPELINE</Title>
              <Text strong style={{ fontSize: 16, display: 'block', color: '#2563EB' }}>Prepared for: VNU Corporation</Text>
              <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>Doc Ref: PROP-2026-VNU-v1.0 • Date: Oct 5</Text>
            </div>

            <ProposalSection
              title="Executive Summary"
              text="aegisOS proposes to execute the complete database modernization from legacy Oracle 19c systems to AWS RDS Aurora PostgreSQL. This proposal establishes the technical architecture, target timeline, resource structures, and commercial milestones necessary to complete the transition."
            />

            <ProposalSection
              title="Customer Challenges"
              text="VNU is constrained by legacy Oracle license limits, restricting the dynamic compute scaling required for peak query operations. Additionally, downstream analytical systems lack real-time synchronization, resulting in query latency delays."
            />

            <ProposalSection
              title="Proposed Solution"
              text="Deploy a cloud-native AWS RDS Aurora PostgreSQL target environment. Utilize Debezium CDC and Kafka Connect clusters to maintain continuous, unidirectional schema state replication, minimizing cutover downtime to under 2 hours."
            />

            <ProposalSection
              title="Solution Architecture"
              text="- Database Engine: Aurora PostgreSQL 15.x (Multi-AZ config).\n- CDC Pipeline: Kafka Connect cluster running Debezium Oracle source connector with wal2json plugin.\n- Networking: AWS DirectConnect connections established between VNU source server racks and AWS Virtual Private Gateways."
            />

            <ProposalSection
              title="Scope"
              text="- Translate and deploy 100% of tables, constraints, indexes, views, and schemas.\n- Convert complex nested PL/SQL packages, packages, and database triggers to pgSQL.\n- Configure real-time Kafka publisher topics and test streaming latency."
            />

            <ProposalSection
              title="Deliverables"
              text="- Target Terraform infrastructure scripts.\n- Translated schema definitions and custom SQL triggers.\n- Deployment profiles for Debezium source connectors.\n- Staging UAT validation reports and Go-live runbook."
            />

            <ProposalSection
              title="Implementation Methodology"
              text="Our delivery model uses the aegisOS Autonomous Lifecycle, dividing execution into distinct sprint-based validation phases to ensure zero-loss transactional migration."
            />

            <ProposalSection
              title="Project Phases"
              text="- Phase 1: Discovery, schema mapping, and PL/SQL code assessment.\n- Phase 2: Terraform infrastructure provisioning and staging DDL deployment.\n- Phase 3: Kafka Debezium replication configuration and stress execution runs.\n- Phase 4: UAT verification, cutover execution, and post-migration handover."
            />

            <ProposalSection
              title="Project Plan"
              text="Tasks are organized in parallel track streams. Discovery starts on Week 1. Staging deployments launch on Week 4. Data validation and continuous UAT runs execute during Weeks 10-11."
            />

            <ProposalSection
              title="Team Structure"
              text="The project team consists of human managers directing digital supervisor nodes to run automated compilation and validation scripts."
            />

            <ProposalSection
              title="Human Employees"
              text="- Sarah Jenkins (Lead Database Migration Architect) - Oversight, architectural sign-off, and validation coordination.\n- Current User (Sales) - Account management, billing coordination, and milestone validation."
            />

            <ProposalSection
              title="Digital Employees"
              text="- Schema Discovery Agent (Owned by Sarah Jenkins) - Discovers tables, analyzes data constraints, and exports translation schema logs.\n- Data Mapping Agent (Owned by Sarah Jenkins) - Converts Oracle SQL functions to pgSQL."
            />

            <ProposalSection
              title="AI Responsibilities"
              text="The autonomous agent runtime performs schema mapping generation, validates column integrity, outputs translation scripts, and verifies topic streaming throughput parameters."
            />

            <ProposalSection
              title="Timeline"
              text="Total Project Duration: 12 Weeks from execution kickoff to cutover sign-off."
            />

            <ProposalSection
              title="Milestones"
              text="- MS 1: Discovery Sign-off (Week 3)\n- MS 2: Staging Schema UAT Completion (Week 9)\n- MS 3: Production Cutover & Handover (Week 12)"
            />

            <ProposalSection
              title="Risk Management"
              text="- Legacy PL/SQL triggers translation failure $\rightarrow$ Mitigated by assigning 15% contingency effort buffer for custom pgSQL rewrites.\n- Staging VPC peer timeout $\rightarrow$ Mitigated by early network direct tunnel validation check."
            />

            <ProposalSection
              title="Assumptions"
              text="1. VNU infrastructure team configures required directPeering access routes within 5 working days of request.\n2. Target Aurora PostgreSQL engine version 15.x meets VNU analytical query requirements."
            />

            <ProposalSection
              title="Dependencies"
              text="- AWS landing zone staging accounts must be fully provisioned before Phase 2 launches."
            />

            <ProposalSection
              title="Pricing"
              text="Total Fixed Project Cost: $57,385.00\n- Engineering Services: $40,000.00\n- Automated Conversion Licensing: $5,000.00\n- Support Retainer: $12,385.00"
            />

            <ProposalSection
              title="Commercial Terms"
              text="Payment terms: Net 30, milestone-based billing (30% upon blueprint approval, 40% mid-point staging success, 30% production delivery)."
            />

            <ProposalSection
              title="Support Model"
              text="Vendor provides Tier-3 integration support for 90 days following production cutover. General support requests resolved within 4 hours during standard operation windows."
            />

            <ProposalSection
              title="Warranty"
              text="All custom pgSQL rewritten functions carry a 90-day post-go-live warranty against syntax bugs or transactional execution faults."
            />

            <ProposalSection
              title="SLA"
              text="- CDC Data Replication Latency: Max 2.0 seconds under peak operations.\n- Staging environment API uptime: 99.9% availability during business hours."
            />

            <ProposalSection
              title="Acceptance Criteria"
              text="1. Successful compile validation of all pgSQL functions.\n2. Checksum validation confirms 100% data parity over 72-hour test replication run.\n3. Steering committee signature sign-off."
            />

            <ProposalSection
              title="Success Metrics"
              text="- Database compute scaling costs reduced by minimum 40%.\n- Target replication latency falls below 1.5 seconds under test write load."
            />

            <ProposalSection
              title="Appendices"
              text="Appendix A: Full mapped table lists and schema statistics\nAppendix B: Target VPC peering network parameters\nAppendix C: Custom post-migration support SLA contract templates"
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
