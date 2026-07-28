import React, { useState } from 'react';
import { Typography, Row, Col, Button, Space, Upload, Progress, ConfigProvider, theme } from 'antd';
import { InboxOutlined, ArrowLeftOutlined, RobotOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ActionToolbar } from '../components/ui/ActionToolbar';
import { LifecycleStepper } from '../components/ui/LifecycleStepper';
import { OpportunitySidebar } from '../components/ui/OpportunitySidebar';
import { ActivityCenter } from '../components/ui/ActivityCenter';

const { Title, Text } = Typography;
const { Dragger } = Upload;

export function UploadRFP() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [complete, setComplete] = useState(false);

  const handleUpload = () => {
    setUploading(true);
    setTimeout(() => {
      setUploading(false);
      setParsing(true);
      setTimeout(() => {
        setParsing(false);
        setComplete(true);
      }, 3000);
    }, 1500);
  };

  return (
    
      <PageContainer maxWidth={1800}>
        <LifecycleStepper currentStage="RFQ" />
        
        <ActionToolbar
          extra={
            complete && (
              <Button type="primary" onClick={() => navigate(`/opportunities/${id || 'demo'}/discovery`)} style={{ background: '#2563EB', fontWeight: 600 }}>
                Proceed to AI Discovery
              </Button>
            )
          }
        >
          <Space direction="vertical" size="small">
            <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(`/opportunities/${id || 'demo'}`)} style={{ color: '#6B7280', padding: 0 }}>Back to Opportunity Hub</Button>
            <Title level={3} style={{ margin: 0, fontWeight: 600 }}>Upload RFP</Title>
          </Space>
        </ActionToolbar>

        <Row gutter={24}>
          <Col span={5}>
            <OpportunitySidebar />
          </Col>
          
          <Col span={13}>
            <Panel bodyStyle={{ padding: 48, textAlign: 'center' }}>
              {!uploading && !parsing && !complete && (
                <Dragger 
                  style={{ background: '#fafafa', borderColor: '#E5E7EB' }}
                  onChange={handleUpload}
                  showUploadList={false}
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined style={{ color: '#2563EB' }} />
                  </p>
                  <p className="ant-upload-text" style={{}}>Click or drag RFP document to this area</p>
                  <p className="ant-upload-hint" style={{ color: '#6B7280' }}>
                    Support for a single PDF or DOCX file. The system will automatically parse and vectorize the contents.
                  </p>
                </Dragger>
              )}

              {uploading && (
                <div style={{ padding: 48 }}>
                  <Progress type="circle" percent={45} strokeColor="#2563EB" />
                  <Title level={4} style={{ marginTop: 24 }}>Uploading File...</Title>
                </div>
              )}

              {parsing && (
                <div style={{ padding: 48 }}>
                  <Progress type="circle" percent={82} strokeColor="#22C55E" />
                  <Title level={4} style={{ marginTop: 24 }}>AI Parsing & Vectorization in Progress...</Title>
                  <Text style={{ color: '#6B7280' }}><RobotOutlined /> Extracting Requirements, Risks, and Timelines</Text>
                </div>
              )}

              {complete && (
                <div style={{ padding: 48 }}>
                  <CheckCircleOutlined style={{ fontSize: 64, color: '#22C55E', marginBottom: 24 }} />
                  <Title level={3} style={{ margin: 0 }}>RFP Processed Successfully</Title>
                  <Text style={{ color: '#6B7280', display: 'block', marginTop: 8 }}>Knowledge Assets created. Memory Engine updated.</Text>
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
