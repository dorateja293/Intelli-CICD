import { Link } from 'react-router-dom';
import { BrainCircuit, GitBranch, Rocket, ShieldCheck } from 'lucide-react';

export default function Landing() {
  const features = [
    'AI Failure Prediction',
    'GitHub Webhook Integration',
    'CI Log Analyzer',
    'Smart Test Selection',
    'Analytics Dashboard',
    'Multi-Project Support'
  ];
  const projectHighlights = [
    { label: 'Repository sync', value: 'Connect GitHub repos and review CI activity in one workspace.' },
    { label: 'Risk scoring', value: 'See failure probability before deciding whether to run full tests.' },
    { label: 'Pipeline insight', value: 'Track skipped jobs, saved time, and commit-level decisions.' },
  ];
  const workflowSteps = [
    { label: 'Code Push', value: 'Developer pushes changes to a GitHub repository.' },
    { label: 'Pipeline Trigger', value: 'Webhook starts build, dependency install, and test stages.' },
    { label: 'AI Analysis', value: 'Logs, code changes, and history are checked for failure patterns.' },
    { label: 'Decision Engine', value: 'Deployment is approved, blocked, or sent with a failure report.' },
  ];
  const modules = [
    'Git Integration',
    'CI Pipeline',
    'Log Collection',
    'AI/ML Analysis',
    'Recommendation Engine',
    'Decision Engine',
    'Deployment',
    'Notifications',
  ];

  return (
    <div className="min-h-screen bg-githubBg text-githubTextPrimary overflow-x-hidden">
      <nav className="h-16 px-8 flex justify-between items-center border-b border-githubBorder">
        <div className="font-bold text-xl text-white">Intelli-CI</div>
        <div className="flex gap-4">
          <Link to="/login" className="px-4 py-2 text-githubTextSecondary hover:text-white transition-colors text-sm font-medium">Login</Link>
          <Link to="/projects" className="px-4 py-2 text-githubTextSecondary hover:text-white transition-colors text-sm font-medium">Add Project</Link>
          <Link to="/signup" className="px-6 py-2 bg-githubPrimary text-white rounded-lg text-sm font-medium hover:bg-green-600 transition-colors">Get Started</Link>
        </div>
      </nav>
      
      <main className="max-w-7xl mx-auto px-8 py-32 flex flex-col gap-32">
        <section className="text-center">
          <h1 className="text-6xl font-extrabold text-white tracking-tight mb-6">AI-Powered CI/CD Optimization</h1>
          <p className="text-xl text-githubTextSecondary max-w-3xl mx-auto mb-10">
            Intelli CI/CD automates software building, testing, failure analysis, risk prediction, and deployment decisions so developers can resolve pipeline issues faster.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/signup" className="px-8 py-3 bg-githubPrimary text-white rounded-lg font-medium hover:bg-green-600 transition-colors">Get Started</Link>
            <Link to="/projects" className="px-8 py-3 border border-githubBorder rounded-lg font-medium hover:bg-githubCard hover:text-white transition-colors">Add Project</Link>
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr] gap-8">
          <div className="bg-githubCard border border-githubBorder p-8 rounded-xl">
            <p className="text-sm font-semibold text-githubPrimary mb-3">Project overview</p>
            <h2 className="text-3xl font-bold text-white mb-4">A smarter CI/CD pipeline from commit to deployment.</h2>
            <p className="text-githubTextSecondary leading-7">
              Traditional CI/CD runs builds and tests. Intelli CI/CD adds an intelligence layer that analyzes code changes, test results, build logs, and historical failures to predict risk and recommend fixes before deployment.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-8">
              <div className="rounded-lg border border-githubBorder bg-githubBg p-5">
                <BrainCircuit className="text-githubPrimary mb-4" size={24} />
                <h3 className="font-bold text-white mb-2">Predict failures</h3>
                <p className="text-sm text-githubTextSecondary leading-6">Estimate build failure risk from code churn, changed files, coverage, and previous failures.</p>
              </div>
              <div className="rounded-lg border border-githubBorder bg-githubBg p-5">
                <ShieldCheck className="text-githubPrimary mb-4" size={24} />
                <h3 className="font-bold text-white mb-2">Control deployment</h3>
                <p className="text-sm text-githubTextSecondary leading-6">Deploy only when build, tests, quality checks, and risk signals meet required conditions.</p>
              </div>
            </div>
          </div>

          <div className="bg-githubCard border border-githubBorder p-8 rounded-xl">
            <p className="text-sm font-semibold text-githubPrimary mb-3">Workflow</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {workflowSteps.map((step, index) => (
                <div key={step.label} className="rounded-lg border border-githubBorder bg-githubBg p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-githubPrimary text-sm font-bold text-white">{index + 1}</span>
                    <h3 className="font-bold text-white">{step.label}</h3>
                  </div>
                  <p className="text-sm text-githubTextSecondary leading-6">{step.value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr] gap-8 items-stretch">
          <div className="bg-githubCard border border-githubBorder p-8 rounded-xl">
            <p className="text-sm font-semibold text-githubPrimary mb-3">Project setup</p>
            <h2 className="text-3xl font-bold text-white mb-4">Add a GitHub project and start predicting CI risk.</h2>
            <p className="text-githubTextSecondary leading-7 mb-8">
              Bring a repository into Intelli-CI to monitor commits, analyze pipeline history, and identify when a lightweight test path is enough.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/projects" className="px-6 py-3 bg-githubPrimary text-white rounded-lg font-medium hover:bg-green-600 transition-colors text-center">Add Project</Link>
              <a
                href="https://github.com/new"
                target="_blank"
                rel="noreferrer"
                className="px-6 py-3 border border-githubBorder rounded-lg font-medium hover:bg-githubBg hover:text-white transition-colors text-center"
              >
                Open GitHub
              </a>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-1 gap-4">
            {projectHighlights.map((item) => (
              <div key={item.label} className="bg-githubCard border border-githubBorder p-6 rounded-xl">
                <h3 className="font-bold text-white mb-2">{item.label}</h3>
                <p className="text-sm text-githubTextSecondary leading-6">{item.value}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-8">
          <div className="bg-githubCard border border-githubBorder p-8 rounded-xl">
            <div className="flex items-center gap-3 mb-6">
              <GitBranch className="text-githubPrimary" size={24} />
              <h2 className="text-2xl font-bold text-white">Core Modules</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {modules.map((module) => (
                <div key={module} className="rounded-lg border border-githubBorder bg-githubBg px-4 py-3 text-sm font-semibold text-githubTextPrimary">
                  {module}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-githubCard border border-githubBorder p-8 rounded-xl">
            <div className="flex items-center gap-3 mb-6">
              <Rocket className="text-githubPrimary" size={24} />
              <h2 className="text-2xl font-bold text-white">Dashboard Reports</h2>
            </div>
            <div className="space-y-4">
              {['Build status and test results', 'Deployment status and release readiness', 'Failure predictions and risk reasons', 'AI-generated recommendations', 'Pipeline history and developer notifications'].map((item) => (
                <div key={item} className="rounded-lg border border-githubBorder bg-githubBg p-4 text-sm text-githubTextPrimary">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, idx) => (
              <div key={idx} className="bg-githubCard border border-githubBorder p-8 rounded-xl hover:shadow-lg transition-shadow">
                <h3 className="text-lg font-bold text-white mb-2">{feature}</h3>
                <p className="text-githubTextSecondary text-sm">Advanced AI logic seamlessly integrated.</p>
              </div>
            ))}
          </div>
        </section>
      </main>
      
      <footer className="border-t border-githubBorder py-12 text-center text-githubTextSecondary text-sm">
        <p>&copy; 2026 Intelli-CI. All rights reserved.</p>
      </footer>
    </div>
  );
}
