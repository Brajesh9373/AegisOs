/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, Typography, Button, Space, Descriptions, message, Select, Tag } from 'antd';
import { ArrowLeftOutlined, RobotOutlined, SaveOutlined } from '@ant-design/icons';
import { ApiClient } from '../api/client';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';

const { Title, Text } = Typography;

export const EmployeeDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [emp, setEmp] = useState<any>(null);

  useEffect(() => {
    ApiClient.get(`/employees/${id}`).then(setEmp);
  }, [id]);

  const changeStatus = async (status: string) => {
    try {
      await ApiClient.put(`/employees/${id}/status`, { status });
      setEmp({ ...emp, status });
      message.success(`Status updated to ${status}`);
    } catch (e: any) {
      ApiClient.handleError(e);
    }
  };

  if (!emp) return <div style={{ padding: 48, textAlign: 'center' }}>Loading...</div>;

  return (
    <PageContainer maxWidth={1200}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid #E5E7EB' }}>
        <Space size="middle">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/home')} style={{ color: '#111827', padding: 0 }} />
          <Title level={4} style={{ margin: 0, fontWeight: 600, color: '#111827' }}>
            <RobotOutlined style={{ marginRight: 8, color: '#2563EB' }} /> {emp.name}
          </Title>
          <Select value={emp.status} onChange={changeStatus} style={{ width: 140 }}>
            <Select.Option value="Draft">Draft</Select.Option>
            <Select.Option value="Configured">Configured</Select.Option>
            <Select.Option value="Ready">Ready</Select.Option>
            <Select.Option value="Disabled">Disabled</Select.Option>
          </Select>
        </Space>
        <Space>
          <Button type="primary" icon={<SaveOutlined />} style={{ background: '#2563EB', fontWeight: 500 }}>
            Save Configuration
          </Button>
        </Space>
      </div>

      <Panel bodyStyle={{ padding: 24 }}>
        <Tabs
          items={[
            {
              key: '1',
              label: 'Configuration',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <Descriptions column={2} bordered size="small">
                    <Descriptions.Item label="Role">{emp.role}</Descriptions.Item>
                    <Descriptions.Item label="Department">{emp.department}</Descriptions.Item>
                    <Descriptions.Item label="Purpose" span={2}>
                      {emp.purpose}
                    </Descriptions.Item>
                    <Descriptions.Item label="Human Owner">{emp.humanOwner}</Descriptions.Item>
                    <Descriptions.Item label="Manager">{emp.manager}</Descriptions.Item>
                  </Descriptions>
                </div>
              ),
            },
            {
              key: '2',
              label: 'Skills',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <pre style={{ background: '#F8FAFC', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', color: '#374151' }}>{JSON.stringify(emp.skills, null, 2)}</pre>
                </div>
              ),
            },
            {
              key: '3',
              label: 'Knowledge',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <pre style={{ background: '#F8FAFC', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', color: '#374151' }}>{JSON.stringify(emp.knowledge, null, 2)}</pre>
                </div>
              ),
            },
            {
              key: '4',
              label: 'Memory',
              children: (
                <div style={{ paddingTop: 16 }}>
                  <pre style={{ background: '#F8FAFC', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB', color: '#374151' }}>{JSON.stringify(emp.memory, null, 2)}</pre>
                </div>
              ),
            },
            {
              key: '5',
              label: 'Assignments',
              children: (
                <div style={{ paddingTop: 16, textAlign: 'center', padding: '40px 0' }}>
                  <Text type="secondary">No active assignments yet.</Text>
                </div>
              ),
            },
          ]}
        />
      </Panel>
    </PageContainer>
  );
};
