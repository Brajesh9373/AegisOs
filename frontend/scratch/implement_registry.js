const fs = require('fs');
const path = require('path');

const pkgDir = 'd:/experiments/aegisOS/packages/runtime';
const registryDir = path.join(pkgDir, 'src', 'registry');
const testsDir = path.join(pkgDir, 'tests');

// Update registry/index.ts
fs.writeFileSync(path.join(registryDir, 'index.ts'), `
export interface IModuleMetadata {
    id: string;
    version: string;
    description?: string;
}

export enum ModuleState {
    REGISTERED = 'REGISTERED',
    DISCOVERED = 'DISCOVERED'
}

export interface IModuleRegistry {
    register(metadata: IModuleMetadata): void;
    discover(): IModuleMetadata[];
    lookup(id: string): IModuleMetadata | undefined;
    getState(id: string): ModuleState | undefined;
    validateRegistration(metadata: IModuleMetadata): boolean;
}

export class ModuleRegistry implements IModuleRegistry {
    private readonly modules = new Map<string, IModuleMetadata>();
    private readonly states = new Map<string, ModuleState>();

    public register(metadata: IModuleMetadata): void {
        if (!this.validateRegistration(metadata)) {
            throw new Error(\`Invalid module metadata for registration: \${metadata.id}\`);
        }
        if (this.modules.has(metadata.id)) {
            throw new Error(\`Module already registered: \${metadata.id}\`);
        }
        this.modules.set(metadata.id, metadata);
        this.states.set(metadata.id, ModuleState.REGISTERED);
    }

    public discover(): IModuleMetadata[] {
        const discovered = Array.from(this.modules.values());
        for (const meta of discovered) {
            this.states.set(meta.id, ModuleState.DISCOVERED);
        }
        return discovered;
    }

    public lookup(id: string): IModuleMetadata | undefined {
        return this.modules.get(id);
    }

    public getState(id: string): ModuleState | undefined {
        return this.states.get(id);
    }

    public validateRegistration(metadata: IModuleMetadata): boolean {
        return !!metadata && typeof metadata.id === 'string' && metadata.id.length > 0 && typeof metadata.version === 'string';
    }
}

export interface IServiceRegistry {}
export interface ICapabilityRegistry {}
`);

// Update index.ts to export the concrete ModuleRegistry
const idxFile = path.join(pkgDir, 'src', 'index.ts');
let idxContent = fs.readFileSync(idxFile, 'utf8');
idxContent = idxContent.replace(
    "export { IModuleRegistry, IServiceRegistry, ICapabilityRegistry } from './registry/index';",
    "export { IModuleRegistry, ModuleRegistry, IModuleMetadata, ModuleState, IServiceRegistry, ICapabilityRegistry } from './registry/index';"
);
fs.writeFileSync(idxFile, idxContent);

// Add tests
fs.writeFileSync(path.join(testsDir, 'registry.spec.ts'), `
import { ModuleRegistry, ModuleState } from '../src/registry/index';

describe('ModuleRegistry', () => {
    it('should register and lookup modules', () => {
        const registry = new ModuleRegistry();
        registry.register({ id: 'test.module', version: '1.0.0' });

        const mod = registry.lookup('test.module');
        expect(mod).toBeDefined();
        expect(mod?.version).toBe('1.0.0');
        expect(registry.getState('test.module')).toBe(ModuleState.REGISTERED);
    });

    it('should prevent duplicate registration', () => {
        const registry = new ModuleRegistry();
        registry.register({ id: 'test.module', version: '1.0.0' });
        expect(() => registry.register({ id: 'test.module', version: '1.0.1' })).toThrow();
    });
});
`);
