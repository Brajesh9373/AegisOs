import { RuntimeAPI } from '../api/runtime-api';
import { ConfigurationRegistry } from '@aegisos/config';

export function createMockRuntime(): RuntimeAPI {
  ConfigurationRegistry._reset();
  process.env.NODE_ENV = 'test';
  process.env.APP_NAME = 'TestRuntime';
  return new RuntimeAPI();
}
