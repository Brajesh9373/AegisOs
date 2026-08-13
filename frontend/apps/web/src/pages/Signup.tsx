import React from 'react';
import { Form, Input, Button, Card, Typography, Select, Row, Col } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, BankOutlined, ProfileOutlined, TeamOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

export function Signup() {
  const navigate = useNavigate();

  const onFinish = () => {
    // Set simulated authentication details so the frontend passes auth check
    localStorage.setItem('auth_token', 'simulated_token');
    localStorage.setItem('auth_user_id', 'simulated_user');
    localStorage.setItem('auth_role', 'Viewer');
    
    // Redirect directly to /business-analyst using React Router
    navigate('/business-analyst');
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5', padding: '24px 16px' }}>
      <Card style={{ width: '100%', maxWidth: 540, borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3} style={{ margin: 0 }}>aegisOS</Title>
          <Text type="secondary">Create your AegisOS account</Text>
          <div style={{ marginTop: 4 }}>
            <Text type="secondary" style={{ fontSize: 13 }}>Set up your account to start working with Business Analyst.</Text>
          </div>
        </div>

        <Form name="signup" onFinish={onFinish} layout="vertical" size="large">
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name="fullName" label="Full Name">
                <Input prefix={<UserOutlined style={{ color: '#888' }} />} placeholder="Full Name" />
              </Form.Item>
            </Col>
            
            <Col xs={24} sm={12}>
              <Form.Item name="email" label="Work Email">
                <Input prefix={<MailOutlined style={{ color: '#888' }} />} placeholder="name@company.com" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name="password" label="Password">
                <Input.Password prefix={<LockOutlined style={{ color: '#888' }} />} placeholder="Password" />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12}>
              <Form.Item name="company" label="Company / Organization">
                <Input prefix={<BankOutlined style={{ color: '#888' }} />} placeholder="Company Name" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name="jobTitle" label="Job Title / Role">
                <Input prefix={<ProfileOutlined style={{ color: '#888' }} />} placeholder="e.g. Project Manager" />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12}>
              <Form.Item name="useCase" label="Primary Use Case">
                <Select placeholder="Select primary use case" options={[
                  { value: 'business_analysis', label: 'Business Analysis' },
                  { value: 'process_automation', label: 'Process Automation' },
                  { value: 'ai_workforce', label: 'AI Workforce' },
                  { value: 'system_migration', label: 'System / Data Migration' },
                  { value: 'other', label: 'Other' }
                ]} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="companySize" label="Company Size">
                <Select 
                  placeholder="Select company size" 
                  suffixIcon={<TeamOutlined style={{ color: '#888' }} />}
                  options={[
                    { value: '1-10', label: '1–10' },
                    { value: '11-50', label: '11–50' },
                    { value: '51-200', label: '51–200' },
                    { value: '201-500', label: '201–500' },
                    { value: '500+', label: '500+' }
                  ]} 
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginTop: 8, marginBottom: 12 }}>
            <Button type="primary" htmlType="submit" block>
              Create Account
            </Button>
          </Form.Item>
        </Form>
        
        <div style={{ textAlign: 'center' }}>
          <Text type="secondary">Already have an account? </Text>
          <a href="/login" onClick={(e) => { e.preventDefault(); navigate('/login'); }} style={{ fontWeight: 600 }}>Sign In</a>
        </div>
      </Card>
    </div>
  );
}
