/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Typography, Layout, Row, Col, Space, Select, Badge } from 'antd';
import { DatabaseOutlined, PlusOutlined, TagOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

const { Title, Text } = Typography;
const { Content } = Layout;

export const KnowledgeCatalog: React.FC = () => {
  const [knowledge, setKnowledge] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    ApiClient.get('/knowledge').then(setKnowledge);
    ApiClient.get('/knowledge/categories').then(setCategories);
  }, []);

  const filteredKnowledge = selectedCategory
    ? knowledge.filter((k) =>
        k.tags?.some((t: string) => t.toLowerCase() === selectedCategory.toLowerCase())
      )
    : knowledge;

  const columns = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (t: string, r: any) => (
        <b>
          {t} {r.isBuiltIn === 1 && <Tag color="blue">Built-in</Tag>}
        </b>
      ),
    },
    { title: 'Type', dataIndex: 'type', key: 'type' },
    { title: 'Version', dataIndex: 'version', key: 'version' },
    {
      title: 'Category',
      dataIndex: 'type',
      key: 'category',
      render: (type: string) => {
        const cat = categories.find((c) => c.name === type);
        return cat ? (
          <Tag color={cat.color}>{cat.name}</Tag>
        ) : (
          <Tag>{type}</Tag>
        );
      },
    },
    {
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => tags?.map((t) => <Tag key={t}>{t}</Tag>),
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (c: number) => c ? `${Math.round(c * 100)}%` : '-',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (t: string) => (
        <Tag color={t === 'active' || t === 'Active' ? 'green' : 'orange'}>{t}</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'action',
      render: (_: any, r: any) => (
        <Button type="link" onClick={() => navigate(`/knowledge/${r.id}`)}>
          View Details
        </Button>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', padding: 24 }}>
      <Content>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={4}>
            <DatabaseOutlined /> Knowledge Registry
          </Title>
          <Button type="primary" icon={<PlusOutlined />}>
            Register Knowledge
          </Button>
        </div>

        {/* Categories Section */}
        {categories.length > 0 && (
          <Card
            title={
              <Space>
                <TagOutlined />
                <span>Categories</span>
              </Space>
            }
            style={{ marginBottom: 16 }}
            bodyStyle={{ padding: 16 }}
          >
            <Row gutter={[12, 12]}>
              <Col>
                <Badge
                  count={knowledge.length}
                  style={{ backgroundColor: '#1890ff' }}
                  offset={[8, -4]}
                >
                  <Tag
                    color={selectedCategory === null ? 'blue' : undefined}
                    style={{ cursor: 'pointer', padding: '4px 12px' }}
                    onClick={() => setSelectedCategory(null)}
                  >
                    All
                  </Tag>
                </Badge>
              </Col>
              {categories.map((cat) => {
                const count = knowledge.filter((k) =>
                  k.tags?.some((t: string) => t.toLowerCase() === cat.name.toLowerCase())
                ).length;
                return (
                  <Col key={cat.id}>
                    <Badge
                      count={count}
                      style={{ backgroundColor: cat.color || '#888' }}
                      offset={[8, -4]}
                    >
                      <Tag
                        color={selectedCategory === cat.name ? cat.color : undefined}
                        style={{
                          cursor: 'pointer',
                          padding: '4px 12px',
                          borderColor: cat.color,
                        }}
                        onClick={() =>
                          setSelectedCategory(selectedCategory === cat.name ? null : cat.name)
                        }
                      >
                        {cat.name}
                      </Tag>
                    </Badge>
                  </Col>
                );
              })}
            </Row>
            {selectedCategory && (
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">
                  Showing {filteredKnowledge.length} of {knowledge.length} items in{' '}
                  <Tag color={categories.find((c) => c.name === selectedCategory)?.color}>
                    {selectedCategory}
                  </Tag>
                </Text>
              </div>
            )}
          </Card>
        )}

        {/* Knowledge Table */}
        <Card>
          <Table dataSource={filteredKnowledge} columns={columns} rowKey="id" />
        </Card>
      </Content>
    </Layout>
  );
};
