import React, { useState } from 'react';
import { Button, Space, Avatar, Input, Select, Modal, Form, Dropdown, MenuProps, Typography, message, ConfigProvider, theme, Row, Col, Tooltip } from 'antd';
import { useNavigate } from 'react-router-dom';
import { BankOutlined, PlusOutlined, SearchOutlined, DownloadOutlined, EllipsisOutlined, ProfileOutlined, FileTextOutlined, StopOutlined, SyncOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { PageContainer } from '../components/ui/PageContainer';
import { Panel } from '../components/ui/Panel';
import { ActionToolbar } from '../components/ui/ActionToolbar';
import { DataTable } from '../components/ui/DataTable';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ExecutiveCard } from '../components/ui/ExecutiveCard';

const { Title, Text } = Typography;
const { Option } = Select;

export function CustomerRegistry() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [industryFilter, setIndustryFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  const [customers, setCustomers] = useState([
    {
      id: 'cust-1',
      company: 'VNU',
      industry: 'Manufacturing',
      status: 'Active',
      owner: 'Current User',
      health: 'Good',
      runningProjects: 1,
      activeOpportunities: 2,
      lastActivity: '2 hours ago',
      contact: 'Sarah Jenkins',
      email: 'sarah@vnu.com',
      phone: '555-0193'
    },
    {
      id: 'cust-2',
      company: 'VNU',
      industry: 'Technology',
      status: 'Onboarding',
      owner: 'Alice Chen',
      health: 'Warning',
      runningProjects: 2,
      activeOpportunities: 4,
      lastActivity: '1 day ago',
      contact: 'Sarah Tech',
      email: 'sarah@global.com',
      phone: '555-0122'
    }
  ]);

  const handleAdd = () => {
    form.validateFields().then(values => {
      const newCustomer = {
        id: `cust-${Date.now()}`,
        company: values.company,
        industry: values.industry?.trim(),
        status: values.status || 'Active',
        owner: 'Current User',
        health: 'Good',
        runningProjects: 0,
        activeOpportunities: 0,
        lastActivity: 'Just now',
        contact: values.contact,
        email: values.email,
        phone: values.phone
      };
      setCustomers([...customers, newCustomer]);
      setIsModalVisible(false);
      form.resetFields();
      message.success('Customer added to registry.');
    });
  };

  const getActionMenu = (record: any): MenuProps => ({
    items: [
      { key: '1', label: 'View Details', icon: <ProfileOutlined />, onClick: () => navigate(`/customers/${record.id}`) },
      { key: '2', label: 'Create Opportunity', icon: <PlusOutlined />, onClick: () => navigate('/opportunities/new') },
      { key: '3', label: 'Upload RFP', icon: <FileTextOutlined />, onClick: () => navigate(`/opportunities/new`) },
      { key: '4', label: 'Archive', icon: <StopOutlined />, danger: true, onClick: () => message.info('Archived') }
    ]
  });

  const columns = [
    { 
      title: 'Company', 
      key: 'company', 
      render: (_: any, r: any) => (
        <Space>
          <Avatar icon={<BankOutlined />} style={{ backgroundColor: '#E5E7EB', color: '#2563EB' }} />
          <div>
            <Text strong style={{ display: 'block' }}>{r.company}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>{r.industry}</Text>
          </div>
        </Space>
      ) 
    },
    { title: 'Owner', dataIndex: 'owner', key: 'owner', render: (t: string) => <Text type="secondary">{t}</Text> },
    { 
      title: 'Status', 
      dataIndex: 'status', 
      key: 'status', 
      render: (t: string) => <StatusBadge status={t} /> 
    },
    { 
      title: 'Health', 
      dataIndex: 'health', 
      key: 'health', 
      render: (t: string) => (
        t === 'Good' ? <CheckCircleOutlined style={{ color: '#22C55E' }} /> : <WarningOutlined style={{ color: '#F59E0B' }} />
      ) 
    },
    { title: 'Active Opps', dataIndex: 'activeOpportunities', key: 'activeOpportunities', render: (t: number) => <Text style={{ color: '#2563EB' }}>{t}</Text> },
    { title: 'Running Projects', dataIndex: 'runningProjects', key: 'runningProjects', render: (t: number) => <Text style={{ color: '#22C55E' }}>{t}</Text> },
    { title: 'Last Activity', dataIndex: 'lastActivity', key: 'lastActivity', render: (t: string) => <Text style={{ color: '#6B7280', fontSize: 12 }}>{t}</Text> },
    { 
      title: 'Actions', 
      key: 'actions', 
      align: 'right' as const,
      render: (_: any, r: any) => (
        <Dropdown menu={getActionMenu(r)} trigger={['click']}>
          <Tooltip title="More Actions">
            <Button size="small" type="text" icon={<EllipsisOutlined />} />
          </Tooltip>
        </Dropdown>
      ) 
    }
  ];

  const filteredCustomers = customers.filter(c => {
    if (searchText && !c.company.toLowerCase().includes(searchText.toLowerCase())) return false;
    if (industryFilter && c.industry !== industryFilter) return false;
    if (statusFilter && c.status !== statusFilter) return false;
    return true;
  });

  return (
    
      <PageContainer maxWidth={1600}>
        
        <div style={{ marginBottom: 32 }}>
          <Title level={3} style={{ margin: 0, fontWeight: 600 }}>Customer Management</Title>
          <Text type="secondary">Manage enterprise customers and business relationships.</Text>
        </div>

        <Row gutter={16}>
          <Col span={4}><ExecutiveCard title="Customers" value={customers.length} valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
          <Col span={5}><ExecutiveCard title="Active Opportunities" value={customers.reduce((acc, c) => acc + c.activeOpportunities, 0)} valueColor='#2563EB' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
          <Col span={5}><ExecutiveCard title="Running Projects" value={customers.reduce((acc, c) => acc + c.runningProjects, 0)} valueColor="#22C55E" bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
          <Col span={5}><ExecutiveCard title="Knowledge Assets" value="3,042" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
          <Col span={5}><ExecutiveCard title="Memory Records" value="15.2M" valueColor='#111827' bg='#FFFFFF' borderColor='#E5E7EB' /></Col>
        </Row>

        <ActionToolbar
          extra={
            <Space>
              <Tooltip title="Download CSV">
                <Button icon={<DownloadOutlined />} onClick={() => message.success('Export started')}>Export</Button>
              </Tooltip>
              <Tooltip title="Refresh Data">
                <Button icon={<SyncOutlined />} onClick={() => message.info('Refreshing...')}>Refresh</Button>
              </Tooltip>
              <Tooltip title="Create a new enterprise customer">
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)} style={{ fontWeight: 600 }}>Add Customer</Button>
              </Tooltip>
            </Space>
          }
        >
          <Space>
            <Input 
              placeholder="Search customers..." 
              prefix={<SearchOutlined />} 
              value={searchText} 
              onChange={e => setSearchText(e.target.value)}
              style={{ width: 250 }}
            />
            <Select placeholder="All Industries" style={{ width: 160 }} allowClear onChange={setIndustryFilter}>
              <Option value="Manufacturing">Manufacturing</Option>
              <Option value="Technology">Technology</Option>
            </Select>
            <Select placeholder="All Statuses" style={{ width: 160 }} allowClear onChange={setStatusFilter}>
              <Option value="Active">Active</Option>
              <Option value="Onboarding">Onboarding</Option>
            </Select>
          </Space>
        </ActionToolbar>
        
        <DataTable 
          dataSource={filteredCustomers} 
          columns={columns} 
          rowKey="id"
        />

        <Modal
          title="Add New Customer"
          open={isModalVisible}
          onOk={handleAdd}
          onCancel={() => setIsModalVisible(false)}
          okText="Create Customer"
        >
          <Form form={form} layout="vertical">
            <Form.Item name="company" label="Company Name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item 
              name="industry" 
              label="Industry" 
              rules={[
                { required: true, message: 'Please enter an industry' },
                { max: 100, message: 'Industry cannot exceed 100 characters' }
              ]}
            >
              <Input placeholder="e.g. Manufacturing, Healthcare, Retail" maxLength={100} />
            </Form.Item>
            <Form.Item name="status" label="Status" initialValue="Active">
              <Select>
                <Option value="Active">Active</Option>
                <Option value="Onboarding">Onboarding</Option>
                <Option value="Prospect">Prospect</Option>
              </Select>
            </Form.Item>
            <Form.Item name="contact" label="Primary Contact" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="phone" label="Phone">
              <Input />
            </Form.Item>
            <Form.Item name="country" label="Country">
              <Input />
            </Form.Item>
          </Form>
        </Modal>

      </PageContainer>
    
  );
}
