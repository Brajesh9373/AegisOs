import React from 'react';
import { Typography, Row, Col, Button, Space, Tag, Input } from 'antd';
import { ArrowLeftOutlined, FilePdfOutlined, MailOutlined, CheckCircleOutlined, SaveOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ActionToolbar } from '../components/ui/ActionToolbar';
import { LifecycleStepper } from '../components/ui/LifecycleStepper';
import { OpportunitySidebar } from '../components/ui/OpportunitySidebar';
import { ActivityCenter } from '../components/ui/ActivityCenter';

const { Title, Text } = Typography;
const { TextArea } = Input;

export function RFQBuilder() {
  const navigate = useNavigate();
  const { id } = useParams();

  const RFQSection = ({ title, text }: { title: string, text: string }) => (
    <div style={{ marginBottom: 32 }}>
      <Text strong style={{ display: 'block', fontSize: 14, borderBottom: '1px solid #E5E7EB', paddingBottom: 6, marginBottom: 12, color: '#111827', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</Text>
      <TextArea bordered={false} autoSize defaultValue={text} style={{ padding: 0, color: '#374151', fontSize: 13, lineHeight: 1.6 }} />
    </div>
  );

  return (
    <PageContainer maxWidth={1800}>
      <LifecycleStepper currentStage="RFQ" />
      
      <ActionToolbar
        extra={
          <Space>
            <Button icon={<EyeOutlined />} style={{ background: 'transparent' }}>Preview</Button>
            <Button icon={<FilePdfOutlined />} style={{ background: 'transparent', color: '#EF4444' }}>Export PDF</Button>
            <Button icon={<MailOutlined />} style={{ background: 'transparent' }}>Email Client</Button>
            <Button icon={<SaveOutlined />} style={{ background: 'transparent', color: '#2563EB' }}>Save Draft</Button>
            <Button type="primary" icon={<CheckCircleOutlined />} onClick={() => navigate(`/opportunities/${id || 'demo'}/proposal`)} style={{ background: '#2563EB', fontWeight: 600 }}>Approve & Create Proposal</Button>
          </Space>
        }
      >
        <Space direction="vertical" size="small">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(`/opportunities/${id || 'demo'}/discovery`)} style={{ color: '#6B7280', padding: 0 }}>Back to Discovery</Button>
          <Space>
            <Title level={3} style={{ margin: 0, fontWeight: 600 }}>RFQ Generation</Title>
            <Tag color="orange">Draft</Tag>
          </Space>
        </Space>
      </ActionToolbar>

      <div style={{ background: '#FFFFFF', border: '1px solid #E5E7EB', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, borderRadius: 8 }}>
        <Space direction="vertical" size={2}>
          <Text strong style={{ fontSize: 15, color: '#111827' }}>VNU Database Modernization</Text>
          <Space size="large" style={{ fontSize: 11, color: '#6B7280' }}>
            <span>Customer: <b>VNU</b></span>
            <span>|</span>
            <span>Current Stage: <Tag color="orange" style={{ margin: 0, fontSize: 10 }}>RFQ</Tag></span>
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
            
            {/* 1. Cover Page */}
            <div style={{ borderBottom: '2px solid #111827', paddingBottom: 48, marginBottom: 48, textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '2px', display: 'block', marginBottom: 16 }}>REQUEST FOR QUOTATION (RFQ)</Text>
              <Title level={1} style={{ margin: '0 0 16px 0', color: '#111827', fontWeight: 800 }}>DATABASE MODERNIZATION & real-time sync</Title>
              <Text strong style={{ fontSize: 16, display: 'block', color: '#2563EB' }}>Target Entity: VNU Corporation</Text>
              <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>Doc Ref: RFQ-2026-VNU-MIG-v1.3 • Status: Draft • Date: Oct 3</Text>
            </div>

            {/* 2. Executive Summary */}
            <RFQSection 
              title="2. Executive Summary" 
              text="VNU is seeking binding vendor bids for database modernization from legacy Oracle 19c systems to PostgreSQL. The primary driver is eliminating license overhead while securing horizontally scalable replication targets and configuring a real-time CDC sync pipeline." 
            />

            {/* 3. Project Background */}
            <RFQSection 
              title="3. Project Background" 
              text="VNU operates a distributed transactional legacy suite. The central Oracle cluster supports the core customer billing and configuration registers, but proprietary licenses restrict compute scaling, leading to substantial cost during peak operations." 
            />

            {/* 4. Current State Assessment */}
            <RFQSection 
              title="4. Current State Assessment" 
              text="The current footprint spans 4 core Oracle transactional databases totaling 12TB. Heavily nested PL/SQL packages, stored procedures, and triggers host the core business rules. Data types include standard numeric, spatial, and custom objects." 
            />

            {/* 5. Business Objectives */}
            <RFQSection 
              title="5. Business Objectives" 
              text="- Objective 1: Reduce database operations and licensing overhead costs by 40% annually.\n- Objective 2: Establish low-latency read replicas supporting real-time downstream analytical consumers.\n- Objective 3: Maintain full transaction isolation integrity during schema cutover." 
            />

            {/* 6. Scope of Work */}
            <RFQSection 
              title="6. Scope of Work" 
              text="The selected vendor is responsible for complete schema discovery, PL/SQL code rewrite to pgSQL, target infrastructure deployment in AWS, CDC pipeline configuration, test validation run execution, and final cutover handover support." 
            />

            {/* 7. In Scope */}
            <RFQSection 
              title="7. In Scope" 
              text="- Translation of 100% of tables, constraints, keys, indexes, views, and schemas.\n- Rewriting Oracle triggers and stored packages to PostgreSQL-compatible functions.\n- Provisioning and configuring Debezium connectors on Apache Kafka." 
            />

            {/* 8. Out of Scope */}
            <RFQSection 
              title="8. Out of Scope" 
              text="- Modernizing or rewriting downstream client application query logic (other than updating driver targets).\n- Migration of historic backups and cold partition archives exceeding 3 years of age." 
            />

            {/* 9. Functional Requirements */}
            <RFQSection 
              title="9. Functional Requirements" 
              text="- System must stream updates to consumer topics within 2 seconds of commit.\n- Failover mechanisms must track replication offset checkpoints automatically." 
            />

            {/* 10. Non Functional Requirements */}
            <RFQSection 
              title="10. Non Functional Requirements" 
              text="- Availability: Aurora replica targets must maintain 99.95% operational availability.\n- Performance: The target schema must support peak 3,500 TPS write workload." 
            />

            {/* 11. Technical Requirements */}
            <RFQSection 
              title="11. Technical Requirements" 
              text="- Source: Oracle 19c Enterprise Edition.\n- Target: AWS RDS Aurora PostgreSQL Engine version 15.x.\n- CDC Core: Kafka Connect runtime utilizing Debezium Oracle source connector." 
            />

            {/* 12. Architecture Requirements */}
            <RFQSection 
              title="12. Architecture Requirements" 
              text="Multi-AZ deployment configurations. Replicas must reside in isolated private subnets. Connection pooling must be configured using PgBouncer to manage high consumer client counts." 
            />

            {/* 13. Security Requirements */}
            <RFQSection 
              title="13. Security Requirements" 
              text="All credentials must be stored inside AWS Secrets Manager. CDC pipeline data must be encrypted in transit via TLS 1.3 and at rest via Customer Managed KMS Keys." 
            />

            {/* 14. Compliance Requirements */}
            <RFQSection 
              title="14. Compliance Requirements" 
              text="Vendor must ensure full SOC2 Type II compliance controls. PII data fields (SSN, payment IDs) must undergo real-time regex hashing within Kafka Connect filters prior to topic dispatch." 
            />

            {/* 15. Integration Requirements */}
            <RFQSection 
              title="15. Integration Requirements" 
              text="Integrate targets with VNU corporate OpenTelemetry dashboards for CDC latency logs and connect event notification webhooks to slack channels." 
            />

            {/* 16. Data Migration Requirements */}
            <RFQSection 
              title="16. Data Migration Requirements" 
              text="Initial full-load snapshot execution must not interrupt source operations. Initial validation checks must confirm checksum values across 100% of migrated source tables." 
            />

            {/* 17. Infrastructure Requirements */}
            <RFQSection 
              title="17. Infrastructure Requirements" 
              text="All infrastructure provisioning must use Terraform templates. AWS landing zone must connect back to local VNU server racks via dual AWS DirectConnect lines." 
            />

            {/* 18. Deliverables */}
            <RFQSection 
              title="18. Deliverables" 
              text="1. Target Terraform configuration files.\n2. Verified schema conversion SQL scripts.\n3. Kafka configuration profiles.\n4. Complete Validation report and Go-Live Cutover Runbook." 
            />

            {/* 19. Acceptance Criteria */}
            <RFQSection 
              title="19. Acceptance Criteria" 
              text="- Zero column format mismatches.\n- CDC latency under 1.5 seconds over continuous 72-hour stress load run.\n- Completed sign-off by VP of Engineering." 
            />

            {/* 20. Project Timeline */}
            <RFQSection 
              title="20. Project Timeline" 
              text="Total Project Duration: 12 Weeks\n- W1-3: Discovery and Schema Analysis.\n- W4-9: Translation, Data Load and CDC Config.\n- W10-12: Testing, Validation and Cutover." 
            />

            {/* 21. Resource Requirements */}
            <RFQSection 
              title="21. Resource Requirements" 
              text="- 1 Lead Database Migration Architect (240 hours)\n- 1 Senior DevOps Infrastructure Engineer (120 hours)\n- 1 QA Integration Engineer (100 hours)" 
            />

            {/* 22. Roles & Responsibilities */}
            <RFQSection 
              title="22. Roles & Responsibilities" 
              text="- Vendor: Delivery of verified target schemas and working replication sync.\n- VNU: Provision of source system DBA access, landing zone VPC permissions, and UAT verification." 
            />

            {/* 23. Assumptions */}
            <RFQSection 
              title="23. Assumptions" 
              text="1. Client infrastructure team will configure AWS account landing zones within 5 business days of kickoff.\n2. Representative anonymized data will be provided for UAT phases." 
            />

            {/* 24. Dependencies */}
            <RFQSection 
              title="24. Dependencies" 
              text="- Clean VPC peering and network route paths between target staging systems and the source Oracle server." 
            />

            {/* 25. Risks */}
            <RFQSection 
              title="25. Risks" 
              text="- Migration delays due to conversion faults on legacy nested Oracle packages.\n- Target network throttling during full-load snapshot copy phases." 
            />

            {/* 26. Customer Responsibilities */}
            <RFQSection 
              title="26. Customer Responsibilities" 
              text="Provide single point of contact for technical coordination, assign database administrators for staging access, and sign off milestones within 3 working days." 
            />

            {/* 27. Vendor Responsibilities */}
            <RFQSection 
              title="27. Vendor Responsibilities" 
              text="Execute task items following the agreed migration timeline, coordinate daily standup updates, and supply full source files of translation scripts." 
            />

            {/* 28. Open Questions */}
            <RFQSection 
              title="28. Open Questions" 
              text="1. Is there an active schema freeze scheduled for source applications during the validation phase?\n2. What is the preferred key management key rotation policy for the target AWS account?" 
            />

            {/* 29. Pricing Template */}
            <RFQSection 
              title="29. Pricing Template" 
              text="Fixed Price Milestones:\n- Milestone 1: Blueprint approval (30%)\n- Milestone 2: Staging validation (40%)\n- Milestone 3: Final go-live (30%)" 
            />

            {/* 30. Appendix */}
            <RFQSection 
              title="30. Appendix" 
              text="Appendix A: Current Schema DDL metrics & Table List\nAppendix B: Downstream API consumer system overview\nAppendix C: Standard Security Ingress/Egress guidelines" 
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
