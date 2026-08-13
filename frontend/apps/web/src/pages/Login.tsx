
import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Checkbox } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

const { Title, Text } = Typography;

export function Login() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: Record<string, string>) => {
    setLoading(true);
    setError('');

    try {
      const res = await ApiClient.post('/auth/login', { email: values.email, password: values.password });
      localStorage.setItem('auth_token', res.token);
      localStorage.setItem('auth_user_id', res.user.id);
      localStorage.setItem('auth_role', res.user.role);
      navigate('/');
    } catch (err) {
      setError((err as Error).message || 'Invalid credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5', padding: '0 16px' }}>
      <Card style={{ width: '100%', maxWidth: 400, borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3} style={{ margin: 0 }}>aegisOS</Title>
          <Text type="secondary">Enterprise AI Operating System</Text>
        </div>

        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}

        <Form name="login" onFinish={onFinish} layout="vertical" size="large" initialValues={{ remember: true }}>
          <Form.Item name="email" rules={[{ required: true, type: 'email', message: 'Please input a valid email!' }]}>
            <Input prefix={<UserOutlined style={{ color: '#888' }} />} placeholder="Email" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: 'Please input your Password!' }]}>
            <Input.Password prefix={<LockOutlined style={{ color: '#888' }} />} placeholder="Password" />
          </Form.Item>
          <Form.Item name="remember" valuePropName="checked" style={{ marginBottom: 16 }}>
            <Checkbox>Remember me</Checkbox>
          </Form.Item>
          <Form.Item style={{ marginBottom: 12 }}>
            <Button type="primary" htmlType="submit" block loading={loading}>
              Sign In
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center' }}>
          <Text type="secondary">Don't have an account? </Text>
          <a href="/signup" onClick={(e) => { e.preventDefault(); navigate('/signup'); }} style={{ fontWeight: 600 }}>Create Account</a>
        </div>
      </Card>
    </div>
  );
}
