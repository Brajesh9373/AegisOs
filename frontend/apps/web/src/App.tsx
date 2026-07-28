import React from 'react';
import { ConfigProvider, theme } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppRouter } from './router/AppRouter';
import { LifecycleProvider } from './context/LifecycleContext';
import 'antd/dist/reset.css';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{ 
          token: { 
            colorPrimary: '#2563EB',
            colorSuccess: '#16A34A',
            colorWarning: '#F59E0B',
            colorError: '#DC2626',
            colorInfo: '#0EA5E9',
            borderRadius: 12,
            fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            colorBgContainer: '#FFFFFF',
            colorBgLayout: '#F8FAFC',
            colorBorder: '#E5E7EB',
            colorText: '#111827',
            colorTextSecondary: '#6B7280',
          },
          components: {
            Button: {
              controlHeight: 36,
              borderRadius: 10,
              fontWeight: 500,
            },
            Card: {
              boxShadowTertiary: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
              borderRadiusLG: 12,
              headerBg: '#FFFFFF',
            },
            Table: {
              headerBg: '#F8FAFC',
              headerColor: '#6B7280',
              borderRadius: 8,
              borderColor: '#E5E7EB',
            },
            Input: {
              borderRadius: 10,
              controlHeight: 36,
              colorBorder: '#E5E7EB',
            },
            Select: {
              borderRadius: 10,
              controlHeight: 36,
            }
          }
        }}
      >
        <LifecycleProvider>
          <AppRouter />
        </LifecycleProvider>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
