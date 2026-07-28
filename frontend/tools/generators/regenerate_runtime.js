const fs = require('fs');
const path = require('path');

const pkgDir = 'd:/experiments/aegisOS/packages/runtime';
const srcDir = path.join(pkgDir, 'src');
const testsDir = path.join(pkgDir, 'tests');

// Helper to write files ensuring no literal \n or \r substrings
function writeCleanFile(filePath, content) {
    if (content.includes('\\\\n') || content.includes('\\\\r')) {
        throw new Error('Validation Failed: Content contains literal escaped newline sequences');
    }
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(filePath, content, 'utf8');
}

// src/api/index.ts
writeCleanFile(path.join(srcDir, 'api/index.ts'), `
export interface IRuntimeEngine {
    start(): Promise<void>;
    stop(): Promise<void>;
}
`.trim() + '\n');

// src/bootstrap/index.ts
writeCleanFile(path.join(srcDir, 'bootstrap/index.ts'), `
import { ILifecycleManager } from '../lifecycle/index';
import { IModuleRegistry } from '../registry/index';
import { IDependencyResolver } from '../resolver/index';

export interface IBootstrapEngine {
    boot(): Promise<void>;
}

export class BootstrapEngine implements IBootstrapEngine {
    constructor(
        private readonly lifecycleManager: ILifecycleManager,
        private readonly moduleRegistry: IModuleRegistry,
        private readonly dependencyResolver: IDependencyResolver
    ) {}

    public async boot(): Promise<void> {
        await this.orchestrateStartup();
        await this.coordinateModuleDiscovery();
        this.triggerDependencyGraphValidation();
        await this.coordinateContainerInitialization();
        await this.transitionToReady();
    }

    private async orchestrateStartup(): Promise<void> {}
    private async coordinateModuleDiscovery(): Promise<void> {}
    private triggerDependencyGraphValidation(): void {}
    private async coordinateContainerInitialization(): Promise<void> {}
    private async transitionToReady(): Promise<void> {}
}
`.trim() + '\n');

// src/context/index.ts
writeCleanFile(path.join(srcDir, 'context/index.ts'), `
export interface IContextManager {
    setContext(key: string, value: unknown): void;
    getContext<T>(key: string): T | undefined;
}
`.trim() + '\n');

// src/errors/index.ts
writeCleanFile(path.join(srcDir, 'errors/index.ts'), `
export interface IErrorBoundary {
    catchPanic(error: unknown): void;
}
`.trim() + '\n');

// src/health/index.ts
writeCleanFile(path.join(srcDir, 'health/index.ts'), `
export interface IHealthManager {
    reportHealth(moduleId: string, isHealthy: boolean): void;
    isSystemHealthy(): boolean;
}
`.trim() + '\n');

// src/lifecycle/index.ts
writeCleanFile(path.join(srcDir, 'lifecycle/index.ts'), `
export interface ILifecycleManager {
    registerHook(phase: string, hook: () => Promise<void>): void;
    executePhase(phase: string): Promise<void>;
}
`.trim() + '\n');

// src/registry/index.ts
writeCleanFile(path.join(srcDir, 'registry/index.ts'), `
export interface IModuleMetadata {
    id: string;
    version: string;
    description?: string;
}

export const ModuleState = {
    REGISTERED: 'REGISTERED',
    DISCOVERED: 'DISCOVERED'
} as const;
export type ModuleState = typeof ModuleState[keyof typeof ModuleState];

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

export const ServiceLifetime = {
    SINGLETON: 'SINGLETON',
    TRANSIENT: 'TRANSIENT',
    SCOPED: 'SCOPED'
} as const;
export type ServiceLifetime = typeof ServiceLifetime[keyof typeof ServiceLifetime];

export interface IServiceMetadata {
    id: string;
    lifetime: ServiceLifetime;
    dependencies: string[];
    providedByModule: string;
}

export interface IServiceRegistry {
    register(metadata: IServiceMetadata): void;
    discover(): IServiceMetadata[];
    lookup(id: string): IServiceMetadata | undefined;
    validateRegistration(metadata: IServiceMetadata): boolean;
}

export class ServiceRegistry implements IServiceRegistry {
    private readonly services = new Map<string, IServiceMetadata>();

    public register(metadata: IServiceMetadata): void {
        if (!this.validateRegistration(metadata)) {
            throw new Error(\`Invalid service metadata for registration: \${metadata.id}\`);
        }
        if (this.services.has(metadata.id)) {
            throw new Error(\`Service already registered: \${metadata.id}\`);
        }
        this.services.set(metadata.id, metadata);
    }

    public discover(): IServiceMetadata[] {
        return Array.from(this.services.values());
    }

    public lookup(id: string): IServiceMetadata | undefined {
        return this.services.get(id);
    }

    public validateRegistration(metadata: IServiceMetadata): boolean {
        return !!metadata
            && typeof metadata.id === 'string'
            && metadata.id.length > 0
            && Object.values(ServiceLifetime).includes(metadata.lifetime)
            && Array.isArray(metadata.dependencies)
            && typeof metadata.providedByModule === 'string'
            && metadata.providedByModule.length > 0;
    }
}

export const CapabilityCategory = {
    SYSTEM: 'SYSTEM',
    DOMAIN: 'DOMAIN',
    INTEGRATION: 'INTEGRATION',
    AGENTIC: 'AGENTIC'
} as const;
export type CapabilityCategory = typeof CapabilityCategory[keyof typeof CapabilityCategory];

export interface ICapabilityMetadata {
    id: string;
    version: string;
    category: CapabilityCategory;
    description: string;
    providedByModule: string;
}

export interface ICapabilityRegistry {
    register(metadata: ICapabilityMetadata): void;
    discover(category?: CapabilityCategory): ICapabilityMetadata[];
    lookup(id: string): ICapabilityMetadata | undefined;
    validateRegistration(metadata: ICapabilityMetadata): boolean;
}

export class CapabilityRegistry implements ICapabilityRegistry {
    private readonly capabilities = new Map<string, ICapabilityMetadata>();

    public register(metadata: ICapabilityMetadata): void {
        if (!this.validateRegistration(metadata)) {
            throw new Error(\`Invalid capability metadata for registration: \${metadata.id}\`);
        }
        if (this.capabilities.has(metadata.id)) {
            throw new Error(\`Capability already registered: \${metadata.id}\`);
        }
        this.capabilities.set(metadata.id, metadata);
    }

    public discover(category?: CapabilityCategory): ICapabilityMetadata[] {
        const all = Array.from(this.capabilities.values());
        if (category) {
            return all.filter(c => c.category === category);
        }
        return all;
    }

    public lookup(id: string): ICapabilityMetadata | undefined {
        return this.capabilities.get(id);
    }

    public validateRegistration(metadata: ICapabilityMetadata): boolean {
        return !!metadata
            && typeof metadata.id === 'string'
            && metadata.id.length > 0
            && typeof metadata.version === 'string'
            && Object.values(CapabilityCategory).includes(metadata.category)
            && typeof metadata.providedByModule === 'string'
            && metadata.providedByModule.length > 0;
    }
}
`.trim() + '\n');

// src/resolver/index.ts
writeCleanFile(path.join(srcDir, 'resolver/index.ts'), `
export interface IDependencyNode {
    id: string;
    dependencies: string[];
}

export interface IDependencyResolver {
    buildGraph(nodes: IDependencyNode[]): void;
    validate(): void;
    getResolutionPlan(): string[];
}

export class DependencyResolver implements IDependencyResolver {
    private readonly graph = new Map<string, string[]>();

    public buildGraph(nodes: IDependencyNode[]): void {
        this.graph.clear();
        for (const node of nodes) {
            this.graph.set(node.id, [...node.dependencies]);
        }
    }

    public validate(): void {
        const visited = new Set<string>();
        const recursionStack = new Set<string>();

        const visit = (nodeId: string) => {
            if (recursionStack.has(nodeId)) {
                throw new Error(\`Circular dependency detected at node: \${nodeId}\`);
            }
            if (visited.has(nodeId)) {
                return;
            }

            visited.add(nodeId);
            recursionStack.add(nodeId);

            const deps = this.graph.get(nodeId) || [];
            for (const dep of deps) {
                if (!this.graph.has(dep)) {
                    throw new Error(\`Missing dependency: \${dep} required by \${nodeId}\`);
                }
                visit(dep);
            }

            recursionStack.delete(nodeId);
        };

        for (const nodeId of this.graph.keys()) {
            visit(nodeId);
        }
    }

    public getResolutionPlan(): string[] {
        this.validate();

        const plan: string[] = [];
        const visited = new Set<string>();

        const visit = (nodeId: string) => {
            if (visited.has(nodeId)) return;

            const deps = this.graph.get(nodeId) || [];
            for (const dep of deps) {
                visit(dep);
            }

            visited.add(nodeId);
            plan.push(nodeId);
        };

        for (const nodeId of this.graph.keys()) {
            visit(nodeId);
        }

        return plan;
    }
}
`.trim() + '\n');

// src/testing/index.ts
writeCleanFile(path.join(srcDir, 'testing/index.ts'), `
export interface IRuntimeTestHarness {
    mockContext(context: unknown): void;
}
`.trim() + '\n');

// src/index.ts
writeCleanFile(path.join(srcDir, 'index.ts'), `
export { IRuntimeEngine } from './api/index';
export { IBootstrapEngine, BootstrapEngine } from './bootstrap/index';
export {
    IModuleRegistry, ModuleRegistry, IModuleMetadata, ModuleState,
    IServiceRegistry, ServiceRegistry, IServiceMetadata, ServiceLifetime,
    ICapabilityRegistry, CapabilityRegistry, ICapabilityMetadata, CapabilityCategory
} from './registry/index';
export { ILifecycleManager } from './lifecycle/index';
export { IContextManager } from './context/index';
export { IHealthManager } from './health/index';
export { IErrorBoundary } from './errors/index';
export { IRuntimeTestHarness } from './testing/index';
export { IDependencyResolver, DependencyResolver, IDependencyNode } from './resolver/index';
`.trim() + '\n');

// tests/bootstrap.spec.ts
writeCleanFile(path.join(testsDir, 'bootstrap.spec.ts'), `
import { describe, it, expect } from 'vitest';
import { BootstrapEngine } from '../src/bootstrap/index';
import { ILifecycleManager } from '../src/lifecycle/index';
import { IModuleRegistry, ModuleState } from '../src/registry/index';
import { IDependencyResolver } from '../src/resolver/index';

describe('BootstrapEngine', () => {
    it('should implement the boot sequence without errors', async () => {
        const mockLifecycle: ILifecycleManager = {
            registerHook: () => {},
            executePhase: async () => {}
        };
        const mockRegistry: IModuleRegistry = {
            register: () => {},
            discover: () => [],
            lookup: () => undefined,
            getState: () => undefined,
            validateRegistration: () => false
        };
        const mockResolver: IDependencyResolver = {
            buildGraph: () => {},
            validate: () => {},
            getResolutionPlan: () => []
        };
        const engine = new BootstrapEngine(mockLifecycle, mockRegistry, mockResolver);
        await expect(engine.boot()).resolves.not.toThrow();
    });
});
`.trim() + '\n');

// tests/capabilityRegistry.spec.ts
writeCleanFile(path.join(testsDir, 'capabilityRegistry.spec.ts'), `
import { describe, it, expect } from 'vitest';
import { CapabilityRegistry, CapabilityCategory } from '../src/registry/index';

describe('CapabilityRegistry', () => {
    it('should register and lookup capabilities', () => {
        const registry = new CapabilityRegistry();
        registry.register({
            id: 'test.capability',
            version: '1.0.0',
            category: CapabilityCategory.DOMAIN,
            description: 'Test capability',
            providedByModule: 'test.module'
        });

        const capability = registry.lookup('test.capability');
        expect(capability).toBeDefined();
        expect(capability?.category).toBe(CapabilityCategory.DOMAIN);
    });

    it('should discover capabilities by category', () => {
        const registry = new CapabilityRegistry();
        registry.register({
            id: 'test.capability1',
            version: '1.0.0',
            category: CapabilityCategory.DOMAIN,
            description: 'Test capability',
            providedByModule: 'test.module'
        });
        registry.register({
            id: 'test.capability2',
            version: '1.0.0',
            category: CapabilityCategory.SYSTEM,
            description: 'Test capability',
            providedByModule: 'test.module'
        });

        const all = registry.discover();
        expect(all.length).toBe(2);

        const domainCaps = registry.discover(CapabilityCategory.DOMAIN);
        expect(domainCaps.length).toBe(1);
        expect(domainCaps[0].id).toBe('test.capability1');
    });

    it('should prevent duplicate registration', () => {
        const registry = new CapabilityRegistry();
        const meta = {
            id: 'test.capability',
            version: '1.0.0',
            category: CapabilityCategory.DOMAIN,
            description: 'Test',
            providedByModule: 'test.module'
        };
        registry.register(meta);
        expect(() => registry.register(meta)).toThrow();
    });

    it('should validate strict registration requirements', () => {
        const registry = new CapabilityRegistry();
        expect(() => registry.register({ id: '', version: '1.0.0', category: CapabilityCategory.DOMAIN, description: '', providedByModule: 'mod' })).toThrow();
    });
});
`.trim() + '\n');

// tests/registry.spec.ts
writeCleanFile(path.join(testsDir, 'registry.spec.ts'), `
import { describe, it, expect } from 'vitest';
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
`.trim() + '\n');

// tests/resolver.spec.ts
writeCleanFile(path.join(testsDir, 'resolver.spec.ts'), `
import { describe, it, expect } from 'vitest';
import { DependencyResolver } from '../src/resolver/index';

describe('DependencyResolver', () => {
    it('should build a resolution plan correctly', () => {
        const resolver = new DependencyResolver();
        resolver.buildGraph([
            { id: 'A', dependencies: ['B', 'C'] },
            { id: 'B', dependencies: ['D'] },
            { id: 'C', dependencies: ['D'] },
            { id: 'D', dependencies: [] }
        ]);

        resolver.validate();
        const plan = resolver.getResolutionPlan();
        expect(plan.indexOf('D')).toBeLessThan(plan.indexOf('B'));
        expect(plan.indexOf('D')).toBeLessThan(plan.indexOf('C'));
        expect(plan.indexOf('B')).toBeLessThan(plan.indexOf('A'));
        expect(plan.indexOf('C')).toBeLessThan(plan.indexOf('A'));
    });

    it('should detect missing dependencies', () => {
        const resolver = new DependencyResolver();
        resolver.buildGraph([
            { id: 'A', dependencies: ['B'] }
        ]);

        expect(() => resolver.validate()).toThrow(/Missing dependency/);
    });

    it('should detect circular dependencies', () => {
        const resolver = new DependencyResolver();
        resolver.buildGraph([
            { id: 'A', dependencies: ['B'] },
            { id: 'B', dependencies: ['C'] },
            { id: 'C', dependencies: ['A'] }
        ]);

        expect(() => resolver.validate()).toThrow(/Circular dependency/);
    });
});
`.trim() + '\n');

// tests/runtime.spec.ts
writeCleanFile(path.join(testsDir, 'runtime.spec.ts'), `
import { describe, it, expect } from 'vitest';
import * as Runtime from '../src/index';

describe('Runtime API Surface', () => {
    it('should expose defined contracts', () => {
        expect(Runtime).toBeDefined();
    });
});
`.trim() + '\n');

// tests/serviceRegistry.spec.ts
writeCleanFile(path.join(testsDir, 'serviceRegistry.spec.ts'), `
import { describe, it, expect } from 'vitest';
import { ServiceRegistry, ServiceLifetime } from '../src/registry/index';

describe('ServiceRegistry', () => {
    it('should register and lookup services', () => {
        const registry = new ServiceRegistry();
        registry.register({
            id: 'test.service',
            lifetime: ServiceLifetime.SINGLETON,
            dependencies: [],
            providedByModule: 'test.module'
        });

        const service = registry.lookup('test.service');
        expect(service).toBeDefined();
        expect(service?.lifetime).toBe(ServiceLifetime.SINGLETON);
    });

    it('should prevent duplicate registration', () => {
        const registry = new ServiceRegistry();
        const meta = {
            id: 'test.service',
            lifetime: ServiceLifetime.SINGLETON,
            dependencies: [],
            providedByModule: 'test.module'
        };
        registry.register(meta);
        expect(() => registry.register(meta)).toThrow();
    });

    it('should validate strict registration requirements', () => {
        const registry = new ServiceRegistry();
        expect(() => registry.register({ id: '', lifetime: ServiceLifetime.SINGLETON, dependencies: [], providedByModule: 'mod' })).toThrow();
    });
});
`.trim() + '\n');

console.log('All runtime source and test files perfectly regenerated from clean templates.');
