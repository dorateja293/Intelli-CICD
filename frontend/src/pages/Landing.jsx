import { Link } from 'react-router-dom'
import { Cpu, Zap, Shield, Activity, ArrowRight, Terminal, CheckCircle2, Github, GitBranch, TerminalSquare, AlertTriangle, Layers } from 'lucide-react'

export default function Landing() {
  return (
    <div className="min-h-screen bg-black text-[#ededed] overflow-hidden relative selection:bg-indigo-500/30">
      {/* Background Effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1200px] h-[600px] bg-indigo-600/15 rounded-full blur-[150px] pointer-events-none"></div>
      
      {/* Navbar */}
      <nav className="border-b border-white/5 px-6 md:px-12 h-20 flex items-center justify-between max-w-[1400px] mx-auto relative z-10 backdrop-blur-md bg-black/30 sticky top-0">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-[0_0_15px_rgba(99,102,241,0.4)] overflow-hidden">
             <div className="absolute inset-0 bg-white/20 blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
             <Layers size={18} className="text-white relative z-10" />
          </div>
          <span className="font-bold text-xl tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white to-[#a1a1aa]">Intelli-CI</span>
        </div>
        <div className="flex items-center gap-6">
          <Link to="/login" className="text-sm font-semibold text-[#a1a1aa] hover:text-white transition-colors hidden sm:block">Sign In</Link>
          <Link to="/signup" className="bg-white text-black px-5 py-2 rounded-lg text-sm font-bold shadow-[0_0_15px_rgba(255,255,255,0.2)] hover:scale-105 transition-transform duration-300">Get Started</Link>
        </div>
      </nav>
      
      {/* Hero */}
      <main className="relative z-10 pt-24 pb-20">
        <div className="max-w-[1200px] mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 mb-8 backdrop-blur-sm hover:bg-white/10 transition-colors cursor-pointer">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
            <span className="text-xs font-semibold text-indigo-300 uppercase tracking-widest">Intelli-CI v3.0 is Live</span>
            <ArrowRight size={14} className="text-indigo-400" />
          </div>
          
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-8 leading-[1.05]">
            Shipping code <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
              at the speed of thought.
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-[#a1a1aa] mb-12 max-w-2xl mx-auto font-medium leading-relaxed">
            The first AI-native CI/CD optimization layer. We analyze your commits in milliseconds to determine exactly what needs testing, cutting pipeline costs by up to 75%.
          </p>
          
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link to="/signup" className="group relative inline-flex items-center justify-center gap-2 bg-white text-black px-8 py-4 rounded-xl font-bold text-base hover:shadow-[0_0_30px_rgba(255,255,255,0.3)] hover:-translate-y-0.5 transition-all duration-300 w-full sm:w-auto">
              Start Optimizing <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform"/>
            </Link>
            <Link to="/dashboard" className="inline-flex items-center justify-center gap-2 bg-white/5 border border-white/10 text-white px-8 py-4 rounded-xl font-bold text-base hover:bg-white/10 hover:-translate-y-0.5 backdrop-blur-md transition-all duration-300 w-full sm:w-auto">
              <Terminal size={18} /> View Live Demo
            </Link>
          </div>
        </div>

        {/* Hero Dashboard UI Mockup */}
        <div className="mt-20 max-w-[1000px] mx-auto px-6 relative">
          <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/20 to-transparent blur-3xl -z-10"></div>
          <div className="glass-panel border border-white/10 rounded-2xl overflow-hidden shadow-2xl relative">
            <div className="h-12 bg-white/5 border-b border-white/10 flex items-center px-4 gap-2">
              <div className="w-3 h-3 rounded-full bg-rose-500"></div>
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              <div className="ml-4 px-3 py-1 rounded bg-black/40 text-[#71717a] text-xs font-mono border border-white/5">intelli-ci/predict</div>
            </div>
            <div className="p-6 bg-black/60 font-mono text-sm leading-relaxed overflow-x-auto whitespace-pre">
              <div className="flex gap-4 text-[#a1a1aa]">
                <span className="text-[#71717a] select-none">1</span>
                <span><span className="text-pink-400">import</span> {'{'} analyze_commit {'}'} <span className="text-pink-400">from</span> <span className="text-emerald-300">'@intelli-ci/core'</span>;</span>
              </div>
              <div className="flex gap-4 text-[#a1a1aa]">
                <span className="text-[#71717a] select-none">2</span>
                <span></span>
              </div>
              <div className="flex gap-4 text-[#a1a1aa]">
                <span className="text-[#71717a] select-none">3</span>
                <span><span className="text-indigo-400">const</span> prediction <span className="text-pink-400">=</span> <span className="text-blue-400">await</span> <span className="text-amber-200">analyze_commit</span>({'{'}</span>
              </div>
              <div className="flex gap-4 text-[#a1a1aa]">
                <span className="text-[#71717a] select-none">4</span>
                <span>  sha: <span className="text-emerald-300">'a1b2c3d4'</span>,</span>
              </div>
              <div className="flex gap-4 text-[#a1a1aa]">
                <span className="text-[#71717a] select-none">5</span>
                <span>  files_changed: <span className="text-purple-400">3</span>,</span>
              </div>
              <div className="flex gap-4 text-[#a1a1aa]">
                <span className="text-[#71717a] select-none">6</span>
                <span>  churn: <span className="text-purple-400">45</span></span>
              </div>
              <div className="flex gap-4 text-[#a1a1aa]">
                <span className="text-[#71717a] select-none">7</span>
                <span>{'}'});</span>
              </div>
              <div className="flex gap-4 text-[#a1a1aa]">
                <span className="text-[#71717a] select-none">8</span>
                <span></span>
              </div>
              <div className="flex gap-4 text-emerald-400 items-center mt-2 bg-emerald-500/10 p-2 rounded border border-emerald-500/20">
                <span className="text-[#71717a] select-none">9</span>
                <span><CheckCircle2 size={14} className="inline mr-2"/> {"// Result: { decision: 'SKIP_TESTS', confidence: 0.992 }"}</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Social Proof */}
      <section className="py-20 border-y border-white/5 bg-white/[0.02]">
        <p className="text-center text-sm font-semibold text-[#71717a] uppercase tracking-widest mb-8">Trusted by extremely paranoid engineering teams</p>
        <div className="flex flex-wrap justify-center gap-12 md:gap-24 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
           <div className="flex items-center gap-2 font-bold text-xl"><Github size={24}/> GitHub</div>
           <div className="flex items-center gap-2 font-bold text-xl"><Zap size={24}/> Vercel</div>
           <div className="flex items-center gap-2 font-bold text-xl"><TerminalSquare size={24}/> Linear</div>
           <div className="flex items-center gap-2 font-bold text-xl"><Activity size={24}/> Stripe</div>
        </div>
      </section>

      {/* Detailed Features */}
      <section className="py-32 relative">
        <div className="max-w-[1200px] mx-auto px-6 space-y-32">
          
          {/* Feature 1 */}
          <div className="flex flex-col md:flex-row items-center gap-16">
            <div className="flex-1 space-y-6">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-6">
                <Cpu size={24} />
              </div>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white">Deterministic <br/>AI Engine.</h2>
              <p className="text-lg text-[#a1a1aa] leading-relaxed">
                We don't just guess. Our model builds an Abstract Syntax Tree of your modifications, cross-references historical failure traces, and computes a definite probability score for your pipeline.
              </p>
              <ul className="space-y-3 pt-4">
                {['Sub-millisecond inference time', '99.2% verified recall rate', 'Local context awareness'].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-[#a1a1aa] font-medium"><CheckCircle2 size={18} className="text-indigo-400"/> {item}</li>
                ))}
              </ul>
            </div>
            <div className="flex-1 w-full">
              <div className="glass-panel p-8 relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"></div>
                <div className="space-y-4 relative z-10 w-full overflow-x-auto">
                  <div className="flex justify-between items-center p-4 bg-black/40 border border-white/5 rounded-xl min-w-[340px]">
                    <div className="flex items-center gap-3"><GitBranch className="text-[#71717a] shrink-0"/> <span className="font-mono text-sm text-[#ededed]">fix/auth-provider</span></div>
                    <span className="text-emerald-400 text-xs font-bold px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-md shrink-0">SKIP TESTS</span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-black/40 border border-white/5 rounded-xl min-w-[340px]">
                    <div className="flex items-center gap-3"><GitBranch className="text-[#71717a] shrink-0"/> <span className="font-mono text-sm text-[#ededed]">feat/payment-gateway</span></div>
                    <span className="text-rose-400 text-xs font-bold px-2 py-1 bg-rose-500/10 border border-rose-500/20 rounded-md shadow-[0_0_10px_rgba(244,63,94,0.2)] shrink-0">RUN TESTS</span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-black/40 border border-white/5 rounded-xl min-w-[340px]">
                    <div className="flex items-center gap-3"><GitBranch className="text-[#71717a] shrink-0"/> <span className="font-mono text-sm text-[#ededed]">chore/update-readme</span></div>
                    <span className="text-emerald-400 text-xs font-bold px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-md shrink-0">SKIP TESTS</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 2 */}
          <div className="flex flex-col md:flex-row-reverse items-center gap-16">
            <div className="flex-1 space-y-6">
              <div className="w-12 h-12 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-6">
                <Shield size={24} />
              </div>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white">Absolute <br/>Risk Boundaries.</h2>
              <p className="text-lg text-[#a1a1aa] leading-relaxed">
                You remain in control. Define strict confidence intervals. If the model isn't completely certain that a commit is safe, it automatically triggers a full test suite. No regressions.
              </p>
            </div>
            <div className="flex-1 w-full">
               <div className="glass-panel p-8">
                  <div className="mb-6 flex flex-wrap justify-between items-end gap-4">
                    <div>
                      <p className="text-sm font-bold text-[#a1a1aa] uppercase tracking-wider mb-2">Confidence Threshold</p>
                      <p className="text-3xl font-black text-white">95.0%</p>
                    </div>
                    <div className="px-3 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-bold flex items-center gap-2">
                       <AlertTriangle size={14}/> Strict Mode
                    </div>
                  </div>
                  <div className="w-full bg-white/5 h-3 rounded-full overflow-hidden flex">
                     <div className="bg-emerald-500 h-full w-[95%] shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                     <div className="bg-amber-500 h-full w-[5%] bg-[url('https://www.transparenttextures.com/patterns/diagonal-stripes.png')] opacity-80"></div>
                  </div>
                  <div className="flex justify-between text-xs text-[#71717a] mt-3 font-medium">
                     <span>0%</span>
                     <span>Required Confidence</span>
                     <span>100%</span>
                  </div>
               </div>
            </div>
          </div>

        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-indigo-600/10 border-t border-indigo-500/20"></div>
        <div className="max-w-[800px] mx-auto px-6 text-center relative z-10">
          <h2 className="text-4xl md:text-5xl font-black text-white mb-6 tracking-tight">Ready to slice your CI bill?</h2>
          <p className="text-xl text-[#a1a1aa] mb-10">Join thousands of developers shipping faster and spending less with Intelli-CI.</p>
          <Link to="/signup" className="inline-block bg-white text-black px-10 py-5 rounded-xl font-bold text-lg shadow-[0_0_30px_rgba(255,255,255,0.2)] hover:scale-105 transition-transform duration-300">
            Start Optimizing For Free
          </Link>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="border-t border-white/5 py-12 text-center bg-black relative z-10">
        <div className="flex items-center justify-center gap-3 mb-6 opacity-60 hover:opacity-100 transition-opacity cursor-pointer group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.1)] group-hover:shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all">
            <Layers size={18} />
          </div>
          <span className="font-bold text-lg tracking-tight text-white">Intelli-CI</span>
        </div>
        <p className="text-[#71717a] text-sm">© 2026 Intelli-CI Inc. All rights reserved.</p>
        <div className="flex justify-center gap-6 mt-6 text-[#71717a] text-sm font-medium">
          <a href="#" className="hover:text-white transition-colors">Twitter</a>
          <a href="#" className="hover:text-white transition-colors">GitHub</a>
          <a href="#" className="hover:text-white transition-colors">Discord</a>
        </div>
      </footer>
    </div>
  )
}