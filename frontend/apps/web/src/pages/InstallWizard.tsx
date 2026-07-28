import React, { useState } from 'react';
import { Steps, Form, Input, Button, Typography, Result, Select, Space, Alert, Divider, Progress, Layout, Row, Col, Card, Modal } from 'antd';
import { ApiClient } from '../api/client';
import { CheckCircleOutlined, CloseCircleOutlined, BankOutlined, UserOutlined, RobotOutlined, RocketOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Header, Content, Sider } = Layout;

const AI_PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'openrouter', label: 'OpenRouter' },
  { value: 'ollama', label: 'Ollama' },
  { value: 'lmstudio', label: 'LM Studio' },
  { value: 'custom', label: 'Custom OpenAI Compatible' }
];

export function InstallWizard({ onComplete }: { onComplete: () => void }) {
  const [current, setCurrent] = useState(0);
  const [form] = Form.useForm();
  const [testingAi, setTestingAi] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  const aiProvider = Form.useWatch('aiProvider', form);

  const steps = [
    { title: 'Organization', icon: <BankOutlined /> },
    { title: 'Super Admin', icon: <UserOutlined /> },
    { title: 'AI Provider', icon: <RobotOutlined /> },
    { title: 'Review', icon: <CheckCircleOutlined /> },
    { title: 'Install', icon: <RocketOutlined /> },
    { title: 'Health', icon: <CheckCircleOutlined /> },
    { title: 'Finish', icon: <CheckCircleOutlined /> }
  ];

  const passwordValidator = async (_: any, value: string) => {
    if (!value) return Promise.resolve();
    if (value.length < 12) return Promise.reject(new Error('Minimum 12 characters'));
    if (!/[A-Z]/.test(value)) return Promise.reject(new Error('Needs uppercase letter'));
    if (!/[a-z]/.test(value)) return Promise.reject(new Error('Needs lowercase letter'));
    if (!/[0-9]/.test(value)) return Promise.reject(new Error('Needs number'));
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) return Promise.reject(new Error('Needs special character'));
    return Promise.resolve();
  };

  const testConnection = async (type: 'ai') => {
    setTestingAi(true);
    try {
      await form.validateFields();
      await ApiClient.post(`/install/test/${type}`, form.getFieldsValue(true));
    } catch (e: any) {
      ApiClient.handleError(e);
    }
    setTestingAi(false);
  };

  const onNext = async () => {
    console.log(`[DEBUG] Current Step: ${current}, Form Values:`, form.getFieldsValue(true));
    try {
      let fields: string[] = [];
      if (current === 0) fields = ['orgName'];
      if (current === 1) fields = ['adminName', 'adminEmail', 'adminPassword'];
      if (current === 2) {
        fields = ['aiProvider', 'aiModel'];
        if (['openai', 'gemini', 'anthropic'].includes(aiProvider)) fields.push('aiApiKey');
      }

      if (fields.length > 0) {
        await form.validateFields(fields);
      }
      console.log(`[DEBUG] Validation Result: Success for fields:`, fields);

      if (current === 3) { // Review step
        console.log(`[DEBUG] Navigation Result: Moving to Install (4)`);
        setCurrent(4); // Install
        setInstalling(true);
        try {
          const payload = form.getFieldsValue(true);
          console.log(`[DEBUG] API Request: POST /api/install`, payload);
          const res = await ApiClient.post('/install', payload);
          console.log(`[DEBUG] API Response:`, res);
          setTimeout(() => {
            setInstalling(false);
            setCurrent(5); // Health
            console.log(`[DEBUG] Navigation Result: Moving to Health (5)`);
            ApiClient.get('/install/health').then(setHealthStatus).catch(() => setHealthStatus({ status: 'error' }));
          }, 2000);
        } catch (e: any) {
          console.error(`[DEBUG] API Error:`, e);
          const status = e.response?.status || 'Unknown';
          const reason = e.response?.data?.error?.message || e.message;
          const code = e.response?.data?.error?.code || 'ERR';
          Modal.error({
            title: 'Installation Failed',
            content: (
              <div>
                <p><strong>Reason:</strong> {reason}</p>
                <p><strong>HTTP Status:</strong> {status}</p>
                <p><strong>Backend Message:</strong> {code}</p>
              </div>
            ),
            okText: 'Retry'
          });
          setCurrent(3);
          setInstalling(false);
        }
        return;
      }

      if (current === 5) {
        console.log(`[DEBUG] Navigation Result: Moving to Finish (6)`);
        setCurrent(6); // Finish
        return;
      }
      console.log(`[DEBUG] Navigation Result: Moving to step ${current + 1}`);
      setCurrent(current + 1);
    } catch (err: any) {
      console.error(`[DEBUG] Validation Result: Failed`, err);
    }
  };

  const renderAiConfig = () => {
    switch (aiProvider) {
      case 'openai':
      case 'anthropic':
        return (
          <>
            <Form.Item name="aiApiKey" label="API Key" rules={[{ required: true }]}><Input.Password size="large" /></Form.Item>
            <Form.Item name="aiModel" label="Default Model" rules={[{ required: true }]}><Input size="large" /></Form.Item>
          </>
        );
      case 'gemini':
        return (
          <>
            <Form.Item name="aiApiKey" label="API Key" rules={[{ required: true }]}><Input.Password size="large" /></Form.Item>
            <Form.Item name="aiModel" label="Default Model" rules={[{ required: true }]}><Input size="large" placeholder="gemini-pro" /></Form.Item>
          </>
        );
      case 'azure':
      case 'openrouter':
      case 'ollama':
      case 'lmstudio':
      case 'custom':
        return (
          <>
            <Form.Item name="aiApiKey" label="API Key"><Input.Password size="large" /></Form.Item>
            <Form.Item name="aiModel" label="Default Model" rules={[{ required: true }]}><Input size="large" /></Form.Item>
          </>
        );
      default: return null;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={280} theme="light" style={{ padding: '32px 16px', borderRight: '1px solid #f0f0f0' }}>
        <div style={{ marginBottom: 40, textAlign: 'center' }}>
          <Title level={3} style={{ color: '#2563EB', margin: 0 }}>aegisOS</Title>
          <Text type="secondary">Enterprise Setup</Text>
        </div>
        <Steps direction="vertical" current={current} items={steps.map(s => ({ title: <span style={{ whiteSpace: 'nowrap' }}>{s.title}</span>, icon: s.icon }))} size="small" />
      </Sider>
      <Layout>
        <Header style={{ background: '#FFFFFF', borderBottom: '1px solid #f0f0f0', padding: '0 32px', display: 'flex', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>{steps[current]?.title}</Title>
        </Header>
        <Content style={{ padding: '48px', background: '#fafafa', display: 'flex', justifyContent: 'center' }}>
          <Card style={{ width: '100%', maxWidth: 700, borderRadius: 12, }} bordered={false}>
            {current < steps.length - 1 ? (
              <Form form={form} layout="vertical" size="large" preserve={true}>
                <div style={{ display: current === 0 ? 'block' : 'none', animation: current === 0 ? 'fadeIn 0.5s' : 'none' }}>
                  <Alert message="Configure the root organization for this self-hosted aegisOS instance." type="info" showIcon style={{ marginBottom: 24 }} />
                  <Form.Item name="orgName" label="Organization Name" rules={[{ required: true, message: 'Organization name is required' }]}><Input placeholder="VNU" /></Form.Item>
                </div>

                <div style={{ display: current === 1 ? 'block' : 'none', animation: current === 1 ? 'fadeIn 0.5s' : 'none' }}>
                  <Alert message="Super Admin acts as the ultimate authority for this installation." type="warning" showIcon style={{ marginBottom: 24 }} />
                  <Form.Item name="adminName" label="Super Admin Name" rules={[{ required: true, message: 'Super Admin Name is required' }]}><Input placeholder="Current User" /></Form.Item>
                  <Form.Item name="adminEmail" label="Super Admin Email" rules={[{ required: true, message: 'Valid email is required', type: 'email' }]}><Input placeholder="admin@vnu.com" /></Form.Item>
                  <Form.Item name="adminPassword" label="Super Admin Password" rules={[{ required: true, message: 'Password is required' }, { validator: passwordValidator }]} hasFeedback>
                    <Input.Password placeholder="Min 12 chars, upper, lower, num, special" />
                  </Form.Item>
                </div>

                <div style={{ display: current === 2 ? 'block' : 'none', animation: current === 2 ? 'fadeIn 0.5s' : 'none' }}>
                  <Form.Item name="aiProvider" label="Default AI Provider" rules={[{ required: true, message: 'AI Provider is required' }]}>
                    <Select options={AI_PROVIDERS} placeholder="Select AI Provider" />
                  </Form.Item>
                  <div style={{ background: '#f5f5f5', padding: 20, marginBottom: 24 }}>
                    {renderAiConfig() || <Text type="secondary">Select a provider to configure</Text>}
                  </div>
                  <Button type="default" onClick={() => testConnection('ai')} loading={testingAi} block>Verify AI Connection</Button>
                </div>

                {current === 3 && (
                  <div style={{ animation: 'fadeIn 0.5s', textAlign: 'center' }}>
                    <Title level={4}>Ready to Install</Title>
                    <Text type="secondary">Please confirm your configuration to begin the provisioning process.</Text>
                    <Divider />
                    <div style={{ background: '#f5f5f5', padding: 24, textAlign: 'left' }}>
                      <Row gutter={[16, 16]}>
                        <Col span={12}><Text strong>Organization:</Text></Col><Col span={12}><Text>{form.getFieldValue('orgName')}</Text></Col>
                        <Col span={12}><Text strong>Super Admin:</Text></Col><Col span={12}><Text>{form.getFieldValue('adminName')} ({form.getFieldValue('adminEmail')})</Text></Col>
                        <Col span={12}><Text strong>AI Provider:</Text></Col><Col span={12}><Text>{form.getFieldValue('aiProvider')}</Text></Col>
                        <Col span={12}><Text strong>Default Model:</Text></Col><Col span={12}><Text>{form.getFieldValue('aiModel')}</Text></Col>
                      </Row>
                    </div>
                  </div>
                )}

                {current === 4 && (
                  <div style={{ animation: 'fadeIn 0.5s', textAlign: 'center', padding: '40px 0' }}>
                    <Title level={4}>Provisioning Platform...</Title>
                    <Progress percent={99} status="active" strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} />
                    <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>Applying database schemas and initializing core services...</Text>
                  </div>
                )}

                {current === 5 && (
                  <div style={{ animation: 'fadeIn 0.5s', textAlign: 'center', padding: '20px 0' }}>
                    <Title level={4}>Health Checks</Title>
                    <Divider />
                    {healthStatus ? (
                      <Row gutter={[0, 16]} style={{ maxWidth: 400, margin: '0 auto', textAlign: 'left' }}>
                        <Col span={20}><Text strong>Database Connectivity</Text></Col><Col span={4}>{healthStatus.db ? <CheckCircleOutlined style={{color: '#52c41a', fontSize: 20}}/> : <CloseCircleOutlined style={{color: '#ff4d4f', fontSize: 20}}/>}</Col>
                        <Col span={20}><Text strong>Storage Connectivity</Text></Col><Col span={4}>{healthStatus.storage ? <CheckCircleOutlined style={{color: '#52c41a', fontSize: 20}}/> : <CloseCircleOutlined style={{color: '#ff4d4f', fontSize: 20}}/>}</Col>
                        <Col span={20}><Text strong>AI Gateway</Text></Col><Col span={4}>{healthStatus.ai ? <CheckCircleOutlined style={{color: '#52c41a', fontSize: 20}}/> : <CloseCircleOutlined style={{color: '#ff4d4f', fontSize: 20}}/>}</Col>
                      </Row>
                    ) : (
                      <Progress type="circle" percent={100} status="active" />
                    )}
                  </div>
                )}

                <Divider />
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  {current > 0 && current !== 4 && current !== 5 ? <Button size="large" onClick={() => setCurrent(current - 1)}>Back</Button> : <div/>}
                  {current !== 4 && <Button type="primary" size="large" onClick={onNext} loading={installing}>{current === 3 ? 'Start Installation' : current === 5 ? 'Complete Setup' : 'Next Step'}</Button>}
                </div>
              </Form>
            ) : (
              <div style={{ animation: 'fadeIn 0.5s' }}>
                <Result
                  status="success"
                  title="aegisOS Enterprise Ready"
                  subTitle="The platform has been securely provisioned and is ready for use."
                  extra={[<Button type="primary" size="large" key="console" onClick={onComplete}>Launch aegisOS</Button>]}
                />
              </div>
            )}
          </Card>
        </Content>
      </Layout>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}} />
    </Layout>
  );
}
