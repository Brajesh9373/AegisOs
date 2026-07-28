import React, { useState } from 'react';
import { Typography, Row, Col, Button, Space, Input, Form, Upload, message } from 'antd';
import { ArrowLeftOutlined, InboxOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { Panel } from '../components/ui/Panel';
import { PageContainer } from '../components/ui/PageContainer';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

export function NewOpportunityWizard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleCreate = (values: any) => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      const generatedId = Math.random().toString(36).substring(2, 9);
      message.success('Opportunity created successfully.');
      navigate(`/opportunities/${generatedId}`);
    }, 1000);
  };

  return (
    <div style={{ background: '#F8FAFC', minHeight: '100vh', padding: '40px 32px' }}>
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <Space size="middle" style={{ marginBottom: 32 }}>
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/home')} style={{ color: '#111827', padding: 0, fontWeight: 500 }}>Back</Button>
          <Title level={3} style={{ margin: 0, fontWeight: 700, color: '#111827' }}>New Opportunity</Title>
        </Space>

        <Panel bodyStyle={{ padding: 40 }}>
          <Paragraph style={{ color: '#6B7280', marginBottom: 32, fontSize: 14 }}>
            Enter the initial details for this new business opportunity. This information will seed the General AI Discovery process.
          </Paragraph>
          
          <Form form={form} layout="vertical" onFinish={handleCreate}>
            <Form.Item 
              name="name" 
              label={<Text style={{ fontWeight: 500, color: '#374151' }}>Opportunity Name</Text>} 
              rules={[{ required: true }]}
            >
              <Input placeholder="e.g. VNU Database Modernization" size="large" />
            </Form.Item>
            
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item 
                  name="customer" 
                  label={<Text style={{ fontWeight: 500, color: '#374151' }}>Customer Name</Text>} 
                  rules={[{ required: true }]}
                >
                  <Input placeholder="e.g. VNU" size="large" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item 
                  name="industry" 
                  label={<Text style={{ fontWeight: 500, color: '#374151' }}>Business Domain / Industry</Text>}
                >
                  <Input placeholder="e.g. Finance" size="large" />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item 
                  name="budget" 
                  label={<Text style={{ fontWeight: 500, color: '#374151' }}>Expected Budget</Text>}
                >
                  <Input placeholder="e.g. $150,000" size="large" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item 
                  name="timeline" 
                  label={<Text style={{ fontWeight: 500, color: '#374151' }}>Expected Timeline</Text>}
                >
                  <Input placeholder="e.g. Q3 2024" size="large" />
                </Form.Item>
              </Col>
            </Row>
            
            <Form.Item 
              name="goal" 
              label={<Text style={{ fontWeight: 500, color: '#374151' }}>Business Goal</Text>} 
              rules={[{ required: true }]}
            >
              <Input.TextArea rows={4} placeholder="Describe the high-level objective..." />
            </Form.Item>

            <Form.Item label={<Text style={{ fontWeight: 500, color: '#374151' }}>Initial Attachments (Optional)</Text>}>
              <Dragger 
                beforeUpload={() => false}
                style={{ borderRadius: 12, border: '2px dashed #E5E7EB', background: '#F8FAFC' }}
              >
                <p className="ant-upload-drag-icon">
                  <InboxOutlined style={{ color: '#2563EB', fontSize: 32 }} />
                </p>
                <p style={{ color: '#4B5563', fontWeight: 500 }}>Click or drag preliminary docs here</p>
              </Dragger>
            </Form.Item>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 16, marginTop: 24 }}>
              <Button onClick={() => navigate('/home')} style={{ borderColor: '#E5E7EB', color: '#4B5563', fontWeight: 500 }}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={loading} style={{ background: '#2563EB', fontWeight: 600, padding: '0 24px' }}>
                Initiate AI Discovery
              </Button>
            </div>
          </Form>
        </Panel>
      </div>
    </div>
  );
}
