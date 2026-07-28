/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { Card, Tag, Button, Typography, Layout, Row, Col, List } from 'antd';
import { ShareAltOutlined, AppstoreAddOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { ApiClient } from '../api/client';

const { Title, Text } = Typography;
const { Content } = Layout;

export const GraphExplorer: React.FC = () => {
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);

  useEffect(() => {
    fetchGraph();
  }, []);

  const fetchGraph = async () => {
    const n = await ApiClient.get('/graph/nodes');
    const e = await ApiClient.get('/graph/edges');
    setNodes(n);
    setEdges(e);
  };

  const getTargetLabel = (id: string) => nodes.find((n) => n.id === id)?.label || id;
  const getSourceLabel = (id: string) => nodes.find((n) => n.id === id)?.label || id;

  return (
    <Layout style={{ minHeight: '100vh', padding: 24 }}>
      <Content>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={4}>
            <ShareAltOutlined /> Knowledge Graph Explorer
          </Title>
          <Button type="primary" icon={<AppstoreAddOutlined />}>
            Create Entity
          </Button>
        </div>

        <Row gutter={24}>
          <Col span={12}>
            <Card title="Graph Nodes (Entities)" style={{ height: '100%' }}>
              <List
                dataSource={nodes}
                renderItem={(node) => (
                  <List.Item actions={[<Button type="link">Detail</Button>]}>
                    <List.Item.Meta
                      title={node.label}
                      description={<Tag color="purple">{node.type}</Tag>}
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="Graph Edges (Relationships)" style={{ height: '100%' }}>
              <List
                dataSource={edges}
                renderItem={(edge) => (
                  <List.Item
                    actions={[
                      <Button type="link" danger>
                        Delete
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Text>
                          <Tag color="blue">{getSourceLabel(edge.source)}</Tag>{' '}
                          <ArrowRightOutlined />{' '}
                          <Tag color="green">{getTargetLabel(edge.target)}</Tag>
                        </Text>
                      }
                      description={<Text type="secondary">{edge.relationship}</Text>}
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};
