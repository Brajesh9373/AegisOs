import React, { useState } from 'react';
import { Typography, Row, Col, Button, Space, Tag, Input, List, Upload, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, EditOutlined, FileDoneOutlined, HistoryOutlined, SyncOutlined, UploadOutlined, FileTextOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ActionToolbar } from '../components/ui/ActionToolbar';
import { SectionHeader } from '../components/ui/SectionHeader';
import { ExecutiveCard } from '../components/ui/ExecutiveCard';
import { LifecycleStepper } from '../components/ui/LifecycleStepper';
import { OpportunitySidebar } from '../components/ui/OpportunitySidebar';
import { ActivityCenter } from '../components/ui/ActivityCenter';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ContractVersion {
  version: string;
  date: string;
  uploadedBy: string;
  status: string;
  fileName: string;
}

export function OpportunityApproval() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected'>('pending');
  const [uploading, setUploading] = useState(false);
  const [history, setHistory] = useState<ContractVersion[]>([
    {
      version: 'v1.0-draft',
      date: '2026-07-12 14:00',
      uploadedBy: 'Current User',
      status: 'Draft Created',
      fileName: 'PROP-1042-Draft.pdf'
    }
  ]);

  const handleSimulatedUpload = () => {
    setUploading(true);
    setTimeout(() => {
      setUploading(false);
      const newVersion: ContractVersion = {
        version: `v1.1-signed`,
        date: new Date().toLocaleString(),
        uploadedBy: 'Current User',
        status: 'Signed & Active',
        fileName: 'VNU_Modernization_Signed_Agreement.pdf'
      };
      setHistory(prev => [newVersion, ...prev]);
      setStatus('approved');
      message.success('Signed agreement uploaded successfully! Contract verified.');
    }, 1500);
  };

  return (
    <PageContainer maxWidth={1800}>
      <LifecycleStepper currentStage="Approval" />
      
      <ActionToolbar
        extra={
          status === 'approved' ? (
            <Button type="primary" onClick={() => navigate(`/opportunities/${id || 'demo'}/init`)} style={{ background: '#2563EB', fontWeight: 600 }}>
              Proceed to Project Initialization
            </Button>
          ) : (
            <Space>
              <Button icon={<SyncOutlined />} onClick={() => setStatus('pending')} style={{ background: 'transparent' }}>Request Changes</Button>
              <Button danger icon={<CloseCircleOutlined />} onClick={() => setStatus('rejected')}>Reject</Button>
              <Button type="primary" icon={<CheckCircleOutlined />} onClick={() => setStatus('approved')} style={{ background: '#22C55E',  fontWeight: 600 }}>Approve Deal</Button>
            </Space>
          )
        }
      >
        <Space direction="vertical" size="small">
          <Text type="secondary" style={{ fontSize: 12, cursor: 'pointer' }} onClick={() => navigate(`/opportunities/${id || 'demo'}/proposal`)}>← Back to Proposal</Text>
          <Space>
            <Title level={3} style={{ margin: 0, fontWeight: 600 }}>Approval Center</Title>
            {status === 'pending' && <Tag color="orange">Pending Client Signature</Tag>}
            {status === 'approved' && <Tag color="green">Contract Signed</Tag>}
            {status === 'rejected' && <Tag color="red">Deal Lost</Tag>}
          </Space>
        </Space>
      </ActionToolbar>

      <div style={{ background: '#FFFFFF', border: '1px solid #E5E7EB', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, borderRadius: 8 }}>
        <Space direction="vertical" size={2}>
          <Text strong style={{ fontSize: 15, color: '#111827' }}>VNU Database Modernization</Text>
          <Space size="large" style={{ fontSize: 11, color: '#6B7280' }}>
            <span>Customer: <b>VNU</b></span>
            <span>|</span>
            <span>Current Stage: <Tag color="green" style={{ margin: 0, fontSize: 10 }}>Approval</Tag></span>
            <span>|</span>
            <span>Status: <Tag color="success" style={{ margin: 0, fontSize: 10 }}>Active</Tag></span>
            <span>|</span>
            <span>Last Updated: <b>Today 10:30 AM</b></span>
          </Space>
        </Space>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><ExecutiveCard title="Proposal Status" value={status.toUpperCase()} valueColor={status === 'approved' ? '#22C55E' : (status === 'rejected' ? '#EF4444' : '#F59E0B')} bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={6}><ExecutiveCard title="Total Value" value="$57,385.00" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={6}><ExecutiveCard title="Approvers" value="2 / 2" valueColor='#2563EB' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        <Col span={6}><ExecutiveCard title="Requested Changes" value="0" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
      </Row>

      <Row gutter={24}>
        <Col span={18}>
          <SectionHeader title="Upload Signed Agreement" />
          <Panel bodyStyle={{ padding: 24, marginBottom: 24 }}>
            <Text style={{ display: 'block', marginBottom: 16 }}>Upload the executed, counter-signed VNU project contract to lock the opportunity scope.</Text>
            
            <div style={{ background: '#F8FAFC', border: '1px dashed #D1D5DB', padding: 24, textAlign: 'center', borderRadius: 8 }}>
              <Upload 
                showUploadList={false} 
                customRequest={handleSimulatedUpload}
                disabled={uploading}
              >
                <Button icon={<UploadOutlined />} loading={uploading} style={{ background: '#2563EB', color: '#FFFFFF', border: 'none', fontWeight: 600 }}>
                  {uploading ? 'Processing File...' : 'Upload Signed PDF'}
                </Button>
              </Upload>
              <Text type="secondary" style={{ display: 'block', fontSize: 11, marginTop: 8 }}>Supported format: PDF up to 10MB</Text>
            </div>
          </Panel>

          <SectionHeader title="Agreement Version History" />
          <Panel bodyStyle={{ padding: 0, marginBottom: 24 }}>
            <List
              dataSource={history}
              renderItem={(item) => (
                <List.Item style={{ padding: '16px 24px', borderBottom: '1px solid #E5E7EB' }}>
                  <List.Item.Meta
                    avatar={<FileTextOutlined style={{ fontSize: 24, color: '#2563EB', marginTop: 4 }} />}
                    title={<Text strong style={{ color: '#111827' }}>{item.fileName} <Tag color="blue" style={{ marginLeft: 8 }}>{item.version}</Tag></Text>}
                    description={
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary" style={{ fontSize: 12, marginRight: 16 }}>Uploaded By: <b>{item.uploadedBy}</b></Text>
                        <Text type="secondary" style={{ fontSize: 12, marginRight: 16 }}>Date: <b>{item.date}</b></Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>Status: <Tag color={item.status.includes('Signed') ? 'green' : 'default'}>{item.status}</Tag></Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Panel>

          <SectionHeader title="Comments & Requested Changes" />
          <Panel bodyStyle={{ padding: 24, marginBottom: 24 }}>
            <TextArea rows={4} placeholder="Add any final approval notes or requested changes here..." />
          </Panel>

          <SectionHeader title="Audit Trail" />
          <Panel bodyStyle={{ padding: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f0f0f0', paddingBottom: 8, marginBottom: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>[Oct 5 14:00] Proposal PROP-1042-Draft created by System.</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>ID: trk-9832</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f0f0f0', paddingBottom: 8, marginBottom: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>[Oct 5 15:30] Sent to Client via Email API.</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>ID: trk-9844</Text>
            </div>
            {status === 'approved' && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ color: '#22C55E', fontSize: 12 }}>[Oct 7 09:00] Signed contract uploaded & verified by Current User.</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>ID: trk-9912</Text>
              </div>
            )}
          </Panel>
        </Col>

        <Col span={6}>
          <ActivityCenter />
        </Col>
      </Row>
    </PageContainer>
  );
}
