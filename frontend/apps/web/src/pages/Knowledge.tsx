import React from 'react';
import { Card, Input, Row, Col, Tree, Typography } from 'antd';
const { Search } = Input;
const { Title } = Typography;

export function Knowledge() {
  const treeData = [
    {
      title: 'Engineering Docs',
      key: '0-0',
      children: [
        { title: 'Architecture.md', key: '0-0-0' },
        { title: 'API.md', key: '0-0-1' },
      ],
    },
    { title: 'HR Policies', key: '0-1', children: [{ title: 'Handbook.pdf', key: '0-1-0' }] },
  ];

  return (
    <Card style={{ height: '100%' }}>
      <Title level={3}>Knowledge Studio</Title>
      <Row gutter={16}>
        <Col span={6}>
          <Search placeholder="Search knowledge..." style={{ marginBottom: 16 }} />
          <Tree treeData={treeData} defaultExpandAll />
        </Col>
        <Col span={12}>
          <Card
            title="Graph View"
            size="small"
            style={{
              height: 400,
              background: '#fafafa',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ color: '#aaa' }}>React Flow Graph Placeholder</span>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="Metadata" size="small">
            <p>
              <strong>Type:</strong> Markdown
            </p>
            <p>
              <strong>Size:</strong> 2.4 KB
            </p>
            <p>
              <strong>Last Updated:</strong> Today
            </p>
          </Card>
        </Col>
      </Row>
    </Card>
  );
}
