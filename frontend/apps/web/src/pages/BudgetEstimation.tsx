import React from 'react';
import { Typography, Row, Col, Button, Space, Table, ConfigProvider, theme, Divider } from 'antd';
import { ArrowLeftOutlined, DollarOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { Panel } from '../components/ui/Panel';
import { SectionHeader } from '../components/ui/SectionHeader';

const { Title, Text } = Typography;

export function BudgetEstimation() {
  const navigate = useNavigate();
  const { id } = useParams();

  const budgetData = [
    { key: '1', item: 'Architecture & Planning', hours: 40, rate: 150, cost: 6000 },
    { key: '2', item: 'Backend Engineering', hours: 160, rate: 120, cost: 19200 },
    { key: '3', item: 'Database Migration Tools', hours: 80, rate: 130, cost: 10400 },
    { key: '4', item: 'QA & Validation', hours: 80, rate: 90, cost: 7200 },
    { key: '5', item: 'Project Management', hours: 40, rate: 140, cost: 5600 },
    { key: '6', item: 'AI Token Consumption (Est)', hours: '-', rate: '-', cost: 1500 },
  ];

  const totalCost = budgetData.reduce((acc, curr) => acc + curr.cost, 0);
  const contingency = totalCost * 0.15;
  const finalBudget = totalCost + contingency;

  const columns = [
    { title: 'Item / Phase', dataIndex: 'item', key: 'item' },
    { title: 'Hours', dataIndex: 'hours', key: 'hours', align: 'right' as const },
    { title: 'Rate ($)', dataIndex: 'rate', key: 'rate', align: 'right' as const },
    { title: 'Total Cost ($)', dataIndex: 'cost', key: 'cost', align: 'right' as const, render: (val: number) => val.toLocaleString() }
  ];

  return (
    
      <div style={{ background: '#F8FAFC', minHeight: '100vh', padding: '24px 32px', fontFamily: 'monospace' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <Space size="middle" style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', width: '100%' }}>
            <Space>
              <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(`/opportunities/${id}/rfq`)} style={{ color: '#6B7280' }}>Back</Button>
              <Title level={4} style={{ margin: 0, fontWeight: 600 }}>Budget Estimation</Title>
            </Space>
            <Button type="primary" onClick={() => navigate(`/opportunities/${id}/proposal`)} style={{ background: '#2563EB', fontWeight: 600 }}>Generate Proposal</Button>
          </Space>

          <SectionHeader title="Detailed Budget Breakdown" />
          <Panel bodyStyle={{ padding: 24 }}>
            <Table 
              dataSource={budgetData} 
              columns={columns} 
              pagination={false}
              summary={() => (
                <>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={3} align="right"><Text strong>Subtotal</Text></Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right"><Text strong>${totalCost.toLocaleString()}</Text></Table.Summary.Cell>
                  </Table.Summary.Row>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={3} align="right"><Text style={{ color: '#6B7280' }}>Contingency (15%)</Text></Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right"><Text style={{ color: '#6B7280' }}>${contingency.toLocaleString()}</Text></Table.Summary.Cell>
                  </Table.Summary.Row>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={3} align="right"><Text strong style={{ color: '#2563EB', fontSize: 16 }}>Total Estimated Budget</Text></Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right"><Text strong style={{ color: '#2563EB', fontSize: 16 }}>${finalBudget.toLocaleString()}</Text></Table.Summary.Cell>
                  </Table.Summary.Row>
                </>
              )}
            />
          </Panel>
        </div>
      </div>
    
  );
}
