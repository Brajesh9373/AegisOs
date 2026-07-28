import React from 'react';
import { Table } from 'antd';

interface DataTableProps {
  columns: any[];
  dataSource: any[];
  rowKey?: string;
  loading?: boolean;
}

export const DataTable: React.FC<DataTableProps> = ({ columns, dataSource, rowKey = 'id', loading = false }) => {
  return (
    <div style={{ border: '1px dashed #d9d9d9', padding: 16 }}>
      <Table 
        columns={columns} 
        dataSource={dataSource} 
        rowKey={rowKey} 
        loading={loading}
        pagination={false}
        style={{ background: 'transparent' }}
      />
    </div>
  );
};
