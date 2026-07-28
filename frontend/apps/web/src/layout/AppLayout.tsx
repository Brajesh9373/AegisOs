import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Dropdown, Avatar, Input, Space, Typography } from 'antd';
import { ApiClient } from '../api/client';
import {
  HomeOutlined,
  ProjectOutlined,
  CheckSquareOutlined,
  FileTextOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  SearchOutlined,
  TeamOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

export function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [email, setEmail] = useState('');

  useEffect(() => {
    ApiClient.get('/auth/me').then(res => {
      setEmail(res.user.email);
    }).catch(() => {});
  }, []);

  const handleLogout = () => {
    ApiClient.post('/auth/logout', {}).catch(() => {});
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user_id');
    localStorage.removeItem('auth_role');
    navigate('/login');
  };

  const getMenuItems = () => {
    return [
      { key: '/home', icon: <HomeOutlined />, label: 'Dashboard' },
      { key: '/administration', icon: <SettingOutlined />, label: 'Administration' },
      { key: '/projects', icon: <ProjectOutlined />, label: 'Projects' },
      { key: '/queue', icon: <CheckSquareOutlined />, label: 'Human Queue' },
      { key: '/customers', icon: <TeamOutlined />, label: 'Customers' },
      { key: '/artifacts', icon: <FileTextOutlined />, label: 'Artifacts' },
    ];
  };

  const staticRouteNotice = (() => {
    const path = location.pathname;
    if (path === '/home') {
      return 'Dashboard is in progress. The overview cards on this screen use sample operating data until live analytics are connected.';
    }
    if (path.startsWith('/customers')) {
      return 'Customer CRM screens are in progress. Customer records shown here are static examples until we integrate opensource CRM.';
    }
    if (path.startsWith('/opportunities')) {
      return 'Opportunity workflow screens are in progress. This legacy opportunity flow uses static proposal/RFQ examples; the live project creation flow is under Projects > New Project.';
    }
    if (path.startsWith('/queue/chat')) {
      return 'AI Agent Chat is in progress. Real-time conversation with escalation agents will be available in a future release.';
    }
    return null;
  })();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        width={220}
        trigger={null}
        style={{
          borderRight: '1px solid #E5E7EB',
          background: '#FFFFFF',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <div
          style={{
            height: 64,
            padding: '0 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            borderBottom: '1px solid #E5E7EB',
            gap: 12,
          }}
        >
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: '#2563EB',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF',
            fontWeight: 700,
            fontSize: 14,
            flexShrink: 0
          }}>
            A
          </div>
          {!collapsed && <Text style={{ fontWeight: 600, fontSize: 15, color: '#111827' }}>aegisOS</Text>}
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          style={{
            background: 'transparent',
            borderRight: 'none',
            padding: '12px 8px',
            flex: 1
          }}
          items={getMenuItems()}
          onClick={(e) => navigate(e.key)}
        />
        <div
          style={{
            padding: '12px 16px',
            borderTop: '1px solid #E5E7EB',
            display: 'flex',
            justifyContent: 'center'
          }}
        >
          <div
            onClick={() => setCollapsed(!collapsed)}
            style={{ cursor: 'pointer', color: '#6B7280', fontSize: 16 }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>
        </div>
      </Sider>
      <Layout style={{ display: 'flex', flexDirection: 'column' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#FFFFFF',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid #E5E7EB',
            height: 64,
            lineHeight: '64px'
          }}
        >
          <Space size="large" style={{ flex: 1 }}>
            <Text style={{ fontWeight: 600, fontSize: 16, color: '#111827' }}>aegisOS</Text>
            <Input
              prefix={<SearchOutlined style={{ color: '#9CA3AF' }} />}
              placeholder="Global Search... (Projects, Workers, Artifacts)"
              style={{
                width: 400,
                background: '#F8FAFC',
                border: '1px solid #E5E7EB',
                borderRadius: 8
              }}
            />
          </Space>
          <Dropdown
            menu={{
              items: [
                { key: 'logout', icon: <LogoutOutlined />, label: 'Logout', onClick: handleLogout },
              ],
            }}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ background: '#F3F4F6', color: '#6B7280' }} />
              <Text style={{ color: '#4B5563', fontWeight: 500 }}>{email || 'admin@aegisos.com'}</Text>
            </Space>
          </Dropdown>
        </Header>
        <Content
          style={{
            flex: 1,
            background: '#F8FAFC',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'auto'
          }}
        >
          {staticRouteNotice && (
            <div style={{ margin: '16px 24px 0', padding: '10px 12px', borderRadius: 8, border: '1px solid #FED7AA', background: '#FFF7ED' }}>
              <Text style={{ fontSize: 12, color: '#9A3412' }}>{staticRouteNotice}</Text>
            </div>
          )}
          <div style={staticRouteNotice ? { opacity: 0.5, pointerEvents: 'none', transition: 'opacity 0.3s' } : {}}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
