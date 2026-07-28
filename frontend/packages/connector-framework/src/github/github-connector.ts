import { UniversalConnector } from '@aegisos/contracts';

export class GitHubConnector {
  public meta: UniversalConnector = {
    id: 'github-connector',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    name: 'GitHub',
    version: '1.0.0',
    state: 'REGISTERED',
    supportedModalities: ['Batch', 'Incremental'],
    rateLimitTokensPerMinute: 5000,
  };

  private token: string | null = null;
  private owner: string | null = null;
  private repo: string | null = null;
  private branch: string = 'main';

  public authenticate(token: string) {
    this.token = token;
    this.meta.state = 'CONFIGURED';
  }

  public configure(owner: string, repo: string, branch: string) {
    this.owner = owner;
    this.repo = repo;
    this.branch = branch;
    this.meta.state = 'VALIDATED';
  }

  public async testConnection(): Promise<boolean> {
    if (!this.token) return false;
    try {
      const res = await fetch('https://api.github.com/user', {
        headers: {
          Authorization: `Bearer ${this.token}`,
          Accept: 'application/vnd.github.v3+json',
        },
      });
      if (res.ok) {
        this.meta.state = 'CONNECTED';
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  public async fetchFiles(): Promise<{ path: string; content: string }[]> {
    if (!this.token || !this.owner || !this.repo) throw new Error('Not configured');

    // Fetch latest commit on branch
    const branchRes = await fetch(
      `https://api.github.com/repos/${this.owner}/${this.repo}/branches/${this.branch}`,
      {
        headers: {
          Authorization: `Bearer ${this.token}`,
          Accept: 'application/vnd.github.v3+json',
        },
      },
    );
    if (!branchRes.ok) throw new Error('Failed to fetch branch');
    const branchData = await branchRes.json();
    const treeSha = branchData.commit.commit.tree.sha;

    // Fetch tree
    const treeRes = await fetch(
      `https://api.github.com/repos/${this.owner}/${this.repo}/git/trees/${treeSha}?recursive=1`,
      {
        headers: {
          Authorization: `Bearer ${this.token}`,
          Accept: 'application/vnd.github.v3+json',
        },
      },
    );
    if (!treeRes.ok) throw new Error('Failed to fetch tree');
    const treeData = await treeRes.json();

    // Filter to a few files for demo
    const files = treeData.tree
      .filter(
        (t: { type: string; path: string }) =>
          t.type === 'blob' && (t.path.endsWith('.md') || t.path.endsWith('.ts')),
      )
      .slice(0, 5);

    const results = [];
    for (const file of files) {
      const contentRes = await fetch(
        `https://api.github.com/repos/${this.owner}/${this.repo}/contents/${file.path}?ref=${this.branch}`,
        {
          headers: {
            Authorization: `Bearer ${this.token}`,
            Accept: 'application/vnd.github.v3+json',
          },
        },
      );
      if (contentRes.ok) {
        const contentData = await contentRes.json();
        let content = '';
        try {
          content = atob(contentData.content);
        } catch {
          content = 'Binary or invalid content';
        }
        results.push({ path: file.path, content });
      }
    }
    return results;
  }
}
