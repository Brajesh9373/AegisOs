import React from 'react';
import { Card, Tabs, Form, Input, Button, Switch, Select } from 'antd';

export function Settings() {
  return (
    <Card>
      <Tabs
        tabPosition="left"
        items={[
          {
            key: '1',
            label: 'Organization',
            children: (
              <Form layout="vertical">
                <Form.Item label="Organization Name">
                  <Input defaultValue="aegisOS (Self-Hosted)" disabled />
                </Form.Item>
                <Button type="primary">Save Changes</Button>
              </Form>
            ),
          },
          {
            key: '2',
            label: 'Security',
            children: (
              <Form layout="vertical">
                <Form.Item label="Enforce 2FA">
                  <Switch />
                </Form.Item>
                <Form.Item label="Session Timeout (mins)">
                  <Input type="number" defaultValue={60} />
                </Form.Item>
                <Button type="primary">Save Changes</Button>
              </Form>
            ),
          },
          {
            key: '3',
            label: 'Providers',
            children: (
              <Form layout="vertical">
                <Form.Item label="Active Provider">
                  <Select
                    defaultValue="openai"
                    options={[
                      { label: 'OpenAI', value: 'openai' },
                      { label: 'Gemini', value: 'gemini' },
                    ]}
                  />
                </Form.Item>
                <Form.Item label="API Key">
                  <Input.Password placeholder="Enter key..." />
                </Form.Item>
                <Button type="primary">Save Configuration</Button>
              </Form>
            ),
          },
          { key: '4', label: 'Connectors', children: <p>Connector settings...</p> },
          { key: '5', label: 'Licensing', children: <p>Self-Hosted License Valid.</p> },
          { key: '6', label: 'Audit', children: <p>Audit retention settings...</p> },
        ]}
      />
    </Card>
  );
}
