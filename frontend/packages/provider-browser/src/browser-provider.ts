import {
  ProviderBase,
  ProviderCategory,
  ProviderCapabilities,
  ProviderConfigurationModel,
  ProviderLifecycleState,
  ProviderHealthContract,
} from '@aegisos/provider';
import { chromium, firefox, webkit, Browser, Page, BrowserContext } from 'playwright';

export interface BrowserProviderOptions {
  engine?: 'chromium' | 'firefox' | 'webkit';
  headless?: boolean;
}

export class BrowserProvider implements ProviderBase {
  public id: string = 'provider-browser';
  public name: string = 'Browser Automation';
  public version: string = '1.0.0';
  public description: string = 'Playwright-based Browser Provider';
  public category: ProviderCategory = ProviderCategory.Browser;
  public state: ProviderLifecycleState = ProviderLifecycleState.Registered;
  public createdAt: string = new Date().toISOString();
  public updatedAt: string = new Date().toISOString();

  private browser: Browser | null = null;
  private contexts: Map<string, BrowserContext> = new Map();
  private pages: Map<string, Page> = new Map();
  private options: BrowserProviderOptions = {};

  public capabilities: ProviderCapabilities = {
    supportedFeatures: [
      'chromium',
      'firefox',
      'webkit',
      'tabs',
      'cookies',
      'downloads',
      'uploads',
      'screenshots',
      'pdf',
      'selectors',
    ],
    supportedActions: ['navigate', 'click', 'type', 'screenshot', 'pdf', 'extract'],
  };

  public async initialize(config: ProviderConfigurationModel): Promise<void> {
    this.options = {
      engine: (config.options?.engine as 'chromium' | 'firefox' | 'webkit') || 'chromium',
      headless: config.options?.headless !== false,
    };

    const launcher = { chromium, firefox, webkit }[this.options.engine || 'chromium'];
    this.browser = await launcher.launch({ headless: this.options.headless });

    this.state = ProviderLifecycleState.Initialized;
  }

  public async healthCheck(): Promise<ProviderHealthContract> {
    if (!this.browser || !this.browser.isConnected()) {
      return { status: 'down', lastChecked: new Date().toISOString(), latencyMs: 0 };
    }
    return { status: 'healthy', lastChecked: new Date().toISOString(), latencyMs: 1 };
  }

  public async createTab(contextId: string = 'default'): Promise<string> {
    if (!this.browser) throw new Error('Browser not initialized');

    let context = this.contexts.get(contextId);
    if (!context) {
      context = await this.browser.newContext({ acceptDownloads: true });
      this.contexts.set(contextId, context);
    }

    const page = await context.newPage();
    const pageId = Math.random().toString(36).substring(7);
    this.pages.set(pageId, page);
    return pageId;
  }

  public async navigate(pageId: string, url: string): Promise<void> {
    const page = this.pages.get(pageId);
    if (!page) throw new Error('Page not found');
    await page.goto(url);
  }

  public async captureScreenshot(pageId: string): Promise<Buffer> {
    const page = this.pages.get(pageId);
    if (!page) throw new Error('Page not found');
    return await page.screenshot();
  }

  public async capturePdf(pageId: string): Promise<Buffer> {
    const page = this.pages.get(pageId);
    if (!page) throw new Error('Page not found');
    return await page.pdf();
  }

  public async getCookies(contextId: string = 'default'): Promise<unknown[]> {
    const context = this.contexts.get(contextId);
    if (!context) throw new Error('Context not found');
    return await context.cookies();
  }

  public async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
    this.state = ProviderLifecycleState.Registered;
  }
}
